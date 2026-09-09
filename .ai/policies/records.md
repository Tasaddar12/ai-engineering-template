---
tier: contract
authority: agent
title: Record policy
---
> Contract: amend within approved work with evidence; human intent remains
> subject to the approval policy.

# Record policy

## Requirements

### One owner and one lifecycle stage

Use [truth-map](../truth-map.md) and [config](../config.yaml). Link facts to
their owner. When duplication causes contradictory obligations, reconcile
the owner and replace copies with links inside the approved scope.

A PLAN or FIX stage is its directory. Do not add status or stage frontmatter
to either: two copies eventually disagree. Preserve IDs and slugs when
moving records, repair links, and journal transitions. Accepted ADR status
and INTAKE disposition are different facts and remain explicit metadata.

### Mutability tiers

| Tier | Holds | What you may do in approved scope |
| --- | --- | --- |
| intent | PROJECT, RULES, approval boundaries | Propose; edit only under the user's explicit instruction. |
| contract | Specs, decisions, operating contracts | Amend with evidence under the protocol below. |
| plan | Plans, fixes and intake | Rewrite the proposed route and findings as evidence changes. |
| status | STATE and run manifests | Replace stale coordination with current observations. |
| log | Journal entries, amendments, completed research, meetings | Append corrections; preserve existing evidence. |

Each new Markdown record declares tier and authority and opens with a tier
notice. Templates model their output's metadata. Existing journal entries
retain their bytes; a legacy journal without frontmatter inherits log tier
from its path until the next new daily file. Metadata does not enforce
filesystem permissions.

Completed plans and fixes keep their recorded result. New work uses a linked
successor; a correction must not erase the evidence of what was accepted.

### Specs say what is true now

Write specs in present tense. Keep future behavior in a plan's Contract
changes section until implementation makes it true in the same commit.
Keep rationale in ADRs and change history in amendments, fixes and Git.

Rewrite or delete obsolete criteria rather than adding historical footnotes.
Avoid TODOs, strikethrough and phrases such as "removed in v2" or "not yet
implemented" in a SPEC. A reader must not guess which requirement is active.
Current limits and unsupported behavior are valid present-tense facts.

Describe observable behavior and invariants with enough detail to verify
them. Keep incidental implementation mechanics in code; link to the owner
when architecture itself is a required contract.

### Contradictions and amendments

1. State the conflict and inspect the code, current specs, accepted ADRs and
   human intent. Tested code is evidence, not automatic proof of correctness.
2. If code violates a valid contract, open a FIX. If the contract is stale
   within the approved outcome, write an AMD first: old wording, supported
   truth, reason, new wording and affected records. Keep it short.
3. Rewrite the spec to the current truth. Land the AMD, contract and related
   implementation together. Link the AMD; keep history out of the spec body.
4. Follow references downstream and journal the correction. If intent or the
   approved outcome must change, propose it and wait under approval policy.

An amendment is a normal correction route, not an admission of failure.
Proposed ADRs are not authority. To replace an accepted decision, create a
new accepted ADR with supersedes, set the old ADR's status to superseded and
superseded_by, and move it to retired with its rationale intact. That status
transition needs no separate AMD; the new decision is the record. Acceptance
must be supported by the approved decision scope.

### Plans, fixes and intake

A FIX restores already agreed behavior. A PLAN changes behavior or contracts.
Size alone does not decide the route: a one-line behavior change can require
a plan. A missing specification may be clarified in an AMD only when existing
intent and evidence establish the behavior; do not invent a requirement.

Fix records capture symptom, root cause or an explicit unknown, change,
scope and before/after regression proof. Without proof, leave the FIX open.
Use [fix](../workflows/fix.md) for the repair process.

INTAKE holds unconfirmed observations, waiting questions and suspected drift.
Capture unrelated findings rather than silently fixing or merely mentioning
them. Check for duplicates; link the confirming FIX or planned successor.
Flag severe impact plainly. Research and meeting notes remain evidence;
they do not authorize implementation.

### Every PR keeps its specification current

Every feature or fix PR updates the affected SPEC in the same change.
A behavior change updates criteria. A pure conformance repair leaves correct
criteria intact and refreshes current verification_refs to its actual proof.
This records the repair without manufacturing a contract change or writing
history into the specification. No recursive post-merge spec commit is needed.

### State and evidence

STATE links current blockers and drift; the owning INTAKE or FIX holds the
evidence. The orchestrator owns shared STATE and journal coordination.
Gate/test/review evidence belongs in the selected PLAN or FIX. New
verification of a historical record belongs in an appended journal entry.
A read-only snapshot returns its report without repository writes.

## Evidence

Use complete templates, stable IDs, factual sources, the amendment when
needed and dated observations. A check that was not run is not evidence.
