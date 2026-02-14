#!/bin/bash
# Hourly git push script
WORKSPACE_DIR="/Users/raythomas/.openclaw/workspace"
cd "$WORKSPACE_DIR" || exit

# Add core files and ignore the problematic submodules/folders
git add MEMORY.md AGENTS.md USER.md SOUL.md TOOLS.md IDENTITY.md HEARTBEAT.md .gitignore scripts/

# Commit if there are changes
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
if ! git diff-index --quiet HEAD --; then
    git commit -m "Hourly auto-push: $TIMESTAMP"
fi

# Push (using gh auth token for reliability if needed, but standard push should work now)
git push origin main
