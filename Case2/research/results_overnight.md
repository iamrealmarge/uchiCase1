# Overnight Return Signal - Backtest Results

**Date:** 2026-04-08
**Evaluator:** validate.py (4-year train / 1-year pseudo-holdout)
**Train:** ticks 0–30,239 (4 years, 252 days/yr, 30 ticks/day)
**Holdout:** ticks 30,240–37,799 (1 year, 252 days)

---

## Timing Verification (No Lookahead)

`get_weights(price_history, meta, day=D)` receives history through end of holdout day **D-1**.
Weights returned are held for **day D**.

The overnight signal is computed as:
```
close_prev  = price_history[-(TICKS_PER_DAY + 1)]   # last tick of day D-2
open_latest = price_history[-TICKS_PER_DAY]          # first tick of day D-1
overnight_return = open_latest / close_prev - 1
```

This overnight return (entering day D-1) is used to predict day D.
- No lookahead: we never see any tick from day D when deciding weights for day D.
- The gap we observe is the close-to-open move from day D-2 to D-1.

### Debug output (first 3 calls, S29/S33):

```
day=0, n_ticks=30240  (= 4*252*30 = full training set)
  close_prev (tick -31): [101.98, 133.30, 116.02, ...]
  open_latest (tick -30): [102.13, 133.58, 115.65, ...]
  overnight_ret sample: [+0.0015, +0.0021, -0.0031, ...]

day=1, n_ticks=30270  (= 30240 + 1*30)
  overnight_ret top3: [+0.0055, +0.0063, +0.0106]

day=2, n_ticks=30300  (= 30240 + 2*30)
  overnight_ret top3: [+0.0043, +0.0047, +0.0048]
```

Timing confirmed correct. Each call adds exactly 30 ticks (one day).

---

## Results Summary

| Strategy | Sharpe | Total Return | Txn Costs | Max Drawdown |
|---|---|---|---|---|
| equal_weight (baseline) | +0.9963 | +15.07% | 0.0290% | -17.87% |
| S29: Overnight Basic (L/S daily) | **-1.3490** | -11.67% | **15.8800%** | -14.88% |
| S30: Overnight Long-Only (5d rebal) | +1.1973 | +19.73% | 2.3306% | -25.06% |
| S31: Overnight + Sector Tilt | **+1.3618** | **+21.88%** | 0.7614% | -22.03% |
| S32: Overnight Dampened (0.1 blend) | +0.7415 | +2.31% | 1.2619% | -3.45% |
| S33: Overnight Quintile Spread | **-1.3490** | -11.67% | **15.8800%** | -14.88% |

---

## Strategy Details and Analysis

### S29: Overnight Basic (Long/Short, Daily Rebalance)

- Signal: overnight return (open[D-1] / close[D-2] - 1)
- Portfolio: Long top 5, Short bottom 5, equal weight, sum|w|=0.8
- Rebalanced: every day

**Result: Sharpe -1.35, Total return -11.67%, Txn costs 15.88%**

The signal is destroyed by transaction costs. Daily rebalancing of a 5-asset long/short portfolio generates ~15.9% in annual costs (spread + market impact). The gross signal is likely positive but the net is deeply negative.

The research finding (IC=0.169, t=29.4) measures signal accuracy, not tradeable alpha. With spread costs on every dollar of turnover, the high-IC signal becomes a money-loser when rebalanced daily.

---

### S30: Overnight Long-Only (Rank-Weighted, 5-Day Rebalance)

- Signal: overnight return, rank-weighted
- Portfolio: long-only, proportional to rank, weight in positive-overnight assets only
- Rebalanced: every 5 days
- Normalize: sum(w) = 0.9

**Result: Sharpe +1.20, Total return +19.73%, Txn costs 2.33%**

Reducing to 5-day rebalancing cuts costs from 15.9% to 2.3% and turns the strategy profitable. Still beats the equal-weight baseline on both Sharpe (+1.20 vs +1.00) and total return (+19.7% vs +15.1%). However, max drawdown is worse (-25.1% vs -17.9%) due to concentrated long-only bets.

