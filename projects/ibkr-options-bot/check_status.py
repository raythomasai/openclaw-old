#!/usr/bin/env python3
"""IBKR Connection Status Checker"""

import socket

def check_ports():
    """Check which IBKR ports are open"""
    print("=" * 50)
    print("IBKR Port Status Check")
    print("=" * 50)
    
    ports = [
        (5000, "Client Portal Gateway"),
        (7497, "IB Gateway/TWS (Paper)"),
        (7496, "IB Gateway/TWS (Live)"),
        (4001, "IB Gateway (Legacy)"),
        (4002, "IB Gateway (Legacy)")
    ]
    
    for port, desc in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                print(f"  ✓ Port {port}: OPEN ({desc})")
            else:
                print(f"  ✗ Port {port}: CLOSED ({desc})")
            sock.close()
        except Exception as e:
            print(f"  ? Port {port}: ERROR ({e})")
    
    print()
    return 5000 in [p for p, _ in [(5000, 0), (7497, 0), (7496, 0), (4001, 0), (4002, 0)] if socket.socket().connect_ex(('127.0.0.1', p)) == 0]

def main():
    print("\n" + "=" * 50)
    print("IBKR Gateway Status")
    print("=" * 50 + "\n")
    
    any_open = check_ports()
    
    print("=" * 50)
    print("Next Steps")
    print("=" * 50)
    
    if not any_open:
        print("""
IB Gateway is NOT running or API is not enabled.

To enable:
1. Open IB Gateway application
2. Go to Settings (gear icon)
3. Navigate to API section
4. Enable:
   - ✓ Enable ActiveX and Socket Clients
5. Set Socket Port to 7497 (paper) or 7496 (live)
6. Click APPLY
7. RESTART IB Gateway

After restart, check again with:
  python quick_test.py
""")
    else:
        print("""
IB Gateway appears to be running!

To test connection:
  python quick_test.py

If connection hangs, IB Gateway may need:
- Login to paper trading account
- API settings enabled
- Restart after settings change
""")

if __name__ == "__main__":
    main()
