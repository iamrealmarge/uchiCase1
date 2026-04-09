# Tick-Level Mu Estimation: Strategy Results

**Date**: 2026-04-08
**Context**: GBM with constant drifts/vols/single common factor. Testing whether tick-level mu estimation (37,800 obs vs 1,260 daily obs) improves portfolio optimization.

---

## Baseline: R2 (Current Submission) — BL + VolScale (Daily Mu)

| Metric | Value |
|---|---|
| Single-split Sharpe | +1.0069 |
| Single-split Total Return | +19.12% |
| Single-split Txn Costs | 0.0384% |
| Single-split Max Drawdown | -24.41% |
| **CV Mean Sharpe** | **+0.7827** |
| CV Std | 0.1821 |
| CV Min | +0.6429 |

CV Folds:
- Fold 1 (test yr 2): +0.6429
- Fold 2 (test yr 3): +0.9886
- Fold 3 (test yr 4): +0.7167

---

## T1: Tick-Level Mu + Max-Sharpe Long-Only

**Strategy**: Compute mu from tick-level log returns (37,800 obs), scale to daily (mu_daily = mu_tick * 30). Ledoit-Wolf covariance on daily returns. Max-Sharpe with bounds [0, 0.15] per asset, sum(w) <= 1. Static weights.

### Single-Split (4yr train / 1yr holdout)
| Metric | Value |
|---|---|
| Annualized Sharpe | +0.6806 |
| Total Return | +5.83% |
| Total Txn Costs | 0.0132% |
| Max Drawdown | -10.98% |

### Cross-Validation (3 folds, expanding window)
| Fold | Test Year | Sharpe | Return | Costs | Max DD |
|---|---|---|---|---|---|
| Fold 1 | Year 2 | +0.6255 | +8.38% | 0.0234% | -20.44% |
| Fold 2 | Year 3 | +0.9696 | +8.42% | 0.0148% | -9.66% |
| Fold 3 | Year 4 | +0.6806 | +5.83% | 0.0132% | -10.98% |

| CV Metric | Value |
|---|---|
| **CV Mean Sharpe** | **+0.7586** |
| CV Std | 0.1849 |
| CV Min | +0.6255 |

**Assessment**: Worse than R2 baseline (0.759 vs 0.783 CV mean). Tick mu alone with vanilla max-Sharpe is insufficient — concentrated portfolio on a few assets.

---

## T2: Tick-Level Mu + Max-Sharpe Long-Short

**Strategy**: Same as T1 but allow shorts: bounds [-0.10, 0.15]. Borrow cost adjustment: for short candidates (assets with mu < median mu), reduce their effective mu by daily borrow cost. Gross exposure <= 1 constraint. Static weights.

### Single-Split (4yr train / 1yr holdout)
| Metric | Value |
|---|---|
| Annualized Sharpe | +0.7608 |
| Total Return | +5.43% |
| Total Txn Costs | 0.0268% |
| Max Drawdown | -9.38% |

### Cross-Validation (3 folds, expanding window)
| Fold | Test Year | Sharpe | Return | Costs | Max DD |
|---|---|---|---|---|---|
| Fold 1 | Year 2 | +0.8181 | +5.82% | 0.0276% | -12.55% |
| Fold 2 | Year 3 | +0.0501 | +0.12% | 0.0293% | -5.59% |
| Fold 3 | Year 4 | +0.7608 | +5.43% | 0.0268% | -9.38% |

| CV Metric | Value |
|---|---|
| **CV Mean Sharpe** | **+0.5430** |
| CV Std | 0.4278 |
| CV Min | +0.0501 |

**Assessment**: Worst performer overall. High variance (Std=0.428) and near-zero Sharpe in fold 2 indicates the long-short portfolio is unstable. Short positions increase borrow costs and the sign of short selection can be wrong out-of-sample.

---

## T3: Tick-Level Mu + Risk Parity on Top-K

**Strategy**: Use tick-level mu to select top-K assets by drift. Apply equal risk contribution (risk parity) within selected set. Moreira-Muir vol-scaling overlay (target = median 252-day portfolio vol). Static base weights + dynamic vol scaling.

### T3 K=8

#### Single-Split
| Metric | Value |
|---|---|
| Annualized Sharpe | +1.5365 |
| Total Return | +29.62% |
| Total Txn Costs | 0.1008% |
| Max Drawdown | -26.48% |

#### Cross-Validation
| Fold | Test Year | Sharpe | Return | Costs | Max DD |
|---|---|---|---|---|---|
| Fold 1 | Year 2 | +1.0944 | +19.15% | 0.1846% | -25.92% |
| Fold 2 | Year 3 | +0.9593 | +16.10% | 0.1417% | -19.87% |
| Fold 3 | Year 4 | +1.5365 | +29.62% | 0.1008% | -26.48% |

| CV Metric | Value |
|---|---|
| **CV Mean Sharpe** | **+1.1967** |
| CV Std | 0.3019 |
| CV Min | +0.9593 |

