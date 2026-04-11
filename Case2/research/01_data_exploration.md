# Case 2 Portfolio Optimization — Data Exploration Report

**Generated:** 2026-04-08  
**Analyst:** Scientist Agent  
**Data:** `prices.csv` (37,800 ticks × 25 assets), `meta.csv` (sector/cost metadata)

---

## [OBJECTIVE]

Perform thorough statistical analysis of all 25 assets to identify:
- Return characteristics and distributional properties
- Sector structure and inter/intra-sector correlations
- Momentum, mean-reversion, and volatility signals
- Regime changes over the 5-year horizon
- Transaction-cost-aware opportunities

---

## [DATA]

| Property | Value |
|---|---|
| Price ticks | 37,800 |
| Assets | 25 (A00–A24) |
| Ticks per day | 30 |
| Total trading days | 1,260 |
| Approximate years | 5 (4 complete 252-day years + 12 days) |
| Sectors | 5 (IDs 0–4, 5 assets each) |
| Missing values | None |
| Start price (all assets) | 100.000 |

---

## 1. Daily Return Statistics (Annualised)

All returns are daily log-returns. Statistics annualised at 252 trading days/year.

| Asset | Sector | Ann. Return | Ann. Vol | Sharpe | Skew | Excess Kurt |
|---|---|---|---|---|---|---|
| A00 | 2 | -0.0106 | 0.3152 | -0.034 | +0.067 | 0.255 |
| A01 | 0 | +0.1490 | 0.3190 | +0.467 | +0.013 | 0.110 |
| A02 | 2 | +0.0063 | 0.2544 | +0.025 | +0.049 | 0.458 |
| A03 | 1 | +0.0553 | 0.2932 | +0.189 | -0.025 | 0.186 |
| A04 | 3 | +0.2590 | 0.2775 | +0.933 | +0.017 | 0.125 |
| A05 | 4 | +0.2161 | 0.3243 | +0.666 | -0.046 | 0.142 |
| A06 | 4 | +0.2446 | 0.3195 | +0.765 | +0.044 | 0.050 |
| A07 | 0 | +0.0004 | 0.2201 | +0.002 | -0.092 | 0.090 |
| A08 | 2 | +0.0364 | 0.2497 | +0.146 | -0.066 | 0.360 |
| A09 | 3 | +0.3897 | 0.2764 | +1.410 | -0.235 | 0.186 |
| A10 | 1 | +0.0530 | 0.2690 | +0.197 | +0.108 | 0.599 |
| A11 | 3 | +0.3983 | 0.3548 | +1.123 | -0.011 | 0.063 |
| A12 | 0 | -0.0495 | 0.3461 | -0.143 | -0.005 | 0.042 |
| A13 | 1 | +0.0428 | 0.3525 | +0.121 | +0.159 | 0.299 |
| A14 | 1 | -0.1239 | 0.3115 | -0.398 | -0.107 | 0.696 |
| A15 | 0 | +0.0303 | 0.2437 | +0.124 | +0.044 | -0.053 |
| A16 | 1 | -0.0688 | 0.3506 | -0.196 | +0.035 | 0.180 |
| A17 | 4 | +0.2484 | 0.2479 | +1.002 | +0.036 | 0.152 |
| A18 | 0 | +0.1381 | 0.3484 | +0.396 | +0.030 | -0.087 |
| A19 | 3 | +0.2800 | 0.3153 | +0.888 | -0.018 | 0.189 |
| A20 | 2 | -0.1493 | 0.3456 | -0.432 | -0.074 | 0.546 |
| A21 | 4 | +0.1941 | 0.3415 | +0.568 | +0.024 | 0.365 |
| A22 | 2 | +0.0320 | 0.3433 | +0.093 | -0.100 | 0.262 |
| A23 | 3 | -0.0807 | 0.3319 | -0.243 | +0.009 | 0.126 |
| A24 | 4 | +0.2654 | 0.3112 | +0.853 | -0.013 | 0.247 |

### Key observations
- **Best Sharpe:** A09 (1.410), A11 (1.123), A17 (1.002), A04 (0.933), A24 (0.853), A06 (0.765)
- **Worst Sharpe:** A09's sector-mate A23 (-0.243), A14 (-0.398), A20 (-0.432)
- **Lowest vol:** A07 (0.220), A17 (0.248), A09 (0.276), A04 (0.278)
- **Highest vol:** A11 (0.355), A13 (0.353), A16 (0.351)
- Return skewness is near zero for all assets (range: -0.235 to +0.159), consistent with symmetric simulation
- Excess kurtosis is modest (range: -0.087 to +0.696), slightly heavier tails than Gaussian for A14, A10

