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

Verification reports are read-only specialist output. The verifier examines the
product/source revision and returns a complete external report. The coordinator
persists that report at the phase's tracked `NN-VERIFICATION.md` path and commits
that file. `verification.status` reads report metadata; it does not enforce the
currentness rule below. The report's `revision` remains the exact commit tested
by the verifier. The coordinator must not replace it with the later report-only
commit's hash, which the verifier never examined.

## Coordinator currentness check

Use this rule in both `/verify-work` report reuse and `/ship` preflight. Let
`tested_revision` be the report's `revision`, `HEAD` be the current session tip,
and `report_path` the exact repository-relative path of this phase's
`NN-VERIFICATION.md`.

1. Require a clean worktree, including untracked files. Dirty state means the
   delivered tree differs from the tested commit, so the report cannot be reused.
2. If `tested_revision` equals `HEAD`, the report is current.
3. Otherwise, require `tested_revision` to be an ancestor of `HEAD`.
4. Enumerate every commit in `tested_revision..HEAD`, in ancestry order. For each
   commit, run `git diff-tree --no-commit-id --name-only --no-renames -r -m
   "$commit"` and compare each output line to the exact `report_path` returned
   by `verification.resolve-file`. Use quoted revision, commit and path values.
   Rename detection is disabled and merge commits are compared against every
   parent. Every changed path in every commit must equal `report_path`. Any
   source, config, planning or other path makes the report stale. This per-commit
   check catches a source edit later reverted; a final-tree diff alone would miss
   it.
5. If ancestry is missing, a changed path differs, or repository state is dirty,
   require fresh verification. Do not change the report's tested revision to
   make the currentness check pass.

The equality case preserves the exact-revision fast path. The sole exception is
the coordinator's tracked report publication after a read-only verifier has
finished; that publication cannot change the already tested product/source. The
exception is narrow to the exact phase report path, checked commit by commit.

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
Capture the resulting HEAD, run the configured checks there (reusing only receipts
valid for that invocation), and have the read-only verifier review the actual
bookkeeping diff plus source/acceptance coverage at that exact new revision. Wait
for these results before persisting the report. The coordinator writes the report
with the revision the verifier actually reviewed and commits that report alone as
the last workflow write. Never retag the report to the following report-only
commit.

The report-only exception above permits subsequent ship preflight to consume the
report for the preceding tested revision. It is a coordinator procedure, not an
enforcement performed by `verification.status`, which only exposes metadata. A
refresh-only verification does not repeat completion/requirement/session writes
and does not invoke `/ship` again. A source repair invalidates evidence and starts
a new verification batch; it is not a report-only publication.
