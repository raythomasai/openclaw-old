#!/bin/bash
# handle-1password.sh - Helper to run op commands and handle the authorization prompt

CMD="$@"
SOCKET_DIR="/tmp/openclaw-tmux-sockets"
mkdir -p "$SOCKET_DIR"
SOCKET="$SOCKET_DIR/openclaw-op.sock"
SESSION="op-$(date +%Y%m%d-%H%M%S)"

echo "Starting op command in tmux session $SESSION..."
tmux -S "$SOCKET" new -d -s "$SESSION" -n shell
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- "$CMD" Enter

# Wait for potential prompt (up to 10 seconds)
for i in {1..10}; do
    sleep 1
    # Check for Authorize button in any 1Password window
    WINDOWS=$(peekaboo list windows --app "1Password" --json | grep '"window_id"' | awk '{print $NF}')
    
    for WINDOW_ID in $WINDOWS; do
        SNAPSHOT=$(peekaboo see --app "1Password" --window-id "$WINDOW_ID" --json 2>/dev/null)
        if [ $? -ne 0 ]; then continue; fi
        
        # Use python to parse JSON safely if available, or a more precise grep
        AUTH_ELEM=$(echo "$SNAPSHOT" | python3 -c 'import sys, json; data = json.load(sys.stdin); elements = data.get("data", {}).get("ui_elements", []); print(next((e["id"] for e in elements if e.get("label") == "Authorize"), ""))' 2>/dev/null)
        
        if [ ! -z "$AUTH_ELEM" ]; then
            echo "Found Authorize button ($AUTH_ELEM) in window $WINDOW_ID. Clicking..."
            peekaboo click --on "$AUTH_ELEM" --window-id "$WINDOW_ID" --json
            echo "Clicked Authorize."
            sleep 2
            break 2
        fi
    done
    
    # If op command already finished, exit
    PANE_CONTENT=$(tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0)
    if echo "$PANE_CONTENT" | grep -q "raythomas@Rays-Mac-mini-2 workspace %"; then
        if ! echo "$PANE_CONTENT" | tail -n 5 | grep -q "$CMD"; then
             echo "Command seems to have finished."
             break
        fi
    fi
done

# Capture final output
tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0
tmux -S "$SOCKET" kill-session -t "$SESSION"
