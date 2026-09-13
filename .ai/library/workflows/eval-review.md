<purpose>
Retroactive audit of an implemented AI phase's evaluation coverage. Standalone command that works on any Workflow-managed AI phase. Produces a scored EVAL-REVIEW.md with gap analysis and remediation plan.

Use after /workflow:execute-phase to verify that the evaluation strategy from AI-SPEC.md was actually implemented. Mirrors the pattern of /workflow:ui-review and /workflow:validate-phase.
</purpose>

<required_reading>
@.ai/library/references/ai-evals.md
</required_reading>

<process>

## 0. Initialize

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(workflow_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
INIT=$(workflow_run query init.phase-op "${PHASE_ARG}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

Parse: `phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `padded_phase`, `commit_docs`.

```bash
AUDITOR_MODEL=$(workflow_run query resolve-model eval-auditor --pick model 2>/dev/null || true)
AGENT_SKILLS_AUDITOR=$(workflow_run query agent-skills eval-auditor)
```

Display banner:
```
### Workflow ► EVAL AUDIT — PHASE {N}: {name}
```

## 1. Detect Input State

```bash
SUMMARY_FILES=$(ls "${PHASE_DIR}"/*-SUMMARY.md 2>/dev/null)
AI_SPEC_FILE=$(ls "${PHASE_DIR}"/*-AI-SPEC.md 2>/dev/null | head -1)
EVAL_REVIEW_FILE=$(ls "${PHASE_DIR}"/*-EVAL-REVIEW.md 2>/dev/null | head -1)
```

**State A** — AI-SPEC.md + SUMMARY.md exist: Full audit against spec
**State B** — SUMMARY.md exists, no AI-SPEC.md: Audit against general best practices
**State C** — No SUMMARY.md: Exit — "Phase {N} not executed. Run /workflow:execute-phase {N} first."

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
**If `EVAL_REVIEW_FILE` non-empty:** Use AskUserQuestion:
- header: "Existing Eval Review"
- question: "EVAL-REVIEW.md already exists for Phase {N}."
- options:
  - "Re-audit — run fresh audit"
  - "View — display current review and exit"

If "View": display file, exit.
If "Re-audit": continue.

**If State B (no AI-SPEC.md):** Warn:
```
No AI-SPEC.md found for Phase {N}.
Audit will evaluate against general AI eval best practices rather than a phase-specific plan.
Consider running /workflow:ai-integration-phase {N} before implementation next time.
```
Continue (non-blocking).

## 2. Gather Context Paths

Build file list for auditor:
- AI-SPEC.md (if exists — the planned eval strategy)
- All SUMMARY.md files in phase dir
- All PLAN.md files in phase dir

## 3. Spawn eval-auditor

```
◆ Spawning eval auditor... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

Build prompt:

```markdown
Read .ai/library/agents/eval-auditor.md for instructions.

<objective>
Conduct evaluation coverage audit of Phase {phase_number}: {phase_name}
{If AI-SPEC exists: "Audit against AI-SPEC.md evaluation plan."}
{If no AI-SPEC: "Audit against general AI eval best practices."}
</objective>

<required_reading>
- {summary_paths}
- {plan_paths}
- {ai_spec_path if exists}
</required_reading>

<input>
ai_spec_path: {ai_spec_path or "none"}
phase_dir: {phase_dir}
phase_number: {phase_number}
phase_name: {phase_name}
padded_phase: {padded_phase}
state: {A or B}
</input>

${AGENT_SKILLS_AUDITOR}
```

Spawn as Task with model `AUDITOR_MODEL`.

## 4. Parse Auditor Result

Read the written EVAL-REVIEW.md. Extract:
- `overall_score`
- `verdict` (PRODUCTION READY | NEEDS WORK | SIGNIFICANT GAPS | NOT IMPLEMENTED)
- `critical_gap_count`

## 5. Display Summary

```
### Workflow ► EVAL AUDIT COMPLETE — PHASE {N}: {name}

◆ Score: {overall_score}/100
◆ Verdict: {verdict}
◆ Critical Gaps: {critical_gap_count}
◆ Output: {eval_review_path}

{If PRODUCTION READY:}
  Next step: /workflow:plan-phase (next phase) or deploy

{If NEEDS WORK:}
  Address critical gaps in EVAL-REVIEW.md, then re-run /workflow:eval-review {N}

{If SIGNIFICANT GAPS or NOT IMPLEMENTED:}
  Review AI-SPEC.md evaluation plan. Critical eval dimensions are not implemented.
  Do not deploy until gaps are addressed.
```

## 6. Commit

```bash
workflow_run query commit "docs({phase_slug}): add EVAL-REVIEW.md — score {overall_score}/100 ({verdict})" --files "${EVAL_REVIEW_FILE}"
```

</process>

<success_criteria>
- [ ] Phase execution state detected correctly
- [ ] AI-SPEC.md presence handled (with or without)
- [ ] eval-auditor spawned with correct context
- [ ] EVAL-REVIEW.md written (by auditor)
- [ ] Score and verdict displayed to user
- [ ] Appropriate next steps surfaced based on verdict
- [ ] Committed if commit_docs enabled
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
