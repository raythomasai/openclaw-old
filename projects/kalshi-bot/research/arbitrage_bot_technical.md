# Building a Prediction Market Arbitrage Bot
**Source:** Navnoorbawa Substack (Nov 2025)
**Date Filed:** 2026-02-05
**URL:** https://navnoorbawa.substack.com/p/building-a-prediction-market-arbitrage

---

## Executive Summary

Academic research documented **$40 million in arbitrage profits** extracted from Polymarket between April 2024-April 2025. The opportunity persists because retail-dominated orderbooks lack institutional market-making infrastructure.

**Key insight:** "Prediction market arbitrage is market microstructure exploitation — not outcome forecasting"

---

## THE NUMBERS

### Total Arbitrage Extracted (April 2024 - April 2025)
| Strategy | Profit |
|----------|---------|
| Single-condition arbitrage (YES+NO≠$1) | $4.68M |
| Market rebalancing (YES across conditions) | $11.09M |
| Market rebalancing (NO across conditions) | $17.31M |
| Sell strategies | $4.88M |
| Cross-market combinatorial | ~$95K |
| **TOTAL** | **$39.59M** |

### Top Performers
- **Top arbitrageur:** $2.01M across 4,049 transactions
- **Extreme outlier:** $0.02 → $58,983.36 (both YES/NO mispriced below $0.02)
- **Top 10 arbitrageurs:** $8.18M (21% of total)

### Market Statistics
- **Polymarket volume (2024 election):** $3.7B
- **Weekly volume (Oct 2025):** $2B+
- **Kalshi weekly (Sep 2025):** $500M+
- **Average profit per condition:** $50-$500 at available liquidity

---

## ARBITRAGE STRATEGIES

### 1. Single-Condition Arbitrage ⭐⭐⭐⭐⭐
**Buy YES + NO when sum ≠ $1**

```python
def detect_single_condition_arbitrage(yes_price, no_price, liquidity):
    sum_price = yes_price + no_price
    
    # Long arbitrage: Buy both if sum < $1
    if sum_price < 1.00 - min_profit:
        profit_per_dollar = 1.00 - sum_price
        return {
            'type': 'buy_both',
            'position_size': min(liquidity, max_capital),
            'expected_profit': profit_per_dollar * position_size
        }
    
    # Short arbitrage: Sell both if sum > $1
    elif sum_price > 1.00 + min_profit:
        return {'type': 'sell_both', ...}
```

**When it works:** Chronic mispricing in illiquid markets
**Frequency:** Always present, larger in low-liquidity conditions

---

### 2. Cross-Platform Arbitrage ⭐⭐⭐⭐
**Buy YES on one platform, NO on another**

```
Example: Fed Rate Cut
- Polymarket YES: $0.45
- Kalshi NO: $0.52

Total cost: $0.97
Guaranteed payout: $1.00
Profit: $0.03 (3.1%)
```

**Critical constraint:** Non-atomic execution
- One leg may fill while hedge fails
- Creates directional exposure

**Mitigation:**
```python
async def execute_atomic_arbitrage(market_id, opportunity):
    # Place both orders simultaneously
    yes_task = place_order('YES', position_size, yes_price)
    no_task = place_order('NO', position_size, no_price)
    
    # With 5-second timeout
    results = await asyncio.gather(yes_task, no_task, timeout=5)
    
    # Verify both fills
    if yes_filled and no_filled:
        return True
    
    # Cancel unfilled leg
    await handle_partial_fill(yes_order, no_order)
    return False
```

---

### 3. Market Rebalancing ⭐⭐⭐⭐
**Buy YES/NO across multiple related conditions**

This exploits correlation between markets (e.g., "Trump wins" + "Republican Senate")

---

### 4. Combinatorial Arbitrage ⭐⭐⭐
**Cross-market dependencies**

13 dependent market pairs identified during 2024 election cycle
Only 5 showed realized extraction (~95K total)

**Rarer than single-market opportunities**

---

## TECHNICAL IMPLEMENTATION

### Architecture
```
┌─────────────────────────────────────────────────────┐
│               WebSocket Monitor                       │
│         (100+ markets, real-time)                   │
└────────────────┬──────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│              Signal Detector                        │
│    (arbitrage opportunity identification)           │
└────────────────┬──────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│              Order Executor                         │
│   (atomic execution, timeout protection)           │
└────────────────┬──────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│             Risk Manager                          │
│   (oracle exposure, gas optimization)            │
└─────────────────────────────────────────────────────┘
```

