# Step: post_merge_gate

Post-merge build & test gate. Runs after all worktrees in a wave are merged
(parallel mode), or after the last plan completes (serial mode). Catches
cross-plan integration failures that individual worktree self-checks cannot
detect.

**Step A — Build gate:**

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
# Resolve build command: project config > Xcode > Makefile > language sniff
BUILD_CMD=$(engineer_run query config-get workflow.build_command --default "" --raw 2>/dev/null || true)
if [ -z "$BUILD_CMD" ]; then
  XCODEPROJ=$(find . -maxdepth 2 -name "*.xcodeproj" -not -path "*/node_modules/*" 2>/dev/null | head -1)
  if [ -n "$XCODEPROJ" ]; then
    # Xcode project: get first scheme from xcodebuild -list -json
    XCODE_SCHEME=$(xcodebuild -list -json -project "$XCODEPROJ" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('project',{}).get('schemes',[None])[0] or '')" 2>/dev/null || true)
    # A concrete simulator NAME is machine state, not project state — the
    # hardcoded 'iPhone 16' can never match on machines whose simulators were
    # never created. Resolve the first available iOS simulator (id= works for
    # both build and test); with none available, skip the Xcode gates loudly
    # instead of running commands that are guaranteed to fail. The sed takes the
    # LAST ≥8-char hex/dash parenthetical WITHOUT a $ anchor: real simctl lines
    # end in a (Shutdown)/(Booted) state suffix (often with trailing space), and
    # the state word is never in the hex class, so the UDID is always the last
    # in-class group even when the device name carries its own parentheses.
    XCODE_SIM=$(xcrun simctl list devices available 2>/dev/null | sed -n 's/.*(\([A-F0-9-]\{8,\}\)).*/\1/p' | head -1)
    if [ -z "$XCODE_SIM" ]; then
      echo "⚠ No available iOS Simulator found — skipping the Xcode build gate. Set workflow.build_command to run it anyway."
      BUILD_CMD=""
      XCODEPROJ=""
    else
      XCODE_DEST="id=$XCODE_SIM"
      # review F2: the command string is re-parsed by `bash -c`, so an
      # apostrophe in a repo/scheme name would terminate the quote (unbalanced-
      # quote failure; a crafted path shape reaches command injection). Escape
      # for the single-quoted span at the only boundary Engineer owns.
      XCODEPROJ=$(printf '%s' "$XCODEPROJ" | sed "s/'/'\\\\''/g")
      XCODE_SCHEME=$(printf '%s' "$XCODE_SCHEME" | sed "s/'/'\\\\''/g")
    fi
    if [ -n "$XCODEPROJ" ] && [ -n "$XCODE_SCHEME" ]; then
      BUILD_CMD="xcodebuild build -project '$XCODEPROJ' -scheme '$XCODE_SCHEME' -destination '${XCODE_DEST}'"
    elif [ -n "$XCODEPROJ" ]; then
      BUILD_CMD="xcodebuild build -project '$XCODEPROJ' -destination '${XCODE_DEST}'"
    fi
  elif [ -f "Makefile" ] && grep -q "^build:" Makefile; then
    BUILD_CMD="make build"
  elif [ -f "Justfile" ] || [ -f "justfile" ]; then
    BUILD_CMD="just build"
  elif [ -f "Cargo.toml" ]; then
    BUILD_CMD="cargo build"
  elif [ -f "go.mod" ]; then
    BUILD_CMD="go build ./..."
  elif [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    BUILD_CMD="python -m py_compile $(find . -name '*.py' -not -path './.planning/*' -not -path './node_modules/*' | head -20 | tr '\n' ' ')"
  elif [ -f "package.json" ] && grep -q '"build"' package.json; then
    # The project's own package manager (packageManager field, then lockfile), npm if unresolved.
    BUILD_CMD=$(engineer_run query resolve-package-manager build --cwd . 2>/dev/null || echo "npm run build")
    [ -n "$BUILD_CMD" ] || BUILD_CMD="npm run build"
    echo "⚠ Build command not configured — running this project's build script (${BUILD_CMD}). Set workflow.build_command to pin it."
  else
    BUILD_CMD=""
    echo "⚠ No build command detected — skipping build gate"
  fi
fi
# Run build with 5-minute timeout
BUILD_EXIT=0
if [ -n "$BUILD_CMD" ]; then
  engineer_run query run-with-timeout 300 -- bash -c "$BUILD_CMD" 2>&1
  BUILD_EXIT=$?
  if [ "${BUILD_EXIT}" -eq 0 ]; then
    echo "✓ Post-merge build gate passed"
  elif [ "${BUILD_EXIT}" -eq 124 ]; then
    echo "⚠ Post-merge build gate timed out after 5 minutes"
  else
    echo "✗ Post-merge build gate failed (exit code ${BUILD_EXIT})"
    # engineer-handoff:begin wave-failure-record
    _ENGINEER_HANDOFF="$( { git rev-parse --absolute-git-dir 2>/dev/null || echo "${TMPDIR:-/tmp}/engineer-$(pwd | cksum | cut -d' ' -f1)"; } )/handoff"; mkdir -p "$_ENGINEER_HANDOFF"
    printf '.\n' >> "$_ENGINEER_HANDOFF/wave-failures"  # one line per failed gate; a variable would not survive the next block 
    # engineer-handoff:end wave-failure-record
  fi
fi
```

**If `BUILD_EXIT` is 0 (pass):** `✓ Build gate passed` → proceed to Test gate.

**If `BUILD_EXIT` is 124 (timeout):** Log warning, treat as non-blocking, continue to Test gate.

**If `BUILD_EXIT` is non-zero (build failure):** The block above has already recorded the failure in the cumulative wave-failure handoff file (same semantics as test failures; step 5.8 reads it). Present failure output and offer "Fix now" or "Continue" options (same as step 5.8).

**Step B — Test gate:**

```bash
# Resolve test command: project config > Xcode > Makefile > language sniff
TEST_CMD=$(engineer_run query config-get workflow.test_command --default "" --raw 2>/dev/null || true)
if [ -z "$TEST_CMD" ]; then
  XCODEPROJ=$(find . -maxdepth 2 -name "*.xcodeproj" -not -path "*/node_modules/*" 2>/dev/null | head -1)
  if [ -n "$XCODEPROJ" ]; then
    # Xcode project: reuse scheme + simulator resolved above (or re-detect)
    if [ -z "${XCODE_SCHEME:-}" ]; then
      XCODE_SCHEME=$(xcodebuild -list -json -project "$XCODEPROJ" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('project',{}).get('schemes',[None])[0] or '')" 2>/dev/null || true)
    fi
    # Reuse the simulator resolved by the build gate; re-detect if this
    # block runs in a fresh shell. No simulator → skip loudly, same as Step A.
    if [ -z "${XCODE_SIM:-}" ]; then
      XCODE_SIM=$(xcrun simctl list devices available 2>/dev/null | sed -n 's/.*(\([A-F0-9-]\{8,\}\)).*/\1/p' | head -1)
    fi
    if [ -z "$XCODE_SIM" ]; then
      echo "⚠ No available iOS Simulator found — skipping the Xcode test gate. Set workflow.test_command to run it anyway."
      TEST_CMD=""
      XCODEPROJ=""
    else
      XCODE_DEST="id=$XCODE_SIM"
      XCODEPROJ=$(printf '%s' "$XCODEPROJ" | sed "s/'/'\\\\''/g")
      XCODE_SCHEME=$(printf '%s' "$XCODE_SCHEME" | sed "s/'/'\\\\''/g")
    fi
    if [ -n "$XCODEPROJ" ] && [ -n "$XCODE_SCHEME" ]; then
      TEST_CMD="xcodebuild test -project '$XCODEPROJ' -scheme '$XCODE_SCHEME' -destination '${XCODE_DEST}'"
    elif [ -n "$XCODEPROJ" ]; then
      TEST_CMD="xcodebuild test -project '$XCODEPROJ' -destination '${XCODE_DEST}'"
    fi
  elif [ -f "Makefile" ] && grep -q "^test:" Makefile; then
    TEST_CMD="make test"
  elif [ -f "Justfile" ] || [ -f "justfile" ]; then
    TEST_CMD="just test"
  elif [ -f "package.json" ]; then
    # Same resolver as the build gate.
    TEST_CMD=$(engineer_run query resolve-package-manager test --cwd . 2>/dev/null || echo "npm test")
    [ -n "$TEST_CMD" ] || TEST_CMD="npm test"
  elif [ -f "Cargo.toml" ]; then
    TEST_CMD="cargo test"
  elif [ -f "go.mod" ]; then
    TEST_CMD="go test ./..."
  elif [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    TEST_CMD="python -m pytest -x -q --tb=short 2>&1 || uv run python -m pytest -x -q --tb=short"
  else
    TEST_CMD="true"
    echo "⚠ No test runner detected — skipping post-merge test gate"
  fi
fi
# Normalize to a one-shot form (defeat vitest/jest watch mode) via the
# same shared normalize-test-command helper the regression gate uses, then bound
# with the configured timeout so a watch-mode runner cannot hang the gate.
TEST_CMD=$(engineer_run query normalize-test-command "$TEST_CMD" --cwd . 2>/dev/null || echo "$TEST_CMD")
TEST_GATE_TIMEOUT=$(engineer_run query config-get workflow.test_gate_timeout --raw 2>/dev/null || echo "600")
TEST_EXIT=0
engineer_run query run-with-timeout "$TEST_GATE_TIMEOUT" -- bash -c "$TEST_CMD" 2>&1
TEST_EXIT=$?
if [ "${TEST_EXIT}" -eq 0 ]; then
  echo "✓ Post-merge test gate passed — no cross-plan conflicts"
elif [ "${TEST_EXIT}" -eq 124 ]; then
  echo "⚠ POST-MERGE TEST GATE TIMED OUT after ${TEST_GATE_TIMEOUT}s — the runner did not exit, likely stuck in watch/dev mode (e.g. vitest without 'run'). Verify tests with a one-shot command (e.g. 'vitest run') or raise workflow.test_gate_timeout. For Xcode suites: xcodebuild collects a sysdiagnose into the .xcresult by default (~10 minutes on a passing suite) — add '-collect-test-diagnostics never' to the test command or raise workflow.test_gate_timeout."
else
  echo "✗ Post-merge test gate failed (exit code ${TEST_EXIT})"
  # engineer-handoff:begin wave-failure-record
  _ENGINEER_HANDOFF="$( { git rev-parse --absolute-git-dir 2>/dev/null || echo "${TMPDIR:-/tmp}/engineer-$(pwd | cksum | cut -d' ' -f1)"; } )/handoff"; mkdir -p "$_ENGINEER_HANDOFF"
  printf '.\n' >> "$_ENGINEER_HANDOFF/wave-failures"  # one line per failed gate; a variable would not survive the next block 
  # engineer-handoff:end wave-failure-record
fi
```

**If `TEST_EXIT` is 0 (pass):** `✓ Post-merge test gate: {N} tests passed — no cross-plan conflicts` → continue to orchestrator tracking update.

**If `TEST_EXIT` is 124 (timeout):** The runner did not exit within the budget — surface the printed message clearly (watch/dev mode is the likely cause). Treated as non-blocking (a genuinely long suite may just need a larger `workflow.test_gate_timeout`), but it is NEVER silently ignored — the watch-mode cause is named so the user can fix it (one-shot command / `workflow.test_command` / larger timeout).

**If `TEST_EXIT` is non-zero (test failure):** The block above has recorded the failure in the cumulative wave-failure handoff file, which tracks
failures across waves (a shell counter cannot: every fenced block is its own shell). Subsequent waves should report:
`⚠ Note: ${WAVE_FAILURE_COUNT} prior wave(s) had test failures` (`WAVE_FAILURE_COUNT` is read from the handoff file, as in step 5.8 of `execute-phase.md`)
