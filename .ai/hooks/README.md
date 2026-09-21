---
tier: contract
authority: agent
title: Advisory host hooks
---

# Advisory host hooks

[Installation](../commands/install.md) registers the existing scripts directly:

| Script | Event | Output |
|---|---|---|
| [ai-tier-notice.sh](ai-tier-notice.sh) | `PostToolUse` | A `NOTICE` naming document ownership and responsibilities |
| [worktree-guard.sh](worktree-guard.sh) | `PreToolUse` on `Agent`/`Task` | **Blocks** (exit 2) a write-capable subagent dispatched without `isolation="worktree"` |
| [worktree-guard.sh](worktree-guard.sh) | `PreToolUse` on write tools | A `WARNING` when an edit lands outside a linked worktree |

`worktree-guard.sh` is the exception to the advisory rule below: worktree
isolation is a hard requirement of this project, so its dispatch check emits a
real permission decision. The workflow text asks the orchestrator to pass
`isolation="worktree"`, but a prose instruction cannot enforce itself — a model
under load skips it, and the executor then commits into the primary checkout
unnoticed. Its write check only warns, because the orchestrator legitimately
edits planning records in the primary checkout and a hook that cannot tell an
orchestrator from a stray executor must not stop the user's work.

Codex registrations use `.codex/config.toml`; Claude uses `.claude/settings.json`.
The Codex Windows launcher ends in `; exit $LASTEXITCODE` because PowerShell
`-Command` does not otherwise propagate the script's exit status, which would
discard a denial the hook had already decided.
Scripts live in the selected host's `hooks` folder. There is no Python hook
adapter. The command locates the script from the active Git root, including when
the host starts from a subdirectory.

Use `--no-hooks` to skip adding registrations; existing hooks are preserved.
Existing settings remain authoritative. Codex must trust the project and hooks
before running them. Installed files alone do not prove live host execution.
See [Codex hooks](https://learn.chatgpt.com/docs/hooks).

Bash and Git must be available. On Windows, the Codex launcher locates Git Bash
beside the Git executable instead of using WSL's `bash.exe`; Claude uses Git Bash.
JSON extraction uses jq when available, then Python, with a limited text
fallback. The script supports file fields and Codex `apply_patch`
Add/Update/Delete/Move headers.

`ai-tier-notice.sh` is advisory: it exits successfully and never emits a
permission decision. `worktree-guard.sh` warns on writes and blocks only an
unisolated write-capable dispatch. Neither parses arbitrary scripts, resolves
every symlink, validates runtime ownership or creates a sandbox. Repository
instructions and host permissions still govern the work.

Run the Bash suite and the installed-launcher test after hook changes:

```text
bash .ai/hooks/ai-tier-notice.test.sh
bash .ai/hooks/worktree-guard.test.sh
python -m unittest discover -s tests -p test_install.py -k registered_hooks -v
```

The tests exercise JSON and stdin behavior, host registrations, patch paths and
direct Bash launchers. They do not establish trusted live host execution.

## Future hook work

These are planned improvements, not implemented or enabled hooks.

- **Pre-commit linting:** run the project's configured linter before a Git commit
  and block the commit when linting fails.
- **Context-triggered handoff:** at 100,000 context tokens or 50% of the context
  window, whichever is reached first, require the current subagent to save a
  handoff and stop taking new work. Preserve its revision, completed work,
  remaining tasks and evidence, then have the orchestrator assign the remainder
  to a fresh subagent. Use actual host-reported context occupancy; cumulative
  token usage is not a substitute.
