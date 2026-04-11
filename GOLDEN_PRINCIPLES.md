# Case 1 Market Making — Golden Principles
**Hard-won rules from live practice exchange testing. Violate at your peril.**

Last updated: 2026-04-11 (Cycle 22)

---

## EXCHANGE FACTS (Immutable)

1. **Symbols are A, B, C, ETF** — NOT APT/DLR/MKJ/AKAV. Confirmed by probe against live exchange.
2. **Option symbols: B_C_950, B_C_1000, B_C_1050, B_P_950, B_P_1000, B_P_1050** — NOT "CALL_100" etc.
3. **Fed symbols: R_CUT, R_HOLD, R_HIKE** — prediction market for Fed rate decision.
4. **Swaps: "toETF" / "fromETF"** — $5 flat fee each direction.
5. **Prices are INTEGERS** — the exchange uses int prices, not floats.
6. **gRPC port is 3333** — NOT 50052. Practice exchange at 34.197.188.76:3333.
7. **Risk limits are per-symbol**: Max Order Size=40, Max Open Orders=50, Outstanding Volume=120, Max Abs Position=200.
8. **Violations are SILENT** — orders just get rejected, no error about which limit.
9. **Scoring: LOWER is BETTER** — rank-based within each round, sum across rounds.
10. **Later rounds weighted more heavily** — consistency beats variance.
11. **Nonlinear P&L → points** — small steady profits >> volatile big swings.
12. **Positions reset at end of each round** — no carry-over.

## PRICE DISCOVERY FACTS

13. **A_PE is NOT 15** — observed implied PE ~657 from market. PE must be AUTO-CALIBRATED from market_price / EPS after first earnings.
14. **C_PE0 is NOT 14 (at practice exchange scale)** — observed implied PE ~546. Auto-calibrate from market.
15. **Ed #40 parameters (PE0=14, D=7.5, C=55, λ=0.65, B0/N=40, y0=0.045)** are confirmed for the FORMULA STRUCTURE but the practice exchange uses scaled values.
16. **A trades ~600-1000, B trades ~1000, C trades ~1000-1100, ETF trades ~2800-3200** on practice exchange.
17. **γ and β_y are UNKNOWN** — must calibrate from observed price reactions to CPI/Fed news.
18. **EPS values are small (0.9-1.8)** — the high prices come from very high PE ratios.
19. **Earnings timing is RANDOM** — NOT at fixed ticks. Parse news dynamically.
20. **A can get >2 earnings per day** — be ready for frequent updates.

## MARKET MAKING RULES

21. **Always cancel before requoting** — stacking orders will hit Outstanding Volume limit.
22. **Use market mid as fallback fair value** — when no earnings received yet, quote around mid. Better to MM at mid than not MM at all.
23. **Logarithmic fade > linear fade** — `fade = -f * sign(pos) * log2(1 + |pos|)`.
24. **Position limits MUST be enforced aggressively** — soft limits at requote time aren't enough; need emergency unwind when exceeded.
25. **ETF position accumulates fastest** — biggest source of runaway positions. Keep soft limit tight (50).

## FED MARKET RULES

26. **Initialize Fed priors from market, NOT 1/3 each** — on practice exchange, market had cut=99.5% while our 33% priors lost money buying R_HIKE at 3.
27. **Blend market prices with model updates** — 60% market, 40% model after CPI/news.

## ANTI-PATTERNS (Things That Hurt)

28. **DON'T hardcode PE values** — they vary dramatically between practice and competition.
29. **DON'T quote when you have no fair value** — blind quoting gets you adversely selected.
30. **DON'T let the bot inherit positions from previous sessions without unwinding** — stale positions accumulate risk.
31. **DON'T ignore the prediction market** — it's a major signal source for C pricing.

## WHAT WORKS

32. **ETF market making generates the most reliable fills** — liquid, two-sided flow.
33. **PCP arb fires on options** — observed fills on B_C_1050 and B_P_1050.
34. **Cancel-before-requote prevents order stacking** — essential for risk management.
35. **Metrics tracking (MetricsTracker class) gives visibility** — fills, orders, fill rate, PNL.