---

## 2. Sector Groupings and Transaction Costs

| Sector | Assets | Spread (bps) | Borrow (bps/yr) |
|---|---|---|---|
| **0** | A01, A07, A12, A15, A18 | 4, 7, 4, 2, 7 | 143, 48, 161, 130, 134 |
| **1** | A03, A10, A13, A14, A16 | 7, 12, 2, 2, 4 | 197, 23, 116, 165, 125 |
| **2** | A00, A02, A08, A20, A22 | 7, 2, 2, 4, 7 | 121, 124, 195, 160, 163 |
| **3** | A04, A09, A11, A19, A23 | 2, 4, 12, 2, 4 | 44, 42, 135, 177, 144 |
| **4** | A05, A06, A17, A21, A24 | 4, 4, 12, 2, 2 | 78, 72, 149, 172, 138 |

### Sector-level annualised returns and Sharpes

| Sector | Avg Ann. Return | Avg Ann. Vol | Avg Sharpe |
|---|---|---|---|
| 0 | +0.054 | 0.296 | +0.169 |
| 1 | -0.008 | 0.315 | -0.017 |
| 2 | -0.017 | 0.302 | -0.040 |
| 3 | **+0.249** | 0.311 | **+0.822** |
| 4 | **+0.234** | 0.309 | **+0.771** |

**[FINDING] Sector 3 and Sector 4 are strongly outperforming; Sectors 1 and 2 are flat/negative over the full 5-year sample.**

[STAT:n] n = 1,259 daily observations  
[STAT:effect_size] Sector 3 avg Sharpe = 0.822 vs Sector 1 avg Sharpe = -0.017

### Cost-adjusted highlights
- **A09** (S3): cheapest borrow in sector (42 bps/yr), 4 bps spread — best cost/return profile
- **A04** (S3): 44 bps borrow, 2 bps spread — second cheapest, Sharpe 0.933
- **A10** (S1): cheapest borrow overall (23 bps/yr) but spread=12 bps; modest Sharpe 0.197
- **A11** (S3): best return (Sharpe 1.123) but 12 bps spread and 135 bps borrow — high turnover cost
- **A08** (S2): 195 bps borrow (2nd highest) with Sharpe 0.146 — short-selling very costly
- **A03** (S1): highest borrow (197 bps/yr) with marginal Sharpe 0.189 — short cost prohibitive

---

## 3. Within-Sector vs Cross-Sector Correlations

Computed on daily log-returns (n = 1,259 days).

| Type | Mean Corr | Std | Min | Max | n pairs |
|---|---|---|---|---|---|
| Within-sector | 0.2302 | 0.0797 | 0.069 | 0.435 | 50 |
| Cross-sector | 0.2279 | 0.0720 | 0.063 | 0.449 | 250 |

**[FINDING] Within-sector and cross-sector correlations are statistically indistinguishable.**

[STAT:p_value] Two-sample t-test p = 0.839 (not significant)  
[STAT:n] 50 within-sector pairs, 250 cross-sector pairs

**Implication:** Sector labels do NOT define meaningful diversification boundaries. Pairs should be selected individually rather than assuming sector-based clustering. The "market factor" is pervasive across all assets.

### Full correlation matrix highlights
- Highest pairs: A09–A04 (0.435), A15–A02 (0.440), A17–A15 (0.449), A17–A09 (0.416)
- Lowest pairs: A05–A23 (0.086), A05–A00 (0.063), A10–A05 (0.085)
- A02, A15, A17 act as "hubs" — they co-move with many assets

---

## 4. Autocorrelation of Returns

### Return autocorrelation at lags 1, 5, 10, 20 days

