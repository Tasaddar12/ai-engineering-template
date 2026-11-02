Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# Step: regression_gate_run

Run the resolved prior-phase test command one-shot, bounded by a timeout, so a
watch-mode runner (vitest defaults to watch in a TTY; jest `--watch`) cannot
hang this gate forever. Uses the configured verification checks
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
# Run the configured checks; retain prior-phase test discovery as diagnostic context.
REG_CHECKS=$(engineer_run query verification.run-checks) && REG_TEST_EXIT=0 || REG_TEST_EXIT=$?
if [ "$REG_TEST_EXIT" -ne 0 ]; then
  echo "REGRESSION GATE ABORTED: configured checks failed or could not run" >&2
  exit "$REG_TEST_EXIT"
fi
```

**On `REG_TEST_EXIT` 124 (`REGRESSION GATE ABORTED`):** HALT — do not proceed to verification. The runner did not exit within the budget (watch/dev mode is the likely cause). Surface the watch-mode cause and the recovery options; never silently continue.
