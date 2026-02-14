#!/usr/bin/env python3
"""
Alpaca Trading System - Main Entry Point

Automated trading system targeting 1% daily returns.
"""
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.alpaca_client import AlpacaClient
from src.strategy_manager import StrategyManager
from src.risk_manager import RiskManager
from src.executor import OrderExecutor
from src.scheduler import TradingScheduler
from src.logger import TradingLogger


def load_config() -> dict:
    """Load configuration from strategy.json."""
    config_path = Path(__file__).parent.parent / "config" / "strategy.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}


def main():
    """Main entry point."""
    # Initialize logger first
    logger = TradingLogger()
    
    try:
        # Load config
        config = load_config()
        trading_config = config.get("trading", {})
        check_interval = trading_config.get("check_interval_seconds", 60)
        
        # Initialize Alpaca client (live trading)
        logger.info("initializing", {"component": "alpaca_client"})
        client = AlpacaClient(paper=False)
        
        # Verify connection
        account = client.get_account()
        logger.info("account_connected", {
            "portfolio_value": account.portfolio_value,
            "buying_power": account.buying_power
        })
        
        # Initialize components
        logger.info("initializing", {"component": "risk_manager"})
        risk_manager = RiskManager()
        
        logger.info("initializing", {"component": "strategy_manager"})
        strategy_manager = StrategyManager(client=client, logger=logger)
        
        logger.info("initializing", {"component": "executor"})
        executor = OrderExecutor(client=client, logger=logger)
        
        # Initialize scheduler
        logger.info("initializing", {"component": "scheduler"})
        scheduler = TradingScheduler(
            client=client,
            strategy_manager=strategy_manager,
            risk_manager=risk_manager,
            executor=executor,
            logger=logger,
            check_interval_seconds=check_interval
        )
        
        # Run
        print(f"Starting Alpaca Trading System...")
        print(f"  Portfolio: ${account.portfolio_value:.2f}")
        print(f"  Strategies: {strategy_manager.get_active_strategies()}")
        print(f"  Check interval: {check_interval}s")
        print(f"  Press Ctrl+C to stop")
        print()
        
        scheduler.run_forever()
        
    except KeyboardInterrupt:
        logger.info("shutdown", {"reason": "keyboard_interrupt"})
        print("\nShutdown complete.")
        
    except Exception as e:
        logger.log_error(e, {"action": "startup"})
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
