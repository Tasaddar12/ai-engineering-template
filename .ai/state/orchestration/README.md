---
tier: contract
authority: agent
title: Run and track evidence
---
> Contract: amend with evidence inside the approved scope.

# Run and track evidence

Use [ORCH-RUN.md](../../templates/ORCH-RUN.md) for the run board. Render it
with `python .ai/runtime/render_record.py TEMPLATE DESTINATION`; the helper
prints source-relative content to stdout and creates no record. Save successful
output in the assigned worktree, and prepare incoming links before final review.
and [orchestrate-track](../../commands/orchestrate-track.md) for track evidence.

Use [orchestrate](../../commands/orchestrate.md) for the run board and shared
state procedure, and each [agent file](../../agents/README.md) for role scope.
[RULES](../../RULES.md#delivery-recovery-and-cleanup) defines shared recovery
and delivery policy, including [related-task batching](../../RULES.md#related-work-and-delivery-ownership).

[Review](../../agents/track-reviewer.md) owns the cold packet and exclusions.
[Parallel execution](../../commands/orchestrate.md) owns scheduling.
The [runtime](../../runtime/README.md) starts worker processes and stores durable
phase/merge receipts in the Git common directory. Runtime mode uses those
receipts instead of track-written review logs. It audits declared paths and
resources; host permissions still provide sandboxing. See [Review and documentation](../../RULES.md#review-and-documentation) for
the review sequence and [Definition of done](../../RULES.md#definition-of-done)
for completion.
