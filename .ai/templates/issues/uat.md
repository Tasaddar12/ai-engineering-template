# UAT issue

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
