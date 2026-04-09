# Portfolio Construction Methods
## Competition Context
- 25 assets, 5 sectors (sector_id known), daily rebalancing
- Gross exposure <= 1 (L1 norm of weights); long/short allowed
- Costs: linear (spread_bps / 2 * |Δw|) + quadratic (2.5 * spread_bps * Δw²)
- Borrow cost: sum(max(-w, 0) * borrow_bps_annual / 252) per day
- Scored on annualized Sharpe (zero risk-free rate) over 12-month holdout
- Only numpy, pandas, scikit-learn, scipy available

---

## 1. Risk Parity (Equal Risk Contribution)

### What It Is
Allocate weights so each asset contributes equally to total portfolio variance.
Asset i's risk contribution: RC_i = w_i * (Σw)_i / (w^T Σ w)
Target: RC_i = 1/N for all i (equal risk contribution).

### Math
Portfolio variance: σ² = w^T Σ w
Marginal risk contribution: MRC_i = (Σw)_i / σ
Risk contribution: RC_i = w_i * MRC_i

Objective: minimize Σ_i (RC_i - RC_j)² for all pairs, or equivalently:

```
minimize Σ_i (w_i * (Σw)_i - σ²/N)²
```

### Implementation (scipy.optimize.minimize)

```python
import numpy as np
from scipy.optimize import minimize

def risk_parity_weights(cov: np.ndarray) -> np.ndarray:
    """
    Equal Risk Contribution portfolio.
    cov: (N, N) covariance matrix
    Returns: (N,) weights (long-only, sum to 1)
    """
    N = cov.shape[0]
    
    def risk_contributions(w):
        port_var = w @ cov @ w
        mrc = cov @ w
        rc = w * mrc
        return rc
    
    def objective(w):
        rc = risk_contributions(w)
        # Minimize variance of risk contributions
        return np.sum((rc - rc.mean()) ** 2)
    
    w0 = np.ones(N) / N
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
    bounds = [(0.0, None)] * N  # long-only; relax for long/short
    
    result = minimize(objective, w0, method='SLSQP',
                      bounds=bounds, constraints=constraints,
                      options={'ftol': 1e-9, 'maxiter': 500})
    w = result.x
    return w / np.sum(np.abs(w))  # normalize to gross exposure constraint
```

**For long/short version:** Remove bounds; add gross exposure constraint:
```python
bounds = [(-1.0, 1.0)] * N
constraints = [
    {'type': 'eq', 'fun': lambda w: np.sum(w)},          # net-zero or near-zero
    {'type': 'ineq', 'fun': lambda w: 1.0 - np.sum(np.abs(w))}  # gross <= 1
]
```

