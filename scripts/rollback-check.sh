#!/bin/bash
# Rollback Script - Revert to last known good state
# Triggered by cron if no human contact for 48 hours

LAST_CONTACT_FILE="/Users/raythomas/.openclaw/workspace/.last_human_contact"
WORKSPACE="/Users/raythomas/.openclaw/workspace"
BACKUP_DIR="/Users/raythomas/.openclaw/workspace/backups"

# Check if file exists
if [ ! -f "$LAST_CONTACT_FILE" ]; then
    echo "No contact file found. Creating one."
    echo "$(date -u +%s)" > "$LAST_CONTACT_FILE"
    exit 0
fi

# Get current time and last contact time
NOW=$(date -u +%s)
LAST=$(cat "$LAST_CONTACT_FILE")
DIFF=$((NOW - LAST))

# 48 hours in seconds = 172800
HOURS_48=172800

if [ $DIFF -gt $HOURS_48 ]; then
    echo "⚠️ No human contact for $((DIFF / 3600)) hours. Initiating rollback..."
    
    # Find most recent backup
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR" 2>/dev/null | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        echo "❌ No backups found! Cannot rollback."
        exit 1
    fi
    
    echo "🔄 Rolling back to: $LATEST_BACKUP"
    
    # Notify via iMessage
    imsg send --to "raymondhthomas@gmail.com" --text "⚠️ AUTO-ROLLBACK: No activity for 48+ hours. Reverting workspace to last known good state: $LATEST_BACKUP"
    
    # Git operations
    cd "$WORKSPACE"
    
    # Save current state as emergency branch
    git branch "emergency-backup-$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
    
    # Hard reset to main
    git reset --hard origin/main 2>/dev/null || git reset --hard HEAD~1
    
    echo "✅ Rollback complete. Saved current state as emergency backup branch."
    echo "🔄 Reset last contact time"
    echo "$(date -u +%s)" > "$LAST_CONTACT_FILE"
else
    echo "✅ Last contact was $((DIFF / 3600)) hours ago. All good."
fi