## POSITION HARD STOP RULES (Cycle 4)

45. **Hard stop in requote is insufficient alone** — resting buy orders placed when short will all fill when price reverses, causing position to overshoot. Must also cancel on fills.
46. **Cancel on fill when |pos| >= 80% of soft limit** — `bot_handle_order_fill` must call `cancel_all_symbol` when position crosses the hard stop threshold.
47. **To really prevent blowout: also cancel the OTHER side** — when going short past threshold, cancel all resting buy orders too (not just the direction of the latest fill).
48. **Inherited stale positions distort metrics** — positions persist across sessions on the exchange; join mid-round and you're already at risk. Always check positions at startup.
49. **`safe_place` checks MAX_ABS_POSITION (200), not soft limit (30/60)** — must add soft limit check directly in safe_place, not just in requote_mm.

## FILL HANDLER FACTS (Cycle 6)

52. **`XChangeClient` does NOT update `self.positions` before calling `bot_handle_order_fill`** — position update arrives via a separate `position_update` message. Always compute post-fill position manually: `pos_after = self.positions.get(sym, 0) + (qty if is_buy else -qty)`.
53. **Cascading fills at the same price level cannot be stopped by async cancel** — all queued fills at a price level arrive before the cancel takes effect. Limit order SIZE so even a full cascade stays within limits.
54. **`open_orders` is still populated when `bot_handle_order_fill` fires** — parent pops the order AFTER calling the callback (for fully-filled orders). So `self.open_orders.get(order_id)` safely returns order info inside the fill handler.

## STARTUP / SESSION RULES (Cycle 7)

55. **CANCEL ALL OPEN ORDERS AT STARTUP** — when connecting or reconnecting to the exchange, resting orders from previous sessions persist. When price moves, ALL 25+ stale orders can cascade-fill before a cancel arrives. This is more dangerous than order size. Must call `cancel_all` for every symbol on first book update before placing any new orders.
56. **Stale inherited orders >> MM_SIZE as cascade source** — reducing MM_SIZE from 8 to 5 does NOT prevent cascades from stale orders. A bot running continuously for 20+ minutes can have 25+ resting ETF buy orders at the same price. When price recovers, all fill at once causing 125+ units of position swing. The startup cancel is the only effective fix.
57. **Best PNL (+356k) can coexist with massive end-of-session blowout (-190k)** — PNL can swing dramatically within a round due to inherited positions. Don't judge a cycle only by end PNL — also track peak PNL and position ranges.

## STARTUP / SESSION RULES (Cycle 8)

58. **Startup cancel fixes ORDERS, not POSITIONS** — `cancel_all_symbol` at startup eliminates stale resting orders from previous sessions. But inherited positions (e.g., ETF=-196 from continuous running) persist. After cancelling orders, must check positions and aggressively unwind any that exceed soft limits before starting normal quoting.
59. **`startup_cancel_done` flag pattern works** — check `not self.startup_cancel_done` at top of `bot_handle_book_update`, iterate `self.order_books.keys()`, cancel all, set flag, log, then `return` early. Confirmed working: no stale cascades on reconnect.
60. **Fill rate can be 50%+ when bot is positioned correctly** — in Cycle 8, after startup cancel, fill rate jumped from 2% to 50% because the bot had a large short position that the market wanted to fill into. Very high fill rates signal inventory imbalance, not necessarily alpha.
61. **`record_arb()` counter is likely buggy — inflated** — 190k arb trades reported in one session is impossible at real arb frequency. Investigate whether `record_arb()` is called in loops rather than only on confirmed arb leg fills.

## CASCADE / POSITION MANAGEMENT RULES (Cycle 9)

