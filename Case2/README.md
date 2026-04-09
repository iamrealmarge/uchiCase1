# Case 2: Portfolio Optimization — Competition Ready

**CV Mean: +2.168, Min: +2.105, Std: 0.057**
**Session improvement: +2.101 → +2.168 (+6.7 bps)**

## Quick Start

```bash
cd Case2/participant
python3 validate.py --cv    # Verify: should show Mean ~+2.168
python3 validate.py         # Single split: should show ~+2.2
```

## What's in the submission

`submission.py` implements a Black-Litterman portfolio with 6 innovations:

1. **4 BL views**: S3>universe, S4>universe, A23<S3, A09>S3
2. **Heterogeneous omega**: sector views tight (0.0002), asset views wider (0.01)
3. **EWMA ensemble** over halflives {6,10,15,20} — averages weights for cov diversification
4. **Within-sector tick-level Sharpe tilt** — redistributes BL weights within S0/S1/S2 sectors using tick-level precision (alpha=0.02). This is the paradigm shift: adds per-asset info where BL has NO views.
5. **Vol scaling** [0.5, 1.5] with cost-aware rebalancing gate
6. **L1 penalty** (0.0003) + gross exposure <= 1

## Key Files

| File | What it is |
|------|-----------|
| `participant/submission.py` | **THE SUBMISSION** — submit this |
| `participant/validate.py` | Competition evaluator (don't modify) |
| `participant/HANDOFF.md` | Current state — read this first if continuing work |
| `participant/GOLDEN_PRINCIPLES.md` | 47 hard-won rules — violating these wastes time |
| `AUDIT_TRAIL.md` | Full history of 46 cycles, 120+ strategies tested |
| `research/17_academic_frontier.md` | Academic research findings + what worked/didn't |
| `participant/exp_*/results.md` | Agent experiment results |

## What was tested and failed (don't re-test)

- **PyTorch direct weight learning** — overfits catastrophically (IS Sharpe 4.0, OOS 0.5)
- **More BL views** (cross-sector, S4 within-sector, S2 underperform) — increases fold variance
- **Academic shrinkage** (Jorion, Kan-Zhou, Tu-Zhou, Michaud) — BL already regularizes optimally
- **Alternative optimizers** (MV utility, analytic tangency, risk-parity) — all find same direction
- **Covariance innovations** (tick-level EWMA, PCA, LW2020 nonlinear) — power EWMA ensemble is best
- **m-Sparse portfolio** — all 25 assets needed for factor hedging

## What could still improve (if you have time)

1. **Per-sector tilt alpha**: S0/S1/S2 separate from S3/S4 (tested, marginal)
2. **EWMA-weighted tick SR** for the tilt (tested, no improvement)
3. **The "dark matter" insight**: BL views only constrain 4 of 25 directions. The tilt fills the other 21. Any way to add MORE information to those 21 directions without increasing fold variance is the key.

## Competition Details

- **Scoring**: AVERAGED Sharpe across MULTIPLE OOS runs (consistency matters)
- **Same DGP as training** confirmed by organizers
- **Libraries**: numpy, pandas, scikit-learn, scipy, PyTorch (all allowed)
- **Deadline**: April 9, 2026, 11:59 PM CST
