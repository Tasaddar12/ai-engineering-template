# Security Risk Issue Template

Template for a separately composed standalone Security risk issue body.

**Purpose:** Record an actionable security concern, assessment and bounded remediation.

**Key principle:** The recorded lifecycle describes the observed risk state.

**Producer:** The coordinator or assigned author, using reviewed safe evidence.

**Downstream consumers:**

- Risk owner and implementer: assess the concern and carry out the remediation.
- Verifier and issue reviewer: compare the observed outcome with secure acceptance.

**Destination:** A reviewed public issue body file.

Read this source in full, then copy only its fenced **File Template** into the
body file. Replace placeholders with inspected facts or explicit pending dependencies.
Follow [canonical threat tracking](../../references/git-workflow.md#canonical-threat-tracking).

---

## File Template

```markdown
## Security concern

[One public-safe sentence: security concern without secrets/exploit details.]

## Affected surface and behavior

- Surface: [component or data]
- Current: [one sentence: current behavior]
- Expected: [one sentence: secure behavior]

## Impact

[One sentence: affected users/data/systems and plausible impact.]

## Risk assessment and lifecycle

- Threat ID / risk key: [stable repository + surface/control + failure mode/remediation key]
- Source aliases: [all source occurrences; PLAN/SUMMARY IDs when present]
- Severity: [critical|high|medium|low; impact/likelihood rationale and uncertainty]
- Owner: [responsible party]
- Status: [unresolved|mitigated|accepted|deferred; observed state, not PLAN disposition]
- Mitigation or safe next action: [bounded remediation; accepted rationale or deferral reason/next action]
- Resolution evidence: [matching revision and actual secure check/result, or Pending with dependency]

## Safe evidence

[1-3 actual accessible, redacted, non-sensitive evidence URLs; identify affected build/commit when known. Omit exploit details.]

## Requested remediation

- [Safe remediation outcome]
- [Observable secure check]
- [Additional safe criterion, if needed]
- [Additional safe criterion, if needed]

## Scope and acceptance

- In: [bounded remediation]
- Out: [related work excluded]
- [Observable safe resolution criterion]
- [Safe regression criterion]

## Related links

[1-3 actual public issue/PR/requirement references or non-sensitive evidence URLs.]
```

## Good and bad examples

**Good example excerpt** (fictional):

```markdown
## Security concern
Session reset tokens remain usable after the session is revoked.

## Risk assessment and lifecycle
- Threat ID / risk key: shop/auth/reset-token-revocation
- Source aliases: P03/T02
- Severity: high; account access can persist after revocation; exposure pending assessment.
- Owner: Authentication maintainer
- Status: unresolved
- Mitigation or safe next action: Reject reset tokens for revoked sessions.
- Resolution evidence: Pending: isolated revocation regression run.
```

**Bad:** "Authentication is insecure; fixed when the PR merges."

## Guidelines

- Retain the File Template headings and order. Describe the affected surface,
  current behavior, secure behavior and plausible impact with public-safe facts.
- Fill the assessment fields with the stable key, source references, severity
  rationale, owner, observed status, safe next action and matching evidence.
- Use `Unknown` or `Pending` with the missing assessment or verification dependency.
  State observable secure acceptance and link accessible redacted evidence.

## Completion and downstream handoff

- Replace prompts and example values with the reviewed concern, assessment,
  bounded remediation and actual lifecycle evidence or pending dependencies.
- Hand off the reviewed body and canonical reference under canonical threat
  tracking. Report the saved issue URL after readback, or the exact blocker.
