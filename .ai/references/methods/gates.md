# Gate types and local recovery

Adapted from the pinned source gate taxonomy; attribution is in
[third-party notices](../../THIRD-PARTY-NOTICES.md). This file is a local method,
not a registration of extra runtime commands.

## Pre-flight gate

Check preconditions before beginning an operation: explicit implementation
authorization, committed inputs, exact ownership, required records, runnable
commands and satisfied dependencies. The coordinator uses `phase.py check` for
structural readiness and inspects semantic feasibility separately. Missing
preconditions block dependent work; existing independent work may continue.
A file-existence check establishes presence, not product correctness.

## Revision gate

Assess a producer's output against acceptance and return specific findings to
the owning author. Describe the expected behavior, actual evidence and exact
revision. Correct authorized gaps and repeat the affected review. Avoid identical
retries: if an approach stalls, inspect the cause and change the approach or
report the external dependency. There is no fixed review-count exemption that
turns an unresolved required gap into success.

## Escalation gate

Ask for a human decision when intent, scope, credentials or required human
observations cannot be established from the existing authorization and evidence.
State the concrete question and which work depends on it. Preserve completed
work and continue independent authorized scope. Do not ask again for approval
already supplied or let a mode flag choose on the user's behalf.

## Stop and preserve gate

Stop an operation that would overwrite unrelated data, violate ownership,
continue from uncertain running processes or use incompatible execution state.
Preserve the checkout, commits, evidence and checkpoint. Follow
[phase-resume](../../commands/phase-resume.md) before retrying interrupted work;
do not delete state or restart a worker blindly.

## Gate placement

| Local procedure | Gate | Evidence | On failure |
|---|---|---|---|
| Phase preparation | Pre-flight | CONTEXT, requirements, actual source | Resolve missing information before dependent planning |
| Preparation review | Revision | PLAN feasibility and acceptance coverage | Return bounded corrections to preparer |
| Phase start | Pre-flight | Authorization, clean inputs, dependencies, configured checks | Do not dispatch until prerequisites are met |
| Component integration | Revision | Commit scope, SUMMARY coverage, actual checks | Preserve result; correct the specific gap without replaying completed work |
| Phase verification | Revision | Behavior, wiring, documentation, tested revision | Route evidenced gaps to owned corrections |
| UAT | Escalation | Actual human observations | Keep pending/failed cases visible |
| Publication | Pre-flight | Current verification and required checks, user delivery limit | Keep draft/unmerged work; disclose any blocker |
| Recovery | Stop and preserve | Process identity, worktree, commits, compatible state | Reconcile before choosing a continuation |

Use the [runtime contract](../../runtime/TEMPLATE-CONTRACT.md) for machine-checked
fields and the [rules](../../RULES.md) for authority. Examples and review methods
do not grant additional permission or weaken acceptance.
