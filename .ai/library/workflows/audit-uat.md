@.ai/library/references/response-language-directive.md

<purpose>
Cross-phase audit of all UAT and verification files. Finds every outstanding item (pending, skipped, blocked, human_needed), optionally verifies against the codebase to detect stale docs, and produces a prioritized human test plan.
</purpose>

<process>

<step name="initialize">
Run the CLI audit:

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
AUDIT=$(workflow_run query audit-uat --raw)
```

Parse JSON for `results` array and `summary` object.

If `summary.total_items` is 0 AND `summary.parse_gap_files` is 0:
```
## All Clear

No outstanding UAT or verification items found across all phases.
All tests are passing, resolved, or diagnosed with fix plans.
```
Stop here.

If `summary.total_items` is 0 but `summary.parse_gap_files` is greater than 0, this is NOT all-clear — one or more files have test blocks that could not be parsed and may be hiding outstanding work. Continue to the `categorize` and `present` steps below; `present` renders the Unparsed section from these `parse_gap: true` entries even though `items` is empty for a mixed project.
</step>

<step name="categorize">
Group items by what's actionable NOW vs. what needs prerequisites:

**Testable Now** (no external dependencies):
- `pending` — tests never run
- `human_uat` — human verification items
- `skipped_unresolved` — skipped without clear blocking reason

**Needs Prerequisites:**
- `server_blocked` — needs external server running
- `device_needed` — needs physical device (not simulator)
- `build_needed` — needs release/preview build
- `third_party` — needs external service configuration

For each item in "Testable Now", use Grep/Read to check if the underlying feature still exists in the codebase:
- If the test references a component/function that no longer exists → mark as `stale`
- If the test references code that has been significantly rewritten → mark as `needs_update`
- Otherwise → mark as `active`
</step>

<step name="present">
If `summary.parse_gap_files` is greater than 0, render this section FIRST (before the `## UAT Audit Report` below, or standalone if `total_items` is also 0). Filter `results` for entries with `parse_gap: true`:
```
## Unparsed UAT Files ({parse_gap_files} files)

| Phase | File | Unparsed Blocks |
|-------|------|------------------|
| {phase} | {file_path} | {unparsed_blocks} |
...

These files have `### N.` test blocks with no readable `result:` line. Fix the file's structure, then re-run the audit.
```
This fires for ANY project with `parse_gap_files > 0`, including a mixed project where other phases also have real outstanding `items` — the two sections are not mutually exclusive. An outstanding item does not stop mattering because its phase belongs to an already-archived milestone (a deferred human-UAT scenario or a `skipped` live-stack test is exactly what gets archived still-open), so an archived phase's parse gap is listed in this same table, unfiltered by `archived_milestone`. If `total_items` is 0, stop after this section (there is no `## UAT Audit Report` to present). Otherwise continue below.

Present the audit report:

```
## UAT Audit Report

**{total_items} outstanding items across {total_files} files in {phase_count} phases**

### Testable Now ({count})

| # | Phase | Test | Description | Status |
|---|-------|------|-------------|--------|
| 1 | {phase} | {test_name} | {expected} | {active/stale/needs_update} |
...

### Needs Prerequisites ({count})

| # | Phase | Test | Blocked By | Description |
|---|-------|------|------------|-------------|
| 1 | {phase} | {test_name} | {category} | {expected} |
...

### Stale (can be closed) ({count})

| # | Phase | Test | Why Stale |
|---|-------|------|-----------|
| 1 | {phase} | {test_name} | {reason} |
...

---

## Recommended Actions

1. **Close stale items:** `/workflow:verify-work {phase}` — mark stale tests as resolved
2. **Run active tests:** Human UAT test plan below
3. **When prerequisites met:** Retest blocked items with `/workflow:verify-work {phase}`
```
</step>

<step name="test_plan">
Generate a human UAT test plan for "Testable Now" + "active" items only:

Group by what can be tested together (same screen, same feature, same prerequisite):

```
## Human UAT Test Plan

### Group 1: {category — e.g., "Billing Flow"}
Prerequisites: {what needs to be running/configured}

1. **{Test name}** (Phase {N})
   - Navigate to: {where}
   - Do: {action}
   - Expected: {expected behavior}

2. **{Test name}** (Phase {N})
   ...

### Group 2: {category}
...
```
</step>

</process>


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
