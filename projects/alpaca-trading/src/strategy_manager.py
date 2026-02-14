"""Strategy manager for loading and coordinating strategies."""
import json
from pathlib import Path
from typing import Optional
import time

import pandas as pd

from .models import TradeSignal
from .strategies import Strategy, MomentumStrategy, MeanReversionStrategy
from .alpaca_client import AlpacaClient
from .logger import TradingLogger


class StrategyManager:
    """Manages trading strategies and generates signals."""
    
    STRATEGY_CLASSES = {
        "momentum_breakout": MomentumStrategy,
        "mean_reversion": MeanReversionStrategy,
    }
    
    def __init__(
        self, 
        config_path: str | Path | None = None,
        client: AlpacaClient | None = None,
        logger: TradingLogger | None = None
    ):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "strategy.json"
        self.config_path = Path(config_path)
        self.client = client
        self.logger = logger or TradingLogger()
        
        self.strategies: list[Strategy] = []
        self._config_mtime: float = 0
        self.load_strategies()
    
    def load_strategies(self) -> None:
        """Load strategies from config file."""
        if not self.config_path.exists():
            self.logger.warning("config_not_found", {"path": str(self.config_path)})
            return
        
        self._config_mtime = self.config_path.stat().st_mtime
        
        with open(self.config_path) as f:
            config = json.load(f)
        
        self.strategies = []
        strategies_config = config.get("strategies", {})
        
        for name, settings in strategies_config.items():
            if not settings.get("enabled", True):
                continue
            
            strategy_class = self.STRATEGY_CLASSES.get(name)
            if strategy_class is None:
                self.logger.warning("unknown_strategy", {"name": name})
                continue
            
            strategy = strategy_class(
                params=settings.get("params", {}),
                watchlist=settings.get("watchlist", [])
            )
            self.strategies.append(strategy)
            self.logger.info("strategy_loaded", {
                "name": name,
                "watchlist_size": len(strategy.get_watchlist())
            })
    
    def reload_if_changed(self) -> bool:
        """Reload config if file has been modified. Returns True if reloaded."""
        if not self.config_path.exists():
            return False
        
        current_mtime = self.config_path.stat().st_mtime
        if current_mtime > self._config_mtime:
            self.logger.info("config_reload", {"reason": "file_modified"})
            self.load_strategies()
            return True
        return False
    
    def get_all_watchlist_symbols(self) -> list[str]:
        """Get unique list of all symbols across all strategies."""
        symbols = set()
        for strategy in self.strategies:
            symbols.update(strategy.get_watchlist())
        return list(symbols)
    
    def get_signals(self) -> list[TradeSignal]:
        """
        Analyze all watchlist symbols and return trade signals.
        Requires client to be set.
        """
        if self.client is None:
            raise RuntimeError("AlpacaClient not set")
        
        signals = []
        symbols = self.get_all_watchlist_symbols()
        
        for symbol in symbols:
            try:
                # Get bar data
                bars = self.client.get_bars(symbol, timeframe="5Min", limit=100)
                
                if bars.empty:
                    continue
                
                # Standardize column names to lowercase
                bars.columns = [c.lower() for c in bars.columns]
                
                # Check each strategy
                for strategy in self.strategies:
                    if symbol not in strategy.get_watchlist():
                        continue
                    
                    signal = strategy.analyze(symbol, bars)
                    if signal:
                        signals.append(signal)
                        self.logger.log_signal(
                            {
                                "symbol": signal.symbol,
                                "side": signal.side,
                                "strategy": signal.strategy_name,
                                "confidence": signal.confidence
                            },
                            action="generated"
                        )
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.log_error(e, {"symbol": symbol, "action": "get_signals"})
        
        # Sort by confidence (highest first)
        signals.sort(key=lambda s: s.confidence, reverse=True)
        return signals
    
    def check_exit_signals(self, positions: list) -> list[str]:
        """
        Check if any positions should be exited based on strategy signals.
        Returns list of symbols to exit.
        """
        if self.client is None:
            return []
        
        symbols_to_exit = []
        
        for position in positions:
            symbol = position.symbol
            
            try:
                bars = self.client.get_bars(symbol, timeframe="5Min", limit=50)
                if bars.empty:
                    continue
                
                bars.columns = [c.lower() for c in bars.columns]
                
                # Check if any strategy says to exit
                for strategy in self.strategies:
                    if strategy.should_exit(symbol, bars, "long"):
                        symbols_to_exit.append(symbol)
                        self.logger.info("exit_signal", {
                            "symbol": symbol,
                            "strategy": strategy.name
                        })
                        break
                
            except Exception as e:
                self.logger.log_error(e, {"symbol": symbol, "action": "check_exit"})
        
        return symbols_to_exit
    
    def get_active_strategies(self) -> list[str]:
        """Get names of active strategies."""
        return [s.name for s in self.strategies]


if __name__ == "__main__":
    # Quick test
    sm = StrategyManager()
    print(f"Active strategies: {sm.get_active_strategies()}")
    print(f"Watchlist: {sm.get_all_watchlist_symbols()}")
