"""
Case 1: Market Making Bot Prototype
====================================
UChicago Trading Competition 2026

Assets:
  - Stock A  : small-cap, earnings-driven (constant P/E)
  - Stock B  : semiconductor, no direct info — trade via options only
  - Stock C  : large-cap insurance, driven by earnings + Fed rate expectations
  - ETF      : 1 share of A + 1 share of B + 1 share of C (swap-able for a fee)
  - Options  : European calls/puts on B across 3 strikes (single expiry per round)
  - Fed Mkt  : prediction market — hike/hold/cut probabilities
  - Meta Mkt : revealed on competition day

Structure:
  - Each round = 10 days, each day = 90 seconds, each second = 5 ticks
  - Positions reset at end of each round
  - Scored on consistent P&L (nonlinear schema penalizes variance)

Strategies implemented:
  1. Stock A market making around earnings-derived fair value
  2. Stock C fair value from operations + bond portfolio model
  3. Fed prediction market parsing → yield update → C fair value update
  4. ETF arbitrage (creation/redemption)
  5. Options put-call parity arbitrage on B
  6. Symmetric market making with inventory skew
"""

import math
from collections import defaultdict

# ─── TUNEABLE PARAMETERS ────────────────────────────────────────────────────
# Adjust these without touching strategy logic.

# --- Market making spreads (in price units, each side from fair value) ---
MM_SPREAD_A   = 0.10   # half-spread quoted around fair value of A
MM_SPREAD_C   = 0.15   # half-spread quoted around fair value of C
MM_SPREAD_ETF = 0.20   # half-spread quoted around ETF fair value
MM_SPREAD_FED = 0.03   # half-spread for Fed prediction market quotes

# --- Order sizes ---
ORDER_SIZE_A   = 5
ORDER_SIZE_C   = 5
ORDER_SIZE_ETF = 3
ORDER_SIZE_OPT = 2     # options order size
ORDER_SIZE_FED = 10    # prediction market order size

# --- Inventory skew: shift quotes away from current position ---
# Per unit of inventory, skew quotes by this many price units
INVENTORY_SKEW_A   = 0.01
INVENTORY_SKEW_C   = 0.01
INVENTORY_SKEW_ETF = 0.01

# --- Max absolute position limits (self-imposed, conservative) ---
MAX_POS_A   = 50
MAX_POS_C   = 50
MAX_POS_ETF = 20
MAX_POS_OPT = 20    # per strike per side

# --- ETF arbitrage: minimum net edge to trigger swap (after swap fee) ---
ETF_SWAP_FEE      = 0.05   # fee per swap (creation or redemption)
ETF_ARB_THRESHOLD = 0.10   # min |ETF_price - NAV| - swap_fee to trade

# --- Options: min PCP violation to trigger arbitrage ---
PCP_ARB_THRESHOLD = 0.10

# --- Stock A model ---
A_PE_RATIO = 15.0   # constant P/E ratio for stock A

# --- Stock C model (from case packet formulas) ---
# P_C = EPS_C * PE_C + lambda * dB/N + noise
# PE_C = PE0_C * exp(-gamma * (y - y0))
# dB = B0 * (-D*dy + 0.5*C_conv*dy^2)
C_PE0    = 12.0    # baseline P/E for C at y0
C_GAMMA  = 2.0     # P/E sensitivity to yield changes
C_B0     = 1000.0  # baseline bond portfolio value
C_D      = 5.0     # duration constant
C_CONV   = 20.0    # convexity constant
C_N      = 100.0   # number of outstanding shares (divisor)
C_LAMBDA = 0.5     # bond portfolio weighting constant

# --- Fed / yield model ---
Y0            = 0.04   # baseline yield (4%)
BETA_Y        = 0.001  # yield sensitivity to expected rate change (bps)
# E[dr] = 25*q_hike + 0*q_hold - 25*q_cut  (in bps)

# --- Risk-free rate for put-call parity ---
RISK_FREE_RATE = 0.05  # annualized, used in C - P = S - K*e^(-rT)

# ─── STATE ───────────────────────────────────────────────────────────────────

