# Repository Survey: Trading Competition Bots & Portfolio Optimization

**Date:** 2026-04-08
**Purpose:** Survey of public GitHub repositories for techniques applicable to UChicago Trading Competition Case 2 (portfolio optimization / Sharpe ratio maximization)

---

## Table of Contents

1. [UChicago Trading Competition Repositories](#1-uchicago-trading-competition-repositories)
2. [Other Trading Competition Repositories](#2-other-trading-competition-repositories)
3. [Portfolio Optimization Libraries](#3-portfolio-optimization-libraries)
4. [Online Portfolio Selection Implementations](#4-online-portfolio-selection-implementations)
5. [Key Technique Summary](#5-key-technique-summary)
6. [What to Steal for Our Case 2 Submission](#6-what-to-steal-for-our-case-2-submission)

---

## 1. UChicago Trading Competition Repositories

### 1.1 John-Trager/UChicago-Trading-Competition (2022, 2nd Place Overall)

- **URL:** https://github.com/John-Trager/UChicago-Trading-Competition
- **Placement:** 2nd overall (3rd Case 1, 4th Case 2, 7th Case 3)
- **What it does:** Full solution for all three UTC 2022 cases — lumber futures market making, options trading, and portfolio optimization.

**Case 2 (Options):**
- Strategy was pure spread-based market making (penny-jumping), NOT Black-Scholes pricing
- Placed orders 0.1 cents inside best bid/ask across 5 escalating price ladder levels (±0.5, ±1.0, ±1.5, ±2.5, ±3.5)
- Greek limits (delta/gamma/theta/vega) were defined in code but never actually enforced — significant oversight
- Position clearing by gradually offloading inventory using market orders after 400 ticks
- Key failure: positions not closed before settlement, turning profits into losses

**Case 3 (Portfolio Optimization):**
- Used **Black-Litterman** portfolio optimization with historical price data and investor views
- Objective: maximize Sharpe ratio over given stock universe
- Placed 7th — suggests B-L alone is not competitive

**Key lessons:**
- Ladder/level orders are more robust than single-spread market making
- Black-Litterman is a starting point but not sufficient alone for top placement
- Position closing before settlement is critical — simple operational discipline matters
- Multi-threading for order submission provides execution speed advantage

**Key files:** `case1_bot.py`, `case2_bot.py`, `Case3.py`

---

### 1.2 zaranip/Chicago-Trading-Competition-2024

- **URL:** https://github.com/zaranip/Chicago-Trading-Competition-2024
- **What it does:** Full solution for UTC 2024 — Case 1 (live market making) and Case 2 (portfolio optimization).

**Case 1 (Market Making):**
- Penny-in, penny-out with ladder levels
- ETF arbitrage: exploit pricing gaps between ETF and underlying basket
- GUI for real-time parameter adjustment (fade, edge, slack, minimum margin)
- Noise injection to prevent deterministic pattern exploitation
- Safety halt when losses exceed thresholds
- `tanh` function for edge parameter margin adjustment (smooth position-size scaling)
- Logarithmic fade functions to limit position accumulation
- Experimented with physics-inspired "proton-electron potential energy" models and kernel density estimation

**Case 2 (Portfolio Optimization):**
- **Primary strategy: PAMR (Passive-Aggressive Mean Reversion)** — selected after comparing 9+ alternatives
- Validation: K-fold cross-validation with 30+ Sharpe ratio comparison graphs across window sizes
- EDA: correlation matrices, ADF stationarity tests, autocorrelation analysis
- Also tested: Genetic algorithms, PSO, OLMAR, Markowitz MVO, Quantum Tabu Search, multi-objective EA
- Selected PAMR for best Sharpe ratio in cross-validation

**Key lessons:**
- PAMR outperformed classical MVO and B-L in this competition setting
- Rigorous cross-validation and backtesting across multiple window sizes is essential
- ADF stationarity testing helps identify mean-reverting assets appropriate for PAMR
- K-fold CV is a sound selection methodology for algorithmic strategies

---

### 1.3 coolkite/Chicago-Trading-Competition-2024

- **URL:** https://github.com/coolkite/Chicago-Trading-Competition-2024
- **What it does:** Another team's solution for UTC 2024 with detailed strategy analysis.

**Case 2 (Portfolio Optimization):**
- Also used **PAMR** as primary strategy (same conclusion as zaranip team)
- 9 strategies tested and benchmarked
- Used K-fold cross-validation to select best Sharpe ratio strategy
- Included genetic algorithm clustering approach and particle swarm optimization

**Key lessons:**
- Multiple teams independently converged on PAMR as best performer in UTC 2024
- This validates PAMR as a serious baseline for UTC Case 2 portfolio problems

---

### 1.4 ACquantclub/UChicago-Trading-Competition-2024 (Amherst College)

- **URL:** https://github.com/ACquantclub/UChicago-Trading-Competition-2024
- **What it does:** Amherst College team's materials for UTC 2024 including case packet PDF and Jupyter notebooks.
- Contains case packet PDF (useful for understanding problem structure)
- Multiple notebook iterations for both cases
- Full case-2 submission notebook available

**Key lessons:**
- The official case packet format reveals constraint structure (long-only, weight bounds, etc.)
- Iterative notebook approach useful for parameter search

---

### 1.5 ACquantclub/UChicago-Trading-Competition-2021 (Amherst College)

- **URL:** https://github.com/ACquantclub/UChicago-Trading-Competition-2021
- **What it does:** FX futures market making using interest rate parity.
- Core strategy: interest rate announcements + interest rate parity for forward contract fair value
- More macro-fundamentals driven than pure order-book market making

**Key lessons:**
- Fundamental valuation (interest rate parity, Black-Scholes) can anchor market making edge
- Useful template for cases involving derivatives or rate-sensitive instruments

---

### 1.6 gurish165/UChicago-Trading-Competition

- **URL:** https://github.com/gurish165/UChicago-Trading-Competition
- **What it does:** Documents the penny-in market making approach in detail with explanation of ladder logic.
- Penny-in with 5 price levels
- Black-Litterman tested for portfolio optimization with modest results
- Pairs trading suggested as an improvement to B-L

**Key lessons:**
- Pairs trading (statistical arbitrage on correlated pairs) can improve portfolio case performance over standalone B-L
- Level-based order books provide robustness against sweep orders

---

### 1.7 stormsurfer98/uchicago-trading (Midwest Trading Competition 2019)

- **URL:** https://github.com/stormsurfer98/uchicago-trading
- **What it does:** Framework/template for UTC 2019 (3 cases). The public repo is a submission skeleton rather than a full strategy disclosure.
- Establishes standard 3-case structure
- Useful for understanding case submission format and package constraints (conda environment, approved packages only)

---

### 1.8 Icyviolet23/UChicagoTrading

- **URL:** https://github.com/Icyviolet23/UChicagoTrading
- **What it does:** UTC competition entry; minimal public documentation.
- Only README available publicly; actual strategy is private
- Worth watching for any future updates

---

## 2. Other Trading Competition Repositories

### 2.1 ericcccsliu/imc-prosperity-2 (2nd Place, IMC Prosperity 2)

- **URL:** https://github.com/ericcccsliu/imc-prosperity-2
- **What it does:** 2nd-place solution for IMC Prosperity 2 global algorithmic trading competition.

**Strategies used:**
- **Market making:** Fair value estimation using market maker mid-prices rather than raw mid; order quotes with optimized edges
- **Position clearing:** Trading at near-zero expected value to free up position limits for better opportunities
- **Statistical arbitrage:** Rolling z-score on spread prices; traded gift baskets when spread deviated from rolling mean using rolling standard deviation thresholds
- **Cross-market prediction:** Discovered historical cross-year data was nearly perfect predictor (R² = 0.99) for certain products
- **Dynamic programming:** Optimized entry/exit timing accounting for position limits, volume constraints, spread costs
- **Parameter optimization:** Grid search over edge sizes and volatility thresholds

**Key lessons:**
- Always check whether historical data from prior years predicts current data — data autocorrelation across time periods is real
- Rolling z-score spread trading is a robust statistical arb approach
- DP for entry/exit optimization beats greedy approaches under position constraints

---

### 2.2 CarterT27/imc-prosperity-3 (9th Global, 2nd USA, IMC Prosperity 3 2025)

- **URL:** https://github.com/CarterT27/imc-prosperity-3
- **What it does:** Alpha Animals team writeup and algorithm for IMC Prosperity 3.

**Strategies used:**
- **Market making (Kelp):** Filter noise from small orders; track mid-prices of dominant market makers to derive fair value; place limit orders around computed fair value
- **Mean reversion (Squid Ink):** Short-term volatility spike detection (>3 standard deviations within 10-timestamp windows); fade the spike, bet on reversion
- **Statistical arb (Baskets):** Linear model with component product coefficients to compute synthetic fair value; trade divergence from market price
- **Options arb (Volcanic Rock):** Treat vouchers as Black-Scholes calls; exploit when price spread between vouchers deviates from strike price difference
- **Copy trading (Round 5):** Detect insider trader "Olivia" and copy her trades to identify market regime

**Key lessons:**
- Volatility spike mean reversion (3-sigma threshold, 10-bar window) is a clean, implementable strategy
- Options arbitrage via Black-Scholes synthetic value vs. market spread is highly profitable when available
- Filtering out noise orders and tracking dominant market maker mids is superior to raw VWAP/mid

---

### 2.3 jmerle/imc-prosperity-2 (9th Place + Open-Source Tools)

- **URL:** https://github.com/jmerle/imc-prosperity-2
- **What it does:** 9th-place solo IMC solution plus widely-used open-source competition infrastructure tools.

**Tools built (widely adopted by community):**
- Local backtester for offline algorithm testing
- Visualizer for submission and backtest results
- Submitter CLI for automated uploads
- Leaderboard viewer

**Trading strategies:**
- Market making based on "popular buy/sell price" levels
- Arbitrage between market locations (orchids)
- Directional trading using de-anonymized trader pattern signals

**Key lessons:**
- A local backtester is essential for rapid iteration — build one first
- De-anonymized trade attribution reveals systematic patterns worth tracking

---

### 2.4 nmishra459/Jane-Street-FTTP-ETC (8th Place, Jane Street ETC 2021)

- **URL:** https://github.com/nmishra459/Jane-Street-FTTP-ETC
- **What it does:** Bot for Jane Street Electronic Trading Competition (ETC); built by MIT/Stanford/Harvard team.
- Uses bond fair value knowledge for arbitrage on mispriced instruments
- TCP socket connection to simulated exchange
- Ranked 8th among all teams

**Key lessons:**
- Knowing theoretical fair value of any instrument is the strongest edge in competition trading
- Bond pricing is deterministic given rates — model this precisely before placing orders

---

## 3. Portfolio Optimization Libraries

### 3.1 PyPortfolioOpt (robertmartin8)

- **URL:** https://github.com/robertmartin8/PyPortfolioOpt
- **Stars:** ~4k
- **What it does:** Gold-standard Python portfolio optimization library. Most commonly referenced in UTC submissions.

**Methods supported:**
- `ef.max_sharpe()` — tangency portfolio (maximum Sharpe ratio)
- `ef.min_volatility()` — global minimum variance
- `ef.efficient_return(target)` / `ef.efficient_risk(target)` — efficient frontier traversal
- Black-Litterman (`BlackLittermanModel`) — combines market equilibrium with investor views
- Hierarchical Risk Parity (`HRPOpt`) — clustering-based diversification
- Mean-CVaR and Mean-Semivariance optimizers
- Ledoit-Wolf, Oracle Approximating Shrinkage covariance estimators

**Key API:**
```python
from pypfopt import EfficientFrontier, risk_models, expected_returns

mu = expected_returns.mean_historical_return(prices)
S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
ef = EfficientFrontier(mu, S)
weights = ef.max_sharpe()
clean_weights = ef.clean_weights()
```

**Key lessons:**
- Ledoit-Wolf shrinkage covariance is superior to sample covariance for small-sample regimes (< 252 observations per asset)
- L2 regularization in `EfficientFrontier` prevents extreme corner-solution weights
- HRP is robust when correlations are unstable

---

### 3.2 Riskfolio-Lib (dcajasn)

- **URL:** https://github.com/dcajasn/Riskfolio-Lib
- **Stars:** ~3k
- **What it does:** Comprehensive quantitative portfolio construction library built on CVXPY; 24+ risk measures.

**Key methods:**
- Mean-Risk optimization (min risk, max return, max Sharpe, max utility)
- Logarithmic Mean-Risk (Kelly Criterion growth optimization)
- Risk Parity (equal risk contribution)
- HRP and HERC (hierarchical clustering)
- Nested Clustered Optimization (NCO)
- Black-Litterman (standard, Bayesian, Augmented)
- Worst-case mean variance
- Risk measures: standard deviation, MAD, CVaR, EVaR, CDaR, Ulcer Index, Max Drawdown, Tail Gini

**Key lessons:**
- When Sharpe ratio is the competition metric, use CVaR or Sortino as risk measure rather than variance — they penalize downside more appropriately
- NCO (Nested Clustered Optimization) is a more sophisticated alternative to HRP for large asset universes
- Kelly Criterion log-utility maximization can outperform Sharpe under certain regimes (growth-focused competitions)

---

### 3.3 skfolio/skfolio

- **URL:** https://github.com/skfolio/skfolio
- **Stars:** ~1.9k
- **What it does:** Portfolio optimization with scikit-learn API compatibility — supports cross-validation, GridSearchCV, and pipelines.

**Key features:**
- Sklearn-compatible `fit/predict` interface
- WalkForward and Combinatorial Purged Cross-Validation built in
- GridSearchCV for hyperparameter search on optimization parameters
- Risk budgeting, maximum diversification, distributionally robust CVaR
- Constraint handling: transaction costs, cardinality, tracking error

**Key lessons:**
- Treating portfolio construction as an sklearn estimator enables systematic walk-forward backtesting with `cross_val_score`
- Combinatorial Purged CV avoids look-ahead bias in strategy validation
- `maximize_ratio` with Sharpe objective is a drop-in for competition use

---

### 3.4 riskparity.py (convexfi)

- **URL:** https://github.com/convexfi/riskparity.py
- **Stars:** ~319
- **What it does:** Fast, scalable risk parity portfolio construction using C++ backend via Python bindings.

**Algorithms:**
- Convex formulation (Spinu 2013) — guaranteed unique solution
- Cyclical methods (Griveau-Billion 2013, Choi & Chen 2022)
- Successive Convex Approximation (Feng & Palomar 2015) — handles non-convex extensions
- Uses JAX for numerical acceleration

**Key lessons:**
- For risk parity, cyclical Newton method is faster than full CVXPY solve — useful if rebalancing frequently
- Risk parity produces more stable out-of-sample Sharpe than MVO in most published backtests

---

### 3.5 Gouldh/ML-Portfolio-Optimization

- **URL:** https://github.com/Gouldh/ML-Portfolio-Optimization
- **What it does:** Combines MVO, Black-Litterman, and ML-generated return forecasts.

**ML models used:**
- Linear Regression, Random Forest, Gradient Boosting for return prediction
- ML predictions fed into Black-Litterman as "views"
- Constraint: individual asset weight bounds
- Metrics: Sharpe, Sortino, Information Ratio

**Key lessons:**
- ML-predicted returns as BL "views" is a clean pipeline: train on rolling window, predict next-period returns, feed as views into BL optimizer
- Random Forest and Gradient Boosting consistently outperform Linear Regression for return prediction on financial data

---

## 4. Online Portfolio Selection Implementations

### 4.1 Marigold/universal-portfolios

- **URL:** https://github.com/Marigold/universal-portfolios
- **What it does:** Reference implementations of 20+ Online Portfolio Selection (OLPS) algorithms.

**Algorithm categories:**
- **Benchmarks:** Buy-and-hold, Constant Rebalanced Portfolio (CRP), BCRP, Dynamic CRP
- **Follow-the-Winner:** Universal Portfolios, Exponential Gradient
- **Follow-the-Loser (Mean Reversion):** Anticorrelation, PAMR, OLMAR, RMR, CWMR, WMAMR, RPRT
- **Pattern Matching:** BNN, CORN
- **Other:** Markowitz, Kelly, ONS, MPT

**Key lessons:**
- PAMR (Passive Aggressive Mean Reversion) and OLMAR (Moving Average Reversion) are the top-performing algorithms in this category for competition-style problems
- CRP is a surprisingly strong benchmark — many "sophisticated" strategies fail to beat it consistently
- Pattern matching (CORN) can outperform in markets with identifiable cyclical patterns

---

### 4.2 nglahani/Online-Quantitative-Trading-Strategies

- **URL:** https://github.com/nglahani/Online-Quantitative-Trading-Strategies
- **What it does:** Implements the full taxonomy from "Online Portfolio Selection: A Survey" (Li & Hoi) with performance evaluation.

**Strategies implemented:**
- FTW: Exponential Gradient, Follow-the-Leader, Follow-the-Regularized-Leader
- FTL: Anticorrelation, PAMR, CWMR, OLMAR, RMR
- Pattern Matching: Histogram, Kernel, Nearest-neighbor
- Meta-Learning: Online Gradient/Newton, Fast Universalization

**Metrics:** Cumulative Wealth, Exponential Growth Rate, Sharpe Ratio, Max Drawdown, Runtime

**Key lessons:**
- The survey paper (Li & Hoi) is the canonical academic reference for PAMR/OLMAR theory — read it before implementing
- Meta-learning ensemble approaches blend FTW and FTL, potentially best of both worlds

---

### 4.3 ACM-Research/online-portfolio-selection

- **URL:** https://github.com/ACM-Research/online-portfolio-selection
- **What it does:** Benchmarking framework for OLPS algorithms on real-world trading scenarios.
- Extensible Python package with data preprocessing, strategy implementations, backtesting, visualization
- Simulates market conditions and runs walk-forward backtests

**Key lessons:**
- Good reference for how to structure a fair backtest comparison across PAMR/OLMAR/MVO variants
- Walk-forward backtesting prevents look-ahead bias

---

## 5. Key Technique Summary

| Technique | Best Suited For | Top Reference Repos |
|-----------|----------------|---------------------|
| PAMR (Passive Aggressive Mean Reversion) | Sharpe optimization in mean-reverting markets | zaranip/UTC-2024, coolkite/UTC-2024, Marigold/universal-portfolios |
| OLMAR (Moving Average Reversion) | Online sequential portfolio updates | Marigold/universal-portfolios |
| Max Sharpe via PyPortfolioOpt | Classical MVO baseline | robertmartin8/PyPortfolioOpt |
| Ledoit-Wolf Shrinkage Covariance | Regularized covariance for small samples | robertmartin8/PyPortfolioOpt |
| Black-Litterman + ML Views | When return forecasts available | Gouldh/ML-Portfolio-Optimization |
| Hierarchical Risk Parity (HRP) | Unstable correlations, large universe | robertmartin8/PyPortfolioOpt, dcajasn/Riskfolio-Lib |
| Risk Parity (ERC) | Stable diversification without return forecast | convexfi/riskparity.py |
| CVaR / Downside Risk Optimization | Penalizing tail losses in Sharpe context | dcajasn/Riskfolio-Lib, skfolio/skfolio |
| Walk-Forward Cross-Validation | Unbiased strategy selection | skfolio/skfolio, nglahani/Online-QTS |
| Nested Clustered Optimization (NCO) | Large asset universes with cluster structure | dcajasn/Riskfolio-Lib |
| ETF Arbitrage | Market making cases with ETF products | zaranip/UTC-2024 |
| Penny-in + Ladder Levels | Market making (Case 1 type) | John-Trager/UTC-2022, gurish165/UTC |
| Volatility Spike Mean Reversion | Short-term tactical allocation | CarterT27/imc-prosperity-3 |

---

## 6. What to Steal for Our Case 2 Submission

### Highest-Priority Takeaways

**1. PAMR as primary strategy**
Two independent UTC 2024 teams (zaranip and coolkite) both independently selected PAMR as the best strategy after testing 9+ alternatives. This strong empirical consensus means PAMR should be our baseline to beat or augment.

Reference: https://github.com/zaranip/Chicago-Trading-Competition-2024
Algorithm paper: Li et al., "PAMR: Passive Aggressive Mean Reversion Strategy for Portfolio Selection" (2012)

**2. K-fold cross-validation for strategy and parameter selection**
Both UTC 2024 teams used K-fold CV with Sharpe ratio as selection metric across multiple window sizes (30+ graphs). This is the correct methodology to avoid overfitting.

Implementation: `skfolio` or `sklearn` KFold directly on our backtest loop

**3. ADF stationarity testing to identify mean-reverting assets**
Run Augmented Dickey-Fuller tests on each asset's price series before deciding on mean-reversion vs. momentum. Only apply PAMR to statistically confirmed mean-reverting series.

Implementation: `statsmodels.tsa.stattools.adfuller`

**4. Ledoit-Wolf shrinkage for covariance matrix**
MVO with sample covariance is notoriously unstable. Ledoit-Wolf shrinkage produces a well-conditioned matrix and is the recommended replacement.

```python
from pypfopt import risk_models
S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
```

**5. Correlation matrix + clustering before optimization**
Use hierarchical clustering on the correlation matrix to identify asset groups before applying HRP or NCO. Riskfolio-Lib has this built in.

**6. Rolling window tuning**
PAMR and OLMAR both have a lookback window parameter (epsilon and window size). Sweep these via cross-validation. UTC 2024 teams generated 30+ Sharpe ratio charts varying these parameters.

**7. Benchmark against CRP and equal-weight**
The Constant Rebalanced Portfolio (equal-weight with daily rebalancing) is a deceptively strong baseline. Any sophisticated strategy should clearly beat it in CV before submission.

**8. Consider CVaR as risk measure over variance**
For Sharpe ratio competitions, minimizing CVaR (tail risk) rather than variance can produce strategies with better realized Sharpe because they avoid catastrophic drawdowns.

**9. ML return forecasts as Black-Litterman views (if time permits)**
Train a gradient-boosting model on rolling returns/factors, use predictions as BL "views" to tilt the optimizer toward predicted outperformers. Reference: Gouldh/ML-Portfolio-Optimization.

**10. Volatility-spike mean reversion (tactical layer)**
CarterT27's IMC team used 3-sigma spike detection on 10-bar windows to fade extreme moves. This could be added as a tactical overlay on top of PAMR weights during extreme market events.

### Implementation Priority Order

```
Priority 1 (must have):
  - PAMR baseline implementation with K-fold CV parameter search
  - ADF test for asset selection/weighting
  - Sharpe ratio as selection metric

Priority 2 (high value):
  - Ledoit-Wolf shrinkage covariance
  - Benchmark comparison: equal-weight, CRP, MVO max-Sharpe
  - Walk-forward validation (not just in-sample)

Priority 3 (if time):
  - HRP as alternative/ensemble component
  - ML return forecasts as BL views
  - CVaR optimization via Riskfolio-Lib or skfolio
```

### Libraries to Install

```
pip install PyPortfolioOpt riskfolio-lib skfolio statsmodels scipy cvxpy
```

Or for online portfolio selection:
```
pip install universal-portfolios  # Marigold's library
```

---

## Sources

- https://github.com/John-Trager/UChicago-Trading-Competition
- https://github.com/zaranip/Chicago-Trading-Competition-2024
- https://github.com/coolkite/Chicago-Trading-Competition-2024
- https://github.com/ACquantclub/UChicago-Trading-Competition-2024
- https://github.com/ACquantclub/UChicago-Trading-Competition-2021
- https://github.com/gurish165/UChicago-Trading-Competition
- https://github.com/stormsurfer98/uchicago-trading
- https://github.com/Icyviolet23/UChicagoTrading
- https://github.com/ericcccsliu/imc-prosperity-2
- https://github.com/CarterT27/imc-prosperity-3
- https://github.com/jmerle/imc-prosperity-2
- https://github.com/nmishra459/Jane-Street-FTTP-ETC
- https://github.com/robertmartin8/PyPortfolioOpt
- https://github.com/dcajasn/Riskfolio-Lib
- https://github.com/skfolio/skfolio
- https://github.com/convexfi/riskparity.py
- https://github.com/Gouldh/ML-Portfolio-Optimization
- https://github.com/Marigold/universal-portfolios
- https://github.com/nglahani/Online-Quantitative-Trading-Strategies
- https://github.com/ACM-Research/online-portfolio-selection
- https://baumohl.dev/blog/chicago-competition/
