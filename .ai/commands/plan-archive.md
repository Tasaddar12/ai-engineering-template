---
tier: contract
authority: agent
links: [AMD-002]
description: Sweep finished plans into their period folder, and abandon stale ones
argument-hint: [period]
---

Tidy the plan lifecycle. Period: **$ARGUMENTS** (default: the current one from
`lifecycle.done_partition` in `.ai/config.yaml`, e.g. `2026-Q3`).

1. **Sweep `done/`.** Any plan sitting loose in `.ai/plans/done/` moves by
   `git mv` into `done/<period>/`, created if needed.
2. **Sweep `.ai/fixes/`.** Any fix loose in `.ai/fixes/done/` moves into
   `done/<period>/`. Then look at `open/`: for each one, is it still being
   worked, or did it stall? A fix that could not be reproduced, or that grew
   past what a fix should be, needs saying out loud rather than sitting there.
   Flag two patterns specifically — a `done/` fix with an empty **Proof**
   section, which will recur, and several fixes sharing a root cause, which is
   a plan nobody has written being paid for one defect at a time.
3. **Triage `intake/`.** This is the pile that rots fastest, and an intake
   pile nobody reads is the same as never having captured anything. For each
   item, propose one of:
   - **fix** — `kind: bug`, and the specs already say what should happen; the
     user runs `/fix INTAKE-{nnn}`. Cheaper than a plan and the common case.
   - **promote** — worth doing, and it changes what correct means; the user
     runs `/plan-new INTAKE-{nnn}`
   - **abandon** — no longer matters, or was fixed incidentally. Verify it was
     actually fixed before saying so.
   - **keep** — still real, still not now

   Group them by `kind` and lead with anything marked severe. Say plainly if
   the pile is growing while nothing gets promoted — that means problems are
   being recorded instead of solved, which is a different failure from losing
   them but not much better.
4. **Review `backlog/`.** For each plan that no longer reflects what the
   project is doing, propose abandoning it. Do not abandon anything without
   telling the user which ones and why — this is a judgment call about scope,
   which is theirs.
5. **Abandon what they confirm.** `git mv` into `.ai/plans/abandoned/` and add
   an `## Abandoned` section: the date, the reason, and anything learned worth
   keeping. Abandoned plans are never deleted — the record of what was
   considered and rejected is worth more than the disk space, and it stops the
   same idea being re-proposed.
6. **Check `review/` and `blocked/`.** Anything that has been sitting a while
   gets flagged, not moved. A plan stuck in `blocked/` usually means the
   question never reached a human.
7. **Prune `.ai/state/STATE.md`.** It is `status` tier and describes only the
   present: trim **Recently verified** to the last handful and drop anything
   already visible in `done/`. History belongs in the journal.
8. Append a journal entry recording the sweep.

Report a one-line summary per stage: what moved, what was abandoned and why,
what is stuck and needs attention. Do not touch specs, decisions, amendments,
or fix records in `done/` — those are permanent regardless of which plan
produced them.
