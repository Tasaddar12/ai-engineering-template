# Report a problem or request

## Purpose

An observation, confirmed defect or change request needs a clear record before action.

## Inputs

The request and read-only access to relevant fact owners.

## Gates

Before the proposed next action: [action-approved](../gates/action-approved.md).

## Steps

1. The orchestrator reads the current owners. For suspected bugs, the bug-reviewer
   inspects evidence and recommends a bounded next action without fixing the product.
2. Follow the [record policy](../policies/records.md): use intake.md under plans/intake
   for uncertainty, waiting questions, suspected drift or requests awaiting planning.
   Use fix.md under fixes/open when evidence confirms a bug or small defect.
3. Describe observed and expected behavior, impact and unknowns. Include reproduction
   or other confirming evidence for a FIX; distinguish observation from hypothesis.
4. When confirming an existing intake, link the FIX in its fix field and set status
   to confirmed. Preserve the original evidence; the FIX references it. Link any PLAN
   that owns execution and propose one bounded next action.
5. Return the decision summary and wait under RULES. The orchestrator records the
   user decision in the journal and updates STATE when focus changes.

## Output and handoff

A linked INTAKE or FIX and a decision summary. Research, a bounded repair or planning
can be proposed; creating a defect record does not authorize repair.

## Stop conditions

Wait when the next action needs approval. Missing evidence remains Unknown; it does
not justify a speculative fix or a confirmed-defect label.
