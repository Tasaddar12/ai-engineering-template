---
tier: plan
authority: agent
id: FIX-{nnn}
title: <the defect, in a few words>
found: YYYY-MM-DD
found_by: <agent or person>
severity: minor      # critical | major | minor | cosmetic
violates: SPEC-{nnn} # the spec the code contradicts, or `none` — see below
links: []
deferred_until: none # affected-tree-available when the inspected tree is unavailable
---

# FIX-{nnn}: <the defect, in a few words>

> **`plan` tier. Its stage is its directory** — `fixes/open/` while it is being
> worked, `fixes/done/<period>/` once the check passes. No `status:` field.
> Once it is in `done/`, treat it as history: append, do not rewrite.
>
> A fix **restores conformance with the contract.** Small bounded repairs use a
> FIX. An approved PLAN may coordinate multiple or large linked FIX records;
> each keeps reproduction, root cause and proof. If this change would move what
> "correct" means, it needs explicit PLAN Contract changes — see
> [RULES.md](../RULES.md#bug-fixes).

## Symptom

What was observed, from the outside. Inputs, environment, and what happened
instead of what should have happened. No diagnosis yet — that is the next
section, and mixing them is how the wrong cause gets fixed.

## Root cause

Why it happened, in the code. Name the file and the mechanism. "Off-by-one in
the pagination cursor" — not "pagination was broken", which is the symptom
again.

If the honest answer is that you could not find the cause and treated the
symptom, **say so here.** A recorded guess is useful; a guess presented as a
diagnosis is what makes the recurrence baffling.

## The change

What was actually changed, and why this is the correct fix rather than the one
that makes the symptom stop.

- `path/to/file.ext` — <what changed>

## Proof

The check that fails before the change and passes after it. **A fix is not done
without this** — a fix with no regression test is a fix with a scheduled
recurrence.

```
<command, and the failing output from before the fix>
```

- **Regression test:** `path/to/test.ext::test_name`

If no automated check is possible, say exactly why, describe the manual
verification performed, and treat that as a known weakness rather than a pass.

## Contract

FIX items correct code only. Cite the existing spec or acceptance criterion
that establishes the defect under `violates:`. If a document or contract also
needs correction, create a separate INTAKE and link it here. Do not amend a
spec to make this FIX pass. If correctness needs a decision, leave the FIX open
pending that INTAKE.

- Related documentation/contract INTAKE: <id, or none>

## Related

Delete when empty. Other fixes with the same root cause, the intake item this
came from, the plan that introduced the defect. Three fixes pointing at one
cause is a signal that the real work is a plan.

- 

<!--
Naming: FIX-{nnn}-{slug}.md, from the coordinator-issued block. Collision
checks cover lifecycle inventories, registered worktrees and receipts;
numbers are never reused.

Run /fix, which does the whole loop: diagnose, record, change, prove, close.

Escalate to /plan-new if the fix turns out to need an ADR, a spec rewrite, or
more than a handful of files. A large conformance repair may be linked into an
approved PLAN while preserving this record's symptom, root cause and proof.
Behavior changes belong in the PLAN Contract changes section.

Write the Symptom and Root cause sections BEFORE changing code. A fix record
written afterwards reliably describes the change and forgets the defect, which
is the half that stops it happening again.
-->
