---
tier: plan
authority: agent
id: INTAKE-{nnn}
title: <the problem, in a few words>
found: YYYY-MM-DD
found_by: <agent or person>
found_while: PLAN-{nnn}
kind: documentation  # documentation | contract | debt | idea | question
links: []
deferred_until: none # all-other-plans-complete for deferred review corrections
---

# INTAKE-{nnn}: <the problem, in a few words>

> **`plan` tier, `plans/intake/` stage.** A captured problem, not yet a plan.
> Keep it to what you knew at the moment you found it — five lines is a good
> length. It gets properly planned by `/plan-new` when someone picks it up.

## What's wrong

One or two sentences. What you observed, not what you would do about it.

## Where

`path/to/file.ext` and the relevant symbol/general area, or the document id.

## Why it wasn't fixed then

Out of scope for the plan in hand · needs a decision · needs its own change ·
larger than it looks.

## What it costs to leave

Who or what breaks, and how badly. This is what decides whether it ever gets
picked up, so be honest rather than dramatic — "cosmetic" is a valid answer.

<!--
Naming: INTAKE-{nnn}-{slug}.md in .ai/plans/intake/, numbered in its own
sequence.

Documentation and contract corrections become their own planned work through
/plan-new INTAKE-{nnn}. Confirmed code defects go directly to FIX, not INTAKE.
If investigating a question proves a code defect, create a linked FIX then.

Either way the new record gets a fresh number and links back to this id; this
file moves to plans/done/<period>/ once evidence proves the work resolved it.
Use plans/abandoned/ for a human decision not to pursue it.

Do NOT fix the thing while writing this. Capturing is a five-line interruption;
fixing is scope creep, and it is what turns one reviewable change into an
unreviewable one.
-->
