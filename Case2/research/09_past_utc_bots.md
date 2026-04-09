# Past UChicago Trading Competition (UTC) Bots — Competitive Intelligence

*Compiled: April 2026. Sources: GitHub public repos, blog writeups, competition websites.*

---

## Table of Contents

1. [Repository Index](#1-repository-index)
2. [Exchange Infrastructure (xchange / utcxchangelib)](#2-exchange-infrastructure)
3. [Case 1: Market Making — Strategies Across Years](#3-case-1-market-making)
4. [Case 2: Options / Portfolio Optimization — Strategies Across Years](#4-case-2)
5. [ETF Arbitrage Implementations](#5-etf-arbitrage)
6. [Fair Value Calculation Methods](#6-fair-value-calculation-methods)
7. [Market Making Spread / Edge / Fade Logic](#7-market-making-spread-edge-fade-logic)
8. [Options Pricing Approaches](#8-options-pricing-approaches)
9. [Portfolio Optimization Strategies](#9-portfolio-optimization-strategies)
10. [Key Lessons and Failure Modes](#10-key-lessons-and-failure-modes)
11. [Summary: What Actually Wins](#11-summary-what-actually-wins)

---

## 1. Repository Index

| Year | Team | Repo | Notes |
|------|------|------|-------|
| 2015 | UIUC Team 1 | https://github.com/thibautx/UChicago-Trading-Competition-2015 | Thibaut Xiong et al. |
| 2015 | — | https://github.com/hanzhiw/2015UChicagoTradingCompetition | Full 2015 materials |
| 2019 | — | https://github.com/stormsurfer98/uchicago-trading | MWTC 2019 template |
| 2019 | — | https://github.com/hj364/pairs-trading | Pairs trading + options MM; 8th overall |
| 2021 | Amherst College | https://github.com/ACquantclub/UChicago-Trading-Competition-2021 | FX futures MM; interest rate parity fair value |
| 2021 | — | https://github.com/awrd2019/UChicago-Trading-Competition-Case-3 | Genetic algorithm portfolio allocation |
| 2022 | U Michigan (2nd overall) | https://github.com/John-Trager/UChicago-Trading-Competition | Case1 lumber MM + Case2 options MM + Case3 BL portfolio |
| 2022 | U Michigan (same) | https://github.com/gurish165/UChicago-Trading-Competition | Mirror / same team repo |
| 2022 | — | https://github.com/Icyviolet23/UChicagoTrading | Minimal content |
| 2022 | — | https://github.com/PMenes/Chicago-Trading-Comp | Multi-strategy market maker w/ JS GUI |
| 2024 | UChicago + UMass | https://github.com/zaranip/Chicago-Trading-Competition-2024 | Best documented; PAMR for Case 2 |
| 2024 | UChicago + UMass (mirror) | https://github.com/coolkite/Chicago-Trading-Competition-2024 | Same team, second contributor |
| 2024 | Amherst College | https://github.com/ACquantclub/UChicago-Trading-Competition-2024 | Sharpe-maximizing optimizer for Case 2 |

**Blog writeups:**
- Trung Dang (2024 participant, most detailed): https://dmtrung.com/blogs/uchicagotc_writeups.html
- Tianyi Liu (winning team, Part 1): https://tianyi.io/post/chicago1/
- Baumohl (experience post, ETF arb emphasis): https://baumohl.dev/blog/chicago-competition/

**Note on "utcxchangelib":** No public GitHub repository under this exact name was found. The competition's exchange client is distributed to participants as `utc_bot.py` (base class) + versioned folders `utc_xchange_v1.2/`, `utc_xchange_v2.0/` inside team repos. The 2024 repos contain `xchangelib-move_repo/` as a local copy of the exchange library. The base bot class is a gRPC client that competitors subclass, overriding `handle_exchange_update()`.

---

## 2. Exchange Infrastructure

The competition uses a proprietary Python exchange client distributed as part of the competition materials. Key architectural facts extracted from public repos:

```python
# Base class pattern (from ACquantclub/UChicago-Trading-Competition-2021/clients/utc_bot.py)
class UTCBot:
    """Base class. Subclass and override handle_exchange_update()."""
    
    async def place_order(self, asset, qty, side, price, order_type=LIMIT): ...
    async def modify_order(self, order_id, asset, order_type, side, qty, price): ...
    async def cancel_order(self, order_id): ...
    
    async def handle_exchange_update(self, update):
        # STUB — override in subclass
        pass
    
    async def handle_round_started(self):
        # STUB — override in subclass
        pass
```

**2024 version** (`xchange_client`): Adds `bot_place_swap_order(swap_name, qty)` for ETF creation/redemption.

**ETF swap mechanics (2024):**
- `"fromSCP"` swap: redeem 10 SCP → get 3 EPT + 3 IGM + 4 BRV
- `"toSCP"` swap: pay 3 EPT + 3 IGM + 4 BRV → receive 10 SCP
- `"fromJAK"` / `"toJAK"`: same pattern for JAK ETF

---

## 3. Case 1: Market Making

### 3.1 Competition Structure (varies by year)

- **2021:** FX Futures market making (ROR/USD forwards, multiple quarterly expiries H/M/U/Z)
- **2022:** Lumber futures market making (6 years daily price data + monthly precipitation data)
- **2024:** Multi-asset market making with ETFs (5 individual stocks: EPT, DLO, MKU, IGM, BRV; 2 ETFs: SCP, JAK; plus risk-free asset)

### 3.2 Penny-In / Penny-Out (PIPO) — Universal baseline

Every team that placed well implemented some version of this:

```python
# 2022 (John-Trager / lumber futures)
penny_ask_price = self.order_book[contract]["Best Ask"]["Price"] - 0.01
penny_bid_price = self.order_book[contract]["Best Bid"]["Price"] + 0.01
```

Competition organizers in 2024 reportedly made pure PIPO less effective by design, but teams still used it as a base layer with additional levels on top.

### 3.3 Multi-Level Ladder Orders

Beyond penny-in, winning teams add progressive levels:

```python
# 2022 Case 2 bot (options, same pattern applies to equity MM)
penny_in_ask = float(self.books[asset].asks[0].px) - 0.1
penny_in_bid = float(self.books[asset].bids[0].px) + 0.1

ladder1_ask = float(self.books[asset].asks[0].px) + 0.5   # 0.5 wider
ladder1_bid = float(self.books[asset].bids[0].px) - 0.5

ladder2_ask = float(self.books[asset].asks[0].px) + 1.0   # 1.0 wider
ladder2_bid = float(self.books[asset].bids[0].px) - 1.0

# Levels 3-5 at 1.5, 2.5, 3.5 spreads
```

**Tianyi Liu winning team (Scales approach):**
> "We offer 100 lots at $3.60, $3.80, $4.00 — building scales so we trade at better prices with reasonable frequency."

Order sizes typically taper: 65 lots (L0 penny-in), 15 (L1), 10 (L2), 5 (L3).

### 3.4 Position Fading

All serious teams implement position-based fair value adjustment:

```python
# Tianyi Liu (winning team, 2022 EFM case):
# For every 100 lots of position, adjust fair price by fade parameter
self.params['EFM'] = {
    "edge": 0.005,
    "fade": 0.005,   # $0.005 per 100 lots
    "size": 100,
    "edge_slack": 0.10
}
```

```python
# 2021 Amherst (FX futures):
fade = (max_range / 2.0) / max_pos
adjusted_fair = fair - self.pos[asset] * fade
bid_p = adjusted_fair - width / 2.0
ask_p = adjusted_fair + width / 2.0
```

```python
# 2024 zaranip (logarithmic fade):
def set_fade_logic(self):
    for symbol in SYMBOLS + ETFS:
        absolute_position = abs(self.positions[symbol]) / MAX_ABSOLUTE_POSITION
        sign = 1 if self.positions[symbol] > 0 else -1
        self.fade_augmented[symbol] = -self.fade * sign * math.log2(1 + absolute_position)
```

The logarithmic version (2024) is superior: it applies light pressure at moderate positions and heavy pressure only as positions approach max, reducing premature fading.

### 3.5 Dynamic Edge (tanh-based spread adjustment)

2024 top teams added activity-sensitive edge adjustment:

```python
# zaranip / coolkite 2024
def set_edge_logic(self):
    for symbol in SYMBOLS + ETFS:
        for side in [xchange_client.Side.BUY, xchange_client.Side.SELL]:
            amplitude = self.slack / 2
            activity_level = self.get_market_activity_level(symbol, side)
            self.edge_augmented[symbol][side] = max(int(round(
                min_margin + (amplitude * math.tanh(
                    -4 * self.edge_sensitivity * activity_level + 2) + 1)
            )) + random.randrange(-1, 1), 1)

def get_market_activity_level(self, symbol, side):
    price = self.get_last_transacted_price(symbol, side)
    side_orders = (self.order_books[symbol].bids 
                   if side == xchange_client.Side.BUY 
                   else self.order_books[symbol].asks)
    count = 0
    edge_window = self.min_margin + self.slack
    for order in side_orders:
        if abs(order - price) < edge_window:
            count += 1
    return count
```

**Parameters (2024 tuned values):**

| Symbol group | min_margin | fade | edge_sensitivity | slack |
|---|---|---|---|---|
| ETFs (SCP, JAK) | 1 | 10 | 1.5 | 3 |
| Stocks (EPT, DLO, MKU, IGM, BRV) | 1 | 80 | 0.25 | 4 |
| max_pos | 200 | — | — | — |
| spreads | [2, 4, 6] | — | — | — |

### 3.6 ML / Statistical Fair Value Attempts

Teams tried but generally abandoned in favor of simpler methods:
- **SVM, TCN, LSTM** — tested on lumber futures data (2022), dropped
- **ARIMA, Exponential Smoothing, Seasonal models** — tested on lumber, dropped
- **Key finding:** Precipitation data did not significantly predict lumber prices

---

## 4. Case 2

**Case 2 structure varies by year:**
- **2022:** Options market making (calls + puts across strikes [90,95,100,105,110], multiple expiries)
- **2024:** Portfolio optimization (5 stocks + 2 ETFs + risk-free asset; maximize Sharpe ratio)

### 4.1 Case 2 as Options Market Making (2022)

The 2022 second-place team (John-Trager) implemented pure options market making, not Black-Scholes valuation:

**Strategy:** Same ladder / penny-in logic applied to all option contracts simultaneously.

**Risk management:** When position in any single option leg became too large, open offsetting position on the same contract (buy if too short, sell if too long) to flatten.

**Critical failure mode (2022):** The team was ranked 1st during every round but failed to close all positions before round end → cash settlement at Black-Scholes theoretical value resulted in losses. Final rank dropped to ~4th.

**Lesson:** Always implement end-of-round position liquidation logic for cash-settled instruments.

```python
# Position clearing logic (case2_bot.py, 2022)
clearing_quant = 6 if ticks_elapsed > 400 else 3
for num in range(self.positions[asset] // 15):
    requests.append(
        self.modify_order(
            f"{asset}{num}", asset,
            pb.OrderSpecType.LIMIT,
            pb.OrderSpecSide.ASK,
            clearing_quant,
            penny_in_ask
        )
    )
```

### 4.2 Case 2 as Portfolio Optimization (2024)

The 2024 Case 2 was a pure portfolio optimization problem: given historical returns data and analyst predictions, construct a portfolio maximizing Sharpe ratio.

**Competition setup:** 5 individual stocks (labeled A–F), 2 ETFs, 1 risk-free asset. Analyst predictions provided as forward-looking signals.

---

## 5. ETF Arbitrage Implementations

ETF arbitrage was the highest-alpha strategy in 2024. The core principle: if ETF fair value (computed from constituent weights) diverges from market price by more than conversion cost, create/redeem.

### 5.1 ETF Compositions (2024 competition)

```python
# SCP: creation requires 3 EPT + 3 IGM + 4 BRV (total 10 units → 10 SCP)
# JAK: creation requires 2 EPT + 5 DLO + 3 MKU (total 10 units → 10 JAK)

def compute_etf_fair(fair):
    scp_fair = (3 * fair["EPT"] + 3 * fair["IGM"] + 4 * fair["BRV"]) / 10
    jak_fair  = (2 * fair["EPT"] + 5 * fair["DLO"] + 3 * fair["MKU"]) / 10
    return scp_fair, jak_fair
```

### 5.2 Arbitrage Trigger and Execution

```python
# From zaranip/coolkite 2024 final bot
async def bot_place_arbitrage_order(self, etf, side, fair):
    convert = {
        "SCP": {"EPT": 3, "IGM": 3, "BRV": 4},
        "JAK": {"EPT": 2, "DLO": 5, "MKU": 3}
    }
    qty = random.randint(1, 3)  # lots of 10

    if side == "from":  # ETF overpriced: sell ETF, buy constituents, redeem
        await self.bot_place_order(etf, qty * 10, xchange_client.Side.BUY,
                                   round(fair[etf]))
    elif side == "to":  # ETF underpriced: buy constituents, create ETF, sell ETF
        for symbol in convert[etf]:
            await self.bot_place_order(symbol, qty * 10,
                                       xchange_client.Side.BUY,
                                       round(fair[symbol]))

    await self.bot_place_swap_order(f"{side}{etf}", qty)

    if side == "from":
        for symbol in convert[etf]:
            await self.bot_place_order(symbol, qty * 10,
                                       xchange_client.Side.SELL,
                                       round(fair[symbol]))
    elif side == "to":
        await self.bot_place_order(etf, qty * 10,
                                   xchange_client.Side.SELL,
                                   round(fair[etf]))

# Trigger condition:
predicted_price = fair[etf]
market_price    = current_book_mid[etf]
if predicted_price - market_price > self.etf_margin:   # ETF underpriced → create and sell
    await self.bot_place_arbitrage_order(etf, "to", fair)
elif predicted_price - market_price < -self.etf_margin:  # ETF overpriced → buy and redeem
    await self.bot_place_arbitrage_order(etf, "from", fair)
```

**Default `etf_margin` parameter:** 120 (tuned to avoid over-firing on noise)

### 5.3 Key Insight from Baumohl Writeup

> "The underlying securities are never mispriced; the ETF is. ETF arbitrage was the most effective strategy when it fired correctly."

The ETF conversion fee matters: if fee > spread, the arb is unprofitable. Teams that failed accounted for this incorrectly.

---

## 6. Fair Value Calculation Methods

In order of sophistication (and rough effectiveness):

### Method 1: Last Transacted Price (LTP)

```python
# Fastest, most responsive, but noisy
fair[symbol] = last_trade_price[symbol]
```

*One team switched to this 24 hours before 2024 competition and lost significantly — it overreacts to single prints.*

### Method 2: Mid-Price

```python
fair = (best_bid + best_ask) / 2
```

*Simple baseline, ignores order imbalance.*

### Method 3: Exponential Moving Average (EMA)

```python
# alpha = 0.2 (2024 teams)
EMA = (1 - alpha) * EMA + alpha * P_n
```

*Stable, slow to react to real moves.*

### Method 4: Sliding Window Mean / Trailing N-Period Average

```python
# 5-period trailing average (zaranip 2024)
fair[symbol] = np.mean(self.history[symbol][-5:]) \
    if len(self.history[symbol]) >= 5 \
    else np.mean(self.history[symbol])
```

### Method 5: Sliding Window Median (Order Book Depth Method)

Described in Trung Dang writeup — most robust but abandoned by his team under competition pressure:

```
Algorithm:
1. Treat each bid order as '(' and each ask order as ')' with volume as repetition count
2. Find the price index i that minimizes |cumulative_bids[i] - cumulative_asks[i]|
3. This index is the "balance point" of supply/demand = fair value

Generated ~$30,000 per round during training. Abandoned at competition for speed concerns.
```

### Method 6: Interest Rate Parity (2021 FX Futures)

```python
# Forward pricing for FX futures
ir_base  = math.pow(self.interestRates[base],  expiry - self.today)
ir_quote = math.pow(self.interestRates[quote], expiry - self.today)

# Blend spot with forward parity over time
t    = (DAYS_IN_YEAR - self.today) / DAYS_IN_YEAR
spot = last * t + spot * (1 - t)   # time-weighted spot price
forwardInterestParity = round_nearest(
    spot * float(ir_base) / float(ir_quote),
    TICK_SIZES[asset]
)

# 80% theoretical forward, 20% current market mid
fair = forwardInterestParity * 0.8 + self.mid[asset] * 0.2
```

Federal rate change events incorporated with 5-day linear smoothing.

### Method 7: Potential Energy / Physics-Inspired Model

From Trung Dang writeup (2024 winning team's approach):

```
δ(y | x, k) = f(x) - f(y) + μ_k ∫[x→y] cos(arctan(df/dx)) √(1 + f'²) dx

Where:
- f(x) is the kernel density estimate of price distribution
- μ_k is "friction" inversely proportional to variance
- The integral computes arc-length weighted by gradient direction

Intuition: Prices behave like a particle in a potential energy field.
Direction of movement predicted by gradient of the KDE.
```

A physics-based extension was subsequently developed using particle-scale models. This was the fair value method that distinguished the first-place team.

---

## 7. Market Making Spread / Edge / Fade Logic

### 7.1 Core Framework (Tianyi Liu / winning team)

```
State variables:
  fair   = estimated fair price
  edge   = minimum profit margin per side
  fade   = position-based fair value adjustment
  slack  = how much edge can flex up/down
  size   = base order size

Bid = fair - edge - fade * (position / 100)
Ask = fair + edge - fade * (position / 100)

Competitive pennying: if competitor quotes better than our edge, 
improve by 1 tick to maintain queue priority
```

### 7.2 Fade Comparison: Linear vs Logarithmic

| Type | Formula | Behavior |
|------|---------|----------|
| Linear (2021/2022) | `fade * position` | Constant pressure per lot |
| Logarithmic (2024) | `-fade * sign(pos) * log2(1 + \|pos\| / max_pos)` | Light at moderate, heavy near max |

**Recommendation:** Use logarithmic fade for larger max positions.

### 7.3 Edge Adjustment (tanh model, 2024)

```
edge = min_margin + (slack/2) * [tanh(-4 * sensitivity * activity + 2) + 1]

When activity is low  (0): edge ≈ min_margin + slack   (wide spread, few competitors)
When activity is high (1): edge ≈ min_margin            (tight spread, many competitors)
```

### 7.4 Penny-In Rule

> *"Send orders one cent below the ask and one cent above the bid to always have the best bid and ask."*

In 2024 this was partially deprecated by organizers, but still functioned when combined with wider-level ladder orders.

---

## 8. Options Pricing Approaches

### 8.1 Black-Scholes (mostly abandoned in practice)

Teams referenced BS but switched away:

```python
# Attempted (commented out in John-Trager 2022 case2_bot.py):
# per_share_val = my_bs('c', underlying_px, strike_px,
#                        time_to_expiry, 0.00, volatility)
# volatility = (stdev + 0.1) ** (1/3) - 0.5  # ad hoc vol estimate
```

**Why it failed:** Volatility estimation in real-time was unstable; the theoretical price diverged enough from the market mid that market-making on theoretical value lost to teams simply quoting the observable mid with tight spreads.

**Settlement mechanic (critical):** At round end, option positions are cash-settled at Black-Scholes value. This means:
- Delta-hedging the underlying (UC stock) against option positions is necessary
- Net delta exposure at round end = PnL impact of underlying move * BS delta

### 8.2 Market Making on Options (what works)

```
Strategy: treat options like any other asset; penny-in across all strikes and expiries.

Risk management:
  if abs(position[option_contract]) > RISK_LIMIT:
      place offsetting order on same contract to flatten

Greek limits (defined but often unused):
  delta_limit = 200
  gamma_limit = 100
  theta_limit = 500
  vega_limit  = 100
```

**2022 second-place team:** Was ranked 1st in every round using this approach but lost position due to end-of-round settlement failure.

### 8.3 Implied Volatility Surface (not seen in public repos)

No public repo shows a working IV surface implementation. The potential energy physics model from 2024 was the closest to a volatility-aware pricing approach.

---

## 9. Portfolio Optimization Strategies

*Applies primarily to Case 2 in 2022/2024 and Case 3 in other years.*

### 9.1 PAMR — Passive Aggressive Mean Reversion (2024, best performing)

**Source:** Springer ML paper: https://link.springer.com/article/10.1007/s10994-012-5281-z

```python
# Complete implementation (zaranip/Chicago-Trading-Competition-2024, case_2/final_algorithm/PAMR.py)

class Allocator:
    def __init__(self, eps=0.5, C=500, max_weight=0.25, variant=0):
        self.eps = eps        # passive threshold
        self.C   = C          # aggressiveness cap
        self.max_weight = max_weight
        self.variant = variant

    def allocate_portfolio(self, asset_prices):
        m = len(asset_prices)
        b = np.ones(m) / m  # equal weight start each period (stateless)

        x = asset_prices / asset_prices.mean()  # price relative vector
        x_mean = np.ones(m) / m

        le = max(0.0, np.dot(b, x) - self.eps)  # passive-aggressive loss

        denom = np.dot(x - x_mean, x - x_mean)

        if self.variant == 0:
            lam = le / denom if denom > 1e-8 else 0
        elif self.variant == 1:
            lam = min(self.C, le / denom) if denom > 1e-8 else 0
        elif self.variant == 2:
            lam = le / (denom + 0.5 / self.C)

        lam = min(lam, 100000)

        b = b - lam * (x - x_mean)
        b = self._simplex_project(b)

        # cap max weight
        b = np.minimum(b, self.max_weight)
        total = b.sum()
        if total > 0:
            b = b / total

        return b

    def _simplex_project(self, v):
        n = len(v)
        u = np.sort(v)[::-1]
        cssv = np.cumsum(u)
        rho = np.where(u > (cssv - 1) / (np.arange(n) + 1))[0][-1]
        theta = (cssv[rho] - 1) / (rho + 1)
        return np.maximum(v - theta, 0)
```

**Key parameters:**
- `eps = 0.5`: Tolerance; how much underperformance triggers rebalancing
- `C = 500`: Aggressiveness cap (variant 1/2)
- `max_weight = 0.25`: Max 25% in any single asset
- Best Sharpe achieved in backtesting: ~2.54 mean across test period

### 9.2 Sharpe Maximization via SLSQP (Amherst College 2024)

```python
# ACquantclub/UChicago-Trading-Competition-2024
from scipy.optimize import minimize

def maximize_sharpe(predicted_returns, cov_matrix):
    n = len(predicted_returns)
    
    def neg_sharpe(weights):
        portfolio_return = np.dot(weights, predicted_returns)
        portfolio_risk   = np.dot(weights.T, np.dot(cov_matrix, weights))
        return -(portfolio_return / np.sqrt(portfolio_risk))
    
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = [(-1.0, 1.0)] * n   # allow short positions
    
    result = minimize(
        neg_sharpe,
        x0=np.ones(n) / n,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )
    return result.x

# Analyst predictions generation:
analyst_predictions = (training_data.rolling(window=window_size).mean() 
                       + np.random.normal(0, training_data.std(), 
                                          training_data.shape))

# Covariance matrix:
cov_matrix = pd.DataFrame(np.cov(np.transpose(training_data)))
```

**Achieved:** Mean Sharpe 2.54 on test set (range 0.11–5.93).

### 9.3 Black-Litterman (2022 — partial implementation)

```python
# John-Trager/UChicago-Trading-Competition, Case3.py
# NOTE: Full BL equations were commented out in final submission

# Market cap weights (5 clusters: AC, DEF, GH, B, I)
w_market = cluster_cap_weights

# Implied returns: π = risk_aversion * Σ * w_market
pi = risk_aversion * sigma @ w_market

# BL posterior (attempted, commented out):
# E[R] = Σ_combined @ (Σ_historical^-1 @ π + Σ_analyst^-1 @ Q)

# What was actually used:
# Minimum variance weights from combined covariance matrix
weight = row_sum / total_sum  # row-normalized covariance inverse

# Final: 97% min-variance + 3% Risk Parity Adjustment (RPA)
rpa = weights * (weights @ historical_cov) / sqrt(portfolio_variance)
final_weights = 0.97 * min_var_weights + 0.03 * rpa
```

Placed 7th — incomplete BL implementation was likely the cause.

### 9.4 Genetic Algorithm (2021 / awrd2019)

- Repo: https://github.com/awrd2019/UChicago-Trading-Competition-Case-3
- Optimizes portfolio weights through evolutionary search
- Handles fat-tailed return distributions (non-Gaussian) better than MVO
- Detailed walkthrough in an associated Medium article (linked in repo README)

### 9.5 Other Strategies Tested (2024 UMass team)

From zaranip README — tested via K-fold cross-validation:
1. Mean-Variance Optimization (MVO / Markowitz)
2. Particle Swarm Optimization (PSO)
3. OLMAR (Online Portfolio Selection with Moving Average Reversion)
4. Genetic algorithms with clustering
5. Quantum-inspired Tabu Search
6. Evolutionary algorithms with multiobjective optimization
7. Heterogeneous Multiple Population PSO

**Winner:** PAMR (Variant 1, C=500) outperformed all above on their data.

### 9.6 ADF Stationarity Testing (2024 standard practice)

Teams used Augmented Dickey-Fuller tests to confirm mean reversion before applying PAMR/OLMAR:

```python
from statsmodels.tsa.stattools import adfuller
result = adfuller(asset_returns)
# p-value < 0.05 → stationary → PAMR applicable
```

---

## 10. Key Lessons and Failure Modes

### From 2022 (John-Trager / Michigan, 2nd place)

1. **Position closure before settlement is mandatory.** Being 1st in every round but missing position close = 4th place.
2. **Multi-threading / multiprocessing for order updates** — the team that beat them (1st place) had faster order placement through async/parallel execution.
3. **Fair value testing is hard without volume.** Lumber futures had thin liquidity; calibrating fair value was nearly impossible in testing.
4. **Black-Scholes for live options trading** is unstable — market making works better.

### From 2024 (Trung Dang writeup)

1. **Don't abandon a working model** for speed. Sliding Window Median generated $30K/round in training; switching to LTP 24h before competition cost them dearly.
2. **Don't overtrain on the practice platform.** The practice environment has different liquidity and bot behavior from the real competition.
3. **Hitter bots will aggressively take your quotes.** Design position limits and fade accordingly.
4. **ETF arbitrage is high-alpha but requires correct conversion fee accounting.** Margin must exceed round-trip conversion cost.
5. **Rank-based scoring** means threshold strategies are viable: even small positive PnL above the median wins points.

### From 2024 (Baumohl writeup)

1. **ETF arb dominated** — "the underlying securities are never mispriced; the ETF is."
2. **Pennying was made obsolete** by organizers in 2024 specifically — must have backup strategies.
3. **Risk-free asset strategy:** If market conditions are stable, max out the risk-free position for guaranteed returns.
4. **Limit orders only** — market orders can be bait traps set by sophisticated bots.

### From 2021 (Amherst / FX futures)

1. **Interest rate event smoothing:** Federal rate announcements spike fair value; implement 5-day linear smoothing to avoid overreaction.
2. **Spot hedging of futures exposure:** Net delta of quarterly futures must be managed in spot FX.

---

## 11. Summary: What Actually Wins

Based on final placements across all available data:

### Case 1 (Market Making): What wins
| Priority | Strategy | Why |
|----------|----------|-----|
| 1 | Dynamic edge + logarithmic fade | Adjusts to market microstructure in real time |
| 2 | ETF arbitrage (when ETFs present) | High-confidence, bounded-risk alpha |
| 3 | Multi-level ladder orders | Captures both penny-in flow and wider opportunistic fills |
| 4 | Robust fair value (sliding window median or EMA) | Resilience against LTP noise |
| 5 | Fast async order placement | Volume advantage over single-threaded competitors |

**Avoid:** Pure PIPO without levels (easily competed away); LTP fair value (too noisy); overtraining on practice platform.

### Case 2 (Portfolio Optimization): What wins
| Priority | Strategy | Why |
|----------|----------|-----|
| 1 | PAMR (mean reversion) with ADF pre-screening | Consistently top Sharpe in published backtests |
| 2 | SLSQP Sharpe maximization with rolling window | Handles time-varying correlations |
| 3 | Max risk-free asset allocation | Guaranteed return, improves Sharpe denominator |

**Avoid:** Pure MVO (assumes normally distributed returns, overfits to sample covariance); incomplete Black-Litterman (dropped to 7th with partial BL); static weights.

### Case 2 / Options Market Making (when applicable): What wins
| Priority | Strategy | Why |
|----------|----------|-----|
| 1 | Market make all strikes and expiries simultaneously | Diversifies fill risk |
| 2 | Hard position limits per contract with auto-hedge | Prevents blowup |
| 3 | **Mandatory position close before round end** | Cash settlement at BS price penalizes open positions |
| 4 | Delta hedging underlying when possible | Reduces directional exposure |

---

*End of document. All strategies above are derived from publicly available GitHub repositories and blog posts by competition participants. Sources listed throughout.*