class BotState:
    """Holds all mutable state for the bot."""

    def __init__(self):
        # Latest fair values (our model's estimate of true price)
        self.fair_A   = None
        self.fair_C   = None
        self.fair_ETF = None  # = fair_A + fair_B_mid + fair_C

        # Latest market mid prices (from order book)
        self.mid_A   = None
        self.mid_B   = None   # used only for options, not direct trading
        self.mid_C   = None
        self.mid_ETF = None

        # Current positions
        self.pos_A   = 0
        self.pos_B   = 0   # should stay ~0; we trade B only via options
        self.pos_C   = 0
        self.pos_ETF = 0
        self.pos_opts = defaultdict(int)  # key: (strike, 'call'/'put')

        # Stock A earnings state
        self.eps_A   = None   # latest EPS for A

        # Stock C earnings state
        self.eps_C   = None   # latest EPS for C

        # Fed market probabilities
        self.q_hike  = 1/3
        self.q_hold  = 1/3
        self.q_cut   = 1/3

        # Derived yield and C P/E
        self.yield_y = Y0
        self.pe_C    = C_PE0

        # Options chain: {strike: {'call_bid', 'call_ask', 'put_bid', 'put_ask', 'expiry_T'}}
        self.options = {}

        # Tick counter (for timing logic)
        self.tick = 0
        self.day  = 0

    # ── Derived fair values ──────────────────────────────────────────────────

    def update_fair_A(self):
        """Fair value of A = EPS_A * constant_PE."""
        if self.eps_A is not None:
            self.fair_A = self.eps_A * A_PE_RATIO

    def update_yield_from_fed(self):
        """
        Expected rate change (bps):
          E[dr] = 25*q_hike + 0*q_hold - 25*q_cut
        Yield:
          y = y0 + beta_y * E[dr]
        """
        e_dr = 25 * self.q_hike + 0 * self.q_hold + (-25) * self.q_cut
        self.yield_y = Y0 + BETA_Y * e_dr
        # Update C's P/E given new yield
        dy = self.yield_y - Y0
        self.pe_C = C_PE0 * math.exp(-C_GAMMA * dy)

    def update_fair_C(self):
        """
        Fair value of C:
          dB = B0 * (-D*dy + 0.5*C_conv*dy^2)
          P_C = EPS_C * PE_C + lambda * dB / N
        """
        if self.eps_C is None:
            return
        dy = self.yield_y - Y0
        d_bond = C_B0 * (-C_D * dy + 0.5 * C_CONV * dy**2)
        self.fair_C = self.eps_C * self.pe_C + C_LAMBDA * d_bond / C_N

    def update_fair_ETF(self):
        """
        ETF NAV = fair_A + mid_B + fair_C
        We use mid_B for B since we have no direct model for it.
        """
        b_val = self.mid_B if self.mid_B is not None else 0
        a_val = self.fair_A if self.fair_A is not None else (self.mid_A or 0)
        c_val = self.fair_C if self.fair_C is not None else (self.mid_C or 0)
        self.fair_ETF = a_val + b_val + c_val


state = BotState()


# ─── MESSAGE HANDLERS ────────────────────────────────────────────────────────
# The exchange calls these functions when it delivers updates.
# Replace the stub bodies with actual exchange API calls.

def on_tick(client, tick_data):
    """
    Called every tick (~18 times per second per day).
    tick_data: dict with order book snapshots, trade prints, news, etc.
    """
    state.tick += 1

    # 1. Parse order books → update mid prices
    _parse_order_books(tick_data)

    # 2. Parse any news messages
    _parse_news(tick_data)

    # 3. Recompute fair values
    state.update_fair_A()
    state.update_yield_from_fed()
    state.update_fair_C()
    state.update_fair_ETF()

    # 4. Market-make on A and C
    _quote_stock(client, 'A', state.fair_A, state.pos_A,
                 MM_SPREAD_A, ORDER_SIZE_A, MAX_POS_A, INVENTORY_SKEW_A)
    _quote_stock(client, 'C', state.fair_C, state.pos_C,
                 MM_SPREAD_C, ORDER_SIZE_C, MAX_POS_C, INVENTORY_SKEW_C)

    # 5. ETF arbitrage
    _etf_arb(client)

    # 6. Options: put-call parity arbitrage on B
    _options_pcp_arb(client)

    # 7. Fed market: quote around our probability estimates
    _quote_fed_market(client)


