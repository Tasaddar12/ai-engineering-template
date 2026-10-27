# Canonical Git workflow

The coordinator owns integration, shared records, provider mutations and publication. Workers commit exact owned slices and return evidence. Read the complete [issue](../templates/issue.md) and [pull request](../templates/pull-request.md) templates before any creation or edit.

## Commit each meaningful slice

Confirm repository root, branch, input revision and exact ownership before writing. Stage exact paths; never `git add .` or `git add -A`. Include required agent summaries in their owned slice unless the user's maintenance assignment explicitly excludes summaries. Preserve unrelated staged, dirty and untracked work.

Use a descriptive `type(scope): outcome` subject and required body:

```text
fix(08-02): preserve submitted comment visibility

Why: the list retained stale state after a successful submission.
Changes: refresh the affected subscription and add the regression evidence.
Verification: exact tested SHA, argv and observed result; pending items remain explicit.

Rows: assigned reconciliation IDs when applicable
```

Types: `feat` new behavior, `fix` defect repair, `test` test-only RED, `refactor` behavior-preserving cleanup, `perf` performance, `docs` documentation/records, `chore` configuration/tooling.

### Per-task formats and TDD

Commit a completed task immediately. Keep RED, GREEN and optional REFACTOR distinct when required by the assignment:

```sh
git add -- src/tests/test_comments.py
git commit -m "test(07-02): capture missing immediate comment visibility" -m "Why: reproduce the observed stale list." -m "Changes: add the targeted failing assertion." -m "Verification: actual RED record and semantic assessment."
git add -- src/comments.py
git commit -m "feat(07-02): refresh submitted comments" -m "Why: satisfy the captured behavior." -m "Changes: update the subscribed list after submission." -m "Verification: actual GREEN command, revision and result."
```

A commit prefix is not RED evidence; read [TDD](tdd.md) for format adapters, actual assertion failure and commit ancestry. Do not bypass hooks silently. If the user defers all check execution, preserve that order and label validation pending.

A plan-completion metadata commit uses `docs(NN-MM): complete outcome` and contains only the assigned complete SUMMARY and coordinator-owned bookkeeping where authorized. Initialization/planning/research artifacts are committed as meaningful reviewed slices under their producing workflow; do not postpone durable planning evidence merely because it is intermediate.

## Delivery and authority

Push only when delivery is authorized. Open a draft on the first push and keep its title/body current after every slice. Stacked work uses the actual parent branch through `pr.open --base REF`; leave every PR open unless the user authorizes merging. An approved design, planned phase, draft PR, passed check or completed phase does not authorize the next phase or merge.

`engineer_run query pr.open BRANCH --title TITLE --body-file FILE --base REF` validates the prepared description and provider readback. Attach a created PR to the chat through the host artifact tool. `pr.ready BRANCH --phase N` requires current verification; `pr.merge BRANCH --phase N --confirm` additionally requires explicit human merge instruction and provider checks. Genuine quick delivery uses `--quick ID`, never a fabricated phase ID.

## Issue creation and updates

1. Read the source artifact, exact stable finding identity, current digest and relevant acceptance.
2. Search existing open and closed canonical trackers for the same behavior and full remediation scope. A similar title alone is not equivalence.
3. Prepare the complete variant in [issue.md](../templates/issue.md) and validate safe content, exact source references, authority, reproduction, acceptance and relationships.
4. Use `phase.issue-declare N ARTIFACT.md` to inspect the declared entries and snapshotDigest when the workflow requires it. Apply entries only with the current expected digest.
5. Preview the exact title/body/labels with `phase.issue-preview N ARTIFACT.md FINDING_ID --title TITLE --body-file FILE --variant "Bug" --no-match`; use the selected exact canonical variant, or --existing-issue for a verified reused tracker; a todo uses `todo.issue-preview`.
6. Inspect the returned source, finding, title/body, snapshotDigest and content-bound preview token. Publish/update with identical inputs and `--preview-token TOKEN`. The token is consumed before provider mutation; an uncertain provider response requires inspection before retry.
7. Read back actual provider title, body, labels, state, number and URL before recording the canonical link locally. Validate content and relationship, not merely HTTP success.
8. Keep neutral references distinct from closing references. Use a closing keyword only for an actually resolved full scope, and preserve required human acceptance.

`issue.validate` or another structural validator proves shape only. It does not prove safe content, semantic coverage, link access, provider state or human decisions.

