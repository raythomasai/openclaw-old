#!/bin/bash
# Simple git backup - runs in background, no timeout
cd /Users/raythomas/.openclaw/workspace
nohup git add MEMORY.md FUTURE_PROJECTS.md scripts/*.py > /tmp/git_backup.log 2>&1 &
sleep 2
nohup git commit -m "Backup: $(date '+%Y-%m-%d %H:%M')" > /tmp/git_commit.log 2>&1 &
sleep 2
nohup git push origin main > /tmp/git_push.log 2>&1 &
echo "Git backup started in background"
