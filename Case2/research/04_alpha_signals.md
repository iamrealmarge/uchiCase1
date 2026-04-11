# Alpha Signal Generation for Portfolio Optimization Competitions

**Context**: 25 assets, 5 sectors (5 assets each), 5 years of intraday data (30 ticks/day),
daily rebalancing, scored on Sharpe ratio. Available: numpy, pandas, sklearn, scipy only.

**Last updated**: 2026-04-08

---

## 1. Cross-Sectional Momentum

### Core Concept
Cross-sectional momentum ranks assets by past returns and goes long top performers, short
bottom performers. The canonical reference is Jegadeesh & Titman (1993).

### Formation and Holding Periods (Empirical)

| Formation | Holding | Skip | Notes |
|-----------|---------|------|-------|
| 1 month | 1 month | 0 | Short-term; blends with reversal |
| 3 months | 1 month | 1 week | Intermediate; robust |
| 6 months | 1 month | 1 week | **Best documented**; ~12% annualized excess (JT 1993) |
| 12 months | 1 month | 1 week | Long-term; widely replicated |

**Key rule**: skip the most recent period (1 day to 1 week) to avoid short-term reversal
contaminating the momentum signal. In a daily-rebalancing setup with intraday data this means
excluding the prior day's return from the formation window.

### Implementation (numpy/pandas)

```python
import numpy as np
import pandas as pd

def cross_sectional_momentum(prices: pd.DataFrame,
                              formation_days: int = 60,
                              skip_days: int = 1) -> pd.Series:
    """
    Returns a cross-sectional z-scored momentum signal.
    prices: DataFrame (dates x assets), daily close prices.
    Returns: signal Series (assets), positive = long, negative = short.
    """
    # Cumulative return over formation window, skipping most recent `skip_days`
    end_idx = -skip_days if skip_days > 0 else len(prices)
    start_idx = end_idx - formation_days
    ret = prices.iloc[end_idx] / prices.iloc[start_idx] - 1

    # Cross-sectional z-score (rank-based is more robust)
    ranked = ret.rank()
    signal = (ranked - ranked.mean()) / ranked.std()
    return signal
```

### Sizing
- Standard: equal-weight top/bottom quintile (long top 20%, short bottom 20%)
- Rank-based weighting: assign weight proportional to rank percentile minus 0.5
- With only 25 assets, use quintiles of 5 assets each; avoid holding fewer than 3 per side to
  prevent concentration risk hurting Sharpe

**Source**: Jegadeesh & Titman (1993) via Springer review
https://link.springer.com/article/10.1007/s11408-022-00417-8

---

## 2. Time-Series Momentum (Trend Following)

### EWMA Crossovers

The signal fires when a fast EWMA crosses a slow EWMA. The key insight from Moskowitz, Ooi &
Pedersen (2012) is that each asset's own past 12-month return predicts its future return
with a positive sign — independently of cross-sectional rank.

**Practical parameter pairs** (short span, long span):
- (5, 20) — intraday / short-term swing
- (10, 60) — medium-term trend
- (20, 120) — monthly-level trend

```python
def ewma_crossover_signal(prices: pd.DataFrame,
                           fast: int = 10,
                           slow: int = 60) -> pd.DataFrame:
    """
    Returns daily signal per asset: +1 (long), -1 (short), 0 (flat).
    """
    fast_ma = prices.ewm(span=fast, adjust=False).mean()
    slow_ma = prices.ewm(span=slow, adjust=False).mean()
    raw = (fast_ma - slow_ma) / slow_ma       # normalized spread
    # Continuous signal: z-score within cross-section
    signal = raw.sub(raw.mean(axis=1), axis=0).div(raw.std(axis=1), axis=0)
    return signal
```

Since fast and slow EMAs are equivalent to a linear filter, they subsume many other trend
indicators including HP filter and Kalman smoothers.

### Breakout Signals

