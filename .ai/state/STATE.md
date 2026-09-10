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

Also: `.ai/intent/PROJECT.md` is still the `CHANGEME` placeholder, and both
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

- `/orchestrate` and its seven agents — building several plans at once in
  parallel git worktrees. See [docs/ORCHESTRATION.md](../../docs/ORCHESTRATION.md).
- The `.ai/` template restructure, replacing the old skill collection.

## Known drift

Places where documents and reality are suspected to disagree but have not been
reconciled yet. Anything sitting here is a legitimate, always-in-scope task:
confirm which side is right, amend, and remove the line.

- The orchestration pipeline is written but has never run end to end. The
  worktree mechanics are verified on Windows; the review loop and the merge
  step are not. Treat the first real run as a test of them.
- Worktree confinement blocks `Write`/`Edit` outside the checkout
  (`worktree-confine.sh`, 20/20 on its test matrix) but `Bash` enforcement is
  narrow by design — shell cannot be parsed reliably, so a determined escape
  gets through. It stops mistakes, not an adversary.
- No forge CLI (`gh` / `glab`) is installed on this machine and `origin` is a
  self-hosted GitLab, so a run here takes the `forge: none` path — it reviews
  and merges locally rather than opening a merge request.

