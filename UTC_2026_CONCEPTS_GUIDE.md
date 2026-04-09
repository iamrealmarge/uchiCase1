# UTC 2026 — Financial Concepts Guide (Everything You Need to Know for Case 1)

**For team ucla_calberkeley — written plain-English, then math.**

---

## TABLE OF CONTENTS
1. Stocks & What Drives Prices
2. P/E Ratio (and why Stock A is simple)
3. Earnings Per Share (EPS)
4. Bonds, Yields, and Interest Rates
5. The Federal Reserve & Prediction Markets
6. How Stock C Works (the hard one)
7. Options — Calls and Puts
8. European vs American Options
9. Single Expiry (what this means for us)
10. Put-Call Parity (free money detector)
11. Box Spreads (another free money detector)
12. ETFs — What They Are
13. ETF Creation & Redemption (Swaps)
14. ETF Arbitrage
15. Market Making — The Core Job
16. Bid, Ask, Spread, Mid
17. Order Books & Limit Orders
18. Inventory & Why It's Dangerous
19. How Scoring Works
20. Glossary

---

## 1. STOCKS & WHAT DRIVES PRICES

A stock is a tiny piece of ownership in a company. If a company is worth $1 billion and has 1 million shares, each share is "worth" $1,000.

But nobody knows exactly what a company is worth. The stock *price* is what people are *willing to pay* right now. Prices move when new information arrives — earnings reports, news headlines, interest rate changes — anything that changes people's beliefs about the company's future profits.

In our competition, we have three stocks (A, B, C) and each moves for different reasons.

---

## 2. P/E RATIO

**P/E = Price / Earnings Per Share**

This is the most common way to value a stock. It answers: "How many dollars am I paying for each dollar of annual profit?"

**Example:** If a company earns $5 per share and the P/E ratio is 20, the stock price should be:
```
Price = EPS × P/E = $5 × 20 = $100
```

**Why it matters for Stock A:** The case packet tells us Stock A has a **constant P/E ratio**. This is huge — it means the ONLY thing that changes A's price is new earnings numbers. When you get an earnings report for A, you instantly know the new fair price:
```
fair_A = new_EPS × constant_PE
```
This makes A the easiest stock to price correctly.

**Stock C is different:** C's P/E ratio is NOT constant. It changes based on interest rates/yields. More on this in section 6.

---

## 3. EARNINGS PER SHARE (EPS)

**EPS = Company's Total Profit / Number of Shares Outstanding**

In our competition, we don't calculate EPS ourselves. The exchange just *tells* us the EPS through "structured news messages." For Stock A, you get earnings 2 times per day. For Stock C, you get earnings at specific ticks (tick 22 and tick 88 of each day).

When you receive a new EPS number, you immediately update your fair price model.

---

## 4. BONDS, YIELDS, AND INTEREST RATES

**Bonds** are loans. When you buy a bond, you're lending money to someone (usually a government or company). They pay you back later with interest.

**Yield** is the annual return you get from a bond, expressed as a percentage. If you buy a $1,000 bond that pays $50/year, the yield is 5%.

**Key relationship: Bond prices and yields move in OPPOSITE directions.**

Why? Imagine you own a bond paying 4%. Then new bonds start paying 5%. Nobody wants your 4% bond anymore, so its price drops. Conversely, if rates fall to 3%, your 4% bond is now valuable, and its price rises.

**Duration (D):** How sensitive a bond's price is to yield changes. Higher duration = more price movement per yield change. Think of it as a lever — longer duration = longer lever = bigger swing.

**Convexity (C):** Duration is a straight-line approximation. Convexity is the correction for the fact that the relationship is actually curved. It makes the bond price go up *more* than duration predicts when yields fall, and go down *less* when yields rise. (Convexity is always your friend if you own bonds.)

The case packet formula:
```
ΔB ≈ B₀ × (-D × Δy + 0.5 × C × (Δy)²)
      ↑         ↑              ↑
  starting   duration       convexity
  bond value  effect         correction
```

---

## 5. THE FEDERAL RESERVE & PREDICTION MARKETS

The Federal Reserve (the "Fed") controls short-term interest rates. In our competition, there's a hypothetical Fed that will do one of three things:

