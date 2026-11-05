# Verification Report Template

Template for `.planning/phases/XX-name/{phase_num}-VERIFICATION.md` — phase goal verification results.

Load @~/.claude/engineer/references/prohibition-probe.md and apply its **Invocation authority
and judgment reporting** rules with verifier Step 2b. That shared section owns invocation
authority/default precedence, eligibility, evidence limits and per-item accounting.

---

## File Template

```markdown
---
phase: XX-name
verified: YYYY-MM-DDTHH:MM:SSZ
status: passed | gaps_found | human_needed
score: N/M must-haves verified
covered_files: #  — see agents/verifier.md's "Create VERIFICATION.md" step for what belongs here and how to compute it
  - .planning/phases/XX-name/{phase_num}-{plan}-PLAN.md
  - .planning/phases/XX-name/{phase_num}-{plan}-SUMMARY.md
  - src/{changed-file}.cts
revision: "{actual current full Git commit SHA}"
fingerprint: "{written by verification.fingerprint; omit until generated}"
behavior_unverified: 0 # Count of ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths (present + wired, behavior not exercised)
advisory: # Only when present: Step 7 convergence findings, eligible Step 2b judgment prohibitions, or both
  - finding: "unverified-prohibition — human review recommended"
    category: other
    reason: "{original PLAN path}#must_haves.prohibitions[{zero-based index}]; exact literal: {statement}; lifecycle: resolved; tier: judgment; disposition: flagged/unverified/NON-AUTHORITATIVE; intent: {trusted source}; invocation authority: {instruction provenance and scope}; recommended human review: {review}"
    evidence_status: "{actual current source revision, independent review/evidence references and limits; no human acceptance claimed}"
behavior_unverified_items: # Only if behavior_unverified > 0 — the truths above as structured items; emitted regardless of overall status
  - truth: "Observable truth whose state transition or cancellation/cleanup/ordering invariant no test exercises"
    test: "What to trigger"
    expected: "What state must hold afterward"
    why_human: "Why presence checks can't see it"
coincidental_reliance_items: # Only if a ✓ VERIFIED truth holds incidentally — emitted regardless of overall status (survives gaps_found)
  - truth: "Observable truth that holds incidentally"
    reason: undeclared-precondition | incidental-ordering | fixture-only
    harden: "Precondition/ordering to declare or enforce"
---

# Phase {X}: {Name} Verification Report

**Phase Goal:** {goal from ROADMAP.md}
**Verified:** {timestamp}
**Status:** {passed | gaps_found | human_needed}
**Completion disclosure:** {If completion justified and flags remain: complete with N flagged prohibitions; otherwise blocking status and flagged count}

## Unverified Prohibitions

**Flagged prohibitions:** {N; state 0 if none}. **Accounting:** {original = projected + dropped; account for each original item}.
For each flagged item retain its original PLAN path/zero-based array position, exact
literal, lifecycle/tier, flagged/unverified/NON-AUTHORITATIVE disposition, sourced intent,
current source/review evidence and limits, invocation-authority provenance/scope, and
recommended human review. Identify eligible advisory, required human item or gap routing.
Judgment remains unverified, never green/VERIFIED or completed human acceptance.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | {truth from must_haves} | ✓ VERIFIED | {what confirmed it} |
| 2 | {truth from must_haves} | ✗ FAILED | {what's wrong} |
| 3 | {truth from must_haves} | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | {present + wired; transition/invariant not exercised by a test — see Human Verification} |
| 4 | {truth from must_haves} | ✓ VERIFIED (coincidental-reliance) | {holds, but incidentally — see coincidental_reliance_items} |
| 5 | {truth from must_haves} | ? UNCERTAIN | {why can't verify} |

**Score:** {N}/{M} truths verified ({P} present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/components/Chat.tsx` | Message list component | ✓ EXISTS + SUBSTANTIVE | Exports ChatList, renders Message[], no stubs |
| `src/app/api/chat/route.ts` | Message CRUD | ✗ STUB | File exists but POST returns placeholder |
| `prisma/schema.prisma` | Message model | ✓ EXISTS + SUBSTANTIVE | Model defined with all fields |

**Artifacts:** {N}/{M} verified

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| Chat.tsx | /api/chat | fetch in useEffect | ✓ WIRED | Line 23: `fetch('/api/chat')` with response handling |
| ChatInput | /api/chat POST | onSubmit handler | ✗ NOT WIRED | onSubmit only calls console.log |
| /api/chat POST | database | prisma.message.create | ✗ NOT WIRED | Returns hardcoded response, no DB call |

**Wiring:** {N}/{M} connections verified

## Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| {REQ-01}: {description} | ✓ SATISFIED | - |
| {REQ-02}: {description} | ✗ BLOCKED | API route is stub |
| {REQ-03}: {description} | ? NEEDS HUMAN | Can't verify WebSocket programmatically |

