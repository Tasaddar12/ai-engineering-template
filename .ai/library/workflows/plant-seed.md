<purpose>
Capture a forward-looking idea as a structured seed file with trigger conditions.
Seeds auto-surface during /workflow:new-milestone when trigger conditions match the
new milestone's scope.

Seeds beat deferred items because they:
- Preserve WHY the idea matters (not just WHAT)
- Define WHEN to surface (trigger conditions, not manual scanning)
- Track breadcrumbs (code references, related decisions)
- Auto-present at the right time via new-milestone scan

**One-shot capture**: the seed file is written immediately from the idea text alone.
Trigger / Why / Scope are optional enrichment — they can be provided now or added
later. The file is never gated behind questions.
</purpose>

<process>

<step name="parse-idea">
Parse `$ARGUMENTS` for the idea summary.

First, check for an enrich flag:

```bash
if echo "$ARGUMENTS" | grep -qE '\-\-enrich[[:space:]]+SEED-[0-9]+'; then
  ENRICH_TARGET=$(echo "$ARGUMENTS" | grep -oE 'SEED-[0-9]+')
  SEED_FILE=$(ls .planning/seeds/${ENRICH_TARGET}-*.md 2>/dev/null | head -1)
  # Skip to enrich-seed step — do not prompt for $IDEA
else
  if [ -n "$ARGUMENTS" ]; then
    IDEA="$ARGUMENTS"
  else
    # Ask only when no arguments at all
    # What's the idea? (one sentence)
    IDEA="<user response>"
  fi
fi
```

If `$ENRICH_TARGET` is set, skip straight to the `enrich-seed` step. Do not set `$IDEA` and do not run `create-seed-dir`, `generate-seed-id`, `write-seed`, `collect-breadcrumbs`, `commit-seed`, or `confirm`.

If `$ARGUMENTS` is non-empty and contains no `--enrich` flag, treat the full value as `$IDEA` (no prompt).

Only prompt for the idea when `$ARGUMENTS` is empty and no enrich target is present. Store the response as `$IDEA`.
</step>

<step name="create-seed-dir">
```bash
mkdir -p .planning/seeds
```
</step>

<step name="generate-seed-id">
```bash
# Find next seed number
EXISTING=$( (ls .planning/seeds/SEED-*.md 2>/dev/null || true) | wc -l )
NEXT=$((EXISTING + 1))
PADDED=$(printf "%03d" $NEXT)
```

Generate slug from idea summary.
</step>

<step name="write-seed">
Write `.planning/seeds/SEED-{PADDED}-{slug}.md` immediately with sensible defaults:

- `trigger_when`: default is `"when relevant"` — the seed will surface during any
  new-milestone scan; the user can narrow it later via `--enrich`
- `scope`: default is `"unknown"` — the user can update it via `--enrich`

```markdown
---
id: SEED-{PADDED}
status: dormant
planted: {ISO date}
planted_during: {current milestone/phase from STATE.md, or "unknown" if not in a Workflow project}
trigger_when: when relevant
scope: unknown
---

# SEED-{PADDED}: {$IDEA}

## Why This Matters

_To be filled in. Run `/workflow:capture --seed --enrich SEED-{PADDED}` to add context._

## When to Surface

**Trigger:** when relevant

This seed will surface during `/workflow:new-milestone` when the milestone scope matches.

## Scope Estimate

**Unknown** — run `/workflow:capture --seed --enrich SEED-{PADDED}` to estimate effort.

## Breadcrumbs

_No breadcrumbs collected yet._

## Notes

_Captured via one-shot seed capture. Enrich with trigger, why, and scope at your convenience._
```
</step>

<step name="collect-breadcrumbs">
After writing the file, search the codebase for relevant references:

Extract one or two key terms from `$IDEA` (the most distinctive noun or phrase) and store as `$KEYWORD`.

