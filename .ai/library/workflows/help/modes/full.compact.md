Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

<purpose>
Display the complete Workflow Core command reference. Output ONLY the reference content. Do NOT add project-specific analysis, git status, next-step suggestions, or any commentary beyond the reference.
</purpose>

<reference>
# Workflow Core Command Reference

**Workflow Core** (Git. Ship. Done.) creates hierarchical project plans optimized for solo agentic development with Claude Code.

## Quick Start

1. `/workflow:new-project` — Initialize project (research, requirements, roadmap)
2. `/workflow:plan-phase 1` — Create detailed plan for first phase
3. `/workflow:execute-phase 1` — Execute the phase

Not sure where to start? `/workflow:next` reads your project state and routes you to the right next action.

### Smart Entry

**`/workflow:next`** — State-aware front door. Detects your situation via `workflow-tools smart-entry` (no-project, paused, blocked, planning, executing, needs-verify, idle, complete, …) and shows a menu with one recommended action. Launcher only; falls back to `/workflow:progress`.

Usage: `/workflow:next`

## Staying Updated

```bash
npx @openworkflow/workflow-core@latest
```

## Core Workflow

```text
/workflow:new-project → /workflow:plan-phase → /workflow:execute-phase → repeat
```

### Project Initialization

**`/workflow:new-project`** — Unified flow from idea to ready-for-planning: deep questioning, optional domain research (4 parallel researchers), requirements with v1/v2/out-of-scope scoping, roadmap with phase breakdown. Creates `.planning/`: `PROJECT.md`, `config.json`, `research/`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`.

Usage: `/workflow:new-project`

**`/workflow:onboard [--fast] [--text]`** — Guides first-time onboarding for an existing codebase: detects brownfield state, routes through `/workflow:map-codebase` → `/workflow:ingest-docs` → `/workflow:new-project` in safe order, idempotent.

Usage: `/workflow:onboard`

**`/workflow:map-codebase [--fast] [--focus <area>] [--query <term>]`** — Maps an existing codebase with parallel Explore agents into `.planning/codebase/` (stack, architecture, structure, conventions, testing, integrations, concerns). `--fast` for rapid assessment, `--query` to search the intel index.

Usage: `/workflow:map-codebase`

### Phase Planning

**`/workflow:discuss-phase <number> [--chain | --analyze | --power | --assumptions] [--batch[=N]]`** — Articulate your vision for a phase before planning; creates CONTEXT.md. `--chain` chained flow, `--analyze` assumption analysis, `--power` extended questions, `--assumptions` surfaces implementation assumptions non-interactively, `--batch` groups 2-5 questions per turn.

Usage: `/workflow:discuss-phase 2`
Usage: `/workflow:discuss-phase 2 --batch=3`

**`/workflow:plan-phase <number> [--research] [--skip-research] [--research-phase <N>] [--view] [--gaps] [--skip-verify] [--skip-ui] [--prd <file>] [--ingest <path-or-glob>] [--ingest-format <auto|nygard|madr|narrative>] [--reviews] [--text] [--bounce] [--skip-bounce] [--chunked] [--tdd] [--mvp] [--granularity <coarse|standard|fine>] [--no-tracer] [--no-reversibility-gates]`** — Creates `.planning/phases/XX-phase-name/XX-YY-PLAN.md` with concrete tasks, verification criteria, and success measures (multiple plans per phase supported).

Key flags: `--research-phase <N>` runs research only and writes `RESEARCH.md` then exits (replaces the deleted `workflow-research-phase`; `--research` forces refresh, `--view` prints existing without spawning). `--gaps` closes gaps from a prior plan-check. `--ingest`/`--ingest-format` pre-ingest external ADRs/PRDs/SPECs (see PRD Express Path). `--bounce`/`--skip-bounce` toggle the optional external refinement pass (`workflow.plan_bounce`). `--chunked` splits planning into short, individually-committed passes for crash resilience (`workflow.plan_chunked`), resumable. `--tdd` tests-before-code order. `--mvp` adds user story + Walking Skeleton (see `/workflow:mvp-phase`). `--granularity` overrides resolved plan granularity. `--no-tracer` opts out of tracer-first ordering. `--no-reversibility-gates` suppresses the one-way-door checkpoint for unattended runs.

Usage: `/workflow:plan-phase 1`
Result: Creates `.planning/phases/01-foundation/01-01-PLAN.md`

**PRD Express Path:** Pass `--prd path/to/requirements.md` to skip discuss-phase — your PRD becomes locked decisions in CONTEXT.md.

### Execution

**`/workflow:execute-phase <phase-number> [--wave N] [--gaps-only] [--tdd]`** — Groups plans by wave (frontmatter), executes sequentially with parallel plans per wave via Task tool, verifies phase goal, updates REQUIREMENTS/ROADMAP/STATE. `--wave N` runs only wave N; `--gaps-only` re-runs verifier-flagged plans; `--tdd` enforces test-driven order.

Usage: `/workflow:execute-phase 5`
Usage: `/workflow:execute-phase 5 --wave 2`

### Smart Router

**`/workflow:progress --do "<description>"`** — Routes freeform text to the best-matching Workflow command; asks you to pick between top matches on ambiguity. Never does the work itself.

Usage: `/workflow:progress --do "fix the login button"`

### Quick Mode

**`/workflow:quick [--full] [--validate] [--discuss] [--research]`** — Small ad-hoc tasks in `.planning/quick/` (updates STATE.md, not ROADMAP.md); spawns planner+executor only by default. `--full` = discuss+research+plan-check+verify; `--validate` = plan-check + post-execution verify; `--discuss`/`--research` add one step each; flags compose.

Usage: `/workflow:quick`
Result: Creates `.planning/quick/NNN-slug/PLAN.md`, `.planning/quick/NNN-slug/NNN-slug-SUMMARY.md`

---

**`/workflow:quick-batch [--file <path>] [--jobs auto|N] [--validate] [--research] [--resume <batch-id>] [task list]`** — Batches several quick-shaped tasks (inline or `--file`); one coordinator plans/dispatches/merges. `--jobs` caps concurrency, `--resume` dispatches only eligible items; `--discuss`/`--full` are rejected.

Usage: `/workflow:quick-batch --jobs 3 --validate`
Result: Per-item artifacts under `.planning/quick/`; batch state in `.planning/quick-batches/<batch-id>/BATCH.json`

---

**`/workflow:fast [description]`** — Trivial task inline, no subagent, no planning files: typo fixes, config changes, ≤3 file edits (redirects to `/workflow:quick` above that). Atomic commit, logs to STATE.md.

Usage: `/workflow:fast "fix the typo in README"`

### Roadmap Management

**`/workflow:phase <description>`** — Appends a new phase (next sequential number) to ROADMAP.md.

Usage: `/workflow:phase "Add admin dashboard"`

**`/workflow:phase --insert <after> <description>`** — Inserts a decimal phase (e.g. 7.1) between existing phases for discovered mid-milestone work.

Usage: `/workflow:phase --insert 7 "Fix critical auth bug"`
Result: Creates Phase 7.1

**`/workflow:phase --remove <number>`** — Deletes a future (unstarted) phase and renumbers subsequent phases; git commit preserves history.

Usage: `/workflow:phase --remove 17`
Result: Phase 17 deleted, phases 18-20 become 17-19

**`/workflow:phase --edit <number> [--force]`** — Edits title/description/requirements/dependencies in place; `--force` allows editing already-started phases.

### Milestone Management

**`/workflow:new-milestone <name>`** — Mirrors `/workflow:new-project`'s flow for brownfield (existing PROJECT.md): questioning, optional research, requirements, roadmap. `--reset-phase-numbers` restarts at Phase 1 (archives old dirs first); `--ws <name>` scopes to a workstream, skipping the shared PROJECT.md write.

Usage: `/workflow:new-milestone "v2.0 Features"`

**`/workflow:complete-milestone <version>`** — Archives to MILESTONES.md + milestones/ dir, tags the release, preps workspace for next version.

Usage: `/workflow:complete-milestone 1.0.0`

### Progress Tracking

**`/workflow:progress [--next | --forensic | --do "<description>"]`** — Progress bar, SUMMARY recap, current position, key decisions, offers to execute/create next plan, detects 100% completion.

Modes: default (report+routing) · `--next` (auto-advance; `--force` bypasses safety gates) · `--next --auto` (chains steps until milestone completion or a blocking decision) · `--next --converge` (routes planning through `/workflow:plan-review-convergence`, requires `workflow.plan_review_convergence`; reviewer flags and `--max-cycles` forward) · `--forensic` (appends a 6-check integrity audit) · `--do "<text>"` (smart router, see above).

Usage: `/workflow:progress`
Usage: `/workflow:progress --next --auto`

### Session Management

**`/workflow:resume-work`** — Reads STATE.md, shows position and recent progress, offers next actions.

Usage: `/workflow:resume-work`

**`/workflow:pause-work [--report]`** — Creates a `.continue-here` handoff, updates STATE.md's session-continuity section. `--report` also writes a post-session summary to `.planning/reports/`.

Usage: `/workflow:pause-work`

### Debugging

**`/workflow:debug [issue description] [--diagnose]`** — Adaptive-question symptom gathering, `.planning/debug/[slug].md` tracking, scientific-method investigation, survives `/clear` (resume with no args), archives resolved issues. `--diagnose` runs a one-shot pass without a persistent session.

Usage: `/workflow:debug "login button doesn't work"`

### Spiking & Sketching

**`/workflow:spike [idea] [--quick]`** — Decomposes into 2-5 risk-ordered Given/When/Then experiments, builds minimum code, captures VALIDATED/INVALIDATED/PARTIAL, saves to `.planning/spikes/` with MANIFEST.md. Works in any repo, no `/workflow:new-project` needed. `--quick` skips decomposition.

Usage: `/workflow:spike "can we stream LLM output over WebSockets?"`

**`/workflow:sketch [idea] [--quick]`** — Conversational mood intake, 2-3 tabbed HTML variants per sketch, shared CSS theme system, saves to `.planning/sketches/` with MANIFEST.md. `--quick` skips mood intake.

Usage: `/workflow:sketch "dashboard layout for the admin panel"`

**`/workflow:spike --wrap-up`** — Curates spikes one-at-a-time (include/exclude/partial/UAT), generates a project skill under `./.claude/skills/spike-findings-[project]/`, writes `.planning/spikes/WRAP-UP-SUMMARY.md`, adds a CLAUDE.md auto-load line.

Usage: `/workflow:spike --wrap-up`

**`/workflow:sketch --wrap-up`** — Same curation flow for sketches, generating `./.claude/skills/sketch-findings-[project]/` with design decisions/CSS/HTML structures.

Usage: `/workflow:sketch --wrap-up`

### Capturing Ideas, Notes, and Todos

**`/workflow:capture [description]`** — Extracts context from conversation (or uses the given text), creates a todo in `.planning/todos/pending/`, infers area, checks duplicates, updates STATE.md count.

Usage: `/workflow:capture Add auth token refresh`

**`/workflow:capture --note <text>`** — Zero-friction timestamped note to `.planning/notes/` (or `~/.claude/notes/` globally). Subcommands: append (default), list, promote (note → todo). Works without a project.

Usage: `/workflow:capture --note refactor the hook system`
Usage: `/workflow:capture --note promote 3`

**`/workflow:capture --list [area]`** — Lists pending todos (optional area filter), loads full context for the one you pick, routes to work-now/add-to-phase/brainstorm, moves it to completed/ on start.

Usage: `/workflow:capture --list api`

**`/workflow:capture --list-seeds [status]`** — Read-only listing of captured seeds (ID, status, scope, trigger, title); optional status filter. Enrich via `/workflow:capture --seed --enrich SEED-NNN`.

Usage: `/workflow:capture --list-seeds dormant`

### User Acceptance Testing

**`/workflow:verify-work [phase]`** — Extracts testable deliverables from SUMMARY.md, presents tests one at a time (yes/no), auto-diagnoses failures into fix plans, ready for re-execution.

Usage: `/workflow:verify-work 3`

### Ship Work

**`/workflow:ship [phase]`** — Pushes branch, opens a PR with a body from SUMMARY/VERIFICATION/REQUIREMENTS, optionally requests review, updates STATE.md. Requires a verified phase and authenticated `gh`.

Usage: `/workflow:ship 4` or `/workflow:ship 4 --draft`

---

**`/workflow:review --phase N [--gemini] [--claude] [--codex] [--coderabbit] [--opencode] [--qwen] [--cursor] [--agy] [--all]`** — Detects available external AI CLIs, each independently reviews the phase's plans with the same structured prompt (CodeRabbit reviews the live diff, up to ~5 min), produces REVIEWS.md with consensus. Feed back via `/workflow:plan-phase N --reviews`.

Usage: `/workflow:review --phase 3 --all`

---

**`/workflow:pr-branch [target]`** — Classifies commits (code-only/planning-only/mixed), cherry-picks code onto a clean branch so reviewers see no `.planning/` artifacts.

Usage: `/workflow:pr-branch` or `/workflow:pr-branch main`

---

**`/workflow:capture --seed [idea]`** — Captures a forward-looking idea with WHY/WHEN-to-surface trigger conditions; auto-surfaces during `/workflow:new-milestone` when triggers match.

Usage: `/workflow:capture --seed "add real-time notifications when we build the events system"`

**`/workflow:capture --backlog [description]`** — Adds an idea to the 999.x backlog without committing to the current milestone; promote later via `/workflow:review-backlog`.

Usage: `/workflow:capture --backlog "real-time notifications when events ship"`

---

**`/workflow:audit-uat`** — Cross-phase audit of all outstanding UAT/verification items (pending, skipped, blocked, human_needed), cross-references the codebase for stale docs, produces a prioritized test plan. Run before a new milestone.

Usage: `/workflow:audit-uat`

### Milestone Auditing

**`/workflow:audit-milestone [version]`** — Reads all phase VERIFICATION.md files, checks requirements coverage, spawns an integration checker for cross-phase wiring, creates MILESTONE-AUDIT.md.

Usage: `/workflow:audit-milestone`

### Configuration

**`/workflow:settings`** — Interactively toggles researcher/plan-checker/verifier agents and the model profile (quality/balanced/budget/inherit); updates `.planning/config.json`.

Usage: `/workflow:settings`

**`/workflow:config [--profile <profile> | --advanced | --integrations]`** — `--profile` quick-switches model profile (`quality` = Opus everywhere but verification, `balanced` = Opus planning/Sonnet execution (default), `budget` = Sonnet writing/Haiku research-verification, `inherit` = current session model). `--advanced` = plan bounce, timeouts, branch templates, cross-AI execution. `--integrations` = third-party API keys, code-review CLI routing, agent-skill injection.

Usage: `/workflow:config --profile budget`

**`/workflow:surface [list|status|profile <name>|disable <cluster>|enable <cluster>|reset]`** — Toggles which skills are surfaced without reinstalling: `list`/`status` show enabled/disabled + token cost, `profile <name>` switches base profile (`core`/`standard`/`full`), `disable`/`enable` a cluster, `reset` returns to install-time profile.

Usage: `/workflow:surface profile standard`

### Utility Commands

**`/workflow:cleanup`** — Dry-run then moves completed-milestone phase dirs from `.planning/phases/` to `.planning/milestones/v{X.Y}-phases/`.

Usage: `/workflow:cleanup`

**`/workflow:help [--brief | --full | <topic> | --brief <topic>]`** — `--brief` = ~10-line refresher; no flag = one-page newcomer tour; `--full` = this complete reference; `<topic>` = matching section only (e.g. `/workflow:help debug`); `--brief <topic>` = compact scoped lookup. Every topic output starts with a `**Topic:** \`<alias>\` → \`<heading>\` *(scope: full | compact)*` preamble. See `.ai/library/workflows/help/modes/topic.md` for the alias table.