62. **Emergency unwind block fires too late if threshold = soft_limit** — by the time pos > soft_limit (60), cascade fills have already occurred. The cascade happens BELOW the soft limit threshold (e.g., pos=30 → cascade → pos=83 in one rapid sequence). Must intervene at 70% of soft limit, not 100%.
63. **Rapid requote + async cancel = order stacking** — cancel_all_symbol is async. If the same symbol's book updates 3x before cancel confirmations arrive, each requote places ~18 units of new orders on top of existing ones. Solution: per-symbol requote throttle (min 100ms between requotes on same symbol).
64. **Correlated asset cascades amplify losses** — A long + ETF short positions created by arb logic cause correlated unwinds. When both hit soft limits simultaneously, the bot enters emergency-unwind mode on ALL symbols and essentially freezes. ETF arb should be disabled when A or C position is near soft limit.

## REQUOTE THROTTLE / CASCADE PREVENTION (Cycle 10)

65. **Startup unwind must be iterative, not one-shot** — placing `min(10, excess+5)` once doesn't unwind positions that are 80+ units over soft limit. Must place `ceil(excess / 10)` orders covering the full gap, or loop until position is within limits. A single 10-unit order for A=141 (81 over soft=60) does almost nothing.
66. **Emergency unwind orders must cross the spread** — quoting at `mid±1` for unwinds only works if the market comes to you. When locked at ±200, place sells at `best_bid` and buys at `best_ask` to guarantee immediate fills. Don't wait for market flow; take liquidity aggressively.
67. **100ms throttle reduces cascade fills but doesn't prevent inherited-position cascades** — the throttle successfully reduced fresh cascade fills (117 vs 408). But inherited positions that start above the emergency threshold still cause cascades because they are immediately in unwind mode, and unwind orders don't fill fast enough. The throttle addresses NEW order stacking, not existing position imbalances.

## THROTTLE / CASCADE PREVENTION (Cycle 11)

68. **50ms throttle doubles fill rate vs 100ms** — Cycle 11 confirmed 244 fills vs 117 in comparable windows. 50ms is the current sweet spot: dampens cascade stacking while preserving fill generation.
69. **`requote_fed` has no throttle — Fed symbols cascade identically to stocks** — the 50ms throttle in `requote_mm` does NOT apply to `requote_fed`. R_HOLD and R_HIKE went to ±180 in Cycle 11 because `requote_fed` fires every 10 ticks unconditionally, allowing async cancel stacking. Must add the same per-symbol throttle to `requote_fed`.
70. **Cross-spread unwind code correct but requires inherited-position session to verify** — best_bid/best_ask logic was implemented in Cycle 11 but Cycle 11 started clean. Need a session that starts with positions over soft limits to confirm fills land immediately.

## FED CASCADE FIX (Cycle 12)

71. **`requote_fed` throttle + emergency unwind CAPS Fed positions** — adding 50ms per-symbol throttle + emergency unwind at 70% of soft limit to `requote_fed` kept R_HOLD/R_HIKE at ±14 (vs ±180 without). The same async-cancel-stacking mechanism affects all symbols, same throttle pattern fixes it everywhere.
72. **Inherited Fed positions drift slightly past soft limit at startup** — starting R_CUT=-18 (past emergency_threshold=14) caused drift to -24 because thin Fed market didn't fill unwind orders immediately. This is acceptable (was -180). Consider startup detect: if Fed pos already past threshold, skip quoting entirely until unwound.
73. **FED_MM_SIZE=2 is safer than 5** — smaller per-tick order size limits cascade exposure even if throttle briefly fails. With size=2 and soft_limit=20, a 10-tick stacking event accumulates ≤20 units (vs 50 with size=5), staying within the soft limit.
74. **Hard stop threshold for R_ symbols must be tighter than for stocks** — using 70% (not 80%) of soft_limit for Fed fill callbacks triggers cancel faster on fills. At soft_limit=20, 70%=14 is more aggressive than 80%=16. Combined with emergency unwind, this keeps Fed positions contained.

## STARTUP UNWIND RULES (Cycle 13)

