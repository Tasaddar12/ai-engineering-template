# Canonical issue templates

Read [Git workflow](../references/git-workflow.md) before creating or editing an issue. The coordinator owns provider mutation; workers return cited requests. Select the actual user intent: Bug, Enhancement, Decision required, Security risk or UAT. Formatting a user-facing Bug never authorizes converting it to UAT.

## Authoring contract

1. Read the actual source artifact and current full SHA. Identify the finding, requirement/acceptance and approved scope.
2. Search existing open and closed canonical trackers by source identity and full behavior/remediation scope. Reuse a complete matching tracker; preserve Pending when lookup is unavailable or ambiguous.
3. Read the entire selected variant, its guidance and consumer contract. Fill concrete observations; use Unknown for unavailable facts and explain the next action. Do not invent reproduction, entry points, controls, fixtures or evidence.
4. Preserve safe evidence: redact credentials, personal data and exploitable production payloads. Cite bounded logs/source/test evidence at actual revisions.
5. Preview the complete title/body/labels through the runtime and inspect source identity/digest. Publish/update only with the returned content-bound token and identical inputs.
6. Read back the actual provider title, body, labels, state, canonical URL and relationships before linking source records. Inspect uncertain mutations before retrying.
7. Keep neutral references separate from closing references. Closure needs scope-complete evidence and actual authority; an issue or checked box does not itself pass acceptance.

## File Template

### Bug

```markdown
## Problem

[Concrete user-visible defect and trigger.]

## Expected behavior

[Observable correct outcome and owning requirement.]

## Actual behavior

[Observed outcome; Unknown when not observed.]

## Reproduction

- Build/version: [exact build or Unknown]
- Environment: [actual platform/account/configuration or Unknown]
- Entry point: [exact accessible URL/path or supplied launcher]
- Prepared setup: [safe fixtures and prerequisites]

1. [Exact user action and visible expected/actual result].
2. [Next action and visible expected/actual result].

## Safe evidence

[Redacted observation, exact source revision and evidence references. Distinguish hypothesis from established cause.]

## Impact

[Affected users/data, severity and concrete consequence.]

## Acceptance

- [ ] [Observable corrected outcome].
- [ ] [Meaningful regression evidence at corrected revision].

## Scope

[Authorized correction, excluded unrelated changes and remaining unknowns.]

## Related links

[Source artifact/finding, requirement, canonical issue and PR URLs.]
```

**Producer:** coordinator from an observed user report or diagnostic packet. **Consumers:** debugger, planner/executor and verifier. Preserve original expected/actual words; a hypothesized root cause is not an observation.

Good: "After Submit, the new comment appears only after refresh; reported at the captured build."
Bad: "The cache is broken" when the cache path has not been investigated, or a fabricated launch path to make the report look runnable.

### Enhancement

```markdown
## User need

[Who needs to accomplish what and why.]

## Proposed outcome

[Observable new capability, without prescribing unsupported mechanism.]

## Current limitation and evidence

[Current behavior, concrete limitation, revision and actual evidence.]

## Impact

[Who benefits and measurable practical effect.]

## Scope

[Included behavior, excluded work, dependencies and authority.]

## Acceptance

- [ ] [Concrete observable outcome].
- [ ] [Required documentation/verification and human judgment].

## Related links

[Source request, requirement, decisions and actual canonical trackers.]
```

**Producer:** coordinator from the authorized request. **Consumers:** discussion and planning. An enhancement issue records intent; it does not authorize implementing a phase or silently replace a Bug's expected behavior.

Good: name the missing capability and a testable outcome.
Bad: add adjacent features or defer the original requirement merely because research suggests a broader design.

### Decision required