Donchian channel breakout: go long when price exceeds N-day high, short when it falls below
N-day low. For daily rebalancing with 30 intraday bars:

```python
def breakout_signal(prices: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Normalized breakout signal: position relative to rolling [min, max] range.
    """
    roll_max = prices.rolling(window).max()
    roll_min = prices.rolling(window).min()
    # Maps to [-1, +1]; values near +1 indicate breakout up
    signal = 2 * (prices - roll_min) / (roll_max - roll_min + 1e-8) - 1
    return signal
```

**Using intraday bars**: aggregate the 30 ticks into OHLC daily bars. Use the high/low across
intraday ticks to get tighter breakout references than just close prices.

**Source**: QuantStart MA crossover implementation
https://www.quantstart.com/articles/Backtesting-a-Moving-Average-Crossover-in-Python-with-pandas/

---

## 3. Mean Reversion Signals

### Short-Term Reversal (1–5 Days)

Stocks that fall sharply in the prior 1–5 days tend to bounce; this is the "reversal" anomaly.
It is the mirror image of momentum but operates at very short horizons.

```python
def short_term_reversal(returns: pd.DataFrame, window: int = 5) -> pd.Series:
    """
    Negative of recent cumulative return = reversal signal.
    """
    recent_ret = (1 + returns.iloc[-window:]).prod() - 1
    signal = -recent_ret  # long losers, short winners
    signal = (signal - signal.mean()) / signal.std()
    return signal
```

**Holding horizon**: 1–3 days is typical; with daily rebalancing this can be applied every day.

### Pairs Trading Within Sectors

Within each of your 5 sectors, form pairs of assets based on correlation. Trade the spread
when it deviates significantly from its mean.

**Step 1 — Find cointegrated pairs (Engle-Granger)**:
```python
from scipy import stats

def engle_granger_ols(y: np.ndarray, x: np.ndarray):
    """OLS hedge ratio and residual for pair (y, x)."""
    slope, intercept, _, _, _ = stats.linregress(x, y)
    spread = y - slope * x - intercept
    return spread, slope

# ADF test using scipy (no statsmodels needed)
def adf_stat(series: np.ndarray, max_lag: int = 1) -> float:
    """Manual ADF t-statistic via OLS (lag=1)."""
    delta = np.diff(series)
    lag_val = series[:-1]
    # Add lagged differences if max_lag > 1
    X = lag_val.reshape(-1, 1)
    slope, intercept, r, p, se = stats.linregress(X.flatten(), delta)
    return slope / se   # negative and large in magnitude = mean reverting
```

**Step 2 — Ornstein-Uhlenbeck half-life**:

The OU process: dX = θ(μ - X)dt + σ dB

Estimate via AR(1) regression on the spread:
```python
def ou_halflife(spread: np.ndarray) -> float:
    """
    Fit AR(1) to spread, return half-life in same time units.
    Half-life = -ln(2) / ln(phi) where phi is the AR(1) coefficient.
    """
    y = np.diff(spread)
    x = spread[:-1]
    slope, intercept, _, _, _ = stats.linregress(x, y)
    # slope = (phi - 1), so phi = 1 + slope
    phi = 1 + slope
    if phi <= 0 or phi >= 1:
        return np.inf   # not mean reverting
    return -np.log(2) / np.log(phi)
```

**Rule of thumb**: target pairs with half-life between 5 and 30 days for daily rebalancing.
Half-lives under 5 days incur too much turnover; over 30 days the signal is too slow.

**Step 3 — Generate signal from z-score of spread**:
```python
def pairs_signal(spread: np.ndarray, lookback: int = 30) -> float:
    mu = np.mean(spread[-lookback:])
    sigma = np.std(spread[-lookback:])
    z = (spread[-1] - mu) / (sigma + 1e-8)
    return -z   # positive signal = long asset y, short asset x
```

**Source**: Hudson & Thames OU pairs trading
https://hudsonthames.org/optimal-stopping-in-pairs-trading-ornstein-uhlenbeck-model/

