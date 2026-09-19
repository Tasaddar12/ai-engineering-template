# Summary Template

Template for `.planning/phases/XX-name/{phase}-{plan}-SUMMARY.md` - phase completion documentation.

---

## File Template

```markdown
---
phase: XX-name
plan: YY
subsystem: [primary category: auth, payments, ui, api, database, infra, testing, etc.]
tags: [searchable tech: jwt, stripe, react, postgres, prisma]

# Dependency graph
requires:
  - phase: [prior phase this depends on]
    provides: [what that phase built that this uses]
provides:
  - [bullet list of what this phase built/delivered]
affects: [list of phase names or keywords that will need this context]

# Actuals — pairs with the plan's `estimate` to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: [chars/4 over files actually changed]
  tasks: [tasks completed]
  commits: [commits made]

# Tech tracking
tech-stack:
  added: [libraries/tools added in this phase]
  patterns: [architectural/code patterns established]

key-files:
  created: [important files created]
  modified: [important files modified]

key-decisions:
  - "Decision 1"
  - "Decision 2"

patterns-established:
  - "Pattern 1: description"
  - "Pattern 2: description"

requirements-completed: []  # REQUIRED — Include only requirement IDs from this plan's `requirements` that the delivered changes and verification evidence actually complete. Record incomplete, failed, or blocked requirements under remaining gaps; never copy them here merely because they were assigned.

# Local runtime coverage — populate from actual delivered and checked results.
acceptance: []  # REQUIRED — Covered acceptance IDs from this plan; these may differ from requirement IDs.
documentation: []  # REQUIRED — Exact required documentation paths completed by this component; [] when none are assigned.

# Coverage metadata — one entry per shipped deliverable for evidence review and UAT planning.
# For legacy/prose-only SUMMARYs, inspect the ## Accomplishments evidence instead.
# See <coverage_guidance> for interpretation; the local runtime does not auto-approve UAT from this block.
coverage:
  - id: D1
    description: "[deliverable in human-readable form — what would have been a prose ## Accomplishments bullet]"
    requirement: "[REQ-ID from this plan's `requirements`, or omit if none]"
    verification:
      - kind: unit            # unit | integration | e2e | automated_ui | manual_procedural | other
        ref: "[tests/path.test.ts#test name | playwright:shot.png | command invocation]"
        status: pass          # pass | fail | unknown — from the latest run
    human_judgment: false     # REQUIRED boolean. Auto-pass requires nonempty verification with every status pass; required human UAT is never waived.
  - id: D2
    description: "[a deliverable that needs a human to sign off]"
    verification: []
    human_judgment: true
    rationale: "[REQUIRED when human_judgment: true — why automation is insufficient]"

# Metrics
duration: Xmin
completed: YYYY-MM-DD
status: complete
---

# Phase [X]: [Name] Summary

**[Substantive one-liner describing outcome - NOT "phase complete" or "implementation finished"]**

## Performance

- **Duration:** [time] (e.g., 23 min, 1h 15m)
- **Started:** [ISO timestamp]
- **Completed:** [ISO timestamp]
- **Tasks:** [count completed]
- **Files modified:** [count]

## Accomplishments
- [Most important outcome]
- [Second key accomplishment]
- [Third if applicable]

## Task Commits

Each task was committed atomically:

1. **Task 1: [task name]** - `abc123f` (feat/fix/test/refactor)
2. **Task 2: [task name]** - `def456g` (feat/fix/test/refactor)
3. **Task 3: [task name]** - `hij789k` (feat/fix/test/refactor)

**Plan metadata:** `lmn012o` (docs: complete plan)

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## Checks

- **Tested revision:** [Tested revision or commit]
- **Command and scenario:** [Command and scenario]
- **Result:** [Observed result, including failures or skips]

[Repeat for each actual check. Explain remaining gaps; do not claim unrun checks passed.
For a TDD plan, also add a TDD Evidence section with the contract's RED/GREEN/REFACTOR evidence.]

## Files Created/Modified
- `path/to/file.ts` - What it does
- `path/to/another.ts` - What it does

## Decisions Made
[Key decisions with brief rationale, or "None - followed plan as specified"]

## Deviations from Plan

[If no deviations: "None - plan executed exactly as written"]

[If deviations occurred:]

### Auto-fixed Issues

**1. [Rule X - Category] Brief description**
- **Found during:** Task [N] ([task name])
- **Issue:** [What was wrong]
- **Fix:** [What was done]
- **Files modified:** [file paths]
- **Verification:** [How it was verified]
- **Committed in:** [hash] (part of task commit)

[... repeat for each auto-fix ...]

---

**Total deviations:** [N] auto-fixed ([breakdown by rule])
**Impact on plan:** [Brief assessment - e.g., "All auto-fixes necessary for correctness/security. No scope creep."]

## Issues Encountered
[Problems and how they were resolved, or "None"]

[Note: "Deviations from Plan" documents unplanned work that was handled automatically via deviation rules. "Issues Encountered" documents problems during planned work that required problem-solving.]

## User Setup Required

[If USER-SETUP.md was generated:]
**External services require manual configuration.** See [{phase}-USER-SETUP.md](./{phase}-USER-SETUP.md) for:
- Environment variables to add
- Dashboard configuration steps
- Verification commands

[If no USER-SETUP.md:]
None - no external service configuration required.

## Next Phase Readiness
[What's ready for next phase]
[Any blockers or concerns]

---
*Phase: XX-name*
*Completed: [date]*
```

