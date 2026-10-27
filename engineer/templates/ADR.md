# Architecture decision rationale template

Use this complete template for optional rationale at `.planning/decisions/ADR-NNN-short-name.md`. PROJECT Key Decisions owns the actual choice and its lifecycle, written with `engineer_run query state.add-decision`. This record explains why; it cannot authorize implementation or become a second decision registry.

**Producer:** coordinator or assigned doc-writer using actual instructions, delegated discretion and inspected evidence.

| Consumer | Uses the rationale to |
|---|---|
| Phase researcher | Identify constraints and evidence that warrant reconsideration |
| Planner / plan-checker | Preserve accepted choices or identify an exact replacement |
| Executor | Apply the chosen approach within assigned scope |
| Doc-writer | Explain why without duplicating the behavior contract |
| Verifier | Check implementation against the choice and its limits |
| Future maintainer | Separate intentional tradeoffs from defects and superseded assumptions |

## File Template

```markdown
# ADR-[NNN]: [Decision rationale]

**Status:** proposed | accepted | superseded
**Date:** [YYYY-MM-DD]
**Decision owner:** `.planning/PROJECT.md` Key Decisions, written with `engineer_run query state.add-decision`.
**Decision reference:** [exact Key Decisions entry]
**Related phase / issues:** [IDs and canonical URLs]

This ADR preserves optional rationale. It does not approve a decision, own its lifecycle or authorize implementation.

## Context

[Describe the concrete problem, constraints and evidence that made the choice consequential.]

## Drivers

| Driver | Constraint / outcome | Evidence |
|--------|----------------------|----------|
| [driver] | [measurable need] | [source or check] |

## Options evaluated

### Option A: [name]

- Mechanism: [how it works in this project].
- Benefits: [specific outcome].
- Costs: [migration, operations and maintenance].
- Risks: [failure modes and reversibility].
- Validation: [command actually run, revision, observed result; otherwise unvalidated].

### Option B: [name]

[Use the same fields. Do not invent an unsupported alternative solely to fill the document.]

## Decision and rationale

[Link the owning Key Decisions entry and explain why its choice best fits the observed constraints. Distinguish measured facts from assumptions.]

## Consequences

### Positive

[Concrete expected benefits.]

### Negative and mitigations

[Tradeoffs, ownership and mitigation.]

### Reversibility

[What makes reversal possible or costly; exact triggers for revisiting.]

## Implementation boundaries

[Authorized scope and dependencies; this ADR itself does not grant implementation permission.]

## Validation

| Revision | Check argv / experiment | Observed result | Limitation |
|----------|-------------------------|-----------------|------------|
| [SHA] | [actual command] | [result] | [remaining uncertainty] |

## Revisit and supersession

[Define the trigger. Record any replacement decision in PROJECT Key Decisions first, then link its rationale here. Preserve history in Git; do not make this document a second decision registry.]

## References

[Primary sources and related contracts.]

## Status history

| Date | Rationale change | Owning decision / evidence |
|---|---|---|
| [YYYY-MM-DD] | Proposed | [Investigation or request; not approval] |
| [YYYY-MM-DD] | Accepted / rejected / superseded | [Actual Key Decisions entry and evidence] |
```

## How to fill it

1. Confirm that the argument needs to outlive the assignment. Routine naming, small refactors and progress belong in the owned execution record and Git history.
2. Read accepted outcomes, relevant rationale and current implementation. Separate established constraints from assumptions and retain the actual evidence.
3. Describe one coherent choice. Split independent choices with different reasons so they can be reconsidered independently.
4. Compare plausible alternatives under the same constraints, including retaining the current approach when plausible. Do not invent a weak alternative to make the selected option seem inevitable.
5. Preserve operational burdens, compatibility costs, migration work and failure modes. Explain why the chosen cost fits the observed constraints.
6. Record actual authority in PROJECT Key Decisions first. Authorized implementation may include ordinary architectural discretion; do not invent another approval gate or attribute an agent recommendation to the human.
7. Link the current behavior specification rather than copying it. That specification owns observable behavior; Key Decisions owns the choice; this record owns its argument.
8. Retain actual experiment commands, full revisions, observed results and uncertainty. An accepted decision does not make an unrun check evidence.
9. Commit the assigned rationale with its meaningful source or documentation slice and identify its exact path and affected interfaces in the normal execution record.

## Good and bad examples

### Concrete context

**Good:** "Three plans replace the same generated index. The fixture at the recorded revision reproduces a lost entry. Serialize that actual shared resource while independent reports stay parallel. Declare a producer dependency only when a later plan consumes an earlier output."

**Why it works:** It names the resource, failure and bounded remedy, without inventing a dependency from file overlap alone.

**Bad:** "Concurrency is difficult, so use a robust architecture."

**Why it fails:** It provides neither a concrete choice nor evidence.

### Honest tradeoff

**Good:** "Use one repository coordinator lock. Shared allocation and integration are serialized, while bounded component workers remain concurrent. Reconsider when separate phase sessions need simultaneous coordinators and their allocation can be isolated safely."

**Why it works:** Benefit, capacity cost and reconsideration trigger are explicit. File ownership does not purport to isolate shared databases or ports.

**Bad:** "The lock guarantees all operations are safe and has no disadvantages."

**Why it fails:** It overstates the mechanism and hides a real planning constraint.

### Authority and evidence

**Good:** "Accepted within the user's authorized storage migration. The coordinator chose the format after the recorded compatibility experiment; the user did not prescribe a serialization library. PROJECT Key Decisions records the choice."

**Why it works:** Work authorization, delegated choice and measured evidence remain distinct.

**Bad:** "Human approved," supported only by an agent's recommendation.

**Why it fails:** Research cannot create human authorization.

### Supersession

**Good:** Record a replacement in PROJECT Key Decisions, create ADR-014 explaining the changed constraint and link ADR-006 as previous rationale. Preserve reciprocal links, dates and the original argument; retire eligible rationale through the supported archive route.

**Why it works:** Both arguments remain recoverable and the authoritative choice is clear.

**Bad:** Rewrite ADR-006 with a new choice while retaining its original date.

**Why it fails:** It conceals history and obscures why earlier code was reasonable.

## Completion and downstream handoff

- One specific choice and its applicability can be applied without guessing.
- Every constraint has evidence or is explicitly an assumption.
- Alternatives are plausible, costs remain visible and reconsideration triggers are concrete.
- Authority and status agree with the actual Key Decisions entry; proposals remain proposals.
- Links identify phase, behavior, checks and prior rationale. Missing future evidence stays Pending.
- The owned execution record identifies affected interfaces, compatibility and operational checks.

## Lifecycle

Keep proposed, rejected and superseded arguments readable when useful. A consequential change gets a new owning decision and linked rationale; do not erase the original argument. Existing code and a complete ADR do not themselves authorize implementation. Routine progress does not need a new rationale record.
