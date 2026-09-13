@.ai/library/references/response-language-directive.md

<purpose>
Package spike experiment findings into a persistent project skill — an implementation blueprint
for future build conversations. Reads from `.planning/spikes/`, writes skill to
`./.claude/skills/spike-findings-[project]/` (project-local) and summary to
`.planning/spikes/WRAP-UP-SUMMARY.md`. Companion to `/workflow:spike`.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="banner">
```
### Workflow ► SPIKE WRAP-UP
```
</step>

<step name="gather">
## Gather Spike Inventory

1. Read `.planning/spikes/MANIFEST.md` for the `## Ideas` sections (each idea's paragraph and
   its own scoped Requirements list) and the `## Spikes` table (its Idea column tells you which
   idea key each spike row belongs to).
2. Glob `.planning/spikes/*/README.md` and parse YAML frontmatter from each — each spike's
   `idea:` field is the idea key that owns it. If a README predates #1700 and has no `idea:`
   field, resolve its idea key from the matching `## Spikes` table row's Idea column instead.
3. Check if `./.claude/skills/spike-findings-*/SKILL.md` exists for this project
   - If yes: read its `processed_spikes` list from the metadata section and filter those out
   - If no: all spikes are candidates

If no unprocessed spikes exist:
```
No unprocessed spikes found in `.planning/spikes/`.
Run `/workflow:spike` first to create experiments.
```
Exit.

Check `commit_docs` config:
```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
COMMIT_DOCS=$(workflow_run query config-get commit_docs --raw 2>/dev/null || echo "true")
```
</step>

<step name="auto_include">
## Auto-Include All Spikes

Include all unprocessed spikes automatically. Present a brief inventory showing what's being processed:

```
Processing N spikes:
  001 — name (VALIDATED)
  002 — name (PARTIAL)
  003 — name (INVALIDATED)
```

Every spike carries forward:
- **VALIDATED** spikes provide proven patterns
- **PARTIAL** spikes provide constrained patterns
- **INVALIDATED** spikes provide landmines and dead ends
</step>

<step name="group">
## Auto-Group by Feature Area

Group spikes by feature area based on tags, names, `related` fields, and content. Proceed directly into synthesis.

Each group becomes one reference file in the generated skill.
</step>

<step name="skill_name">
## Determine Output Skill Name

Derive the skill name from the project directory:

1. Get the project root directory name (e.g., `solana-tracker`)
2. The skill will be created at `./.claude/skills/spike-findings-[project-dir-name]/`

If a skill already exists at that path (append mode), update in place.
</step>

<step name="copy_sources">
## Copy Source Files

For each included spike:

1. Identify the core source files — the actual scripts, main files, and config that make the spike work. Exclude:
   - `node_modules/`, `__pycache__/`, `.venv/`, build artifacts
   - Lock files (`package-lock.json`, `yarn.lock`, etc.)
   - `.git/`, `.DS_Store`
2. Copy the README.md and core source files into `sources/NNN-spike-name/` inside the generated skill directory
</step>

<step name="synthesize">
## Synthesize Reference Files

For each feature-area group, write a reference file at `.ai/library/references/[feature-area-name].md` as an **implementation blueprint** — it should read like a recipe, not a research paper. A future build session should be able to follow this and build the feature correctly without re-spiking anything.

```markdown
# [Feature Area Name]

## Requirements

[Non-negotiable design decisions pulled ONLY from the Requirements list of the idea key(s) that
own the spikes in this feature-area group — match each spike's `idea:` frontmatter (or Idea
column) to its `### {idea-key}` Requirements list in MANIFEST.md. These MUST be honored in the
real build. E.g., "Must use streaming JSON output", "Must support reconnection".

Never include a requirement from an idea key that has no spike in this group.]

## How to Build It

[Step-by-step: what to install, how to configure, what code pattern to use. Include key code snippets extracted from the spike source. This is the proven approach — not theory, but tested and working code.]

## What to Avoid

