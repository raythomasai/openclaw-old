# TASKS.md - Central Task Tracker

This file is the source of truth for all ongoing work.
Follow the **openclaw-runbook** visibility pattern:
1. Create a task entry before starting long-running work.
2. Update state (In Progress, Blocked, Done).
3. Notify Ray for high-priority/blocked items.

---

## 🟢 Active Implementation: OpenClaw Runbook Phase 1

- [x] Create `memory/heartbeat-state.json` (Phase 2 start)
- [x] Update `HEARTBEAT.md` with rotating logic
- [/] Update `openclaw.json` (Phase 1 config)
    - [x] maxConcurrent caps
    - [ ] contextPruning (update to 6h)
    - [ ] memorySearch (verify embedding model)
- [ ] Establish `TASKS.md` usage in `SOUL.md` (Phase 3)

---

## 🔐 Credentials & Trading

- [ ] Re-engineer the Kalshi bot
- [x] Update Polymarket credentials for `secondkalshibot` (2026-02-16)
- [x] Restart arbitrage bot in LIVE mode