Mean reversion implementation reference:
https://letianzj.github.io/mean-reversion.html

---

## 4. Volatility Signals

### Low-Volatility Anomaly

Low-volatility stocks historically deliver higher risk-adjusted returns than predicted by CAPM.
The anomaly is strongest in cross-sectional form: rank assets by trailing realized volatility
and overweight low-vol, underweight high-vol.

```python
def low_vol_signal(returns: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    Signal: negative of realized volatility (long low-vol, short high-vol).
    """
    vol = returns.iloc[-window:].std()
    signal = -vol
    signal = (signal - signal.mean()) / signal.std()
    return signal
```

**Source**: Wikipedia low-volatility anomaly
https://en.wikipedia.org/wiki/Low-volatility_anomaly

### Volatility-Managed Portfolios (Moreira & Muir 2017)

Scale each asset's position by the inverse of its recent realized variance. This mechanically
reduces exposure when volatility spikes, increasing Sharpe ratio by ~25% for the market
portfolio per the paper.

**Scaling formula**:
```
w_t = c / RV_{t-1}
```
where RV is realized variance over the prior month and c is a constant that targets a
fixed long-run variance level.

```python
def vol_scale_weights(raw_signal: pd.Series,
                      returns: pd.DataFrame,
                      vol_window: int = 21,
                      target_vol: float = 0.10) -> pd.Series:
    """
    Scale a raw signal by inverse realized volatility to target annualized vol.
    """
    ann_factor = 252
    realized_vol = returns.iloc[-vol_window:].std() * np.sqrt(ann_factor)
    # Avoid division by zero
    realized_vol = realized_vol.clip(lower=1e-4)
    scaled = raw_signal / realized_vol * target_vol
    return scaled
```

**Key finding**: volatility timing works because high-volatility periods are not offset by
proportionally higher expected returns — the Sharpe ratio of the market actually falls during
high-vol regimes.

**Source**: Moreira & Muir (2017) NBER working paper
https://www.nber.org/papers/w22208

### Volatility Clustering Exploitation

Use the autocorrelation of squared returns (or absolute returns) as a regime indicator.
When recent realized variance is above its trailing average, reduce position sizes; when
it is below, scale up. This is the simple scalar version of GARCH targeting.

```python
def vol_regime_signal(returns: pd.DataFrame,
                       short_window: int = 5,
                       long_window: int = 60) -> pd.Series:
    """
    Returns a multiplier: >1 means low-vol regime (scale up), <1 means high-vol (scale down).
    Apply this to any signal's weights before submitting.
    """
    short_vol = returns.iloc[-short_window:].std()
    long_vol = returns.iloc[-long_window:].std()
    ratio = long_vol / (short_vol + 1e-8)  # >1 = currently calm relative to history
    return ratio.clip(0.25, 4.0)   # cap range
```

---

## 5. Sector Rotation

### Cross-Sector Momentum

Rank sectors by their aggregate return over a lookback window and rotate into top-performing
sectors. Quantpedia documents this with a 12-month lookback and monthly rebalancing, achieving
~13.9% annualized with outperformance in ~70% of years vs. buy-and-hold.

With daily rebalancing you can use shorter lookbacks (1–3 months) to be more responsive.

```python
def sector_momentum_signal(prices: pd.DataFrame,
                            sector_map: dict,
                            formation_days: int = 60) -> pd.Series:
    """
    sector_map: {'sector_A': ['AAPL','MSFT',...], ...}
    Returns per-asset signal based on sector-level momentum ranking.
    """
    sector_returns = {}
    for sector, assets in sector_map.items():
        sec_prices = prices[assets]
        sec_ret = (sec_prices.iloc[-1] / sec_prices.iloc[-formation_days] - 1).mean()
        sector_returns[sector] = sec_ret

    sec_series = pd.Series(sector_returns)
    sec_rank = sec_series.rank()

    # Map sector rank back to assets
    signal = pd.Series(index=prices.columns, dtype=float)
    for sector, assets in sector_map.items():
        signal[assets] = sec_rank[sector]

    signal = (signal - signal.mean()) / signal.std()
    return signal
```