75. **`min(15, ceil(excess/10))` startup unwind rounds work for large inherited positions** — B=155 (excess=95) unwound to ~45 (within soft=60) via 10 rounds of 10-unit cross-spread sells. Old `min(5,...)` would have left B=105, still 45 over limit. Use ceil not floor to ensure coverage.
76. **B position source is inherited, NOT live options arb** — during normal 60s sessions, B position only changes via startup unwind orders. PCP arb code places orders on B_C_*/B_P_* options, NOT on the B underlier directly. B accumulates across sessions from inherited fills.
77. **B position can change silently between sessions** — B went +45 (post-startup-unwind) → -122 during one session without triggering `bot_handle_order_fill`. The exchange may update positions via `position_snapshot` messages or inherited order fills that bypass the fill callback. Must investigate and log `bot_handle_position_update` if it exists.
78. **ETF cascade direction can flip sign** — ETF started at -172, unwind pushed toward 0, but then normal MM quoting caused a +125 cascade in the opposite direction. ETF is the most volatile position: oscillates between -170 and +125 across sessions. Need tighter ETF emergency threshold (SOFT_POS_LIMIT_ETF = 20, not 30) and consider disabling ETF MM when startup ETF pos is already past emergency threshold.

## STARTUP UNWIND TIMING (Cycle 14)

79. **Startup unwind silently skips symbols whose `mid_price` is None at startup time** — `startup_unwind_done` fires on the 2nd book update (the 1st was consumed by cancel-all + early return). If this 2nd update is for symbol A before ETF book data arrives, `mid_price("ETF")` returns None and the `if mid:` guard at line 1025 silently skips ETF. Result: ETF=109 (inherited) proceeds directly to MM quoting with no position reduction. Must defer startup unwind until all MM symbols have mid_price, or use fair_value/estimated_price as fallback.
80. **ETF emergency unwind block in `requote_mm` is silent** — the emergency unwind code at line 1057 places orders but has no log.warning, making it invisible in audit logs. Without logging it is impossible to verify it fires or quantify its effectiveness. Always log unwind attempts: "EMERGENCY UNWIND: {sym} pos={pos} >= {threshold:.0f}, qty={qty} @ {px}".
81. **ETF cascade is bidirectional when async cancel can't keep up** — emergency unwind sells ETF to -170, then stale resting buy orders cascade-fill pushing ETF back to +200. `cancel_all_symbol` is async: confirmations arrive AFTER cascade fills complete. The cancel-before-unwind sequence does NOT prevent inherited stale orders from all filling simultaneously on price recovery. Only a true synchronous cancel (or MM_SIZE=1 with position-gated quoting) prevents this.

## STARTUP UNWIND TIMING (Cycle 15)

82. **Per-symbol `startup_unwind_pending` set correctly defers each symbol until IT has quotes** — the old `startup_unwind_done` single flag fired once for ANY symbol (often A), silently skipping ETF whose mid_price was None. The new pattern: after cancel-all, add all over-limit symbols to `startup_unwind_pending`. On each subsequent book update, check `if symbol in startup_unwind_pending` and only execute the unwind if `mid_price(symbol)` is valid. ETF=-51 confirmed: 4 unwind orders placed vs 0 in Cycle 14.
83. **Emergency unwind fires repeatedly but fills don't always land** — with ETF=-51, 20+ emergency unwind buy orders were placed at best_ask, but the position only moved from -51 to -21 slowly. Orders are placed but exchange may be thin or price may move away. Track whether unwind orders are actually filling (by checking position change rate vs order submission rate).

## QUOTING BLOCK / CASCADE PREVENTION (Cycle 16)

84. **`startup_unwind_pending` guard in requote loop only blocks symbols whose mid_price is still None** — `if sym in startup_unwind_pending: continue` fires only before the deferred unwind triggers (i.e., while mid_price is unavailable). Once mid_price arrives, the unwind fires and clears the symbol from pending — so normal MM resumes immediately in the same session. To block quoting AFTER startup unwind fires, need a separate `startup_quoting_blocked` flag that stays set until position returns below the soft limit.
85. **Positive end PNL (+227k) is achievable even with very heavy inherited positions (A=199, C=200, ETF=41)** — startup unwind cross-spread sells reduce all inherited long positions quickly (first 1000 ticks), locking in realized gains. Even after the bot freezes in multi-symbol emergency-unwind mode, the positive PNL from unwind-fills is retained. The key is placing enough startup unwind orders (15 rounds) to actually trade out of large inherited positions.

