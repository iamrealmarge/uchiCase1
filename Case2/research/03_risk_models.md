# Risk Models for Portfolio Optimization
## Competition Context
- 25 assets, 5 sectors, ~5 years of daily data (4-year train + 1-year holdout)
- Tick resolution: 30 ticks/day; only daily close-to-close matters for covariance estimation
- Available libraries: numpy, pandas, scikit-learn, scipy
- Scored on annualized Sharpe over 12-month hidden holdout
- Gross exposure <= 1 (long/short allowed); borrow costs apply to shorts

---

## 1. Covariance Estimation

### 1.1 Sample Covariance — Pitfalls

With N=25 assets and T≈1000 trading days of history, the ratio p/n = 25/1000 = 0.025.
This is "low-dimensional" by asymptotic standards, but the sample covariance still has problems:

**Why sample covariance causes trouble in portfolio optimization:**
- The optimizer amplifies estimation errors: small eigenvalue errors → huge weight instability
- The minimum eigenvalue of the sample covariance is systematically underestimated (Marcenko-Pastur law)
- Out-of-sample variance of a minimum-variance portfolio built on sample covariance is substantially
  higher than in-sample — often 2–4x
- Rule of thumb: regularization is recommended when T < 3N. For 25 assets that means < 75 days.
  With 1000 days we are fine *in principle*, but covariance is non-stationary, so the effective
  sample size for recent structure is much smaller.

**Practical effect in this competition:**
- Daily rebalancing means the optimizer runs every day; any instability in the covariance matrix
  cascades into high turnover and transaction costs
- Borrow costs penalize shorts — an unstable covariance estimate will randomly flip signs on weights

**References:**
- Ledoit & Wolf (2004), "A Well-Conditioned Estimator for Large-Dimensional Covariance Matrices"
  https://www.ledoit.net/honey.pdf
- sklearn documentation on shrinkage: https://scikit-learn.org/stable/modules/covariance.html

---

### 1.2 Ledoit-Wolf Shrinkage (Available in sklearn)

**Formula:**

```
Σ_shrunk = (1 - α) * Σ_sample + α * μ * I
where μ = trace(Σ_sample) / n_assets
```

α (shrinkage intensity) is chosen analytically to minimize expected MSE — no cross-validation needed.

**sklearn implementation:**

```python
from sklearn.covariance import LedoitWolf

lw = LedoitWolf(assume_centered=False)
lw.fit(returns)          # returns: shape (T, N)
cov = lw.covariance_     # shape (N, N)
alpha = lw.shrinkage_    # shrinkage coefficient, typically 0.05–0.20 for 25 assets
```

