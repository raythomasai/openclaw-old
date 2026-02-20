#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

project_root = Path("/Users/raythomas/.openclaw/workspace/projects/kalshi-bot")
sys.path.append(str(project_root))

from src.kalshi_client import KalshiClient

async def attempt_permission_test():
    client = KalshiClient(demo=False)
    
    # Just pick a known market or the first one we find
    events = await client.get_events(limit=1)
    if not events:
        print("No events found.")
        return

    eid = events[0].get('event_id') or events[0].get('ticker')
    markets = await client.get_markets_by_event(eid)
    if not markets:
        print(f"No markets for event {eid}")
        return
        
    market = markets[0]
    ticker = market['ticker']
    
    print(f"Testing permissions by attempting to buy 1 share of {ticker}...")
    # Attempt to buy at $0.01 (this will likely fail due to price/balance)
    order = await client._place_order(ticker, "yes", amount=0.01, price=0.01)
    
    print(f"\nResult status: {order.status}")
    if order.order_id:
        print(f"Order ID: {order.order_id}")
    
    # We are looking for the error message in the logs or returned status
    # The client logs the full error text.

if __name__ == "__main__":
    asyncio.run(attempt_permission_test())
