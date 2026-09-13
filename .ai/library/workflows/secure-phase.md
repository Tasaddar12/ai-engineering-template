<purpose>
Verify threat mitigations for a completed phase. Confirm PLAN.md threat register dispositions are resolved. Update SECURITY.md.
</purpose>

<required_reading>
@.ai/library/references/ui-brand.md
</required_reading>

<available_agent_types>
Valid Workflow subagent types (use exact names — do not fall back to 'general-purpose'):
- security-auditor — Verifies threat mitigation coverage
</available_agent_types>

<process>

## 0. Initialize

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(workflow_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
INIT=$(workflow_run query init.phase-op "${PHASE_ARG}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_AUDITOR=$(workflow_run query agent-skills security-auditor)
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

Parse: `phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `padded_phase`.

```bash
AUDITOR_MODEL=$(workflow_run query resolve-model security-auditor --raw)
VERIFY_POST_HOOKS_JSON=$(workflow_run loop render-hooks verify:post --raw)
SECURITY_ASVS=$(workflow_run query config-get workflow.security_asvs_level --raw 2>/dev/null || echo "1")
SECURITY_BLOCK_ON=$(workflow_run query config-get workflow.security_block_on --raw 2>/dev/null || echo "high")
```

Resolve active step hooks from `VERIFY_POST_HOOKS_JSON` where `kind == "step"` and `ref.skill == "secure-phase"`.

If no active secure-phase step hook exists: exit with "Security enforcement disabled. Enable via /workflow:settings."

Display banner: `Workflow > SECURE PHASE {N}: {name}`

## 1. Detect Input State

```bash
SECURITY_FILE=$(ls "${PHASE_DIR}"/*-SECURITY.md 2>/dev/null | head -1)
PLAN_FILES=$(ls "${PHASE_DIR}"/*-PLAN.md 2>/dev/null)
SUMMARY_FILES=$(ls "${PHASE_DIR}"/*-SUMMARY.md 2>/dev/null)
```

- **State A** (`SECURITY_FILE` non-empty): Audit existing
- **State B** (`SECURITY_FILE` empty, `PLAN_FILES` and `SUMMARY_FILES` non-empty): Run from artifacts
- **State C** (`SUMMARY_FILES` empty): Exit — "Phase {N} not executed. Run /workflow:execute-phase {N} first."

## 2. Discovery

### 2a. Read Phase Artifacts

Read PLAN.md — extract `<threat_model>` block: trust boundaries, STRIDE register (`threat_id`, `category`, `component`, `severity`, `disposition`, `mitigation_plan`).

### 2b. Read Summary Threat Flags

Read SUMMARY.md — extract `## Threat Flags` entries.

### 2c. Build Threat Register

Per threat: `{ threat_id, category, component, severity, disposition, mitigation_pattern, files_to_check }`

Also set `register_authored_at_plan_time: true` if **at least one** PLAN file contained a parseable `<threat_model>` block; `false` if no PLAN files had any `<threat_model>` block (legacy phase authored before formal threat modelling was standard).

## 3. Threat Classification

Classify each threat:

| Status | Criteria |
|--------|----------|
| CLOSED | mitigation found OR accepted risk documented in SECURITY.md OR transfer documented |
| OPEN | none of the above |

Build: `{ threat_id, category, component, severity, disposition, status, evidence }`

**Short-circuit rule:**
- If `threats_open: 0 AND register_authored_at_plan_time: true AND asvs_level == 1` → skip to Step 6 directly. No open threats at or above the block threshold remain (threats_open: 0); below-threshold open threats may remain and are non-blocking. L1 grep-depth is sufficient; no deeper verification required.
- If `threats_open: 0 AND register_authored_at_plan_time: true AND asvs_level >= 2` → **do NOT skip**. The preliminary threat classification is grep-level (L1 depth) and is insufficient for L2/L3. Proceed to Step 5 (spawn the auditor) so that L2 boundary-placement checks and L3 end-to-end trace checks are performed. Skipping the auditor here would defeat ASVS level scaling for "clean" phases.
- If `threats_open: 0 AND register_authored_at_plan_time: false` → **do NOT skip**. Empty-by-no-planning must not rubber-stamp a clean SECURITY.md. Proceed to Step 5 in **retroactive-STRIDE mode** — the auditor builds a register from implementation files first, then verifies mitigations.
- If `threats_open > 0` → proceed to Step 4 (present threat plan to user).

## 4. Present Threat Plan

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
Call AskUserQuestion with threat table and options:
1. "Verify all open threats" → Step 5
2. "Accept all open — document in accepted risks log" → add to SECURITY.md accepted risks, set all CLOSED, Step 6
3. "Cancel" → exit

## 5. Spawn security-auditor

**Auditor constraint — varies by register origin:**

- `register_authored_at_plan_time: true` — **Verify mitigations exist** — do not scan for new threats. The register is complete; verify each threat's mitigation is present in the implementation.
- `register_authored_at_plan_time: false` (retroactive-STRIDE mode) — **Retroactive-STRIDE: build a STRIDE register from implementation files first, then verify mitigations.** The phase was authored before formal threat modelling; the auditor must construct the register from scratch before verifying.

Substitute `{SECURITY_ASVS}` with the value of `$SECURITY_ASVS` and `{SECURITY_BLOCK_ON}` with the value of `$SECURITY_BLOCK_ON` resolved in Step 0 via `config-get`.

Print: `◆ Spawning security auditor... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)`

<!-- #2508 runtime-aware-dispatch -->

> **Runtime-aware dispatch (#2508 Phase 4).** Workflow workflows dispatch specialized subagents by role. Before dispatching on a built-in-only runtime (kimi-code — three built-ins only), resolve the role to a built-in via `workflow_run query resolve-dispatch-type --requested <role> --raw`. On named-dispatch runtimes (Claude/OpenCode/…) the role is returned unchanged; on kimi-code it maps to `coder`/`explore`/`plan` by role-suffix. The persona rides `${AGENT_SKILLS_<ROLE>}` (Phase 3) regardless. See @.ai/library/references/runtime-aware-dispatch.md.

<!-- #2517 model-omit-on-inherit -->

> **Model omission (#2517).** Omit the `model` parameter entirely when the value it would carry (`AUDITOR_MODEL`) is `"inherit"` or empty. An empty value 404s on runtimes without native tier aliases — the default on non-Claude runtimes. Omitting it inherits the orchestrator's model. See @.ai/library/references/model-profile-resolution.md.

```
Agent(
  prompt="Read .ai/library/agents/security-auditor.md for instructions.\n\n" +
    "<required_reading>{PLAN, SUMMARY, impl files, SECURITY.md}</required_reading>" +
    "<threat_register>{threat register}</threat_register>" +
    "<config>asvs_level: {SECURITY_ASVS}, block_on: {SECURITY_BLOCK_ON}</config>" +
    "<constraints>Never modify implementation files. Verify mitigations exist — do not scan for new threats. Escalate implementation gaps. Return a structured verdict only — do NOT write SECURITY.md (the orchestrator owns the file write).</constraints>" +
    "${AGENT_SKILLS_AUDITOR}",
  subagent_type="security-auditor",
  model="{AUDITOR_MODEL}",
  description="Verify threat mitigations for Phase {N}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

Handle return:
- `## SECURED` → record closures → Step 6
- `## OPEN_THREATS` → record closed + open, present user with accept/block choice → Step 6
- `## ESCALATE` → present to user → Step 6

## 6. Write/Update SECURITY.md

**State B (create):**
1. Read template from `.ai/templates/SECURITY.md`
2. Fill: frontmatter, threat register, accepted risks, audit trail
3. Write to `${PHASE_DIR}/${PADDED_PHASE}-SECURITY.md`

**State A (update):**
1. Update threat register statuses, append to audit trail:

```markdown
## Security Audit {date}
| Metric | Count |
|--------|-------|
| Threats found | {N} |
| Closed | {M} |
| Open | {K} |
```

**ENFORCING GATE:** If `threats_open > 0` after all options exhausted (user did not accept, not all verified closed):

```
Workflow > PHASE {N} SECURITY BLOCKED
{K} blocking threats open — phase advancement blocked until threats_open: 0
▶ Fix mitigations then re-run: /workflow:secure-phase {N}
▶ Or document accepted risks in SECURITY.md and re-run.
```

Do NOT emit next-phase routing. Stop here.

## 7. Commit

```bash
workflow_run query commit "docs(phase-${PHASE}): add/update security threat verification" \
  --files "${PHASE_DIR}/${PADDED_PHASE}-SECURITY.md"
```

## 8. Results + Routing

**Secured (threats_open: 0):**
```
Workflow > PHASE {N} THREAT-SECURE
threats_open: 0 — no blocking threats remain (threats_open: 0).
▶ /workflow:validate-phase {N}    validate test coverage
▶ /workflow:verify-work {N}       run UAT
```

Display `/clear` reminder.

</process>

<success_criteria>
- [ ] Security enforcement checked — exit if false
- [ ] Input state detected (A/B/C) — state C exits cleanly
- [ ] PLAN.md threat model parsed, register built
- [ ] SUMMARY.md threat flags incorporated
- [ ] threats_open: 0 AND register_authored_at_plan_time: true AND asvs_level == 1 → skip directly to Step 6 (L1 grep-depth sufficient)
- [ ] threats_open: 0 AND register_authored_at_plan_time: true AND asvs_level >= 2 → do NOT skip; auditor spawned for L2/L3 deep verification
- [ ] threats_open: 0 AND register_authored_at_plan_time: false → retroactive-STRIDE mode (Step 5), not skipped
- [ ] User gate with threat table presented
- [ ] Auditor spawned with complete context
- [ ] All three return formats (SECURED/OPEN_THREATS/ESCALATE) handled
- [ ] SECURITY.md created or updated
- [ ] threats_open > 0 BLOCKS advancement (no next-phase routing emitted)
- [ ] Results with routing presented on success
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
