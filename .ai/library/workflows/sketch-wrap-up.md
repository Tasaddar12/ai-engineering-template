@.ai/library/references/response-language-directive.md

<purpose>
Curate sketch design findings and package them into a persistent project skill for future
UI implementation. Reads from `.planning/sketches/`, writes skill to `./.claude/skills/sketch-findings-[project]/`
(project-local) and summary to `.planning/sketches/WRAP-UP-SUMMARY.md`.
Companion to `/workflow:sketch`.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="banner">
```
### Workflow ► SKETCH WRAP-UP
```
</step>

<step name="gather">
## Gather Sketch Inventory

1. Read `.planning/sketches/MANIFEST.md` for the design direction and reference points
2. Glob `.planning/sketches/*/README.md` and parse YAML frontmatter from each
3. Check if `./.claude/skills/sketch-findings-*/SKILL.md` exists for this project
   - If yes: read its `processed_sketches` list and filter those out
   - If no: all sketches are candidates

If no unprocessed sketches exist:
```
No unprocessed sketches found in `.planning/sketches/`.
Run `/workflow:sketch` first to create design explorations.
```
Exit.

Check `commit_docs` config:
```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
COMMIT_DOCS=$(workflow_run query config-get commit_docs --raw 2>/dev/null || echo "true")
```
</step>

<step name="curate">
## Curate Sketches One-at-a-Time

Present each unprocessed sketch in ascending order. For each sketch, show:

- **Sketch number and name**
- **Design question:** from frontmatter
- **Winner:** which variant was selected (if any)
- **Tags:** from frontmatter
- **Key decisions:** summarize what was decided visually

Then ask the user:

### CHECKPOINT: Decision Required

Sketch {NNN}: {name} — Winner: Variant {X}

{key design decisions summary}

---

**→ Include / Exclude / Partial / Let me look at it**

**If "Let me look at it":**
1. Provide: `open .planning/sketches/NNN-name/index.html`
2. Remind them which variant won and what to look for
3. After they've looked, return to the include/exclude/partial decision

**If "Partial":**
Ask what specifically to include or exclude from this sketch's decisions.
</step>

<step name="group">
## Auto-Group by Design Area

After all sketches are curated:

1. Read all included sketches' tags, names, and content
2. Propose design-area groupings, e.g.:
   - "**Layout & Navigation** — sketches 001, 004"
   - "**Form Controls** — sketches 002, 005"
   - "**Color & Typography** — sketches 003"
3. Present the grouping for approval — user may merge, split, rename, or rearrange

Each group becomes one reference file in the generated skill.
</step>

<step name="skill_name">
## Determine Output Skill Name

Derive from the project directory name: `./.claude/skills/sketch-findings-[project-dir-name]/`

If a skill already exists at that path (append mode), update in place.
</step>

<step name="copy_sources">
## Copy Source Files

For each included sketch:

1. Copy the winning variant's HTML file (or the full index.html with all variants) into `sources/NNN-sketch-name/`
2. Copy the winning theme.css into `sources/themes/`
3. Exclude node_modules, build artifacts, .DS_Store
</step>

<step name="synthesize">
## Synthesize Reference Files

For each design-area group, write a reference file at `.ai/library/references/[design-area-name].md`:

```markdown
# [Design Area Name]

## Design Decisions
[For each validated decision: what was chosen, why it won over alternatives, the key visual properties (colors, spacing, border radius, typography)]

## CSS Patterns
[Key CSS snippets from winning variants — layout structures, component patterns, animation patterns. Extracted and cleaned up for reference.]

## HTML Structures
[Key HTML patterns from winning variants — page layout, component markup, navigation structures.]

## What to Avoid
[Design directions that were tried and rejected. Why they didn't work.]

## Origin
Synthesized from sketches: NNN, NNN
Source files available in: sources/NNN-sketch-name/
```
</step>

<step name="write_skill">
## Write SKILL.md

