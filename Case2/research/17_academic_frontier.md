# Academic Frontier Research — Portfolio Optimization Beyond BL

Last updated: April 9, 2026 (Cycle 28)

## Our Bottleneck
BL with 4 views + EWMA ensemble achieves CV Mean +2.12 (81% of oracle 2.627). The gap is mu estimation noise amplified by max-Sharpe optimization. DeMiguel et al. (2009) says N=25 assets need ~3000 months for sample MV to beat 1/N; we have 60 months.

## Techniques TESTED and Failed

### Classical Shrinkage (all worse than BL baseline)
| Technique | Paper | Result | Why it failed |
|---|---|---|---|
| Jorion Bayes-Stein | Jorion 1986, JFQA | Mean +2.01 | Shrinks mu_BL toward uniform return, destroys cross-sectional signal |
| Kan-Zhou three-fund | Kan & Zhou 2007, JFQA | Mean +2.10 | BL already regularizes; KZ3 delta is tiny because BL Sharpe is high |
| Tu-Zhou 1/N combo | Tu & Zhou 2011, JFE | Mean +0.63 | Blending with 1/N catastrophically dilutes sector signal |
| Tangency-GMV blend | Lassance 2021 | Mean +2.10 at c=0.9 | More tangency always better; BL tangency IS the signal |
| James-Stein toward zero | — | Mean +0.54 | Same failure as per-asset mu without BL |
| Michaud resampled frontier | Michaud 1998 | Mean +1.58 | Averaging sampled portfolios dilutes concentrated BL bets |

**Key learning**: These techniques assume noisy sample means. Our BL posterior is already well-conditioned by views that match the true DGP. Additional shrinkage/averaging destroys accuracy.

### Alternative Optimizers (all equivalent)
MV utility, analytic tangency, regularized Sharpe, risk-parity, Ridge-penalized MV, two-step optimization — all find the same weight direction as SLSQP max-Sharpe when BL inputs are used.

**Key learning**: The objective function doesn't matter when inputs are regularized (GP#35). The ceiling is the BL posterior quality.

## Techniques NOT YET TESTED — Ranked by Promise

### Tier 1: High Promise (PyTorch available)

