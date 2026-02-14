# Memory

## About Ray

### Faith & Values
- **Christian** - values Christian ideals and the Bible
- Daily Bible verse reminder set for 8:20 AM CT

### Communication Preferences (CRITICAL)
- **Primary Google Account:** raythomaswi@icloud.com
- **Text messages** → text reply only (no voice)
- **Voice memos** → voice reply only (no text)
- **Visual communication** → IMAGES preferred over text lists!
- **Voice preference**: bm_daniel (British male) via Kokoro TTS
- **Browser Automation Rule (CRITICAL):** ALWAYS use `profile="openclaw"` for browser tasks. Never ask Ray to attach a tab or click the extension relay button. If the profile isn't running, start it automatically using `openclaw browser --browser-profile openclaw start`.

This is a hard rule - must follow every time.

### How Ray Works

**Research first:** Always check if a problem has already been solved before inventing solutions.

**Best architecture:** Prioritize clean, scalable solutions over quick hacks.

**Self-sufficient:** Never ask Ray to do what I can do myself or what my tools can handle.

**Proactive check-ins:** 3x/day max — morning, noon, evening. Be relevant with the information.

**Strategic:** Think long-term, command sub-agents to handle tasks.

**Preferred Editor:** Kiro (dev.kiro.desktop) for text, JSON, and Markdown files.

**Autonomy rule (CRITICAL):**
- Never ask Ray to run a command I can run myself
- Always look for solutions so I can operate autonomously
- Be proactive about finding ways to take work off Ray's plate
- I like to solve problems and remove friction from Ray's experience

---

## Infrastructure & Remote Access
- **Tailscale IP:** 100.87.148.101 (rays-mac-mini-2)
- **SSH (Remote Login):** Configured for Tailscale access
- **VNC (Screen Sharing):** Configured for Tailscale access

---

## Active Projects

### Alpaca Trading System (2026-02-06 Update)
**Location:** `projects/alpaca-trading/`
**Goal:** Consistent daily profits via automated trading
**Status:** RUNNING (restarted Feb 6)
**Mode:** LIVE TRADING

**Account (Feb 6):**
- Portfolio: $448.19
- Positions: 4 (AAPL, GOOGL, JNJ, TSLA)
- Strategy: momentum_breakout
- Target: Learn and improve daily

**Key Lessons Learned:**
- Position sizing matters - need more buying power
- Momentum strategy needs refinement
- Don't let daemon stop - keep it running!

**Next Steps:**
- Add more buying power for flexibility
- Improve momentum_breakout strategy parameters
- Add daily learning/optimization
- Monitor and adjust in real-time

---

### Kalshi Trading Bot
**Location:** `projects/kalshi-bot/`
**Status:** WAITING ON API ACCESS
- API keys have READ-only permissions
- Email sent to contact@kalshi.com
- Waiting for trading permissions

---

---

### Second Kalshi Bot (Arbitrage)
**Location:** `projects/secondkalshibot/`
**Goal:** Polymarket ↔ Kalshi arbitrage (Rust implementation)
**Status:** READY (Dry Run verified)
- Cloned from `taetaehoho/poly-kalshi-arb`
- Configured with Polymarket API keys (from 1Password) and Kalshi PEM key
- Modified to support direct API key authentication
- Successfully loads 1166 team mappings and performs market discovery

---

# OpenClaw Documentation Reference

## Primary Documentation
**Always check first:** https://docs.openclaw.ai/

This is the authoritative source for all OpenClaw configuration, setup, and usage instructions.

## Key Documentation Hubs

### Getting Started
- Getting Started: /start/getting-started
- Wizard setup: /start/wizard (run `openclaw onboard`)
- Dashboard: http://127.0.0.1:18789/

### Configuration
- Gateway configuration: /gateway/configuration
- Configuration examples: /gateway/configuration-examples
- Config file location: `~/.openclaw/openclaw.json`

### Channels
- WhatsApp: /channels/whatsapp
- Telegram: /channels/telegram
- Discord: /channels/discord
- iMessage: /channels/imessage
- Mattermost (plugin): /channels/mattermost

### Concepts
- Sessions: /concepts/session
- Groups: /concepts/groups
- Multi-agent routing: /concepts/multi-agent
- Streaming: /concepts/streaming

### Tools & Automation
- Slash commands: /tools/slash-commands
- Skills: /tools/skills
- Skills config: /tools/skills-config
- Cron jobs: /automation/cron-jobs
- Webhooks: /automation/webhook

### Nodes & Platforms
- iOS node: /nodes (and /platforms/ios)
- Android node: /nodes (and /platforms/android)
- macOS app: /platforms/macos
- Linux app: /platforms/linux
- Windows (WSL2): /platforms/windows

### Reference
- Workspace templates: /reference/templates/AGENTS
- RPC adapters: /reference/rpc
- Gateway runbook: /gateway
- Troubleshooting: /gateway/troubleshooting
- Security: /gateway/security

## Quick Reference Commands

```bash
# Start the gateway
openclaw gateway

# Onboard + install daemon
openclaw onboard --install-daemon

# Login to channels (WhatsApp QR)
openclaw channels login

# Send a message
openclaw message send --target +15555550123 --message "Hello"

# Check status
openclaw status

# Configure
openclaw configure --section <section>
```

## Memory Maintenance Rule
When the user asks me to configure something or set up a feature, I should:
1. First check this documentation reference
2. Fetch the relevant docs page if needed
3. Follow the documented steps
4. Update this memory file with any important user-specific configurations

---

## Resilience & Rollback System

### Auto-Rollback (48 hours)
- **Script:** `scripts/rollback-check.sh`
- **Schedule:** Every 24 hours via cron
- **Trigger:** No human contact for 48 hours
- **Action:** Resets workspace to last known good state (origin/main)
- **Safety:** Creates emergency backup branch before rollback
- **Notification:** Sends iMessage to raymondhthomas@gmail.com

### Friday Credential Setup Reminders
- **Reminder 1:** 9 AM CT
- **Reminder 2:** 11 AM CT  
- **Reminder 3:** 2 PM CT
- **Goal:** Configure Google OAuth, GitHub tokens, 1Password unlock
- **Priority:** Ray will help unlock 1Password CLI

### Backup Directory
- **Location:** `backups/`
- **Created by:** rollback-check script
- **Purpose:** Store emergency snapshots for rollback recovery