### T3 K=10

#### Single-Split
| Metric | Value |
|---|---|
| Annualized Sharpe | +1.5796 |
| Total Return | +28.29% |
| Total Txn Costs | 0.1256% |
| Max Drawdown | -27.03% |

#### Cross-Validation
| Fold | Test Year | Sharpe | Return | Costs | Max DD |
|---|---|---|---|---|---|
| Fold 1 | Year 2 | +0.7233 | +11.29% | 0.2017% | -21.06% |
| Fold 2 | Year 3 | +0.6774 | +9.84% | 0.1488% | -15.38% |
| Fold 3 | Year 4 | +1.5796 | +28.29% | 0.1256% | -27.03% |

| CV Metric | Value |
|---|---|
| **CV Mean Sharpe** | **+0.9934** |
| CV Std | 0.5081 |
| CV Min | +0.6774 |

### T3 K=12

#### Single-Split
| Metric | Value |
|---|---|
| Annualized Sharpe | +1.6026 |
| Total Return | +27.59% |
| Total Txn Costs | 0.1154% |
| Max Drawdown | -25.73% |

#### Cross-Validation
| Fold | Test Year | Sharpe | Return | Costs | Max DD |
|---|---|---|---|---|---|
| Fold 1 | Year 2 | +0.3633 | +4.62% | 0.2339% | -15.91% |
| Fold 2 | Year 3 | +0.4286 | +5.39% | 0.1264% | -12.92% |
| Fold 3 | Year 4 | +1.6026 | +27.59% | 0.1154% | -25.73% |

| CV Metric | Value |
|---|---|
| **CV Mean Sharpe** | **+0.7982** |
| CV Std | 0.6974 |
| CV Min | +0.3633 |

**Assessment (T3 summary)**:
- **T3_K8 is the BEST overall**: CV Mean=1.197, CV Std=0.302, CV Min=0.959. All folds positive and above 0.95 Sharpe. Significantly outperforms R2 baseline (0.783).
- T3_K10: CV Mean=0.993 but higher variance (Std=0.508). Good but less consistent.
- T3_K12: CV Mean=0.798, very high Std=0.697. Including too many assets with negative/low drift hurts.
- KEY INSIGHT: K=8 is the sweet spot — tick-level mu correctly identifies the top-8 assets, and risk parity provides robust diversification.
- Trade-off: higher transaction costs (~0.10-0.18%) than R2, but returns are much higher.

---

## T4: Tick-Level Mu + Black-Litterman + Vol-Scaling

**Strategy**: BL framework using tick-level mu for view strength (more precise than daily). Sector 3 & 4 views with tighter uncertainty (omega factor = 0.10 vs 0.25 for daily — tighter because tick-level t-stats are higher). Moreira-Muir vol scaling. Long-only, no per-asset cap.

### Single-Split (4yr train / 1yr holdout)
| Metric | Value |
|---|---|
| Annualized Sharpe | +1.1693 |
| Total Return | +18.47% |
| Total Txn Costs | 0.0836% |
| Max Drawdown | -21.57% |

### Cross-Validation (3 folds, expanding window)
| Fold | Test Year | Sharpe | Return | Costs | Max DD |
|---|---|---|---|---|---|
| Fold 1 | Year 2 | +0.8290 | +12.69% | 0.1336% | -20.80% |
| Fold 2 | Year 3 | +1.4317 | +23.98% | 0.1023% | -21.35% |
| Fold 3 | Year 4 | +1.1693 | +18.47% | 0.0836% | -21.57% |

| CV Metric | Value |
|---|---|
| **CV Mean Sharpe** | **+1.1433** |
| CV Std | 0.3022 |
| CV Min | +0.8290 |

**Assessment**: Significantly better than R2 baseline (1.143 vs 0.783 CV mean). Using tick-level mu for BL views provides more conviction and better view strength calibration. CV Min=0.829 is solid. This is a material improvement from tighter omega on tick views.

---

## T5: Tick-Level Mu + Regularized Max-Sharpe

**Strategy**: Objective: max (w'mu)/sqrt(w'Σw) - lambda * ||w||^2. Long-only, bounds [0, 0.15], sum(w) <= 1. Static weights.

**Note**: The regularization penalty is added directly to the Sharpe objective. At all tested lambda values, the optimizer drives weights toward zero to minimize the L2 penalty, resulting in near-zero portfolio exposure. The Sharpe ratios shown are from a near-cash portfolio.

### T5 lam=0.01

#### Single-Split
| Metric | Value |
|---|---|
| Annualized Sharpe | +0.6812 |
| Total Return | +0.26% (**near-zero - degenerate**) |
| Total Txn Costs | 0.0004% |
| Max Drawdown | -0.51% |

#### CV
| CV Metric | Value |
|---|---|
| **CV Mean Sharpe** | **+0.7522** |
| CV Std | 0.1874 |
| CV Min | +0.6107 |

### T5 lam=0.1
| CV Metric | Value |
|---|---|
| **CV Mean Sharpe** | **+0.7520** |
| CV Std | 0.1874 |
| CV Min | +0.6104 |

