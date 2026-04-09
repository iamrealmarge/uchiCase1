# Handoff Document — Portfolio Optimization State

## Current Submission (verified via validate.py --cv)
- **CV Mean: +2.163, Min: +2.100, Std: 0.055**
- **In-sample (5yr): ~2.28**
- **Oracle: +2.627 (81% efficiency)**
- Folds: +2.192, +2.197, +2.100
- **Tick tilt**: PER-SECTOR alpha — S0/S1/S2=0.02, S3/S4=0.0 (only tilt unviewed sectors)

## Key Parameters
- **Covariance**: EWMA ensemble {halflife=8, 12, 15, 18} — average weights across 4 halflives
- **BL views**: 4 (S3 outperforms, S4 outperforms, A23 underperforms S3, A09 outperforms S3)
- **omega_sector**: 0.0005 (sector views — high confidence, averaging 5+ assets)
- **omega_asset**: 0.01 (asset views — lower confidence, individual assets are noisier)
- **tau**: 0.10 (prior uncertainty)
- **lambda**: 1.0 (risk aversion in prior)
- **L1 penalty**: 0.0003 (sparsity — promotes concentration in best assets)
- **Bounds**: [-0.08, 0.02] for short candidates (A14, A20, A16, A23), [-0.03, 0.25] for others
- **Vol scaling**: [0.5, 1.5] clip, cost-aware gate (2x cost threshold)
- **L1 constraint**: sum(|w|) <= 1

## Journey (key milestones)
| Date | Sharpe | Key Change |
|---|---|---|
| Start | 1.00 | Equal weight baseline |
| Phase 2 | 1.19 | Black-Litterman with sector views |
| N12 | 1.57 | A23 within-sector outlier view |
| N15 | 1.66 | Relaxed long-short bounds |
| N20 | 1.88 | omega/tau calibration (0.05/0.05) |
| N28 | 1.90 | A09 positive outlier view |
| Cycle 24 | 1.96 | Systematic omega/tau CV grid (0.005/0.15) |
| EWMA cov | 2.02 | EWMA halflife=30 replaces Ledoit-Wolf |
| hl+lam tune | 2.04 | halflife=22, lambda=1.5 |
| L1 sparsity | 2.10 | L1=0.0003 penalty + halflife=15 + lambda=1.0 |
| omega push | 2.11 | omega_scale 0.01→0.001 (views more dominant) |
| Ensemble | 2.12 | EWMA ensemble {8,12,15,18} + omega=0.001 |
| **Power shrink** | **2.12** | **Power eigenvalue shrinkage gamma=0.9 (Min +2.055, Std 0.101)** |

## What's Been Exhaustively Tested (DON'T re-test)
- All BL parameter combos (omega, tau, lambda, per-view omega): ~200 configs
- Covariance estimators: LW, EWMA (hl=8-252), OAS, sample cov, tick-level EWMA, PCA factor (1-5 factors), EWMA-PCA tick
- Bounds: 4 variants (current, wider, deeper shorts, cap at 15%)
- Extra views: A14, A20, S4 (A17+, A21-), A11 positive, refined A09, cross-sector short views (S1 underperforms, S2 underperforms) — all degrade fold consistency
- Dynamic approaches: 5-day momentum, time-varying views — turnover kills them
- Different objectives: max-Sharpe, MV utility, Ridge-penalized — all equivalent with BL
- Different mu: tick-level, James-Stein, per-asset BL views, Jorion Bayes-Stein shrinkage — all overfit or destroy signal
- Min-var prior, Bayesian posterior averaging, weight shrinkage — all worse
- Kan-Zhou three-fund rule, Tu-Zhou 1/N combination — BL already regularizes equivalently
- Multiple initial guesses, multi-restart — optimizer already at global optimum
- Vol-scaling: window sizes, clip ranges, cost-gate params, target vol methods
- Optimizer formulations: SLSQP max-Sharpe, analytic tangency, mean-variance utility (gamma 1-1000), regularized Sharpe (L2 deviation from EW), two-step (direction + scale), risk-parity inspired — ALL find the same direction
- Gross exposure: fixed gross 0.3-1.0, no L1 penalty, L1 with gross floor — Sharpe is scale-invariant, tiny weights minimize costs
- Michaud resampled frontier: N=50-500 samples, scale 0.1-5.0, posterior predictive — averaging dilutes BL signal
- Tangency-GMV blend: c=0.1 to 0.9 — more tangency always better (BL tangency IS the signal)
- Weight ensemble across halflives: {10,15,20}, {8,12,15,18}, {10,12,15,18,20}, all 8 — marginal gain only from {8,12,15,18}

