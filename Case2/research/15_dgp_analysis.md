# DGP Reverse-Engineering Analysis
**Date:** 2026-04-08  
**Data:** 37,800 ticks, 30 ticks/day, 1,260 days (~5 years), 25 assets  
**Figures:** `/Users/stao042906/.omc/scientist/figures/`

---

## [OBJECTIVE]
Reverse-engineer the data generating process (DGP) underlying the competition price data to identify the exact statistical structure and derive the optimal portfolio strategy.

---

## [DATA]
- **Shape:** 37,800 ticks × 25 assets, all starting at 100
- **Time structure:** 30 ticks/day, 1,260 trading days (5 years)
- **Sectors:** 5 sectors (0–4), 5 assets each
- **Meta:** spread_bps (2–12), borrow_bps_annual (23–197)
- **Daily return observations:** 1,259 per asset
- **Tick return observations:** 37,799 per asset

---

## Section 1: GBM Test — Normality of Log Returns

**Hypothesis:** If the DGP is GBM, daily log returns should be normally distributed (Jarque-Bera and Shapiro-Wilk tests).

### Results (Daily Log Returns)

| Asset | Sector | Skew | Ex.Kurt | JB p-val | SW p-val | Normal? |
|-------|--------|------|---------|----------|----------|---------|
| A00 | 2 | 0.082 | 0.371 | 0.0134 | 0.0945 | NO |
| A01 | 0 | 0.019 | 0.087 | 0.787 | 0.968 | YES |
| A02 | 2 | 0.038 | 0.487 | 0.002 | 0.036 | NO |
| A03 | 1 | 0.042 | 0.168 | 0.395 | 0.503 | YES |
| A04 | 3 | 0.008 | 0.183 | 0.412 | 0.189 | YES |
| A05 | 4 | -0.083 | 0.072 | 0.422 | 0.417 | YES |
| A06 | 4 | 0.014 | 0.039 | 0.940 | 0.520 | YES |
| A07 | 0 | -0.047 | -0.064 | 0.711 | 0.608 | YES |
| A08 | 2 | -0.065 | 0.282 | 0.079 | 0.339 | YES |
| A09 | 3 | -0.233 | 0.303 | 0.0003 | 0.002 | NO |
| A10 | 1 | 0.120 | 0.607 | 0.000 | 0.002 | NO |
| A11 | 3 | -0.005 | -0.018 | 0.989 | 0.946 | YES |
| A12 | 0 | -0.029 | 0.061 | 0.830 | 0.160 | YES |
| A13 | 1 | 0.192 | 0.430 | 0.0002 | 0.006 | NO |
| A14 | 1 | -0.106 | 0.618 | 0.000 | 0.004 | NO |
| A15 | 0 | 0.043 | 0.022 | 0.814 | 0.894 | YES |
| A16 | 1 | 0.024 | 0.129 | 0.609 | 0.779 | YES |
| A17 | 4 | -0.015 | 0.126 | 0.643 | 0.569 | YES |
| A18 | 0 | 0.004 | 0.015 | 0.992 | 0.538 | YES |
| A19 | 3 | -0.027 | 0.086 | 0.761 | 0.378 | YES |
| A20 | 2 | -0.098 | 0.772 | 0.000 | 0.001 | NO |
| A21 | 4 | 0.020 | 0.318 | 0.068 | 0.131 | YES |
| A22 | 2 | -0.112 | 0.188 | 0.106 | 0.090 | YES |
| A23 | 3 | -0.023 | 0.150 | 0.521 | 0.265 | YES |
| A24 | 4 | 0.007 | 0.388 | 0.019 | 0.129 | NO |

[FINDING] Daily log returns are **approximately normally distributed** for 17/25 assets (JB p>0.05), consistent with GBM.  
[STAT:n] n=1,259 daily observations per asset  
[STAT:p_value] JB test: 17/25 assets fail to reject normality (p>0.05); 8 assets show mild non-normality (excess kurtosis 0.3–0.8)  
[STAT:effect_size] Mean excess kurtosis = 0.28 (very mild fat tails vs GBM prediction of 0)

