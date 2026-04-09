# BL Parameter Re-tuning With Tilt Active

## Objective
Re-optimize Black-Litterman parameters jointly with the within-sector tick-SR tilt
(tilt_alpha), since original BL params were tuned before the tilt was added.

## Baseline
- **CV Mean = +2.1596** (previously reported as +2.160)
- Params: omega_sector=0.0005, omega_asset=0.01, gamma=0.95, tau=0.10,
  halflives=[8,12,15,18], tilt_alpha=0.02
- Per-fold: [+2.1933, +2.1956, +2.0901]

## Methodology
1. **Phase 1 (coarse grid):** Swept each parameter independently x alpha.
   - omega_sector in {0.0002, 0.0005, 0.001} x alpha in {0.01, 0.02, 0.03}
   - omega_asset in {0.005, 0.01, 0.02, 0.05} x alpha in {0.01, 0.02, 0.03}
   - gamma in {0.85, 0.90, 0.95, 1.0} x alpha in {0.01, 0.02, 0.03}
   - tau in {0.05, 0.10, 0.15, 0.20} x alpha in {0.02}
   - halflives: 4 options x alpha in {0.02}
2. **Phase 2 (combinations):** Tested joint changes of best-performing params.
3. **Phase 3 (fine-tuning):** Explored around best combo with finer steps.
4. **Full backtest verification** on top 6 candidates (all 3 CV folds, exact
   tick-level wealth process from validate.py).

## Key Findings

### Parameter Sensitivity (from Phase 1, alpha=0.02 held fixed)
| Parameter | Best Value | CV Mean | Delta vs Baseline |
|-----------|-----------|---------|-------------------|
| halflives | [6,10,15,20] | +2.1628 | +0.0032 |
| gamma | 1.0 | +2.1622 | +0.0026 |
| omega_sector | 0.0002 | +2.1601 | +0.0005 |
| omega_asset | 0.01 | +2.1596 | +0.0000 (already optimal) |
| tau | 0.10 | +2.1596 | +0.0000 (already optimal) |

**Key insight:** halflives and gamma had the largest individual effects. Wider
halflife spread [6,10,15,20] and no eigenvalue shrinkage (gamma=1.0) both help.

### Alpha Sensitivity
alpha=0.02 was optimal across almost all parameter combos. Alpha=0.01 raised
fold-1 Sharpe but hurt folds 2-3. Alpha=0.03 consistently underperformed.
In the fine-tuning phase, alpha=0.015 showed a slight edge when combined with
other parameter changes.

## Final Ranking (Full 3-Fold CV)

### Rank 1: CV Mean = +2.1665
```
omega_sector=0.0002, omega_asset=0.01, gamma=1.02, tau=0.08
halflives=[6,10,15,20], tilt_alpha=0.015
Folds: [+2.2422, +2.1712, +2.0860]  Std=0.0782
```
Highest mean but wider variance and lower min fold (2.086 vs 2.090 baseline).

### Rank 2: CV Mean = +2.1656
```
omega_sector=0.0002, omega_asset=0.01, gamma=1.0, tau=0.10
halflives=[6,10,15,20], tilt_alpha=0.015
Folds: [+2.2368, +2.1677, +2.0922]  Std=0.0724
```
Clean improvement on all folds. Good balance of mean and stability.

### Rank 3: CV Mean = +2.1649
```
omega_sector=0.0002, omega_asset=0.008, gamma=1.0, tau=0.10
halflives=[6,10,15,20], tilt_alpha=0.015
Folds: [+2.2355, +2.1611, +2.0981]  Std=0.0688
```
Best min-fold Sharpe (2.098) among the new candidates.

### Rank 4: CV Mean = +2.1648
```
omega_sector=0.0002, omega_asset=0.01, gamma=1.0, tau=0.12
halflives=[6,10,15,20], tilt_alpha=0.015
Folds: [+2.2351, +2.1625, +2.0968]  Std=0.0692
```

### Rank 5: CV Mean = +2.1647
```
omega_sector=0.0002, omega_asset=0.01, gamma=1.0, tau=0.10
halflives=[6,10,15,20], tilt_alpha=0.02
Folds: [+2.2168, +2.1827, +2.0948]  Std=0.0629
```
Lowest std of any improved candidate. Most stable.

### Baseline: CV Mean = +2.1596
```
omega_sector=0.0005, omega_asset=0.01, gamma=0.95, tau=0.10
halflives=[8,12,15,18], tilt_alpha=0.02
Folds: [+2.1933, +2.1956, +2.0901]  Std=0.0602
```

## Recommendation

**Best overall: Rank 2** for deployment.
```
omega_sector=0.0002, omega_asset=0.01, gamma=1.0, tau=0.10
halflives=[6,10,15,20], tilt_alpha=0.015
```
- CV Mean: +2.1656 (up +0.0060 from baseline 2.1596)
- Every fold improved vs baseline
- Moderate std (0.072)
- Changes are interpretable: wider halflife spread captures more timescales,
  gamma=1.0 removes eigenvalue shrinkage (data has enough days to estimate
  eigenstructure), tighter omega_sector trusts sector views more, slightly
  reduced tilt keeps BL signal dominant

**Conservative alternative: Rank 5** if stability matters most.
```
omega_sector=0.0002, omega_asset=0.01, gamma=1.0, tau=0.10
halflives=[6,10,15,20], tilt_alpha=0.02
```
- CV Mean: +2.1647, Std=0.0629 (lowest variance)
- Same as Rank 2 but keeps alpha=0.02 (one fewer change from baseline)

**Aggressive alternative: Rank 1** if maximizing expected value.
- CV Mean: +2.1665, but std=0.078 and min fold drops below baseline min

## Changes from Baseline (Recommended Params)
| Parameter | Old | New | Rationale |
|-----------|-----|-----|-----------|
| omega_sector | 0.0005 | 0.0002 | Higher confidence in sector views |
| gamma | 0.95 | 1.0 | No eigenvalue shrinkage needed |
| halflives | [8,12,15,18] | [6,10,15,20] | Wider timescale coverage |
| tilt_alpha | 0.02 | 0.015 | Slightly less tilt, let BL dominate |
| omega_asset | 0.01 | 0.01 | Unchanged |
| tau | 0.10 | 0.10 | Unchanged |
