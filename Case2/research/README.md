# Case 2: Portfolio Optimization Research

## Objective
Maximize annualized Sharpe ratio on a hidden 12-month holdout period.
**Deadline: April 9, 2026, 11:59 PM CST**

## Problem Summary
- 25 assets across 5 sectors
- 5 years of intraday tick data (30 ticks/day, 252 trading days/year = 37,800 ticks)
- Daily rebalancing: output weight vector each day given all price history so far
- Gross exposure constraint: sum(|w_i|) <= 1
- Shorting allowed (incurs borrow cost)
- Transaction costs: linear (half-spread * |delta_w|) + quadratic (2.5 * spread * delta_w^2)
- Scoring: annualized Sharpe = sqrt(252) * mean(daily_returns) / std(daily_returns)

## Data Files
- `prices.csv` — 37,800 ticks x 25 assets, all starting at 100
- `meta.csv` — per-asset: sector_id (0-4), spread_bps (2-12), borrow_bps_annual (23-197)

## Evaluation
- `python validate.py` — 4yr train / 1yr holdout
- `python validate.py --cv` — 3-fold expanding-window cross-validation
- Baseline equal-weight: Sharpe ~1.00

## Runtime Constraints
- Python 3.12 only
- Only NumPy, pandas, scikit-learn, SciPy available
- Must not crash or produce NaN/Inf weights
- Code in `submission.py`, entry point is `create_strategy()` returning a `StrategyBase` subclass

## Research Areas
Each area has its own file in this directory.

| File | Topic |
|------|-------|
| `01_data_exploration.md` | Statistical properties of the 25 assets |
| `02_cost_analysis.md` | Transaction cost and borrow cost modeling |
| `03_risk_models.md` | Covariance estimation, shrinkage, factor models |
| `04_alpha_signals.md` | Return prediction: momentum, mean reversion, cross-asset |
| `05_portfolio_construction.md` | Optimization methods: risk parity, mean-variance, etc. |
| `06_strategy_candidates.md` | Concrete strategies to implement and test |
| `07_backtest_results.md` | Results from validate.py for each strategy iteration |

## Workflow
1. Explore data thoroughly (sector structure, correlations, return distributions)
2. Understand cost structure (which assets are cheap/expensive to trade and short)
3. Build risk model (covariance estimation)
4. Identify alpha signals (what predicts returns?)
5. Construct portfolio (combine risk model + signals + constraints)
6. Backtest and iterate
7. Final submission = best performing strategy on CV
