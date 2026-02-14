#!/bin/bash
# OpenClaw Workspace Backup Script
# Creates zip backup and syncs to Google Drive AND GitHub

set -euo pipefail

WORKSPACE_DIR="/Users/raythomas/.openclaw/workspace"
BACKUP_DIR="/tmp/openclaw-backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="openclaw-workspace-${TIMESTAMP}.zip"
DRIVE_REMOTE="google-drive"
DRIVE_PATH="OpenClaw-Backups"
RCLONE="/opt/homebrew/bin/rclone"
GIT="/usr/bin/git"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create zip of workspace (excluding .git to save space)
echo "=== Creating backup: $BACKUP_NAME ==="
cd "$WORKSPACE_DIR"
zip -r "$BACKUP_DIR/$BACKUP_NAME" . -x '*.git*' '*.crdownload' 'node_modules/*' 'target/*' 'venv/*' '.venv/*' '*.log' 'logs/*'

# Get size
SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)
echo "Zip backup created: $SIZE"

# === SYNC TO GOOGLE DRIVE ===
echo "=== Syncing to Google Drive ==="
if "$RCLONE" listremotes 2>/dev/null | grep -q "$DRIVE_REMOTE"; then
    "$RCLONE" mkdir "$DRIVE_REMOTE:$DRIVE_PATH" 2>/dev/null || true
    "$RCLONE" copy "$BACKUP_DIR/$BACKUP_NAME" "$DRIVE_REMOTE:$DRIVE_PATH/" --verbose
    echo "Google Drive sync complete"
else
    echo "WARNING: Google Drive remote '$DRIVE_REMOTE' not configured"
fi

# === SYNC TO GITHUB ===
echo "=== Syncing to GitHub ==="
cd "$WORKSPACE_DIR"

# Check if git repo is configured
if "$GIT" remote get-url origin &>/dev/null; then
    # Add all changes (excluding logs to avoid huge files)
    "$GIT" add -A 2>/dev/null || "$GIT" add -f . 2>/dev/null || true

    # Check if there are changes to commit
    if "$GIT" diff --cached --quiet; then
        echo "No changes to commit"
    else
        # Commit with timestamp
        "$GIT" commit -m "Auto-backup: $(date '+%Y-%m-%d %H:%M')"

        # Push to GitHub
        "$GIT" push origin main 2>/dev/null || "$GIT" push origin master 2>/dev/null || "$GIT" push -u origin HEAD
        echo "GitHub sync complete"
    fi
else
    echo "WARNING: GitHub remote not configured"
fi

# Keep only last 7 local backups
ls -t "$BACKUP_DIR"/*.zip 2>/dev/null | tail -n +8 | xargs -r rm
echo "Local backups cleaned up (kept last 7)"

echo "=== Backup complete ==="
