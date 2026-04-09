# Batch 4 Strategy Results

Evaluation setup: 4-year train / 1-year pseudo-holdout split, same as validate.py.
Baseline equal-weight Sharpe: +0.9963, Total return: +15.07%, Txn costs: 0.0290%, Max DD: -17.87%

---

## S16: Top-N Static (Concentrate in Best Assets)

**Implementation:**
- In `fit()`, compute trailing 252-day Sharpe for each of 25 assets
- Select top 8 assets by Sharpe
- Weight by inverse volatility among those 8 assets
- Weights are set once in `fit()` and held completely static during holdout (zero turnover)
- Long-only

**Results:**
| Metric | Value |
|---|---|
| Annualized Sharpe | +0.7244 |
| Total Return | +12.06% |
| Total Txn Costs | 0.0370% |
| Max Drawdown | -16.60% |

**Notes:** Low turnover (costs nearly as low as baseline). Lower Sharpe than baseline despite concentrating in best assets - concentration hurts diversification. The top-8 assets from training may not maintain alpha in holdout.

---

## S17: Cost-Weighted Sharpe

**Implementation:**
- Compute Sharpe per asset over trailing 252-day training window
- Compute cost score: `spread_bps + borrow_bps_annual / 252`
- Score = `Sharpe / cost_score` (reward high risk-adjusted return, penalize trading cost)
- Weight proportional to `max(0, score)`
- Rebalance monthly (every 21 trading days)

**Results:**
| Metric | Value |
|---|---|
| Annualized Sharpe | +0.4703 |
| Total Return | +6.90% |
| Total Txn Costs | 0.1225% |
| Max Drawdown | -17.93% |

**Notes:** Underperformed baseline significantly. The cost-weighting may over-penalize high-cost assets that have legitimate alpha (e.g., A11 has spread 12bps but Sharpe 1.12). Monthly rebalancing adds moderate costs. Score denominator amplification distorts weights.

---

## S18: Exponentially Weighted MinVar

**Implementation:**
- Like MinVar but use exponentially weighted covariance (half-life = 63 days)
- EWMA covariance computed manually with numpy: `weights[t] = lambda^(T-1-t)`, normalized
- Rebalance every 5 days (cached between)
- Long-only, SLSQP optimization

**Results:**
| Metric | Value |
|---|---|
| Annualized Sharpe | +0.3978 |
| Total Return | +4.99% |
| Total Txn Costs | 0.2689% |
| Max Drawdown | -13.35% |

**Notes:** Lowest Sharpe of the batch. EWMA covariance recomputed every 5 days causes high turnover (0.27% costs). The shorter effective lookback (63-day half-life vs. 252-day static) leads to noisier estimates and more weight churn. Best max drawdown of the batch due to genuine variance minimization.

---

## S19: Long-Short Factor

**Implementation:**
- Long: top 8 assets by trailing 252-day Sharpe, equal weight at 8% each (64% gross long)
- Short: bottom 3 assets by Sharpe, equal weight at 5% each (15% gross short), but only if `borrow_bps_annual < 150`
- Net exposure ~49%, gross ~64-79% depending on how many shorts pass borrow filter
- Recompute monthly (every 21 days)

**Results:**
| Metric | Value |
|---|---|
| Annualized Sharpe | +0.7476 |
| Total Return | +7.18% |
| Total Txn Costs | 0.1574% |
| Max Drawdown | -14.62% |

**Notes:** Second-best Sharpe of the batch, second-best max drawdown. Monthly rebalancing keeps costs moderate. The short book adds some hedging value (lower drawdown than S16). However, lower total return than S16 due to net exposure below 1.0. A09 (borrow 42 bps) and A04 (44 bps) likely satisfy the short borrow filter, but these are actually the best performers - the "short bottom 3" may include assets where borrow threshold blocks them (many bottom assets have borrow > 150 bps per meta).

---

## S20: Ensemble of InvVol + MinVar + RiskParity

**Implementation:**
- Compute weights from 3 sub-strategies each period:
  - Inverse volatility (1/sigma, normalized)
  - Minimum variance (LedoitWolf + SLSQP)
  - Risk parity (equal risk contribution via iterative algo, 100 iterations)
- Average the three weight vectors
- Normalize so sum(|w|) <= 1
- Recompute every 5 days

**Results:**
| Metric | Value |
|---|---|
| Annualized Sharpe | +0.8462 |
| Total Return | +12.24% |
| Total Txn Costs | 0.0763% |
| Max Drawdown | -15.98% |

**Notes:** Best Sharpe of the batch. Ensembling successfully diversifies single-strategy risk. High total return (near baseline's 15%). Moderate costs (0.076%). The averaging of three complementary approaches produces smoother, more stable weights. This is a strong result for a long-only strategy.

---

## Summary Table

| Strategy | Sharpe | Total Return | Txn Costs | Max DD |
|---|---|---|---|---|
| Baseline (Equal Weight) | +0.9963 | +15.07% | 0.0290% | -17.87% |
| S16: Top-N Static | +0.7244 | +12.06% | 0.0370% | -16.60% |
| S17: Cost-Weighted Sharpe | +0.4703 | +6.90% | 0.1225% | -17.93% |
| S18: EW MinVar | +0.3978 | +4.99% | 0.2689% | -13.35% |
| S19: Long-Short Factor | +0.7476 | +7.18% | 0.1574% | -14.62% |
| S20: Ensemble InvVol+MinVar+RP | +0.8462 | +12.24% | 0.0763% | -15.98% |

## Key Takeaways

1. **None beat the baseline** on Sharpe in this holdout period. Equal-weight's diversification is hard to beat.
2. **S20 Ensemble** is the best of this batch at +0.8462 Sharpe - close to baseline and has lower max drawdown.
3. **S19 Long-Short** shows value in hedging (low max DD of -14.62%) but low net exposure hurts returns.
4. **S16 Static** has very low costs (0.037%) which is good, but concentration hurts.
5. **S17 and S18** underperform due to high turnover and/or noisy signals - cost-weighted scoring distorts allocation.
6. **Turnover minimization** remains the dominant factor: S16 (static) and S20 (5-day cache, smooth weights) have best cost profiles.

## Strategy Files
- `/Users/stao042906/Documents/UCHICAGO/Case2/participant/submission_s16.py`
- `/Users/stao042906/Documents/UCHICAGO/Case2/participant/submission_s17.py`
- `/Users/stao042906/Documents/UCHICAGO/Case2/participant/submission_s18.py`
- `/Users/stao042906/Documents/UCHICAGO/Case2/participant/submission_s19.py`
- `/Users/stao042906/Documents/UCHICAGO/Case2/participant/submission_s20.py`

submission.py has been restored to equal-weight baseline (Sharpe +0.9963 confirmed).
