# Alpaca Trading System - Implementation Tasks

## Overview
Sequential implementation tasks linked to requirements. Execute in order.

---

## Phase 1: Foundation

### T-001: Project Setup
**Requirement:** US-005 (Operational Reliability)  
**Status:** ✅ Complete

- [x] Create project directory structure
- [x] Create `pyproject.toml` with dependencies
- [x] Create virtual environment
- [x] Install dependencies
- [x] Create empty module files

---

### T-002: Alpaca Client
**Requirement:** US-001 (Core Trading Engine)  
**Status:** ✅ Complete

- [x] Implement `alpaca_client.py`
- [x] Load credentials from 1Password via `op` CLI
- [x] Implement `get_account()`
- [x] Implement `get_positions()`
- [x] Implement `get_bars()`
- [x] Implement `submit_order()`
- [x] Implement `get_clock()`

---

### T-003: Data Models
**Requirement:** US-001, US-002, US-003  
**Status:** ✅ Complete

- [x] Create `models.py` with dataclasses:
  - [x] `TradeSignal`
  - [x] `ValidationResult`
  - [x] `RiskConfig`
  - [x] `DailySummary`
  - [x] `Trade`

---

### T-004: Logger
**Requirement:** US-005 (Operational Reliability)  
**Status:** ✅ Complete

- [x] Implement `logger.py`
- [x] JSON Lines format output
- [x] Daily file rotation
- [x] Methods: `log_trade`, `log_signal`, `log_error`, `log_daily_summary`

---

## Phase 2: Risk Management

### T-005: Risk Manager
**Requirement:** US-002 (Risk Management)  
**Status:** ✅ Complete

- [x] Implement `risk_manager.py`
- [x] `validate_trade()` - check against limits
- [x] `calculate_position_size()` - max 10% of portfolio
- [x] `check_daily_limits()` - track daily P&L
- [x] `should_halt_trading()` - return true if -2% daily
- [x] Load config from `config/strategy.json`

---

### T-006: SQLite Database
**Requirement:** US-001 (Core Trading Engine)  
**Status:** ✅ Complete

- [x] Create `data/trades.db` schema
- [x] Implement trade insert function
- [x] Implement trade query functions
- [x] Implement daily P&L calculation from DB

---

## Phase 3: Strategy Framework

### T-007: Strategy Base
**Requirement:** US-003 (Strategy Framework)  
**Status:** ✅ Complete

- [x] Create `strategies/base.py` with `Strategy` protocol
- [x] Define `analyze()` method signature
- [x] Define `get_watchlist()` method signature

---

### T-008: Momentum Strategy
**Requirement:** US-003 (Strategy Framework)  
**Status:** ✅ Complete

- [x] Implement `strategies/momentum.py`
- [x] VWAP calculation
- [x] Volume confirmation logic
- [x] Signal generation with confidence score
- [x] Configurable parameters from JSON

---

### T-009: Mean Reversion Strategy
**Requirement:** US-003 (Strategy Framework)  
**Status:** ✅ Complete

- [x] Implement `strategies/mean_reversion.py`
- [x] RSI calculation
- [x] Oversold/overbought detection
- [x] Signal generation

---

### T-010: Strategy Manager
**Requirement:** US-003 (Strategy Framework)  
**Status:** ✅ Complete

- [x] Implement `strategy_manager.py`
- [x] Load strategies from config
- [x] Hot-reload on config change
- [x] Aggregate signals from all strategies
- [x] Track per-strategy performance

---

## Phase 4: Execution

### T-011: Order Executor
**Requirement:** US-001 (Core Trading Engine)  
**Status:** ✅ Complete

- [x] Implement `executor.py`
- [x] `submit_order()` - market orders
- [x] `cancel_order()`
- [x] `get_positions()`
- [x] `close_position()`
- [x] `close_all_positions()`

---

### T-012: Trailing Stop Logic
**Requirement:** US-002 (Risk Management)  
**Status:** ✅ Complete

- [x] Implement trailing stop updates in risk manager
- [x] Activate trailing stop at 2% profit
- [x] Trail at 1% below current price

---

## Phase 5: Orchestration

