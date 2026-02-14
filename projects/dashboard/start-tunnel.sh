#!/bin/bash
# Dashboard + Cloudflare Tunnel Startup Script
# Keeps the dashboard running with a public tunnel

DASHBOARD_DIR="/Users/raythomas/.openclaw/workspace/projects/dashboard"
PORT=3333

# Start the Next.js development server
echo "Starting dashboard..."
cd "$DASHBOARD_DIR"
npm run dev -- -p $PORT &
DASHBOARD_PID=$!

# Wait for dashboard to be ready
echo "Waiting for dashboard to start..."
for i in {1..30}; do
    if curl -s "http://localhost:$PORT" > /dev/null 2>&1; then
        echo "Dashboard is ready!"
        break
    fi
    sleep 1
done

# Start cloudflared tunnel
echo "Starting Cloudflare tunnel..."
cloudflared tunnel --url "http://localhost:$PORT" --hostname "dashboard.trycloudflare.com" 2>&1

# Cleanup on exit
trap "kill $DASHBOARD_PID 2>/dev/null" EXIT
wait
