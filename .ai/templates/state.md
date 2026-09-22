# State Template

Template for `.planning/STATE.md` — the project's living memory.

---

## File Template

The frontmatter is derived, never authored: `state.save` recomputes `progress`
from ROADMAP.md on every write, so the two cannot disagree.

**Every section below has a runtime writer, and the set is closed.** A section
that appears here but is written by nothing is dead weight that agents hand-fill
and drift; a section the runtime writes but this template omits is an unbudgeted
section nobody planned for. `planning.validate` checks both directions. See the
[STATE contract](../runtime/TEMPLATE-CONTRACT.md) for the writer of each one.

<!-- STATE-MD-SCHEMA:START:frontmatter -->
```markdown
---
workflow_state_version: '1.0'  # authoring metadata; coordinator maintains from observed evidence
status: planning
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---
<!-- STATE-MD-SCHEMA:END:frontmatter -->

# Project State

## Project Reference

See: .planning/PROJECT.md (updated [date])

**Core value:** [One-liner from PROJECT.md Core Value section]
**Current focus:** [Current phase name]

## Current Position

Phase: [X] of [Y] ([Phase name])
Plan: [A] of [B] in current phase
Status: [Ready to plan / Planning / Ready to execute / In progress / Phase complete]
Last activity: [YYYY-MM-DD] — [What happened]

Progress: [░░░░░░░░░░] 0%

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Phase X]: [Decision summary]
- [Phase Y]: [Decision summary]

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work. Cleared with `state.clear-blocker` when
resolved - removed, not struck through.]

None yet.

### Roadmap Evolution

[Phase added, inserted, edited or removed. Written by the roadmap verbs; the
5 most recent survive, older ones rotate to .planning/archive/STATE-LOG.md.]

None yet.

## Deferred Items

Items acknowledged and deferred at milestone close, written by
`state.add-deferred`, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: [YYYY-MM-DD HH:MM]
Stopped at: [Description of last completed action]
Resume file: [Path to .continue-here*.md if exists, otherwise "None"]
```

<purpose>

STATE.md is the project's short-term memory spanning all phases and sessions.

**Problem it solves:** Information is captured in summaries, issues, and decisions but not systematically consumed. Sessions start without context.

**Solution:** A single, small file that's:
- Read first in every workflow
- Updated after every significant action
- Contains digest of accumulated context
- Enables instant session restoration

</purpose>

<lifecycle>

**Creation:** After ROADMAP.md is created (during init)
- Reference PROJECT.md (read it for current context)
- Initialize empty accumulated context sections
- Set position to "Phase 1 ready to plan"

**Reading:** First step of every workflow
- progress: Present status to user
- plan: Inform planning decisions
- execute: Know current position
- transition: Know what's complete

**Writing:** After every significant action
- execute: After SUMMARY.md created
  - Update position (phase, plan, status)
  - Note new decisions (detail in PROJECT.md)
  - Add blockers/concerns
- transition: After phase marked complete
  - Update progress bar
  - Clear resolved blockers
  - Refresh Project Reference date

</lifecycle>

<sections>

### Project Reference
Points to PROJECT.md for full context. Includes:
- Core value (the ONE thing that matters)
- Current focus (which phase)
- Last update date (triggers re-read if stale)

Claude reads PROJECT.md directly for requirements, constraints, and decisions.

### Current Position
Where we are right now:
- Phase X of Y — which phase
- Plan A of B — which plan within phase
- Status — current state
- Last activity — what happened most recently
- Progress bar — visual indicator of overall completion

Progress calculation: (completed plans) / (total plans across all phases) × 100%

### Accumulated Context

**Decisions:** The 5 most recent, for quick access. `state.add-decision` writes
each one to the PROJECT.md Key Decisions table at the same time, so the digest
can be trimmed without consulting anything. The full log lives in PROJECT.md.

