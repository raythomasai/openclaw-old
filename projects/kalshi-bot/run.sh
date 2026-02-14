#!/bin/bash
# Kalshi Trading Bot Runner

# Set working directory
cd "$(dirname "$0")"

# Check for Python virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Parse arguments
DEMO=true
LIVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --live)
            DEMO=false
            LIVE=true
            shift
            ;;
        --demo)
            DEMO=true
            LIVE=false
            shift
            ;;
        --help|-h)
            echo "Usage: ./run.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --live    Use live trading (requires API keys)"
            echo "  --demo    Use demo mode (default)"
            echo "  --help    Show this help"
            echo ""
            echo "Environment variables:"
            echo "  KALSHI_API_KEY       Your Kalshi API key"
            echo "  KALSHI_PRIVATE_KEY   Your Kalshi private key"
            echo "  POLYNETMARKET_PRIVATE_KEY  Polymarket private key (read-only)"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set environment variables if not already set
export KALSHI_USE_DEMO=$DEMO

# Check if API keys are set
if [ "$LIVE" = true ]; then
    if [ -z "$KALSHI_API_KEY" ] || [ -z "$KALSHI_PRIVATE_KEY" ]; then
        echo "ERROR: Live trading requires KALSHI_API_KEY and KALSHI_PRIVATE_KEY"
        echo ""
        echo "Set environment variables:"
        echo "  export KALSHI_API_KEY=your_api_key"
        echo "  export KALSHI_PRIVATE_KEY=your_private_key"
        exit 1
    fi
    echo "⚠️  LIVE TRADING MODE - Real money at risk!"
else
    echo "✓ Demo mode - No real money at risk"
fi

# Create required directories
mkdir -p logs
mkdir -p data

# Run the bot
echo "Starting Kalshi Trading Bot..."
python3 src/main.py --demo=$DEMO --live=$LIVE
