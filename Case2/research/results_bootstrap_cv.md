# Bootstrap & CV Strategy Results

Reference: Oracle max-Sharpe = 2.63 (long-short), 1.68 (long-only)
Current best (R2): CV Mean = +1.1949, Std = 0.2597, Min = +0.8950

---

## B1: Bootstrap Aggregated (Bagged) Max-Sharpe

**Implementation:** 100 bootstrap samples of daily returns (with replacement). For each sample: estimate mu and LW cov, compute max-Sharpe weights (long-only). Average all 100 weight vectors. Static weights.

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +0.8775
- Total return: +15.05%
- Max drawdown: -21.35%
- Txn costs: 0.0346%

**Cross-Validation (3-fold expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1 | Year 2 | +0.4985 |
| 2 | Year 3 | +0.7631 |
| 3 | Year 4 | +0.8775 |

- **CV Mean: +0.7130**
- **CV Std: 0.1944**
- **CV Min: +0.4985**

**Assessment:** Worse than R2 by a wide margin. Bagging the max-Sharpe optimizer mostly averages out the sector signal that R2/BL captures intentionally. Low transaction costs but low alpha.

---

## B2: Walk-Forward Optimized Weights

**Implementation:** Split training data into 4 sub-periods. For each of 3 walk-forward splits, train max-Sharpe on preceding data, evaluate on next period. Select the weight vector with the highest validation Sharpe.

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +1.3862
- Total return: +27.56%
- Max drawdown: -28.43%
- Txn costs: 0.0396%

**Cross-Validation (3-fold expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1 | Year 2 | +0.5011 |
| 2 | Year 3 | -0.0621 |
| 3 | Year 4 | +1.3862 |

- **CV Mean: +0.6084**
- **CV Std: 0.7301**
- **CV Min: -0.0621**

**Assessment:** High variance and negative fold. Single-split looks good (+1.39) but that's driven by the specific holdout year. CV reveals the approach is unstable — sometimes picks the wrong sub-period's weights. Not suitable for submission.

---

## B3: Resampled Efficient Frontier (Michaud)

**Implementation:** Estimate mu and LW cov from training data. Generate 500 Monte Carlo simulations by perturbing mu with its standard error (N(0, diag(cov)/T)). For each simulation, compute max-Sharpe weights. Average all 500 weight vectors. Static weights.

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +0.9730
- Total return: +16.91%
- Max drawdown: -21.92%
- Txn costs: 0.0327%

**Cross-Validation (3-fold expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1 | Year 2 | +0.5258 |
| 2 | Year 3 | +0.7019 |
| 3 | Year 4 | +0.9730 |

- **CV Mean: +0.7336**
- **CV Std: 0.2253**
- **CV Min: +0.5258**

**Assessment:** Consistently positive and more stable than B1/B2, but below R2. The mu perturbation averages away the sector tilt. Similar to bagging but with smoother perturbations. Better than B1 CV mean (+0.73 vs +0.71) but still far from R2.

---

## B4: Direct Weight Search via CV (Sector-Parameterized)

**Implementation:** Parameterize weights by allocation to sector 3 (alpha3) and sector 4 (alpha4). Within each sector, use inverse-vol weighting. Hold out last 25% of training data for validation. Grid search over alpha3/alpha4 followed by Nelder-Mead refinement to maximize hold-out Sharpe. Static weights.

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +0.7854
- Total return: +14.67%
- Max drawdown: -22.24%
- Txn costs: 0.0446%

**Cross-Validation (3-fold expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1 | Year 2 | +0.9073 |
| 2 | Year 3 | +1.0761 |
| 3 | Year 4 | +1.1318 |

- **CV Mean: +1.0384**
- **CV Std: 0.1169**
- **CV Min: +0.9073**

**Assessment:** Best CV mean of all B1-B5 strategies and lowest CV std. Robust across all folds with consistent improvement across years (alpha signal strengthens with more training data). The sector-parameterized approach directly exploits the known DGP structure without overfitting. Single-split is modest because the 4-year training has a different sector regime in the last year used for internal validation. **Close to R2 (1.03 vs 1.19 CV mean).**

---

## B5: Shrinkage Intensity Optimization

**Implementation:** Parameterize mu as: mu_shrunk = alpha * mu_sample + (1-alpha) * mu_grand_mean. For alpha in [0, 0.05, ..., 1.0]: compute max-Sharpe weights, evaluate on hold-out (last 25% of training). Select best alpha, refit on full training data. Static weights.

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +0.7167
- Total return: +13.13%
- Max drawdown: -22.69%
- Txn costs: 0.0419%

**Cross-Validation (3-fold expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1 | Year 2 | +0.6429 |
| 2 | Year 3 | +0.9886 |
| 3 | Year 4 | +0.7167 |

- **CV Mean: +0.7827**
- **CV Std: 0.1821**
- **CV Min: +0.6429**

**Assessment:** Moderate performance. The shrinkage toward grand mean reduces sector tilt too aggressively when there is genuine sector outperformance in the DGP. Fold 2 shows +0.99 (good training signal), but Fold 3 drops back to +0.72 suggesting the alpha selection overfits to the specific hold-out period.

---

## B6: B4 + Moreira-Muir Vol-Scaling

**Implementation:** Take B4 (best from B1-B5) and add Moreira-Muir vol-scaling: compute trailing 21-day realized portfolio vol, scale weights by min(1, target_vol / realized_vol) where target_vol = median 252-day vol from training.

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +0.7680
- Total return: +13.74%
- Max drawdown: -23.09%
- Txn costs: 0.0854%

**Cross-Validation (3-fold expanding window):**
| Fold | Test Year | Sharpe |
|------|-----------|--------|
| 1 | Year 2 | +0.6472 |
| 2 | Year 3 | +1.0737 |
| 3 | Year 4 | +0.7680 |

- **CV Mean: +0.8296**
- **CV Std: 0.2198**
- **CV Min: +0.6472**

**Assessment:** Vol-scaling HURTS B4. CV mean drops from +1.0384 to +0.8296 and transaction costs double (0.04% -> 0.09%). This makes sense: B4 uses inverse-vol weighting within sectors which already provides some volatility management. Adding an outer vol-scaling layer introduces extra turnover without improving risk-adjusted returns. The B4 base weights are already relatively stable.

---

## Summary Table

| Strategy | Single Sharpe | CV Mean | CV Std | CV Min | Notes |
|----------|--------------|---------|--------|--------|-------|
| **R2 (baseline)** | **+1.3420** | **+1.1949** | **0.2597** | **+0.8950** | BL + vol-scaling |
| B1 (Bagged Max-Sharpe) | +0.8775 | +0.7130 | 0.1944 | +0.4985 | Averages away sector signal |
| B2 (Walk-Forward) | +1.3862 | +0.6084 | 0.7301 | -0.0621 | High variance, unstable |
| B3 (Michaud Resampled) | +0.9730 | +0.7336 | 0.2253 | +0.5258 | Stable but low alpha |
| **B4 (Sector CV Search)** | +0.7854 | **+1.0384** | **0.1169** | **+0.9073** | Best consistency, low variance |
| B5 (Shrinkage Intensity) | +0.7167 | +0.7827 | 0.1821 | +0.6429 | Alpha selection overfits |
| B6 (B4 + Vol-Scaling) | +0.7680 | +0.8296 | 0.2198 | +0.6472 | Vol-scaling hurts B4 |

---

## Key Findings

1. **R2 remains the best strategy** by CV mean (+1.19 vs best challenger B4 at +1.04).

2. **B4 is the most robust challenger**: CV std of only 0.1169 (vs R2's 0.2597), all folds positive (min = +0.91). If the competition averages over many OOS runs, B4's consistency could be valuable.

3. **Vol-scaling helps R2 but hurts B4**: R2 benefits from vol-scaling because BL weights are relatively static and the vol-scaling provides dynamic risk management. B4's inverse-vol construction already handles this internally.

4. **Bootstrap/resampling methods (B1, B3) underperform**: Both achieve CV mean ~0.73, far below R2. They average away the sector-specific alpha signal that the DGP generates.

5. **Walk-forward selection (B2) is dangerously unstable**: A single negative fold (-0.06) disqualifies it for competition use.

6. **Bottleneck confirmed**: mu estimation error is the key bottleneck. Strategies that explicitly incorporate the known DGP structure (sector 3/4 outperformance) — like R2 via BL views and B4 via sector allocation — beat agnostic methods.

## Recommendation

**Keep R2 as the submission.** B4 offers better CV consistency (lower std, higher min) but lower CV mean. If the competition scoring is purely on mean Sharpe, R2 dominates. If there is a floor/risk penalty, B4's stability could be valuable — but with no indication of a floor penalty, R2 is the right choice.

**Potential next directions:**
- Combine B4's sector-allocation approach with R2's BL mu estimation (hybrid)
- Try R2 with a stronger sector 3/4 view signal (higher tau)
- Explore whether B4's sector weights can be initialized from BL mu rather than raw returns
