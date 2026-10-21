# Enhancement Issue Template

Template for a separately composed Enhancement issue body.

**Purpose:** Connect a user's unmet need to a bounded, verifiable capability.

**Key principle:** Acceptance describes an observable user outcome.

**Producer:** The coordinator or assigned author, using the requested outcome and evidence.

**Downstream consumers:**

- Planner and implementer: establish the capability and its scope.
- Verifier and issue reviewer: check the proposed outcome against acceptance.

**Destination:** A reviewed public issue body file.

Read this source in full, then copy only its fenced **File Template** into the
body file. Replace placeholders with known facts or explicit pending dependencies.
Follow the [Git workflow](../../references/git-workflow.md) for title and publication.

---

## File Template

```markdown
## User need

[One sentence: user + goal + current limitation.]

## Proposed outcome

[One sentence: requested observable user-facing change.]

## Current limitation and evidence

[1-2 sentences: limitation. Add build/version, environment, observed commit and 1-3 actual safe evidence URLs.]

## Impact

[One sentence: affected users/systems and practical impact.]

## Scope

- In: [bounded capability]
- Out: [adjacent behavior excluded]

## Acceptance

- [Outcome 1: observable user result]
- [Outcome 2: observable user result]
- [Outcome 3: if needed]
- [Outcome 4: if needed]

## Related links

[1-3 actual issue/PR/requirement references or accessible evidence URLs.]
```

## Good and bad examples

**Good example excerpt** (fictional):

```markdown
## User need
Shoppers need to save a delivery address before placing an order.

## Scope
- In: Saving an address from the account page.
- Out: Order submission and address sharing.

## Acceptance
- A saved address appears after reloading the account page.
- Invalid required fields show the corresponding field error.
```

**Bad:** "Make account management better."

## Guidelines

- Retain the File Template headings and order. Name the user, current limitation
  and proposed observable outcome in their respective sections.
- Ground the current limitation in inspected behavior, build/environment and safe
  evidence. Use `Unknown` or `Pending` with the missing fact or dependency.
- Bound the capability in Scope and give two to four acceptance outcomes that a
  reviewer can check. Link the actual related requirements or issues.

## Completion and downstream handoff

- Replace prompts and example values with the requested capability, inspected
  limitation, evidence and bounded acceptance.
- Hand off the reviewed body file under the Git workflow. Report the saved issue
  URL after readback, or the exact publication blocker.
