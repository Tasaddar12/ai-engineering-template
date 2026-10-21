# Consolidated security risk

Use this block for consolidated security risks. One row and one task per risk.
Put the task under the ID heading, label it `Remediation verified`.
Follow [canonical threat tracking](../../references/git-workflow.md#canonical-threat-tracking).

## File Template

```markdown
## Security concern

[Concern]

## Affected surface and behavior

[Surface and secure behavior]

## Impact

[Impact]

## Risk assessment and lifecycle

| Risk ID | Risk / remediation | Severity / assessment | Owner | Status | Acceptance / evidence | Sources / canonical |
|---|---|---|---|---|---|---|
| [Risk ID] | [Risk / remediation] | [Assessment link] | [Owner] | [Status] | [Acceptance / evidence] | [Source links] |

### [Risk ID]

- [ ] Remediation verified

## Safe evidence

[Evidence links]

## Requested remediation

[Remediation]

## Scope and acceptance

[Scope and acceptance]

## Related links

[Related links]
```

**Good example** (fictional):

```markdown
| Risk ID | Risk / remediation | Severity / assessment | Owner | Status | Acceptance / evidence | Sources / canonical |
|---|---|---|---|---|---|---|
| R-001 | Cross-tenant read; apply tenant filter ([mitigation](https://example.test/plans/p01#mitigation)) | [High](https://example.test/plans/p01#assessment) | API maintainer | unresolved | Other tenant denied; Pending: regression run | shop/api/tenant-read; [P01/T01](https://example.test/plans/p01#t01); alias P02/T03; [canonical](https://example.test/issues/7#r-001) |

### R-001

- [ ] Remediation verified
```
