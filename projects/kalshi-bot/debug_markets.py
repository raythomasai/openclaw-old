#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

project_root = Path("/Users/raythomas/.openclaw/workspace/projects/kalshi-bot")
sys.path.append(str(project_root))

from src.kalshi_client import KalshiClient

async def debug_markets():
    client = KalshiClient(demo=False)
    data = await client._request("GET", "/trade-api/v2/markets?limit=5")
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    import json
    asyncio.run(debug_markets())
