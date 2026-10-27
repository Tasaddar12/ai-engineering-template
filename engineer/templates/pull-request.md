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

## Title format and examples

- Use `type(scope): description` with `feat`, `fix`, `docs`, `refactor`, `test` or `chore`, and a short lowercase scope consistent with the repository's Git subjects. This is authoring guidance inspired by Conventional Commits; Git and GitHub do not enforce it.
- Describe the final implemented problem and resulting behavior. A title must remain useful to a reviewer who did not read the conversation. Examples:

  ```text
  feat(checkout): save addresses independently of orders
  fix(search): return an empty result for blank queries
  docs(api): document pagination parameters and defaults
  test(import): cover duplicate rows in the CSV preview
  ```

## How to fill it

1. Copy only the fenced File Template into a separate public body file. Replace every prompt and bracketed value with actual scope and evidence; remove explanatory examples from the published body.
2. Lead Goal and Changes with the concrete trigger and resulting behavior. Describe the final implementation, not abandoned approaches or conversational history, unless a tradeoff requires that history.
3. Ground claims in the actual delivered commits, complete owned records and current verification. Distinguish the current full Candidate SHA from the full Tested SHA. If nothing ran, record Pending instead of inventing a revision or result.
4. Put one exact command or argv per evidence row. Record its actual result and an accessible evidence URL matching the Tested SHA. A timestamp, an agent's exit code or a link to a different revision is not behavioral proof.
5. Use `N/A` only with an explanation of why a field does not apply. Use Unknown or Pending with the missing evidence or dependency. In Known gaps, use None only after the relevant scope has been checked.
6. Include material risks and a practical rollback or recovery action with its limits. Preserve each threat's owning PLAN/Threat ID, verified canonical issue, distinct outcome, actual Git state and evidence. Accepted/deferred and merged/closed are not interchangeable with resolved.
7. Review open and closed issues, related PRs and the current PR before adding issue references or creating follow-ups. Keep in-scope defects in this change. Neutral links preserve tracking; closing references require scope-complete evidence and existing closure authority.
8. Redact secrets, private logs, personal information and restricted security details. Do not paste internal metadata or unreviewed worker requests into the public body.
9. Include Stack only for an actual stack. State the real parent, target, prerequisites and full base-to-head boundary. Do not imply this PR independently implements its prerequisites.
10. Review the exact title/body file before the authorized provider write. Read back the saved title, body, base, head and draft state. Recover an uncertain write by inspecting the exact intended PR before retrying.

The following excerpt is fictional authoring guidance, not evidence:

| Field | Example |
|---|---|
| Goal / Changes | Checkout can save an address before an order. Persist the address independently and validate its required fields. |
| Revision status | Candidate: `a3f14d9c6b2e8075c1a4f9b3d6e20a7c8f51b4e0` (fictional); Tested: Pending. |
| Check | `python -m unittest discover -s tests -p test_workflow_links.py -v` — Pending (not run). |
| Evidence | `https://github.com/example/project/actions/runs/12345` is only a fictional URL format; replace it with an accessible run for the actual Tested SHA. |

## Completion and downstream handoff

- The public body contains the authorized outcome, final owned changes, actual evidence and remaining obligations; no template prompts remain.
- Stack fields describe the actual dependency, or the entire Stack section is omitted.
- Hand off the reviewed body file and exact candidate/evidence identities to the coordinator. A tracking draft is not a readiness verdict.
- Ready requires current passed verification, applicable independent reviews, local/provider checks and issue-link audit. Merge additionally requires the user's explicit instruction.
