# UTC 2026 — Advanced Market Making & Arbitrage Strategy Deep Dive

**Team ucla_calberkeley | Compiled April 8, 2026 | Competition April 11**

---

## PART 1: CRITICAL ED DISCUSSION INTEL (LIVE FROM FORUM)

### CONFIRMED PARAMETERS (from Staff post #40 — Khush Jammu)
```
y₀ = 0.045        (baseline yield = 4.5%)
PE₀ = 14.0        (baseline P/E for C)
EPS₀ = 2.00       (baseline EPS for C)
D = 7.5            (duration constant)
B₀/N = 40          (bond portfolio value / shares outstanding)
C = 55.0           (convexity constant)
λ = 0.65           (bond portfolio weighting constant)
```

**⚠️ NOT PROVIDED (must calibrate ourselves):**
- γ (P/E sensitivity to yield changes) — constant across rounds
- β_y (yield sensitivity to expected rate change) — constant across rounds

### KEY RULE CHANGES FROM ED
| Finding | Source | Impact |
|---------|--------|--------|
| **EPS releases are NO LONGER at fixed ticks** | #40, #44 | Cannot hardcode tick 22/88 for earnings. Must parse news dynamically |
| **A can get MORE than 2 EPS per day** | #44 (Leon Luo) | More frequent fair value updates, more trading opportunities |
| **No compounding/annualizing needed for A** | #44 | fair_A = EPS × PE directly |
| **News for A won't always be on same tick** | #34 | Price paths are randomized |
| **Score = RANK within round (lower = better)** | #39 (Viresh) | Not raw P&L! Relative performance matters |
| **Later rounds will NOT be previewed** | #60 | Must build adaptive strategy blind |
| **One bot recommended, not multiple** | #28 | Multiple bots cause throttling and risk mgmt issues |
| **Async Python is critical** | #28 | gRPC disconnections from improper async code |
| **utcxchangelib must be reinstalled** | #46 | Bug fix: serialized write requests for concurrent gRPC |
| **Exchange ticks every 200ms** | #52 | As long as latency < 200ms, you keep up |
| **Competition runs on EC2 instances (same VPC)** | #52, #26 | Much lower latency than practice |
| **Stock A news may/may not affect future earnings** | #41 | "No comment!" — test empirically |
| **Risk limits will be announced; may change day-of** | #45, case packet | Must handle rejection gracefully |
| **Position >200 bug exists** | #58 | Known bug, being fixed |

### X-CHANGE PLATFORM DETAILS (from browser scraping)
```
TRADEABLE INSTRUMENTS (13 total):
  Equities:    A, B, C
  ETF:         ETF
  Calls:       B_C_950, B_C_1000, B_C_1050
  Puts:        B_P_950, B_P_1000, B_P_1050
  Prediction:  R_CUT, R_HOLD, R_HIKE

RISK LIMITS (per instrument):
  Max Order Size:        40
  Max Open Orders:       50
  Outstanding Volume:    120
  Max Absolute Position: 200

ETF SWAP FEE: $5 flat (both directions)
  TO ETF:   1A + 1B + 1C → 1 ETF (cost $5)
  FROM ETF: 1 ETF → 1A + 1B + 1C (cost $5)

OPTION STRIKES: 950, 1000, 1050 (on Stock B)

NEWS TYPES OBSERVED:
  - EARNINGS: "earnings released: X.X" (for A and C)
  - CPI: "actual X.XXXX vs forecast X.XXXX"
  - FEDSPEAK: unstructured headlines about Fed policy

LEADERBOARD: ~40 teams competing
  Top teams scoring <100k (rank-based, lower = better)
  Your team (ucla_calberkeley): 151,514 (needs improvement)
```

### CURRENT LEADERBOARD (top 10)
```
1. texas_carnegiemellon_stanford_purdue  98,057
2. chicago4                              98,961
3. chicago10                             99,876
4. uiuc                                 102,662
5. usc                                  110,546
6. chicago7                             114,298
7. texas1                               119,077
8. emory_chicago_cornell                122,101
9. chicago12                            128,219
10. chicago_harvard                      129,047
...
   ucla_calberkeley                     151,514 (tied with many at default)
```

---

## PART 2: REAL-WORLD MM STRATEGIES FROM TOP FIRMS

### The Avellaneda-Stoikov Framework (Foundation of Professional MM)

**Reservation Price** — the price at which a market maker is indifferent:
```
r(s, q, t) = s - q × γ × σ² × (T - t)
```
- s = mid-price
- q = current inventory
- γ = risk aversion (higher = more conservative)
- σ = volatility
- (T-t) = time remaining

