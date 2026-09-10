---
tier: plan
authority: agent
id: INTAKE-{nnn}
title: <the problem, in a few words>
found: YYYY-MM-DD
found_by: <agent or person>
found_while: PLAN-{nnn}
kind: bug            # bug | drift | debt | idea | question
links: []
---

# INTAKE-{nnn}: <the problem, in a few words>

> **`plan` tier, `plans/intake/` stage.** A captured problem, not yet a plan.
> Keep it to what you knew at the moment you found it — five lines is a good
> length. It gets properly planned by `/plan-new` when someone picks it up.

## What's wrong

One or two sentences. What you observed, not what you would do about it.

## Where

`path/to/file.ext:42`, or the spec or document id.

## Why it wasn't fixed then

Out of scope for the plan in hand · needs a decision · needs its own change ·
larger than it looks.

## What it costs to leave

Who or what breaks, and how badly. This is what decides whether it ever gets
picked up, so be honest rather than dramatic — "cosmetic" is a valid answer.

<!--
Naming: INTAKE-{nnn}-{slug}.md in .ai/plans/intake/, numbered in its own
sequence.

Promotion goes by `kind`:
  bug  — code that contradicts a spec        -> /fix INTAKE-{nnn}
  anything that changes what correct means   -> /plan-new INTAKE-{nnn}

Either way the new record gets a fresh number and links back to this id; this
file then moves to plans/abandoned/ once the work lands, or if planning it
reveals it is not worth doing.

Do NOT fix the thing while writing this. Capturing is a five-line interruption;
fixing is scope creep, and it is what turns one reviewable change into an
unreviewable one.
-->
