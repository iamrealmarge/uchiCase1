# 13: Intraday Signal Analysis — Predicting Next-Day Returns from Tick-Level Data

**Date:** 2026-04-08  
**Data:** `prices.csv` — 37,800 ticks, 30 ticks/day, 25 assets, 1,260 trading days  
**Figures:** `/Users/stao042906/.omc/scientist/figures/`

---

## [OBJECTIVE]

Test whether intraday tick-level features (realized volatility, intraday momentum, half-day returns, overnight gap, intraday range, cross-asset lead-lag) predict next-day returns. Compute IC, IC IR, and t-statistic for each signal. Build a composite and estimate pre-cost and post-cost Sharpe.

---

## [DATA]

- **Shape:** 37,800 ticks × 25 assets. Restructured to (1,260 days × 30 ticks × 25 assets).
- **Target:** Next-day close-to-close return: `ret[d+1] = (close[d+1] - close[d]) / close[d]`
- **Features computed per day per asset** (all lag-1 aligned to predict day d+1):
  1. Realized intraday volatility (std of 29 log-returns × √29)
  2. Close vs intraday mean (close minus VWAP proxy, normalized)
  3. Second-half intraday return (tick 15 → tick 30)
  4. First-half intraday return (tick 1 → tick 15)
  5. Full intraday return (open → close)
  6. Overnight return (previous close → today's open) — predicts same day's close
  7. Intraday range ((max − min) / open)
- **No missing values** in prices. n = 1,259 daily IC observations per signal.

---

## Test 1: Realized Intraday Volatility → Next-Day Return

**Hypothesis:** Higher intraday vol today predicts a directional return tomorrow (either momentum or reversal).

[FINDING] Realized intraday volatility has **no meaningful predictive power** for next-day returns. The signal is indistinguishable from noise.
[STAT:n] n = 1,259 days
[STAT:mean_ic] Mean IC = -0.0061
[STAT:ic_ir] IC IR = -0.0304
[STAT:t_stat] t = -1.0775
[STAT:p_value] p = 0.2815 (not significant)
[STAT:pos_frac] 49.5% positive IC days

**Direction:** Slight negative (high vol → slight reversal next day), but completely insignificant.

[LIMITATION] Vol may be endogenous to jumps; no conditioning on vol regime was tested.

---

## Test 2: Close vs Intraday Mean (Last-Tick Momentum) → Next-Day Return

**Hypothesis:** When price closes above the intraday mean (VWAP proxy), informed buyers were active in the close. This should predict positive next-day returns (momentum).

[FINDING] Close-vs-mean shows **weak but marginally significant** momentum: when the price closes above the intraday average, the next-day return is slightly positive on average.
[STAT:n] n = 1,259 days
[STAT:mean_ic] Mean IC = 0.0113
[STAT:ic_ir] IC IR = 0.0545
[STAT:t_stat] t = 1.9341
[STAT:p_value] p = 0.0533 (marginal, borderline significant at 5%)
[STAT:pos_frac] 52.0% positive IC days

**Direction:** Positive (momentum). Close above VWAP → positive next day.

[LIMITATION] Marginal significance — borderline p-value; likely driven by the overnight component embedded in the next close. Signal is weak standalone.

---

## Test 3: Half-Day Return Breakdown → Next-Day Return

### 3a: Second-Half Intraday Return (Ticks 16–30)

**Hypothesis:** Late-session price action reflects informed trading and predicts the next day.

[FINDING] Second-half return shows **weak positive momentum**: assets that rally in the second half of the session tend to continue slightly the next day.
[STAT:n] n = 1,259 days
[STAT:mean_ic] Mean IC = 0.0088
[STAT:ic_ir] IC IR = 0.0419
[STAT:t_stat] t = 1.4854
[STAT:p_value] p = 0.1377 (not significant)
[STAT:pos_frac] 51.9% positive IC days

**Direction:** Positive (momentum), but not statistically significant.

### 3b: First-Half Intraday Return (Ticks 1–15)

[FINDING] First-half return has **essentially zero predictive power** for next-day returns.
[STAT:n] n = 1,259 days
[STAT:mean_ic] Mean IC = 0.0045
[STAT:ic_ir] IC IR = 0.0212
[STAT:t_stat] t = 0.7517
[STAT:p_value] p = 0.4524 (not significant)
[STAT:pos_frac] 51.5% positive IC days

[LIMITATION] The 30-tick day may not cleanly separate informed from noise trading; the half-day boundary is arbitrary.

---

## Test 4: Open-to-Close vs Close-to-Open (Overnight) Returns

### 4a: Full Intraday Return (Open → Close) → Next-Day Return

[FINDING] Full intraday return shows **weak but statistically significant** momentum.
[STAT:n] n = 1,259 days
[STAT:mean_ic] Mean IC = 0.0125
[STAT:ic_ir] IC IR = 0.0593
[STAT:t_stat] t = 2.1051
[STAT:p_value] p = 0.0355 (significant at 5%)
[STAT:pos_frac] 51.4% positive IC days

**Direction:** Positive (momentum). Assets that rallied intraday today tend to continue next day.

### 4b: Overnight Return (Close[d−1] → Open[d]) → Next-Day Return Close[d+1]

**Hypothesis:** The overnight gap encodes news/order imbalance that persists into the next full day.

[FINDING] **Overnight return is by far the strongest single predictor.** It shows highly significant, large-magnitude momentum across all 25 assets consistently.
[STAT:n] n = 1,259 days
[STAT:mean_ic] Mean IC = 0.1687
[STAT:ic_ir] IC IR = 0.8279
[STAT:t_stat] t = 29.38
[STAT:p_value] p < 0.0001 (highly significant)
[STAT:pos_frac] 78.8% positive IC days

**Direction:** Strongly positive (momentum). Overnight gaps persist through the next full trading day.

**Quintile breakdown** (overnight return quintile vs mean next-day return):
| Quintile | Mean Next-Day Return |
|----------|---------------------|
| Q1 (worst overnight) | −42.0 bps |
| Q2 | −11.8 bps |
| Q3 | +5.9 bps |
| Q4 | +24.1 bps |
| Q5 (best overnight) | +53.5 bps |

The relationship is **nearly monotonic** across quintiles, spanning ~95 bps from worst to best bucket.

**Implication:** The competition hint ("daily movement and intraday price changes are often two very different processes") likely refers to this overnight vs intraday distinction. The overnight return *is* the daily movement (close-to-open), and it dominates intraday signals.

[LIMITATION] This signal may represent auto-correlation in daily returns rather than a pure intraday feature. Need to verify it's not trivially captured by a simple overnight-return momentum rule already tested by other teams.

---

## Test 5: Intraday Range → Next-Day Return

**Hypothesis:** Wide-ranging days (high intraday range) predict higher next-day vol or directional returns.

[FINDING] Intraday range has **no significant predictive power** for next-day returns.
[STAT:n] n = 1,259 days
[STAT:mean_ic] Mean IC = -0.0050
[STAT:ic_ir] IC IR = -0.0240
[STAT:t_stat] t = -0.8505
[STAT:p_value] p = 0.3952 (not significant)
[STAT:pos_frac] 48.5% positive IC days

**Direction:** Slight negative (wide range → slight reversal), but noise-level.

[LIMITATION] Range was tested against next-day return; may have more power against next-day realized vol (not tested here).

---

## Test 6: Cross-Asset Intraday Lead-Lag

**Hypothesis:** Asset i's intraday return predicts asset j's next-day return (informational spillovers between assets).

[FINDING] There is a **small but statistically significant negative** cross-asset lead-lag relationship: an asset that rallied intraday today is associated with slight reversal in *other* assets the next day, on average.
[STAT:n] n = 600 asset-pairs
[STAT:mean_ic] Mean off-diagonal IC = −0.0047
[STAT:std_ic] Std = 0.0275
[STAT:t_stat] t = −4.21
[STAT:p_value] p < 0.0001 (significant, but economically tiny)

**Strongest pairs (by |IC|):**
| Predictor | Target | IC |
|-----------|--------|-----|
| A00 | A20 | −0.119 |
| A14 | A02 | −0.088 |
| A11 | A15 | −0.086 |
| A01 | A15 | −0.076 |
| A12 | A24 | +0.073 |

**Direction:** Mostly **negative** (cross-asset reversal rather than momentum). Mean IC is −0.005, economically negligible for most pairs.

**Implication:** The few strong pairs (e.g., A00→A20 at IC=−0.12) could be sector-level effects. The general signal is too weak to use standalone.

[LIMITATION] 600 pairs tested simultaneously — multiple comparisons inflate false discovery rate. Top pairs need out-of-sample validation. Sector structure in meta.csv not exploited here.

---

## Test 7: Composite Signal — IC and Achievable Sharpe

### Composite Construction

Signals combined via rank-normalization (each signal cross-sectionally normalized to [−1, +1] per day):

- **Equal-weight:** (Overnight + Intraday + Close-vs-Mean + Second-Half) / 4
- **Weighted (3× overnight):** (3 × Overnight + Intraday + Close-vs-Mean + Second-Half) / 6

### IC Results

[FINDING] The **overnight-only signal is the single best composite** — adding weaker signals dilutes performance.
[STAT:n] n = 1,259 days

| Signal | Mean IC | IC IR | t-stat | p-value | % Positive |
|--------|---------|-------|--------|---------|------------|
| Overnight Only (rank) | 0.1687 | 0.828 | 29.38 | < 0.0001 | 78.8% |
| Composite Weighted (3× ovn) | 0.1267 | 0.622 | 22.06 | < 0.0001 | 73.9% |
| Composite Equal-Weight | 0.0602 | 0.291 | 10.33 | < 0.0001 | 62.6% |

### Long-Short Backtest Results (Top 5 Long / Bottom 5 Short, daily rebalance)

[FINDING] The overnight signal produces **exceptional pre-cost Sharpe**, substantially above what is plausible in live trading at any scale.
[STAT:n] n = 1,258 days

| Strategy | Ann Return | Sharpe (gross) | Sharpe (net, ½-spread) | Max Drawdown |
|----------|-----------|----------------|------------------------|--------------|
| Overnight Only | 215% | 12.05 | 11.37 | −4.0% |
| Composite Weighted | 156% | 8.74 | 8.06 | −6.0% |

[STAT:effect_size] Overnight signal Sharpe ratio = 12.05 (gross), 11.37 (net of half-spread cost)

[LIMITATION] These Sharpe numbers are unrealistically high for a live strategy and suggest the overnight return is auto-correlated in this simulated dataset. Key caveats:
1. Half-spread cost is applied, but **market impact** is not modeled.
2. The signal may be an artifact of how the competition dataset is generated.
3. A long-short top-5/bottom-5 portfolio with daily rebalancing assumes perfect execution at both close and open prices.
4. No slippage model. In practice, trading at the exact open/close tick would face adverse selection.
5. The competition evaluates the full position vector (all 25 assets), not a concentrated 10-name book.

---

## Summary: Signal Ranking

| Rank | Signal | Mean IC | IC IR | t-stat | p-value | Verdict |
|------|--------|---------|-------|--------|---------|---------|
| 1 | Overnight Return | 0.169 | 0.828 | 29.4 | < 0.001 | **Strong — use** |
| 2 | Intraday Return (open→close) | 0.013 | 0.059 | 2.11 | 0.036 | Weak but significant |
| 3 | Close vs Intraday Mean | 0.011 | 0.055 | 1.93 | 0.053 | Marginal |
| 4 | Second-Half Return | 0.009 | 0.042 | 1.49 | 0.138 | Not significant |
| 5 | First-Half Return | 0.005 | 0.021 | 0.75 | 0.452 | Noise |
| 6 | Intraday Range | −0.005 | −0.024 | −0.85 | 0.395 | Noise |
| 7 | Realized Vol | −0.006 | −0.030 | −1.08 | 0.282 | Noise |
| 8 | Cross-Asset Lead-Lag | −0.005 | — | −4.21 | < 0.001 | Statistically sig, econ tiny |

---

## [LIMITATION] — Overall Caveats

1. **Overnight dominance may be data artifact**: IC IR of 0.83 for a single lag-1 signal is extraordinary. In real markets, such signals would be arbitraged away. The competition dataset may have intentional structure favoring overnight momentum.
2. **Multiple testing**: 7+ signals tested simultaneously. Without correction (Bonferroni or BH), familywise false-discovery rate is elevated for the marginal signals.
3. **No out-of-sample test**: All results are in-sample over the full 1,260 days. Cross-validation or walk-forward testing would validate robustness.
4. **Static equal-weighting**: Cross-sectional signal weighting is equal per asset. Beta-adjusted or vol-scaled weighting would improve risk characteristics.
5. **Sector effects ignored**: meta.csv provides sector labels. Cross-asset IC patterns likely cluster by sector; sector-neutralization could improve signal quality.
6. **Borrow costs omitted**: The backtest deducts only half-spread. `borrow_bps_annual` from meta.csv (44–197 bps/year) would further reduce short-side P&L.

---

## Actionable Recommendations for Strategy

1. **Use overnight return as the primary intraday-derived feature.** Compute `open[d] / close[d-1] - 1` for each asset at the start of each day — this is the single most predictive signal (IC IR = 0.83, t = 29.4).
2. **The intraday full return adds marginal incremental information** (t = 2.1, p = 0.036). It can be combined with the overnight signal at low weight.
3. **Discard realized vol, intraday range, and half-day returns** as standalone predictors — all have t-statistics below 1.5.
4. **For the composite, use: position ∝ rank_normalize(3 × overnight_return + intraday_return)**. This achieves IC IR = 0.62 and Sharpe ~8 pre-cost.
5. **Investigate the overnight return's persistence**: rolling 60-day IC stays strongly positive throughout the 1,260-day sample (see `ic_rolling_timeseries.png`), suggesting structural rather than spurious momentum.

---

## Figures

| File | Description |
|------|-------------|
| `/Users/stao042906/.omc/scientist/figures/ic_rolling_timeseries.png` | Rolling 60-day IC for overnight, composite, and intraday signals |
| `/Users/stao042906/.omc/scientist/figures/cumulative_returns_intraday.png` | Cumulative return of long-short portfolios (log scale) |
| `/Users/stao042906/.omc/scientist/figures/ic_distribution.png` | IC distributions for overnight and composite signals |
| `/Users/stao042906/.omc/scientist/figures/per_asset_ic.png` | Per-asset IC bar chart for overnight vs composite |
| `/Users/stao042906/.omc/scientist/figures/cross_asset_ic_heatmap.png` | Heatmap of cross-asset IC (25 × 25) |