### Sector Mean Reversion

At shorter horizons (1–5 days), sectors can mean-revert. If a sector has underperformed its
long-run average recently, tilt toward it. Combine with cross-sectional reversal within sectors.

**Practical note**: with only 5 sectors and 25 assets, sector-level signals have limited
statistical power on their own. Best used as a tilt on top of asset-level signals.

**Source**: Quantpedia sector momentum rotation
https://quantpedia.com/strategies/sector-momentum-rotational-system

---

## 6. Statistical / Factor Signals

### PCA-Based Residual Signals

PCA extracts the dominant systematic factors from your 25-asset return matrix. The residuals
after projecting out the top K PCA factors are "idiosyncratic" returns that are more
amenable to mean reversion.

```python
from sklearn.decomposition import PCA

def pca_residual_signal(returns_window: np.ndarray,
                         n_components: int = 3) -> np.ndarray:
    """
    returns_window: (T, N) array of daily returns over a rolling window.
    Returns residual signal: last-day residual, z-scored cross-sectionally.
    """
    pca = PCA(n_components=n_components)
    pca.fit(returns_window[:-1])   # fit on history, not today

    # Project today's returns onto factor space
    today = returns_window[-1].reshape(1, -1)
    factors_today = pca.transform(today)
    reconstructed = pca.inverse_transform(factors_today).flatten()
    residual = returns_window[-1] - reconstructed

    # Mean reversion signal: negative of residual (buy underperformers)
    signal = -residual
    signal = (signal - signal.mean()) / (signal.std() + 1e-8)
    return signal
```

**Number of components**: for 25 assets, use 3–5 PCA components. The first 1–2 capture the
market factor; the next 2–3 capture sector/industry factors. Residuals after 5 components are
largely idiosyncratic.

**Source**: QuantConnect PCA and pairs trading
https://www.quantconnect.com/docs/v2/research-environment/applying-research/pca-and-pairs-trading

### Kalman Filter for Dynamic Hedge Ratios

A Kalman filter estimates a time-varying hedge ratio between two assets, producing a more
stationary spread than a fixed OLS ratio. The state-space form:

- State: hedge ratio β_t
- Observation: y_t = β_t * x_t + ε_t
- Transition: β_t = β_{t-1} + η_t (random walk hedge ratio)

```python
from scipy.linalg import solve

def kalman_hedge_ratio(y: np.ndarray, x: np.ndarray,
                        delta: float = 1e-4) -> np.ndarray:
    """
    Simple 1D Kalman filter for time-varying hedge ratio.
    delta: process noise (higher = faster adaptation, typically 1e-5 to 1e-3).
    Returns array of hedge ratios, same length as y.
    """
    n = len(y)
    beta = np.zeros(n)
    P = 1.0     # initial variance
    R = 1.0     # observation noise (tunable)
    Q = delta   # process noise

    beta[0] = y[0] / (x[0] + 1e-8)

    for t in range(1, n):
        # Predict
        P_pred = P + Q
        # Update
        K = P_pred * x[t] / (x[t]**2 * P_pred + R)
        beta[t] = beta[t-1] + K * (y[t] - beta[t-1] * x[t])
        P = (1 - K * x[t]) * P_pred

    return beta
```

**Practical use**: replace static OLS hedge in pairs trading with `kalman_hedge_ratio` to
get a more stationary spread. Shown to be "much more stable than rolling OLS."

**Source**: Portfolio Optimization Book - Kalman Pairs Trading
https://portfoliooptimizationbook.com/book/15.6-kalman-pairs-trading.html

Jonathan Kinlay statistical arbitrage with Kalman filter:
https://jonathankinlay.com/2018/09/statistical-arbitrage-using-kalman-filter/