## PERSISTENT QUOTING BLOCK (Cycle 17)

86. **`startup_quoting_blocked` mechanism requires inherited-position session to verify** — when startup positions are all 0, the set remains empty and the mechanism is a no-op. The set is populated only when `abs(pos) > soft_limit` at startup. The mechanism will fire on the next session that has inherited positions exceeding the soft limit (competition exchange, or after continuous running).
87. **Within-session cascade is distinct from startup-inherited cascade** — even starting with 0 positions, normal MM fill accumulation can drive A=-197, C=-195, ETF=+189 within 200 ticks. This is NOT blocked by `startup_quoting_blocked`. Requires a separate gate: refuse to quote when already in emergency mode (abs(pos) > soft_limit) rather than still trying to MM through it.

## POSITION GATE (Cycle 18)

88. **Position gate in `requote_mm` (abs(pos) >= soft_limit → return) CAPS within-session accumulation** — in Cycle 17 (clean start), A cascaded to -197. In Cycle 18 with `if abs(pos) >= soft_limit: return` at the top of requote_mm, A maxed at 46 (below soft=60). This is structurally different from the emergency threshold: the emergency threshold SWITCHES to unwind mode at 70%, but still allows requote_mm to run between 0% and 70% accumulation. The position gate is a hard wall that prevents ANY new MM orders once soft limit is reached.
89. **Emergency unwind price staleness causes persistent frozen states** — emergency unwind places sell/buy orders at `best_bid`/`best_ask` at time of requote, but price moves after placement. With 50ms throttle, the bot re-places at current `best_bid`/`best_ask` every 50ms, but async cancels may not clear old orders quickly enough. Net effect: hundreds of emergency unwind orders pile up at stale prices, none filling, bot frozen. Fix: track consecutive unwind ticks with no position change; after N ticks, switch to `mid_price ± adjustment`.
90. **Outer emergency threshold at 60% (not 70%) catches cascades earlier** — with SOFT_POS_LIMIT_STOCK=60, 60% = 36. This means normal MM stops at pos=36 and emergency mode starts. Less accumulation between threshold and soft limit (36 vs 42 at 70%), reducing the "gap" that cascades can exploit.

## STALENESS ESCALATION (Cycle 19)

91. **Staleness counter fires correctly but `mid±2` escalation is insufficient for large market moves** — switching from `best_ask`/`best_bid` to `mid±2` only adds ~2-3 price units of aggressiveness. When market moves 50+ units while bot is stuck in emergency mode, even `mid±2` stays unfilled indefinitely. Need escalating offset: start at `mid±2`, then `mid±4`, then `mid±6` (every 20 ticks), capped at `mid±20`. The escalation should also reset when position moves.
92. **SOFT_POS_LIMIT_ETF=30 is structurally better than 20 when position gate is active** — with the Cycle 18 position gate (abs(pos) >= soft_limit → refuse MM), raising ETF soft limit from 20 to 30 is safe: the gate prevents runaway accumulation at 30, while the emergency threshold at 60%=18 now gives more normal-MM range (0-18 instead of 0-12). ETF positions 0-18 get normal MM; 18-30 get emergency unwind; 30+ are blocked by gate.

## UNWIND CASCADE MECHANICS (Cycle 20)