def on_position_update(positions: dict):
    """Called by exchange when fills occur. Update our position tracking."""
    state.pos_A   = positions.get('A',   state.pos_A)
    state.pos_B   = positions.get('B',   state.pos_B)
    state.pos_C   = positions.get('C',   state.pos_C)
    state.pos_ETF = positions.get('ETF', state.pos_ETF)
    for key, qty in positions.items():
        if isinstance(key, tuple):  # (strike, side)
            state.pos_opts[key] = qty


# ─── PARSING HELPERS ─────────────────────────────────────────────────────────

def _parse_order_books(tick_data: dict):
    """
    Extract best bid/ask from order books and compute mid prices.
    Adapt field names to match the actual exchange message schema.
    """
    books = tick_data.get('order_books', {})

    for symbol in ('A', 'B', 'C', 'ETF'):
        book = books.get(symbol)
        if book:
            best_bid = book['bids'][0][0] if book['bids'] else None
            best_ask = book['asks'][0][0] if book['asks'] else None
            if best_bid and best_ask:
                mid = (best_bid + best_ask) / 2
                setattr(state, f'mid_{symbol}', mid)

    # Options chain
    opts = tick_data.get('options', {})  # {strike: {call_bid, call_ask, put_bid, put_ask, T}}
    for strike, data in opts.items():
        state.options[strike] = data
        # Keep a rough B mid from options ATM if no direct book
        if state.mid_B is None and abs(strike - (state.mid_B or strike)) < 5:
            state.mid_B = strike  # rough proxy; replace with actual B book if available


def _parse_news(tick_data: dict):
    """
    Parse structured and unstructured news.

    Structured news types (adapt field names to exchange schema):
      - 'earnings_A': {'eps': float}
      - 'earnings_C': {'eps': float}
      - 'cpi_print':  {'forecasted': float, 'actual': float}
      - 'fed_probs':  {'hike': float, 'hold': float, 'cut': float}
    """
    news = tick_data.get('news', [])
    for msg in news:
        kind = msg.get('type')

        if kind == 'earnings_A':
            state.eps_A = msg['eps']

        elif kind == 'earnings_C':
            state.eps_C = msg['eps']

        elif kind == 'fed_probs':
            # Exchange provides quoted probabilities directly
            state.q_hike = msg['hike']
            state.q_hold = msg['hold']
            state.q_cut  = msg['cut']

        elif kind == 'cpi_print':
            # Adjust Fed probabilities based on CPI surprise
            # Actual > Forecasted → inflationary → shift toward hike
            surprise = msg['actual'] - msg['forecasted']
            _update_fed_probs_from_cpi(surprise)

        elif kind == 'headline':
            # Unstructured news: do simple keyword sentiment for now
            _parse_headline(msg.get('text', ''))


def _update_fed_probs_from_cpi(surprise: float):
    """
    Shift Fed probability mass toward hike (surprise > 0) or cut (surprise < 0).
    Magnitude of shift is proportional to |surprise|.
    This is a simple heuristic; refine with historical calibration.
    """
    # Sensitivity: each 0.1 CPI surprise shifts 10% probability mass
    SENSITIVITY = 1.0   # fraction of prob to shift per unit surprise

    shift = min(abs(surprise) * SENSITIVITY, 0.3)  # cap at 30% shift
    if surprise > 0:
        # Inflationary: shift from cut → hike
        transfer = min(shift, state.q_cut)
        state.q_cut  -= transfer
        state.q_hike += transfer
    else:
        # Deflationary: shift from hike → cut
        transfer = min(shift, state.q_hike)
        state.q_hike -= transfer
        state.q_cut  += transfer

    # Normalize so probabilities sum to 1
    total = state.q_hike + state.q_hold + state.q_cut
    state.q_hike /= total
    state.q_hold /= total
    state.q_cut  /= total


def _parse_headline(text: str):
    """
    Very basic keyword sentiment for unstructured Fed headlines.
    Replace with a more sophisticated NLP approach if time permits.
    """
    text_l = text.lower()
    hike_words = ['inflation', 'hike', 'hawkish', 'overheat', 'hot']
    cut_words  = ['recession', 'cut', 'dovish', 'slowdown', 'weak', 'cool']

    hike_score = sum(1 for w in hike_words if w in text_l)
    cut_score  = sum(1 for w in cut_words  if w in text_l)

    net = hike_score - cut_score
    if net != 0:
        _update_fed_probs_from_cpi(net * 0.05)  # treat each keyword hit as 0.05 surprise


# ─── MARKET MAKING ───────────────────────────────────────────────────────────

