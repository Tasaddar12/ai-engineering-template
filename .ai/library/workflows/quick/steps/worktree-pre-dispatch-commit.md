**Step 5.6: Pre-dispatch plan commit (worktree mode only)**

When `USE_WORKTREES !== "false"`, commit PLAN.md to the current branch **before** spawning the executor. This ensures the worktree inherits PLAN.md at its branch HEAD so the executor can read it via a worktree-rooted path — avoiding the main-repo path priming that triggers CC #36182 path-resolution drift.

Skip this step entirely if `USE_WORKTREES === "false"` (non-worktree mode: PLAN.md is committed in Step 8 as usual).

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
QUICK_PLAN_PARENT=""
QUICK_PLAN_COMMIT=""
if [ "${USE_WORKTREES}" != "false" ]; then
  QUICK_PLAN_PARENT=$(git rev-parse HEAD)
  COMMIT_DOCS=$(workflow_run query config-get commit_docs --raw 2>/dev/null || echo "true")
  if [ "$COMMIT_DOCS" != "false" ]; then
    git add "${QUICK_DIR}/${quick_id}-PLAN.md"
    # No-op skip if nothing actually staged (idempotent re-runs).
    if git diff --cached --quiet -- "${QUICK_DIR}/${quick_id}-PLAN.md"; then
      echo "ℹ Pre-dispatch PLAN.md commit skipped (no staged changes)"
    else
      # Run hooks normally (#2924). If a project opts out via
      # workflow.worktree_skip_hooks=true, honor that opt-in only.
      SKIP_HOOKS=$(workflow_run query config-get workflow.worktree_skip_hooks --raw 2>/dev/null || echo "false")
      if [ "$SKIP_HOOKS" = "true" ]; then
        git commit --no-verify -m "docs(${quick_id}): pre-dispatch plan for ${DESCRIPTION}" -- "${QUICK_DIR}/${quick_id}-PLAN.md" \
          || { echo "ERROR: pre-dispatch PLAN.md commit failed (--no-verify path). Aborting before executor dispatch." >&2; exit 1; }
      else
        git commit -m "docs(${quick_id}): pre-dispatch plan for ${DESCRIPTION}" -- "${QUICK_DIR}/${quick_id}-PLAN.md" \
          || { echo "ERROR: pre-dispatch PLAN.md commit failed — likely a pre-commit hook failure. Fix the hook output above (or set workflow.worktree_skip_hooks=true to bypass) and re-run." >&2; exit 1; }
      fi
      QUICK_PLAN_COMMIT=$(git rev-parse HEAD)
    fi
  fi
  if [ -z "$QUICK_PLAN_COMMIT" ]; then
    QUICK_PLAN_COMMIT=$(git rev-parse HEAD)
  fi
fi
```


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
