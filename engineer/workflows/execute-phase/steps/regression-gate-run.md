Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# Step: regression_gate_run

Run the resolved prior-phase test command one-shot, bounded by a timeout, so a
watch-mode runner (vitest defaults to watch in a TTY; jest `--watch`) cannot
hang this gate forever. Uses the shared `normalize-test-command` helper
— the same one the post-merge gate uses — so the two gate paths cannot drift.

Reads the prior step's test-file list from the handoff file `regression-files`; a shell variable
cannot carry it, because each fenced `bash` block runs as its own shell.

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
# engineer-handoff:begin regression-files-read
_ENGINEER_HANDOFF="$( { git rev-parse --absolute-git-dir 2>/dev/null || echo "${TMPDIR:-/tmp}/engineer-$(pwd | cksum | cut -d' ' -f1)"; } )/handoff"; mkdir -p "$_ENGINEER_HANDOFF"
REGRESSION_FILES=""
if [ -s "$_ENGINEER_HANDOFF/regression-files" ]; then
  while IFS= read -r _f; do
    if [ -n "$_f" ]; then REGRESSION_FILES="${REGRESSION_FILES}$(printf '%q ' "$_f")"; fi
  done < "$_ENGINEER_HANDOFF/regression-files"
fi
# engineer-handoff:end regression-files-read
# Resolve test command: project config > Makefile > language sniff
REG_TEST_CMD=$(engineer_run query config-get workflow.test_command --default "" --raw 2>/dev/null || true)
if [ -z "$REG_TEST_CMD" ]; then
  if [ -f "Makefile" ] && grep -q "^test:" Makefile; then
    REG_TEST_CMD="make test"
  elif [ -f "Justfile" ] || [ -f "justfile" ]; then
    REG_TEST_CMD="just test"
  elif [ -f "package.json" ]; then
    REG_TEST_CMD=$(engineer_run query resolve-package-manager test --cwd . 2>/dev/null || echo "npm test")
    [ -n "$REG_TEST_CMD" ] || REG_TEST_CMD="npm test"
  elif [ -f "Cargo.toml" ]; then
    REG_TEST_CMD="cargo test"
  elif [ -f "go.mod" ]; then
    REG_TEST_CMD="go test ./..."
  elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    # engineer-handoff:begin regression-pytest-arm
    if [ -n "$REGRESSION_FILES" ]; then
      REG_TEST_CMD="python -m pytest -q --tb=short -- ${REGRESSION_FILES}"
    else
      echo "⚠ Regression gate: no prior-phase test files were collected — skipping the scoped pytest run instead of falling back to the full suite."
      REG_TEST_CMD="true"
    fi
    # engineer-handoff:end regression-pytest-arm
  else
    REG_TEST_CMD="true"
  fi
fi
# Normalize to a one-shot form (defeat vitest/jest watch mode) and bound
# with a timeout so a watch-mode runner cannot hang the gate indefinitely.
REG_TEST_CMD=$(engineer_run query normalize-test-command "$REG_TEST_CMD" --cwd . 2>/dev/null || echo "$REG_TEST_CMD")
TEST_GATE_TIMEOUT=$(engineer_run query config-get workflow.test_gate_timeout --raw 2>/dev/null || echo "600")
engineer_run query run-with-timeout "$TEST_GATE_TIMEOUT" -- bash -c "$REG_TEST_CMD" 2>&1
REG_TEST_EXIT=$?
if [ "$REG_TEST_EXIT" -eq 124 ]; then
  echo "✗ REGRESSION GATE ABORTED — test runner did not exit within ${TEST_GATE_TIMEOUT}s, likely stuck in watch/dev mode (e.g. vitest without 'run'). Run tests one-shot (e.g. 'vitest run'), set workflow.test_command, or raise workflow.test_gate_timeout."
fi
```

**On `REG_TEST_EXIT` 124 (`REGRESSION GATE ABORTED`):** HALT — do not proceed to verification. The runner did not exit within the budget (watch/dev mode is the likely cause). Surface the watch-mode cause and the recovery options; never silently continue.
