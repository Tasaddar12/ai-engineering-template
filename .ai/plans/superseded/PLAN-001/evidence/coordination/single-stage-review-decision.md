# Single task review stage for the remaining implementation

On 2026-09-08 the user instructed:

> For the remaining tasks lets do a single review stage. This is to reduce time and credit usage. We will do final reviews after and plan changes after to further refine everything.

This instruction supersedes the two-stage manual development review schedule for
all remaining PLAN-001 tasks, including current candidates and bounded repairs.
It takes precedence over earlier coordination briefs and recovery recommendations
where they require separate task R1 and R2 invocations. Preserve those finalized
records unchanged as history; do not rewrite their verdicts or claim a missing
review occurred.

Use one independent Astra/xhigh review per remaining task, separate from its
Sol/xhigh implementer. The reviewer checks the existing eleven implementation
items, including relevant accepted interfaces, task boundaries and consumer
compatibility in that pass. Keep the existing `implementation` report stage and
R1 checklist identifiers. Do not dispatch a separate task consistency review.

When that review finds a concrete defect, the owner makes the scoped correction
and adds the required tracked regression. Validate the changed candidate and
obtain focused verification from the independent reviewer, preferably by resuming
that reviewer. Retain a new report for the exact corrected candidate; reference
the earlier full review and explain which checks the change affects. Unaffected
checks may reuse verified reasoning and unchanged evidence rather than trigger
another broad review. This is continuation of the single stage, not self-approval.
If the reviewer is unavailable, a replacement receives that bounded history.

Candidate identity, source scope, accepted dependencies, actual nonzero validation,
honest model provenance and unresolved defect handling still matter. A known
failed report for the exact candidate prevents acceptance. Changed code needs
current evidence; historical passing reviews do not approve it automatically.
Review and invocation counts remain cumulative. Existing structural and authority
boundaries remain in force; ordinary task fixes do not require an extra review
stage or a new graph merely because their source changed.

The coordinator helper now requires one passing implementation report and binds
this decision into newly formed candidate contexts. Earlier accepted tasks retain
their original two-stage acceptance history. The current TASK-007 review finishes
on its unchanged candidate before any correction or new checkpoint.

After all tasks are assembled, run the combined tests, clean checkout and package
checks, then final independent reviews of the complete project. Broader plan and
design refinements follow those results. This change concerns how this development
run is reviewed; it does not silently edit the toolkit's frozen runtime review
ports, schemas or approved product graph. Record any proposed product changes for
that later refinement work.
