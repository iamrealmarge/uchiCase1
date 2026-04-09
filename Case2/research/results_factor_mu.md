# Factor Model Mu Strategies — Results

Date: 2026-04-08
Baseline (R2, BL sector 3&4 views + Moreira-Muir vol-scaling): CV mean +1.1949 (verified)
  Fold 1: +0.8950, Fold 2: +1.3476, Fold 3: +1.3420, Std: 0.2597, Min: +0.8950
Oracle max-Sharpe: 2.63 long-short, 1.68 long-only

## Strategy Descriptions

All strategies use max-Sharpe optimization with long-only constraints.
The key innovation in each is the mu estimation method (alpha from factor models).

---

## F1: Factor Model Mu (PCA-based)

**Approach:**
- Compute PCA on daily returns, extract PC1 as market factor
- OLS: r_i(t) = alpha_i + beta_i * PC1(t) + e_i(t)
- Use alpha_i (market-noise-free) as mu for max-Sharpe
- LW covariance

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +0.7167
- Total return: +13.13%
- Max drawdown: -22.69%

**Cross-validation (3 folds, expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1    | year 2    | +0.5011 |
| 2    | year 3    | -0.0621 |
| 3    | year 4    | +1.3862 |

- **CV Mean: +0.6084**
- CV Std: 0.7301
- CV Min: -0.0621

**Assessment:** High variance across folds (fold 2 negative). Worse than R2 baseline.

---

## F2: Factor Model + Residual Covariance

**Approach:**
- Same PCA alpha as F1
- Structured covariance: cov = beta * beta' * var(F) + diag(var(e_i))
- Fewer parameters than LW, parsimonious representation

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +0.7241
- Total return: +13.36%
- Max drawdown: -23.31%

**Cross-validation (3 folds, expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1    | year 2    | +0.5258 |
| 2    | year 3    | +0.7019 |
| 3    | year 4    | +0.9730 |

- **CV Mean: +0.7336**
- CV Std: 0.2253
- CV Min: +0.5258

**Assessment:** Dramatically more stable than F1 (std drops from 0.73 to 0.23). All folds positive. The factor covariance reduces estimation noise and concentration risk. Strong improvement.

---

## F3: Sector Factor Model

**Approach:**
- Use sector-average return as the factor (instead of PC1)
- OLS: r_i(t) = alpha_i + beta_i * sector_avg_s(t) + e_i(t)
- Use alpha_i as mu, LW cov

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: -0.3279
- Total return: -7.85%
- Max drawdown: -19.81%

**Cross-validation (3 folds, expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1    | year 2    | +0.4333 |
| 2    | year 3    | -0.3745 |
| 3    | year 4    | -0.3279 |

- **CV Mean: -0.0897**
- CV Std: 0.4535
- CV Min: -0.3745

**Assessment:** Poor. Sector factors are less informative than PC1 for this dataset (all pairwise correlations ~0.23, no clean block structure). Alpha extraction is noisy.

---

## F4: Multi-Factor (PC1 + Sector Dummies)

**Approach:**
- OLS: r_i(t) = alpha_i + beta_mkt * PC1(t) + sum_s(gamma_s * sector_avg_s(t)) + e_i(t)
- Residual alpha after all systematic factors
- LW cov

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +0.6264
- Total return: +12.28%
- Max drawdown: -16.54%

**Cross-validation (3 folds, expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1    | year 2    | -0.3325 |
| 2    | year 3    | -0.1251 |
| 3    | year 4    | +0.6264 |

- **CV Mean: +0.0563**
- CV Std: 0.5045
- CV Min: -0.3325

**Assessment:** Poor. Over-parametrized: adding sector dummies to PC1 when correlations are all positive and there's no block structure just adds noise. Early folds (small training data) suffer most.

---

## F5: Factor Model with Tick-Level Estimation

**Approach:**
- Use tick-level returns (~37,800 obs) to estimate PC1 factor model
- OLS at tick level: r_i_tick(t) = alpha_i_tick + beta_i * PC1_tick(t) + e_i(t)
- Scale tick alpha to daily: alpha_daily = alpha_tick * 30
- Daily LW covariance for portfolio optimization

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +0.6798
- Total return: +12.36%
- Max drawdown: -22.71%

**Cross-validation (3 folds, expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1    | year 2    | +0.6327 |
| 2    | year 3    | +0.9756 |
| 3    | year 4    | +0.6798 |

- **CV Mean: +0.7627**
- CV Std: 0.1859
- CV Min: +0.6327

**Assessment:** Best stability so far (lowest std=0.1859, min=0.6327). All folds positive. 30x more data for alpha estimation helps denoise. Strong candidate.

---

## F6: Best Factor Model (F5) + Moreira-Muir Vol-Scaling

**Approach:**
- Base weights from F5 (tick-level PCA factor alpha + daily LW cov)
- Moreira-Muir (2017) vol-scaling:
  - Compute realized portfolio vol from rolling 21-day window
  - Scale weights: scale = target_vol / realized_vol (capped at 2x)
  - target_vol = daily std of in-sample portfolio returns
- Dynamic weights at each day based on recent volatility regime

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +0.7680
- Total return: +13.74%
- Max drawdown: -23.09%

**Cross-validation (3 folds, expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1    | year 2    | +0.6472 |
| 2    | year 3    | +1.0737 |
| 3    | year 4    | +0.7680 |

- **CV Mean: +0.8296**
- CV Std: 0.2198
- CV Min: +0.6472

**Assessment:** Best CV mean (+0.8296) and all folds positive. Vol-scaling adds ~0.07 CV mean over F5. Higher transaction costs (dynamic rebalancing) but Sharpe improvement outweighs. Top performer in this batch.

---

## Summary Table

| Strategy | Description | Single Sharpe | CV Mean | CV Std | CV Min |
|----------|-------------|---------------|---------|--------|--------|
| R2 (baseline) | BL sector 3&4 + vol-scaling | — | +1.1949 | 0.2597 | +0.8950 |
| F1 | PCA alpha + LW cov | +0.7167 | +0.6084 | 0.7301 | -0.0621 |
| F2 | PCA alpha + factor cov | +0.7241 | +0.7336 | 0.2253 | +0.5258 |
| F3 | Sector alpha + LW cov | -0.3279 | -0.0897 | 0.4535 | -0.3745 |
| F4 | Multi-factor alpha + LW cov | +0.6264 | +0.0563 | 0.5045 | -0.3325 |
| F5 | Tick-level PCA alpha + LW cov | +0.6798 | +0.7627 | 0.1859 | +0.6327 |
| **F6** | **F5 + Moreira-Muir vol-scaling** | **+0.7680** | **+0.8296** | **0.2198** | **+0.6472** |

---

## Key Findings

1. **Factor model alpha (removing PC1 market noise) does NOT beat R2 baseline in CV mean.** All F1-F6 peak at 0.8296 (F6) vs R2's 1.1949. R2 uses Black-Litterman with sector 3 & 4 views, which leverages more informative prior knowledge about which sectors have genuine positive alpha.

2. **F2 (factor cov) dramatically stabilizes F1**: reducing std from 0.73 to 0.23. The structured covariance with fewer parameters avoids the concentration risk from LW on the (noisy) alpha vector.

3. **Tick-level estimation (F5) improves stability** but not dramatically vs F2. The 30x more data helps denoise alpha, giving F5 the best CV min (+0.6327) and low std (0.1859).

4. **Sector factors are harmful** for this DGP: all correlations ~0.23 with no block-diagonal structure means sector averages add noise to alpha extraction (F3, F4 both poor).

5. **Moreira-Muir vol-scaling (F6)** adds ~0.07 CV mean over F5, reaching best CV mean of 0.8296, but at cost of higher transaction costs. Good but not transformative.

6. **The path to beating R2 likely requires**: better alpha signal (not just less noisy raw mu), possibly using cross-sectional information about which assets have genuine positive alpha vs. which are just noise.

---

## Recommendation

F6 (tick-level factor alpha + vol-scaling) is the best from this batch with CV mean 0.8296, but is below the R2 baseline. F2 is a close second with better stability per unit risk (lower std). Neither exceeds R2.

Next steps to investigate:
- Bayesian shrinkage of factor model alphas toward zero (rather than using raw OLS intercepts)
- Combining factor alpha with James-Stein shrinkage
- Using the factor residual covariance (F2's cov) with tick-level alpha (F5's mu) together
