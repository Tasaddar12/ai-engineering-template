# Git workflow

Use this reference for commits, pull requests, issues, stacks, branch history and source worktree delivery. Follow [worktree sessions](worktree-sessions.md), [path safety](worktree-path-safety.md) and [recovery](worktree-recovery-policy.md) for lifecycle mechanics.

## Roles

| Coordinator | Worker |
|---|---|
| Create or reuse the validated session and isolated worker checkouts; assign exact paths and base. | Inspect the pinned base and repository root before writing. |
| Integrate commits, update shared records, run applicable checks, push and publish PRs or issues. Own rebase, restack and cleanup. | Edit only assigned paths. Preserve unrelated staged or dirty files. |
| Confirm ownership, branch movement and merge evidence before rewriting or removing worktrees. | Return each completed meaningful slice's commit, checks and required summary. |

Before a worker commit:

1. Inspect `git status --short`, `git diff` and `git diff --cached`. Confirm which changes are assigned and owned.
2. Stage only owned paths: `git add -- <exact owned paths>`.
3. Inspect the staged paths and content. Do not include unrelated staged or dirty work.
4. Commit only the named paths, even when the index already contains other changes:

   ```bash
   git commit --only --file <message-file> -- <exact owned paths>
   ```

Never use `git add .`, `git add -A`, repository-wide staging, or stash/reset another person's work. Use this subject and body:

```text
type(phase-plan): concise outcome

Why: problem or goal
Changes: paths and behavior
Verification: exact checks and observed results
```

For numbered phases, use the phase-plan identifier. For quick work or maintenance without a numbered phase, use a stable quick or maintenance identifier such as `quick-YYMMDD-NNN` or `git-workflow`. Include issue references only when applicable and describe breaking changes when present. Workers do not integrate, push, publish, rebase, merge or clean up worktrees.

## Tracking and delivery

- After integrating a meaningful worker slice and passing its applicable checks, push the session branch. Create the first PR with a stable title, `--body-file` and `--draft`; update that same PR and body after later slices.
- On an existing PR, `pr.open --base TARGET` changes the target only when `--base` is explicit. Omit `--base` to preserve the current target. Edits preserve the PR draft state regardless of the creation-only `--draft` option. On creation, omitted `--base` uses the repository default.
- Keep the body current as evidence changes. State the exact revision and actual commands/results, or say final verification is pending. List unfinished acceptance under Known gaps.
- Treat a draft as tracking only. It does not establish verification, readiness, delivery or merge authority.
- Require current passed verification, applicable independent review, documentation and integration evidence, required local and remote checks, and repository protections before calling a PR ready.
- Merge only with explicit user authorization. `workflow.auto_advance` never authorizes implementation, branch rewrites or merge.

## Pull requests

- Read [the pull request template](../templates/pull-request.md) and copy only its **File Template** block into the PR body file. Keep the outcome title stable; update the body as evidence grows. Rewrite the title only when the authorized scope materially changes.
- Ground claims in summaries and the current verification report, not the diff alone. Do not present template prompts as evidence.
- Run `phase_run query pr.validate --body-file PATH` on the reviewed body before
  direct CLI, API or connector publication. Publish that same file content and
  compare the saved body with it after readback. If validation or readback fails,
  repair the body before continuing. Use `pr.open` for validated phase, quick and
  non-phase creates and edits, including body-omitted edits.
- Put each command, result and evidence reference in the template's Verification
  table. Retain its section order and field shapes; record pending work in Known gaps.

## Follow-up issues

- Read the [issue templates](../templates/issues/README.md) and copy the selected file's **File Template** block into the reviewed public body file.
  Authorized execution includes necessary issue creation/update for
  every actionable unresolved problem at normal, deferred or early handoff;
  do not request another issue approval. Honor actual platform permissions and
  sensitive-security reporting requirements.
- Invoking `/capture` authorizes reviewed publication for its new TODO or the single TODO selected by `/capture --list`, in the current repository. It does not authorize unrelated follow-ups, issue closure or implementation.
- For a captured TODO, inspect `todo.issue-preview` candidates across open and closed issues and the related PR context. Runtime provides evidence; it does not perform semantic deduplication.
- Reuse only an actionable matching issue. Linking does not edit or close it. For closed matches, compare closure evidence with the full TODO scope; closed status alone does not prove resolution. Keep mismatches pending and report them. Reopen only with separate authorization or choose an appropriate distinct scope.
- Add only separately reviewed safe context when needed, then preview again or block publication.
- Supported `todo.issue-publish` requires `--variant` with the exact variant name
  from the issue template and validates structural shape before publication.
  For direct issue creates/edits, first run `phase_run query issue.validate
  --variant "Bug" --body-file "${public_body_file}"` (select the actual variant).
  Direct `gh`/API writes bypass the runtime gate; this check does not verify
  working links, delivered UI controls, safe content or actual human decisions.
