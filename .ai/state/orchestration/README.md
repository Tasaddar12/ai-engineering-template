---
tier: contract
authority: agent
title: Run and track evidence
---

# Run and track evidence

The [ORCH-RUN template](../../templates/ORCH-RUN.md) creates
`ORCH-{nnn}.md` here. The scheduler owns the board, shared STATE and journal.
The orchestrator role can draft the board when assigned; tracks cannot edit it.

Each track owns `<run>/<track>/RESEARCH-PLAN-{nnn}.md` and
`<run>/<track>/REVIEW-LOG.md` in its branch. Use the
[research template](../../templates/research.md) for a brief; the
[track command](../../commands/orchestrate-track.md) defines review-round and
terminal formats. Run/track/plan together identify a brief.

Read actual Git and forge state when resuming; after branch cleanup, use the
recorded merge revision. A missing terminal result is unknown, not ready.
Cold review excludes these evidence files. The coordinator still reviews
changes to operating documents here separately so exclusions hide no changes.