**If you're long (q > 0)**, reservation price drops below mid → you want to sell.
**If you're short (q < 0)**, reservation price rises above mid → you want to buy.

**Optimal Half-Spread:**
```
δ* = γ × σ² × (T - t) + (2/γ) × ln(1 + γ/κ)
      ↑ inventory risk       ↑ adverse selection
```
- κ = order arrival intensity (higher κ = more trades = tighter spread)

**For our competition:**
- Each round = 10 days × 90 seconds × 5 ticks = 4,500 ticks
- T-t decreases within each round
- σ can be estimated from recent price moves (rolling window of ~50-100 ticks)
- γ should be HIGH given nonlinear scoring (penalizes variance)
- κ estimated from observed fill rates

### How Top Firms Apply This

**Citadel Securities** — $652B daily volume, 35-40% of US retail. Real-time ML recalibrating parameters millisecond-by-millisecond.

**Jane Street** — World's leading ETF liquidity provider. $4T annual ETF volume. Their edge: when ETF trades at premium, they simultaneously sell ETF and buy underlying basket, then deliver basket to issuer as Authorized Participant. The arbitrage is locked in the instant both legs execute.

**Virtu Financial** — 25% of daily US equity transactions. Edge comes from detecting and pricing adverse selection more accurately. Adjust spreads up to 300-400 bps for high-PIN stocks during news.

**SIG (Susquehanna)** — Options MM specialists. Apply game theory (Nash equilibria) to options pricing. Equilibrium spread widens when more informed traders enter.

**Flow Traders** — ETF specialists across 13,000+ listings. Modular architecture for microsecond-accurate timing. Layer orders across multiple depth levels.

### Key Firm Strategies Applicable to UTC

**1. Multi-Level Depth (Flow Traders style)**
```
L1 (top of book): Tight spread, small size → capture flow
L2 (2-3 ticks out): Medium spread, medium size → bread and butter
L3 (5-10 ticks out): Wide spread, medium size → adverse selection premium
L4 (deep): Very wide, large size → inventory management / volatility capture
```

**2. Adverse Selection Detection (Virtu/Kyle model)**
```
λ = ΔPrice / ΔOrderFlow  (price impact per unit flow)

If λ is high → informed traders active → WIDEN spreads
If λ is low → noise traders → TIGHTEN spreads for volume

Practical: track signed volume over last 10-20 ticks.
If buy_volume >> sell_volume → someone knows price is going up → raise ask, don't buy.
```

**3. VPIN — Volume-Synchronized Probability of Informed Trading**
```
Divide trading into volume buckets.
For each bucket: compute |buy_volume - sell_volume| / total_volume
Average over N buckets = VPIN

VPIN < 0.3 → safe, tight spreads
VPIN 0.3-0.5 → moderate, standard spreads
VPIN > 0.5 → toxic flow, widen aggressively
```

**4. Jane Street ETF Arb Loop (adapted for UTC)**
```
1. Monitor: NAV = fair_A + fair_B + fair_C
2. Monitor: ETF_price from order book
3. If ETF_price > NAV + $5 (swap fee) + threshold:
   → Sell ETF at market, buy A+B+C, swap TO ETF to flatten
4. If ETF_price < NAV - $5 - threshold:
   → Buy ETF, swap FROM ETF, sell A+B+C
5. Key: the $5 flat fee means you need >$5 of mispricing to profit
```

---

## PART 3: ADVANCED ARBITRAGE STRATEGIES

### Put-Call Parity Arb (3 strikes × every tick)

For each strike K ∈ {950, 1000, 1050}:
```
PCP: C - P = S - K × e^(-rT)

Check using WORST execution prices:
  violation = (call_bid - put_ask) - (S_bid - K × e^(-rT))
  
  If violation > threshold:
    SELL call at call_bid, BUY put at put_ask → lock in profit
  
  violation = (call_ask - put_bid) - (S_ask - K × e^(-rT))
  
  If violation < -threshold:
    BUY call at call_ask, SELL put at put_bid → lock in profit
```

### Box Spread Arb (3 possible boxes)

With strikes 950, 1000, 1050, we have 3 boxes:
```
Box(950, 1000): payoff always = 50
Box(950, 1050): payoff always = 100
Box(1000, 1050): payoff always = 50

Fair box value = (K₂ - K₁) × e^(-rT)

To BUY a box (K₁, K₂):
  Buy Call K₁ + Sell Call K₂ + Buy Put K₂ + Sell Put K₁
  Cost = (C₁_ask - C₂_bid) + (P₂_ask - P₁_bid)

If Cost < Fair Value → BUY box → risk-free profit
If Cost > Fair Value → SELL box → risk-free profit
```

