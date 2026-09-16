# Verify-Work — MVP Mode UAT Framing

Use this optional framing when the coordinator assigns verification of an
approved user story. The local runtime has no automatic MVP mode or slash command.
User-flow evidence supplements, and never replaces, other required acceptance.

## Core rule

**Show expected, ask if reality matches.** Describe the user-visible outcome:

- **Standard verify-work:** "The API endpoint at /users/register returns 201 with the new user's ID." → user confirms.
- **MVP verify-work:** "Open the registration page. Fill in 'name', 'email', 'password'. Click Submit. You should see your dashboard with your name in the header." → user confirms.

The user-flow form mirrors what a real user does: open, fill, click, see. No HTTP verbs, no JSON shapes, no error codes.

## When this framing applies

Read the approved story from CONTEXT: "As a [role], I want to [capability], so
that [outcome]." The wording is a helpful structure, not a regex gate. If role,
capability or outcome is missing, report the unresolved scope to the coordinator.
Do not require a nonexistent command or force rewording of an already clear goal.

## Generated UAT script structure under MVP mode

The proposed UAT script has THREE sections, in this exact order:

### 1. User-flow walk-through (always first, always required)

Derive ordered steps from the phase's user-story goal:

1. The first step opens the entry point ("Open the app", "Navigate to /register", "Run the product's CLI command").
2. Each subsequent step is one user action: fill, click, type, observe.
3. The final step asserts the user-visible outcome from the `[outcome]` clause of the user story.

Format each step as: "**Step N: [action]** — Expected: [what the user should see]". The user responds with one of:
- an explicit report of the observed expected result → step passes
- a reported mismatch → issue; a skipped, blocked or unanswered step remains unresolved. Do not proceed to a dependent step with a broken prerequisite.

If ALL user-flow steps pass, advance to section 2. If a step fails, preserve the failure and stop dependent user actions. Continue independent technical checks when authorized; never hide their results.

### 2. Technical checks

After the user-flow section, record technical checks for the approved scope:
- API endpoint schema verification (if the phase shipped APIs)
- Error state behavior (4xx, 5xx codes; invalid input handling)
- Edge cases (empty data, large data, concurrent requests if applicable)
- Cross-browser / cross-runtime checks (if applicable)

Run only authorized checks. Independent checks can proceed despite a failed flow; blocked or unrun checks must be labeled honestly.

### 3. Coverage check (always last, always required)

Verify that the user-story `[outcome]` clause is observably true in the codebase:
- If the outcome is "I can access my dashboard", verify a dashboard route exists and renders for an authenticated user.
- If the outcome is "I can bulk-import contacts", verify the import path produces persisted records.

Coverage is a goal-backward check: "did this phase deliver what its user story promised?" — sourced from the local verifier's goal-backward methodology, narrowed to the user story.

## Anti-patterns to reject under MVP mode

- **Lead with technical checks.** "Step 1: GET /api/users/me returns 200." Reject. The user does not see API endpoints. Reorder so a user action comes first.
- **Schema-as-feature.** "User has a `name` field on the User model." Reject. The user does not see database fields. Express the same check as a user-visible outcome ("the user's name appears in the dashboard header").
- **Skip user flow because the test passed.** The unit test passing in CI is not evidence that the user flow works. The user-flow walk-through is mandatory under MVP mode even when all unit tests are green.

## Local UAT contract

The coordinator records actual observations through the local phase UAT procedure.
Silence, an empty reply, a skipped case or source inspection alone is not a human
pass. Preserve source revision and actual expected/observed results. Required UAT
remains incomplete until every required case passes; no framing auto-passes it.

## Output: VERIFICATION.md changes under MVP mode

The verifier produces `VERIFICATION.md`. Under MVP mode, the report adds a top-level "User Flow Coverage" section that maps each step of the user story to evidence in the codebase:

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