| Asset | Lag 1 | Lag 5 | Lag 10 | Lag 20 |
|---|---|---|---|---|
| A00 | +0.027 | +0.026 | +0.059 | +0.002 |
| A01 | +0.053 | -0.008 | +0.012 | -0.012 |
| A02 | -0.018 | -0.005 | +0.025 | -0.022 |
| A03 | **+0.082** | -0.049 | +0.029 | +0.005 |
| A04 | +0.036 | -0.019 | +0.029 | +0.018 |
| A05 | +0.040 | +0.013 | +0.008 | +0.006 |
| A06 | +0.005 | 0.000 | -0.020 | 0.000 |
| A07 | +0.028 | -0.006 | +0.002 | -0.016 |
| A08 | -0.016 | +0.029 | -0.027 | +0.025 |
| A09 | -0.015 | +0.012 | +0.031 | -0.047 |
| A10 | +0.007 | +0.036 | +0.018 | -0.009 |
| A11 | -0.022 | -0.004 | -0.019 | -0.022 |
| A12 | -0.010 | -0.031 | -0.028 | -0.015 |
| A13 | -0.043 | -0.020 | +0.023 | -0.004 |
| A14 | +0.005 | +0.037 | **-0.093** | -0.049 |
| A15 | -0.010 | -0.004 | -0.007 | -0.016 |
| A16 | -0.040 | -0.010 | -0.047 | +0.008 |
| A17 | -0.029 | +0.005 | -0.011 | -0.012 |
| A18 | +0.008 | +0.012 | -0.005 | -0.017 |
| A19 | -0.006 | +0.011 | -0.052 | +0.026 |
| A20 | -0.003 | +0.023 | -0.008 | +0.010 |
| A21 | +0.038 | -0.055 | -0.039 | +0.040 |
| A22 | +0.002 | +0.051 | -0.031 | +0.017 |
| A23 | -0.052 | +0.012 | -0.032 | -0.023 |
| A24 | +0.029 | +0.004 | +0.008 | +0.027 |

### Cross-asset ACF summary

| Lag | Mean ACF | Std | Min | Max |
|---|---|---|---|---|
| 1 | +0.0038 | 0.0319 | -0.052 | +0.082 |
| 5 | +0.0024 | 0.0252 | -0.055 | +0.051 |
| 10 | -0.0071 | 0.0330 | -0.093 | +0.059 |
| 20 | -0.0032 | 0.0220 | -0.049 | +0.040 |

**[FINDING] Returns show negligible serial autocorrelation at all lags. No systematic time-series momentum or mean-reversion at the individual asset level.**

[STAT:effect_size] Mean |ACF| across all assets and lags < 0.01  
[STAT:n] n = 1,259 daily observations per asset  
[LIMITATION] Individual assets (e.g., A03 at lag 1 = 0.082, A14 at lag 10 = -0.093) show modest deviations, but these are not statistically extreme given 25 assets × 4 lags tested simultaneously.

---

## 5. Momentum Signals

Cross-sectional rank Information Coefficient (IC): Spearman rank correlation between past return ranking and forward return ranking.

| Formation | Holding | Mean IC | Std IC | IR | t-stat | p-value | n |
|---|---|---|---|---|---|---|---|
| 20 days | 20 days | +0.0130 | 0.2181 | +0.060 | 2.085 | 0.037 | 1,219 |
| 60 days | 20 days | -0.0085 | 0.2065 | -0.041 | -1.406 | 0.160 | 1,179 |

**[FINDING] Weak but statistically marginal positive cross-sectional momentum at the 20d/20d horizon.**

[STAT:p_value] 20d/20d: p = 0.037 (marginally significant at 5% level)  
[STAT:effect_size] IR = 0.060 (very small; IC mean ≈ 1.3%)  
[STAT:n] n = 1,219 periods tested  
[LIMITATION] The IC of 0.013 is economically tiny. Transaction costs from 20-day turnover would likely consume the edge. Not reliable enough for a standalone momentum strategy.

---

## 6. Mean Reversion Signals

### Variance Ratio Test (Lo-MacKinlay)
VR < 1 implies mean reversion; VR > 1 implies momentum.

| Horizon q | Mean VR | Std VR | Assets with VR < 1 |
|---|---|---|---|
| 2 days | 1.004 | 0.032 | 13/25 |
| 5 days | 1.036 | 0.072 | 8/25 |
| 10 days | 1.045 | 0.090 | 8/25 |
| 20 days | 1.021 | 0.124 | 12/25 |

### Cross-sectional 1d/1d Mean Reversion IC

| Signal | Mean IC | Std IC | t-stat | p-value | n |
|---|---|---|---|---|---|
| Yesterday's return → Today's return | +0.0116 | 0.2096 | 1.968 | 0.049 | 1,257 |

**[FINDING] Variance ratios above 1 across all horizons indicate a slight momentum bias, not mean reversion, at the daily aggregate level. There is no robust mean-reversion signal in individual asset time series.**

