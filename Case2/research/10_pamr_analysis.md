# PAMR Algorithm Analysis: Deep Dive from CTC Competition Repos

## 1. Source Repositories Analyzed

| Repo | Year | Case 2 Type | Final Algorithm |
|------|------|-------------|-----------------|
| zaranip/Chicago-Trading-Competition-2024 | 2024 | Portfolio Optimization (6 assets) | **PAMR** |
| coolkite/Chicago-Trading-Competition-2024 | 2024 | Portfolio Optimization (6 assets) | **PAMR** (identical fork) |
| John-Trager/UChicago-Trading-Competition | 2022 | Options Market Making | N/A (different case) |

**Key finding:** zaranip and coolkite repos are forks of each other -- identical code. The john-trager repo is from 2022 where Case 2 was options market making, not portfolio optimization. All portfolio optimization analysis comes from the zaranip/coolkite codebase.

---

## 2. The PAMR Algorithm: Theory

### 2.1 What is PAMR?

**PAMR = Passive Aggressive Mean Reversion** (Li et al., 2012)

It is an online portfolio selection algorithm based on the **mean reversion** assumption -- the hypothesis that asset prices will tend to revert to their historical averages. It belongs to the family of "follow-the-loser" strategies (as opposed to momentum/follow-the-winner).

The key insight: if prices go up "too much" (above a threshold epsilon), the algorithm passively-aggressively shifts weight away from winners and toward losers, betting on reversion.

### 2.2 Mathematical Formulation

Given:
- `b_t` = portfolio weight vector at time t (on the simplex: all non-negative, sum to 1)
- `x_t` = price relative vector at time t (today's price / yesterday's price, or normalized prices)
- `eps` (epsilon) = mean reversion threshold
- `C` = aggressiveness parameter (for PAMR-1 and PAMR-2 variants)

**Step 1: Compute the loss**
```
loss_t = max(0, b_t . x_t - eps)
```
The loss is positive only when the portfolio return exceeds epsilon. This is the "passive" part -- no adjustment needed if returns are below the threshold.

**Step 2: Compute the Lagrangian multiplier (lambda)**

Three variants:
- **PAMR-0:** `lambda = loss / ||x - x_mean||^2` (unconstrained)
- **PAMR-1:** `lambda = min(C, loss / ||x - x_mean||^2)` (capped at C)
- **PAMR-2:** `lambda = loss / (||x - x_mean||^2 + 1/(2C))` (regularized)

**Step 3: Update weights**
```
b_{t+1} = b_t - lambda * (x_t - x_mean)
```
This shifts weight *away* from assets that performed above average and *toward* those that performed below average.

**Step 4: Project back to the simplex**
Ensure weights are non-negative and sum to 1 using simplex projection.

### 2.3 Parameters and Their Effects

| Parameter | Role | Range | Effect |
|-----------|------|-------|--------|
| `eps` (epsilon) | Mean reversion threshold | 0.0 - 1.0+ | Lower = more aggressive rebalancing; higher = more passive |
| `C` | Aggressiveness cap (variants 1,2 only) | 1 - 10000 | Higher = more aggressive; PAMR-1 caps lambda at C; PAMR-2 uses C as regularization |
| `variant` | Algorithm variant | 0, 1, 2 | 0 = unconstrained; 1 = capped; 2 = regularized |
| `max_weight` | Per-asset weight cap | 0.0 - 1.0 | Prevents over-concentration in a single asset |

### 2.4 Why PAMR Works for This Competition

1. **Mean-reverting data**: The EDA in the repos confirmed that the provided assets exhibit mean reversion (Hurst exponents < 0.5 for some assets, cointegration between pairs).
2. **Online learning**: PAMR updates weights incrementally with each new price observation -- perfect for the competition's sequential day-by-day format.
3. **No lookahead bias**: The algorithm only uses current and past prices.
4. **Simplex constraint**: Naturally produces valid portfolio weights (non-negative, sum to 1).
5. **Computational efficiency**: O(n) per update where n = number of assets. No matrix inversions, no optimization solvers.

