# Verification evidence and report currentness

`phase_run query verification.run-checks` runs the configured deterministic
commands and returns their ordered results. Each successful check can carry a
receipt identifying its command, declared source inputs, environment, tested
revision and captured output. Reuse a passing result only when its receipt is
valid for the current invocation's revision and declared inputs. Include
generated dependency/build data in the check's declared source paths or provide
a project-managed source stamp. Declare relevant environment names, but never
put secret values in the receipt. Volatile external state without a stable source
or environment stamp cannot be safely reused; set `reuse: false` for that check,
or disable reuse with `verification.reuse: false`. When an input, configuration
or command changes, or a receipt is missing or invalid, run the check again. See
the runtime README for the exact check configuration fields. Report command
results and receipt identity; do not infer a pass from an earlier log. AI
diagnosis is useful for failed or ambiguous checks, not for rechecking an
unambiguous successful result.

With no explicit `sources`, the check key covers all tracked and nonignored
untracked repository inputs, including planning records. With no explicit
`environment`, it covers the full inherited environment; configuration is also
part of the receipt key. There is no automatic planning-record exclusion. To reuse
checks across bookkeeping commits, adopting projects must declare the actual
source, test, dependency and configuration paths plus relevant environment names.
Ignored dependencies consumed by a check must be declared too; otherwise disable
reuse for that volatile check.

## Independent review and evidence packets

Every source-changing phase receives one independent code review of its final
integrated source snapshot. Store its result with a schema-1 review request and
result, then let verify-work and ship look up and consume that evidence. A review
key hashes the request and actual committed manifests for its declared paths,
requirements, configuration and runtime validator; it excludes the commit SHA so
identical review inputs may be reused across revisions with identical inputs. The
review request still names a full committed revision. Recording requires a clean,
stable worktree and hashes that immutable commit; lookup requires the requested
revision to equal clean `HEAD`. Scope expands to a manifest of literal tracked
paths; additions and deletions are part of that manifest. Successful review
packets must account for every path in the expanded scope and carry validated
reviewer provenance.

Keep these states separate: `never_run` means no packet exists, `failed` means an
attempt failed, and `incomplete` means the packet does not establish its contract.
Only validated `passed` review evidence is reusable as a completed review. A
changed source/requirement/configuration input or unresolved finding invalidates
the affected portion; request a bounded review of the uncovered delta and retain
prior findings. Do not dispatch a fresh full code review merely because verification
or shipping started.

Scouts use the same schema-1 evidence store. Their content-addressed request keys
include the question, scope, requested output schema/fields, declared inputs and
configuration, with hashes of the actual committed inputs and runtime validator.
Reuse a packet only when those inputs match; compatible questions may be batched.
Absence claims are valid only when the packet records the complete declared
search-scope manifest. Preserve the inspected revision, input hashes and
validation provenance in every accepted packet. A scout extracts, classifies,
summarizes or proposes a transformation; it does not decide correctness or
acceptance.

Verification reports are read-only specialist output. The verifier examines the
product/source revision and returns a complete external report. The coordinator
persists that report at the phase's tracked `NN-VERIFICATION.md` path and commits
that file. `verification.status` reads report metadata; it does not enforce
currentness. The report's `revision` remains the exact commit inspected by the
verifier. The coordinator must not replace it with a later report or bookkeeping
commit's hash, which the verifier never examined. Runtime currentness consumes a
validated bounded-transition receipt when an approved success-record commit
follows that inspection.

## Coordinator currentness check

Use `phase_run query verification.currentness <phase>` in both `/verify-work`
report reuse and `/ship` preflight. Let
`tested_revision` be the report's `revision`, `HEAD` be the current session tip,
and `report_path` the exact repository-relative path of this phase's
`NN-VERIFICATION.md`.

1. Require a clean worktree, including untracked files. Dirty state means the
   delivered tree differs from the tested commit, so the report cannot be reused.
2. If `tested_revision` equals `HEAD`, the report is current.
3. Otherwise, require `tested_revision` to be an ancestor of `HEAD` and inspect
   every intervening single-parent commit in order. Exact report-only commits may
   change only this phase's tracked report path. A success-bookkeeping commit is
   current only when a valid `verification.validate-bookkeeping` receipt binds
   that exact before/after pair, the same original source report and its validator.
   The runtime replays the allowed schema transition; merge commits, source edits
   (including edit-then-revert), unrelated paths or missing receipts fail closed.
4. If ancestry is missing, a commit is not an approved report or bookkeeping
   transition, or repository state is dirty, require affected re-verification. Do
   not change the report's inspected revision to make currentness pass.

