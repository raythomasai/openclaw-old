# OpenClaw Runbook Implementation Plan

Based on the [openclaw-runbook](https://github.com/digitalknk/openclaw-runbook), this plan outlines how to stabilize and optimize our OpenClaw environment for predictability, cost-control, and reliability.

## 1. Goal
Move from "experimental" usage to a "production-ready" infrastructure where OpenClaw runs autonomously, stays within quota/cost limits, and maintains high visibility into its tasks.

## 2. Architecture: Coordinator vs. Worker
The core principle is to use cheap models for high-frequency plumbing and expensive models only for specialized tasks.

### 2.1 Model Routing
*   **Coordinator (Main Session):** Use `anthropic/claude-sonnet-4-5` (or a mid-tier model) as the primary.
*   **Heartbeat/Plumbing:** Use `openai/gpt-4o-mini` or `google/gemini-2.0-flash-lite` (cheap and fast).
*   **Specialized Agents:**
    *   `researcher`: Uses `kimi-coding/k2p5` or `synthetic/hf:zai-org/GLM-4.7`.
    *   `architect`: Uses `anthropic/claude-opus-4-6`.
*   **Fallbacks:** Define explicit fallback chains in `openclaw.json` to prevent total stalls.

### 2.2 Concurrency Caps
Prevent runaway costs and API hammering by setting limits in `openclaw.json`:
```json
"agents": {
  "defaults": {
    "maxConcurrent": 4,
    "subagents": {
      "maxConcurrent": 8
    }
  }
}
```

## 3. Memory & Context Management
Eliminate the "why did it forget" problem by making memory explicit and managing context size.

### 3.1 Explicit Search
*   Use `text-embedding-3-small` for cheap, high-quality vector search.
*   Enable `sessionMemory` to allow agents to search through their own recent history.

### 3.2 Context Pruning & Compaction
*   **Pruning:** Set `cache-ttl` mode with a 6-hour TTL to keep the hot context window lean.
*   **Compaction:** Enable `memoryFlush` with a soft threshold (e.g., 40k tokens). This automatically distills sessions into daily memory files (`memory/YYYY-MM-DD.md`) before the context gets too bloated.

## 4. Proactive Monitoring: The Rotating Heartbeat
Instead of dozens of separate cron jobs, implement a single "Rotating Heartbeat" pattern.

### 4.1 Implementation
1.  **State File:** Maintain `memory/heartbeat-state.json` to track last run times for:
    *   Email checks
    *   Calendar review
    *   Trading bot status (Alpaca/Kalshi)
    *   Workspace git status
2.  **Logic:** The heartbeat prompt (set in `openclaw.json`) should:
    *   Read the state file.
    *   Pick the most overdue check.
    *   Execute it (or spawn a sub-agent for it).
    *   Update the state file.
3.  **Cheap Routing:** Ensure the heartbeat model is pinned to a low-cost model.

## 5. Task Visibility (Todoist Pattern)
Avoid the "black box" syndrome. Every major task should be visible outside of terminal logs.

### 5.1 Plan
*   Integrate a task manager (e.g., Apple Reminders via `remindctl` or a dedicated Markdown file `TASKS.md`).
*   **Rules:**
    *   Agents MUST create a task entry before starting long-running work.
    *   Agents MUST update the task state (In Progress, Blocked, Done).
    *   Human intervention requests (e.g., 1Password unlock) get high-priority task flags.

## 6. Security Hardening
Since we interact with untrusted web content and remote nodes, we need clear boundaries.

### 6.1 Actions
*   **Tool Policies:** Restrict sensitive tools (gateway config, file deletion) to certain sessions.
*   **Credential Management:** Continue using 1Password CLI (`op`) via the skill for all secret injection.
*   **Redaction:** Enable `redactSensitive: "tools"` in `openclaw.json` logging.

## 7. Immediate Implementation Steps

### Phase 1: Configuration Update (Today)
1.  [ ] Review current `openclaw.json` against the `sanitized-config.json` patterns.
2.  [ ] Apply concurrency caps and context pruning settings.
3.  [ ] Configure `text-embedding-3-small` for memory search.

### Phase 2: Heartbeat Refactor (Next 48h)
1.  [ ] Create `memory/heartbeat-state.json`.
2.  [ ] Update `HEARTBEAT.md` with instructions for the rotating pattern.
3.  [ ] Test with a simple check (e.g., "Check local weather if >4h since last").

### Phase 3: Task Visibility (Next 72h)
1.  [ ] Establish `TASKS.md` as the local source of truth.
2.  [ ] Update `SOUL.md` to mandate task logging for all sub-agent spawns.

---
*Created by Jarvis | Reference: digitalknk/openclaw-runbook*