### T-013: Scheduler
**Requirement:** US-001 (Core Trading Engine)  
**Status:** ✅ Complete

- [x] Implement `scheduler.py`
- [x] Check market hours via Alpaca clock API
- [x] Schedule trading loop (every 1 minute)
- [x] Market open initialization
- [x] Market close cleanup

---

### T-014: Main Entry Point
**Requirement:** US-001, US-005  
**Status:** ✅ Complete

- [x] Implement `main.py`
- [x] Initialize all components
- [x] Start scheduler
- [x] Handle graceful shutdown (SIGTERM/SIGINT)
- [x] Write status.json on each iteration

---

## Phase 6: Deployment

### T-015: Configuration Files
**Requirement:** US-003, US-004  
**Status:** ✅ Complete

- [x] Create `config/strategy.json` with defaults
- [x] Create `config/daemon.plist`

---

### T-016: launchd Integration
**Requirement:** US-005 (Operational Reliability)  
**Status:** ✅ Complete

- [x] Create daemon plist file
- [x] Create start/stop scripts
- [x] Document start/stop commands

---

### T-017: Agent Check-in Cron
**Requirement:** US-004 (Agent Oversight)  
**Status:** ✅ Complete

- [x] Create cron job for morning check-in (8:30 AM CT)
- [x] Create cron job for mid-day check (12:00 PM CT)
- [x] Create cron job for EOD review (4:30 PM ET)

---

## Phase 7: Testing & Validation

### T-018: Unit Tests
**Requirement:** All  
**Status:** 🔲 Not Started

- [ ] Test risk manager calculations
- [ ] Test strategy signals
- [ ] Test position sizing
- [ ] Test daily limit tracking

---

### T-019: Integration Test
**Requirement:** All  
**Status:** 🔄 In Progress

- [x] Daemon started and running
- [ ] Verify order execution (waiting for market open)
- [x] Verify logging
- [x] Verify status.json updates

---

### T-020: Go Live
**Requirement:** All  
**Status:** 🔄 In Progress

- [x] System running
- [x] Live trading enabled
- [ ] Monitor first live trading day (Monday)
- [ ] Review daily report

---

## Task Status Legend

| Symbol | Meaning |
|--------|---------|
| 🔲 | Not Started |
| 🔄 | In Progress |
| ✅ | Complete |
| ❌ | Blocked |

---

## Progress Tracker

| Phase | Tasks | Complete | Progress |
|-------|-------|----------|----------|
| 1. Foundation | 4 | 4 | 100% |
| 2. Risk Management | 2 | 2 | 100% |
| 3. Strategy Framework | 4 | 4 | 100% |
| 4. Execution | 2 | 2 | 100% |
| 5. Orchestration | 2 | 2 | 100% |
| 6. Deployment | 3 | 3 | 100% |
| 7. Testing | 3 | 0 | 0% |
| **Total** | **20** | **17** | **85%** |

---

## Notes

---

## Phase 8: Self-Improvement & Autonomy

### T-021: Integrated Learning Loop
**Requirement:** US-006 (Self-Improvement)  
**Status:** ✅ Complete

- [x] Integrate `StrategyLearner` into `TradingScheduler`
- [x] Record all signals (executed and rejected)
- [x] Track P&L per strategy

### T-022: Automated Parameter Optimization
**Requirement:** US-006 (Self-Improvement)  
**Status:** 🔲 Not Started

- [ ] Implement backtesting script that iterates through parameter ranges
- [ ] Create weekend job to find "best fit" parameters for previous week
- [ ] Implement "Proposal" system where Jarvis suggests config changes

### T-023: Sentiment & Macro Integration
**Requirement:** US-006 (Self-Improvement)  
**Status:** 🔲 Not Started

- [ ] Integrate web search for earnings/macro news
- [ ] Adjust risk multiplier based on "Market Fear/Greed"
- [ ] Avoid trading symbols with pending high-volatility events

### 2026-02-19 (Self-Improvement)
- Ray requested long-term self-improvement and strategy adjustment.
- Integrated `StrategyLearner` into the live trading loop.
- Defined roadmap for automated backtesting and sentiment analysis.
