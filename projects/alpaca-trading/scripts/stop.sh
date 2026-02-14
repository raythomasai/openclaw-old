#!/bin/bash
# Stop the trading daemon

PID=$(pgrep -f "python.*src/main.py" 2>/dev/null)
if [ -n "$PID" ]; then
    kill "$PID"
    echo "Stopped trading daemon (PID: $PID)"
else
    echo "Trading daemon not running"
fi