**Coverage:** {N}/{M} requirements satisfied

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| src/app/api/chat/route.ts | 12 | `// TODO: implement` | ⚠️ Warning | Indicates incomplete |
| src/components/Chat.tsx | 45 | `return <div>Placeholder</div>` | 🛑 Blocker | Renders no content |
| src/hooks/useChat.ts | - | File missing | 🛑 Blocker | Expected hook doesn't exist |

**Anti-patterns:** {N} found ({blockers} blockers, {warnings} warnings)

## Human Verification Required

{If no human verification needed:}
No required human verification identified. Any eligible judgment advisories remain
explicitly unverified in Unverified Prohibitions; automated gaps are reported separately.

{If human verification needed:}

### 1. {Test Name}
**Test:** {What to do}
**Expected:** {What should happen}
**Why human:** {Why can't verify programmatically}

### 2. {Test Name}
**Test:** {What to do}
**Expected:** {What should happen}
**Why human:** {Why can't verify programmatically}

## Gaps Summary

{If no gaps:}
**No gaps found.** {If no required human items: actual source/phase goal achieved. If flags
remain: complete with N flagged prohibitions — see Unverified Prohibitions. If required
human items remain: human_needed; source completion is not yet established.}

{If gaps found:}

### Critical Gaps (Block Progress)

1. **{Gap name}**
   - Missing: {what's missing}
   - Impact: {why this blocks the goal}
   - Fix: {what needs to happen}

2. **{Gap name}**
   - Missing: {what's missing}
   - Impact: {why this blocks the goal}
   - Fix: {what needs to happen}

### Non-Critical Gaps (Can Defer)

1. **{Gap name}**
   - Issue: {what's wrong}
   - Impact: {limited impact because...}
   - Recommendation: {fix now or defer}

## Recommended Fix Plans

{If gaps found, generate fix plan recommendations:}

### {phase}-{next}-PLAN.md: {Fix Name}

**Objective:** {What this fixes}

**Tasks:**
1. {Task to fix gap 1}
2. {Task to fix gap 2}
3. {Verification task}

**Estimated scope:** {Small / Medium}

---

### {phase}-{next+1}-PLAN.md: {Fix Name}

**Objective:** {What this fixes}

**Tasks:**
1. {Task}
2. {Task}

**Estimated scope:** {Small / Medium}

---

## Verification Metadata

**Verification approach:** Goal-backward (derived from phase goal)
**Must-haves source:** {PLAN.md frontmatter | derived from ROADMAP.md goal}
**Automated checks:** {N} passed, {M} failed
**Human checks required:** {N}
**Flagged prohibitions:** {N; separate from verified truths and required human checks}
**Total verification time:** {duration}

---
*Verified: {timestamp}*
*Verifier: Claude (subagent)*
```

---

## Guidelines

**Native fingerprint and revision:** First write a valid report with the truthful
`passed`, `gaps_found` or `human_needed` status and actual observations. For
`passed`, include the actual nonempty `covered_files` and current full Git
`revision`. Omit the example `fingerprint` field until the runtime generates it;
do not invent a digest. After the report evidence and structural decision check
are complete, populate `COVERED_FILES` with the actual covered paths described in
`agents/verifier.md` and fingerprint the existing report:

```bash
FINGERPRINT_ARGS=()
for file in "${COVERED_FILES[@]}"; do
  FINGERPRINT_ARGS+=(--files "$file")
done
engineer_run query verification.fingerprint "${PHASE_DIR}" "${FINGERPRINT_ARGS[@]}"
```

Repeated `--files` arguments preserve paths containing spaces. The native command
writes `fingerprint` (a SHA-256 hex string), `covered_files` (the explicit file
arguments) and `revision` (the captured Git HEAD) into the existing report while
preserving its status and observations. It returns only `fingerprint` and `path`;
read back and retain the written metadata. Do not substitute `covered_digest`
or a manually computed digest, and do not change unresolved findings to `passed`.

**Status values (overall, frontmatter `status:`):**
- `passed` — Actual source/phase goal verified, no blockers or genuine outstanding human/evidence obligations; eligible judgment advisories remain individually flagged/unverified
- `gaps_found` — One or more critical gaps found
- `human_needed` — Automated checks pass but human verification required

**Prohibition routing and disclosure:** Only the shared reference's eligible resolved
judgment items may use the existing `advisory:` mapping/text fields shown above. No new
top-level key, PLAN provenance field or status value is needed. Emit each item and its
count prominently in **Unverified Prohibitions** even alongside `passed`; do not score it
as VERIFIED, green or human-accepted. Preserve original literals, positions, tiers and
descriptor-less fallback projections with no auto-dismissal or silent drop. Read current
goal/requirements, locked/trusted decisions and checkpoints; missing manual-test wording
alone is insufficient. Unknown provenance/intent/authority, required-human ambiguity or
actual present human obligations cannot be advisory-routed. Behavior-unverified and
unconfirmed backstop/`insufficient_spec` remain human items, including infrastructure.
Failed truth/artifact/link/security/test-quality/evidence checks remain gaps. Test-tier
missing/failing/unprovable enforcement is `gaps_found` in both modes, never advisory.

Step 7 convergence findings keep their distinct re-verification-only scope/evidence rules;
use their existing mapping and **Advisory (New Scope, Unevidenced)** section separately.
Whenever completion with flags is justified, the report headline/return, SUMMARY and
delivery disclosure must literally include **“complete with N flagged prohibitions”**
with actual count and per-item references. A bare “complete” or “Verified” headline must
not hide flags. For blocked results report status/count without claiming completion.
Source-passed does not qualify production, complete pending UAT or approve future scans
or operations. Preserve old reports/history and obtain fresh evidence/fingerprint rather
than relabeling status. Existing review, currentness, checks, CI and merge authority apply.

**Per-truth states (Observable Truths `Status` column):**
- `✓ VERIFIED` — supporting artifacts pass all checks; for a behavior-dependent truth, a behavioral test exercised the asserted behavior
- `⚠️ PRESENT_BEHAVIOR_UNVERIFIED` — present + wired, but a state transition or cancellation/cleanup/ordering invariant was not exercised by any test. Counts toward `behavior_unverified`, routes to human verification, and is *excluded* from the verified score. Per-truth only — on its own the overall `status:` becomes `human_needed` (unless a higher-precedence `gaps_found` also applies); the item is preserved in `behavior_unverified_items` regardless.
- `✓ VERIFIED (coincidental-reliance)` — an **advisory** qualifier on a truth that *is* verified but holds for an incidental reason rather than a guaranteed one: `undeclared-precondition` (state nothing in the phase's artifacts or a declared prerequisite guarantees), `incidental-ordering` (an order or side effect nothing in the code enforces), or `fixture-only` (the test's own setup establishes the precondition; the production path has no equivalent). The base `✓ VERIFIED` token is kept verbatim and leading, so it counts toward the verified score exactly as before — the advisory changes no score and no status, and never produces a human-verification item. Each flagged truth is listed in `coincidental_reliance_items` with the reason and what to harden. Not applied to a truth that never reached `✓ VERIFIED`, nor to a `PASSED (override)` truth.

  **Filling this column — apply the reliance check to every `✓ VERIFIED` truth before writing the row.** Ask why the truth holds and classify the evidence you already recorded, not your confidence in it. Flag it when the evidence names one of the three reasons above. Do NOT flag: a precondition the code establishes or explicitly defaults; ordering the code enforces (await, explicit sequencing); a fixture merely supplying input the real caller also supplies; unease naming no specific state, ordering, or fixture. The check is endogenous and so weaker than an exogenous tag (`engineer/references/honest-verifier.md`) — which is why it is advisory and never a gate. The usual fix is to promote the hidden assumption into a declared precondition.
- `✗ FAILED` — artifact missing, stub, or unwired
- `? UNCERTAIN` — can't verify programmatically

**Evidence types:**
- For EXISTS: "File at path, exports X"
- For SUBSTANTIVE: "N lines, has patterns X, Y, Z"
- For WIRED: "Line N: code that connects A to B"
- For FAILED: "Missing because X" or "Stub because Y"

**Severity levels:**
- 🛑 Blocker: Prevents goal achievement, must fix
- ⚠️ Warning: Indicates incomplete but doesn't block
- ℹ️ Info: Notable but not problematic

**Fix plan generation:**
- Only generate if gaps_found
- Group related fixes into single plans
- Keep to 2-3 tasks per plan
- Include verification task in each plan

---

## Example

The chat example below illustrates `gaps_found`. For prohibition routing, apply these
additional cases (illustrative outcomes, not evidence about any current project):

- **Eligible advisory:** a resolved judgment against manipulative reminder framing has a
  sourced intent, explicit unattended invocation authority, current independent source/copy
  review and no required present human acceptance. Store its original PLAN position/literal,
  scope and evidence limits in the shown advisory fields. With all actual truths/checks
  verified and no real human/evidence gap, overall `passed` may coexist with
  **complete with 1 flagged prohibitions**; the judgment is still NON-AUTHORITATIVE/unverified.
- **Human hold:** the same item with only saved interactive defaults, ambiguous provenance,
  or a locked decision requiring present owner copy acceptance yields `human_needed`.
  One eligible advisory plus one required human item also yields `human_needed`.
- **Evidence hold:** either case plus a failed truth, security/test-quality blocker or
  unresolved evidence gap yields `gaps_found`. A test-tier prohibition with absent descriptor,
  unproven violation RED or vacuous clean GREEN remains `gaps_found` even with unattended
  authority. Behavior-unverified/backstop abstention stays a human item, never this advisory.
- **Accounting failure:** dropping/rewording the literal or losing its original PLAN
  association/flag/count is not an eligible completion. A fixture pass never proves a broad
  judgment or human acceptance. See the shared reference's exact two-prohibition dashboard
  example for `2 original = 2 projected + 0 dropped` and the separate future scan guard.

```markdown
---
phase: 03-chat
verified: 2025-01-15T14:30:00Z
status: gaps_found
score: 2/5 must-haves verified
---

# Phase 3: Chat Interface Verification Report

**Phase Goal:** Working chat interface where users can send and receive messages
**Verified:** 2025-01-15T14:30:00Z
**Status:** gaps_found

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can see existing messages | ✗ FAILED | Component renders placeholder, not message data |
| 2 | User can type a message | ✓ VERIFIED | Input field exists with onChange handler |
| 3 | User can send a message | ✗ FAILED | onSubmit handler is console.log only |
| 4 | Sent message appears in list | ✗ FAILED | No state update after send |
| 5 | Messages persist across refresh | ? UNCERTAIN | Can't verify - send doesn't work |

**Score:** 1/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/components/Chat.tsx` | Message list component | ✗ STUB | Returns `<div>Chat will be here</div>` |
| `src/components/ChatInput.tsx` | Message input | ✓ EXISTS + SUBSTANTIVE | Form with input, submit button, handlers |
| `src/app/api/chat/route.ts` | Message CRUD | ✗ STUB | GET returns [], POST returns { ok: true } |
| `prisma/schema.prisma` | Message model | ✓ EXISTS + SUBSTANTIVE | Message model with id, content, userId, createdAt |

**Artifacts:** 2/4 verified

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| Chat.tsx | /api/chat GET | fetch | ✗ NOT WIRED | No fetch call in component |
| ChatInput | /api/chat POST | onSubmit | ✗ NOT WIRED | Handler only logs, doesn't fetch |
| /api/chat GET | database | prisma.message.findMany | ✗ NOT WIRED | Returns hardcoded [] |
| /api/chat POST | database | prisma.message.create | ✗ NOT WIRED | Returns { ok: true }, no DB call |

**Wiring:** 0/4 connections verified

## Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| CHAT-01: User can send message | ✗ BLOCKED | API POST is stub |
| CHAT-02: User can view messages | ✗ BLOCKED | Component is placeholder |
| CHAT-03: Messages persist | ✗ BLOCKED | No database integration |

**Coverage:** 0/3 requirements satisfied

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| src/components/Chat.tsx | 8 | `<div>Chat will be here</div>` | 🛑 Blocker | No actual content |
| src/app/api/chat/route.ts | 5 | `return Response.json([])` | 🛑 Blocker | Hardcoded empty |
| src/app/api/chat/route.ts | 12 | `// TODO: save to database` | ⚠️ Warning | Incomplete |

**Anti-patterns:** 3 found (2 blockers, 1 warning)

## Human Verification Required

None needed until automated gaps are fixed.

## Gaps Summary

### Critical Gaps (Block Progress)

1. **Chat component is placeholder**
   - Missing: Actual message list rendering
   - Impact: Users see "Chat will be here" instead of messages
   - Fix: Implement Chat.tsx to fetch and render messages

2. **API routes are stubs**
   - Missing: Database integration in GET and POST
   - Impact: No data persistence, no real functionality
   - Fix: Wire prisma calls in route handlers

3. **No wiring between frontend and backend**
   - Missing: fetch calls in components
   - Impact: Even if API worked, UI wouldn't call it
   - Fix: Add useEffect fetch in Chat, onSubmit fetch in ChatInput

## Recommended Fix Plans

### 03-04-PLAN.md: Implement Chat API

**Objective:** Wire API routes to database

**Tasks:**
1. Implement GET /api/chat with prisma.message.findMany
2. Implement POST /api/chat with prisma.message.create
3. Verify: API returns real data, POST creates records

**Estimated scope:** Small

---

### 03-05-PLAN.md: Implement Chat UI

**Objective:** Wire Chat component to API

**Tasks:**
1. Implement Chat.tsx with useEffect fetch and message rendering
2. Wire ChatInput onSubmit to POST /api/chat
3. Verify: Messages display, new messages appear after send

**Estimated scope:** Small

---

## Verification Metadata

**Verification approach:** Goal-backward (derived from phase goal)
**Must-haves source:** 03-01-PLAN.md frontmatter
**Automated checks:** 2 passed, 8 failed
**Human checks required:** 0 (blocked by automated failures)
**Total verification time:** 2 min

---
*Verified: 2025-01-15T14:30:00Z*
*Verifier: Claude (subagent)*
```
