# One owner per fact

| Fact | Owner | Other files should |
| --- | --- | --- |
| Starting context and navigation through engagement contracts | RULES.md | Follow its links to the owning policy. |
| Firm action/approval requirements | policies/approval.md | Apply the policy; do not grant exceptions implicitly. |
| Record mutability, amendment obligations and history requirements | policies/records.md | Reference its requirements. |
| Parallel assignment and concurrent ownership requirements | policies/parallel-execution.md | Apply the requirements before each wave. |
| Worktree, validation, review and Git delivery requirements | policies/execution.md | Apply them in the relevant workflow. |
| Paths, filename formats and ID patterns | config.yaml | Use the configured values. |
| Project purpose, users, desired outcome and background | state/PROJECT.md | Link to stable project context. |
| Current implemented behavior and limitations | specs/SPEC-*.md, split by declared scope | Link to the one spec owning the behavior. |
| Why an approach was chosen | decisions/ADR-*.md | Link to the rationale. |
| Why an accepted contract changed | decisions/amendments/AMD-*.md | Link to the amendment. |
| Unconfirmed observations, waiting questions and suspected drift | plans/intake/INTAKE-*.md | Link evidence and any confirmed FIX or planned successor. |
| Confirmed defect, expected behavior and repair outcome | fixes/{open,done}/FIX-*.md | Reference the defect; do not duplicate intake/research evidence. |
| Fix lifecycle transitions | fixes/README.md | Follow its open/done conventions. |
| Investigation question, sources, findings and uncertainty | research/RES-*.md | Cite the research; do not treat a recommendation as a decision. |
| Approved change scope, acceptance and task checklist | Selected PLAN; for a bounded repair without a PLAN, its FIX | Reference the single execution owner. |
| Current focus, next action and blockers | state/STATE.md | Read live coordination. |
| Historical events and recorded user decisions | state/journal/{date}.md | Append and link; do not rewrite earlier entries. |
| Role-specific responsibilities and reporting | agents/{role}.md | Follow policies for authority. |
| Which operation an entry point selects | commands/{operation}.md | Follow its linked workflow. |
| Steps and handoffs for an operation | workflows/{operation}.md | Link to the procedure instead of copying it. |
| PASS/FAIL criteria for a transition | gates/{gate}.md | Evaluate those criteria against current evidence. |
| A subject's gate results and review evidence | Its PLAN validation section; otherwise FIX or INTAKE. New verification of a historical done plan belongs in an appended journal entry | Link to the dated evaluation and subject revision. |
| When a manual checkpoint runs | hooks/README.md | Link to the gate; do not duplicate its criteria. |
| Required document/report sections | templates/{type}.md | Instantiate the template. |
| Source revisions, remote refs and PR merge state | Git and GitHub | Observe directly; record dated observations. |

This map assigns ownership; it does not make stale content correct. Report conflicting
facts as drift. A new spec declares bounded ownership that does not overlap an existing
spec. A gate checks a policy; it cannot weaken that policy.