```bash
# Derive a single keyword for breadcrumb search.
# Lower-case, strip punctuation, take the first token longer than 2 chars.
KEYWORD=$(printf '%s' "$IDEA" \
  | tr '[:upper:]' '[:lower:]' \
  | tr -cs 'a-z0-9' '\n' \
  | awk 'length > 2 {print; exit}')
KEYWORD="${KEYWORD:-seed}"  # fallback to literal "seed" if extraction yields nothing
```

```bash
# Find files related to the idea keywords ($KEYWORD derived from $IDEA)
grep -rl "$KEYWORD" --include="*.ts" --include="*.js" --include="*.md" . 2>/dev/null | head -10
```

Also check:
- Current STATE.md for related decisions
- ROADMAP.md for related phases
- todos/ for related captured ideas

If any breadcrumbs are found, update the Breadcrumbs section of the seed file.
Store relevant file paths as `$BREADCRUMBS`.
</step>

<step name="commit-seed">
```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(workflow_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
workflow_run query commit "docs: plant seed — {$IDEA}" --files .planning/seeds/SEED-{PADDED}-{slug}.md
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.
</step>

<step name="confirm">
```text
✅ Seed planted: SEED-{PADDED}

"{$IDEA}"
File: .planning/seeds/SEED-{PADDED}-{slug}.md

Trigger and scope are set to defaults. Run `/workflow:capture --seed --enrich SEED-{PADDED}`
to add trigger conditions, rationale, and scope estimate at your convenience.

This seed will surface automatically when you run /workflow:new-milestone.
```
</step>

<step name="enrich-seed">
**Optional enrichment — only run this step when `--enrich` flag is present.**

If `--enrich` flag is in `$ARGUMENTS`:
- `$ENRICH_TARGET` and `$SEED_FILE` are already set by `parse-idea`. Derive `$SEED_ID` from `$ENRICH_TARGET` (e.g. `SEED_ID="$ENRICH_TARGET"`). If `$SEED_FILE` is empty, fall back to the most-recently modified file in `.planning/seeds/` and set `$SEED_ID` from its filename.
- Ask focused questions to build a complete seed:


**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.

```text
AskUserQuestion(
  header: "Trigger",
  question: "When should this idea surface? (e.g., 'when we add user accounts', 'next major version', 'when performance becomes a priority')",
  options: []  // freeform
)
```

Store as `$TRIGGER`.

```text
AskUserQuestion(
  header: "Why",
  question: "Why does this matter? What problem does it solve or what opportunity does it create?",
  options: []
)
```

Store as `$WHY`.

```text
AskUserQuestion(
  header: "Scope",
  question: "How big is this? (rough estimate)",
  options: [
    { label: "Small", description: "A few hours — could be a quick task" },
    { label: "Medium", description: "A phase or two — needs planning" },
    { label: "Large", description: "A full milestone — significant effort" }
  ]
)
```

Store as `$SCOPE`.

Update the seed file's frontmatter and sections with the gathered values:
- Set `trigger_when: {$TRIGGER}`
- Set `scope: {$SCOPE}`
- Fill in `## Why This Matters` with `{$WHY}`
- Fill in `## When to Surface` trigger detail
- Fill in `## Scope Estimate` elaboration

Commit the update:
```bash
workflow_run query commit "docs: enrich seed ${SEED_ID} — trigger + why + scope" --files "$SEED_FILE"
```

Confirm:
```text
✅ Seed enriched: ${SEED_ID}
Trigger: {$TRIGGER}
Scope: {$SCOPE}
```
</step>

</process>

<success_criteria>
- [ ] Seed file created in .planning/seeds/ in one step, no questions required
- [ ] Frontmatter includes status, trigger_when (default: "when relevant"), scope (default: "unknown")
- [ ] File is written BEFORE any optional enrichment questions are asked
- [ ] Committed to git
- [ ] User shown confirmation with file path
- [ ] Optional --enrich path available for adding trigger, why, scope post-capture
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
