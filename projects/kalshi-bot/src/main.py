#!/usr/bin/env python3
"""
Kalshi Trading Bot - Main Orchestrator
Combines Polymarket signals with Kalshi execution
"""

import os
import sys
import asyncio
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from .env file FIRST (before config imports)
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(str(env_file))
    except ImportError:
        # Fallback to line-by-line parsing
        for line in env_file.read_text().split('\n'):
            if '=' in line and not line.strip().startswith('#'):
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()

from config.settings import (
    PROJECT_ROOT, LOGS_DIR, DEMO_MODE,
    KALSHI_USE_DEMO, MAX_TRADE_AMOUNT, MAX_DAILY_LOSS,
    POLL_INTERVAL, MOMENTUM_THRESHOLD, WHALE_MIN_AMOUNT
)

from src.polymarket_client import PolymarketClient, get_polymarket_prices
from src.kalshi_client import KalshiClient
from src.signal_engine import SignalEngine, SignalAggregator, SignalType
from src.mechanical_arbitrage import MechanicalArbitrage
from src.risk_manager import RiskManager, TradeRequest

# Configure logging
LOG_DIR = LOGS_DIR
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"kalshi_bot_{datetime.now():%Y%m%d}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class KalshiTradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self, demo: bool = True):
        self.demo = demo
        
        # Initialize clients
        self.poly_client = PolymarketClient(
            private_key=os.getenv("POLYNETMARKET_PRIVATE_KEY"),
            demo=demo
        )
        
        self.kalshi_client = KalshiClient(
            api_key=os.getenv("KALSHI_API_KEY"),
            private_key=os.getenv("KALSHI_PRIVATE_KEY"),
            demo=demo
        )
        
        # Initialize components
        self.signal_engine = SignalEngine({
            "momentum_threshold": MOMENTUM_THRESHOLD,
            "whale_min_amount": WHALE_MIN_AMOUNT,
            "arb_threshold": 0.03
        })
        
        self.arbitrage_engine = MechanicalArbitrage({
            "max_trade_amount": MAX_TRADE_AMOUNT,
            "arb_threshold": 0.02
        })
        
        self.risk_manager = RiskManager({
            "max_trade_amount": MAX_TRADE_AMOUNT,
            "max_daily_loss": MAX_DAILY_LOSS,
            "daily_trade_limit": 50,
            "max_open_positions": 10,
            "stop_loss_percent": 0.25,
            "take_profit_percent": 0.50
        })
        
        # State
        self.running = False
        self.market_cache: Dict[str, Dict] = {}
        self.last_poll = datetime.now()
        
        # Stats
        self.stats = {
            "start_time": None,
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0.0,
            "signals_processed": 0,
            "errors": 0
        }
    
    async def start(self):
        """Start the trading bot"""
        logger.info("=" * 60)
        logger.info("KALSHI TRADING BOT STARTING")
        logger.info(f"Demo Mode: {self.demo}")
        logger.info("=" * 60)
        
        self.running = True
        self.stats["start_time"] = datetime.now()
        
        # Check balance
        balance = await self.kalshi_client.get_balance()
        logger.info(f"Starting Balance: ${balance.available_balance:.2f}")
        
        # Main loop
        try:
            while self.running:
                await self._poll_cycle()
                await asyncio.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.shutdown()
    
    async def _poll_cycle(self):
        """Main polling cycle"""
        try:
            # Fetch market data
            await self._fetch_market_data()
            
            # Generate signals
            signals = await self._generate_signals()
            
            # Execute trades
            trades_executed = await self._execute_signals(signals)
            
            # Run mechanical arbitrage
            await self._run_arbitrage()
            
            # Check risk limits
            self._check_risk_limits()
            
            # Log stats
            self._log_stats(trades_executed)
            
        except Exception as e:
            logger.error(f"Error in poll cycle: {e}")
            self.stats["errors"] += 1
    
    async def _fetch_market_data(self):
        """Fetch current market data from both platforms"""
        try:
            # Get trending events from Kalshi
            events = await self.kalshi_client.get_trending_events()
            
            for event in events[:20]:  # Top 20 events
                event_id = event.get("id")
                if not event_id:
                    continue
                
                # Get markets for event
                markets = await self.kalshi_client.get_markets_by_event(event_id)
                
                for market in markets:
                    market_id = market.get("id") or market.get("market_id")
                    if not market_id:
                        continue
                    
                    # Cache market data
                    self.market_cache[market_id] = {
                        "market": market,
                        "event_id": event_id,
                        "fetched_at": datetime.now()
                    }
            
            logger.debug(f"Fetched {len(self.market_cache)} markets")
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
    
    async def _generate_signals(self) -> List:
        """Generate trading signals from Polymarket data"""
        signals = []
        
        try:
            # Get Polymarket trending
            poly_markets = await self.poly_client.get_trending_markets(limit=50)
            
            for poly_market in poly_markets:
                poly_id = poly_market.get("id") or poly_market.get("market_id")
                if not poly_id:
                    continue
                
                # Get current price
                poly_price = await self.poly_client.get_market_price(poly_id)
                
                if not poly_price:
                    continue
                
                # Check for momentum
                momentum = await self.poly_client.get_price_momentum(poly_id)
                
                # Generate signals
                if abs(momentum.get("5min", 0)) > MOMENTUM_THRESHOLD:
                    signals.append({
                        "type": SignalType.MOMENTUM,
                        "poly_market_id": poly_id,
                        "poly_yes": poly_price.yes_price,
                        "momentum": momentum.get("5min", 0),
                        "confidence": min(abs(momentum["5min"]) * 5, 0.9)
                    })
                
                self.stats["signals_processed"] += 1
            
            logger.debug(f"Generated {len(signals)} signals")
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
        
        return signals
    
    async def _execute_signals(self, signals: List) -> int:
        """Execute trading signals"""
        trades = 0
        
        for signal in signals:
            try:
                if signal["type"] == SignalType.MOMENTUM:
                    # Follow Polymarket momentum
                    market_id = signal["poly_market_id"]
                    poly_yes = signal["poly_yes"]
                    momentum = signal["momentum"]
                    
                    # Find corresponding Kalshi market
                    kalshi_market = await self._find_kalshi_market(market_id)
                    
                    if not kalshi_market:
                        continue
                    
                    kalshi_id = kalshi_market.get("id") or kalshi_market.get("market_id")
                    
                    # Determine side
                    side = "yes" if momentum > 0 else "no"
                    
                    # Check confidence
                    if signal["confidence"] < 0.5:
                        continue
                    
                    # Create trade request
                    request = TradeRequest(
                        market_id=kalshi_id,
                        side=side,
                        amount=MAX_TRADE_AMOUNT,
                        price=kalshi_market.get("yes_price" if side == "yes" else "no_price", 0.5),
                        strategy="momentum",
                        signal_confidence=signal["confidence"]
                    )
                    
                    # Risk check
                    approved, reason = self.risk_manager.assess_risk(request)
                    
                    if not approved:
                        logger.debug(f"Trade rejected: {reason}")
                        continue
                    
                    # Execute trade
                    if side == "yes":
                        order = await self.kalshi_client.buy_yes(
                            kalshi_id, request.amount, request.price
                        )
                    else:
                        order = await self.kalshi_client.buy_no(
                            kalshi_id, request.amount, request.price
                        )
                    
                    if order.status in ["filled", "pending"]:
                        self.risk_manager.update_position(
                            market_id=kalshi_id,
                            side=side,
                            amount=request.amount,
                            price=request.price
                        )
                        
                        logger.info(f"EXECUTED: {side.upper()} {request.amount} @ {request.price} on {kalshi_id}")
                        trades += 1
                        self.stats["total_trades"] += 1
            
            except Exception as e:
                logger.error(f"Error executing signal: {e}")
                self.stats["errors"] += 1
        
        return trades
    
    async def _run_arbitrage(self):
        """Run mechanical arbitrage on Kalshi markets"""
        try:
            for market_id, cache_data in self.market_cache.items():
                market = cache_data["market"]
                
                yes_price = market.get("yes_price", 0.5)
                no_price = market.get("no_price", 0.5)
                
                # Check for arbitrage opportunity
                result = self.arbitrage_engine.analyze_market(
                    yes_price, no_price, market_id
                )
                
                if result:
                    side, amount, expected_profit = result
                    
                    if expected_profit < 0.01:
                        continue  # Not worth it
                    
                    # Create trade request
                    request = TradeRequest(
                        market_id=market_id,
                        side=side,
                        amount=min(amount, MAX_TRADE_AMOUNT),
                        price=yes_price if side == "yes" else no_price,
                        strategy="arbitrage",
                        signal_confidence=0.95
                    )
                    
                    # Risk check
                    approved, _ = self.risk_manager.assess_risk(request)
                    if not approved:
                        continue
                    
                    # Execute
                    if side == "yes":
                        order = await self.kalshi_client.buy_yes(
                            market_id, amount, yes_price
                        )
                    else:
                        order = await self.kalshi_client.buy_no(
                            market_id, amount, no_price
                        )
                    
                    if order.status in ["filled", "pending"]:
                        self.arbitrage_engine.execute_buy(
                            market_id, side, amount, 
                            yes_price if side == "yes" else no_price
                        )
                        
                        logger.info(f"ARB EXECUTED: {side.upper()} {amount:.2f} @ ${yes_price if side == 'yes' else no_price:.2f} on {market_id}")
        
        except Exception as e:
            logger.error(f"Error in arbitrage: {e}")
    
    async def _find_kalshi_market(self, poly_market_id: str) -> Optional[Dict]:
        """Find corresponding Kalshi market for Polymarket market"""
        # In real implementation, would match by:
        # - Market name/slug
        # - Event name
        # - Description
        
        # For now, return None (would need proper correlation logic)
        return None
    
    def _check_risk_limits(self):
        """Check and enforce risk limits"""
        metrics = self.risk_manager.get_metrics()
        
        if metrics.risk_level.value in ["critical", "high"]:
            logger.warning(f"RISK LEVEL: {metrics.risk_level.value}")
            logger.warning(f"Daily P&L: ${metrics.daily_pnl:.2f}")
            
            if metrics.risk_level.value == "critical":
                logger.error("STOPPING BOT: Critical risk level")
                self.running = False
    
    def _log_stats(self, trades_executed: int):
        """Log current statistics"""
        if trades_executed == 0:
            return
        
        metrics = self.risk_manager.get_metrics()
        arb_stats = self.arbitrage_engine.get_stats()
        
        logger.info("=" * 40)
        logger.info("BOT STATS:")
        logger.info(f"  Running: {datetime.now() - self.stats['start_time']}")
        logger.info(f"  Total Trades: {self.stats['total_trades']}")
        logger.info(f"  Daily P&L: ${metrics.daily_pnl:.2f}")
        logger.info(f"  Open Positions: {metrics.open_positions}")
        logger.info(f"  ARB Open: {arb_stats['open_positions']}")
        logger.info(f"  ARB Locked: {arb_stats['locked_positions']}")
        logger.info("=" * 40)
    
    async def shutdown(self):
        """Shutdown the bot"""
        logger.info("Shutting down...")
        self.running = False
        
        # Get final stats
        metrics = self.risk_manager.get_metrics()
        arb_stats = self.arbitrage_engine.get_stats()
        
        logger.info("=" * 60)
        logger.info("FINAL STATS:")
        logger.info(f"  Runtime: {datetime.now() - self.stats['start_time']}")
        logger.info(f"  Total Trades: {self.stats['total_trades']}")
        logger.info(f"  Daily P&L: ${metrics.daily_pnl:.2f}")
        logger.info(f"  ARB P&L: ${arb_stats['total_pnl']:.2f}")
        logger.info(f"  Errors: {self.stats['errors']}")
        logger.info("=" * 60)
        
        logger.info("Bot shutdown complete")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Kalshi Trading Bot")
    parser.add_argument("--live", action="store_true", 
                       help="Use live trading (not demo)")
    parser.add_argument("--demo", action="store_true", default=True,
                       help="Use demo mode (default)")
    args = parser.parse_args()
    
    # demo = False if args.live else args.demo # OLD
    # Use settings.py's value or CLI override
    demo = not args.live and (args.demo or DEMO_MODE)
    
    bot = KalshiTradingBot(demo=demo)
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