### Implied B Price from Options (better than raw mid)
```
For each strike K:
  implied_B = C_mid - P_mid + K × e^(-rT)

fair_B = average(implied_B across all 3 strikes)
```
This uses PCP in reverse. More robust than raw order book mid for B.

### Conversion/Reversal Arb
```
Conversion: Long stock + Long put + Short call (same K, T)
  Profit = (C_bid - P_ask) - (S_ask - K × e^(-rT))

Reversal: Short stock + Long call + Short put
  Profit = (S_bid - K × e^(-rT)) - (C_ask - P_bid)
```
These are the actual trades that enforce PCP. Execute when violation > transaction cost.

### Volatility Arb / Gamma Scalping
```
If implied vol > realized vol:
  Sell options (collect overpriced premium)
  Delta-hedge with stock B
  Profit from theta decay exceeding gamma losses

If implied vol < realized vol:
  Buy options (cheap)
  Delta-hedge
  Profit from gamma gains exceeding theta cost
```

### Cross-Asset Triangular Arb
```
ETF = A + B + C
If fair_A + fair_B + fair_C ≠ ETF_price:
  Trade the mispriced leg
  
But also: if A moves and ETF doesn't:
  Buy/sell ETF to capture the lag
  (ETF is more likely mispriced per case packet hint)
```

---

## PART 4: OPTIMAL MM THEORY FOR COMPETITION SCORING

### The Scoring Function Changes Everything

**Scoring = rank-based (lower score = better)**

This means:
- You don't need the HIGHEST P&L
- You need to be CONSISTENTLY better than others
- Variance is your enemy (nonlinear P&L → points conversion)
- One terrible round doesn't ruin you, but one great round doesn't save you

### Optimal γ (Risk Aversion) Given Scoring

Since scoring penalizes variance, we want to MAXIMIZE:
```
U = E[PnL] - λ_score × Var[PnL]
```
This maps directly to the Avellaneda-Stoikov γ parameter:
- **Higher γ** = wider spreads = lower expected PnL but lower variance
- **Lower γ** = tighter spreads = higher expected PnL but higher variance

**Recommendation for UTC:** Start with γ ≈ 5-10 (moderately conservative). Adjust based on observed round-by-round performance.

### Adaptive Edge Formula (from 2024 top placer)
```python
edge = min_margin + (slack/2) * tanh(-4 * edge_sensitivity * activity_level + 2)
```
- **min_margin**: floor profit per trade (e.g., $0.02)
- **slack**: range of edge adjustment (e.g., $0.10)
- **edge_sensitivity**: how fast edge adapts (e.g., 0.5)
- **activity_level**: normalized recent trade volume (0 to 1)

When activity is HIGH → edge shrinks → capture more volume
When activity is LOW → edge widens → maximize per-trade profit

### Position Fade Formula (from 2024 top placer)
```python
fade = -f * sign(position) * log2(1 + abs(position))
```
- **f**: fade strength (e.g., 0.05-0.20)
- Logarithmic: heavily punishes medium positions, gentle on small ones

### Volatility Estimation (Real-Time)
```python
# Rolling window of last N log-returns
returns = [log(p[i] / p[i-1]) for i in range(-N, 0)]
sigma = std(returns)
# Annualize if needed: sigma_annual = sigma * sqrt(252 * ticks_per_day)
```
Use N = 50-100 ticks. Update every tick.

---

## PART 5: THE WINNING BOT ARCHITECTURE

### Event-Driven Async Architecture
```python
import asyncio
from utcxchangelib import XChangeClient

class TradingBot:
    def __init__(self):
        self.fair = {}          # symbol → fair value
        self.positions = {}     # symbol → qty
        self.orders = {}        # order_id → (symbol, side, price, qty)
        self.params = Params()  # live-reloadable config
    
    async def on_market_update(self, update):
        # 1. Parse books → update mids
        # 2. Parse news → update models
        # 3. Recompute fair values
        # 4. Cancel stale orders
        # 5. Place new quotes (multi-level)
        # 6. Check arb opportunities
        pass
    
    async def on_fill(self, fill):
        # Update positions
        # Check if arb leg completed
        # Adjust quotes based on new inventory
        pass
```

