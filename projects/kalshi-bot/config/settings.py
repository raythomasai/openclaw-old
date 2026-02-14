#!/usr/bin/env python3
"""
Kalshi Trading Bot Configuration
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Environment
KALSHI_USE_DEMO = os.getenv("KALSHI_USE_DEMO", "true").lower() == "true"
POLYNETMARKET_READ_ONLY = True  # Cannot trade, only read

# API Configuration
KALSHI_BASE_URL = "https://demo-api.kalshi.co/trade-api/v2" if KALSHI_USE_DEMO else "https://api.elections.kalshi.com/trade-api/v2"
POLYNETMARKET_BASE_URL = "https://api.polymarket.com"

# Position Sizing
MAX_TRADE_AMOUNT = float(os.getenv("MAX_TRADE_AMOUNT", "25.0"))  # Per trade
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "100.0"))  # Stop trading
MIN_TRADE_AMOUNT = 1.0  # Minimum trade size

# Strategy Thresholds
MOMENTUM_THRESHOLD = float(os.getenv("MOMENTUM_THRESHOLD", "0.05"))  # 5% price difference
WHALE_MIN_AMOUNT = float(os.getenv("WHALE_MIN_AMOUNT", "1000.0"))  # Only follow large positions
ARBITRAGE_THRESHOLD = float(os.getenv("ARBITRAGE_THRESHOLD", "0.03"))  # 3% for arb opportunities

# Polling Intervals (seconds)
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))
ARB_POLL_INTERVAL = int(os.getenv("ARB_POLL_INTERVAL", "60"))

# Logging
LOG_TRADES = True
LOG_PNL = True
LOG_LEVEL = "INFO"

# Risk Management
MAX_OPEN_POSITIONS = 10
DAILY_TRADE_LIMIT = 50
STOP_LOSS_PERCENT = 0.25  # Close if position drops 25%
TAKE_PROFIT_PERCENT = 0.50  # Take profit at 50%

# Demo Mode
DEMO_MODE = KALSHI_USE_DEMO  # When True, no real trades executed
