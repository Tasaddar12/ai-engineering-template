# Architecture Decision Record Template

Template for `.planning/decisions/ADR-NNN-short-name.md`.

**Purpose:** Preserve the reasoning behind a consequential architectural choice so
future agents can change the system without repeating the original investigation
or mistaking an implementation accident for a required constraint.

**Producer:** The coordinator or an assigned documentor, using recorded human
instructions, delegated discretion and inspected evidence.

**Downstream consumers:**

| Consumer | Uses this record to |
|---|---|
| Phase researcher | Understand constraints and identify conditions that warrant reconsideration |
| Planner and checker | Keep new plans compatible with accepted decisions or explicitly propose a replacement |
| Coder | Apply the selected approach within the assigned scope |
| Documentor | Explain architectural rationale without duplicating the current behavior contract |
| Verifier | Check that implementation follows the accepted choice and its stated limits |
| Future maintainer | Distinguish intentional tradeoffs from defects and superseded assumptions |

This is a local extension. It complements the complete upstream template catalog;
it is not a replacement for the upstream phase specification.

---

## File Template

```markdown
---
status: proposed
supersedes: []
superseded_by: []
---

# ADR-[NNN]: [Specific decision]

**Date:** [YYYY-MM-DD]
**Related phase:** [.planning/phases/NN-name/NN-CONTEXT.md]
**Decision basis:** [Actual human instruction and date, or the recorded scope of delegated judgment]

## Context

[Describe the concrete problem, affected users or maintainers, existing design,
and constraints that made this choice consequential. Link inspected code,
research and phase decisions. Separate facts from assumptions.]

| Constraint or observation | Evidence | Effect on the decision |
|---|---|---|
| [Specific constraint] | [Source/revision or actual instruction] | [Which option it supports or rules out] |

## Decision

[State the selected approach in plain language, including its scope and limits.
If proposed, say what remains undecided. Do not label a proposal accepted simply
because an implementation or research report prefers it.]

**Applies to:** [Subsystems, operations and conditions governed by this decision]
**Does not decide:** [Adjacent choices deliberately left to another record or phase]

## Alternatives

| Option | Benefits | Costs and risks | Why selected or rejected |
|---|---|---|---|
| [Selected option] | [Concrete benefit] | [Concrete cost] | [Evidence-based reason] |
| [Plausible alternative] | [Concrete benefit] | [Concrete cost] | [Reason under the same constraints] |
| [Keep the existing approach, when plausible] | [Concrete benefit] | [Concrete cost] | [Why change is justified] |

## Consequences

**Benefits:**
- [Expected benefit, with a way to observe whether it occurs]

**Costs and obligations:**
- [Operational burden, compatibility constraint, migration work or new failure mode]

**Risks and mitigations:**
- [Risk] -> [Mitigation, owner or linked bounded follow-up]

## Validation and reconsideration

| Assumption or tradeoff | Evidence available | Reconsider when |
|---|---|---|
| [Assumption] | [Observed result or explicitly untested assumption] | [Specific trigger] |

[Describe remaining uncertainty honestly. Acceptance of the decision does not
prove implementation correctness or make an untested benefit an observed fact.]

## Related phase and behavior

- Decision and authorization: [phase CONTEXT]
- Supporting investigation: [relevant RESEARCH or inspected source]
- Current behavior: [.planning/specs/SPEC-NNN-capability.md, if one exists]
- Implementation and verification: [PLAN, SUMMARY and VERIFICATION when available]
- Previous/replacement decision: [ADR links, if applicable]

## Status history

| Date | Change | Basis |
|---|---|---|
| [YYYY-MM-DD] | Proposed | [Investigation or request] |
| [YYYY-MM-DD] | Accepted / rejected / superseded | [Actual decision or replacement ADR] |
```

## How to fill it

1. Confirm the decision is significant enough to outlive the current assignment.
   Routine variable naming, a small refactor or ordinary progress belongs in the
   component SUMMARY and Git history.
2. Read the phase acceptance, relevant existing ADRs and current implementation.
   Establish which constraints are confirmed and which are assumptions.
3. State one coherent decision. Split unrelated decisions with different reasons
   into separate records so they can be reconsidered independently.
4. Compare plausible alternatives under the same constraints. Include staying
   with the existing approach when that is a real option.
5. Preserve the downside of the selected option. A useful ADR explains why its
   cost was acceptable, not why every competing approach is bad.
6. Record the actual authority. Existing implementation authorization may include
   routine architectural discretion; do not invent a new approval gate or claim
   a human selected an option they never selected.
7. Link the behavioral contract instead of copying it. This record owns why the
   design was chosen; the current specification owns what the system does.
8. Commit the record with the phase's implementation or documentation slice and
   include coverage in the assigned SUMMARY.

## Good and bad examples

### Concrete context

**Good:** “Three independent report workers write to the same generated index.
The integration fixture at revision `<revision>` reproduces a lost entry when
both writers replace the file. We will serialize index writes while independent
report generation remains parallel.”

**Why it works:** It names the shared resource, observed failure and exact scope
of the remedy. Another agent can evaluate whether the constraint still applies.

**Bad:** “Concurrency is difficult, so use a robust architecture.”

**Why it fails:** It supplies neither a decision nor evidence. It could justify
mutually incompatible implementations.

### Honest tradeoff

**Good:** “Use one repository coordinator lock. This limits orchestration to one
phase at a time but still permits bounded component concurrency. Reconsider when
independent phase branches need simultaneous coordinators and shared allocation
and integration can be isolated safely.”

**Why it works:** The benefit, limitation and reconsideration trigger are explicit.
It does not claim worktree isolation also isolates shared databases or ports.

**Bad:** “The lock guarantees all operations are safe and has no disadvantages.”

**Why it fails:** It promises more than the mechanism provides and hides a real
capacity constraint from planners.

### Authority and evidence

**Good:** “Accepted within the user's authorized storage migration. The coordinator
selected the format after the documented compatibility experiment. The user did
not prescribe a particular serialization library.”

**Why it works:** It distinguishes authorization for the work from the agent's
implementation choice without unnecessarily reopening approved scope.

**Bad:** “Human approved,” when the only evidence is an agent's recommendation.

**Why it fails:** A research conclusion cannot create human authorization.

### Superseding a decision

**Good:** Create ADR-014, link ADR-006 under `supersedes`, explain the changed
constraint, and mark ADR-006 superseded with a link to ADR-014.

**Why it works:** Future readers can recover both the old rationale and the new
basis without treating both as simultaneously binding.

**Bad:** Replace the old ADR's explanation with the new decision and retain its
original date.

**Why it fails:** It rewrites history and obscures why older code was reasonable.

## Completion and downstream handoff

- The decision is specific enough for a planner to apply without guessing.
- Every claimed constraint has evidence or is labeled an assumption.
- Alternatives are plausible and evaluated consistently.
- Costs, remaining risks and reconsideration triggers are recorded.
- Status and authority match actual decisions.
- Links identify the owning phase and relevant behavior; missing future evidence
  is described as pending instead of fabricated.
- The component SUMMARY tells downstream workers which decision affects their
  interfaces, compatibility or operational checks.

## Lifecycle

`proposed` records remain proposals until a decision is established. An accepted
record stays readable as history. A rejected proposal may remain when its
reasoning prevents repeated investigation. A changed significant decision gets
a new ADR and reciprocal supersession links; do not rewrite historical rationale.
Routine progress does not require another ADR.
