<purpose>
Validate `.planning/` directory structure and report actionable findings without changing records. Structural health does not establish product readiness.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>
```bash
_ENGINEER_SHIM_NAME="engineer_run"; _ENGINEER_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; ENGINEER_TOOLS="${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}"; _engineer_at() { for _p; do if [ -f "$_p" ]; then ENGINEER_TOOLS="$_p"; return 0; fi; done; return 1; }; _engineer_id_ok() { case "$("$1" runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"engineer-runtime"'*'}') return 0;; *) return 1;; esac; }; _engineer_homes() { set -- "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" "${CODEX_HOME:-$HOME/.codex}"; for _h; do _engineer_at "$_h/engineer/bin/${_ENGINEER_SHIM_NAME}" && return 0; done; return 1; }; if _engineer_at "${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.claude/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.codex/engineer/bin/${_ENGINEER_SHIM_NAME}"; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif _engineer_homes; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif unset -f engineer_run; _G="$(command -v engineer_run)"; [ -n "$_G" ] && _engineer_id_ok "$_G"; then ENGINEER_TOOLS="$_G"; engineer_run() { "$ENGINEER_TOOLS" "$@"; }; else echo "ERROR: engineer_run not found at $ENGINEER_TOOLS and no identity-proving engineer_run is on PATH. Run: python -I bin/install.py --source <local-source> --ref <pinned-ref> --target <project-root> --host claude --local" >&2; exit 1; fi; ENGINEER_IDENTITY_STATUS=unverified; _engineer_id_ok engineer_run && ENGINEER_IDENTITY_STATUS=ok; export ENGINEER_IDENTITY_STATUS; [ "$ENGINEER_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$ENGINEER_TOOLS\" did not prove it is engineer-runtime - it is either a different package or an engineer-runtime older than the runtime-identity verb." >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${ENGINEER_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${ENGINEER_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(engineer_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

<step name="parse_args">
**Parse arguments:**

Check if `--context` is present in the command arguments. If `--repair` or
`--backfill` was requested, explain that `validate.health` rejects those flags
with `health-repair-requires-planning-review`; use the guarded planning review
route described below for any separately authorized repair. Do not pass either
flag, change planning records or clean host task directories in this workflow.

```
CONTEXT_MODE=""
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

The query returns JSON containing `message`, `state`, `utilization`, `tokensUsed`
and `contextWindow`. Display its `message`, then end the workflow - do **not** mix in `.planning/`
health output, the two modes are independent diagnostics.
</step>

<step name="run_health_check">
**Run health validation:**

```bash
engineer_run query validate.health
```

Parse JSON output:
- `status`: "healthy" | "degraded" | "broken"
- `errors[]`: Missing records (`code`, `path`) or configuration failures (`code`, `message`)
- `warnings[]`: Phase naming or unmatched SUMMARY findings (`code`, `path`)
- `info[]`: PLAN files without a matching SUMMARY (`code`, `path`, `meaning`)
- `counts`: Error, warning and information counts
- `structuralOnly`: `true`; no product behavior, acceptance or readiness is verified

Required records are `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`
and `config.yaml` under `.planning/`. Report `missing-record`, `phase-name`,
`orphan-summary`, `plan-without-summary` and any actual configuration failure
codes as returned; do not translate them to the legacy library codes below.

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

Use `counts` for the runtime totals and include any workflow-layer W025 warning
in the displayed total. Render each actual diagnostic's code, path or message;
do not invent `fix` or `repairable` fields.

**Example error:**
```
## Errors

- [missing-record] .planning/PROJECT.md
  Next: Locate the existing project record before proposing a repair.
```

**Example warning:**
```
## Warnings

- [orphan-summary] .planning/phases/01-setup/01-01-SUMMARY.md
  Next: Check the summary's provenance and plan filename before concluding work is missing.
```

**Example information:**
```
## Info

- [plan-without-summary] .planning/phases/02-implementation/02-01-PLAN.md
  Note: May be unexecuted or in progress.
```

