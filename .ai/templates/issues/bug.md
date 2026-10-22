# Bug Issue Template

Use this template for Bug issue bodies.

**Purpose:** Describe an observed failure, a reproducible starting point and the
observable result required to fix it.

**Key principle:** Match reproduction and acceptance to the same failing behavior.

**Producer:** The coordinator or assigned author, using inspected behavior and evidence.

**Downstream consumers:**

- Implementer: reproduce the failure and identify the bounded correction.
- Verifier and issue reviewer: compare the correction with the recorded acceptance.

**Destination:** A reviewed public issue body file.

Read this source in full, then copy only its fenced **File Template** into the
body file. Replace placeholders with observed facts or explicit pending dependencies.
Follow the [Git workflow](../../references/git-workflow.md) for title and publication.

---

## File Template

```markdown
## Problem
[One sentence: affected user/system + failing action or current state.]

## Expected behavior
[One sentence: observable result the affected user should get.]

## Actual behavior
[One sentence: observed result, build/version and environment; Unknown if unverified.]

## Reproduction

- Build/version: [exact version or artifact]
- Environment: [name/configuration]
- Entry point: [one exact accessible URL including full path/trailing slash, or directly runnable supplied launcher]
- Prepared setup: [one line: ready test role/session and safe fixture values; maintainer prepares prerequisites]

1. [One action: visible screen/control/object + exact click/key and concrete safe input. Expected: one visible result.]
2. [Next action with exact control/input. Expected: one visible result. Actual: observed failure or Unknown with reason.]

## Safe evidence
[1-3 accessible redacted evidence URLs; include the observed revision. No secrets.]

## Impact
[One sentence: affected users/systems and practical impact or severity.]

## Acceptance
- [Outcome 1: observable pass/fail result]
- [Outcome 2: observable pass/fail result]
- [Outcome 3: if needed]
- [Outcome 4: if needed]

## Scope
- In: [bounded behavior]
- Out: [adjacent behavior excluded]

## Related links
[1-3 actual issue/PR/requirement references or accessible evidence URLs.]
```

## Good and bad examples

**Good example excerpt** (fictional; replace with actual observations):

```markdown
## Problem
Submitting an empty search returns HTTP 500 in the staging build.

## Expected behavior
The search returns HTTP 200 with an empty result list.

## Acceptance
- An empty search returns HTTP 200 with [].
- The empty-query regression check passes at the corrected revision.
```

**Bad:** "Search is broken; improve it."

## Guidelines

- Retain the File Template headings and order. State current and expected
  behavior separately. If behavior is unobserved, use `Unknown` with the missing check.
- Record the tested build, environment, prepared setup and exact reproduction
  actions. Use the [UAT authoring contract](../UAT.md#authoring-contract) for
  user-facing entry points, visible controls and safe inputs.
- Give two to four observable acceptance outcomes within the stated scope.
  Link accessible redacted evidence to the observed revision.

## Completion and downstream handoff

- Replace prompts and example values with the reviewed failure, reproduction,
  evidence and acceptance; retain explicit dependencies for unavailable checks.
- Hand off the reviewed body file under the Git workflow. Read back the saved body, then report its URL.
  If publication or readback fails, report the exact blocker.
