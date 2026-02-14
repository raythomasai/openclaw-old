---
name: mail-send
description: Send emails via macOS Mail.app using AppleScript. Works with iCloud, Gmail, or any account configured in Mail.app.
metadata: {"openclaw":{"emoji":"📧","os":["darwin"],"requires":{"bins":["osascript"]}}}
---

# macOS Mail.app Email Skill

Send emails using the native macOS Mail.app via AppleScript.

## Usage

**Basic email:**
```
Send email to: raymondhthomas@icloud.com
Subject: Meeting Tomorrow
Body: Hi, let's meet at 3pm.
```

**Multi-line body:**
```
Send email to: recipient@example.com
Subject: Project Update
Body: Hi Team,

Here's the weekly update:
- Task 1: Complete
- Task 2: In progress
- Task 3: Blocked

Best regards
```

## Commands (for agent)

Send email via AppleScript:
```bash
osascript -e '
tell application "Mail"
  set newMessage to make new outgoing message with properties {subject:"Subject Here", content:"Body Here"}
  tell newMessage
    make new to recipient with properties {address:"recipient@email.com"}
  end tell
  send newMessage
end tell'
```

**Important:** Escape quotes in subject/body: `"` → `\"`

## Requirements

- macOS with Mail.app configured
- iCloud or any email account set up in Mail.app
- Mail.app must be running (or will auto-launch)

## Notes

- Uses native AppleScript - no OAuth/setup needed
- Works with any account in Mail.app (iCloud, Gmail, etc.)
- Email appears in Sent folder automatically
- macOS only (darwin)
