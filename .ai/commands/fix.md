---
description: Diagnose, record and fix a single defect, with the check that stops it coming back
argument-hint: <what's broken, or a FIX/INTAKE id>
---

Read and follow [RULES](../RULES.md).

Run this mutating FIX lifecycle in an assigned worktree; use [worktree lifecycle](worktree.md).

Fix: **$ARGUMENTS**

If the argument is a `FIX-{nnn}` id, resume that record in `.ai/fixes/open/`.
If it is an `INTAKE-{nnn}` id, read it first. A confirmed code defect gets a
linked FIX; documentation or contract work stays INTAKE for `/plan-new`.

This is the short route for a small bounded change that makes the code do what
the record already says it should. Large or multiple-defect conformance repairs
may use an approved PLAN coordinating linked FIX records while preserving each
existing contract. If what is being asked for is new or different behavior,
say so and use `/plan-new`; see `.ai/RULES.md#bug-fixes`.

## 1. Establish it is a defect, not a disagreement

Find the requirement, approved target or demonstrable code invariant the
code contradicts. Use [Bug fixes](../RULES.md#bug-fixes) for classification. Then one of:

- **A spec forbids the observed behavior** → a defect. Proceed.
- **No spec covers the case** → use existing PLAN acceptance or a demonstrable code invariant if it
  establishes the defect. Any missing contract decision gets a separate INTAKE; do
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

Use the coordinator-issued FIX id block, or the serialized standalone single-ID
allocation in [Scheduling and IDs](../RULES.md#scheduling-and-ids). Do not
derive an id from the highest filename; collision checks cover lifecycle
directories, registered worktrees, reviewed issued blocks and common receipts.
Render `.ai/templates/FIX.md` with `.ai/runtime/render_record.py` and save its
stdout as `.ai/fixes/open/FIX-{nnn}-{slug}.md`; fill in
**Symptom** and **Root cause** *now*, before touching code.

That ordering is the point. A fix record written afterwards describes the
change and forgets the defect, and the defect is the half that stops it
happening again.

Find the actual cause, not the place the symptom surfaces. If you end up
treating the symptom because the cause resisted you, write that down in **Root
cause** — a recorded guess is useful, a guess presented as a diagnosis is what
makes the recurrence baffling.

## 4. Make the change

Delegate to the assigned **implementor** or **track-fixer** agent, and give it the fix id. Smallest change that addresses the
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

## 6. Review and close it

Gather the code review and hand its evidence to the documentation agent for
any record/documentation updates under
[Review and documentation](../RULES.md#review-and-documentation).

1. Build the complete source-to-destination mapping for the FIX and any linked
   closing INTAKE. Call pure `rebase_record_links(text, source, target, moves)`
   for every source and retain each returned string before moving anything.
   Then `git mv` the validated records into `.ai/fixes/done/<period>/` and,
   when proven resolved, `.ai/plans/done/<period>/`; write the returned UTF-8
   text at each target, stage and commit the mechanical moves. Use
   `lifecycle.done_partition` in `.ai/config.yaml`.
2. Append a journal entry: the defect, the cause, and the check that now guards
   it.
3. Update `.ai/state/STATE.md` only if this changed what is being worked on.
   A routine fix does not belong in **Now**.

Leave it in `open/` and say so if you could not finish — could not reproduce,
blocked on a decision, or it grew past what a fix should be.

## When it is not a fix

FIX items are code-only. Documentation and contract corrections each become
their own INTAKE. The autonomous review loop attempts code corrections once
between reviews 1 and 2, then leaves residual FIX items open until an affected
integrated or preserved tree is available. It does not repeatedly
invoke `/fix` to evade the ceiling.

Escalate to `/plan-new` and link the fix record from the plan when the work
needs an ADR, a spec rewrite, or more than a handful of files. An approved PLAN
may coordinate multiple or large linked conformance FIX records; each FIX still
keeps its reproduction, root cause and proof, and closes only with evidence.
Small bounded conformance repairs remain on `/fix`. A behavior change landing
as a fix needs explicit PLAN Contract changes and intent resolution.

Report the fix id, the root cause in one sentence, the check that now guards
it, and anything you found and did not fix — captured with `/defer`, not merely
mentioned.
