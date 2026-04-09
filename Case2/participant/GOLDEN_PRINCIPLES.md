# Golden Principles — Portfolio Optimization Harness

These are hard-won rules from 70+ strategy experiments. They are MECHANICALLY ENFORCED
by the validation step. An agent that violates these will waste a cycle.

## DGP Rules (what the data IS)
1. The DGP is constant-drift multi-asset GBM with a single common factor (PC1=25.4%)
2. Drifts are stable across all 5 years (ANOVA confirmed, p>0.05 for all 25 assets)
3. There is NO autocorrelation in daily returns (mean AC(1) = 0.004)
4. There is a weak 5-day cross-sectional momentum signal (IC=0.019, t=3.21) — real but small
5. Sector structure exists ONLY in drifts, NOT in covariance (within-sector corr = cross-sector corr)
6. Vol varies across years (Year 2 is 14% higher) — vol scaling has value

## Optimization Rules (what WORKS)
7. BL regularization is essential. Per-asset mu without BL ALWAYS overfits (N9, N10, N23 all failed)
8. The equal-weight BL prior is better than min-variance prior for this DGP (tested, confirmed)
9. Within-sector outlier views work ONLY for extreme outliers (A23: -1.87σ, A09: global max). Moderate outliers (A17: +1.62σ) have zero effect.
10. Relaxed LS bounds [-0.03, 0.25] allow the optimizer to reduce net exposure — this helps
11. omega_scale=0.05 for views gives best CV results (sector views + A23 + A09)
12. The L1 gross constraint doesn't bind (optimizer voluntarily uses ~70% gross = Kelly-optimal)
13. Vol scaling [0.5, 1.5] with cost-aware gate is net positive for Sharpe

## Anti-Patterns (what NEVER works)
14. Dynamic signals (momentum, reversal, regime switching) fail — DGP has no dynamics to exploit
15. Multi-restart optimization finds higher in-sample Sharpe that doesn't generalize
16. Systematic outlier views in neutral sectors (0, 1, 2) add noise — only view in strong sectors
17. Borrow-cost-adjusted objective over-penalizes useful shorts
18. Ensemble with weak component drags down the strong component (N24, N26)
19. Vol scaling using current_weights (not base_weights) creates a feedback loop that explodes costs
20. Tick-level mu precision (5.6x better) doesn't help without BL regularization

## Efficiency Bounds
21. Theoretical max Sharpe: 2.627 (unconstrained, perfect mu). No constraints bind.
22. Current submission: 1.900 mean, 1.817 min. Gap = 0.73 Sharpe points.
23. The ENTIRE gap is mu estimation noise amplified by max-Sharpe optimization.
24. Daily mu t-stats are weak (max 3.16). Tick-level t-stats are strong (max 286).
25. Per-asset ABSOLUTE views (P=I, q=mu) defeat BL regularization even inside BL framework (N29: Mean 0.58). The 25 absolute views drown out the prior. RELATIVE views (asset-vs-asset differences) preserve BL's level regularization while adding cross-sectional info.
29. S4 within-sector views (A17+, A21-) are a HIGH-VARIANCE addition: omega=0.05 → folds hit 2.06 but collapse to 0.90. Heterogeneous omega (0.20) → folds hit 1.95 but min still 1.52. For CONSISTENT performance, S4 views are net-negative. Only add them if scoring AVERAGES multiple OOS runs (confirmed in audit trail header).
30. The tradeoff: N28 (4 views) gives Mean=1.90, Min=1.82. N31 (6 views, hetero omega) gives Mean=1.82, Min=1.52. More views = higher ceiling but lower floor. Optimal strategy depends on scoring mechanism.
31. Tick-level mu for sector VIEW Q-VALUES has zero effect (N32 ≈ N28). Sector-level aggregates are already well-estimated at daily frequency because they average 5+ assets. Tick precision only helps for INDIVIDUAL asset views, which need BL regularization (see #25).
32. James-Stein shrinkage on mu toward zero (N33: 0.54) fails same as N9/N10/N23. The problem is NOT mu estimation quality — even theoretically optimal mu doesn't stabilize max-Sharpe. BL's value is regularizing the OPTIMIZER (via posterior covariance), not just shrinking mu. Any replacement for BL must regularize the OPTIMIZATION step, not just the inputs.
33. DeMiguel et al. (2009): For 25 assets, need ~3000 months for sample MV to beat 1/N. We have 60 months. This confirms BL regularization is essential and we are near the information-theoretic limit for this sample size.
34. Ridge-inflated covariance (Σ+λI) in the optimizer with λ=median_eigenvalue is TOO aggressive (N34: mean 1.789 vs N28: 1.900). It over-regularizes, washing out the cross-sectional signal from BL views. If tried again, use λ << min_eigenvalue.
35. MV utility objective ≈ max-Sharpe when BL inputs are used (N35 ≈ N28 within 0.4 bps). The objective function doesn't matter when inputs are regularized. BL is the regularizer — the optimizer just extracts what BL provides. Changing the objective alone cannot close the gap.
36. With FULL 5-year fit, submission in-sample Sharpe = 2.286 (87% of oracle). CV folds train on 2-4 years → pessimistic by ~10%. Expected holdout performance: 2.0-2.1 (between CV 1.90 and IS 2.29). The submission is stronger than CV scores suggest.
37. SYSTEMATIC CV over omega×tau grid found omega=0.01, tau=0.10 DRAMATICALLY better than omega=0.05, tau=0.05. Mean +1.960 vs +1.900, Min +1.931 vs +1.817, Std HALVED. The original omega/tau were ad-hoc and suboptimal. Tighter view confidence (omega=0.01) + weaker prior (tau=0.10) = views dominate, which is correct when views capture true constant drifts. GP#11 (omega=0.05 best) is WRONG — updated.
38. The omega/tau surface is SMOOTH and monotonic: lower omega + higher tau = better, up to a point. The optimal is near the corner omega→0, tau→∞ (pure views, no prior). This confirms the DGP has strong, stable sector structure that views capture accurately.

## Phase 6 Principles (Multi-Agent Session)
39. PyTorch gradient descent on Sharpe ALWAYS overfits for this DGP, regardless of initialization or trust-region regularization. BL's regularization is STRUCTURAL (view matrix), not parametric (L1/L2).
40. Power eigenvalue shrinkage (gamma=0.95) mildly improves stability. Compresses eigenvalue spread without changing eigenvector directions.
41. Eigenvalue compression (power shrinkage) helps; eigenvector rotation (JSE) hurts. Eigenvector DIRECTIONS are well-estimated; only MAGNITUDES need correction.
42. Heterogeneous omega: sector views (avg 5+ assets) deserve tighter omega (0.0005) than asset views (individual, noisier → 0.01).
43. m-Sparse portfolio fails. All 25 assets needed for long-short factor hedging. Removing any asset increases factor exposure.
44. Within-sector tick-level Sharpe tilt at alpha=0.02 is a paradigm shift (+6.2 bps). Adds per-asset info in BL-blind directions using tick-level precision (37,800 obs vs 1,260 daily).
45. Tick tilt should ONLY apply to unviewed sectors (S0/S1/S2). Tilting viewed sectors (S3/S4) adds noise — BL already optimally handles them.
46. Simplified CV and validate.py rank differently. ALWAYS verify with validate.py. Simplified overestimates aggressive configs.
47. Parameter sweeps should be batch FOR LOOPS within one cycle, not one value per cycle.

## Submission Rules
26. NEVER submit with min fold < 2.00
27. ALWAYS verify with `python3 validate.py --cv` before updating submission.py
28. Standalone strategy tests can diverge from validate.py — only trust validate.py
