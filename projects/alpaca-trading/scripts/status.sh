#!/bin/bash
# Quick status check for Alpaca trading system

PROJECT_DIR="$HOME/.openclaw/workspace/projects/alpaca-trading"

echo "=== Alpaca Trading System Status ==="
echo

# Check if process is running
PID=$(pgrep -f "python.*src/main.py" 2>/dev/null)
if [ -n "$PID" ]; then
    echo "✅ Trading daemon: RUNNING (PID: $PID)"
else
    echo "❌ Trading daemon: NOT RUNNING"
fi

echo

# Check status.json
if [ -f "$PROJECT_DIR/logs/status.json" ]; then
    echo "📊 Status:"
    cat "$PROJECT_DIR/logs/status.json" | python3 -m json.tool 2>/dev/null
else
    echo "⚠️  No status.json found"
fi

echo

# Show recent logs
LOG_FILE="$PROJECT_DIR/logs/$(date +%Y-%m-%d).jsonl"
if [ -f "$LOG_FILE" ]; then
    echo "📝 Recent logs (last 5):"
    tail -5 "$LOG_FILE" | while read line; do
        echo "$line" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"  {d.get('timestamp','?')[:19]} [{d.get('level','?')}] {d.get('event','?')}\")" 2>/dev/null
    done
else
    echo "⚠️  No log file for today"
fi
