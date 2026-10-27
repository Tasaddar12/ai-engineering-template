# Hooks

These hooks use Python 3.11 standard-library code through `python-hook.sh`. They do not install packages or invoke Node tooling. Installed registrations use the selected host namespace and resolve from the Git root, including calls made from subdirectories.

| Entry | Event | Contract |
|---|---|---|
| planning-integrity.sh / .py | PreToolUse shell commands | Detect prospective Git commits and call `engineer/bin/engineer.py query planning.integrity`. An integrity failure returns 2. `planning.validate` diagnostics are warn-only. |
| worktree-path-guard.py | PreToolUse Agent/Task and write tools | Warn about missing isolation, primary-checkout writes, scratchpad destinations and paths traversing symlinks/reparse points. Always return 0, including malformed JSON. Append dispatch metadata under `.planning/handoffs/` only after checking state-path containment. |
| context-handoff.sh / .py | PostToolUse, SubagentStop, Stop; SessionStart on Codex | Read `handoff.limits`, compare observed context tokens with its percent/token threshold, and persist a continuation digest through `handoff.write`. Advisory additionalContext only; never stops the coordinator. |
| ai-tier-notice.sh / .py | PostToolUse write/shell tools | Warn about primary-checkout location and the recorded phase-implementation authority boundary. Always return 0. |
| worktree-location.sh / .py | WorktreeCreate/WorktreeRemove on Claude | Create a validated `<root>/.worktrees/<name>` on `worktree-<name>`. Removal uses Git without force and refuses dirty or linked locations. Lifecycle failure returns 2. |

`lib/agent-roles.sh` is the shared canonical role inventory. Python consumers parse its quoted assignments; they do not source arbitrary commands. Read-only roles never receive a request to write a SUMMARY. Source workers converge on committed owned work; artifact writers preserve a useful partial artifact and name coverage gaps.

Hook JSON is untrusted input. A malformed event must not become a tool denial from an advisory hook. No hook recursively deletes a path, follows a state-directory reparse point, publishes work, approves a decision, switches a worker branch or creates a successful check result.

`context-handoff.py` obtains configured limits through the runtime, which reads `.planning/config.yaml`. It uses a bounded transcript tail when the event carries no direct token usage. Missing context evidence or an unavailable runtime is an advisory diagnostic, not permission to infer completion.

`scripts/cleanup.py` is deliberately absent from registrations. Use `preview`, inspect its exact entries, then `apply --approval-token TOKEN --confirm`. The runtime revalidates ownership, clean state, ancestry and captured HEAD separately before every deletion. No implicit force option exists.

Tests are under `tests/hooks/` and `tests/test_worktree_path_guard.py`. Execute them only at the workflow's authorized validation point.