[FINDING] **Tick-level returns are strongly non-normal** — all 25 assets reject normality with JB statistics in the thousands (p≈0).  
[STAT:n] n=37,799 tick observations  
[STAT:effect_size] Mean excess kurtosis at tick level = 2.1 (heavy tails). This is consistent with aggregation: sum of 30 near-normal tick shocks → approximately normal daily return (Central Limit Theorem)

**GBM Parameters (annualized):**

| Asset | Sector | mu_ann | sig_ann | Sharpe |
|-------|--------|--------|---------|--------|
| A04 | 3 | 0.267 | 0.278 | 0.958 |
| A09 | 3 | 0.390 | 0.276 | 1.415 |
| A11 | 3 | 0.404 | 0.351 | 1.150 |
| A17 | 4 | 0.252 | 0.248 | 1.015 |
| A19 | 3 | 0.278 | 0.316 | 0.882 |
| A24 | 4 | 0.261 | 0.312 | 0.837 |
| A14 | 1 | -0.127 | 0.310 | -0.411 |
| A20 | 2 | -0.143 | 0.345 | -0.416 |
| A23 | 3 | -0.077 | 0.329 | -0.233 |

[LIMITATION] With 1,259 daily observations, the standard error of mean estimation is sig/sqrt(1259) ≈ 0.3/35.5 ≈ 0.008/day, or ~2% annually — drifts below ~4% annualized are statistically indistinguishable from zero.

---

## Section 2: Mean Reversion vs Momentum — AR(1) Test

**Hypothesis:** If there is momentum (OU process with positive feedback) or mean reversion (OU with negative feedback), the AR(1) coefficient b should be significantly different from zero.

[FINDING] **Essentially no serial correlation in daily returns.** Mean AR(1) beta = 0.0037 across all 25 assets.  
[STAT:n] n=1,258 return pairs  
[STAT:p_value] Only 3/25 assets show significant AR(1): A01 (b=0.057, momentum), A03 (b=0.081, momentum), A23 (b=-0.056, mean reversion). All barely significant at 5% level.  
[STAT:effect_size] Mean |beta| = 0.029 — economically negligible  
[STAT:ci] R² of AR(1) model: mean = 0.002 (0.2%) — essentially zero predictability from lagged returns

[FINDING] **Tick-level returns show weak positive serial correlation** (mean beta = 0.016), suggesting a slight momentum effect within the trading day. This is consistent with the implementation of a correlated noise process or a tick-level trend injection.  
[STAT:effect_size] Mean within-day autocorrelation = 0.016; mean across-day autocorrelation = -0.008 — asymmetry suggests the intraday and interday processes may differ slightly.  
[STAT:n] n=37,798 tick pairs

**Variance Ratio Test:** Mean VR = 1.061 (>1), consistent with slight positive intraday autocorrelation, but close to 1 at the daily level.

[LIMITATION] The weak tick-level momentum could reflect the simulation's numerical integration method (Euler-Maruyama) rather than a true momentum DGP feature.

---

## Section 3: GARCH / Volatility Clustering

**Hypothesis:** If the DGP includes GARCH(1,1), squared returns should be positively autocorrelated (persistent volatility).

[FINDING] **No significant GARCH effects.** Only 5/25 assets show significant AR(1) in squared returns; Ljung-Box on squared returns is significant for only 3/25 assets.  
[STAT:n] n=1,259  
[STAT:p_value] Ljung-Box (lag 10) on r²: only A05 (p=0.027), A16 (p=0.037), A20 (p<0.001) reject the null. For 22/25 assets, p>0.05.  
[STAT:effect_size] Mean AR(1) coefficient on r²: b=0.014 — near zero

[FINDING] **No leverage effect.** Mean correlation between r(t) and r²(t+1) = -0.008. Only 1/25 assets shows a statistically significant negative correlation (A07, p=0.046).  
[STAT:n] n=1,258  
[STAT:effect_size] Mean leverage corr = -0.008 (essentially zero)

[FINDING] The DGP **does not include GARCH(1,1) or stochastic volatility** at the daily level. Volatility appears **constant** (homoskedastic GBM).  
[STAT:effect_size] Rolling 30-day realized vol shows mild variation but no persistent clustering pattern.

[LIMITATION] The Ljung-Box test with only 1,259 observations has limited power to detect GARCH with small parameters (alpha+beta < 0.3). A true GARCH with persistence near 0.95 would be detectable; a weak GARCH would not.