### WebSocket Monitoring
```python
import asyncio
import websockets
import json

class ArbitrageMonitor:
    def __init__(self, private_key):
        self.host = "https://clob.polymarket.com"
        self.chain_id = 137  # Polygon
        
    async def monitor_markets(self, market_ids: list):
        ws_url = f"{self.host}/ws/market"
        
        async with websockets.connect(ws_url) as ws:
            subscribe_msg = {
                "type": "subscribe",
                "markets": market_ids
            }
            await ws.send(json.dumps(subscribe_msg))
            
            async for message in ws:
                data = json.loads(message)
                await self.process_update(data)
```

### Gas Optimization (Polygon)
```python
class GasOptimizer:
    def estimate_transaction_cost(self, order_size: Decimal) -> Decimal:
        # Typical Polygon gas: 30-100 gwei
        gas_price = self.w3.eth.gas_price
        gas_limit = 150000  # Standard CLOB order
        
        gas_cost_wei = gas_price * gas_limit
        gas_cost_matic = Decimal(gas_cost_wei) / Decimal(10**18)
        
        return gas_cost_matic * matic_usd_price
    
    def is_profitable_after_costs(self, expected_profit, order_size):
        total_cost = self.estimate_transaction_cost(order_size)
        net_profit = expected_profit - total_cost
        net_roi = net_profit / order_size
        
        return net_roi > 0.02  # 2% minimum
```

---

## CRITICAL RISKS

### 1. Oracle Manipulation ⭐⭐⭐⭐⭐
**REAL EXAMPLE (March 2025):**
- Whale with 5 million UMA tokens (25% of voting power)
- Manipulated $7M market resolution on Ukraine mineral deal
- No formal agreement existed
- Winner: +$55,000 | Loser: -$73,000

**Mitigation:**
```python
# Avoid cross-platform positions unless spread > 15 cents
if spread < 0.15:
    return None  # Insufficient buffer for oracle risk
```

### 2. Partial Fills
- One order fills, other fails
- Creates directional exposure
- **Solution:** 5-second timeout with cancellation

### 3. Gas Fees
- Polygon fees compress returns on small arbitrages
- Need >2% spread to be profitable

### 4. Regulatory Risk
- Massachusetts sued Kalshi (Sep 2025)
- $1B+ wagers (Jan-Jun 2025), 75% sports-related
- Polymarket settled with CFTC (2022)

---

## PROFITABILITY METRICS

### Per-Trade Economics
| Metric | Value |
|--------|-------|
| Average ROI | 1-5% |
| Average profit | $50-$500 per condition |
| Top trader average | $496 per trade |
| Frequency needed | 4,000+ trades/year |

### Scaling Requirements
- Monitor 100+ markets simultaneously
- Sub-second execution for high-frequency opportunities
- Capital: $10K-$50K per condition based on liquidity
- **Frequency > position size**

---

## TIMELINE & OUTLOOK

### Current State
- Weekly volume: $2B+
- Institutional entering (ICE invested $2B in Polymarket)
- Early crypto arbitrage generated 1,000%+ returns

### Compression Inevitable
As institutional market makers deploy:
- Spreads compress
- Execution speeds increase
- Retail opportunities shrink

### Window
Early crypto (2016-2018) trajectory:
- Early arbitrageurs extracted outsized returns
- Professional market makers eliminated inefficiencies
- Same pattern emerging in prediction markets

**Deploy now or wait for compressed spreads**

---

## IMPLEMENTATION PRIORITY

### Phase 1: Monitor & Alert
1. WebSocket connection to Polymarket
2. Kalshi REST API polling
3. Alert system for opportunities >$10 profit

### Phase 2: Execute
4. Atomic order placement
5. Timeout protection
6. Partial fill handling

### Phase 3: Scale
7. Multi-market monitoring
8. Gas optimization
9. Cross-platform arbitrage

---

## KEY TAKEAWAYS

1. **$40M extracted** in 12 months (research-verified)
2. **Microstructure > forecasting** - exploiting mechanics, not predicting outcomes
3. **Speed is everything** - seconds matter, milliseconds differentiate
4. **Oracle risk is real** - March 2025 example shows manipulation potential
5. **Frequency over size** - $496 avg per trade, 4,000+ trades
6. **Window closing** - institutional capital professionalizing the space

---

## REFERENCES

1. Saguillo et al. (2025). "Unravelling the Probabilistic Forest: Arbitrage in Prediction Markets." arXiv:2508.03474
2. Rodriguez (2025). "Kalshi Outpaces Polymarket." CoinDesk
3. Polymarket Documentation (2025). CLOB Introduction
4. Kalshi API Documentation (2025). Rate Limits and Tiers
5. Yahoo Finance (2025). "Polymarket Suffers UMA Governance Attack"
6. Yahoo Finance (2025). "Prediction Markets Hit All-Time High"
7. ICE Press Release (2025). Strategic Investment in Polymarket
8. WBUR News (2025). "Massachusetts Attorney General Files Lawsuit Against Kalshi"
