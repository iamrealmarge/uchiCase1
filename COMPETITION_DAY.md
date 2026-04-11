# Competition Day Playbook — April 11, 2026
**Team ucla_calberkeley | Willis Tower Chicago | 9:15am-12:15pm CDT**

---

## WHAT IS EC2?

EC2 = Amazon cloud server. The competition gives each team a virtual computer in the cloud. You SSH (remote connect) into it from your laptop and run your bot there. Everyone's EC2 is in the same network as the exchange server, so latency is ~1ms (vs ~80ms from your home machine).

**You need:**
- SSH client (built into Mac Terminal)
- The EC2 hostname/IP + credentials (provided competition morning)
- VSCode with SSH extension (recommended) OR just use terminal

**Connect:** `ssh -i <key.pem> ubuntu@<ec2-ip>` (exact command provided day-of)

---

## TIMELINE

### 8:00 — Arrive at Willis Tower, Set Up
```
□ Open laptop
□ Connect to WiFi
□ Open Claude Code on laptop (this repo)
□ Open browser: leaderboard URL (will be given)
□ Open browser: Ed Discussion for announcements
```

### 8:30 — SSH into EC2, Deploy Code
```
□ Get EC2 credentials from organizers
□ SSH in: ssh -i key.pem ubuntu@<ec2-ip>
□ Clone repo: git clone https://github.com/iamrealmarge/uchiCase1.git
□ cd uchiCase1
□ pip install utcxchangelib  (REINSTALL fresh per Ed post #46)
□ Verify: python3 -c "import bot; print('OK')"
□ Upload helper scripts: status.sh, tweak.sh, restart.sh
```

### 9:00 — Tech Case Prep (Meta Market Revealed)
```
□ READ the meta market rules carefully
□ Describe rules to Claude Code on laptop
□ Claude writes handler code → paste into bot.py on EC2
□ Check if risk limits changed from practice
□ Get COMPETITION exchange host:port (DIFFERENT from practice!)
□ Test connection: python3 bot.py <comp-host:port> <user> <pass>
□ Verify: STARTUP message, positions=0, fair values appearing
```

### 9:15 — LIVE TRADING BEGINS
```
□ Start bot: nohup python3 bot.py <host> <user> <pass> > bot_live.log 2>&1 &
□ echo $! > .bot_pid
□ Start monitoring: tail -f bot_live.log | grep -E "(STATUS|FILL|METRICS|FLATTEN)"
□ DO NOT TOUCH for 15 minutes
```

### 9:30-12:15 — Round-by-Round Loop (see below)

### 12:15 — Trading Ends
```
□ Check final rank on leaderboard
□ Save logs: cp bot_live.log bot_final.log
```

---

## BETWEEN-ROUND PROTOCOL (30-second window)

### Step 1: Grab Metrics (5 seconds)
```bash
# On EC2:
./status.sh
```

### Step 2: Feed to Claude Code (10 seconds)
Copy-paste the output into Claude Code on laptop. Or if tunnel is set up, Claude reads it automatically.

### Step 3: Get Analysis (10 seconds)
Claude responds with: keep current params OR specific change to make.

### Step 4: Apply (5 seconds)
```bash
# On EC2:
./tweak.sh MM_BASE_EDGE 0    # example
# Bot picks up changes when round resets
```

---

## WHAT TO MONITOR

### GREEN (Good) — Keep Going
- Score < 10 per round
- PNL positive and growing
- Fills on A, C, ETF (not just options)
- Flattening phases appearing: [FLATTEN_GENTLE] → [FLATTEN_HARD] → [FLATTEN_STOP]
- Positions near zero at settlement

### YELLOW (Watch) — Consider Changes
- Score 10-50
- Fill rate dropping below 5%
- Only getting fills on one side (all buys, no sells)
- Positions > 30 at settlement (flattening not working)

### RED (Act Now) — Change Parameters
- Score > 100
- PNL negative at settlement despite positive cash
- Bot not getting any fills
- Bot crashed
- Positions at 200 (max limit hit)

---

## PARAMETER CHEAT SHEET

