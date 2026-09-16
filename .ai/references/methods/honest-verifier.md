# Honest verification of underspecified outcomes

Some outcomes cannot be inferred from the specification alone. For example,
should intervals `[1,2]` and `[2,3]` merge? Does "character" mean a grapheme or a
code unit? A confident answer from an agent does not supply the missing decision.

## Evidence, specification and independent expectations

Distinguish these cases:

| Case | Required response |
|---|---|
| Spec defines the expected behavior and evidence proves it | VERIFIED |
| Spec defines the expected behavior and implementation contradicts it | FAILED |
| Spec defines behavior but only symbols/wiring were inspected | PRESENT_BEHAVIOR_UNVERIFIED when runtime evidence is needed |
| Spec does not settle the relevant rule | `insufficient_spec`, request the decision through the coordinator |

An existing `verification: backstop` annotation marks an outcome known to need
explicit evidence. Read truth items whether represented as plain strings or an
object with `statement` and `verification`; no special parser service is required.
Do not downgrade an ordinary, determinate truth merely because this method exists.

For a tagged truth, seek an independently defined expected result: a human-authored
held-out case, a property grounded in approved acceptance, or an actual observation
whose expected behavior is already settled. A test written by assuming the same
missing rule as the implementation does not resolve the specification gap. Symbol
presence and wiring alone never resolve it either.

## Reporting

If explicit evidence is missing, abstain on that truth with
`reason: insufficient_spec`, explain the unresolved decision and route it to
`human_needed`. Preserve it even when other defects make the overall status
`gaps_found`. Infrastructure phases follow the same rule. Continue independent
review; do not silently pass, invent a decision, or say all outcomes are complete.

A false annotation can create unnecessary uncertainty: read the approved contract
before abstaining. An omitted annotation does not excuse a concrete ambiguity
found during review. The procedure is an evidence discipline, not a claim that a
particular model or deterministic helper guarantees accurate judgments.

## Negative constraints and incidental success

A prohibition is a must-NOT outcome, such as rejecting unauthorized access. Trace
the enforcement and use a meaningful negative case. A model's opinion is not proof
that every forbidden path is excluded. Record missing enforcement as a gap.

For a passing truth, also inspect why it passes: does production establish the
state/ordering, or only the fixture? Name any undeclared precondition,
incidental ordering or fixture-only setup. A suspicion alone is advisory; an
actual counterexample or missing required production path is a defect. Do not let
an advisory label hide a demonstrated failure.
