# Planner — Load Graph Context

> Loaded by `planner` at the `load_graph_context` step.

Check for a knowledge graph and read its freshness in one call. `status` resolves the
graph through `graphify.graph_path`, so it is also the presence gate — a bare
`ls` of the default location misses an umbrella graph shared across sibling repos:

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
engineer_run graphify status
```

If `exists` is `false`, continue without graph context — skip the rest of this step.

If the status response has `stale: true`, note for later: "Graph is {age_hours}h old -- treat semantic relationships as approximate." Include this annotation inline with any graph context injected below.

The same response carries `graph_path` — the resolved graph location. Substitute it for `<graph>` below. `graph_path` comes from `graphify.graph_path` in `.planning/config.yaml`, a config surface already trusted elsewhere; if it ever carried attacker-controlled content, the literal double-quoted substitution below would need escaping.

Query the graph for phase-relevant dependency context (single query per D-06). Prefer the `graphify` CLI when it is on PATH; fall back to the built-in reader otherwise:

```bash
if command -v graphify >/dev/null 2>&1; then
  graphify query "<phase-goal-keyword>" --graph "<graph>" --budget 2000
  graphify affected "<phase-goal-keyword>" --graph "<graph>" --depth 2
else
  engineer_run graphify query "<phase-goal-keyword>" --budget 2000
fi
```

Why the CLI is preferred: it ranks seeds (IDF weighting, fuzzy matching) and applies context filters before traversal, where the built-in reader seeds by case-insensitive substring over label and description — so a term like "auth" seeds equally on `author` and `authorize` — and then expands a fixed two hops. `affected` answers "which subsystems may be affected by changes in this phase" directly, by reverse traversal; it has no built-in equivalent, so the fallback path runs the query alone.

The two paths return **different shapes**: the CLI emits prose, the built-in emits JSON with per-edge confidence tiers and `budget_met`/`budget_estimate`. `--budget` caps rendered output on the CLI and estimated payload bytes in the built-in — same flag name, different unit. Read whichever you get; do not assume a stable shape and do not paste raw output into PLAN.md.

Use the keyword that best captures the phase goal. Prefer the full domain word over a
prefix of it — on the fallback path a prefix is matched as a substring, so "auth" also
seeds on `author` and `authoring`. Examples:
- Phase "User Authentication" -> query term "authentication"
- Phase "Payment Integration" -> query term "payment"
- Phase "Database Migration" -> query term "migration"

If the query returns related nodes, incorporate as dependency context for planning:
- Which modules/files are semantically related to this phase's domain
- Which subsystems may be affected by changes in this phase
- Cross-document relationships that inform task ordering and wave structure

If nothing comes back, continue without graph context.

## Current-source confirmation

Verify every relevant graph edge against current source, annotate stale edges and cite the inspected revision. A graph result is discovery evidence, not authority to change scope. Put producer/consumer dependencies in `depends_on` and shared external identities in `resources`; a graph label does not schedule work.
