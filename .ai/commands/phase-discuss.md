# Discuss a phase

Read [RULES](../RULES.md), selected CONTEXT, project constraints and relevant
requirements. Inspect nearby code enough to ask informed questions.

1. Establish the observable outcome, included behavior and exclusions.
2. Identify consequential choices. Reuse settled decisions and distinguish areas
   the user delegated from choices requiring human resolution.
3. Write stable acceptance IDs such as A1. Preserve the exact intended behavior;
   broad labels such as "authentication works" are insufficient.
4. Record incoming information and actual decisions in CONTEXT. When useful,
   preserve discussion history in DISCUSSION-LOG, with a link to the decision;
   downstream agents use CONTEXT rather than interpreting the transcript.
5. Record actual execution authorization and its boundaries. Mark approved only
   when the real instruction authorizes that scope. Pending choices identify
   what they block; continue independent preparation.
6. Record unrelated discoveries in Deferred with sources and reasons. A required
   unresolved behavior cannot be deferred out of the phase's completion criteria.

Commit authorized context changes. Continue to [research](phase-research.md)
when uncertainty warrants it, or [prepare](phase-prepare.md) when the approach
is sufficiently understood. A changed approved target must be reconciled with
any active execution attempt before more dispatch.

## Template and downstream use

Read the complete [context template](../templates/context.md) and its good/bad
examples before authoring. Use domain-specific decision categories, numbered
decisions, canonical references with real paths, reusable code insights and
explicit deferred ideas. Preserve the user's locked decisions verbatim where
required; document delegated discretion separately. The researcher needs to know
what to investigate and the planner needs to know which choices are fixed.

Use [discussion-log](../templates/discussion-log.md) when a transcript is useful
and [spec](../templates/spec.md) for a phase-level specification of desired
behavior. A phase specification is distinct from a current-behavior contract.
Add the [runtime fields](../runtime/TEMPLATE-CONTRACT.md) to the full context
output. [GSD discussion](../gsd/workflows/discuss-phase.md) provides the complete
discussion method; [adaptation](../references/gsd-adaptation.md) resolves local
authority, host and storage differences.
