---
name: regression-design
description: Design meaningful automated checks for a bug repair or changed behavior. Choose observable assertions, boundary cases and integration seams; avoid tests that merely repeat implementation or document wording.
---

# Design checks that can catch the defect

Follow the assigned role and [shared rules](../../../.ai/RULES.md).
Start with the behavior being promised, preserved or repaired, not the shape of
the current implementation.

## Find a discriminating assertion

Identify the authoritative expected result and the observation that distinguishes
correct behavior from the likely defect. For a repair, demonstrate failure on
the original behavior where feasible, then success with the correction. Record
why the original test fails; setup errors and missing dependencies are not a
valid regression oracle.

Use the smallest representative input while retaining the original failure case.
Choose neighbors according to the behavior: empty/single/multiple items, values
around a boundary, missing versus invalid data, retries, ordering, failures and
cleanup. Do not turn this into a mandatory Cartesian product for every change.

Ask whether a plausible wrong implementation would still pass. Useful contrasts
include allowed and rejected requests, distinct inputs producing distinct results,
and a state change followed by a read through the real consumer. An assertion
that only checks a file exists or a process exits does not prove its behavior.

## Pick the right layer

| Risk | Useful evidence |
|---|---|
| Pure transformation or boundary logic | Direct behavior checks with representative inputs |
| Components connect incorrectly | A check through the actual producer/consumer interface |
| State, ordering or recovery changes | A controlled stateful scenario preserving relevant transitions |
| External provider behavior | A focused adapter check plus clearly stated simulated boundaries |
| Documentation-only edit | Existing link/example checks and claim inspection where applicable |

Keep the behavior under test real. Simulate unrelated external services when
needed, while stating what that cannot establish. Avoid duplicating the
implementation's internal conditions in the expected-result calculation.

## Make the check usable

Ground the command in existing manifests, configuration and the assigned working
directory. Verify fixture prerequisites and cleanup; keep tests isolated from
shared accounts or databases unless that use is already authorized.

Put executable commands in config or IMPLEMENT, with supporting strategy in
VALIDATION only when useful. Report actual before/after results and revisions
in the assigned result. Run the checks required by the change and project;
broaden testing when new failures, risks or changes justify it.
