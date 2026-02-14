# IBKR Options Trading Bot - AGGRESSIVE IMPLEMENTATION PLAN

## ⚡ Strategy Shift: Conservative → Aggressive

**Previous:** Wheel Strategy (income-focused, theta decay)
**New:** Directional Betting - Long & Short Premium (chasing daily returns)

---

## 🎯 New Strategy: Dual-Sided Momentum Trading

### Core Approach
- **Long Side:** Buy calls, call spreads, debit spreads on bullish setups
- **Short Side:** Buy puts, put spreads on bearish setups
- **Timeframe:** Daily to weekly (1-5 day hold)
- **Goal:** Capture directional moves quickly
- **Style:** Momentum, breakouts, reversals

### Primary Strategies

| Strategy | Direction | Risk/Reward | Use Case |
|----------|-----------|-------------|----------|
| **Long Call** | Bullish | Unlimited/Defined | Strong breakouts |
| **Long Put** | Bearish | Defined/Unlimited | Sharp breakdowns |
| **Call Debit Spread** | Bullish | Defined/Defined | Moderate bullish, cost reduction |
| **Put Debit Spread** | Bearish | Defined/Defined | Moderate bearish, cost reduction |
| **Long Straddle** | Neutral | Defined | Earnings, volatility plays |
| **Long Strangle** | Neutral | Defined | Cheaper volatility play |

---

## 📊 Aggressive Parameters

### Position Sizing (High Conviction)

```yaml
strategy:
  # Entry criteria
  min_confidence: 0.65              # 65%+ conviction required
  min_reward_risk: 1.5              # Min 1.5:1 ratio
  
  # Strike selection (more aggressive deltas)
  long_delta_min: 0.40              # ATM to slightly OTM
  long_delta_max: 0.60
  
  # Expiration (shorter = faster theta burn, need directional move)
  min_days_to_expiry: 2             # 2-5 day "weeklys"
  max_days_to_expiry: 7
  
  # Position limits (aggressive)
  max_positions: 10                 # More concurrent trades
  max_allocation_per_trade: 0.08   # 8% per trade
  max_side_exposure: 0.60          # Max 60% in one direction

# Risk (tighter controls, faster exits)
risk:
  max_daily_loss_pct: 0.05          # 5% daily stop (aggressive)
  max_loss_per_trade: 0.02         # 2% stop per trade
  profit_target_pct: 0.03           # 3% target per trade (grab quick wins)
  trailing_stop: True               # Lock in gains
  trailing_stop_pct: 0.015          # 1.5% trail
```

---

## 🎯 Entry Signals (Momentum-Based)

### Long (Bullish) Signals
1. Price breaks above daily VWAP with volume
2. RSI crossing above 50 from oversold (<40)
3. Gap up opening with sustained volume
4. Support bounce with bullish candle
5. Sector leading stock breaking resistance

### Short (Bearish) Signals
1. Price breaks below daily VWAP with volume
2. RSI crossing below 50 from overbought (>60)
3. Gap down opening with heavy volume
4. Resistance rejection with bearish candle
5. Sector lagging stock breaking support

### Volatility Expansion Plays
1. Implied volatility rank < 20 (cheap options)
2. Earnings announcement approaching (2-5 days)
3. Major news catalyst expected
4. Pre-market unusual options activity

---

## 🚀 Quick-Chop Strategy (Daily Focus)

### Pre-Market (8:00-9:15 AM CT)
- Scan for gapers (stocks gapping 3%+)
- Identify sector momentum
- Flag high-volume premarket movers

### Market Open (9:30-10:00 AM)
- Watch for initial momentum fade or continuation
- Entries on first pullback after gap
- Quick scalps on volatility

### Mid-Day (10:00-2:00 PM)
- Fade lunch moves (contrarian)
- Support/resistance bounces
- Trend continuation entries

### Close (2:00-4:00 PM)
- Exit day trades
- Roll expiring positions
- Capture "sell the close" moves

---

## 🛡️ Aggressive Risk Controls

### Daily Limits (Non-Negotiable)
```
START_OF_DAY: 100% portfolio
-2% P&L → Reduce size by 50%
-4% P&L → Stop taking new long positions
-5% P&L → FULL STOP for the day
```

### Per-Trade Rules
```
ENTRY: Calculate stop BEFORE entry
- Long: Stop = 15% below entry (aggressive)
- Short: Stop = 15% above entry (aggressive)
- NO TRADE if can't define exit before entry

EXIT:
- Hit profit target (3%+) → Exit 50% position
- Hit stop → Exit 100% position
- 2:00 PM cutoff → Exit all day trades
```

