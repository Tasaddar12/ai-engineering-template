<step name="close_parent_artifacts">
**For decimal/polish phases only (X.Y pattern):** Close the feedback loop by resolving parent UAT and debug artifacts.

**Skip if** phase number has no decimal (e.g., `3`, `04`) — only applies to gap-closure phases like `4.1`, `03.1`.

**1. Detect decimal phase and derive parent:**
```bash
# Check if phase_number contains a decimal
if [[ "$PHASE_NUMBER" == *.* ]]; then
  PARENT_PHASE="${PHASE_NUMBER%%.*}"
fi
```

**2. Find parent UAT file:**
```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
PARENT_INFO=$(workflow_run query find-phase "${PARENT_PHASE}" --raw)
# Extract directory from PARENT_INFO JSON, then find UAT file in that directory
```

**If no parent UAT found:** Skip this step (gap-closure may have been triggered by VERIFICATION.md instead).

**3. Update UAT gap statuses:**

Read the parent UAT file's `## Gaps` section. For each gap entry with `status: failed`:
- Update to `status: resolved`

**4. Update UAT frontmatter:**

If all gaps now have `status: resolved`:
- Update frontmatter `status: diagnosed` → `status: resolved`
- Update frontmatter `updated:` timestamp

**5. Resolve referenced debug sessions:**

For each gap that has a `debug_session:` field:
- Read the debug session file
- Update frontmatter `status:` → `resolved`
- Update frontmatter `updated:` timestamp
- Move to resolved directory:
```bash
mkdir -p .planning/debug/resolved
mv .planning/debug/{slug}.md .planning/debug/resolved/
```

**6. Commit updated artifacts:**
```bash
workflow_run query commit "docs(phase-${PARENT_PHASE}): resolve UAT gaps and debug sessions after ${PHASE_NUMBER} gap closure" --files .planning/phases/*${PARENT_PHASE}*/*-UAT.md .planning/debug/resolved/*.md
```
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
