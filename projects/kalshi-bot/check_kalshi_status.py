#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path to import KalshiClient
project_root = Path("/Users/raythomas/.openclaw/workspace/projects/kalshi-bot")
sys.path.append(str(project_root))

from src.kalshi_client import KalshiClient

async def check_status():
    # Use real credentials from .env
    client = KalshiClient(demo=False)
    
    print(f"--- Kalshi Account Status (LIVE) ---")
    print(f"Base URL: {client.base_url}")
    print(f"Key ID: {client.api_key}")
    
    try:
        balance = await client.get_balance()
        print(f"Total Balance: ${balance.total_balance:.2f}")
        print(f"Available Balance: ${balance.available_balance:.2f}")
        print(f"Locked Balance: ${balance.locked_balance:.2f}")
        
        if balance.total_balance > 0:
            print("\nSuccessfully fetched live balance! API keys are active.")
        else:
            print("\nBalance is $0.00. (Could be empty or still restricted)")
            
        print("\nChecking positions...")
        positions = await client.get_positions()
        if positions:
            print(f"Open Positions: {len(positions)}")
            for p in positions:
                print(f" - {p.market_id}: {p.quantity} {p.outcome} @ ${p.avg_price:.2f}")
        else:
            print("No open positions.")
            
        # Try to fetch one market to verify read access
        print("\nChecking market access (NFL)...")
        markets = await client.get_events(limit=5)
        if markets:
            print(f"Successfully fetched {len(markets)} events.")
        else:
            print("Could not fetch events.")
            
    except Exception as e:
        print(f"Error checking status: {e}")

if __name__ == "__main__":
    asyncio.run(check_status())
