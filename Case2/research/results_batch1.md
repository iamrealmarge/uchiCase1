# Batch 1 Strategy Results

Backtest setup: 4-year train / 1-year pseudo-holdout split.
Baseline equal-weight Sharpe: ~1.0 (per competition spec).

## Results Table

| Strategy | Sharpe | Total Return | Max Drawdown | Total Txn Costs |
|----------|--------|-------------|--------------|-----------------|
| S1: Inverse Volatility | +0.9835 | +14.79% | -17.83% | 0.0452% |
| S2: Minimum Variance (Ledoit-Wolf) | +0.6074 | +8.31% | -13.65% | 0.1518% |
| S3: Risk Parity (ERC) | +0.9300 | +13.77% | -17.08% | 0.0482% |
| S4: Maximum Diversification | +0.7337 | +10.64% | -15.02% | 0.1366% |
| S5: Sharpe-Weighted Allocation | +0.8363 | +13.34% | -21.77% | 0.5837% |

## Implementation Notes

### S1: Inverse Volatility
- Trailing 252-day window of daily log returns (or all history if shorter)
- Weights = (1/vol_i) / sum(1/vol_j), long-only
- Recomputed daily, very low txn costs due to smooth weight evolution
- **Best Sharpe of the batch at 0.9835**, close to the ~1.0 baseline

### S2: Minimum Variance (Ledoit-Wolf)
- Ledoit-Wolf shrinkage covariance on trailing 252-day returns
- Constrained SLSQP: min w'Σw, sum(w)=1, w>=0
- Recalculated every 5 days to reduce compute
- Lower Sharpe (0.6074) with higher txn costs — concentrated positions churn

### S3: Risk Parity (ERC)
- Ledoit-Wolf covariance, ERC objective via SLSQP
- Minimize sum((RC_i - target_RC)^2) with lower bounds 1e-6
- Second-best Sharpe at 0.9300, low txn costs comparable to S1
- Better drawdown control than S1 (-17.08% vs -17.83%)

### S4: Maximum Diversification
- Maximize (w'sigma) / sqrt(w'Σw) via SLSQP with analytic gradient
- Ledoit-Wolf covariance, long-only, recalculated every 5 days
- Moderate Sharpe (0.7337), higher txn costs than S1/S3

### S5: Sharpe-Weighted Allocation
- Per-asset trailing 252-day Sharpe, zero-weight for negative Sharpe assets
- High txn costs (0.5837%) due to frequent rebalancing as Sharpe estimates shift
- Highest max drawdown (-21.77%) — concentration risk when few assets have positive Sharpe
- Weakest risk-adjusted performance in the batch

## Key Takeaways

1. **S1 (Inverse Vol) is the clear winner** among these 5 strategies on Sharpe alone
2. **S3 (Risk Parity)** is competitive and has slightly better drawdown control
3. Optimization-heavy strategies (S2, S4) suffer from higher txn costs due to more concentrated/unstable weights
4. S5 (Sharpe-weighted) has a turnover problem — Sharpe estimates fluctuate daily, causing high costs
5. None of the 5 strategies beat the equal-weight baseline (~1.0 Sharpe), suggesting the test period may favor diversification over tilts
6. Future directions: momentum overlays, sector-neutral constraints, lower rebalancing frequency for optimization strategies

## Backup File
- `/Users/stao042906/Documents/UCHICAGO/Case2/participant/submission_backup_s11.py` contains S11 (HRP) from another agent's run during testing