def _quote_stock(client, symbol: str, fair: float, position: int,
                 half_spread: float, size: int, max_pos: int, skew_per_unit: float):
    """
    Post a two-sided quote around `fair` with inventory skew.

    Inventory skew: if we're long, lower both bid and ask to encourage sells;
    if short, raise both to encourage buys.
    """
    if fair is None:
        return  # no model yet, don't quote blindly

    # Skew: push quotes away from direction of inventory
    skew = position * skew_per_unit

    bid_price = round(fair - half_spread - skew, 2)
    ask_price = round(fair + half_spread - skew, 2)

    # Don't post if position is at limit (on the side that would worsen it)
    bid_size = size if position < max_pos  else 0
    ask_size = size if position > -max_pos else 0

    if bid_size > 0:
        _place_limit_order(client, symbol, 'buy',  bid_price, bid_size)
    if ask_size > 0:
        _place_limit_order(client, symbol, 'sell', ask_price, ask_size)


def _quote_fed_market(client):
    """
    Quote the Fed prediction market.
    Our 'fair' probability for each outcome comes from state.q_hike/hold/cut.
    We quote a small spread around each.

    The market quotes prices in [0, 1] where price ≈ probability.
    """
    for outcome, q in [('hike', state.q_hike), ('hold', state.q_hold), ('cut', state.q_cut)]:
        bid = max(0.0, round(q - MM_SPREAD_FED, 4))
        ask = min(1.0, round(q + MM_SPREAD_FED, 4))
        _place_limit_order(client, f'FED_{outcome}', 'buy',  bid, ORDER_SIZE_FED)
        _place_limit_order(client, f'FED_{outcome}', 'sell', ask, ORDER_SIZE_FED)


# ─── ETF ARBITRAGE ───────────────────────────────────────────────────────────

def _etf_arb(client):
    """
    ETF NAV = A + B + C (one share each).
    If ETF market price deviates from NAV by more than swap_fee + threshold, arb it.

    Creation  (NAV < ETF price): buy A+B+C, swap into ETF, sell ETF
    Redemption (NAV > ETF price): buy ETF, swap into A+B+C, sell A+B+C

    The hint says: when ETF and equity prices diverge, ETF is more likely mis-priced.
    We trade the ETF leg first, then the equity legs to hedge.
    """
    if state.mid_ETF is None or state.mid_A is None or state.mid_C is None:
        return

    b_val = state.mid_B if state.mid_B is not None else 0
    nav   = state.mid_A + b_val + state.mid_C
    etf_p = state.mid_ETF
    edge  = etf_p - nav

    if abs(edge) - ETF_SWAP_FEE < ETF_ARB_THRESHOLD:
        return  # not enough edge after fees

    if edge > 0:
        # ETF overpriced vs NAV → sell ETF, buy components
        # But hint: ETF is likely the mis-priced one, so just sell ETF for now
        _place_limit_order(client, 'ETF', 'sell', etf_p - 0.01, ORDER_SIZE_ETF)
        # Hedge: buy A and C (skip B for now unless we have a good price)
        _place_limit_order(client, 'A', 'buy', state.mid_A + 0.01, ORDER_SIZE_ETF)
        _place_limit_order(client, 'C', 'buy', state.mid_C + 0.01, ORDER_SIZE_ETF)
    else:
        # ETF underpriced vs NAV → buy ETF, sell components
        _place_limit_order(client, 'ETF', 'buy',  etf_p + 0.01, ORDER_SIZE_ETF)
        _place_limit_order(client, 'A', 'sell', state.mid_A - 0.01, ORDER_SIZE_ETF)
        _place_limit_order(client, 'C', 'sell', state.mid_C - 0.01, ORDER_SIZE_ETF)


# ─── OPTIONS: PUT-CALL PARITY ARBITRAGE ──────────────────────────────────────

