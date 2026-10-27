# Pull request template

Read [Git workflow](../references/git-workflow.md) before creating or editing. The coordinator prepares a complete exact body file, validates it and verifies actual provider readback. Open a draft on the first authorized push and keep it current after every slice.

## File Template

```markdown
## Goal

[Concrete problem, trigger and resulting behavior for a reviewer without conversation context.]

## Changes

[Final implementation and why it satisfies the bounded goal; link owning decisions and affected contracts.]

## Requirements or Issues

[Actual requirement IDs and canonical issues. Omit this section when none exist. Distinguish neutral references from closing references.]

## Verification

| Revision status | SHA |
|-----------------|-----|
| Candidate | [full current candidate SHA] |
| Tested | [full actually tested SHA, or Not run] |

| Exact command | Result | Evidence URL |
|---------------|--------|--------------|
| [One exact command/argv per row] | [observed pass/fail/not run/not configured] | [actual evidence URL matching tested SHA, or Pending reason] |

[Required human acceptance, independent audits, source/currentness limitations and user test ordering.]

## Known gaps

[Remaining scope, failed/missing checks, pending human decisions and explicit authorized deferrals; use None only when supported.]

## Risks or rollback

[Material behavior/deployment/migration risks and a practical concrete rollback/recovery action, with its limits.]

| PLAN / Threat ID | Canonical issue | Outcome | Git state | Evidence |
|------------------|-----------------|---------|-----------|----------|
| [exact source / stable ID] | [verified URL] | [unresolved / mitigated / accepted / deferred] | [actual commit/integration state] | [actual evidence at tested revision] |

[If no threats: None identified, with the exact inspected scope and evidence; do not use an empty unsupported assurance.]

## Stack

- stackParent: [actual parent PR/branch]
- Target: [actual target branch]
- DependsOn: [actual prerequisite PRs]
- OwnChangeBoundary: [this PR's exact delta and exclusions]

[Include Stack only when an actual stack exists.]
```

## Authoring and consumer contract

- Describe the final problem/result and implementation. Rewrite title/body when final scope changes; omit abandoned conversational history unless it explains a material tradeoff.
- Preserve required Goal, Changes, Verification, Known gaps and Risks or rollback. Requirements or Issues is optional when none; Stack is conditional on a real stack.
- Candidate and Tested SHA are distinct. Never imply checks cover later source without valid matching evidence. Keep one row per exact command, actual result and a usable evidence URL matching Tested SHA.
- Label pending/deferred checks honestly. If the user orders every stacked draft PR before checks, keep every draft's validation pending until that final batch.
- Preserve practical rollback and every threat's canonical relationship, lifecycle outcome, Git state and actual evidence. A merged commit or closed issue does not itself establish mitigation or human acceptance.
- Record known gaps and required human decisions. An accepted/deferred risk is not a passed obligation or closure authority.
- Validate the complete description before provider mutation, then read back title/body/base/head/draft state. An uncertain provider outcome requires inspection before retry.
- Ready/merge require current passed verification, required provider checks and independent issue-link audit. Merge additionally requires the user's explicit instruction.

## Good and bad evidence

Good: Candidate and Tested show actual SHAs; each exact argv row records observed status and the evidence URL tied to Tested. Human visual acceptance stays pending until the real response.

Bad: "Tests pass", unsupported "No risks", an inaccessible guessed evidence URL, or a timestamp substituted for the tested revision.

Good: a real stack names stackParent, Target, DependsOn and OwnChangeBoundary, allowing a reviewer to distinguish this PR's delta from prerequisites.

Bad: add a Stack section to an unstacked PR or imply this PR independently delivers its parent's changes.
