# Windows Troubleshooting

**Windows users:** If plan-phase freezes during agent spawning (common on Windows due to
stdio deadlocks with MCP servers — see Claude Code issue anthropics/claude-code#28126):

1. **Force-kill:** Close the terminal (Ctrl+C may not work)
2. **Clean up orphaned processes:**
   ```powershell
   # Kill orphaned node processes from stale MCP servers
   Get-Process node -ErrorAction SilentlyContinue | Where-Object {$_.StartTime -lt (Get-Date).AddHours(-1)} | Stop-Process -Force
   ```
3. **Clean up stale task directories:**
   ```powershell
   # Remove stale subagent task dirs (Claude Code never cleans these on crash)
   Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\tasks\*" -ErrorAction SilentlyContinue
   ```
4. **Reduce MCP server count:** Temporarily disable non-essential MCP servers in settings.json
5. **Retry:** Restart Claude Code and run `/workflow:plan-phase` again

If freezes persist, try `--skip-research` to reduce the agent chain from 3 to 2 agents:
```
/workflow:plan-phase N --skip-research
```


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