93. **Reducing unwind qty from 10→5 slows oscillation but does NOT prevent bidirectional cascade** — the cascade is driven by dozens of stale queued unwind orders all filling when price recovers (async cancel lag). With stale_count=130+, the bot has queued 130 unwind orders of 5 = 650 units of potential cascade. Reducing qty per order is less dangerous, but doesn't fix the fundamental issue: too many pending orders. The real fix requires limiting the NUMBER of pending unwind orders (e.g., track a single active unwind order ID and cancel before placing a new one).
94. **Sign-crossing guard (`min(unwind_qty, abs(pos))`) is a structural safety net** — mathematically prevents any single unwind order from pushing position through zero. At current threshold values (ETF threshold=18 > max_qty=5), it doesn't trigger in practice (can't reach near-zero while in emergency block). But it correctly constrains future parameter changes where threshold could be reduced below 5. Always include in emergency unwind code.
95. **The async cancel lag is the root cause of bidirectional cascade** — `cancel_all_symbol` is async. In 130+ stuck ticks, the bot places 130+ unwind orders. When price finally recovers: ALL 130 orders fill before cancel confirmations arrive. Position swings 650 units in one tick. No qty reduction or sign-crossing guard fixes this — only reducing the NUMBER of queued orders (track active unwind order count) or making cancel synchronous (not possible with gRPC) would help.

## COMPETITION DAY RULES (Cycle 21)

96. **`startup_quoting_blocked` must NOT block emergency unwind** — the flag was designed to prevent normal MM quoting while inherited positions are elevated. But the original `continue` statement skipped emergency unwind too. For symbols with startup_quoting_blocked AND abs(pos) > emergency_threshold, emergency unwind is still needed. Fix: check `mm_quoting_allowed` before calling `requote_mm`, but run emergency unwind regardless of this flag.
97. **Lower PCP/box arb thresholds generate more fills per round** — PCP_ARB_EDGE=1 fires more frequently than PCP_ARB_EDGE=3. At competition with clean slate, each additional arb fill adds pure risk-free PNL. Lower thresholds improve fill count with no additional risk (arb positions cancel out across legs).
98. **Positions reset every round at competition — inherited cascade is a non-issue** — practice exchange runs continuously across rounds, accumulating inherited positions. At competition, each 15-min round is a clean slate. All the Cycle 7-20 inherited-position cascade issues don't apply. Focus on clean-start PNL generation.
99. **Order book imbalance (OBI) skew improves fill rate** — if bid volume >> ask volume, more participants want to buy → shift quotes slightly bullish to make our sell side tighter (more likely to fill). Formula: skew = OBI_STRENGTH * (bid_vol - ask_vol) / (bid_vol + ask_vol), capped at ±OBI_MAX_SKEW. Incorporated into `adjusted_fair = fair + fade + obi_skew`.

## ADAPTIVE EDGE (Cycle 22)

100. **Adaptive edge (tanh formula) earns more PNL per fill as inventory builds** — formula: `edge = MM_BASE_EDGE + ADAPTIVE_EDGE_MAX * tanh(|pos| / ADAPTIVE_EDGE_SCALE)`. At pos=0: edge=1 (tightest, max fills). At pos=20: edge=3.28 (wider, earns more per fill). At competition (clean start), this means the bot starts tight to capture the most fills and widens as inventory accumulates, properly compensating for risk.
101. **75% emergency threshold rejected — 60% must stay** — raising emergency threshold from 60% to 75% of soft_limit allowed positions to accumulate to ~56 before emergency kicked in (vs 36 at 60%). The extra headroom created async-cancel-lag cascade room: stale resting orders from ticks where pos was 36-56 all filled when price recovered, pushing C to 200. The 60% threshold (=36 for stock soft_limit=60) is the correct balance between early intervention and normal MM range.
102. **MM_SIZE=7 rejected for same reason as rule 101** — larger per-order size means more units queued in resting orders during the normal-MM range (0 to 36). When price cascades, all 7-unit orders fill simultaneously vs 5-unit orders. Root cause is async cancel lag; smaller MM_SIZE reduces cascade magnitude.

## UNTESTED / UNKNOWN

37. **Box spread arb frequency** — now fires every 3 ticks (was every 5). Higher frequency = more arb captures at competition.
38. **Multi-level quoting beyond 3 levels** — current 3 levels may not be enough.
39. **Competition exchange may use DIFFERENT parameters** — be ready to re-calibrate on April 11.
40. **ADAPTIVE_EDGE_MAX=3 tuning** — if competition fill rate is low (< 5%), edge may be too wide. Consider reducing to 2. If PNL/fill is low but fills are high, consider increasing to 4.
