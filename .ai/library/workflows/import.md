# Import Workflow

External plan ingestion with conflict detection and agent delegation.

- **--from**: Import external plan → conflict detection → write PLAN.md → validate via plan-checker

Future: `--prd` mode (PRD extraction into PROJECT.md + REQUIREMENTS.md + ROADMAP.md) is planned for a follow-up PR.

---

<step name="banner">

Display the stage banner:
```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(workflow_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

```
### Workflow ► IMPORT
```

</step>

<step name="parse_arguments">

Parse `$ARGUMENTS` to determine the execution mode:

- If `--from` is present: extract FILEPATH (the next token after `--from`), set MODE=plan
- If `--prd` is present: display message that `--prd` is not yet implemented and exit:
  ```
  Workflow > --prd mode is planned for a future release. Use --from to import plan files.
  ```
- If neither flag is found: display usage and exit:

```
Usage: /workflow:import --from <path>

  --from <path>   Import an external plan file into Workflow format
```

**Validate the file path:**

Verify the path does not contain traversal sequences and the file exists:

```bash
case "{FILEPATH}" in
  *..* ) echo "SECURITY_ERROR: path contains traversal sequence"; exit 1 ;;
esac
test -f "{FILEPATH}" || echo "FILE_NOT_FOUND"
```

If FILE_NOT_FOUND: display error and exit:

```
### ERROR

File not found: {FILEPATH}

**To fix:** Verify the file path and try again.
```

</step>

---

## Path A: MODE=plan (--from)

<step name="plan_load_context">

Load project context for conflict detection:

1. Read `.planning/ROADMAP.md` — extract phase structure, phase numbers, dependencies
2. Read `.planning/PROJECT.md` — extract project constraints, tech stack, scope boundaries.
   **If PROJECT.md does not exist:** skip constraint checks that rely on it and display:
   ```
   Workflow > Note: No PROJECT.md found. Conflict checks against project constraints will be skipped.
   ```
3. Read `.planning/REQUIREMENTS.md` — extract existing requirements for overlap and contradiction checks.
   **If REQUIREMENTS.md does not exist:** skip requirement conflict checks and continue.
4. Glob for all CONTEXT.md files across phase directories:
   ```bash
   find .planning/phases/ -name "*-CONTEXT.md" -o -name "CONTEXT.md" 2>/dev/null
   ```
   Read each CONTEXT.md found — extract locked decisions (any decision in a `<decisions>` block)

Store loaded context for conflict detection in the next step.

</step>

<step name="plan_read_input">

Read the imported file at FILEPATH.

Determine the format:
- **Workflow PLAN.md format**: Has YAML frontmatter with `phase:`, `plan:`, `type:` fields
- **Freeform document**: Any other format (markdown spec, design doc, task list, etc.)

Extract from the imported content:
- **Phase target**: Which phase this plan belongs to (from frontmatter or inferred from content)
- **Plan objectives**: What the plan aims to accomplish
- **Tasks listed**: Individual work items described in the plan
- **Files modified**: Any files mentioned as targets
- **Dependencies**: Any referenced prerequisites

</step>

<step name="plan_conflict_detection">

Run conflict checks against the loaded project context. The report format, severity semantics, and safety-gate behavior are defined by `.ai/library/references/doc-conflict-engine.md` — read it and apply it here. Operation noun: `import`.

### BLOCKER checks (any one prevents import):

- Plan targets a phase number that does not exist in ROADMAP.md → [BLOCKER]
- Plan specifies a tech stack that contradicts PROJECT.md constraints → [BLOCKER]
- Plan contradicts a locked decision in any CONTEXT.md `<decisions>` block → [BLOCKER]
- Plan contradicts an existing requirement in REQUIREMENTS.md → [BLOCKER]

### WARNING checks (user confirmation required):

- Plan partially overlaps existing requirement coverage in REQUIREMENTS.md → [WARNING]
- Plan has `depends_on` referencing plans that are not yet complete → [WARNING]
- Plan modifies files that overlap with existing incomplete plans → [WARNING]
- Plan phase number conflicts with existing phase numbering in ROADMAP.md → [WARNING]

### INFO checks (informational, no action needed):

- Plan uses a library not currently in the project tech stack → [INFO]
- Plan adds a new phase to the ROADMAP.md structure → [INFO]

Render the full Conflict Detection Report using the format in `.ai/library/references/doc-conflict-engine.md`.

**If any [BLOCKER] exists:** apply the safety gate from the reference — exit WITHOUT writing any files. No PLAN.md is written when blockers exist.

**If only WARNINGS and/or INFO (no blockers):**

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.

Ask via AskUserQuestion using the approve-revise-abort pattern (see `.ai/library/references/gate-prompts.md`):
- question: "Review the warnings above. Proceed with import?"
- header: "Approve?"
- options: Approve | Abort

If user selects "Abort": exit cleanly with message "Import cancelled."

</step>

<step name="plan_convert">

Convert the imported content to Workflow PLAN.md format.

Ensure the PLAN.md has all required frontmatter fields:
```yaml
---
phase: "{NN}-{slug}"
plan: "{NN}-{MM}"
type: "feature|refactor|config|test|docs"
wave: 1
depends_on: []
files_modified: []
autonomous: true
must_haves:
  truths: []
  artifacts: []