- Before other issue creation, search open and closed issues, linked PRs and the current PR for duplicates. Keep in-scope defects in the current change; track actionable unresolved discoveries through the phase issue path and retain their canonical URLs in the owned SUMMARY.
- For phase records, amend declarations through `phase.issue-declare`, then use
  `phase.issue-preview`/`phase.issue-publish`/`phase.issue-update`. Keep Bug/UAT
  intent and canonical origin linkage. `phase.handoff` gates completion, and
  `pr.open` automatically gates the phase session's effective body. Pending human
  UAT can accompany advancing code as a followup/plain link, never auto-closing.
- Retire selected folded TODOs only through `phase.reconcile-todos` after matching
  MERGED PR and CLOSED issue readback. Open/unknown results are pending; retry
  reconciliation alone. Resolved inline work needs no new issue; this generic
  exemption does not waive separate threat-record tracking requirements.
- Remove secrets, private logs and sensitive data from publishable text. Close an issue only after acceptance is demonstrated and closure is authorized. Do not use premature auto-closing references for tracking or deferred work.

### Issue type and title

- Use `type(scope): summary` for issue titles.
- Preserve an existing issue's type from its original intent, labels and prior body.
- If UAT reveals a bug, use Bug. If the work is an engineering prerequisite,
  select its engineering issue type.
