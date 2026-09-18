# Phase runtime launcher. Workflows paste this block verbatim as the first
# lines of their init step, then call `phase_run query <verb> ...`.
#
# Resolution order: an explicit PHASE_RUNTIME, the repository's own namespace
# (authoring checkout or installed project), then the host's global install.
_PHASE_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
_PHASE_PY="$(command -v python3 || command -v python)"
for _candidate in "${PHASE_RUNTIME:-}" \
  "${_PHASE_ROOT}/.ai/runtime/phase.py" \
  "${_PHASE_ROOT}/.claude/runtime/phase.py" \
  "${_PHASE_ROOT}/.codex/runtime/phase.py" \
  "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/runtime/phase.py" \
  "${CODEX_HOME:-$HOME/.codex}/runtime/phase.py"; do
  if [ -n "$_candidate" ] && [ -f "$_candidate" ]; then PHASE_RUNTIME="$_candidate"; break; fi
done
if [ -z "${PHASE_RUNTIME:-}" ] || [ ! -f "$PHASE_RUNTIME" ]; then
  echo "ERROR: phase runtime not found (looked for runtime/phase.py under the repository and host config). Run the installer." >&2
  exit 1
fi
if [ -z "$_PHASE_PY" ]; then
  echo "ERROR: python3 is required to run the phase runtime." >&2
  exit 1
fi
phase_run() { "$_PHASE_PY" "$PHASE_RUNTIME" "$@"; }
case "$(phase_run query runtime-identity --raw 2>/dev/null || true)" in
  *ai-phase-runtime*) : ;;
  *) echo "WARNING: \"$PHASE_RUNTIME\" did not identify itself as the phase runtime." >&2 ;;
esac