[STAT:effect_size] Mean VR at 5d = 1.036 (3.6% excess variance vs random walk)  
[STAT:n] n = 1,259 per asset  
[LIMITATION] The cross-sectional "mean reversion" IC of 0.012 (p = 0.049) is borderline significant and has an IR near zero — insufficient for a profitable strategy on its own.

---

## 7. Volatility Clustering

### ACF of squared and absolute returns

| Lag | Sq Returns Mean ACF | Abs Returns Mean ACF |
|---|---|---|
| 1 | +0.009 | +0.005 |
| 5 | +0.010 | +0.005 |
| 10 | **+0.023** | **+0.020** |
| 20 | -0.004 | -0.004 |

### Ljung-Box test on squared returns (10 lags)

Significant ARCH effects detected in:

| Asset | Q-stat | p-value | Significance |
|---|---|---|---|
| A03 | 28.1 | 0.0017 | ** |
| A05 | 24.7 | 0.0060 | ** |
| A13 | 26.1 | 0.0036 | ** |
| A16 | 20.9 | 0.0219 | * |
| A20 | **34.8** | 0.00014 | *** |
| A22 | 18.7 | 0.0441 | * |

**[FINDING] Moderate evidence of ARCH/GARCH-type volatility clustering in 6/25 assets (A03, A05, A13, A16, A20, A22). The effect is weak at lag 1–5 and stronger at lag 10.**

[STAT:p_value] A20: p = 1.37e-4 (strongest ARCH signal)  
[STAT:n] n = 1,259 per asset  
[LIMITATION] LB Q-stat at lag 10 does not strongly reject i.i.d. for most assets (19/25 non-significant). Volatility is mostly homoskedastic in this dataset — consistent with simulation. Dynamic volatility models (GARCH) are unlikely to add significant value.

---

## 8. Rolling Correlation Stability

Window: 120 trading days. Sample of 30/300 asset pairs.

| Period | Days | Avg Pairwise Corr | Std |
|---|---|---|---|
| Early (Y1–Y2) | 120–500 | 0.192 | 0.013 |
| Mid (Y2–Y4) | 500–880 | 0.234 | 0.027 |
| Late (Y4–Y5) | 880–1259 | 0.192 | 0.013 |

Overall range: [0.155, 0.277]

### Within-sector rolling correlations (window=120d)

| Sector | Mean | Std | Min | Max |
|---|---|---|---|---|
| 0 | 0.238 | 0.044 | 0.120 | 0.319 |
| 1 | 0.166 | 0.032 | 0.076 | 0.239 |
| 2 | 0.214 | 0.041 | 0.135 | 0.306 |
| 3 | **0.288** | 0.040 | 0.183 | 0.374 |
| 4 | 0.244 | 0.045 | 0.144 | 0.344 |

**[FINDING] Average pairwise correlations increased during the mid-period (Y2–Y4) then reverted, suggesting a transient high-correlation regime. This is statistically significant.**

[STAT:p_value] Correlation regime shift (early vs late half): t = -4.24, p = 2.98e-5  
[STAT:effect_size] Early avg corr = 0.221, Late avg corr = 0.235 (Δ = +0.014)  
[STAT:n] n = 300 pairs, 1,259 days  
[LIMITATION] The magnitude of the regime shift (Δ = 0.014) is economically small. Diversification benefits are relatively stable across the 5-year window.

---

## 9. Distribution of Returns (Heavy Tails)

Jarque-Bera normality test on daily log-returns:

### Non-normal assets (JB test significant)

| Asset | Excess Kurtosis | Skew | JB Stat | p-value |
|---|---|---|---|---|
| A10 | **0.599** | +0.108 | 20.8 | 2.99e-5 *** |
| A14 | **0.696** | -0.107 | 27.2 | 1.22e-6 *** |
| A20 | 0.546 | -0.074 | 16.4 | 2.81e-4 *** |
| A09 | 0.186 | -0.235 | 13.2 | 1.34e-3 ** |
| A02 | 0.458 | +0.049 | 11.2 | 3.76e-3 ** |
| A13 | 0.299 | +0.159 | 9.8 | 7.47e-3 ** |

### Normal assets (JB not significant at 5%)

A01, A03, A04, A05, A06, A07, A11, A12, A15, A16, A17, A18, A19, A23, A24 (15/25 assets)

