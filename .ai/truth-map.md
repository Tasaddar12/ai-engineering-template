---
tier: contract
authority: agent
title: One owner per fact
---
> Contract: link to the owner; reconcile ownership before changing copies.

# One owner per fact

| Fact | Owner |
| --- | --- |
| Purpose, non-goals and hard constraints | state/PROJECT.md |
| Entry point and engagement protocol | RULES.md |
| User authority and action boundaries | policies/approval.md |
| Mutability, amendments, tense and record routing | policies/records.md |
| Validation, Git delivery and cleanup requirements | policies/execution.md |
| Concurrent ownership requirements | policies/parallel-execution.md |
| Paths, ID formats and operating settings | config.yaml |
| Current correct behavior and acceptance | specs/SPEC-*.md by declared scope |
| Behavior intended but not built | Selected PLAN's Contract changes |
| How implementation works | Source and tests; link rather than restate |
| Why a decision was made | Accepted ADR; superseded rationale stays intact |
| Why a contract changed and its old wording | decisions/amendments/AMD-*.md |
| What was said in a meeting | decisions/meetings/MEET-*.md |
| Proposed scope, dependencies and task order | Selected PLAN |
| A confirmed defect and its repair proof | Selected FIX |
| Unconfirmed observations and waiting questions | Selected INTAKE |
| PLAN/FIX lifecycle stage | Its directory alone |
| Current focus, blockers and linked drift | state/STATE.md |
| Historical events and user decisions | state/journal/{date}.md |
| Investigation sources, findings and uncertainty | research/RES-*.md |
| Run schedule, reservations and assignments | state/orchestration/ORCH-*.md |
| A track's review rounds and terminal report | Its run's track evidence file |
| Role responsibilities and write scope | agents/{role}.md |
| Workflow steps and handoffs | workflows/{operation}.md |
| Operation selected by a command | commands/{operation}.md |
| PASS/FAIL transition criteria | gates/{gate}.md |
| Gate/test/review evidence for a subject | Selected PLAN/FIX evidence section |
| New evidence concerning a historical record | Appended journal entry |
| Checkpoint timing | hooks/README.md |
| Required report fields | templates/{type}.md |
| Revisions, branch tips and merge state | Git and the hosting service |

Specs own behavior, not their own history. Plans own intended changes, not
proof they shipped. Research and meetings own evidence, not permission.
A status report is a dated view of these owners, not another database.

Declare a bounded scope for each new SPEC. If two specs own the same fact,
choose its owner and link the other. Code alone cannot establish which side
of a contradiction is correct; use the record policy's evidence protocol.