| Action | Rate Change | What It Means |
|--------|------------|---------------|
| **Hike** | +25 basis points (+0.25%) | Economy is too hot, raise rates to cool it |
| **Hold** | 0 | Keep rates the same |
| **Cut** | -25 basis points (-0.25%) | Economy is weak, lower rates to stimulate |

**Basis point (bp):** 1/100th of a percentage point. So 25 bps = 0.25%.

**Prediction market:** A market where you bet on which outcome will happen. Prices represent probabilities. If "hike" is trading at 0.40, the market thinks there's a 40% chance of a hike.

**Expected rate change:**
```
E[Δr] = (+25) × P(hike) + (0) × P(hold) + (-25) × P(cut)
```
Example: If P(hike)=0.4, P(hold)=0.4, P(cut)=0.2:
```
E[Δr] = 25×0.4 + 0×0.4 + (-25)×0.2 = 10 - 5 = +5 bps
```
The market expects rates to go up slightly.

**CPI (Consumer Price Index):** Measures inflation. The exchange gives you Forecasted vs Actual CPI:
- Actual > Forecasted → inflation is higher than expected → more likely the Fed HIKES
- Actual < Forecasted → inflation is lower → more likely the Fed CUTS

---

## 6. HOW STOCK C WORKS (THE HARD ONE)

Stock C is an insurance company. Its value comes from TWO sources:

**Source 1: Business Operations**
Like any company, C earns money from its operations. This part works like Stock A:
```
Operations value = EPS_C × PE_C
```

**Source 2: Bond Portfolio**
Insurance companies hold massive bond portfolios. When yields change, bond values change (see section 4). This adds or subtracts from C's stock price:
```
Bond contribution = λ × ΔB / N
```
Where λ is a weighting constant, ΔB is the change in bond value, and N is shares outstanding.

**The twist: C's P/E ratio changes with yields!**
```
PE_C = PE₀ × e^(-γ × (y - y₀))
```
When yields go UP (y > y₀), the exponent is negative, so PE drops. This makes sense — higher bond yields make stocks less attractive (investors can earn more from safe bonds), so they're willing to pay less per dollar of earnings.

**Putting it all together:**
```
Price_C = EPS_C × PE₀ × e^(-γ×Δy) + λ × B₀ × (-D×Δy + 0.5×C×(Δy)²) / N + noise
            ↑                              ↑                                    ↑
      operations value               bond portfolio effect                 random noise
```

**Chain of causation:**
```
CPI news → Fed probability update → Expected rate change → Yield change → C's P/E changes AND bond portfolio changes → C's fair price changes
```

This chain is why C is the hardest stock but also the biggest alpha opportunity — teams that model this correctly will price C better than everyone else.

---

## 7. OPTIONS — CALLS AND PUTS

An option is a **contract** that gives you the RIGHT (not obligation) to buy or sell a stock at a specific price.

**Call Option:** The right to BUY at a fixed price (the "strike price").
- You buy a call if you think the stock will go UP.
- Example: Buy a call with strike $100. If stock goes to $120, you can buy at $100 and immediately sell at $120 → profit $20.
- If stock stays at $95, you just don't exercise. You lose only what you paid for the call.

**Put Option:** The right to SELL at a fixed price.
- You buy a put if you think the stock will go DOWN.
- Example: Buy a put with strike $100. If stock falls to $80, you can sell at $100 → profit $20.
- If stock rises to $110, you don't exercise. You lose only what you paid.

**Strike Price (K):** The fixed price at which you can buy (call) or sell (put).

**In our competition:** We have calls and puts on Stock B across 3 different strike prices, all with the same expiry.

---

## 8. EUROPEAN vs AMERICAN OPTIONS

**American option:** Can be exercised ANY TIME before expiry. More flexible, therefore usually more expensive.

**European option:** Can ONLY be exercised AT expiry. Less flexible, easier to price mathematically.

**Our competition uses European options.** This matters because:
1. Put-Call Parity (the formula below) only works perfectly for European options
2. You can't early-exercise to capture dividends or lock in profits early
3. The only thing that matters is the stock price AT expiry

---

## 9. SINGLE EXPIRY

All the options in our competition expire at the **same time** — the end of the round. There's only one expiry date, not multiple.

