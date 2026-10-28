# TDD-applicability resolution 

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
TDD_APPLICABLE_RAW=$(engineer_run query phase.tdd-applicable "{phase_dir}/{plan_file}" --pick applicable 2>/dev/null)
TDD_APPLICABLE_RC=$?
if [ $TDD_APPLICABLE_RC -ne 0 ]; then
  echo "FATAL: could not resolve TDD-applicability for plan {plan_number} — 'engineer_run query phase.tdd-applicable' failed. Refusing to guess whether this dispatch needs the TDD procedure. Halting." >&2
  exit 1
fi
TDD_APPLICABLE="$TDD_APPLICABLE_RAW"
```

## Pre-dispatch check (MANDATORY)

Before calling Agent(), confirm every `${...}` conditional in the prompt below
(`TDD_APPLICABLE`, `CONTEXT_WINDOW`, `AGENT_SKILLS`) was resolved to concrete
text for THIS plan. If any marker's value was not computed, HALT — do not
dispatch a prompt containing literal `${...}` template syntax .
