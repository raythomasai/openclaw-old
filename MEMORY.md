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
