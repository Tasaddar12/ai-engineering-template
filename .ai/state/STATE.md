---
tier: status
authority: agent
id: STATE
title: Where things stand
links: []
updated: 2026-09-09
---

# State

> **`status` tier.** Overwrite freely — this file is expected to churn every
> session. It describes the present only; history belongs in
> [the journal](journal/).

## Now

Nothing in flight. The `/orchestrate` pipeline landed on
`full-orchestration-template` and has not been exercised on a real run yet.

## Next

Do a first real run to exercise the review loop and merge, which are the parts
never executed. `/orchestrate --all-backlog --dry-run` first.

Also: `.ai/state/PROJECT.md` is still the `CHANGEME` placeholder, and both
`orchestrator` and `track-reviewer` cite it as authority when deciding what to
schedule and what to approve.

## Blockers

Questions that need a human. Each with the plan it blocks, the options, and a
recommendation. Move the blocked plan to `plans/blocked/` as well.

| Blocks | Question | Recommendation |
|---|---|---|
| | | |

## Recently landed

Last few completed plans, newest first, so a returning reader has context
without reading the journal.

## Known drift

Places where documents and reality are suspected to disagree but have not been
reconciled yet. Anything sitting here is a legitimate, always-in-scope task:
confirm which side is right, amend, and remove the line.