## Canonical threat tracking

### Identity and PLAN ownership

Keep each PLAN's complete six-column threat register in place:

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-{phase}-NN | [STRIDE/category] | [actual surface] | [assessment] | [mitigate / accept / defer / transfer with authority] | [exact mitigation and canonical reference or Pending reason] |

Continue IDs after the highest existing phase register; preserve source aliases and occurrences when numbering changes. Reserved `T-{phase}-SC` remains distinct. Never move or collapse a PLAN's register into a phase-wide summary. The PLAN owns its assessment/mitigation; a worker reports actual Threat Outcomes and Pending requests without editing shared PLANs. The coordinator reconciles canonical links and dispositions.

Canonical risk identity is **repository + surface/control + failure mode/remediation scope**, not a newly invented ID scheme. A stable threat/finding ID locates a source occurrence; semantic deduplication determines whether occurrences describe the same full risk. Preserve every alias and source occurrence.

### Matching evidence and provider authority

Keep a stable canonical risk key and all aliases/occurrences across reruns. A closed match is reusable only when its semantic scope and matching resolution evidence cover the entire obligation; otherwise retain the reopening-authority blocker. Inspect uncertain creation against the exact reviewed intent before retrying. Runtime issue publication is GitHub-only; on another provider a verified authorized host tool must preserve the same complete template, matching, preview/readback and authority contract. If that route is unavailable, retain a Pending/publication blocker. Never invent a URL or change provider to bypass a closed unresolved identity.

### Deterministic planned-risk container lookup

Before per-risk search, look up the exact repository/phase-scoped checklist container in both open and closed issues:

- Title: `chore(security): phase {phase-id} security checklist`
- Label: `phase-security-checklist`

Exactly one matching container is required. Multiple matches, unavailable search or ambiguous provider results remain Pending and prohibit creating a replacement container. A closed unresolved match requires separately authorized reopen; never bypass it through a new container or duplicate entry.

Then search each risk by canonical semantic key and full remediation scope. Existing actionable full-scope trackers remain canonical and are linked from a checklist entry instead of duplicated. All NEW planned risks without such a tracker use checklist entries, including accepted/deferred risks. Distinct UNPLANNED threats require an existing full-scope tracker or a standalone Security risk issue; checklist-only tracking is insufficient.

### Planned checklist entry schema

Every risk entry is a stable `###` heading in the **issue body**, including entries that link an existing issue. Keep these exact 11 columns/fields with the entry:

| Entry identity | Canonical risk key | Aliases / occurrences | PLAN / Threat ID | Owner | Scope / acceptance | Assessment / uncertainty | Lifecycle / outcome | Next action | Revision / check evidence | Canonical reference |
|----------------|--------------------|-----------------------|------------------|-------|--------------------|--------------------------|---------------------|-------------|---------------------------|---------------------|
| [stable BODY heading] | [repo + surface/control + failure/remediation scope] | [all source identities] | [exact PLAN / ID] | [accountable owner] | [full obligation] | [severity, confidence, missing facts] | [unresolved / mitigated / accepted / deferred] | [concrete owner/action] | [actual revision and check or missing] | [verified provider URL or Pending reason] |

The heading is durable identity. Obtain its actual provider heading anchor and verify the URL targets the exact stable key, PLAN/ID and content. Never fabricate a slug from a guessed heading. Preserve headings on reruns; a necessary rename requires repairing every reference and provider readback. Labels are descriptive; do not use a `(comment)` suffix or pretend comment URLs are stable issue-body entry anchors.

Checklist entries link the PLAN assessment and mitigation. Standalone issues carry their own assessment, mitigation and secure-check evidence. A container link without the exact verified entry or canonical tracker does not cover an individual risk.

### Standalone Security risk issue

Use these headings in this order and fill the complete semantic content:

1. `Security concern` — concrete risk and canonical identity.
2. `Affected surface and behavior` — component/control, actor capability, boundary and actual behavior.
3. `Impact` — reachable consequence and affected users/data.
4. `Risk assessment and lifecycle` — severity, uncertainty, authority and distinct unresolved/mitigated/accepted/deferred state.
5. `Safe evidence` — redacted reproduction, actual source/head revision, observed behavior and check evidence.
6. `Requested remediation` — smallest sufficient full-scope repair, owner and required secure check.
7. `Scope and acceptance` — exact in/out boundary and measurable completion, including required human decisions.
8. `Related links` — verified source, aliases, PLAN/Threat ID, canonical issue/checklist entry and PR relationships.

