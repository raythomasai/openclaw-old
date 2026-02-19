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

## 🛠 Maintenance & Background

- [x] Fix `hourly-git-push.sh` to include `TASKS.md` (2026-02-18)
- [ ] Investigate missing Alpaca logs/daemon status
- [ ] Check VPN/Proton credentials for Polymarket bot