---

## Section 4: Factor Model Structure

**Hypothesis:** Returns follow a factor structure r_i(t) = alpha_i + beta_i*F1(t) + e_i(t) where F1 = PC1.

[FINDING] **A single factor (PC1) explains 25.4% of variance**, with each additional PC explaining only 4–6% incrementally.  
[STAT:effect_size] PC1 variance explained: 25.4%; cumulative first 8 PCs: 56.3%  
[STAT:n] n=1,259 days, p=25 assets

[FINDING] **All PC1 loadings are positive and approximately equal** (range: 0.147–0.250), consistent with a market-wide common factor with roughly uniform exposure.  
[STAT:effect_size] PC1 loading range [0.147, 0.250]; coefficient of variation = 18% — moderate uniformity

[FINDING] **Sector alphas are NOT uniformly significant.** Only 6/25 assets show significant alpha against the PC1 factor (p<0.05). However, sector 3 and sector 4 have systematically higher alphas.  
[STAT:p_value] Significant alphas: A04 (S3), A09 (S3), A11 (S3), A17 (S4), A19 (S3), A24 (S4)  
[STAT:effect_size] Mean single-factor R² = 0.266, ranging from 0.13 (A14) to 0.46 (A17)

**Sector-level alpha summary:**
| Sector | Mean Ann. Alpha (vs PC1) | Interpretation |
|--------|--------------------------|---------------|
| 0 | +0.050 | Slight positive |
| 1 | -0.009 | Near zero |
| 2 | -0.015 | Slightly negative |
| 3 | +0.253 | **Strong positive drift** |
| 4 | +0.233 | **Strong positive drift** |

[FINDING] The DGP likely encodes **sector-specific drift components** for sectors 3 and 4, while sectors 1 and 2 have near-zero drift.

---

## Section 5: Sector Correlation Structure

**Hypothesis:** If sector structure is meaningful, within-sector correlations should be significantly higher than between-sector correlations.

[FINDING] **The correlation structure is NOT block-diagonal.** Within-sector and between-sector correlations are statistically indistinguishable.  
[STAT:ci] Within-sector mean: 0.2312 ± 0.0811; Between-sector mean: 0.2277 ± 0.0716  
[STAT:p_value] Welch t-test: t=0.309, p=0.758 — no significant difference  
[STAT:effect_size] Ratio of within/between = 1.015 — essentially 1.0; difference in means = 0.0035

[FINDING] **100% of all pairwise correlations (both within and between sector) are positive**, consistent with a single dominant common factor driving all assets uniformly.  
[STAT:n] 300 pairs total (25×24/2)

[FINDING] **The single-factor model (PC1) consistently outperforms the sector-factor model** for all 25 assets (sector factor R² is lower for every asset).  
[STAT:effect_size] Mean R²: single-factor = 0.266 vs sector-factor = 0.130 — single factor is 2× better

**Conclusion:** The "sector structure" in the DGP manifests as **differential drift rates** (particularly S3 and S4 outperforming), NOT as a distinct correlation block structure. The common factor (PC1) dominates covariances uniformly across sectors.

[LIMITATION] Sector correlation differences could exist at finer timescales not captured by daily returns. The PC1 itself may encode a mix of sector and market effects.

---

## Section 6: Tick-Level vs Daily Process

**Hypothesis:** The 30 intraday ticks are generated by a different process than the daily process.

[FINDING] **Tick-level volatility is consistent with daily volatility** when scaled by sqrt(30): mean ratio = 0.972 (close to 1.0).  
[STAT:effect_size] Mean ratio = 0.972; range [0.929, 1.013] — within 7% of the iid scaling expectation  
[STAT:n] 37,799 tick observations

[FINDING] **Tick returns are strongly non-normal** (all 25 assets reject JB with p≈0), but **daily returns are approximately normal** for most assets. This is consistent with the Central Limit Theorem: summing 30 leptokurtic tick returns produces approximately normal daily returns.  
[STAT:effect_size] Tick excess kurtosis: mean 2.1 (heavy-tailed); daily excess kurtosis: mean 0.28 (nearly Gaussian)

