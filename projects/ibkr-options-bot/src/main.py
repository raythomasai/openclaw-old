#!/usr/bin/env python3
"""
IBKR Options Trading Bot - Main Entry Point
Aggressive dual-sided momentum trading
"""

import asyncio
import sys
from pathlib import Path

# Fix event loop for ib_insync with Python 3.14+
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import nest_asyncio
nest_asyncio.apply()

import logging
import signal
from datetime import datetime, timedelta

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from ibkr_client import IBKRClient
from scanner import MarketScanner
from strategy import AggressiveStrategyManager
from risk_manager import RiskManager


# Configure logging
def setup_logging(config: dict):
    """Configure logging"""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_config.get('file', 'logs/trading.log')),
            logging.StreamHandler(sys.stdout)
        ]
    )


class TradingBot:
    """Main trading bot class"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        setup_logging(self.config)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.client: IBKRClient = None
        self.scanner: MarketScanner = None
        self.strategy: AggressiveStrategyManager = None
        self.risk: RiskManager = None
        
        self.running = False
        self.scan_interval = 60  # seconds
        
    def _load_config(self) -> dict:
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    async def initialize(self):
        """Initialize all components"""
        self.logger.info("Initializing trading bot...")
        
        # Initialize IBKR client
        self.client = IBKRClient(self.config_path)
        
        # Connect to IBKR
        connected = await self.client.connect()
        if not connected:
            self.logger.error("Failed to connect to IBKR")
            return False
        
        # Initialize scanner
        self.scanner = MarketScanner(self.config_path)
        
        # Initialize strategy
        self.strategy = AggressiveStrategyManager(self.config_path)
        self.strategy.initialize(self.client)
        
        # Initialize risk manager
        self.risk = RiskManager(self.config_path)
        
        self.logger.info("Bot initialized successfully")
        return True
    
    async def run(self):
        """Main trading loop"""
        if not await self.initialize():
            self.logger.error("Initialization failed")
            return
        
        self.running = True
        self.logger.info("Starting trading loop...")
        
        # Set up signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: self.stop())
        
        last_scan = datetime.now()
        last_check = datetime.now()
        
        while self.running:
            try:
                now = datetime.now()
                
                # Update account data periodically
                if (now - last_check).seconds >= 30:
                    await self.client.update_account_data()
                    if self.client.positions:
                        self.risk.update_portfolio(
                            self.client.account_value,
                            self.client.cash,
                            self.client.positions
                        )
                    last_check = now
                
                # Check exits every 10 seconds
                await self.strategy.check_exits()
                
                # Scan for new opportunities
                if (now - last_scan).seconds >= self.scan_interval:
                    if self.client.is_market_open():
                        await self.strategy.scan_and_trade()
                        last_scan = now
                    else:
                        self.logger.debug("Market closed, skipping scan")
                
                # Brief pause
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(5)
        
        await self.shutdown()
    
    def stop(self):
        """Stop the trading bot"""
        self.logger.info("Stopping trading bot...")
        self.running = False
    
    async def shutdown(self):
        """Clean shutdown"""
        self.logger.info("Shutting down...")
        
        # Close all positions
        if self.client and self.client.connected:
            self.logger.info("Closing all positions...")
            for pos in self.client.positions:
                await self.client.close_position(pos.contract)
            
            await self.client.disconnect()
        
        # Print summary
        if self.strategy:
            summary = self.strategy.get_daily_summary()
            self.logger.info(f"Daily Summary: {summary}")
        
        self.logger.info("Bot stopped")


async def test_connection():
    """Test IBKR connection"""
    print("Testing IBKR connection...")
    
    client = IBKRClient("config/config.yaml")
    
    if await client.connect():
        print(f"✓ Connected! Account: {client.account_id}")
        print(f"✓ Portfolio Value: ${client.account_value:,.2f}")
        print(f"✓ Cash: ${client.cash:,.2f}")
        
        # Test quote
        quote = await client.get_quote("AAPL")
        if quote:
            print(f"✓ AAPL Quote: ${quote['last']:.2f}")
        
        await client.disconnect()
        return True
    else:
        print("✗ Failed to connect to IBKR")
        return False


async def test_scanner():
    """Test market scanner"""
    print("\nTesting market scanner...")
    
    scanner = MarketScanner("config/config.yaml")
    watchlist = scanner.get_watchlist()
    
    print(f"✓ Watchlist loaded: {len(watchlist)} symbols")
    print(f"  {', '.join(watchlist[:10])}...")
    
    strategies = [s.get_name() for s in scanner.strategies]
    print(f"✓ Strategies loaded: {len(strategies)}")
    for s in strategies:
        print(f"  - {s}")
    
    return True


async def dry_run():
    """Run in dry run mode (no trading)"""
    print("\n=== IBKR Options Trading Bot ===\n")
    
    # Test components
    conn_ok = await test_connection()
    scan_ok = await test_scanner()
    
    if conn_ok and scan_ok:
        print("\n✓ All systems ready")
        print("\nTo start trading, run:")
        print("  python src/main.py")
    else:
        print("\n✗ Some systems failed initialization")
        print("Please check your IBKR connection and config")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="IBKR Options Trading Bot")
    parser.add_argument('--test', action='store_true', help='Test connection')
    parser.add_argument('--scan', action='store_true', help='Test scanner')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no trading)')
    parser.add_argument('--config', default='config/config.yaml', help='Config path')
    
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(test_connection())
    elif args.scan:
        asyncio.run(test_scanner())
    elif args.dry_run:
        asyncio.run(dry_run())
    else:
        # Start trading
        bot = TradingBot(args.config)
        asyncio.run(bot.run())


if __name__ == "__main__":
    main()
