# Rotating Heartbeat Instructions

You are responsible for proactive workspace maintenance and situational awareness. 
Follow these steps every time you receive a heartbeat prompt:

1. **Read State:** Load `memory/heartbeat-state.json`.
2. **Prioritize:** Find the task with the oldest timestamp.
3. **Execute:** Perform the check (e.g., search emails, check calendar, verify trading logs).
4. **Update:** Update the timestamp in `memory/heartbeat-state.json` to the current time (use `📊 session_status` for the time).
5. **Report:** Only notify Ray if there is something urgent or noteworthy. Otherwise, finish quietly.

## Check Definitions
- **Email:** Check raythomaswi@icloud.com for urgent messages.
- **Calendar:** Check for upcoming events in the next 24 hours.
- **Trading:** Check `projects/alpaca-trading/logs/status.json` for errors or major profit/loss.
- **Workspace:** Check `git status` in the workspace to ensure no uncommitted changes are sitting for too long.
- **Weather:** Check weather if Ray is likely to be heading out.

If multiple checks are due, you may combine 2-3 in one go.
