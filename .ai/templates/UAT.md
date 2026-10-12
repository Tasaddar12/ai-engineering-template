# UAT Template

Template for `.planning/phases/XX-name/{phase_num}-UAT.md` — persistent UAT session tracking.

**Producer:** Coordinator or assigned author; the verifier returns a proposed script read-only.
**Consumers:** Human reviewer for actions/results; coordinator for durable session tracking.

## Authoring contract

- Copy only the File Template block. Fill the visible bracket placeholders with
  the indicated content and length; remove unused rows/fields and prompts before
  delivery. Do not insert hidden HTML comments or authoring rationale in the body.
- This template tracks a phase session. The [UAT issue variant](issue.md#uat)
  is the canonical issue body; its readiness instructions own saved-issue
  readback, saved entry-point checks and authoring/publication-error repair.
- Start with one exact accessible URL, including its full path and trailing slash
  when required, or a directly runnable supplied launcher. Verify it opens the
  delivered build. A homepage, package name or guessed route is insufficient.
  For a supplied Windows launcher, state the exact launch actions, such as
  `Win+R`, paste the full prepared path, then press `Enter`, and its expected
  startup screen. The maintainer selects the source/build before handoff.
- When multiple tests need an index, give a numbered run order with descriptive
  linked test names. Do not use bare issue numbers or ask the human to choose a
  source/build. An issue index uses the same [issue UAT variant](issue.md#uat),
  preserving its headings, order and step table. Each numbered row names the
  linked test and exact opening action; its Actual outcome / evidence column
  says reporting belongs in that linked test. Record each reply there once.
  Replace the standalone "Reply for each numbered step" sentence with "Record
  action results only in each linked test; no separate index-row replies."
  Retain Human acceptance fields; its decision/evidence reference the actual
  linked test decisions, without a duplicate acceptance action at the index.
- Give a short checklist of 2-4 observable behaviors and numbered actions. Each
  action identifies the actual visible screen, button, field or object and exact
  click/key; supply concrete safe fixture values for required inputs. Every action
  has its own expected visible result. Map actions to approved acceptance IDs.
- Verify the script against the delivered UI, including labels and key behavior.
  Do not invent controls. Mark an unavailable function or unverified entry point
  `BLOCKED` with the missing prerequisite, keep dependent actions unresolved, and
  do not count it as passing. Author checks do not supply human acceptance.
- AI/maintainer selects and prepares the build, credentials/test session and data,
  extracts packages, records hashes, versions and provenance, runs technical
  checks, gathers evidence and prepares bundles. Never assign these tasks to the
  human reviewer. Link a clearly separate **maintainer-owned record** containing
  that provenance and evidence; the human need not read or compare it.
  The record identifies the exact build/commit, artifact hashes/versions,
  environment, prepared access/data references, UI inspection evidence and
  technical check/bundle references. Keep secrets out of public records.
- Ask for `N PASS`, `N FAIL <short observation>`, or `N BLOCKED <reason>` for each
  numbered action in a test (index results belong only in the linked tests).
  Record actual replies; silence, skips and source inspection
  never imply PASS. Keep `PENDING HUMAN acceptance` until the actual human
  decision is recorded, even when author checks pass.

---

## File Template

```markdown
---
status: testing | partial | complete
phase: XX-name
source: [1+ SUMMARY.md paths tested]
started: [ISO timestamp]
updated: [ISO timestamp]
---

## Current Test

number: [N]
name: [one short action name]
expected: [one sentence: visible result]
awaiting: user response

## Entry point and prepared fixtures

- Open: [one exact accessible URL including full path/trailing slash, or supplied launcher with full path and exact launch keys]
- Ready environment: [one line: environment name and prepared test role/session]
- Safe fixtures: [1-3 exact input values or prepared objects; N/A with reason if no inputs]
- Maintainer record: [one accessible reference to separate build/provenance/technical evidence; reference only]

## Acceptance checklist

- [ ] [One short observable behavior]
- [ ] [One short observable behavior]

## Tests

### 1. [Open the delivered screen; short action name]
acceptance: [approved acceptance ID(s)]
action: [Open exact entry point above; verified click/key sequence, including Win+R, paste full path, Enter when applicable]
expected: [one sentence: visible screen and identifying label/object]
result: pending

### 2. [Use the visible control; short action name]
acceptance: [approved acceptance ID(s)]
action: [one action: actual visible button/field/object + exact click/key + safe fixture value if needed]
expected: [one sentence: visible state/output after that action]
result: pending

## Reply format

Reply for each numbered action: `N PASS`, `N FAIL <short observation>`, or `N BLOCKED <reason>`.

## Human acceptance

Status: PENDING HUMAN acceptance
Reviewer: [Pending until human review; actual reviewer name]
Date: [Pending until human review; YYYY-MM-DD]
Decision: [Pending until human review; one sentence stating actual decision]
Evidence: [Pending until human review; actual decision reference]

## Summary

total: [N]
passed: [N]
issues: [N]
pending: [N]
skipped: [N]
blocked: [N]

## Gaps

- truth: "[expected behavior from test]"
  status: failed
  reason: "User reported: [verbatim response]"
  severity: blocker | major | minor | cosmetic
  test: [N]
  root_cause: "[maintainer diagnosis, or Unknown with missing evidence]"
  artifacts:
    - path: "[affected source path]"
      issue: "[one sentence: diagnosed source issue]"
  missing:
    - "[one sentence: needed correction]"
  debug_session: "[actual diagnosis reference, or N/A with reason]"
```

---

<section_rules>

**Frontmatter:**
- `status`: OVERWRITE - "testing", "partial", or "complete"
- `phase`: IMMUTABLE - set on creation
- `source`: IMMUTABLE - SUMMARY files being tested
- `started`: IMMUTABLE - set on creation
- `updated`: OVERWRITE - update on every change

**Current Test:**
- OVERWRITE entirely on each test transition
- Shows which test is active and what's awaited
- On completion: "testing complete"
- When all required actions pass but the final human decision is absent:
  `awaiting: final human acceptance decision`; omit number, name and expected
  because no test remains. Keep `status: partial`.

**Tests:**
- Each test: OVERWRITE result field when user responds
- `result` values: pending, pass, issue, skipped, blocked
- If issue: add `reported` (verbatim) and `severity` (inferred)
- If skipped: record the user's explicit decision in `reason`.
- If blocked: record the prerequisite in `blocked_by` and its `reason`.

**Summary:**
- OVERWRITE counts after each response
- Tracks: total, passed, issues, pending, skipped, blocked

**Gaps:**
- APPEND only when issue found (YAML format)
- After diagnosis: fill `root_cause`, `artifacts`, `missing`, `debug_session`
- This section feeds directly into plan-phase with the recorded verification gaps

</section_rules>

<diagnosis_lifecycle>

**When an observed failure creates a gap, diagnose it while `status: partial`:**

1. Coordinator routes the observed failure to bounded debugger diagnosis within the authorized scope
2. Coordinator assigns bounded investigations using the local debugger role
3. Each agent investigates one gap, returns root cause
4. UAT.md Gaps section updated with diagnosis:
   - Each gap gets `root_cause`, `artifacts`, `missing`, `debug_session` filled
5. Retain `status: partial`; store diagnosis in Gaps, not in a new session status
6. Return the diagnosed gaps to `plan-phase` for repair planning

**After diagnosis (fictional example only; replace with actual diagnosis):**
```yaml
## Gaps

- truth: "Comment appears immediately after submission"
  status: failed
  reason: "User reported: works but doesn't show until I refresh the page"
  severity: major
  test: 2
  root_cause: "useEffect in CommentList.tsx missing commentCount dependency"
  artifacts:
    - path: "src/components/CommentList.tsx"
      issue: "useEffect missing dependency"
  missing:
    - "Add commentCount to useEffect dependency array"
  debug_session: ".planning/debug/comment-not-refreshing.md"
```

</diagnosis_lifecycle>

<lifecycle>

**Creation:** When verify-work starts new session
- Derive actions covering each CONTEXT acceptance ID; use SUMMARY files as claims to check against the delivered UI.
- Set status to "testing"
- Current Test points to test 1
- All runnable tests have result: pending; unavailable/unverified actions have result: blocked and a reason.

**During testing:**
- Present test from Current Test section
- User replies `N PASS`, `N FAIL <short observation>` or `N BLOCKED <reason>`
- Coordinator records the reply and updates result (pass/issue/blocked; skipped only by explicit decision)
- Update Summary counts
- If issue: append to Gaps section (YAML format), infer severity
- Current Test names the first nonpassing action; coordinator may explicitly select an independent remaining action by its number.

**On completion:**
- Set `status: complete` only when every required action result is `pass` and actual human acceptance is recorded.
- Current Test → "[testing complete]"
- Commit file
- Present summary with next steps

**Partial completion:**
- After any recorded response, set `status: partial` while any case is pending, issue/failed, blocked or skipped, or the actual final human acceptance decision is absent.
- Keep Current Test on the first nonpassing case with its expected result and `awaiting: user response`.
- If all required actions pass, replace Current Test with only
  `awaiting: final human acceptance decision`; do not invent another test.
- Preserve pending Human acceptance status, reviewer, date, decision and evidence
  until actual final feedback arrives. Action PASS replies never imply the final
  decision or supply its reviewer/date/evidence.
- Commit file
- Present summary with outstanding items highlighted

**Resuming partial session:**
- Read the UAT file directly; inspect the first nonpassing action or the pending
  final decision when all required actions pass. Preserve prior observations
  and pending Human acceptance fields until actual final feedback arrives.
- Set `status: complete` only after every required action records `pass` AND
  the actual final human acceptance decision, reviewer, date and evidence are recorded.

The coordinator authors and updates this session document. The local runtime has
no UAT creation, case-selection or result-recording verbs/flags.
`verification.status PHASE` reads `NN-VERIFICATION.md` metadata only; it does not
report UAT progress. Use the supported verification workflow for phase status,
and preserve this file's actual observations when reconciling its report.

**Resume after /clear:**
1. Read frontmatter → know phase and status
2. Read Current Test → know where we are
3. Inspect the first nonpassing result or, if all required actions pass, the pending final human decision; record a new outcome only from fresh user feedback. Apply the same action-pass AND actual-decision completion predicate.
4. Summary shows progress so far

</lifecycle>

<severity_guide>

Severity is INFERRED from user's natural language, never asked.

| User describes | Infer |
|----------------|-------|
| Crash, error, exception, fails completely, unusable | blocker |
| Doesn't work, nothing happens, wrong behavior, missing | major |
| Works but..., slow, weird, minor, small issue | minor |
| Color, font, spacing, alignment, visual, looks off | cosmetic |

Default: **major** (safe default, user can clarify if wrong)

</severity_guide>

<good_example>
Fictional example only: the URL, controls, fixtures, record and observations below
describe an assumed comments UI, not this repository or verified project evidence.

```markdown
---
status: partial
phase: 04-comments
source: 04-01-SUMMARY.md
started: 2025-01-15T10:30:00Z
updated: 2025-01-15T10:45:00Z
---

## Current Test

number: 4
name: Post the comment
expected: A comment reading "UAT comment 04" appears below UAT Post 04 immediately
awaiting: correction and user retest

## Entry point and prepared fixtures

- Open: https://comments.example.test/posts/uat-post-04/
- Ready environment: staging, prepared signed-in test account UAT Reviewer
- Safe fixtures: post "UAT Post 04"; comment text "UAT comment 04"
- Maintainer record: comments-04-build-record.md (reference only)

## Acceptance checklist

- [x] UAT Post 04 opens with a usable comment composer.
- [ ] Posting a comment displays its text immediately.

## Tests

### 1. Open the test post
acceptance: AC-04-01
action: Open https://comments.example.test/posts/uat-post-04/
expected: The heading "UAT Post 04" and "New comment" button appear
result: pass
reported: "1 PASS"

### 2. Open the composer
acceptance: AC-04-01
action: Click "New comment" below "UAT Post 04"
expected: The "Comment" field and "Post comment" button appear
result: pass
reported: "2 PASS"

### 3. Enter the safe comment
acceptance: AC-04-02
action: Type "UAT comment 04" into the "Comment" field
expected: The field displays "UAT comment 04"
result: pass
reported: "3 PASS"

### 4. Post the comment
acceptance: AC-04-02
action: Click "Post comment" below the "Comment" field
expected: A comment reading "UAT comment 04" appears below UAT Post 04 immediately
result: issue
reported: "4 FAIL The comment appears only after I refresh."
severity: major

## Reply format

Reply for each numbered action: `N PASS`, `N FAIL <short observation>`, or `N BLOCKED <reason>`.

## Human acceptance

Status: PENDING HUMAN acceptance
Reviewer: Pending final human review
Date: Pending final human review
Decision: Pending correction and retest of action 4
Evidence: Recorded action replies above; final decision pending

## Summary

total: 4
passed: 3
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Posting a comment displays its text immediately"
  status: failed
  reason: "User reported: 4 FAIL The comment appears only after I refresh."
  severity: major
  test: 4
  root_cause: "Unknown; maintainer diagnosis pending"
  artifacts: []
  missing:
    - "Diagnose and correct delayed display before human retest"
  debug_session: "N/A; diagnosis has not started"
```
</good_example>


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
