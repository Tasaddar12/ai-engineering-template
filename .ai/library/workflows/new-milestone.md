<purpose>

Start a new milestone cycle for an existing project. Loads project context, gathers milestone goals (from MILESTONE-CONTEXT.md or conversation), updates PROJECT.md and STATE.md, optionally runs parallel research, defines scoped requirements with REQ-IDs, spawns the roadmapper to create phased execution plan, and commits all artifacts. Brownfield equivalent of new-project.

</purpose>

<required_reading>

Read all files referenced by the invoking prompt's execution_context before starting.

</required_reading>

<available_agent_types>
Valid Workflow subagent types (use exact names — do not fall back to 'general-purpose'):
- project-researcher — Researches project-level technical decisions
- research-synthesizer — Synthesizes findings from parallel research agents
- roadmapper — Creates phased execution roadmaps
</available_agent_types>

<process>

## 1. Load Context

Parse `$ARGUMENTS` before doing anything else:

- `--reset-phase-numbers` flag → opt into restarting roadmap phase numbering at `1`. If absent, keep the current behavior of continuing phase numbering from the previous milestone.
- `--ws <name>` flag → active workstream scope, parsed into `Workflow_WS`
- remaining text, with `--ws <name>` stripped → use as milestone name if present, captured into `MILESTONE_ARG`

