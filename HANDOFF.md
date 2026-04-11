# Case 1 Bot — HANDOFF
**Current state for next iteration. Updated: 2026-04-11 00:10**

---

## CURRENT BOT: bot.py

### Architecture
- Subclasses `utcxchangelib.XChangeClient` (async gRPC)
- Callback-driven: `bot_handle_book_update`, `bot_handle_news`, `bot_handle_order_fill`, etc.
- MetricsTracker class logs per-round stats to `metrics.jsonl`
- Auto-calibrates PE from first earnings + market mid
- Falls back to market mid when no model fair value available

### What's Implemented (Working)
- [x] Exchange connectivity (port 3333, correct symbols)
- [x] Stock A market making (mid fallback + PE calibration)
- [x] Stock C market making (mid fallback + PE calibration)
- [x] ETF market making
- [x] Fair value: A (EPS*PE), C (yield+bond model), B (implied from options), ETF (NAV)
- [x] Put-call parity arb on B options (3 strikes)
- [x] Box spread arb (3 strike pairs)
- [x] CPI structured news → Fed probability Bayesian update
- [x] Earnings news → EPS update → fair value recalc
- [x] Unstructured news → keyword sentiment → Fed probability shift
- [x] Petition news → Fed probability mapping
- [x] Fed probability initialization from market prices
- [x] Cancel-before-requote cycle
- [x] Startup cancel (cancel all stale inherited orders on first book update)
- [x] Logarithmic inventory fade
- [x] Risk limit tracking with buffers
- [x] Emergency position unwind when past soft limits
- [x] 3-level multi-level quoting
- [x] Metrics tracking (fills, orders, fill rate, PNL)

### What's NOT Implemented
- [x] Adaptive edge (tanh formula) — IMPLEMENTED Cycle 22 (ADAPTIVE_EDGE_MAX=3, ADAPTIVE_EDGE_SCALE=20)
- [ ] Penny-in logic (improve on best bid/ask by 1) — NOTE: partially implemented in requote_mm as L1 penny-in
- [x] Order book imbalance skew — IMPLEMENTED Cycle 21 (OBI_STRENGTH=1.5, OBI_MAX_SKEW=3)
- [ ] Fed prediction market quoting (R_CUT/R_HOLD/R_HIKE as MM)
- [ ] VPIN toxicity detection
- [ ] Smart/dumb bot detection
- [ ] Live parameter config reload
- [ ] Meta market handler
- [ ] Gamma scalping
- [ ] Noise injection on order sizes

### Current Parameters
```python
MM_LEVELS       = 3        # restored from 2→3 in Cycle 18 (with position gate)
UNWIND_STALE_TICKS = 20   # ticks before switching from best_bid/ask to mid±offset (Cycle 19)
UNWIND_STALE_OFFSET = 2   # offset from mid when stuck; escalates every 20 ticks (Cycle 19)
UNWIND_STALE_OFFSET_MAX = 50  # raised 20→50 in Cycle 22 (mid±20 was insufficient for large moves)
MM_LEVEL_STEP   = 2
MM_BASE_EDGE    = 1
MM_SIZE         = 5        # reduced from 8 in Cycle 7; 7 tried in Cycle 22 and reverted (cascade risk)
MM_FADE_FACTOR  = 0.5
ADAPTIVE_EDGE_MAX   = 3   # Cycle 22: max additional edge from inventory for adaptive spread
ADAPTIVE_EDGE_SCALE = 20  # Cycle 22: position scale for tanh formula
OBI_STRENGTH    = 1.5      # order book imbalance skew strength (Cycle 21)
OBI_MAX_SKEW    = 3        # max OBI skew in price units (Cycle 21)
ETF_SWAP_FEE    = 5
ETF_ARB_EDGE    = 1        # lowered 2→1 in Cycle 21 for more arb captures
PCP_ARB_EDGE    = 1        # lowered 3→1 in Cycle 21 for more arb captures
BOX_ARB_EDGE    = 1        # lowered 2→1 in Cycle 21
OPT_SIZE        = 1        # reduced from 2 in Cycle 7
FED_MM_EDGE     = 3
FED_MM_SIZE     = 2        # reduced from 5 in Cycle 12
SOFT_POS_LIMIT_STOCK = 60
SOFT_POS_LIMIT_ETF   = 30   # raised from 20 in Cycle 19 (position gate makes it safer to widen)
SOFT_POS_LIMIT_OPT   = 20
SOFT_POS_LIMIT_FED   = 20  # reduced from 30 in Cycle 7
```

