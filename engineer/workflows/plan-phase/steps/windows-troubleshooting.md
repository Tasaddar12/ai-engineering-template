# Windows Troubleshooting

**Windows users:** If plan-phase freezes during agent spawning (common on Windows due to
stdio deadlocks with MCP servers â€” see Claude Code issue anthropics/claude-code#28126):

1. **Preserve and identify:** Record each actual worker/session handle, assigned checkout, branch/base/head, known dirty paths and observed host state. A quiet wait, process age or executable name does not prove an orphan or ownership.
2. **Request a bounded status observation:** Use the native host handle and record the returned state/timestamps under [parallel status](../../../references/parallel-status.md). Do not force-close a terminal that may own unrelated work.
3. **Confirm stop before recovery:** If stopping is necessary, request it through the actual host interface and wait for terminal completion or positive stopped confirmation. A timeout is not confirmation. Preserve ownership when the host cannot confirm stop.
4. **Recover only positively owned resources:** A process must have a recorded PID plus creation time and assignment provenance; re-read that identity immediately before stopping it. Never enumerate all Node processes and infer ownership from age or name. A task directory must be an exact recorded assignment directory whose owner is confirmed stopped, with useful evidence already preserved. Resolve its absolute path, verify it remains beneath the intended task root, inspect the exact target and require the applicable cleanup authorization before removing it. Never wipe a shared task root or use a wildcard deletion. Unknown ownership means preserve and report.
5. **Adjust only the affected session:** Inspect which MCP server or native operation actually stalled. Disable a nonessential server only within authorized configuration scope, preserving its prior setting and the evidence gap it creates. Do not silently weaken required research.
6. **Continue from durable progress:** After stop is confirmed, inspect the assigned committed artifacts and use a fresh bounded continuation for remaining work. Keep completed research/plans and existing authority. Restarting the host does not authorize duplicate writers or changing the base.

If freezes persist, try `--skip-research` to reduce the agent chain from 3 to 2 agents:
```
/plan-phase N --skip-research
```
