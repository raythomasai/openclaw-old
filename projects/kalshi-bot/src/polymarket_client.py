#!/usr/bin/env python3
"""
Polymarket Client (Read-Only)
Uses pmxt library for unified API access
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import pmxt, fall back to direct API calls
try:
    import pmxt
    PMXT_AVAILABLE = True
except ImportError:
    PMXT_AVAILABLE = False
    logger.warning("pmxt not available, using direct API calls")


@dataclass
class MarketPrice:
    """Price data for a market"""
    market_id: str
    yes_price: float
    no_price: float
    volume: float
    liquidity: float
    updated_at: datetime


@dataclass
class WhaleActivity:
    """Whale wallet activity"""
    wallet_address: str
    market_id: str
    side: str  # 'yes' or 'no'
    amount: float
    timestamp: datetime


class PolymarketClient:
    """Read-only Polymarket client"""
    
    # Known profitable wallets to track
    WHALE_WALLETS = {
        "ImJustKen": "0x9d84ce0306f8551e02efef1680475fc0f1dc1344",
        "SwissMiss": "0xdbade4c82fb72780a0db9a38f821d8671aba9c95",
        "fengdubiying": "0x17db3fcd93ba12d38382a0cade24b200185c5f6d",
    }
    
    def __init__(self, private_key: Optional[str] = None, demo: bool = False):
        self.private_key = private_key
        self.demo = demo
        self.client = None
        
        if PMXT_AVAILABLE and private_key:
            self._init_pmxt()
        else:
            logger.info("Polymarket client initialized (read-only, no private key)")
    
    def _init_pmxt(self):
        """Initialize pmxt client"""
        try:
            self.client = pmxt.polymarket({"privateKey": self.private_key})
            logger.info("Polymarket pmxt client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize pmxt: {e}")
            self.client = None
    
    async def get_markets(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of markets"""
        try:
            if self.client:
                return await self.client.get_markets({"category": category} if category else {})
            else:
                # Direct API call fallback
                return await self._fetch_markets_direct(category)
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []
    
    async def get_market_price(self, market_id: str) -> Optional[MarketPrice]:
        """Get current price for a market"""
        try:
            if self.client:
                data = await self.client.get_market(market_id)
                return self._parse_price_data(data, market_id)
            else:
                return await self._fetch_price_direct(market_id)
        except Exception as e:
            logger.error(f"Error fetching price for {market_id}: {e}")
            return None
    
    async def get_order_book(self, market_id: str) -> Dict[str, Any]:
        """Get order book for a market"""
        try:
            if self.client:
                return await self.client.get_order_book(market_id)
            else:
                return await self._fetch_orderbook_direct(market_id)
        except Exception as e:
            logger.error(f"Error fetching order book: {e}")
            return {}
    
    async def get_whale_activity(self, wallet_address: str, 
                                  limit: int = 100) -> List[WhaleActivity]:
        """Get recent activity for a whale wallet"""
        try:
            if self.client:
                # pmxt might have wallet activity methods
                return await self._fetch_wallet_activity(wallet_address, limit)
            else:
                return await self._fetch_wallet_activity(wallet_address, limit)
        except Exception as e:
            logger.error(f"Error fetching whale activity: {e}")
            return []
    
    async def get_trending_markets(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending markets by volume"""
        try:
            markets = await self.get_markets()
            # Sort by volume and return top N
            sorted_markets = sorted(markets, 
                                   key=lambda x: x.get("volume", 0), 
                                   reverse=True)
            return sorted_markets[:limit]
        except Exception as e:
            logger.error(f"Error fetching trending markets: {e}")
            return []
    
    async def get_political_markets(self) -> List[Dict[str, Any]]:
        """Get political/policy markets (high value for Kalshi arbitrage)"""
        try:
            markets = await self.get_markets(category="politics")
            if not markets:
                markets = await self.get_markets(category="us-elections")
            return markets
        except Exception as e:
            logger.error(f"Error fetching political markets: {e}")
            return []
    
    async def get_macro_markets(self) -> List[Dict[str, Any]]:
        """Get macro/economic markets"""
        try:
            markets = await self.get_markets(category="economics")
            if not markets:
                markets = await self.get_markets(category="finance")
            return markets
        except Exception as e:
            logger.error(f"Error fetching macro markets: {e}")
            return []
    
    async def get_price_momentum(self, market_id: str, 
                                  windows: List[int] = [5, 15, 60]) -> Dict[str, float]:
        """Calculate price momentum over different time windows (in minutes)"""
        try:
            # In a real implementation, we'd fetch historical prices
            # For now, return placeholder
            return {f"{w}min": 0.0 for w in windows}
        except Exception as e:
            logger.error(f"Error calculating momentum: {e}")
            return {}
    
    def _parse_price_data(self, data: Dict, market_id: str) -> MarketPrice:
        """Parse price data from API response"""
        # Handle different API response formats
        yes_price = data.get("yes_price", 0.5)
        no_price = data.get("no_price", 0.5)
        
        # Sometimes prices are in different fields
        if "best_yes" in data:
            yes_price = data["best_yes"]
        if "best_no" in data:
            no_price = data["best_no"]
        
        return MarketPrice(
            market_id=market_id,
            yes_price=float(yes_price),
            no_price=float(no_price),
            volume=float(data.get("volume", 0)),
            liquidity=float(data.get("liquidity", 0)),
            updated_at=datetime.now()
        )
    
    async def _fetch_markets_direct(self, category: Optional[str]) -> List[Dict]:
        """Direct API fallback for fetching markets"""
        import aiohttp
        
        url = f"{self.client.base_url if self.client else 'https://api.polymarket.com'}/markets"
        params = {}
        if category:
            params["category"] = category
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.ok:
                    data = await resp.json()
                    return data.get("markets", [])
        return []
    
    async def _fetch_price_direct(self, market_id: str) -> Optional[MarketPrice]:
        """Direct API fallback for fetching single market price"""
        import aiohttp
        
        url = f"https://api.polymarket.com/markets/{market_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.ok:
                    data = await resp.json()
                    return self._parse_price_data(data, market_id)
        return None
    
    async def _fetch_orderbook_direct(self, market_id: str) -> Dict:
        """Direct API fallback for order book"""
        import aiohttp
        
        url = f"https://api.polymarket.com/markets/{market_id}/order-book"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.ok:
                    return await resp.json()
        return {}
    
    async def _fetch_wallet_activity(self, wallet: str, limit: int) -> List[WhaleActivity]:
        """Fetch wallet activity"""
        # Placeholder - would need proper API integration
        return []


# Utility functions
async def get_polymarket_prices(client: PolymarketClient, 
                                  market_ids: List[str]) -> Dict[str, MarketPrice]:
    """Fetch prices for multiple markets concurrently"""
    import asyncio
    
    prices = {}
    tasks = [client.get_market_price(mid) for mid in market_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for market_id, result in zip(market_ids, results):
        if isinstance(result, MarketPrice):
            prices[market_id] = result
    
    return prices


async def find_momentum_opportunities(client: PolymarketClient,
                                        threshold: float = 0.05) -> List[Dict]:
    """Find markets with significant price momentum"""
    try:
        trending = await client.get_trending_markets(limit=50)
        opportunities = []
        
        for market in trending:
            market_id = market.get("id") or market.get("market_id")
            if not market_id:
                continue
            
            momentum = await client.get_price_momentum(market_id)
            if abs(momentum.get("5min", 0)) > threshold:
                opportunities.append({
                    "market_id": market_id,
                    "market": market,
                    "momentum": momentum
                })
        
        return opportunities
    except Exception as e:
        logger.error(f"Error finding momentum opportunities: {e}")
        return []
