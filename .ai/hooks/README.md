---
tier: contract
authority: agent
title: Optional hook examples
links: [AMD-002]
---

# Optional hook examples

These Bash scripts are present but unregistered. No settings file, hook
installer or dispatcher is supplied. Run with Bash; a compatible host must
explicitly connect its tool events to the scripts and interpret their output.

| Script | Input and behavior |
| --- | --- |
| [ai-tier-notice.sh](ai-tier-notice.sh) | Reads JSON containing file_path, emits advisory tier reminders, exits zero. PROJECT, RULES and approval policy use intent reminders. |
| [worktree-confine.sh](worktree-confine.sh) | Reads cwd, tool_name and tool_input JSON. Some Write/Edit/NotebookEdit targets and obvious Bash redirects outside the checkout produce a PreToolUse denial response. Shared Git and supplied scratch space are allowed. |

Neither script is a sandbox. Missing context can fail open. Path checks are
lexical, do not resolve symlinks or junctions, and fold case on every platform.
The confinement script cannot reliably parse arbitrary shell commands. Its
JSON parser prefers jq, then Python, then a weaker sed fallback. The tier
reminder also uses a simple parser. Keep the host's actual permissions in force.

Configuration's `enforcement: advisory` describes the tier reminder; it does
not install either script or disable a separately registered confinement hook.
Use [gates](../gates/README.md) for the manual transition requirements. Test
any host integration in its actual environment before relying on it.
