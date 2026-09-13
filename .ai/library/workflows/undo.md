<purpose>
Safe git revert workflow. Rolls back Workflow phase or plan commits using the phase manifest with dependency checks and a confirmation gate. Uses git revert --no-commit (NEVER git reset) to preserve history.
</purpose>

<required_reading>
@.ai/library/references/ui-brand.md
@.ai/library/references/gate-prompts.md
</required_reading>

<process>
```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(workflow_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

<step name="banner" priority="first">
Display the stage banner:

```
### Workflow ► UNDO
```
</step>

<step name="parse_arguments">
Parse $ARGUMENTS for the undo mode:

- `--last N` → MODE=last, COUNT=N (integer, default 10 if N missing)
- `--phase NN` → MODE=phase, TARGET_PHASE=NN (two-digit phase number)
- `--plan NN-MM` → MODE=plan, TARGET_PLAN=NN-MM (phase-plan ID)

If no valid argument is provided, display usage and exit:

```
Usage: /workflow:undo --last N | --phase NN | --plan NN-MM

Modes:
  --last N      Show last N Workflow commits for interactive selection
  --phase NN    Revert all commits for phase NN
  --plan NN-MM  Revert all commits for plan NN-MM

Examples:
  /workflow:undo --last 5
  /workflow:undo --phase 03
  /workflow:undo --plan 03-02
```
</step>

<step name="gather_commits">
Based on MODE, gather candidate commits.

**MODE=last:**

Run:
```bash
git log --oneline --no-merges -${COUNT}
```

Filter for Workflow conventional commits matching `type(scope): message` pattern (e.g., `feat(04-01):`, `docs(03):`, `fix(02-03):`).

Display a numbered list of matching commits:
```
Recent Workflow commits:
  1. abc1234 feat(04-01): implement auth endpoint
  2. def5678 docs(03-02): complete plan summary
  3. ghi9012 fix(02-03): correct validation logic
```

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
Use AskUserQuestion to ask:
- question: "Which commits to revert? Enter numbers (e.g., 1,3) or 'all'"
- header: "Select"

Parse the user's selection into COMMITS list.

---

**MODE=phase:**

Read `.planning/.phase-manifest.json` if it exists.

If the file exists and `manifest.phases?.[TARGET_PHASE]?.commits` is a non-empty array:
  - Use `manifest.phases[TARGET_PHASE].commits` entries as COMMITS (each entry is a commit hash)

If the file does not exist, or `manifest.phases?.[TARGET_PHASE]` is missing:
  - Display: "Manifest has no entry for phase ${TARGET_PHASE} (or file missing), falling back to git log search"
  - Fallback: run git log and filter for the target phase scope:
    ```bash
    git log --oneline --no-merges --all | grep -E "\(0*${TARGET_PHASE}(-[0-9]+)?\):" | head -50
    ```
  - Use matching commits as COMMITS

---

**MODE=plan:**

Run:
```bash
git log --oneline --no-merges --all | grep -E "\(${TARGET_PLAN}\)" | head -50
```

Use matching commits as COMMITS.

---

**Empty check:**

If COMMITS is empty after gathering:
```
No commits found for ${MODE} ${TARGET}. Nothing to revert.
```
Exit cleanly.
</step>

<step name="dependency_check">
**Applies when MODE=phase or MODE=plan.**

Skip this step entirely for MODE=last.

---

**MODE=phase:**

Read `.planning/ROADMAP.md` inline.

Search for phases that list a dependency on the target phase. Look for patterns like:
- "Depends on: Phase ${TARGET_PHASE}"
- "Depends on: ${TARGET_PHASE}"
- "depends_on: [${TARGET_PHASE}]"

For each dependent phase N found:
1. Check if `.planning/phases/${N}-*/` directory exists
2. If directory exists, check for any PLAN.md or SUMMARY.md files inside it

If any downstream phase has started work, collect warnings:
```
⚠  Downstream dependency detected:
   Phase ${N} depends on Phase ${TARGET_PHASE} and has started work.
```

---

**MODE=plan:**

Extract the phase number from TARGET_PLAN (the NN part of NN-MM). Extract the plan number (the MM part).

Look for later plans in the same phase directory (`.planning/phases/${NN}-*/`). For each later plan (plans with number > MM):
1. Read the later plan's PLAN.md
2. Check if its `<files>` sections or `consumes` fields reference outputs from the target plan

If any later plan references the target plan's outputs, collect warnings:
```
⚠  Intra-phase dependency detected:
   Plan ${LATER_PLAN} in phase ${NN} references outputs from plan ${TARGET_PLAN}.
