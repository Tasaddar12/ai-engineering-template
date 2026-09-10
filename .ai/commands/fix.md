---
description: Diagnose, record and fix a single defect, with the check that stops it coming back
argument-hint: <what's broken, or a FIX/INTAKE id>
---

Fix: **$ARGUMENTS**

If the argument is a `FIX-{nnn}` id, resume that record in `.ai/fixes/open/`.
If it is an `INTAKE-{nnn}` id, read it first. A confirmed code defect gets a
linked FIX; documentation or contract work stays INTAKE for `/plan-new`.

This is the short route, for a change that makes the code do what the record
already says it should. **A fix restores conformance with the contract; a plan
changes what conformance means** — see `.ai/RULES.md#bug-fixes`. If what is
being asked for is new or different behavior, this is the wrong command: say so
and use `/plan-new`.

## 1. Establish it is a defect, not a disagreement

Find the spec, ADR, or intent statement the code contradicts. Then one of:

- **A spec forbids the observed behavior** → a defect. Proceed.
- **No spec covers the case** → use existing PLAN acceptance if it establishes
  the code defect. Any missing contract decision gets a separate INTAKE; do
  not decide what correct means inside a FIX.
- **A spec permits or requires the observed behavior** → not a defect yet.
  Either the spec is wrong (capture a contract INTAKE for later) or the request
  is a behavior change (`/plan-new`).
  Say which, and do not proceed as though it were a bug.

Check `.ai/fixes/` and `.ai/plans/intake/` for the same defect already
recorded. Add to that record rather than opening a second one.

## 2. Reproduce it before diagnosing it

Get the failure in front of you — a failing command, a script, a test. A fix
for a defect you never reproduced is a guess, and you will not know whether it
worked.

If you cannot reproduce it, say so plainly, record what you tried in the fix
document, and stop rather than changing code speculatively.

## 3. Write the record first

Allocate the next id — the highest `FIX-` anywhere under `.ai/fixes/`,
including `done/`, plus one. Numbers are never reused. Copy
`.ai/templates/FIX.md` to `.ai/fixes/open/FIX-{nnn}-{slug}.md` and fill in
**Symptom** and **Root cause** *now*, before touching code.

That ordering is the point. A fix record written afterwards describes the
change and forgets the defect, and the defect is the half that stops it
happening again.

Find the actual cause, not the place the symptom surfaces. If you end up
treating the symptom because the cause resisted you, write that down in **Root
cause** — a recorded guess is useful, a guess presented as a diagnosis is what
makes the recurrence baffling.

## 4. Make the change

Delegate to the **implementor** agent, which is the only agent that writes
production code, and give it the fix id. Smallest change that addresses the
cause. Nothing else — a fix that also tidies two files nearby is no longer
reviewable as a fix, and the tidying belongs in `/defer`.

## 5. Prove it

Add the check that **fails before the change and passes after it**, and put its
name and the pre-fix failure output in **Proof**. Then run
`verification.commands` from `.ai/config.yaml` in full — a fix that breaks
something else is not a fix.

**Do not close a fix without that check.** If an automated one is genuinely
impossible, say exactly why, record the manual verification, and report it as a
known weakness rather than a pass.

## 6. Close it

1. `git mv` the record into `.ai/fixes/done/<period>/`, per
   `lifecycle.done_partition` in `.ai/config.yaml`. Create the directory if
   needed.
2. If this came from an intake item, `git mv` that file to
   `.ai/plans/abandoned/` with a line pointing at the fix id — the problem is
   handled, so the capture is spent.
3. Append a journal entry: the defect, the cause, and the check that now guards
   it.
4. Update `.ai/state/STATE.md` only if this changed what is being worked on.
   A routine fix does not belong in **Now**.

Leave it in `open/` and say so if you could not finish — could not reproduce,
blocked on a decision, or it grew past what a fix should be.

## When it is not a fix

FIX items are code-only. Documentation and contract corrections each become
their own INTAKE. The autonomous review loop attempts code corrections once
between reviews 1 and 2, then leaves residual FIX items open for after all
other PLANs complete. It does not repeatedly invoke `/fix` to evade the ceiling.

Escalate to `/plan-new` and link the fix record from the plan when the work
needs an ADR, a spec rewrite, or more than a handful of files. A fix growing
into a plan is normal and expected. A behavior change landing as a fix is not:
it skips the plan-checker and the verifier, which is the one real risk this
route carries.

Report the fix id, the root cause in one sentence, the check that now guards
it, and anything you found and did not fix — captured with `/defer`, not merely
mentioned.
