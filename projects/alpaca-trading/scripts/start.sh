#!/bin/bash
# Start the trading daemon

PROJECT_DIR="$HOME/.openclaw/workspace/projects/alpaca-trading"
cd "$PROJECT_DIR"

# Check if already running
PID=$(pgrep -f "python.*src/main.py" 2>/dev/null)
if [ -n "$PID" ]; then
    echo "Trading daemon already running (PID: $PID)"
    exit 0
fi

# Activate venv and start
source .venv/bin/activate

# Try 1Password first, fall back to env file
if command -v op &> /dev/null; then
    export ALPACA_API_KEY=$(op item get "Alpaca" --fields "API Key" --reveal 2>/dev/null)
    export ALPACA_API_SECRET=$(op item get "Alpaca" --fields "API Secret" --reveal 2>/dev/null)
fi

# If 1Password didn't work, try env file
if [ -z "$ALPACA_API_KEY" ] && [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
fi

if [ -z "$ALPACA_API_KEY" ]; then
    echo "Error: Could not load Alpaca credentials"
    exit 1
fi

export PYTHONPATH="$PROJECT_DIR"
nohup python src/main.py > logs/stdout.log 2> logs/stderr.log &

echo "Started trading daemon (PID: $!)"