The equality case preserves the exact-revision fast path. Approved commits after
inspection are limited to exact report publication and the deterministic
success-record transition described above. `verification.status` exposes report
metadata only; `verification.currentness` enforces these rules.

## Final-report lifecycle

The verifier is read-only and returns an external report; the coordinator alone
writes and commits the tracked phase report. On the initial pass, start the
provisional verifier, configured checks and applicable independent specialists
together against one frozen revision. The provisional verifier receives no
future results and cannot finalize status. Join the whole batch, then resume the
verifier with check receipts/results and bounded specialist findings so it can
reconcile shared evidence and inspect only gaps or conflicts.

If that joined result provisionally passes, perform and commit phase-completion,
requirement-closure and session/roadmap bookkeeping before final reconciliation.
Validate the bounded success-record transition deterministically against the
captured before/after revisions. Only the direct child, clean tree and nonempty
delta limited to STATE, ROADMAP and REQUIREMENTS can be accepted. Existing phase
plans and checklist may advance; requirement IDs, phase assignments and narrative
stay fixed; progress and completion dates must derive from the resulting phase
counts; STATE may update only the established session/progress fields while
preserving phase and narrative. The prior passed source report must include
acceptance and requirements-completed IDs. Every completed phase plan needs a
committed structured SUMMARY with matching plan/phase and complete status,
nonempty body, valid coverage entries and matching acceptance/requirement IDs;
each completed requirement needs coverage. A legacy prose summary or required
human judgment cannot pass this deterministic path and needs a bounded specialist
review. Rerun only checks whose declared inputs changed.
A discrepancy receives a bounded decision-owner inspection of that delta, not a
broad replacement verifier. Preserve the original verifier's inspected revision
and let currentness consume the exact validation receipt chain. Never retag the
report to a later commit.

The report-only and success-record rules permit subsequent ship preflight to
consume the report for the preceding inspected revision. `verification.status`
only exposes metadata; `verification.currentness` validates the receipt chain. A
refresh-only verification does not repeat completion/requirement/session writes
and does not invoke `/ship` again. A source repair invalidates evidence and starts
a new verification batch; it is not a report-only publication.

## Compensating a failed final verification

Success bookkeeping is provisional until `verification.validate-bookkeeping`
validates the allowed transition and `verification.currentness` accepts its
receipt. Before changing any success records, require a clean worktree confirmed
with `git status --porcelain --untracked-files=all` and save
`pre_bookkeeping_revision=$(git rev-parse HEAD)`. Save the exact new commit from
the coordinator's bookkeeping commit as `bookkeeping_commit`.

If final reconciliation returns `gaps_found` or `human_needed`, and only when
that coordinator-created bookkeeping is the direct child of the saved revision,
the coordinator may compensate it with a narrow Git revert. Require all of these
guards before reverting:

1. `git status --porcelain --untracked-files=all` is empty.
2. `git rev-parse HEAD` equals the saved `bookkeeping_commit`.
3. `git rev-parse "${bookkeeping_commit}^"` equals
   `pre_bookkeeping_revision`.
4. `git diff-tree --no-commit-id --name-only --no-renames -r
   "${bookkeeping_commit}"` lists only `.planning/ROADMAP.md`,
   `.planning/STATE.md`, and `.planning/REQUIREMENTS.md`.

When every guard passes, run `git revert --no-edit "${bookkeeping_commit}"`.
This removes only the isolated success-record commit and preserves implementation
history and source changes. Never reset, force-move a branch, or hand-edit
planning structures. If a guard fails, preserve the current work and do not
claim completion. If the revert conflicts, abort only that attempted revert and
preserve the bookkeeping commit; record the blocked/nonpass verification state
through `state.record-session` and its explicit STATE-only commit when the tree is
clean. If the attempt cannot be returned cleanly, stop without overwriting it.

After successful compensation, record the nonpass session status through the
runtime and commit that STATE-only update, for example:

```bash
phase_run query state.record-session \
  --stopped-at "Phase ${phase_number} final verification ${final_status}; bookkeeping compensated" \
  --status "Verification blocked"
phase_run query commit "docs(state): record phase ${phase_number} verification block" \
  --files .planning/STATE.md
```

Then capture this compensated-status revision and run a fresh read-only
verifier/check batch there. The final report
must use that last revision and status; persist it alone only after the batch
joins. Do not repeat `phase.complete`, requirement closure, or success bookkeeping
during this nonpass path.

This `git revert` is the sole narrow exception to runtime-only structural
authoring: it may reverse only the exact, guarded, coordinator-created
bookkeeping-only commit from this attempt. It is not permission to edit planning
records manually or revert a worker/source commit.