[FINDING] **Slight intraday autocorrelation** exists (mean within-day AC = 0.016) while across-day transitions have near-zero AC (mean = -0.008). This suggests the tick simulation uses Euler-Maruyama discretization with correlated noise, not independent ticks.  
[STAT:effect_size] Difference: within-day AC (0.016) vs across-day AC (-0.008) = 0.024

**Variance Ratio Test:** Mean VR = 1.061, marginally above 1.0, confirming slight positive intraday autocorrelation.

**Key finding on intraday architecture:** The mean return at the open tick (0.000032) and close tick (0.000055) are comparable to the overall mean tick return (0.000013), suggesting **no intraday seasonality** (U-shaped or J-shaped pattern) was built in.

[LIMITATION] The VR being only 6% above 1.0 means intraday momentum is very small. It may not be exploitable after transaction costs.

---

## Section 7: Drift Stability

**Hypothesis:** The drift (mu) per asset is constant over 5 years vs. time-varying.

[FINDING] **Drift is statistically constant for ALL 25 assets** at both yearly and half-yearly resolution.  
[STAT:p_value] ANOVA across 4 annual periods: all p>0.05 (range p=0.084 to 0.992)  
[STAT:p_value] ANOVA across 9 half-year periods: all p>0.05 (range p=0.085 to 0.995)  
[STAT:p_value] Chow break test at midpoint (day 630): all p>0.05 (0/25 significant breaks)  
[STAT:n] n=252 returns per annual period, n=126 per half-year period

[FINDING] **Year-by-year drift estimates fluctuate substantially** (e.g., A06: Yr1=0.76, Yr2=-0.06, Yr3=0.27, Yr4=0.10) but these fluctuations are not statistically significant — they are consistent with noise from a constant-drift GBM.  
[STAT:effect_size] Typical range of annual drift estimates per asset: ±0.3 to ±0.6 annualized — the uncertainty from 252 obs per year is large

[FINDING] **Sector-level drifts confirm high-drift sectors:**
- Sector 3: consistently positive across all years (Yr1=0.24, Yr2=0.51, Yr3=0.18, Yr4=0.21)
- Sector 4: consistently positive (Yr1=0.40, Yr2=0.29, Yr3=0.03, Yr4=0.11)
- Sectors 1 and 2: oscillate near zero  
[STAT:effect_size] Sector 3 mean annual drift = 0.29 annualized; Sector 4 = 0.21 annualized

[FINDING] **5-asset sector means confirm significant positive drift for sectors 3 and 4** even at individual asset level (A04, A09, A11, A17, A19 all have t-test p<0.05 for mu≠0).  
[STAT:p_value] A09: p=0.0016; A11: p=0.010; A17: p=0.023; A19: p=0.049; A04: p=0.033

[LIMITATION] With only ~252 daily observations per year, ANOVA has limited power (~30-40%) to detect drift changes of the magnitude seen (±0.3 annualized). The stability conclusion must be interpreted as "consistent with stability" not "confirmed stable."

---

## Section 8: Proposed Data Generating Process

### Evidence Summary

| Test | Result | Implication |
|------|--------|-------------|
| GBM normality (daily) | 17/25 normal, mild kurtosis | ~GBM daily |
| Tick normality | 0/25 normal (kurt≈2) | Heavy-tailed tick noise |
| AR(1) daily | Mean b=0.004, 2/25 significant | No momentum/MR |
| GARCH on r² | 5/25 significant, tiny b | No vol clustering |
| Leverage effect | 1/25 significant | No asymmetric vol |
| PC1 variance | 25.4% | One dominant factor |
| Sector block structure | p=0.758 (no difference) | No block diagonal |
| Within/between corr ratio | 1.015 | Pure single-factor |
| Drift stability | 25/25 stable | Constant drift |
| Drift magnitude | S3: 0.29, S4: 0.21 ann. | Sector-specific drifts |
| VR test | 1.061 | Mild intraday momentum |

### [FINDING] Most Likely DGP

**The DGP is a multi-asset GBM (Geometric Brownian Motion) with:**

1. **Asset-specific constant drifts (mu_i)** — each asset has a fixed annualized drift embedded at simulation start, creating large dispersion (A09: +39%, A20: -14%)

2. **Asset-specific constant volatilities (sigma_i)** — homoskedastic, ranging from 0.22 (A07) to 0.35 (A13, A18) annualized

