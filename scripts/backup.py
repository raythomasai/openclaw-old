#!/usr/bin/env python3
"""Daily backup script - copies key files to backup directory"""

import shutil
import os
from datetime import datetime

BACKUP_DIR = "/Users/raythomas/.openclaw/workspace/backups"
KEY_FILES = [
    "/Users/raythomas/.openclaw/workspace/MEMORY.md",
    "/Users/raythomas/.openclaw/workspace/FUTURE_PROJECTS.md",
    "/Users/raythomas/.openclaw/workspace/scripts/visual_helper.py",
]

def backup():
    """Copy key files to backup directory."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    
    for filepath in KEY_FILES:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            backup_path = os.path.join(BACKUP_DIR, f"{timestamp}_{filename}")
            shutil.copy2(filepath, backup_path)
            print(f"✅ Backed up: {filename} → {backup_path}")
        else:
            print(f"❌ Missing: {filepath}")

if __name__ == "__main__":
    backup()
    print("\n🚀 Starting git backup...")
    os.system("bash /Users/raythomas/.openclaw/workspace/scripts/git_backup.sh > /dev/null 2>&1 &")