### Hurst Exponent for Signal Regime Detection

Use the Hurst exponent to gate which signal type to apply:
- H < 0.45: apply mean reversion signals (strongly mean-reverting)
- 0.45 <= H <= 0.55: random walk — flat or small positions
- H > 0.55: apply trend-following signals

```python
def hurst_exponent(ts: np.ndarray) -> float:
    lags = range(2, min(50, len(ts) // 2))
    tau = [np.std(np.subtract(ts[lag:], ts[:-lag])) for lag in lags]
    poly = np.polyfit(np.log(list(lags)), np.log(tau), 1)
    return poly[0]
```

---

## 7. Combining Signals

### Signal Blending Approaches

**1. Linear combination (weighted sum)** — simplest and most robust:
```python
def blend_signals(signals: dict, weights: dict) -> pd.Series:
    """signals: {name: pd.Series}, weights: {name: float}"""
    combined = sum(weights[k] * signals[k] for k in signals)
    return combined / combined.std()   # normalize to unit vol
```

**2. Rank combination** — more robust to outliers than value combination:
```python
def rank_blend(signals: dict) -> pd.Series:
    ranked = {k: s.rank() for k, s in signals.items()}
    return pd.DataFrame(ranked).mean(axis=1)
```

**3. IC-weighted combination** — weight each signal by its recent information coefficient
(rank correlation of signal with next-day return). More adaptive but requires a training window.

```python
from scipy.stats import spearmanr

def ic_weighted_blend(signals: dict,
                      future_returns: pd.Series,
                      window: int = 60) -> pd.Series:
    """
    Weight each signal by its rolling IC (Spearman rank correlation with realized returns).
    """
    ics = {}
    for name, sig in signals.items():
        ic, _ = spearmanr(sig, future_returns)
        ics[name] = max(ic, 0)   # discard negative-IC signals

    total = sum(ics.values()) + 1e-8
    weights = {k: v / total for k, v in ics.items()}
    return blend_signals(signals, weights)
```

**4. Orthogonalization** — remove correlation between signals before blending to avoid
double-counting the same information:
```python
def orthogonalize(signal_new: np.ndarray, signal_existing: np.ndarray) -> np.ndarray:
    """Project signal_new onto residual orthogonal to signal_existing."""
    slope, intercept, _, _, _ = scipy.stats.linregress(signal_existing, signal_new)
    return signal_new - (slope * signal_existing + intercept)
```

**Source**: Goldman Sachs on combining investment signals in long/short strategies
https://www.gsam.com/content/dam/gsam/pdfs/institutions/en/articles/2018/Combining_Investment_Signals_in_LongShort_Strategies.pdf

5 alpha signal blending methods (Medium):
https://medium.com/@tzjy/5-different-ways-of-alpha-signal-blending-with-python-code-and-research-papers-d7f3f6f6009c

### Avoiding Overfitting with Multiple Signals

**The core problem**: with 25 assets and many signals, in-sample fitting is trivial but
out-of-sample decay is severe. Research finds backtest Sharpe has R² < 0.025 for predicting
OOS performance when strategies have been extensively fit.

**Practical rules**:

1. **Limit free parameters**: prefer signals with at most 1–2 tunable parameters per asset
2. **Use economic priors**: choose parameters that have theoretical justification (e.g.,
   6-month momentum from Jegadeesh & Titman) rather than grid-searching
3. **Correlation budget**: treat highly correlated signals as one signal; use orthogonalization
4. **Deflated Sharpe Ratio**: adjust your in-sample Sharpe for the number of strategies tested:
   ```
   SR_deflated = SR * (1 - gamma * log(N_trials) / sqrt(T))
   ```
   where gamma ≈ 0.577 (Euler-Mascheroni), N_trials = number of parameter combinations tested,
   T = number of time periods
