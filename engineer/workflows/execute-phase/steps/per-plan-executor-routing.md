# Per-plan executor routing 

Run for each plan, immediately before its `Agent()` dispatch in step 3. Sets
`EXECUTOR_TYPE` so a plan can opt into a specialist executor instead of the
default `executor`. `plan_json` (the current plan's object from
`phase-plan-index`, same scope step 2.5 uses) is in scope.

## Contract

- Default: `EXECUTOR_TYPE="executor"` — byte-identical to pre- dispatch.
- A plan opts into a specialist by declaring `agent_hint: <name>` in its PLAN.md
  frontmatter. The field reaches the orchestrator as `plan_json.agent_hint`
  (parsed by `phase-plan-index`; `null` when unset).
- When routing is enabled AND the hint is non-empty AND the named agent resolves
  on the active runtime, `EXECUTOR_TYPE` becomes the hint. Otherwise it stays
  `executor`.
- The resolved `EXECUTOR_TYPE` is used as `subagent_type` in BOTH worktree and
  sequential dispatch (sequential reuses the worktree-mode `Agent()` template).

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
# Default-on; opt out with: engineer config-set workflow.agent_hint_routing false
AGENT_HINT_ROUTING=$(engineer_run query config-get workflow.agent_hint_routing --raw 2>/dev/null || echo "true")

EXECUTOR_TYPE="executor"
if [ "${AGENT_HINT_ROUTING:-true}" != "false" ]; then
  PLAN_HINT=$(jq -r '.agent_hint // empty' <<<"$plan_json" 2>/dev/null | tr -d '"')
  if [ -n "$PLAN_HINT" ]; then
    EXECUTOR_TYPE=$(engineer_run query resolve-agent --name "$PLAN_HINT" --raw 2>/dev/null || echo "executor")
  fi
fi

#  v1 routes only the Agent()-based dispatch. On the orchestrator-worktree
# backend (process-spawn; no subagent_type) a resolved hint cannot be honored
# yet — surface it so a set hint is never silently ignored.
if [ "${ISOLATION:-}" = "orchestrator-worktree" ] && [ -n "${PLAN_HINT:-}" ]; then
  echo "note: plan ${plan_id} agent_hint='${PLAN_HINT}' resolved, but orchestrator-worktree dispatch does not route subagent types in this release — using the default executor." >&2
fi
```

`engineer_run query resolve-agent` consults the **active runtime's agent directory**
(both project-local and user-global, across runtime filename variants — `.md`,
`.toml`) and fails
closed to `executor` when the named agent does not resolve or on any error,
so a missing or misspelled hint never blocks dispatch.

## Scope

Routing applies to the `Agent()`-based dispatch (harness-worktree and sequential
modes). The `orchestrator-worktree` isolation backend spawns executors via a
separate process path that has no `subagent_type` and is not routed in this
release.

## Checkpoint gate rule 

Loaded with the routing resolution so the orchestrator reads it immediately
before composing each dispatch prompt, in every isolation mode.

On `checkpoint:human-verify` / `checkpoint:decision` tasks, `gate="blocking"`
(the default) is auto-approvable in auto-mode — that is the executor's own
`<checkpoint_protocol>` (`agents/executor.md`), and `checkpoints.md` (the
full gate table) is embedded in the dispatch `<execution_context>` verbatim.
Only `gate="blocking-human"` always surfaces to a human, regardless of
auto-mode. An unmet `<precondition>` checkpoint (executor step 0, `Blocked by:
Precondition not met` — unmet `user_setup` step, missing env var, absent
prior-phase artifact) reports `blocking-human` and therefore always surfaces
to a human, in every mode : the missing prerequisite is a fact only a
human can establish, not a verification step to rubber-stamp.

When composing the `Agent()` prompt, do NOT add text refusing or overriding
auto-approval for a `blocking` gate. Orchestrator-composed instructions that contradict the
executor's protocol win the executor's attention, stall autonomous runs at the
checkpoint, and defeat `_auto_chain_active`/auto-advance for the common case.
Executor-side gate semantics are already complete; compose nothing about gates
beyond what the template already embeds.
