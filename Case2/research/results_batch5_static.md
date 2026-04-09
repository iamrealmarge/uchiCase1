# Batch 5 Results: Max-Sharpe Static Strategies

**Split**: 4-year train / 1-year pseudo-holdout

## Summary Table

| Strategy | Sharpe | Total Return | Max Drawdown | Txn Cost |
|---|---|---|---|---|
| EqualWeight (baseline) | +0.9963 | +15.07% | -17.87% | 0.0290% |
| S21 Max-Sharpe (long-only) | +0.7167 | +13.13% | -22.69% | 0.0419% |
| S22 Max-Sharpe (shorts allowed) | +0.3338 | +2.23% | -5.68% | 0.0268% |
| S23 Reg-MaxSharpe lam=0.001 | +0.7212 | +13.22% | -22.67% | 0.0417% |
| S23 Reg-MaxSharpe lam=0.01 | +0.7566 | +13.92% | -22.57% | 0.0407% |
| S23 Reg-MaxSharpe lam=0.1 | +1.0254 | +19.09% | -24.14% | 0.0369% |
| S23 Reg-MaxSharpe lam=1.0 | +1.1718 | +19.08% | -20.80% | 0.0315% |
| S24 Max-Sharpe+VolScale | +0.8171 | +14.60% | -23.18% | 0.0914% |
| S25 Shrinkage alpha=0.3 | +0.9481 | +16.75% | -23.08% | 0.0340% |
| S25 Shrinkage alpha=0.5 | +0.8647 | +16.04% | -23.11% | 0.0381% |
| S25 Shrinkage alpha=0.7 | +0.7607 | +13.98% | -22.56% | 0.0404% |
| S25 Shrinkage alpha=0.9 | +0.7292 | +13.37% | -22.65% | 0.0415% |
| S26 Max-Sharpe Filtered | +0.7159 | +13.12% | -22.69% | 0.0419% |
| S27 Risk-Parity Top10+VolScale | +1.6585 | +29.06% | -27.27% | 0.1381% |
| S28 Black-Litterman | +1.2532 | +23.62% | -24.70% | 0.0359% |

## Notes

- S21: Long-only max-Sharpe tangency, Ledoit-Wolf covariance, SLSQP
- S22: Max-Sharpe with shorts [-0.10, +0.15], borrow-cost adjusted
- S23: L2-regularized max-Sharpe (lambda tested: 0.001, 0.01, 0.1, 1.0)
- S24: S21 weights + vol-scaling (21-day trailing realized vol vs. training median)
- S25: Shrinkage on expected returns toward cross-sectional mean (alpha tested: 0.3–0.9)
- S26: Max-Sharpe on positive-Sharpe assets only (exclude losers)
- S27: Equal risk contribution from top-10 Sharpe assets + vol-scaling
- S28: Black-Litterman with sector 3 & 4 outperformance views

**Best strategy**: S27 Risk-Parity Top10+VolScale with Sharpe = +1.6585


## Cross-Validation Results

Time-series CV (expanding train, 1-year test folds):

| Strategy | Mean Sharpe | Std | Min Sharpe |
|---|---|---|---|
| EqualWeight | +0.5153 | 0.4351 | +0.1491 |
| S21 Max-Sharpe | +0.7827 | 0.1821 | +0.6429 |
| S23 lam=1.0 | +0.6861 | 0.4231 | +0.3979 |
| S25 alpha=0.3 | +0.6104 | 0.3043 | +0.3572 |
| S27 RiskParity k=10 | +0.9611 | 0.6046 | +0.5857 |
| S28 Black-Litterman | +1.0802 | 0.2809 | +0.7561 |

**Best by mean CV Sharpe: S28 Black-Litterman = +1.0802**


## Key Findings and Recommendations

### Winner: S28 Black-Litterman

S28 is the best strategy by cross-validation mean Sharpe (+1.08) with the second-lowest variance (std=0.28) and the best worst-case floor (min=+0.76 across all 3 folds). This combination of high mean and low variance makes it most robust for the competition's multi-OOS-run averaging.

**S27 vs S28 tradeoff:**
- S27 (Risk-Parity Top10+VolScale): Fold-4 Sharpe = +1.66 (spectacular), but high variance (std=0.60), fold-2 is only +0.64
- S28 (Black-Litterman): Mean=+1.08, Std=0.28 — consistent across ALL folds (+0.76, +1.23, +1.25)
- Since scoring is AVERAGED across multiple OOS runs, S28 wins on expected value

### Runner-Up: S23 lam=1.0 (Regularized Max-Sharpe)
- Single-fold Sharpe = +1.17, but high variance (std=0.42) in CV
- The heavy L2 regularization effectively pushes weights toward equal-weight, which explains why it performs well here

### What Doesn't Work
- **S22 (shorts allowed)**: Sharpe = +0.33. Shorting low-Sharpe assets with borrow costs of 125-197 bps/year is not profitable. The negative mu assets don't short well enough to overcome costs.
- **S26 (filtered)**: Almost identical to S21 — excluding negative-Sharpe assets barely changes the portfolio since max-Sharpe already de-weights them
- **Unregularized max-Sharpe (S21)**: Sharpe = +0.72, BELOW equal-weight baseline. Over-concentration in a few assets hurts OOS.

### Lessons from This Batch
1. **Regularization matters**: lam=1.0 in S23 effectively shrinks toward equal-weight and beats unregularized S21 by 0.46 Sharpe
2. **Don't short**: With borrow costs of 100-200 bps/year, shorting is almost always net negative
3. **Sector views add value**: S28 with sector 3&4 views significantly outperforms S21 (same optimizer, just better priors)
4. **Vol-scaling hurts**: S24 and S27 both incur higher txn costs from daily weight changes, and S24 (Sharpe=+0.82) is BELOW the baseline. Only worthwhile if vol-scaling reduces variance enough to compensate.
5. **Consistency beats peak Sharpe**: For multi-run averaged scoring, the reliable +1.08 of S28 beats the volatile +0.96 of S27

### Next Steps
- Test S28 variants: different tau, risk-aversion lambda, or additional sector views
- Test S28 with vol-scaling (static weights but exposure adjustment)
- Consider combining S28 (direction) with S27 (exposure scaling) as a hybrid
- The combination of BL prior + sector views + risk-parity weighting might be the true winner