[Things that look right but aren't. Gotchas. Anti-patterns discovered during spiking. Dead ends that were tried and failed.]

## Constraints

[Hard facts: rate limits, library limitations, version requirements, incompatibilities]

## Origin

Synthesized from spikes: NNN, NNN, NNN
Source files available in: sources/NNN-spike-name/, sources/NNN-spike-name/
```
</step>

<step name="write_skill">
## Write SKILL.md

Create (or update) the generated skill's SKILL.md:

```markdown
---
name: spike-findings-[project-dir-name]
description: Implementation blueprint from spike experiments. Requirements, proven patterns, and verified knowledge for building [project-dir-name]. Auto-loaded during implementation work.
---

<context>
## Project: [project-dir-name]

[One paragraph per idea key represented among the wrapped spikes, taken from that idea's
`### {idea-key}` section in MANIFEST.md — not the whole MANIFEST.md if it holds unrelated ideas.]

Spike sessions wrapped: [date(s)]
</context>

<requirements>
## Requirements

[Union of the Requirements lists for every idea key represented among the spikes being wrapped
in this session — never the whole MANIFEST.md. These are non-negotiable design decisions that
emerged from the user's choices while spiking those specific idea(s). Every feature area
reference must honor these. If this wrap-up spans more than one idea key, group the list by
idea key so a future reader can tell which requirement belongs to which idea.]

- [requirement 1]
- [requirement 2]
</requirements>

<findings_index>
## Feature Areas

| Area | Reference | Key Finding |
|------|-----------|-------------|
| [Name] | .ai/library/references/[name].md | [One-line summary] |

## Source Files

Original spike source files are preserved in `sources/` for complete reference.
</findings_index>

<metadata>
## Processed Spikes

[List of spike numbers wrapped up]

- 001-spike-name
- 002-spike-name
</metadata>
```
</step>

<step name="write_summary">
## Write Planning Summary

Write `.planning/spikes/WRAP-UP-SUMMARY.md` for project history:

```markdown
# Spike Wrap-Up Summary

**Date:** [date]
**Spikes processed:** [count]
**Feature areas:** [list]
**Skill output:** `./.claude/skills/spike-findings-[project]/`

## Processed Spikes
| # | Name | Type | Verdict | Feature Area |
|---|------|------|---------|--------------|

## Key Findings
[consolidated findings summary]
```
</step>

<step name="update_claude_md">
## Update Project CLAUDE.md

Add an auto-load routing line to the project's CLAUDE.md (create the file if it doesn't exist):

```
- **Spike findings for [project]** (implementation patterns, constraints, gotchas) → `Skill("spike-findings-[project-dir-name]")`
```

If this routing line already exists (append mode), leave it as-is.
</step>

<step name="generate_conventions">
## Generate or Update CONVENTIONS.md

Analyze all processed spikes for recurring patterns and write `.planning/spikes/CONVENTIONS.md`. This file tells future spike sessions *how we spike* — the stack, structure, and patterns that have been established.

1. Read all spike source code and READMEs looking for:
   - **Stack choices** — What language/framework/runtime appears across multiple spikes?
   - **Structure patterns** — Common file layouts, port numbers, naming schemes
   - **Recurring approaches** — How auth is handled, how styling is done, how data is served
   - **Tools & libraries** — Packages that showed up repeatedly with versions that worked

2. Write or update `.planning/spikes/CONVENTIONS.md`:

```markdown
# Spike Conventions

Patterns and stack choices established across spike sessions. New spikes follow these unless the question requires otherwise.

## Stack
[What we use for frontend, backend, scripts, and why — derived from what repeated across spikes]

## Structure
[Common file layouts, port assignments, naming patterns]

## Patterns
[Recurring approaches: how we handle auth, how we style, how we serve, etc.]

## Tools & Libraries
[Preferred packages with versions that worked, and any to avoid]
```

3. Only include patterns that appeared in 2+ spikes or were explicitly chosen by the user.

4. If `CONVENTIONS.md` already exists (append mode), update sections with new patterns. Remove entries contradicted by newer spikes.
</step>

<step name="commit">
Commit all artifacts (if `COMMIT_DOCS` is true):

```bash
workflow_run query commit "docs(spike-wrap-up): package [N] spike findings into project skill" --files .planning/spikes/WRAP-UP-SUMMARY.md .planning/spikes/CONVENTIONS.md
```
</step>

<step name="report">
```
### Workflow ► SPIKE WRAP-UP COMPLETE ✓

**Processed:** {N} spikes
**Feature areas:** {list}
**Skill:** `./.claude/skills/spike-findings-[project]/`
**Conventions:** `.planning/spikes/CONVENTIONS.md`
**Summary:** `.planning/spikes/WRAP-UP-SUMMARY.md`
**CLAUDE.md:** routing line added

The spike-findings skill will auto-load in future build conversations.
```
</step>

<step name="whats_next">
## What's Next

After the summary, present next-step options:

---

## ▶ Next Up

**Explore frontier spikes** — see what else is worth spiking based on what we've learned

`/workflow:spike` (run with no argument — its frontier mode analyzes the spike landscape and proposes integration and frontier spikes)

---

**Also available:**
- `/workflow:plan-phase` — start planning the real implementation
- `/workflow:spike [idea]` — spike a specific new idea
- `/workflow:explore` — continue exploring
- Other

---
</step>

</process>

<success_criteria>
- [ ] All unprocessed spikes auto-included and processed
- [ ] Spikes grouped by feature area
- [ ] Spike-findings skill exists at `./.claude/skills/` with SKILL.md (including requirements), .ai/library/references/, sources/
- [ ] Reference files are implementation blueprints with Requirements, How to Build It, What to Avoid, Constraints
- [ ] Requirements in each reference file and in SKILL.md are scoped to the idea key(s) actually represented among the wrapped spikes — never blended with an unrelated idea's requirements
- [ ] `.planning/spikes/CONVENTIONS.md` created or updated with recurring stack/structure/pattern choices
- [ ] `.planning/spikes/WRAP-UP-SUMMARY.md` written for project history
- [ ] Project CLAUDE.md has auto-load routing line
- [ ] Summary presented
- [ ] Next-step options presented (including frontier spike exploration via `/workflow:spike`)
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