### Throttle (Cycle 12)
- `requote_mm` throttle: **50ms** (relaxed from 100ms in Cycle 10)
- `requote_fed` throttle: **50ms per-symbol** (added Cycle 12) + emergency unwind at 70% of SOFT_POS_LIMIT_FED
- Fed hard stop in `bot_handle_order_fill`: **70% of soft limit** (vs 80% for stocks)

### Position Gate (Cycle 18)
- `requote_mm` position gate: `if abs(pos) >= soft_limit: return` — refuses MM orders when pos >= soft limit
- Outer emergency threshold: **60% of soft limit** (tightened from 70% in Cycle 18)
- Combined effect: pos 0-60% → normal MM; pos 60-100% → emergency unwind only; pos >= 100% → position gate blocks requote_mm

### Emergency Unwind Fix (Cycle 20)
- Unwind qty reduced from 10 → **5** in both emergency unwind paths (requote_mm + bot_handle_book_update)
- Sign-crossing guard: `unwind_qty = min(unwind_qty, abs(pos))` prevents any single order from pushing position through zero
- Staleness escalation (from Cycle 19, still active): escalating offset mid±2 → mid±4 → ... → mid±20 (every 20 stuck ticks)
- `UNWIND_STALE_OFFSET_BASE=2`, `UNWIND_STALE_OFFSET_STEP=2`, `UNWIND_STALE_OFFSET_MAX=20`
- Bidirectional cascade root cause IDENTIFIED: 130+ queued unwind orders all fill on price recovery — async cancel lag. Qty reduction doesn't fix this; need to limit NUMBER of pending unwind orders.

### Performance (Practice Exchange 2026-04-10)
- **Rank: 26 / 30** (268,996 total — mostly idle rounds)
- **Best single session PNL: +991k** (Cycle 8 mid-session peak, full-session fills=8216)
- **Cycle 18 clean-start PNL: +41,572** (65s, 199 fills — vs -131k in Cycle 17, +172k improvement)
- **Cycle 19 inherited-pos PNL: -774,483 end / +670,297 peak** (heavy inherited A=72, ETF=-175; bidirectional cascade)
- **Fill rate: ~8.5%** (Cycle 18 clean start, 199 fills / 2338 orders)
- **Position gate CONFIRMED**: A capped at 46 (< soft=60), NO cascade to ±200 from clean start
- **Startup cancel: CONFIRMED WORKING** — no stale cascade on connect
- **Staleness detection CONFIRMED**: Fires at 20 stuck ticks, switches to mid±2 (confirmed in Cycle 19 logs)