This simplifies things enormously:
- All options share the same time-to-expiry T (which decreases as the round progresses)
- You can compare calls and puts across different strikes knowing they all expire together
- Box spread arbitrage works cleanly because all four legs share the same expiry

**As T shrinks (approaching end of round):** Options lose "time value" and converge to their intrinsic value (how much they'd be worth if exercised right now). This is called **theta decay**.

---

## 10. PUT-CALL PARITY (FREE MONEY DETECTOR #1)

This is a fundamental no-arbitrage relationship. For European options with the same strike and expiry:

```
C - P = S - K × e^(-rT)
```

Where:
- **C** = call price
- **P** = put price
- **S** = current stock price (Stock B in our case)
- **K** = strike price
- **r** = risk-free interest rate
- **T** = time to expiry (in years)
- **e^(-rT)** = the "discount factor" (a dollar in the future is worth less than a dollar today)

**Why it must hold:** A long call + short put at the same strike = a synthetic "forward" position in the stock. If C - P ≠ S - Ke^(-rT), you can construct a trade that makes risk-free profit.

**How to arb it:**

If `C - P > S - Ke^(-rT)` (calls are overpriced relative to puts):
→ SELL the call, BUY the put, BUY the stock. Lock in the difference as profit.

If `C - P < S - Ke^(-rT)` (puts are overpriced relative to calls):
→ BUY the call, SELL the put, SELL the stock. Lock in the difference as profit.

**For us:** We check this across all 3 strikes every tick. Even a few cents of violation is free money.

**Bonus use:** We can reverse-engineer Stock B's fair price from options:
```
S = C - P + K × e^(-rT)
```
Average this across all 3 strikes for a robust estimate of B's true value (since we get no direct info on B).

---

## 11. BOX SPREADS (FREE MONEY DETECTOR #2)

A box spread combines four options across two strikes (K₁ < K₂), all same expiry:

```
Box = (Buy Call K₁ + Sell Call K₂) + (Buy Put K₂ + Sell Put K₁)
       ↑ bull call spread              ↑ bear put spread
```

**The magic:** The payoff is ALWAYS K₂ - K₁, no matter what the stock does.

- If stock ends at $200 → box pays K₂ - K₁
- If stock ends at $50 → box pays K₂ - K₁
- If stock ends at $0 → box still pays K₂ - K₁

Since the payoff is guaranteed, the fair price of the box today is:
```
Fair Box Price = (K₂ - K₁) × e^(-rT)
```

**Arbitrage:** If the market prices the box above or below this fair value, you can make risk-free profit. Buy the box if it's cheap, sell it if it's expensive.

**With 3 strikes (K₁, K₂, K₃):** We get 3 possible boxes:
- K₁ to K₂
- K₁ to K₃
- K₂ to K₃

That's 3 chances to find mispricing. Most teams only check put-call parity and miss box spreads entirely.

---

## 12. ETFs — WHAT THEY ARE

**ETF = Exchange-Traded Fund.** It's a basket of stocks packaged into one tradeable thing.

In our competition:
```
1 ETF share = 1 share of A + 1 share of B + 1 share of C
```

The **Net Asset Value (NAV)** is the true value of the basket:
```
NAV = Price_A + Price_B + Price_C
```

The ETF has its own order book and trades at its own price, which *should* equal the NAV but often doesn't (because different people are trading it with different information).

---

## 13. ETF CREATION & REDEMPTION (SWAPS)

This is how ETFs stay close to their NAV in the real world, and how we can arb them in the competition.

**Creation (swap IN):** You give 1 share of A + 1 share of B + 1 share of C → you receive 1 ETF share. There's a small fee.

**Redemption (swap OUT):** You give 1 ETF share → you receive 1 share of A + 1 share of B + 1 share of C. There's a small fee.

Think of it like converting currencies. You're converting between "basket of stocks" and "ETF shares," and the exchange charges a small conversion fee.

**In our competition:** You can do these swaps at any time by paying the swap fee. This is the mechanism that keeps ETF prices close to NAV.

---

## 14. ETF ARBITRAGE

If the ETF price diverges from NAV by more than the swap fee, free money is available:

**ETF overpriced (ETF > NAV + fee):**
1. Buy shares of A, B, C in the market (total cost ≈ NAV)
2. Swap them into 1 ETF share (pay the fee)
3. Sell the ETF at the higher market price
4. Profit = ETF price - NAV - fee

**ETF underpriced (ETF < NAV - fee):**
1. Buy the ETF cheap
2. Swap it into A, B, C shares (pay the fee)
3. Sell A, B, C at their market prices
4. Profit = NAV - ETF price - fee

**Key insight from the case packet:** "When the ETF and equity prices don't align, it's more likely that the ETF is mispriced." This means when you see a divergence, you should bet on the ETF moving back to NAV rather than the stocks moving to match the ETF.

**When to swap short:** If you're short the ETF and long the components (or vice versa), you might want to swap to flatten out your position. This reduces risk but costs the fee.

---

## 15. MARKET MAKING — THE CORE JOB

A market maker is someone who stands ready to buy AND sell at all times. You're providing a service: liquidity. Other people can trade whenever they want because you're always offering prices.

**How you make money:** You buy at a lower price (bid) and sell at a higher price (ask). The difference is the "spread," and you keep it.

**Example:**
- You post: "I'll buy at $99.90 and sell at $100.10"
- Someone sells to you at $99.90
- Someone else buys from you at $100.10
- Profit: $0.20 per share (the spread)

**How you lose money:** If the price moves against your inventory.
- You bought at $99.90, now hold shares
- Bad news hits, price drops to $98.00
- Your shares are now worth $2.00 less than you paid

The entire game of market making is: **capture spreads consistently while managing the risk that prices move against your inventory.**

---

## 16. BID, ASK, SPREAD, MID

**Bid:** The highest price someone is willing to BUY at. (Your sell target)

**Ask (or Offer):** The lowest price someone is willing to SELL at. (Your buy target)

**Spread:** Ask - Bid. This is the "toll" for trading. Wider spread = more profit per trade but fewer trades.

**Mid (midpoint):** (Bid + Ask) / 2. Often used as a rough estimate of fair value.

**Example order book:**
```
SELL (asks):    $100.20 (50 shares)
                $100.15 (30 shares)
                $100.10 (20 shares)  ← best ask
--- spread = $0.10 ---
                $100.00 (25 shares)  ← best bid
BUY (bids):     $99.95 (40 shares)
                 $99.90 (60 shares)

Mid = ($100.10 + $100.00) / 2 = $100.05
Spread = $100.10 - $100.00 = $0.10
```

**Penny-in:** Posting a bid at $100.01 (1 cent better than the best bid) so your order gets filled first. This is a key competitive tactic — you're outbidding other market makers by a tiny amount.

---

## 17. ORDER BOOKS & LIMIT ORDERS

**Limit order:** "I want to buy/sell at THIS price or better." It sits on the book waiting until someone agrees to trade with you.

**Market order:** "I want to buy/sell RIGHT NOW at whatever price is available." These execute immediately but you have no control over the price.

**Order book:** The list of all outstanding limit orders, organized by price. When a new order comes in, the exchange matches it against the best available price on the other side.

**In our competition:** We place limit orders. We do NOT place market orders (too risky — you might get a terrible price). Our bot continuously posts bid and ask limit orders, cancels old ones, and posts new ones as our fair value estimate changes.

---

## 18. INVENTORY & WHY IT'S DANGEROUS

**Inventory = your current position.** If you've bought 50 shares net, your inventory is +50. If you've sold net 30, your inventory is -30.

**Why inventory is bad:**
- Positive inventory (long) means you lose money if the price drops
- Negative inventory (short) means you lose money if the price rises
- The bigger your inventory, the bigger your risk

**Inventory management techniques:**

**Skew/Fade:** Shift your quotes to attract trades that reduce your position.
- If you're long 100 shares → lower both your bid and ask slightly
- This makes people more likely to sell to you (nope, you're already long!) — wait, actually it makes you less likely to buy more and more likely to sell
- Specifically: if long, lower your bid (less eager to buy more) and lower your ask (more eager to sell)

**Position limits:** Hard caps on how much inventory you'll carry. If at the limit, stop quoting the side that would add more.

**Formula from winners:**
```
fade = -f × sign(position) × log₂(1 + |position|)
```
This shifts your fair price estimate. If you're long, your "fair" price drops, making you quote lower (encouraging sells). The log₂ means the fade grows quickly at first, then slows — it heavily punishes medium-sized positions without overreacting to small ones.

---

## 19. HOW SCORING WORKS

**Within a round:**
```
P&L = Σ (sell_price × sell_qty) - Σ (buy_price × buy_qty) + position × settlement_price
```
At the end of each round, all your remaining inventory is "settled" at the final fair prices. So even unsold inventory becomes realized P&L.

**ETF settlement:** The ETF settles at its NAV (computed from A, B, C fair values).

**Across rounds:**
- P&L is converted to points using a **nonlinear** function
- This means: making $500 in each of 5 rounds is MUCH better than making $2,500 in 1 round and $0 in 4
- Extreme losses in one round won't destroy you completely, but extreme gains in one round won't save you either
- **Later rounds count more** (increasingly weighted)

**The implication:** Be consistent. Don't take huge gambles. Small steady profits across every round will win the competition.

---

## 20. GLOSSARY

| Term | Meaning |
|------|---------|
| **Arb / Arbitrage** | Risk-free profit from price discrepancies |
| **Ask / Offer** | Price at which someone will sell |
| **Basis point (bp)** | 0.01% (1/100th of a percent) |
| **Bid** | Price at which someone will buy |
| **Call** | Option giving right to BUY |
| **Convexity** | Curvature correction in bond pricing |
| **CPI** | Consumer Price Index (inflation measure) |
| **Duration** | Bond price sensitivity to yield changes |
| **Edge** | Your profit margin per trade |
| **EPS** | Earnings Per Share |
| **ETF** | Exchange-Traded Fund (basket of stocks) |
| **European option** | Can only exercise at expiry |
| **Expiry** | When an option contract ends |
| **Fade** | Shift quotes based on inventory to reduce risk |
| **Fair value** | Your model's estimate of what something is truly worth |
| **Fill** | When your order gets executed/traded |
| **Forward** | Agreement to buy/sell at a future date |
| **Hike** | Fed raising interest rates |
| **Inventory** | Your current net position (long or short) |
| **Limit order** | Order that specifies exact price |
| **Liquidity** | How easily you can buy/sell without moving the price |
| **Long** | You own the asset (positive position) |
| **Market maker** | Someone who quotes both buy and sell prices |
| **Market order** | Order that executes immediately at best available price |
| **Mid** | Midpoint between bid and ask |
| **NAV** | Net Asset Value (true value of an ETF's basket) |
| **P/E ratio** | Price to Earnings ratio |
| **PCP** | Put-Call Parity |
| **Penny-in** | Improving best bid/ask by 1 cent to get priority |
| **Position** | How many shares you hold (+ is long, - is short) |
| **Put** | Option giving right to SELL |
| **Risk-free rate (r)** | Return on a perfectly safe investment |
| **Settlement** | Final price used to close all positions at round end |
| **Short** | You owe the asset (negative position, sold what you don't own) |
| **Skew** | Shifting quotes asymmetrically |
| **Spread** | Ask minus Bid |
| **Strike (K)** | The fixed price in an option contract |
| **Swap** | ETF creation/redemption (converting between ETF and components) |
| **T** | Time to expiry |
| **Tick** | Smallest time unit in the simulation |
| **Yield** | Annual return on a bond |

---

## QUICK REFERENCE: THE FLOW OF CASE 1

```
Every tick, your bot needs to:

1. READ order books → compute mid prices for A, B, C, ETF
2. READ news → update EPS values, Fed probabilities, CPI data
3. COMPUTE fair values:
   - A: EPS_A × PE (easy)
   - B: derive from options via PCP (no direct info)
   - C: EPS_C × PE_C(yield) + bond_portfolio_effect (complex)
   - ETF: fair_A + fair_B + fair_C
4. QUOTE on A and C:
   - Post bids below fair value, asks above fair value
   - Adjust for inventory (fade)
   - Multiple levels at increasing spreads
5. CHECK for arbitrage:
   - PCP violations on B's options → trade them
   - Box spread violations → trade them
   - ETF vs NAV divergence → swap + trade
6. QUOTE Fed prediction market:
   - Post bids/asks around your probability estimates
7. MANAGE risk:
   - Cancel stale orders
   - Monitor position limits
   - Adjust spreads if approaching limits
```

---

*Written for team ucla_calberkeley, April 8 2026. 3 days to competition.*
