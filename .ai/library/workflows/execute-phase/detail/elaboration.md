# execute-phase.md — deferred elaboration

Read in full when `workflow.compact_content` is `false` (the default) — see
`.ai/library/references/compact-content-gate.md` for the check and resolution rule this
spine defers to. Each `§` below is the full text the spine condenses at the point it
names.

(safe_resume_gate, checkpoint_handling, and auto_copy_learnings are stated verbatim in the
spine itself — pre-existing structural drift guards in this repo's test suite pin their exact
wording and bash there, so nothing about them is deferred to this file.)

## § 1 — check_interactive_mode

**Parse `--interactive` flag from $ARGUMENTS.**

**If `--interactive` flag present:** Switch to interactive execution mode.

Interactive mode executes plans sequentially **inline** (no subagent spawning) with user
checkpoints between tasks. The user can review, modify, or redirect work at any point.

**Interactive execution flow:**

1. Load plan inventory as normal (discover_and_group_plans)
2. For each plan (sequentially, ignoring wave grouping):

   a. **Present the plan to the user:**
      ```
      ## Plan {plan_id}: {plan_name}

      Objective: {from plan file}
      Tasks: {task_count}

      Options:
      - Execute (proceed with all tasks)
      - Review first (show task breakdown before starting)
      - Skip (move to next plan)
      - Stop (end execution, save progress)
      ```

   b. **If "Review first":** Read and display the full plan file. Ask again: Execute, Modify, Skip.

   c. **If "Execute":** Read and follow `.ai/library/workflows/execute-plan.md` **inline**
      (do NOT spawn a subagent). Execute tasks one at a time.

   d. **After each task:** Pause briefly. If the user intervenes (types anything), stop and address
      their feedback before continuing. Otherwise proceed to next task.

   e. **After plan complete:** Show results, commit, create SUMMARY.md, then present next plan.

3. After all plans: proceed to verification (same as normal mode).

(The spine's own condensed text already states the handle_branching hand-off; not repeated here.)

## § 2 — cross_ai_delegation

**Optional step 2.5 — Delegate plans to an external AI runtime.**

This step runs after plan discovery and before normal wave execution. It identifies plans
that should be delegated to an external AI command and executes them via stdin-based prompt
delivery. Plans handled here are removed from the execute_waves plan list so the normal
executor skips them.

**Activation logic:**

1. If `CROSS_AI_DISABLED` is true (`--no-cross-ai` flag): skip this step entirely.
2. If `CROSS_AI_FORCE` is true (`--cross-ai` flag): mark ALL incomplete plans for cross-AI execution.
3. Otherwise: check each plan's frontmatter for `cross_ai: true` AND verify config
   `workflow.cross_ai_execution` is `true`. Plans matching both conditions are marked for cross-AI.

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
CROSS_AI_ENABLED=$(workflow_run query config-get workflow.cross_ai_execution --raw 2>/dev/null || echo "false")
CROSS_AI_CMD=$(workflow_run query config-get workflow.cross_ai_command --raw 2>/dev/null || echo "")
CROSS_AI_TIMEOUT=$(workflow_run query config-get workflow.cross_ai_timeout --raw 2>/dev/null || echo "300")
```

**If no plans are marked for cross-AI:** Skip to execute_waves.

**If plans are marked but `cross_ai_command` is empty:** Error — tell user to set
`workflow.cross_ai_command` via `workflow_run query config-set workflow.cross_ai_command "<command>"`.

**For each cross-AI plan (sequentially):**

1. **Construct the task prompt** from the plan file:
   - Extract `<objective>` and `<tasks>` sections from the PLAN.md
   - Append PROJECT.md context (project name, description, tech stack)
   - Format as a self-contained execution prompt

2. **Check for dirty working tree before execution:**
   ```bash
   if ! git diff --quiet HEAD 2>/dev/null; then
     echo "WARNING: dirty working tree detected — the external AI command may produce uncommitted changes that conflict with existing modifications"
   fi
   ```

3. **Run the external command** from the project root, writing the prompt to stdin.
   Never shell-interpolate the prompt — always pipe via stdin to prevent injection:
   ```bash
   echo "$TASK_PROMPT" | workflow_run run-with-timeout "${CROSS_AI_TIMEOUT}" -- ${CROSS_AI_CMD} > "$CANDIDATE_SUMMARY" 2>"$ERROR_LOG"
   EXIT_CODE=$?
   ```

4. **Evaluate the result:**

   **Success (exit 0 + valid summary):**
   - Read `$CANDIDATE_SUMMARY` and validate it contains meaningful content
     (not empty, has at least a heading and description — a valid SUMMARY.md structure)
   - Write it as the plan's SUMMARY.md file
   - Update STATE.md plan status to complete
   - Update ROADMAP.md progress
   - Mark plan as handled — skip it in execute_waves

   **Failure (non-zero exit or invalid summary):**
   - Display the error output and exit code
   - Warn: "The external command may have left uncommitted changes or partial edits
     in the working tree. Review `git status` and `git diff` before proceeding."
   - Offer three choices:
     - **retry** — run the same plan through cross-AI again
     - **skip** — fall back to normal executor for this plan (re-add to execute_waves list)
     - **abort** — stop execution entirely, preserve state for resume

5. **After all cross-AI plans processed:** Remove successfully handled plans from the
   incomplete plan list so execute_waves skips them. Any skipped-to-fallback plans remain
   in the list for normal executor processing.


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