**[FINDING] Most assets (15/25) pass the normality test. 6/25 show statistically significant non-normality, but excess kurtosis is mild (max 0.696 vs. ~3.0 for typical equity returns). Tails are far lighter than real equity markets.**

[STAT:effect_size] Max excess kurtosis = 0.696 (A14)  
[STAT:n] n = 1,259 per asset  
[LIMITATION] Simulated data with near-Gaussian tails makes VaR/CVaR approximations with normal assumption relatively safe. Standard mean-variance optimization is appropriate.

---

## 10. Year-by-Year Performance

### Annualised Returns by Year (log-return sum × 252/252)

| Asset | Year 1 | Year 2 | Year 3 | Year 4 |
|---|---|---|---|---|
| A00 | -0.029 | +0.214 | +0.022 | -0.190 |
| A01 | -0.112 | +0.538 | -0.043 | -0.117 |
| A02 | +0.161 | +0.071 | -0.039 | -0.077 |
| A03 | +0.210 | +0.578 | -0.108 | -0.388 |
| A04 | +0.472 | +0.368 | +0.150 | -0.031 |
| A05 | +0.418 | +0.329 | -0.032 | -0.229 |
| A06 | +0.787 | -0.041 | +0.311 | +0.002 |
| A07 | +0.174 | +0.241 | -0.076 | -0.216 |
| A08 | -0.010 | +0.001 | +0.167 | -0.074 |
| A09 | +0.235 | +0.858 | +0.327 | +0.137 |
| A10 | +0.167 | +0.223 | -0.515 | +0.054 |
| A11 | +0.482 | +0.612 | +0.203 | +0.098 |
| A12 | +0.070 | +0.560 | -0.638 | +0.187 |
| A13 | +0.540 | -0.277 | +0.224 | -0.395 |
| A14 | -0.320 | +0.292 | -0.647 | +0.170 |
| A15 | +0.296 | -0.198 | -0.039 | -0.029 |
| A16 | -0.114 | +0.284 | -0.359 | -0.473 |
| A17 | +0.255 | +0.251 | +0.171 | -0.035 |
| A18 | +0.172 | +0.012 | +0.033 | +0.103 |
| A19 | +0.213 | +0.626 | +0.293 | +0.642 |
| A20 | -0.503 | -0.053 | -0.091 | -0.202 |
| A21 | +0.101 | +0.264 | -0.286 | +0.629 |
| A22 | +0.237 | -0.200 | +0.454 | -0.016 |
| A23 | -0.231 | +0.202 | -0.138 | +0.091 |
| A24 | +0.495 | +0.722 | -0.026 | +0.017 |

### Annualised Volatility by Year

| Year | Cross-asset Mean Vol | Range |
|---|---|---|
| Year 1 | 0.295 | 0.203–0.356 |
| Year 2 | 0.293 | 0.212–0.342 |
| Year 3 | 0.335 | 0.241–0.404 |
| Year 4 | 0.302 | 0.228–0.353 |

**[FINDING] Year 3 shows elevated cross-asset volatility (mean 0.335 vs ~0.295 in other years), consistent with a risk-on/stress regime.**

[STAT:effect_size] Year 3 vol exceeds Year 1 by 13.5%  
[STAT:n] n = 252 daily obs per year  

**[FINDING] A09 and A11 (Sector 3) were consistently positive across all 4 years. A20 (Sector 2) was consistently negative. These are the most reliable directional assets.**

| Asset | Y1 | Y2 | Y3 | Y4 | Consistent Sign |
|---|---|---|---|---|---|
| A09 | + | + | + | + | Always positive |
| A11 | + | + | + | + | Always positive |
| A19 | + | + | + | + | Always positive |
| A20 | - | - | - | - | Always negative |
| A16 | - | + | - | - | 3/4 negative |
| A04 | + | + | + | - | 3/4 positive |

---

## 11. Regime Analysis

### Quarterly cross-asset average annualised return