---

## 3. Exact Implementation from the Repos

### 3.1 Final PAMR Implementation (chosen for submission)

File: `case_2/final_algorithm/PAMR.py`

```python
class Allocator():
    def __init__(self, train_data, eps=0.5, C=500, variant=0, max_weight=0.25):
        self.running_price_paths = train_data.copy()
        self.train_data = train_data.copy()
        self.eps = eps
        self.C = C
        self.variant = variant
        self.max_weight = max_weight
        self.last_b = self.init_weights(train_data.columns)

    def init_weights(self, columns):
        m = len(columns)
        return np.ones(m) / m  # Equal weight initialization

    def update(self, b, x, eps, C):
        x_mean = np.mean(x)
        le = max(0.0, np.dot(b, x) - eps)  # Loss: max(0, portfolio_return - eps)

        if self.variant == 0:  # PAMR-0: unconstrained
            lam = le / np.linalg.norm(x - x_mean) ** 2
        elif self.variant == 1:  # PAMR-1: capped at C
            lam = min(C, le / np.linalg.norm(x - x_mean) ** 2)
        elif self.variant == 2:  # PAMR-2: regularized
            lam = le / (np.linalg.norm(x - x_mean) ** 2 + 0.5 / C)

        lam = min(100000, lam)  # Safety cap to prevent numerical explosion
        b = b - lam * (x - x_mean)  # Mean reversion update
        b = self.simplex_proj(b)     # Project onto simplex
        b = np.minimum(b, self.max_weight)  # Cap individual weights
        b /= np.sum(b)              # Re-normalize
        return b

    def simplex_proj(self, b):
        """Euclidean projection onto the probability simplex."""
        m = len(b)
        bget = False
        s = sorted(b, reverse=True)
        tmpsum = 0.0
        for ii in range(m - 1):
            tmpsum = tmpsum + s[ii]
            tmax = (tmpsum - 1) / (ii + 1)
            if tmax >= s[ii + 1]:
                bget = True
                break
        if not bget:
            tmax = (tmpsum + s[m - 1] - 1) / m
        return np.maximum(b - tmax, 0.0)

    def allocate_portfolio(self, asset_prices):
        new_data = pd.DataFrame([asset_prices], columns=self.train_data.columns)
        self.running_price_paths = pd.concat(
            [self.running_price_paths, new_data], ignore_index=True
        )
        # Normalize prices by their mean before updating
        self.last_b = self.update(
            self.last_b,
            asset_prices / asset_prices.mean(),  # <-- CRITICAL: normalized prices
            self.eps,
            self.C
        )
        return self.last_b
```

### 3.2 Key Implementation Details

**Chosen parameters for final submission:**
- `eps = 0.5`
- `C = 500`
- `variant = 0` (PAMR-0, unconstrained lambda)
- `max_weight = 0.25` (no single asset gets more than 25% allocation)
- Commented-out alternative: `max_weight=0.3`

**Data normalization:** Prices are divided by their cross-sectional mean (`asset_prices / asset_prices.mean()`) before being passed to the update function. This is important -- it makes the "x" in the PAMR formula a relative price measure rather than absolute prices.

**Train/test split:** `test_size=0.9` -- they used only 10% of data for training, 90% for testing. This is very aggressive and shows confidence that PAMR doesn't need much warm-up data.

**Safety cap:** `lam = min(100000, lam)` prevents numerical issues when the denominator `||x - x_mean||^2` is very small.

---

## 4. All Strategies Tested and Their Results

### 4.1 Algorithms from the `universal` library benchmarking

Results from `case2_study.ipynb` (using the `universal` Python package for online portfolio selection):

