# Milestone record contract

**Purpose:** Preserve what shipped, its evidence and any explicitly deferred scope.
**Producer:** complete-milestone coordinator, after auditing every selected phase.
**Consumers:** progress, new-milestone and onboarding readers. Counts come from the runtime `milestone_phases` result, never guessed statistics.

# Milestone Entry Template

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
- [Y] lines changed (actual Git diff)
- [Z] phases and [N] plans from milestone_phases

**Git range:** `[first SHA]` → `[last SHA]`

**What's next:** [Brief description of next milestone goals, or "Project complete"]

---
```

<structure>
If MILESTONES.md doesn't exist, create it with header:

```markdown
# Project Milestones: [Project Name]

[Entries in reverse chronological order - newest first]
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
- Count modified files: `git diff --stat FIRST_SHA LAST_SHA`
- Count lines changed: `git diff --numstat FIRST_SHA LAST_SHA`
- Phase/plan counts from milestone_phases

**Git range format:**
- First commit of milestone → last commit of milestone
- Example: `[first SHA]` → `docs(04)` for phases 1-4
</guidelines>

<example>
```markdown
# Project Milestones: WeatherBar

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
- 2 phases, 3 plans (milestone_phases)

**Git range:** `[first SHA]` → `docs(06)`

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
- 4 phases, 7 plans (milestone_phases)

**Git range:** `[first SHA]` → `docs(04)`

**What's next:** Security audit and hardening for v1.1
```
</example>

## Counterexample

Bad: "Shipped 12,000 LOC in three days; everything complete." This conflates size with delivered value and hides gaps.

Good: "Shipped the account recovery flow across two phases and four plans, with 418 lines changed. Verification reports identify the tested revisions and human acceptance. Deferred retry analytics retains its explicit disposition."

## Division of labour

The coordinator selects the milestone, audits phase evidence, uses runtime counts from `milestone_phases`, records the shipped outcome and archives exact selected records. Workers return their owned evidence; they do not close milestones or publish independently. Commit ranges use actual SHA ranges or `docs(NN)` bookkeeping commits, not assumed `feat(XX-XX)` prefixes.

## Completion criteria

Every selected phase has a reconciled verification outcome; required checks and human acceptance are present; remaining scope has an explicit authorized disposition; shipped revision and PRs are linked; runtime archival preserves history. Record lines changed and actual phase/plan counts. Missing evidence keeps the milestone open.
