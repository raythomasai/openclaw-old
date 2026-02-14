# IB Gateway API Setup Guide

## Check IB Gateway Status

1. **Open IB Gateway** - You should see it in your menu bar or applications
2. **Verify login** - Make sure you're logged into the paper trading account
3. **Check API settings:**

### Enable API Access in IB Gateway

1. Go to **Settings** (gear icon)
2. Navigate to **API** section
3. Enable:
   - [x] **Enable ActiveX and Socket Clients**
   - [x] **Enable DDE Socket Clients**
4. Set **Socket Port** to `7497` (paper) or `7496` (live)
5. **Important:** Click **Apply** and **restart IB Gateway**

## Verify Port is Listening

After restarting IB Gateway, check if port 7497 is listening:

```bash
# On macOS with lsof:
lsof -i :7497

# Or check with IB Gateway logs
# Look for: "Socket port: 7497" in the logs
```

## Test Connection

```bash
cd /Users/raythomas/.openclaw/workspace/projects/ibkr-options-bot
source venv/bin/activate
python test_connection.py
```

## Common Issues

| Issue | Solution |
|-------|----------|
| "Connection refused" | IB Gateway not running or API not enabled |
| "Timeout" | Wrong port, or IB Gateway needs restart |
| "Login required" | Log into paper account in IB Gateway |
| Port 7497 not found | Enable API settings and restart IB Gateway |

## IB Gateway Logs

Check IB Gateway logs for API connection attempts:
- Location: `~/Library/Application Support/IB Gateway/logs/`
- Look for `gateway.log` or `twsapi.log`

## Once Connected

You should see:
```
✓ Connected!
  Account: XXXXXXXX
  Server version: XXXX
```

Then you can run the trading bot:
```bash
python src/main.py --test
```
