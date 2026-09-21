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
| [context-handoff.sh](context-handoff.sh) | `PostToolUse` | A `CONTEXT HANDOFF` advisory, injected as `additionalContext`, once the session crosses its token limit |
| [context-handoff.sh](context-handoff.sh) | `SubagentStop` | Nothing on stdout; writes a handoff record for an executor that stopped without a `complete` SUMMARY |
| [context-handoff.sh](context-handoff.sh) | `Stop` | Nothing; clears the session's debounce state |

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
unisolated write-capable dispatch. `context-handoff.sh` is advisory throughout:
losing a handoff costs a re-read, blocking the agent costs the session. Neither parses arbitrary scripts, resolves
every symlink, validates runtime ownership or creates a sandbox. Repository
instructions and host permissions still govern the work.

Run the Bash suite and the installed-launcher test after hook changes:

```text
bash .ai/hooks/ai-tier-notice.test.sh
bash .ai/hooks/worktree-guard.test.sh
bash .ai/hooks/context-handoff.test.sh
python -m unittest discover -s tests -p test_handoff.py -v
python -m unittest discover -s tests -p test_install.py -k registered_hooks -v
```

The tests exercise JSON and stdin behavior, host registrations, patch paths and
direct Bash launchers. They do not establish trusted live host execution.

## The handoff hook

`context-handoff.sh` is the one managed hook that measures rather than inspects.
It reads the session's own transcript -- `transcript_path` in the hook payload,
which both hosts supply -- and takes the latest token reading from it. That is
occupancy, not cumulative usage: a compaction lowers it, and the last reading
wins. Two transcript shapes are understood, matched structurally rather than by
wrapper name so an upstream rename does not silently zero the measurement:

- **Claude Code** -- a usage block, summed across `input_tokens`,
  `cache_creation_input_tokens`, `cache_read_input_tokens` and `output_tokens`,
  which is what `/context` reports.
- **Codex** -- a rollout `TokenUsageRecord`, read from
  `thread_token_usage.total_tokens`.

The fire-point is `handoff.context_percent` of `context_window` or
`handoff.context_tokens`, whichever comes first, both from
`.planning/config.yaml`. The percentage binds on a small window (60% of 200,000
is 120,000); the absolute ceiling binds on a large one, where 60% of a million
tokens is far past the point a single plan should still be accumulating context.
`phase_run query handoff.limits` reports which one binds.

Its two triggers write to `.planning/handoffs/`, which is gitignored:

- **Crossing the limit** writes a record and injects the advisory. The record is
  refreshed, not duplicated, on later tool uses, and the advisory debounces to
  one every five.
- **A subagent stopping early** writes a record naming the plan and the SUMMARY
  to read first. `worktree-guard.sh` supplies the other half: every write-capable
  dispatch it lets through is appended to a per-session active-agent stack, and
  `SubagentStop` closes one entry against its plan's SUMMARY. Missing or
  `blocked` is unfinished; only `status: complete` clears without a handoff.

Two implementation constraints are load-bearing on Windows. Records are written
by one Python process each: the obvious shape -- a `printf` per key -- spawns an
interpreter thirteen times for one record, more than the hook's whole timeout
budget, which is also why `many_fields` in [lib/json-field.sh](lib/json-field.sh)
exists alongside `field`. And every Python emitter writes binary stdout, because
text mode appends a CR that rides into each value the caller reads, turning an
event name into one that matches nothing.

The hook exits 0 on a missing transcript, absent Python, an unparseable payload
or a session id that could escape the handoff directory. Consumption is the
orchestrator's job, not the hook's -- see
[worker-handoff](../references/worker-handoff.md#handoff-records).

## Future hook work

These are planned improvements, not implemented or enabled hooks.

- **Pre-commit linting:** run the project's configured linter before a Git commit
  and block the commit when linting fails.
