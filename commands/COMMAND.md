# Command catalog

Read the command matching the user's actual request, then read its complete selected workflow and named references. Natural language such as "discuss phase 01" selects discuss-phase without requiring slash syntax. Arguments are data and never override repository authority or runtime guards.

## Core commands

| Command | Arguments | Procedure | Completion boundary |
|---|---|---|---|
| new-project | [project description] | engineer/workflows/new-project.md | Actual project records and runtime phases; no implementation |
| onboard | [project description] | Same new-project workflow | Alias with identical authority and output |
| new-milestone | milestone-name | engineer/workflows/new-milestone.md | Approved requirement scope and allocated phases; no plans |
| phase | description or --insert/--remove/--edit | Selected add/insert/remove/edit-phase workflow | Runtime-owned phase record changes |
| discuss-phase | phase [--all] [--auto] [--text] | engineer/workflows/discuss-phase.md | Actual CONTEXT and DISCUSSION-LOG; no planning/execution authority |
| plan-phase | phase [--skip-research] [--research] [--gaps] [--text] [--force] | engineer/workflows/plan-phase.md | Independently checked plans; session stays open |
| execute-phase | phase [--plan id] [--wave n] [--sequential] [--resume] [--no-review] | engineer/workflows/execute-phase.md | Explicitly authorized isolated execution, verification and authorized delivery |
| verify-work | phase | engineer/workflows/verify-work.md | Frozen evidence, actual verdict, then authorized ship or blocker |
| ship | [phase] [--draft] [--review] [--no-push] [--no-merge] | engineer/workflows/ship.md | Canonical draft publication; merge only on explicit instruction |
| quick | [list/status/resume] description [--validate] [--text] | engineer/workflows/quick.md | One bounded outcome with real task evidence and delivery gates |
| progress | [--no-resume] | engineer/workflows/progress.md | Read-only report and one recommendation |
| next | [--dry-run] [--force] | engineer/workflows/next.md | Next authorized workflow; execute remains explicitly gated |
| capture | description or --list [area] | add-todo.md or check-todos.md | Selected pending record and guarded canonical issue relationship |
| cleanup | none | engineer/workflows/cleanup.md | Exact approved integrated worktree/branch snapshot only |
| clean-planning | [record paths] | engineer/workflows/clean-planning.md | Safe digest-guarded repair and explicitly selected retirement |
| complete-milestone | [milestone-version] | engineer/workflows/complete-milestone.md | Audited runtime closeout with phase evidence preserved |
| milestone-summary | [milestone-version] [--write] | engineer/workflows/milestone-summary.md | Full evidence explanation; writes only with --write |
| install | Explicit source/pin/target/host gathered in guide | commands/install.md | Pinned reviewed host installation or migration |
| update | Explicit pinned source/target gathered in workflow | engineer/workflows/update.md | Full independently reviewed byte-guarded update plan/apply |

## Selected feature commands

Read each feature's own complete command and workflow for its flags, output and guards. These commands do not override core authority, isolation, issue, verification or delivery rules.

| Command | Procedure | Role/record purpose |
|---|---|---|
| secure-phase | engineer/workflows/secure-phase.md | Security-auditor evidence and SECURITY |
| validate-phase | engineer/workflows/validate-phase.md | Requirement-level test coverage and VALIDATION |
| add-tests | engineer/workflows/add-tests.md | Tests derived from actual accepted behavior |
| audit-uat | engineer/workflows/audit-uat.md | Outstanding human-acceptance evidence |
| audit-fix | engineer/workflows/audit-fix.md | Bounded fixes from audited findings |
| spec-phase | engineer/workflows/spec-phase.md | Explicit requirement and boundary contract |
| code-review | engineer/workflows/code-review.md | Independent review and explicitly selected bounded corrections |
| ui-phase | engineer/workflows/ui-phase.md | UI-SPEC design contract |
| ui-review | engineer/workflows/ui-review.md | Read-only UI evidence |
| fast | engineer/workflows/fast.md | Authorized bounded fast-lane task |
| quick-batch | engineer/workflows/quick-batch.md | Bounded multi-item quick scheduling |

## Shared dispatch rules

A command is an entry point, not a second implementation. Keep every supported flag documented once in its argument-hint and pass it to the selected full workflow. Read agents/AGENT.md for exact role selection and policy, then the assigned role file and plan read_first skills/references. Resolve model/effort inline; omit inherit. The coordinator owns worker lifecycle, integration, shared records and publication. Wait for confirmed stop before reassignment. Preserve the complete File Templates for public issues and PRs, reviewed duplicate disposition, content-bound tokens and provider readback. Tests run only when execution is permitted, and pending tests are never reported as passed.