def _options_pcp_arb(client):
    """
    Put-Call Parity: C - P = S0 - K * e^(-rT)

    For each strike, check if the market violates PCP.
    If C - P > S - K*e^(-rT): sell call, buy put, buy stock (synthetic)
    If C - P < S - K*e^(-rT): buy call, sell put, sell stock

    We use mid_B as S0. If mid_B is unknown, skip.
    """
    if state.mid_B is None:
        return

    S0 = state.mid_B

    for strike, opt in state.options.items():
        K = strike
        T = opt.get('expiry_T', 1.0)  # time to expiry in years

        call_mid = (opt.get('call_bid', 0) + opt.get('call_ask', 0)) / 2
        put_mid  = (opt.get('put_bid',  0) + opt.get('put_ask',  0)) / 2

        pcp_rhs = S0 - K * math.exp(-RISK_FREE_RATE * T)
        diff    = call_mid - put_mid - pcp_rhs

        if diff > PCP_ARB_THRESHOLD:
            # Call overpriced relative to put: sell call, buy put
            _place_limit_order(client, f'CALL_{K}', 'sell', opt['call_bid'], ORDER_SIZE_OPT)
            _place_limit_order(client, f'PUT_{K}',  'buy',  opt['put_ask'],  ORDER_SIZE_OPT)

        elif diff < -PCP_ARB_THRESHOLD:
            # Put overpriced relative to call: buy call, sell put
            _place_limit_order(client, f'CALL_{K}', 'buy',  opt['call_ask'], ORDER_SIZE_OPT)
            _place_limit_order(client, f'PUT_{K}',  'sell', opt['put_bid'],  ORDER_SIZE_OPT)


# ─── ORDER PLACEMENT STUB ────────────────────────────────────────────────────

def _place_limit_order(client, symbol: str, side: str, price: float, size: int):
    """
    Send a limit order to the exchange.
    Replace the body with the actual exchange client API call, e.g.:
        client.place_order(symbol=symbol, side=side, price=price, quantity=size, order_type='limit')
    """
    if size <= 0 or price <= 0:
        return
    # Suppress unused-variable warning until wired up; remove line below when real call is added.
    _ = client
    # TODO: replace print with real exchange call
    print(f"[ORDER] {side.upper()} {size}x {symbol} @ {price:.4f}")


def _cancel_all_orders(client, symbol: str):
    """Cancel all open orders for a symbol. Call before re-quoting."""
    # TODO: replace with real exchange call
    # client.cancel_all_orders(symbol=symbol)
    _ = client, symbol  # suppress unused warnings until wired up


# ─── MAIN LOOP (STANDALONE / TESTING) ────────────────────────────────────────

def main():
    """
    Entry point. In the actual competition, the exchange SDK will call
    on_tick() and on_position_update() for you. This main() is for
    local testing with a mock client.
    """
    # TODO: initialize exchange client
    # from exchange_sdk import Client
    # client = Client(team_id='YOUR_TEAM_ID', api_key='YOUR_API_KEY')
    client = None  # placeholder

    print("Bot started. Waiting for tick data...")

    # Example: manually feed a fake tick for testing
    fake_tick = {
        'order_books': {
            'A':   {'bids': [[99.50, 10]], 'asks': [[100.50, 10]]},
            'C':   {'bids': [[49.00, 10]], 'asks': [[51.00, 10]]},
            'ETF': {'bids': [[199.00, 5]], 'asks': [[202.00, 5]]},
            'B':   {'bids': [[100.00, 5]], 'asks': [[101.00, 5]]},
        },
        'options': {
            100: {'call_bid': 5.0, 'call_ask': 5.5, 'put_bid': 4.8, 'put_ask': 5.2, 'expiry_T': 0.1},
            105: {'call_bid': 2.0, 'call_ask': 2.5, 'put_bid': 7.0, 'put_ask': 7.5, 'expiry_T': 0.1},
            95:  {'call_bid': 8.0, 'call_ask': 8.5, 'put_bid': 2.5, 'put_ask': 3.0, 'expiry_T': 0.1},
        },
        'news': [
            {'type': 'earnings_A', 'eps': 6.5},
            {'type': 'earnings_C', 'eps': 3.2},
            {'type': 'fed_probs',  'hike': 0.4, 'hold': 0.4, 'cut': 0.2},
        ],
    }

    on_tick(client, fake_tick)

    print(f"\nFair A   = {state.fair_A}")
    print(f"Fair C   = {state.fair_C}")
    print(f"Fair ETF = {state.fair_ETF}")
    print(f"Yield    = {state.yield_y:.4f}")
    print(f"PE_C     = {state.pe_C:.4f}")
    print(f"Fed probs: hike={state.q_hike:.2f} hold={state.q_hold:.2f} cut={state.q_cut:.2f}")


if __name__ == '__main__':
    main()
