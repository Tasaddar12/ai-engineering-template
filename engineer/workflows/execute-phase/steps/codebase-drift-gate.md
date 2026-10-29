Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# Step: codebase_drift_gate

Post-execution structural drift detection. Runs after the last wave
commits, before verification. **Non-blocking by contract:** any internal
error here MUST fall through and continue to `verify_phase_goal`. The phase
is never failed by this gate.

```bash
_ENGINEER_SHIM_NAME="engineer_run"; _ENGINEER_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; ENGINEER_TOOLS="${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}"; _engineer_at() { for _p; do if [ -f "$_p" ]; then ENGINEER_TOOLS="$_p"; return 0; fi; done; return 1; }; _engineer_id_ok() { case "$("$1" runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"engineer-runtime"'*'}') return 0;; *) return 1;; esac; }; _engineer_homes() { set -- "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" "${CODEX_HOME:-$HOME/.codex}"; for _h; do _engineer_at "$_h/engineer/bin/${_ENGINEER_SHIM_NAME}" && return 0; done; return 1; }; if _engineer_at "${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.claude/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.codex/engineer/bin/${_ENGINEER_SHIM_NAME}"; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif _engineer_homes; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif unset -f engineer_run; _G="$(command -v engineer_run)"; [ -n "$_G" ] && _engineer_id_ok "$_G"; then ENGINEER_TOOLS="$_G"; engineer_run() { "$ENGINEER_TOOLS" "$@"; }; else echo "ERROR: engineer_run not found at $ENGINEER_TOOLS and no identity-proving engineer_run is on PATH. Run: python -I bin/install.py --source <local-source> --ref <pinned-ref> --target <project-root> --host claude --local" >&2; exit 1; fi; ENGINEER_IDENTITY_STATUS=unverified; _engineer_id_ok engineer_run && ENGINEER_IDENTITY_STATUS=ok; export ENGINEER_IDENTITY_STATUS; [ "$ENGINEER_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$ENGINEER_TOOLS\" did not prove it is engineer-runtime - it is either a different package or an engineer-runtime older than the runtime-identity verb." >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${ENGINEER_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${ENGINEER_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
# Resolve engineer_run through the runtime shim launcher, NOT the bare PATH binary. On a
# shim-only install (engineer_run present, `engineer_run` not on PATH) the bare call exits
# 127, `2>/dev/null` hides it, and this non-blocking gate would silently skip drift
# detection forever. The canonical launcher preamble is defined once here — the
# always-run drift check, the file's first launcher block — and the conditional auto-remap
# block below reuses the launcher function from this shared shell scope (the single-preamble
# pattern established by discuss-phase, enforced by tests/runtime-launcher-parity.test.cjs).
# Non-blocking is preserved: an internal drift-command failure still falls through to the
# skip JSON below. Exit 69 (UNAVAILABLE, ) is the verb saying "could not look": its payload is
# already on stdout and is kept as the verdict; the fallback is applied only when the verb printed
# nothing, so the two JSON documents are never concatenated.
DRIFT=$(engineer_run verify codebase-drift 2>/dev/null) && DRIFT_EXIT=0 || DRIFT_EXIT=$?
if [ -z "$DRIFT" ]; then DRIFT='{"skipped":true,"reason":"sdk-failed"}'; fi
if [ "$DRIFT_EXIT" -ne 0 ]; then echo "Warning: codebase-drift check could not look (exit ${DRIFT_EXIT})" >&2; fi
```

Parse JSON for: `skipped`, `reason`, `action_required`, `directive`,
`spawn_mapper`, `affected_paths`, `elements`, `threshold`, `action`,
`last_mapped_commit`, `message`.

**If `skipped` is true (no STRUCTURE.md, missing git, or any internal error):**
Log one line — `Codebase drift check skipped: {reason}` — and continue to
`verify_phase_goal`. Do NOT prompt the user. Do NOT block.

**If `action_required` is false:** Continue silently to `verify_phase_goal`.

**If `action_required` is true AND `directive` is `warn`:**
Print the `message` field verbatim. The format is:

```text
Codebase drift detected: {N} structural element(s) since last mapping.

New directories:
  - {path}
New barrel exports:
  - {path}
New migrations:
  - {path}
New route modules:
  - {path}
Modified files in mapped directories:
  - {path}
Deleted files in mapped directories:
  - {path}
{N} path(s) withheld: not passed to the mapper or listed (absolute, traversal, whitespace, non-ASCII or shell-metacharacter characters)

Run /map-codebase --paths {affected_paths} to refresh planning context.
```

Then continue to `verify_phase_goal`. Do NOT block. Do NOT spawn anything.

**If `action_required` is true AND `directive` is `auto-remap`:**

First load the mapper agent's skill bundle (the executor's `AGENT_SKILLS`
from step `init_context` is for `executor`, not the mapper):

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
# engineer_run is defined by the canonical preamble in the drift-check block above and reused
# here via the workflow's shared shell scope — defining it once keeps the file compliant
# with the single-canonical-preamble parity invariant. This block only runs on the
# `auto-remap` directive, which is always reached after the drift check above has run.
# This file is Read, not textually substituted - write the parent command's original argument string in place of $ARGUMENTS so --ws reaches the query.
ENGINEER_WS=$(echo " $ENGINEER_ARGS" | sed -nE 's/.* --ws +([A-Za-z0-9][A-Za-z0-9._-]*).*/--ws \1/p' | head -n 1)
AGENT_SKILLS_MAPPER=$(engineer_run query agent-skills codebase-mapper ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }})
```

Then spawn `codebase-mapper` agents with the `--paths` hint (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze):

```text
Agent(
  subagent_type="codebase-mapper",
  description="Incremental codebase remap (drift)",
  prompt="Focus: arch
Today's date: {date}
--paths {affected_paths joined by comma}

Refresh STRUCTURE.md and ARCHITECTURE.md scoped to the listed paths only.
${AGENT_SKILLS_MAPPER}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

If the spawn fails or the agent reports an error: log `Codebase drift
auto-remap failed: {reason}` and continue to `verify_phase_goal`. The phase
is NOT failed by a remap failure.

If the remap succeeds, stamp the new baseline into the two documents the
mapper just refreshed:

```bash
engineer_run stamp-codebase-map --files STRUCTURE.md,ARCHITECTURE.md
```

The stamp is a shell step, not a line in the mapper's prompt. An agent that
concludes its work is already done skips a prose instruction silently, and the
stamp is the one marker no human reviewing the documents would notice missing
. `--files` is scoped to what this step actually refreshed -- the other
five documents were not remapped and must not claim currency at HEAD.

Only stamp on success: stamping after a failed remap would record a baseline
the map never reached.

Then log `Codebase drift auto-remap completed for paths: {affected_paths}` and
continue to `verify_phase_goal`.

The two relevant config keys (continue on error / failure if either is invalid):
- `workflow.drift_threshold` (integer, default 3) — minimum drift elements before action
- `workflow.drift_action` — `warn` (default) or `auto-remap`

This step is fully non-blocking — it never fails the phase, and any
exception path returns control to `verify_phase_goal`.
