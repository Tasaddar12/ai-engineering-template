# Consolidated Security Risk Template

Template for a separately composed consolidated Security risk issue body.

**Purpose:** Track related security risks in one concise table with one task per risk.

**Key principle:** Each row and its task address the same stable risk identity.

**Producer:** The coordinator or assigned author, using reviewed risk assessments.

**Downstream consumers:**

- Risk owners and implementers: follow each risk's remediation and source assessment.
- Verifier and issue reviewer: inspect individual outcomes and canonical references.

**Destination:** A reviewed public issue body file.

Read this source in full, then copy only its fenced **File Template** into the
body file. Replace placeholders with reviewed facts or explicit pending dependencies.
Follow [canonical threat tracking](../../references/git-workflow.md#canonical-threat-tracking).

---

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

## Good and bad examples

**Good example excerpt** (fictional):

```markdown
| Risk ID | Risk / remediation | Severity / assessment | Owner | Status | Acceptance / evidence | Sources / canonical |
|---|---|---|---|---|---|---|
| R-001 | Cross-tenant read; apply tenant filter ([mitigation](https://example.test/plans/p01#mitigation)) | [High](https://example.test/plans/p01#assessment) | API maintainer | unresolved | Other tenant denied; Pending: regression run | shop/api/tenant-read; [P01/T01](https://example.test/plans/p01#t01); alias P02/T03; [canonical](https://example.test/issues/7#r-001) |

### R-001

- [ ] Remediation verified
```

**Bad:** "R-001: authentication risk; done after planning."

## Guidelines

- Use this block for consolidated security risks. One row and one task per risk.
  Retain the File Template headings, column order and matching risk-ID heading.
- Put the task under the ID heading, label it `Remediation verified`.
- Keep risk/remediation concise. Link the assessment and source records from the
  row; record the actual owner, observed status, acceptance and available evidence.
- Fill unavailable facts or checks with `Pending` and the specific dependency.

## Completion and downstream handoff

- Replace prompts and example values with the reviewed risk rows, matching tasks
  and verified source/canonical links.
- Reconcile the saved body under canonical threat tracking. Hand off its verified
  per-risk references and actual outcomes, or the exact readback blocker.
