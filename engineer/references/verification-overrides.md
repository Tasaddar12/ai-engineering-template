# Decision-reference traceability

Verification reports preserve approved decision changes without waiving acceptance. There is no fuzzy match, automatic override, accepted-gap pass or decision-count exemption.

## Inputs

Read the exact approved decision in PROJECT Key Decisions or phase CONTEXT, the current requirement/acceptance wording, the PLAN/SUMMARY contract and the covered source revision. An ADR supplies optional rationale only; it is not the decision owner.

## Traceability format

```yaml
decision_references:
  - id: D-03
    source: .planning/PROJECT.md
    entry: "Use session authentication"
    obligation: REQ-AUTH-01
    effect: "Approved authentication mechanism is session based"
    evidence: "Actual behavioral check and covered revision"
    status: verified # verified | unverified | failed
```

| Field | Required meaning |
|-------|------------------|
| id | Exact stable decision identifier |
| source / entry | Owning record and unambiguous entry |
| obligation | Requirement, acceptance or must-have affected |
| effect | Precise approved change; no implied deferral |
| evidence | Actual revision-scoped verification or missing reason |
| status | Observed outcome, never inferred approval |

## Procedure

1. Identify the exact owning decision and authority. A reviewer preference or an issue comment is not automatically a scope change.
2. Compare the approved outcome with the current PLAN, requirement wording and implementation. Establish which artifact is wrong with evidence.
3. Ask the coordinator to reconcile structured requirements/roadmap/state through their owning runtime verbs. Preserve the approved outcome and historical rationale.
4. Verify the resulting acceptance obligation normally. An alternative mechanism can satisfy the approved intent when the actual behavior demonstrates it; cite that evidence rather than waiving the old wording silently.
5. If a required outcome is missing, failed or unexercised, retain the gap. A known deviation and its acceptance rationale do not turn a failing check into a pass.
6. If deferral is explicitly authorized, retain its exact scope, owner and destination. A deferral is a changed obligation, not verification evidence for behavior that did not ship.
7. Return decision-reference dispositions with the final report. The coordinator resolves conflicts; the verifier does not invent scope or author fix plans.

## Examples

Good: PROJECT D-03 approves session authentication; the current requirement is reconciled, and the session lifecycle test exercises expiration and revocation at the covered revision.

Bad: a report marks missing authentication behavior accepted because an earlier decision discussed a different mechanism.

Good: a recorded user instruction defers visual testing; the report leaves required visual acceptance pending and does not run it before the authorized point.

Bad: unattended mode, repeated review count or a fuzzy text match treats an unverified behavior as passed.

## Report impact

VERIFIED requires direct evidence for the current obligation. FAILED remains a gap. PRESENT_BEHAVIOR_UNVERIFIED and insufficient_spec route to the appropriate missing-evidence or human acceptance path. Decision-reference counts are traceability only and cannot replace the report's observable truths, artifact/link evidence, check receipts or UAT acceptance.
