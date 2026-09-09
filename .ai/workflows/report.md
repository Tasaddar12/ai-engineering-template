# Report a problem or request

## Purpose

A problem, bug, drift observation or change request needs a clear record before action.

## Inputs

The request and read-only access to relevant fact owners.

## Gates

Before the proposed next action: [action-approved](../gates/action-approved.md).

## Steps

1. The orchestrator reads the current owners. For bugs, the bug-reviewer inspects
   evidence and recommends a bounded next action without fixing the product.
2. Allocate an intake ID and use the intake template under plans/intake.
3. Describe observed behavior, expected outcome, impact and unknowns. Include a
   reproduction only if known; distinguish observation from assumption.
4. Link related records and propose one bounded next action.
5. Return the decision summary and wait under RULES. The orchestrator records the
   user decision in the journal and updates STATE when focus changes.

## Output and handoff

A linked intake and a decision summary. Research or planning can be a proposed next action.

## Stop conditions

Wait when the next action needs approval. Missing evidence remains Unknown; it does not justify a speculative fix.