Parse `Workflow_WS` and `MILESTONE_ARG` using the established idiom (see `verify-work.md`):

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
Workflow_WS=""
echo "$ARGUMENTS" | grep -qE -- '--ws[[:space:]]+[A-Za-z0-9._-]+' && Workflow_WS=$(echo "$ARGUMENTS" | grep -oE -- '--ws[[:space:]]+[A-Za-z0-9._-]+')
MILESTONE_ARG=$(echo "$ARGUMENTS" | sed -E 's/--ws[[:space:]]+[A-Za-z0-9._-]+//g' | xargs)
# #4456: persist Workflow_WS to a file so later steps' bash fences (each a
# separate shell) can forward it — the same cross-fence problem Step 5/6
# already solve for OUTGOING_MILESTONE via .workflow-outgoing-milestone.
printf '%s' "$Workflow_WS" > .planning/.workflow-ws-arg 2>/dev/null || true
RESPONSE_LANGUAGE=$(workflow_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
# #2994: EARLY, section-manifest-only init.new-milestone call — needed here
# (before Step 4) to gate the project-md-milestone-write section. This is
# DELIBERATELY separate from Step 7's full init.new-milestone call below,
# which must stay AFTER Step 6's phase archival/phases.clear so its
# phase_dir_count / roadmap_exists / latest_completed_milestone fields
# reflect POST-archival state — moving that call here would compute those
# fields too early and corrupt the roadmapper's phase-numbering context.
# init.new-milestone is a pure read (no mutation), so calling it twice is
# safe; only `section_manifest` is consumed from this early call.
# #4456: $Workflow_WS forwarded (same fence as the parse above, no round-trip
# needed here) so the section manifest — and the shared PROJECT.md write
# guard it gates — reflects the EXPLICITLY requested workstream, not
# whatever ambient Workflow_WORKSTREAM/session pointer happens to be active.
INIT_EARLY=$(workflow_run query init.new-milestone $Workflow_WS)
if [[ "$INIT_EARLY" == @file:* ]]; then INIT_EARLY=$(cat "${INIT_EARLY#@file:}"); fi
```

`Workflow_WS` must chain to every downstream routing suggestion in this workflow (Step 4's shared-file guard, and the `/workflow:discuss-phase`/`/workflow:plan-phase` routing hints below) per the routing-propagation contract in `.ai/library/references/workstream-flag.md` — never let it silently drop.

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations (including the "What do you want to build next?" prompt and seed-selection questions below) — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

- Read PROJECT.md (existing project, validated requirements, decisions)
- Read MILESTONES.md (what shipped previously)
- Read STATE.md (pending todos, blockers)
- Check for MILESTONE-CONTEXT.md (from /workflow-discuss-milestone)

## 2. Gather Milestone Goals

**If MILESTONE-CONTEXT.md exists:**
- Use features and scope from discuss-milestone
- Present summary for confirmation

**If no context file:**
- Present what shipped in last milestone

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
- Ask inline (freeform, NOT AskUserQuestion): "What do you want to build next?"
- Wait for their response, then use AskUserQuestion to probe specifics
- If user selects "Other" at any point to provide freeform input, ask follow-up as plain text — not another AskUserQuestion

## 2.5. Scan Planted Seeds

Check `.planning/seeds/` for seed files that match the milestone goals gathered in step 2.

```bash
ls .planning/seeds/SEED-*.md 2>/dev/null
```

**If no seed files exist:** Skip this step silently — do not print any message or prompt.

**If seed files exist:** Read each `SEED-*.md` file and extract from its frontmatter and body:
- **Idea** — the seed title (heading after frontmatter, e.g. `# SEED-001: <idea>`)
- **Trigger conditions** — the `trigger_when` frontmatter field and the "When to Surface" section's bullet list
- **Planted during** — the `planted_during` frontmatter field (for context)

Compare each seed's trigger conditions against the milestone goals from step 2. A seed matches when its trigger conditions are relevant to any of the milestone's target features or goals.

**If no seeds match:** Skip silently — do not prompt the user.

**If matching seeds found:**

**`--auto` mode:** Auto-select ALL matching seeds. Log: `[auto] Selected N matching seed(s): [list seed names]`

**Text mode (`TEXT_MODE=true`):** Present matching seeds as a plain-text numbered list:
```
Seeds that match your milestone goals:
1. SEED-001: <idea> (trigger: <trigger_when>)
2. SEED-003: <idea> (trigger: <trigger_when>)

Enter numbers to include (comma-separated), or "none" to skip:
```

**Normal mode:** Present via AskUserQuestion:
```
AskUserQuestion(
  header: "Seeds",
  question: "These planted seeds match your milestone goals. Include any in this milestone's scope?",
  multiSelect: true,
  options: [
    { label: "SEED-001: <idea>", description: "Trigger: <trigger_when> | Planted during: <planted_during>" },
    ...
  ]
)
```

**After selection:**
- Selected seeds become additional context for requirement definition in step 9. Store them in an accumulator (e.g. `$SELECTED_SEEDS`) so step 9 can reference the ideas and their "Why This Matters" sections when defining requirements.
- Unselected seeds remain untouched in `.planning/seeds/` — never delete or modify seed files during this workflow.

## 3. Determine Milestone Version

- Parse last version from MILESTONES.md
- Suggest next version (v1.0 → v1.1, or v2.0 for major)
- Confirm with user

## 3.5. Verify Milestone Understanding

Before writing any files, present a summary of what was gathered and ask for confirmation.

```
### Workflow ► MILESTONE SUMMARY

**Milestone v[X.Y]: [Name]**

**Goal:** [One sentence]

**Target features:**
- [Feature 1]
- [Feature 2]
- [Feature 3]

**Key context:** [Any important constraints, decisions, or notes from questioning]
```

AskUserQuestion:
- header: "Confirm?"
- question: "Does this capture what you want to build in this milestone?"
- options:
  - "Looks good" — Proceed to write PROJECT.md
  - "Adjust" — Let me correct or add details

**If "Adjust":** Ask what needs changing (plain text, NOT AskUserQuestion). Incorporate changes, re-present the summary. Loop until "Looks good" is selected.

**If "Looks good":** Proceed to Step 4.

## 4. Update PROJECT.md

PROJECT.md is shared across workstreams (`.ai/library/references/workstream-flag.md` marks it `# Shared` in the directory diagram). This step has two independently-scoped parts — only Part A is workstream-guarded.

<!-- workflow:section id="project-md-milestone-write" when="state:flat-mode" -->
If `section_manifest` (from `INIT_EARLY`) is `null` or `"project-md-milestone-write"` is in its `included` list: read and execute `.ai/library/workflows/new-milestone/steps/project-md-milestone-write.md`. Otherwise (a workstream is active) skip — do not read the file; Part B below still runs regardless of `Workflow_WS`.
<!-- /workflow:section -->

**Part B — Evolution structural repair (always runs, regardless of `Workflow_WS`).** `## Evolution` is a shared, idempotent structural section, not workstream state — a pre-Evolution project must be backfilled whether or not a workstream is active, so this part is NOT covered by Part A's skip. Ensure the `## Evolution` section exists in PROJECT.md. If missing (projects created before this feature), add it before the footer:

```markdown
## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/workflow-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/workflow:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state
```

## 5. Update STATE.md

Reset STATE.md frontmatter AND body atomically via the SDK. This writes the new
milestone version/name into the YAML frontmatter, resets `status` to
`planning`, zeroes `progress.*` counters, and rewrites the `## Current Position`
section to the new-milestone template. Accumulated Context (decisions,
blockers, todos) is preserved across the switch — symmetric with
`milestone.complete`.

```bash
Workflow_WS_ARG=$(cat .planning/.workflow-ws-arg 2>/dev/null || true)
OUTGOING_MILESTONE=$(workflow_run query state.get milestone --raw $Workflow_WS_ARG 2>/dev/null || true)
printf '%s' "$OUTGOING_MILESTONE" > .planning/.workflow-outgoing-milestone 2>/dev/null || true
echo "Outgoing milestone (phase history archives under THIS version in step 6): ${OUTGOING_MILESTONE:-<unknown>}"
workflow_run query state.milestone-switch --milestone "v[X.Y]" --name "[Name]" $Workflow_WS_ARG
```

**Capture the outgoing version now.** The lines above read the *current* (previous) milestone
version BEFORE the switch flips STATE.md's `milestone:` field to the new one, and persist it to
`.planning/.workflow-outgoing-milestone` so Step 6 can consume it via a shell variable — do NOT
transcribe the echoed value into a later command by hand. Step 6 reads that file back into
`--archive-version` so the previous milestone's phase directories archive under
`<outgoing-version>-phases/`, not the new one (#2288). Once `state.milestone-switch` runs,
current-milestone state no longer holds the outgoing version, which is why it is captured here.

The resulting Current Position section looks like:

```markdown
## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: [today] — Milestone v[X.Y] started
```

Bug #2630: a prior version of this workflow rewrote the Current Position body
manually but left the frontmatter pointing at the previous milestone, so every
downstream reader (`state.json`, `getMilestoneInfo`, progress bars) reported the
stale milestone until the first phase advance forced a resync. Always use the
SDK handler above — do not hand-edit STATE.md here.

## 6. Cleanup and Commit

Delete MILESTONE-CONTEXT.md if exists (consumed).

Clear leftover phase directories from the previous milestone. Read the outgoing version
persisted in Step 5 back into a shell variable and pass it as `--archive-version` so the
archive lands under the *previous* milestone's label — the switch in Step 5 has already
advanced current-milestone state, so without this override the archive would be mislabeled
with the *new* version (#2288). Use the shell variable directly (quoted) — never hand-retype
the captured value into the command, so untrusted STATE.md content cannot be re-parsed by the
shell:

```bash
Workflow_WS_ARG=$(cat .planning/.workflow-ws-arg 2>/dev/null || true)
OUTGOING_MILESTONE=$(cat .planning/.workflow-outgoing-milestone 2>/dev/null || true)
if [ -n "$OUTGOING_MILESTONE" ]; then
  workflow_run query phases.clear --confirm --archive-version "$OUTGOING_MILESTONE" $Workflow_WS_ARG
else
  workflow_run query phases.clear --confirm $Workflow_WS_ARG
fi
rm -f .planning/.workflow-outgoing-milestone 2>/dev/null || true
```

If the captured file is empty or absent (a fresh project with no prior milestone), the
fallback branch runs `phases.clear --confirm` with no override — it then uses current-milestone
state, and a dated archive label only if no version label is resolvable at all. `phases.clear`
rejects any `--archive-version` value that is not a plain version token (no path separators or
`..`), so a malformed capture fails loudly rather than writing outside the archive directory.

Stage the phase archive move + source removal so they land in the same commit as the milestone start (atomic — no orphaned uncommitted deletions, no un-archived dirs carried forward). `phases.clear` archives each non-999 dir to `milestones/<version>-phases/`; staging both dirs captures the new archive and the removals together (#1871).

```bash
COMMIT_DOCS=$(workflow_run query config-get commit_docs --raw 2>/dev/null || echo "true")
Workflow_WS_ARG=$(cat .planning/.workflow-ws-arg 2>/dev/null || true)
INIT_STAGE=$(workflow_run query init.new-milestone $Workflow_WS_ARG)
if [[ "$INIT_STAGE" == @file:* ]]; then INIT_STAGE=$(cat "${INIT_STAGE#@file:}"); fi
_workflow_field() { node -e "const o=JSON.parse(process.argv[1]); const v=o[process.argv[2]]; process.stdout.write(v==null?'':String(v))" "$1" "$2"; }
ARCHIVE_DIR=$(_workflow_field "$INIT_STAGE" archive_dir)
PHASES_DIR=$(_workflow_field "$INIT_STAGE" phases_dir)
if [ "$COMMIT_DOCS" != "false" ]; then
  git add "$ARCHIVE_DIR/" "$PHASES_DIR/" 2>/dev/null || true
fi
```

When `commit_docs` is false, the archive move and phase removals are deliberately left unstaged here — not a bug — since Step 6's commit is skipped too.

Stage PROJECT.md in both modes. Step 4's Part A guard — not this commit — is what protects the shared `## Current Milestone` heading (#2308): when a workstream is active Part A never writes it, so the only change PROJECT.md can carry here is Part B's idempotent `## Evolution` backfill, which must be committed rather than stranded as a dangling edit. Do NOT reintroduce a `[ -n "$Workflow_WS" ]` branch around this commit: `Workflow_WS` is set in Step 1's shell and each step's bash block runs in its own shell (the same reason Step 5 round-trips `OUTGOING_MILESTONE` through a file), so such a guard reads an unset variable, always takes the flat-mode branch, and only appears to work. STATE.md, unlike PROJECT.md, IS workstream-scoped (Step 5's switch just wrote the workstream's own copy) — resolved below via `init.new-milestone` rather than a literal `.planning/STATE.md`, which would commit the wrong (or a stale, unrelated) file under an active workstream.

```bash
Workflow_WS_ARG=$(cat .planning/.workflow-ws-arg 2>/dev/null || true)
INIT_COMMIT=$(workflow_run query init.new-milestone $Workflow_WS_ARG)
if [[ "$INIT_COMMIT" == @file:* ]]; then INIT_COMMIT=$(cat "${INIT_COMMIT#@file:}"); fi
_workflow_field() { node -e "const o=JSON.parse(process.argv[1]); const v=o[process.argv[2]]; process.stdout.write(v==null?'':String(v))" "$1" "$2"; }
STATE_PATH=$(_workflow_field "$INIT_COMMIT" state_path)
PROJECT_PATH=$(_workflow_field "$INIT_COMMIT" project_path)
workflow_run query commit "docs: start milestone v[X.Y] [Name]" --files "$PROJECT_PATH" "$STATE_PATH"
```

## 7. Load Context and Resolve Models

```bash
RESET_PHASE_NUMBERS_PARAM=""; if [[ "$ARGUMENTS" =~ (^|[[:space:]])--reset-phase-numbers([[:space:]]|$) ]]; then RESET_PHASE_NUMBERS_PARAM="--reset-phase-numbers"; fi
Workflow_WS_ARG=$(cat .planning/.workflow-ws-arg 2>/dev/null || true)
INIT=$(workflow_run query init.new-milestone $RESET_PHASE_NUMBERS_PARAM $Workflow_WS_ARG)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_RESEARCHER=$(workflow_run query agent-skills project-researcher)
AGENT_SKILLS_SYNTHESIZER=$(workflow_run query agent-skills research-synthesizer)
AGENT_SKILLS_ROADMAPPER=$(workflow_run query agent-skills roadmapper)
```
<!-- #4456: .planning/.workflow-ws-arg is NOT cleaned up here — Steps 9 and 10
below still need to re-read it (each is its own shell) to resolve
REQUIREMENTS.md/ROADMAP.md/STATE.md correctly under a workstream. It is
removed in Step 10, its true last consumer. -->

Extract from init JSON: `researcher_model`, `synthesizer_model`, `roadmapper_model`, `commit_docs`, `research_enabled`, `current_milestone`, `project_exists`, `roadmap_exists`, `latest_completed_milestone`, `phase_dir_count`, `phase_archive_path`, `agents_installed`, `missing_agents`, `project_path`, `roadmap_path`, `requirements_path`, `config_path`, `research_dir`, `milestones_path`, `phases_dir`, `archive_dir`.

**If `agents_installed` is false:** Display a warning before proceeding:
```
⚠ Workflow agents not installed. The following agents are missing from your agents directory:
  {missing_agents joined with newline}

Subagent spawns (project-researcher, research-synthesizer, roadmapper) will fail
with "agent type not found". Run the installer with --global to make agents available:

  npx @openworkflow/workflow-core@latest --global

Proceeding without research subagents — roadmap will be generated inline.
```
Skip the parallel research spawn step and generate the roadmap inline.

<!-- workflow:section id="reset-phase-safety" when="flag:--reset-phase-numbers" -->
If `section_manifest` is `null` or `"reset-phase-safety"` is in its `included` list: read and execute `.ai/library/workflows/new-milestone/steps/reset-phase-safety.md`. Otherwise skip — do not read the file.
<!-- /workflow:section -->

## 8. Research Decision

Check `research_enabled` from init JSON (loaded from config).

**If `research_enabled` is `true`:**

AskUserQuestion: "Research the domain ecosystem for new features before defining requirements?"
- "Research first (Recommended)" — Discover patterns, features, architecture for NEW capabilities
- "Skip research for this milestone" — Go straight to requirements (does not change your default)

**If `research_enabled` is `false`:**

AskUserQuestion: "Research the domain ecosystem for new features before defining requirements?"
- "Skip research (current default)" — Go straight to requirements
- "Research first" — Discover patterns, features, architecture for NEW capabilities

**IMPORTANT:** Do NOT persist this choice to config.json. The `workflow.research` setting is a persistent user preference that controls plan-phase behavior across the project. Changing it here would silently alter future `/workflow:plan-phase` behavior. To change the default, use `/workflow:settings`.

**If user chose "Research first":**

```
### Workflow ► RESEARCHING

◆ Spawning 4 researchers in parallel... (each runs in a subagent — no output until they return, ~1–5 min; expected, not a freeze)
  → Stack, Features, Architecture, Pitfalls
```

```bash
mkdir -p .planning/research
```

Spawn 4 parallel project-researcher agents. Each uses this template with dimension-specific fields:

**Common structure for all 4 researchers:**
<!-- #2517 model-omit-on-inherit -->

> **Model omission (#2517).** Omit the `model` parameter entirely when the value it would carry (`researcher_model`, `synthesizer_model`, `roadmapper_model`) is `"inherit"` or empty. An empty value 404s on runtimes without native tier aliases — the default on non-Claude runtimes. Omitting it inherits the orchestrator's model. See @.ai/library/references/model-profile-resolution.md.

```text
Agent(prompt="
<research_type>Project Research — {DIMENSION} for [new features].</research_type>

<milestone_context>
SUBSEQUENT MILESTONE — Adding [target features] to existing app.
{EXISTING_CONTEXT}
Focus ONLY on what's needed for the NEW features.
</milestone_context>

<question>{QUESTION}</question>

<required_reading>
- {project_path} (Project context)
</required_reading>

${AGENT_SKILLS_RESEARCHER}

<downstream_consumer>{CONSUMER}</downstream_consumer>

<quality_gate>{GATES}</quality_gate>

<!-- #2508 runtime-aware-dispatch -->

> **Runtime-aware dispatch (#2508 Phase 4).** Workflow workflows dispatch specialized subagents by role. Before dispatching on a built-in-only runtime (kimi-code — three built-ins only), resolve the role to a built-in via `workflow_run query resolve-dispatch-type --requested <role> --raw`. On named-dispatch runtimes (Claude/OpenCode/…) the role is returned unchanged; on kimi-code it maps to `coder`/`explore`/`plan` by role-suffix. The persona rides `${AGENT_SKILLS_<ROLE>}` (Phase 3) regardless. See @.ai/library/references/runtime-aware-dispatch.md.

<output>
Write to: {research_dir}/{FILE}
Use template: .ai/templates/research-project/{FILE}
</output>
", subagent_type="project-researcher", model="{researcher_model}", description="{DIMENSION} research")
```

**Dimension-specific fields:**

| Field | Stack | Features | Architecture | Pitfalls |
|-------|-------|----------|-------------|----------|
| EXISTING_CONTEXT | Existing validated capabilities (DO NOT re-research): [from PROJECT.md] | Existing features (already built): [from PROJECT.md] | Existing architecture: [from PROJECT.md or codebase map] | Focus on common mistakes when ADDING these features to existing system |
| QUESTION | What stack additions/changes are needed for [new features]? | How do [target features] typically work? Expected behavior? | How do [target features] integrate with existing architecture? | Common mistakes when adding [target features] to [domain]? |
| CONSUMER | Specific libraries with versions for NEW capabilities, integration points, what NOT to add | Table stakes vs differentiators vs anti-features, complexity noted, dependencies on existing | Integration points, new components, data flow changes, suggested build order | Warning signs, prevention strategy, which phase should address it |
| GATES | Versions current (verify with Context7), rationale explains WHY, integration considered | Categories clear, complexity noted, dependencies identified | Integration points identified, new vs modified explicit, build order considers deps | Pitfalls specific to adding these features, integration pitfalls covered, prevention actionable |
| FILE | STACK.md | FEATURES.md | ARCHITECTURE.md | PITFALLS.md |

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling all 4 researcher Agent() calls above, do NOT read research files or synthesize content independently while the subagents are active. Wait for all 4 researchers to complete before spawning the synthesizer. This prevents duplicate work and wasted context.

After all 4 complete, spawn synthesizer:

```text
Agent(prompt="
Synthesize research outputs into SUMMARY.md.

<required_reading>
- {research_dir}/STACK.md
- {research_dir}/FEATURES.md
- {research_dir}/ARCHITECTURE.md
- {research_dir}/PITFALLS.md
</required_reading>

${AGENT_SKILLS_SYNTHESIZER}

Write to: {research_dir}/SUMMARY.md
Use template: .ai/templates/research-project/SUMMARY.md
Commit after writing.
", subagent_type="research-synthesizer", model="{synthesizer_model}", description="Synthesize research")
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

**Synthesizer output self-heal (#222) — verify SUMMARY.md materialized:** The synthesizer's canonical output is `.planning/research/SUMMARY.md` on disk; its brief structured return (`## SYNTHESIS COMPLETE` plus a few `###` confirmation lines) is NOT the file content. A known LLM false-refusal (issue #222) sometimes makes the agent return the full SUMMARY.md document inline — fabricating a write restriction (e.g. "the runtime is blocking file writes") — instead of writing the file. Prompt hardening alone does not fully eliminate it, so the orchestrator MUST absorb the failure deterministically before spawning `roadmapper`:

1. Verify `.planning/research/SUMMARY.md` exists AND is substantive — non-empty, and free of any leftover `<!-- workflow:write-continue -->` continuation sentinel (which marks a truncated/incomplete write). You may validate with `workflow_run verify-summary .planning/research/SUMMARY.md` — it exits 0 regardless, so check its JSON `passed` field (`"passed": false` means missing or invalid), not the process exit code. If it passes, continue normally.
2. If it is MISSING or invalid AND the synthesizer's return message contains the FULL SUMMARY.md document — recognizable by the template's top-level markers `# Project Research Summary`, `## Key Findings`, `## Implications for Roadmap`, and `## Sources`, not merely the brief `## SYNTHESIS COMPLETE` confirmation — the false-refusal fired: write that returned document to `.planning/research/SUMMARY.md` with the Write tool, then commit ALL research artifacts the synthesizer owns (it commits on behalf of the four researchers) with `workflow_run query commit "docs: complete project research" --files .planning/research/` unless they are already committed. Log `⚠ #222 self-heal: synthesizer returned SUMMARY.md inline without writing it; orchestrator persisted the file.`
3. If it is MISSING or invalid AND the return is only a brief confirmation (no full SUMMARY document to recover), the synthesizer genuinely failed — surface the error and stop; do NOT spawn `roadmapper` against a missing or incomplete SUMMARY.md.

This guarantees `roadmapper` (which lists SUMMARY.md as required reading) never runs against a missing or truncated SUMMARY.md.

Display key findings from SUMMARY.md:
```
### Workflow ► RESEARCH COMPLETE ✓

**Stack additions:** [from SUMMARY.md]
**Feature table stakes:** [from SUMMARY.md]
**Watch Out For:** [from SUMMARY.md]
```

**If "Skip research":** Continue to Step 9.

## 9. Define Requirements

```
### Workflow ► DEFINING REQUIREMENTS
```

Read PROJECT.md: core value, current milestone goals, validated requirements (what exists).

**If `$SELECTED_SEEDS` is non-empty (from step 2.5):** Include selected seed ideas and their "Why This Matters" sections as additional input when defining requirements. Seeds provide user-validated feature ideas that should be incorporated into the requirement categories alongside research findings or conversation-gathered features.

**If research exists:** Read FEATURES.md, extract feature categories.

Present features by category:
```
## [Category 1]
**Table stakes:** Feature A, Feature B
**Differentiators:** Feature C, Feature D
**Research notes:** [any relevant notes]
```

**If no research:** Gather requirements through conversation. Ask: "What are the main things users need to do with [new features]?" Clarify, probe for related capabilities, group into categories.

**Scope each category** via AskUserQuestion (multiSelect: true, header max 12 chars):
- "[Feature 1]" — [brief description]
- "[Feature 2]" — [brief description]
- "None for this milestone" — Defer entire category

Track: Selected → this milestone. Unselected table stakes → future. Unselected differentiators → out of scope.

**Identify gaps** via AskUserQuestion:
- "No, research covered it" — Proceed
- "Yes, let me add some" — Capture additions

**Generate REQUIREMENTS.md:**
- v1 Requirements grouped by category (checkboxes, REQ-IDs)
- Future Requirements (deferred)
- Out of Scope (explicit exclusions with reasoning)
- Traceability section (empty, filled by roadmap)

**REQ-ID format:** `[CATEGORY]-[NUMBER]` (AUTH-01, NOTIF-02). Continue numbering from existing.

**Requirement quality criteria:**

Good requirements are:
- **Specific and testable:** "User can reset password via email link" (not "Handle password reset")
- **User-centric:** "User can X" (not "System does Y")
- **Atomic:** One capability per requirement (not "User can login and manage profile")
- **Independent:** Minimal dependencies on other requirements

Present FULL requirements list for confirmation:

```
## Milestone v[X.Y] Requirements

### [Category 1]
- [ ] **CAT1-01**: User can do X
- [ ] **CAT1-02**: User can do Y

### [Category 2]
- [ ] **CAT2-01**: User can do Z

Does this capture what you're building? (yes / adjust)
```

If "adjust": Return to scoping.

**Commit requirements:**
```bash
Workflow_WS_ARG=$(cat .planning/.workflow-ws-arg 2>/dev/null || true)
INIT_REQ=$(workflow_run query init.new-milestone $Workflow_WS_ARG)
if [[ "$INIT_REQ" == @file:* ]]; then INIT_REQ=$(cat "${INIT_REQ#@file:}"); fi
_workflow_field() { node -e "const o=JSON.parse(process.argv[1]); const v=o[process.argv[2]]; process.stdout.write(v==null?'':String(v))" "$1" "$2"; }
REQUIREMENTS_PATH=$(_workflow_field "$INIT_REQ" requirements_path)
workflow_run query commit "docs: define milestone v[X.Y] requirements" --files "$REQUIREMENTS_PATH"
```

## 10. Create Roadmap

```
### Workflow ► CREATING ROADMAP

◆ Spawning roadmapper... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

**Starting phase number:**
- If `--reset-phase-numbers` is active, start at **Phase 1**
- Otherwise, continue from the previous milestone's last phase number (v1.0 ended at phase 5 → v1.1 starts at phase 6)

```text
Agent(prompt="
<planning_context>
<required_reading>
- {project_path}
- {requirements_path}
- {research_dir}/SUMMARY.md (if exists)
- {config_path}
- {milestones_path}
</required_reading>

${AGENT_SKILLS_ROADMAPPER}

</planning_context>

<instructions>
Create roadmap for milestone v[X.Y]:
1. Respect the selected numbering mode:
   - `--reset-phase-numbers` → start at Phase 1
   - default behavior → continue from the previous milestone's last phase number
2. Derive phases from THIS MILESTONE's requirements only
3. Map every requirement to exactly one phase
4. Derive 2-5 success criteria per phase (observable user behaviors)
5. Validate 100% coverage
6. Write files immediately (ROADMAP.md, STATE.md, update REQUIREMENTS.md traceability)
7. Return ROADMAP CREATED with summary

Write files first, then return.
</instructions>
", subagent_type="roadmapper", model="{roadmapper_model}", description="Create roadmap")
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

**Handle return:**

**If `## ROADMAP BLOCKED`:** Present blocker, work with user, re-spawn.

**If `## ROADMAP CREATED`:** Read ROADMAP.md, present inline:

```
## Proposed Roadmap

**[N] phases** | **[X] requirements mapped** | All covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| [N] | [Name] | [Goal] | [REQ-IDs] | [count] |

### Phase Details

**Phase [N]: [Name]**
Goal: [goal]
Requirements: [REQ-IDs]
Success criteria:
1. [criterion]
2. [criterion]
```

**Ask for approval** via AskUserQuestion:
- "Approve" — Commit and continue
- "Adjust phases" — Tell me what to change
- "Review full file" — Show raw ROADMAP.md

**If "Adjust":** Get notes, re-spawn roadmapper with revision context, loop until approved.
**If "Review":** Display raw ROADMAP.md, re-ask.

**Commit roadmap** (after approval):
```bash
Workflow_WS_ARG=$(cat .planning/.workflow-ws-arg 2>/dev/null || true)
INIT_ROADMAP=$(workflow_run query init.new-milestone $Workflow_WS_ARG)
if [[ "$INIT_ROADMAP" == @file:* ]]; then INIT_ROADMAP=$(cat "${INIT_ROADMAP#@file:}"); fi
_workflow_field() { node -e "const o=JSON.parse(process.argv[1]); const v=o[process.argv[2]]; process.stdout.write(v==null?'':String(v))" "$1" "$2"; }
ROADMAP_PATH=$(_workflow_field "$INIT_ROADMAP" roadmap_path)
STATE_PATH=$(_workflow_field "$INIT_ROADMAP" state_path)
REQUIREMENTS_PATH=$(_workflow_field "$INIT_ROADMAP" requirements_path)
workflow_run query commit "docs: create milestone v[X.Y] roadmap ([N] phases)" --files "$ROADMAP_PATH" "$STATE_PATH" "$REQUIREMENTS_PATH"
# #4456: true last consumer of the persisted --ws in this workflow — the
# round-trip file is no longer needed after this commit.
rm -f .planning/.workflow-ws-arg 2>/dev/null || true
```

## 10.5. Link Pending Todos to Roadmap Phases

After roadmap approval, scan pending todos against the newly approved phases. For each todo whose scope matches a phase, tag it with `resolves_phase: N` in its YAML frontmatter.

**Check for pending todos:**
```bash
PENDING_TODOS=$(ls .planning/todos/pending/*.md 2>/dev/null | head -50)
```

**If no pending todos exist:** Skip this step silently.

**If pending todos exist:**

Read the approved ROADMAP.md and extract the phase list: phase number, phase name, goal, and requirement IDs.

For each pending todo, compare:
- The todo's `title` and `area` frontmatter fields
- The todo body (Problem and Solution sections)

Against each phase's:
- Phase goal
- Requirement IDs and descriptions

**Match criteria (best-effort — do not over-match):** A todo is considered resolved by a phase if the phase's goal or requirements directly describe implementing the same feature, area, or capability as the todo. Narrow, specific todos with concrete scopes are the best candidates. Vague or cross-cutting todos should be left unlinked.

**For each matched todo**, add `resolves_phase: [N]` to the YAML frontmatter block (after the existing fields):
```yaml
---
created: [existing]
title: [existing]
area: [existing]
resolves_phase: [N]
files: [existing]
---
```

**Only modify todos that have a clear, confident match.** Leave unmatched todos unmodified.

**If any todos were linked:**
```bash
workflow_run query commit "docs: tag [count] pending todos with resolves_phase after milestone v[X.Y] roadmap" --files .planning/todos/pending/*.md
```

Print a summary:
```
◆ Linked [N] pending todos to roadmap phases:
  → [todo title] → Phase [N]: [Phase Name]
  (Leave [M] unmatched todos in pending/)
```

## 11. Done

```
### Workflow ► MILESTONE INITIALIZED ✓

**Milestone v[X.Y]: [Name]**

| Artifact       | Location                    |
|----------------|-----------------------------|
| Project        | `.planning/PROJECT.md`      |
| Research       | `.planning/research/`       |
| Requirements   | `.planning/REQUIREMENTS.md` |
| Roadmap        | `.planning/ROADMAP.md`      |

**[N] phases** | **[X] requirements** | Ready to build ✓

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Phase [N]: [Phase Name]** — [Goal]

`/clear` then:

`/workflow:discuss-phase [N] ${Workflow_WS}` — gather context and clarify approach

Also: `/workflow:plan-phase [N] ${Workflow_WS}` — skip discussion, plan directly
```

</process>

<success_criteria>
- [ ] PROJECT.md updated with Current Milestone section (skipped when a workstream is active — shared file, see Step 4)
- [ ] STATE.md reset for new milestone
- [ ] MILESTONE-CONTEXT.md consumed and deleted (if existed)
- [ ] Research completed (if selected) — 4 parallel agents, milestone-aware
- [ ] Requirements gathered and scoped per category
- [ ] REQUIREMENTS.md created with REQ-IDs
- [ ] roadmapper spawned with phase numbering context
- [ ] Roadmap files written immediately (not draft)
- [ ] User feedback incorporated (if any)
- [ ] Phase numbering mode respected (continued or reset)
- [ ] All commits made (if planning docs committed)
- [ ] Pending todos scanned for phase matches; matched todos tagged with `resolves_phase: N`
- [ ] User knows next step: `/workflow:discuss-phase [N] ${Workflow_WS}`

**Atomic commits:** Each phase commits its artifacts immediately.
</success_criteria>
</output>


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
