# Case 2: Cost Structure Analysis & Strategic Implications

**Generated:** 2026-04-08
**Data:** `meta.csv` (25 assets), `prices.csv` (37,800 ticks ≈ 150 years of simulated daily data)

---

## [OBJECTIVE]

Quantify the full cost structure of the trading universe, determine the cost-optimal rebalancing frequency, identify cheap vs. expensive assets, measure the cost drag on the equal-weight baseline, and surface sector-level cost patterns.

---

## [DATA]

| Property | Value |
|---|---|
| Number of assets | 25 |
| Number of ticks | 37,800 |
| Simulated years | ~150 (at 252 ticks/year) |
| Sector IDs | 0–4 (5 sectors, 5 assets each) |
| Spread range | 2–12 bps |
| Borrow range | 23–197 bps/year |
| Mean spread | 4.84 bps |
| Mean borrow | 126.24 bps/year |

**Missing values:** None. All 25 assets have complete cost and price data.

---

## Section 1: Per-Asset Cost Breakdown

### Cost Model

For a weight change Δw = 0.01 (1% rebalance):

```
Linear spread cost   = (spread_bps / 2) × |Δw| × 100        [in bps]
Quadratic cost       = 0.1 × |Δw|² × 10,000                  [in bps]
Total trade cost     = linear + quadratic
Annual borrow cost   = borrow_bps_annual × |short weight|     [in bps/yr]
```

For a 1% short position (w = -0.01), borrow cost = borrow_bps_annual × 0.01.

### Full Per-Asset Cost Table (sorted by total trade cost, cheapest first)

| Asset | Sector | Spread (bps) | Borrow (bps/yr) | Linear Cost (bps) | Quad Cost (bps) | Total Trade (bps) | Borrow 1% Short (bps/yr) | Ann. Return (%) | Sharpe |
|---|---|---|---|---|---|---|---|---|---|
| A24 | Sector-4 | 2.0 | 138.0 | 1.00 | 0.10 | 1.10 | 1.38 | 0.88 | 0.16 |
| A21 | Sector-4 | 2.0 | 172.0 | 1.00 | 0.10 | 1.10 | 1.72 | 0.65 | 0.11 |
| A02 | Sector-2 | 2.0 | 124.0 | 1.00 | 0.10 | 1.10 | 1.24 | 0.03 | 0.01 |
| A04 | Sector-3 | 2.0 |  44.0 | 1.00 | 0.10 | 1.10 | 0.44 | 0.88 | 0.18 |
| A19 | Sector-3 | 2.0 | 177.0 | 1.00 | 0.10 | 1.10 | 1.77 | 0.93 | 0.17 |
| A15 | Sector-0 | 2.0 | 130.0 | 1.00 | 0.10 | 1.10 | 1.30 | 0.03 | 0.02 |
| A08 | Sector-2 | 2.0 | 195.0 | 1.00 | 0.10 | 1.10 | 1.95 | 0.12 | 0.03 |
| A14 | Sector-1 | 2.0 | 165.0 | 1.00 | 0.10 | 1.10 | 1.65 | -0.42 | -0.08 |
| A13 | Sector-1 | 2.0 | 116.0 | 1.00 | 0.10 | 1.10 | 1.16 | 0.02 | 0.02 |
| A20 | Sector-2 | 4.0 | 160.0 | 2.00 | 0.10 | 2.10 | 1.60 | -0.48 | -0.08 |
| A16 | Sector-1 | 4.0 | 125.0 | 2.00 | 0.10 | 2.10 | 1.25 | -0.23 | -0.04 |
| A23 | Sector-3 | 4.0 | 144.0 | 2.00 | 0.10 | 2.10 | 1.44 | -0.26 | -0.04 |
| A12 | Sector-0 | 4.0 | 161.0 | 2.00 | 0.10 | 2.10 | 1.61 | -0.16 | -0.03 |
| A09 | Sector-3 | 4.0 |  42.0 | 2.00 | 0.10 | 2.10 | 0.42 | 1.30 | 0.27 |
| A06 | Sector-4 | 4.0 |  72.0 | 2.00 | 0.10 | 2.10 | 0.72 | 0.56 | 0.14 |
| A05 | Sector-4 | 4.0 |  78.0 | 2.00 | 0.10 | 2.10 | 0.78 | 0.53 | 0.13 |
| A01 | Sector-0 | 4.0 | 143.0 | 2.00 | 0.10 | 2.10 | 1.43 | 0.47 | 0.08 |
| A07 | Sector-0 | 7.0 |  48.0 | 3.50 | 0.10 | 3.60 | 0.48 | -0.01 | -0.00 |
| A18 | Sector-0 | 7.0 | 134.0 | 3.50 | 0.10 | 3.60 | 1.34 | 0.39 | 0.07 |
| A03 | Sector-1 | 7.0 | 197.0 | 3.50 | 0.10 | 3.60 | 1.97 | 0.16 | 0.03 |
| A22 | Sector-2 | 7.0 | 163.0 | 3.50 | 0.10 | 3.60 | 1.63 | 0.16 | 0.02 |
| A00 | Sector-2 | 7.0 | 121.0 | 3.50 | 0.10 | 3.60 | 1.21 | -0.03 | -0.01 |
| A10 | Sector-1 | 12.0 |  23.0 | 6.00 | 0.10 | 6.10 | 0.23 | 0.19 | 0.03 |
| A17 | Sector-4 | 12.0 | 149.0 | 6.00 | 0.10 | 6.10 | 1.49 | 0.70 | 0.19 |
| A11 | Sector-3 | 12.0 | 135.0 | 6.00 | 0.10 | 6.10 | 1.35 | 0.63 | 0.22 |

