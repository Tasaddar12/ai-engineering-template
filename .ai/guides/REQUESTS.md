# Requests for prepared work

Use these prompts after [onboarding](../commands/onboard.md), or to continue an
existing phase. Name the actual phase, the desired outcome, the relevant source
context, and the delivery boundary if you are overriding the
[shared defaults](../RULES.md#session-and-authorization): commit each completed
slice, push, and open a draft PR.

Preserve prior decisions and authorization. These ordinary-language requests use
the installed procedures; they do not require a slash command to be registered.

## Discuss an existing phase

> Let's discuss phase 01.

Route this directly to [discuss-phase](../commands/discuss-phase.md). Resolve the
phase, reuse its confirmed source paths and follow the workflow's own analysis
order. The user does not need to supply a slash command or a file inventory.
**This request does not authorize implementation.**

## Add work to the roadmap

> Add a phase for API key session hardening — we want sessions issued and managed
> through an IDP rather than static keys.

Route to [phase](../commands/phase.md). The runtime allocates the number, creates
the directory and updates the roadmap. For urgent work that must land between two
existing phases, ask for an insertion so nothing is renumbered.

## Plan a phase for execution

> Research and plan the selected phase. Produce `NN-MM-PLAN.md` assignments with
> concrete task actions, the files each task must read first, real dependencies,
> exact ownership, acceptance criteria, and verification commands that each state
> what failure would look like. Arrange an independent plan check, correct its
> findings within scope, and report readiness and any unresolved decisions before
> implementation.

Route to [plan-phase](../commands/plan-phase.md).

## Implement and leave a verified PR open (explicit no-merge override)

> Implement the authorized phase. Dispatch fresh coders for independent plans,
> integrate and check their committed results, keep required docs attached to the
> phase, and obtain independent outcome verification. Fix actionable findings,
> commit and push a PR, and observe the required remote checks. Do not merge;
> report when the final revision is ready.

Route to [execute-phase](../commands/execute-phase.md), then
[verify-work](../commands/verify-work.md), then
[ship](../commands/ship.md). Implementation requires an explicit instruction like
the one above; planning and readiness do not grant it.

## Show progress continuously

> Complete this scope with fresh agents for independent plans. Commit after each
> meaningful slice and push frequent updates to a draft PR so I can review
> progress. Preserve the full template guidance and record consequential
> deviations in the phase's context. Once the scope and documentation are
> complete, review the integrated result, fix findings, and verify the final
> revision and required checks.

Draft progress pushes and verified publication are different steps.
[ship](../commands/ship.md) is gated on verification passing for the current
revision, and it never merges.

## Repair a defect

> Investigate this failure. Preserve a representative reproduction, then either
> handle it as a quick task or insert a phase for the authorized repair. Add
> checks that reject plausible wrong fixes. Implement the correction, reconcile
> affected specifications and guides, independently verify the outcome and
> commit the result. Report actual evidence and remaining limitations.

A small, self-contained fix is [quick](../commands/quick.md). A fix that needs
decisions captured, or more than about three tasks, is a phase — insert it with
`/phase --insert`.

## Capture something without acting on it

> Note that we should rotate service account keys quarterly — don't work on it now.

Route to [capture](../commands/capture.md). It records the todo with enough
context to be actionable weeks later, then returns to the work in hand. Pending
todos are cross-referenced automatically when the matching phase is discussed.

## Resume interrupted work

> Inspect the selected phase's saved records, plans, summaries and commits.
> Reconcile the interruption before restarting. Reuse valid committed output where
> possible and preserve incomplete results. Continue previously authorized work
> with the original acceptance; record and explicitly replan any input changes.

[next](../commands/next.md) and [progress](../commands/progress.md) both detect
this case: the lowest-numbered phase whose plan files outnumber its summary files
is resumed ahead of new work.

## Report status without continuing

> Report the selected phase's current readiness, integrated results, blockers,
> verification and publication state. Inspect the current PR checks when relevant,
> name the revision covered by the evidence, and identify the next action. Keep
> this read-only; do not start agents, update records or publish.

Route to [progress](../commands/progress.md), which reports and recommends without
starting the work it recommends.

---

The [workflow guide](PHASE-WORKFLOW.md), [artifact guide](ARTIFACT-GUIDE.md),
[feature inventory](WORKFLOW-FEATURES.md) and
[command catalog](../commands/README.md) explain the exact boundaries. The
request still determines scope and authority.
