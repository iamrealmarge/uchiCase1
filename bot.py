"""
Case 1 Bot — UChicago Trading Competition 2026
================================================
Team: ucla_calberkeley

Subclasses utcxchangelib.XChangeClient.
Implements: market making on APT/MKJ, ETF arb via swaps,
put-call parity arb on DLR options, news-driven fair value,
logarithmic inventory fade, cancel-before-requote.

Symbols:
  APT  = Stock A (small-cap, constant PE, earnings-driven)
  DLR  = Stock B (semiconductor, traded via options)
  MKJ  = Stock C (insurance, yield + bond portfolio model)
  AKAV = ETF (= APT + DLR + MKJ, swap fee $5 flat)
  AKIM = additional instrument (handle generically)

Usage:
  python bot.py [host] [username] [password]
"""

import asyncio
import math
import sys
import logging
from collections import defaultdict
from utcxchangelib.xchange_client import XChangeClient, Side, OrderBook

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("case1-bot")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIRMED PARAMETERS (Ed post #40)
# ═══════════════════════════════════════════════════════════════════════════════

# Stock A: fair_A = EPS_A * PE_A  (PE_A is constant)
A_PE = 15.0  # constant P/E for APT — update if Ed confirms differently

# Stock C model:
#   PE_C = PE0 * exp(-gamma * (y - y0))
#   dB   = (B0/N) * (-D * dy + 0.5 * C_conv * dy^2)
#   fair_C = EPS_C * PE_C + lambda * dB
C_PE0    = 14.0    # baseline P/E for MKJ
C_GAMMA  = 2.0     # P/E sensitivity to yield (UNKNOWN — calibrate on practice)
C_B0_N   = 40.0    # B0/N combined constant
C_D      = 7.5     # duration
C_CONV   = 55.0    # convexity
C_LAMBDA = 0.65    # bond portfolio weight

# Yield model
Y0       = 0.045   # baseline yield (4.5%)
BETA_Y   = 0.001   # yield sensitivity to E[dr] in bps

# Risk-free rate (for put-call parity)
RISK_FREE = 0.05

# ═══════════════════════════════════════════════════════════════════════════════
# TRADING PARAMETERS (tune these!)
# ═══════════════════════════════════════════════════════════════════════════════

# Market making
MM_LEVELS       = 3        # number of quote levels per side
MM_LEVEL_STEP   = 2        # price increment between levels (in exchange ticks)
MM_BASE_EDGE    = 3        # minimum half-spread from fair value (ticks)
MM_SIZE         = 5        # order size per level
MM_FADE_FACTOR  = 0.4      # logarithmic inventory fade strength

# ETF arbitrage
ETF_SWAP_FEE    = 5        # flat fee per swap (in exchange price units)
ETF_ARB_EDGE    = 2        # min edge beyond swap fee to trigger arb

# Options / PCP arbitrage
PCP_ARB_EDGE    = 3        # min parity violation to trigger (ticks)
OPT_SIZE        = 2        # option order size

# Risk limits (from exchange rules)
MAX_ORDER_SIZE       = 40
MAX_OPEN_ORDERS      = 50
MAX_OUTSTANDING_VOL  = 120   # per symbol
MAX_ABS_POSITION     = 200   # per symbol

# Position limits (self-imposed, conservative)
SOFT_POS_LIMIT_STOCK = 100
SOFT_POS_LIMIT_ETF   = 50
SOFT_POS_LIMIT_OPT   = 30

# Symbols we actively market-make
MM_SYMBOLS = ["APT", "MKJ", "AKAV"]


# ═══════════════════════════════════════════════════════════════════════════════
# BOT CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class Case1Bot(XChangeClient):

    def __init__(self, host: str, username: str, password: str):
        super().__init__(host, username, password)

        # ── Fair values ──
        self.fair = {}          # symbol → float fair value
        self.eps = {}           # asset → latest EPS  (keyed by news asset name)

        # ── Fed / yield state ──
        self.q_hike = 1/3
        self.q_hold = 1/3
        self.q_cut  = 1/3
        self.yield_y = Y0
        self.pe_c    = C_PE0

        # ── Petition (Fed proxy) state ──
        self.petition_cumulative = {}  # asset → cumulative signatures

        # ── Options state ──
        # We'll discover option symbols dynamically from order books
        self.option_symbols = set()    # e.g. {"DLR50C", "DLR50P", ...}
        self.option_strikes = {}       # symbol → strike price
        self.option_types   = {}       # symbol → 'C' or 'P'

        # ── Tracking ──
        self.pending_cancels = set()   # order IDs we've requested cancel for
        self.requote_needed  = set()   # symbols that need requoting

        # ── Round / timing ──
        self.tick_count = 0
        self.started = False

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS: Order book reading
    # ─────────────────────────────────────────────────────────────────────────

    def best_bid(self, symbol: str):
        """Return (price, qty) of best bid, or (None, 0)."""
        book = self.order_books.get(symbol)
        if book and book.bids:
            px = max(book.bids.keys())
            return px, book.bids[px]
        return None, 0

    def best_ask(self, symbol: str):
        """Return (price, qty) of best ask, or (None, 0)."""
        book = self.order_books.get(symbol)
        if book and book.asks:
            px = min(book.asks.keys())
            return px, book.asks[px]
        return None, 0

    def mid_price(self, symbol: str):
        """Return mid price as float, or None."""
        bb, _ = self.best_bid(symbol)
        ba, _ = self.best_ask(symbol)
        if bb is not None and ba is not None:
            return (bb + ba) / 2.0
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS: Risk checks
    # ─────────────────────────────────────────────────────────────────────────

    def count_open_orders(self):
        return len(self.open_orders)

    def outstanding_volume(self, symbol: str):
        """Sum of unfilled qty for open orders on this symbol."""
        vol = 0
        for oid, info in self.open_orders.items():
            if info[0].symbol == symbol:
                vol += info[1]  # remaining qty
        return vol

    def can_place(self, symbol: str, qty: int) -> bool:
        """Check exchange risk limits before placing an order."""
        if qty > MAX_ORDER_SIZE:
            return False
        if self.count_open_orders() >= MAX_OPEN_ORDERS - 2:
            return False
        if self.outstanding_volume(symbol) + qty > MAX_OUTSTANDING_VOL - 5:
            return False
        return True

    def position_room(self, symbol: str, side: str) -> int:
        """How many more shares can we buy/sell before hitting position limit."""
        pos = self.positions.get(symbol, 0)
        if side == "buy":
            return max(0, MAX_ABS_POSITION - 5 - pos)
        else:
            return max(0, MAX_ABS_POSITION - 5 + pos)

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS: Safe order placement
    # ─────────────────────────────────────────────────────────────────────────

    async def safe_place(self, symbol: str, qty: int, side: str, px: int):
        """Place a limit order with risk checks. Returns order_id or None."""
        if qty <= 0 or px <= 0:
            return None
        if not self.can_place(symbol, qty):
            return None
        # Clamp qty to position room
        room = self.position_room(symbol, side)
        qty = min(qty, room)
        if qty <= 0:
            return None
        try:
            oid = await self.place_order(symbol, qty, side, px)
            return oid
        except Exception as e:
            log.warning(f"Order failed {side} {qty}x {symbol}@{px}: {e}")
            return None

    async def cancel_all_symbol(self, symbol: str):
        """Cancel all our open orders for a given symbol."""
        to_cancel = []
        for oid, info in list(self.open_orders.items()):
            if info[0].symbol == symbol and oid not in self.pending_cancels:
                to_cancel.append(oid)
        for oid in to_cancel:
            self.pending_cancels.add(oid)
            try:
                await self.cancel_order(oid)
            except Exception as e:
                log.warning(f"Cancel failed for {oid}: {e}")
                self.pending_cancels.discard(oid)

    # ─────────────────────────────────────────────────────────────────────────
    # FAIR VALUE MODELS
    # ─────────────────────────────────────────────────────────────────────────

    def compute_fair_A(self):
        """fair_A = EPS_A * PE_A (constant PE)."""
        eps_a = self.eps.get("APT")
        if eps_a is not None:
            self.fair["APT"] = eps_a * A_PE

    def compute_yield(self):
        """
        E[dr] = 25 * q_hike - 25 * q_cut  (in bps)
        y = y0 + beta_y * E[dr]
        PE_C = PE0 * exp(-gamma * (y - y0))
        """
        e_dr = 25.0 * self.q_hike - 25.0 * self.q_cut
        self.yield_y = Y0 + BETA_Y * e_dr
        dy = self.yield_y - Y0
        self.pe_c = C_PE0 * math.exp(-C_GAMMA * dy)

    def compute_fair_C(self):
        """
        dB = (B0/N) * (-D * dy + 0.5 * C_conv * dy^2)
        fair_C = EPS_C * PE_C + lambda * dB
        """
        eps_c = self.eps.get("MKJ")
        if eps_c is None:
            return
        dy = self.yield_y - Y0
        d_bond = C_B0_N * (-C_D * dy + 0.5 * C_CONV * dy ** 2)
        self.fair["MKJ"] = eps_c * self.pe_c + C_LAMBDA * d_bond

    def compute_fair_ETF(self):
        """ETF NAV = APT + DLR + MKJ (one share each)."""
        a = self.fair.get("APT") or self.mid_price("APT")
        b = self.mid_price("DLR")  # no model for B, use market mid
        c = self.fair.get("MKJ") or self.mid_price("MKJ")
        if a is not None and b is not None and c is not None:
            self.fair["AKAV"] = a + b + c

    def compute_implied_B(self):
        """
        From put-call parity: S = C - P + K * e^(-rT)
        Use option mid prices to get implied B price.
        If we have multiple strikes, average them.
        """
        # TODO: implement once we discover option symbol format
        pass

    def recompute_all_fairs(self):
        """Recompute all fair values from current state."""
        self.compute_fair_A()
        self.compute_yield()
        self.compute_fair_C()
        self.compute_implied_B()
        self.compute_fair_ETF()

    # ─────────────────────────────────────────────────────────────────────────
    # MARKET MAKING
    # ─────────────────────────────────────────────────────────────────────────

    def inventory_fade(self, symbol: str) -> float:
        """
        Logarithmic inventory fade: pushes quotes away from inventory direction.
        fade = -f * sign(pos) * log2(1 + |pos|)
        Positive fade = shift quotes UP (encourage selling to us).
        Negative fade = shift quotes DOWN (encourage buying from us).
        """
        pos = self.positions.get(symbol, 0)
        if pos == 0:
            return 0.0
        sign = 1 if pos > 0 else -1
        return -MM_FADE_FACTOR * sign * math.log2(1 + abs(pos))

    async def requote_mm(self, symbol: str):
        """
        Cancel-before-requote cycle for market making.
        1. Cancel all existing orders on symbol
        2. Compute quotes with inventory fade
        3. Place multi-level two-sided quotes
        """
        fair = self.fair.get(symbol)
        if fair is None:
            # No fair value yet — don't quote blind
            return

        # Cancel existing orders first
        await self.cancel_all_symbol(symbol)

        # Compute fade
        fade = self.inventory_fade(symbol)
        pos = self.positions.get(symbol, 0)

        # Determine soft position limit for this symbol
        if symbol == "AKAV":
            soft_limit = SOFT_POS_LIMIT_ETF
        else:
            soft_limit = SOFT_POS_LIMIT_STOCK

        for level in range(MM_LEVELS):
            offset = MM_BASE_EDGE + level * MM_LEVEL_STEP
            # Size decreases at wider levels
            size = max(1, MM_SIZE - level)

            # Bid (buy) side
            bid_px = int(round(fair - offset + fade))
            if pos < soft_limit and bid_px > 0:
                await self.safe_place(symbol, size, "buy", bid_px)

            # Ask (sell) side
            ask_px = int(round(fair + offset + fade))
            if pos > -soft_limit and ask_px > 0:
                await self.safe_place(symbol, size, "sell", ask_px)

    # ─────────────────────────────────────────────────────────────────────────
    # ETF ARBITRAGE (via swaps)
    # ─────────────────────────────────────────────────────────────────────────

    async def check_etf_arb(self):
        """
        Compare ETF market price vs NAV.
        If ETF overpriced: sell ETF + buy components (or redeem via swap).
        If ETF underpriced: buy ETF + sell components (or create via swap).

        Swap is cleaner — no leg risk:
          toAKAV:   give APT+DLR+MKJ → get AKAV,  cost 5
          fromAKAV: give AKAV → get APT+DLR+MKJ,   cost 5
        """
        nav = self.fair.get("AKAV")
        etf_mid = self.mid_price("AKAV")
        if nav is None or etf_mid is None:
            return

        edge = etf_mid - nav  # positive = ETF overpriced

        threshold = ETF_SWAP_FEE + ETF_ARB_EDGE

        if edge > threshold:
            # ETF overpriced: sell ETF at market, then redeem (fromAKAV)
            bb, _ = self.best_bid("AKAV")
            if bb is not None and bb - nav > ETF_SWAP_FEE:
                qty = min(5, self.position_room("AKAV", "sell"))
                if qty > 0:
                    await self.safe_place("AKAV", qty, "sell", bb)
                    # Also try swap if we hold AKAV
                    akav_pos = self.positions.get("AKAV", 0)
                    if akav_pos > 0:
                        swap_qty = min(akav_pos, 3)
                        try:
                            await self.place_swap_order("fromAKAV", swap_qty)
                        except Exception as e:
                            log.warning(f"Swap fromAKAV failed: {e}")

        elif edge < -threshold:
            # ETF underpriced: buy ETF, then create (toAKAV) if we hold components
            ba, _ = self.best_ask("AKAV")
            if ba is not None and nav - ba > ETF_SWAP_FEE:
                qty = min(5, self.position_room("AKAV", "buy"))
                if qty > 0:
                    await self.safe_place("AKAV", qty, "buy", ba)
                    # Try create swap if we hold all components
                    apt_pos = self.positions.get("APT", 0)
                    dlr_pos = self.positions.get("DLR", 0)
                    mkj_pos = self.positions.get("MKJ", 0)
                    can_swap = min(apt_pos, dlr_pos, mkj_pos)
                    if can_swap > 0:
                        swap_qty = min(can_swap, 3)
                        try:
                            await self.place_swap_order("toAKAV", swap_qty)
                        except Exception as e:
                            log.warning(f"Swap toAKAV failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # PUT-CALL PARITY ARBITRAGE
    # ─────────────────────────────────────────────────────────────────────────

    async def check_pcp_arb(self):
        """
        For each strike K with both call and put books:
          PCP: C - P = S - K * e^(-rT)
        If violated beyond threshold, arb it.

        We discover option symbols by checking all order books for
        symbols containing 'C' or 'P' after the base (DLR).
        """
        # Get DLR mid as underlying price
        s_mid = self.mid_price("DLR")
        if s_mid is None:
            return

        # Group options by strike
        # Expected symbol format: unknown until we see actual data
        # Common patterns: "DLR50C", "DLR 50C", etc.
        # For now, try to detect from order_books keys
        strikes = {}  # strike → {'call_sym': ..., 'put_sym': ..., 'strike': int}

        for sym in self.order_books:
            if sym in ("APT", "DLR", "MKJ", "AKAV", "AKIM"):
                continue
            # Try to parse option symbol
            sym_upper = sym.upper()
            if 'C' in sym_upper or 'P' in sym_upper:
                self.option_symbols.add(sym)
                # Try to extract strike and type
                # Heuristic: last char is C or P, digits before it are strike
                try:
                    if sym_upper.endswith('C'):
                        opt_type = 'C'
                        strike_str = ''.join(c for c in sym_upper[:-1] if c.isdigit())
                    elif sym_upper.endswith('P'):
                        opt_type = 'P'
                        strike_str = ''.join(c for c in sym_upper[:-1] if c.isdigit())
                    else:
                        continue
                    strike = int(strike_str)
                    self.option_strikes[sym] = strike
                    self.option_types[sym] = opt_type

                    if strike not in strikes:
                        strikes[strike] = {}
                    if opt_type == 'C':
                        strikes[strike]['call_sym'] = sym
                    else:
                        strikes[strike]['put_sym'] = sym
                except (ValueError, IndexError):
                    continue

        # Check parity for each strike that has both call and put
        for strike, info in strikes.items():
            if 'call_sym' not in info or 'put_sym' not in info:
                continue

            call_mid = self.mid_price(info['call_sym'])
            put_mid = self.mid_price(info['put_sym'])
            if call_mid is None or put_mid is None:
                continue

            # PCP: C - P should equal S - K*e^(-rT)
            # Using T ≈ small fraction (within a round, time decays fast)
            # For simplicity, use T=0.01 (options expire end of round)
            T = 0.01
            pcp_rhs = s_mid - strike * math.exp(-RISK_FREE * T)
            diff = (call_mid - put_mid) - pcp_rhs

            if abs(diff) < PCP_ARB_EDGE:
                continue

            if diff > PCP_ARB_EDGE:
                # Call overpriced vs put: sell call, buy put
                call_bb, _ = self.best_bid(info['call_sym'])
                put_ba, _ = self.best_ask(info['put_sym'])
                if call_bb and put_ba:
                    await self.safe_place(info['call_sym'], OPT_SIZE, "sell", call_bb)
                    await self.safe_place(info['put_sym'], OPT_SIZE, "buy", put_ba)

            elif diff < -PCP_ARB_EDGE:
                # Put overpriced vs call: buy call, sell put
                call_ba, _ = self.best_ask(info['call_sym'])
                put_bb, _ = self.best_bid(info['put_sym'])
                if call_ba and put_bb:
                    await self.safe_place(info['call_sym'], OPT_SIZE, "buy", call_ba)
                    await self.safe_place(info['put_sym'], OPT_SIZE, "sell", put_bb)

    # ─────────────────────────────────────────────────────────────────────────
    # NEWS HANDLING
    # ─────────────────────────────────────────────────────────────────────────

    def handle_earnings(self, asset: str, value: float):
        """Process earnings announcement."""
        self.eps[asset] = value
        log.info(f"EARNINGS: {asset} EPS = {value}")

        # Recompute fairs immediately
        self.recompute_all_fairs()

        # Flag for aggressive requote
        if asset == "APT":
            self.requote_needed.add("APT")
            self.requote_needed.add("AKAV")
        elif asset == "MKJ":
            self.requote_needed.add("MKJ")
            self.requote_needed.add("AKAV")

    def handle_petition(self, asset: str, new_sigs: int, cumulative: int):
        """
        Process petition event.
        Petition likely maps to Fed prediction market or similar.
        More signatures → more support for rate action.
        """
        self.petition_cumulative[asset] = cumulative
        log.info(f"PETITION: {asset} +{new_sigs} sigs (total: {cumulative})")

        # TODO: map petition cumulative to Fed probabilities
        # For now, treat large cumulative as hawkish signal
        # This needs calibration from practice data

    def handle_unstructured_news(self, content: str):
        """
        Parse unstructured news for Fed-relevant keywords.
        Shift Fed probabilities based on sentiment.
        """
        text = content.lower()
        log.info(f"NEWS: {content[:80]}")

        hawk_words = ['inflation', 'hike', 'hawkish', 'overheat', 'hot',
                       'tighten', 'restrictive', 'surge']
        dove_words = ['recession', 'cut', 'dovish', 'slowdown', 'weak',
                       'cool', 'ease', 'loosen', 'unemployment']

        hawk = sum(1 for w in hawk_words if w in text)
        dove = sum(1 for w in dove_words if w in text)
        net = hawk - dove

        if net != 0:
            # Each keyword hit shifts ~5% probability
            shift = min(abs(net) * 0.05, 0.25)
            if net > 0:
                transfer = min(shift, self.q_cut)
                self.q_cut -= transfer
                self.q_hike += transfer
            else:
                transfer = min(shift, self.q_hike)
                self.q_hike -= transfer
                self.q_cut += transfer

            # Normalize
            total = self.q_hike + self.q_hold + self.q_cut
            if total > 0:
                self.q_hike /= total
                self.q_hold /= total
                self.q_cut /= total

            self.recompute_all_fairs()
            self.requote_needed.add("MKJ")
            self.requote_needed.add("AKAV")

    # ─────────────────────────────────────────────────────────────────────────
    # XChangeClient CALLBACK OVERRIDES
    # ─────────────────────────────────────────────────────────────────────────

    async def bot_handle_book_update(self, symbol: str) -> None:
        """Called on every book snapshot and incremental update."""
        self.tick_count += 1

        # Recompute fairs (cheap — do it every update)
        self.recompute_all_fairs()

        # Requote the symbol that changed (and any flagged symbols)
        symbols_to_requote = {symbol} | self.requote_needed
        self.requote_needed.clear()

        for sym in symbols_to_requote:
            if sym in MM_SYMBOLS:
                await self.requote_mm(sym)

        # Check arb opportunities periodically (not every single tick)
        if self.tick_count % 3 == 0:
            await self.check_etf_arb()
        if self.tick_count % 5 == 0:
            await self.check_pcp_arb()

    async def bot_handle_trade_msg(self, symbol: str, price: int, qty: int):
        """Called when any trade occurs on the exchange (not just ours)."""
        # Could use for volatility estimation or trade flow analysis
        pass

    async def bot_handle_order_fill(self, order_id: str, qty: int, price: int):
        """Called when one of OUR orders gets filled."""
        # Position already updated by parent class
        # Log it for monitoring
        info = self.open_orders.get(order_id)
        if info:
            sym = info[0].symbol
            side = "BUY" if info[0].side == 1 else "SELL"
            log.info(f"FILL: {side} {qty}x {sym} @ {price}  |  pos={self.positions[sym]}")

    async def bot_handle_order_rejected(self, order_id: str, reason: str) -> None:
        """Called when our order is rejected."""
        log.warning(f"REJECTED order {order_id}: {reason}")

    async def bot_handle_cancel_response(self, order_id: str, success: bool, error) -> None:
        """Called when cancel request completes."""
        self.pending_cancels.discard(order_id)
        if not success:
            log.warning(f"Cancel failed for {order_id}: {error}")

    async def bot_handle_swap_response(self, swap: str, qty: int, success: bool):
        """Called when swap completes."""
        if success:
            log.info(f"SWAP OK: {swap} x{qty}")
        else:
            log.warning(f"SWAP FAILED: {swap} x{qty}")

    async def bot_handle_news(self, news_release: dict):
        """
        Called when news arrives.
        NOTE: library has a signature bug — it passes one dict arg,
        not (timestamp, news_release). We accept just the dict.

        news_release format:
          {
            'timestamp': int,
            'kind': 'structured' | 'unstructured',
            'new_data': {
              # earnings: {'value': float, 'asset': str, 'structured_subtype': 'earnings'}
              # petition: {'new_signatures': int, 'cumulative': int, 'asset': str, 'structured_subtype': 'petition'}
              # unstructured: {'content': str}
            }
          }
        """
        data = news_release.get('new_data', {})
        kind = news_release.get('kind', '')

        if kind == 'structured':
            subtype = data.get('structured_subtype', '')
            if subtype == 'earnings':
                self.handle_earnings(data['asset'], data['value'])
            elif subtype == 'petition':
                self.handle_petition(
                    data['asset'],
                    data['new_signatures'],
                    data['cumulative']
                )
        elif kind == 'unstructured':
            content = data.get('content', '')
            if content:
                self.handle_unstructured_news(content)

        # After any news, requote everything
        for sym in MM_SYMBOLS:
            self.requote_needed.add(sym)

    # ─────────────────────────────────────────────────────────────────────────
    # STARTUP
    # ─────────────────────────────────────────────────────────────────────────

    async def start(self):
        """Main entry point — connect and run forever."""
        log.info(f"Starting Case1Bot on {self.host} as {self.username}")
        log.info(f"Parameters: PE0_C={C_PE0}, D={C_D}, C={C_CONV}, "
                 f"lambda={C_LAMBDA}, y0={Y0}, B0/N={C_B0_N}")

        # Optionally launch the phoenixhood web UI for manual monitoring
        # self.launch_user_interface()

        await self.connect()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 4:
        print("Usage: python bot.py <host:port> <username> <password>")
        print("Example: python bot.py 34.197.188.76:50052 ucla_calberkeley yourpassword")
        sys.exit(1)

    host = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    bot = Case1Bot(host, username, password)
    asyncio.run(bot.start())


if __name__ == "__main__":
    main()
