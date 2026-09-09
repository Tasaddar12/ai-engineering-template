# Workflows

The executable workflow definitions live in the root [workflows directory](../workflows/) and install under `.ai/workflows` in target projects. They cover project initialization, research, planning, implementation, validation, critical review, delivery, cleanup, bugfix, recovery and state reconciliation.

The CLI routes operations to these workflows and the coordinator's programmatic APIs. Planning remains separate from implementation permission. Work runs in managed worktrees, product commands use the central runner, and delivery records actual GitHub merge results.

See [PLAN-003](../.ai/plans/completed/PLAN-003.md) for the current implementation scope and its explicit instruction to defer testing. This page contains reusable workflow documentation, not an implementation task graph.
