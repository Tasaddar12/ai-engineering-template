# Canonical issue template

Read [Git workflow](../references/git-workflow.md) before creating or editing an issue. The coordinator owns provider mutation. Use an exact body file and validate provider readback; do not claim an uncertain publication succeeded.

## Required metadata

- Kind: defect | threat | UAT | scope | maintenance.
- Source: repository-relative artifact path, stable finding ID and source revision.
- Canonical relationship: existing issue URL or new issue request; search before creating a duplicate.
- Severity and authority: observed impact and the requirement, acceptance, decision or rule it violates.
- Status: open / resolved with evidence / Pending with the concrete blocker.

## Body template

```markdown
## Problem

[Concrete trigger, expected result and actual result.]

## Source and authority

- Finding ID: [stable ID]
- Source artifact: [path and section]
- Revision: [full SHA]
- Requirement / acceptance: [ID and exact obligation]
- Decision reference: [owning Key Decisions or CONTEXT entry, if relevant]

## Reproduction

1. [Precondition and fixture].
2. [Exact action / argv / API input].
3. [Observed result].

## Evidence

[Bounded logs, test output, screenshot or source locations. Redact secrets. Distinguish observed facts from hypotheses.]

## Impact

[Who is affected, failure mode, severity and scope.]

## Proposed correction

[Smallest sufficient repair; label uncertain root causes as hypotheses.]

## Acceptance

- [ ] [Observable behavior and exact expected result].
- [ ] [Regression evidence at the corrected revision].
- [ ] [Required human acceptance, if applicable].

## Relationships

- Phase / plan: [IDs]
- Related issue / PR: [canonical links]
- Threat / UAT action: [stable IDs or none]

## Resolution evidence

[Pending until actual fix, executed checks and required human acceptance are available.]
```

## Defect

Include a minimal reproduction, observed failure, expected contract and environment. Do not assert a root cause without evidence. Preserve the original failing revision and correction evidence.

## Threat

Use stable `T-{phase}-NN` IDs across PLAN, SUMMARY, review and verification. Include the trust boundary, actor capability, abuse path, impact, mitigation and behavioral evidence. A grep hit is discovery, not proof that the control resists abuse. Do not close a threat merely because mitigation source exists.

## UAT

Include the source UAT path, action number, acceptance ID, exact entry point, fixtures, expected result and the human's actual observed words. Preserve blocking/skipped reasons and severity. A resolving plan must exist with a matching SUMMARY before setting `resolved_by` and `resolved_at`; reconciliation does not fabricate final human acceptance.

### UAT example

```markdown
## Problem

Action 2 submits a new comment, but the list updates only after refresh.

## Source and authority

- Finding ID: UAT-04-02
- Source artifact: .planning/phases/04-comments/04-UAT.md, action 2
- Revision: [actual failing SHA]
- Acceptance: submitted comments appear immediately in the current list

## Reproduction

1. Open the comments fixture post as its authorized author.
2. Submit "A new comment" using the composer.
3. Observe the old list until manual refresh.

## Evidence

Human reported: "works but doesn't show until I refresh the page".
Root cause remains under diagnosis.

## Acceptance

- [ ] The new comment appears immediately without refresh.
- [ ] Existing comments and count remain correct.
- [ ] Human retest and final acceptance are recorded in the source UAT.
```

## Scope and maintenance

Identify authorized outcome and exact path ownership. Link any required scope decision; an issue does not authorize phase implementation. Record deferred work only when authorized and preserve its owner and next action.

## Publication contract

1. Read the source artifact and its current digest.
2. Search existing issues for the stable finding ID and the concrete behavior; reuse the canonical issue when present.
3. Prepare a complete body using the relevant variant above.
4. Call `phase.issue-preview N ARTIFACT.md FINDING_ID --title TITLE --body-file FILE` (or `todo.issue-preview` for a captured todo).
5. Review returned source, snapshot digest, title and body. Publish/update with the returned `--preview-token` and identical arguments.
6. Read back the provider result before linking the issue in the source. Inspect an uncertain result before retrying.
7. Keep the source artifact, canonical issue and eventual PR consistent. Do not silently discard findings or equate issue closure with acceptance.
