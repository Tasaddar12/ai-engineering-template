---
tier: contract
authority: agent
title: Managed host hooks
---

# Managed host hooks

[Installation](../commands/install.md) registers the existing scripts directly:

| Script | Event | Output |
|---|---|---|
| [destructive-git-guard.py](destructive-git-guard.py) | `PreToolUse` on `Bash`, `exec_command`, `shell_command`, `shell` | Blocking refusal JSON with stable `reason_code` and exit 2 for recognized unsafe Git/backup operations |
| [planning-integrity.sh](planning-integrity.sh) | `PreToolUse` on `Bash`, `exec_command`, `shell_command`, `shell` | Exit 2 with a diagnostic when prospective commits contain malformed changed canonical planning records |
| [ai-tier-notice.sh](ai-tier-notice.sh) | `PostToolUse` | A `NOTICE` naming document ownership and responsibilities |
| [source-prewrite.sh](source-prewrite.sh) | `PreToolUse` on write tools | Cancels source mutations that need isolation; Claude can receive a ticketed same-agent native-entry instruction, while Codex cannot move that caller (its separate launcher starts a new run) |
| [worktree-guard.sh](worktree-guard.sh) | `PreToolUse` on `Agent`/`Task` | A stderr `WARNING` with isolation guidance; exits 0 and records the write-capable dispatch |
| [worktree-guard.sh](worktree-guard.sh) | `PreToolUse` on write tools | A stderr `WARNING` for primary-checkout writes, including scratchpads, or paths into another checkout; exits 0 |
| [context-handoff.sh](context-handoff.sh) | `PostToolUse` | A `CONTEXT HANDOFF` advisory, injected as `additionalContext`, once the session crosses its token limit |
| [context-handoff.sh](context-handoff.sh) | `SubagentStop` | Nothing on stdout; writes a handoff record for an executor that stopped without a `complete` SUMMARY. Works on both hosts, from different inputs — see below |
| [context-handoff.sh](context-handoff.sh) | `Stop` | Nothing; clears the session's debounce state |
| [context-handoff.sh](context-handoff.sh) | `SessionStart` (Codex only) | Nothing on stdout; writes the orchestrator's transcript path to `.planning/handoffs/.root-<session>.json` |
| [worktree-location.sh](worktree-location.sh) | `WorktreeCreate` (Claude only) | Ordinary dispatch creation retains name reuse and starts from the dispatching checkout's `HEAD`; reserved `wf-entry-<request>` creation is ticket-validated, fresh-only, and starts from its pinned local base |
| [worktree-location.sh](worktree-location.sh) | `WorktreeRemove` (Claude only) | Ordinary removal runs `git worktree remove` without `--force`; native-entry candidates are preserved for inspection |

`source-prewrite.sh` runs after the advisory guard in the managed editing group.
It treats source, mixed, tracked and unsafe mutations as source decisions; it
does not precreate a worktree. Untracked planning scratchpads and handoff scratch
notes, plus plain add/update notes under the OS temporary directory outside any
repository, retain their narrow allow path. The advisory guard still warns on
primary-checkout writes, including scratchpads; its behavior is unchanged.

For Codex, the installed `.codex/codex-worktree.py` starts a **new** phase or
quick run in a validated session worktree. It does not move the active caller.
The Codex guard registers synchronous `PreToolUse` (`*`), `SessionStart` and
`UserPromptSubmit` handlers. Lifecycle events provide repository diagnostics;
the primary checkout's ordinary note lifecycle remains available at
`UserPromptSubmit`, while supported source operations remain subject to
`PreToolUse`. The canonical startup reference explains direct-executable
requirements, trust and policy checks, and unverified host behavior.
Installation or export inspection alone does not prove that a live Codex host
ran a generated guard.

