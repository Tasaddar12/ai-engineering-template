@~/.claude/engineer/references/response-language-directive.md

<purpose>
Autonomous audit-to-fix pipeline. Runs an audit, parses findings, classifies each as
auto-fixable vs manual-only, spawns executor agents for fixable issues, runs tests
after each fix, and commits atomically with finding IDs for traceability.
</purpose>

<available_agent_types>
- executor — executes a specific, scoped code change
</available_agent_types>

<process>

<step name="parse-arguments">
Extract flags from the user's invocation:

- `--max N` — maximum findings to fix (default: **5**)
- `--severity high|medium|all` — minimum severity to process (default: **medium**)
- `--dry-run` — classify findings without fixing (shows classification table only)
- `--source <audit>` — which audit to run (default: **audit-uat**)

Validate `--source` is a supported audit. Currently supported:
- `audit-uat`

If `--source` is not supported, stop with an error:
```
Error: Unsupported audit source "{source}". Supported sources: audit-uat
```
</step>

<step name="run-audit">
Invoke the source audit command and capture output.

For `audit-uat` source:
```bash
_engineer_identity_ok() {
  [ -f "$1" ] || return 1
  [ "$(sh "$1" query runtime-identity --pick packageName --raw 2>/dev/null)" = "engineer-runtime" ]
}
_engineer_select() {
  for _engineer_candidate do
    if _engineer_identity_ok "$_engineer_candidate"; then
      ENGINEER_RUN="$_engineer_candidate"
      return 0
    fi
  done
  return 1
}
if [ -n "${ENGINEER_RUN:-}" ]; then
  _engineer_identity_ok "$ENGINEER_RUN" || {
    printf '%s\n' "ERROR: ENGINEER_RUN does not identify engineer-runtime: $ENGINEER_RUN" >&2
    exit 1
  }
else
  _engineer_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  _engineer_runtime_root=${RUNTIME_DIR:-$_engineer_root}
  _engineer_path_candidate=$(command -v engineer_run 2>/dev/null || true)
  _engineer_select \
    "$_engineer_root/engineer/bin/engineer_run" \
    "$_engineer_runtime_root/engineer/bin/engineer_run" \
    "$_engineer_root/.claude/engineer/bin/engineer_run" \
    "$_engineer_root/.codex/engineer/bin/engineer_run" \
    "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/engineer/bin/engineer_run" \
    "${CODEX_HOME:-$HOME/.codex}/engineer/bin/engineer_run" \
    "$_engineer_path_candidate" || {
    printf '%s\n' 'ERROR: No engineer-runtime launcher was found. Install the Claude or Codex workflow runtime or set ENGINEER_RUN.' >&2
    exit 1
  }
fi
export ENGINEER_RUN
engineer_run() {
  sh "$ENGINEER_RUN" "$@"
}
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  _engineer_path_escaped=$(printf '%s' "${ENGINEER_RUN%/*}" | sed 's/[\\`"$]/\\&/g')
  printf 'export PATH="%s:$PATH"\n' "$_engineer_path_escaped" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
fi
INIT=$(engineer_run query audit-uat 2>/dev/null || echo "{}")
```

Read existing UAT and verification files to extract findings:
- Glob: `.planning/phases/*/*-UAT.md`
- Glob: `.planning/phases/*/*-VERIFICATION.md`

Parse each finding into a structured record:
- **ID** — sequential identifier (F-01, F-02,...)
- **description** — concise summary of the issue
- **severity** — high, medium, or low
- **file_refs** — specific file paths referenced in the finding
</step>

<step name="classify-findings">
For each finding, classify as one of:

- **auto-fixable** — clear code change, specific file referenced, testable fix
- **manual-only** — requires design decisions, ambiguous scope, architectural changes, user input needed
- **skip** — severity below the `--severity` threshold

**Classification heuristics** (err on manual-only when uncertain):

Auto-fixable signals:
- References a specific file path + line number
- Describes a missing test or assertion
- Missing export, wrong import path, typo in identifier
- Clear single-file change with obvious expected behavior

Manual-only signals:
- Uses words like "consider", "evaluate", "design", "rethink"
- Requires new architecture or API changes
- Ambiguous scope or multiple valid approaches
- Requires user input or design decisions
- Cross-cutting concerns affecting multiple subsystems
- Performance or scalability issues without clear fix

**When uncertain, always classify as manual-only.**
</step>

<step name="present-classification">
Display the classification table:

```
## Audit-Fix Classification

| # | Finding | Severity | Classification | Reason |
|---|---------|----------|---------------|--------|
| F-01 | Missing export in index.ts | high | auto-fixable | Specific file, clear fix |
| F-02 | No error handling in payment flow | high | manual-only | Requires design decisions |
| F-03 | Test stub with 0 assertions | medium | auto-fixable | Clear test gap |
```

If `--dry-run` was specified, **stop here and exit**. The classification table is the
final output — do not proceed to fixing.
</step>

<step name="fix-loop">
For each **auto-fixable** finding (up to `--max`, ordered by severity desc):

```bash
EXECUTOR_MODEL=$(engineer_run query resolve-model executor --raw)
```

<!-- model-omit-on-inherit -->

> **Model omission.** Omit the `model` parameter entirely when the value it would carry (`EXECUTOR_MODEL`) is `"inherit"` or empty. An empty value 404s on runtimes without native tier aliases — the default on non-Claude runtimes. Omitting it inherits the orchestrator's model.

**a. Spawn executor agent** (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze):
```
Agent(
  prompt="Fix finding {ID}: {description}. Files: {file_refs}. Make the minimal change to resolve this specific finding. Do not refactor surrounding code.",
  subagent_type="executor",
  model="{EXECUTOR_MODEL}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

**b. Run tests:**
```bash
AUDIT_CHECKS=$(engineer_run query verification.run-checks) && AUDIT_TEST_EXIT=0 || AUDIT_TEST_EXIT=$?
# Inspect configured-check receipts; absent checks are missing evidence, never an inferred pass.
```

**c. If tests pass** — commit atomically:
```bash
git add {changed_files}
git commit -m "fix({scope}): resolve {ID} — {description}"
```
The commit message **must** include the finding ID (e.g., F-01) for traceability.

**d. If tests fail** — revert changes, mark finding as `fix-failed`, and **stop the pipeline**:
```bash
git checkout -- {changed_files} 2>/dev/null
```
Log the failure reason and stop processing — do not continue to the next finding.
A test failure indicates the codebase may be in an unexpected state, so the pipeline
must halt to avoid cascading issues. Remaining auto-fixable findings will appear in the
report as `not-attempted`.
</step>

<step name="report">
Present the final summary:

```
## Audit-Fix Complete

**Source:** {audit_command}
**Findings:** {total} total, {auto} auto-fixable, {manual} manual-only
**Fixed:** {fixed_count}/{auto} auto-fixable findings
**Failed:** {failed_count} (reverted)

| # | Finding | Status | Commit |
|---|---------|--------|--------|
| F-01 | Missing export | Fixed | abc1234 |
| F-03 | Test stub | Fix failed | (reverted) |

### Manual-only findings (require developer attention):
- F-02: No error handling in payment flow — requires design decisions
```
</step>

</process>

<success_criteria>
- Auto-fixable findings processed sequentially until --max reached or a test failure stops the pipeline
- Tests pass after each committed fix (no broken commits)
- Failed fixes are reverted cleanly (no partial changes left)
- Pipeline stops after the first test failure (no cascading fixes)
- Every commit message contains the finding ID
- Manual-only findings are surfaced for developer attention
- --dry-run produces a useful standalone classification table
</success_criteria>
