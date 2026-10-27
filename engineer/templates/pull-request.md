# Pull request template

Use [Git workflow](../references/git-workflow.md). Prepare the complete description before publication; update it after every delivered slice.

```markdown
## Problem and result

[Concrete trigger and before/after behavior. Explain why the change is needed and what the final implementation delivers.]

## Scope

- Phase / plan or maintenance assignment: [IDs and source]
- Base and head revisions: [actual SHAs]
- Included outcomes: [bounded list]
- Remaining / explicitly deferred work: [items and authority, or none]

## Changes

[Reviewer-relevant implementation and ownership boundaries. Link significant decisions and optional ADR rationale.]

## Validation

| Revision | Command argv / review | Observed result | Evidence |
|----------|-----------------------|-----------------|----------|
| [SHA] | [exact command] | [passed / failed / not run / not configured] | [receipt / report] |

[State why any required validation remains pending and the exact next step. Never infer a pass from source inspection.]

## Acceptance and documentation

- Acceptance: [evidence and required human decision / pending]
- Documentation: [updated paths and verification / not applicable reason]
- Verification report: [current report and covered digest / pending]

## Issues and threats

[Canonical issue links and stable finding/threat IDs with disposition. Use closing keywords only for work actually resolved by this PR.]

## Risks and recovery

[Material limitations, migration/deployment implications and exact rollback/recovery approach.]

## Stack

[Parent PR / branch and dependency order, or none. Keep stacked bases current without merging without the user's instruction.]
```

## Authoring rules

- Describe the final implementation for a reviewer who has not read the conversation.
- Use exact evidence from the tested revision; label checks deferred or not run honestly.
- Keep meaningful failures, warnings, remaining scope and required human acceptance visible.
- Preserve canonical issue and threat relationships. Avoid duplicate issues and unsupported close claims.
- Use the body file directly; do not encode real newlines as literal backslash sequences.
- Validate required sections before provider mutation, then read back the title, body, base, branch and draft state.
- Open a draft on the first authorized push. Keep it current after each slice.
- Ready/merge require current verification and required provider checks; merging additionally requires the user's explicit instruction.

## Good and bad validation

Bad: "Tests pass." This omits the revision, command and evidence.

Good: "At [SHA], [exact argv] exited 0; receipt [path] covers [inputs]. Human acceptance for the visual flow remains pending."

Bad: "No tests needed" when the assignment explicitly requires tests.

Good: "Not run yet: the user requires all check execution after every stacked draft PR exists. This PR remains draft pending that final validation batch."