```

---

If any warnings exist (from either mode):
- Display all warnings
- Use AskUserQuestion with approve-revise-abort pattern:
  - question: "Downstream work depends on the target being reverted. Proceed anyway?"
  - header: "Confirm"
  - options: Proceed | Abort

If user selects "Abort": exit with "Revert cancelled. No changes made."
</step>

<step name="confirm_revert">
Display the confirmation gate using approve-revise-abort pattern from gate-prompts.md.

Show:
```
The following commits will be reverted (in reverse chronological order):

  {hash} — {message}
  {hash} — {message}
  ...

Total: {N} commit(s) to revert
```

Use AskUserQuestion:
- question: "Proceed with revert?"
- header: "Approve?"
- options: Approve | Abort

If "Abort": display "Revert cancelled. No changes made." and exit.
If "Approve": ask for a reason:

```
AskUserQuestion(
  header: "Reason",
  question: "Brief reason for the revert (used in commit message):",
  options: []
)
```

Store the response as REVERT_REASON. Continue to execute_revert.
</step>

<step name="execute_revert">
**HARD CONSTRAINT: Use git revert --no-commit. NEVER use git reset (except for conflict cleanup as documented below).**

**Dirty-tree guard (run first, before any revert):**

Run `git status --porcelain`. If the output is non-empty, display the dirty files and abort:
```
Working tree has uncommitted changes. Commit or stash them before running /workflow:undo.
```
Exit immediately — do not proceed to any revert operations.

---

Sort COMMITS in reverse chronological order (newest first). If commits came from git log (already newest-first), they are already in correct order.

For each commit hash in COMMITS:
```bash
git revert --no-commit ${HASH}
```

If any revert fails (merge conflict or error):
1. Display the error message
2. Run cleanup — handle both first-call and mid-sequence cases:
   ```bash
   # Try git revert --abort first (works if this is the first failed revert)
   git revert --abort 2>/dev/null
   # If prior --no-commit reverts already staged cleanly before this failure,
   # revert --abort may be a no-op. Clean up staged and working tree changes:
   git reset HEAD 2>/dev/null
   git restore . 2>/dev/null
   ```
3. Display:
   ```
### ERROR

   Revert failed on commit ${HASH}.
   Likely cause: merge conflict with subsequent changes.

   **To fix:** Resolve the conflict manually or revert commits individually.
   All pending reverts have been aborted — working tree is clean.
   ```
4. Exit with error.

After all reverts are staged successfully, create a single commit:

For MODE=phase:
```bash
git commit -m "revert(${TARGET_PHASE}): undo phase ${TARGET_PHASE} — ${REVERT_REASON}"
```

For MODE=plan:
```bash
git commit -m "revert(${TARGET_PLAN}): undo plan ${TARGET_PLAN} — ${REVERT_REASON}"
```

For MODE=last:
```bash
git commit -m "revert: undo ${N} selected commits — ${REVERT_REASON}"
```
</step>

<step name="summary">
Display the completion banner:

```
### Workflow ► UNDO COMPLETE ✓
```

Show summary:
```
  ✓ ${N} commit(s) reverted
  ✓ Single revert commit created: ${REVERT_HASH}
```

Show next steps:
```
---

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Review state** — verify project is in expected state after revert

/clear then:

/workflow:progress

---

**Also available:**
- `/workflow:execute-phase ${PHASE}` — re-execute if needed
- `/workflow:undo --last 1` — undo the revert itself if something went wrong

---
```
</step>

</process>

<success_criteria>
- [ ] Arguments parsed correctly for all three modes
- [ ] --phase mode reads .planning/.phase-manifest.json using manifest.phases[TARGET_PHASE].commits
- [ ] --phase mode falls back to git log if manifest entry missing
- [ ] Dependency check warns when downstream phases have started (MODE=phase)
- [ ] Dependency check warns when later plans reference target plan outputs (MODE=plan)
- [ ] Dirty-tree guard aborts if working tree has uncommitted changes
- [ ] Confirmation gate shown before any revert execution
- [ ] Reverts use git revert --no-commit in reverse chronological order
- [ ] Single commit created after all reverts staged
- [ ] Error handling cleans up both first-call and mid-sequence conflict cases
- [ ] git reset --hard is NEVER used anywhere in this workflow
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