<frontmatter_guidance>
**Purpose:** Enable automatic context assembly via dependency graph. Frontmatter makes summary metadata machine-readable so plan-phase can scan all summaries quickly and select relevant ones based on dependencies.

**Fast scanning:** Frontmatter is first ~25 lines, cheap to scan across all summaries without reading full content.

**Dependency graph:** `requires`/`provides`/`affects` create explicit links between phases, enabling transitive closure for context selection.

**Subsystem:** Primary categorization (auth, payments, ui, api, database, infra, testing) for detecting related phases.

**Tags:** Searchable technical keywords (libraries, frameworks, tools) for tech stack awareness.

**Key-files:** Important files for @context references in PLAN.md.

**Patterns:** Established conventions future phases should maintain.

**Population:** Populate frontmatter during the [coder method](../agents/coder.md) summary step using the [local contract](../runtime/TEMPLATE-CONTRACT.md).

**Status:** `status: complete` is the default — the plan finished. Use `status: halted` instead when the plan reached a designed stop (a gate failure, a spike concluding without expanding into the full build, or any other intentional non-completion) and intentionally left tasks unfinished. `halted` is machine-read: any plan whose `depends_on` (directly or transitively) names a halted plan is reported as blocked, not offered to the executor, until the halt is resolved and re-summarized as `complete`.
</frontmatter_guidance>

<coverage_guidance>
**Purpose:** The `coverage:` block records each deliverable, related requirement and observed verification evidence. The coordinator and verifier MUST apply the deterministic classification below when assessing acceptance and preparing UAT. They record each classification and its evidence in VERIFICATION. The local runtime does not implement a coverage-classification command; this mandatory review procedure supplies the classification and never invents human observations.

**Field semantics:**

| Field | Purpose |
|---|---|
| `id` | Stable identifier (`D1`, `D2`…) for cross-referencing from UAT.md and audit reports. Must be unique within the SUMMARY. |
| `description` | The deliverable in human-readable form — what would have been a prose bullet. |
| `requirement` | Links back to a REQUIREMENTS.md REQ-ID (joins `requirements-completed`). Optional. |
| `verification[].kind` | Enum: `unit \| integration \| e2e \| automated_ui \| manual_procedural \| other`. |
| `verification[].ref` | Test path + descriptor (`file#test name`), Playwright screenshot ref, or command invocation. Required per entry. |
| `verification[].status` | `pass \| fail \| unknown` — populated from the latest test run. |
| `human_judgment` | Explicit boolean; REQUIRED. `true` always routes to a human. |
| `rationale` | REQUIRED when `human_judgment: true`. The audit trail for why automation is insufficient. |

