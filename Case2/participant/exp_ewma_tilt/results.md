# Tilt Target Experiment Results

Date: experiment run
Current best: CV Mean=+2.160, Min=+2.090 (baseline raw tick_mu/tick_std, alpha=0.02)

## Quick Screen (single fold, train yr 0-3, test yr 4)

| Rank | Config | Sharpe | Blown |
|------|--------|--------|-------|
| 1 | baseline_a0.02 | +2.0901 |  |
| 2 | tstat_a0.02 | +2.0901 |  |
| 3 | winsor_a0.02 | +2.0901 |  |
| 4 | tstat_a0.03 | +2.0875 |  |
| 5 | baseline_a0.03 | +2.0875 |  |
| 6 | winsor_a0.03 | +2.0875 |  |
| 7 | baseline_a0.01 | +2.0785 |  |
| 8 | tstat_a0.01 | +2.0785 |  |
| 9 | winsor_a0.01 | +2.0785 |  |
| 10 | ewma_hl252_a0.01 | +2.0434 |  |
| 11 | ewma_hl252_a0.02 | +2.0422 |  |
| 12 | ewma_hl252_a0.03 | +2.0403 |  |
| 13 | recent_120d_a0.01 | +2.0389 |  |
| 14 | recent_120d_a0.02 | +2.0305 |  |
| 15 | ewma_hl120_a0.01 | +2.0220 |  |
| 16 | recent_120d_a0.03 | +2.0185 |  |
| 17 | ewma_hl60_a0.01 | +2.0071 |  |
| 18 | ewma_hl120_a0.02 | +1.9997 |  |
| 19 | ewma_hl120_a0.03 | +1.9769 |  |
| 20 | ewma_hl60_a0.02 | +1.9671 |  |
| 21 | recent_504d_a0.01 | +1.9333 |  |
| 22 | ewma_hl60_a0.03 | +1.9242 |  |
| 23 | recent_252d_a0.01 | +1.9003 |  |
| 24 | recent_504d_a0.02 | +1.7801 |  |
| 25 | recent_252d_a0.02 | +1.7051 |  |
| 26 | recent_504d_a0.03 | +1.6071 |  |
| 27 | recent_252d_a0.03 | +1.4866 |  |
| 28 | rank_a0.01 | -0.1113 |  |
| 29 | rank_a0.02 | -0.1113 |  |
| 30 | rank_a0.03 | -0.1113 |  |

## Full 3-Fold CV (top configs)

| Rank | Config | Mean | Std | Min | Fold 1 | Fold 2 | Fold 3 |
|------|--------|------|-----|-----|--------|--------|--------|
| 1 | baseline_a0.02 | +2.1596 | 0.0602 | +2.0901 | +2.1933 | +2.1956 | +2.0901 |
| 2 | winsor_a0.02 | +2.1596 | 0.0602 | +2.0901 | +2.1933 | +2.1956 | +2.0901 |
| 3 | tstat_a0.02 | +2.1596 | 0.0602 | +2.0901 | +2.1933 | +2.1956 | +2.0901 |
| 4 | tstat_a0.03 | +2.1370 | 0.0479 | +2.0875 | +2.1401 | +2.1832 | +2.0875 |
| 5 | baseline_a0.03 | +2.1370 | 0.0479 | +2.0875 | +2.1401 | +2.1832 | +2.0875 |

## Conclusion

Best variant: **baseline_a0.02** with CV Mean=+2.1596, Min=+2.0901
This is -0.0004 vs current best (no improvement).

### Tilt Variants Tested

- **Baseline**: raw tick_mu / tick_std (current implementation)
- **EWMA**: exponentially weighted tick mean, halflives 60/120/252 days
- **Recent**: only use last K days of tick data (K=120/252/504)
- **Rank**: within sector, use rank 1-5 instead of raw SR
- **T-stat**: tick_mu * sqrt(n) / tick_std (significance-weighted)
- **Winsorized**: clip tick_sr at +/-2 std within each sector

Alpha values tested: 0.01, 0.02, 0.03
