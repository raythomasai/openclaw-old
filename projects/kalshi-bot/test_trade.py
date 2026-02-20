#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

project_root = Path("/Users/raythomas/.openclaw/workspace/projects/kalshi-bot")
sys.path.append(str(project_root))

from src.kalshi_client import KalshiClient

async def find_cheap_market():
    client = KalshiClient(demo=False)
    print("Searching for cheap markets (< $0.05)...")
    
    events = await client.get_events(limit=50)
    # print(f"DEBUG: First event: {events[0] if events else 'None'}")
    for event in events:
        eid = event.get('event_id') or event.get('ticker') # Try both
        if not eid:
            continue
        markets = await client.get_markets_by_event(eid)
        for market in markets:
            # Check YES price
            yes_ask = market.get('yes_ask')
            if yes_ask and yes_ask <= 5: # 5 cents
                print(f"FOUND: {market['ticker']} (YES) @ ${yes_ask/100:.2f}")
                return market['ticker'], "yes", yes_ask/100
            
            # Check NO price
            no_ask = market.get('no_ask')
            if no_ask and no_ask <= 5: # 5 cents
                print(f"FOUND: {market['ticker']} (NO) @ ${no_ask/100:.2f}")
                return market['ticker'], "no", no_ask/100
                
    print("No cheap markets found.")
    return None, None, None

async def attempt_trade():
    client = KalshiClient(demo=False)
    ticker, side, price = await find_cheap_market()
    
    if ticker:
        print(f"\nAttempting to buy 1 share of {ticker} ({side.upper()}) at ${price:.2f}...")
        # amount=price means 1 share
        order = await client._place_order(ticker, side, amount=price, price=price)
        print(f"Order Status: {order.status}")
        print(f"Order ID: {order.order_id}")
        
        if order.status == "filled" or order.status == "placed" or order.status == "pending":
            print("\nSUCCESS: Trade execution capability confirmed!")
        else:
            print("\nFAILED: Trade was rejected. API keys might be read-only or balance insufficient (including fees).")
    else:
        print("Could not find a cheap enough market to test with $0.18 balance.")

if __name__ == "__main__":
    asyncio.run(attempt_trade())