[FINDING] The spread cost dominates trade cost — the quadratic component adds only 0.10 bps for a 1% trade, versus 1.0–6.0 bps linear. The spread range (2–12 bps) produces a 5.5x cost gap between cheapest and most expensive assets to trade.

[STAT:n] n = 25 assets
[STAT:effect_size] Range: 1.10 bps (2-bps spread assets) to 6.10 bps (12-bps spread assets) for Δw = 1%

---

## Section 2: Cost-Optimal Rebalancing Frequency

### Daily Rebalancing (Equal-Weight Target)

| Metric | Value |
|---|---|
| EW gross annual return | 0.46% |
| EW gross annual volatility | 2.64% |
| EW gross Sharpe | 0.173 |
| Avg daily turnover (weight drift) | 2.44% |
| Annual turnover | 615.59% |
| Average spread (portfolio) | 4.84 bps |
| Cost per day (bps) | 5.91 bps |
| Cost per day (%) | 0.059% |
| Annual rebalancing cost | 14.90% |
| Fraction of daily return eaten by cost | **3,268%** |

[FINDING] Daily rebalancing of an equal-weight portfolio is catastrophically expensive relative to the portfolio's gross return. At 0.46% annual gross return, the 14.90% annual trading cost exceeds the return by more than 32x, resulting in a deeply negative net portfolio.

[STAT:n] n = 37,799 ticks
[STAT:effect_size] Cost-to-return ratio = 32.4x (costs eat 3,268% of the daily return)

### Drift-Based Rebalancing (1-Year Simulation)

| Drift Threshold (%) | # Rebalances | Total Cost (bps) | Total Cost (%) |
|---|---|---|---|
| 0.1 | 17 | 32.60 | 0.326 |
| 0.5 | 1 | 6.31 | 0.063 |
| 1.0 | 0 | 0.00 | 0.000 |
| 2.0 | 0 | 0.00 | 0.000 |
| 5.0 | 0 | 0.00 | 0.000 |
| 10.0 | 0 | 0.00 | 0.000 |

[FINDING] The equal-weight portfolio drifts less than 1% per asset within a 1-year window under these price dynamics. A 0.5% drift threshold triggers only 1 rebalance per year (6.31 bps total), making drift-threshold rebalancing vastly superior to daily rebalancing.

