# AI Engineering Framework architecture

The Python 3.11+ package coordinates bounded engineering work through durable repository artifacts. `python -m ai_engineering plan implement PLAN-002` is the primary execution entry point; installation also provides `ai`.

| Authority | Purpose |
| --- | --- |
| Git | Source, revisions, branches, worktrees, merge reality |
| `.ai/STATE.yaml` | Compact index of intent, active work, delivery/review state, blockers and next actions |
| Markdown plans/tasks/features | Desired change, small planning units, executable batches |
| Markdown handoffs/reviews | Communication and approval/failure evidence |
| ADRs/research | Rationale and dated evidence |
| YAML configuration | Limits, models, agent definitions, constraints and commands |

Tasks are batched into features by the Work Decomposition Agent. It checks clarity, acceptance, size, prerequisites, file ownership and schema/interface conflicts. Deterministic validation checks exact coverage, both DAGs, bounded batches and conflict-free parallel waves. A feature owns one branch/worktree and implementation session. Independent features run concurrently up to configured limits; dependencies wait until their code is available on the selected base. Approval and PR creation alone are not merge evidence.

The coordinator is the sole state writer, using a process lock and atomic file replacement. All subprocesses use the central Python runner. Agents receive relevant references, not all repository knowledge. Roles and permissions are separate from model/provider/reasoning profiles. Reusable templates and role definitions are package assets under `src/ai_engineering/templates/` and `src/ai_engineering/definitions/`, installed as editable project assets under `.ai/`.

Implementation produces a handoff and actual validation. One independent Critical Change Reviewer checks the complete diff for correctness, relevant security and documentation. The only verdicts are PASS and CHANGES_REQUIRED. Reports bind to the reviewed revision; repair reruns validation and the full review. There is no second stage or mandatory plan-wide review. External writes need configured authority. Changed code invalidates earlier approval.

Recovery fixes structural mistakes through reasoned task/feature revision, supersession, decomposition and resumed scheduling. Ordinary defects return to the same implementer. Bugs use investigation, root cause, fix worktree, regression test, validation, critical review and PR; substantial architecture becomes a plan. Bounded retry budgets expose blockers without inventing success.

The provider-neutral command adapter requires a configured trusted bridge and explicit model profile before real dispatch. Controlled test providers are not real model execution. Permission declarations are enforced at framework tool boundaries; arbitrary provider processes require their own containment and cannot be made safe by prompts alone.

Reconciliation compares index/artifacts with Git, reporting missing/unknown worktrees, changed branches/revisions, stale reviews and merge observations. It never invents approvals. Cleanup requires a checked managed path, clean files including ignored-data checks, no active owner and merge confirmation or explicit supersession/abandonment with a retained branch. Unknown worktrees are preserved; age and force deletion are never used.

See `.ai/plans/active/PLAN-002.md` for Python boundaries and `docs/workflows.md` for workflows. The 2026-09-08 reset audit is in `.ai/archive/2026-09-08/`; PLAN-001 is in `.ai/plans/superseded/PLAN-001/`. Compatible subprocess, containment, ownership, graph and installation algorithms are adapted from the archived Python implementation. Legacy schemas, roles and provider namespaces are excluded from current packaging.
