# Shrinkage Mu Strategies: J1–J6 Results

Date: 2026-04-08
Oracle max-Sharpe: 2.63 (long-short), 1.68 (long-only)
Baseline R2 (BL + vol-scaling): CV Mean = +1.195, Std = 0.260, Min = +0.895

All strategies: long-only, static weights, max-Sharpe optimization, Ledoit-Wolf covariance.

---

## J1: James-Stein Shrinkage on Daily Mu

**Method:**
- Compute daily log returns; estimate mu_sample per asset
- sigma^2_pooled = mean(var_i / T) = average SE^2 of the mean
- JS shrinkage: c = min(1, (n-2)*sigma^2_pooled / sum((mu_i - mu_mean)^2))
- mu_JS = (1-c)*mu_sample + c*grand_mean
- max-Sharpe + LW cov, long-only

**Single-split (4yr train / 1yr holdout):**
- Annualized Sharpe: +0.9725
- Total return: +15.70%
- Max drawdown: -20.67%
- Transaction costs: 0.0342%

**CV (3-fold expanding window):**
- Fold 1 (test year 2): +0.2278 (negative... wait: -0.2278)
- Actually: Fold 1 = -0.2278, Fold 2 = +0.0553, Fold 3 = +0.9725
- Mean Sharpe: +0.2667
- Std Sharpe: 0.6274
- Min Sharpe: -0.2278

**Assessment:** Poor. JS on daily mu is insufficient — early folds have too few training days, and shrinkage toward the grand mean (near zero) hurts when sectors 3&4 have high drift.

---

## J2: James-Stein Shrinkage on Tick-Level Mu (scaled to daily)

**Method:**
- Use tick-level returns (30x more data: ~30,000 ticks vs ~1,000 days in train)
- mu_tick estimated with 30x more precision
- JS shrinkage at tick level, then scale to daily: mu_daily = mu_tick_JS * 30
- max-Sharpe + LW cov (on daily returns), long-only

**Single-split:**
- Annualized Sharpe: +0.9098
- Total return: +14.89%
- Max drawdown: -20.85%
- Transaction costs: 0.0335%

**CV:**
- Fold 1 = -0.1217, Fold 2 = +0.2461, Fold 3 = +0.9098
- Mean Sharpe: +0.3447
- Std Sharpe: 0.5228
- Min Sharpe: -0.1217

**Assessment:** Slightly better than J1 (CV mean +0.345 vs +0.267) but still problematic in early folds. Tick-level precision helps slightly but the shrinkage target (grand mean near zero) remains the core problem.

---

## J3: Sector-Pooled Mu (Hierarchical Blend)

**Method:**
- mu_sector_s = mean of mu_asset_i for assets in sector s
- mu_blended_i = alpha * mu_asset_i + (1-alpha) * mu_sector_i
- Tested alpha = 0.3, 0.5, 0.7

### J3 alpha=0.3 (70% sector pooling)

**Single-split:** Sharpe = +0.8775, Return = +15.05%, MDD = -21.35%

**CV:**
- Fold 1 = +0.4985, Fold 2 = +0.7631, Fold 3 = +0.8775
- Mean: +0.7130, Std: 0.1944, Min: +0.4985

### J3 alpha=0.5 (50/50 blend) — BEST of J3 variants

**Single-split:** Sharpe = +1.0069, Return = +19.12%, MDD = -24.41%, Costs = 0.0384%

**CV:**
- Fold 1 = +0.8580, Fold 2 = +1.0932, Fold 3 = +1.0069
- **Mean: +0.9860, Std: 0.1190, Min: +0.8580**

### J3 alpha=0.7 (30% sector pooling)

**Single-split:** Sharpe = +0.8463, Return = +15.80%, MDD = -23.23%

**CV:**
- Fold 1 = +0.8241, Fold 2 = +1.0569, Fold 3 = +0.7241 (wait: +0.8463 last fold is test yr 4)
- Actually: Fold 1 = +0.8241, Fold 2 = +1.0569, Fold 3 = +0.8463 (test yr 4 was +0.8463 but single split was different year overlap... let me recheck)
- Fold 3 (test year 4) = +0.7241
- Mean: +0.8684, Std: 0.1707, Min: +0.7241

**J3 Summary (best alpha=0.5):**
- Sector pooling dramatically improves early-fold performance vs J1/J2
- alpha=0.5 is optimal: sufficient sectoral information without losing asset-level signal
- CV mean +0.986 vs J1 +0.267 — huge improvement

---

## J4: Bayesian Conjugate Normal Posterior Mu

**Method:**
- Prior: mu_i ~ N(mu_prior, tau^2) where mu_prior = grand mean of sample means, tau^2 = cross-sectional variance of sample means
- Likelihood: x_bar_i | mu_i ~ N(mu_i, sigma^2_i / T)
- Posterior: mu_post_i = (mu_prior/tau^2 + x_bar_i * T/sigma^2_i) / (1/tau^2 + T/sigma^2_i)
- Automatically shrinks uncertain assets more toward the prior
- max-Sharpe + LW cov, long-only

**Single-split:**
- Annualized Sharpe: +0.8462
- Total return: +15.66%
- Max drawdown: -22.91%
- Transaction costs: 0.0376%

**CV:**
- Fold 1 = +0.5572, Fold 2 = +0.8132, Fold 3 = +0.8462
- **Mean: +0.7388, Std: 0.1582, Min: +0.5572**

