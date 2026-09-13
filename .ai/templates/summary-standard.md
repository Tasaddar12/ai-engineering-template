---
phase: XX-name
plan: YY
subsystem: [primary category]
tags: [searchable tech]
provides:
  - [bullet list of what was built/delivered]
affects: [list of phase names or keywords]
actuals:
  tokens: [chars/4 over files actually changed]
  tasks: [tasks completed]
  commits: [commits made]
tech-stack:
  added: [libraries/tools]
  patterns: [architectural/code patterns]
key-files:
  created: [important files created]
  modified: [important files modified]
key-decisions:
  - "Decision 1"
# coverage: (#1602) optional per-deliverable UAT-routing block — see .ai/templates/summary.md <coverage_guidance>.
#   Add live `coverage:` entries (id/description/verification[]/human_judgment[/rationale]) to enable
#   deterministic UAT routing in verify-work; OMIT for legacy prose-only SUMMARYs. When coverage is
#   uncertain, default human_judgment: true with a rationale — never auto-skip the human.
duration: Xmin
completed: YYYY-MM-DD
status: complete
---

**Status (#2830):** `status: complete` is the default — the plan finished. Use `status: halted` instead when the plan reached a designed stop (a gate failure, a spike concluding without expanding into the full build, or any other intentional non-completion) and intentionally left tasks unfinished.

# Phase [X]: [Name] Summary

**[Substantive one-liner describing outcome]**

## Performance
- **Duration:** [time]
- **Tasks:** [count completed]
- **Files modified:** [count]

## Accomplishments
- [Key outcome 1]
- [Key outcome 2]

## Task Commits
1. **Task 1: [task name]** - `hash`
2. **Task 2: [task name]** - `hash`
3. **Task 3: [task name]** - `hash`

## Files Created/Modified
- `path/to/file.ts` - What it does
- `path/to/another.ts` - What it does

## Decisions & Deviations
[Key decisions or "None - followed plan as specified"]
[Minor deviations if any, or "None"]

## Next Phase Readiness
[What's ready for next phase]


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
