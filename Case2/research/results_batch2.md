# Batch 2 Strategy Results

**Date:** 2026-04-08
**Evaluator:** 4-year train / 1-year pseudo-holdout split
**Baseline (equal-weight):** Sharpe +0.98, Total Return +14.79%, Max DD -17.83%, Txn Costs 0.0452%

---

## Summary Table

| Strategy | Sharpe | Total Return | Max Drawdown | Txn Costs | vs Baseline |
|----------|--------|-------------|--------------|-----------|-------------|
| Baseline (equal-weight) | +0.98 | +14.79% | -17.83% | 0.0452% | — |
| S6: Cross-Sectional Momentum (60d) | -0.47 | -3.06% | -8.89% | 1.3206% | WORSE |
| S7: Short-Term Reversal (5d) | -3.69 | -23.43% | -23.13% | 4.9479% | MUCH WORSE |
| S8: Combined Momentum + Reversal | -1.17 | -10.73% | -10.57% | 4.3967% | WORSE |
| S9: Sector Rotation | **+1.04** | **+15.41%** | -18.65% | 0.7469% | **BETTER** |
| S10: PCA Residual Mean Reversion | -1.58 | -18.29% | -22.71% | 7.7257% | MUCH WORSE |

---

## Strategy Details

### S6: Cross-Sectional Momentum (60-day)
- **Sharpe:** -0.4739
- **Total Return:** -3.06%
- **Max Drawdown:** -8.89%
- **Txn Costs:** 1.3206%
- **Notes:** 60-day momentum signal with rank-based weighting. Long top 10, short bottom 5. Gross target 0.8. The strategy loses money — this dataset does not reward 60-day cross-sectional momentum, suggesting mean reversion dominates at this horizon. Transaction costs 29x baseline from daily rebalancing.

### S7: Short-Term Reversal (5-day)
- **Sharpe:** -3.6864
- **Total Return:** -23.43%
- **Max Drawdown:** -23.13%
- **Txn Costs:** 4.9479%
- **Notes:** Worst performer of the batch. Long recent losers, short recent winners over 5-day window. Very high transaction costs (110x baseline) from daily rebalancing with frequent position turnover. The 5-day reversal signal either doesn't hold in this dataset or is completely consumed by costs.

### S8: Combined Momentum + Reversal (50/50 blend)
- **Sharpe:** -1.1746
- **Total Return:** -10.73%
- **Max Drawdown:** -10.57%
- **Txn Costs:** 4.3967%
- **Notes:** Z-scored combination of 60-day momentum and inverse 5-day reversal. Blending two negative signals predictably produces a negative combined signal. High transaction costs from daily rebalancing drag performance further. The approach inherits the worst of both component strategies in this dataset.

### S9: Sector Rotation (63-day quarterly)
- **Sharpe:** +1.0442
- **Total Return:** +15.41%
- **Max Drawdown:** -18.65%
- **Txn Costs:** 0.7469%
- **Notes:** **Best performer of batch 2, beats baseline.** Top 2 sectors get 80% of allocation (40% each), middle sector gets 10%, bottom 2 sectors excluded. Within-sector inverse volatility weighting. Rebalances only when sector ranking changes — this dramatically reduces turnover vs daily rebalancers. Low transaction costs relative to momentum/reversal strategies. The sector-level signal with slow rebalancing aligns well with how this data is structured (5 sectors, 5 assets each, clear sector structure).

### S10: PCA Residual Mean Reversion
- **Sharpe:** -1.5786
- **Total Return:** -18.29%
- **Max Drawdown:** -22.71%
- **Txn Costs:** 7.7257%
- **Notes:** PCA with 3 components, 252-day fit window, 10-day cumulative residual z-score, entry/exit at ±1.5 sigma. Highest transaction costs of all strategies (171x baseline). The mean reversion signal either doesn't work in this dataset or the ±1.5 threshold generates too many trades. The cost-adjusted return is deeply negative.

---

## Key Takeaways

1. **Transaction costs are the dominant performance driver** for strategies with daily full rebalancing. S7, S8, S10 all have 4-8% annual costs vs 0.05% baseline.

2. **Sector Rotation (S9) is the only winner** because:
   - It rebalances only on rank changes (not daily), minimizing turnover
   - Sector-level aggregation smooths out noise
   - Inverse-vol weighting within sectors adds mild risk control
   - Long-only structure avoids borrow costs

3. **Cross-sectional momentum and short-term reversal both fail** on this dataset. Suggests the underlying assets may have significant mean-reversion properties at the daily level that punish momentum, combined with costs making reversal unviable.

4. **PCA residuals are a promising signal type but require much sparser trading** — entering/exiting only at high z-score thresholds (e.g., ±2.5 or ±3.0) and holding for days rather than rebalancing daily.

---

## Recommendations

- **Best strategy from this batch: S9 (Sharpe 1.04)**. Consider tuning: extend lookback to 126d, try rebalancing with minimum hold periods.
- Cross-batch winner to date: compare against batch 1 strategies.
- High-priority next experiments: S9 variant with minimum 5-day hold, PCA residual with wide thresholds (±2.5) and 5-day minimum hold.
