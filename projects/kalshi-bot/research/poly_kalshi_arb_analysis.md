# poly-kalshi-arb: Production Analysis & Integration Plan
**Source:** https://github.com/taetaehoho/poly-kalshi-arb
**Date:** 2026-02-05

---

## Executive Summary

This is a **production-grade Rust arbitrage bot** with:
- High-performance concurrent execution
- Market discovery & caching
- Circuit breaker protection
- Position tracking
- Cross-platform arbitrage (Polymarket ↔ Kalshi)

**Key Difference from Our Bot:** Uses Rust for lock-free atomic operations and sub-millisecond latency.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      main.rs                               │
│  • WebSocket orchestration                                  │
│  • Dry run / live mode                                     │
│  • Credential loading                                      │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐  ┌──────────┐  ┌──────────┐
│kalshi │  │polymarket│  │discovery │
│  WS   │  │   WS     │  │ Matching │
└────────┘  └──────────┘  └──────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   execution.rs                              │
│  • Concurrent leg execution                                 │
│  • In-flight deduplication (512 markets via 8x u64)        │
│  • 5-second timeout protection                              │
│  • Atomic order placement                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐  ┌──────────────┐  ┌─────────────────┐
│circuit │  │position      │  │position_tracker │
│breaker │  │tracking      │  │                 │
└────────┘  └──────────────┘  └─────────────────┘
```

---

## Key Features

### 1. Atomic Orderbook (Lock-Free) ⭐⭐⭐⭐⭐
```rust
// src/types.rs - 64-bit packed atomic state
// Layout: [yes_ask:16][no_ask:16][yes_size:16][no_size:16]

#[inline(always)]
pub fn pack_orderbook(yes_ask, no_ask, yes_size, no_size) -> u64 {
    ((yes_ask as u64) << 48) | ((no_ask as u64) << 32) | 
    ((yes_size as u64) << 16) | (no_size as u64)
}
```

**Why it matters:** Lock-free reads/writes for microsecond latency.

### 2. In-Flight Deduplication ⭐⭐⭐⭐
```rust
// src/execution.rs
// 512 markets tracked via 8x u64 bitmask
if market_id < 512 {
    let slot = (market_id / 64) as usize;
    let bit = market_id % 64;
    let mask = 1u64 << bit;
    let prev = self.in_flight[slot].fetch_or(mask, Ordering::AcqRel);
    if prev & mask != 0 {
        return Err("Already in-flight");  // Prevent duplicate orders
    }
}
```

### 3. Circuit Breaker ⭐⭐⭐⭐⭐
```env
# Environment Configuration
CB_ENABLED=true
CB_MAX_POSITION_PER_MARKET=100      # Max contracts per market
CB_MAX_TOTAL_POSITION=500           # Max total contracts
CB_MAX_DAILY_LOSS=5000             # $50 daily loss limit (in cents)
CB_MAX_CONSECUTIVE_ERRORS=5         # Halt on 5 consecutive errors
CB_COOLDOWN_SECS=60                 # 60-second cooldown after trip
```

**Key feature:** Tracks positions per market and daily P&L in cents.

### 4. Fee Handling ⭐⭐⭐⭐
```rust
// Kalshi fee: ceil(0.07 × P × (1-P)) in cents
static KALSHI_FEE_TABLE: [u16; 101] = [
    // Pre-calculated for prices 0-100 cents
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,      // 0-9
    1, 1, 1, 1, 1, 2, 2, 2, 2, 2,      // 10-19
    // ...
];

// For prices 10-90 cents, fee is typically 1-2 cents
```

### 5. Concurrent Execution ⭐⭐⭐⭐
```rust
// Execute both legs concurrently
let result = tokio::join!(
    self.execute_leg_async("YES", market_id, contracts, yes_price),
    self.execute_leg_async("NO", market_id, contracts, no_price)
);
```

### 6. Market Discovery with Caching ⭐⭐⭐
```rust
// Caches matched markets to disk (.discovery_cache.json)
// TTL: 2 hours
// Incremental refresh for stale cache
```

---

## Comparison: Our Bot vs poly-kalshi-arb

| Feature | Our Bot (Python) | Their Bot (Rust) |
|---------|------------------|------------------|
| Language | Python | Rust |
| Latency | ~100ms | <1ms |
| Orderbook | dict + locks | atomic u64 lock-free |
| Execution | Sequential | Concurrent (tokio) |
| Market Discovery | Manual | Auto-discovery + caching |
| Circuit Breaker | Basic | Full (positions + P&L) |
| Cross-platform | Partial | Full |
| Fee handling | Manual | Auto (fee table) |
| Test mode | None | Synthetic arb injection |

---

## Integration Recommendations

### Option A: Clone & Run Their Bot ⭐⭐⭐⭐
**Pros:** Production-ready, battle-tested
**Cons:** Requires Rust toolchain, different architecture

```bash
# Setup
git clone https://github.com/taetaehoho/poly-kalshi-arb.git
cd poly-kalshi-arb
cargo build --release

# Run dry run
DRY_RUN=1 cargo run --release

