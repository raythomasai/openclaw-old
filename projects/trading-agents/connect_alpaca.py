#!/usr/bin/env python3
"""
TradingAgents → Alpaca Connector

This script:
1. Runs TradingAgents analysis on a ticker
2. Parses the trading decision (buy/sell/hold)
3. Executes orders via Alpaca API
"""
import os
import sys
import re
from datetime import datetime, date
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add projects to path
sys.path.insert(0, '/Users/raythomas/.openclaw/workspace/projects')

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Alpaca imports
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading import GetAssetsRequest

# Configure TradingAgents
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = os.getenv("LLM_PROVIDER", "minimax")
config["deep_think_llm"] = os.getenv("DEEP_THINK_LLM", "minimax/minimax-m2.1")
config["quick_think_llm"] = os.getenv("QUICK_THINK_LLM", "minimax/minimax-m2.1")
config["backend_url"] = os.getenv("BACKEND_URL", "https://api.minimax.io/anthropic")


class TradingAgentsAlpacaConnector:
    def __init__(self):
        # Initialize TradingAgents
        self.ta = TradingAgentsGraph(debug=False, config=config)
        
        # Initialize Alpaca
        self.alpaca = TradingClient(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_API_SECRET"),
            paper=os.getenv("ALPACA_PAPER", "true").lower() == "true"
        )
        
    def get_signal(self, ticker: str, trade_date: str = None) -> dict:
        """Run TradingAgents and extract signal."""
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y-%m-%d")
            
        print(f"\n{'='*60}")
        print(f"Running TradingAgents analysis for {ticker}")
        print(f"{'='*60}")
        
        final_state, decision = self.ta.propagate(ticker, trade_date)
        
        # Parse the decision
        signal = self._parse_decision(decision, final_state)
        
        return {
            "ticker": ticker,
            "date": trade_date,
            "raw_decision": decision,
            "signal": signal.get("action", "hold"),
            "confidence": signal.get("confidence", 0.0),
            "position_size": signal.get("position_size", 0.0),
            "investment_plan": final_state.get("investment_plan", ""),
            "final_trade_decision": final_state.get("final_trade_decision", ""),
        }
    
    def _parse_decision(self, decision: str, state: dict) -> dict:
        """Parse TradingAgents decision into structured signal."""
        decision_lower = decision.lower()
        
        # Extract action
        if "buy" in decision_lower and "sell" not in decision_lower:
            action = "buy"
        elif "sell" in decision_lower:
            action = "sell"
        else:
            action = "hold"
        
        # Extract confidence (look for percentage or confidence level)
        confidence = 0.5  # default
        confidence_match = re.search(r'(\d+)%', decision)
        if confidence_match:
            confidence = int(confidence_match.group(1)) / 100
        
        # Extract position size from investment plan
        position_size = 0.0
        investment_plan = state.get("investment_plan", "")
        if investment_plan:
            # Look for dollar amounts or percentages
            dollar_match = re.search(r'\$([\d,]+)', investment_plan)
            if dollar_match:
                position_size = float(dollar_match.group(1).replace(',', ''))
        
        return {
            "action": action,
            "confidence": confidence,
            "position_size": position_size,
        }
    
    def get_current_positions(self) -> dict:
        """Get current open positions."""
        positions = self.alpaca.get_all_positions()
        return {
            p.symbol: {
                "qty": float(p.qty),
                "side": p.side.value,
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
            }
            for p in positions
        }
    
    def execute_signal(self, signal: dict, max_risk_pct: float = 0.01) -> dict:
        """Execute the TradingAgents signal via Alpaca.
        
        Conservative parameters for initial trading:
        - max_risk_pct: 1% of portfolio (very conservative)
        - min_confidence: 70% (only act on high-conviction signals)
        """
        ticker = signal["ticker"]
        action = signal["signal"]
        confidence = signal.get("confidence", 0.0)
        
        if action == "hold":
            print(f"\n⚠️  Signal is HOLD - no trade executed")
            return {"status": "skipped", "reason": "hold_signal"}
        
        # Confidence threshold check (conservative: 70%+)
        min_confidence = 0.70
        if confidence < min_confidence:
            print(f"\n⚠️  Confidence {confidence:.0%} below threshold {min_confidence:.0%}")
            return {"status": "skipped", "reason": "low_confidence"}
        
        # Get current positions
        positions = self.get_current_positions()
        
        # Check if we already have a position
        has_position = ticker in positions
        
        if action == "sell" and not has_position:
            print(f"\n⚠️  Sell signal but no position in {ticker}")
            return {"status": "skipped", "reason": "no_position_to_sell"}
        
        # Get account info
        account = self.alpaca.get_account()
        buying_power = float(account.buying_power)
        portfolio_value = float(account.portfolio_value)
        
        # Calculate position size (conservative risk management)
        # Use max 1% of portfolio per trade, with additional 50% safety margin
        safety_margin = 0.50  # Only use 50% of allocated risk
        max_position_value = portfolio_value * max_risk_pct * safety_margin
        
        # Get current price
        bars = self.alpaca.get_latest_trade(ticker)
        current_price = float(bars.price)
        qty = int(max_position_value / current_price)
        
        if qty <= 0:
            print(f"\n⚠️  Position size too small ({qty})")
            return {"status": "skipped", "reason": "position_too_small"}
        
        # Execute order
        order_side = OrderSide.BUY if action == "buy" else OrderSide.SELL
        
        # Use market order for simplicity
        order = MarketOrderRequest(
            symbol=ticker,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY
        )
        
        try:
            response = self.alpaca.submit_order(order)
            print(f"\n✅ Order submitted successfully!")
            print(f"   Symbol: {ticker}")
            print(f"   Action: {action.upper()}")
            print(f"   Quantity: {qty}")
            print(f"   Order ID: {response.id}")
            
            return {
                "status": "submitted",
                "order_id": response.id,
                "ticker": ticker,
                "action": action,
                "qty": qty,
            }
        except Exception as e:
            print(f"\n❌ Order failed: {e}")
            return {"status": "failed", "error": str(e)}


def main():
    """Main entry point."""
    connector = TradingAgentsAlpacaConnector()
    
    # Get ticker from command line or use default
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    
    # Run analysis and get signal
    signal = connector.get_signal(ticker)
    
    print(f"\n{'='*60}")
    print("TRADING SIGNAL")
    print(f"{'='*60}")
    print(f"Ticker: {signal['ticker']}")
    print(f"Action: {signal['signal'].upper()}")
    print(f"Confidence: {signal['confidence']:.0%}")
    print(f"{'='*60}")
    
    # Execute if not in paper mode
    paper_mode = os.getenv("ALPACA_PAPER", "true").lower() == "true"
    
    if paper_mode:
        print(f"\n📝 Paper mode - would execute: {signal['signal']} {signal['ticker']}")
    else:
        print(f"\n🚀 Live mode - executing trade...")
        result = connector.execute_signal(signal)
        print(f"\nResult: {result['status']}")


if __name__ == "__main__":
    main()
