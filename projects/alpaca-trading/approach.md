# Alpaca Trading System - High-Level Approach

## Goal
Achieve **1% daily returns** via automated trading on Alpaca, with continuous strategy optimization.

---

## Architecture Recommendation: **Hybrid App + Agent Oversight**

### Why Not Pure Agent?
- Agents burn tokens on every decision loop
- Trading requires fast, consistent execution (milliseconds matter)
- Running an agent 24/7 for market hours = expensive and slow

### Why Not Pure App?
- Static algorithms can't adapt to changing market conditions
- No intelligent strategy evolution
- You'd need manual intervention to optimize

### The Hybrid Approach
```
┌─────────────────────────────────────────────────────────────┐
│                      JARVIS (Me)                            │
│  - Strategic oversight via cron/heartbeat                   │
│  - Performance analysis & strategy optimization             │
│  - Spawns sub-agents for deep research when needed          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   TRADING ENGINE (App)                      │
│  - Python service running on your Mac mini                  │
│  - Executes trades via Alpaca API                           │
│  - Applies current strategy parameters                      │
│  - Logs all activity to files I can read                    │
│  - Exposes simple control API (start/stop/status/params)    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      ALPACA API                             │
│  - Paper trading first, then live                           │
│  - Market data streaming                                    │
│  - Order execution                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## How It Works

### 1. Trading Engine (The App)
A Python service that:
- Connects to Alpaca for market data + order execution
- Implements multiple trading strategies (momentum, mean reversion, etc.)
- Uses a **config file** for strategy parameters that I can modify
- Logs trades, P&L, and performance metrics to structured files
- Runs as a daemon (launchd on macOS)

### 2. My Role (Agent Oversight)
Via cron jobs + heartbeats:
- **Morning (pre-market)**: Review overnight news, set day's strategy bias
- **Mid-day**: Check performance, adjust if needed
- **After close**: Analyze day's trades, update strategy parameters
- **Weekly**: Deep performance review, potentially spawn sub-agent for research

### 3. Strategy Evolution
- Start with proven strategies (momentum breakouts, VWAP mean reversion)
- Track performance metrics per strategy
- I analyze what's working and adjust parameters
- Can add/remove strategies based on market conditions

---

## Risk Management (Critical)

| Control | Setting |
|---------|---------|
| Max daily loss | 2% of portfolio (stops trading for day) |
| Max position size | 10% of portfolio per trade |
| Stop loss per trade | 1-2% |
| Paper trading period | 2 weeks minimum before live |

---

## Target: 1% Daily

Let's be real about this:
- **1% daily = ~250% annually** (compounded)
- This is aggressive but achievable with:
  - High win rate strategies
  - Proper position sizing
  - Multiple uncorrelated strategies
  - Quick cut of losers

We'll start with paper trading to validate before risking real capital.

---

## Proposed Stack

| Component | Technology |
|-----------|------------|
| Trading Engine | Python 3.11+ |
| Alpaca SDK | `alpaca-py` (official) |
| Data Storage | SQLite for trades, JSON for config |
| Scheduling | macOS launchd daemon |
| Logging | Structured JSON logs I can parse |
| My Interface | File-based config + CLI commands |

---

## Development Phases

### Phase 1: Foundation (Week 1)
- Set up project structure
- Alpaca API connection + authentication
- Basic order execution
- Logging infrastructure

### Phase 2: First Strategy (Week 2)
- Implement momentum breakout strategy
- Backtesting framework
- Paper trading integration

### Phase 3: Oversight Integration (Week 3)
- Config file for strategy parameters
- Performance reporting files
- Cron jobs for my check-ins

### Phase 4: Strategy Expansion (Ongoing)
- Add more strategies
- Optimize based on performance
- Eventually go live

---

## Questions for You

1. **Account size**: What's the starting capital? (affects position sizing)
2. **Risk tolerance**: Is 2% max daily loss acceptable?
3. **Trading hours**: US market hours only, or also pre/post market?
4. **Paper first**: Confirm you want 2 weeks paper trading before live?

---

## Next Steps

Once you approve this approach:
1. I'll create `requirements.md` with EARS-notation acceptance criteria
2. Then `design.md` with technical architecture
3. Then `tasks.md` with implementation steps

Ready when you are. 🤖
