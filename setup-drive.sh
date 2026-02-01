#!/bin/bash
# Setup Google Drive remote for rclone
# Run this interactively: ./setup-drive.sh

echo "Setting up Google Drive remote for OpenClaw backups..."
echo ""
echo "This will open rclone's interactive configuration."
echo "When prompted:"
echo "  1. Type 'n' for new remote"
echo "  2. Name it 'google-drive'"
echo "  3. Type '18' for Google Drive"
echo "  4. Follow the OAuth prompts (will open browser)"
echo "  5. Type 'y' to confirm"
echo "  6. Type 'q' to quit"
echo ""
read -p "Press Enter to continue..."

rclone config

echo ""
echo "To test: rclone listremotes"
echo "To sync manually: rclone sync /tmp/openclaw-backups google-drive:OpenClaw-Backups"
