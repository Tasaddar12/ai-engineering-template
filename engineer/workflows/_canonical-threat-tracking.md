# Reconcile and publish canonical phase or quick threats

Read `engineer/references/git-workflow.md#canonical-threat-tracking` and the complete Security risk variant in `engineer/templates/issue.md`. This procedure applies their policy; the reference owns identity, lifecycle and closure authority, and the pinned runtime owns argv/schema. Do not infer mitigation, acceptance or closure from issue state, a checked entry or a merge.

## Select the real scope

For a phase, use phase.threat-review/preview/publish/audit with its actual phase number and the phase-local PLAN. For a quick task, use quick.threat-review/preview/publish/audit with the real quick ID and quick-local PLAN; never fabricate a phase. Both routes use the full JSON, body, matching, lifecycle and provider-anchor contract below. Phase containers retain the original phase title/label. Quick containers use `chore(security): quick {quick-id} security checklist` and label `quick-security-checklist`; kind-aware identity prevents phase/quick collisions.

## Collect actual PLAN evidence

Read every applicable PLAN's complete six-column register in place:

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| Actual stable ID | Actual category | Exact affected component | Evidence-backed severity | Current lifecycle and canonical reference | Concrete mitigation and acceptance |

The PLAN remains the owner of severity and mitigation. Preserve threat identities across phase renumbering. Establish a stable canonical risk key from repository, affected surface/control, failure mode and full remediation scope; similar titles alone do not establish equivalence. Read actual summaries, review/security findings, revisions and check evidence. Include every new planned risk, including accepted and deferred exposure, rather than omitting risks that do not require immediate code changes. Distinct unplanned risks follow the standalone route.

## Prepare the complete entries file

Create a nonempty JSON array and retain it as the complete reviewed input. Each entry contains these actual runtime fields:

- `key`: established stable canonical risk key.
- `id`: stable entry identity.
- `heading`: stable issue-body heading, preserved on reruns.
- `plan`: exact PLAN filename local to the selected real phase or quick scope.
- `threat_id`: exact ID from that PLAN's six-column register.
- `planned`: a real boolean distinguishing planned from unplanned risk.
- `owner`: accountable owner or explicit unresolved owner dependency.
- `scope_acceptance`: full affected/remediation scope and observable acceptance.
- `assessment_uncertainty`: severity reasoning and explicit uncertainty.
- `lifecycle_outcome`: unresolved, mitigated, accepted or deferred, with its actual evidence and limits.
- `next_action`: concrete safe next action and human decision dependency when applicable.
- `revision_check_evidence`: exact source/tested revision, relevant commands/results or explicit pending evidence.
- `aliases_occurrences`: actual source aliases and occurrences, preserving identity across files and phases.
- `match_review`: `disposition: existing | no-match | pending`, cited `evidence`, complete `reviewed_issue_urls` and `reviewed_pr_urls`, and `url` for an existing full-scope canonical match. Include `heading_url` only when it was read from an actual rendered provider anchor.

For a new unplanned risk, also supply its complete `standalone_body`. Keep these exact ordered `##` headings: Security concern; Affected surface and behavior; Impact; Risk assessment and lifecycle; Safe evidence; Requested remediation; Scope and acceptance; Related links. Fill all semantic content: key, aliases, severity rationale/uncertainty, owner, observed status, mitigation or safe next action, and matching resolution/check evidence or an explicit Pending dependency. A checklist-only entry cannot satisfy an unplanned-risk route.

Preserve safe evidence: no credentials, personal data or exploitable production payloads. An unavailable observation is Unknown/Pending with a concrete owner/action, not fabricated evidence. Structural validation establishes shape only; independently inspect semantic scope, safety, matching, mitigation and actual human acceptance.

## Review canonical matching and deterministic container identity

Run `engineer_run query phase.threat-review "${PHASE_NUMBER}" --entries-file "${ENTRIES_FILE}"`, or `engineer_run query quick.threat-review "${QUICK_ID}" --entries-file "${ENTRIES_FILE}"` for a real quick task. Review its complete exact-container lookup, each risk's existing full-scope issues, current and linked PR candidates, uncertainty and pending reasons. Search both open and closed canonical trackers. A genuinely equivalent actionable existing identity takes precedence over a new issue.

Planned phase risk publication uses exactly one container titled `chore(security): phase {padded-phase-id} security checklist` with label `phase-security-checklist`. Multiple matching containers, unavailable lookup, ambiguous remediation scope, an unresolved closed match, or a closed checklist remain Pending. These verbs never reopen or close issues; reopening requires independent actual authority. Do not duplicate a closed unresolved risk to escape that boundary.

Every planned risk receives its own stable `###` heading under the container's Risk assessment and lifecycle section, including entries linking an existing canonical issue. Preserve all eleven entry fields: Entry identity; Canonical risk key; Aliases/occurrences; PLAN/Threat ID; Owner; Scope/acceptance; Assessment/uncertainty; Lifecycle/outcome; Next action; Revision/check evidence; Canonical reference. The container itself retains the full eight-heading Security risk variant.

## Preview, publish and read back

Only after the match review is ready, run:

```bash
engineer_run query phase.threat-preview "${PHASE_NUMBER}" --entries-file "${ENTRIES_FILE}" --variant "Security risk"
```

For a quick task use `engineer_run query quick.threat-preview "${QUICK_ID}" --entries-file "${ENTRIES_FILE}" --variant "Security risk"` instead, preserving the same exact inputs and reviewed kind-aware scope.

Inspect the complete returned container/standalone title, body, label, source/template/origin/provider identity, entry relationships and content-bound token. Pending review is not publication permission. Any source, template, origin, body or disposition change requires a new preview.

Publish once with exactly those reviewed inputs:

```bash
engineer_run query phase.threat-publish "${PHASE_NUMBER}" --entries-file "${ENTRIES_FILE}" --variant "Security risk" --preview-token "${PREVIEW_TOKEN}"
```

For a quick task use `engineer_run query quick.threat-publish "${QUICK_ID}" --entries-file "${ENTRIES_FILE}" --variant "Security risk" --preview-token "${PREVIEW_TOKEN}"` instead. A phase token cannot authorize a quick mutation or the reverse.

The runtime consumes the token before provider writes. Read back exact published content and preserve partial results in the durable preview record. An uncertain create must be searched/read by exact container identity or standalone title and full body before retry; when the result cannot be proved, preserve the consumed attempt and report Pending. Never create another issue to escape an uncertain first mutation.

## Link only real provider targets and obtain independent audit

Update each PLAN's canonical link from the returned actual issue or entry target. Provider-rendered anchors are authoritative: never compute a slug from a heading. Missing anchors remain Pending. Preserve headings on reruns; a heading change requires repairing every reference and reading back the new target before readiness.

Run `engineer_run query phase.threat-audit "${PHASE_NUMBER}"`, or `engineer_run query quick.threat-audit "${QUICK_ID}"` for the selected quick scope, when audit execution is permitted, and obtain a fresh independent non-author issue-link audit of the exact source/head and provider body/link snapshot. It must inspect every PLAN/Threat ID target, canonical key, aliases, owner, lifecycle/evidence, rendered heading and current/linked PR relationship. A deferred audit remains pending and blocks dependent readiness. `phase.handoff` and PR readiness enforce the actual targets; they do not replace the independent semantic audit.

Checked checklist entries need individual scope-complete outcome evidence. Accepted/deferred risk remains distinct from a demonstrated mitigation and never automatically passes acceptance. Close a container or standalone issue only with complete scope evidence and actual explicit closure authority. Continue independent authorized work while unresolved dependencies remain `Pending: reason; owner; next action`.
