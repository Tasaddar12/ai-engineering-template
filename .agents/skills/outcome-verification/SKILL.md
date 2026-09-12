---
name: outcome-verification
description: Independently assess an integrated phase or a PR's claimed outcome. Trace real behavior, data flow, error paths and documentation against acceptance instead of trusting summaries or structural readiness checks.
---

# Verify the observable outcome

Use the assigned review scope and [verifier responsibility](../../../.ai/agents/verifier.md).
Keep the checkout unchanged; report findings rather than silently fixing them.

## Work backward from the claim

Read the approved acceptance and identify the reviewed revision. Derive the
observable behavior, required artifacts, connections and checks from that
contract. Do not invent new acceptance or accept a worker's completion assertion
as evidence.

Distinguish these levels:

| Level | What it establishes | What it does not establish |
|---|---|---|
| Artifact exists | A file, route or function is present | It implements the behavior |
| Implementation is substantive | Real logic handles the relevant inputs | A production caller uses it |
| Flow is connected and observed | The real entry point reaches the logic and consumes the result | Untested paths or external environments also work |

Trace both the request and returned data. Locate registration, caller, state
change, response and consuming UI or service. Use distinguishable input values
to expose hardcoded outputs or disconnected placeholders. Search hits, line
counts and TODO markers are leads for inspection, not automatic verdicts.

For authentication, trace submission, server validation, session persistence,
protected requests and logout rejection only as required by the agreed contract.
An imported access hook or isolated helper test cannot establish the whole flow.

## Check the evidence and documentation

Inspect assertions and simulated boundaries, run applicable required checks,
and examine failures and relevant error paths. For a correction, revisit prior
findings and affected connections while checking for regressions. Widen review
when the change invalidates earlier evidence, not merely to add another pass.

Compare required guides/SPECs with the integrated implementation. Missing behavior,
missing proof, missing documentation and unresolved intent are different findings.
Keep required gaps visible. Human observations remain pending when they cannot
be established by this review.

## Return a usable verdict

Map acceptance and documentation to actual evidence, with the exact revision.
For findings, give the affected area, reproduction or source evidence, impact
and needed correction. Separate blocking gaps from optional editorial advice.

Use the assigned [VERIFICATION report](../../../.ai/templates/VERIFICATION.md)
for a phase, or the requested review format for a scoped PR review. A changed
source needs current evidence; a previous pass or an old merged PR does not
attest to newer work. Do not publish, merge, alter acceptance or manufacture UAT.