```markdown
## Decision question

[One exact unresolved choice.]

## Context

[Approved outcome, constraints, reversible/one-way consequences and existing decisions.]

## Options

| Option | Choice | Consequence / tradeoff |
|--------|--------|------------------------|
| [A] | [concrete choice] | [observed benefit/cost/uncertainty] |
| [B] | [concrete choice] | [observed benefit/cost/uncertainty] |

## Evidence

[Primary sources and actual checks with revision; label unvalidated claims.]

## Recommendation

[Evidence-based recommendation and remaining uncertainty; not assumed approval.]

## Blocking dependency

| Blocked work | Decision needed | Observable unblock condition |
|--------------|-----------------|------------------------------|
| [dependent task only] | [exact choice] | [actual recorded answer or prerequisite] |

## Scope

[Covered authority, independent work that continues and excluded decisions.]

## Acceptance

- [ ] [Actual decision recorded in owning CONTEXT/PROJECT Key Decisions].
- [ ] [Affected obligations reconciled without inventing implementation authority].

## Related links

[Owning decisions, source packet, phase/plan and canonical trackers.]
```

**Producer:** coordinator after preparing a concrete reviewable choice. **Consumers:** the human decision maker and continuation coordinator. Preserve previously supplied authority and settled choices. Record the actual answer before resuming; silence and a recommended option do not decide.

Good: exact blocked task plus a measurable unblock condition; continue unrelated work.
Bad: pause the entire assignment or ask for the same approval again because another workflow step repeats it.

### Security risk

```markdown
## Security concern

[Canonical repository + surface/control + failure mode/remediation scope. For the planned container, state the phase security scope.]

## Affected surface and behavior

[Actual component, trust boundary, actor capability, abuse path and source occurrences.]

## Impact

[Concrete reachable consequence and affected users/data.]

## Risk assessment and lifecycle

- Severity: [critical/high/medium/low, with concrete impact/likelihood rationale and uncertainty].
- Lifecycle / authority: [distinct unresolved/mitigated/accepted/deferred status with actual authority and evidence].
- Mitigation or safe next action: [smallest sufficient full-scope outcome, accountable owner and dependency].

### [Stable per-risk issue BODY heading]

| Entry identity | Canonical risk key | Aliases / occurrences | PLAN / Threat ID | Owner | Scope / acceptance | Assessment / uncertainty | Lifecycle / outcome | Next action | Revision / check evidence | Canonical reference |
|----------------|--------------------|-----------------------|------------------|-------|--------------------|--------------------------|---------------------|-------------|---------------------------|---------------------|
| [stable heading] | [repo + surface/control + failure/remediation scope] | [all sources] | [exact PLAN / ID] | [owner] | [full obligation] | [risk and missing facts] | [distinct state] | [owner/action] | [actual evidence or missing] | [verified URL or Pending reason] |

## Safe evidence

[Redacted source/reproduction, exact source/head revision, actual check evidence and limitations.]

## Requested remediation

[Smallest sufficient full-scope repair, owner and required secure check. Checklist entries link the PLAN assessment/mitigation; standalone issues carry both here.]

## Scope and acceptance

[Exact included obligation, excluded unrelated work and required human/closure decisions.]

- [ ] [Safe remediation outcome with individual scope-complete evidence].
- [ ] [Observable secure check with actual revision/result, or explicit Pending dependency].
- [ ] [Fresh independent non-author issue-link audit].
- [ ] [Actual closure authority when closure is proposed].

## Related links

[Provider-verified BODY anchors, source aliases, PLAN/Threat ID, canonical full-scope tracker, checklist and PR links.]
```

**Producer:** coordinator from PLAN registers or unplanned findings. **Consumers:** executor, reviewer/security-auditor, verifier, independent issue-link auditor and ready/ship gates. The SAME eight-heading variant is required for a standalone Security risk and a planned checklist container. Per-risk stable `###` entries live under Risk assessment and lifecycle; do not create an abbreviated checklist variant.

Only checklist entries link the owning PLAN rather than repeating its assessment and mitigation. Record `PLAN assessment:` and `PLAN mitigation:` with exact owning source/anchor links. Standalone issues require no PLAN and carry their own assessment, mitigation, secure check and next action.