5. **Out-of-sample reserve**: hold out the final 20% of data completely untouched until
   final submission

### Walk-Forward Optimization

Split the 5-year history into expanding or rolling windows:
- Training window: 3 years (756 trading days)
- Validation window: 6 months (126 days), walk forward by 1 month (21 days)
- Re-estimate signal weights quarterly, not daily (too much risk of fitting)

```python
def walk_forward_weights(signals_history: pd.DataFrame,
                          returns_history: pd.Series,
                          train_days: int = 756,
                          val_days: int = 63,
                          step_days: int = 21) -> pd.DataFrame:
    """
    Roll through time, estimating signal weights on train, validating on val.
    Returns a DataFrame of weights indexed by date.
    """
    results = []
    n = len(returns_history)
    for start in range(0, n - train_days - val_days, step_days):
        train_sig = signals_history.iloc[start:start+train_days]
        train_ret = returns_history.iloc[start:start+train_days]
        # Estimate IC for each signal
        ics = train_sig.apply(lambda s: spearmanr(s, train_ret)[0])
        ics = ics.clip(lower=0)
        weights = ics / (ics.sum() + 1e-8)
        results.append({'date': returns_history.index[start+train_days], 'weights': weights})
    return pd.DataFrame(results).set_index('date')
```

---

## 8. Competition-Specific Insights

### What Tends to Win Sharpe-Maximization Competitions

Based on WorldQuant IQC writeups and practitioner experience:

1. **Price reversion dominates**: "Price reversion strategies worked especially well — all
   winning alphas incorporated some form of price reversion." Short-term reversal at 1–5 day
   horizons is the most reliable signal in competition contexts where there are no transaction
   costs or where costs are capped.

2. **Neutralization is critical**: Market-neutral portfolios have lower variance denominators.
   Sector-neutral is even better — neutralize within each of your 5 sectors so that sector
   bets cancel. This directly reduces variance without touching expected return.
   ```python
   def sector_neutralize(signal: pd.Series, sector_map: dict) -> pd.Series:
       neutralized = signal.copy()
       for sector, assets in sector_map.items():
           sec_signal = signal[assets]
           neutralized[assets] = sec_signal - sec_signal.mean()
       return neutralized
   ```

3. **Uncorrelated signal combination**: combining 3–5 signals with low pairwise correlation
   produces a smoother Sharpe profile than optimizing one signal. Target correlation < 0.3
   between signal pairs.

4. **Low turnover for Sharpe**: high-turnover strategies suffer from bid-ask spread and
   market impact even in competitions with synthetic costs. EWMA-based signals naturally
   reduce daily position changes vs. rank-flip signals.

5. **Vol targeting beats fixed weights**: applying volatility scaling (Section 4) consistently
   improves Sharpe across signal types. Apply it as the final layer before submitting weights.

### Common Mistakes to Avoid

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| Look-ahead bias in normalization | Inflated backtest Sharpe | Use only past data in rolling z-scores |
| Fitting signal parameters per asset | Overfitting 25 parameters at once | Use the same parameters cross-sectionally |
| Using raw price levels in mean reversion | Non-stationary spread | Always use log-price differences or spreads |
| Ignoring the skip period in momentum | Short-term reversal corrupts signal | Skip the most recent 1 day |
| Equal weighting all signals | Dominated by most volatile | IC-weight or vol-adjust each signal |
| Not normalizing position sizes | Large positions in low-liquidity assets | Scale by signal / (N * asset_vol) |
| Testing parameters in-sample then reporting | Backtest overfitting | Walk-forward OOS validation mandatory |

### Specific Tips for This Competition Setup

**Given**: 25 assets, 5 sectors (5 each), 30 intraday ticks/day, daily rebalancing, Sharpe
scoring.

1. **Aggregate intraday data thoughtfully**: compute intraday realized variance (sum of
   squared 30-min returns) as a better vol estimate than end-of-day range. Use the
   first-bar and last-bar returns as intraday momentum sub-signals.

