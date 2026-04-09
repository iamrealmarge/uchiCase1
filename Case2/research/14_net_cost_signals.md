# Net-of-Cost Signal Analysis
**Date:** 2026-04-08
**Analysis:** Transaction cost impact on momentum signals and portfolio construction

---

## [OBJECTIVE]

Determine whether cross-sectional momentum signals survive realistic transaction costs and identify the optimal implementation parameters (dampening, formation/holding periods, universe selection, rebalancing frequency, drift thresholds) for a long-short equity strategy.

---

## [DATA]

- **Prices:** 37,800 ticks, 30 ticks/day → 1,260 EOD observations (1,259 daily returns)
- **Assets:** 25 assets across 3 sectors
- **Spreads:** 2–12 bps (mean: see meta.csv)
- **Borrow costs:** 23–197 bps/year
- **Transaction cost model:** Linear = (spread_bps/2) × |Δw|; Quadratic = 2.5 × spread_bps × Δw²; Borrow = borrow_bps_annual/252 × |short_weight|

---

## Task 1: 5-Day Momentum NET of Costs

### [FINDING] 5-day cross-sectional momentum is DESTROYED by transaction costs when rebalanced daily.

The strategy with PRE-COST IC IR = 1.43 collapses to a near-zero Sharpe ratio after costs.

| Metric | Value |
|--------|-------|
| Net Sharpe Ratio | **-0.015** |
| Net Annualized Return | -0.28% |
| Net Annualized Volatility | 18.03% |
| Total Transaction Costs (cumulative) | **93.25%** of portfolio |
| Annualized Turnover | 359.57× |

[STAT:n] n = 1,259 daily return observations
[STAT:effect_size] Pre-cost IC IR = 1.43 → Post-cost Sharpe = -0.015 (complete signal destruction)

**Interpretation:** Annualized turnover of 360× means the strategy is trading its entire book roughly every business day. With spreads averaging ~6 bps, this generates ~93% cumulative transaction costs over the sample — completely overwhelming any alpha.

[LIMITATION] Total cost > 100% is theoretically possible in a leveraged long-short book since both legs incur costs. The number reflects the gross cumulative cost across 1,259 days.

---

## Task 2: Turnover Dampening via Weight Blending

Strategy: `w_new = α × w_signal + (1-α) × w_prev`

### [FINDING] Turnover dampening significantly improves net Sharpe; optimal blend factor is α = 0.5.

| Alpha | Net Sharpe | Ann. Turnover | Cumulative Cost |
|-------|-----------|---------------|-----------------|
| 0.05  | 0.018     | 28.9×         | 6.1%            |
| 0.10  | 0.140     | 58.0×         | 11.0%           |
| 0.20  | 0.287     | 112.0×        | 20.0%           |
| 0.30  | 0.383     | 158.7×        | 28.4%           |
| **0.50**  | **0.420** | **232.6×**    | **44.2%**       |
| 1.00  | -0.015    | 359.6×        | 93.3%           |

[STAT:effect_size] Best α=0.5 achieves Sharpe = 0.420, vs. -0.015 unblended (improvement: +0.435 Sharpe units)
[STAT:n] n = 1,259 daily observations per alpha configuration

**Interpretation:** The monotonic improvement from α=0.05 to α=0.5 shows the signal has genuine predictive content but needs time-averaging to reduce turnover. However, even at α=0.5, turnover is still 233× annually — significantly above what is efficient.

**Key insight:** At very low alpha (0.05), turnover is minimal but the signal barely gets incorporated — the portfolio stagnates. At high alpha (1.0 = no dampening), costs destroy all alpha. The sweet spot is α=0.5 where signal incorporation and cost control balance.

[LIMITATION] α=0.5 still incurs 44% cumulative costs. A Sharpe of 0.42 is marginally positive but not competitive. The optimal alpha may vary with spread environment.

---

## Task 3: Signal Formation × Holding Period Sweep (Net Sharpe)

### [FINDING] 3-day formation / 5-day holding is the best parameter combination with Net Sharpe = 1.04.

Net Sharpe heatmap by (formation, holding) period:

| Formation \ Holding | 1d      | 5d      | 10d     | 21d     |
|---------------------|---------|---------|---------|---------|
| 1d                  | **-1.72** | -0.06   | -0.19   | -0.49   |
| 3d                  | -0.37   | **1.04** | 0.68    | 0.06    |
| 5d                  | -0.02   | 0.16    | -0.06   | 0.12    |
| 10d                 | 0.24    | 0.18    | -0.16   | -0.16   |
| 20d                 | -0.25   | -0.07   | -0.19   | 0.18    |
| 60d                 | -0.19   | 0.26    | -0.07   | -0.42   |