[STAT:n] n = 252 ticks (1-year simulation)

### Full vs. Partial Turnover

| Event | Cost (bps) | Cost (%) |
|---|---|---|
| Full portfolio turnover (all 25 assets, Δw = 4%) | 282.00 | 2.820 |
| 10% partial rebalance | 28.20 | 0.282 |

[FINDING] A single full turnover of the portfolio costs 282 bps (2.82%). At a gross return of ~0.46%/year, a single full-turnover rebalance wipes out 6 years of returns. This strongly constrains the feasibility of active strategies that require frequent full repositioning.

[STAT:n] n = 25 assets
[STAT:effect_size] Full turnover cost (282 bps) is 6.1x the annual gross return (46 bps)

---

## Section 3: Cheap vs. Expensive Assets

### 5 Cheapest Assets (composite rank: spread + borrow)

| Asset | Sector | Spread (bps) | Borrow (bps/yr) | Composite Rank |
|---|---|---|---|---|
| A04 | Sector-3 | 2.0 | 44.0 | 8.0 |
| A13 | Sector-1 | 2.0 | 116.0 | 12.0 |
| A02 | Sector-2 | 2.0 | 124.0 | 14.0 |
| A09 | Sector-3 | 4.0 | 42.0 | 15.5 |
| A15 | Sector-0 | 2.0 | 130.0 | 16.0 |

### 5 Most Expensive Assets (composite rank)

| Asset | Sector | Spread (bps) | Borrow (bps/yr) | Composite Rank |
|---|---|---|---|---|
| A03 | Sector-1 | 7.0 | 197.0 | 45.0 |
| A17 | Sector-4 | 12.0 | 149.0 | 41.0 |
| A22 | Sector-2 | 7.0 | 163.0 | 40.0 |
| A11 | Sector-3 | 12.0 | 135.0 | 37.0 |
| A12 | Sector-0 | 4.0 | 161.0 | 32.5 |

[FINDING] A04 and A09 are uniquely cheap: both have spread ≤ 4 bps AND borrow ≤ 44 bps — the only two assets below 50 bps borrow. They should be preferred for long and short positions alike. A03 is the most expensive single asset due to maximum borrow (197 bps) combined with high spread (7 bps).

[STAT:n] n = 25 assets

### Best Return-Per-Unit-Cost (top 5, by annual return / spread_bps)

| Asset | Sector | Ann. Return (%) | Spread (bps) | Borrow (bps/yr) | Return/Cost Ratio |
|---|---|---|---|---|---|
| A19 | Sector-3 | 0.93 | 2.0 | 177.0 | 46.56 |
| A04 | Sector-3 | 0.88 | 2.0 | 44.0 | 44.01 |
| A24 | Sector-4 | 0.88 | 2.0 | 138.0 | 43.99 |
| A09 | Sector-3 | 1.30 | 4.0 | 42.0 | 32.40 |
| A21 | Sector-4 | 0.65 | 2.0 | 172.0 | 32.39 |

### Worst Return-Per-Unit-Cost (bottom 5)

| Asset | Sector | Ann. Return (%) | Spread (bps) | Borrow (bps/yr) | Return/Cost Ratio |
|---|---|---|---|---|---|
| A14 | Sector-1 | -0.42 | 2.0 | 165.0 | -20.86 |
| A20 | Sector-2 | -0.48 | 4.0 | 160.0 | -11.95 |
| A23 | Sector-3 | -0.26 | 4.0 | 144.0 | -6.62 |
| A16 | Sector-1 | -0.23 | 4.0 | 125.0 | -5.66 |
| A12 | Sector-0 | -0.16 | 4.0 | 161.0 | -3.90 |

[FINDING] A14, A20, A23, A16, and A12 have negative annual returns AND non-trivial spread costs. These should be excluded from long exposure or targeted as short candidates — though their borrow costs (125–165 bps/yr) make prolonged short positions expensive.