---

### S31: Overnight Signal + Static Sector Tilt (BEST)

- Base: static equal-weight within sectors 3 & 4 (from fit())
- Overlay: blend 80% static + 20% overnight rank signal
- Rebalanced: daily but small tilts
- Normalize: gross = 0.9

**Result: Sharpe +1.36, Total return +21.88%, Txn costs 0.76%**

The best strategy overall. Key insight: the static base portfolio means daily rebalancing only moves 20% of the weight (the signal overlay), so turnover is low despite daily updates. The sector 3&4 tilt captures the research finding that those sectors have favorable return characteristics, while the overnight signal provides within-sector edge.

- Beats equal-weight: +37 bps Sharpe, +6.8pp total return
- Costs only 0.76% (vs 15.88% for raw daily L/S)
- Max drawdown slightly worse at -22% (concentrated in 2 sectors)

**This is the most promising strategy for further development.**

---

### S32: Overnight Dampened (0.1 blend, very low turnover)

- Signal: same overnight L/S as S29
- Update: w_new = 0.1 * w_signal + 0.9 * w_old
- This creates exponential smoothing with ~9-day half-life

**Result: Sharpe +0.74, Total return +2.31%, Txn costs 1.26%**

Low costs (1.26%) but significantly underperforms the baseline (Sharpe 0.74 vs 1.00). The heavy dampening kills both costs AND the signal too aggressively. The portfolio converges to a near-zero position over time, explaining the tiny 2.31% total return. Not recommended.

---

### S33: Overnight Quintile Spread (Pure Validation)

- Signal: overnight return quintiles, long Q1, short Q5
- Equal weight, sum|w| = 0.8
- Identical to S29 (both use top-5/bottom-5 long-short)

**Result: Sharpe -1.35, Total return -11.67%, Txn costs 15.88%**

Identical to S29. Confirms the pure overnight momentum L/S signal is unviable with daily rebalancing due to transaction costs. The signal works statistically (IC=0.169) but cannot be monetized by daily turnover due to spread + market impact costs.

---

## Key Conclusions

1. **The overnight return signal has real IC (0.169, t=29.4) but daily L/S is unviable.** Transaction costs of ~15.9% per year wipe out all alpha when rebalancing a full long-short portfolio daily.

2. **The signal IS usable with cost management.** S30 (+1.20 Sharpe) and S31 (+1.36 Sharpe) both beat the baseline by using the signal with low-turnover portfolio structures.

3. **Best approach: use as overlay on a stable base (S31).** Static sector allocation provides low-cost base exposure; overnight signal as a small tilt captures signal without excessive turnover.

4. **Sector 3&4 tilt is doing heavy lifting in S31.** The ~0.4 Sharpe improvement over equal-weight comes from combining sector selection with overnight signal. Would be worth isolating each contribution.

5. **Overnight signal direction may be mean-reversion, not momentum.** The negative Sharpe of the pure signal strategy (-1.35) suggests the signal may actually predict the OPPOSITE direction in the evaluator, or that costs entirely reverse it. Further investigation: test the SHORT-overnight-return portfolio (inverse signal).

---

## Next Steps Recommended

1. **Test inverse overnight signal** (short assets with highest overnight return, long lowest) - the -1.35 Sharpe hints the signal may be mean-reverting in this dataset
2. **Optimize S31 sector weights** - which sectors are driving the return?
3. **Test multi-day overnight signal** (average of last N overnight gaps) to smooth noise
4. **Increase S30 rebalance frequency** - test 2-day, 3-day windows to find cost/signal tradeoff
5. **Add momentum filter to S31** - only apply overnight signal when it confirms a multi-day trend

---

## Files

- `/Users/stao042906/Documents/UCHICAGO/Case2/participant/submission.py` - All strategies implemented (S29-S33), `ACTIVE_STRATEGY = "equal"` restored
- `/Users/stao042906/Documents/UCHICAGO/Case2/participant/run_overnight_strategies.py` - Runner script for all strategies