#### 1. End-to-End Differentiable Portfolio Optimization
**Paper**: Zhang et al. "A Universal End-to-End Approach to Portfolio Optimization via Deep Learning" (2021, arxiv 2111.09170). Updated in 2025 with improved architectures.
**Key idea**: Define portfolio weights as learnable parameters. Forward pass computes portfolio returns from training data. Loss = negative Sharpe ratio. Backward pass via autograd. Projected gradient descent enforces constraints.
**Why promising**: Completely bypasses BL. No explicit mu/cov estimation — the optimizer directly learns which weights maximize Sharpe. With constant-drift GBM, the optimal weights are STATIC, so this reduces to learning 25 numbers.
**Implementation**: Simple PyTorch — nn.Parameter(25), Adam optimizer, project to bounds + gross<=1 after each step.
**Risk**: May overfit to training set (same concern as N9/N10/N23). Need regularization (L1/L2 penalty, early stopping, or ensemble over subsets).
**Sources**: [arxiv 2111.09170](https://arxiv.org/pdf/2111.09170), [GitHub reference impl](https://github.com/hobinkwak/Portfolio-Optimization-Deep-Learning)

#### 2. Neural Nonlinear Eigenvalue Shrinkage
**Paper**: "Neural Nonlinear Shrinkage of Covariance Matrices for Minimum Variance Portfolio Optimization" (Jan 2026, arxiv 2601.15597)
**Key idea**: Decompose sample covariance into eigenvalues + eigenvectors. Learn a nonlinear function f(lambda_i) that maps sample eigenvalues to optimal shrunk eigenvalues. Uses a small transformer/MLP trained to minimize out-of-sample portfolio variance.
**Why promising**: Addresses covariance estimation directly. EWMA is a linear estimator; nonlinear shrinkage captures the Marchenko-Pastur correction optimally. Feed shrunk cov into existing BL framework.
**Implementation**: PyTorch MLP with ~100 parameters. Train on bootstrap subsets of training returns. Apply to EWMA eigenvalues.
**Risk**: Needs careful train/val split WITHIN the training set to avoid overfitting the shrinkage function. N=25 eigenvalues is a small input.
**Sources**: [arxiv 2601.15597](https://arxiv.org/abs/2601.15597)

### Tier 2: Medium Promise (numpy/scipy)

#### 3. Strategy-Specific Eigenvector Shrinkage
**Paper**: Kercheval & Navarro, "Portfolio optimisation via strategy-specific eigenvector shrinkage" (Finance & Stochastics, May 2025)
**Key idea**: Standard covariance shrinkage (LW) is strategy-agnostic. This paper shrinks eigenvectors toward the constraint subspace of the specific optimization problem (e.g., max-Sharpe). This neutralizes the components of estimation error that are amplified by THAT particular optimization.
**Implementation**: James-Stein estimator for eigenvectors (JSE). Ready-to-code formulas in the paper. Pure numpy.
**Why promising**: Directly addresses "estimation noise amplified by max-Sharpe" — our exact bottleneck.
**Risk**: Theory is asymptotic (N,T → ∞). With N=25, T=1260, may not see significant improvement.
**Source**: [Finance & Stochastics 2025](https://link.springer.com/article/10.1007/s00780-025-00566-4), [PDF](https://www.math.fsu.edu/~kercheva/papers/strategy_specific_shrinkage.pdf)

#### 4. m-Sparse Sharpe via L0 Constraint
**Paper**: Lin et al., "A Globally Optimal Portfolio for m-Sparse Sharpe Ratio Maximization" (NeurIPS 2024)
**Key idea**: Replace L1 penalty with exact cardinality constraint ||w||_0 <= m. Convert fractional Sharpe optimization to equivalent quadratic program. Proximal gradient algorithm finds globally optimal m-sparse portfolio.
**Implementation**: Pure numpy. Convert max-Sharpe to min-QP, apply proximal gradient with L0 projection (keep top-m positive components).
**Caveat**: Paper assumes long-only + self-financing (w >= 0, sum=1). Our problem allows shorts and has gross<=1 constraint. Need adaptation.
**Why promising**: With m=10-15 assets, reduces the effective dimensionality, which reduces estimation noise. Could combine with BL posterior.
**Source**: [NeurIPS 2024 proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/file/1eaa5146756be028ad6fff1efcc8e6bd-Paper-Conference.pdf)

### Tier 3: Lower Promise (reference only)

#### 5. Lassance OOS-Sharpe Maximization
**Paper**: Lassance, "Maximizing the Out-of-Sample Sharpe Ratio" (SSRN 2021, published ~2023)
**Key insight**: The optimal combination of tangency + GMV for maximizing E[OOS Sharpe] is DIFFERENT from the utility-based combination (Kan-Zhou). Implies less shrinkage toward GMV.
**Status**: We tested the tangency-GMV blend at various c values. More tangency is always better in our setup. This confirms BL tangency IS the right direction.
**Source**: [SSRN 3959708](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3959708)

#### 6. End-to-End Covariance Cleaning via Neural Networks
**Paper**: 2025/2026, "End-to-End Large Portfolio Optimization for Variance Minimization with Neural Networks through Covariance Cleaning"
**Key idea**: Learn rotation-invariant covariance estimator end-to-end with the portfolio objective.
**Status**: Requires PyTorch. Complex architecture. Lower priority than simpler end-to-end weight learning.
**Source**: [arxiv 2507.01918](https://arxiv.org/html/2507.01918v2)

#### 7. Adaptive Beta Shrinkage (ABS)
**Paper**: 2025, Tandfonline
**Key idea**: Novel nonlinear shrinkage operating in univariate framework, suited to financial datasets.
**Status**: Reference only — would need to read full paper for implementation.
**Source**: [Tandfonline 2025](https://www.tandfonline.com/doi/full/10.1080/10293523.2025.2553255)

## Synthesized Learnings

1. **Linear methods are saturated for our problem**: BL + EWMA + ensemble at 81% efficiency is near the theoretical limit for linear estimators with N=25, T=60 months.

2. **The gap is in nonlinear estimation**: The oracle uses true mu and true Sigma. Our estimates are linear functions of the data. Nonlinear estimators (neural nets) can potentially capture structure that linear estimators miss.

3. **End-to-end > two-stage**: Estimating mu and Sigma separately, then optimizing, propagates errors. End-to-end approaches that directly learn the portfolio weights avoid this error propagation.

4. **Regularization is everything**: Every approach that removed BL regularization failed catastrophically. Any new approach MUST include strong regularization (L1/L2 penalty, dropout, early stopping, ensemble).

5. **The DGP is simple enough that 25 static numbers suffice**: With constant-drift GBM and no dynamics, the optimal portfolio is a fixed weight vector. This is the simplest possible learning problem — find 25 numbers that maximize Sharpe. PyTorch should be able to learn this.

6. **BL has "dark matter" in unviewed sectors**: The 4 BL views span only 4 directions in 25D weight space. The other 21 directions default to the uninformative EW prior. Within S0/S1/S2 (no views), all assets get equal treatment. Tick-level Sharpe tilt fills this gap — the BIGGEST improvement this session (+3.5 bps from tilt alone, +6.2 bps total).

7. **Tilt should ONLY target unviewed sectors**: Tilting viewed sectors (S3/S4) adds noise because BL already optimally allocates within them. Per-sector alpha (S0/S1/S2=0.02, S3/S4=0.0) beats uniform alpha (all=0.02).

8. **Simplified CV and validate.py rank differently**: Always verify winners with validate.py. The simplified CV (daily rets, no costs) overestimates aggressive configs and underestimates conservative ones.

## Techniques TESTED — Updated

### Within-Sector Tick-Level Sharpe Tilt (SUCCEEDED — +6.2 bps)
| Variant | Mean (validate.py) | Notes |
|---|---|---|
| **Per-sector (rest=0.02, S3/S4=0)** | **+2.163** | **BEST — only tilt unviewed sectors** |
| Uniform alpha=0.02 | +2.160 | Good but tilts S3/S4 unnecessarily |
| Uniform alpha=0.03 | +2.137 | Higher mean in simplified CV but worse in validate.py |
| EWMA-weighted tick SR | +2.160 | No improvement — full sample SR is best signal |
| Rank-based tilt | -0.11 | Destroys signal structure |
| T-stat weighted | +2.160 | Numerically identical to raw SR (sqrt(n) cancels) |
| Winsorized | +2.160 | No outliers within 5-asset sectors |

### PyTorch Direct Weight Learning (FAILED)
- End-to-end Sharpe optimization: Mean +0.49 (random init finds bad local minima)
- BL-initialized fine-tuning: Mean +0.52 (gradient immediately overfits away from BL)
- GP#39: BL provides structural regularization that gradient descent cannot replicate