2. **Sector structure is a gift**: with 5 clean sectors you can build sector-neutral signals
   for free. Within-sector pairs trading is more likely to be cointegrated than random pairs.

3. **25 assets means high idiosyncratic noise**: use the 3-5 PCA factor structure to separate
   systematic from idiosyncratic components. Signal on the residuals for mean reversion.

4. **Daily rebalancing with Sharpe scoring**: the scoring period is likely 1–2 years OOS.
   Strategies that are consistent beat those that are high-return but high-variance. Target a
   realized daily Sharpe of ~0.08–0.12 (annualized ~1.2–1.9) with low drawdown.

5. **Stack these signals in order of robustness**:
   - Tier 1 (most robust): cross-sectional momentum (6M), short-term reversal (1–5D),
     low-vol tilt
   - Tier 2 (robust): sector-neutral EWMA crossover, PCA residual reversion
   - Tier 3 (opportunistic): pairs trading within sector (OU-based), intraday first-bar
     momentum

6. **Final weight construction**:
   ```python
   # Recommended pipeline
   # 1. Generate each signal cross-sectionally z-scored
   # 2. Sector-neutralize each signal
   # 3. Vol-scale each signal by inverse realized vol
   # 4. IC-blend the signals
   # 5. Apply portfolio-level vol targeting
   # 6. Normalize to sum-to-zero (long-short) or sum-to-one (long-only)
   ```

### Walk-Forward Validation Checklist

- [ ] Signals computed using only data available at time t (no look-ahead)
- [ ] Parameters chosen a priori from academic literature, not grid-searched
- [ ] At least 252 trading days of OOS period tested
- [ ] Sharpe computed on OOS period, not full backtest
- [ ] Deflated Sharpe reported if >5 parameter variants were tested
- [ ] Turnover measured (daily weight change); flag if >20% of portfolio turns over per day
- [ ] Performance stable across at least 3 sub-periods of the OOS window

---

## References

- Jegadeesh & Titman (1993), "Returns to Buying Winners and Selling Losers" — canonical
  cross-sectional momentum:
  https://link.springer.com/article/10.1007/s11408-022-00417-8

- Moreira & Muir (2017), "Volatility-Managed Portfolios":
  https://www.nber.org/papers/w22208

- Quantpedia Sector Momentum Rotation system:
  https://quantpedia.com/strategies/sector-momentum-rotational-system

- Hudson & Thames, OU optimal stopping in pairs trading:
  https://hudsonthames.org/optimal-stopping-in-pairs-trading-ornstein-uhlenbeck-model/

- Portfolio Optimization Book, Kalman Filter for Pairs Trading:
  https://portfoliooptimizationbook.com/book/15.6-kalman-pairs-trading.html

- Jonathan Kinlay, Statistical Arbitrage with Kalman Filter:
  https://jonathankinlay.com/2018/09/statistical-arbitrage-using-kalman-filter/

- QuantConnect, PCA and Pairs Trading:
  https://www.quantconnect.com/docs/v2/research-environment/applying-research/pca-and-pairs-trading

- Goldman Sachs, Combining Investment Signals in Long/Short Strategies (2018):
  https://www.gsam.com/content/dam/gsam/pdfs/institutions/en/articles/2018/Combining_Investment_Signals_in_LongShort_Strategies.pdf

- WorldQuant IQC competition writeup (Glazar):
  https://jglazar.github.io/projects/wq_project/

- Intraday momentum — Zarattini, Aziz, Barbon (SSRN):
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172

- Mean reversion implementation (Letian Zhang):
  https://letianzj.github.io/mean-reversion.html

- Low-volatility anomaly (Wikipedia):
  https://en.wikipedia.org/wiki/Low-volatility_anomaly

- Volatility clustering and GARCH (Jonathan Kinlay, 2026):
  https://jonathankinlay.com/2026/02/garch-volatility-clustering-asset-classes/
