# Kalshi Trading Bot

A Python trading bot that reads Polymarket prices as signals and executes trades on Kalshi.

## Features

- **Polymarket Reader**: Monitors Polymarket prices, whale activity, and order flow (read-only)
- **Kalshi Trader**: Executes trades on Kalshi using official API
- **Signal Engine**: Detects momentum, whale following, and arbitrage opportunities
- **Mechanical Arbitrage**: Implements the Gabagool method (buy YES/NO until cost < $1.00)
- **Risk Management**: Position limits, stop-loss, daily loss tracking

## Strategies

### 1. Momentum Following
- Monitor Polymarket price changes
- When Polymarket moves significantly, trade Kalshi in the same direction
- Expect Kalshi to catch up to Polymarket prices

### 2. Whale Following
- Track profitable wallets (ImJustKen, SwissMiss, fengdubiying)
- Mirror their large positions on Kalshi
- 1-2% allocation of whale position size

### 3. Mechanical Arbitrage (Gabagool Method)
- Track YES and NO quantities and costs
- Buy the cheap side when mispriced
- Stop when `avg_YES + avg_NO < $1.00` (guaranteed profit)

## Installation

```bash
# Clone or navigate to project directory
cd /Users/raythomas/.openclaw/workspace/projects/kalshi-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Set environment variables for API access:

```bash
export KALSHI_API_KEY=your_kalshi_api_key
export KALSHI_PRIVATE_KEY=your_kalshi_private_key
export POLYNETMARKET_PRIVATE_KEY=your_polymarket_private_key  # optional, read-only

# Demo mode (default) - no real money
export KALSHI_USE_DEMO=true

# Or live trading
export KALSHI_USE_DEMO=false
```

## Usage

### Demo Mode (Safe Testing)
```bash
./run.sh --demo
```

### Live Trading
```bash
./run.sh --live
```

### Python Direct
```bash
source venv/bin/activate
python3 src/main.py --demo
```

## Project Structure

```
kalshi-bot/
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration file
├── src/
│   ├── __init__.py
│   ├── polymarket_client.py  # Read-only Polymarket client
│   ├── kalshi_client.py      # Kalshi trading client
│   ├── signal_engine.py      # Signal detection
│   ├── mechanical_arbitrage.py  # Arbitrage strategy
│   ├── risk_manager.py       # Risk management
│   └── main.py               # Main orchestrator
├── logs/                      # Trading logs
├── data/                      # Data files
├── research/
│   └── strategies.md         # Strategy research
├── requirements.txt
├── run.sh
└── README.md
```

## Risk Settings

Default settings in `config/settings.py`:

```python
MAX_TRADE_AMOUNT = 25.0      # Max per trade
MAX_DAILY_LOSS = 100.0       # Stop trading if reached
MOMENTUM_THRESHOLD = 0.05    # 5% price difference to trigger
WHALE_MIN_AMOUNT = 1000.0    # Only follow large whale positions
ARB_THRESHOLD = 0.03          # 3% for arb opportunities
POLL_INTERVAL = 30            # Seconds between polls
```

## How It Works

1. **Fetch Data**: Bot polls Polymarket and Kalshi for market prices
2. **Generate Signals**: Detects momentum, whale activity, arbitrage
3. **Risk Check**: Each trade is checked against risk limits
4. **Execute**: Trades are placed on Kalshi
5. **Monitor**: Positions are tracked for P&L and risk

## Safety Features

- **Demo Mode**: All trades simulated, no real money
- **Risk Limits**: Max daily loss, max trade size, max positions
- **Stop-Loss**: Auto-close losing positions at 25% loss
- **Take-Profit**: Auto-close winning positions at 50% gain

## Disclaimer

This software is for educational and research purposes only. Trading prediction markets involves significant financial risk. You may lose some or all of your invested capital. Use at your own risk.

## References

- [Kalshi API Documentation](https://docs.kalshi.com/)
- [Polymarket Documentation](https://docs.polymarket.com/)
- [pmxt Library](https://github.com/qoery-com/pmxt)
- [Gabagool's Mechanical Arbitrage](https://www.reddit.com/r/PredictionsMarkets/comments/1phgdzd/inside_the_mind_of_a_polymarket_bot_100kmonth/)
