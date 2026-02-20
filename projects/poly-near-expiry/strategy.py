import os
import time
import datetime
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.clob_types import OrderArgs, OrderType
import requests

load_dotenv()

def get_client():
    host = "https://clob.polymarket.com"
    key = os.getenv("POLY_PRIVATE_KEY")
    funder = os.getenv("POLY_FUNDER")
    
    # API Creds from .env (to avoid re-deriving)
    api_key = os.getenv("POLY_API_KEY")
    api_secret = os.getenv("POLY_API_SECRET")
    api_passphrase = os.getenv("POLY_API_PASSPHRASE")
    
    from py_clob_client.clob_types import ApiCreds
    
    client = ClobClient(
        host, 
        key=key, 
        chain_id=POLYGON,
        funder=funder,
        signature_type=1 # Standard for most wallets
    )
    
    if api_key and api_secret and api_passphrase:
        client.set_api_creds(ApiCreds(
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=api_passphrase
        ))
    else:
        # Fallback to derivation
        client.set_api_creds(client.create_or_derive_api_creds())
        
    return client

def run_strategy():
    # Initialize client
    client = get_client()
    print(f"Connected to Polymarket CLOB.")

    # DRY RUN FLAG
    DRY_RUN = os.getenv("DRY_RUN", "1") == "1"
    if DRY_RUN:
        print("!!! DRY RUN MODE ACTIVE !!! (No trades will be executed)")
    else:
        print("!!! LIVE TRADING ACTIVE !!!")
    
    now = datetime.datetime.now(datetime.timezone.utc)
    # Increase window to 1 week (168 hours)
    expiry_threshold = now + datetime.timedelta(hours=168)

    # Get active markets
    # Note: Polymarket has a LOT of markets. We might need to filter.
    # We'll use the Gamma API (standard for discovery) as CLOB is for execution.
    print("Fetching markets from Gamma API...")
    gamma_url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=1000&order=createdAt&ascending=false"
    resp = requests.get(gamma_url)
    markets = resp.json()
    
    potential_trades = []
    
    seen_questions = set()
    for m in markets:
        question = m.get("question")
        if question in seen_questions:
            continue
            
        # Check expiry
        end_date_str = m.get("endDate")
        if not end_date_str:
            continue
            
        try:
            # Format: 2026-02-18T00:00:00Z
            end_date = datetime.datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        except:
            continue
            
        if now < end_date < expiry_threshold:
            # Check odds/price
            # Gamma gives "outcomePrices". CLOB gives better real-time data but let's check Gamma first.
            prices_data = m.get("outcomePrices")
            if not prices_data:
                continue
            
            import json
            if isinstance(prices_data, str):
                try:
                    prices = json.loads(prices_data)
                except:
                    continue
            else:
                prices = prices_data
                
            outcomes_data = m.get("outcomes")
            if isinstance(outcomes_data, str):
                try:
                    outcomes = json.loads(outcomes_data)
                except:
                    outcomes = []
            else:
                outcomes = outcomes_data or []
                
            clob_token_ids_data = m.get("clobTokenIds")
            if isinstance(clob_token_ids_data, str):
                try:
                    clob_token_ids = json.loads(clob_token_ids_data)
                except:
                    continue
            else:
                clob_token_ids = clob_token_ids_data
            
            if not clob_token_ids:
                continue
                
            # prices is a list of strings ["0.95", "0.05"]
            for i, p_str in enumerate(prices):
                p = float(p_str)
                if p >= 0.70 and p <= 0.995: # Cap at 0.995 to ensure some liquidity/feasibility
                    seen_questions.add(question)
                    token_id = clob_token_ids[i]
                    outcome_name = outcomes[i] if i < len(outcomes) else "Unknown"
                    
                    potential_trades.append({
                        "id": m.get("id"),
                        "question": m.get("question"),
                        "outcome": outcome_name,
                        "token_id": token_id,
                        "price": p,
                        "expiry": end_date_str
                    })

    print(f"Found {len(potential_trades)} potential trades near expiry with >85% odds.")
    
    for trade in potential_trades:
        print(f"\nEvaluating: {trade['question']}")
        print(f"Outcome: {trade['outcome']} | Price: {trade['price']} | Expiry: {trade['expiry']}")
        
        # Check current orderbook on CLOB for better price accuracy
        try:
            orderbook = client.get_order_book(trade['token_id'])
            # Get best ask (we want to buy)
            asks = orderbook.asks
            if not asks:
                print("No asks available.")
                continue
                
            best_ask = float(asks[0].price)
            if best_ask > 0.995:
                print(f"Price too high on CLOB: {best_ask}")
                continue
                
            if best_ask < 0.85:
                print(f"Price shifted below 85% on CLOB: {best_ask}")
                continue
                
            # Calculate size for $20
            # cost = price * size
            # 20 = best_ask * size => size = 20 / best_ask
            size = 20.0 / best_ask
            
            if DRY_RUN:
                print(f"[DRY RUN] Would execute: Buying {size:.2f} contracts at {best_ask} (~$20)")
            else:
                print(f"Executing trade: Buying {size:.2f} contracts at {best_ask} (~$20)")
                # Place order (FOK = Fill Or Kill) - use create_and_post_order to actually submit!
                resp = client.create_and_post_order(OrderArgs(
                    price=best_ask,
                    size=size,
                    side="BUY",
                    token_id=trade['token_id']
                ))
                print(f"Order Response: {resp}")
            
        except Exception as e:
            print(f"Error during execution: {e}")

if __name__ == "__main__":
    run_strategy()
