# Summary Template

Template for `.planning/phases/XX-name/{phase}-{plan}-SUMMARY.md` - phase completion documentation.

---

Required current-record metadata: `phase`, `plan`, `status`, `requirements-completed`, `acceptance`, `documentation`, `issue_refs`.

## File Template

```markdown
---
phase: XX-name
plan: YY
subsystem: "[primary category: auth, payments, ui, api, database, infra, testing, etc.]"
tags: ["searchable tech: jwt, stripe, react, postgres, prisma"]

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

requirements-completed: [] # REQUIRED — include only IDs the delivered changes and evidence actually complete.

acceptance: []
documentation: []
issue_refs: []

# Optional runtime-owned observations of checks actually executed for this plan.
# Replace [] only with actual observations; use [] when no check was run.
checks_run: []

# Coverage metadata — one entry per shipped deliverable. Drives DETERMINISTIC UAT routing in verify-work.
# Current summaries preserve this complete block. Legacy prose may inform review but cannot pass required acceptance.
# See <coverage_guidance> for coordinator/verifier classification.
coverage:
  - id: D1
    description: "[deliverable in human-readable form — what would have been a prose ## Accomplishments bullet]"
    requirement: "[REQ-ID from this plan's `requirements`, or omit if none]"
    verification:
      - kind: unit # unit | integration | e2e | automated_ui
        ref: "[exact receipt path returned by verification.run-checks]"
        status: passed # actual receipt result; only passed can qualify for automatic coverage
        revision: "[optional full tested SHA; if supplied it must match the receipt]"
    human_judgment: false # Set false only with actual current passing native receipt evidence; otherwise true with rationale. It never waives required UAT.
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

| Tested revision | Command argv | Observed result | Evidence |
|-----------------|--------------|-----------------|----------|
| [SHA] | [exact argv] | [pass / fail / not run] | [receipt or output path] |

`checks_run` is optional metadata accepted by the current runtime. Each entry records only a check that was actually executed: `command` is either its exact argv list or exact observed command text, `status` is the observed status (`passed` for a passing entry), and `revision` is the actual tested commit SHA. Use `checks_run: []` when no check ran. Planned checks, unexecuted commands, inferred success, or a revision other than the one tested must not appear as executed evidence. The Markdown table remains the human-readable record and may include failures or not-run obligations; it does not replace the full runtime receipt when one exists. TDD Evidence: record the RED failure, GREEN pass and commit ancestry; missing evidence remains a gap.

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

## Threat Flags

[Newly discovered surfaces only; omit this section when none were found. These flags do not replace the owning PLAN register.]

| Flag | File | Description |
|------|------|-------------|
| [threat_flag: category] | [exact file] | [new boundary/surface and impact] |

## Threat Outcomes

| PLAN / Threat ID | Canonical issue | Outcome | Git state | Evidence |
|------------------|-----------------|---------|-----------|----------|
| [exact PLAN / stable ID] | [verified canonical URL or Pending reason] | [unresolved / mitigated / accepted / deferred, with remaining exposure] | [actual owned commit/integration state] | [tested revision and actual check result or Pending] |

Follow [canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking); do not silently drop open threats. Keep mitigation details and remaining exposure in the outcome/evidence cells; do not duplicate the six-column PLAN register here.

For every planned threat, preserve the stable PLAN threat ID and record the canonical issue URL (or the exact Pending reason), final outcome and remaining exposure. Outcomes are `unresolved`, `mitigated`, `accepted`, or `deferred`; `resolved` is not a threat disposition. A closed issue is not proof by itself: read the canonical issue back and reconcile its current state, discussion and closure evidence with the committed implementation and actual checks. Record the actual owned commit/integration state and tested revision with the relevant evidence. `accepted` and `deferred` remain distinct decisions with their authority and rationale; do not describe a deferred risk as resolved or a closed tracker as proof of mitigation.

## Next Phase Readiness

[What's ready for next phase]
[Any blockers or concerns]

---

_Phase: XX-name_
_Completed: [date]_
```

<frontmatter_guidance>
**Purpose:** Enable automatic context assembly via dependency graph. Frontmatter makes summary metadata machine-readable so plan-phase can scan all summaries quickly and select relevant ones based on dependencies.

**Fast scanning:** Frontmatter is first ~25 lines, cheap to scan across all summaries without reading full content.

**Dependency graph:** `requires`/`provides`/`affects` create explicit links between phases, enabling transitive closure for context selection.

**Subsystem:** Primary categorization (auth, payments, ui, api, database, infra, testing) for detecting related phases.

**Tags:** Searchable technical keywords (libraries, frameworks, tools) for tech stack awareness.

**Key-files:** Important files for @context references in PLAN.md.