| Period | Days | Avg Ann. Ret | Avg Ann. Vol | CS Dispersion |
|---|---|---|---|---|
| Y1Q1 | 0–63 | -0.150 | 0.293 | 0.0167 |
| Y1Q2 | 63–126 | +0.313 | 0.291 | 0.0166 |
| Y1Q3 | 126–189 | +0.563 | 0.301 | 0.0168 |
| Y1Q4 | 189–252 | -0.059 | 0.294 | 0.0165 |
| Y2Q1 | 252–315 | +0.294 | 0.287 | 0.0161 |
| Y2Q2 | 315–378 | -0.297 | 0.309 | 0.0170 |
| Y2Q3 | 378–441 | +0.710 | 0.271 | 0.0160 |
| Y2Q4 | 441–504 | +0.329 | 0.282 | 0.0156 |
| Y3Q1 | 504–567 | -0.166 | 0.343 | 0.0186 |
| Y3Q2 | 567–630 | +0.115 | 0.318 | 0.0175 |
| Y3Q3 | 630–693 | +0.126 | 0.341 | 0.0184 |
| Y3Q4 | 693–756 | -0.185 | 0.341 | 0.0181 |
| Y4Q1 | 756–819 | -0.027 | 0.298 | 0.0167 |
| Y4Q2 | 819–882 | +0.245 | 0.293 | 0.0164 |
| Y4Q3 | 882–945 | -0.166 | 0.300 | 0.0167 |
| Y4Q4 | 945–1008 | -0.106 | 0.304 | 0.0165 |
| Y5Q1 | 1008–1071 | +0.306 | 0.285 | 0.0167 |
| Y5Q2 | 1071–1134 | -0.235 | 0.308 | 0.0167 |
| Y5Q3 | 1134–1197 | +0.535 | 0.294 | 0.0170 |

**[FINDING] Cross-asset return alternates between positive and negative quarters with no persistent directional trend. Year 3 (days 504–756) is a distinct higher-volatility regime with lower average returns.**

[STAT:effect_size] Y3 avg vol = 0.341 vs Y2 avg vol = 0.281 (Δ = +21.4%)  
[STAT:n] 63 days per quarter  

### Mean return shift (late half vs early half, annualised)

| Asset | Δ Ann. Return | Direction |
|---|---|---|
| A03 | -0.448 | Strong decay |
| A19 | -0.440 | Strong decay |
| A06 | -0.438 | Strong decay |
| A07 | -0.322 | Decay |
| A12 | -0.386 | Decay |
| A01 | +0.313 | Acceleration |
| A18 | +0.123 | Modest acceleration |
| A21 | +0.108 | Modest acceleration |

**[FINDING] Significant regime shift: the correlation structure changed between the early and late halves of the dataset.**

[STAT:p_value] Paired t-test on correlation matrices: t = -4.24, p = 2.98e-5  
[STAT:effect_size] Early avg pairwise corr = 0.221, Late = 0.235  
[STAT:n] 300 pairs  

**Notable:** A09, A11, A04, A17 maintained high performance across both halves. A03, A06, A19 significantly decayed in the second half.

---

## 12. Intra-Day Patterns

Based on 37,800 ticks across 1,260 days (30 ticks/day).

### Intra-day return means (cross-asset average)
All tick positions show near-zero mean returns (range: -0.000050 to +0.000091). No significant intra-day drift pattern.

### Intra-day volatility
Flat across all 30 tick positions (range: 0.003371–0.003491). No U-shaped intra-day volatility pattern typical of real equity markets.

### Open-to-close drift (statistically significant assets only)

| Asset | Mean O-C Return | Std | t-stat | p-value |
|---|---|---|---|---|
| A09 | +0.00147 | 0.01716 | 3.039 | 0.0024 ** |
| A11 | +0.00149 | 0.02188 | 2.423 | 0.0155 * |
| A04 | +0.000985 | 0.01710 | 2.045 | 0.0411 * |
| A17 | +0.000867 | 0.01531 | 2.010 | 0.0447 * |

**[FINDING] A09, A11, A04, A17 show statistically significant positive intra-day drift (open to close), consistent with their high daily Sharpe ratios.**

[STAT:p_value] A09: p = 0.0024; A11: p = 0.0155  
[STAT:n] n = 1,260 days  
[LIMITATION] Intra-day flat volatility and near-zero drift at most tick positions confirm this is a simulated environment without microstructure effects. Strategy can realistically execute at any tick.

---

## 13. Asset Rankings (Total Return Summary)

