---
name: workflow:discuss-phase
description: Gather phase context through adaptive questioning before planning.
argument-hint: "<phase> [--all] [--auto] [--chain] [--batch] [--analyze] [--text] [--power] [--assumptions]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
  - Agent
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
requires: [config, phase]
---

<objective>
Extract implementation decisions that downstream agents need — researcher and planner will use CONTEXT.md to know what to investigate and what choices are locked.

**How it works:**
1. Load prior context (PROJECT.md, REQUIREMENTS.md, STATE.md, prior CONTEXT.md files)
2. Scout codebase for reusable assets and patterns
3. Analyze phase — skip gray areas already decided in prior phases
4. Present remaining gray areas — user selects which to discuss
5. Deep-dive each selected area until satisfied
6. Create CONTEXT.md with decisions that guide research and planning

**Output:** `{phase_num}-CONTEXT.md` — decisions clear enough that downstream agents can act without asking the user again
</objective>

<execution_context>
Workflow files are loaded on-demand in the <process> section below — not upfront.
Do not pre-load any workflow files before reading the mode routing instructions.
</execution_context>

<runtime_note>
**Copilot (VS Code):** Use `vscode_askquestions` wherever this workflow calls `AskUserQuestion`. They are equivalent — `vscode_askquestions` is the VS Code Copilot implementation of the same interactive question API.
</runtime_note>

<context>
Phase number: $ARGUMENTS (required)

Context files are resolved in-workflow using `init phase-op` and roadmap/state tool calls.
</context>

<process>
**Mode routing:**
```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; if [ -f "$Workflow_TOOLS" ]; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif [ -f "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" ]; then Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}"; workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif command -v workflow-tools >/dev/null 2>&1; then Workflow_TOOLS="$(command -v workflow-tools)"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif [ -f "$HOME/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" ]; then Workflow_TOOLS="$HOME/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}"; workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow-tools is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi
DISCUSS_MODE=$(workflow_run query config-get workflow.discuss_mode --raw 2>/dev/null || echo "discuss")
```

If `--assumptions` is in $ARGUMENTS:
Read and execute `.ai/library/workflows/list-phase-assumptions.md` end-to-end.
Stop here.

Otherwise, if `DISCUSS_MODE` is `"assumptions"`:
Read and execute `.ai/library/workflows/discuss-phase-assumptions.md` end-to-end.

Otherwise (`"discuss"` / unset / any other value):
Read and execute `.ai/library/workflows/discuss-phase.md` end-to-end.

**MANDATORY:** Read the appropriate workflow file BEFORE taking any action. The objective and success_criteria sections in this command file are summaries — the workflow file contains the complete step-by-step process with all required behaviors, config checks, and interaction patterns. Do not improvise from the summary.

**Lazy loading:** `.ai/templates/context.md` is loaded inside the `write_context` step of the active workflow. `discuss-phase-power.md` is loaded inside `discuss-phase.md` when `--power` is detected. Do not load either here.
</process>

<success_criteria>
- Prior context loaded and applied (no re-asking decided questions)
- Gray areas identified through intelligent analysis
- User chose which areas to discuss
- Each selected area explored until satisfied
- Scope creep redirected to deferred ideas
- CONTEXT.md captures decisions, not vague vision
- User knows next steps
</success_criteria>


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