### Known Issues (Priority Order)
0. **[PARTIAL Cycle 19] Emergency unwind staleness escalation** — staleness detection implemented (switches to mid±2 after 20 stuck ticks). But mid±2 is still insufficient for large market moves. Staleness counter hit 46,000+ ticks — bot stuck for entire session even at mid±2. Fix needed: escalating offset (mid±2 → mid±4 → mid±6 ... capped at mid±20, every 20 ticks).
1. **[FIXED Cycle 11] Async cancel stacking (stocks)** — throttle relaxed to 50ms (from 100ms). Fills doubled (244 vs 117). Still present but dampened.
2. **[FIXED Cycle 11, PARTIALLY TESTED] Startup unwind too conservative** — now iterative: loop up to 5 × 10-unit orders at best_bid/best_ask. Tested Cycle 12 but only 5 rounds = 50 units; C=-200 (140 over soft=60) needs 14+ rounds. MUST increase to 15 rounds.
3. **[FIXED Cycle 11, CONFIRMED Cycle 12] Emergency unwind orders crossing spread** — best_bid/best_ask logic confirmed working for Fed symbols (1,282 unwind attempts in Cycle 12 with no runaway cascade). Stock unwind still needs inherited-position test.
4. **[FIXED Cycle 12] Fed symbols cascading to ±180** — Added 50ms throttle + emergency unwind at 70% threshold + FED_MM_SIZE 5→2 + 70% hard stop on fills for R_. R_HOLD/R_HIKE capped at ±14. R_CUT drifted to -24 (started at -18 inherited) but no cascade.
5. **[FIXED Cycle 13] Startup unwind rounds too few** — changed `min(5,...)` → `min(15, ceil(excess/10))`. B=155 unwound to ~45 in one startup pass (10 orders vs old 5). CONFIRMED WORKING.
6. **A and ETF correlated cascade** — when A runs away, ETF goes opposite direction. Both freeze in emergency-unwind simultaneously.
6b. **[FIXED Cycle 15] Startup unwind timing bug** — replaced `startup_unwind_done` with `startup_unwind_pending` set. Each symbol deferred until IT has mid_price. ETF=-51 now gets 4 startup unwind orders (was 0). Per-symbol pattern confirmed working.
6c. **[FIXED Cycle 16] Quoting blocked on pending symbols** — `if sym in startup_unwind_pending: continue` guard prevents MM quoting on symbols whose unwind hasn't fired yet (mid_price=None). ETF arb also blocked during ETF startup unwind. PNL improved to +227k end (from -74k).
7. **[CONFIRMED Cycle 13] B position source = inherited, not live arb** — B=155 at startup in Cycle 13, fully explained by inherited positions from prior session. No B POSITION CHANGE during live session. However B went +45 → -122 without triggering fill handler — position may update via exchange position_snapshot without fills. Need to investigate `bot_handle_position_update`.
8. **arbs counter inflated** — `record_arb()` counting inflated numbers. Bug in call location.
9. **Fed priors don't initialize when market has no quotes** — falls back to 1/3 each.
10. **PE calibration requires earnings in current round** — mid fallback used if joined mid-round.

### Journey Milestones
| Cycle | Score | PNL | Key Change |
|-------|-------|-----|-----------|
| 0 | N/A | N/A | Setup — fixed symbols, deps, connectivity |
| 1 | 100 | +17,524 | First trades: 325 fills, ETF MM + PCP arb |
| 2 | ~1400 (idle) | -273k | PE calibration, mid fallback, metrics tracker |
| 3 | TBD | **+374,655** | Penny-in, edge 3→1, size 5→8, limits tighter, 332 fills |
| 4 | TBD | N/A (tainted by stale pos) | Hard stop at 80% soft limit (requote + fill callback cancel), bot running continuously |
| 5 | TBD | +175k | Soft limit in position_room; C max 72 (was 199), 505 fills |
| 6 | TBD | +50k (60s) | Fix fill handler position tracking: compute post-fill delta manually; hard stop now fires at correct threshold |
| 7 | TBD | +356k (peak) / -190k (end) | MM_SIZE 8→5, OPT_SIZE 2→1, SOFT_POS_LIMIT_FED 30→20; discovered stale inherited orders are #1 cascade cause |
| 8 | TBD | +991k (peak) / -97k (end) | Startup cancel: cancel all stale orders on first book update; fill rate 2%→50%; no more stale order cascades |
| 9 | TBD | -95k (end, 60s clean-slate test) | Startup position unwind + emergency unwind mode when pos > soft limit; A cascade persists from async cancel stacking |
| 10 | TBD | ~-94k (60s, inherited positions) | 100ms requote throttle + 70% emergency threshold + MM_LEVELS 4→2; throttle confirmed working (fills 408→117), cascade persists from inherited pos |
| 11 | TBD | -193k end / +538k peak (65s, clean slate) | 50ms throttle + cross-spread emergency unwind (best_bid/best_ask) + iterative startup unwind (5×10); fills doubled (244 vs 117); NEW: Fed symbols cascaded to ±180 (no throttle on requote_fed) |
| 12 | TBD | -549k end / +499k peak (60s, inherited pos) | Fed fix: 50ms throttle + emergency unwind in requote_fed + 70% hard stop on fills for R_ + FED_MM_SIZE 5→2; R_HOLD/R_HIKE CAPPED at ±14 (was ±180); R_CUT drifted to -24 (inherited -18) but no cascade |
| 13 | TBD | -192k end / +453k peak (60s, inherited pos) | Startup unwind 5→15 rounds + B logging; B=155 unwound to ~45; B source confirmed inherited not live arb; ETF still cascading; PNL +356k vs Cycle 12 |
| 14 | TBD | -977k end (147s, very heavy inherited pos) | SOFT_POS_LIMIT_ETF 30→20; ETF startup unwind FAILED (mid_price=None at startup time); ETF cascaded 109→±200; startup unwind timing bug confirmed |
| 15 | TBD | -74,938 end / +37k peak | Per-symbol deferred startup unwind (startup_unwind_pending set); ETF unwind FIRES now (4 orders for -51 inherited); emergency unwind logging added; bidirectional cascade persists |
| 16 | TBD | **+227,956 end / +511k peak** | Block quoting on startup_unwind_pending symbols; ETF arb blocked during ETF unwind; quoting guard fires for deferred (None mid_price) symbols only; bidirectional cascade persists but PNL positive |
| 17 | TBD | -131k end (clean start, bot frozen) | startup_quoting_blocked set: persists after startup unwind, clears when pos <= soft; mechanism correct but not triggered (session started with 0 inherited pos); within-session cascade unchanged |
| 18 | TBD | **+41,572 end** (clean start, 65s) | Position gate in requote_mm (abs(pos) >= soft → return); outer threshold 70%→60%; MM_LEVELS 2→3; A capped at 46 (NO cascade to ±200); +172k vs Cycle 17 |
| 19 | TBD | -774,483 end / +670,297 peak (inherited pos A=72 ETF=-175) | Staleness counter (mid±2 after 20 stuck ticks); SOFT_POS_LIMIT_ETF 20→30; staleness CONFIRMED WORKING; mid±2 insufficient for large moves — need escalating offset |
| 20 | TBD | ~-460k end (inherited pos A=84 ETF=-142) | Unwind qty 10→5 in both emergency paths; sign-crossing guard min(qty,abs(pos)); qty=5 CONFIRMED in logs; bidirectional cascade persists (async cancel lag, not qty per order) |
| 21 | TBD | -257k end (inherited pos ETF=142, B=-103 heavy) | **STRATEGIC PIVOT**: Lower arb thresholds PCP 3→1, BOX 2→1, ETF 2→1; OBI skew (bid/ask vol imbalance shifts quotes); emergency unwind bug fix (startup_quoting_blocked no longer blocks emergency path); arb freq increased |
| 22 | TBD | -57k (inherited B=198); 49-58% fill rate early | Adaptive edge (tanh formula, wide with inventory, tight when flat); arb freq ETF/tick, PCP/2, box/3; UNWIND_STALE_OFFSET_MAX 20→50 |