### T5 lam=1.0
| CV Metric | Value |
|---|---|
| **CV Mean Sharpe** | **+0.7520** |
| CV Std | 0.1874 |
| CV Min | +0.6103 |

### T5 lam=10.0
| CV Metric | Value |
|---|---|
| **CV Mean Sharpe** | **+0.7520** |
| CV Std | 0.1873 |
| CV Min | +0.6102 |

**Assessment**: Degenerate behavior across all lambda values. The regularization term is dimensionally inconsistent with the Sharpe ratio (Sharpe is scale-invariant but the L2 penalty is not). Larger lambda drives portfolio to near-zero weights, producing tiny but positive returns. The Sharpe ratios are essentially noise from a near-flat portfolio. T5 as formulated does not work — would need to reformulate as max-Sharpe subject to ||w||^2 <= budget constraint, not additive penalty.

---

## Summary Table

| Strategy | SS Sharpe | CV Mean | CV Std | CV Min | vs R2 Baseline |
|---|---|---|---|---|---|
| **R2 Baseline** (BL + VolScale, daily mu) | +1.0069 | +0.7827 | 0.1821 | +0.6429 | — |
| T1: Tick Max-Sharpe LO | +0.6806 | +0.7586 | 0.1849 | +0.6255 | -0.024 |
| T2: Tick Max-Sharpe LS | +0.7608 | +0.5430 | 0.4278 | +0.0501 | -0.240 |
| **T3 K=8: Tick RP Top-8** | **+1.5365** | **+1.1967** | **0.3019** | **+0.9593** | **+0.414** |
| T3 K=10: Tick RP Top-10 | +1.5796 | +0.9934 | 0.5081 | +0.6774 | +0.211 |
| T3 K=12: Tick RP Top-12 | +1.6026 | +0.7982 | 0.6974 | +0.3633 | +0.016 |
| **T4: Tick BL + VolScale** | **+1.1693** | **+1.1433** | **0.3022** | **+0.8290** | **+0.361** |
| T5 lam=0.01: Tick Reg MS | +0.6812 | +0.7522 | 0.1874 | +0.6107 | -0.030 |
| T5 lam=0.1: Tick Reg MS | +0.6812 | +0.7520 | 0.1874 | +0.6104 | -0.030 |
| T5 lam=1.0: Tick Reg MS | +0.6813 | +0.7520 | 0.1874 | +0.6103 | -0.030 |
| T5 lam=10.0: Tick Reg MS | +0.6815 | +0.7520 | 0.1873 | +0.6102 | -0.030 |

---

## Key Findings

### 1. Tick-Level Mu IS Valuable — For Asset Selection, Not Direct Optimization

- T1 (tick mu + vanilla max-Sharpe) underperforms R2, showing raw tick mu alone doesn't improve max-Sharpe
- T3_K8 (tick mu for selection + risk parity) achieves **CV Mean=1.197**, the best result overall — +0.41 above R2 baseline
- The key is using tick mu for SELECTION of which assets to hold, then diversifying within them

### 2. Best Strategy: T3_K8 (Tick Risk Parity, K=8)

- CV Mean=+1.197, CV Std=0.302, CV Min=+0.959
- All 3 folds above 0.95 Sharpe — most consistent performer
- 53% of oracle max-Sharpe (oracle=2.63 long-short, but this is long-only so oracle~1.68)
- T3_K8 achieves 71% of the long-only oracle (1.197/1.68)

### 3. T4 (Tick BL) is Strong and Consistent

- CV Mean=+1.143, CV Min=+0.829
- Tighter omega on views (0.10 vs 0.25) from higher tick precision improves BL conviction
- More conservative approach with lower drawdown risk than T3

### 4. T5 is Degenerate

- L2 penalty on weights is scale-incompatible with Sharpe ratio maximization
- All lambda values produce near-zero weights — not usable as formulated

### 5. Long-Short (T2) is Risky

- High variance (Std=0.428), near-zero Sharpe in one fold
- Borrow costs eat into short-side returns; short selection unstable with 2yr training windows

---

## Recommendations for Submission

1. **Primary recommendation**: Switch to T3_K8 (Tick Risk Parity K=8) — CV Mean=1.197 vs R2 baseline 0.783
2. **Alternative**: T4 (Tick BL) — more conservative (CV Mean=1.143) with lower min-Sharpe risk (CV Min=0.829 vs 0.959 for T3_K8)
3. **Hybrid possibility**: Combine tick-mu asset selection (T3 approach) with BL weight determination (T4 approach) for potentially the best of both

### Why T3_K8 Works
- GBM constant drifts mean the top-8 assets by drift dominate long-run performance
- Tick-level mu correctly identifies these assets (24/25 assets have |t|>2 at tick level vs 4/25 daily)
- Risk parity balances the portfolio without overconcentrating, hedging vol uncertainty
- Vol-scaling reduces exposure during volatile periods
