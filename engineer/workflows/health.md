<purpose>
Validate `.planning/` directory integrity and report actionable issues. The current runtime checks required planning records, loads `.planning/config.yaml`, and checks phase names and plan/summary pairing. It reports structural findings without rewriting records.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

**Runtime behavior:** `validate.health` reads the canonical YAML config through `config.load`. Malformed YAML or unsupported values return the runtime failure code and message. A missing config is first collected as a `missing-record`, but the handler then calls `config.load()` without catching its `FileNotFoundError`, so the command can abort before returning that JSON. The current command is structural-only: `--repair` and `--backfill` are refused with `health-repair-requires-planning-review` and make no changes. The diagnostic-code and repair-action tables below describe retained `health_diagnostic.py` metadata, which still models upstream JSON `config.json` behavior; those codes and actions are not the response format of current `validate.health`.

```bash
_ENGINEER_SHIM_NAME="engineer_run"; _ENGINEER_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; ENGINEER_TOOLS="${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}"; _engineer_at() { for _p; do if [ -f "$_p" ]; then ENGINEER_TOOLS="$_p"; return 0; fi; done; return 1; }; _engineer_id_ok() { case "$("$1" runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"engineer-runtime"'*'}') return 0;; *) return 1;; esac; }; _engineer_homes() { set -- "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" "${CODEX_HOME:-$HOME/.codex}"; for _h; do _engineer_at "$_h/engineer/bin/${_ENGINEER_SHIM_NAME}" && return 0; done; return 1; }; if _engineer_at "${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.claude/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.codex/engineer/bin/${_ENGINEER_SHIM_NAME}"; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif _engineer_homes; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif unset -f engineer_run; _G="$(command -v engineer_run)"; [ -n "$_G" ] && _engineer_id_ok "$_G"; then ENGINEER_TOOLS="$_G"; engineer_run() { "$ENGINEER_TOOLS" "$@"; }; else echo "ERROR: engineer_run not found at $ENGINEER_TOOLS and no identity-proving engineer_run is on PATH. Run: python -I bin/install.py --source <local-source> --ref <pinned-ref> --target <project-root> --host claude --local" >&2; exit 1; fi; ENGINEER_IDENTITY_STATUS=unverified; _engineer_id_ok engineer_run && ENGINEER_IDENTITY_STATUS=ok; export ENGINEER_IDENTITY_STATUS; [ "$ENGINEER_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$ENGINEER_TOOLS\" did not prove it is engineer-runtime - it is either a different package or an engineer-runtime older than the runtime-identity verb." >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${ENGINEER_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${ENGINEER_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(engineer_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

<step name="parse_args">
**Parse arguments:**

Check if `--repair`, `--backfill`, or `--context` flags are present in the command arguments.

```
REPAIR_FLAG=""
BACKFILL_FLAG=""
CONTEXT_MODE=""
if arguments contain "--repair"; then
  REPAIR_FLAG="--repair"
fi
if arguments contain "--backfill"; then
  BACKFILL_FLAG="--backfill"
fi
if arguments contain "--context"; then
  CONTEXT_MODE="true"
fi
```

If `CONTEXT_MODE` is set, jump to the `context_check` step and skip the
integrity validation steps. The two modes are orthogonal — context utilization
has nothing to do with `.planning/` directory health.
</step>

<step name="context_check">
**Run only when `--context` is set.**

The model running this workflow self-reports the current session's
approximate `tokensUsed` and the active model's `contextWindow`. Use the values
visible in your runtime (Claude Code's `/context` slash command output, or the
model's own session telemetry). If the runtime exposes neither, prompt the user
once via AskUserQuestion for both numbers.

**TEXT_MODE fallback:** when `text_mode` is true (config or `--text` flag) the
runtime is non-Claude (Codex) and `AskUserQuestion` is not
available — replace the prompt with a plain-text two-question sequence
("Approximate tokens used? Context window size?") and read the answers as
plain text from the user's response.

```bash
engineer_run query validate.context \
  --tokens-used "$TOKENS_USED" \
  --context-window "$CONTEXT_WINDOW"
