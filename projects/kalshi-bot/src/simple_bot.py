#!/usr/bin/env python3
"""
Simple Kalshi Trading Bot - Mechanical Arbitrage Strategy
Focused version that actually works
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load env vars
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().split('\n'):
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

# Settings
DEMO_MODE = os.getenv("KALSHI_USE_DEMO", "false").lower() == "true"
MAX_TRADE = float(os.getenv("MAX_TRADE_AMOUNT", "25"))
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "100"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleBot:
    """Simple trading bot focused on mechanical arbitrage"""
    
    def __init__(self):
        from src.kalshi_client import KalshiClient
        from pathlib import Path
        
        # Load credentials
        api_key = None
        private_key = None
        
        for line in (PROJECT_ROOT / ".env").read_text().split('\n'):
            if line.startswith('KALSHI_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
        
        key_file = PROJECT_ROOT / "kalshi-key.pem"
        if key_file.exists():
            private_key = key_file.read_text()
        
        self.client = KalshiClient(api_key, private_key, demo=DEMO_MODE)
        self.daily_pnl = 0
        self.daily_trades = 0
        self.positions = {}
        
    async def run(self):
        mode = "DEMO" if DEMO_MODE else "LIVE"
        balance = await self.client.get_balance()
        
        print("\n" + "=" * 60)
        print(f"KALSHI TRADING BOT - {mode} MODE")
        print("=" * 60)
        print(f"Starting Balance: ${balance.available_balance:,.2f}")
        print(f"Max Trade: ${MAX_TRADE}")
        print(f"Max Daily Loss: ${MAX_DAILY_LOSS}")
        print("=" * 60)
        
        # Main loop
        cycle = 0
        while self.daily_pnl > -MAX_DAILY_LOSS:
            cycle += 1
            print(f"\n--- Cycle {cycle} ---")
            
            # Get markets
            markets = await self.client._request("GET", "/trade-api/v2/markets")
            
            if not markets or 'markets' not in markets:
                print("No markets found")
                await asyncio.sleep(30)
                continue
            
            # Find good opportunities
            opportunities = []
            for m in markets['markets'][:100]:
                title = m.get('title', '')[:40]
                yes = m.get('yes_bid', 0) or m.get('yes_ask', 0)
                no = m.get('no_bid', 0) or m.get('no_ask', 0)
                volume = m.get('volume', 0)
                
                # Look for mispriced markets
                if yes > 0 and no > 0:
                    pair_cost = yes + no
                    
                    # Arbitrage opportunity
                    if pair_cost < 0.98:
                        opportunities.append({
                            'title': title,
                            'ticker': m.get('ticker', ''),
                            'yes': yes,
                            'no': no,
                            'pair_cost': pair_cost,
                            'volume': volume,
                            'arb': 1 - pair_cost
                        })
                    
                    # Cheap side (arbitrage potential)
                    if yes < 0.3 and volume > 1000:
                        opportunities.append({
                            'title': title,
                            'ticker': m.get('ticker', ''),
                            'yes': yes,
                            'no': no,
                            'pair_cost': pair_cost,
                            'volume': volume,
                            'arb': 0,
                            'signal': 'BUY YES (cheap)'
                        })
                    
                    if no < 0.3 and volume > 1000:
                        opportunities.append({
                            'title': title,
                            'ticker': m.get('ticker', ''),
                            'yes': yes,
                            'no': no,
                            'pair_cost': pair_cost,
                            'volume': volume,
                            'arb': 0,
                            'signal': 'BUY NO (cheap)'
                        })
            
            # Show top opportunities
            opportunities.sort(key=lambda x: x.get('arb', 0), reverse=True)
            
            if opportunities[:5]:
                print("Top Opportunities:")
                for i, opp in enumerate(opportunities[:5]):
                    if opp.get('arb', 0) > 0:
                        print(f"  {i+1}. [{opp['ticker'][:20]}] {opp['title'][:30]}")
                        print(f"      YES=${opp['yes']:.2f} NO=${opp['no']:.2f} PAIR=${opp['pair_cost']:.2f}")
                        print(f"      ✅ ARBITRAGE: {opp['arb']*100:.1f}% guaranteed if buy both sides")
                    else:
                        print(f"  {i+1}. [{opp['ticker'][:20]}] {opp['title'][:30]}")
                        print(f"      YES=${opp['yes']:.2f} NO=${opp['no']:.2f}")
                        print(f"      💡 {opp['signal']}")
            else:
                print("No significant opportunities found")
            
            print(f"\nDaily P&L: ${self.daily_pnl:.2f} | Trades: {self.daily_trades}")
            
            await asyncio.sleep(60)
        
        print("\n" + "=" * 60)
        print("STOPPED: Daily loss limit reached")
        print("=" * 60)


if __name__ == "__main__":
    bot = SimpleBot()
    asyncio.run(bot.run())
