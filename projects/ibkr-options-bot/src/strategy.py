"""
Trading Strategy
Aggressive dual-sided momentum trading strategy
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import yaml
import pandas as pd
import numpy as np

from scanner import ScanResult, MarketScanner
from ibkr_client import IBKRClient

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a completed or pending trade"""
    symbol: str
    direction: str  # 'long' or 'short'
    strategy: str
    entry_price: float
    quantity: int
    contract: any
    order_id: Optional[int] = None
    entry_time: datetime = field(default_factory=datetime.now)
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    status: str = "pending"  # pending, open, closed
    pnl: float = 0.0
    pnl_pct: float = 0.0
    confidence: float = 0.0
    reason: str = ""
    stop_loss: float = 0.0
    profit_target: float = 0.0


@dataclass
class TradeSetup:
    """Trade setup before execution"""
    signal: ScanResult
    option_type: str  # 'call' or 'put'
    strike: float
    expiration: str
    quantity: int
    estimated_entry: float
    stop_loss: float
    profit_target: float
    reward_risk_ratio: float


class Strategy(ABC):
    """Base strategy class"""
    
    @abstractmethod
    async def find_setups(self, signals: List[ScanResult], 
                         client: IBKRClient) -> List[TradeSetup]:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass


class MomentumStrategy(Strategy):
    """Aggressive momentum strategy - trades breakouts"""
    
    def __init__(self, config: dict, client: IBKRClient):
        self.config = config
        self.client = client
        
    def get_name(self) -> str:
        return "Momentum Strategy"
    
    async def find_setups(self, signals: List[ScanResult], 
                         client: IBKRClient) -> List[TradeSetup]:
        setups = []
        
        for signal in signals:
            try:
                if signal.signal_type == 'long':
                    setup = await self._create_long_setup(signal)
                elif signal.signal_type == 'short':
                    setup = await self._create_short_setup(signal)
                
                if setup:
                    setups.append(setup)
                    
            except Exception as e:
                logger.error(f"Error creating setup for {signal.symbol}: {e}")
        
        return setups
    
    async def _get_nearest_expiration(self, symbol: str) -> str:
        """Get nearest weekly expiration"""
        # For now, return a placeholder
        # In production, use ibkr_client to get actual expirations
        return (datetime.now() + timedelta(days=7)).strftime('%Y%m%d')
    
    async def _find_best_strike(self, symbol: str, direction: str,
                                current_price: float, expiration: str) -> float:
        """Find best strike for the trade"""
        # ATM to slightly OTM
        if direction == 'long':  # Buying calls
            return round(current_price * 1.02, 1)  # 2% OTM
        else:  # Buying puts
            return round(current_price * 0.98, 1)  # 2% OTM
    
    async def _create_long_setup(self, signal: ScanResult) -> Optional[TradeSetup]:
        """Create a long (call) setup"""
        try:
            symbol = signal.symbol
            price = signal.price
            
            # Get expiration and strike
            expiration = await self._get_nearest_expiration(symbol)
            strike = await self._find_best_strike(symbol, 'call', price, expiration)
            
            # Calculate position size (in production, use real option price)
            estimated_entry = price * 0.05  # Placeholder - real price from IBKR
            stop_loss = estimated_entry * 0.70  # 30% stop
            profit_target = estimated_entry * 1.50  # 50% profit target
            reward_risk = profit_target / (estimated_entry - stop_loss) if stop_loss < estimated_entry else 1.5
            
            return TradeSetup(
                signal=signal,
                option_type='call',
                strike=strike,
                expiration=expiration,
                quantity=1,
                estimated_entry=estimated_entry,
                stop_loss=stop_loss,
                profit_target=profit_target,
                reward_risk_ratio=reward_risk
            )
            
        except Exception as e:
            logger.error(f"Error creating long setup: {e}")
            return None
    
    async def _create_short_setup(self, signal: ScanResult) -> Optional[TradeSetup]:
        """Create a short (put) setup"""
        try:
            symbol = signal.symbol
            price = signal.price
            
            expiration = await self._get_nearest_expiration(symbol)
            strike = await self._find_best_strike(symbol, 'put', price, expiration)
            
            estimated_entry = price * 0.05
            stop_loss = estimated_entry * 1.30  # 30% stop (for puts)
            profit_target = estimated_entry * 0.50  # 50% profit target
            reward_risk = profit_target / (stop_loss - estimated_entry) if stop_loss > estimated_entry else 1.5
            
            return TradeSetup(
                signal=signal,
                option_type='put',
                strike=strike,
                expiration=expiration,
                quantity=1,
                estimated_entry=estimated_entry,
                stop_loss=stop_loss,
                profit_target=profit_target,
                reward_risk_ratio=reward_risk
            )
            
        except Exception as e:
            logger.error(f"Error creating short setup: {e}")
            return None


class ScalpStrategy(Strategy):
    """Quick scalping strategy - very short-term"""
    
    def __init__(self, config: dict, client: IBKRClient):
        self.config = config
        self.client = client
        
    def get_name(self) -> str:
        return "Scalp Strategy"
    
    async def find_setups(self, signals: List[ScanResult],
                         client: IBKRClient) -> List[TradeSetup]:
        # Ultra-short-term setups - smaller size, faster exits
        return []


