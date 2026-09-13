@.ai/library/references/response-language-directive.md

# Ultraplan Phase Workflow [BETA]

Offload Workflow's plan phase to Claude Code's ultraplan cloud infrastructure.

⚠ **BETA feature.** Ultraplan is in research preview and may change. This workflow is
intentionally isolated from /workflow:plan-phase so upstream changes to ultraplan cannot
affect the core planning pipeline.

---

<step name="banner">

Display the stage banner:

```text
### Workflow ► ULTRAPLAN PHASE  ⚠ BETA
Ultraplan is in research preview (Claude Code v2.1.91+).
Use /workflow:plan-phase for stable local planning.
```

</step>

---

<step name="runtime_gate">

Check that the session is running inside Claude Code:

```bash
if [ "$CLAUDECODE" = "1" ] || [ -n "$CLAUDE_CODE_ENTRYPOINT" ]; then
  CC_VERSION="$(claude --version 2>/dev/null | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1)"
  if [ -n "$CC_VERSION" ] && [ "$(printf '%s\n' "2.1.91" "$CC_VERSION" | sort -V | head -n1)" = "2.1.91" ]; then
    echo "claude-code:${CC_VERSION}"
  else
    echo ""
  fi
else
  echo ""
fi
```

If the output is empty or unset, display the following error and exit:

```text
### RUNTIME ERROR

/workflow:ultraplan-phase requires Claude Code.
ultraplan is not available in this runtime.

Use /workflow:plan-phase for local planning instead.
```

</step>

---

<step name="initialize">

Parse phase number from `$ARGUMENTS`. If no phase number is provided, detect the next
unplanned phase from the roadmap (same logic as /workflow:plan-phase).

Load Workflow phase context:

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
INIT=$(workflow_run query init.plan-phase "$PHASE")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Parse JSON for: `phase_found`, `phase_number`, `phase_name`, `phase_slug`, `padded_phase`,
`phase_dir`, `roadmap_path`, `requirements_path`, `research_path`, `planning_exists`.

**If `planning_exists` is false:** Error and exit:

```text
No .planning directory found. Initialize the project first:

/workflow:new-project
```

**If `phase_found` is false:** Error with the phase number provided and exit.

Display detected phase:

```text
Phase {N}: {phase name}
```

</step>

---

<step name="build_prompt">

Build the ultraplan prompt from Workflow context.

1. Read the phase scope from ROADMAP.md — extract the goal, deliverables, and scope for
   the target phase.

2. Read REQUIREMENTS.md if it exists (`requirements_path` is not null) — extract a
   concise summary (key requirements relevant to this phase, not the full document).

3. Read RESEARCH.md if it exists (`research_path` is not null) — extract a concise
   summary of technical findings. Including this reduces redundant cloud research.

Construct the prompt:

```text
Plan phase {phase_number}: {phase_name}

## Phase Scope (from ROADMAP.md)

{phase scope block extracted from ROADMAP.md}

## Requirements Context

{requirements summary, or "No REQUIREMENTS.md found — infer from phase scope."}

## Existing Research

{research summary, or "No RESEARCH.md found — research from scratch."}

## Output Format

Produce a Workflow PLAN.md with the following YAML frontmatter:

---
phase: "{padded_phase}-{phase_slug}"
plan: "{padded_phase}-01"
type: "feature"
wave: 1
depends_on: []
files_modified: []
autonomous: true
must_haves:
  truths: []
  artifacts: []
---

Then a ## Plan section with numbered tasks. Each task should have:
- A clear imperative title
- Files to create or modify
- Specific implementation steps

Keep the plan focused and executable.
```

</step>

---

<step name="return_path_card">

Display the return-path instructions **before** triggering ultraplan so they are visible
in the terminal scroll-back after ultraplan launches:

```text
### WHEN THE PLAN IS READY — WHAT TO DO

When ◆ ultraplan ready appears in your terminal:

  1. Open the session link in your browser
  2. Review the plan — use inline comments and emoji reactions to give feedback
  3. Ask Claude to revise until you're satisfied
  4. Click "Approve plan and teleport back to terminal"
  5. At the terminal dialog, choose Cancel  ← saves the plan to a file
  6. Note the file path Claude prints
  7. Run: /workflow:import --from <the file path>

/workflow:import will run conflict detection, convert to Workflow format,
validate via plan-checker, update ROADMAP.md, and commit.

### Launching ultraplan for Phase {N}: {phase_name}...
```

</step>

---

<step name="trigger">

Trigger ultraplan with the constructed prompt:

```text
/ultraplan {constructed prompt from build_prompt step}
```

Your terminal will show a `◇ ultraplan` status indicator while the remote session works.
Use `/tasks` to open the detail view with the session link, agent activity, and a stop action.

</step>


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
