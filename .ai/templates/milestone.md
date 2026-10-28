# Milestone Entry Template

Template for one entry in `.planning/MILESTONES.md`.

**Purpose:** Record what a milestone actually shipped, in terms a reader who was
not present can understand, so the project's delivery history survives the phase
directories it was derived from.

**Producer:** `milestone.complete` writes the entry's structure and facts; the
coordinator rewrites its prose in the complete-milestone `review_entry` step and
adds `**What's next:**`. Do not hand-write an entry — the runtime owns the
heading, ordering and file creation.

**Downstream consumers:**

| Consumer | Uses this record to |
|---|---|
| Returning coordinator | See what has already shipped before scoping new work |
| Milestone summariser | Anchor the long-form summary against the shipped facts |
| Onboarding reader | Learn the project's delivery history without reading every phase |
| Human maintainer | Distinguish released capability from planned capability |

Entries are append-only history. A shipped entry is not edited to reflect later
changes; a later milestone records those.

---

## File Template

Add this entry to `.planning/MILESTONES.md` when completing a milestone:

```markdown
## v[X.Y] [Name] (Shipped: YYYY-MM-DD)

**Delivered:** [One sentence describing what shipped]

**Phases completed:** [X-Y] ([Z] plans total)

**Key accomplishments:**
- [Major achievement 1]
- [Major achievement 2]
- [Major achievement 3]
- [Major achievement 4]

**Stats:**
- [X] files created/modified
- [Y] lines changed
- [Z] phases, [N] plans

**Git range:** `[first milestone commit]` → `[last milestone commit]`

**What's next:** [Brief description of next milestone goals, or "Project complete"]

---
```

<structure>
If MILESTONES.md doesn't exist, the runtime creates it with header:

```markdown
# Project Milestones

Entries in reverse chronological order - newest first.
```
</structure>

<guidelines>
**When to create milestones:**
- Initial v1.0 MVP shipped
- Major version releases (v2.0, v3.0)
- Significant feature milestones (v1.1, v1.2)
- Before archiving planning (capture what was shipped)

**Don't create milestones for:**
- Individual phase completions (normal workflow)
- Work in progress (wait until shipped)
- Minor bug fixes that don't constitute a release

**Stats to include:**
- Files changed and lines changed: `git diff --stat {first milestone commit}..HEAD | tail -1`
- Phase and plan counts from `milestone_phases` in the init result, not counted by hand
- Omit a stat you cannot source; an absent number is better than an invented one

**Git range format:**
- First commit of the milestone → last commit of the milestone
- Phase commits are scoped by padded phase number, so the range reads
  `docs(01): …` → `docs(04): …` for phases 1-4; SHAs are equally acceptable
</guidelines>

<example>
```markdown
# Project Milestones

Entries in reverse chronological order - newest first.

## v1.1 Security & Polish (Shipped: 2025-12-10)

**Delivered:** Security hardening with Keychain integration and comprehensive error handling

**Phases completed:** 5-6 (3 plans total)

**Key accomplishments:**
- Migrated API key storage from plaintext to macOS Keychain
- Implemented comprehensive error handling for network failures
- Added Sentry crash reporting integration
- Fixed memory leak in auto-refresh timer

**Stats:**
- 23 files modified
- 650 lines changed
- 2 phases, 3 plans

**Git range:** `docs(05): …` → `docs(06): …`

**What's next:** v2.0 SwiftUI redesign with widget support

---

## v1.0 MVP (Shipped: 2025-11-25)

**Delivered:** Menu bar weather app with current conditions and 3-day forecast

**Phases completed:** 1-4 (7 plans total)

**Key accomplishments:**
- Menu bar app with popover UI (AppKit)
- OpenWeather API integration with auto-refresh
- Current weather display with conditions icon
- 3-day forecast list with high/low temperatures
- Code signed and notarized for distribution

**Stats:**
- 47 files created
- 2,450 lines changed
- 4 phases, 7 plans

**Git range:** `docs(01): …` → `docs(04): …`

**What's next:** Security audit and hardening for v1.1
```
</example>

## Counterexample

```markdown
## v2.0 (Shipped: 2026-03-04)

**Delivered:** Lots of improvements

**Key accomplishments:**
- Refactored the codebase
- Various bug fixes
- Performance is much better now
```

Why this fails: no phase or plan span, so nothing ties the entry to the evidence
behind it; "lots of improvements" names no capability a reader could use; no
SUMMARY.md supports "performance is much better"; and the missing
`**What's next:**` leaves a returning session with no continuation. An entry is
a claim about delivered software, and every line of it has to be traceable to a
phase summary, a verification report or a Git range.

## Division of labour

| Part | Written by |
|---|---|
| Heading, `**Delivered:**` stub, phase/plan span, `**Stats:**` phase and plan counts | `milestone.complete` |
| Accomplishment bullets | `milestone.complete` extracts them from each phase SUMMARY.md; the coordinator edits them for readability |
| File and line counts, Git range | The coordinator, from the complete-milestone `gather_stats` step |
| `**What's next:**`, and the final prose of `**Delivered:**` | The coordinator, in `review_entry` |

## Completion criteria

- [ ] Every phase named in the span is Complete in the roadmap
- [ ] Each accomplishment traces to a phase SUMMARY.md, not to intent
- [ ] Stats are sourced from Git and the init result, with unsourceable ones omitted
- [ ] `**Delivered:**` reads as a capability, not as process
- [ ] `**What's next:**` names the next milestone or says "Project complete"
- [ ] The entry sits above all older entries, newest first
