# Batch 3 Strategy Results (S11–S15)

Backtest: 4-year train / 1-year pseudo-holdout
Baseline (equal-weight 1/N restored to submission.py): Sharpe ~+1.00, Return ~+15%, TxnCosts ~0.03%
Note: submission.py was previously S3 ERC (Sharpe +0.9300) at session start. Equal-weight baseline = Sharpe +0.9963.

---

## S11: HRP (Hierarchical Risk Parity)

**Implementation:**
- Ledoit-Wolf covariance, trailing 252-day window
- Distance matrix: `sqrt((1 - corr) / 2)`
- Hierarchical clustering with `scipy.cluster.hierarchy` (single linkage)
- Recursive bisection: allocates risk by inverse-vol-weighted cluster variance
- Long-only, recomputed every 5 days

**Results:**
| Metric | Value |
|--------|-------|
| Annualized Sharpe | +1.0021 |
| Total Return | +15.72% |
| Total Txn Costs | 0.7974% |
| Max Drawdown | -20.48% |

**Assessment:** At par with baseline. High txn costs (0.80%) from HRP changing weights frequently at rebalance points — even with 5-day caching. The equal-weight-like distribution doesn't leverage sector alpha. Not compelling vs simpler strategies.

---

## S12: Vol-Managed Inverse Volatility

**Implementation:**
- Base: inverse volatility weights (trailing 252-day window per asset)
- Overlay: scale total exposure by `target_vol / realized_vol_20d`
- `target_vol` = median of rolling 20-day vols over training period
- Caps total gross exposure at 1.0
- Recomputed every 5 days

**Results:**
| Metric | Value |
|--------|-------|
| Annualized Sharpe | +1.0977 |
| Total Return | +15.36% |
| Total Txn Costs | 0.0648% |
| Max Drawdown | -17.79% |

**Assessment:** Best Sharpe of the batch. Very low transaction costs (0.06%) due to slow-moving vol scaling. The vol overlay reduces exposure during high-vol regimes, cutting drawdown. This is the strongest new strategy from batch 3.

---

## S13: Cost-Aware Mean-Variance

**Implementation:**
- Ledoit-Wolf covariance + trailing 252-day mean returns
- Objective: `-w'mu + lambda*w'Sigma*w + tc * sum(spread * |w - w_old|) + borrow_penalty`
- Parameters: lambda=1.5, tc=15 (turnover penalty)
- Bounds: [-0.15, 0.15] per asset, gross <= 1
- L-BFGS-B optimizer, recomputed every 5 days
- Two parameter sets tested: (lam=2.0, tc=30) and (lam=1.5, tc=15) — same result

**Results:**
| Metric | Value |
|--------|-------|
| Annualized Sharpe | +0.9963 |
| Total Return | +15.07% |
| Total Txn Costs | 0.0290% |
| Max Drawdown | -17.87% |

**Assessment:** Slightly below baseline Sharpe but very low costs (0.03%). Mean-return signal is noisy over 252 days — mu has low predictive power, so the MV optimizer mostly finds a near-equal solution. The borrow penalty suppresses shorts, so this essentially acts like a constrained long-only. Not compelling given S12 beats it clearly.

---

## S14: Sector-Tilted Minimum Variance

**Implementation:**
- Minimum variance (Ledoit-Wolf cov) with sector-based per-asset upper bounds:
  - Sectors 3, 4 (A04,A09,A11,A19,A23 / A05,A06,A17,A21,A24): ub = 0.12
  - Sector 0 (A01,A07,A12,A15,A18): ub = 0.05
  - Sectors 1, 2: ub = 0.01
- SLSQP optimizer, sum(w)=1, long-only
- Recomputed every 5 days

**Results (final tuned version):**
| Metric | Value |
|--------|-------|
| Annualized Sharpe | +1.0542 |
| Total Return | +17.05% |
| Total Txn Costs | 0.0915% |
| Max Drawdown | -18.74% |

**First attempt (looser bounds: s3/4=0.10, s0=0.05, s1/2=0.02) results:** Sharpe +0.9781
**Tuned (s3/4=0.12, s1/2=0.01):** Sharpe +1.0542, higher return (+17.05%)

**Assessment:** Sector tilting with tight constraints on bad sectors materially improves performance. The strategy forces concentration in high-Sharpe sectors 3 and 4 while keeping diversification within those sectors. Highest absolute return of the batch.

---

## S15: Adaptive Allocation (Regime-Aware)

**Implementation:**
- Trailing 63-day realized vol of equal-weight portfolio for regime detection
- `vol_median` calibrated from training data (rolling 63-day vols)
- Defensive (vol > median): minimum variance (15% cap per asset)
- Aggressive (vol <= median): inverse volatility weights
- Multiple variants tested: with blend (0.8/0.2), no blend, different blend ratios
- Recomputed every 5 days

**Results across variants:**
| Variant | Sharpe | Return | MaxDD | TxnCosts |
|---------|--------|--------|-------|----------|
| Blend 0.8/0.2 w_old + 0.2 w_new | +0.8790 | +12.82% | -16.03% | 0.1708% |
| Blend 0.7/0.3 | +0.8441 | +12.24% | -14.90% | 0.1116% |
| No blend | +0.9326 | +13.80% | -16.00% | 0.1747% |

**Assessment:** Underperforms baseline. The regime-switching between MinVar and InvVol doesn't clearly outperform either strategy alone in this period. The 63-day vol signal may not be a reliable regime indicator in this dataset. Higher transaction costs from strategy switching. Not recommended.

---

## Summary Rankings (by Sharpe)

| Rank | Strategy | Sharpe | Return | MaxDD | TxnCosts |
|------|----------|--------|--------|-------|----------|
| 1 | **S12: Vol-Managed InvVol** | **+1.0977** | +15.36% | -17.79% | 0.06% |
| 2 | S14: Sector-Tilted MinVar | +1.0542 | +17.05% | -18.74% | 0.09% |
| 3 | S11: HRP | +1.0021 | +15.72% | -20.48% | 0.80% |
| 4 | S13: Cost-Aware MV | +0.9963 | +15.07% | -17.87% | 0.03% |
| 5 | S15: Adaptive (no blend) | +0.9326 | +13.80% | -16.00% | 0.17% |
| ref | Baseline (S3 ERC) | +0.9300 | +13.77% | -17.08% | 0.05% |

## Key Takeaways

1. **S12 is the best from this batch** — vol-managed inverse vol with very low costs and best Sharpe.
2. **S14 with tight sector tilts** delivers highest absolute return (+17%) by concentrating in sectors 3/4.
3. **HRP has high txn costs** despite 5-day caching — the recursive bisection produces volatile weights.
4. **Mean-return signals are weak** — S13 MV barely beats baseline because mu is noisy over 252 days.
5. **Regime switching doesn't help here** — equal-vol distribution of regimes, or signal too slow.

## Recommendations for Next Strategies

- Combine S12's vol-overlay with S14's sector tilts (sector-tilted vol-managed InvVol)
- Try momentum-based sector rotation (trailing 3-month return ranking to weight sectors)
- Explore shrinking mu toward zero more aggressively in S13 (use Black-Litterman or return signal filtering)
- S14: test even tighter restrictions (sectors 1,2 = 0.001, force all weight to sectors 3+4)
