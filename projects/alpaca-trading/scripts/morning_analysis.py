#!/usr/bin/env python3
"""
Morning Routine - Run at 9:30 AM CT

This script:
1. Analyzes overnight market action
2. Identifies top 2 momentum setups
3. Generates tomorrow's rebalancing plan
4. Outputs a summary for review
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
from src.logger import TradingLogger


def analyze_overnight():
    """Analyze overnight and pre-market action."""
    print("=" * 60)
    print("🌅 MORNING ANALYSIS")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M CT')}")
    print("=" * 60)
    print()
    
    client = AlpacaClient(paper=False)
    account = client.get_account()
    
    print(f"💰 ACCOUNT:")
    print(f"   Portfolio: ${account.portfolio_value:.2f}")
    print(f"   Cash: ${account.cash:.2f}")
    print(f"   Daily P&L: ${account.daily_pnl:.2f} ({account.daily_pnl_pct:+.2f}%)")
    print()
    
    # Analyze watchlist
    watchlist = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA", "META", "AMD", "AMZN", "GOOGL"]
    
    analysis = []
    
    print("📈 MARKET SETUPS:")
    for symbol in watchlist:
        try:
            bars = client.get_bars(symbol, timeframe="1Day", limit=5)
            if bars.empty:
                continue
            
            latest = bars.iloc[-1]
            prev = bars.iloc[-2] if len(bars) > 1 else latest
            
            # Daily metrics
            daily_change = (latest['close'] - prev['close']) / prev['close'] * 100
            
            # Volume
            avg_volume = bars['volume'].mean()
            volume_ratio = latest['volume'] / avg_volume if avg_volume > 0 else 1
            
            # Momentum score
            momentum = daily_change * volume_ratio
            
            analysis.append({
                "symbol": symbol,
                "price": latest['close'],
                "daily_change": daily_change,
                "volume_ratio": volume_ratio,
                "momentum": momentum
            })
            
            emoji = "🟢" if daily_change > 0 else "🔴"
            print(f"   {emoji} {symbol}: ${latest['close']:.2f} ({daily_change:+.2f}%, vol: {volume_ratio:.1f}x)")
            
        except Exception as e:
            print(f"   ⚠️  {symbol}: {e}")
    
    # Sort by momentum
    analysis.sort(key=lambda x: x['momentum'], reverse=True)
    
    print()
    print("🎯 TOP SETUPS:")
    
    # Generate plan
    plan = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "account_value": account.portfolio_value,
        "analysis": analysis,
        "entries": []
    }
    
    for i, a in enumerate(analysis[:2]):
        # 45% position, 1% stop, 2% target
        position_pct = 0.45
        position_size = account.portfolio_value * position_pct
        shares = position_size / a['price']
        stop = a['price'] * 0.99
        target = a['price'] * 1.02
        
        expected_return = position_size * 0.02
        
        plan["entries"].append({
            "symbol": a["symbol"],
            "entry_price": a["price"],
            "shares": shares,
            "position_pct": position_pct,
            "stop_loss": stop,
            "take_profit": target,
            "expected_return": expected_return
        })
        
        emoji = "🥇" if i == 0 else "🥈"
        print(f"   {emoji} {a['symbol']}")
        print(f"      Price: ${a['price']:.2f}")
        print(f"      Position: ${position_size:.2f} ({position_pct*100:.0f}%)")
        print(f"      Shares: {shares:.4f}")
        print(f"      Stop: ${stop:.2f} (-1%)")
        print(f"      Target: ${target:.2f} (+2%)")
        print(f"      Expected: +${expected_return:.2f}")
        print()
    
    # Summary
    total_expected = sum(e["expected_return"] for e in plan["entries"])
    print("=" * 60)
    print("📊 PLAN SUMMARY")
    print(f"   Positions: {len(plan['entries'])}")
    print(f"   Expected Return: ${total_expected:.2f} ({total_expected/account.portfolio_value*100:.2f}%)")
    print(f"   Max Risk: ${account.portfolio_value * 0.02:.2f} (-2%)")
    print()
    
    if plan["entries"]:
        print("✅ READY TO EXECUTE")
        print("   Run: python scripts/execute_plan.py")
    else:
        print("⚠️  No clear setups found")
    
    print("=" * 60)
    
    # Save plan
    plan_file = PROJECT_DIR / "data" / "morning_plan.json"
    with open(plan_file, "w") as f:
        json.dump(plan, f, indent=2)
    
    print(f"\n📁 Plan saved to: {plan_file}")
    
    return plan


if __name__ == "__main__":
    plan = analyze_overnight()