Before per-risk search, lookup exact title `chore(security): phase {phase-id} security checklist` plus `phase-security-checklist` label in both open and closed issues. Multiple/unavailable lookup remains Pending; do not create a duplicate. A closed unresolved match needs separately authorized reopen. New planned risks, including accepted/deferred, use entries unless an existing full-scope tracker remains canonical. Distinct unplanned risks need a standalone tracker or existing full-scope match, never checklist-only tracking.

Preserve each PLAN's six-column register: Threat ID, Category, Component, Severity, Disposition, Mitigation Plan. Preserve every source alias/occurrence and semantic canonical key. Never invent an alternative threat ID/title/label scheme. Existing issue links also receive stable BODY-heading entries. Obtain and verify actual provider anchors; never guess slugs. Rename only with reference repair and readback.

Checked, mitigated, accepted and deferred remain distinct. Each checked item needs its own outcome evidence. Merge, a checked box or accepted/deferred assessment does not authorize closure. Container closure requires complete evidence for every risk plus explicit closure authority. Structural issue validation proves shape only; semantic coverage, safe content, links/provider state and human decisions need actual evidence and independent audit. Read the full [canonical tracking contract](../references/git-workflow.md#canonical-threat-tracking).

Good: reuse a full-scope issue, link it through its stable verified entry, preserve PLAN assessment and record the actual mitigation evidence.
Bad: fabricate an anchor, replace missing provider readback with a heading check, or close the container because the PR merged.

### UAT

```markdown
## Acceptance checklist

- [ ] [Acceptance ID and delivered observable outcome].
- [ ] [Required human judgment with concrete expected result].

## Context

[Actual delivered scope and source SUMMARY/UAT paths.]

## Impact and scope

[Who performs acceptance, included outcomes and exclusions.]

## Build and environment

- Build/version: [exact build]
- Commit: [full actual SHA]
- Entry point: [exact accessible full URL/path/trailing slash, or supplied launcher plus keys]
- Ready environment: [actual prepared environment or BLOCKED prerequisite]
- Safe fixtures: [available safe account/data and cleanup]
- Maintainer record: [separate build/technical preparation evidence reference]

## Steps and expected outcomes

| Step | Action | Expected outcome | Actual outcome / evidence |
|------|--------|------------------|---------------------------|
| 1 | [Exact delivered control/label/action] | [Visible observable result] | pending |
| 2 | [Next exact action] | [Visible observable result] | pending |

Reply `N PASS`, `N FAIL <observation>`, or `N BLOCKED <reason>`.

## Related links

[Source SUMMARY/UAT, exact build/entry point, canonical defects and PRs.]

## Human acceptance

- Status: PENDING HUMAN acceptance
- Reviewer: [actual human or pending]
- Date: [actual acceptance date or pending]
- Decision: [actual words or pending]
- Evidence: [actual response reference or pending]
```

**Producer:** coordinator prepares the protocol from delivered controls, labels, fixtures and exact entry point, then records actual human responses. **Consumers:** the human reviewer, verify-work/audit-uat, gap planning and closure gates. Read the complete [UAT record contract](UAT.md#authoring-contract).

Verify the delivered controls/labels and safe fixtures before publishing instructions. Unavailable prerequisites are BLOCKED; actual product defects are FAIL. Do not invent launch paths or controls. Maintainer build/technical preparation is separate from human product acceptance. Only an actual human decision replaces PENDING HUMAN acceptance; AI cannot waive it. Preserve exact observations, skip/block reasons and unresolved actions.

Good: exact build SHA, accessible URL including required trailing slash, prepared fixture and a visible expected result for each action.
Bad: generic "test the feature", a guessed command/route, reporting a missing server as a product defect, or treating a maintainer smoke check as final human acceptance.

## Consumer and publication guidance

Select the exact canonical variant through supported issue validation/preview interfaces. The parser reads only the selected File Template fenced body; catalog headings and authoring guidance are not body-required. Validate shape, then separately inspect semantics, safe content, source identity and actual provider evidence. Preserve Pending for unavailable evidence. A variant change needs the user's actual intent and matching consumer contract, not a formatter's convenience.