### What's Been Exhaustively Tested (DON'T re-test)
- Wrong symbols APT/DLR/MKJ/AKAV — confirmed wrong in Cycle 0
- Hardcoded A_PE=15 — way too low, implied PE ~657
- Hardcoded C_PE0=14 — way too low at practice scale, implied ~546
- Port 50052 — wrong, correct port is 3333
- protobuf 5.29 — incompatible with generated code, need 6.x
- grpcio 1.71 — incompatible, need >=1.78
- Equal Fed priors (1/3 each) — market has very different distribution

### Directions to Try Next
1. **[DONE Cycle 12] Add throttle to `requote_fed`** — CONFIRMED WORKING: R_HOLD/R_HIKE capped at ±14. FED_MM_SIZE 5→2.
2. **[DONE Cycle 13] Increase startup unwind rounds from 5 to 15** — CONFIRMED WORKING: B=155 unwound to ~45 (10 rounds × 10 units = 100 units unwound). Previously 5 rounds × 10 = 50 max.
3. **[DONE Cycle 11, CONFIRMED Cycle 12] Cross-spread emergency unwind** — confirmed active (1,282 Fed unwind attempts). Stock version needs inherited-position test.
4. **[DONE Cycle 13] B position investigation** — B source confirmed inherited from prior sessions. B went +45→-122 during session without triggering fill handler. Need to investigate if `bot_handle_position_update` is a callback that fires. Add logging to confirm.
5. **Fix arbs counter bug** — `record_arb()` counting inflated numbers (190k reported, impossible).
6. **Lower arb thresholds** — PCP_ARB_EDGE from 3 to 1
7. **Track round transitions** — use market_resolved to log per-round PNL properly
8. **Adaptive edge** — widen when volatile, tighten when calm
9. **Consider disabling Fed quoting when inherited Fed pos already past threshold** — if startup shows R_CUT/R_HOLD/R_HIKE already past emergency_threshold_fed, skip quoting and unwind first
10. **[DONE Cycle 14, INEFFECTIVE] Reduce SOFT_POS_LIMIT_ETF from 30 to 20** — parameter changed but ETF startup unwind failed (mid_price=None at startup). ETF=109 never unwound; cascaded to ±200 anyway. Root cause is startup unwind timing, not soft limit value.
11. **[DONE Cycle 15] Fix startup unwind timing** — replaced `startup_unwind_done` with per-symbol `startup_unwind_pending` set. Each symbol defers until IT has mid_price. ETF=-51 now gets 4 unwind orders. CONFIRMED WORKING.
12. **[DONE Cycle 15] Add logging to ETF emergency unwind in requote_mm** — added "EMERGENCY UNWIND: {sym} pos={pos} >= threshold, selling/buying qty @ px". Now visible and quantifiable.
14. **[DONE Cycle 16] Block quoting on startup_unwind_pending symbols** — guard `if sym in startup_unwind_pending: continue` added to requote loop. ETF arb also blocked while ETF in pending. Bidirectional cascade persists but PNL improved to +227k.
15. **[DONE Cycle 17] Add `startup_quoting_blocked` per-symbol set** — persists AFTER startup unwind fires, cleared only when position falls below soft limit. Both requote_mm and check_etf_arb blocked. Mechanism correct but not triggered in Cycle 17 test (session started with 0 inherited positions). Will activate on next inherited-position session.
16. **[DONE Cycle 18] Gate requote_mm when abs(pos) >= soft_limit** — position gate added: `if abs(pos) >= soft_limit: return` inside requote_mm. A capped at 46 in Cycle 18 (was -197 in Cycle 17). CONFIRMED WORKING. Combined with tightened outer threshold (70%→60%) and MM_LEVELS 2→3.
17. **[ONGOING] Investigate B pos silent changes** — B went 17→55→184 without fill logs. `bot_handle_position_update` doesn't exist as a callback. The exchange uses `handle_position_snapshot` (not overridable) and `position_update` messages that directly update `self.positions` without callbacks. B pos changes come from exchange position_snapshot updates — not interceptable without modifying the base class.
18. **[ONGOING] Test startup_quoting_blocked with inherited positions** — bot running continuously; will trigger on next restart with inherited positions > soft limit.
19. **[NEW Cycle 18] Fix emergency unwind price staleness** — emergency unwind freezes when market moves away from `best_bid`/`best_ask` at order placement time. Need: (a) staleness counter (if pos unchanged for >20 ticks while in emergency mode, try mid±2 instead), OR (b) raise SOFT_POS_LIMIT_ETF from 20 to 30 to give more room before emergency fires.
20. **[NEW Cycle 18] Consider raising SOFT_POS_LIMIT_ETF from 20 to 30** — with position gate now providing hard cap at soft_limit, raising it back to 30 gives ETF more room for normal MM. ETF at -24 with soft=20 means perpetually in emergency mode. With soft=30, ETF=-24 is within normal range and gets requoted normally.
13. **[NEW] Investigate B pos change without fills** — B went +45→-122 in Cycle 13 without triggering `bot_handle_order_fill`. Check if `bot_handle_position_update` exists and add logging.

---

## CONNECTION INFO
- Practice exchange: `34.197.188.76:3333`
- Web UI: `http://34.197.188.76:3001`
- Team: `ucla_calberkeley`
- Password: `titan-solar-kelp`
- Competition: Saturday April 11, 9:15am CDT, Willis Tower Chicago
- Competition exchange: DIFFERENT from practice (EC2 instances, same VPC)

## FILE MAP
```
bot.py              — Main trading bot
strat1.py           — Original prototype (OBSOLETE — wrong params, not wired)
probe.py            — Exchange symbol verification tool
probe2.py           — Market price observation tool
run.sh              — Continuous execution wrapper
metrics.jsonl       — Per-round metrics log
logs/               — Bot output logs
GOLDEN_PRINCIPLES.md — Hard-won rules
HANDOFF.md          — This file
AUDIT_TRAIL.md      — Iteration history
CASE1_IMPLEMENTATION_PLAN.md — Original 4-phase plan
UTC_2026_*.md       — Research briefs and strategy guides
```
