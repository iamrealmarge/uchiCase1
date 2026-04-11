"""
Case 1 Bot — UChicago Trading Competition 2026
================================================
Team: ucla_calberkeley

Subclasses utcxchangelib.XChangeClient.
Implements: market making on A/C, ETF arb via swaps,
put-call parity + box spread arb on B options, news-driven fair value,
logarithmic inventory fade, cancel-before-requote, CPI/petition handling.

Symbols (confirmed from exchange):
  A       = Stock A (small-cap, constant PE, earnings-driven)
  B       = Stock B (semiconductor, traded via options)
  C       = Stock C (insurance, yield + bond portfolio model)
  ETF     = ETF (= A + B + C, swap fee $5 flat)
  B_C_950, B_C_1000, B_C_1050 = Call options on B
  B_P_950, B_P_1000, B_P_1050 = Put options on B
  R_CUT, R_HOLD, R_HIKE       = Fed prediction market

Usage:
  python3 bot.py <host:port> <username> <password>
"""

import asyncio
import math
import sys
import time
import json
import logging
from collections import defaultdict
from utcxchangelib.xchange_client import XChangeClient, Side

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("case1-bot")

# ═══════════════════════════════════════════════════════════════════════════════
# METRICS TRACKER (inspired by Case 2 harness)
# ═══════════════════════════════════════════════════════════════════════════════

