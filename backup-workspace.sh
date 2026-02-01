#!/bin/bash
# OpenClaw Workspace Backup Script
# Creates zip backup and syncs to Google Drive

set -euo pipefail

WORKSPACE_DIR="/Users/raythomas/.openclaw/workspace"
BACKUP_DIR="/tmp/openclaw-backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="openclaw-workspace-${TIMESTAMP}.zip"
DRIVE_REMOTE="google-drive"
DRIVE_PATH="OpenClaw-Backups"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create zip of workspace (excluding .git to save space)
echo "Creating backup: $BACKUP_NAME"
cd "$WORKSPACE_DIR"
zip -r "$BACKUP_DIR/$BACKUP_NAME" . -x '*.git*' '*.crdownload' 'node_modules/*'

# Get size
SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)
echo "Backup created: $SIZE"

# Sync to Google Drive (if configured)
if rclone listremotes | grep -q "$DRIVE_REMOTE"; then
    echo "Syncing to Google Drive..."
    rclone sync "$BACKUP_DIR/$DRIVE_REMOTE:$DRIVE_PATH" --verbose
    echo "Backup synced to Google Drive"
else
    echo "Google Drive remote '$DRIVE_REMOTE' not configured. Run 'rclone config' to set up."
fi

# Keep only last 7 local backups
ls -t "$BACKUP_DIR"/*.zip 2>/dev/null | tail -n +8 | xargs -r rm
echo "Local backups cleaned up (kept last 7)"

echo "Backup complete!"
