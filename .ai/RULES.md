---
tier: intent
authority: human
title: Rules of engagement
---
> Intent: the user owns these boundaries. Propose changes unless their
> instruction already authorizes the exact edit.

# Rules of engagement

Read [PROJECT](state/PROJECT.md), [STATE](state/STATE.md), the selected record,
[truth-map](truth-map.md), and the relevant role and workflow. Reading a
plausible file in the wrong checkout can silently supply the wrong contract;
confirm your assigned root and branch first.

## Report, summary, decision

Follow [approval](policies/approval.md). Report the need, use
[decision-summary](templates/decision-summary.md), then follow the user's
decision. Direct instructions authorize their stated action. Once execution
is approved, finish that scope without asking again for each ordinary step.

Scope changes, human-owned intent changes and delivery beyond the granted
action need a new decision. A role definition or PASS cannot supply it.

## Resolve contradictions instead of working around them

During approved work, identify the conflicting statements and inspect their
evidence. A failing implementation does not authorize weakening a valid
requirement. A stale document does not justify preserving a broken design.

Use the [record policy](policies/records.md) to correct the wrong side and
record why. If you cannot establish which side is right, state the conflict,
your recommendation and the missing decision; continue independent work.
This prevents refusal, silent workarounds and code/document divergence.

## Read each document for the fact it owns

| Document | Read it for |
| --- | --- |
| PROJECT | Purpose, hard constraints, non-goals and human authority. |
| SPEC | Current correct behavior, observable criteria and invariants. |
| ADR | Why a decision was made; only accepted ADRs carry authority. |
| PLAN | Proposed work, dependencies and contract changes to land. |
| FIX | A confirmed defect and proof that its repair restores conformance. |
| INTAKE | Uncertainty, waiting questions and discrepancies needing triage. |
| STATE | Current coordination, blockers and linked suspected drift. |
| Journal, research, meetings | Evidence and history, never new authority. |

Use [records](policies/records.md) for tiers, tense and amendments. Use
[truth-map](truth-map.md) for ownership. Repeating a requirement in several
files makes later corrections disagree; link to its owner instead.

## Advance on evidence

[Workflows](workflows/README.md) own steps, [policies](policies/README.md)
own firm requirements, and [gates](gates/README.md) own PASS/FAIL criteria.
[Commands](commands/README.md) select a workflow; [hooks](hooks/README.md)
name checkpoints. These documents do not install executable enforcement.

A plan is a prediction. Verify the actual result against current specs and
approved outcomes. Checked boxes alone prove nothing. Correct the plan when
the approved route changes; do not silently abandon an approved outcome.

Use [execution](policies/execution.md) for validation, descriptive commits,
delivery and exact cleanup after merge. Use
[parallel execution](policies/parallel-execution.md) for independent tracks.