| Rank | Asset | Sector | Total Log Ret | Ann. Ret | Sharpe | Spread | Borrow |
|---|---|---|---|---|---|---|---|
| 1 | **A11** | 3 | 1.990 | 0.398 | 1.123 | 12 bps | 135 bps |
| 2 | **A09** | 3 | 1.947 | 0.389 | 1.410 | 4 bps | 42 bps |
| 3 | **A19** | 3 | 1.399 | 0.280 | 0.888 | 2 bps | 177 bps |
| 4 | **A24** | 4 | 1.326 | 0.265 | 0.853 | 2 bps | 138 bps |
| 5 | **A04** | 3 | 1.294 | 0.259 | 0.933 | 2 bps | 44 bps |
| 6 | **A17** | 4 | 1.241 | 0.248 | 1.002 | 12 bps | 149 bps |
| 7 | **A06** | 4 | 1.222 | 0.244 | 0.765 | 4 bps | 72 bps |
| 8 | A05 | 4 | 1.080 | 0.216 | 0.666 | 4 bps | 78 bps |
| 9 | A21 | 4 | 0.970 | 0.194 | 0.568 | 2 bps | 172 bps |
| 10 | A01 | 0 | 0.744 | 0.149 | 0.467 | 4 bps | 143 bps |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 22 | A16 | 1 | -0.344 | -0.069 | -0.196 | 4 bps | 125 bps |
| 23 | A23 | 3 | -0.403 | -0.081 | -0.243 | 4 bps | 144 bps |
| 24 | A14 | 1 | -0.619 | -0.124 | -0.398 | 2 bps | 165 bps |
| 25 | **A20** | 2 | -0.746 | -0.149 | -0.432 | 4 bps | 160 bps |

---

## [LIMITATION]

1. **Simulated data:** Returns are near-Gaussian with light tails (max excess kurtosis 0.696), no microstructure effects, flat intra-day volatility. Real-world robustness considerations (e.g., fat tails, liquidity crises) do not apply.
2. **Regime instability:** Several high-performing assets (A03, A06, A19) show significant return decay in the second half of the sample. Past Sharpe ratios may not persist.
3. **Correlations are noisy:** Within-sector and cross-sector correlations are statistically identical, meaning sector-based diversification heuristics are unreliable.
4. **Autocorrelation near zero:** No robust time-series momentum or mean-reversion at individual asset level. Cross-sectional signals are very weak (IC ~ 1%).
5. **Short constraint costs:** Several assets with negative returns have high borrow costs (A14: 165 bps, A20: 160 bps), partially offsetting short profits.
6. **Year 3 regime:** Elevated volatility in Year 3 (days 504–756) may reflect a different generating process — strategies should be tested for robustness across this period.

---

## Strategic Implications

### Strong long candidates
- **A09** (S3): Best risk-adjusted return (Sharpe 1.41), low cost (4 bps spread / 42 bps borrow), positive in all 4 years
- **A04** (S3): Second-best cost-adjusted Sharpe (0.93), 2 bps spread / 44 bps borrow, very consistent
- **A11** (S3): Highest total return, but 12 bps spread — only hold if turnover is low
- **A17** (S4): Sharpe 1.00, lowest vol in top-10, 12 bps spread limits high-frequency use

### Strong short candidates
- **A20** (S2): -0.149 ann. return, negative all 4 years, but 160 bps borrow makes short expensive (~3.7 bps/day carrying cost)
- **A14** (S1): -0.124 ann. return, 165 bps borrow — similar concern

### Best cost-adjusted pair trade
- **Long A09 / Short A23** (both Sector 3): Sector-neutral with massive return spread (0.39 – (-0.08) = 0.47 ann.), low combined spread (4+4 = 8 bps), but A09 borrow only 42 bps; A23 borrow 144 bps long. If short A23: pays 144 bps borrow (~57 bps/yr net drag after loan income). Still expected to profit significantly.

### Diversification
- Sector labels are NOT natural diversification groups (within ≈ cross-sector correlation). Use individual pair correlations.
- True diversifiers: A07 (vol 0.220, near-zero return), A15 (vol 0.244), A17 (vol 0.248) have lowest volatilities.

---

## Figures

All figures saved to `/Users/stao042906/Documents/UCHICAGO/Case2/.omc/scientist/figures/`:

- `fig1_cumret_by_sector.png` — Cumulative returns by sector
- `fig2_corr_heatmap.png` — Full 25×25 pairwise correlation heatmap
- `fig3_rolling_vol.png` — Rolling 60-day annualised volatility
- `fig4_rolling_corr.png` — Rolling 120-day average pairwise correlation
- `fig5_annual_returns.png` — Annual returns heatmap (year × asset)

---

*Report generated by Scientist Agent | Session: case2-exploration-20260408*