The Claude continuation is conditional on the same existing agent actually
having a compatible native `EnterWorktree` tool/schema, an eligible role, policy
permission, and the trusted registered creation hook. The installed coordinator
and coder roles export the native tool, but an export alone does not prove that
the active host advertises or permits it. After source denial, the caller uses
the request ID from the reason and the documented `prewrite.begin` verb. For a
new unit, only the reserved fresh `wf-entry-` name enters the ticketed
`WorktreeCreate` path, which verifies source root/branch/HEAD and creates from
that pinned local commit. A creation callback or returned path is not movement:
the same agent must observe native completion and prove that later calls use the
destination by default, then run `prewrite.confirm` for Git checks. Confirmation
returns `host_binding_verified: false`; it does not authenticate host binding,
permissions or loaded context. Fresh destination reads and a rebuilt edit are
required, and the cancelled mutation is never replayed.

Phase and quick workflows also request native entry before their first edit,
without inventing a pending mutation. `prewrite.request` binds a known unit in
explicit `new` or `existing` mode. Existing mode targets the validated ordinary
session and preserves its accumulated HEAD, historical base and ownership; it
uses the host's native existing-path form and honors any required approval.
Native creation never reuses an existing name to bypass that approval. The
regular `session.open` route still creates or resumes ordinary sessions with
its existing behavior. See [same-agent native entry](../references/same-agent-worktree.md)
for the full gate and recovery protocol.

`worktree-guard.sh` is advisory for both dispatches and editing tools. It warns
and continues when a write-capable dispatch lacks `isolation="worktree"`, when a
write targets the primary checkout (including planning records and scratchpads),
or when an absolute path targets another checkout. Workflows still start source
work in session worktrees and dispatch isolated executors. Allowed write-capable
dispatches, including warned and qualified roles, retain handoff tracking.

Codex registrations use `.codex/config.toml`; Claude uses `.claude/settings.json`.
The Codex Windows launcher ends in `; exit $LASTEXITCODE` because PowerShell
`-Command` does not otherwise propagate the script's exit status. The advisory
guard returns 0; launcher failures still need their actual status. Three other
details of that one line are each load-bearing, and each was a hook that
silently did not run:

- **Git Bash is probed, not computed.** `git.exe` sits at `<root>/cmd/git.exe`
  in an installer-managed install but at `<root>/mingw64/bin/git.exe` in a
  portable, scoop or winget one. Resolving `../bin/bash.exe` from the second
  layout names a file that does not exist, so every Codex hook failed to launch
  on those machines. The launcher now tries the known layouts and takes the
  first bash that is really there. PATH is deliberately not a fallback: on
  Windows it commonly finds WSL's `bash.exe`, which cannot see the Windows
  checkout the hook is about to inspect. Finding none exits 1 -- an error worth
  seeing rather than a silent no-op.
- **The repository path never crosses into PowerShell.** Capturing
  `git rev-parse` there and passing the result to bash mangles every non-ASCII
  component; a checkout under `projet café 日本語` reached bash as box-drawing
  characters. bash gets an ASCII-only `-c` string and resolves the root itself,
  exactly as the POSIX `command` does.
- **The inner quotes are written `\"`.** PowerShell re-parses a native command's
  arguments and consumes a bare `"` rather than passing it, which re-split the
  script at its spaces and left bash treating `rev-parse` as its own name.

Scripts live in the selected host's `hooks` folder. Python suffixes use the
`python` interpreter; shell scripts use Bash. The command locates the script
from the active Git root, including when the host starts from a subdirectory.
`source-prewrite.sh` is a shell entrypoint delegating its source decision to
`runtime/lib/prewrite.py`.
The Codex Python `commandWindows` resolves that root inside Python, runs the
entrypoint with `runpy` and propagates `$LASTEXITCODE`. Python source is never
interpreted as Bash. Both `.codex` and `.claude` copies import their adjacent
`runtime/lib/destructive_guard.py` rather than the source `.ai` namespace.

The planning integrity hook has a 10-second host timeout and invokes its
installed sibling Python checker through the same Bash launcher on both hosts.
It validates prospective commit bytes without modifying the real Git index;
missing required frontmatter such as `issue_refs` blocks the commit with exit 2.
Ordinary runtime mutations also retain canonical planning snapshots and return
authored-content `integrity_warnings` on success or expected errors. The exact
registered `prewrite.request`, `prewrite.begin` and `prewrite.confirm` adapters
instead use bounded UTF-8 Git discovery and write Git-common-dir journal/session
metadata, so they skip canonical `.planning` snapshots. Handler registration is
checked first; unknown names and future prefix-sharing verbs have no exception.
This adapter boundary does not disable the installed planning commit hook.

