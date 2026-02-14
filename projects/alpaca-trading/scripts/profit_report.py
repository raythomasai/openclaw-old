#!/usr/bin/env python3
"""
Hourly profit report - posts current P&L status.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.database import TradeDatabase
from src.learner import StrategyLearner


def get_env_credentials():
    """Get credentials from environment."""
    key = os.environ.get("ALPACA_API_KEY")
    secret = os.environ.get("ALPACA_API_SECRET")
    return (key, secret) if key and secret else None


def main():
    """Generate and output profit report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M CT")
    
    print("=" * 60)
    print(f"📊 ALPACA TRADING - HOURLY REPORT")
    print(f"   {now}")
    print("=" * 60)
    
    # Load status
    status_file = PROJECT_DIR / "logs" / "status.json"
    if status_file.exists():
        with open(status_file) as f:
            status = json.load(f)
        
        print()
        
        if 'account' in status:
            acc = status['account']
            portfolio = acc.get('portfolio_value', 0)
            daily_pnl = acc.get('daily_pnl', 0)
            daily_pct = acc.get('daily_pnl_pct', 0)
            bp = acc.get('buying_power', 0)
            
            print(f"💰 PORTFOLIO: ${portfolio:,.2f}")
            print(f"📈 DAILY P&L:  ${daily_pnl:,.2f} ({daily_pct:+.2f}%)")
            print(f"💵 BUYING POWER: ${bp:,.2f}")
            
            # Emoji based on performance
            if daily_pct > 0.5:
                emoji = "🟢 CRUSHING IT"
            elif daily_pct > 0:
                emoji = "🟢 GREEN"
            elif daily_pct > -0.5:
                emoji = "🟡 HOLDING"
            elif daily_pct > -1:
                emoji = "🟠 CAUTION"
            else:
                emoji = "🔴 STOP LOSS RISK"
            
            print(f"   {emoji}")
        
        if 'positions' in status:
            positions = status['positions']
            pos_count = status.get('position_count', len(positions))
            
            print()
            print(f"📈 POSITIONS: {pos_count}")
            
            # Best/worst
            if positions:
                best = max(positions, key=lambda p: p.get('unrealized_pnl', 0))
                worst = min(positions, key=lambda p: p.get('unrealized_pnl', 0))
                
                print(f"   🏆 Best:  {best['symbol']} ${best.get('unrealized_pnl', 0):+.2f}")
                print(f"   ⚠️  Worst: {worst['symbol']} ${worst.get('unrealized_pnl', 0):+.2f}")
    
    print()
    print("-" * 60)
    
    # Database stats
    try:
        db = TradeDatabase()
        today_trades = db.get_trades_today()
        
        print(f"🗄️  TRADES TODAY: {len(today_trades)}")
        
        if today_trades:
            closed = [t for t in today_trades if t.get('status') == 'filled']
            wins = [t for t in closed if t.get('pnl', 0) > 0]
            losses = [t for t in closed if t.get('pnl', 0) < 0]
            
            if closed:
                win_rate = len(wins) / len(closed) * 100
                print(f"   Win Rate: {win_rate:.0f}% ({len(wins)}/{len(closed)})")
    
    except Exception as e:
        print(f"⚠️  Database error: {e}")
    
    print()
    
    # Learning insights
    try:
        learner = StrategyLearner()
        recommendations = learner.get_recommendations()
        if recommendations:
            print("💡 INSIGHTS:")
            for rec in recommendations[:3]:
                print(f"   • {rec}")
        else:
            print("💡 Gathering data for insights...")
    
    except Exception as e:
        pass
    
    print()
    print("=" * 60)
    
    # Target comparison
    print(f"🎯 DAILY TARGET: 1.00%")
    print("=" * 60)


if __name__ == "__main__":
    main()