**Patterns:** Established conventions future phases should maintain.

**Population:** Frontmatter is populated during summary creation in agents/executor.md. See `<summary_creation>` for field-by-field guidance.

**Status:** `status: complete` is the default — the plan finished. Use `status: halted` instead when the plan reached a designed stop (a gate failure, a spike concluding without expanding into the full build, or any other intentional non-completion) and intentionally left tasks unfinished. `halted` is machine-read: any plan whose `depends_on` (directly or transitively) names a halted plan is reported as blocked, not offered to the executor, until the halt is resolved and re-summarized as `complete`.
</frontmatter_guidance>

<coverage_guidance>
**Purpose:** The `coverage:` block is a per-deliverable Requirements Traceability Matrix. It lets `verify-work`'s `extract_tests` step route deliverables DETERMINISTICALLY — classifying outcomes with valid non-empty automated evidence while preserving all required human acceptance — instead of re-deriving coverage from prose. Consumed via `engineer_run query uat.classify-coverage SUMMARY_PATH`.

**Field semantics:**

| Field                   | Purpose                                                                                                                 |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `id`                    | Stable identifier (`D1`, `D2`…) for cross-referencing from UAT.md and audit reports. Must be unique within the SUMMARY. |
| `description`           | The deliverable in human-readable form — what would have been a prose bullet.                                           |
| `requirement`           | Links back to a REQUIREMENTS.md REQ-ID (joins `requirements-completed`). Optional.                                      |
| `verification[].kind`   | Native enum: `unit \| integration \| e2e \| automated_ui`. Manual observations do not qualify as automated evidence. |
| `verification[].ref`    | Exact receipt path returned by `engineer_run query verification.run-checks`; required per entry. A test path, screenshot or command string is not a native receipt. |
| `verification[].status` | `passed` for an actually passing native receipt; any other or missing result remains unverified. |
| `verification[].revision` | Optional full SHA of the revision actually tested; when present it must match the receipt's tested revision. |
| `human_judgment`        | Explicit boolean; REQUIRED. `true` routes the outcome to a human; the field is not itself a human decision.            |
| `rationale`             | REQUIRED when `human_judgment: true`. Explain why automation is insufficient or coverage is undetermined.               |

**Deterministic contract (what the classifier does):**

- The runtime binds a receipt's actual `result.name` to exactly one configured check ID, then reads that receipt using the current check fingerprint and current HEAD. The receipt must have matching source/configuration/argv/environment/input/log digests and valid revision ancestry. Use only the actual receipt path returned by `verification.run-checks`; metadata that merely names a test, command or SHA is not proof.
- The coordinator and verifier may classify an automated deliverable only when `human_judgment` is false, verification is non-empty, every entry uses a native automated kind and has `status: passed`, each ref resolves to a valid current native receipt, and any supplied revision matches the receipt's actual tested revision. This never waives separately required human UAT or final acceptance.
- **Everything else is presented to a human or left unverified** — `human_judgment: true`, an empty `verification:`, any non-passing status, missing/unbound/stale receipt, schema error, or unknown coverage. `human_judgment: false` alone is never evidence of automation and never waives required human acceptance.
- **Fail-safe default:** if you cannot determine coverage for a deliverable, set `human_judgment: true` with `rationale: "Coverage not determined at authoring time — verifier must classify"`. Never leave `human_judgment` empty. Metadata-only claims, a test path, a command, or a screenshot must not be substituted for an actual receipt.
- Current SUMMARYs require coverage for every delivered outcome. Empty coverage or missing required metadata remains a classification gap; legacy prose is discovery input only and cannot automatically approve current acceptance.
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

_Phase: 01-foundation_
_Completed: 2025-01-15_

```
</example>

<guidelines>
**Frontmatter:** MANDATORY - complete all fields. Enables automatic context assembly for future planning.

**One-liner:** Must be substantive. "JWT auth with refresh rotation using jose library" not "Authentication implemented".

**Decisions section:**
- Key decisions made during execution with rationale
- Extracted to STATE.md accumulated context
- Use "None - followed plan as specified" if no deviations

**After creation:** only the coordinator reconciles STATE/CONTEXT/ROADMAP through supported runtime operations, including state.update-progress. Workers return proposed updates and Remaining; they do not write shared records.
</guidelines>
```

## Coordinator reconciliation

Workers report delivered changes and Remaining; they do not write shared STATE, ROADMAP, REQUIREMENTS traceability or CONTEXT decisions. The coordinator reconciles those records with supported `engineer_run query` operations. Coverage is mandatory for current summaries: classify each deliverable as automated, human-needed or unverified; automated requires non-empty passing evidence at the assigned revision. Required human UAT remains pending until an actual human accepts. Never turn absent evidence into a pass.
