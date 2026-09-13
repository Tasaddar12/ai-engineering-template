<purpose>
Analyze freeform text from the user and route to the most appropriate Workflow command. This is a dispatcher — it never does the work itself. Match user intent to the best command, confirm the routing, and hand off.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(workflow_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

<step name="validate">
**Check for input.**

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
If `$ARGUMENTS` is empty, ask via AskUserQuestion:

```
What would you like to do? Describe the task, bug, or idea and I'll route it to the right Workflow command.
```

Wait for response before continuing.
</step>

<step name="check_project">
**Check if project exists.**

```bash
INIT=$(workflow_run query state.load 2>/dev/null)
```

Track whether `.planning/` exists — some routes require it, others don't.
</step>

<step name="route">
**Match intent to command.**

Evaluate `$ARGUMENTS` against these routing rules. Rules are ordered **most-specific first**: apply the **first matching** rule, and never let a generic keyword rule ("set up", "spike", "review") preempt a more specific operation that also matches ("set up this existing codebase", "wrap up the spike findings", "review the changed source code").

| If the text describes... | Route to | Why |
|--------------------------|----------|-----|
| First-time setup for an existing codebase, brownfield onboarding, "onboard this codebase" | `/workflow:onboard` | Safe map → docs ingest → project setup sequence |
| Starting a new greenfield project, "set up", "initialize" (no existing codebase named) | `/workflow:new-project` | Needs full project initialization |
| Mapping or analyzing an existing codebase map | `/workflow:map-codebase` | Codebase discovery or refresh |
| A bug, error, crash, failure, or something broken | `/workflow:debug` | Needs systematic investigation |
| Wrapping up spikes, "package the spikes", "consolidate spike findings" | `/workflow:spike --wrap-up` | Package spike findings into reusable skill |
| Wrapping up sketches, "package the designs", "consolidate sketch findings" | `/workflow:sketch --wrap-up` | Package sketch findings into reusable skill |
| Spiking, "test if", "will this work", "experiment", "prove this out", validate feasibility | `/workflow:spike` | Throwaway experiment to validate feasibility |
| Sketching, "mockup", "what would this look like", "prototype the UI", "design this", explore visual direction | `/workflow:sketch` | Throwaway HTML mockups to explore design |
| Reviewing changed source code for bugs, security issues, or code quality ("code review the changes") | `/workflow:code-review` | Source review of phase-changed files |
| Requesting peer review of phase plans from another AI CLI ("plan review", "review the plan") | `/workflow:review` | Cross-AI plan review |
| Reviewing or hardening implemented UI ("visual audit", "review the UI") | `/workflow:ui-review` | Retroactive 6-pillar visual audit |
| Verifying security mitigations of a completed phase ("security check", "secure phase N") | `/workflow:secure-phase` | Retroactive threat-mitigation verification |
| Auditing milestone completion against original intent ("audit the milestone") | `/workflow:audit-milestone` | Milestone audit against original intent |
| An autonomous audit-to-fix pass ("audit and fix", "audit the repo and fix what it finds") | `/workflow:audit-fix` | Audit-to-fix pipeline |
| Generating or updating project documentation ("update the docs", "documentation update") | `/workflow:docs-update` | Docs verified against the codebase |
| Exploring, researching, comparing, or "how does X work" | `/workflow:explore` | Socratic ideation and idea routing |
| Discussing vision, "how should X look", brainstorming | `/workflow:discuss-phase` | Needs context gathering |
| Planning a specific phase or "plan phase N" | `/workflow:plan-phase` | Direct planning request |
| Executing a phase or "build phase N", "run phase N" (SDD dependency-aware wave execution) | `/workflow:execute-phase` | Direct execution request |
| Adding, inserting, removing, or editing phases in the roadmap ("multi-phase", roadmap phase management) | `/workflow:phase` | Roadmap phase CRUD |
| A complex task: refactoring, migration, multi-file architecture, system redesign | `/workflow:plan-phase` | Needs a full phase with plan/build cycle |
| Running all remaining phases automatically | `/workflow:autonomous` | Full autonomous execution |
| A review or quality concern about existing work | `/workflow:verify-work` | Needs verification |
| Checking progress, status, "where am I" | `/workflow:progress` | Status check |
| Resuming work, "pick up where I left off" | `/workflow:resume-work` | Session restoration |
| A note, idea, or "remember to..." | `/workflow:capture` | Capture for later |
| Adding tests, "write tests", "test coverage" | `/workflow:add-tests` | Test generation |
| Completing a milestone, shipping, releasing | `/workflow:complete-milestone` | Milestone lifecycle |
| A specific, actionable, small task (add feature, fix typo, update config) | `/workflow:quick` | Self-contained, single executor |

**Requires `.planning/` directory:** All routes except `/workflow:new-project`, `/workflow:onboard`, `/workflow:map-codebase`, `/workflow:spike`, `/workflow:sketch`, and `/workflow:help`. If the project doesn't exist and the route requires it, suggest `/workflow:onboard` for existing codebases or `/workflow:new-project` for greenfield projects.

**Ambiguity handling:** If the text could reasonably match multiple routes, ask the user via AskUserQuestion with the top 2-3 options. For example:

```
"Refactor the authentication system" could be:
1. /workflow:plan-phase — Full planning cycle (recommended for multi-file refactors)
2. /workflow:quick — Quick execution (if scope is small and clear)

Which approach fits better?
```
</step>

<step name="display">
**Show the routing decision.**

```
### Workflow ► ROUTING

**Input:** {first 80 chars of $ARGUMENTS}
**Routing to:** {chosen command}
**Reason:** {one-line explanation}
```
</step>

<step name="confirm">
**Confirm the route before dispatching (REQ-DO-03).**

Before invoking anything, ask the user to confirm the displayed route via AskUserQuestion:

```
Route to {chosen command}?
1. Yes — proceed with {chosen command} (recommended)
2. Choose a different command
3. Cancel — do not dispatch
```

- **Yes / proceed:** continue to the dispatch step.
- **Choose a different command:** present the 2-3 next-best routes from the routing table as options and loop back through display + confirm with the new selection.
- **Cancel:** stop. Do not invoke any command.

**TEXT_MODE:** present the same choices as a plain-text numbered list and ask the user to type their choice number, exactly like other AskUserQuestion calls in this workflow.
</step>

<step name="dispatch">
**Invoke the chosen command with only the arguments it accepts.**

Read the chosen command's frontmatter `argument-hint` (in `commands/<name>.md`) and forward **only arguments that command accepts**. Do NOT pass the full freeform sentence wholesale.

- If the command expects a phase number or flags only (e.g. `/workflow:verify-work [phase number]`, `/workflow:plan-phase`, `/workflow:execute-phase`), extract the phase number / flags from the input; if none was provided, extract it from context or ask via AskUserQuestion. Drop the surrounding prose.
- If the command explicitly accepts a freeform task description (e.g. `/workflow:quick`, `/workflow:debug`, `/workflow:spike`, `/workflow:sketch`), forward the relevant portion of `$ARGUMENTS` as the description.
- If the command takes no arguments, invoke it without arguments.

After invoking the command, stop. The dispatched command handles everything from here.
</step>

</process>

<success_criteria>
- [ ] Input validated (not empty)
- [ ] Intent matched to exactly one Workflow command
- [ ] Ambiguity resolved via user question (if needed)
- [ ] Project existence checked for routes that require it
- [ ] Routing decision displayed before dispatch
- [ ] Route confirmed by the user before dispatch (REQ-DO-03), with TEXT_MODE equivalent
- [ ] Command invoked with only the arguments it accepts (argument-hint aware; freeform text only where the command takes a freeform description)
- [ ] No work done directly — dispatcher only
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
