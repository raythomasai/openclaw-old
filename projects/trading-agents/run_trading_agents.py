#!/usr/bin/env python3
"""
TradingAgents with MiniMax - Quick Test Run

Usage:
    python run_trading_agents.py [ticker] [date]
    
Example:
    python run_trading_agents.py NVDA 2024-05-10
"""
import os
import sys

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Create a custom config for MiniMax
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = os.getenv("LLM_PROVIDER", "minimax")
config["deep_think_llm"] = os.getenv("DEEP_THINK_LLM", "minimax/minimax-m2.1")
config["quick_think_llm"] = os.getenv("QUICK_THINK_LLM", "minimax/minimax-m2.1")
config["backend_url"] = os.getenv("BACKEND_URL", "https://api.minimax.io/anthropic")

print("=" * 60)
print("TradingAgents with MiniMax")
print("=" * 60)
print(f"Provider: {config['llm_provider']}")
print(f"Deep Think LLM: {config['deep_think_llm']}")
print(f"Quick Think LLM: {config['quick_think_llm']}")
print(f"Backend URL: {config['backend_url']}")
print("=" * 60)

# Get ticker and date from command line or use defaults
ticker = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
trade_date = sys.argv[2] if len(sys.argv) > 2 else "2024-05-10"

print(f"\nAnalyzing {ticker} for {trade_date}...")
print()

# Initialize the graph
ta = TradingAgentsGraph(debug=False, config=config)

# Run the analysis
final_state, decision = ta.propagate(ticker, trade_date)

print()
print("=" * 60)
print("TRADING DECISION")
print("=" * 60)
print(decision)
print("=" * 60)

# Show the investment plan
print("\nInvestment Plan:")
print(final_state.get("investment_plan", "N/A"))
