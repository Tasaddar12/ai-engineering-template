---
description: Capture a problem you found but should not fix now, so it survives the session
argument-hint: <what's wrong, and where>
---

Read and follow [RULES](../RULES.md).

This mutating capture runs in an assigned worktree; use [worktree lifecycle](worktree.md).

Capture, without fixing: **$ARGUMENTS**

This exists so a discovered problem outlives the session that found it. A
finding you only mention in a summary is gone when the conversation ends, and
the next agent rediscovers it and improvises around it.

1. **Check it isn't already captured.** Search `.ai/fixes/`, `.ai/plans/intake/` and
   `.ai/plans/backlog/` for the same problem. If it is there, add what is new
   to that file instead of creating a second one.
2. **Classify the finding:**
   - Confirmed code defect, at any severity or scope → a code-only FIX in
     `.ai/fixes/open/`, from `.ai/templates/FIX.md`.
   - Wrong or missing documentation, including duplicated facts → its own
     INTAKE with `kind: documentation`.
   - Wrong or missing contract → its own INTAKE with `kind: contract`.
   - A question only a human can answer, blocking current work → `/plan-block`.
   - Uncertain defect → INTAKE with `kind: question`; do not label a guess a bug.
   - Other unplanned work → INTAKE with the appropriate kind.
3. **Write non-code findings** to `.ai/plans/intake/INTAKE-{nnn}-{slug}.md` from
   `.ai/templates/INTAKE.md`, numbered after the highest existing. Fill in
   what's wrong, where, why not now, and what it costs to leave. Five lines.
4. **Do not fix it.** Not a small version of it either. The point of capturing
   is that the current change stays reviewable.
5. If it is severe enough that leaving it is a bad idea — data loss, a security
   hole, a broken build — say so plainly in your report and recommend it be
   promoted immediately. Capturing something urgent is not the same as
   handling it, and it is your job to say which one this is.
6. Append a one-line journal entry, or return the event to the coordinator in
   a track. Use reserved IDs. In autonomous review set
   `deferred_until: all-other-plans-complete` on deferred FIX/INTAKE records.

Report the FIX or INTAKE id, the one-line problem, and your read on urgency. Then
carry on with what you were doing.

Code FIX items proceed through `/fix` after the other PLANs. Documentation,
contract and other INTAKE work proceeds through `/plan-new INTAKE-{nnn}`, where
it gets sized, spec'd and checked. Nothing in
`intake/` is a commitment to do the work — `/plan-archive` reviews the pile and
abandons what no longer matters.