```

The query prints a one-line status (`Context utilization: NN% (state)`) plus
a recommendation line for the warning and critical states. Print the SDK
output verbatim and end the workflow — do **not** mix in `.planning/`
health output, the two modes are independent diagnostics.
</step>

<step name="run_health_check">
**Run health validation:**

```bash
engineer_run query validate.health $REPAIR_FLAG $BACKFILL_FLAG
```

Parse JSON output:
- `status`: "healthy" | "degraded" | "broken"
- `errors[]`: Missing required records or caught config load failures (`code` with `path` or `message`); missing config can abort before a report is returned
- `warnings[]`: Phase naming mismatches or orphan summaries
- `info[]`: Plans without summaries
- `counts`: Error, warning, and info totals
- `structuralOnly`: `true`

If `--repair` or `--backfill` was supplied, the runtime rejects the request with `health-repair-requires-planning-review`. Display that failure and stop; do not parse it as a health report or offer an automatic repair.

**Isolation compatibility check:** use the read-only inspection verb to report whether either supported worktree mode is available. Unknown or missing capability blocks write-capable dispatch; there is no opt-out.

```bash
_INSPECTED_RAW=$(engineer_run query inspect-dispatch-isolation --raw 2>/dev/null)
_ISOLATION_RC=$?
if [ $_ISOLATION_RC -ne 0 ] || [ -z "$_INSPECTED_RAW" ]; then
  INSPECTED_ISOLATION=none
  INSPECTED_RESOLVED=false      # no verdict learned — not the same as "declares none"
else
  INSPECTED_ISOLATION="$_INSPECTED_RAW"
  INSPECTED_RESOLVED=true
fi
case "$INSPECTED_ISOLATION" in
  harness-worktree|orchestrator-worktree|none) ;;
  *) INSPECTED_ISOLATION=none; INSPECTED_RESOLVED=false ;;   # out of vocabulary is not a verdict either
esac

if [ "$INSPECTED_ISOLATION" = "none" ]; then
  if [ "$INSPECTED_RESOLVED" = "true" ]; then
    echo "W025: mandatory worktree isolation is unavailable; repair runtime isolation before dispatching write-capable workers."
  else
    echo "W025: mandatory worktree isolation is unavailable; repair runtime isolation before dispatching write-capable workers."
  fi
fi
```

If the check prints, append it to the Warnings section of the report as `[W025]` with the printed fix, include it in the displayed warning count, and report `Status: DEGRADED` if `validate.health` returned `healthy` (a config the execution workflows fail closed on is not a healthy planning state). It is not auto-repairable: report the unavailable isolation primitive and preserve the existing installation until its runtime configuration is repaired.
</step>

<step name="format_output">
**Format and display results:**

```
### Engineer Health Check

Status: HEALTHY | DEGRADED | BROKEN
Errors: N | Warnings: N | Info: N
```

**If errors exist:**
```
## Errors

- [missing-record] .planning/PROJECT.md is missing
  Fix: Create the project through `/new-project`.

- [invalid-yaml] <runtime message>
  Fix: Correct `.planning/config.yaml` and rerun `/health`.
