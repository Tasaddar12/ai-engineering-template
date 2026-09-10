---
tier: contract
authority: agent
id: SPEC-{nnn}
title: <What this specifies>
links: []
---

# SPEC-{nnn}: <What this specifies>

> **`contract` tier.** Amendable by any agent via the
> [amendment protocol](../RULES.md#the-amendment-protocol). If this document
> and the code disagree, one of them is wrong — determine which, fix it, and
> record why. Do not work around this file.
>
> **Present tense only.** Every sentence below is a true statement about the
> software as it is today. This file carries no history and no intentions —
> see [what each document is for](../RULES.md#what-each-document-is-for).

## Requirement

What must be true, in one or two sentences. Written so it stays true through a
rewrite of the implementation.

## Acceptance criteria

Observable, checkable, implementation-free. These are what verification grades
against.

- [ ] Given <situation>, when <action>, then <observable outcome>
- [ ] Given <situation>, when <action>, then <observable outcome>

## Invariants

Things that must hold at all times, not just at the end of a happy path.

- 

## Explicitly out of scope

Adjacent behavior this spec does not govern, so a later reader does not infer
requirements that were never intended. Behavior that *is* governed elsewhere
gets a spec id, not a description.

- 

## Open questions

Delete when empty. Anything here is a reason to ask, not to guess — and it is
the only place in this file where something unsettled may appear.

- 

---

<!--
Naming: SPEC-{nnn}-{slug}.md, next number after the highest in .ai/specs/.

TWO RULES, and both matter.

1. NO IMPLEMENTATION DETAIL. "Use a 300ms debounce in useSearch.ts" belongs in
   a plan or an ADR; "typing quickly issues at most one request per burst"
   belongs here. Test: could this survive a rewrite of the module?
   See RULES.md#writing-specs-that-survive.

2. NO HISTORY, NO INTENTIONS. This file states what IS. Never write:

     "removed in v2"      "deprecated"        "no longer applies"
     "not yet implemented"  "was previously"  "will be"     "TODO"
     strikethrough          commented-out criteria

   When a requirement changes, rewrite the line to state the new requirement
   and nothing else. When a requirement goes away, DELETE it — the criterion,
   the section, or this whole file. Deleting loses nothing: the amendment
   record in .ai/decisions/amendments/ holds what it said and why it moved, the
   ADR holds why the decision changed, and git holds every version.

   Behavior that is decided but not built does not go here at all. It lives in
   the plan that will build it, under Contract changes, and the implementor lands
   it here in the same change as the working code. A spec asserting the target
   state makes every verification fail, which teaches everyone to ignore the
   verifier.

   Test: is every sentence in this file true of the software right now?
-->
