# Alpaca Trading System

Automated trading system targeting 1% daily returns via Alpaca API.

## Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Set credentials (or use 1Password integration)
export ALPACA_API_KEY="your_key"
export ALPACA_API_SECRET="your_secret"

# Run
PYTHONPATH=. python src/main.py
```

## Install as Daemon

```bash
# Copy plist
cp config/daemon.plist ~/Library/LaunchAgents/com.openclaw.alpaca-trader.plist

# Load (starts immediately)
launchctl load ~/Library/LaunchAgents/com.openclaw.alpaca-trader.plist

# Check status
launchctl list | grep alpaca

# Stop
launchctl unload ~/Library/LaunchAgents/com.openclaw.alpaca-trader.plist
```

## Configuration

Edit `config/strategy.json` to adjust:
- Risk parameters (max position size, daily loss limit)
- Strategy parameters (watchlist, indicators)
- Trading schedule

Changes are auto-reloaded every minute.

## Monitoring

```bash
# View logs
tail -f logs/$(date +%Y-%m-%d).jsonl

# Check status
cat logs/status.json | jq
```

## Architecture

```
src/
├── main.py            # Entry point
├── alpaca_client.py   # Alpaca API wrapper
├── strategy_manager.py # Strategy orchestration
├── risk_manager.py    # Risk controls
├── executor.py        # Order execution
├── scheduler.py       # Market hours scheduling
├── logger.py          # JSON logging
├── models.py          # Data classes
└── strategies/
    ├── momentum.py    # Momentum breakout
    └── mean_reversion.py
```

## Account Info

- Portfolio: ~$462
- Positions: 10 stocks
- Mode: **LIVE TRADING**