```

**If warnings exist:** report the phase directory or orphan summary path returned by the runtime. **If info exists:** report the plan path without its SUMMARY.md; it may be unexecuted or in progress.

Do not report automatic repairs: the current `validate.health` command is structural-only and refuses `--repair`/`--backfill` without changing files.
</step>

</process>

<error_codes>
| Code | Severity | Description | Repairable |
|------|----------|-------------|------------|
| E001 | error | .planning/ directory not found | No |
| E002 | error | PROJECT.md not found | No |
| E003 | error | ROADMAP.md not found | No |
| E004 | error | STATE.md not found | No |
| E005 | error | config.json parse error | No |
| E010 | error | CWD resolves to the user's home directory — health check would target the wrong .planning/ | No |
| W001 | warning | PROJECT.md missing required section | No |
| W002 | warning | STATE.md references invalid phase | No |
| W003 | warning | config.json not found | Yes |
| W004 | warning | config.json invalid field value | No |
| W005 | warning | Phase directory naming mismatch | No |
| W006 | warning | Phase in ROADMAP but no directory | No |
| W007 | warning | Phase on disk but not in ROADMAP | No |
| W008 | warning | config.json: workflow.nyquist_validation absent (defaults to enabled but agents may skip) | Yes |
| W009 | warning | Phase has Validation Architecture in RESEARCH.md but no VALIDATION.md | No |
| W010 | warning | Engineer agent installation missing or incomplete | No |
| W011 | warning | STATE.md current-phase status disagrees with ROADMAP.md checkbox | No |
| W012 | warning | config.json invalid branching_strategy value | No |
| W013 | warning | config.json context_window not a positive integer | No |
| W014 | warning | config.json phase_branch_template missing {phase} placeholder | No |
| W015 | warning | config.json milestone_branch_template missing {milestone} placeholder | No |
| W017 | warning | Orphan git worktree (path no longer exists on disk) | No |
| W018 | warning | MILESTONES.md missing entry for archived milestone snapshot | Yes (`--backfill`) |
| W019 | warning | Unrecognized .planning/ root file — not a canonical Engineer artifact | No |
| W020 | warning | Worktree health scan degraded — git worktree list timed out, failed, or a finding could not be verified | No |
| W021 | warning | Phase's integer prefix implies a different milestone than its ROADMAP section (phase_id_convention: milestone-prefixed) | No |
| W022 | warning | config.json models entry malformed (unknown phase type, invalid tier, or non-object value) | No |
| W023 | warning | Phase directories collide on normalized key | No |
| W024 | warning | STATE.md was written many commits ago — treat its contents as approximate | No |
| W026 | warning | STATE says milestone complete but ROADMAP lists an unstarted phase for that milestone | No |
| W027 | warning | Stale git worktree (not modified in a long time) | No |
| W028 | warning | A Engineer-owned install scope shadows another on this machine | No |
| W029 | warning | .planning/ matches a gitignore rule but is still tracked by git (gitignore has no effect on already-tracked files) | No |
| W030 | warning | Phase verification report status is outside the closed set | Yes (known legacy statuses only) |
| I001 | info | Plan without SUMMARY (may be in progress) | No |
| I010 | info | Resolved CWD reported alongside the E010 home-directory guard | No |

This table describes retained upstream Python health metadata: 36 diagnostic codes and 6 repair actions. Its JSON config diagnostics are not emitted by the current structural-only `validate.health` command. `engineer/bin/lib/health_diagnostic_rules.py` owns the diagnostic catalog. Keep the tables synchronized with that metadata when changing a code or repair action. W025 is the workflow-layer mandatory-isolation diagnostic above.

</error_codes>

<repair_actions>
| Action | Effect | Risk |
|--------|--------|------|
| createConfig | Create config.json with defaults | None |
| resetConfig | Delete + recreate config.json | Loses custom settings |
| regenerateState | Create STATE.md from ROADMAP structure when it is missing | Loses session history |
| addNyquistKey | Add workflow.nyquist_validation: true to config.json | None — matches existing default |
| backfillMilestones | Synthesize missing MILESTONES.md entries from `.planning/milestones/vX.Y-ROADMAP.md` snapshots | None — additive only; triggered by `--backfill` flag |
| repairVerificationStatus | Rewrite a known legacy verification `status` (`pass_with_caveats`) to `passed`, keeping the original as `legacy_status` | None — only the `status` line changes; unknown statuses are never touched |

**Not repairable (too risky):**
- PROJECT.md, ROADMAP.md content
- Phase directory renaming
- Orphaned plan cleanup

</repair_actions>

<stale_task_cleanup>
**Windows-specific:** Check for stale Claude Code task directories that accumulate on crash/freeze.
These are left behind when subagents are force-killed and consume disk space.

When `--repair` is active, detect and clean up:

```bash
# Check for stale task directories (older than 24 hours)
TASKS_DIR="$HOME/.claude/tasks"
if [ -d "$TASKS_DIR" ]; then
  STALE_COUNT=$( (find "$TASKS_DIR" -maxdepth 1 -type d -mtime +1 2>/dev/null || true) | wc -l )
  if [ "$STALE_COUNT" -gt 0 ]; then
    echo "⚠️  Found $STALE_COUNT stale task directories in ~/.claude/tasks/"
    echo "   These are leftover from crashed subagent sessions."
    echo "   Run: rm -rf ~/.claude/tasks/*  (safe — only affects dead sessions)"
  fi
fi
```

Report as info diagnostic: `I002 | info | Stale subagent task directories found | Yes (--repair removes them)`
</stale_task_cleanup>