**Key properties:**
- Guaranteed positive definite (invertible) — critical for mean-variance optimization
- Shrinkage coefficient is computed analytically (Oracle Approximating Shrinkage formula)
- Converges to the Oracle estimator asymptotically
- For N=25, T=1000: typical shrinkage ~0.05–0.15 (small, appropriate — won't distort much)
- Computationally trivial: O(N²T)

**Pros:**
- No tuning; just call `.fit()`
- Sklearn's OAS variant is marginally better asymptotically but nearly identical in practice
- Well-suited for minimum-variance and mean-variance portfolios

**Cons:**
- Shrinks toward scaled identity — assumes all assets have similar variance, which may not hold
- Does not capture time-varying volatility (regimes, GARCH effects)
- Alternative target: shrink toward constant-correlation matrix (not in sklearn but easy to code)

**Source:** https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html

---

### 1.3 Exponentially Weighted Covariance (EWMA)

**Formula:**

```
Σ_t = λ * Σ_{t-1} + (1-λ) * r_t r_t^T
```

Equivalently, using pandas:

```python
# pandas EWM covariance
def ewm_cov(returns, span=60):
    """
    span: effective window in days (λ = 1 - 2/(span+1))
    span=60  → λ ≈ 0.967  (half-life ≈ 20 days)
    span=120 → λ ≈ 0.984  (half-life ≈ 40 days)
    """
    return returns.ewm(span=span).cov().iloc[-25:].values  # last slice = most recent N×N block
```

**Pure numpy implementation:**

```python
def ewma_cov(returns: np.ndarray, half_life: int = 30) -> np.ndarray:
    """
    returns: shape (T, N)
    half_life: days — recent observations decay by half over this window
    """
    T, N = returns.shape
    lam = 0.5 ** (1.0 / half_life)
    weights = lam ** np.arange(T - 1, -1, -1)   # oldest → smallest weight
    weights /= weights.sum()
    mu = (weights[:, None] * returns).sum(axis=0)
    demeaned = returns - mu
    cov = (weights[:, None, None] * demeaned[:, :, None] * demeaned[:, None, :]).sum(axis=0)
    return cov
```

**Half-life guidance (Bloomberg/RiskMetrics standard):**
- Volatilities: half-life 26–60 days (captures regime shifts quickly)
- Correlations: half-life 52–120 days (correlations are stickier)
- RiskMetrics uses λ=0.94 daily → equivalent window ≈ 33 days

**Pros:**
- Reacts to volatility regimes in real time
- Simple to implement with numpy
- Naturally down-weights stale data during quiet periods before a crisis

**Cons:**
- Sensitive to choice of half-life (requires validation)
- Can produce unstable covariance during market stress (sudden spikes in all correlations)
- Doesn't provide analytical confidence bounds like Ledoit-Wolf

**Sources:**
- https://portfoliooptimizer.io/blog/covariance-matrix-forecasting-iterated-exponentially-weighted-moving-average-model/
- https://web.stanford.edu/~boyd/papers/pdf/ewmm.pdf (Luxenberg & Boyd)

---

### 1.4 Factor Models (PCA-Based and Sector-Based)

#### 1.4.1 PCA Factor Model

Decomposes returns into K systematic factors + idiosyncratic noise:

```
r = B f + ε
Σ = B F B^T + D
```

where B is N×K loadings matrix, F is K×K factor covariance, D is diagonal idiosyncratic covariance.

**Implementation:**

```python
from sklearn.decomposition import PCA
import numpy as np

def pca_cov(returns: np.ndarray, n_factors: int = 5) -> np.ndarray:
    """
    returns: shape (T, N)
    n_factors: number of PCA factors to retain
    """
    T, N = returns.shape
    pca = PCA(n_components=n_factors)
    pca.fit(returns)
    
    B = pca.components_.T             # (N, K) loadings
    factors = returns @ B              # (T, K) factor returns
    F = np.cov(factors.T)             # (K, K) factor covariance
    
    residuals = returns - factors @ B.T
    D = np.diag(np.var(residuals, axis=0))  # (N, N) diagonal idiosyncratic
    
    cov = B @ F @ B.T + D
    return cov
```

**How many factors for 25 assets?**
- Scree plot / variance explained: 5 factors often explain 60–80% of variance for equity portfolios
- Bai-Ng (2002) criterion suggests ~3–6 factors for 25 US-style assets
- For sector-structured data: K = number of sectors = 5 is a natural choice

**Pros:**
- Drastically reduces parameter count: K(K+1)/2 + N for factor model vs N(N+1)/2 for full sample
  (e.g., 5 factors + 25 idio: 40 params vs 325 params)
- Naturally handles sector co-movements
- More stable out-of-sample than unrestricted sample covariance

**Cons:**
- PCA factors have no economic interpretation — may be hard to regularize sensibly
- Rotation ambiguity: PCA factors change as data window grows
- With 25 assets, the gain over Ledoit-Wolf is modest unless T is short

#### 1.4.2 Sector-Based Factor Model

Given that we have sector_id for all 25 assets, a sector factor model is natural:

```python
def sector_factor_cov(returns: np.ndarray, sector_ids: np.ndarray) -> np.ndarray:
    """
    Construct covariance from sector factors.
    returns: (T, N), sector_ids: (N,) with integer labels 0..4
    """
    T, N = returns.shape
    sectors = np.unique(sector_ids)
    K = len(sectors)
    
    # Sector factor returns = equal-weight average within sector
    factor_returns = np.zeros((T, K))
    for k, s in enumerate(sectors):
        mask = (sector_ids == s)
        factor_returns[:, k] = returns[:, mask].mean(axis=1)
    
    F = np.cov(factor_returns.T)  # (K, K)
    
    # Loadings: OLS regression of each asset on sector factors
    B = np.zeros((N, K))
    residuals = np.zeros((T, N))
    for i in range(N):
        coef = np.linalg.lstsq(factor_returns, returns[:, i], rcond=None)[0]
        B[i] = coef
        residuals[:, i] = returns[:, i] - factor_returns @ coef
    
    D = np.diag(np.var(residuals, axis=0))
    return B @ F @ B.T + D
```

**Source:** https://docs.mosek.com/portfolio-cookbook/factormodels.html

---

### 1.5 Recommendation: Which Covariance Estimator to Use?

**For 25 assets, 5 years (~1000 days) of daily data:**

| Estimator | Recommended? | Reason |
|-----------|-------------|--------|
| Sample covariance | No | Unstable despite adequate T due to non-stationarity |
| Ledoit-Wolf (sklearn) | **Yes — primary choice** | Analytical, no tuning, positive-definite, sklearn native |
| EWMA (half-life=30-60) | **Yes — secondary/blend** | Captures regime changes; use for risk budgeting |
| PCA factor model (K=5) | Maybe | Good if sector structure is strong; adds complexity |
| Sector factor model | **Yes — good supplement** | Exploits known sector_id metadata |

**Practical recommendation:**
Use Ledoit-Wolf as the base for optimization (stable, invertible).
Use EWMA as a cross-check for risk scaling: if EWMA shows a volatility spike, reduce gross exposure.
The sector factor model is worth trying as a robustness check.

**Do not combine multiple estimators naively** — pick one for the optimizer and stick with it per strategy variant tested via CV.

---

## 2. Return Forecasting

### 2.1 Cross-Sectional Momentum

**Definition:** Sort assets by past return over a lookback window; go long top decile, short bottom decile.

```python
def cross_sectional_momentum(returns: np.ndarray, lookback: int = 60, skip: int = 1) -> np.ndarray:
    """
    Cross-sectional momentum signal.
    returns: (T, N) daily log-returns
    lookback: formation window in days (e.g., 60 = 3 months)
    skip: skip most recent `skip` days (avoids short-term reversal)
    Returns signal: (N,) — positive = long, negative = short
    """
    if returns.shape[0] < lookback + skip:
        return np.zeros(returns.shape[1])
    
    # Cumulative return over lookback, skipping most recent `skip` days
    window = returns[-(lookback + skip):-skip] if skip > 0 else returns[-lookback:]
    cum_ret = window.sum(axis=0)   # (N,) cumulative log-return
    
    # Cross-sectionally standardize
    signal = (cum_ret - cum_ret.mean()) / (cum_ret.std() + 1e-8)
    return signal
```

**Evidence:** Cross-sectional momentum (Jegadeesh & Titman 1993) has been the most robust anomaly
in academic literature. Lookbacks of 3–12 months (skipping last 1 month) are standard.

**Key nuance for this competition:**
- With only 25 assets, cross-sectional sorting is noisy (only 25 observations per sort)
- Use z-scores rather than rank-based signals for smooth weight interpolation
- The 1-month skip is less important at daily rebalancing but consider a 5-day skip

**Sources:**
- https://quantpedia.com/strategies/time-series-momentum-effect
- Jegadeesh & Titman (1993) — foundational

---

### 2.2 Time-Series (Absolute) Momentum

**Definition:** Go long an asset if its past return is positive; short if negative. Independent of
cross-asset comparisons.

```python
def time_series_momentum(returns: np.ndarray, lookback: int = 60) -> np.ndarray:
    """
    TSMOM signal: sign of cumulative return over lookback.
    Returns (N,) values in {-1, 0, +1} or smoothed version.
    """
    if returns.shape[0] < lookback:
        return np.zeros(returns.shape[1])
    window = returns[-lookback:]
    cum_ret = window.sum(axis=0)
    # Smooth version: scale by Sharpe-like measure
    sharpe_signal = cum_ret.mean(axis=0) / (cum_ret.std(axis=0) + 1e-8) * np.sqrt(lookback)
    return sharpe_signal
```

**Evidence:**
- Moskowitz, Ooi & Pedersen (2012) showed TSMOM earns positive risk-adjusted returns at 1–12 month
  horizons, with time-series implementation outperforming cross-sectional on Sharpe
- TSMOM is less affected by cross-asset correlation estimation errors

---

### 2.3 Mean Reversion at Different Horizons

**Short-term reversal (1–5 days):**
- Past losers over 1 week tend to outperform next week; past winners underperform
- Mechanism: liquidity provision, market microstructure
- Daily reversal signal:

```python
def short_reversal_signal(returns: np.ndarray, lookback: int = 5) -> np.ndarray:
    """Negative of recent returns — mean reversion signal."""
    if returns.shape[0] < lookback:
        return np.zeros(returns.shape[1])
    recent = returns[-lookback:].sum(axis=0)
    signal = -recent  # long recent losers, short recent winners
    return (signal - signal.mean()) / (signal.std() + 1e-8)
```

**Evidence:** Jegadeesh (1990), Lehmann (1990) — weekly reversal is statistically significant but
decreases after transaction costs. The reversal is strongest at the 1-week horizon and fades by 1 month.

**Monthly/intermediate reversal (1–36 months):**
- Contrarian signal: long 3-5 year losers, short winners (De Bondt & Thaler 1985)
- Less relevant for daily rebalancing; works over multi-year horizons

**Combination for this competition:**
A dual-signal approach is practical:
```
signal = α * momentum_signal(lookback=60) + β * reversal_signal(lookback=5)
```
where α > 0, β > 0 (both go in opposite directions of recent returns at different scales).

---

### 2.4 Sector Momentum / Rotation

```python
def sector_momentum_signal(returns: np.ndarray, sector_ids: np.ndarray,
                            lookback: int = 60) -> np.ndarray:
    """
    Compute sector-level momentum; assign each asset the signal of its sector.
    """
    T, N = returns.shape
    if T < lookback:
        return np.zeros(N)
    
    sectors = np.unique(sector_ids)
    sector_signal = np.zeros(N)
    
    for s in sectors:
        mask = (sector_ids == s)
        sector_ret = returns[-lookback:][:, mask].mean(axis=1)  # equal-weight sector index
        cum = sector_ret.sum()
        sector_signal[mask] = cum
    
    # Cross-sectionally normalize across sectors
    sector_signal = (sector_signal - sector_signal.mean()) / (sector_signal.std() + 1e-8)
    return sector_signal
```

**Interpretation:** Overweight assets in high-momentum sectors; underweight in low-momentum sectors.
This is orthogonal to within-sector cross-sectional momentum.

**Evidence:** Moskowitz & Grinblatt (1999) showed sector momentum explains much of individual stock
momentum. With 5 sectors and 25 assets, this is cleaner than pure stock-level momentum.

---

### 2.5 Volatility-Adjusted Returns

**Idea:** Divide raw return signals by recent volatility to equalize risk contribution of signals.

```python
def vol_adjusted_signal(raw_signal: np.ndarray, returns: np.ndarray,
                         vol_lookback: int = 20) -> np.ndarray:
    """
    Scale signal by inverse of recent volatility.
    Reduces position in high-vol assets automatically.
    """
    recent_vol = returns[-vol_lookback:].std(axis=0) + 1e-8
    return raw_signal / recent_vol
```

This is closely related to volatility targeting: allocate inversely proportional to volatility
so each position contributes equal ex-ante risk.

---

### 2.6 Which Signals Are Robust Out-of-Sample?

Based on academic literature and competition evidence:

| Signal | Lookback | Out-of-Sample Robustness | Notes |
|--------|----------|--------------------------|-------|
| Cross-sectional momentum | 60–252 days, skip 5 | High | Most replicated anomaly |
| Time-series momentum | 60–252 days | High | Better Sharpe than XS momentum |
| Short-term reversal | 1–5 days | Moderate | Eroded by transaction costs in liquid markets |
| Sector momentum | 60–120 days | High | Robust, explains individual stock momentum |
| Long-term reversal | 1–3 years | Low | Only useful at very long horizons |
| Vol-adjusted signals | — | High | Reduces drawdowns, not alpha itself |

**Bottom line for this competition:**
1. **Primary signal:** Time-series momentum with 60-day and 252-day lookbacks
2. **Secondary signal:** Sector momentum (exploits the known sector_id metadata)
3. **Tertiary signal:** Short-term reversal (5-day) — but only if transaction costs are managed
4. Always volatility-adjust before constructing portfolio weights

**Sources:**
- https://quantpedia.com/strategies/time-series-momentum-effect
- https://www.cmegroup.com/education/files/dissecting-investment-strategies-in-the-cross-section-and-time-series.pdf
- https://alphaarchitect.com/cross-section-of-returns/
