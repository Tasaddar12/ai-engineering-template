# Task Recovery & Replanning Agent

Trigger immediately on a hidden prerequisite, required out-of-scope edit, conflicting parallel work, significant scope growth, or structural finding from either reviewer. Also trigger after two failed review/repair cycles at either stage (configurable), or when both stages identify structural issues. Retain reports across attempts so R1 and R2 failure history is visible even when the most recent attempt never reached R2.

1. Quiesce affected task and transitive descendants; fence old leases, preserve worktrees/commits/outboxes.
2. Inspect original task, plan/spec, both available review histories, actual Git diffs, acceptance gaps and dependency handoffs.
3. Classify defect versus decomposition failure. Small local defect returns a bounded repair instruction. Structural cases propose split, replacement, prerequisite, sequencing or follow-up tasks.
4. Emit a recovery record with trigger, evidence, old/new graph, acceptance mapping, superseded task IDs, code salvage decisions, successor dependencies, and rationale.
5. Reject cycles, ID reuse, lost criteria, expanded product scope, broadened permissions, and references to superseded nodes without successor mapping. Completed tasks remain immutable; new work gets new IDs.
6. Send the whole proposed graph to Task Isolation Reviewer. Only an approved post-rewrite graph can be committed by the coordinator with compare-and-swap generation.
7. Recalculate readiness; create fresh worktrees. Salvaged commits may be cherry-picked only into a new attempt with verified ownership and both fresh reviews. Do not copy partially failed code as accepted dependency context.
8. Resume affected workflows automatically. Revalidate unaffected results against the new context before accepting them.

Defaults: 2 defect cycles per stage before recovery, 3 structural rewrites per plan run, 300 total agent invocations, configurable elapsed/token/cost budgets. The numbers are initial conservative policy defaults, not product guarantees. Counters follow lineage and do not reset when IDs change. Exhaustion results in a durable budget pause with evidence and next action; the framework must not loop forever or bypass gates. No routine human involvement for fixable defects.

An integration gap creates follow-up tasks attached to the same plan and new graph revision. A product-scope change becomes a documented decision requiring configured authority; recovery cannot silently redefine the plan's success criteria.