[STAT:effect_size] Best combo (form=3, hold=5): Net Sharpe = 1.04 vs. worst (form=1, hold=1): -1.72
[STAT:n] n = 1,259 daily observations per configuration

**Key patterns:**
1. Daily rebalancing (hold=1) consistently produces negative Sharpe for most formation periods — costs dominate.
2. Formation = 1 day is universally bad: very high turnover, no signal stability.
3. Formation = 3 days is the best formation period. The signal captures short-term reversals/momentum with manageable turnover when held 5+ days.
4. Longer formations (20d, 60d) are inconsistent — the signal either decays too slowly or picks up noise.

### [FINDING] Formation period matters more than holding period for net performance.

The 3-day formation period works well across multiple holding periods (1.04, 0.68, 0.06 for holds 5/10/21), while 1-day and 20-day formations are poor regardless of holding period.

[LIMITATION] Parameter selection on the same dataset introduces look-ahead bias. These parameters should be validated on a held-out period.

---

## Task 4: Cost-Aware Universe (Low-Spread Assets Only)

Low-spread universe (≤4 bps): **17 of 25 assets**
Assets: A01, A02, A04, A05, A06, A08, A09, A12, A13, A14, A15, A16, A19, A20, A21, A23, A24

### [FINDING] Restricting to low-spread assets does NOT improve net Sharpe when using daily rebalancing.

| Universe | Assets | Net Sharpe | Cumulative Cost |
|----------|--------|-----------|-----------------|
| Full     | 25     | -0.015    | 93.25%          |
| Low-spread (≤4 bps) | 17 | -0.001 | 83.92% |

[STAT:effect_size] Improvement in Sharpe: +0.014 (negligible); Cost reduction: -9.33%
[STAT:n] n = 1,259 daily observations

**Interpretation:** The turnover is so high that even with cheaper assets, costs still overwhelm alpha. The fundamental problem is rebalancing frequency, not asset selection. Costs are proportional to turnover; reducing spread by ~33% (from full to cheap universe) reduces costs proportionally, but the signal is still negative before costs at this frequency.

**Implication:** Cheap asset selection is meaningful only when combined with reduced turnover (e.g., longer holding periods or drift-based rebalancing).

[LIMITATION] The cheap universe has only 17 assets; with top-5/bottom-5 strategy, diversification is reduced.

---

## Task 5: Optimal Rebalancing Frequency by Strategy Type

### [FINDING] Inverse-volatility weighting is robust to rebalancing frequency; Sharpe ≈ 1.0 across all frequencies tested.

| Rebal Freq | Inv-Vol Sharpe | Sharpe-Weighted Sharpe | Momentum Sharpe |
|-----------|----------------|----------------------|-----------------|
| Daily (1d) | 1.009         | 0.994                | 0.030           |
| Weekly (5d) | 1.010        | 0.987                | 0.196           |
| Biweekly (10d) | 1.012    | 0.894                | 0.019           |
| Monthly (21d) | **1.021** | 0.812                | 0.136           |
| Quarterly (63d) | 1.014  | **1.004**            | -0.322          |

[STAT:effect_size] Best: Inv-Vol @ 21d (Sharpe=1.021); Momentum best @ 5d (Sharpe=0.196)
[STAT:n] n = 1,259 daily observations, 60-day estimation window

**Key findings by strategy:**

**Inverse Volatility:** Remarkably stable across all frequencies (1.009–1.021). This is because inv-vol weights change slowly — assets with similar volatilities don't need constant rebalancing. BEST at **21-day frequency**.

**Sharpe-Weighted:** Degrades with medium frequencies (10d: 0.89, 21d: 0.81) but recovers at quarterly rebalancing (1.004). This U-shaped pattern suggests Sharpe estimates are noisy at short windows and benefit from infrequent re-estimation. BEST at **63-day frequency**.

**Momentum:** Never achieves competitive Sharpe. Best at 5-day (0.196) but performance is inconsistent. At 63-day frequency, Sharpe turns negative (-0.322) — momentum signals go stale. BEST at **5-day frequency**.

### [FINDING] Inv-Vol and Sharpe-weighted strategies are dramatically superior to momentum on a NET basis.