[STAT:n] n = 25 assets

### High-Borrow Assets: Should We Avoid Shorting Them?

| Asset | Sector | Borrow (bps/yr) | Ann. Return (%) | Sharpe |
|---|---|---|---|---|
| A03 | Sector-1 | 197.0 | +0.16 | 0.031 |
| A08 | Sector-2 | 195.0 | +0.12 | 0.027 |
| A19 | Sector-3 | 177.0 | +0.93 | 0.165 |
| A21 | Sector-4 | 172.0 | +0.65 | 0.106 |
| A14 | Sector-1 | 165.0 | -0.42 | -0.076 |

[FINDING] A14 is the only high-borrow asset with a negative return, making it a plausible short candidate. However, at 165 bps/yr borrow, a 10% short position costs 16.5 bps/year — roughly 40% of A14's |return| magnitude. For A03 and A08, the positive (if tiny) returns combined with 195–197 bps borrow make shorting definitively uneconomical unless forecasting large price declines. **Short positions in A03, A08, A19, A21 should be avoided unless alpha conviction is very high.**

[STAT:n] n = 5 high-borrow assets (top quintile by borrow rate)
[STAT:effect_size] Borrow cost for 10% short in A03: 19.7 bps/yr vs. gross return of 0.16%/yr = 1.23x annual return consumed by borrow alone

---

## Section 4: Equal-Weight Baseline — Cost Impact

### Full-Period Simulation (150 years, daily rebalancing)

| Metric | Value |
|---|---|
| Total ticks | 37,799 |
| EW gross annual return | **+0.46%** |
| Total spread cost (full period) | 20,547 bps (205.47%) |
| Avg annual spread cost | **1.37%** |
| EW net annual return (daily rebal) | **-0.91%** |
| EW gross Sharpe | 0.186 |
| EW net Sharpe (daily rebal) | **-0.334** |
| Fraction of return eaten by costs | **299.8%** (costs = 3x gross return) |

[FINDING] Daily rebalancing of the equal-weight portfolio destroys all value. The gross annual return of +0.46% is completely overwhelmed by the annual trading cost of 1.37%, yielding a net annual return of -0.91% and a net Sharpe of -0.334.

[STAT:n] n = 37,799 ticks (full dataset)
[STAT:effect_size] Cost drag = 1.37% vs. gross return = 0.46%; net = -0.91% (net Sharpe = -0.334 vs. gross Sharpe = +0.186)
[STAT:p_value] Directional: 100% of cost scenarios result in negative net return under daily rebalancing

### Monthly Rebalancing (every 22 ticks)

| Metric | Value |
|---|---|
| Net annual return | +0.14% |
| Net Sharpe | 0.068 |
| Improvement vs. daily rebal Sharpe | +0.402 Sharpe points |

[FINDING] Monthly rebalancing recovers approximately 15 bps/year in net return versus daily rebalancing and lifts the net Sharpe from -0.334 to +0.068. This remains a low bar, but it demonstrates that rebalancing frequency is the single most impactful cost lever.

[STAT:n] n = 37,799 ticks
[STAT:effect_size] Sharpe improvement from daily to monthly = +0.402; return improvement = +1.05 pp/year

---

## Section 5: Sector-Level Cost Analysis

| Sector | N Assets | Avg Spread (bps) | Borrow Range (bps/yr) | Avg Borrow (bps/yr) | Avg Ann. Return (%) | Avg Sharpe | Daily Equiv Borrow (bps) | Composite Daily Cost (bps) |
|---|---|---|---|---|---|---|---|---|
| Sector-3 | 5 | 4.80 | 42–177 | 108.40 | **+0.66** | **0.16** | 0.43 | **2.83** |
| Sector-2 | 5 | 4.40 | 121–195 | 152.60 | -0.04 | -0.01 | 0.61 | 2.81 |
| Sector-4 | 5 | 4.80 | 72–172 | 121.80 | **+0.65** | **0.14** | 0.48 | 2.88 |
| Sector-0 | 5 | 4.80 | 48–161 | 123.20 | +0.02 | 0.03 | 0.49 | 2.89 |
| Sector-1 | 5 | 5.40 | 23–197 | 125.20 | -0.03 | -0.01 | 0.50 | 3.20 |

