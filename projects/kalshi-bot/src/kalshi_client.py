#!/usr/bin/env python3
"""
Kalshi Client (Execute Trades)
Properly implements RSA signing for Kalshi API
"""

import os
import sys
import json
import base64
import hmac
import hashlib
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class KalshiPosition:
    """Open position on Kalshi"""
    market_id: str
    outcome: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    created_at: datetime


@dataclass
class KalshiOrder:
    """Order status"""
    order_id: str
    market_id: str
    side: str
    amount: float
    price: float
    status: str
    filled_amount: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AccountBalance:
    """Account balance"""
    total_balance: float
    available_balance: float
    locked_balance: float
    currency: str = "USD"


class KalshiClient:
    """Kalshi trading client with proper RSA signing"""
    
    def __init__(self, api_key: str = None, private_key: str = None, demo: bool = True):
        # Try to load from .env if not provided
        if not api_key or not private_key:
            from pathlib import Path
            env_file = Path(__file__).parent.parent / ".env"
            key_file = Path(__file__).parent.parent / "kalshi-key.pem"
            
            if env_file.exists():
                content = env_file.read_text()
                
                if not api_key:
                    for line in content.split('\n'):
                        if line.startswith('KALSHI_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            break
                
                if not private_key and key_file.exists():
                    private_key = str(key_file)
        
        self.api_key = api_key  # This is the Key ID
        self._private_key_pem = private_key
        self.demo = demo
        
        # Correct URLs for Kalshi API
        if demo:
            self.base_url = "https://demo-api.kalshi.co"
        else:
            self.base_url = "https://api.elections.kalshi.com"
        
        # Load RSA key
        self._rsa_key = self._load_private_key(private_key)
        
        logger.info(f"Kalshi client initialized: {'DEMO' if demo else 'PRODUCTION'}")
    
    def _load_private_key(self, pem_data: str) -> Optional[Any]:
        """Load RSA private key from PEM string or file"""
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend
            
            # Try reading from file first
            if os.path.exists(pem_data):
                with open(pem_data, 'rb') as f:
                    pem_data = f.read().decode('utf-8')
            
            # Clean up the PEM data
            if isinstance(pem_data, bytes):
                pem_data = pem_data.decode('utf-8')
            pem_data = pem_data.strip()
            
            # Ensure proper PEM format
            if not pem_data.startswith('-----'):
                # Try to find PEM content
                lines = pem_data.split('\n')
                clean_lines = []
                for line in lines:
                    if 'BEGIN' in line or 'END' in line:
                        clean_lines.append(line)
                    elif line.strip() and not line.startswith('#'):
                        clean_lines.append(line.strip())
                pem_data = '\n'.join(clean_lines)
            
            if not pem_data.startswith('-----'):
                logger.error("PEM data doesn't contain proper headers")
                return None
            
            key = serialization.load_pem_private_key(
                pem_data.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            return key
        except Exception as e:
            logger.warning(f"Could not load RSA key: {e}")
            return None
    
    def _sign_message(self, message: str) -> str:
        """Sign message with RSA-PSS-SHA256"""
        if not self._rsa_key:
            return ""
        
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.exceptions import InvalidSignature
            
            signature = self._rsa_key.sign(
                message.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH
                ),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            logger.error(f"Signing error: {e}")
            return ""
    
    def _get_headers(self, method: str, path: str, body: Optional[Dict] = None) -> Dict:
        """Generate auth headers for a request"""
        timestamp = str(int(datetime.now().timestamp() * 1000))
        
        # Message to sign: timestamp + method + path [+ body for POST]
        message = timestamp + method.upper() + path
        if body:
            message += json.dumps(body, separators=(',', ':'))
        
        signature = self._sign_message(message)
        
        return {
            'KALSHI-ACCESS-KEY': self.api_key,
            'KALSHI-ACCESS-TIMESTAMP': timestamp,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'Content-Type': 'application/json'
        }
    
    async def _request(self, method: str, path: str, 
                       body: Optional[Dict] = None) -> Optional[Dict]:
        """Make signed API request"""
        import aiohttp
        
        url = f"{self.base_url}{path}"
        headers = self._get_headers(method, path, body)
        
        async with aiohttp.ClientSession() as session:
            try:
                if method == "GET":
                    async with session.get(url, headers=headers) as resp:
                        if resp.ok:
                            return await resp.json()
                        else:
                            text = await resp.text()
                            logger.error(f"API error {resp.status}: {text[:200]}")
                elif method == "POST":
                    async with session.post(url, headers=headers, json=body) as resp:
                        if resp.ok:
                            return await resp.json()
                        else:
                            text = await resp.text()
                            logger.error(f"API error {resp.status}: {text[:200]}")
                elif method == "DELETE":
                    async with session.delete(url, headers=headers) as resp:
                        return {"status": "deleted"} if resp.ok else None
            except Exception as e:
                logger.error(f"Request error: {e}")
        
        return None
    
    async def get_balance(self) -> AccountBalance:
        """Get account balance"""
        if self.demo:
            # Demo mode - return simulated balance
            return AccountBalance(500, 500, 0)
        
        data = await self._request("GET", "/trade-api/v2/portfolio/balance")
        if data:
            # Kalshi returns balance in cents, convert to dollars
            return AccountBalance(
                total_balance=data.get("balance", 0) / 100,
                available_balance=data.get("available_balance", data.get("balance", 0)) / 100,
                locked_balance=data.get("locked_balance", 0) / 100
            )
        return AccountBalance(0, 0, 0)
    
    async def get_positions(self) -> List[KalshiPosition]:
        """Get open positions"""
        data = await self._request("GET", "/trade-api/v2/portfolio/positions")
        if data:
            positions = []
            for pos in data.get("positions", []):
                positions.append(KalshiPosition(
                    market_id=pos.get("market_id", ""),
                    outcome=pos.get("outcome", ""),
                    quantity=float(pos.get("quantity", 0)),
                    avg_price=float(pos.get("avg_price", 0)),
                    current_price=float(pos.get("current_price", 0)),
                    market_value=float(pos.get("market_value", 0)),
                    created_at=datetime.fromisoformat(pos.get("created_at", "2025-01-01"))
                ))
            return positions
        return []
    
    async def get_market(self, market_id: str) -> Optional[Dict]:
        """Get market details"""
        return await self._request("GET", f"/trade-api/v2/markets/{market_id}")
    
    async def get_events(self, limit: int = 50) -> List[Dict]:
        """Get list of events"""
        data = await self._request("GET", f"/trade-api/v2/events?limit={limit}")
        return data.get("events", []) if data else []
    
    async def get_markets_by_event(self, event_id: str) -> List[Dict]:
        """Get markets for an event"""
        data = await self._request("GET", f"/trade-api/v2/events/{event_id}/markets")
        return data.get("markets", []) if data else []
    
    async def buy_yes(self, market_id: str, amount: float, 
                       price: Optional[float] = None) -> KalshiOrder:
        """Buy YES on a market"""
        return await self._place_order(market_id, "yes", amount, price)
    
    async def buy_no(self, market_id: str, amount: float,
                      price: Optional[float] = None) -> KalshiOrder:
        """Buy NO on a market"""
        return await self._place_order(market_id, "no", amount, price)
    
    async def _place_order(self, market_id: str, side: str, 
                           amount: float, price: Optional[float]) -> KalshiOrder:
        """Place an order"""
        if self.demo:
            logger.info(f"[DEMO] {side.upper()} {amount} @ {price or 'market'} on {market_id}")
            return KalshiOrder(
                order_id=f"demo_{int(datetime.now().timestamp())}",
                market_id=market_id,
                side=side,
                amount=amount,
                price=price or 0.5,
                status="filled"
            )
        
        # Kalshi API expects:
        # - ticker (market_id)
        # - side (yes/no)  
        # - action (buy/sell)
        # - count (quantity in whole contracts, minimum 1)
        # - type (limit/market)
        # - yes_price_dollars or no_price_dollars (as string like "0.3300")
        
        if price is None:
            # Market order - use a reasonable default price
            price = 0.50
        
        count = max(1, int(amount / price))
        
        body = {
            "ticker": market_id,
            "side": side,
            "action": "buy",
            "count": count,
            "type": "limit",
        }
        
        price_str = f"{price:.4f}"
        if side == "yes":
            body["yes_price_dollars"] = price_str
        else:
            body["no_price_dollars"] = price_str
        
        logger.info(f"Placing order: {body}")
        
        data = await self._request("POST", "/trade-api/v2/orders", body)
        
        if data:
            return KalshiOrder(
                order_id=data.get("order_id", ""),
                market_id=market_id,
                side=side,
                amount=amount,
                price=price,
                status=data.get("status", "pending")
            )
        
        logger.warning("Order placement failed - API may require trading permissions")
        return KalshiOrder("", market_id, side, amount, price, "rejected")
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if self.demo:
            return True
        data = await self._request("DELETE", f"/trade-api/v2/orders/{order_id}")
        return data is not None
    
    async def get_order_status(self, order_id: str) -> Optional[KalshiOrder]:
        """Check order status"""
        data = await self._request("GET", f"/trade-api/v2/orders/{order_id}")
        if data:
            return KalshiOrder(
                order_id=data.get("order_id", ""),
                market_id=data.get("market_id", ""),
                side=data.get("side", ""),
                amount=float(data.get("amount", 0)),
                price=float(data.get("price", 0)),
                status=data.get("status", "")
            )
        return None
    
    async def get_trending_events(self, category: Optional[str] = None) -> List[Dict]:
        """Get trending events by volume"""
        events = await self.get_events(100)
        
        # Filter by category if specified
        if category:
            events = [e for e in events if e.get("category") == category]
        
        # Sort by volume
        events = sorted(events, key=lambda x: x.get("volume", 0), reverse=True)
        return events[:50]


# Test function
async def test_client():
    """Test the client"""
    from pathlib import Path
    
    # Load credentials
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        content = env_file.read_text()
        
        # Parse API key (simple key=value)
        api_key = None
        private_key_lines = []
        in_private_key = False
        
        for line in content.split('\n'):
            if line.startswith('KALSHI_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
            elif line.startswith('KALSHI_PRIVATE_KEY='):
                in_private_key = True
                # Get everything after the = 
                rest = line.split('=', 1)[1].strip()
                if rest:
                    private_key_lines.append(rest)
            elif in_private_key:
                if line.startswith('-----END RSA PRIVATE KEY-----'):
                    in_private_key = False
                else:
                    private_key_lines.append(line.strip())
        
        private_key = '\n'.join(private_key_lines)
        
        if api_key and private_key and not api_key.startswith('your_') and not private_key.startswith('your_'):
            client = KalshiClient(api_key, private_key, demo=True)
            
            print("Testing Kalshi client...")
            
            # Get balance
            balance = await client.get_balance()
            print(f"Balance: ${balance.available_balance}")
            
            # Get events
            events = await client.get_events(limit=10)
            print(f"Found {len(events)} events")
            
            for e in events[:5]:
                title = e.get('title', 'Unknown')[:50]
                volume = e.get('volume', 0)
                print(f"  - {title}: {volume:,}")
            
            return True
    
    print("No valid credentials found")
    return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_client())