### Position Limits
```
MAX daily new positions: 5
MAX concurrent: 10
MAX single-direction exposure: 60%
MAX sector concentration: 40%
```

---

## 📋 Revised Architecture

```
ibkr-options-bot/
├── src/
│   ├── ibkr_client.py          # IBKR API (ib_insync)
│   ├── scanner.py              # Momentum scanner
│   ├── signals.py              # Entry signal generator
│   ├── strategy.py             # Aggressive strategy logic
│   ├── risk_manager.py         # Aggressive risk controls
│   ├── scheduler.py            # Trading schedule
│   ├── exit_manager.py         # Profit-taking & stops
│   └── main.py
├── config/
│   ├── config.yaml             # Aggressive settings
│   └── secrets.yaml
├── data/
│   ├── watchlist.txt           # Active watchlist
│   ├── signals.json            # Today's signals
│   └── positions.json          # Open positions
├── logs/
│   └── trading.log
└── requirements.txt
```

---

## 🔧 Implementation Phases (Accelerated)

### Phase 1: Foundation (Day 1-2)
- [ ] IBKR Gateway setup & connection test
- [ ] ib_insync installation
- [ ] Basic client wrapper
- [ ] Account/position tracking

### Phase 2: Scanner & Signals (Day 3-4)
- [ ] Price scanner (gap up/down, volume)
- [ ] RSI/VWAP signal generator
- [ ] Real-time monitoring loop
- [ ] Signal alerting system

### Phase 3: Execution (Day 5-6)
- [ ] Order execution engine
- [ ] Paper trading mode
- [ ] Position management
- [ ] P&L tracking

### Phase 4: Risk & Exits (Day 7-8)
- [ ] Daily loss limits
- [ ] Per-trade stops
- [ ] Profit target automation
- [ ] Trailing stop implementation

### Phase 5: Testing (Day 9-14)
- [ ] Paper trade 1 week minimum
- [ ] Tune parameters based on results
- [ ] Document win/loss patterns

### Phase 6: Live (Day 15+)
- [ ] Start with 25% intended size
- [ ] Scale to 50% after 1 profitable week
- [ ] Full size after 2 profitable weeks

---

## 📈 Expected Performance (Aggressive)

| Metric | Conservative | Aggressive |
|--------|--------------|------------|
| Daily Target | 0.03-0.05% | 0.10-0.25% |
| Weekly Target | 0.2-0.4% | 1.0-2.0% |
| Win Rate Target | 80%+ | 55-65% |
| Risk/Reward | 1:1.2 | 1:2+ |
| Max Drawdown | 5-8% | 10-15% |
| Trades/Day | 0-1 | 2-5 |

---

## ⚠️ Important Warnings

1. **Higher Volatility:** Expect larger daily swings (+/- 3-5%)
2. **Lower Win Rate:** More whipsaws, more losses
3. **Faster Decisions:** Need to act quickly on signals
4. **Emotional Discipline:** Critical - stick to stops
5. **Capital Requirements:** Need more cushion for drawdowns

---

## 🚦 Decision Tree: Entry or Pass

```
IS THERE A SIGNAL?
├─ NO → Pass, wait for setup
└─ YES → CONTINUE
    ├─ Is confidence ≥ 65%?
    │   ├─ NO → Pass
    │   └─ YES → CONTINUE
    │       ├─ Is reward:risk ≥ 1.5:1?
    │       │   ├─ NO → Pass
    │       │   └─ YES → CONTINUE
    │       │       ├─ Have we hit daily loss limit?
    │       │       │   ├─ YES → Pass (stop trading)
    │       │       │   └─ NO → CONTINUE
    │       │       │       ├─ Position size calculated?
    │       │       │       │   └─ YES → TAKE TRADE
```

---

## 📊 Sample Day (Aggressive Mode)

| Time | Action | Target |
|------|--------|--------|
| 8:00 AM | Scan premarket, identify 3-5 candidates | Setup list |
| 9:30 AM | Execute top 1-2 setups | First entry |
| 10:00 AM | Check exits, scale in if winning | Add to winners |
| 11:00 AM | Mid-day scan, fade moves | Opportunistic |
| 1:00 PM | Close profitable winners | Take profits |
| 2:30 PM | Exit all day trades | Closeout |
| 3:00 PM | EOD review, log trades | Journal |

---

## 🎯 Next Steps

1. **Confirm setup:** IBKR Gateway ready?
2. **Capital:** How much for aggressive trading?
3. **Time commitment:** Can you monitor during market hours?
4. **Risk tolerance:** Comfortable with 5% daily swings?

Ready to build the aggressive bot, or want to discuss parameters first?