### Pros for This Competition
- Does not require return forecasts — avoids estimation error in expected returns
- Naturally diversified; stable weights day-to-day → lower turnover → lower transaction costs
- Works well when you have no strong return signal (don't know future returns)
- Borrow costs: long-only or near-long-only → minimal short exposure → low borrow costs

### Cons
- Ignores expected returns entirely — leaves alpha on the table if signals exist
- Optimal for risk minimization, not Sharpe maximization
- Long-only risk parity concentrates in low-volatility assets

### When to Use
Use risk parity as a **baseline** and as a component of an ensemble.
If your return signals have poor out-of-sample IC, risk parity will beat mean-variance.

**Sources:**
- https://www.luxalgo.com/blog/risk-parity-allocation-with-python/
- https://thequantmba.wordpress.com/2016/12/14/risk-parityrisk-budgeting-portfolio-in-python/

---

## 2. Minimum Variance Portfolio

### What It Is
```
minimize w^T Σ w
subject to: sum(|w|) <= 1
            (optional) sum(w) = 0 or free
```

### Implementation

```python
from scipy.optimize import minimize
import numpy as np

def min_variance_weights(cov: np.ndarray, long_only: bool = False) -> np.ndarray:
    """
    Global minimum variance portfolio.
    """
    N = cov.shape[0]
    
    def objective(w):
        return w @ cov @ w
    
    def grad(w):
        return 2 * cov @ w
    
    w0 = np.ones(N) / N
    constraints = [{'type': 'ineq', 'fun': lambda w: 1.0 - np.sum(np.abs(w))}]
    
    if long_only:
        bounds = [(0.0, 1.0)] * N
    else:
        bounds = [(-1.0, 1.0)] * N
    
    result = minimize(objective, w0, jac=grad, method='SLSQP',
                      bounds=bounds, constraints=constraints,
                      options={'ftol': 1e-10, 'maxiter': 1000})
    return result.x

# Analytic solution (unconstrained, full gross exposure):
def min_variance_analytic(cov: np.ndarray) -> np.ndarray:
    """Closed-form minimum variance (no gross exposure constraint)."""
    N = cov.shape[0]
    ones = np.ones(N)
    inv_cov = np.linalg.solve(cov, ones)
    w = inv_cov / (ones @ inv_cov)
    # Project to gross exposure <= 1
    gross = np.sum(np.abs(w))
    if gross > 1.0:
        w /= gross
    return w
```

### When Minimum Variance Beats Equal Weight
Research (DeMiguel et al. 2009, Clarke et al. 2011) shows:
- MinVar beats 1/N when there is significant variation in asset volatilities (factor of 2+ range)
- MinVar beats 1/N when correlations are heterogeneous (some assets genuinely low-corr)
- MinVar *fails* equal weight when covariance estimation is very noisy (T << N)

For this competition (T=1000, N=25): MinVar should outperform equal weight, especially with
Ledoit-Wolf covariance. The key risk is that MinVar concentrates heavily in low-vol assets
unless you add diversification constraints.

**Add minimum weight / diversification constraints:**
```python
bounds = [(0.01, 0.2)] * N  # force at least 1% in each asset
```

### Pros
- No return forecasts needed
- Best ex-ante variance by definition (on the estimated covariance)
- Stable when using Ledoit-Wolf covariance

### Cons
- Does not maximize Sharpe unless returns are proportional to variance (CAPM)
- Concentrates in low-vol assets; can be sector-concentrated without constraints
- Out-of-sample variance is higher than in-sample due to estimation error

**Sources:**
- DeMiguel, Garlappi & Uppal (2009) "Optimal vs Naive Diversification"
- https://link.springer.com/article/10.1057/s41283-022-00091-0

---

## 3. Mean-Variance with Shrinkage

### The Problem with Classical MVO
Mean-variance optimization is famously "error-maximizing": the optimizer amplifies errors
in expected return estimates. With 25 assets, expected return estimation is very noisy;
even if your signal has IC=0.05, the optimizer will exploit noise as if it were signal.

### Practical Shrinkage Approaches

#### Option A: Shrink Expected Returns Toward Zero (Grand Mean)
```python
def shrink_returns(mu_hat: np.ndarray, shrinkage: float = 0.5) -> np.ndarray:
    """
    Shrink return forecast toward cross-sectional mean.
    shrinkage=1.0 → use cross-sectional mean for all assets (risk parity equivalent)
    shrinkage=0.0 → use raw signal
    """
    grand_mean = mu_hat.mean()
    return (1 - shrinkage) * mu_hat + shrinkage * grand_mean
```

#### Option B: Maximum Sharpe Portfolio (Tangency Portfolio)
```
maximize (w^T μ) / sqrt(w^T Σ w)
subject to: sum(|w|) <= 1
```

```python
def max_sharpe_weights(mu: np.ndarray, cov: np.ndarray,
                        risk_aversion: float = 1.0) -> np.ndarray:
    """
    Mean-variance tangency portfolio.
    risk_aversion: scales between min-var (large) and return-chasing (small)
    """
    N = len(mu)
    
    def neg_sharpe(w):
        ret = w @ mu
        vol = np.sqrt(w @ cov @ w + 1e-10)
        return -ret / vol
    
    def grad_neg_sharpe(w):
        ret = w @ mu
        var = w @ cov @ w + 1e-10
        vol = np.sqrt(var)
        d_ret = mu
        d_vol = (cov @ w) / vol
        return -(d_ret * vol - ret * d_vol) / var
    
    w0 = np.ones(N) / N
    constraints = [{'type': 'ineq', 'fun': lambda w: 1.0 - np.sum(np.abs(w))}]
    bounds = [(-1.0, 1.0)] * N
    
    result = minimize(neg_sharpe, w0, jac=grad_neg_sharpe, method='SLSQP',
                      bounds=bounds, constraints=constraints)
    return result.x
```

#### Option C: L2-Regularized MVO (Ridge Penalty on Weights)
```
minimize (1/2) w^T Σ w - μ^T w + (λ/2) ||w||²
```
The λ term penalizes large positions, equivalent to shrinking toward zero weights.
Higher λ → more stable, more like equal weight.

```python
def ridge_mvo(mu: np.ndarray, cov: np.ndarray, lam: float = 0.01) -> np.ndarray:
    """
    Ridge-regularized MVO. Adds λI to covariance → stabilizes inversion.
    """
    N = len(mu)
    cov_reg = cov + lam * np.eye(N)
    # Unconstrained solution: w* = (1/gamma) * Σ_reg^{-1} * μ
    w_raw = np.linalg.solve(cov_reg, mu)
    # Project to gross exposure <= 1
    gross = np.sum(np.abs(w_raw))
    if gross > 1.0:
        w_raw /= gross
    return w_raw
```

**Recommended practice for this competition:**
- Use return signals (momentum/reversal) as μ
- Use Ledoit-Wolf Σ
- Add L2 regularization λ ≈ 0.001–0.01
- Validate λ via time-series CV on the 5-year training data

**Source:** https://www.tidy-finance.org/python/constrained-optimization-and-backtesting.html

---

## 4. Maximum Diversification Portfolio

### Definition (Choueifaty & Coignard 2008)
Maximize the Diversification Ratio:
```
DR(w) = (w^T σ) / sqrt(w^T Σ w)
```
where σ_i = sqrt(Σ_ii) are individual asset volatilities.
Numerator = weighted average of individual volatilities.
Denominator = portfolio volatility.
DR > 1 always (by Cauchy-Schwarz); maximum DR exploits diversification maximally.

### Implementation

```python
def max_diversification_weights(cov: np.ndarray) -> np.ndarray:
    """
    Maximum Diversification Portfolio.
    """
    N = cov.shape[0]
    vols = np.sqrt(np.diag(cov))
    
    def neg_dr(w):
        port_vol = np.sqrt(w @ cov @ w + 1e-12)
        weighted_avg_vol = w @ vols
        return -weighted_avg_vol / port_vol
    
    def grad_neg_dr(w):
        port_var = w @ cov @ w + 1e-12
        port_vol = np.sqrt(port_var)
        avg_vol = w @ vols
        d_avg = vols
        d_port_vol = (cov @ w) / port_vol
        return -(d_avg * port_vol - avg_vol * d_port_vol) / port_var
    
    w0 = vols / vols.sum()  # vol-weighted starting point
    constraints = [{'type': 'ineq', 'fun': lambda w: 1.0 - np.sum(np.abs(w))}]
    bounds = [(0.0, 1.0)] * N  # long-only original formulation
    
    result = minimize(neg_dr, w0, jac=grad_neg_dr, method='SLSQP',
                      bounds=bounds, constraints=constraints)
    return result.x
```

**Note:** The original Choueifaty formulation is long-only. The long/short extension is less studied.

### Relationship to Other Methods
- When all correlations are equal: Max Diversification = Minimum Variance
- When all volatilities are equal: Max Diversification = Minimum Variance
- In general: Max Diversification overweights low-corr/high-vol assets vs MinVar

### Pros/Cons
**Pros:** No return forecasts; good Sharpe in empirical studies; naturally diversified
**Cons:** Long-only constraint limits applicability in short-selling context;
  sensitive to correlation estimation noise

**Source:** https://www.tobam.fr/wp-content/uploads/2014/12/TOBAM-JoPM-Maximum-Div-2008.pdf

---

## 5. Black-Litterman Approach

### What It Is
BL blends equilibrium returns (implied by market cap weights or risk-parity weights)
with investor views (your signals), producing a posterior expected return vector:

```
μ_BL = [(τΣ)^{-1} + P^T Ω^{-1} P]^{-1} [(τΣ)^{-1} π + P^T Ω^{-1} q]
```

where:
- π = equilibrium returns (e.g., Σ w_eq * δ, where δ = risk aversion)
- P = views matrix (K views × N assets)
- q = view returns vector (K,)
- Ω = diagonal uncertainty matrix on views
- τ ≈ 1/T (often set to 0.05)

### Practical Use Without Specific Views
If you use BL purely as a shrinkage device (shrink your return signal toward equilibrium):

```python
def black_litterman(cov: np.ndarray, mu_signal: np.ndarray,
                     w_eq: np.ndarray = None, tau: float = 0.05,
                     confidence: float = 0.5) -> np.ndarray:
    """
    Simplified BL: blend signal with equilibrium returns.
    confidence: 0=use only equilibrium, 1=use only signal
    """
    N = cov.shape[0]
    delta = 2.5  # risk aversion coefficient
    
    if w_eq is None:
        w_eq = np.ones(N) / N  # equal weight as equilibrium
    
    # Implied equilibrium returns
    pi = delta * cov @ w_eq
    
    # Single view per asset: we believe returns = mu_signal
    # P = I (N views, one per asset), q = mu_signal
    P = np.eye(N)
    q = mu_signal
    
    # Uncertainty proportional to asset variance
    omega = (1.0 / confidence - 1) * (tau * P @ cov @ P.T)
    
    # BL posterior mean
    left = np.linalg.inv(tau * cov) + P.T @ np.linalg.solve(omega, P)
    right = np.linalg.solve(tau * cov, pi) + P.T @ np.linalg.solve(omega, q)
    mu_bl = np.linalg.solve(left, right)
    
    return mu_bl
```

Then use mu_bl in standard MVO or max-Sharpe optimization.

### Assessment for This Competition
BL is primarily useful when you have a good equilibrium model *and* strong views.
With 25 assets and no market cap data, the equilibrium (π) is artificial.
**Verdict:** BL is likely overkill here. Use shrinkage of returns directly (Section 3, Option A).

**Source:** https://python-advanced.quantecon.org/black_litterman.html

---

## 6. Hierarchical Risk Parity (HRP)

### Why HRP Is Well-Suited for Sector Structure
HRP uses hierarchical clustering to group correlated assets before allocating risk.
With 5 known sectors, the cluster structure will likely mirror the sector labels —
making HRP particularly natural for this competition.

### Algorithm (Lopez de Prado 2016)

**Step 1: Compute correlation-based distance matrix**
```python
dist = np.sqrt((1 - corr) / 2)  # element-wise; corr = correlation matrix
```

**Step 2: Hierarchical clustering**
```python
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform

dist_condensed = squareform(dist)
link = linkage(dist_condensed, method='single')  # or 'ward'
order = leaves_list(link)  # quasi-diagonalization order
```

**Step 3: Quasi-diagonalization**
Reorder the covariance matrix so similar (correlated) assets are adjacent.

**Step 4: Recursive bisection**
Split the asset tree recursively; at each split, allocate inversely proportional to
each cluster's variance.

### Full Implementation (numpy/scipy only)

```python
import numpy as np
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform

def hrp_weights(returns: np.ndarray) -> np.ndarray:
    """
    Hierarchical Risk Parity.
    returns: (T, N) daily returns
    Returns: (N,) portfolio weights (long-only)
    """
    T, N = returns.shape
    cov = np.cov(returns.T)
    corr = np.corrcoef(returns.T)
    
    # Step 1: Distance matrix
    dist = np.sqrt(np.clip((1 - corr) / 2, 0, 1))
    np.fill_diagonal(dist, 0)
    
    # Step 2: Hierarchical clustering
    dist_condensed = squareform(dist)
    link = linkage(dist_condensed, method='single')
    order = leaves_list(link)
    
    # Step 3: Recursive bisection
    def get_cluster_var(cov, cluster_items):
        """Minimum variance portfolio within a cluster."""
        sub_cov = cov[np.ix_(cluster_items, cluster_items)]
        w = np.ones(len(cluster_items)) / len(cluster_items)
        return float(w @ sub_cov @ w)
    
    def recursive_bisect(cov, sorted_items):
        if len(sorted_items) == 1:
            return {sorted_items[0]: 1.0}
        
        mid = len(sorted_items) // 2
        left = sorted_items[:mid]
        right = sorted_items[mid:]
        
        var_left = get_cluster_var(cov, left)
        var_right = get_cluster_var(cov, right)
        
        alpha = 1 - var_left / (var_left + var_right)  # weight for left cluster
        
        w_left = recursive_bisect(cov, left)
        w_right = recursive_bisect(cov, right)
        
        weights = {}
        for k, v in w_left.items():
            weights[k] = v * alpha
        for k, v in w_right.items():
            weights[k] = v * (1 - alpha)
        return weights
    
    weight_dict = recursive_bisect(cov, list(order))
    w = np.array([weight_dict[i] for i in range(N)])
    return w

# Sector-aware version: use sector_id to inform clustering
def hrp_with_sector_prior(returns: np.ndarray, sector_ids: np.ndarray) -> np.ndarray:
    """
    HRP with sector structure: blend distance matrix with sector indicator.
    """
    T, N = returns.shape
    cov = np.cov(returns.T)
    corr = np.corrcoef(returns.T)
    
    stat_dist = np.sqrt(np.clip((1 - corr) / 2, 0, 1))
    np.fill_diagonal(stat_dist, 0)
    
    # Sector distance: 0 if same sector, 1 if different sector
    sector_dist = (sector_ids[:, None] != sector_ids[None, :]).astype(float)
    
    # Blend: 70% statistical, 30% sector structure
    blend_dist = 0.7 * stat_dist + 0.3 * sector_dist
    np.fill_diagonal(blend_dist, 0)
    
    dist_condensed = squareform(blend_dist)
    link = linkage(dist_condensed, method='ward')
    order = leaves_list(link)
    
    # ... recursive bisection as above ...
    return hrp_weights(returns)  # simplified; plug in order from blend_dist
```

### HRP vs Other Methods (Out-of-Sample Evidence)
From Lopez de Prado (2016) Monte Carlo simulations:
- HRP achieves **lower out-of-sample variance than CLA/MinVar** despite not explicitly minimizing variance
- HRP improves Sharpe over CLA by ~31% out-of-sample
- MinVar in-sample variance < HRP, but out-of-sample: MinVar variance is 72% *higher* than HRP

This is because HRP avoids matrix inversion — the key source of instability in MinVar.

**Sources:**
- https://hudsonthames.org/an-introduction-to-the-hierarchical-risk-parity-algorithm/
- https://kenwuyang.com/posts/2024_10_20_portfolio_optimization_with_python_hierarchical_risk_parity/
- https://en.wikipedia.org/wiki/Hierarchical_Risk_Parity

---

## 7. Incorporating Transaction Costs into the Optimization

### The Problem
The validate.py scoring deducts:
```
cost_day = sum(spread/2 * |Δw|) + sum(2.5 * spread * Δw²)
```
For assets with spread_bps up to 12 bps, each round-trip costs 6–30 bps.
Daily rebalancing with high turnover can easily destroy 5–10% annually.

### Method 1: Direct Cost Penalization in Objective
Add transaction costs explicitly to the optimization objective:

```python
def cost_aware_weights(mu: np.ndarray, cov: np.ndarray,
                        w_prev: np.ndarray, spread: np.ndarray,
                        gamma: float = 1.0, tc_weight: float = 1.0) -> np.ndarray:
    """
    MVO with explicit transaction cost penalty.
    
    Objective: maximize μ^T w - γ/2 * w^T Σ w - TC(w - w_prev)
    
    spread: (N,) spread in fraction (e.g., 0.0007 for 7 bps)
    tc_weight: multiplier on transaction cost term
    """
    N = len(mu)
    linear_cost = spread / 2.0
    quad_cost = 2.5 * spread
    
    def neg_objective(w):
        ret = w @ mu
        risk = 0.5 * gamma * (w @ cov @ w)
        delta = w - w_prev
        tc_linear = tc_weight * np.sum(linear_cost * np.abs(delta))
        tc_quad = tc_weight * np.sum(quad_cost * delta**2)
        return -(ret - risk - tc_linear - tc_quad)
    
    w0 = w_prev.copy()
    bounds = [(-1.0, 1.0)] * N
    constraints = [{'type': 'ineq', 'fun': lambda w: 1.0 - np.sum(np.abs(w))}]
    
    result = minimize(neg_objective, w0, method='SLSQP',
                      bounds=bounds, constraints=constraints)
    return result.x
```

**Key insight:** Because quadratic costs are proportional to Δw², the optimizer will naturally
prefer small rebalancing steps. The cost structure in this competition is exactly proportional to
what MVO + quadratic penalty handles.

### Method 2: Turnover Constraint
Add a hard constraint: sum(|w - w_prev|) <= turnover_limit

```python
constraints = [
    {'type': 'ineq', 'fun': lambda w: 1.0 - np.sum(np.abs(w))},
    {'type': 'ineq', 'fun': lambda w: turnover_limit - np.sum(np.abs(w - w_prev))}
]
```

**Pros:** Easy to interpret; directly limits cost exposure
**Cons:** Hard constraint → optimizer may be infeasible if limit is too tight; discontinuous gradient

### Method 3: Lazy Rebalancing (No-Trade Band)
Only rebalance when a position deviates by more than a threshold from its target:

```python
def lazy_rebalance(w_target: np.ndarray, w_current: np.ndarray,
                    threshold: float = 0.01) -> np.ndarray:
    """Only rebalance assets deviating > threshold from target."""
    delta = np.abs(w_target - w_current)
    w_new = w_current.copy()
    rebalance_mask = delta > threshold
    w_new[rebalance_mask] = w_target[rebalance_mask]
    # Renormalize
    gross = np.sum(np.abs(w_new))
    if gross > 1.0:
        w_new /= gross
    return w_new
```

### Choosing the Right Approach for This Competition
Given the cost structure (linear + quadratic), **direct penalization (Method 1) is best**.
The quadratic term especially benefits from being in the objective — it naturally discourages
large position changes in a way that is consistent with the actual scoring mechanic.

**Calibrate tc_weight via CV:** Try tc_weight in {0.5, 1.0, 2.0, 5.0} and validate Sharpe
on the 5-year training data using the 3-fold CV option in validate.py.

**Sources:**
- https://www.tidy-finance.org/python/constrained-optimization-and-backtesting.html
- https://wp.lancs.ac.uk/fofi2018/files/2018/03/FoFI-2017-0031-Chulwoo-Han.pdf

---

## 8. Turnover Constraints vs Cost Penalization

| Approach | Pros | Cons | Best for |
|----------|------|------|----------|
| Turnover constraint (hard) | Guarantees max cost; easy to reason about | Infeasibility risk; non-smooth | Simple strategies |
| Cost penalization (soft) | Smooth, consistent with scoring mechanic; always feasible | Parameter to tune | MVO + transaction costs |
| No-trade band | Very low overhead; easy to implement | May miss large rebalancing signals | High-frequency strategies |
| Decay weights to previous | Continuous interpolation; no optimization needed | Ignores signal strength | Pure risk-based methods |

**For this competition (daily rebalancing, linear + quadratic costs):**
Use soft penalization with tc_weight tuned via CV. The quadratic cost structure in the competition
matches exactly the quadratic penalty term in the objective.

**Turnover budget rule of thumb:**
If average spread is ~5 bps and you rebalance daily:
- 10% turnover/day → ~0.5 bps linear cost/day → ~1.3%/year linear cost
- Plus quadratic: 2.5 * 5bps * (0.1)² = 0.0125 bps/day → negligible
- At 50% turnover/day: ~3%/year linear + 0.3%/year quadratic
- Target: keep daily turnover < 20% of gross exposure

---

## 9. Practical Tips: What Actually Works in Competitions vs Theory

### What Actually Works

1. **Ensemble of simple strategies beats clever single strategy**
   Combine min-variance + risk-parity + momentum signal with fixed blend weights.
   Ensemble reduces model risk significantly.

2. **Reduce gross exposure based on market stress**
   Track rolling portfolio volatility. When realized vol > 2x historical average,
   scale gross exposure down. This avoids blow-up events.

3. **Covariance matters more than return forecasts**
   A good covariance estimate with zero return signal (risk parity) often beats
   a noisy return signal with sample covariance. Use Ledoit-Wolf covariance always.

4. **Turnover kills Sharpe at daily frequency**
   At 5–12 bps spread, the cost of excessive turnover dominates small alpha.
   A strategy with Sharpe 1.0 pre-cost but 40% daily turnover may end up with Sharpe 0.3 after costs.

5. **Momentum lookback should match your rebalancing frequency**
   For daily rebalancing: use momentum lookbacks of 20–60 days.
   Avoid 252-day momentum for daily rebalancing — it changes too slowly to add value.

6. **Use sector_id to reduce noise**
   Sector-neutralize your signal: compute within-sector z-scores rather than cross-asset z-scores.
   This makes the signal more stable and avoids systematic sector bets.

7. **Validate everything with the CV flag**
   Run `python validate.py --cv` to get 3-fold time-series cross-validation.
   Don't use the single 4-year/1-year split for hyperparameter tuning — it has only one test period.

8. **Don't over-optimize to training data**
   Strategies with many hyperparameters tuned to a 5-year backtest will over-fit.
   Stick to 1–3 key parameters (lookback, risk aversion, tc_weight) each with economic motivation.

### What Theory Predicts vs Reality

| Method | Theoretical Edge | Competition Reality |
|--------|----------------|---------------------|
| Full MVO (sample cov) | Optimal if cov/returns known | Usually loses to 1/N due to estimation error |
| Mean-variance + L-W shrinkage | Near-optimal | Works well; use as primary |
| Risk parity | No alpha but low vol | Very competitive when no good signal |
| HRP | Better OOS than MinVar | Strong baseline; implement this |
| Black-Litterman | Elegant blending | Overkill without reliable equilibrium |
| ML return prediction | Potentially high IC | Dangerous without large data; stick to momentum |

### Recommended Build Order

1. **Start with Ledoit-Wolf minimum variance** as the base — stable, implementable, beats equal weight
2. **Add HRP as alternative** — implement with sector structure; compare via CV
3. **Add time-series momentum signal (60-day)** on top of risk parity weights
4. **Add transaction cost penalization** to whatever optimizer you use
5. **Ensemble**: combine MinVar, HRP, and momentum-weighted risk parity with equal blend weights
6. **Scale exposure** by inverse of rolling realized volatility

### Pseudo-implementation Sketch

```python
class MyStrategy(StrategyBase):
    def __init__(self, lookback=60, lw_shrink=True, tc_weight=1.0, vol_target=0.10):
        self.lookback = lookback
        self.lw_shrink = lw_shrink
        self.tc_weight = tc_weight
        self.vol_target = vol_target
        self.w_prev = None
    
    def fit(self, train_prices, meta, **kwargs):
        self.meta = meta
        self.w_prev = np.ones(N_ASSETS) / N_ASSETS
    
    def get_weights(self, price_history, meta, day):
        # 1. Compute returns
        prices = price_history[-(self.lookback * 30 + 1):]  # last lookback days
        # Sample one tick per day (end of day)
        daily_px = prices[::30] if prices.shape[0] >= 30 else prices
        if daily_px.shape[0] < 20:
            return self.w_prev
        returns = np.log(daily_px[1:] / daily_px[:-1])
        
        # 2. Estimate covariance
        from sklearn.covariance import LedoitWolf
        lw = LedoitWolf().fit(returns)
        cov = lw.covariance_
        
        # 3. Compute momentum signal
        if returns.shape[0] >= self.lookback:
            mu = returns.mean(axis=0)  # simple mean as proxy
        else:
            mu = np.zeros(N_ASSETS)
        
        # 4. Risk-parity + signal blend
        w_rp = risk_parity_weights(cov)
        # Scale by signal
        signal = (mu - mu.mean()) / (mu.std() + 1e-8)
        w_signal = w_rp * (1 + 0.2 * signal)
        
        # 5. Cost-aware optimization
        w_opt = cost_aware_weights(mu, cov, self.w_prev,
                                    meta.spread_bps / 1e4,
                                    tc_weight=self.tc_weight)
        
        # 6. Blend
        w_final = 0.5 * w_rp + 0.5 * w_opt
        
        # 7. Volatility scaling
        port_vol = np.sqrt(w_final @ cov @ w_final) * np.sqrt(252)
        if port_vol > 0:
            scale = min(1.0, self.vol_target / port_vol)
            w_final *= scale
        
        # 8. Project to gross exposure constraint
        gross = np.sum(np.abs(w_final))
        if gross > 1.0:
            w_final /= gross
        
        self.w_prev = w_final
        return w_final
```

---

## Summary Recommendation

**Best single strategy for this competition:**
Hierarchical Risk Parity with Ledoit-Wolf covariance + 60-day time-series momentum tilt
+ transaction cost penalization.

**Rationale:**
- HRP avoids matrix inversion (stable OOS)
- LW covariance is guaranteed PD and analytical
- Momentum tilt adds alpha without full MVO instability
- TC penalization directly targets the scoring mechanic
- All implementable with numpy + scipy + sklearn

**Fallback if HRP/momentum underperforms on CV:**
Ledoit-Wolf minimum variance portfolio (no return signal) — clean, stable, likely to deliver
Sharpe > 1.0 in a structured market with 25 assets.
