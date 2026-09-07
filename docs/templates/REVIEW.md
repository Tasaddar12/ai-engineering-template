# Review: <review-id>

Copy this master to `.ai/plans/current/<plan-id>/reviews/<review-id>.md`.

- Stage: `isolation | implementation | consistency | integration`
- Plan/task: `<plan-id>/<optional-task-id>`
- Candidate: `<immutable commit and content fingerprint>`
- Reviewer invocation/profile: `<provenance>`
- Prior review: `<reference-or-none>`

## Evidence inspected

List exact files, commands, outputs, hashes, and prior handoffs. Distinguish direct observation from author claims.

## Checklist

| Check | Pass/fail/N/A | Evidence and reason |
| --- | --- | --- |
| `<check-id>` | `<result>` | `<specific support>` |

## Findings

For each finding record severity, exact location, expected behavior, observed behavior, reproduction, acceptance impact, and required repair. Reviewers report; they do not edit the candidate.

## Verdict

Record `pass` only when every required check is supported for the exact candidate. Any material change invalidates the affected verdict.
