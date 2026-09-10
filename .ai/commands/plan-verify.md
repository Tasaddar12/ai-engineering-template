---
tier: contract
authority: agent
description: Verify a PLAN or FIX against current specs and observed behavior, including before merge.
argument-hint: <PLAN-or-FIX-id> [revision]
---

# Verify a plan or fix

Identify the selected record, base, revision and any pending diff. Use the
[verifier](../agents/verifier.md) procedure and its verdict format. Grade the
current specs and approved outcome, including every promised Contract change;
then run configured checks and the checks named by the record. Read-only
requests return the report without moving a file or recording new evidence.

Return **verified**, **defects found**, or **cannot verify**, with per-criterion
evidence, actual commands/results, record drift and limitations. Use the
[plan-verification report](../templates/plan-verification.md) to retain evidence
when record writes are authorized. Missing required evidence prevents a pass.

For lifecycle changes use [plan-review](plan-review.md); for Git publication
use [deliver](deliver.md). Verification itself never repairs or merges.
