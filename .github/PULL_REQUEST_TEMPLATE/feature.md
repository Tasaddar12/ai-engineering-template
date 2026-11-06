<!--
Feature PR: Introduce a new capability.
Use template=feature.md when creating a GitHub PR.
Read the shared authoring guidance in .github/pull_request_template.md.
Replace all prompts with facts; remove this comment before publication.
Omit Requirements or Issues when none apply and Stack when there is no stack.
-->

## Goal

[One sentence: intended user + new capability + observable outcome.]

## Changes

- [New user-facing capability and why it is needed]
- [Implemented behavior and bounded entry points]
- [Configuration, compatibility or migration requirements, if applicable]

## Requirements or Issues

[1-3 exact requirement IDs and issue URLs; omit this section if none apply.]

## Verification

| Revision status | SHA |
|---|---|
| Candidate | [one full current head SHA] |
| Tested | [one full tested SHA, or Pending until verified] |

| Exact command (one row per check) | Result (one sentence or Pending) | Evidence URL matching tested SHA |
|---|---|---|
| [one exact acceptance or regression check for the new capability] | [one sentence with actual result, or Pending (not run)] | [one accessible matching URL, or Pending] |

## Known gaps

- [Gap 1 of 1-3: unfinished work, unverified behavior, pending check or dependency; or None after checking]
- [Gap 2: if applicable]
- [Gap 3: if applicable]

## Risks or rollback

- Risks: [one sentence: material risks or none identified]
- Rollback: [one sentence: practical rollback for this change]

| PLAN / Threat ID | Canonical issue | Outcome | Git state | Evidence |
|---|---|---|---|---|
| [Owning PLAN#threat-id] | [Verified issue URL or Pending: dependency] | [Observed outcome] | [open/closed/Pending readback] | [Safe revision/check/result and readback, or Pending: dependency] |

[Use None identified with inspected scope when applicable.]

## Stack

- stackParent: [parent PR number or URL]
- Target: [current target branch]
- DependsOn: [prerequisite PR URLs, or None if none]
- OwnChangeBoundary: [full base SHA..full head SHA]
