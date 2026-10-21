# Security risk issue

Follow [canonical threat tracking](../../references/git-workflow.md#canonical-threat-tracking).

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