Usage: `/workflow:help debug`
Usage: `/workflow:help --brief debug`

**`/workflow:update [--sync] [--reapply] [--next | --rc]`** — Shows installed-vs-latest, changelog since your version, breaking changes, confirms before installing. `--sync` syncs managed skills across runtime roots; `--reapply` reapplies local modifications post-update; `--next`/`--rc` installs from the `@next` RC dist-tag (ADR #660) instead of `@latest`.

Usage: `/workflow:update`

## Additional Commands

Every command below is also a live `/workflow-*` slash command, grouped by purpose.

### Discovery & Specification

- **`/workflow:explore`** — Socratic ideation and idea routing before committing to plans.
- **`/workflow:spec-phase <phase> [--auto] [--text]`** — Clarify WHAT a phase delivers with ambiguity scoring; produces SPEC.md before discuss-phase.
- **`/workflow:ai-integration-phase [phase]`** — Generate an AI-SPEC.md design contract for phases building AI systems.
- **`/workflow:ui-phase [phase]`** — Generate UI design contract (UI-SPEC.md) for frontend phases.
- **`/workflow:import --from <filepath> | --from-workflow2`** — Ingest external plans with conflict detection, or reverse-migrate a Workflow-2 project to v1 format.
- **`/workflow:ingest-docs [path] [--mode new|merge] [--manifest <file>] [--resolve auto|interactive]`** — Bootstrap or merge `.planning/` from existing ADRs/PRDs/SPECs/docs.

### Planning & Execution

- **`/workflow:mvp-phase <phase-number>`** — Plans a phase as a vertical MVP slice (user story + SPIDR splitting) before handoff to plan-phase; same end-state as `/workflow:plan-phase --mvp` with a guided intro.
- **`/workflow:ultraplan-phase [phase]`** — [BETA] Offload plan phase to Claude Code's ultraplan cloud; review in browser, import back.
- **`/workflow:plan-review-convergence <phase> [--gemini] [--claude] [--codex] [--coderabbit] [--opencode] [--qwen] [--cursor] [--agy/--antigravity] [--ollama] [--lm-studio] [--llama-cpp] [--kimi-code] [--all] [--text] [--ws <name>] [--max-cycles N]`** — Cross-AI convergence loop: replan with review feedback until no HIGH concerns remain (cloud and local-model reviewers).
- **`/workflow:autonomous [--from N] [--to N] [--only N] [--interactive] [--converge]`** — Runs all remaining phases unattended: discuss → plan → execute per phase; `--converge`/`--cross-ai` routes planning through convergence.

### Quality, Review & Verification

- **`/workflow:code-review <phase> [--depth=quick|standard|deep] [--files file1,file2,...] [--fix [--all] [--auto]]`** — Reviews phase-changed source for bugs, security, quality.
- **`/workflow:secure-phase [phase]`** — Retroactively verifies threat mitigations for a completed phase.
- **`/workflow:validate-phase [phase]`** — Retroactively audits and fills Nyquist validation gaps.
- **`/workflow:ui-review [phase]`** — Retroactive 6-pillar visual audit of implemented frontend code.
- **`/workflow:eval-review [phase]`** — Audits an executed AI phase's evaluation coverage; produces EVAL-REVIEW.md.
- **`/workflow:audit-fix --source <audit-uat> [--severity medium|high|all] [--max N] [--dry-run]`** — Autonomous audit-to-fix: find, classify, fix, test, commit.
- **`/workflow:add-tests <phase> [additional instructions]`** — Generates tests for a completed phase from UAT criteria and implementation.

### Diagnostics & Maintenance

- **`/workflow:health [--repair] [--context]`** — Diagnoses planning-directory health, optionally repairs.
- **`/workflow:forensics [problem description]`** — Post-mortem investigation for failed Workflow workflows.
- **`/workflow:undo --last N | --phase NN | --plan NN-MM`** — Safe git revert using the phase manifest with dependency checks.
- **`/workflow:docs-update [--force] [--verify-only]`** — Generates/updates docs verified against the codebase.
- **`/workflow:extract-learnings <phase>`** — Extracts decisions, lessons, patterns, surprises from phase artifacts.

### Knowledge & Context

- **`/workflow:graphify [build|query <term>|status|diff]`** — Builds/queries/inspects the project knowledge graph in `.planning/graphs/`.
- **`/workflow:mempalace-recall`** — Recalls prior decisions/patterns/surprises from MemPalace before planning.
- **`/workflow:mempalace-capture [artifact-type]`** — Files a phase artifact into MemPalace, mirrors decisions into its temporal KG.
- **`/workflow:thread [list [--open|--resolved] | close <slug> | status <slug> | name | description]`** — Manages persistent context threads across sessions.
- **`/workflow:profile-user [--questionnaire] [--refresh]`** — Generates a developer behavioral profile + Claude-discoverable artifacts.
- **`/workflow:stats`** — Project statistics: phases, plans, requirements, git metrics, timeline.

### Workflow & Orchestration

- **`/workflow:manager [--analyze-deps]`** — Interactive command center for multiple phases from one terminal; `--analyze-deps` scans dependency relationships before parallel execution.
- **`/workflow:workspace [--new | --list | --remove] [name]`** — Creates/lists/removes isolated Workflow workspace environments.
- **`/workflow:workstreams`** — List, create, switch, status, progress, complete, and resume parallel workstreams.
- **`/workflow:review-backlog`** — Reviews and promotes backlog items to the active milestone.
- **`/workflow:milestone-summary [version]`** — Comprehensive project summary from milestone artifacts, for onboarding/review.

### Repository Integration

- **`/workflow:inbox [--issues] [--prs] [--label] [--close-incomplete] [--repo owner/repo]`** — Triages open GitHub issues/PRs against project templates and contribution guidelines.

### Namespace Routers (model-facing meta-skills)

Six skills for two-stage hierarchical routing across 60+ skills; invoke directly to browse a category interactively:

- **`/workflow-context`** — Codebase intelligence (map, graphify, docs, learnings, mempalace).
- **`/workflow-ideate`** — Exploration/capture (explore, sketch, spike, spec, capture).
- **`/workflow-manage`** — Configuration/workspace (workstreams, thread, update, ship, inbox).
- **`/workflow-project`** — Project-lifecycle (milestones, audits, summary).
- **`/workflow-quality`** — Quality gates (code review, debug, audit, security, eval, ui).
- **`/workflow-workflow`** — Phase pipeline (discuss, plan, execute, verify, phase, progress).

## Files & Structure

```text
.planning/
├── PROJECT.md            # Project vision
├── ROADMAP.md            # Current phase breakdown
├── STATE.md              # Project memory & context
├── RETROSPECTIVE.md      # Living retrospective (updated per milestone)
├── config.json           # Workflow mode & gates
├── todos/                # Captured ideas and tasks (pending/, completed/)
├── spikes/               # Spike experiments — MANIFEST.md + NNN-name/ dirs
├── sketches/             # Design sketches — MANIFEST.md, themes/, NNN-name/ dirs
├── debug/                # Active debug sessions (resolved/ archive)
├── milestones/           # Archived roadmap/requirements snapshots + v{X.Y}-phases/
├── codebase/             # Codebase map (brownfield): STACK/ARCHITECTURE/STRUCTURE/
│                         # CONVENTIONS/TESTING/INTEGRATIONS/CONCERNS.md
└── phases/               # 01-foundation/01-01-PLAN.md + -SUMMARY.md, etc.
```

## Workflow Modes

Set during `/workflow:new-project`, changeable anytime in `.planning/config.json`:

- **Interactive** — confirms each major decision, pauses at checkpoints, more guidance.
- **YOLO** — auto-approves most decisions, executes without confirmation, stops only for critical checkpoints.

## Planning Configuration

`.planning/config.json`:

- **`planning.commit_docs`** (default `true`) — `false` keeps planning artifacts local-only (add `.planning/` to `.gitignore`); useful for OSS/client projects wanting private planning.
- **`planning.search_gitignored`** (default `false`) — `true` adds `--no-ignore` to broad ripgrep searches when `.planning/` is gitignored.

```json
{
  "planning": {
    "commit_docs": false,
    "search_gitignored": true
  }
}
```

## Common Workflows

**New project:** `/workflow:new-project` → `/clear` → `/workflow:plan-phase 1` → `/clear` → `/workflow:execute-phase 1`

**Resuming:** `/workflow:progress`

**Urgent mid-milestone work:** `/workflow:phase --insert 5 "Critical security fix"` → `/workflow:plan-phase 5.1` → `/workflow:execute-phase 5.1`

**Completing a milestone:** `/workflow:complete-milestone 1.0.0` → `/clear` → `/workflow:new-milestone`

**Capturing ideas:** `/workflow:capture` (from context) · `/workflow:capture --note ...` (quick note) · `/workflow:capture --seed "..."` (forward-looking) · `/workflow:capture --list` (review)

**Debugging:** `/workflow:debug "symptom"` → (investigate, context fills) → `/clear` → `/workflow:debug` (resumes)

## Getting Help

- Read `.planning/PROJECT.md` for project vision
- Read `.planning/STATE.md` for current context
- Check `.planning/ROADMAP.md` for phase status
- Run `/workflow:progress` to check where you're up to
</reference>


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