---
```

**Reject PBR naming conventions in source content:**
If the imported plan references PBR plan naming (e.g., `PLAN-01.md`, `plan-01.md`), rename all references to Workflow `{NN}-{MM}-PLAN.md` convention during conversion.

Apply Workflow naming convention for the output filename:
- Format: `{NN}-{MM}-PLAN.md` (e.g., `04-01-PLAN.md`)
- NEVER use `PLAN-01.md`, `plan-01.md`, or any other format
- NN = phase number (zero-padded), MM = plan number within the phase (zero-padded)

Determine the target directory by querying `init.phase-op` for the phase number extracted in `plan_read_input`. This ensures the `project_code` prefix from `.planning/config.json` is applied:

```bash
INIT=$(workflow_run query init.phase-op "{NN}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
expected_phase_dir=$(echo "$INIT" | node -e "process.stdout.write(JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')).expected_phase_dir)")
```

If the directory does not exist, create it:
```bash
mkdir -p "${expected_phase_dir}"
```

Set `phase_dir="${expected_phase_dir}"` for use in subsequent steps.

Write the PLAN.md file to the target directory.

</step>

<step name="plan_validate">

Delegate validation to plan-checker:

Print: "Delegating to plan-checker (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)"

```bash
CHECKER_MODEL=$(workflow_run query resolve-model plan-checker --raw)
```

<!-- #2508 runtime-aware-dispatch -->

> **Runtime-aware dispatch (#2508 Phase 4).** Workflow workflows dispatch specialized subagents by role. Before dispatching on a built-in-only runtime (kimi-code — three built-ins only), resolve the role to a built-in via `workflow_run query resolve-dispatch-type --requested <role> --raw`. On named-dispatch runtimes (Claude/OpenCode/…) the role is returned unchanged; on kimi-code it maps to `coder`/`explore`/`plan` by role-suffix. The persona rides `${AGENT_SKILLS_<ROLE>}` (Phase 3) regardless. See @.ai/library/references/runtime-aware-dispatch.md.

<!-- #2517 model-omit-on-inherit -->

> **Model omission (#2517).** Omit the `model` parameter entirely when the value it would carry (`CHECKER_MODEL`) is `"inherit"` or empty. An empty value 404s on runtimes without native tier aliases — the default on non-Claude runtimes. Omitting it inherits the orchestrator's model. See @.ai/library/references/model-profile-resolution.md.

```
Agent({
  subagent_type: "plan-checker",
  model: "{CHECKER_MODEL}",
  prompt: "Validate: ${phase_dir}/{plan}-PLAN.md — check frontmatter completeness, task structure, and Workflow conventions. Report any issues."
})
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

Handle the checker return by severity, never by the sentinel alone: count BLOCKER + WARNING entries in the YAML issues block; an entry whose severity is missing or unrecognized counts as a BLOCKER (fail closed). If the return is `## VERIFICATION PASSED`, or the count is zero — every entry is explicitly INFO — display `ℹ advisory — {dimension}: {description}` per INFO entry and treat the plan as imported; INFO is advisory and never blocks an import (#3724). Otherwise:
- Display the blocking issues to the user
- Ask the user to resolve issues before the plan is considered imported
- Do not delete the written file — the user can fix and re-validate manually

If the checker returns clean:
- Display: "Plan validation passed"

</step>

<step name="plan_finalize">

Update `.planning/ROADMAP.md` to reflect the new plan:
- Add the plan to the Plans list under the correct phase section
- Include the plan name and description

Update `.planning/STATE.md` if appropriate (e.g., increment total plan count).

Commit the imported plan and updated files:
```bash
workflow_run query commit "docs({phase}): import plan from {basename FILEPATH}" --files .planning/phases/{phase}/{plan}-PLAN.md .planning/ROADMAP.md
```

Display completion:
```
### Workflow ► IMPORT COMPLETE
```

Show: plan filename written, phase directory, validation result, next steps.

</step>

---

## Anti-Patterns

Do NOT:
- Violate the shared conflict-engine contract in `.ai/library/references/doc-conflict-engine.md` (no markdown tables, no new severity labels, no bypass of the BLOCKER gate)
- Write PLAN.md files as `PLAN-01.md` or `plan-01.md` — always use `{NN}-{MM}-PLAN.md`
- Use `pbr:plan-checker` or `pbr:planner` — use `plan-checker` and `planner`
- Write `.planning/.active-skill` — this is a PBR pattern with no Workflow equivalent
- Reference `pbr-tools`, `pbr:`, or `PLAN-BUILD-RUN` anywhere
- Write any PLAN.md file when blockers exist — the safety gate must hold
- Skip path validation on the --from file argument


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
