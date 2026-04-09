# Strategy Candidates for Case 2

## Research Synthesis

Key constraints from research:
- **Transaction costs dominate** — daily rebalancing costs 300% of returns
- **No strong alpha signals** — momentum IC = 0.013, mean reversion weak
- **Sectors 3 & 4 massively outperform** (Sharpe 0.82, 0.77 vs ~0 for sectors 1, 2)
- **A09 is the star** (Sharpe 1.41, low costs)
- **PAMR won in 2024** but on 6 assets with no costs — needs heavy adaptation
- **HRP + Ledoit-Wolf** is the recommended risk-model approach
- **Vol-scaling** adds ~25% Sharpe improvement

## Candidate Strategies (ordered by expected performance)

### Strategy A: Cost-Dampened PAMR
- PAMR core with `eps=0.5, C=500`
- Add exponential blending: `w_new = alpha * w_pamr + (1-alpha) * w_old` (alpha ~0.1-0.3)
- Only rebalance when total turnover exceeds threshold
- Cap max weight at 0.10 for 25 assets
- Long-only (avoid borrow costs entirely)
- **Risk:** May still have too much turnover; PAMR designed for mean reversion which is weak here

### Strategy B: Sector-Tilted Risk Parity
- Ledoit-Wolf covariance estimation on trailing 252-day window
- Risk parity (equal risk contribution) allocation
- Overweight sectors 3 & 4 by 2x, underweight sectors 1 & 2 by 0.5x
- Rebalance only when max weight drift > 2%
- Vol-scale total exposure by inverse realized vol
- **Risk:** Sector outperformance may not persist in holdout

### Strategy C: Smart Static + Vol Scaling
- Compute trailing 252-day Sharpe per asset
- Allocate proportional to positive Sharpe (zero weight for negative Sharpe assets)
- Diversify within using inverse-volatility weighting
- Moreira-Muir vol scaling (scale all positions by target_vol / realized_vol)
- Rebalance monthly (every 21 days) only
- **Risk:** Very low turnover = very low cost, but may miss regime changes

### Strategy D: HRP with Momentum Tilt
- Hierarchical Risk Parity using Ledoit-Wolf covariance
- Sector-aware distance metric
- Light 60-day momentum tilt (overweight recent winners)
- Transaction cost penalty in rebalancing decision
- **Risk:** HRP may spread weight too evenly including bad assets

### Strategy E: Ensemble
- Equal-weight blend of strategies A, B, C, D
- Or: pick best 2 from CV and blend those
- Reduces single-strategy risk

## Implementation Plan

1. Build all 4 standalone strategies (A-D) in parallel
2. Run `validate.py` and `validate.py --cv` on each
3. Compare Sharpe, max drawdown, turnover, total costs
4. Build ensemble of top 2-3
5. Submit best performer

## Key Implementation Details

- All weights must satisfy: sum(|w_i|) <= 1.0
- `get_weights(price_history, meta, day)` receives ALL history including train + holdout so far
- `fit(train_prices, meta)` is called once with training data
- Transaction costs are computed on weight CHANGES, so stability = free money
- The evaluator projects to L1 ball if violated (but better to do it ourselves)
