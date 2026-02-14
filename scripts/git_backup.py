#!/usr/bin/env python3
"""Git backup script - commits and pushes key files"""

import subprocess
import os
from datetime import datetime

os.chdir("/Users/raythomas/.openclaw/workspace")

def git_backup():
    """Commit and push key files to GitHub."""
    files = ["MEMORY.md", "FUTURE_PROJECTS.md"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Stage files
    result = subprocess.run(["git", "add"] + files, capture_output=True)
    if result.returncode != 0:
        print(f"❌ Git add failed: {result.stderr}")
        return
    
    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", f"Backup: {timestamp}"],
        capture_output=True
    )
    if result.returncode != 0:
        if "nothing to commit" in result.stderr:
            print("ℹ️ No changes to commit")
            return
        print(f"❌ Git commit failed: {result.stderr}")
        return
    
    # Push
    result = subprocess.run(["git", "push"], capture_output=True, timeout=30)
    if result.returncode != 0:
        print(f"⚠️ Git push failed (may be network): {result.stderr}")
    else:
        print("✅ Git backup complete")

if __name__ == "__main__":
    git_backup()