### Order Management (Critical)
```python
class OrderTracker:
    def __init__(self):
        self.by_id = {}        # order_id → OrderInfo
        self.by_symbol = {}    # symbol → {order_id, ...}
        self.open_count = 0    # track against 50 limit
        self.outstanding_vol = 0  # track against 120 limit
    
    def can_place(self, symbol, qty):
        """Check risk limits before placing"""
        if qty > 40: return False  # max order size
        if self.open_count >= 48: return False  # leave buffer
        if self.outstanding_vol + qty > 115: return False  # leave buffer
        if abs(self.positions[symbol]) + qty > 195: return False
        return True
    
    async def cancel_and_replace(self, client, symbol, new_orders):
        """Cancel all orders for symbol, then place new ones"""
        for oid in self.by_symbol.get(symbol, []):
            await client.cancel_order(oid)
        for order in new_orders:
            if self.can_place(symbol, order.qty):
                await client.place_order(order)
```

### Multi-Level Quote Generator
```python
def generate_quotes(fair, position, sigma, params):
    """Generate 4-level two-sided quotes"""
    # Reservation price (A-S model)
    reservation = fair - position * params.gamma * sigma**2 * params.tau
    
    # Adaptive edge
    activity = get_recent_activity()
    edge = params.min_edge + (params.slack/2) * math.tanh(
        -4 * params.edge_sens * activity + 2)
    
    # Fade
    fade = -params.fade_f * math.copysign(1, position) * math.log2(1 + abs(position))
    
    adjusted_fair = reservation + fade
    
    quotes = []
    for level in range(4):
        spread = edge * (1 + level * 0.5)  # L1=edge, L2=1.5x, L3=2x, L4=2.5x
        size = params.base_size // (1 + level)  # decreasing size at depth
        
        bid = round(adjusted_fair - spread, 2)
        ask = round(adjusted_fair + spread, 2)
        
        # Don't quote side that would exceed position limit
        if position < params.max_pos:
            quotes.append(('buy', bid, size))
        if position > -params.max_pos:
            quotes.append(('sell', ask, size))
    
    return quotes
```

### News Parser (Updated for Variable Timing)
```python
def parse_news(news_msg):
    """Parse all news types. DO NOT hardcode timing."""
    if news_msg.type == 'EARNINGS':
        # Could be for A or C, multiple per day, any tick
        eps_value = float(news_msg.body.split(': ')[1])
        # Determine which stock (need context from message)
        update_eps(eps_value)
    
    elif news_msg.type == 'CPI':
        # "actual X.XXXX vs forecast X.XXXX"
        parts = news_msg.body.split()
        actual = float(parts[1])
        forecast = float(parts[4])
        surprise = actual - forecast
        bayesian_update_fed_probs(surprise)
    
    elif news_msg.type == 'FEDSPEAK':
        # Unstructured headline
        sentiment = analyze_headline(news_msg.body)
        adjust_fed_probs(sentiment)
```

---

## PART 6: PARAMETER CALIBRATION FOR γ AND β_y

These are the TWO unknown parameters we must estimate ourselves.

### Calibrating γ (P/E sensitivity to yields)
```
PE_C = PE₀ × e^(-γ × (y - y₀))

Given: PE₀ = 14.0, y₀ = 0.045
Method: Observe C's price behavior around CPI releases.

1. Before CPI: note PE_C (from C_price / EPS_C)
2. After CPI: note new PE_C
3. Calculate Δy from Fed probability shift
4. Solve: γ = -ln(PE_new / PE_old) / Δy

Do this across multiple CPI events. Average for robust estimate.
```

### Calibrating β_y (yield sensitivity to rate expectations)
```
y = y₀ + β_y × E[Δr]

Method: Observe yield changes from Fed probability shifts.

1. Track prediction market prices (R_HIKE, R_HOLD, R_CUT)
2. Compute E[Δr] = 25 × q_hike + 0 × q_hold - 25 × q_cut
3. Infer yield from C's price movements
4. Regress y against E[Δr] to estimate β_y

Alternative: β_y likely in range [0.0005, 0.005].
Start with 0.001 and adjust based on observed C price sensitivity.
```

