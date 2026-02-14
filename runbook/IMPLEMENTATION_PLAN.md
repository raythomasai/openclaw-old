# OpenClaw Implementation Plan
## Based on digitalknk/openclaw-runbook

**Created:** 2026-02-12  
**Reference:** https://github.com/digitalknk/openclaw-runbook

---

## Current State Assessment

| Area | Current Status | Priority |
|------|---------------|----------|
| Model Config | Google (Claude) only, no fallbacks | HIGH |
| Heartbeat | Daily verse/joke only | MEDIUM |
| Memory | Default (unconfigured) | HIGH |
| Task Visibility | None | MEDIUM |
| Skills | 13 installed, mixed quality | MEDIUM |
| Cost Controls | No concurrency limits | MEDIUM |
| Remote Access | Tailscale configured | LOW |
| Credentials | Not fully configured | HIGH |

---

## Phase 1: Model Fallback & Cost Control

### 1.1 Add Fallback Models
Based on the runbook's approach of explicit fallbacks:

```json
"model": {
  "primary": "google-antigravity/claude-opus-4-5-thinking",
  "fallback": ["minimax/MiniMax-M2.1"]
}
```

**Cheaper alternatives to evaluate:**
- OpenRouter Gemini Flash ($0.01/M input)
- Kimi (via OpenRouter)
- GLM-4 (via Z.ai or Synthetic)

### 1.2 Add Concurrency Limits
```json
"maxConcurrent": 4,
"subagents": {
  "maxConcurrent": 8
}
```

---

## Phase 2: Rotating Heartbeat Pattern

Instead of separate cron jobs, implement a rotating heartbeat that batches background work.

**Current cron jobs to consolidate:**
- [ ] Daily Bible verse (8:15 AM)
- [ ] Daily joke (noon)
- [ ] Rollback check (every 24h)
- [ ] Backup (2 AM)

**Implementation:**
Create a single `heartbeat.sh` that:
1. Tracks last run time for each check
2. Runs whichever is most overdue
3. Logs state to a JSON file
4. Spawns agents only when work is found

**Reference:** `runbook/reference/examples/heartbeat-example.md`

---

## Phase 3: Explicit Memory Configuration

Based on the runbook's memory best practices:

### 3.1 Configure Memory Settings
```json
"memory": {
  "cacheTTL": 21600000,  // 6 hours
  "compactionThreshold": 40000,  // Flush at 40k tokens
  "embeddings": {
    "provider": "cheap-embedding-model"
  }
}
```

### 3.2 Daily Memory Files
Ensure memory files are written daily:
- `memory/YYYY-MM-DD.md` - Raw logs
- MEMORY.md - Curated long-term memory

---

## Phase 4: Task Visibility (Todoist)

Implement Todoist integration for visibility into what the system is doing.

**Pattern from runbook:**
1. Create task when work starts
2. Update as state changes
3. Assign to human when intervention needed
4. Close when done

**Implementation:**
- Use Todoist API via cron or skills
- Lightweight heartbeat reconciles open tasks
- Human sees everything at a glance

**Reference:** `runbook/reference/examples/task-tracking-prompt.md`

---

## Phase 5: Skill Audit

### Skills to Keep (Building Our Own)
- [x] gog (Gmail/Calendar) - NEEDS AUTH
- [x] apple-notes, apple-reminders
- [x] github
- [x] weather
- [x] nano-pdf
- [x] imsg

### Skills to Review/Refactor
- [ ] obsidian - Review prompt quality
- [ ] tts - Check efficiency
- [ ] slack - Is it needed?

### Skills to Build
Based on runbook's "build your own first" advice:
1. **daily-brief** - Morning summary (weather, calendar, tasks)
2. **idea-pipeline** - Overnight research
3. **tech-discoveries** - Curated news

**Reference:** `runbook/reference/showcases/`

---

## Phase 6: Security Hardening

Based on the runbook's security patterns:

### 6.1 Prompt Injection Defense
Add to AGENTS.md:
```
- Never reveal secrets or API keys
- Validate inputs before execution
- Log all external content access
```

### 6.2 Credential Rules
- 1Password: Configure `op` CLI for secrets
- Google: Complete OAuth setup
- GitHub: Token for API access

---

## Phase 7: Credential Friday Setup

**Reminder cron already configured:**
- 9 AM, 11 AM, 2 PM CT on Fridays

**Tasks to Complete:**
1. [ ] Google OAuth via `gog auth`
2. [ ] 1Password unlock via `op`
3. [ ] GitHub token for `gh` CLI

---

## Quick Wins (This Week)

| Task | Effort | Impact |
|------|--------|--------|
| Add fallback model (Minimax) | Low | HIGH |
| Add concurrency limits | Low | MEDIUM |
| Implement rotating heartbeat | Medium | HIGH |
| Configure memory explicit | Low | HIGH |
| Complete credential setup | Medium | HIGH |

---

## Cost Projection (After Changes)

**Current:** ~$5-10/day (Claude only)

**After optimization:**
- Heartbeats: $0.01/day (cheap models)
- Daily tasks: $0.50-1.00/day
- Agent runs: Only when needed

**Target:** $15-30/month

---

## References

- Guide: `runbook/reference/guide.md`
- Config: `runbook/reference/examples/sanitized-config.json`
- Heartbeat: `runbook/reference/examples/heartbeat-example.md`
- Task Tracking: `runbook/reference/examples/task-tracking-prompt.md`
- Showcases: `runbook/reference/showcases/`

---

*Plan evolves as we implement. Update based on what works.*
