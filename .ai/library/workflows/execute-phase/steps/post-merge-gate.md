# Step: post_merge_gate

Post-merge build & test gate. Runs after all worktrees in a wave are merged
(parallel mode), or after the last plan completes (serial mode). Catches
cross-plan integration failures that individual worktree self-checks cannot
detect.

**Step A — Build gate:**

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
# Resolve build command: project config > Xcode > Makefile > language sniff
BUILD_CMD=$(workflow_run query config-get workflow.build_command --default "" --raw 2>/dev/null || true)
if [ -z "$BUILD_CMD" ]; then
  XCODEPROJ=$(find . -maxdepth 2 -name "*.xcodeproj" -not -path "*/node_modules/*" 2>/dev/null | head -1)
  if [ -n "$XCODEPROJ" ]; then
    # Xcode project: get first scheme from xcodebuild -list -json
    XCODE_SCHEME=$(xcodebuild -list -json -project "$XCODEPROJ" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('project',{}).get('schemes',[None])[0] or '')" 2>/dev/null || true)
    if [ -n "$XCODE_SCHEME" ]; then
      BUILD_CMD="xcodebuild build -scheme '$XCODE_SCHEME' -destination 'platform=iOS Simulator,name=iPhone 16'"
    else
      BUILD_CMD="xcodebuild build -destination 'platform=iOS Simulator,name=iPhone 16'"
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
    BUILD_CMD="npm run build"
  else
    BUILD_CMD=""
    echo "⚠ No build command detected — skipping build gate"
  fi
fi
# Run build with 5-minute timeout
BUILD_EXIT=0
if [ -n "$BUILD_CMD" ]; then
  workflow_run run-with-timeout 300 -- bash -c "$BUILD_CMD" 2>&1
  BUILD_EXIT=$?
  if [ "${BUILD_EXIT}" -eq 0 ]; then
    echo "✓ Post-merge build gate passed"
  elif [ "${BUILD_EXIT}" -eq 124 ]; then
    echo "⚠ Post-merge build gate timed out after 5 minutes"
  else
    echo "✗ Post-merge build gate failed (exit code ${BUILD_EXIT})"
    WAVE_FAILURE_COUNT=$((WAVE_FAILURE_COUNT + 1))
  fi
fi
```

**If `BUILD_EXIT` is 0 (pass):** `✓ Build gate passed` → proceed to Test gate.

**If `BUILD_EXIT` is 124 (timeout):** Log warning, treat as non-blocking, continue to Test gate.

**If `BUILD_EXIT` is non-zero (build failure):** Increment `WAVE_FAILURE_COUNT` (same semantics as test failures). Present failure output and offer "Fix now" or "Continue" options (same as step 5.8).

**Step B — Test gate:**

```bash
# Resolve test command: project config > Xcode > Makefile > language sniff
TEST_CMD=$(workflow_run query config-get workflow.test_command --default "" --raw 2>/dev/null || true)
if [ -z "$TEST_CMD" ]; then
  XCODEPROJ=$(find . -maxdepth 2 -name "*.xcodeproj" -not -path "*/node_modules/*" 2>/dev/null | head -1)
  if [ -n "$XCODEPROJ" ]; then
    # Xcode project: reuse scheme detected above (or re-detect)
    if [ -z "${XCODE_SCHEME:-}" ]; then
      XCODE_SCHEME=$(xcodebuild -list -json -project "$XCODEPROJ" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('project',{}).get('schemes',[None])[0] or '')" 2>/dev/null || true)
    fi
    if [ -n "$XCODE_SCHEME" ]; then
      TEST_CMD="xcodebuild test -scheme '$XCODE_SCHEME' -destination 'platform=iOS Simulator,name=iPhone 16'"
    else
      TEST_CMD="xcodebuild test -destination 'platform=iOS Simulator,name=iPhone 16'"
    fi
  elif [ -f "Makefile" ] && grep -q "^test:" Makefile; then
    TEST_CMD="make test"
  elif [ -f "Justfile" ] || [ -f "justfile" ]; then
    TEST_CMD="just test"
  elif [ -f "package.json" ]; then
    TEST_CMD="npm test"
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
# #1857: normalize to a one-shot form (defeat vitest/jest watch mode) via the
# same shared normalize-test-command helper the regression gate uses, then bound
# with the configured timeout so a watch-mode runner cannot hang the gate.
TEST_CMD=$(workflow_run query normalize-test-command "$TEST_CMD" --cwd . 2>/dev/null || echo "$TEST_CMD")
TEST_GATE_TIMEOUT=$(workflow_run query config-get workflow.test_gate_timeout --raw 2>/dev/null || echo "600")
TEST_EXIT=0
workflow_run run-with-timeout "$TEST_GATE_TIMEOUT" -- bash -c "$TEST_CMD" 2>&1
TEST_EXIT=$?
if [ "${TEST_EXIT}" -eq 0 ]; then
  echo "✓ Post-merge test gate passed — no cross-plan conflicts"
elif [ "${TEST_EXIT}" -eq 124 ]; then
  echo "⚠ POST-MERGE TEST GATE TIMED OUT after ${TEST_GATE_TIMEOUT}s — the runner did not exit, likely stuck in watch/dev mode (e.g. vitest without 'run'). Verify tests with a one-shot command (e.g. 'vitest run') or raise workflow.test_gate_timeout."
else
  echo "✗ Post-merge test gate failed (exit code ${TEST_EXIT})"
  WAVE_FAILURE_COUNT=$((WAVE_FAILURE_COUNT + 1))
fi
```

**If `TEST_EXIT` is 0 (pass):** `✓ Post-merge test gate: {N} tests passed — no cross-plan conflicts` → continue to orchestrator tracking update.

**If `TEST_EXIT` is 124 (timeout):** The runner did not exit within the budget — surface the printed message clearly (watch/dev mode is the likely cause; #1857). Treated as non-blocking (a genuinely long suite may just need a larger `workflow.test_gate_timeout`), but it is NEVER silently ignored — the watch-mode cause is named so the user can fix it (one-shot command / `workflow.test_command` / larger timeout).

**If `TEST_EXIT` is non-zero (test failure):** Increment `WAVE_FAILURE_COUNT` to track
cumulative failures across waves. Subsequent waves should report:
`⚠ Note: ${WAVE_FAILURE_COUNT} prior wave(s) had test failures`


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