The managed editing group remains advisory guard first, source decision second.
Python hook entries have a 120-second timeout, `source-prewrite.sh` has 30 seconds,
and other shared shell hooks have 10 seconds; Claude creation/removal retain their
180/60-second timeouts. User hooks and distinct dispatch/editing registrations
remain preserved when the workflow is installed or updated.

The destructive hook has a 120-second host timeout and an 80-second evidence
budget, with individual subprocess calls limited to 20 seconds. Missing or
failed Git/provider evidence refuses the recognized operation. The installed
launcher tests verify refusal status and JSON on Windows and allow behavior
from nested paths with spaces/non-ASCII characters. They establish launcher
execution, not a trusted live host session.

See [destructive operations](../references/destructive-operations.md) for the
literal command grammar, preservation policy and limits. This new hook is
separate from `worktree-guard.sh`, whose bytes and advisory behavior are unchanged.

Use `--no-hooks` to skip adding registrations; existing hooks are preserved.
Existing settings remain authoritative. Codex must trust the project and hooks
before running them. Installed files alone do not prove live host execution.
See [Codex hooks](https://learn.chatgpt.com/docs/hooks).

Bash and Git must be available. On Windows, the Codex launcher locates Git Bash
near the Git executable instead of using WSL's `bash.exe`; Claude uses Git Bash.
JSON extraction uses jq when available, then Python, with a limited text
fallback. The script supports file fields and Codex `apply_patch`
Add/Update/Delete/Move headers.

`ai-tier-notice.sh` is advisory: it exits successfully and never emits a
permission decision. `worktree-guard.sh` warns and exits 0 for both dispatch and
write checks. `source-prewrite.sh` is the separate blocking source decision; it
cancels the original call when required and never turns cancellation into native
movement. `context-handoff.sh` is advisory throughout: losing a handoff costs
a re-read, blocking the agent costs the session. These hooks do not parse
arbitrary scripts, resolve every symlink, validate runtime ownership or create
a sandbox. Repository
instructions and host permissions still govern the work.

Run the Bash suite and the installed-launcher test after hook changes:

```text
bash .ai/hooks/ai-tier-notice.test.sh
bash .ai/hooks/worktree-guard.test.sh
bash .ai/hooks/context-handoff.test.sh
bash .ai/hooks/worktree-location.test.sh
python -m unittest discover -s tests -p test_handoff.py -v
python -m unittest discover -s tests -p test_install.py -k registered_hooks -v
```

The tests exercise JSON and stdin behavior, host registrations, patch paths and
direct Bash launchers. They do not establish trusted live host execution.

## The handoff hook

`context-handoff.sh` is the one managed hook that measures rather than inspects.
It measures subagents only; it never tells the orchestrator to stop:

- **Claude Code:** a tool use without `agent_id` is the orchestrator. Skip it.
- **Codex:** a tool use whose `transcript_path` matches
  `.planning/handoffs/.root-<session>.json` is the orchestrator. Skip it. Any
  other transcript is a subagent: measure that transcript and key its record
  `<session>--agent-<transcript stem>`. `Stop` keeps the root record.
- **Neither recognised:** the advisory tells an orchestrator the limit does not
  apply to it.
It reads the session's own transcript -- `transcript_path` in the hook payload,
which both hosts supply -- and takes the latest token reading from it. The
advisory envelope is identical on both: `hookSpecificOutput.additionalContext`
on `PostToolUse` is accepted by Claude Code and by Codex, which treats it as
extra developer context, so one emitted shape satisfies both. Neither host shows
a hook's plain stdout to the model, which is why the advisory is JSON rather
than an echo. That is
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

  The hook can record only where the attempt stopped. The advisory therefore
  asks the agent, by the record's exact id, to add its digest with
  `handoff.write` — the files it read, the findings it established, what is done
  and what is left — from what is already in its context. A refresh starts from
  the previous record, so that digest survives every later tool use: git state
  is re-read, and an empty agent, plan, summary or occupancy never erases a known
  one. The digest is what the continuation ingests in place of re-reading the
  assignment; see
  [recording your digest](../references/worker-handoff.md#recording-your-digest).

  The agent measured is the one calling. Claude Code gives a hook fired inside
  a subagent the *parent's* `transcript_path`, with `agent_id` and `agent_type`
  beside it, so the hook reads the subagent's own transcript at
  `<parent without .jsonl>/subagents/agent-<id>.jsonl` (Codex's
  `agent_transcript_path` when present) and keys its record and debounce to
  `<session>--agent-<id>`. When that transcript cannot be found it stays silent
  rather than measuring the parent — which is how a researcher was once
  stopped for its orchestrator's occupancy.

  The advisory depends on what the role produces. A plan executor is told to
  write its SUMMARY with `status: blocked` and hand the rest on. An artifact
  role (researcher, phase-preparer, codebase-mapper) is told the limit is not a
  blocker and to converge: write its artifact from what it has and return it
  partial. A reviewer reports what it reached. A session with no agent identity
  gets guidance that holds for any of them.
- **A subagent stopping early** writes a record naming the plan and the SUMMARY
  to read first. Missing or `blocked` is unfinished; only `status: complete`
  clears without a handoff. An agent that already crossed the limit has a record
  carrying its digest, and its exit is folded into that record rather than a
  second one, so there is one handoff per stopped agent.

  The two hosts reach that event from opposite directions, so the hook resolves
  the agent's identity from whichever side actually carries it:

  | | Claude Code | Codex |
  |---|---|---|
  | How a subagent is dispatched | an `Agent`/`Task` tool call | `SubagentStart`, not a tool call |
  | Which role stopped | the active-agent stack `worktree-guard.sh` recorded at `PreToolUse` | `agent_type`, straight off the stop payload |
  | Which plan it had | the plan named in the dispatch prompt | the plan named in `agent_transcript_path` |

  Codex never produces a `PreToolUse` dispatch, so the active stack it would
  read is always empty — this branch used to exit immediately and Codex got no
  exit handoff at all. Its stop payload carries more than Claude's does, so
  nothing had to be recorded in advance: the role arrives in `agent_type`, and
  the assigned plan is recovered from the subagent's own transcript, matched
  after JSON decoding so an escaped Windows path resolves to a real file. An
  absolute path is cut back to its `.planning/` prefix, because the SUMMARY
  lookup joins against `cwd`. A transcript that names no plan still produces a
  handoff, unattributed: one the orchestrator must inspect beats none.

  Claude Code now sends `agent_type` and `agent_id` on its stop payload too, so
  it takes the same payload-first path, recovering the plan from the
  subagent's own transcript and dropping the closed dispatch from the active
  stack. The stack still attributes a stop whose transcript cannot be read.

  Which roles are write-capable, artifact or review lives in
  [lib/agent-roles.sh](lib/agent-roles.sh), because both hooks need the same
  answer and a list kept in two places is a hole in whichever copy was missed.
  The runtime's continuation brief keeps a Python copy of the artifact and
  review lists, held equal to this one by `tests/test_handoff.py`.

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

## Where worktrees are created

Every worktree lives under `worktree.root` from `.planning/config.yaml`
(default `.worktrees/`). Never under `.claude/worktrees/` or anywhere else.

- **Claude:** [worktree-location.sh](worktree-location.sh) handles
  `WorktreeCreate`. It runs
  `git worktree add -b worktree-<name> <primary>/<root>/<name> HEAD` from the
  dispatching checkout and prints the path as the last stdout line. On any
  failure it exits non-zero and the dispatch is refused. On `WorktreeRemove` it
  runs `git worktree remove <path>` without `--force` and keeps the branch.
  `.worktreeinclude` is not processed.
- **Codex:** create each plan's checkout with
  `phase_run query worktree.create <plan> --phase <N>`.

## Future hook work

These are planned improvements, not implemented or enabled hooks.

- **Pre-commit linting:** run the project's configured linter before a Git commit
  and block the commit when linting fails.