Heading presence alone is insufficient: verify source identity, full-scope coverage, safe content, actual lifecycle evidence and provider state. Do not invent threat titles or labels beyond the established container identity.

### Lifecycle and closure

Keep unresolved, mitigated, accepted and deferred distinct. Checked checklist items require individual outcome evidence; a checked box is not itself that evidence. Accepted/deferred state, merge, issue closure or a checked item never authorizes closure or passes acceptance.

Close a checklist container only when every risk has scope-complete evidence **and** actual explicit closure authority exists. Preserve remaining exposure and required human decisions. Closed unresolved trackers need authorized reopen rather than duplication. Missing provider access or evidence remains `Pending: reason; owner; next action`, blocking dependent readiness/publication without inventing links or abandoning independent work.

### Safe reporting

Publish sanitized evidence only after checking destination visibility. Keep exploitable details, secrets and private data in the authorized restricted channel; safe public text states impact and the next action without exposing a reproduction payload. When disclosure needs private-channel approval, prepare the redacted issue and record that dependency. Missing access or visibility authority blocks only the dependent publication, not independent work. A same-execution fixed-work exemption for ordinary findings never waives threat canonicalization, safe separate review, serialized writes, template validation, uncertain-create recovery or required issue-link audit. Never route threats through a generic fixed-work exemption.

## Issue-link audit

The verifier owns this audit and must not be the author of the issue/PR body. A code-reviewer may supply optional supplementary evidence; it does not replace a fresh non-author verifier. Join the result before readiness.

Before readiness, obtain a fresh independent non-author audit of the actual source/head SHA and provider snapshot. The packet contains:

- Source/head SHA and exact source artifact identities.
- Actual issue body plus link snapshot, with provider readback timestamps and state.
- `verifiedURLs` proving each BODY heading/canonical reference resolves to the exact risk key, source PLAN/ID and content.
- Coverage of every planned and unplanned canonical risk, including aliases and full remediation scope.
- Neutral references versus closing references and their authority/evidence.
- Safe-content, lifecycle, human-decision and closure findings, with Pending for unavailable evidence.

Audit CONTEXT acceptance, every PLAN threat/checklist, SUMMARY outcomes, PR links and ordinary linked follow-ups. Find omitted risks, duplicate tracking, wrong planned-checklist versus standalone routing, and unsafe destinations. `issue.validate` proves shape only. Check neutral versus closing keywords on GitHub and GitLab; never infer closure from merge or issue state. Every closing relationship needs scope-complete evidence and explicit closure authority.

Preserve unresolved findings/dependencies as Pending, never a pass. Changed source, head, body, links, canonical lifecycle or provider state invalidate affected evidence. Obtain a fresh applicable audit or a documented coordinator currentness check against the exact new snapshot; do not silently reuse the old packet. After publication, recheck actual PR body/head and linked issue states. Before merge, retain the last provider readback and timestamp and revalidate changed inputs; with no new merge authority, keep the PR open.

The coordinator joins all findings before ready/ship. An author's structural validation is not the independent audit; inaccessible provider evidence cannot silently pass. Preserve exact audit revision and readback evidence for runtime handoff/readiness checks.

## Provider uncertainty and retries

After an uncertain mutation, inspect provider state using the stable source identity before retrying. Never create duplicates to escape a failed search or token. Re-preview after any body/source/digest drift. Report actual success, failure or uncertainty and continue independent authorized work.

## Supported repository topology

The runtime operates on the current Git project and explicit isolated worktrees. Upstream multi-repository `sub_repos` commit automation and dynamic model routing are intentionally unsupported. A discovered submodule is not authority to mutate or publish another repository; assign it explicitly if the user requests that work.

## Canonical variant arguments

Select Bug, Enhancement, Decision required, Security risk or UAT exactly. Issue validation/preview/publication bind `--variant NAME`; all preview/publish requests declare either an actual verified `--existing-issue` relationship or `--no-match` after deterministic lookup. Security tracking uses --variant "Security risk" for both planned checklist and standalone issues. Do not use no-match to bypass unavailable/ambiguous lookup or an unresolved closed match. The complete selected fence owns structural headings; independent semantic/provider/human evidence remains mandatory.