Conclude with `Structural check only; no records changed.` Do not infer a
repair count, performed repairs or product readiness from this diagnostic.
</step>

<step name="repair_guidance">
Report findings without repairing them. For authorized follow-up, the existing
guarded route begins with a read-only review:

```bash
engineer_run query planning.review
```

Only the repairs actually proposed by that review are supported by
`planning.repair --apply --expect <snapshotDigest>`. Preserve identity,
acceptance and history; do not describe this as a general health auto-fix.
After a separately authorized repair, rerun `validate.health` and report its
actual remaining findings.
</step>

</process>

## Legacy diagnostic library reference

The generated tables below describe the retained `health_diagnostic` library,
not the current `validate.health` command. They are not an execution checklist
or available `/health` repair actions. Current output and the guarded follow-up
route are defined above; do not invoke `--repair` or `--backfill` from this appendix.

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
| W010 | warning | GSD agent installation missing or incomplete | No |
| W011 | warning | STATE.md current-phase status disagrees with ROADMAP.md checkbox | No |
| W012 | warning | config.json invalid branching_strategy value | No |
| W013 | warning | config.json context_window not a positive integer | No |
| W014 | warning | config.json phase_branch_template missing {phase} placeholder | No |
| W015 | warning | config.json milestone_branch_template missing {milestone} placeholder | No |
| W017 | warning | Orphan git worktree (path no longer exists on disk) | No |
| W018 | warning | MILESTONES.md missing entry for archived milestone snapshot | Yes (`--backfill`) |
| W019 | warning | Unrecognized .planning/ root file — not a canonical GSD artifact | No |
| W020 | warning | Worktree health scan degraded — git worktree list timed out, failed, or a finding could not be verified | No |
| W021 | warning | Phase's integer prefix implies a different milestone than its ROADMAP section (phase_id_convention: milestone-prefixed) | No |
| W022 | warning | config.json models entry malformed (unknown phase type, invalid tier, or non-object value) | No |
| W023 | warning | Phase directories collide on normalized key | No |
| W024 | warning | STATE.md was written many commits ago — treat its contents as approximate | No |
| W026 | warning | STATE says milestone complete but ROADMAP lists an unstarted phase for that milestone | No |
| W027 | warning | Stale git worktree (not modified in a long time) | No |
| W028 | warning | A GSD-owned install scope shadows another on this machine | No |
| W029 | warning | .planning/ matches a gitignore rule but is still tracked by git (gitignore has no effect on already-tracked files) | No |
| W030 | warning | Phase verification report status is outside the closed set | Yes (known legacy statuses only) |
| I001 | info | Plan without SUMMARY (may be in progress) | No |
| I010 | info | Resolved CWD reported alongside the E010 home-directory guard | No |

Note: this table is **generated** — do not hand-edit it. It is produced by `python -m engineer.bin.lib.gen_health_docs --write` from `engineer/bin/lib/health_diagnostic.py`'s `RULES` table (31 rules as of #3309, each carrying a static `description`/`repairable` on its `Rule` entry — see `engineer/bin/lib/health_diagnostic_rules.py`) plus the 3 pre-checks that stay outside the rule table by design (`E001`, `E010`, `I010` — safety rails in `cmdValidateHealth`, `engineer/bin/lib/workflow_ops.py`, never `.planning/` findings). `engineer/bin/lib/lint_health_diagnostic_rule_table.py` already enforces the 1:1 code invariant this table depends on (no duplicate codes; severity is always a `Rule` property, never set per emit call) — before assigning a new code, add a `Rule` entry under `engineer/bin/lib/health_diagnostic_rules.py` (its `code` is simply the next free number the lint guard has not yet seen) and run `python -m engineer.bin.lib.gen_health_docs --write` to regenerate this table; `python -m engineer.bin.lib.gen_health_docs --check` fails if it drifts. `W025` (the `workflow.use_worktrees`/`dispatch.isolation` check, #2486) is a workflow-layer diagnostic emitted directly by this file's own `run_health_check` step, not by `cmdValidateHealth` — it stays documented in that step, not in this generated table.

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
