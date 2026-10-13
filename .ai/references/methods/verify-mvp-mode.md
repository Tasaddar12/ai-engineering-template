# Verify-Work — MVP Mode UAT Framing

When the coordinator assigns verification of an approved user story, the verifier
MUST use the user-flow framing and ordered UAT script below. Without that assignment,
use the normal phase verification procedure. The local runtime has no automatic MVP mode or slash command.
User-flow evidence supplements, and never replaces, other required acceptance.

## Core rule

**Show expected, ask if reality matches.** The human script describes what a
real user opens, fills, clicks and sees, using the canonical template linked below.
AI/maintainer prepares access and data, performs technical checks and keeps their
results in the separate maintainer-owned record.

## When this framing applies

Read the approved story from CONTEXT: "As a [role], I want to [capability], so
that [outcome]." The wording is a helpful structure, not a regex gate. If role,
capability or outcome is missing, report the unresolved scope to the coordinator.
Do not require a nonexistent command or force rewording of an already clear goal.

## Generated UAT script structure under MVP mode

The verification packet has THREE sections, in this exact order. Only section 1
is the human script; sections 2 and 3 belong to the separate maintainer record.
Apply the [canonical UAT authoring contract](../../templates/UAT.md#authoring-contract)
to that script, including the prepared environment and numbered PASS/FAIL/BLOCKED replies.

### 1. User-flow walk-through (always first, always required)

Derive ordered steps from the phase's user-story goal:

1. The first step opens the verified exact URL (full path and required trailing slash) or directly runnable supplied launcher from the canonical template.
2. Each subsequent step names one actual visible screen/control/object, exact click/key and concrete safe input when needed.
3. The final step asserts the user-visible outcome from the `[outcome]` clause of the user story.

Use the canonical template's numbered action and expected-visible-result fields.
The user replies `N PASS`, `N FAIL <short observation>` or `N BLOCKED <reason>`.
A skipped, blocked or unanswered step stays unresolved. Do not proceed to a
dependent step with a broken prerequisite. Mark unavailable functions or
unverified entry points BLOCKED; never invent labels or substitute a guessed route.

If ALL user-flow steps pass, advance to section 2. If a step fails, preserve the failure and stop dependent user actions. Continue independent technical checks when authorized; never hide their results.

### 2. Technical checks (AI/maintainer only)

After the user-flow section, record technical checks for the approved scope:
- API endpoint schema verification (if the phase shipped APIs)
- Error state behavior (4xx, 5xx codes; invalid input handling)
- Edge cases (empty data, large data, concurrent requests if applicable)
- Cross-browser / cross-runtime checks (if applicable)

Run only authorized checks. Independent checks can proceed despite a failed flow; blocked or unrun checks must be labeled honestly.

### 3. Coverage check (AI/maintainer only; always last, always required)

Verify that the user-story `[outcome]` clause is observably true in the codebase:
- If the outcome is "I can access my dashboard", verify a dashboard route exists and renders for an authenticated user.
- If the outcome is "I can bulk-import contacts", verify the import path produces persisted records.

Coverage is a goal-backward check: "did this phase deliver what its user story promised?" — sourced from the local verifier's goal-backward methodology, narrowed to the user story.

## Anti-patterns to reject under MVP mode

- **Lead with technical checks.** "Step 1: GET /api/users/me returns 200." Reject. The user does not see API endpoints. Reorder so a user action comes first.
- **Schema-as-feature.** "User has a `name` field on the User model." Reject. The user does not see database fields. Express the same check as a user-visible outcome ("the user's name appears in the dashboard header").
- **Skip user flow because the test passed.** The unit test passing in CI is not evidence that the user flow works. The user-flow walk-through is mandatory under MVP mode even when all unit tests are green.

## Local UAT contract

The coordinator records actual observations in the canonical UAT session
document through [verify-work](../../workflows/verify-work.md). The runtime has
no UAT result-recording or case-selection verb. Keep PENDING HUMAN acceptance
until the actual human decision is recorded.
Silence, an empty reply, a skipped case or source inspection alone is not a human
pass. Preserve source revision and actual expected/observed results. Required UAT
remains incomplete until every required case passes; no framing auto-passes it.

## Output: VERIFICATION.md changes under MVP mode

The verifier returns a read-only proposed `VERIFICATION.md` report to the
coordinator. Under this framing, it adds a top-level "User Flow Coverage"
section mapping each story step to codebase evidence. This fictional example
shows source coverage only; it is not human acceptance or actual project evidence:

```markdown
## User Flow Coverage

User story: «As a new user, I want to register and log in, so that I can access my dashboard.»

| Step | Expected | Evidence | Status |
|------|----------|----------|--------|
| Register | Form at /register accepts name/email/password | src/app/register/page.tsx:12 (form component) | ✓ |
| Submit | Persists user, redirects to /dashboard | src/api/register/route.ts:34 (db.insert + redirect) | ✓ |
| See dashboard | Dashboard page renders, shows user's name | src/app/dashboard/page.tsx:8 (greeting line) | ✓ |
| Outcome | "Access my dashboard" — user lands on a populated page | dashboard route + greeting both verified above | ✓ |
```

Standard technical-check sections of VERIFICATION.md remain (API verification, error handling, etc.) but are appended below "User Flow Coverage", not above.
