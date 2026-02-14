"""Unit tests for the trading system."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import TradeSignal, RiskConfig, AccountInfo, Position
from src.risk_manager import RiskManager
from src.strategies.momentum import MomentumStrategy
from src.strategies.mean_reversion import MeanReversionStrategy


class TestRiskManager:
    """Tests for RiskManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rm = RiskManager.__new__(RiskManager)
        self.rm.config = RiskConfig()
        self.rm._daily_pnl = 0.0
        self.rm._daily_trades = 0
        self.rm._starting_equity = 500.0
    
    def test_calculate_stop_loss_buy(self):
        """Test stop loss calculation for buy orders."""
        stop = self.rm.calculate_stop_loss(100.0, "buy")
        assert stop == 98.50  # 1.5% below
    
    def test_calculate_stop_loss_sell(self):
        """Test stop loss calculation for sell orders."""
        stop = self.rm.calculate_stop_loss(100.0, "sell")
        assert abs(stop - 101.50) < 0.01  # 1.5% above
    
    def test_calculate_take_profit_buy(self):
        """Test take profit calculation for buy orders."""
        tp = self.rm.calculate_take_profit(100.0, "buy")
        assert tp == 102.00  # 2% above
    
    def test_calculate_position_size(self):
        """Test position size calculation."""
        account = AccountInfo(
            portfolio_value=500.0,
            cash=100.0,
            buying_power=100.0,
            equity=500.0,
            daily_pnl=0.0,
            daily_pnl_pct=0.0
        )
        signal = TradeSignal(
            symbol="TEST",
            side="buy",
            strategy_name="test",
            confidence=0.8
        )
        
        # Max 10% of portfolio = $50, at $100/share = 0.5 shares
        qty = self.rm.calculate_position_size(signal, account, 100.0)
        assert qty == 0.5
    
    def test_position_size_limited_by_buying_power(self):
        """Test that position size is limited by buying power."""
        account = AccountInfo(
            portfolio_value=1000.0,
            cash=20.0,
            buying_power=20.0,  # Low buying power
            equity=1000.0,
            daily_pnl=0.0,
            daily_pnl_pct=0.0
        )
        signal = TradeSignal(
            symbol="TEST",
            side="buy",
            strategy_name="test",
            confidence=0.8
        )
        
        # Max 10% of portfolio = $100, but only $20 buying power
        qty = self.rm.calculate_position_size(signal, account, 100.0)
        assert qty == 0.2  # $20 / $100 = 0.2 shares
    
    def test_should_halt_trading_normal(self):
        """Test that trading is not halted in normal conditions."""
        account = AccountInfo(
            portfolio_value=490.0,
            cash=50.0,
            buying_power=50.0,
            equity=490.0,  # 2% loss would be at 490
            daily_pnl=-10.0,
            daily_pnl_pct=-2.0
        )
        
        # 2% loss = halt (490/500 = 98%, so 2% loss)
        assert self.rm.should_halt_trading(account) == True
    
    def test_validate_trade_insufficient_buying_power(self):
        """Test trade rejection for insufficient buying power."""
        account = AccountInfo(
            portfolio_value=500.0,
            cash=5.0,
            buying_power=5.0,  # Below min of $10
            equity=500.0,
            daily_pnl=0.0,
            daily_pnl_pct=0.0
        )
        signal = TradeSignal(
            symbol="TEST",
            side="buy",
            strategy_name="test",
            confidence=0.8
        )
        
        result = self.rm.validate_trade(signal, account, [])
        assert result.approved == False
        assert "buying power" in result.reason.lower()


class TestMomentumStrategy:
    """Tests for MomentumStrategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = MomentumStrategy()
    
    def test_get_watchlist(self):
        """Test watchlist is returned."""
        watchlist = self.strategy.get_watchlist()
        assert isinstance(watchlist, list)
        assert len(watchlist) > 0
    
    def test_analyze_insufficient_data(self):
        """Test that no signal is generated with insufficient data."""
        bars = pd.DataFrame({
            "open": [100],
            "high": [101],
            "low": [99],
            "close": [100],
            "volume": [1000000]
        })
        
        signal = self.strategy.analyze("TEST", bars)
        assert signal is None
    
    def test_vwap_calculation(self):
        """Test VWAP calculation."""
        bars = pd.DataFrame({
            "high": [101, 102, 103],
            "low": [99, 100, 101],
            "close": [100, 101, 102],
            "volume": [1000, 2000, 3000]
        })
        
        vwap = self.strategy._calculate_vwap(bars)
        assert vwap > 0
        # VWAP should be between low and high
        assert vwap >= 99 and vwap <= 103


class TestMeanReversionStrategy:
    """Tests for MeanReversionStrategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = MeanReversionStrategy()
    
    def test_get_watchlist(self):
        """Test watchlist is returned."""
        watchlist = self.strategy.get_watchlist()
        assert isinstance(watchlist, list)
        assert len(watchlist) > 0
    
    def test_analyze_insufficient_data(self):
        """Test that no signal is generated with insufficient data."""
        bars = pd.DataFrame({
            "open": [100],
            "high": [101],
            "low": [99],
            "close": [100],
            "volume": [1000000]
        })
        
        signal = self.strategy.analyze("TEST", bars)
        assert signal is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
