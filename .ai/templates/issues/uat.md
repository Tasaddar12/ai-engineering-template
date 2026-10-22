# UAT Issue Template

Template for a separately composed human acceptance test issue body.

**Purpose:** Give a human reviewer a prepared test with visible actions and outcomes.

**Key principle:** Human acceptance records the actual human decision.

**Producer:** The coordinator or assigned author, using the prepared delivered build.

**Downstream consumers:**

- Human reviewer: perform the numbered actions and report visible results.
- Coordinator: record actual replies and the human acceptance decision.

**Destination:** A reviewed public UAT issue body file.

Read this source in full, then copy only its fenced **File Template** into the
body file. Follow the [UAT authoring contract](../UAT.md#authoring-contract) for
prepared setup, script verification and saved-body readback.
Follow the [Git workflow](../../references/git-workflow.md) for title and publication.

---

## File Template

```markdown
## Acceptance checklist

- [ ] [One short visible behavior]
- [ ] [One short visible behavior]

## Context
[One brief factual sentence: user flow and problem under review.]

## Impact and scope
Impact: [One short sentence: practical effect on affected users/systems]
- In: [bounded flow/behavior being validated]
- Out: [adjacent flow/behavior excluded]

## Build and environment

- Build/version: [exact release or artifact identifier]
- Commit: [full SHA]
- Entry point: [one exact accessible URL including full path/trailing slash, or supplied launcher with full path and exact launch keys]
- Ready environment: [one line: environment name and prepared test role/session]
- Safe fixtures: [1-3 exact input values or prepared test objects used below; N/A with reason if no inputs]
- Maintainer record: [one accessible reference to the separate build/provenance/technical evidence record; reference only]

## Steps and expected outcomes

| Step | Action | Expected outcome | Actual outcome / evidence |
|---|---|---|---|
| 1 | [Open exact entry point above via verified click/key sequence; include Win+R, paste full path, Enter for a Windows launcher] | [One sentence: actual visible screen and identifying label/object] | [Pending until human runs; then numbered reply and short observation] |
| 2 | [One action: actual visible button/field/object + exact click/key + safe fixture value if needed] | [One sentence: visible state/output after that action] | [Pending until human runs; then numbered reply and short observation] |

Reply for each numbered step: `N PASS`, `N FAIL <short observation>`, or `N BLOCKED <reason>`.

## Related links
[1-3 actual issue/PR/requirement references or accessible evidence URLs.]

## Human acceptance
Status: PENDING HUMAN acceptance
Reviewer: [Pending until human review; actual reviewer name]
Date: [Pending until human review; YYYY-MM-DD]
Decision: [Pending until human review; one sentence stating the actual human decision]
Evidence: [Pending until human review; actual decision evidence URL/reference]
```

## Good and bad examples

**Good example excerpt** (fictional; the maintainer has prepared the build and session):

```markdown
## Build and environment
- Safe fixtures: Search text: zzzz-no-match.

## Steps and expected outcomes
| Step | Action | Expected outcome | Actual outcome / evidence |
|---|---|---|---|
| 1 | Open https://example.test/search/ in the prepared test session. | The Search page shows the Query field. | Pending human run. |
| 2 | Click Query, enter zzzz-no-match, then press Enter. | The result area shows No results. | Pending human run. |

Reply for each numbered step: N PASS, N FAIL <short observation>, or N BLOCKED <reason>.
```

**Bad:** "Build the project, find the right page, and confirm everything works."

## Guidelines

- Retain the File Template headings, numbered step table and Human acceptance
  fields. Put build/provenance evidence in the linked maintainer record.
- Supply the exact verified entry point, prepared access and concrete safe inputs.
  Give each action one expected visible result and record the actual human reply.
- Keep `PENDING HUMAN acceptance` until the human decision is recorded. Record
  unavailable prerequisites as `BLOCKED` with the missing dependency.
- For an index, retain the headings, step table and Human acceptance fields.
  Replace the standalone step-reply instruction with "Record action results only
  in each linked test; no separate index-row replies." Link the actual test
  decisions and evidence instead of adding duplicate acceptance actions.

## Completion and downstream handoff

- Replace prompts and example values with the prepared test. Verify the saved
  links and actions against the delivered UI before handing it to the reviewer.
- Hand off the read-back issue URL under the UAT authoring contract. Retain pending
  acceptance until the actual reviewer, date, decision and evidence are available.
- Verify saved links and launch instructions against the prepared delivered UI
  before claiming readiness. Repair publication errors; preserve product bugs as
  FAIL/unresolved and unavailable prerequisites as BLOCKED. Recover an uncertain
  create through the Git workflow's exact-intent procedure before retrying.