| Algorithm | Sharpe Ratio | Ann. Return | Ann. Volatility | Max Drawdown | Turnover |
|-----------|-------------|-------------|-----------------|--------------|----------|
| **BCRP** (Best Constant Rebalanced Portfolio) | **0.86** | 13.06% | 15.17% | -29.34% | 2.9 |
| **BestMarkowitz** | **0.89** | 12.92% | 14.43% | -30.42% | 3.0 |
| CRP (Constant Rebalanced Portfolio) | 0.63 | 7.24% | 11.43% | -19.62% | 3.3 |
| EG (Exponential Gradient) | 0.63 | 7.20% | 11.44% | -19.40% | 3.2 |
| UP (Universal Portfolio) | 0.62 | 7.08% | 11.48% | -19.08% | 2.9 |
| **RMR** (Robust Median Reversion) | 0.60 | **17.84%** | 29.59% | -35.71% | 282.4 |
| Anticor | 0.54 | 15.35% | 28.46% | -56.37% | 67.0 |
| OLMAR (Online Lazy Moving Average Reversion) | 0.52 | 15.39% | 29.35% | -50.62% | 267.9 |
| WMAMR (Weighted Moving Average Mean Reversion) | 0.49 | 14.10% | 28.73% | -44.20% | 197.6 |
| ONS (Online Newton Step) | 0.49 | 8.03% | 16.33% | -43.48% | 9.8 |
| BAH (Buy and Hold) | 0.46 | 5.88% | 12.80% | -23.62% | 0.0 |
| CWMR (Confidence Weighted Mean Reversion) | 0.19 | 5.49% | 28.21% | -54.29% | 403.2 |
| PAMR (default params from universal lib) | 0.15 | 4.13% | 28.17% | -56.04% | 402.9 |
| Kelly | 0.01 | 1.80% | 130.47% | -100.00% | 294.6 |
| HRP (Hierarchical Risk Parity) | 0.34 | 5.7% | 11.1% | -- | -- |
| EfficientFrontier max_sharpe | 0.52 | 9.5% | 14.3% | -- | -- |
| Risk Parity (nonconvex) | 0.12 | 3.3% | 11.3% | -- | -- |

**Critical observation:** The PAMR from the `universal` library with default parameters scored only 0.15 Sharpe. The team's custom PAMR with tuned parameters (eps=0.5, C=500, max_weight=0.25) scored MUCH higher -- indicating parameter tuning is essential.

### 4.2 Custom Algorithm Results (from `mc_chungus.txt` and `results.txt`)

#### PAMR Results Across Different Configurations

Using the team's custom validation (rolling window approach):

| Train/Test Ratio | Window Size | Average Sharpe |
|-----------------|-------------|----------------|
| 0.70 | 252 | **2.64** |
| 0.75 | 252 | **2.51** |
| 0.80 | 252 | **2.44** |
| 0.80 | 2520 | **2.20** |
| 0.85 | 2520 | **2.09** |
| 0.75 | 2520 | 1.43 |
| 0.70 | 2520 | 0.85 |
| 0.70 | 1260 | -2.11 |
| 0.75 | 1260 | -2.44 |
| 0.80 | 1260 | -1.95 |

**Peak PAMR Sharpe: ~2.64 (252-day windows, 70% train)**

#### PAMR FINAL Results (from `final_metric.txt`)

With expanded window testing after parameter tuning:

| Train Ratio | Window 1260 | Window 1890 | Window 2520 |
|-------------|------------|------------|------------|
| 0.75 | Avg ~0.51 | Avg ~0.59 | **1.43** |
| 0.80 | Avg ~0.63 | Avg ~0.59 | **2.20** |
| 0.85 | Avg ~0.65 | Avg ~0.56 | **2.09** |

Individual windows showed Sharpe ratios up to **2.27** (one window) and **1.97** (another), but also negative windows (-0.84, -0.92), showing significant regime sensitivity.

#### Markowitz Results for Comparison