- Use the [UAT authoring contract](../templates/UAT.md#authoring-contract) for human-test issues.

## Canonical threat tracking

- Create/reuse an issue for every identified PLAN/SUMMARY threat: prose, tables,
  deviations, Deferred/Remaining, pre-existing, mitigated, accepted and deferred.
  New planned risks, including accepted/deferred risks, use one phase security
  checklist issue under the routing below; each risk still needs its own canonical
  reference. Do not expand remediation beyond the plan.
- Keep description, category, component, severity, disposition and mitigation in
  its respective PLAN's existing six-column register. Link the local Threat ID to
  the verified issue or individually addressable checklist entry, or keep the
  ID plus `Pending: <dependency>`.
- Reuse the same issue for duplicate findings in different PLANs. Do not relocate
  or collapse PLAN content into a combined registry.
- Workers return safe requests/SUMMARY. Coordinators update each owning PLAN's
  links before preparation/execution completion; add discoveries to that PLAN.
  Do not add an ordinary approval gate.
- In SUMMARY/PR, link PLAN/Threat ID and issue; show outcomes and Git state without
  repeating the register. Use `None identified` with inspected scope when applicable.

### Identity and publication

1. Keep the stable canonical risk key (repository, surface/control, failure mode/
   remediation scope) and source aliases/occurrences in the Security risk issue
   or its individually addressable planned checklist entry.
   Preserve keys across reruns.
2. First perform the deterministic phase-checklist lookup in the routing section
   below, then search open and closed issues, linked PR/MRs and current PR/MR.
   Compare semantic scope; reuse an actionable full-scope match. Reuse resolved closed matches only
   with matching resolution evidence. For unresolved closed matches, use existing
   reopening authority or record the blocker; do not duplicate. Separate distinct risks.
3. Serialize coordinator writes. Review the [Security risk template](../templates/issues/security-risk.md)
   title/body; run `phase_run query issue.validate --variant "Security risk" --body-file PATH`
   before authorized writes. Never create a TODO or use `todo.issue-publish` for threats.
4. Create/reuse; read back key, aliases, scope, lifecycle, evidence and URL. After
   uncertain creation, search/read back the exact reviewed intent and key before retrying.
   Update each owning PLAN's links and SUMMARY/PR outcomes. Keep unavailable
   publication `Pending: <dependency>`; continue independent work. Never fabricate URLs.

- Apply neutral-link policy to GitLab MRs. Runtime support is GitHub-only; use a
  verified authorized host tool, otherwise retain Pending/publication blocker.

### Planned checklist and unplanned routing

Mandatory preparation/execution reconciliation begins with **Checklist lookup**:
use the exact title `chore(security): phase {phase-id} security checklist` and
label `phase-security-checklist`, with the repository and stable phase id as the
lookup key. Search open and closed issues for that title AND label before any
per-risk semantic search. Reuse the matching container across reruns. Multiple
matches or unavailable lookup stay Pending with the reconciliation dependency;
do not create another container. A closed container with unresolved work requires
existing reopening authority or a recorded blocker. After uncertain creation,
repeat this lookup and read back the exact intended container before retrying.

Then perform the open/closed issue and linked/current PR/MR semantic search above
for every risk. Existing actionable matching trackers remain canonical: a phase
checklist links them without duplicating or replacing their identities. Preserve
stable canonical risk keys and aliases across reruns, including occurrences in
different PLANs. Closed unresolved matches retain the reopening-authority blocker;
creating a new checklist entry must not bypass it.

For ALL NEW planned risks, including accepted/deferred, without an existing
canonical match, distinct entries in this phase security checklist are the
mandatory default canonical references. Create the container only when needed after both searches, using the
exact title and label above. Existing matching issue identities always take
precedence, including a closed unresolved match's reopening-authority blocker.
Use the [consolidated security checklist](../templates/issues/security-risk-consolidated.md) for consolidated risk tracking issues.

**Entry identity:** every risk entry is a stable `###` heading in the checklist
issue BODY, including entries that link an existing canonical issue. Entry URLs
are provider heading anchors. Inspect the saved body/rendered heading and verify
that its provider-supplied anchor URL reaches the exact key, PLAN/ID and content
before using the link; never fabricate anchor slugs. Reuse the matching heading
on reruns and keep it immutable: renaming a heading breaks the link. A necessary
rename requires readback and repair of all affected references before readiness.
Use descriptive link labels without a "(comment)" suffix. An existing issue
remains canonical while its checklist entry points to it; the entry does not
replace that identity. Unavailable heading-anchor verification remains Pending
with its dependency. After an uncertain body update, read back the exact reviewed
key and intent before retrying.

Verify that each entry URL actually addresses that risk at the provider.
If an actionable matching issue already exists, link that issue
as the canonical reference and keep its lifecycle/evidence authoritative. A new
entry is canonical only for a new planned risk with all fields above. Semantic
deduplication, safe separate review, serialized writes, template validation,
readback and uncertain-create recovery apply to the checklist and every entry.
Run `issue.validate` to check structural shape, unique row IDs and matching risk
headings/tasks. Verify per-risk facts, canonical identity, links and outcome
evidence against the provider and source assessments.

A distinct unplanned threat discovered during execution or review needs its own
actionable standalone Security risk issue, or an existing full-scope matching
issue. Add its canonical reference to the owning PLAN and the phase checklist
when one exists; a checklist-only entry cannot replace standalone tracking for a
distinct unplanned risk. Never route threats through TODO publication. The generic
resolved-problem exemption never waives this reconciliation, including findings
already mitigated in the current execution.

Check a checklist item only with individual outcome evidence.

### Safe reporting

- Publish reviewed sanitized tracking without private-channel approval.
- Exclude credentials, private logs, exploit steps and sensitive attachments from
  publishable titles, bodies, documents and links.
- Use an existing authorized restricted channel for sensitive detail. Missing
  private access blocks only that detail/dependent action; continue safe tracking.
- Respect destination visibility. If safe disclosure is impossible, retain the
  publication blocker and accessible restricted canonical reference.

### Assessment, status and closure

- For checklist entries, the owning PLAN assessment records severity
  (`critical|high|medium|low`), impact/likelihood, uncertainty and mitigation in
  its six-column register and associated assessment. Issue entries link that assessment rather than copying
  severity or mitigation. Record owner, scope/acceptance, next action and
  revision/check evidence in the tracking entry. Do not blanket-classify as critical.
- Standalone Security risk issues require no PLAN. Record their severity,
  impact/likelihood, uncertainty, mitigation or safe next action and observable
  secure check directly in the issue, with owner, acceptance and outcome evidence.

| Observed status | Required evidence |
|---|---|
| unresolved | Pending mitigation/check or transfer; disposition alone is not an outcome |
| mitigated | Secure outcome at matching revision; actual check/result |
| accepted | Responsible-party decision/rationale; retain residual risk |
| deferred | Owner, reason and next action; retain unresolved work |

- Distinguish open/unresolved, accepted/deferred and mitigated/resolved outcomes.
  List actual closed issues only with readback and scope-complete resolution evidence.
- Keep neutral issue links until scope-complete mitigation and existing explicit
  closure authority are verified. Audit closing references before publication/merge.
  Never label accepted/deferred as resolved or infer closure from merge.
- Limitation: `issue.validate` checks headings/order only; assessment, dedup,
  disclosure safety and resolution truth require review.

## Issue-link audit

Before merge eligibility, obtain a fresh independent non-author verifier's audit of
the PR/MR body and all issue links. The auditor must not be the author of the
reviewed changes. Compare CONTEXT acceptance, every PLAN threat/checklist identity,
SUMMARY outcomes and actual provider readback of the PR/MR and linked issues.
Ordinary linked follow-ups need the same audit as security records. This is a
semantic/provider review: structural `issue.validate` success does not prove it.

The independent result must check:

- Actionable link destination and full scope/acceptance; verified URLs must reach
  the intended issue or individually addressable checklist entry. Detect omitted
  or duplicate tracking, planned-checklist coverage and separate standalone
  tracking for distinct unplanned risks. Reuse existing matching canonical issues.
- Per-risk key/aliases, PLAN ownership, assessment/uncertainty, owner, actual
  lifecycle/outcome, revision/check evidence and safe destination visibility.
  Preserve unresolved, accepted/deferred and mitigated/resolved distinctions.
- Neutral versus closing references across the actual body/links and provider
  semantics, including GitLab neutral-link policy. Closing references need
  scope-complete resolution evidence and existing explicit closure authority.
  Never infer closure from merge, checked checklist items or accepted/deferred status.

Capture reviewed source revision, actual PR/MR head SHA, PR/MR body/link snapshot,
verified URLs, provider readback evidence (including observed state and when it
was read), and
unresolved findings/dependencies in the independent result. Missing required
readback or an unverifiable link is a gap with a dependency, never a pass. An
unpublished body or unavailable provider may be reviewed provisionally, but its
required provider readback remains Pending. Use a verified authorized host tool;
otherwise keep the Pending dependency and continue independent work.

The verifier owns this audit in verify-work and ship. A code-reviewer may provide
an optional supplementary audit. If the required audit is missing or stale, the
coordinator dispatches a fresh non-author verifier with the current source/head,
exact proposed or published body/link snapshot, CONTEXT, PLANs, SUMMARYs and
timestamped provider readback. The verifier obtains/validates actual provider
readback and returns the packet above. Join the result before using it as a gate;
an unpublished body keeps provider confirmation Pending. After publication,
recheck the actual saved body/links and linked issue states against the packet;
dispatch fresh applicable verification for changed or missing evidence.

Material changes to links, body, risk outcomes or source invalidate the affected
audit. Obtain fresh applicable independent evidence before claiming ready; apply
[verification currentness](verification-evidence.md#coordinator-currentness-check)
to source evidence and compare the current provider body/link snapshot as well.
Preflight/body generation may support truthful tracking drafts with pending
audit findings under the existing delivery policy; they do not establish merge
eligibility. Before merge, require the current independent audit and last provider
readback to match the proposed body/links and source. Reconcile changed or
unavailable readback first. The audit grants no new merge or issue closure authority.

## Stacks

- Create a stacked PR only for a real dependency. Record `stackParent`, `Target`, `DependsOn` and `OwnChangeBoundary`. Target the parent branch while it is open and show only the child's delta. Give independent changes independent PRs.
- Merge bottom-up only after each PR's gates pass and the user authorizes each merge.
- After a parent lands, record the commit tips and target branch separately: `OLD_PARENT_TIP` is the saved old-parent commit, `NEW_PARENT_TIP` is the commit at the new target, and `NEW_PARENT_BRANCH` is that target's branch name. Set `CHILD` to the child branch.
- Only the coordinator may restack an explicitly authorized child on a clean owned worktree after checking upstream movement. Rebase only its own commits:

  ```bash
  git rebase --onto "$NEW_PARENT_TIP" "$OLD_PARENT_TIP" "$CHILD"
  ```

  The child's own-change boundary is `OLD_PARENT_TIP..CHILD`. Retarget its existing PR with `pr.open --base "$NEW_PARENT_BRANCH"`; this option takes the branch name, not the commit tip. Then inspect the diff, rerun affected checks and review, and update stack and evidence fields. Publish rewritten history only with the exact expected-tip lease below. Do not replay parent commits already included by a squash or rebase merge.

## Branch rewrites

- Only the coordinator may rebase or restack an explicitly authorized owned branch. Check ownership, a clean worktree, upstream movement and the saved own-change boundary first.
- Fetch and capture the exact remote tip before rewriting:

  ```bash
  git fetch origin
  EXPECTED=$(git rev-parse refs/remotes/origin/branch)
  ```

- Inspect and test the result, then lease the exact branch ref against that captured SHA:

  ```bash
  git push --force-with-lease=refs/heads/branch:$EXPECTED origin HEAD:refs/heads/branch
  ```

- Never use plain force or a lease without an expected value. If the lease is stale or the remote moved unexpectedly, stop, inspect the new state and preserve work.
- This manual branch rewrite is separate from `delivery.merge_method: rebase`, which selects GitHub's PR merge strategy.

## Sessions and worktrees

- Reuse a session only after validating matching ownership, task and base. Create executor checkouts through the existing isolation route.
- Preserve dirty, unmerged, blocked, unowned or unclear worktrees and ignored data. Remove only owned clean worktrees with repository evidence that their work integrated or merged.
- Limit the planning-record-only exception to the named runtime-owned planning workflows in [worktree sessions](worktree-sessions.md). Reusable `.ai` instructions, templates or tooling, and changes mixed with source use the source session and PR path. Template maintenance does not broaden the exception.
- `auto_advance` may advance already-authorized transitions; it never waives implementation authority, merge confirmation or verified ship gates.
