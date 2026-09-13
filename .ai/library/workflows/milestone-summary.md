@.ai/library/references/response-language-directive.md

# Milestone Summary Workflow

Generate a comprehensive, human-friendly project summary from completed milestone artifacts.
Designed for team onboarding — a new contributor can read the output and understand the entire project.

---

## Step 1: Resolve Version

```bash
VERSION="$ARGUMENTS"
```

If `$ARGUMENTS` is empty:
1. Check `.planning/STATE.md` for current milestone version
2. Check `.planning/milestones/` for the latest archived version
3. If neither found, check if `.planning/ROADMAP.md` exists (project may be mid-milestone)
4. If nothing found: error "No milestone found. Run /workflow:new-project or /workflow:new-milestone first."

Set `VERSION` to the resolved version (e.g., "1.0").

## Step 2: Locate Artifacts

Determine whether the milestone is **archived** or **current**:

**Archived milestone** (`.planning/milestones/v{VERSION}-ROADMAP.md` exists):
```
ROADMAP_PATH=".planning/milestones/v${VERSION}-ROADMAP.md"
REQUIREMENTS_PATH=".planning/milestones/v${VERSION}-REQUIREMENTS.md"
AUDIT_PATH=".planning/milestones/v${VERSION}-MILESTONE-AUDIT.md"
```

**Current/in-progress milestone** (no archive yet):
```
ROADMAP_PATH=".planning/ROADMAP.md"
REQUIREMENTS_PATH=".planning/REQUIREMENTS.md"
AUDIT_PATH=".planning/v${VERSION}-MILESTONE-AUDIT.md"
```

Note: The audit file moves to `.planning/milestones/` on archive (per `complete-milestone` workflow). Check both locations as a fallback.

**Always available:**
```
PROJECT_PATH=".planning/PROJECT.md"
RETRO_PATH=".planning/RETROSPECTIVE.md"
STATE_PATH=".planning/STATE.md"
```

Read all files that exist. Missing files are fine — the summary adapts to what's available.

## Step 3: Discover Phase Artifacts

Find all phase directories:

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
workflow_run query init.progress
```

This returns phase metadata. For each phase in the milestone scope:

- Read `{phase_dir}/{padded}-SUMMARY.md` if it exists — extract `one_liner`, `accomplishments`, `decisions`
- Read `{phase_dir}/{padded}-VERIFICATION.md` if it exists — extract status, gaps, deferred items
- Read `{phase_dir}/{padded}-CONTEXT.md` if it exists — extract key decisions from `<decisions>` section
- Read `{phase_dir}/{padded}-RESEARCH.md` if it exists — note what was researched

Track which phases have which artifacts.

**If no phase directories exist** (empty milestone or pre-build state): skip to Step 5 and generate a minimal summary noting "No phases have been executed yet." Do not error — the summary should still capture PROJECT.md and ROADMAP.md content.

## Step 4: Gather Git Statistics

Try each method in order until one succeeds:

**Method 1 — Tagged milestone** (check first):
```bash
git tag -l "v${VERSION}" | head -1
```
If the tag exists:
```bash
git log v${VERSION} --oneline | wc -l
git diff --stat $(git log --format=%H --reverse v${VERSION} | head -1)..v${VERSION}
```

**Method 2 — STATE.md date range** (if no tag):
Read STATE.md and extract the `started_at` or earliest session date. Use it as the `--since` boundary:
```bash
git log --oneline --since="<started_at_date>" | wc -l
```

**Method 3 — Earliest phase commit** (if STATE.md has no date):
Find the earliest `.planning/phases/` commit:
```bash
git log --oneline --diff-filter=A -- ".planning/phases/" | tail -1
```
Use that commit's date as the start boundary.

**Method 4 — Skip stats** (if none of the above work):
Report "Git statistics unavailable — no tag or date range could be determined." This is not an error — the summary continues without the Stats section.

Extract (when available):
- Total commits in milestone
- Files changed, insertions, deletions
- Timeline (start date → end date)
- Contributors (from git log authors)

## Step 5: Generate Summary Document

Write to `.planning/reports/MILESTONE_SUMMARY-v${VERSION}.md`:

```markdown
# Milestone v{VERSION} — Project Summary