| Configuration | Average Sharpe |
|--------------|----------------|
| MARKOWITZ_ONESHOT, 0.80, w252 | **5.14** |
| MARKOWITZ_ONESHOT, 0.75, w252 | **4.49** |
| MARKOWITZ_ONESHOT, 0.70, w252 | 3.89 |
| MARKOWITZ, 0.80, w252 | 2.08 |
| MARKOWITZ, 0.70, w252 | 1.99 |
| MARKOWITZ_ONESHOT, 0.80, w2520 | 1.86 |
| MARKOWITZ, 0.75, w252 | 1.24 |
| MARKOWITZ, 0.80, w1260 | 0.99 |

**Caution about MARKOWITZ_ONESHOT:** These suspiciously high Sharpe values (5.14) likely involve lookahead bias -- "ONESHOT" suggests optimizing over the entire period at once, not online. Not valid for out-of-sample evaluation.

#### HMPPSO Results

| Configuration | Average Sharpe |
|--------------|----------------|
| 0.80, w252 | 4.06 |
| 0.75, w252 | 3.94 |
| 0.70, w252 | 3.11 |
| 0.80, w2520 | 0.96 |
| 0.70, w1260 | -1.62 |

HMPPSO performed well on short windows but poorly on longer ones, suggesting overfitting.

### 4.3 Sharpe Optimization (Scipy) Results

From `optimize_sharpe.py` results, various optimizers maximizing Sharpe on rolling windows:

| Method | Mean Sharpe (rolling) |
|--------|----------------------|
| SLSQP | 1.36 |
| TNC | 1.32 |
| L-BFGS-B | 1.32 |
| Nelder-Mead | 1.31 |
| Powell | 1.30 |
| CG | 0.99 |
| BFGS | 0.98 |

### 4.4 Why They Chose PAMR Over Everything Else

Despite Markowitz-ONESHOT showing higher raw numbers, the team chose PAMR for their final submission because:

1. **Online/adaptive**: PAMR updates every period without needing to re-solve an optimization. Markowitz requires matrix inversion each step.
2. **Robustness**: PAMR's 252-window Sharpe of ~2.5 was consistent across train/test splits. Markowitz was more variable.
3. **No lookahead**: PAMR is a legitimate online algorithm. MARKOWITZ_ONESHOT's 5.14 Sharpe is unrealistic for live trading.
4. **Simplicity**: The algorithm is ~20 lines of core logic. Fewer things to go wrong.
5. **Mean reversion fit**: Their EDA showed the data had mean-reverting characteristics, making PAMR a natural fit.

---

## 5. Validation Approach

### 5.1 EDA Methods Used

From `Case2_EDA.ipynb`, the team performed:

1. **Augmented Dickey-Fuller tests** -- tested stationarity of each asset
2. **Hurst exponents** -- measured mean reversion vs. trend persistence
   - Values < 0.5 indicate mean reversion (favorable for PAMR)
   - Values > 0.5 indicate trending behavior
3. **Cointegration tests** -- tested pairwise equilibrium relationships (10,000 bootstrap iterations)
4. **Granger Causality tests** -- tested if one asset's returns predict another's
5. **PCA** -- decomposed variance structure across assets
6. **Predictive modeling** -- tested Logistic Regression, LDA, QDA, SVM, Decision Trees, Random Forests for return direction prediction

### 5.2 Backtesting Framework

The team used a rolling window approach:
- Split data with `train_test_split` (test_size ranging from 0.2 to 0.9)
- For each window, compute Sharpe ratio
- Track mean, variance, and std of Sharpe across windows
- Tested window sizes: 252 (1 year), 1260 (5 years), 2520 (10 years)
- Tested train/test ratios: 0.70, 0.75, 0.80, 0.85

### 5.3 Metric Computation

Their Sharpe ratio computation:
```python
returns = (capital[1:] - capital[:-1]) / capital[:-1]
sharpe = np.mean(returns) / np.std(returns)
```
This is the **daily Sharpe ratio** (not annualized). To annualize, multiply by sqrt(252). Their reported Sharpe of ~2.5 daily translates to roughly 2.5 * sqrt(252) = ~39.7 annualized, which seems extremely high and suggests their computation may be using a different convention or the competition uses a non-standard Sharpe.

