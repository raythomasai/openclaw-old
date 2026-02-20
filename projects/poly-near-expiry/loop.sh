#!/bin/bash
# Loop script for Polymarket Near-Expiry Bot
# Parameters: 1 week expiry, >= 70% odds

PROJECT_DIR="/Users/raythomas/.openclaw/workspace/projects/poly-near-expiry"
LOG_FILE="$PROJECT_DIR/output.log"

cd "$PROJECT_DIR"
source venv/bin/activate

echo "Starting Polymarket Loop: $(date)" | tee -a "$LOG_FILE"

while true; do
    echo "--- Evaluation Cycle: $(date) ---" >> "$LOG_FILE"
    python strategy.py >> "$LOG_FILE" 2>&1
    echo "Cycle complete. Waiting 1 hour..." >> "$LOG_FILE"
    sleep 3600
done