**Generated:** {date}
**Purpose:** Team onboarding and project review

---

## 1. Project Overview

{From PROJECT.md: "What This Is", core value proposition, target users}
{If mid-milestone: note which phases are complete vs in-progress}

## 2. Architecture & Technical Decisions

{From CONTEXT.md files across phases: key technical choices}
{From SUMMARY.md decisions: patterns, libraries, frameworks chosen}
{From PROJECT.md: tech stack if documented}

Present as a bulleted list of decisions with brief rationale:
- **Decision:** {what was chosen}
  - **Why:** {rationale from CONTEXT.md}
  - **Phase:** {which phase made this decision}

## 3. Phases Delivered

| Phase | Name | Status | One-Liner |
|-------|------|--------|-----------|
{For each phase: number, name, status (complete/in-progress/planned), one_liner from SUMMARY.md}

## 4. Requirements Coverage

{From REQUIREMENTS.md: list each requirement with status}
- ✅ {Requirement met}
- ⚠️ {Requirement partially met — note gap}
- ❌ {Requirement not met — note reason}

{If MILESTONE-AUDIT.md exists: include audit verdict}

## 5. Key Decisions Log

{Aggregate from all CONTEXT.md <decisions> sections}
{Each decision with: ID, description, phase, rationale}

## 6. Tech Debt & Deferred Items

{From VERIFICATION.md files: gaps found, anti-patterns noted}
{From RETROSPECTIVE.md: lessons learned, what to improve}
{From CONTEXT.md <deferred> sections: ideas parked for later}

## 7. Getting Started

{Entry points for new contributors:}
- **Run the project:** {from PROJECT.md or SUMMARY.md}
- **Key directories:** {from codebase structure}
- **Tests:** {test command from PROJECT.md or CLAUDE.md}
- **Where to look first:** {main entry points, core modules}

---

## Stats

- **Timeline:** {start} → {end} ({duration})
- **Phases:** {count complete} / {count total}
- **Commits:** {count}
- **Files changed:** {count} (+{insertions} / -{deletions})
- **Contributors:** {list}
```

## Step 6: Write and Commit

**Overwrite guard:** If `.planning/reports/MILESTONE_SUMMARY-v${VERSION}.md` already exists, ask the user:
> "A milestone summary for v{VERSION} already exists. Overwrite it, or view the existing one?"
If "view": display existing file and skip to Step 8 (interactive mode). If "overwrite": proceed.

Create the reports directory if needed:
```bash
mkdir -p .planning/reports
```

Write the summary, then commit:
```bash
workflow_run query commit "docs(v${VERSION}): generate milestone summary for onboarding" --files \
  ".planning/reports/MILESTONE_SUMMARY-v${VERSION}.md"
```

## Step 7: Present Summary

Display the full summary document inline.

## Step 8: Offer Interactive Mode

After presenting the summary:

> "Summary written to `.planning/reports/MILESTONE_SUMMARY-v{VERSION}.md`.
>
> I have full context from the build artifacts. Want to ask anything about the project?
> Architecture decisions, specific phases, requirements, tech debt — ask away."

If the user asks questions:
- Answer from the artifacts already loaded (CONTEXT.md, SUMMARY.md, VERIFICATION.md, etc.)
- Reference specific files and decisions
- Stay grounded in what was actually built (not speculation)

If the user is done:
- Suggest next steps: `/workflow:new-milestone`, `/workflow:progress`, or sharing the summary with the team

## Step 9: Update STATE.md

```bash
workflow_run query state.record-session \
  --stopped-at "Milestone v${VERSION} summary generated" \
  --resume-file ".planning/reports/MILESTONE_SUMMARY-v${VERSION}.md"
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
