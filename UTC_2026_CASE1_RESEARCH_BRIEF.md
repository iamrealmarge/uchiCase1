# UTC 2026 — Case 1: Market Making — Deep Research & Strategy Brief

**Team:** ucla_calberkeley (Yifan, Emily Mo, Gary Tao, Margaret Zhou)  
**Competition:** 14th Annual UChicago Trading Competition, April 10-11 2026, Willis Tower Chicago  
**Platform:** X-Change (in-house, built by FM program)  
**Case 1:** Run LIVE on competition day (Saturday April 11, 9:15am–12:15pm CDT)

---

## 1. CASE 1 STRUCTURE (from case packet)

### Assets
| Asset | Type | Key Mechanics |
|-------|------|---------------|
| **Stock A** | Small-cap | Constant P/E ratio. Earnings 2x/day as structured news. `fair_A = EPS_A × PE_ratio` |
| **Stock B** | Semiconductor | NO direct info on stock. Trade via **European options** (calls/puts, 3 strikes, single expiry). One underlying path per round. |
| **Stock C** | Large-cap insurance | Driven by operations earnings + bond portfolio. Bond portfolio inversely depends on Fed rate expectations. P/E is NOT constant — varies with yields. |
| **ETF** | 1 share A + 1 share B + 1 share C | Can swap (create/redeem) for a fee. Settlement = NAV. |
| **Fed Market** | Prediction market | 3 outcomes: hike (+25bps), hold (0), cut (-25bps). Probabilities quoted. |
| **Meta Market** | Unknown | Revealed competition day only. |

### Round Structure
- **3 hours** of rounds, each **15 minutes**
- Each round = **10 days**, each day = **90 seconds**, each second = **5 ticks**
- Positions **reset at end of each round**
- **Increasing difficulty** over rounds (tighter spreads, less volume, more volatile)
- **Later rounds weighted more heavily** in scoring
- **Nonlinear P&L → points** conversion (rewards consistency, punishes variance)
- Practice round doesn't count

### Key Formulas

**Stock C pricing:**
```
PE_t = PE_0 × exp(-γ × (y_t - y_0))          # P/E decays with yield
ΔB ≈ B_0 × (-D×Δy + 0.5×C×(Δy)²)            # Bond portfolio Taylor expansion
P_C = EPS_C × PE_t + λ × ΔB/N + noise         # Final C price
```

**Yield from Fed market:**
```
E[Δr] = (+25)×q_hike + 0×q_hold + (-25)×q_cut  # Expected rate change (bps)
y_t = y_0 + β_y × E[Δr]                          # Yield update
```

**Put-Call Parity (European options on B):**
```
C - P = S_0 - K×e^(-rT)
```
Violation → riskless arb.

**Box Spread Arbitrage:**
```
Bull call spread + Bear put spread at K1 < K2
Payoff = K2 - K1 regardless of underlying
If quoted above/below PV → arbitrage
```

### Structured vs Unstructured News
- **Structured:** Earnings (A at known times, C at tick 22 and 88), CPI prints (Forecast vs Actual), Fed probabilities
- **Unstructured:** Headlines — may or may not relate to Fed decision. Need NLP/keyword parsing.
- **CPI rule:** Actual > Forecast → inflation → points toward HIKE. Vice versa → CUT.

### Risk Limits (released on Ed, subject to change day-of)
- Max Order Size
- Max Open Order (unfilled order size)
- Outstanding Volume (total unfilled volume)
- Max Absolute Position (sum of long + short)

**CRITICAL:** Exceeding = orders BLOCKED. You are NOT told which limit you breached.

---

## 2. YOUR CURRENT BOT (strat1.py) — ANALYSIS

### What's Good
- ✅ Correct formulas for A (constant PE), C (yield-dependent PE + bond portfolio), Fed yield model
- ✅ ETF arbitrage logic
- ✅ PCP arbitrage on options
- ✅ Inventory skew on market making
- ✅ Clean modular architecture

