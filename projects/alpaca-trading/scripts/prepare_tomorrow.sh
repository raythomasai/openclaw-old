#!/bin/bash
# Quick start script - generates tomorrow's plan
# Usage: ./scripts/prepare_tomorrow.sh

cd "$(dirname "$0")"

# Set credentials if available
if [ -f .env ]; then
    source .env
fi

# Run morning analysis
echo "Generating tomorrow's plan..."
PYTHONPATH=. python scripts/morning_analysis.py

echo ""
echo "=== TOMORROW'S WORKFLOW ==="
echo "1. Review the plan above"
echo "2. At 9:30 AM CT: ALPACA_API_KEY='...' ALPACA_API_SECRET='...' PYTHONPATH=. python scripts/execute_plan.py"
echo "3. Monitor throughout the day"
echo ""
