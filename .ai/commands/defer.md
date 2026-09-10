---
tier: contract
authority: agent
links: [AMD-002]
description: Capture a problem you found but should not fix now, so it survives the session
argument-hint: <what's wrong, and where>
---

Capture, without fixing: **$ARGUMENTS**

This exists so a discovered problem outlives the session that found it. A
finding you only mention in a summary is gone when the conversation ends, and
the next agent rediscovers it and improvises around it.

1. **Check it isn't already captured.** Search `.ai/plans/intake/` and
   `.ai/plans/backlog/` for the same problem. If it is there, add what is new
   to that file instead of creating a second one.
2. **Route the finding without repairing it.** Unconfirmed observations,
   waiting questions and suspected drift belong in INTAKE. A confirmed
   conformance defect belongs in a FIX record through `/report`; that does not
   authorize the repair. For a question blocking approved work, use `/plan-block`.
   If an already authorized correction is the next action, report that route
   rather than silently treating this capture command as implementation.
3. **Write it** to `.ai/plans/intake/INTAKE-{nnn}-{slug}.md` from
   `.ai/templates/INTAKE.md`, using config's ID allocation rules. Fill in
   what's wrong, where, why not now, and what it costs to leave. Five lines.
4. **Do not fix it.** Not a small version of it either. The point of capturing
   is that the current change stays reviewable.
5. If it is severe enough that leaving it is a bad idea — data loss, a security
   hole, a broken build — say so plainly in your report and recommend it be
   promoted immediately. Capturing something urgent is not the same as
   handling it, and it is your job to say which one this is.
6. Append a one-line journal entry.

Report the intake id, the one-line problem, and your read on urgency. Then
carry on with what you were doing.

Intake items get promoted by the route their `kind` calls for: a `bug` — suspected code nonconformance — through `/fix INTAKE-{nnn}`, which is one command end
to end; anything that changes what correct means through
`/plan-new INTAKE-{nnn}`, where it gets sized, spec'd and checked. Nothing in
`intake/` is a commitment to do the work — `/plan-archive` reviews the pile and
abandons what no longer matters.
