# Alpaca Trading System - Requirements

## Overview
Automated trading system targeting **1% daily returns** on a **$462 live account** via Alpaca API.

---

## User Stories

### US-001: Core Trading Engine
**As a** trader  
**I want** an automated system that executes trades based on defined strategies  
**So that** I can generate returns without manual intervention

#### Acceptance Criteria (EARS Notation)

**[Ubiquitous]**
- The system shall connect to Alpaca live trading API using stored credentials
- The system shall only trade during US market hours (9:30 AM - 4:00 PM ET)
- The system shall log all trading activity to structured JSON files

**[Event-Driven]**
- When the market opens, the system shall initialize and begin monitoring for trade signals
- When a trade signal is detected, the system shall validate against risk controls before execution
- When a trade is executed, the system shall log entry price, quantity, and timestamp
- When the market closes, the system shall generate a daily performance report

**[State-Driven]**
- While buying power is below $10, the system shall not open new positions
- While daily loss exceeds 2%, the system shall halt all trading until next day
- While a position is open, the system shall monitor for exit signals

---

### US-002: Risk Management
**As a** trader  
**I want** strict risk controls to prevent catastrophic losses  
**So that** I preserve capital for future trading opportunities

#### Acceptance Criteria (EARS Notation)

**[Ubiquitous]**
- The system shall never risk more than 2% of portfolio value on a single trade
- The system shall maintain a maximum of 5 concurrent positions
- The system shall set a stop-loss on every trade (max 1.5% loss per position)

**[Event-Driven]**
- When daily P&L reaches -2%, the system shall close all positions and halt trading
- When a position hits stop-loss, the system shall immediately exit the position
- When a position gains 2%, the system shall trail the stop to lock in profits

**[State-Driven]**
- While portfolio is below $400 (drawdown protection), the system shall reduce position sizes by 50%

---

### US-003: Strategy Framework
**As a** trader  
**I want** a modular strategy framework  
**So that** I can test and deploy multiple strategies

#### Acceptance Criteria (EARS Notation)

**[Ubiquitous]**
- The system shall support multiple trading strategies via a plugin architecture
- The system shall load strategy parameters from a configuration file
- The system shall track performance metrics per strategy

**[Event-Driven]**
- When strategy parameters are updated, the system shall reload without restart
- When a strategy is disabled, the system shall close any positions opened by that strategy

**Initial Strategies:**
1. **Momentum Breakout**: Buy when price breaks above VWAP with volume confirmation
2. **Mean Reversion**: Buy oversold conditions (RSI < 30) on high-volume stocks

---

### US-004: Agent Oversight Integration
**As a** system operator (Jarvis)  
**I want** to monitor and adjust the trading system  
**So that** I can optimize strategy parameters based on performance

#### Acceptance Criteria (EARS Notation)

**[Ubiquitous]**
- The system shall expose a status endpoint readable via command line
- The system shall write performance data in a format parseable by the agent
- The system shall accept parameter updates via configuration file

**[Event-Driven]**
- When the agent updates config/strategy.json, the system shall apply changes within 60 seconds
- When the agent requests status, the system shall return current positions, P&L, and daily stats

---

### US-005: Operational Reliability
**As a** trader  
**I want** the system to run reliably as a background service  
**So that** it operates without constant supervision

#### Acceptance Criteria (EARS Notation)

**[Ubiquitous]**
- The system shall run as a launchd daemon on macOS
- The system shall automatically restart on failure
- The system shall not consume more than 100MB memory or 5% CPU on average

**[Event-Driven]**
- When the system starts, it shall verify API connectivity before trading
- When API connection fails, the system shall retry with exponential backoff
- When a critical error occurs, the system shall halt trading and log the error

---

## Non-Functional Requirements

### Performance
- Trade execution latency: < 500ms from signal to order submission
- Status queries: < 100ms response time

### Security
- API credentials stored in 1Password, retrieved at runtime via `op` CLI
- No credentials stored in plain text files

### Logging
- All logs written to `~/.openclaw/workspace/projects/alpaca-trading/logs/`
- Log rotation: daily files, keep 30 days
- Format: JSON lines (one JSON object per line)

### Data Storage
- Trade history: SQLite database
- Configuration: JSON files
- Performance metrics: JSON daily reports

---

## Constraints

| Constraint | Value |
|------------|-------|
| Starting Capital | $462.38 |
| Available Buying Power | $0.20 |
| Target Daily Return | 1% (~$4.62) |
| Max Daily Loss | 2% (~$9.25) |
| Trading Hours | 9:30 AM - 4:00 PM ET |
| Platform | macOS (arm64) |
| Language | Python 3.11+ |

---

## Out of Scope (v1)
- Options trading
- Crypto trading
- Pre/post market trading
- Short selling
- Margin trading beyond 1x

---

## Glossary

| Term | Definition |
|------|------------|
| VWAP | Volume Weighted Average Price |
| RSI | Relative Strength Index |
| PDT | Pattern Day Trader rule (3 day trades per 5 days for accounts < $25k) |
| Buying Power | Available funds for new positions |
