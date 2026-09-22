# Project planning and management

This directory stores project-specific records. The reusable agent machinery lives
in [`.ai`](../.ai/README.md); full authoring templates live in [`.ai/templates`](../.ai/templates/README.md).
Preserve existing project records. Onboarding completes missing context from
actual source, documentation and user intent.

| Location | Stores | Owner |
|---|---|---|
| `PROJECT.md` | Purpose, users, success and boundaries | Human intent, recorded during onboarding; Key Decisions by `project.add-decision` |
| `REQUIREMENTS.md` | Identified desired outcomes and traceability | Prose by the orchestrator; the Traceability Status column by `requirements.*` |
| `ROADMAP.md` | Phase goals, order, plan checklists, milestones and progress | Runtime `phase.*`, `roadmap.*` and `milestone.*` verbs |
| `STATE.md` | Position, decisions, blockers and session continuity | Runtime `state.*` verbs; counters derived from ROADMAP.md. A bounded digest, not an archive |
| `config.yaml` | Commit behavior, model overrides and the project's real checks | Project setup |
| `phases/NN-name/` | Context, research, PLAN/SUMMARY pairs and verification | Assigned agents; the orchestrator integrates |
| `codebase/` | Revision-specific maps and research on existing implementation | codebase-mapper; freshness derived from git by `codebase.status` |
| `specs/` | Verified current behavior | Assigned author or doc-writer |
| `decisions/` | Significant architectural decisions and supersession | Recorded human decisions |
| `todos/pending/`, `todos/completed/` | Captured ideas not yet scoped into a phase | Runtime `todo.add` and `todo.complete` |
| `quick/YYMMDD-NNN-slug/` | Small changes tracked outside the roadmap | Runtime `quick.create` and `quick.update` |
| `MILESTONES.md`, `milestones/` | What each milestone shipped, and its long-form summary | Runtime `milestone.complete`; summaries on `--write` |

Optional workflow artifacts, including project research and milestones, use
destinations described by their complete templates. Their presence does not
start an agent or authorize a change.

Everything the runtime records is a tracked project record, so a fresh clone
inherits the full picture. The only untracked artifact is `.planning/.lock`,
which serializes concurrent writers for the duration of a single write.

`phase_run query planning.validate` reports where these records have drifted from
their templates. It is warn-only — `/progress`, `/verify-work` and
`/complete-milestone` run it and present the findings without blocking on them.

Start with [onboarding](../.ai/commands/onboard.md), then use the
[workflow guide](../.ai/guides/PHASE-WORKFLOW.md) and [feature reference](../.ai/guides/WORKFLOW-FEATURES.md).
