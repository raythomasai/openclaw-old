# IBKR Options Trading Bot

Aggressive dual-sided momentum options trading bot using Interactive Brokers API.

## Setup

```bash
# Clone/create project
cd projects/ibkr-options-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## IBKR Setup

1. **Download IB Gateway** from interactivebrokers.com
2. **Log in** to paper trading account
3. **Configure API access:**
   - Settings → API → Enable "Enable ActiveX and Socket Clients"
   - Set port to `7497` (paper) or `7496` (live)
4. **Subscribe** to market data:
   - US Securities Snapshot Bundle
   - US Options Add-On

## Configuration

Edit `config/config.yaml`:

```yaml
ibkr:
  host: "127.0.0.1"
  port: 7497  # paper
  mode: "paper"

strategy:
  max_positions: 10
  max_allocation_per_trade: 0.08

risk:
  max_daily_loss_pct: 0.05
  max_loss_per_trade: 0.02
```

## Running

```bash
# Test connection
python src/main.py --test

# Dry run (no trading)
python src/main.py --dry-run

# Start trading
python src/main.py
```

## Strategies

- **Gap Up/Down:** Trade stocks gapping 2%+
- **RSI Reversal:** Oversold bounces / Overbought fades
- **VWAP Breakout:** Momentum through VWAP

## Risk Controls

- 5% daily loss limit
- 2% stop loss per trade
- 3% profit target
- Max 10 concurrent positions

## Warning

⚠️ This is aggressive trading software. You can lose money.
Paper trade first. Never risk more than you can afford.
