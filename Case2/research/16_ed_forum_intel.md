# Ed Forum Intelligence — Case 2

## Critical Answers from Organizers

### Q1: Gross exposure < 1 is allowed
**Weights are NOT rescaled up.** If you output weights summing to |w| = 0.6, they stay at 0.6. Only rescaled DOWN if gross > 1.
→ **IMPLICATION:** Vol-scaling (reducing exposure in high-vol periods) is a legitimate lever. S12 is validated.

### Q2: Same underlying process for holdout
**The OOS test period is generated from the SAME process** as training data — same sector structure, same asset dynamics.
→ **IMPLICATION:** Sector 3&4 tilt is VALIDATED. Historical Sharpe ratios are meaningful for the holdout. This is the single most important answer.

### Q3: Full 5 years passed to fit()
→ We can use all training data for parameter estimation.

### Q4: AVERAGED across MULTIPLE runs
**Final ranking is based on average across multiple OOS realizations, NOT a single one.**
→ **IMPLICATION:** This is HUGE. Strategies with CONSISTENT performance win. Low variance matters more than a single high-Sharpe run. Favors diversified, stable strategies over concentrated bets. Sharpe ratio IS the right metric to optimize (it penalizes variance).

### Q5: day parameter starts at 0, increments by 1
→ Confirmed. day=0 is first holdout day.

### Q6: No hard time limit
But keep it reasonable. Reserve right to disqualify.
→ Can use moderate computation, no heavy ML per call.

### Q7: validate.py is the test
→ No separate test server for Case 2.

### Q8: Non-finite values = disqualification
→ Must be bulletproof. Add safety checks.

### Q9: PyTorch and TensorFlow are ALLOWED
→ Opens deep learning approaches for return prediction.

### Auth: New credentials on competition day
→ Practice creds are separate from live.

## Strategic Impact Summary

1. **Vol-scaling is valid** (exposure < 1 kept as-is)
2. **Sector tilt is safe** (same DGP for holdout)
3. **Consistency matters most** (averaged across multiple runs)
4. **Deep learning is an option** (PyTorch/TF approved)
5. **Code must be bulletproof** (crash = disqualification)