3. **A single common factor (Sigma = L*L' + D)** — the covariance matrix is consistent with a factor model where PC1 explains 25% of variance with uniform positive loadings (~0.15–0.25)

4. **No GARCH / stochastic volatility** — volatility is time-invariant

5. **No mean reversion** — AR(1) coefficient indistinguishable from zero at daily level

6. **Sector drifts built in as constant per-asset alphas** — sectors 3 and 4 have systematically high drifts; sectors 1 and 2 near zero; sector 0 mixed

7. **Tick-level process: heavy-tailed noise** with mild intraday autocorrelation (VR=1.06), possibly generated by a student-t or Laplace distribution at tick level, which aggregates to near-normal daily returns via CLT

**Proposed mathematical form:**
```
dP_i / P_i = mu_i * dt + sigma_i * (sqrt(rho) * dW_0 + sqrt(1-rho) * dW_i)

where:
  mu_i     = asset-specific constant drift (set at simulation start)
  sigma_i  = asset-specific constant vol
  dW_0     = common Brownian motion (market factor)
  dW_i     = idiosyncratic Brownian motion
  rho      = ~0.25 (average pairwise correlation ≈ rho * sigma_i * sigma_j / (sigma_i * sigma_j))
```

Discretized at tick level with dt = 1/7560 years (1 tick = 1/(30×252) years) using **Euler-Maruyama** or **exact simulation** with possibly student-t distributed noise.

[STAT:effect_size] This DGP is consistent with: (a) 17/25 assets passing normality daily; (b) 25/25 assets failing normality at tick level; (c) PC1 explaining 25% of variance; (d) no ARCH effects; (e) drift stability across all windows

[LIMITATION] We cannot distinguish between: (1) a pure GBM with fat-tailed noise vs. (2) a GBM with a weak GARCH component below detection power with 1,259 obs. The true DGP could include very mild vol clustering (persistence <0.5) that would not be detectable.

---

## Section 9: Implications for Portfolio Strategy

### Strategic Implications of the Identified DGP

#### 9.1 Drift Is the Primary Alpha Source

[FINDING] **Static allocation to high-drift assets dominates all dynamic strategies** under a constant-drift GBM.

The 5 highest-drift assets (A09, A11, A19, A04, A17) have annualized drifts of 0.25–0.40. Under constant GBM, the optimal strategy is **fixed-weight maximum Sharpe** — no rebalancing signal is generated by past returns.

**Optimal portfolio (exploiting known drifts):**
- Maximize: w' * mu - 0.5 * lambda * w' * Sigma * w
- Solution: w* = (1/lambda) * Sigma^{-1} * mu
- Expected Sharpe: mu' * Sigma^{-1} * mu
- Key insight: sectors 3 and 4 should receive heavy overweight; sectors 1 and 2 underweight/short

[STAT:effect_size] Sharpe ratios: A09=1.42, A11=1.15, A17=1.02, A04=0.96, A19=0.88

#### 9.2 No Benefit from Dynamic Rebalancing on Returns

[FINDING] Since AR(1) beta ≈ 0 for daily returns, **momentum or mean-reversion signals have no predictive power.** Strategies that rebalance based on recent returns (PAMR, momentum, etc.) will perform at best at the same level as static allocation, and likely worse due to transaction costs.  
[STAT:p_value] AR(1) R² ≈ 0.002 (0.2% predictability) — economically worthless after costs

#### 9.3 No Benefit from Vol-Timing

[FINDING] Since there is no GARCH effect (vol is constant), **variance-targeting or vol-scaling strategies provide no edge.** Risk parity works only if the static risk-adjusted returns are equalized, but given asymmetric drifts, true optimal is not risk parity.

#### 9.4 Correlation Structure Does Not Support Sector Rotation

[FINDING] Since within-sector correlation ≈ between-sector correlation (both ≈0.23), **sector rotation strategies have no structural advantage.** The correlation benefit of diversification is uniform across all asset pairs. The only advantage from sectors is their differential drift.

#### 9.5 Tick-Level Momentum Is Barely Exploitable

[FINDING] The intraday autocorrelation (mean AC = 0.016, VR = 1.06) is small. At typical spread costs of 2–12 bps per trade, the expected tick-level momentum profit is below the cost threshold for all but the lowest-spread assets.

#### 9.6 Recommended Strategy Architecture

**Primary alpha:** Static long exposure to high-drift assets, weighted by Sharpe ratio or Markowitz optimization.

**Portfolio construction:**
1. Estimate asset drifts (use all available history, uniform weighting)
2. Estimate covariance matrix (sample covariance or factor shrinkage)
3. Compute Markowitz optimal weights with leverage constraint
4. Hold static — do not rebalance on return signals
5. Rebalance only to maintain target weights (pure drift-based reallocation)

**Sector allocation (derived from drift analysis):**
- **Overweight:** Sector 3 (S3 drift ~0.29 ann.) and Sector 4 (S4 drift ~0.21 ann.)
- **Neutral/underweight:** Sector 0 (drift ~0.05), Sector 1 (drift ~-0.01), Sector 2 (drift ~-0.01)
- **Short candidates:** A14 (mu=-0.13), A20 (mu=-0.14), A16 (mu=-0.06), A12 (mu=-0.05)

**Critical quantitative result:**
- Best single asset: A09 (Sharpe=1.42, mu=0.39, sig=0.28)
- Best sector (equal weight): Sector 3 terminal return = +355%
- Worst sector (equal weight): Sector 2 terminal return = -2.7%

#### 9.7 Transaction Cost Constraint

Given borrow_bps_annual (23–197 bps) and spread_bps (2–12 bps), the cost budget significantly constrains short positions. For short candidates:
- A14: borrow=165 bps/yr. With mu=-0.13 and sig=0.31, Sharpe=-0.41 before costs, deteriorates quickly with borrow costs.
- A20: borrow=160 bps/yr. Sharpe=-0.42 before borrow.

**Net of costs, marginally shorting these assets may still be profitable if allocations are small and turnover is low.**

---

## [LIMITATION] Overall Caveats

1. **Estimation uncertainty in drifts:** With 1,259 days, SE(mu) ≈ 0.008/day = ~2% annualized. Many drifts are within 1 SE of zero. The DGP may have smaller or larger true drifts than measured.

2. **Out-of-sample drift stability:** All evidence points to constant drift, but this is tested over 5 years of training data. If the competition evaluates on unseen data from the same DGP, the signal should be stable.

3. **Covariance estimation:** Sample covariance with 1,259 obs and 25 assets (ratio ≈ 50:1) is relatively reliable, but eigenvalue concentration in PC1 means the portfolio may be sensitive to the common factor.

4. **Inability to test weak GARCH:** The LB test for ARCH has ~50% power at alpha+beta=0.3 with n=1,259. A weak GARCH component may exist but would provide only marginal vol-timing benefit.

5. **Tick-level strategy costs:** The 0.97 ratio of actual vs. expected tick vol means that strategies trading at every tick face approximately 3% "roundtrip vol drag" per day from any intraday timing error.

---

## Summary Table

| Property | Evidence | Conclusion |
|----------|----------|------------|
| Return distribution | JB: 17/25 normal daily | ~GBM (daily) |
| Autocorrelation | AR(1) b=0.004, R²=0.002 | No MR/Momentum |
| Vol clustering | ARCH: 3/25 significant | No GARCH |
| Leverage effect | Corr=-0.008 | No asymmetric vol |
| Factor structure | PC1=25.4%, single factor | Single-factor GBM |
| Sector correlations | Within≈Between≈0.23 | Single factor dominates |
| Drift stability | All p>0.05 | Constant drifts |
| Sector drifts | S3: +0.29, S4: +0.21 ann. | Built-in sector drift |
| Intraday structure | VR=1.06, tick kurt=2.1 | Mild tick AC, CLT aggregation |
| **Optimal strategy** | | **Static Markowitz long-biased to S3/S4** |

---

*Report generated: 2026-04-08*  
*Figures: `/Users/stao042906/.omc/scientist/figures/01_qq_plots_daily.png`, `03_vol_clustering.png`, `04_factor_model.png`, `05_correlation_heatmap.png`, `06_tick_vs_daily_vol.png`, `07_yearly_drift.png`, `08_scree_and_paths.png`, `09_intraday_pattern.png`*
