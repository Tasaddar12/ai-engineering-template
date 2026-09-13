# Planner — Load Graph Context

> Loaded by `planner` at the `load_graph_context` step.

Check for knowledge graph:

```bash
ls .planning/graphs/graph.json 2>/dev/null
```

If graph.json exists, check freshness:

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; if [ -f "$Workflow_TOOLS" ]; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif [ -f "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" ]; then Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}"; workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif command -v workflow-tools >/dev/null 2>&1; then Workflow_TOOLS="$(command -v workflow-tools)"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif [ -f "$HOME/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" ]; then Workflow_TOOLS="$HOME/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}"; workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow-tools is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi
workflow_run graphify status
```

If the status response has `stale: true`, note for later: "Graph is {age_hours}h old -- treat semantic relationships as approximate." Include this annotation inline with any graph context injected below.

Query the graph for phase-relevant dependency context (single query per D-06):

```bash
workflow_run graphify query "<phase-goal-keyword>" --budget 2000
```

Use the keyword that best captures the phase goal. Examples:
- Phase "User Authentication" -> query term "auth"
- Phase "Payment Integration" -> query term "payment"
- Phase "Database Migration" -> query term "migration"

If the query returns nodes and edges, incorporate as dependency context for planning:
- Which modules/files are semantically related to this phase's domain
- Which subsystems may be affected by changes in this phase
- Cross-document relationships that inform task ordering and wave structure

If no results or graph.json absent, continue without graph context.


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