**Important note for our competition:** The `validate.py` in our participant directory uses:
```python
def annualized_sharpe(daily_returns):
    mu, sd = float(np.mean(x)), float(np.std(x, ddof=1))
    return math.sqrt(252) * mu / sd
```
This is the proper annualized Sharpe with ddof=1. The 2024 repos used ddof=0 (biased estimate) without annualization.

---

## 6. Adapting PAMR for Our Competition (2025)

### 6.1 Key Differences from 2024

| Aspect | 2024 Competition | Our Competition (2025) |
|--------|-----------------|----------------------|
| Assets | 6 | **25** |
| Data | Daily prices | **Tick-level** (30 ticks/day) |
| Rebalancing | Daily | **Daily** (weights held for full day) |
| Short selling | Not mentioned | **Allowed** (gross exposure <= 1) |
| Transaction costs | None | **Spread + quadratic impact** |
| Borrowing costs | None | **Per-asset borrow rate** |
| Weight constraints | 0 <= w <= 1 | **L1 gross exposure <= 1** (shorts allowed) |
| Train period | Varied | **4 years** (30,240 ticks) |
| Test period | Varied | **1 year** (7,560 ticks) |

### 6.2 Modifications Needed

1. **25 assets instead of 6**: The `max_weight` parameter needs adjustment. With 25 assets, max_weight of 0.25 may be too restrictive or too loose. Consider 0.10-0.15 for diversification.

2. **Transaction costs**: The original PAMR ignores trading costs. High turnover (the `universal` library PAMR had turnover of 402.9) will be devastating with the competition's spread + quadratic impact costs. We must either:
   - Reduce turnover by increasing `eps` (less frequent rebalancing)
   - Add a "don't trade if cost exceeds expected benefit" filter
   - Blend PAMR weights with previous weights: `w_new = alpha * pamr_weights + (1-alpha) * old_weights`

3. **Short selling**: Standard PAMR projects onto the simplex (non-negative weights). For short selling, we need to modify the projection to allow negative weights while respecting the L1 gross constraint.

4. **Tick-level data**: We get 30 ticks per day but only rebalance daily. We should use all tick data to compute more accurate return estimates, but only output daily weight vectors.

5. **Borrowing costs**: Assets have annual borrow costs of 23-197 bps. Shorting expensive-to-borrow assets (A03: 197 bps, A08: 195 bps) erodes returns. Consider cost-adjusted PAMR.

### 6.3 Recommended Parameter Tuning

Based on the 2024 team's extensive testing:

| Parameter | 2024 Final | Suggested Starting Range for 2025 |
|-----------|-----------|----------------------------------|
| `eps` | 0.5 | 0.3 - 1.0 (higher if we want lower turnover) |
| `C` | 500 | 100 - 1000 |
| `variant` | 0 | Test all three; variant 2 may be more stable with 25 assets |
| `max_weight` | 0.25 | 0.08 - 0.20 (lower for 25 assets) |

### 6.4 PAMR Implementation Template for Our Competition

