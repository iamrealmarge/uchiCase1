# CASE 1 IMPLEMENTATION PLAN — The Optimal Path to Winning
**Team ucla_calberkeley | 3 Days to Competition**

---

## WHERE WE ARE RIGHT NOW

### Our Setup
- **Team:** 4 members (Yifan, Emily, Gary, Margaret)
- **Current code:** `strat1.py` — a 530-line prototype with correct formulas but NO exchange wiring
- **Platform:** X-Change (gRPC-based, Python client library `utcxchangelib`)
- **Practice exchange:** LIVE at http://34.197.188.76:3001/ (running 24/7 until competition)
- **Our score:** 151,514 (default — we haven't been actively trading)
- **Top score:** 98,057 (texas_carnegiemellon_stanford_purdue)
- **Competition:** Saturday April 11, 9:15am CDT, live on EC2 instances

### What strat1.py Has (Good Foundation)
✅ Correct A fair value formula (EPS × PE)
✅ Correct C model skeleton (PE with yield sensitivity + bond portfolio)
✅ Fed probability → yield → C price chain
✅ ETF NAV calculation and arb logic
✅ Put-call parity arb on B options
✅ Basic inventory skew
✅ Clean modular structure

### What strat1.py Is Missing (Must Fix)
❌ **Not connected to X-Change** — `_place_limit_order` just prints
❌ **Wrong parameters** — uses placeholder values, not the confirmed ones from Ed
❌ **No order cancellation** — stacks infinite orders
❌ **No order tracking** — can't manage open orders against risk limits
❌ **Single-level quoting** — winners use 4 levels
❌ **Static spreads** — doesn't adapt to market conditions
❌ **Linear inventory skew** — should be logarithmic fade
❌ **No async** — exchange requires async Python (gRPC streaming)
❌ **No box spread arb** — missing free money across 3 strikes
❌ **No implied-B pricing** — should derive B from options
❌ **Hardcoded earnings timing** — Ed confirmed timing is now RANDOM
❌ **No risk limit tracking** — will get orders silently rejected
❌ **No safety mechanisms** — no stop-loss, no circuit breaker

---

## THE PLAN: 4 PHASES OVER 3 DAYS

### Timeline
```
Wed Apr 8 (today):  Phase 1 — Wire to exchange, get TRADING
Thu Apr 9:          Phase 2 — Core strategies (MM + arbs working)
Fri Apr 10:         Phase 3 — Optimization (multi-level, adaptive, tuning)
Sat Apr 11 morning: Phase 4 — Competition day (deploy, monitor, tune live)
```

### Priority Ranking (if time runs short, do in this order)
```
P0 (MUST HAVE — bot won't function without these):
  1. Connect to X-Change via utcxchangelib
  2. Parse market updates (books, news, fills)
  3. Place and cancel orders
  4. Track positions and open orders vs risk limits
  5. Update confirmed parameters (from Ed post #40)

P1 (MUST HAVE — competitive minimum):
  6. Stock A market making (fair = EPS × PE)
  7. Stock C market making (full yield + bond model)
  8. ETF arbitrage (with $5 fee threshold)
  9. Put-call parity arb on B options
  10. Fed prediction market quoting
  11. Inventory fade (logarithmic)
  12. Cancel-before-requote cycle

P2 (SHOULD HAVE — competitive edge):
  13. Multi-level quoting (4 levels)
  14. Adaptive edge (tanh formula)
  15. Box spread arb (3 boxes)
  16. Implied-B pricing from options
  17. Bayesian CPI → Fed probability updating
  18. Headline sentiment parsing
  19. Real-time volatility estimation

P3 (NICE TO HAVE — top-tier):
  20. VPIN toxicity detection
  21. Smart/dumb bot detection
  22. Live parameter config file reload
  23. Meta market handler (flexible unknown instrument)
  24. Gamma scalping on B options
  25. Noise injection on order sizes
```

---

## PHASE 1: WIRE TO EXCHANGE (Wednesday Evening)

**Goal:** Bot connects, receives data, places an order, gets a fill.

### Step 1.1 — Install and Understand utcxchangelib

```bash
# On your machine (and later on EC2)
pip install utcxchangelib
# If already installed, UNINSTALL and REINSTALL (per Ed post #46)
pip uninstall utcxchangelib
pip install utcxchangelib
```

The library uses **gRPC streaming** — it's async Python. You'll need to understand:
- How to connect (team credentials from email)
- How market updates arrive (streaming callback)
- How to place/cancel orders
- How fill confirmations come back

### Step 1.2 — Skeleton Async Bot

```python
import asyncio
import math
from utcxchangelib import XChangeClient  # adjust import to actual library

class Bot:
    def __init__(self):
        self.positions = {}       # symbol → int
        self.open_orders = {}     # order_id → {symbol, side, price, qty}
        self.fair = {}            # symbol → float
        self.mids = {}            # symbol → float
        self.eps_A = None
        self.eps_C = None
        self.q_hike = 1/3
        self.q_hold = 1/3
        self.q_cut = 1/3
        
    async def run(self):
        client = XChangeClient("YOUR_USERNAME", "YOUR_PASSWORD")
        # Register callbacks
        client.on_market_update = self.on_market_update
        client.on_fill = self.on_fill
        client.on_news = self.on_news
        await client.connect()
        # Keep running
        await asyncio.Event().wait()
    
    async def on_market_update(self, update):
        # Parse order books → update mids
        # Recompute fair values
        # Cancel stale orders
        # Place new quotes
        pass
    
    async def on_fill(self, fill):
        # Update positions
        pass
    
    async def on_news(self, news):
        # Parse earnings, CPI, fedspeak
        pass

if __name__ == "__main__":
    bot = Bot()
    asyncio.run(bot.run())
```

**⚠️ CRITICAL:** Look at the example bot from Ed post #2 and the client library source code. The actual API methods, callback signatures, and message formats are defined there. Our skeleton must match EXACTLY.

### Step 1.3 — Risk Limit Tracker

```python
class RiskTracker:
    MAX_ORDER_SIZE = 40
    MAX_OPEN_ORDERS = 50
    MAX_OUTSTANDING_VOL = 120
    MAX_ABS_POSITION = 200
    
    def __init__(self):
        self.open_orders = {}  # order_id → (symbol, qty)
        self.positions = {}    # symbol → qty
    
    def outstanding_volume(self, symbol):
        return sum(qty for oid, (sym, qty) in self.open_orders.items() if sym == symbol)
    
    def can_place(self, symbol, qty):
        if qty > self.MAX_ORDER_SIZE:
            return False
        if len(self.open_orders) >= self.MAX_OPEN_ORDERS - 2:  # buffer
            return False
        if self.outstanding_volume(symbol) + qty > self.MAX_OUTSTANDING_VOL - 5:
            return False
        if abs(self.positions.get(symbol, 0)) + qty > self.MAX_ABS_POSITION - 5:
            return False
        return True
```

### Step 1.4 — Validate Connection

Run the bot. Confirm you see:
- [ ] Market update messages flowing
- [ ] Order books for all 13 instruments
- [ ] News events (EARNINGS, CPI, FEDSPEAK)
- [ ] Prediction market prices (R_CUT, R_HOLD, R_HIKE)
- [ ] Can place a limit order and see it acknowledged
- [ ] Can cancel an order
- [ ] Fill messages when your orders execute

**Test:** Place a single buy order on Stock A at a low price. Place a sell order at a high price. Confirm fills. This proves the full pipeline works.

---

## PHASE 2: CORE STRATEGIES (Thursday)

**Goal:** All P0+P1 strategies operational. Bot is making money on practice exchange.

### Step 2.1 — Fair Value Models (with CONFIRMED parameters)

```python
# ═══ CONFIRMED PARAMETERS (from Ed post #40) ═══
Y0 = 0.045          # baseline yield
PE0_C = 14.0         # baseline P/E for C
EPS0_C = 2.00        # baseline EPS for C (reference)
DURATION = 7.5       # bond duration
B0_OVER_N = 40.0     # bond portfolio / shares outstanding
CONVEXITY = 55.0     # bond convexity
LAMBDA = 0.65        # bond portfolio weight

# ═══ MUST CALIBRATE FROM DATA ═══
GAMMA_C = 2.0        # P/E sensitivity to yield — START HERE, TUNE
BETA_Y = 0.001       # yield sensitivity to rate expectations — START HERE, TUNE
PE_A = 15.0          # Stock A P/E ratio — observe from first earnings

# ═══ OPTIONS ═══
RISK_FREE_RATE = 0.045  # use y0 as proxy
STRIKES = [950, 1000, 1050]

def compute_fair_A(eps_A, pe_A):
    if eps_A is None: return None
    return eps_A * pe_A

def compute_fair_C(eps_C, q_hike, q_hold, q_cut):
    if eps_C is None: return None
    
    # Yield from Fed expectations
    e_dr = 25 * q_hike + 0 * q_hold + (-25) * q_cut  # basis points
    y = Y0 + BETA_Y * e_dr
    dy = y - Y0
    
    # P/E with yield sensitivity
    pe_c = PE0_C * math.exp(-GAMMA_C * dy)
    
    # Bond portfolio effect (Taylor expansion)
    d_bond = B0_OVER_N * (-DURATION * dy + 0.5 * CONVEXITY * dy**2)
    
    return eps_C * pe_c + LAMBDA * d_bond

def compute_fair_B(options_data, r, T):
    """Implied B price from put-call parity across all strikes"""
    implied = []
    for K in STRIKES:
        opt = options_data.get(K)
        if opt is None: continue
        call_mid = (opt['call_bid'] + opt['call_ask']) / 2
        put_mid = (opt['put_bid'] + opt['put_ask']) / 2
        if call_mid > 0 and put_mid > 0:
            S_implied = call_mid - put_mid + K * math.exp(-r * T)
            implied.append(S_implied)
    return sum(implied) / len(implied) if implied else None

def compute_fair_ETF(fair_A, fair_B, fair_C):
    if any(v is None for v in [fair_A, fair_B, fair_C]): return None
    return fair_A + fair_B + fair_C
```

### Step 2.2 — Market Making with Cancel-Before-Requote

```python
async def quote_instrument(client, symbol, fair, position, params):
    """Core MM logic — cancel old, post new"""
    if fair is None:
        return
    
    # 1. Cancel all existing orders for this symbol
    await cancel_all_for_symbol(client, symbol)
    
    # 2. Compute fade (logarithmic)
    fade = 0
    if position != 0:
        fade = -params.fade_f * math.copysign(1, position) * math.log2(1 + abs(position))
    
    adjusted_fair = fair + fade
    
    # 3. Compute spread
    spread = params.base_spread  # start simple, upgrade to adaptive later
    
    # 4. Post bid and ask (if within risk limits)
    bid_price = round(adjusted_fair - spread, 2)
    ask_price = round(adjusted_fair + spread, 2)
    
    if risk_tracker.can_place(symbol, params.size):
        if position < risk_tracker.MAX_ABS_POSITION - 10:
            await client.place_limit_order(symbol, 'buy', bid_price, params.size)
        if position > -(risk_tracker.MAX_ABS_POSITION - 10):
            await client.place_limit_order(symbol, 'sell', ask_price, params.size)
```

### Step 2.3 — ETF Arbitrage

```python
ETF_SWAP_FEE = 5.0  # $5 flat
ETF_ARB_THRESHOLD = 1.0  # minimum edge after fees

async def check_etf_arb(client, fair_etf, etf_mid, positions):
    if fair_etf is None or etf_mid is None:
        return
    
    edge = etf_mid - fair_etf
    
    if abs(edge) < ETF_SWAP_FEE + ETF_ARB_THRESHOLD:
        return  # not enough edge
    
    size = min(5, 40)  # conservative
    
    if edge > 0:
        # ETF overpriced → sell ETF
        # Case packet hint: ETF is more likely mispriced
        await client.place_limit_order('ETF', 'sell', etf_mid - 0.01, size)
    else:
        # ETF underpriced → buy ETF
        await client.place_limit_order('ETF', 'buy', etf_mid + 0.01, size)
```

### Step 2.4 — Put-Call Parity Arb

```python
async def check_pcp_arb(client, options_data, fair_B, r, T):
    if fair_B is None: return
    
    for K in STRIKES:
        opt = options_data.get(K)
        if opt is None: continue
        
        call_symbol = f'B_C_{K}'
        put_symbol = f'B_P_{K}'
        
        pcp_rhs = fair_B - K * math.exp(-r * T)
        
        # Check if calls overpriced (sell call, buy put)
        if opt['call_bid'] > 0 and opt['put_ask'] > 0:
            diff = (opt['call_bid'] - opt['put_ask']) - pcp_rhs
            if diff > 0.50:  # threshold
                size = min(5, 40)
                await client.place_limit_order(call_symbol, 'sell', opt['call_bid'], size)
                await client.place_limit_order(put_symbol, 'buy', opt['put_ask'], size)
        
        # Check if puts overpriced (buy call, sell put)
        if opt['call_ask'] > 0 and opt['put_bid'] > 0:
            diff = (opt['call_ask'] - opt['put_bid']) - pcp_rhs
            if diff < -0.50:
                size = min(5, 40)
                await client.place_limit_order(call_symbol, 'buy', opt['call_ask'], size)
                await client.place_limit_order(put_symbol, 'sell', opt['put_bid'], size)
```

### Step 2.5 — News Parser (Dynamic Timing)

```python
def on_news(self, news_event):
    """Parse ALL news — DO NOT assume timing."""
    body = news_event.body
    event_type = news_event.type  # or however the API labels it
    
    if 'earnings released' in body:
        eps = float(body.split(': ')[1])
        # Determine if this is A or C from context
        # (need to figure out from API — may have asset field)
        # For now: if only one unknown, infer
        self.handle_earnings(eps, event_type)
    
    elif 'actual' in body and 'forecast' in body:
        # CPI: "actual 0.0027 vs forecast 0.0021"
        parts = body.split()
        actual = float(parts[1])
        forecast = float(parts[4])
        self.handle_cpi(actual, forecast)
    
    elif event_type == 'FEDSPEAK':
        self.handle_headline(body)

def handle_cpi(self, actual, forecast):
    surprise = actual - forecast
    # Bayesian-ish update
    # Actual > Forecast → inflation hot → shift toward hike
    shift_magnitude = min(abs(surprise) * 200, 0.25)  # cap at 25% shift
    
    if surprise > 0:
        transfer = min(shift_magnitude, self.q_cut * 0.5)
        self.q_cut -= transfer
        self.q_hike += transfer
    else:
        transfer = min(shift_magnitude, self.q_hike * 0.5)
        self.q_hike -= transfer
        self.q_cut += transfer
    
    # Renormalize
    total = self.q_hike + self.q_hold + self.q_cut
    self.q_hike /= total
    self.q_hold /= total
    self.q_cut /= total
```

---

## PHASE 3: OPTIMIZATION (Friday)

**Goal:** Multi-level quoting, adaptive edge, box spreads, parameter calibration.

### Step 3.1 — Multi-Level Quoting

```python
LEVELS = [
    {'spread_mult': 1.0, 'size_mult': 1.0},    # L1: tight, full size
    {'spread_mult': 1.5, 'size_mult': 0.7},     # L2: medium
    {'spread_mult': 2.5, 'size_mult': 0.5},     # L3: wide
    {'spread_mult': 4.0, 'size_mult': 0.3},     # L4: deep, small
]

async def quote_multilevel(client, symbol, fair, position, params):
    if fair is None: return
    await cancel_all_for_symbol(client, symbol)
    
    fade = -params.fade_f * math.copysign(1, position) * math.log2(1 + abs(position)) if position != 0 else 0
    adjusted_fair = fair + fade
    
    for level in LEVELS:
        spread = params.base_spread * level['spread_mult']
        size = max(1, int(params.base_size * level['size_mult']))
        
        bid = round(adjusted_fair - spread, 2)
        ask = round(adjusted_fair + spread, 2)
        
        if risk_tracker.can_place(symbol, size):
            if position < 190:
                await client.place_limit_order(symbol, 'buy', bid, size)
            if position > -190:
                await client.place_limit_order(symbol, 'sell', ask, size)
```

### Step 3.2 — Adaptive Edge

```python
class ActivityTracker:
    def __init__(self, window=100):
        self.trades = []  # (timestamp, volume)
        self.window = window
    
    def add_trade(self, volume):
        self.trades.append(volume)
        if len(self.trades) > self.window:
            self.trades.pop(0)
    
    def activity_level(self):
        """0 to 1 normalized activity"""
        if not self.trades: return 0.5
        return min(sum(self.trades) / (self.window * 20), 1.0)

def compute_edge(activity, params):
    """Tanh-based adaptive edge"""
    return params.min_edge + (params.slack / 2) * math.tanh(
        -4 * params.edge_sensitivity * activity + 2
    )
```

### Step 3.3 — Box Spread Arb

```python
async def check_box_spreads(client, options_data, r, T):
    """Check all 3 possible box spreads"""
    strike_pairs = [(950, 1000), (950, 1050), (1000, 1050)]
    
    for K1, K2 in strike_pairs:
        opt1 = options_data.get(K1)
        opt2 = options_data.get(K2)
        if opt1 is None or opt2 is None: continue
        
        fair_box = (K2 - K1) * math.exp(-r * T)
        
        # Cost to BUY the box
        buy_cost = ((opt1.get('call_ask',0) - opt2.get('call_bid',0)) +
                    (opt2.get('put_ask',0) - opt1.get('put_bid',0)))
        
        # Cost to SELL the box
        sell_revenue = ((opt1.get('call_bid',0) - opt2.get('call_ask',0)) +
                        (opt2.get('put_bid',0) - opt1.get('put_ask',0)))
        
        if buy_cost > 0 and buy_cost < fair_box - 0.50:
            # Box is cheap → buy it
            size = 2
            await client.place_limit_order(f'B_C_{K1}', 'buy', opt1['call_ask'], size)
            await client.place_limit_order(f'B_C_{K2}', 'sell', opt2['call_bid'], size)
            await client.place_limit_order(f'B_P_{K2}', 'buy', opt2['put_ask'], size)
            await client.place_limit_order(f'B_P_{K1}', 'sell', opt1['put_bid'], size)
        
        if sell_revenue > fair_box + 0.50:
            # Box is expensive → sell it
            size = 2
            await client.place_limit_order(f'B_C_{K1}', 'sell', opt1['call_bid'], size)
            await client.place_limit_order(f'B_C_{K2}', 'buy', opt2['call_ask'], size)
            await client.place_limit_order(f'B_P_{K2}', 'sell', opt2['put_bid'], size)
            await client.place_limit_order(f'B_P_{K1}', 'buy', opt1['put_ask'], size)
```

### Step 3.4 — Calibrate γ and β_y from Practice Data

```python
class ParameterCalibrator:
    """Collect data points from practice to estimate unknown parameters."""
    
    def __init__(self):
        self.observations = []  # (dy, pe_ratio_observed)
    
    def observe(self, eps_C, price_C, q_hike, q_hold, q_cut):
        """Call after each C earnings + price observation."""
        if eps_C is None or price_C is None: return
        if eps_C == 0: return
        
        # Observed P/E
        pe_observed = price_C / eps_C  # rough, ignoring bond component
        
        # Expected rate change
        e_dr = 25 * q_hike - 25 * q_cut
        
        self.observations.append({
            'e_dr': e_dr,
            'pe_observed': pe_observed,
        })
    
    def estimate_gamma(self):
        """Fit γ from observations: PE = PE0 * exp(-γ * β_y * E[Δr])"""
        if len(self.observations) < 3: return None
        
        # Simple: try different γ×β_y products, find best fit
        best_error = float('inf')
        best_gamma_beta = 0
        
        for gb in [x * 0.0001 for x in range(1, 100)]:
            error = 0
            for obs in self.observations:
                pe_pred = PE0_C * math.exp(-gb * obs['e_dr'])
                error += (pe_pred - obs['pe_observed'])**2
            if error < best_error:
                best_error = error
                best_gamma_beta = gb
        
        return best_gamma_beta  # this is γ × β_y combined
```

---

## PHASE 4: COMPETITION DAY (Saturday April 11)

### 8:00am — Arrive at Willis Tower
- [ ] Set up laptops
- [ ] SSH into EC2 instance (VSCode + SSH)
- [ ] Clone/upload bot code
- [ ] Install utcxchangelib (fresh install)
- [ ] Verify connection to competition exchange

### 8:45am — Welcome & Agenda

### 9:00am — Tech Case Prep
- [ ] **Learn Meta Market rules** → build quick handler if simple enough
- [ ] **Check if risk limits changed** → update constants
- [ ] **Note any parameter reveals** → update model
- [ ] **Verify bot connects to COMPETITION exchange** (different from practice!)

### 9:15am — LIVE TRADING BEGINS

**Role Assignment:**
```
Person 1 (primary coder): At keyboard, ready to hotfix bugs
Person 2 (monitor): Watch leaderboard + positions + P&L
Person 3 (parameter tuner): Adjust edge/fade/spread between rounds
Person 4 (strategist): Watch market events, call out arb opportunities
```

**Between-Round Tuning Checklist:**
```
After each round, quickly assess:
□ What was our P&L? What rank?
□ Are we getting fills? (If not → tighten spreads)
□ Are positions drifting? (If yes → increase fade)
□ Are arbs firing? (If not → lower thresholds)
□ Are we hitting risk limits? (If yes → reduce order sizes)
□ Any new patterns in news? (Adjust CPI sensitivity)
```

**Round-by-Round Strategy Shift:**
```
Rounds 1-3 (early, weighted less):
  → Wide spreads, big sizes, harvest easy money
  → All arb strategies active
  → Conservative position limits (±100)
  → Goal: positive P&L, learn the dynamics

Rounds 4-6 (mid, moderate weight):
  → Tighten spreads to compete
  → Aggressive arb hunting
  → Position limit ±150
  → Goal: top-half ranking

Rounds 7+ (late, HIGHEST weight):
  → Very tight spreads
  → Arb-dominant (MM edges shrinking)
  → Maximum discipline on inventory
  → Goal: every point counts, be consistent
```

### 12:15pm — Trading Ends

---

## TASK DELEGATION (4 TEAM MEMBERS)

### Yifan — Lead Architect & C/Fed Model
- Wire bot to utcxchangelib (Phase 1)
- Implement Stock C fair value model (with confirmed params)
- Fed probability updating (CPI + headline parsing)
- Calibrate γ and β_y from practice data
- Competition day: primary coder

### Emily — Stock A & ETF Systems
- Stock A market making (simplest, get working first)
- ETF NAV calculation and arb logic
- ETF swap decision logic ($5 fee threshold)
- Competition day: monitor positions + P&L

### Gary — Options & Arb Engine
- Put-call parity arb across 3 strikes
- Box spread arb (3 combinations)
- Implied-B pricing from options
- Competition day: parameter tuner

### Margaret — Infrastructure & Risk
- Risk limit tracker (max orders, position limits)
- Order management (cancel-before-requote, tracking)
- Multi-level quoting system
- Adaptive edge + log fade implementation
- Competition day: strategist / market watcher

---

## CRITICAL GOTCHAS (Things That Will Break Your Bot)

1. **Concurrent gRPC writes crash the client** → Reinstall utcxchangelib (patched version serializes writes)

2. **Earnings timing is RANDOM** → Do NOT hardcode tick numbers. Parse news events dynamically.

3. **A can get >2 earnings per day** → Your model must handle frequent updates

4. **Risk limit violations are SILENT** → Orders just get rejected with no error. Track limits yourself.

5. **Position >200 bug exists** → Known issue, may or may not be fixed by competition day. Build your own tracking.

6. **Score is RANK-based, lower = better** → Don't chase max P&L. Chase consistency across rounds.

7. **Late rounds are weighted more** → Save your best play for rounds 7+

8. **Exchange ticks every 200ms** → Your bot must process and respond within 200ms or fall behind

9. **Async Python is mandatory** → Blocking calls will disconnect you from gRPC stream

10. **Unicode edge case in news** → Some headlines have U+2019 apostrophes. Handle encoding properly.

---

## MINIMUM VIABLE BOT (If Everything Goes Wrong)

If you're running out of time, here's the absolute minimum to be competitive:

```
1. Connect to exchange ✓
2. Parse earnings for A → post bid/ask around EPS×PE ✓
3. Cancel old orders every tick ✓
4. Track positions, don't exceed 200 ✓
5. Wide spreads (capture easy money) ✓
```

This alone should beat teams that don't trade at all (currently ~20 teams at default score).

---

## SUCCESS METRICS

```
BARE MINIMUM: Score < 145,000 (beat default teams)
COMPETITIVE:  Score < 130,000 (top half)
STRONG:       Score < 115,000 (top 10)
WINNING:      Score < 100,000 (top 3)
```

---

*Let's build this. Time to go from prototype to competition-ready bot.*
