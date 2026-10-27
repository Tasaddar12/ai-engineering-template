# TDD-applicability resolution (#4266/#4272)

Run for each plan, immediately after executor routing and before composing
that plan's `Agent()` prompt in step 3. Resolves whether this dispatch is TDD
— fail closed, do not guess.

## Resolution

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
TDD_APPLICABLE_RAW=$(engineer_run query phase.tdd-applicable "{phase_dir}/{plan_file}" --pick applicable)
TDD_APPLICABLE_RC=$?
if [ $TDD_APPLICABLE_RC -ne 0 ]; then
  echo "FATAL: could not resolve TDD-applicability for plan {plan_number} — 'engineer_run query phase.tdd-applicable' failed. Refusing to guess whether this dispatch needs the TDD procedure. Halting." >&2
  exit 1
fi
TDD_APPLICABLE="$TDD_APPLICABLE_RAW"
```

## Pre-dispatch check (MANDATORY)

Before calling Agent(), confirm every `${...}` conditional in the prompt below
(`handoff`, `context_window`, `ISOLATION`, `TDD_APPLICABLE`) was resolved to concrete
text for THIS plan. If any marker's value was not computed, HALT — do not
dispatch a prompt containing literal `${...}` template syntax (#4266).

## Concrete resolution and evidence contract

Require TDD_APPLICABLE to be literal true or false; empty/malformed output halts dispatch. Read the full result `{applicable,plan_tdd,enabled}` when needed to explain the outcome. `phase.tdd-applicable PLAN_PATH` selects type:tdd or task TDD markers AND the actual workflow.tdd_mode policy; a test-generation label alone does not claim RED. Pass the concrete resolved value and full TDD method into this plan's isolated executor assignment. An explicitly requested TDD outcome cannot be silently downgraded by conflicting configuration; reconcile that conflict before writing dependent implementation.

A genuine TDD task commits the failing behavioral test before implementation. Execute the exact focused test argv at that RED source state, retain full runner output, exit code and target identity, and write a real JSON evidence record under an assigned path:

```json
{
  "command": ["python", "-m", "unittest", "tests.test_price.PriceTests.test_threshold"],
  "exitCode": 1,
  "output": "<actual complete runner report; never this placeholder>",
  "targetTest": "tests.test_price.PriceTests.test_threshold",
  "targetFile": "tests/test_price.py",
  "expected": "<required observable value>",
  "actual": "<observed incorrect value>",
  "testCommit": "<full RED test commit SHA>",
  "implementationCommit": "<full later GREEN implementation commit SHA>"
}
```

Before implementing, validate the report evidence with `engineer_run query check.tdd-red-evidence RECORD.json`; require exit 0 and `RED_EVIDENCE_OK`. The pre-implementation record has neither ancestry field yet (do not invent a future SHA). Commit RED, implement the bounded behavior, run the exact tests for genuine GREEN, then add BOTH testCommit and implementationCommit and run the same check again. Require strict RED ancestor of GREEN and targetFile present in the RED commit. The worker and independent verifier inspect that the recorded RED run actually used that commit and unchanged target assertions, not just an ancestral arbitrary commit. No squashed same-commit RED/GREEN claim qualifies.

Supported reports are complete TAP, Python unittest, JUnit XML, Go test and Swift Testing. Preserve exact emitted target IDs: TAP named leaf or qualified subtest, unittest qualified class.method, JUnit unambiguous name/class#name, Go package.TestName, Swift emitted display/function name. Complete counters/plan and one unambiguous target assertion failure are required. JUnit also records actual reportPath, runStartedAt and reportModifiedAt, proving the report belongs to this run. A stale XML file never supplies RED.

A nonzero process exit alone is not RED. Reject zero discovered tests, missing/ambiguous targets, compile/build/load errors, fixture/setup/import/syntax failures, unsupported/malformed/truncated reports, cancellations, skipped/TODO tests, and stale reports. Diagnose the infrastructure first; do not change expected behavior or implement against a test that never ran. Classifier exits 1 for rejected evidence and 69 for unreadable records; neither can be treated as valid RED.

Existing passing behavior with added characterization tests is reported as such; do not manufacture RED or claim TDD ancestry. If the user defers tests/checks, author only authorized source and evidence placeholders clearly marked pending, execute no runner/classifier check, do not fabricate output/receipts or claim the TDD gate passed. A required RED-first task waits at that dependency before GREEN implementation unless the actual user explicitly changes that requirement. Report pending work to the coordinator in SUMMARY Remaining.
