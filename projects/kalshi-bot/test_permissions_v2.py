#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

project_root = Path("/Users/raythomas/.openclaw/workspace/projects/kalshi-bot")
sys.path.append(str(project_root))

from src.kalshi_client import KalshiClient

async def test_permission_v2():
    client = KalshiClient(demo=False)
    
    # Get all markets
    data = await client._request("GET", "/trade-api/v2/markets?limit=10&status=active")
    if not data or 'markets' not in data:
        print("No active markets found.")
        return
        
    for market in data['markets']:
        ticker = market['ticker']
        print(f"Testing with ticker: {ticker}")
        
        # Try a buy order (will likely fail due to balance or price, but checks permissions)
        # Using a tiny price to ensure it doesn't actually fill if it's a real market
        order = await client._place_order(ticker, "yes", amount=0.01, price=0.01)
        
        if order.status == "rejected":
            # If rejected, check the logs for why
            # The client should have logged the error
            print(f"Order rejected. Status: {order.status}")
        else:
            print(f"Order result status: {order.status}")
        
        # Just test one
        break

if __name__ == "__main__":
    asyncio.run(test_permission_v2())