### Critical Gaps
- ❌ **Not wired to actual X-Change API** — all stubs (`_place_limit_order` just prints)
- ❌ **No order cancellation before re-quoting** — will stack orders
- ❌ **No multi-level quoting** — only quotes 1 level per side (winners use 3-5 levels)
- ❌ **No dynamic spread adjustment** — static spreads won't adapt to round difficulty
- ❌ **No penny-in logic** — doesn't read competitor quotes to improve by 1 cent
- ❌ **No box spread arbitrage** — only PCP, missing box spreads across strikes
- ❌ **No position fade with tanh/log scaling** — linear skew is too crude
- ❌ **No safety/stop-loss mechanism** — no circuit breaker for runaway losses
- ❌ **No real-time parameter reloading** — can't tune live during competition
- ❌ **No handling of Meta Market** — need flexible handler for unknown instrument
- ❌ **CPI parsing is a heuristic** — needs calibration, sensitivity constant is arbitrary
- ❌ **Headline parser is too simple** — keyword list is minimal
- ❌ **No order tracking** (id→price maps) — can't cancel/modify specific orders
- ❌ **No noise injection** — predictable quoting makes you exploitable

---

## 3. WINNING STRATEGIES FROM PAST COMPETITIONS

### Sources Analyzed
| Source | Year | Placement | Key Strategy |
|--------|------|-----------|--------------|
| [John Trager](https://github.com/John-Trager/UChicago-Trading-Competition) | 2022 | **2nd overall** | Multi-level penny-in, async execution |
| [Zaranip/UMass](https://github.com/zaranip/Chicago-Trading-Competition-2024) | 2024 | Top placer | Potential energy fair price, ETF arb, noise injection |
| [Tianyi Liu blog](https://tianyi.io/post/chicago1/) | Winner | **1st place** | Edge/fade/size tuning, scales, live param reload |
| [Trung Dang blog](https://dmtrung.com/blogs/uchicagotc_writeups.html) | 2024 | Competitor | SWM fair price, tanh edge, log fade |
| [Baumohl blog](https://baumohl.dev/blog/chicago-competition/) | 2024 | Competitor | ETF arb primary, Bayesian missed opp |
| [Gurish165](https://github.com/gurish165/UChicago-Trading-Competition) | 2022 | Competitor | ML (SVR) fair price prediction |
| [Amherst College](https://github.com/ACquantclub/UChicago-Trading-Competition-2024) | 2024 | Competitor | Notebook-based approach |

### The 5 Pillars of Winning Market Making

#### Pillar 1: Fair Price Estimation (THE BOTTLENECK)
> "Price prediction robustness matters more than speed." — Trung Dang (learned the hard way)

**Best approaches ranked:**
1. **Sliding Window Median (SWM)** — $30k/round in testing. Treat order book volumes as information signals. Sort prices, use bid/ask volumes as weights, find equilibrium point.
2. **Exponential Moving Average** — EMA = (1-α)×EMA + α×P_n, α=0.2. Good balance of smoothness and responsiveness.
3. **Model-based** (for A and C specifically) — Use the given formulas. For A: `EPS × PE`. For C: full yield + bond model.
4. **Order book midpoint** — Simple but vulnerable to manipulation.
5. **Last transacted price** — DANGEROUS. Trung's team switched to this the night before and got destroyed.

**For 2026 Case 1 specifically:** We have explicit formulas for A and C, so use those. For B, use options-implied price (from put-call parity). For ETF, compute NAV.

#### Pillar 2: Adaptive Spread / Edge Management
```python
edge = min_margin + (slack/2) × tanh(-4 × edge_sensitivity × activity_level + 2)
```
- **Early rounds:** Wide spreads (0.10-0.20), capture easy money from dumb bots
- **Late rounds:** Tight spreads (0.02-0.05), compete for scarce volume
- **High activity:** Tighter edge to ensure fills
- **Low activity:** Wider edge to maximize per-trade profit

#### Pillar 3: Position Management (Fade)
```python
fade = -f × sign(position) × log₂(1 + |position|)
```
- Logarithmic beats linear: heavily punishes medium positions without overcorrecting small ones
- Per Tianyi (winner): "For every 100 lots, augment fair by $0.02"
- **Critical insight:** Fade protects you from informed traders who know something you don't

#### Pillar 4: Multi-Level Quoting (Scales)
- **L1:** Penny-in (best bid +0.01, best ask -0.01) — small size, capture flow
- **L2:** Fair ± edge — main bread-and-butter quotes
- **L3:** Fair ± 2×edge — catch volatility spikes
- **L4:** Fair ± 3×edge — deep liquidity, outsized profit on panics

Typical sizes: L1=20, L2=40, L3=30, L4=20

#### Pillar 5: Speed & Execution
- **Cancel-before-requote:** Always cancel stale orders before posting new ones
- **Order tracking:** Maintain `order_id → (price, qty)` and `price → order_id` maps
- **Async execution:** Use threading/multiprocessing to send orders faster
- **The winner's edge:** "Our orders were able to get on the books faster using multi-threading"

---

## 4. ALPHA OPPORTUNITIES SPECIFIC TO 2026

### Alpha #1: Stock C Yield Model
Most teams will use a simplistic yield → price mapping. The case packet gives you the EXACT formula with Taylor expansion for the bond portfolio. Teams that correctly implement `ΔB ≈ B₀(-D×Δy + 0.5×C×(Δy)²)` including the convexity term will have a pricing edge, especially when yields move significantly.

### Alpha #2: CPI Surprise → Fed Probability Bayesian Update
Don't just shift probabilities linearly. Use **Bayesian updating**:
```
P(hike|CPI_surprise) ∝ P(CPI_surprise|hike) × P(hike)
```
Calibrate likelihoods from the structured news patterns. This compounds over multiple news releases per round.

### Alpha #3: Box Spread Arbitrage
Most teams will only implement PCP arbitrage. The case packet EXPLICITLY mentions box spreads:
```
Box payoff = K2 - K1 (always)
Fair box value = (K2 - K1) × e^(-rT)
If quoted box ≠ fair value → free money
```
With 3 strikes, you have 3 possible box spreads (K1-K2, K1-K3, K2-K3).

### Alpha #4: ETF Mispricing Bias
Case packet hint: "When ETF and equity prices diverge, it's MORE LIKELY the ETF is mispriced." This means:
- Don't arb both sides equally
- When NAV ≠ ETF price, bet on ETF reverting to NAV
- Trade the ETF leg aggressively, hedge equity legs passively

### Alpha #5: Options Implied B Price
Since B has no direct information, reverse-engineer its fair value from the options chain:
```
From PCP: S = C - P + K×e^(-rT)
Average across all 3 strikes for robust estimate
```
This is better than raw order book mid for B.

### Alpha #6: Smart vs Dumb Bot Detection
Case packet: "There will be some 'smart' and 'dumb' money bots." 
- Track which counterparties consistently move prices in the right direction → those are smart bots
- Fade (widen quotes) when smart bots are aggressive
- Lean into trades against dumb bots
- Large orders imply confidence (Baumohl's missed insight)

### Alpha #7: Earnings Timing Exploitation
Stock A earnings come 2x per day as structured news. Stock C earnings at ticks 22 and 88.
- **Pre-earnings:** Widen spreads (uncertainty high)
- **Post-earnings:** Aggressively penny-in at new fair value before others update
- "If you receive information before the rest of the market, where will you be willing to buy and sell?"

### Alpha #8: Nonlinear Scoring Exploitation
Scoring is nonlinear P&L → points. Consistent small profits >> volatile big swings.
- **Strategy implication:** Prefer many small edge captures over risky directional bets
- Don't chase one monster round; aim for positive P&L in EVERY round
- "Outlier results of both large positive and negative P&L will not excessively impact total score"

### Alpha #9: Late-Round Adaptation
"Strategies that generate positive P&L at the start will decrease over time. Later rounds weighted more heavily."
- Round 1-3: Market-make aggressively, capture dumb money
- Round 4+: Shift to arb-heavy (ETF, PCP, box spreads) as spreads tighten
- Round 7+: Focus on information advantage (news parsing, yield model accuracy)

### Alpha #10: Meta Market Preparation
The "meta market" is revealed day-of. Past competitions have included:
- Prediction markets on other teams' performance
- Markets on competition-specific events
- Markets requiring lateral thinking
- **Prep:** Build a flexible handler that can parse unknown instruments and apply basic market-making

---

## 5. COMPETITIVE LANDSCAPE

### 30+ Schools Competing
Top threats: MIT, Stanford, Princeton, Harvard, Caltech, Carnegie Mellon, Columbia, Yale, Cornell, Georgia Tech, Northwestern, UC Berkeley, UChicago

### What Top Teams Will Do
1. **Everyone** will implement penny-in and basic market making
2. **Most** will have ETF arb and PCP arb
3. **Strong teams** will have dynamic edge/fade, multi-level quoting
4. **Elite teams** will have: live parameter tuning GUI, Bayesian news processing, box spread arb, async multi-threaded execution, smart bot detection

### Our Edge Needs To Be
- **Superior fair price estimation** for C (most complex asset, biggest alpha)
- **Speed** (async order execution, cancel-before-requote)
- **Adaptivity** (live parameter tuning, round-by-round strategy shifting)
- **Completeness** (trade ALL instruments including fed market, options, ETF)

---

## 6. CRITICAL TODO FOR COMPETITION DAY

### Before April 11
1. [ ] Get X-Change API docs from Ed (should be posted)
2. [ ] Wire bot to actual exchange API (replace stubs)
3. [ ] Implement order tracking (id↔price maps)
4. [ ] Add cancel-before-requote
5. [ ] Add multi-level quoting (4 levels)
6. [ ] Implement adaptive edge (tanh formula)
7. [ ] Implement log₂ position fade
8. [ ] Add box spread arbitrage
9. [ ] Add options-implied B pricing
10. [ ] Add Bayesian CPI → Fed probability updates
11. [ ] Build parameter config file + live reload (`exec` or file watcher)
12. [ ] Add safety stop-loss / circuit breaker
13. [ ] Add noise injection on order sizes
14. [ ] Test on mock exchange locally
15. [ ] Practice SSH into competition box (VSCode + SSH required!)

### Competition Day (April 11)
1. [ ] Arrive by 8:00am CDT at Willis Tower
2. [ ] 9:00-9:15: Tech case prep — learn Meta Market, get risk limits
3. [ ] 9:15-12:15: LIVE TRADING — one person starts algo, others monitor/tune
4. [ ] Monitor: positions, P&L, order fill rates, spread evolution
5. [ ] Between rounds: adjust edge, fade, size parameters
6. [ ] Late rounds: shift from MM to arb-heavy strategy

---

## 7. KEY REFERENCES

- [John Trager — 2nd Place 2022](https://github.com/John-Trager/UChicago-Trading-Competition)
- [Zaranip — 2024 Top Placer](https://github.com/zaranip/Chicago-Trading-Competition-2024)
- [Tianyi Liu — Winner Blog](https://tianyi.io/post/chicago1/)
- [Trung Dang — 2024 Writeup](https://dmtrung.com/blogs/uchicagotc_writeups.html)
- [Baumohl — 2024 Experience](https://baumohl.dev/blog/chicago-competition/)
- [Gurish165 — ML Approach](https://github.com/gurish165/UChicago-Trading-Competition)
- [Amherst College — 2024](https://github.com/ACquantclub/UChicago-Trading-Competition-2024)
- [UChicago TC Official](https://tradingcompetition.uchicago.edu/)
- [Ed Discussion Forum](https://edstem.org/us/courses/96484/discussion/)

---

*Generated April 8, 2026. Competition in 3 days.*