**Assessment:** Better than J1/J2 in early folds (positive), CV mean +0.739. However, prior = grand mean (near zero for early folds) still partially hurts. Cross-sectional tau^2 is small when all assets have similar mu, leading to heavy shrinkage toward zero.

---

## J5: Sector-Level Bayesian Hierarchical Mu

**Method:**
Two-level hierarchy:
- Level 1: sector drift ~ N(grand_mean, tau_sector^2), tau_sector^2 = variance of sector means
- Level 2: asset drift | sector ~ N(mu_sector, tau_asset^2), tau_asset^2 = within-sector variance of asset means
- Posterior sector mean: empirical Bayes combining grand mean + sector-specific data
- Posterior asset mean: combines sector posterior + asset-level data
- Automatically pools within-sector information
- max-Sharpe + LW cov, long-only

**Single-split:**
- Annualized Sharpe: **+1.1318**
- Total return: +21.75%
- Max drawdown: -25.55%
- Transaction costs: 0.0371%

**CV:**
- Fold 1 = +0.9073, Fold 2 = +1.0761, Fold 3 = +1.1318
- **Mean: +1.0384, Std: 0.1169, Min: +0.9073**

**Assessment:** Best of the pure shrinkage strategies. Two-level pooling correctly identifies that sectors 3&4 have high drift even in early folds, because the sector-level prior captures the cross-sector heterogeneity. Consistently positive across all folds (min +0.907). CV std only 0.117 — very stable.

---

## J6: Ensemble of J1–J5 Weight Vectors

**Method:**
- Compute weights from J1, J2, J3(alpha=0.5), J4, J5 independently
- Average: w_ensemble = (w_J1 + w_J2 + w_J3 + w_J4 + w_J5) / 5
- Normalize to sum = 1, long-only
- Static weights

**Single-split:**
- Annualized Sharpe: +0.9855
- Total return: +17.45%
- Max drawdown: -22.76%
- Transaction costs: 0.0346%

**CV:**
- Fold 1 = +0.4440, Fold 2 = +0.7121, Fold 3 = +0.9855
- **Mean: +0.7139, Std: 0.2707, Min: +0.4440**

**Assessment:** Diluted by J1 and J2 which pull weights toward poor estimators in early folds. The ensemble is dragged down by the weakest members. J5 alone beats the ensemble on CV mean (+1.038 vs +0.714).

---

## Summary Table

| Strategy | Single-Split Sharpe | CV Mean | CV Std | CV Min | Notes |
|----------|-------------------|---------|--------|--------|-------|
| R2 (baseline) | +1.3420 | +1.195 | 0.260 | +0.895 | BL + vol-scaling |
| J1 | +0.9725 | +0.267 | 0.627 | -0.228 | JS on daily mu |
| J2 | +0.9098 | +0.345 | 0.523 | -0.122 | JS on tick mu |
| J3 (alpha=0.3) | +0.8775 | +0.713 | 0.194 | +0.499 | Sector pooled 70% |
| J3 (alpha=0.5) | +1.0069 | +0.986 | 0.119 | +0.858 | Sector pooled 50/50 |
| J3 (alpha=0.7) | +0.8463 | +0.868 | 0.171 | +0.724 | Sector pooled 30% |
| J4 | +0.8462 | +0.739 | 0.158 | +0.557 | Bayes conjugate |
| **J5** | **+1.1318** | **+1.038** | **0.117** | **+0.907** | **Hierarchical Bayes** |
| J6 | +0.9855 | +0.714 | 0.271 | +0.444 | Ensemble J1-J5 |

---

## Key Findings

1. **J5 (Hierarchical Bayes) is the strongest new strategy**: CV mean +1.038, min +0.907, std 0.117. It does NOT beat R2 (CV mean +1.195) but is the best pure shrinkage approach.

2. **Sector pooling is the critical ingredient**: J3 and J5 both benefit from sharing information within sectors. Sectors 3&4 have ~25% ann drift, which propagates to their assets even in short training windows via sector-level pooling.

3. **J1/J2 fail in early folds** because James-Stein shrinks toward the grand mean (~zero), which is wrong when sectors 3&4 have strongly positive drift. Classic JS is agnostic to the sector structure.

4. **J4 (flat Bayes prior) is moderate**: Better than J1/J2 but worse than J5 because it doesn't exploit sector structure. The flat prior misses that sector 3&4 assets should have high mu.

5. **Ensemble (J6) is diluted**: Including weak strategies (J1, J2) in the ensemble hurts overall CV performance. A selective ensemble (J3 + J5 only) would likely be better.

6. **None of the J-series beats R2**: R2 (Black-Litterman + vol-scaling) with its hard-coded sector 3&4 views achieves CV mean +1.195 vs J5's +1.038. The BL approach explicitly encodes the sector signal and adds vol-scaling.

## Recommendations

- **J5 is worth combining with R2**: Consider BL-posterior hybrid — use J5 mu estimates as the "views" input to the BL framework instead of hard-coded view values.
- **Best standalone pure-shrinkage**: J5 (hierarchical Bayes) with CV mean +1.038, very consistent (min +0.907).
- **J3(alpha=0.5) is a good lightweight alternative**: Simple, interpretable, CV mean +0.986 with very low std (0.119).
- **Avoid J1, J2 standalone**: Their lack of sector awareness makes them fail when training data is short.
