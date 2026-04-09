# Oracle Gap Decomposition Results

## Executive Summary

The "18% oracle gap" (CV Mean 2.160 vs Oracle 2.627) is **misleading**. The 2.627 is the in-sample theoretical maximum Sharpe using ALL 5 years of data (including future test periods). When the oracle (inv(cov)@mu) is trained on available data and applied out-of-sample, it gets **Sharpe 0.27-0.89** -- our BL strategy at **2.09-2.20** beats it by 2-8x.

The reason: max-Sharpe optimization amplifies mu estimation noise. With ~500-1000 daily observations and 25 assets, the inv(cov)@mu direction is dominated by noise. Our BL framework + constrained optimization + low gross exposure (~3%) is what makes us dramatically better than the naive oracle.

**We are at the practical information-theoretic ceiling for this problem.** Marginal tuning yields +0.003-0.004 Sharpe at most.

## Part 1: Oracle Gap Decomposition

### Per-Fold Comparison (static weights, no costs)

| Fold | Test Year | Oracle SR | Our SR | Gap   | Correlation |
|------|-----------|-----------|--------|-------|-------------|
| 1    | 2         | +0.798    | +2.062 | -1.26 | 0.609       |
| 2    | 3         | +0.269    | +2.305 | -2.04 | 0.587       |
| 3    | 4         | +0.887    | +2.271 | -1.38 | 0.754       |

Our strategy consistently OUTPERFORMS the oracle by 1.2-2.0 Sharpe points OOS.

### Full Backtest (with costs, vol scaling)

| Fold | Our Full Backtest | Oracle Full Backtest |
|------|-------------------|---------------------|
| 1    | +2.193            | +0.803              |
| 2    | +2.196            | +0.097              |
| 3    | +2.090            | +0.754              |

Oracle at gross=1 gets destroyed by transaction costs (0.097 in fold 2!).

### Sector vs Within-Sector Decomposition

The hybrid analysis comparing oracle sector allocation + our within-sector (and vice versa) shows:

| Fold | Hybrid1 (oracle sector, our within) | Hybrid2 (our sector, oracle within) |
|------|--------------------------------------|--------------------------------------|
| 1    | +0.670                               | +0.509                               |
| 2    | +2.353                               | +0.958                               |
| 3    | +2.188                               | +0.877                               |

**Key insight**: Both hybrid portfolios perform WORSE than our strategy (except hybrid1 in fold 2 which barely beats). This means our BL strategy's sector AND within-sector allocations are both superior to the oracle's when applied OOS. The oracle's allocations are noise-dominated.

## Part 2: Parameter Sensitivity Analysis

### Tilt Alpha
| Alpha | Mean   | Min    | Std   |
|-------|--------|--------|-------|
| 0.00  | +2.125 | +2.044 | 0.119 |
| 0.01  | +2.157 | +2.079 | 0.078 |
| 0.015 | +2.162 | +2.087 | 0.067 |
| 0.02  | +2.160 | +2.090 | 0.060 |
| 0.025 | +2.151 | +2.090 | 0.054 |
| 0.03  | +2.137 | +2.088 | 0.048 |
| 0.05  | +2.131 | +1.896 | 0.200 |

**Finding**: alpha=0.02 is near-optimal. alpha=0.015 gives marginally higher mean but higher variance. No significant improvement available.

### Tilt Signal Type (all at alpha=0.02)
| Signal      | Mean   | Min    |
|-------------|--------|--------|
| tick_sr     | +2.160 | +2.090 |
| daily_sr    | +1.909 | +1.243 |
| tick_mu     | +2.095 | +1.821 |
| daily_mu    | +2.133 | +1.965 |
| inv_vol     | +2.126 | +2.039 |
| clipped_sr  | +2.142 | +2.044 |

**Finding**: tick_sr is by far the best tilt signal. All alternatives are worse.

### Power Shrinkage Gamma
| Gamma | Mean   | Min    |
|-------|--------|--------|
| 0.80  | +2.112 | +1.976 |
| 0.90  | +2.115 | +1.991 |
| 0.95  | +2.160 | +2.090 |
| 0.97  | +2.161 | +2.091 |
| 1.00  | +2.162 | +2.093 |

**Finding**: gamma=1.00 (no power shrinkage) is marginally best (+0.003). Removing the power shrinkage step simplifies code with no downside.

### Vol Scaling Clip Range
| Range       | Mean   | Min    |
|-------------|--------|--------|
| [1.0, 1.0]  | +2.115 | +1.998 |
| [0.7, 1.3]  | +2.161 | +2.092 |
| [0.5, 1.5]  | +2.160 | +2.090 |
| [0.3, 2.0]  | +2.155 | +2.090 |

**Finding**: Vol scaling is worth +0.045 Sharpe. [0.7,1.3] is marginally best but difference from [0.5,1.5] is noise.

### Omega Parameters
| omega_sector | Mean   |  | omega_asset | Mean   |
|-------------|--------|--|-------------|--------|
| 0.0001      | +2.115 |  | 0.001       | +2.113 |
| 0.0005      | +2.115 |  | 0.005       | +2.114 |
| 0.001       | +2.115 |  | 0.010       | +2.115 |
| 0.005       | +2.111 |  | 0.020       | +2.114 |

**Finding**: omega parameters have near-zero sensitivity. The strategy is robust to omega changes.

### Best Combined Configuration
| Config | Mean   | Min    | Delta vs Baseline |
|--------|--------|--------|-------------------|
| BASELINE (g=0.95, t=0.02, v=[0.5,1.5]) | +2.160 | +2.090 | -- |
| g=1.00, t=0.018, v=[0.6,1.4] | +2.164 | +2.092 | +0.004 |
| g=1.00, t=0.015, v=[0.5,1.5] | +2.164 | +2.090 | +0.004 |
| g=1.00, t=0.020, v=[0.7,1.3] | +2.163 | +2.095 | +0.003 |

**All improvements are within +0.004 Sharpe -- essentially noise.**

## Part 3: Conclusions and Recommendations

### Why the gap is unclosable with this framework

1. **The 2.627 "oracle" is not an achievable OOS target.** It requires perfect future knowledge of mu. With 252-1000 daily observations, per-asset mu t-stats are 0.5-3.2 -- deep in the noise regime. The true achievable OOS Sharpe with BL is likely 2.1-2.2.

2. **BL regularization is near-optimal for this sample size.** DeMiguel et al. (2009) showed that for 25 assets, ~3000 months are needed for sample MV to beat 1/N. With 60 months, BL is the right framework and we're extracting most of the available signal.

3. **The parameter surface is flat.** Gamma, tilt alpha, vol scaling clip, omega -- all have near-zero marginal effect. This is the hallmark of a well-regularized strategy near its optimum.

### Actionable recommendations

1. **Consider removing power eigenvalue shrinkage** (set gamma=1.00). It simplifies code and gives +0.003 mean, +0.003 min. Low risk change.

2. **Do NOT increase tilt alpha.** alpha=0.02 is the sweet spot. Higher values increase variance dramatically (alpha=0.05 drops min to +1.896).

3. **Do NOT change omega parameters.** The strategy is insensitive to omega, meaning BL is working as intended -- views are dominating the prior.

4. **The only way to meaningfully close the gap is a fundamentally different approach** -- e.g., PyTorch end-to-end differentiable optimization, which bypasses BL entirely and could potentially learn the optimal static weights directly. This is the last untested major direction per HANDOFF.md.

5. **Current submission is competition-ready.** Mean=+2.167, Min=+2.103, Std=0.056 (verified via validate.py --cv).