**Pending Todos:** Ideas recorded by the coordinator from the current assignment.
- Keep one bullet per pending item; never collapse multiple items into a count.
- Use `- [date] [area] title — [todo file](repository-relative path) — Needs ...`
  when a record exists. Keep the bullet concise (up to 240 characters) without
  dropping the actionable condition. If no record exists, retain the item as
  prose rather than fabricating a path.
- Use `None yet.` when there are no pending items.
- Maintain this section directly; no separate todo command or generated init payload is installed.

**Blockers/Concerns:** From "Next Phase Readiness" sections
- Issues that affect future work
- Prefix with originating phase
- Cleared with `state.clear-blocker` when addressed, which removes the entry and
  appends it to the archive log. Do not mark it resolved in place.

**Roadmap Evolution:** One entry per phase added, inserted, edited or removed,
written by the roadmap verbs so the digest explains why the phase numbering looks
the way it does. Bounded to 5; the rest is in the archive log and the milestone
records.

### Session Continuity
Enables instant resumption:
- When was last session
- What was last completed
- Is there a .continue-here file to resume from

</sections>

<size_constraint>

**Budget: 125 lines.** The empty skeleton above is already around 55, so a single
global number was never enough guidance on its own. The budget is enforced per
section, by the runtime, on every write:

| Section | Cap | Enforced by | Overflow goes to |
|---------|-----|-------------|------------------|
| Decisions | 5 entries | `state.add-decision` | PROJECT.md Key Decisions (recorded at the same time), plus the archive log |
| Blockers/Concerns | 10 entries | `state.add-blocker` | Archive log; resolve with `state.clear-blocker` |
| Roadmap Evolution | 5 entries | `state.add-roadmap-evolution` | Archive log |
| Deferred Items | 10 rows | `state.add-deferred` | Archive log |
| Pending Todos | - | `state.sync-todos` replaces it wholesale from disk | `.planning/todos/` |

Rotation is never deletion: every trimmed entry is appended to
`.planning/archive/STATE-LOG.md` before it leaves the digest, and decisions are
written to PROJECT.md as they are added, not as they are trimmed. That is what
makes trimming safe enough to do automatically.

The goal is "read once, know where we are" — if it's too long, that fails.
`planning.validate` reports a warning when the file exceeds the budget, so the
overrun is visible at `/progress` instead of being discovered a week later.

</size_constraint>

<retirement>

**Never strike through an entry, and never annotate one as "Closed", "Done" or
"Superseded" in place.** An item that no longer applies is removed from STATE.md
and recorded where that kind of fact is owned:

| Item | How it retires | Where it lands |
|------|----------------|----------------|
| Decision | Already in PROJECT.md when added; rotates out of the digest | PROJECT.md Key Decisions |
| Decision reversed | Record the replacement; supersede the ADR | New ADR with `supersedes` set |
| Blocker | `state.clear-blocker "<match>"` | Archive log |
| Requirement satisfied | `requirements.set-status <id> Complete` | REQUIREMENTS.md Traceability |
| Todo | `todo.complete` | `.planning/todos/completed/` |
| Item deferred at milestone close | `state.add-deferred` | Deferred Items table |

Strikethrough is what agents reach for when no retirement path exists. Each row
above is that path. `planning.validate` flags `~~strikethrough~~` and in-place
closure markers in any planning record.

</retirement>


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

Read this complete authoring guide, including its examples and methods.
Source attribution is available in `.ai/THIRD-PARTY-NOTICES.md`.

Read `.ai/agents/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local runtime behavior,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. Only the documented local runtime commands are installed. Tool names and product
examples do not establish that a tool is available; inspect the actual project
configuration and host capabilities before using them. Bundled supporting methods provide local guidance for explicit assignments;
they do not install additional runtime features.
Local rules, recorded authorization, plan-declared ownership and verification
safeguards govern execution. Publication never merges.
<!-- LOCAL-ADOPTION:END -->
