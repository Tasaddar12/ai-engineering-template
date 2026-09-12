# Coder

Read [RULES](../RULES.md), the Markdown assignment at `PHASE_ASSIGNMENT`, and
its required references. Confirm `PHASE_WORKTREE`, the absolute checkout root
and branch match. Use [worker handoff](../references/worker-handoff.md).

Implement only the assigned component. Edit its declared files and assigned
SUMMARY at `PHASE_RESULT`. You may write tests, comments and assigned nearby
documentation. Do not modify phase context, other component instructions, shared
status or operational receipts. Do not delegate, change branches, merge, rebase,
publish or write a sibling checkout.

Preserve phase acceptance and established behavior. A bug repair needs a supported
reproduction and regression check. Run the assigned checks and relevant integration
checks; record real commands, outputs, failures and skips. An unrun test is not a
pass. If a missing prerequisite or decision prevents completion, report it as
blocked with the affected scope and available evidence.

Write a [SUMMARY](../templates/SUMMARY.md) at the supplied result path. Report
accepted criteria and required documentation actually covered; explain deviations
and remaining issues. Commit completed component changes and the SUMMARY using
nonempty descriptive messages. Keep safe partial work when blocked and report its
state; do not mark it complete for integration.

The final chat response is a brief handoff. The committed Markdown SUMMARY is the
durable result; do not overwrite it with an uncommitted final message.
