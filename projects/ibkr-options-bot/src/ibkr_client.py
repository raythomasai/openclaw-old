"""
IBKR Client Wrapper using official IBKR API (ibapi)
"""

import logging
import socket
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass
from queue import Queue, Empty

from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order as IBOrder

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Position:
    symbol: str
    contract: Contract
    position: int
    avg_cost: float
    market_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float


class IBKRApp(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        
        self.account_value = 0.0
        self.cash = 0.0
        self.positions = []
        self.account_queue = Queue()
        self.position_queue = Queue()
        self._connected = False
        self._account_id = None
        self._connection_error = None
        
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        # Log errors but don't crash - 2104, 2106, 2158 are info messages
        if errorCode in [2104, 2106, 2158]:
            logger.info(f"API Status: {errorString}")
        else:
            logger.error(f"Error {errorCode}: {errorString}")
        
    def connectionClosed(self):
        self._connected = False
        logger.info("Connection closed")
        
    def connectAck(self):
        """Called when connection is established"""
        self._connected = True
        logger.info("Connection acknowledged")
        
    def managedAccounts(self, accountsList):
        """Called with account list after connection"""
        self._account_id = accountsList
        logger.info(f"Managed accounts: {accountsList}")
        
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        self.account_queue.put({'tag': tag, 'value': value})
        
    def accountSummaryEnd(self, reqId: int):
        """Account summary complete"""
        pass
        
    def position(self, account: str, contract: Contract, position: float,
                 avgCost: float, unrealizedPNL: float, realizedPNL: float):
        self.position_queue.put({
            'symbol': contract.symbol,
            'contract': contract,
            'position': position,
            'avgCost': avgCost,
            'unrealizedPNL': unrealizedPNL,
            'realizedPNL': realizedPNL
        })
        
    def positionEnd(self):
        """Position data complete"""
        pass


class IBKRClient:
    """Client for interacting with IBKR API"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.app = None
        self._thread = None
        self.connected = False
        self.account_id = None
        self.account_value = 0.0
        self.cash = 0.0
        self.positions = []
        
    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _check_port(self, host: str, port: int, timeout: float = 1.0) -> bool:
        """Check if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def connect(self, timeout: float = 10.0) -> bool:
        """Connect to IBKR with timeout"""
        ibkr_config = self.config.get('ibkr', {})
        host = ibkr_config.get('host', '127.0.0.1')
        port = ibkr_config.get('port', 7497)
        
        logger.info(f"Connecting to IBKR at {host}:{port}...")
        
        # Check port first
        if not self._check_port(host, port):
            for p in [7497, 5000, 7496, 4002]:
                if self._check_port(host, p):
                    port = p
                    logger.info(f"Found IBKR on port {p}")
                    break
            else:
                logger.error(f"No IBKR port open at {host}")
                return False
        
        try:
            self.app = IBKRApp()
            self.app.connect(host, port, clientId=ibkr_config.get('client_id', 1))
            
            # Start the app in a daemon thread
            self._thread = threading.Thread(target=self.app.run, daemon=True)
            self._thread.start()
            
            # Wait for connection with timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                if hasattr(self.app, '_connected') and self.app._connected:
                    # Wait for account info
                    time.sleep(0.5)
                    
                    self.connected = True
                    self.account_id = self.app._account_id
                    logger.info(f"✓ Connected! Account: {self.account_id}")
                    
                    # Get account data
                    self.update_account_data()
                    return True
                time.sleep(0.1)
            
            logger.error("Connection timeout - IB Gateway may not be fully initialized")
            return False
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected and self.app:
            self.app.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    def update_account_data(self):
        """Update account summary and positions"""
        if not self.connected or not self.app:
            return
        
        try:
            self.app.reqAccountSummary(9001, "All", "NetLiquidation,CashBalance")
            time.sleep(0.5)
            
            while True:
                try:
                    item = self.app.account_queue.get(timeout=0.5)
                    if item['tag'] == 'NetLiquidation':
                        self.account_value = float(item['value'])
                    elif item['tag'] == 'CashBalance':
                        self.cash = float(item['value'])
                except Empty:
                    break
            
            self.app.reqPositions()
            time.sleep(0.5)
            
            self.positions = []
            while True:
                try:
                    pos_data = self.app.position_queue.get(timeout=0.5)
                    self.positions.append(Position(
                        symbol=pos_data['symbol'],
                        contract=pos_data['contract'],
                        position=pos_data['position'],
                        avg_cost=pos_data['avgCost'],
                        market_price=0.0,
                        market_value=abs(pos_data['position']) * pos_data['avgCost'],
                        unrealized_pnl=pos_data['unrealizedPNL'],
                        realized_pnl=pos_data['realizedPNL']
                    ))
                except Empty:
                    break
            
            logger.debug(f"Account value: ${self.account_value:,.2f}, Cash: ${self.cash:,.2f}")
            
        except Exception as e:
            logger.error(f"Error updating account data: {e}")
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        
        # Simple check - weekdays 9:30 AM - 4:00 PM CT
        if now.weekday() > 4:
            return False
            
        minute = now.hour * 60 + now.minute
        return 570 <= minute <= 960  # 9:30 AM - 4:00 PM CT


# Convenience functions for async usage
def run_async(coro):
    """Run an async coroutine"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == "__main__":
    # Test connection
    print("Testing IBKR connection...")
    client = IBKRClient()
    
    if client.connect(timeout=10):
        print(f"✓ Connected! Account: {client.account_id}")
        print(f"  Value: ${client.account_value:,.2f}")
        print(f"  Cash: ${client.cash:,.2f}")
        print(f"  Positions: {len(client.positions)}")
        client.disconnect()
        print("\n✓ Test passed!")
    else:
        print("✗ Failed to connect")