class MetricsTracker:
    """Track per-round performance metrics. Writes to metrics.jsonl."""

    def __init__(self, path="metrics.jsonl"):
        self.path = path
        self.round_start_time = time.time()
        self.round_start_cash = 0
        self.fills = 0
        self.orders_placed = 0
        self.orders_rejected = 0
        self.buys = 0
        self.sells = 0
        self.max_position = {}      # symbol → max abs position seen
        self.pnl_snapshots = []     # periodic cash snapshots
        self.arb_trades = 0         # ETF/PCP/box arb fills

    def record_fill(self, symbol, side, qty, price):
        self.fills += 1
        if side == "BUY":
            self.buys += qty
        else:
            self.sells += qty

    def record_order(self):
        self.orders_placed += 1

    def record_reject(self):
        self.orders_rejected += 1

    def record_arb(self):
        self.arb_trades += 1

    def update_position(self, positions):
        for sym, pos in positions.items():
            if sym == "cash":
                continue
            cur_max = self.max_position.get(sym, 0)
            self.max_position[sym] = max(cur_max, abs(pos))

    def snapshot(self, cash, positions):
        self.pnl_snapshots.append({
            "t": time.time() - self.round_start_time,
            "cash": cash,
        })

    def report(self, cash, positions):
        elapsed = time.time() - self.round_start_time
        pnl = cash - self.round_start_cash
        fill_rate = self.fills / max(self.orders_placed, 1)
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_sec": round(elapsed, 1),
            "pnl": pnl,
            "cash": cash,
            "fills": self.fills,
            "orders": self.orders_placed,
            "rejections": self.orders_rejected,
            "fill_rate": round(fill_rate, 3),
            "buys": self.buys,
            "sells": self.sells,
            "arb_trades": self.arb_trades,
            "max_positions": {k: v for k, v in self.max_position.items() if v > 0},
            "final_positions": {k: v for k, v in positions.items() if v != 0 and k != "cash"},
        }
        log.info(f"METRICS: PNL={pnl:+d} fills={self.fills} orders={self.orders_placed} "
                 f"fill_rate={fill_rate:.1%} arbs={self.arb_trades}")
        try:
            with open(self.path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass
        return entry

    def reset(self, cash):
        self.round_start_time = time.time()
        self.round_start_cash = cash
        self.fills = 0
        self.orders_placed = 0
        self.orders_rejected = 0
        self.buys = 0
        self.sells = 0
        self.max_position = {}
        self.pnl_snapshots = []
        self.arb_trades = 0


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIRMED PARAMETERS (Ed post #40)
# ═══════════════════════════════════════════════════════════════════════════════

# Stock A: fair_A = EPS_A * PE_A  (PE_A is constant, must calibrate from market)
A_PE = None  # Will be auto-calibrated: observe market_price / EPS after first earnings

# Stock C model:
#   PE_C = PE0 * exp(-gamma * (y - y0))
#   dB   = (B0/N) * (-D * dy + 0.5 * C_conv * dy^2)
#   fair_C = EPS_C * PE_C + lambda * dB
# NOTE: PE0 from Ed #40 is 14.0, but observed practice market PE ~546.
# The formula might use a scaled PE. We auto-calibrate PE0_C from first observation.
C_PE0    = None    # Will be auto-calibrated from market observation
C_GAMMA  = 2.0     # P/E sensitivity to yield (UNKNOWN — calibrate on practice)
C_B0_N   = 40.0    # B0/N combined constant
C_D      = 7.5     # duration
C_CONV   = 55.0    # convexity
C_LAMBDA = 0.65    # bond portfolio weight

# Yield model
Y0       = 0.045   # baseline yield (4.5%)
BETA_Y   = 0.001   # yield sensitivity to E[dr] in bps

# Risk-free rate (for put-call parity)
RISK_FREE = 0.05

# ═══════════════════════════════════════════════════════════════════════════════
# OPTION / INSTRUMENT CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

OPTION_STRIKES = [950, 1000, 1050]
CALL_SYMS = {K: f"B_C_{K}" for K in OPTION_STRIKES}
PUT_SYMS  = {K: f"B_P_{K}" for K in OPTION_STRIKES}
FED_SYMS  = ["R_CUT", "R_HOLD", "R_HIKE"]

# ═══════════════════════════════════════════════════════════════════════════════
# TRADING PARAMETERS (tune these!)
# ═══════════════════════════════════════════════════════════════════════════════

# Market making
MM_LEVELS       = 2        # number of quote levels per side (defensive: 2 levels, less resting exposure)
MM_LEVEL_STEP   = 2        # price increment between levels
MM_BASE_EDGE    = 4        # wider half-spread from fair value to avoid +26pt adverse selection
MM_SIZE         = 3        # small size per level to limit exposure
MM_FADE_FACTOR  = 0.5      # logarithmic inventory fade strength

# ETF arbitrage
ETF_SWAP_FEE    = 5        # flat fee per swap
ETF_ARB_EDGE    = 1        # min edge beyond swap fee to trigger arb (lowered 2→1 Cycle 21 for more captures)

# Options / PCP arbitrage
PCP_ARB_EDGE    = 1        # min parity violation to trigger (lowered 3→1 Cycle 21 for more arb captures)
BOX_ARB_EDGE    = 1        # min box spread violation to trigger (lowered 2→1 Cycle 21)
OPT_SIZE        = 1        # option order size (reduced from 2 to limit cascade fill exposure)

# Prediction market
FED_MM_EDGE     = 3        # half-spread for Fed market quotes
FED_MM_SIZE     = 2        # order size for Fed market (reduced from 5 in Cycle 12 to limit cascade exposure)

# Risk limits (from exchange rules)
MAX_ORDER_SIZE       = 40
MAX_OPEN_ORDERS      = 50
MAX_OUTSTANDING_VOL  = 120   # per symbol
MAX_ABS_POSITION     = 200   # per symbol

# Position limits (self-imposed — TIGHT to prevent accumulation)
SOFT_POS_LIMIT_STOCK = 30   # defensive: tighter to prevent adverse selection accumulation
SOFT_POS_LIMIT_ETF   = 15   # defensive: tighter ETF limit
SOFT_POS_LIMIT_OPT   = 20   # was 30
SOFT_POS_LIMIT_FED   = 20   # was 30 — tightened to prevent Fed symbol accumulation

# Symbols we actively market-make
MM_SYMBOLS = ["A", "C"]  # ETF MM removed — lost -29/fill from adverse selection

# Time to expiry for options (fraction of a year, approximate)
# Each round = 15 min, ~10 days at 90s each = 900s of sim time
# We'll treat T as small constant; refine if we can track ticks
OPT_T = 0.01


# ═══════════════════════════════════════════════════════════════════════════════
# BOT CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class Case1Bot(XChangeClient):

    def __init__(self, host: str, username: str, password: str):
        super().__init__(host, username, password)

        # ── Fair values ──
        self.fair = {}          # symbol → float fair value
        self.eps = {}           # asset → latest EPS  (keyed "A" or "C")

        # ── PE calibration ──
        self.a_pe = A_PE        # None until calibrated from first earnings + market price
        self.c_pe0 = C_PE0      # None until calibrated
        self.pe_calibrated_a = False
        self.pe_calibrated_c = False

        # ── Fed / yield state ──
        self.q_hike = 1/3
        self.q_hold = 1/3
        self.q_cut  = 1/3
        self.yield_y = Y0
        self.pe_c    = self.c_pe0 if self.c_pe0 else 14.0
        self.fed_initialized = False  # whether we've read market priors

        # ── Petition state (Fed proxy) ──
        self.petition_cumulative = {}  # asset → cumulative signatures

        # ── Tracking ──
        self.pending_cancels = set()   # order IDs we've requested cancel for
        self.requote_needed  = set()   # symbols that need requoting

        # ── Metrics ──
        self.metrics = MetricsTracker()

        # ── Round / timing ──
        self.tick_count = 0
        self.started = False

        # ── Per-symbol requote throttle ──
        self.last_requote_time = {}  # symbol → timestamp of last requote

        # ── Startup cancel ──
        self.startup_cancel_done = False

        # ── News mode state ──
        self.news_positions = {}   # symbol → (direction, size, entry_time) for 15s exit
        self.news_mode_until = 0   # timestamp when news mode ends

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS: Order book reading
    # ─────────────────────────────────────────────────────────────────────────

    def best_bid(self, symbol: str):
        """Return (price, qty) of best bid (non-zero qty only), or (None, 0)."""
        book = self.order_books.get(symbol)
        if book and book.bids:
            valid = [(p, q) for p, q in book.bids.items() if q > 0]
            if valid:
                px, qty = max(valid, key=lambda x: x[0])
                return px, qty
        return None, 0

    def best_ask(self, symbol: str):
        """Return (price, qty) of best ask (non-zero qty only), or (None, 0)."""
        book = self.order_books.get(symbol)
        if book and book.asks:
            valid = [(p, q) for p, q in book.asks.items() if q > 0]
            if valid:
                px, qty = min(valid, key=lambda x: x[0])
                return px, qty
        return None, 0

    def mid_price(self, symbol: str):
        """Return mid price as float, or None."""
        bb, _ = self.best_bid(symbol)
        ba, _ = self.best_ask(symbol)
        if bb is not None and ba is not None:
            return (bb + ba) / 2.0
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS: Risk checks
    # ─────────────────────────────────────────────────────────────────────────

    def count_open_orders(self):
        return len(self.open_orders)

    def outstanding_volume(self, symbol: str):
        """Sum of unfilled qty for open orders on this symbol."""
        vol = 0
        for oid, info in self.open_orders.items():
            if info[0].symbol == symbol:
                vol += info[1]  # remaining qty
        return vol

    def can_place(self, symbol: str, qty: int) -> bool:
        """Check exchange risk limits before placing an order."""
        if qty > MAX_ORDER_SIZE:
            return False
        if self.count_open_orders() >= MAX_OPEN_ORDERS - 2:
            return False
        if self.outstanding_volume(symbol) + qty > MAX_OUTSTANDING_VOL - 5:
            return False
        return True

    def get_soft_limit(self, symbol: str) -> int:
        """Return the soft position limit for a symbol."""
        if symbol == "ETF":
            return SOFT_POS_LIMIT_ETF
        elif symbol.startswith("B_"):
            return SOFT_POS_LIMIT_OPT
        elif symbol.startswith("R_"):
            return SOFT_POS_LIMIT_FED
        else:
            return SOFT_POS_LIMIT_STOCK

    def position_room(self, symbol: str, side: str) -> int:
        """How many more shares can we buy/sell before hitting SOFT limit."""
        pos = self.positions.get(symbol, 0)
        soft = self.get_soft_limit(symbol)
        if side == "buy":
            return max(0, soft - pos)
        else:
            return max(0, soft + pos)

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS: Safe order placement
    # ─────────────────────────────────────────────────────────────────────────

    async def safe_place(self, symbol: str, qty: int, side: str, px: int):
        """Place a limit order with risk checks. Returns order_id or None."""
        if qty <= 0 or px <= 0:
            return None
        if not self.can_place(symbol, qty):
            return None
        # Clamp qty to position room
        room = self.position_room(symbol, side)
        qty = min(qty, room)
        if qty <= 0:
            return None
        try:
            self.metrics.record_order()
            oid = await self.place_order(symbol, qty, side, px)
            return oid
        except Exception as e:
            log.warning(f"Order failed {side} {qty}x {symbol}@{px}: {e}")
            return None

    async def cancel_all_symbol(self, symbol: str):
        """Cancel all our open orders for a given symbol."""
        to_cancel = []
        for oid, info in list(self.open_orders.items()):
            if info[0].symbol == symbol and oid not in self.pending_cancels:
                to_cancel.append(oid)
        for oid in to_cancel:
            self.pending_cancels.add(oid)
            try:
                await self.cancel_order(oid)
            except Exception as e:
                log.warning(f"Cancel failed for {oid}: {e}")
                self.pending_cancels.discard(oid)

    # ─────────────────────────────────────────────────────────────────────────
    # FAIR VALUE MODELS
    # ─────────────────────────────────────────────────────────────────────────

    def calibrate_pe_a(self):
        """Auto-calibrate PE_A from market mid / EPS. Recalibrates every time earnings arrive."""
        eps_a = self.eps.get("A")
        mid_a = self.mid_price("A")
        if eps_a and eps_a > 0 and mid_a and mid_a > 0:
            self.a_pe = mid_a / eps_a
            self.pe_calibrated_a = True
            log.info(f"CALIBRATED A_PE = {self.a_pe:.1f} (mid={mid_a}, eps={eps_a:.4f})")

    def calibrate_pe_c(self):
        """Auto-calibrate PE0_C from market mid / EPS. Recalibrates every time earnings arrive."""
        eps_c = self.eps.get("C")
        mid_c = self.mid_price("C")
        if eps_c and eps_c > 0 and mid_c and mid_c > 0:
            # At baseline (dy=0): fair_C = eps_c * PE0_C + 0 (bond effect is 0)
            # So PE0_C ≈ mid_c / eps_c
            self.c_pe0 = mid_c / eps_c
            self.pe_c = self.c_pe0  # reset current PE to calibrated baseline
            self.pe_calibrated_c = True
            log.info(f"CALIBRATED C_PE0 = {self.c_pe0:.1f} (mid={mid_c}, eps={eps_c:.4f})")

    def compute_fair_A(self):
        """fair_A = EPS_A * PE_A (constant PE). Falls back to market mid."""
        eps_a = self.eps.get("A")
        if eps_a is not None and self.a_pe is not None:
            self.fair["A"] = eps_a * self.a_pe
            return
        # Fallback: use market mid when we lack earnings or PE calibration
        mid = self.mid_price("A")
        if mid:
            self.fair["A"] = mid

    def compute_yield(self):
        """
        E[dr] = 25 * q_hike - 25 * q_cut  (in bps)
        y = y0 + beta_y * E[dr]
        PE_C = PE0 * exp(-gamma * (y - y0))
        """
        e_dr = 25.0 * self.q_hike - 25.0 * self.q_cut
        self.yield_y = Y0 + BETA_Y * e_dr
        dy = self.yield_y - Y0
        if self.c_pe0 is not None:
            self.pe_c = self.c_pe0 * math.exp(-C_GAMMA * dy)
        # else: pe_c stays at last known value

    def compute_fair_C(self):
        """
        dB = (B0/N) * (-D * dy + 0.5 * C_conv * dy^2)
        fair_C = EPS_C * PE_C + lambda * dB
        Falls back to market mid.
        """
        eps_c = self.eps.get("C")
        if eps_c is not None and self.c_pe0 is not None:
            dy = self.yield_y - Y0
            d_bond = C_B0_N * (-C_D * dy + 0.5 * C_CONV * dy ** 2)
            self.fair["C"] = eps_c * self.pe_c + C_LAMBDA * d_bond
            return
        # Fallback: use market mid when we lack earnings or PE calibration
        mid = self.mid_price("C")
        if mid:
            self.fair["C"] = mid

    def compute_implied_B(self):
        """
        From put-call parity: S = C - P + K * e^(-rT)
        Use option mid prices to get implied B price.
        Average across all strikes with valid data.
        """
        implied = []
        for K in OPTION_STRIKES:
            call_mid = self.mid_price(CALL_SYMS[K])
            put_mid = self.mid_price(PUT_SYMS[K])
            if call_mid is not None and put_mid is not None:
                s_implied = call_mid - put_mid + K * math.exp(-RISK_FREE * OPT_T)
                implied.append(s_implied)
        if implied:
            self.fair["B"] = sum(implied) / len(implied)

    def compute_fair_ETF(self):
        """ETF NAV = A + B + C (one share each)."""
        a = self.fair.get("A") or self.mid_price("A")
        b = self.fair.get("B") or self.mid_price("B")
        c = self.fair.get("C") or self.mid_price("C")
        if a is not None and b is not None and c is not None:
            self.fair["ETF"] = a + b + c

    def init_fed_from_market(self):
        """
        On first opportunity, initialize Fed probabilities from market prices.
        This replaces our naive 1/3 priors with actual market consensus.
        """
        r_hike_mid = self.mid_price("R_HIKE")
        r_hold_mid = self.mid_price("R_HOLD")
        r_cut_mid  = self.mid_price("R_CUT")

        if r_hike_mid is not None and r_hold_mid is not None and r_cut_mid is not None:
            total = r_hike_mid + r_hold_mid + r_cut_mid
            if total > 0:
                self.q_hike = r_hike_mid / total
                self.q_hold = r_hold_mid / total
                self.q_cut  = r_cut_mid / total
                self.fed_initialized = True
                log.info(f"FED INIT from market: hike={self.q_hike:.3f} hold={self.q_hold:.3f} cut={self.q_cut:.3f}")

    def update_fed_from_market(self):
        """
        Read Fed prediction market mid prices to supplement our model.
        Blend market prices with our model estimate.
        """
        r_hike_mid = self.mid_price("R_HIKE")
        r_hold_mid = self.mid_price("R_HOLD")
        r_cut_mid  = self.mid_price("R_CUT")

        if r_hike_mid is not None and r_hold_mid is not None and r_cut_mid is not None:
            total = r_hike_mid + r_hold_mid + r_cut_mid
            if total > 0:
                # Blend: 60% market, 40% our model
                mkt_hike = r_hike_mid / total
                mkt_hold = r_hold_mid / total
                mkt_cut  = r_cut_mid / total
                self.q_hike = 0.6 * mkt_hike + 0.4 * self.q_hike
                self.q_hold = 0.6 * mkt_hold + 0.4 * self.q_hold
                self.q_cut  = 0.6 * mkt_cut  + 0.4 * self.q_cut
                # Normalize
                total_q = self.q_hike + self.q_hold + self.q_cut
                if total_q > 0:
                    self.q_hike /= total_q
                    self.q_hold /= total_q
                    self.q_cut  /= total_q

    def recompute_all_fairs(self):
        """Recompute all fair values from current state."""
        # Auto-calibrate PEs from market data if not done yet
        self.calibrate_pe_a()
        self.calibrate_pe_c()
        # Initialize Fed priors from market if not done yet
        if not self.fed_initialized:
            self.init_fed_from_market()

        self.compute_fair_A()
        self.compute_yield()
        self.compute_fair_C()
        self.compute_implied_B()
        self.compute_fair_ETF()

    # ─────────────────────────────────────────────────────────────────────────
    # MARKET MAKING
    # ─────────────────────────────────────────────────────────────────────────

    def inventory_fade(self, symbol: str) -> float:
        """
        Logarithmic inventory fade: pushes quotes away from inventory direction.
        fade = -f * sign(pos) * log2(1 + |pos|)
        """
        pos = self.positions.get(symbol, 0)
        if pos == 0:
            return 0.0
        sign = 1 if pos > 0 else -1
        return -MM_FADE_FACTOR * sign * math.log2(1 + abs(pos))


    async def requote_mm(self, symbol: str):
        """
        Simple defensive market making:
        1. Cancel all existing orders
        2. Compute fade
        3. One-sided position gate
        4. Post MM_LEVELS levels around fair + fade with fixed MM_BASE_EDGE
        5. Emergency unwind at 60% threshold
        """
        # Per-symbol requote throttle: min 50ms between requotes on same symbol.
        now = time.time()
        if now - self.last_requote_time.get(symbol, 0) < 0.05:
            return
        self.last_requote_time[symbol] = now

        fair = self.fair.get(symbol)
        if fair is None:
            return

        # Cancel existing orders first
        await self.cancel_all_symbol(symbol)

        fade = self.inventory_fade(symbol)
        adjusted_fair = fair + fade
        pos = self.positions.get(symbol, 0)

        soft_limit = self.get_soft_limit(symbol)

        # One-sided position gate: allow reducing side, block accumulating side
        allow_buy  = pos < soft_limit
        allow_sell = pos > -soft_limit

        # Multi-level quotes around adjusted fair with fixed edge
        for level in range(MM_LEVELS):
            offset = MM_BASE_EDGE + level * MM_LEVEL_STEP
            size = max(1, MM_SIZE - level)

            bid_px = int(round(adjusted_fair - offset))
            if allow_buy and bid_px > 0:
                await self.safe_place(symbol, size, "buy", bid_px)

            ask_px = int(round(adjusted_fair + offset))
            if allow_sell and ask_px > 0:
                await self.safe_place(symbol, size, "sell", ask_px)

        # Emergency unwind at 60% of soft limit: cross the spread for guaranteed fill
        emergency_threshold = 0.6 * soft_limit
        if abs(pos) > emergency_threshold:
            bb, _ = self.best_bid(symbol)
            ba, _ = self.best_ask(symbol)
            mid = self.mid_price(symbol)
            if mid:
                unwind_size = min(5, int(abs(pos) - emergency_threshold) + 5)
                unwind_size = min(unwind_size, abs(pos))
                if pos > emergency_threshold:
                    sell_px = int(bb) if bb is not None else int(mid - 1)
                    await self.safe_place(symbol, unwind_size, "sell", sell_px)
                elif pos < -emergency_threshold:
                    buy_px = int(ba) if ba is not None else int(mid + 1)
                    await self.safe_place(symbol, unwind_size, "buy", buy_px)

    # ─────────────────────────────────────────────────────────────────────────
    # FED PREDICTION MARKET QUOTING
    # ─────────────────────────────────────────────────────────────────────────

    async def requote_fed(self):
        """Quote the Fed prediction market based on our probability model."""
        now = time.time()
        for sym, q in [("R_HIKE", self.q_hike), ("R_HOLD", self.q_hold), ("R_CUT", self.q_cut)]:
            # ── Per-symbol throttle (same 50ms pattern as requote_mm) ──
            if now - self.last_requote_time.get(sym, 0) < 0.05:
                continue
            self.last_requote_time[sym] = now

            await self.cancel_all_symbol(sym)

            mid = self.mid_price(sym)
            if mid is not None and mid > 0:
                # Infer scale from existing prices
                scale = mid / q if q > 0.1 else mid / 0.33
                fair_px = int(round(q * scale))
            else:
                # Default: assume prices are 0-100
                fair_px = int(round(q * 100))

            if fair_px <= 0:
                continue

            pos = self.positions.get(sym, 0)
            emergency_threshold_fed = 0.7 * SOFT_POS_LIMIT_FED  # ~14

            # ── Emergency unwind for Fed symbols at 70% of soft limit ──
            if abs(pos) >= emergency_threshold_fed:
                mid = self.mid_price(sym)
                if mid:
                    unwind_qty = min(FED_MM_SIZE, abs(pos))
                    bb, _ = self.best_bid(sym)
                    ba, _ = self.best_ask(sym)
                    if pos > emergency_threshold_fed:
                        sell_px = int(bb) if bb is not None else int(mid - 1)
                        log.warning(f"FED EMERGENCY UNWIND: {sym} pos={pos} >= {emergency_threshold_fed:.0f}, selling {unwind_qty} @ {sell_px}")
                        await self.safe_place(sym, unwind_qty, "sell", sell_px)
                    elif pos < -emergency_threshold_fed:
                        buy_px = int(ba) if ba is not None else int(mid + 1)
                        log.warning(f"FED EMERGENCY UNWIND: {sym} pos={pos} <= -{emergency_threshold_fed:.0f}, buying {unwind_qty} @ {buy_px}")
                        await self.safe_place(sym, unwind_qty, "buy", buy_px)
                continue  # skip normal MM quoting when in emergency mode

            bid_px = max(1, fair_px - FED_MM_EDGE)
            ask_px = fair_px + FED_MM_EDGE

            if pos < SOFT_POS_LIMIT_FED and bid_px > 0:
                await self.safe_place(sym, FED_MM_SIZE, "buy", bid_px)
            if pos > -SOFT_POS_LIMIT_FED and ask_px > 0:
                await self.safe_place(sym, FED_MM_SIZE, "sell", ask_px)

    # ─────────────────────────────────────────────────────────────────────────
    # ETF ARBITRAGE (via swaps)
    # ─────────────────────────────────────────────────────────────────────────

    async def check_etf_arb(self):
        """
        Compare ETF market price vs NAV.
        Use swaps for clean execution (no leg risk).
        """
        nav = self.fair.get("ETF")
        etf_mid = self.mid_price("ETF")
        if nav is None or etf_mid is None:
            return

        edge = etf_mid - nav  # positive = ETF overpriced

        threshold = ETF_SWAP_FEE + ETF_ARB_EDGE

        if edge > threshold:
            # ETF overpriced: sell ETF, then redeem (fromETF)
            bb, _ = self.best_bid("ETF")
            if bb is not None and bb - nav > ETF_SWAP_FEE:
                qty = min(5, self.position_room("ETF", "sell"))
                if qty > 0:
                    await self.safe_place("ETF", qty, "sell", bb)
                    # Try swap if we hold ETF
                    etf_pos = self.positions.get("ETF", 0)
                    if etf_pos > 0:
                        swap_qty = min(etf_pos, 3)
                        try:
                            await self.place_swap_order("fromETF", swap_qty)
                        except Exception as e:
                            log.warning(f"Swap fromETF failed: {e}")

        elif edge < -threshold:
            # ETF underpriced: buy ETF, then create (toETF) if we hold components
            ba, _ = self.best_ask("ETF")
            if ba is not None and nav - ba > ETF_SWAP_FEE:
                qty = min(5, self.position_room("ETF", "buy"))
                if qty > 0:
                    await self.safe_place("ETF", qty, "buy", ba)
                    # Try create swap if we hold all components
                    a_pos = self.positions.get("A", 0)
                    b_pos = self.positions.get("B", 0)
                    c_pos = self.positions.get("C", 0)
                    can_swap = min(a_pos, b_pos, c_pos)
                    if can_swap > 0:
                        swap_qty = min(can_swap, 3)
                        try:
                            await self.place_swap_order("toETF", swap_qty)
                        except Exception as e:
                            log.warning(f"Swap toETF failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # PUT-CALL PARITY ARBITRAGE
    # ─────────────────────────────────────────────────────────────────────────

    async def check_pcp_arb(self):
        """
        For each strike K with both call and put books:
          PCP: C - P = S - K * e^(-rT)
        Compare executable prices (bid/ask) to avoid crossing on stale mids.
        Use market mid of B (not PCP-derived fair) as reference to avoid circularity.
        """
        # Use market mid of B directly to avoid circularity with PCP-implied fair
        s_mid = self.mid_price("B")
        if s_mid is None:
            return

        for K in OPTION_STRIKES:
            call_sym = CALL_SYMS[K]
            put_sym = PUT_SYMS[K]

            call_bb, _ = self.best_bid(call_sym)
            call_ba, _ = self.best_ask(call_sym)
            put_bb, _ = self.best_bid(put_sym)
            put_ba, _ = self.best_ask(put_sym)

            if any(v is None for v in [call_bb, call_ba, put_bb, put_ba]):
                continue

            pcp_rhs = s_mid - K * math.exp(-RISK_FREE * OPT_T)

            # Check: call_bid - put_ask vs parity (sell call, buy put)
            sell_call_edge = call_bb - put_ba - pcp_rhs
            if sell_call_edge > PCP_ARB_EDGE:
                await self.safe_place(call_sym, OPT_SIZE, "sell", call_bb)
                await self.safe_place(put_sym, OPT_SIZE, "buy", put_ba)
                self.metrics.record_arb()
                log.info(f"PCP ARB: sell {call_sym}@{call_bb} buy {put_sym}@{put_ba} edge={sell_call_edge:.1f}")

            # Check: put_bid - call_ask vs -parity (sell put, buy call)
            sell_put_edge = put_bb - call_ba + pcp_rhs
            if sell_put_edge > PCP_ARB_EDGE:
                await self.safe_place(call_sym, OPT_SIZE, "buy", call_ba)
                await self.safe_place(put_sym, OPT_SIZE, "sell", put_bb)
                self.metrics.record_arb()
                log.info(f"PCP ARB: buy {call_sym}@{call_ba} sell {put_sym}@{put_bb} edge={sell_put_edge:.1f}")

    # ─────────────────────────────────────────────────────────────────────────
    # NEWS HANDLING
    # ─────────────────────────────────────────────────────────────────────────

    async def handle_earnings(self, asset: str, value: float):
        """Process earnings announcement with aggressive news trading."""
        # Capture old mid before updating EPS
        old_mid = self.mid_price(asset)

        # Compute new fair using EXISTING PE (before recalibration!) + NEW EPS
        # Critical: if we recalibrate PE with new EPS against stale mid,
        # the edge collapses to zero (PE = stale_mid/new_eps, fair = new_eps*PE = stale_mid)
        if asset == "A" and self.a_pe is not None:
            new_fair = value * self.a_pe
        elif asset == "C" and self.pe_c is not None:
            dy = self.yield_y - Y0
            d_bond = C_B0_N * (-C_D * dy + 0.5 * C_CONV * dy ** 2)
            new_fair = value * self.pe_c + C_LAMBDA * d_bond
        else:
            new_fair = None

        self.eps[asset] = value
        log.info(f"EARNINGS: {asset} EPS = {value}")

        # Cancel ALL orders on ALL symbols immediately (stop being dumb money)
        for sym in list(self.order_books.keys()):
            await self.cancel_all_symbol(sym)

        # Update fair values (PE will recalibrate from market on next book update)
        if new_fair is not None:
            self.fair[asset] = new_fair
        self.compute_fair_ETF()

        # Suppress MM for 2 seconds after news
        self.news_mode_until = time.time() + 2

        # Aggressive news trade if edge is large enough
        if old_mid is not None and new_fair is not None:
            edge = new_fair - old_mid
            log.info(f"EARNINGS EDGE: {asset} old_mid={old_mid:.1f} new_fair={new_fair:.1f} edge={edge:+.1f}")

            if abs(edge) > 3:
                now = time.time()
                if edge > 0:
                    # Fair went up: buy at best_ask (take stale offer)
                    ba, _ = self.best_ask(asset)
                    if ba:
                        await self.safe_place(asset, 20, "buy", ba)
                        self.news_positions[asset] = ("BUY", 20, now)
                        log.info(f"NEWS TRADE: BUY {asset} x20 @ {ba} (edge={edge:+.1f})")
                else:
                    # Fair went down: sell at best_bid (take stale bid)
                    bb, _ = self.best_bid(asset)
                    if bb:
                        await self.safe_place(asset, 20, "sell", bb)
                        self.news_positions[asset] = ("SELL", 20, now)
                        log.info(f"NEWS TRADE: SELL {asset} x20 @ {bb} (edge={edge:+.1f})")

                # If A or C earnings and edge > 10, also trade ETF in same direction
                if abs(edge) > 10:
                    if edge > 0:
                        ba_etf, _ = self.best_ask("ETF")
                        if ba_etf:
                            await self.safe_place("ETF", 5, "buy", ba_etf)
                            self.news_positions["ETF"] = ("BUY", 5, now)
                            log.info(f"NEWS TRADE: BUY ETF x5 @ {ba_etf} ({asset} edge={edge:+.1f})")
                    else:
                        bb_etf, _ = self.best_bid("ETF")
                        if bb_etf:
                            await self.safe_place("ETF", 5, "sell", bb_etf)
                            self.news_positions["ETF"] = ("SELL", 5, now)
                            log.info(f"NEWS TRADE: SELL ETF x5 @ {bb_etf} ({asset} edge={edge:+.1f})")

        # Flag for requote after news mode expires
        if asset == "A":
            self.requote_needed.add("A")
            self.requote_needed.add("ETF")
        elif asset == "C":
            self.requote_needed.add("C")
            self.requote_needed.add("ETF")

    def handle_cpi(self, forecast: float, actual: float):
        """
        CPI structured news: actual vs forecast.
        Actual > Forecast → inflation hot → shift toward hike.
        Actual < Forecast → inflation low → shift toward cut.
        """
        surprise = actual - forecast
        log.info(f"CPI: actual={actual} forecast={forecast} surprise={surprise:+.4f}")

        # Bayesian-ish shift: magnitude proportional to surprise
        shift_magnitude = min(abs(surprise) * 200, 0.25)  # cap at 25% shift

        if surprise > 0:
            # Inflationary: shift from cut → hike
            transfer = min(shift_magnitude, self.q_cut * 0.5)
            self.q_cut -= transfer
            self.q_hike += transfer
        else:
            # Deflationary: shift from hike → cut
            transfer = min(shift_magnitude, self.q_hike * 0.5)
            self.q_hike -= transfer
            self.q_cut += transfer

        # Normalize
        total = self.q_hike + self.q_hold + self.q_cut
        if total > 0:
            self.q_hike /= total
            self.q_hold /= total
            self.q_cut /= total

        self.recompute_all_fairs()
        self.requote_needed.add("C")
        self.requote_needed.add("ETF")
        self.requote_needed.update(FED_SYMS)

    def handle_petition(self, asset: str, new_sigs: int, cumulative: int):
        """
        Process petition event.
        Petitions may map to Fed probability support.
        More signatures for an outcome → more probability mass there.
        """
        self.petition_cumulative[asset] = cumulative
        log.info(f"PETITION: {asset} +{new_sigs} sigs (total: {cumulative})")

        # Map petition cumulative to probability shifts
        total_sigs = sum(self.petition_cumulative.values())
        if total_sigs > 0 and len(self.petition_cumulative) >= 2:
            # Blend petition signal with current probs (20% weight to petitions)
            for key, cum in self.petition_cumulative.items():
                pct = cum / total_sigs
                if "HIKE" in key.upper() or "hike" in key:
                    self.q_hike = 0.8 * self.q_hike + 0.2 * pct
                elif "CUT" in key.upper() or "cut" in key:
                    self.q_cut = 0.8 * self.q_cut + 0.2 * pct
                elif "HOLD" in key.upper() or "hold" in key:
                    self.q_hold = 0.8 * self.q_hold + 0.2 * pct

            # Normalize
            total = self.q_hike + self.q_hold + self.q_cut
            if total > 0:
                self.q_hike /= total
                self.q_hold /= total
                self.q_cut /= total

            self.recompute_all_fairs()
            self.requote_needed.add("C")
            self.requote_needed.add("ETF")

    def handle_unstructured_news(self, content: str):
        """
        Parse unstructured news for Fed-relevant keywords.
        Shift Fed probabilities based on sentiment.
        """
        text = content.lower()
        log.info(f"NEWS: {content[:80]}")

        hawk_words = ['inflation', 'hike', 'hawkish', 'overheat', 'hot',
                       'tighten', 'restrictive', 'surge', 'strong']
        dove_words = ['recession', 'cut', 'dovish', 'slowdown', 'weak',
                       'cool', 'ease', 'loosen', 'unemployment', 'soft']

        hawk = sum(1 for w in hawk_words if w in text)
        dove = sum(1 for w in dove_words if w in text)
        net = hawk - dove

        if net != 0:
            # Each keyword hit shifts ~5% probability
            shift = min(abs(net) * 0.05, 0.25)
            if net > 0:
                transfer = min(shift, self.q_cut)
                self.q_cut -= transfer
                self.q_hike += transfer
            else:
                transfer = min(shift, self.q_hike)
                self.q_hike -= transfer
                self.q_cut += transfer

            # Normalize
            total = self.q_hike + self.q_hold + self.q_cut
            if total > 0:
                self.q_hike /= total
                self.q_hold /= total
                self.q_cut /= total

            self.recompute_all_fairs()
            self.requote_needed.add("C")
            self.requote_needed.add("ETF")

    # ─────────────────────────────────────────────────────────────────────────
    # XChangeClient CALLBACK OVERRIDES
    # ─────────────────────────────────────────────────────────────────────────

    async def bot_handle_book_update(self, symbol: str) -> None:
        """Called on every book snapshot and incremental update."""

        # Startup cancel: clear any stale orders from a previous session
        if not self.startup_cancel_done:
            for sym in list(self.order_books.keys()):
                await self.cancel_all_symbol(sym)
            self.startup_cancel_done = True
            log.info("STARTUP: Cancelled all stale orders")
            return

        self.tick_count += 1

        # Recompute fairs (cheap — do it every update)
        self.recompute_all_fairs()

        # 15-second news position exit check
        now = time.time()
        for sym in list(self.news_positions.keys()):
            direction, size, entry_time = self.news_positions[sym]
            if now - entry_time >= 15:
                if direction == "BUY":
                    bb, _ = self.best_bid(sym)
                    if bb:
                        await self.safe_place(sym, size, "sell", bb)
                else:
                    ba, _ = self.best_ask(sym)
                    if ba:
                        await self.safe_place(sym, size, "buy", ba)
                del self.news_positions[sym]
                log.info(f"NEWS EXIT: {sym} {direction} {size} after 15s")

        # Suppress all MM during news reaction window
        if time.time() < self.news_mode_until:
            return

        # Requote the symbol that changed (and any flagged symbols)
        symbols_to_requote = {symbol} | self.requote_needed
        self.requote_needed.clear()

        for sym in symbols_to_requote:
            if sym in MM_SYMBOLS:
                await self.requote_mm(sym)

        # Check arb opportunities
        await self.check_etf_arb()
        if self.tick_count % 2 == 0:
            await self.check_pcp_arb()
        if self.tick_count % 10 == 0:
            await self.requote_fed()
        # Periodically blend in market fed prices
        if self.tick_count % 20 == 0:
            self.update_fed_from_market()

        # Periodic status log + metrics snapshot
        if self.tick_count % 200 == 0:
            cash = self.positions.get('cash', 0)
            pos_str = {k: v for k, v in self.positions.items() if v != 0 and k != 'cash'}
            fair_str = {k: f"{v:.0f}" for k, v in self.fair.items()}
            self.metrics.snapshot(cash, self.positions)
            log.info(f"STATUS tick={self.tick_count} pos={pos_str} fair={fair_str} "
                     f"cash={cash} "
                     f"fed=({self.q_hike:.2f}/{self.q_hold:.2f}/{self.q_cut:.2f})")
        # Metrics report every 1000 ticks
        if self.tick_count % 1000 == 0:
            self.metrics.report(self.positions.get('cash', 0), self.positions)

    async def bot_handle_trade_msg(self, symbol: str, price: int, qty: int):
        """Called when any trade occurs on the exchange (not just ours)."""
        pass

    async def bot_handle_order_fill(self, order_id: str, qty: int, price: int):
        """Called when one of OUR orders gets filled."""
        info = self.open_orders.get(order_id)
        if info:
            sym = info[0].symbol
            is_buy = (info[0].side == 1)
            side = "BUY" if is_buy else "SELL"
            self.metrics.record_fill(sym, side, qty, price)
            self.metrics.update_position(self.positions)

            delta = qty if is_buy else -qty
            pos = self.positions.get(sym, 0) + delta
            log.info(f"FILL: {side} {qty}x {sym} @ {price}  |  pos={pos}")

            # HARD STOP ON FILL: if position just crossed hard stop threshold,
            # cancel ALL remaining orders on this symbol (both sides).
            # Fed symbols use 70% threshold (more aggressive) because they can cascade faster.
            soft_limit = self.get_soft_limit(sym)
            if sym.startswith("R_"):
                # Fed symbols: hard stop at 70% of soft limit (~14 for SOFT_POS_LIMIT_FED=20)
                hard_stop = 0.7 * soft_limit
            else:
                hard_stop = 0.8 * soft_limit
            if abs(pos) >= hard_stop:
                log.warning(f"HARD STOP HIT on fill: {sym} pos={pos} (threshold={hard_stop:.0f}) — cancelling all {sym} orders")
                await self.cancel_all_symbol(sym)

    async def bot_handle_order_rejected(self, order_id: str, reason: str) -> None:
        """Called when our order is rejected."""
        self.metrics.record_reject()
        log.warning(f"REJECTED order {order_id}: {reason}")

    async def bot_handle_cancel_response(self, order_id: str, success: bool, error) -> None:
        """Called when cancel request completes."""
        self.pending_cancels.discard(order_id)
        if not success:
            log.warning(f"Cancel failed for {order_id}: {error}")

    async def bot_handle_swap_response(self, swap: str, qty: int, success: bool):
        """Called when swap completes."""
        if success:
            log.info(f"SWAP OK: {swap} x{qty}")
        else:
            log.warning(f"SWAP FAILED: {swap} x{qty}")

    async def bot_handle_news(self, news_release):
        """
        Called when news arrives.

        news_release format (dict):
          {
            'tick': int,
            'kind': 'structured' | 'unstructured',
            'symbol': str or None,
            'new_data': {
              # earnings: {'value': float, 'asset': str, 'structured_subtype': 'earnings'}
              # cpi_print: {'forecast': float, 'actual': float, 'structured_subtype': 'cpi_print'}
              # petition: {'new_signatures': int, 'cumulative': int, 'asset': str, 'structured_subtype': 'petition'}
              # unstructured: {'content': str}
            }
          }
        """
        data = news_release.get('new_data', {})
        kind = news_release.get('kind', '')

        if kind == 'structured':
            # Cancel all orders immediately when structured news arrives
            for sym in list(self.order_books.keys()):
                await self.cancel_all_symbol(sym)
            log.info("NEWS: Cancelled all orders for news event")

            subtype = data.get('structured_subtype', '')
            if subtype == 'earnings':
                await self.handle_earnings(data['asset'], data['value'])
            elif subtype == 'cpi_print':
                self.handle_cpi(data['forecast'], data['actual'])
            elif subtype == 'petition':
                self.handle_petition(
                    data.get('asset', ''),
                    data.get('new_signatures', 0),
                    data.get('cumulative', 0)
                )
        elif kind == 'unstructured':
            content = data.get('content', '')
            if content:
                self.handle_unstructured_news(content)

        # After any news, requote everything
        for sym in MM_SYMBOLS:
            self.requote_needed.add(sym)

    async def bot_handle_market_resolved(self, market_id: str, winning_symbol: str, tick: int):
        """Called when prediction market resolves — signals round end."""
        log.info(f"MARKET RESOLVED: {market_id} winner={winning_symbol} tick={tick}")
        # Report round metrics and reset for new round
        self.metrics.report(self.positions.get('cash', 0), self.positions)
        self.metrics.reset(self.positions.get('cash', 0))
        # Reset PE calibration for new round (prices may change)
        self.pe_calibrated_a = False
        self.pe_calibrated_c = False
        self.a_pe = None
        self.c_pe0 = None
        self.fed_initialized = False
        self.eps.clear()
        self.fair.clear()
        self.tick_count = 0

    async def bot_handle_settlement_payout(self, user: str, market_id: str, amount: int, tick: int):
        """Called when settlement payout occurs."""
        log.info(f"SETTLEMENT: user={user} market={market_id} amount={amount} tick={tick}")

    # ─────────────────────────────────────────────────────────────────────────
    # STARTUP
    # ─────────────────────────────────────────────────────────────────────────

    async def start(self):
        """Main entry point — connect and run forever."""
        log.info(f"Starting Case1Bot on {self.host} as {self.username}")
        log.info(f"Parameters: PE0_C={C_PE0}, D={C_D}, C={C_CONV}, "
                 f"lambda={C_LAMBDA}, y0={Y0}, B0/N={C_B0_N}")
        log.info(f"Symbols: MM={MM_SYMBOLS}, Options={list(CALL_SYMS.values())+list(PUT_SYMS.values())}")
        log.info(f"Fed: {FED_SYMS}")

        await self.connect()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 bot.py <host:port> <username> <password>")
        print("Example: python3 bot.py 34.197.188.76:3333 ucla_calberkeley yourpassword")
        sys.exit(1)

    host = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    bot = Case1Bot(host, username, password)
    asyncio.run(bot.start())


if __name__ == "__main__":
    main()