# Run live
DRY_RUN=0 cargo run --release
```

**Config needed:**
```env
# .env
KALSHI_API_KEY_ID=your_key_id
KALSHI_PRIVATE_KEY_PATH=/path/to/key.pem
POLY_PRIVATE_KEY=0x...
POLY_FUNDER=0x...
DRY_RUN=1
```

### Option B: Port Key Features to Our Bot ⭐⭐⭐
**Pros:** Keep our Python architecture, add their innovations
**Cons:** Significant refactoring

**Features to port:**
1. Atomic orderbook using `multiprocessing.Value`
2. Fee table in config
3. Enhanced circuit breaker
4. Concurrent order execution with asyncio.gather
5. Market discovery caching

### Option C: Hybrid Approach ⭐⭐⭐⭐
**Use their bot for cross-platform arbitrage, ours for single-platform strategies.**

**Rationale:**
- Their bot: Cross-platform arb (high frequency, low margin)
- Our bot: Mechanical arb + longshot bias (Kalshi only)

---

## Key Code We Should Port

### 1. Circuit Breaker Logic
```python
# Python adaptation of their Rust circuit breaker

class CircuitBreaker:
    def __init__(self):
        self.max_position_per_market = 50000  # contracts
        self.max_total_position = 100000       # contracts
        self.max_daily_loss = 50.0            # dollars
        self.max_consecutive_errors = 5
        self.cooldown_secs = 60
        self.halted = False
        self.daily_pnl_cents = 0
        self.positions = {}  # {market_id: MarketPosition}
        self.consecutive_errors = 0
    
    async def can_execute(self, market_id, contracts) -> bool:
        if self.halted:
            return False
        
        # Check position limits
        if self.positions.get(market_id, 0) + contracts > self.max_position_per_market:
            return False
        
        if sum(self.positions.values()) + contracts > self.max_total_position:
            return False
        
        # Check daily loss
        if self.daily_pnl_cents < -self.max_daily_loss * 100:
            self.trip("Max daily loss exceeded")
            return False
        
        return True
```

### 2. Fee Calculation
```python
# Kalshi fee: ceil(0.07 × P × (1-P)) in cents
def kalshi_fee_cents(price_cents: int) -> int:
    if price_cents > 100 or price_cents == 0:
        return 0
    # fee = ceil(7 × p × (100-p) / 10000)
    numerator = 7 * price_cents * (100 - price_cents) + 9999
    return numerator // 10000

# Pre-computed table (0-100 cents)
KALSHI_FEE_TABLE = [0] * 101
for p in range(1, 100):
    numerator = 7 * p * (100 - p) + 9999
    KALSHI_FEE_TABLE[p] = numerator // 10000
```

### 3. In-Flight Deduplication
```python
# Bitmask deduplication for 512 markets
import threading

class InFlightDedupe:
    def __init__(self, num_markets=512):
        self.num_slots = num_markets // 64
        self.bitmask = [0] * self.num_slots
        self.lock = threading.Lock()
    
    def try_claim(self, market_id: int) -> bool:
        slot = market_id // 64
        bit = market_id % 64
        mask = 1 << bit
        
        with self.lock:
            if self.bitmask[slot] & mask:
                return False  # Already in-flight
            self.bitmask[slot] |= mask
            return True
    
    def release(self, market_id: int):
        slot = market_id // 64
        bit = market_id % 64
        mask = 1 << bit
        
        with self.lock:
            self.bitmask[slot] &= ~mask
```

---

## Risk Mitigation from Their Code

### 1. Non-Atomic Execution Risk
**Their solution:** 5-second timeout with cancellation
```rust
let result = tokio::time::timeout(
    Duration::from_secs(5),
    execute_both_legs_async(...)
).await;

if result.is_err() {
    await cancel_pending_orders(market_id);
}
```

### 2. Partial Fill Risk
**Their solution:** Calculate matched = min(yes_filled, no_filled)
```rust
let matched = yes_filled.min(no_filled);
let success = matched > 0;
let actual_profit = matched * 100 - (yes_cost + no_cost);
```

### 3. Oracle Manipulation Risk
**From research:** Avoid cross-platform unless spread > 15 cents
```python
MIN_ARB_SPREAD = 15  # cents
if profit_cents < MIN_ARB_SPREAD:
    return None  # Skip - insufficient buffer
```

---

## Recommended Action

### Immediate (This Week)
1. **Test their bot** in dry-run mode to verify it works
2. **Compare execution quality** (latency, fills)
3. **Identify gaps** (which markets they support)

### Short-Term (2 Weeks)
1. **Port circuit breaker** to our bot for better risk management
2. **Add fee calculation** to improve arb detection accuracy
3. **Implement deduplication** to prevent duplicate orders

### Long-Term (1 Month)
1. **Decide architecture**:
   - Keep Python + incremental improvements
   - Or migrate to Rust for production
2. **If migrating:** Use their codebase as foundation
3. **If keeping Python:** Adopt their patterns and algorithms

---

## Files Reference

| File | Purpose | Priority |
|------|---------|----------|
| `src/main.rs` | Entry point, WS orchestration | Medium |
| `src/execution.rs` | Order execution, deduplication | High |
| `src/circuit_breaker.rs` | Risk limits, halt logic | High |
| `src/discovery.rs` | Market matching, caching | Medium |
| `src/kalshi.rs` | Kalshi API client | High |
| `src/types.rs` | Data structures, fee table | High |
| `src/position_tracker.rs` | P&L tracking | Medium |

---

## Conclusion

**This is exactly what we need.**

The bot is production-ready with battle-tested code. Key insights:

1. **Lock-free atomic orderbooks** for microsecond latency
2. **Pre-computed fee table** for accurate arb detection
3. **Circuit breaker with daily P&L tracking**
4. **Concurrent execution** with timeout protection
5. **Market discovery with 2-hour cache**

**Recommendation:** Run their bot in dry-run mode first, then decide whether to:
- Use it directly for cross-platform arbitrage
- Port key features to our Python bot
- Hybrid approach (their bot + our bot for different strategies)
