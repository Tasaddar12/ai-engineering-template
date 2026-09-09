# One owner per fact

| Fact | Owner | Other files should |
| --- | --- | --- |
| Rules, approval boundaries, mutability and amendment procedure | RULES.md | Link to the rule; do not redefine it. |
| Paths, filename formats and ID patterns | config.yaml | Use the configured values. |
| Desired project outcome and exclusions | intent/INTENT.md | Link to intent. |
| Current implemented behavior and limitations | specs/SPEC-*.md, split by explicitly declared scope | Link to the one spec that owns the behavior. |
| Why an approach was chosen | decisions/ADR-*.md | Link to its rationale. |
| Why an accepted contract changed | decisions/amendments/AMD-*.md | Link to the amendment. |
| Reported problem, bug or drift evidence | plans/intake/INTAKE-*.md | Reference its report. |
| Approved change scope, acceptance and task checklist | The selected PLAN file | Reference the plan; do not copy its checklist. |
| Current focus, next action and blockers | state/STATE.md | Read the live status. |
| Historical sequence of events and recorded user decisions | state/journal/{date}.md | Append and link; never rewrite history. |
| Role-specific responsibilities and reporting | agents/{role}.md | Follow RULES for authority and link to the role. |
| Steps for a workflow | commands/{workflow}.md | Follow the referenced procedure. |
| Manual gate checkpoints | hooks/README.md | Do not claim executable enforcement exists. |
| Required document sections | templates/{type}.md | Instantiate the template, not a second schema. |
| Source revisions, remote refs, PR merge state | Git and the GitHub PR | Observe directly; journal observations with a date. |

A new spec must declare a bounded scope that does not overlap an existing spec's
ownership. If two files disagree, consult the owner and report the drift in intake.
This map assigns ownership; it does not make a stale owner automatically correct.
