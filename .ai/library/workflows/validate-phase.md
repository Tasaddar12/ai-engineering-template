<purpose>
Audit Nyquist validation gaps for a completed phase. Generate missing tests. Update VALIDATION.md.
</purpose>

<required_reading>
@.ai/library/references/ui-brand.md
</required_reading>

<available_agent_types>
Valid Workflow subagent types (use exact names — do not fall back to 'general-purpose'):
- nyquist-auditor — Validates verification coverage
</available_agent_types>

<process>

## 0. Initialize

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(workflow_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
INIT=$(workflow_run query init.phase-op "${PHASE_ARG}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_AUDITOR=$(workflow_run query agent-skills nyquist-auditor)
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

Parse: `phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `padded_phase`.

```bash
AUDITOR_MODEL=$(workflow_run query resolve-model nyquist-auditor --raw)
VERIFY_POST_HOOKS_JSON=$(workflow_run loop render-hooks verify:post --raw)
```

Resolve active step hooks from `VERIFY_POST_HOOKS_JSON` where `kind == "step"` and `ref.skill == "validate-phase"`.

If no active validate-phase step hook exists: exit with "Nyquist validation is disabled. Enable via /workflow:settings."

Display banner: `Workflow > VALIDATE PHASE {N}: {name}`

## 1. Detect Input State

```bash
VALIDATION_FILE=$(ls "${PHASE_DIR}"/*-VALIDATION.md 2>/dev/null | head -1)
SUMMARY_FILES=$(ls "${PHASE_DIR}"/*-SUMMARY.md 2>/dev/null)
```

- **State A** (`VALIDATION_FILE` non-empty): Audit existing
- **State B** (`VALIDATION_FILE` empty, `SUMMARY_FILES` non-empty): Reconstruct from artifacts
- **State C** (`SUMMARY_FILES` empty): Exit — "Phase {N} not executed. Run /workflow:execute-phase {N} ${Workflow_WS} first."

## 2. Discovery

### 2a. Read Phase Artifacts

Read all PLAN and SUMMARY files. Extract: task lists, requirement IDs, key-files changed, verify blocks.

### 2b. Build Requirement-to-Task Map

Per task: `{ task_id, plan_id, wave, requirement_ids, has_automated_command }`

### 2c. Detect Test Infrastructure

State A: Parse from existing VALIDATION.md Test Infrastructure table.
State B: Filesystem scan:

```bash
find . -name "pytest.ini" -o -name "jest.config.*" -o -name "vitest.config.*" -o -name "pyproject.toml" 2>/dev/null | head -10
find . \( -name "*.test.*" -o -name "*.spec.*" -o -name "test_*" \) -not -path "*/node_modules/*" 2>/dev/null | head -40
```

### 2d. Cross-Reference

Match each requirement to existing tests by filename, imports, test descriptions. Record: requirement → test_file → status.

## 3. Gap Analysis

Classify each requirement:

| Status | Criteria |
|--------|----------|
| COVERED | Test exists, targets behavior, runs green |
| PARTIAL | Test exists, failing or incomplete |
| MISSING | No test found |

Build: `{ task_id, requirement, gap_type, suggested_test_path, suggested_command }`

No gaps → skip to Step 6, set `nyquist_compliant: true`.

## 4. Present Gap Plan

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
Call AskUserQuestion with gap table and options:
1. "Fix all gaps" → Step 5
2. "Skip — mark manual-only" → add to Manual-Only, Step 6
3. "Cancel" → exit

## 5. Spawn nyquist-auditor

Print: `◆ Spawning nyquist auditor... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)`

<!-- #2508 runtime-aware-dispatch -->

> **Runtime-aware dispatch (#2508 Phase 4).** Workflow workflows dispatch specialized subagents by role. Before dispatching on a built-in-only runtime (kimi-code — three built-ins only), resolve the role to a built-in via `workflow_run query resolve-dispatch-type --requested <role> --raw`. On named-dispatch runtimes (Claude/OpenCode/…) the role is returned unchanged; on kimi-code it maps to `coder`/`explore`/`plan` by role-suffix. The persona rides `${AGENT_SKILLS_<ROLE>}` (Phase 3) regardless. See @.ai/library/references/runtime-aware-dispatch.md.

<!-- #2517 model-omit-on-inherit -->

> **Model omission (#2517).** Omit the `model` parameter entirely when the value it would carry (`AUDITOR_MODEL`) is `"inherit"` or empty. An empty value 404s on runtimes without native tier aliases — the default on non-Claude runtimes. Omitting it inherits the orchestrator's model. See @.ai/library/references/model-profile-resolution.md.

```
Agent(
  prompt="Read .ai/library/agents/nyquist-auditor.md for instructions.\n\n" +
    "<required_reading>{PLAN, SUMMARY, impl files, VALIDATION.md}</required_reading>" +
    "<gaps>{gap list}</gaps>" +
    "<test_infrastructure>{framework, config, commands}</test_infrastructure>" +
    "<constraints>Never modify impl files. Max 3 debug iterations. Escalate impl bugs.</constraints>" +
    "${AGENT_SKILLS_AUDITOR}",
  subagent_type="nyquist-auditor",
  model="{AUDITOR_MODEL}",
  description="Fill validation gaps for Phase {N}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

Handle return:
- `## GAPS FILLED` → record tests + map updates, Step 6
- `## PARTIAL` → record resolved, move escalated to manual-only, Step 6
- `## ESCALATE` → move all to manual-only, Step 6

## 6. Generate/Update VALIDATION.md

**State B (create):**
1. Read template from `.ai/templates/VALIDATION.md`
2. Fill: frontmatter (**set `status: validated`**), Test Infrastructure, Per-Task Map, Manual-Only, Sign-Off
3. Write to `${PHASE_DIR}/${PADDED_PHASE}-VALIDATION.md`

**State A (update):**
1. Update Per-Task Map statuses, add escalated to Manual-Only, update frontmatter (**set `status: validated`**)
2. Append audit trail:

```markdown
## Validation Audit {date}
| Metric | Count |
|--------|-------|
| Gaps found | {N} |
| Resolved | {M} |
| Escalated | {K} |
```

## 7. Commit

```bash
git add {test_files}
git commit -m "test(phase-${PHASE}): add Nyquist validation tests"

workflow_run query commit "docs(phase-${PHASE}): add/update validation strategy" \
  --files "${PHASE_DIR}/${PADDED_PHASE}-VALIDATION.md"
```

## 8. Results + Routing

**Compliant:**
```
Workflow > PHASE {N} IS NYQUIST-COMPLIANT
All requirements have automated verification.
▶ Next: /workflow:audit-milestone ${Workflow_WS}
```

**Partial:**
```
Workflow > PHASE {N} VALIDATED (PARTIAL)
{M} automated, {K} manual-only.
▶ Retry: /workflow:validate-phase {N} ${Workflow_WS}
```

Display `/clear` reminder.

</process>

<success_criteria>
- [ ] Nyquist config checked (exit if disabled)
- [ ] Input state detected (A/B/C)
- [ ] State C exits cleanly
- [ ] PLAN/SUMMARY files read, requirement map built
- [ ] Test infrastructure detected
- [ ] Gaps classified (COVERED/PARTIAL/MISSING)
- [ ] User gate with gap table
- [ ] Auditor spawned with complete context
- [ ] All three return formats handled
- [ ] VALIDATION.md created or updated
- [ ] Test files committed separately
- [ ] Results with routing presented
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
