#!/usr/bin/env python3
"""
Execute Tomorrow's Plan
Run at 9:30 AM CT to execute the aggressive rebalancing plan.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.alpaca_client import AlpacaClient
from src.executor import OrderExecutor
from src.logger import TradingLogger


def execute_plan():
    """Execute tomorrow's trading plan."""
    print("=" * 60)
    print("🚀 EXECUTING AGGRESSIVE REBALANCING PLAN")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # Load plan
    plan_file = PROJECT_DIR / "data" / "tomorrows_plan.json"
    
    if not plan_file.exists():
        print("❌ No plan found! Run rebalance.py first.")
        return
    
    with open(plan_file) as f:
        plan = json.load(f)
    
    print(f"📋 Plan for {plan['date']}")
    print()
    
    # Initialize
    client = AlpacaClient(paper=False)
    logger = TradingLogger()
    executor = OrderExecutor(client, logger)
    
    # Check positions
    positions = client.get_positions()
    
    if positions:
        print("⚠️  Existing positions detected!")
        print("   Closing all positions first...")
        for pos in positions:
            executor.close_position(pos.symbol, reason="plan_execution")
        print()
    
    # Get account
    account = client.get_account()
    print(f"💰 Available capital: ${account.portfolio_value:.2f}")
    print()
    
    # Execute entries
    print("📤 EXECUTING ENTRIES:")
    executed = []
    
    for i, entry in enumerate(plan.get("entries", [])):
        symbol = entry["symbol"]
        target_price = entry["entry_price"]
        shares = (account.portfolio_value * entry["position_pct"]) / target_price
        
        print(f"   {i+1}. {symbol}")
        print(f"      Target: ${target_price:.2f}")
        print(f"      Shares: {shares:.4f}")
        
        try:
            # Get current price
            bars = client.get_bars(symbol, timeframe="1Min", limit=1)
            if not bars.empty:
                current_price = bars.iloc[0]['close']
                print(f"      Current: ${current_price:.2f}")
                
                # Execute market order
                if current_price <= target_price * 1.02:  # Within 2% of target
                    result = executor.submit_order(
                        type("Signal", (), {
                            "symbol": symbol,
                            "side": "buy",
                            "strategy_name": "aggressive_rebalance",
                            "confidence": 0.9,
                            "entry_price": current_price
                        })(),
                        qty=shares
                    )
                    
                    if result:
                        executed.append(symbol)
                        print(f"      ✅ Executed: {result.order_id}")
                    else:
                        print(f"      ❌ Failed to execute")
                else:
                    print(f"      ⚠️  Price too high, skipping")
            else:
                print(f"      ❌ No price data")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        print()
    
    # Summary
    print("=" * 60)
    print("📊 EXECUTION SUMMARY")
    print(f"   Entries attempted: {len(plan.get('entries', []))}")
    print(f"   Entries executed: {len(executed)}")
    print(f"   Symbols: {', '.join(executed)}")
    print()
    
    if executed:
        print("💡 NEXT STEPS:")
        print("   1. Monitor positions")
        print("   2. Exit at stop (1% loss) OR target (+2% gain)")
        print("   3. No additional entries today")
    
    print("=" * 60)
    
    return executed


if __name__ == "__main__":
    execute_plan()