## What HASN'T Been Tried (research directions)
1. **End-to-end differentiable portfolio optimization (PyTorch)**: Define weights as nn.Parameter, backprop through differentiable Sharpe ratio. Bypasses BL entirely — learns optimal static weights directly from training returns via gradient descent. PyTorch 2.0.1 is available.
2. **Neural nonlinear eigenvalue shrinkage (PyTorch)**: Decompose EWMA cov into eigvals/eigvecs, learn optimal nonlinear shrinkage function via small MLP. Jan 2026 paper (arxiv 2601.15597). Feed shrunk cov into BL.
3. **Strategy-specific eigenvector shrinkage (numpy)**: From Finance & Stochastics May 2025. Shrink leading eigenvectors toward the max-Sharpe constraint gradient subspace. Reduces estimation error amplification specific to the optimization objective.
4. **m-Sparse Sharpe via L0 constraint (NeurIPS 2024)**: Proximal gradient with exact cardinality. Select top m assets for BL posterior optimization. Test m=8,10,12,15.
5. **Realized variance for vol-scaling**: Use sum of squared tick returns instead of daily close-to-close for more precise vol estimates.
6. **Different BL prior equilibrium**: Instead of lambda*Sigma*w_eq, use market-cap-weighted or inverse-vol as prior.
7. **Cross-validation within training for view selection**: Use inner CV to select which views improve OOS Sharpe.
8. **Nonlinear portfolio via sklearn**: Ridge/Lasso regression directly predicting returns, use predictions as BL view q-values.

## Key Insights from Multi-Agent Testing (this session)
- **The optimizer is NOT the bottleneck** — SLSQP finds the globally optimal direction for any BL posterior. Every alternative optimizer (MV utility, analytic, regularized, risk-parity) finds the same direction.
- **Scale doesn't matter** — Sharpe is scale-invariant. L1 penalty drives gross to 2.7% which is OPTIMAL (minimizes costs while preserving direction).
- **BL posterior quality IS the ceiling** — all improvements came from better BL inputs (omega, tau, views, cov), never from optimizer changes.
- **Research-based shrinkage hurts** — Jorion, Kan-Zhou, Tu-Zhou all destroy the BL signal because BL views already capture the true constant-drift DGP. Further shrinkage degrades accuracy.
- **PyTorch is completely untested** — this is the biggest remaining opportunity.

## Files
- `submission.py` — Current best strategy (ensemble + omega=0.001)
- `strategies_n.py` — 36 experimental strategies (N1-N36)
- `GOLDEN_PRINCIPLES.md` — 38+ hard-won rules
- `../AUDIT_TRAIL.md` — Full history of all experiments
- `validate.py` — Competition evaluator
- `prices.csv`, `meta.csv` — Data
- `test_*.py` — Various experiment scripts from this session

## DGP Summary
- Multi-asset GBM with constant drifts, single common factor (PC1=25.4%)
- Sectors 3&4 strongly outperform (Sharpe 0.77-0.82)
- A09 is star asset (Sharpe 1.42), A23 is negative outlier in S3 (Sharpe -0.23)
- No autocorrelation in daily returns
- Vol varies slightly across years (Year 2 is 14% higher)
- 5-day cross-sectional momentum signal exists (IC=0.019) but is too costly to trade dynamically

## Competition Details
- Scoring: AVERAGED across MULTIPLE OOS runs (consistency matters)
- Same DGP as training confirmed
- Libraries: numpy, pandas, scikit-learn, scipy, **PyTorch 2.0** (all confirmed allowed)
- Deadline: April 9, 2026, 11:59 PM CST
