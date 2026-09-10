---
tier: contract
authority: agent
description: Show every plan by stage, plus current state, blockers and suspected drift
allowed-tools: Read, Grep, Glob, Bash
---

Report where this project stands. Read, do not change anything.

1. List plan files in each stage directory under `.ai/plans/` — `intake/`,
   `backlog/`, `active/`, `blocked/`, `review/`, `done/` (all partitions), and `abandoned/`. Take each plan's title from its frontmatter.
2. List fix files in `.ai/fixes/open/` and `.ai/fixes/done/` (all partitions), with their `severity`.
3. Read `.ai/state/STATE.md`.
4. Read the most recent file in `.ai/state/journal/`.

List every PLAN by ID, title and stage, grouping done records by partition.
Intake and fix records retain their own kinds. Then output the compact totals:

```
ACTIVE      PLAN-nnn  <title>          (n of max_active)
REVIEW      PLAN-nnn  <title>
BLOCKED     PLAN-nnn  <title>  — <the question>
BACKLOG     n plans   (next up: PLAN-nnn <title>)
INTAKE      n captured, unplanned  (oldest: <date>)
FIXES       FIX-nnn  <title>  [severity]        (n open)
DONE        n plans, n fixes across listed partitions
ABANDONED   n
```

List intake items individually only if there are five or fewer, or if one looks
urgent — otherwise the count and the oldest date are enough. List every open
fix: there should not be many, and one sitting open is usually one that could
not be reproduced or that quietly grew into a plan.

Follow it with:

- **Now / Next** from `.ai/state/STATE.md`
- **Blockers**, each with the question and its recommendation
- **Known drift** — documents suspected of disagreeing with reality

Close with anything that looks wrong and is worth acting on:

- `active/` over `lifecycle.max_active` in `.ai/config.yaml`
- a plan in `active/` with no recent journal entry
- a plan in `review/` that has been there a while
- entries under **Known drift** that nobody has reconciled
- an intake item marked severe, or an intake pile that is growing and never
  being promoted — that means work is being captured but never scheduled
- a fix in `open/` that has been there a while, or a `critical` one still open
- several fixes pointing at the same root cause — that is a plan nobody has
  written, being paid for one defect at a time
- a fix in `done/` with an empty **Proof** section: it will recur
- `.ai/state/PROJECT.md` still containing `CHANGEME`

Use the compact totals and observations above for the report. Be brief; this
is a status check, not an audit.