class AggressiveStrategyManager:
    """Main strategy manager for aggressive trading"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.scanner = MarketScanner(config_path)
        self.client: Optional[IBKRClient] = None
        self.active_trades: List[Trade] = []
        self.completed_trades: List[Trade] = []
        self.strategies: List[Strategy] = []
        self.daily_pnl = 0.0
        self.daily_started = datetime.now()
        
    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def initialize(self, client: IBKRClient):
        """Initialize with IBKR client"""
        self.client = client
        
        # Initialize strategies
        strategy_config = self.config.get('strategy', {})
        
        self.strategies = [
            MomentumStrategy(strategy_config, client),
        ]
        
        logger.info(f"Initialized {len(self.strategies)} strategies")
    
    def can_trade(self) -> Tuple[bool, str]:
        """Check if we can take new trades"""
        # Check market hours
        if not self.client or not self.client.is_market_open():
            return False, "Market closed"
        
        # Check daily loss limit
        risk_config = self.config.get('risk', {})
        max_daily_loss = risk_config.get('max_daily_loss_pct', 0.05)
        
        if self.client.account_value > 0:
            daily_loss_pct = abs(self.daily_pnl) / self.client.account_value
            if daily_loss_pct >= max_daily_loss:
                return False, f"Daily loss limit reached ({daily_loss_pct*100:.1f}%)"
        
        # Check position count
        max_positions = strategy_config.get('max_positions', 10)
        if len(self.active_trades) >= max_positions:
            return False, f"Max positions reached ({max_positions})"
        
        return True, "OK"
    
    async def scan_and_trade(self):
        """Main scanning and trading loop"""
        if not self.client:
            logger.error("Client not initialized")
            return
        
        can_trade, reason = self.can_trade()
        
        if not can_trade:
            logger.warning(f"Cannot trade: {reason}")
            return
        
        # Get quotes for watchlist
        watchlist = self.scanner.get_watchlist()
        quotes = {}
        
        for symbol in watchlist:
            quote = await self.client.get_quote(symbol)
            if quote:
                quotes[symbol] = quote
        
        # Scan for signals
        signals = await self.scanner.scan_all(quotes)
        
        if not signals:
            logger.debug("No signals found")
            return
        
        logger.info(f"Found {len(signals)} signals")
        
        # Generate setups from each strategy
        for strategy in self.strategies:
            setups = await strategy.find_setups(signals, self.client)
            
            for setup in setups[:3]:  # Limit to 3 setups per strategy
                await self._execute_setup(setup)
    
    async def _execute_setup(self, setup: TradeSetup) -> Optional[Trade]:
        """Execute a trade setup"""
        try:
            # Check if we already have a position in this symbol
            for trade in self.active_trades:
                if trade.symbol == setup.signal.symbol:
                    logger.info(f"Already have position in {setup.signal.symbol}")
                    return None
            
            # Execute the trade
            direction = 'long' if setup.option_type == 'call' else 'short'
            
            trade = await self.client.buy_option(
                symbol=setup.signal.symbol,
                direction=setup.option_type,
                strike=setup.strike,
                expiration=setup.expiration,
                quantity=setup.quantity
            )
            
            if trade:
                logger.info(f"Executed trade: {setup.signal.symbol} {setup.option_type} "
                           f"{setup.strike} {setup.expiration}")
                return trade
            
            return None
            
        except Exception as e:
            logger.error(f"Error executing setup: {e}")
            return None
    
    async def check_exits(self):
        """Check and execute exits for all active trades"""
        for trade in self.active_trades:
            try:
                # Get current price
                current_price = self._get_position_price(trade)
                
                if current_price == 0:
                    continue
                
                # Check stop loss
                if trade.direction == 'long':
                    if current_price <= trade.stop_loss:
                        await self._close_trade(trade, current_price, "Stop loss")
                        continue
                    
                    # Check profit target
                    if current_price >= trade.profit_target:
                        await self._close_trade(trade, current_price, "Profit target")
                        continue
                        
                else:  # short
                    if current_price >= trade.stop_loss:
                        await self._close_trade(trade, current_price, "Stop loss")
                        continue
                    
                    if current_price <= trade.profit_target:
                        await self._close_trade(trade, current_price, "Profit target")
                        continue
                        
            except Exception as e:
                logger.error(f"Error checking exit for {trade.symbol}: {e}")
    
    def _get_position_price(self, trade: Trade) -> float:
        """Get current price for a position"""
        try:
            ticker = self.client.ib.reqMktData(trade.contract, "", False, False)
            if ticker.last:
                return ticker.last
            return ticker.bid or 0
        except:
            return 0
    
    async def _close_trade(self, trade: Trade, price: float, reason: str):
        """Close a trade"""
        try:
            success = await self.client.close_position(trade.contract)
            
            if success:
                trade.exit_price = price
                trade.exit_time = datetime.now()
                trade.status = "closed"
                trade.pnl = (price - trade.entry_price) * trade.quantity
                trade.pnl_pct = ((price - trade.entry_price) / trade.entry_price) * 100
                trade.reason = reason
                
                self.active_trades.remove(trade)
                self.completed_trades.append(trade)
                self.daily_pnl += trade.pnl
                
                logger.info(f"Closed {trade.symbol}: {reason}, P&L: ${trade.pnl:.2f} ({trade.pnl_pct:.1f}%)")
                
        except Exception as e:
            logger.error(f"Error closing trade: {e}")
    
    def get_daily_summary(self) -> Dict:
        """Get daily trading summary"""
        return {
            'date': self.daily_started.strftime('%Y-%m-%d'),
            'trades_completed': len(self.completed_trades),
            'trades_active': len(self.active_trades),
            'daily_pnl': self.daily_pnl,
            'wins': len([t for t in self.completed_trades if t.pnl > 0]),
            'losses': len([t for t in self.completed_trades if t.pnl <= 0]),
        }


if __name__ == "__main__":
    # Quick test
    print("Strategy module loaded")