```python
class MyStrategy(StrategyBase):
    def __init__(self):
        self.eps = 0.5
        self.C = 500
        self.variant = 0
        self.max_weight = 0.15
        self.last_b = None
        self.turnover_penalty = 0.5  # Blend factor to reduce turnover

    def fit(self, train_prices, meta, **kwargs):
        n_assets = train_prices.shape[1]
        self.last_b = np.ones(n_assets) / n_assets
        self.spread = meta.spread_bps / 1e4
        self.borrow = meta.borrow_bps_annual / 1e4
        # Could analyze train_prices here to estimate eps, etc.

    def get_weights(self, price_history, meta, day):
        if day == 0:
            return self.last_b.copy()

        # Get latest day's close prices (last tick)
        latest_prices = price_history[-1]

        # Normalize prices (cross-sectional)
        x = latest_prices / np.mean(latest_prices)

        # PAMR update
        x_mean = np.mean(x)
        le = max(0.0, np.dot(self.last_b, x) - self.eps)

        denom = np.linalg.norm(x - x_mean) ** 2
        if denom < 1e-10:
            lam = 0.0
        elif self.variant == 0:
            lam = le / denom
        elif self.variant == 1:
            lam = min(self.C, le / denom)
        elif self.variant == 2:
            lam = le / (denom + 0.5 / self.C)

        lam = min(100000, lam)
        new_b = self.last_b - lam * (x - x_mean)

        # Project to simplex (long-only version)
        new_b = self._simplex_proj(new_b)

        # Cap individual weights
        new_b = np.minimum(new_b, self.max_weight)
        new_b /= np.sum(new_b)

        # Reduce turnover by blending
        blended = self.turnover_penalty * new_b + (1 - self.turnover_penalty) * self.last_b
        blended /= np.sum(blended)

        self.last_b = blended
        return blended

    def _simplex_proj(self, b):
        m = len(b)
        s = np.sort(b)[::-1]
        tmpsum = 0.0
        tmax = 0.0
        bget = False
        for ii in range(m - 1):
            tmpsum += s[ii]
            tmax_candidate = (tmpsum - 1) / (ii + 1)
            if tmax_candidate >= s[ii + 1]:
                tmax = tmax_candidate
                bget = True
                break
        if not bget:
            tmax = (tmpsum + s[m - 1] - 1) / m
        return np.maximum(b - tmax, 0.0)
```

---

## 7. Additional Strategy Ideas from the Repos

Beyond PAMR, the repos tested these approaches which could be combined:

1. **OLMAR** (Online Lazy Moving Average Reversion): Similar mean-reversion but uses a moving average to predict next-period prices. Sharpe 0.52 in their tests.

2. **RMR** (Robust Median Reversion): Uses L1-median instead of mean for robustness. Best return (17.84% annualized) among tested algorithms.

3. **BestMarkowitz**: Classic mean-variance optimization. High Sharpe (0.89) but requires covariance estimation which is noisy with many assets.

4. **WMAMR**: Weighted moving average extension of PAMR. Sharpe 0.49 but better than vanilla PAMR from the library.

5. **Ensemble/Meta approach**: The team explored meta-analysis combining multiple strategy signals (`meta_analysis.py` tests across methods, windows, train ratios).

---

## 8. Critical Takeaways

### What Worked (2024 competition)
- **PAMR with custom tuning** outperformed all other online algorithms
- **Mean reversion assumption** was validated by the data
- **Simple, efficient algorithms** beat complex optimization
- **Small training data** (10% train, 90% test) worked fine for PAMR
- **max_weight cap** at 0.25 prevented over-concentration

### What to Watch Out For (2025)
- **Transaction costs**: The 2024 repos had ZERO transaction costs. Our competition has significant costs. This changes everything -- high-turnover strategies like vanilla PAMR will get destroyed.
- **25 assets**: More assets = more diversification opportunity but also more noise in the PAMR update step.
- **Tick-level data**: We can extract much richer signals from intraday data than the 2024 teams could from daily data.
- **Short selling**: PAMR naturally produces long-only portfolios. Allowing shorts via modified projection could improve returns, but borrowing costs are non-trivial.
- **Regime changes**: The 2024 results showed PAMR had negative Sharpe in some windows (e.g., -2.44 at 1260-day windows). We need regime detection or adaptive parameters.

### Recommended Next Steps
1. Implement basic PAMR with our competition's API format
2. Add transaction-cost-aware weight blending
3. Run `validate.py` to get baseline Sharpe
4. Grid search over (eps, C, variant, max_weight, turnover_penalty)
5. Consider hybrid: PAMR for direction + Markowitz for sizing
6. Test whether tick-level mean reversion signals are stronger than daily ones