### Fair Value Formulas with Confirmed Parameters
```python
# Stock A
fair_A = eps_A * PE_A  # PE_A is constant (unknown, estimate from data)

# Stock C (with confirmed parameters)
y0 = 0.045
PE0 = 14.0
D = 7.5
B0_N = 40.0  # B₀/N
C_conv = 55.0
lam = 0.65

def fair_C(eps_C, q_hike, q_hold, q_cut, gamma_est, beta_y_est):
    e_dr = 25 * q_hike + 0 * q_hold + (-25) * q_cut
    y = y0 + beta_y_est * e_dr
    dy = y - y0
    
    pe_c = PE0 * math.exp(-gamma_est * dy)
    d_bond = B0_N * (-D * dy + 0.5 * C_conv * dy**2)
    
    return eps_C * pe_c + lam * d_bond

# Stock B (implied from options)
def fair_B(options, r, T):
    implied_prices = []
    for K, opt in options.items():
        call_mid = (opt['call_bid'] + opt['call_ask']) / 2
        put_mid = (opt['put_bid'] + opt['put_ask']) / 2
        implied_S = call_mid - put_mid + K * math.exp(-r * T)
        implied_prices.append(implied_S)
    return sum(implied_prices) / len(implied_prices)

# ETF
fair_ETF = fair_A + fair_B + fair_C
```

---

## PART 7: COMPETITION DAY GAME PLAN

### Pre-Competition (9:00-9:15 CDT)
- SSH into EC2 instance via VSCode
- Verify utcxchangelib is latest version
- Start bot, verify connection
- Note risk limits if they changed
- Learn Meta Market rules

### Round-by-Round Strategy
```
EARLY ROUNDS (1-3): "Harvest Mode"
  - Wide spreads (capture dumb money)
  - All strategies active (MM + arb)
  - Conservative position limits
  - Focus: consistent positive P&L

MID ROUNDS (4-6): "Compete Mode"
  - Tighten spreads (match competition)
  - Aggressive arb (ETF, PCP, box spreads)
  - Dynamic edge adjustment
  - Focus: beat the median team

LATE ROUNDS (7+): "Alpha Mode"
  - Very tight spreads (fight for every fill)
  - Information edge (news parsing, yield model accuracy)
  - Arb-dominant (edges shrink in MM)
  - Focus: every point matters (weighted heavily)
```

### Live Parameter Tuning Checklist
```
Every round, check and adjust:
□ Edge (wider if getting picked off, tighter if few fills)
□ Fade rate (increase if positions drifting too large)
□ Order sizes (reduce if hitting risk limits)
□ Arb thresholds (lower if no arbs triggering)
□ γ and β_y estimates (refine from observed prices)
□ Spread per instrument (some need wider than others)
```

---

## SOURCES

**Ed Discussion Posts:**
- [#40 Case Updates (parameters)](https://edstem.org/us/courses/96484/discussion/7903564)
- [#39 Leaderboard (scoring)](https://edstem.org/us/courses/96484/discussion/7903424)
- [#44 Earnings timing](https://edstem.org/us/courses/96484/discussion/7907080)
- [#43 γ and β_y not provided](https://edstem.org/us/courses/96484/discussion/7906468)
- [#34 Changes coming](https://edstem.org/us/courses/96484/discussion/7901653)
- [#46 utcxchangelib bug fix](https://edstem.org/us/courses/96484/discussion/7907413)
- [#52 Network latency](https://edstem.org/us/courses/96484/discussion/7910027)
- [#28 One bot recommended](https://edstem.org/us/courses/96484/discussion/7894415)

**Past Competition Winners:**
- [Tianyi Liu — Winner Blog](https://tianyi.io/post/chicago1/)
- [Trung Dang — 2024 Writeup](https://dmtrung.com/blogs/uchicagotc_writeups.html)
- [Baumohl — 2024 Experience](https://baumohl.dev/blog/chicago-competition/)
- [John Trager — 2nd Place 2022](https://github.com/John-Trager/UChicago-Trading-Competition)
- [Zaranip — 2024](https://github.com/zaranip/Chicago-Trading-Competition-2024)

**Academic/Industry:**
- [Avellaneda-Stoikov Model](https://people.orie.cornell.edu/sfs33/LimitOrderBook.pdf)
- [Guéant-Lehalle-Fernandez-Tapia](https://arxiv.org/abs/1105.3115)
- [Jane Street ETF Arbitrage](https://theprincipledportfolio.substack.com/p/the-house-of-brain-teasers-a-deep)
- [SIG Game Theory](https://www.risk.net/investing/quant-investing/7955140/role-of-the-dice-how-susquehanna-puts-game-theory-to-work)
- [Optiver Market Making](https://optiver.com/working-at-optiver/career-hub/engineering-the-three-pillars-of-trading-pricing-risk-and-execution/)

---

*Competition in 3 days. Time to build the winning bot.*