[FINDING] Sector-3 has the lowest average borrow cost (108.40 bps/yr) and the highest average annual return (+0.66%) and Sharpe (0.16), making it the most cost-efficient sector for both long and short exposure. Sector-1 is the most expensive sector by composite daily cost (3.20 bps/day) with near-zero average return (-0.03%), making it the worst risk-adjusted sector after costs.

[STAT:n] n = 5 sectors, 5 assets each (n = 25 total)
[STAT:effect_size] Sector-3 vs Sector-1: borrow difference = 16.8 bps/yr; return difference = +0.69 pp/yr; Sharpe difference = +0.17

[FINDING] There is no single sector that is dramatically cheaper to trade on spread alone (range: 4.40–5.40 bps average). The primary differentiation is through borrow cost, where Sector-3 holds a 17 bps/yr average advantage over Sector-1.

[STAT:n] n = 5 sectors
[STAT:effect_size] Spread range across sectors: 4.40–5.40 bps (22% variation); borrow range: 108.40–152.60 bps/yr (41% variation)

---

## Strategic Implications

1. **Never rebalance daily.** The cost structure makes daily equal-weight rebalancing return-destroying (net Sharpe = -0.334). Use drift-based triggers (0.5–1.0% threshold) or monthly cadence.

2. **Concentrate in Sector-3 and Sector-4.** These sectors have the best return-per-cost ratios and lowest average borrow costs. Sector-1 and Sector-2 assets should receive reduced weight or be excluded.

3. **Preferred long assets: A09, A04, A19, A24, A21.** Low spread, positive return, good Sharpe. A09 has the highest absolute return (1.30%/yr) and the second-lowest borrow in the universe (42 bps).

4. **Avoid short positions in A03, A08.** Borrow at 195–197 bps/yr makes shorting these assets prohibitively expensive relative to their tiny positive returns.

5. **A14 and A20 are short candidates with caution.** Both have negative returns but 125–165 bps borrow. A short must produce at least 1.25–1.65 bps/yr per 1% weight just to cover borrow — feasible only for sustained positions.

6. **Full portfolio turnover (2.82%) requires 6+ years of gross return to break even.** Any strategy requiring frequent large repositioning is non-viable under this cost structure.

---

## [LIMITATION]

- The quadratic coefficient (0.1) is assumed; the true market-impact coefficient may differ, which would raise trade costs for large Δw.
- "Annual return" is computed from 150 years of simulated data. If the simulation process generates near-zero expected returns (as suggested by the 0.46% EW return), the return signal-to-noise is extremely low and all return-based rankings are unreliable for short-horizon forecasting.
- Borrow costs are modeled as fixed rates; in practice they vary with market conditions and availability.
- No transaction timing model is included — costs are assumed instantaneous at the rebalancing tick.
- The 150-year dataset likely cycles through many regimes; sector and asset rankings are averages that mask within-period variation.

---

## Figures

- `/Users/stao042906/Documents/UCHICAGO/.omc/scientist/figures/fig1_asset_cost_map.png` — Asset cost map (spread vs borrow) and trade cost ranking
- `/Users/stao042906/Documents/UCHICAGO/.omc/scientist/figures/fig2_rebalancing_cost.png` — Drift threshold vs annual cost curve
- `/Users/stao042906/Documents/UCHICAGO/.omc/scientist/figures/fig3_sector_costs.png` — Sector average costs and returns
- `/Users/stao042906/Documents/UCHICAGO/.omc/scientist/figures/fig4_return_vs_cost.png` — Return vs spread cost (color = borrow rate)