**Deterministic classification contract (coordinator/verifier MUST apply):**
- A deliverable requires automated evidence to auto-pass (no human prompt). Auto-pass **only** when `human_judgment: false` AND `verification` is non-empty AND every `verification[].status` is `pass`. Inspect each entry's `ref` and actual result at the reviewed revision; a declared pass without evidence is not a pass. Required human UAT remains pending even when automated checks pass.
- **Everything else is presented to a human** — `human_judgment: true`, empty `verification`, any non-`pass`/`unknown` status, missing evidence, or any schema error. Record the exact failed condition and retain the deliverable as pending or failed. A human response does not waive a required automated check or turn its failure into success.
- **Fail-safe default:** if coverage cannot be determined, set `human_judgment: true` and `rationale: "Coverage not determined at authoring time — verifier must classify"`. Never omit `human_judgment` or set it `false` to skip a prompt. Auto-pass additionally requires a nonempty `verification` list whose entries all have passing evidence; the flag alone never bypasses the human.
- `coverage: []` means **"no deliverables to classify"**: ask for one confirmation that no deliverables require classification. If Accomplishments or the implemented work lists a deliverable, report the empty list as a coverage defect and require its entry before completion. OMITTING `coverage` means **legacy**: the coordinator/verifier extracts each deliverable from `## Accomplishments`, matches actual Checks evidence, and applies the same classification. Neither path waives phase acceptance or required UAT.
</coverage_guidance>

<one_liner_rules>
The one-liner MUST be substantive:

**Good:**
- "JWT auth with refresh rotation using jose library"
- "Prisma schema with User, Session, and Product models"
- "Dashboard with real-time metrics via Server-Sent Events"

**Bad:**
- "Phase complete"
- "Authentication implemented"
- "Foundation finished"
- "All tasks done"

The one-liner should tell someone what actually shipped.
</one_liner_rules>

<example>
```markdown
# Phase 1: Foundation Summary

**JWT auth with refresh rotation using jose library, Prisma User model, and protected API middleware**

## Performance

- **Duration:** 28 min
- **Started:** 2025-01-15T14:22:10Z
- **Completed:** 2025-01-15T14:50:33Z
- **Tasks:** 5
- **Files modified:** 8

## Accomplishments
- User model with email/password auth
- Login/logout endpoints with httpOnly JWT cookies
- Protected route middleware checking token validity
- Refresh token rotation on each request

## Files Created/Modified
- `prisma/schema.prisma` - User and Session models
- `src/app/api/auth/login/route.ts` - Login endpoint
- `src/app/api/auth/logout/route.ts` - Logout endpoint
- `src/middleware.ts` - Protected route checks
- `src/lib/auth.ts` - JWT helpers using jose

## Decisions Made
- Used jose instead of jsonwebtoken (ESM-native, Edge-compatible)
- 15-min access tokens with 7-day refresh tokens
- Storing refresh tokens in database for revocation capability

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added password hashing with bcrypt**
- **Found during:** Task 2 (Login endpoint implementation)
- **Issue:** Plan didn't specify password hashing - storing plaintext would be critical security flaw
- **Fix:** Added bcrypt hashing on registration, comparison on login with salt rounds 10
- **Files modified:** src/app/api/auth/login/route.ts, src/lib/auth.ts
- **Verification:** Password hash test passes, plaintext never stored
- **Committed in:** abc123f (Task 2 commit)

**2. [Rule 3 - Blocking] Installed missing jose dependency**
- **Found during:** Task 4 (JWT token generation)
- **Issue:** jose package not in package.json, import failing
- **Fix:** Ran `npm install jose`
- **Files modified:** package.json, package-lock.json
- **Verification:** Import succeeds, build passes
- **Committed in:** def456g (Task 4 commit)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 blocking)
**Impact on plan:** Both auto-fixes essential for security and functionality. No scope creep.

## Issues Encountered
- jsonwebtoken CommonJS import failed in Edge runtime - switched to jose (planned library change, worked as expected)

## Next Phase Readiness
- Auth foundation complete, ready for feature development
- User registration endpoint needed before public launch

---
*Phase: 01-foundation*
*Completed: 2025-01-15*
```
</example>

<guidelines>
**Frontmatter:** MANDATORY - complete all fields. Enables automatic context assembly for future planning.

**One-liner:** Must be substantive. "JWT auth with refresh rotation using jose library" not "Authentication implemented".

**Decisions section:**
- Key decisions made during execution with rationale
- Extracted to STATE.md accumulated context
- Use "None - followed plan as specified" if no deviations

**After creation:** the agent MUST return position, decisions and issues in its
committed SUMMARY. The orchestrator MUST update STATE.md's current position,
progress, accumulated decisions, blockers and session continuity from the
integrated results, before dispatching the next dependent agent. Only the
orchestrator edits those shared records. Update CONTEXT for consequential
decisions and ROADMAP/REQUIREMENTS for verified progress; retain pending and
failed items. `phase.py query state.update-progress` refreshes only
the marked Runtime Status block and does not perform these authored updates.
</guidelines>


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
