# Project planning and management

This directory stores project-specific records. The reusable agent machinery lives
in [`.ai`](../.ai/README.md); full authoring templates live in [`.ai/templates`](../.ai/templates/README.md).
Leave the adopting project's identity unfilled until onboarding records real intent.

| Location | Stores | Owner |
|---|---|---|
| `PROJECT.md` | Purpose, users, success and boundaries | Human intent, recorded by coordinator |
| `REQUIREMENTS.md` | Identified desired outcomes and traceability | Coordinator |
| `ROADMAP.md` | Phase goals, order, dependencies and navigation | Coordinator |
| `STATE.md` | Compact derived continuation view | Coordinator through explicit sync |
| `config.yaml` | Python worker routes, capacity and actual checks | Project setup |
| `phases/NN-name/` | Context, research, PLAN/SUMMARY pairs, verification and UAT | Assigned authors; coordinator integrates |
| `codebase/` | Revision-specific maps and research on existing implementation | Assigned researcher |
| `specs/` | Verified current behavior | Assigned author/documentor |
| `decisions/` | Significant architectural decisions and supersession | Recorded human decisions |
| `maintenance/` | Explicitly requested work on this reusable template | Assigned maintenance coordinator |

Optional upstream artifacts, including project research, debugging, design,
milestones and retrospectives, use destinations described by their complete
templates. Their presence does not start an agent or authorize a change.

Operational locks, launch receipts, process results and checkpoints remain in the
Git common directory, outside tracked planning records. Worktrees remain under
the primary checkout's ignored `.worktrees/`. Neither location is a replacement
for committed source, summaries or verification reports.

Start with [onboarding](../.ai/commands/onboard.md), then use the
[workflow guide](../docs/PHASE-WORKFLOW.md) and [feature reference](../docs/WORKFLOW-FEATURES.md).
