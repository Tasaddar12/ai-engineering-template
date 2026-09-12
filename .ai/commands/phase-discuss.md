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