Momentum's best net Sharpe (0.196 at 5d rebalancing) is 5× lower than inv-vol (1.021). The pre-cost IC IR advantage of momentum cannot survive its inherent high turnover.

[LIMITATION] 60-day rolling window for estimation may be too short for stable covariance estimates in some regimes.

---

## Task 6: Drift-Based Rebalancing

### [FINDING] Drift-based rebalancing provides no improvement over time-based rebalancing for 5-day momentum.

| Drift Threshold | Net Sharpe | Rebalance Events | Cumulative Cost |
|----------------|-----------|------------------|-----------------|
| 0.5%           | -0.015    | 1,251            | 93.25%          |
| 1.0%           | -0.015    | 1,251            | 93.25%          |
| 2.0%           | -0.015    | 1,251            | 93.25%          |
| 5.0%           | -0.015    | 1,251            | 93.25%          |

[STAT:effect_size] Zero improvement across all thresholds
[STAT:n] n = 1,259 daily observations

**Interpretation:** The drift condition triggers on virtually every day (1,251 out of 1,259 days). This occurs because the 5-day momentum signal generates entirely new discrete target weights each day — the target portfolio itself shifts by >5% at nearly every step. Drift-based rebalancing is only effective when the *target* portfolio is stable and only *current* weights drift due to price movements.

**Conclusion:** Drift-based rebalancing is incompatible with high-frequency momentum signals. It is well-suited to low-turnover strategies (e.g., strategic allocation, inv-vol) where the target changes slowly.

[LIMITATION] Drift threshold would need to be tested with the blended (dampened) momentum strategy where the target weight is more stable.

---

## Overall Summary and Recommendations

### Critical takeaway: Pre-cost IC IR is misleading for high-turnover strategies.

| Implementation | Net Sharpe | Recommendation |
|---------------|-----------|----------------|
| 5d momentum, daily rebal (naive) | -0.015 | Do not use |
| 5d momentum, α=0.5 dampening | 0.420 | Marginal — investigate further |
| **3d formation / 5d hold** | **1.040** | **Best momentum implementation** |
| Momentum, 5d rebal | 0.196 | Acceptable |
| Low-spread universe only | -0.001 | Negligible improvement alone |
| **Inv-Vol, 21d rebal** | **1.021** | **Best risk-adjusted, lowest cost** |
| Sharpe-weighted, 63d rebal | 1.004 | Comparable to inv-vol |
| Drift-based (5-day mom) | -0.015 | Ineffective for momentum |

### Actionable Recommendations

1. **Abandon daily momentum rebalancing.** It loses money after costs regardless of signal quality.
2. **Use 3-day formation / 5-day holding** as the optimal momentum specification (Net Sharpe = 1.04).
3. **Blend momentum with inv-vol.** Inv-vol at Net Sharpe ≈ 1.02 is robust and cheap. Momentum adds return only with careful parameter selection.
4. **Rebalance monthly for inv-vol** (Net Sharpe = 1.021) — lowest turnover, highest Sharpe.
5. **Drift-based rebalancing** should be applied to inv-vol or Sharpe-weighted portfolios, not to momentum strategies. Test thresholds on the dampened momentum target.
6. **Low-spread universe restriction** is only useful when combined with reduced turnover — test in combination with 5-day holding.

---

## [LIMITATION]

1. **In-sample parameter selection:** All parameters (formation, holding, alpha, threshold) are selected on the full dataset. Out-of-sample performance will likely be worse.
2. **No market impact model beyond quadratic:** Large orders may face additional impact not captured by the quadratic cost model.
3. **Single-path simulation:** No Monte Carlo uncertainty quantification on Sharpe ratios.
4. **Constant spreads assumption:** Spreads are fixed from meta.csv; real spreads widen in stress periods.
5. **Drift-based rebalancing** was only tested with unblended momentum targets. The analysis should be repeated with dampened (α=0.5) targets.
6. **Borrow cost model:** Annual borrow rates are annualized linearly; actual borrow availability and costs fluctuate.

---

## Files

- **Report:** `/Users/stao042906/Documents/UCHICAGO/Case2/research/14_net_cost_signals.md`
- **Figure:** `/Users/stao042906/Documents/UCHICAGO/Case2/.omc/scientist/figures/14_net_cost_signals.png`
- **Summary JSON:** `/Users/stao042906/Documents/UCHICAGO/Case2/.omc/scientist/reports/14_summary.json`
- **Analysis Script:** `/tmp/net_cost_analysis.py`

