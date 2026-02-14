"""Trading scheduler - orchestrates market hours trading."""
import signal
import time
from datetime import datetime
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .alpaca_client import AlpacaClient
from .strategy_manager import StrategyManager
from .risk_manager import RiskManager
from .executor import OrderExecutor
from .logger import TradingLogger, write_status
from .models import DailySummary


class TradingScheduler:
    """Orchestrates the trading loop during market hours."""
    
    def __init__(
        self,
        client: AlpacaClient,
        strategy_manager: StrategyManager,
        risk_manager: RiskManager,
        executor: OrderExecutor,
        logger: TradingLogger,
        check_interval_seconds: int = 60
    ):
        self.client = client
        self.strategy_manager = strategy_manager
        self.risk_manager = risk_manager
        self.executor = executor
        self.logger = logger
        self.check_interval = check_interval_seconds
        
        self.scheduler = BackgroundScheduler()
        self._running = False
        self._market_was_open = False
    
    def start(self) -> None:
        """Start the trading scheduler."""
        self._running = True
        
        # Schedule the main trading loop
        self.scheduler.add_job(
            self._trading_loop,
            IntervalTrigger(seconds=self.check_interval),
            id="trading_loop",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.logger.log_startup({
            "check_interval": self.check_interval,
            "strategies": self.strategy_manager.get_active_strategies()
        })
        
        # Run initial check immediately
        self._trading_loop()
    
    def stop(self) -> None:
        """Stop the trading scheduler."""
        self._running = False
        self.scheduler.shutdown(wait=False)
        self.logger.log_shutdown("requested")
    
    def _trading_loop(self) -> None:
        """Main trading loop - runs every check_interval seconds."""
        try:
            # Check if config changed
            self.strategy_manager.reload_if_changed()
            
            # Check market status
            is_open = self.client.is_market_open()
            
            # Market just opened
            if is_open and not self._market_was_open:
                self._on_market_open()
            
            # Market just closed
            if not is_open and self._market_was_open:
                self._on_market_close()
            
            self._market_was_open = is_open
            
            # Only trade when market is open
            if not is_open:
                self._update_status(is_open=False)
                return
            
            # Get current state
            account = self.client.get_account()
            positions = self.client.get_positions()
            
            # Check if we should halt trading
            if self.risk_manager.should_halt_trading(account):
                self.logger.warning("trading_halted", {
                    "reason": "daily_loss_limit",
                    "daily_pnl": account.daily_pnl
                })
                self._update_status(is_open=True, halted=True)
                return
            
            # Check for exit signals on existing positions
            exit_symbols = self.strategy_manager.check_exit_signals(positions)
            for symbol in exit_symbols:
                self.executor.close_position(symbol, reason="strategy_exit")
            
            # Get new trade signals
            signals = self.strategy_manager.get_signals()
            
            # Process signals
            for signal in signals:
                # Validate against risk manager
                validation = self.risk_manager.validate_trade(signal, account, positions)
                
                if not validation.approved:
                    self.logger.log_signal(
                        {"symbol": signal.symbol, "reason": validation.reason},
                        action="rejected"
                    )
                    continue
                
                # Calculate position size
                current_price = signal.entry_price or 0
                if current_price <= 0:
                    continue
                
                qty = self.risk_manager.calculate_position_size(
                    signal, account, current_price
                )
                
                if qty <= 0:
                    continue
                
                # Execute trade
                trade = self.executor.submit_order(signal, qty)
                
                if trade:
                    # Refresh positions for next signal
                    positions = self.client.get_positions()
                    account = self.client.get_account()
            
            # Update status file for agent monitoring
            self._update_status(is_open=True, account=account, positions=positions)
            
        except Exception as e:
            self.logger.log_error(e, {"action": "trading_loop"})
    
    def _on_market_open(self) -> None:
        """Called when market opens."""
        self.logger.info("market_open", {})
        
        # Reset daily tracking
        account = self.client.get_account()
        self.risk_manager.reset_daily_limits(account.equity)
    
    def _on_market_close(self) -> None:
        """Called when market closes."""
        self.logger.info("market_close", {})
        
        # Generate daily summary
        account = self.client.get_account()
        stats = self.risk_manager.get_daily_stats()
        
        summary = {
            "date": stats["date"],
            "starting_equity": stats["starting_equity"],
            "ending_equity": account.equity,
            "pnl": account.daily_pnl,
            "pnl_pct": account.daily_pnl_pct,
            "trades_count": stats["trades_count"]
        }
        
        self.logger.log_daily_summary(summary)
    
    def _update_status(
        self, 
        is_open: bool, 
        halted: bool = False,
        account=None,
        positions=None
    ) -> None:
        """Update status.json for agent monitoring."""
        status = {
            "market_open": is_open,
            "trading_halted": halted,
            "strategies_active": self.strategy_manager.get_active_strategies()
        }
        
        if account:
            status["account"] = {
                "portfolio_value": account.portfolio_value,
                "cash": account.cash,
                "buying_power": account.buying_power,
                "daily_pnl": account.daily_pnl,
                "daily_pnl_pct": account.daily_pnl_pct
            }
        
        if positions:
            status["positions"] = [
                {
                    "symbol": p.symbol,
                    "qty": p.qty,
                    "unrealized_pnl": p.unrealized_pnl
                }
                for p in positions
            ]
            status["position_count"] = len(positions)
        
        write_status(status)
    
    def run_forever(self) -> None:
        """Run until interrupted."""
        self.start()
        
        # Handle graceful shutdown
        def shutdown_handler(signum, frame):
            self.logger.info("shutdown_signal", {"signal": signum})
            self.stop()
        
        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)
        
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


if __name__ == "__main__":
    print("Scheduler module loaded OK")