Create (or update) the generated skill's SKILL.md:

```markdown
---
name: sketch-findings-[project-dir-name]
description: Validated design decisions, CSS patterns, and visual direction from sketch experiments. Auto-loaded during UI implementation on [project-dir-name].
---

<context>
## Project: [project-dir-name]

[Design direction paragraph from MANIFEST.md]
[Reference points mentioned during intake]

Sketch sessions wrapped: [date(s)]
</context>

<design_direction>
## Overall Direction

[Summary of the validated visual direction: palette, typography, spacing system, layout approach, interaction patterns]
</design_direction>

<findings_index>
## Design Areas

| Area | Reference | Key Decision |
|------|-----------|--------------|
| [Name] | .ai/library/references/[name].md | [One-line summary] |

## Theme

The winning theme file is at `sources/themes/default.css`.

## Source Files

Original sketch HTML files are preserved in `sources/` for complete reference.
</findings_index>

<metadata>
## Processed Sketches

[List of sketch numbers wrapped up]

- 001-sketch-name
- 002-sketch-name
</metadata>
```
</step>

<step name="write_summary">
## Write Planning Summary

Write `.planning/sketches/WRAP-UP-SUMMARY.md` for project history:

```markdown
# Sketch Wrap-Up Summary

**Date:** [date]
**Sketches processed:** [count]
**Design areas:** [list]
**Skill output:** `./.claude/skills/sketch-findings-[project]/`

## Included Sketches
| # | Name | Winner | Design Area |
|---|------|--------|-------------|

## Excluded Sketches
| # | Name | Reason |
|---|------|--------|

## Design Direction
[consolidated design direction summary]

## Key Decisions
[layout, palette, typography, spacing, interaction patterns]
```
</step>

<step name="update_claude_md">
## Update Project CLAUDE.md

Add an auto-load routing line:

```
- **Sketch findings for [project]** (design decisions, CSS patterns, visual direction) → `Skill("sketch-findings-[project-dir-name]")`
```

If this routing line already exists (append mode), leave it as-is.
</step>

<step name="commit">
Commit all artifacts (if `COMMIT_DOCS` is true):

```bash
workflow_run query commit "docs(sketch-wrap-up): package [N] sketch findings into project skill" --files .planning/sketches/WRAP-UP-SUMMARY.md
```
</step>

<step name="report">
```
### Workflow ► SKETCH WRAP-UP COMPLETE ✓

**Curated:** {N} sketches ({included} included, {excluded} excluded)
**Design areas:** {list}
**Skill:** `./.claude/skills/sketch-findings-[project]/`
**Summary:** `.planning/sketches/WRAP-UP-SUMMARY.md`
**CLAUDE.md:** routing line added

The sketch-findings skill will auto-load when building the UI.
```

---

## ▶ Next Up

**Explore frontier sketches** — see what else is worth sketching based on what we've explored

`/workflow:sketch` (run with no argument — its frontier mode analyzes the sketch landscape and proposes consistency and frontier sketches)

---

**Also available:**
- `/workflow:plan-phase` — start building the real UI
- `/workflow:ui-phase` — generate a UI design contract for a frontend phase
- `/workflow:sketch [idea]` — sketch a specific new design area
- `/workflow:explore` — continue exploring

---
</step>

</process>

<success_criteria>
- [ ] Every unprocessed sketch presented for individual curation
- [ ] Design-area grouping proposed and approved
- [ ] Sketch-findings skill exists at `./.claude/skills/` with SKILL.md, .ai/library/references/, sources/
- [ ] Winning theme.css copied into skill sources
- [ ] Reference files contain design decisions, CSS patterns, HTML structures, anti-patterns
- [ ] `.planning/sketches/WRAP-UP-SUMMARY.md` written for project history
- [ ] Project CLAUDE.md has auto-load routing line
- [ ] Summary presented
- [ ] Next-step options presented (including frontier sketch exploration via `/workflow:sketch`)
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
