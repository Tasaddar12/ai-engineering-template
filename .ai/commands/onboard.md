---
description: Set up the .ai/ structure for this project, or brief yourself on an existing one
---

Read and follow [RULES](../RULES.md).

Run onboarding writes in an assigned worktree; use [worktree lifecycle](worktree.md).

Bring this project's `.ai/` structure to life. Behave differently depending on
what you find.

## If `.ai/state/PROJECT.md` still says `CHANGEME`

This is a fresh drop-in. Set it up:

1. **Read the repository** before asking anything — languages, frameworks,
   entry points, test setup, existing docs, recent git history. Come to the
   conversation already informed.
2. **Pick a mode** and say why, then confirm with the user:
   - `light` — small or short-lived, with compact planning.
   - `standard` — default for real projects.
   - `full` — long-running or multi-team. Adds a roadmap of phases.
   Write it into `.ai/config.yaml`, along with `project.name`,
   `project.summary`, and `verification.commands` (the real test and lint
   commands for this repo — an empty list makes the verifier much weaker).
3. **Interview the user for `.ai/state/PROJECT.md`.** This is `intent` tier and
   human authority, so ask rather than invent. Push hardest on **Non-goals**
   and **Hard constraints** — those are what keep agents from confidently
   building the wrong thing. Draft from what they say, then have them confirm.
4. **Adopt what the project already has.** On a project already in flight this
   is the step that decides whether the structure helps or hurts. Requirements
   are already written down somewhere — `README.md`, `docs/`, design notes, a
   `AGENTS.md`, comments, ticket links. Copying `.ai/` in beside them creates a
   *second* home for the same facts, which is the exact duplicated-fact failure
   `.ai/truth-map.md` exists to prevent.

   Inventory the documents and the code areas they discuss. Propose **leave**
   for useful human guides/history and **retire** for obsolete material, with
   the exact proposed moves/deletions for the user's decision. Use those areas
   to direct code inspection in step 6 under
   [Configuration and onboarding](../RULES.md#configuration-and-onboarding).
   Keep this inventory separate from evidence supporting SPEC claims.

   - **Leave** — useful human-facing documentation stays in `docs/`.
     Migration guides, changelogs and upgrade notes preserve history.
   - **Retire** — obsolete documentation gets a named move/deletion proposal
     and a reason, so the user can review exactly what would be lost.
   - **Inspect code** — identify the entry points, callers and checks that
     establish implemented behavior for the documentor's later SPEC work.

   **Meeting notes and design docs are a fourth case — do not treat them as
   requirements.** They are `log` tier: a record of what was said, where a
   rejected option reads exactly like a chosen one. Inventory them, `git mv`
   them under `.ai/decisions/meetings/`, and leave them unharvested. Point the
   user at `/harvest` for the ones covering the area about to be worked on.
   Harvesting a backlog of them during onboarding produces a pile of ADRs
   nobody has verified.
5. **Audit the existing `AGENTS.md` and `.ai/agents/` for contradictions.**
   This is the other retrofit trap. Compare each agent's instructions and tools
   with its intended scope: documentation agents need usable write tools;
   code reviewers stay read-only; implementors report documentation discoveries.
   Look for automatic intent overrides, conflicting handoff instructions and
   documentation-agent prohibitions that contradict `.ai/RULES.md`.
   Report exact files and sections and propose targeted edits.

   Look for one more thing while you are in there: instructions to *preserve*
   documentation history — "mark requirements deprecated rather than removing
   them", "keep a changelog at the top of each spec", "never delete a
   requirement". Those read as prudence and produce the specs-as-archaeology
   problem instead, and they will fight the present-tense rule. Propose moving
   that history into `docs/`, where it belongs, and out of the specs.
6. **Review the relevant actual code**, including callers and checks, then
   hand the evidence to a documentation agent to write the first SPECs for
   implemented behavior in the areas about to be worked on. Use
   [What each document is for](../RULES.md#what-each-document-is-for). For
   greenfield areas, capture proposed behavior in PLAN/INTAKE until code exists.
7. **Sweep known problems into a classified inventory.** Gather:
   - `TODO`, `FIXME`, `HACK`, `XXX` comments
   - skipped, commented-out or failing tests
   - temporary or known-broken behavior mentioned in existing guides
   - tickets available through the user's supplied sources

   Investigate enough to distinguish confirmed code bugs from unknowns and
   fragments using [Bug fixes](../RULES.md#bug-fixes). Cluster related findings,
   show the user the proposed FIX/INTAKE list with urgency, then write the
   confirmed inventory through the assigned record owner. Include which FIXes
   look ready for `/fix` and which captures need investigation or `/plan-new`.

8. **Capture decisions that were made but never written down.** Ask the user
   what the project's real architectural commitments are — and check the git
   history and any design notes for choices that clearly got made. Anything
   still live and load-bearing goes to the documentor for an ADR in
   `.ai/decisions/` after the code review handoff. Record only
   the ones the user confirms; inventing a rationale for a past decision is
   worse than leaving it unrecorded.

   Where one decision clearly replaced another and both matter, record both and
   mark the older `status: superseded` with `superseded_by:` — an ADR is a
   dated record and is allowed to describe the past, which is the one place in
   `.ai/` where history belongs. Only `status: accepted` is authority, so this
   is what stops a fresh agent implementing from an obsolete decision.
9. **Seed the backlog** with plans for what is obviously next.
   Work already in progress becomes a plan
   in `.ai/plans/active/` describing the remaining steps, not the finished ones.
10. **Initialize `.ai/state/STATE.md`** with the real present — including
   anything you noticed under **Known drift**.
11. **Wire up the root `AGENTS.md`.** Append
   `.ai/templates/AGENTS.snippet.md`; if the project has no `AGENTS.md`, create
   one from it. An agent that never reads `RULES.md` will fall back to exactly
   the refuse-or-contort behavior the structure exists to prevent, so do not
   finish onboarding without this.

Report the mode, what you wrote, and what still needs the user's input.

## If it is already set up

Brief yourself and report — do not restructure anything:

1. Read `.ai/RULES.md`, `.ai/truth-map.md`, `.ai/config.yaml`,
   `.ai/state/PROJECT.md`, `.ai/state/STATE.md`, and the latest journal entry.
2. Read the specs, and the plans in `active/`, `review/` and `blocked/`. For
   the active plans, read their **Contract changes** section — that is what the
   specs are about to say.
3. Skim `.ai/plans/intake/` — captured problems nobody has picked up. Note
   anything that looks urgent, or anything that overlaps what is active now.
   Skim `.ai/fixes/open/` too: an open fix is either in flight or stalled.
4. Spot-check the record against reality: does the code look like what the
   specs describe? Sample two or three criteria rather than auditing
   everything.
5. Check the specs are in the present tense — nothing marked deprecated, no
   criteria for behavior that does not exist. Either is drift, and it is the
   kind that makes every later reading of that spec a guess.

Report: what this project is, where it stands, what is next, what is blocked,
and any drift you spotted between the documents and the code. List drift as candidate work with evidence and its appropriate owner under
[Roles](../RULES.md#roles).
Capture with `/defer` anything you find that you are not about to fix.
