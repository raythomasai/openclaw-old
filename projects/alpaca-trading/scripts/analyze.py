#!/usr/bin/env python3
"""
Performance analysis script for Jarvis check-ins.
Outputs a summary suitable for reviewing the trading system.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

def get_env_credentials():
    """Get credentials from environment or return None."""
    key = os.environ.get("ALPACA_API_KEY")
    secret = os.environ.get("ALPACA_API_SECRET")
    return (key, secret) if key and secret else None


def main():
    print("=" * 60)
    print("ALPACA TRADING SYSTEM - ANALYSIS REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # Check daemon status
    import subprocess
    result = subprocess.run(
        ["pgrep", "-f", "python.*src/main.py"],
        capture_output=True, text=True
    )
    daemon_running = result.returncode == 0
    daemon_pid = result.stdout.strip() if daemon_running else None
    
    print(f"🤖 DAEMON STATUS: {'✅ RUNNING (PID: ' + daemon_pid + ')' if daemon_running else '❌ NOT RUNNING'}")
    print()
    
    # Load status.json
    status_file = PROJECT_DIR / "logs" / "status.json"
    if status_file.exists():
        with open(status_file) as f:
            status = json.load(f)
        
        print("📊 CURRENT STATUS:")
        print(f"   Market Open: {status.get('market_open', 'unknown')}")
        print(f"   Trading Halted: {status.get('trading_halted', 'unknown')}")
        print(f"   Strategies: {', '.join(status.get('strategies_active', []))}")
        
        if 'account' in status:
            acc = status['account']
            print(f"\n💰 ACCOUNT:")
            print(f"   Portfolio Value: ${acc.get('portfolio_value', 0):.2f}")
            print(f"   Buying Power: ${acc.get('buying_power', 0):.2f}")
            print(f"   Daily P&L: ${acc.get('daily_pnl', 0):.2f} ({acc.get('daily_pnl_pct', 0):.2f}%)")
        
        if 'positions' in status:
            print(f"\n📈 POSITIONS ({status.get('position_count', len(status['positions']))}):")
            for p in status['positions'][:5]:  # Show top 5
                pnl = p.get('unrealized_pnl', 0)
                emoji = "🟢" if pnl >= 0 else "🔴"
                print(f"   {emoji} {p['symbol']}: {p['qty']:.4f} shares, P&L: ${pnl:.2f}")
            if len(status.get('positions', [])) > 5:
                print(f"   ... and {len(status['positions']) - 5} more")
        
        print(f"\n   Last Update: {status.get('timestamp', 'unknown')}")
    else:
        print("⚠️  No status.json found")
    
    print()
    
    # Analyze today's logs
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = PROJECT_DIR / "logs" / f"{today}.jsonl"
    
    if log_file.exists():
        print("📝 TODAY'S LOG ANALYSIS:")
        
        events = {"trade_executed": 0, "signal_generated": 0, "signal_rejected": 0, "error": 0}
        
        with open(log_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    event = entry.get("event", "")
                    if event in events:
                        events[event] += 1
                    elif entry.get("level") == "ERROR":
                        events["error"] += 1
                except:
                    pass
        
        print(f"   Trades Executed: {events['trade_executed']}")
        print(f"   Signals Generated: {events['signal_generated']}")
        print(f"   Signals Rejected: {events['signal_rejected']}")
        print(f"   Errors: {events['error']}")
    else:
        print(f"📝 No log file for today ({today})")
    
    print()
    
    # Database stats
    try:
        from src.database import TradeDatabase
        db = TradeDatabase()
        today_trades = db.get_trades_today()
        today_pnl = db.get_daily_pnl()
        
        print("🗄️  DATABASE:")
        print(f"   Trades Today: {len(today_trades)}")
        print(f"   Today's P&L: ${today_pnl:.2f}")
    except Exception as e:
        print(f"🗄️  Database: Error - {e}")
    
    print()
    print("=" * 60)
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if not daemon_running:
        print("   ⚠️  Daemon not running - consider starting it")
    
    # Check buying power constraint
    if status_file.exists():
        with open(status_file) as f:
            status = json.load(f)
        if 'account' in status:
            bp = status['account'].get('buying_power', 0)
            if bp < 10:
                print(f"   ⚠️  Low buying power (${bp:.2f}) - cannot open new positions")
                print("      Options: Add funds OR sell existing positions to free up capital")
    
    print()


if __name__ == "__main__":
    main()
