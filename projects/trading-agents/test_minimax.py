#!/usr/bin/env python3
"""
Test script for TradingAgents with MiniMax
"""
import os
import sys

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

# Set the MiniMax API key from environment or config
os.environ["MINIMAX_API_KEY"] = os.getenv("MINIMAX_API_KEY", "")

# Now import and run
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Create a custom config for MiniMax
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "minimax"
config["deep_think_llm"] = "minimax/minimax-m2.1"
config["quick_think_llm"] = "minimax/minimax-m2.1"
config["backend_url"] = "https://api.minimax.io/anthropic"

print("Initializing TradingAgents with MiniMax...")
print(f"Provider: {config['llm_provider']}")
print(f"Deep Think LLM: {config['deep_think_llm']}")
print(f"Quick Think LLM: {config['quick_think_llm']}")
print(f"Backend URL: {config['backend_url']}")
print()

# Initialize the graph
ta = TradingAgentsGraph(debug=False, config=config)

print("Graph initialized successfully!")
print(f"Tickers available: {list(ta.tool_nodes.keys())}")
print()
print("TradingAgents is ready to run.")
print("\nTo run a trade analysis, call:")
print("  _, decision = ta.propagate('NVDA', '2024-05-10')")
print("  print(decision)")
