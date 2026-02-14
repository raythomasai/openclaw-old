#!/usr/bin/env python3
"""
Aggressive Rebalancing Strategy for Tomorrow

This script:
1. Sells all current positions at market open
2. Analyzes market conditions
3. Enters 1-2 concentrated positions (40-50% each)
4. Sets tight stops and profit targets

Run at 9:30 AM CT: python scripts/rebalance.py
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
from src.strategy_manager import StrategyManager
from src.risk_manager import RiskManager
from src.executor import OrderExecutor
from src.logger import TradingLogger


def get_market_analysis(client: AlpacaClient) -> dict:
    """Analyze market conditions for tomorrow."""
    watchlist = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA", "META", "AMD"]
    
    analysis = []
    
    for symbol in watchlist:
        try:
            bars = client.get_bars(symbol, timeframe="1Day", limit=5)
            if bars.empty:
                continue
            
            latest = bars.iloc[-1]
            prev = bars.iloc[-2] if len(bars) > 1 else latest
            
            # Calculate daily change
            daily_change = (latest['close'] - prev['close']) / prev['close'] * 100
            
            # Get volume
            avg_volume = bars['volume'].mean()
            volume_ratio = latest['volume'] / avg_volume if avg_volume > 0 else 1
            
            analysis.append({
                "symbol": symbol,
                "price": latest['close'],
                "daily_change": daily_change,
                "volume_ratio": volume_ratio,
                "momentum_score": daily_change * volume_ratio
            })
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
    
    # Sort by momentum
    analysis.sort(key=lambda x: x['momentum_score'], reverse=True)
    
    return analysis


def execute_aggressive_rebalance():
    """Execute the aggressive rebalancing strategy."""
    print("=" * 60)
    print("🚀 AGGRESSIVE REBALANCING - TOMORROW'S PLAN")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print()
    
    # Initialize
    client = AlpacaClient(paper=False)
    logger = TradingLogger()
    risk_manager = RiskManager()
    executor = OrderExecutor(client, logger)
    
    # Get current positions
    positions = client.get_positions()
    
    print(f"📊 CURRENT STATE:")
    print(f"   Portfolio: ${client.get_account().portfolio_value:.2f}")
    print(f"   Positions: {len(positions)}")
    print()
    
    # Step 1: Close all positions
    print("📤 CLOSING ALL POSITIONS:")
    total_exit_value = 0
    
    for pos in positions:
        print(f"   Closing {pos.symbol}...")
        success = executor.close_position(pos.symbol, reason="aggressive_rebalance")
        if success:
            total_exit_value += pos.current_price * pos.qty
    
    print(f"   Total exit value: ${total_exit_value:.2f}")
    print()
    
    # Step 2: Analyze market
    print("📈 MARKET ANALYSIS:")
    analysis = get_market_analysis(client)
    
    print("   Top momentum setups:")
    for i, a in enumerate(analysis[:5]):
        emoji = "🟢" if a['daily_change'] > 0 else "🔴"
        print(f"   {emoji} {a['symbol']}: ${a['price']:.2f} ({a['daily_change']:+.2f}%, vol: {a['volume_ratio']:.1f}x)")
    
    print()
    
    # Step 3: Select top 2 entries
    top_picks = analysis[:2]
    
    print("🎯 TOMORROW'S SETUPS:")
    portfolio = client.get_account().portfolio_value
    
    for i, pick in enumerate(top_picks):
        # Aggressive: 45% per position
        position_pct = 0.45
        position_size = portfolio * position_pct
        shares = position_size / pick['price']
        
        print(f"   {i+1}. {pick['symbol']}")
        print(f"      Entry: ${pick['price']:.2f}")
        print(f"      Size: ${position_size:.2f} ({position_pct*100:.0f}%)")
        print(f"      Shares: {shares:.4f}")
        print(f"      Stop: ${pick['price'] * 0.99:.2f} (-1%)")
        print(f"      Target: ${pick['price'] * 1.02:.2f} (+2%)")
        print()
    
    # Step 4: Save tomorrow's plan
    plan = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "market_analysis": analysis,
        "entries": [
            {
                "symbol": p["symbol"],
                "entry_price": p["price"],
                "position_pct": 0.45,
                "stop_loss": p["price"] * 0.99,
                "take_profit": p["price"] * 1.02
            }
            for p in top_picks
        ],
        "expected_return": sum(p["price"] * 0.02 * 0.45 for p in top_picks),
        "max_risk": sum(p["price"] * 0.01 * 0.45 for p in top_picks)
    }
    
    plan_file = PROJECT_DIR / "data" / "tomorrows_plan.json"
    with open(plan_file, "w") as f:
        json.dump(plan, f, indent=2)
    
    print("📁 Plan saved to:", plan_file)
    print()
    print("=" * 60)
    print("✅ READY FOR TOMORROW")
    print(f"   Expected return: ${plan['expected_return']:.2f} ({plan['expected_return']/portfolio*100:.2f}%)")
    print(f"   Max risk: ${plan['max_risk']:.2f} ({plan['max_risk']/portfolio*100:.2f}%)")
    print("=" * 60)
    
    return plan


if __name__ == "__main__":
    plan = execute_aggressive_rebalance()
    
    print("\n💡 TOMORROW MORNING:")
    print("   1. Run: ALPACA_API_KEY='...' ALPACA_API_SECRET='...' \\")
    print("      PYTHONPATH=. python scripts/execute_plan.py")
    print("   2. Monitor positions")
    print("   3. Exit at stop or target")
