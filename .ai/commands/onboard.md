---
tier: contract
authority: agent
description: Set up the .ai/ structure for this project, or brief yourself on an existing one
---

Bring this project's `.ai/` structure to life. Behave differently depending on
what you find.

## If `.ai/state/PROJECT.md` still says `CHANGEME`

This is a fresh drop-in. Set it up:

1. **Read the repository** before asking anything — languages, frameworks,
   entry points, test setup, existing docs, recent git history. Come to the
   conversation already informed.
2. **Pick a mode** and say why, then confirm with the user:
   - `light` — small or short-lived. No specs, one plan at a time.
   - `standard` — default for real projects.
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

   For each requirement-bearing document you find, propose one of three, and
   get the user's call before moving anything:
   - **Promote** — it is a real contract. Rewrite it as a spec in `.ai/specs/`
     (acceptance criteria, not implementation) and replace the original with a
     link. **Promote only the parts that are true right now.** Existing docs
     are usually layered with history and aspiration — "deprecated in 2.1",
     "planned for Q4", a changelog section, a struck-through paragraph. A spec
     states what *is*: drop all of it, keep the present-tense requirement, and
     say what you dropped. Anything aspirational becomes an intake item or a
     plan, never a spec criterion.
   - **Leave** — it is human-facing documentation. It stays in `docs/`, and no
     spec restates it. Migration guides, changelogs and upgrade notes belong
     here permanently — history is their whole point, which is exactly why it
     is not the spec's.
   - **Retire** — it describes a past state. Say so and propose deleting it; a
     stale document that stays will be read as a requirement.

   Do not silently duplicate anything into `.ai/specs/`. List what you found,
   your recommendation for each, and let the user decide.

   **Meeting notes and design docs are a fourth case — do not treat them as
   requirements.** They are `log` tier: a record of what was said, where a
   rejected option reads exactly like a chosen one. Inventory them, `git mv`
   them under `.ai/decisions/meetings/`, and leave them unharvested. Point the
   user at `/harvest` for the ones covering the area about to be worked on.
   Harvesting a backlog of them during onboarding produces a pile of ADRs
   nobody has verified.
5. **Audit the existing `AGENTS.md` and `.ai/agents/` for contradictions.**
   This is the other retrofit trap. Look for language that forbids editing
   documentation — "never modify the spec", "the plan is the source of truth",
   "do not change requirements" — and for agent definitions whose `tools:` list
   omits `Write`/`Edit`. Both cause the refuse-or-contort behavior directly,
   and both will now contradict `.ai/RULES.md`, leaving agents with two
   conflicting instructions. Report every instance and propose the edit.

   Look for one more thing while you are in there: instructions to *preserve*
   documentation history — "mark requirements deprecated rather than removing
   them", "keep a changelog at the top of each spec", "never delete a
   requirement". Those read as prudence and produce the specs-as-archaeology
   problem instead, and they will fight the present-tense rule. Propose moving
   that history into `docs/`, where it belongs, and out of the specs.
6. **Write the first specs** from `.ai/templates/SPEC.md` for behavior that already exists and matters, if
   the mode calls for specs. Acceptance criteria, not implementation, and
   **present tense only** — every sentence has to be true of the code as it is
   today. Not what the team wishes were true, not what is half-built behind a
   flag. Behavior nobody has built yet is a plan, and behavior that used to be
   true is not recorded at all.

   Only for the areas about to be worked on — retro-specifying a whole codebase
   produces a pile of unverified claims, which is worse than having no specs.
7. **Sweep the project's known problems into `.ai/plans/intake/`.** An
   in-flight project already knows about a pile of deferred work; it is just
   scattered where no agent will look. Gather it:
   - `TODO`, `FIXME`, `HACK`, `XXX` comments in the source
   - skipped, commented-out, or currently failing tests
   - anything the README or docs describe as temporary, known broken, or
     "for now"
   - open tickets and bugs — **ask the user for these**, you cannot see them

   **Cluster before writing.** Fifty `TODO`s become a handful of intake items
   by theme, not fifty files — an intake pile nobody can read is the same as no
   pile. Write one `INTAKE-{nnn}` per real problem from
   `.ai/templates/INTAKE.md`, and for trivia that will never be scheduled, say
   so and write nothing.

   Show the user the clustered list with your read on severity before writing
   the files. Nothing in `intake/` commits anyone to doing the work.

   Mark each one's `kind`, since that decides its route out: a `bug` — code
   that contradicts a spec — gets promoted with `/fix`, everything else with
   `/plan-new`. Say which of the pile look like same-day `/fix` candidates;
   that is usually the most useful thing to come out of this step.
8. **Capture decisions that were made but never written down.** Ask the user
   what the project's real architectural commitments are — and check the git
   history and any design notes for choices that clearly got made. Anything
   still live and load-bearing becomes an ADR from `.ai/templates/ADR.md` in `.ai/decisions/`. Write only
   the ones the user confirms; inventing a rationale for a past decision is
   worse than leaving it unrecorded.

   Where one decision clearly replaced another and both matter, record both and
   mark the older `status: superseded` with `superseded_by:` — an ADR is a
   dated record and is allowed to describe the past, which is the one place in
   `.ai/` where history belongs. Only `status: accepted` is authority, so this
   is what stops a fresh agent implementing from an obsolete decision.
9. **Seed the backlog** with plans for what is explicitly agreed next.
   Work already in progress becomes a plan
   in `.ai/plans/active/` describing the remaining steps, not the finished ones.
10. **Initialize `.ai/state/STATE.md`** with Now, Next, Blockers and Known drift
    describing the real present, including any suspected drift you noticed.
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
and any drift you spotted between the documents and the code. List drift as
candidate work. An orientation request does not authorize restructuring;
return proposed intake items if record writes have not been requested.
