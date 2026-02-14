#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export KALSHI_USE_DEMO=false
export KALSHI_API_KEY=237d6215-e3b5-44b4-b97b-d3fd077f7e60
echo "Starting LIVE trading bot..."
python src/main.py