| Parameter | Current | Tighter (more fills) | Wider (more PNL/fill) |
|-----------|---------|---------------------|-----------------------|
| MM_BASE_EDGE | 1 | 0 | 2-3 |
| MM_SIZE | 5 | 8 | 3 |
| SOFT_POS_LIMIT_STOCK | 60 | 30 | 80 |
| SOFT_POS_LIMIT_ETF | 30 | 15 | 40 |
| MM_LEVELS | 3 | 4 | 2 |

**When to tighten:** Fill rate dropping, other teams getting tighter
**When to widen:** Getting adversely selected (buying high, selling low)

---

## ROUND-BY-ROUND STRATEGY

| Rounds | Fill rate likely | Strategy | Edge | Size |
|--------|-----------------|----------|------|------|
| 1-3 | High (10%+) | Wide spreads, capture dumb money | 1-2 | 5 |
| 4-6 | Medium (5-10%) | Moderate, increase arb reliance | 1 | 5 |
| 7-9 | Low (3-5%) | Tight spreads, fight for fills | 0-1 | 5-8 |
| 10-12 | Very low (<3%) | Arb-dominant, minimal MM | 0 | 3 |

---

## EMERGENCY PROCEDURES

### Bot Crashes
```bash
# Check if running:
ps -p $(cat .bot_pid)
# Restart:
./restart.sh <host> <user> <pass>
# Startup cancel will clear stale orders automatically
```

### Not Getting Fills
```bash
./tweak.sh MM_BASE_EDGE 0
# This makes penny-in the only quoting — most aggressive
```

### Positions Blowing Up
```bash
./tweak.sh SOFT_POS_LIMIT_STOCK 20
./tweak.sh SOFT_POS_LIMIT_ETF 10
# Restart bot between rounds
```

### Flattening Not Working
Check: is exchange_tick updating? Look for etick > 0 in STATUS logs.
If etick stays at 0, wall clock fallback kicks in at 12 min (720 sec).
If neither works, manually kill bot at 14:00 mark of each round.

---

## CLAUDE CODE LIVE TUNNEL

### Option A: Manual Copy-Paste (Simplest)
Every round end → copy status.sh output → paste into Claude Code

### Option B: SSH Log Tail to Local File
```bash
# On laptop, run in background:
ssh -i key.pem ubuntu@<ec2-ip> 'tail -f ~/uchiCase1/bot_live.log' > /tmp/bot_live.log &

# Claude Code can then read /tmp/bot_live.log directly
# Ask Claude: "Read /tmp/bot_live.log, analyze the latest round"
```

### Option C: Periodic SCP
```bash
# On laptop, every 30 seconds:
while true; do
  scp -i key.pem ubuntu@<ec2-ip>:~/uchiCase1/bot_live.log /tmp/bot_live.log
  sleep 30
done
```

### Option D: Claude Code SSH MCP (if available)
If Claude Code supports SSH MCP server, configure it to connect directly to EC2.
Then Claude can read/write files on EC2 natively.

---

## KEY LEARNINGS FROM PRACTICE (Don't Forget)

1. **PE auto-calibrates** — don't hardcode. Wait for first earnings, bot handles it.
2. **Fed priors from market** — bot reads R_CUT/R_HOLD/R_HIKE prices on startup.
3. **Positions reset every round** — clean start each time. No inherited position problem.
4. **Flattening is critical** — cash PNL ≠ settlement PNL. Bot flattens last 3 min.
5. **Score=1 is achievable** — we've done it twice on practice. Let the bot run.
6. **Don't restart mid-round** — only between rounds when positions reset.
7. **Competition exchange is DIFFERENT from practice** — different host:port, maybe different params.
8. **PE values will be DIFFERENT** on competition exchange — auto-calibration handles this.

---

## TEAM ROLES

| Person | Primary | Tool | Between Rounds |
|--------|---------|------|----------------|
| **Yifan** | Coder on EC2 | SSH Terminal | Apply param changes, fix crashes |
| **Emily** | Monitor | EC2 Terminal 2 | Run status.sh, call out issues |
| **Gary** | Analyst | Claude Code on laptop | Paste metrics, get analysis, write patches |
| **Margaret** | Strategist | Leaderboard + Ed | Track rank, watch competitors, announcements |
