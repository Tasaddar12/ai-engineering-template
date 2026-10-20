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

## Qualifying check receipts across a report-only successor

Report currentness and check-receipt qualification answer different questions.
The coordinator currentness rule above establishes whether the verifier's report
still describes the source at HEAD. The successor qualifier establishes whether
the original configured check results still cover HEAD. One result never stands
in for the other, and verification.status still only reports metadata.

Capture the complete passing result at tested revision R outside the
checkout. For current HEAD H, qualify it against the exact phase report path:

    phase_run query verification.run-checks > "$original_evidence"
    phase_run query verification.qualify-successor \\
      --evidence-file "$original_evidence" \\
      --report-only-paths "$phase_report" \\
      --expected-head "$H"

The phase_report value must be the exact repository-relative
NN-VERIFICATION.md path owned by its matching NN-CONTEXT.md. Arbitrary Markdown,
quick-task reports, plans, specifications, STATE/ROADMAP/REQUIREMENTS, security
records, and other bookkeeping are unsupported. The history proof requires a
clean tree, available commit objects, R as an ancestor of H, and every
intervening commit and merge-parent diff to change only the approved regular
report. Edits later reverted, report deletion or rename, mode changes, links,
unavailable Git objects, overridden history, and unsafe external filters fail
closed. Missing objects are never lazy-fetched.

A check qualifies only when its original schema-1 configuration already
contained this prospective contract before the fresh baseline:

    successor_independence:
      schema: 1
      report_paths:
        - .planning/phases/01-example/01-VERIFICATION.md
      protected_inputs: all-other-inputs
      revision_semantics: provenance-only

The exact command, order, specification, configuration and captured inputs
remain bound. The contract says the named report does not affect the command's
result, all other inputs stay protected, and revision records provenance rather
than a command input. It is a reviewed per-check assertion, not established by
the CLI argument. Old receipts without the contract/input bundle cannot qualify
retroactively. Preserve revision and reuse flags; normal execution and cache
semantics do not change. Report/HEAD-reading, opaque/full-tree diff and
unbound-volatile checks remain fresh-required.

The response separates tested_revision (R) from qualified_revision (H), and
returns approved paths, checked commits, original receipt references, ordered
qualifications and fresh_required zero-based indices. It preserves original
rows and stored evidence. A qualified: true result requires complete configured
accounting through authenticated original receipts or passing fresh H evidence.
Invalid baseline, history or protected-input proof cannot be repaired by fresh
rows; a failed original aggregate requires a complete fresh baseline.

For only the fresh_required indices, run the unchanged checks freshly at H and
save their JSON outside the checkout:

    phase_run query verification.run-checks --only-checks 1 3 > "$fresh_evidence"
    phase_run query verification.qualify-successor \\
      --evidence-file "$original_evidence" \\
      --report-only-paths "$phase_report" \\
      --expected-head "$H" \\
      --fresh-evidence-file "$fresh_evidence"

Use the exact ordered indices returned by qualification. A proper subset keeps
full-order indices and full configuration/order hashes, reports selected_passed,
and always has aggregate passed: false. The qualifier accepts genuine current-H
receipts/logs for all and only the required indices and returns complete mixed
accounting with original R rows and fresh H rows. If the original aggregate or
protected-input proof is invalid, run the whole configured set fresh. Keep both
evidence files external to the report commit they validate.

This qualifies check evidence only; it does not qualify a report's status or
revision and does not replace the currentness procedure above.

### Consumer adapter boundary

The canonical helper and CLI validate this template's schema-1 receipts only.
They do not read or adopt a consumer's customized schema-2 joined/profile
validator. For a Whiskance adapter, use this bounded route:

1. Pin the exact canonical source commit and reviewed diff. Compare them with
   the installed ownership manifest before editing. The consumer owns
   .codex/runtime/lib/verification_checks.py,
   .codex/runtime/lib/verification.py,
   .codex/runtime/lib/verification_profiles.py,
   .codex/runtime/lib/delivery.py and .codex/runtime/phase.py; preserve
   the project's customized files and tests rather than copying the canonical
   runtime over them.
2. Keep the consumer receipt schema at 1 and retain its runner,
   capture_inputs, receipt storage and validate_joined behavior. Add a separate
   schema-2 successor adapter around those authorities. Do not transplant the
   canonical validate_successor over validate_joined or import the canonical
   runtime into the consumer.
3. Keep the schema-2 profile closed contract: exact selected profile
   identity/content/hash/path/registry, purpose=development,
   deployment_deferred=true, selected command order, and complete default
   application-command digest plus ordered dispositions. Preserve the current
   profile owner and command policy of revision=true and reuse=false.
4. Add the exact prospective successor_independence contract to check
   normalization, and bind it before execution into the original receipt
   inputs. Keep it distinct from independent=true, which only controls
   scheduling. Capture the complete protected inventory plus the union of all
   configured declared inputs, source fingerprints, effective verification
   configuration, runtime implementation identity, executable/tool identity,
   environment digest, timeout, exact specification and full check order.
   The original manifests and profile/base/allowed-path scope belong to R.
5. After the consumer adapter and configuration are ready, run a complete,
   fresh schema-2 development baseline at R. Authenticate it with the existing
   validate_joined path. Require the full passing aggregate, matching tested
   revision, actual successful exits, snapshot_valid=true and reused=false for
   each original result; preserve the genuine original receipt and stdout/
   stderr logs and hashes. Existing receipts without the new prospective
   bundle cannot qualify after adoption.
6. For candidate H, keep the worktree clean and prove R-to-H with the canonical
   phase-report attestor. Only exact canonical phase NN-VERIFICATION.md paths
   with their matching tracked NN-CONTEXT.md owners are eligible. Check every
   intervening commit and merge parent. Preserve the original tested R and
   return a separate qualified H.
7. Authenticate the profile content, registry, base and allowed-path scope
   against baseline R. Do not rerun ordinary profile selection or scope as if H
   were a new baseline: the approved report can lie outside the original
   allowed_paths. The independent R-to-H history proof accounts for that
   report. Do not add a broad report exception to scope or remove the existing
   R==HEAD/profile-scope protections.
8. Recompute and compare the current effective configuration, runtime/helper
   implementation, tool, environment, timeout, selected profile, commands,
   default dispositions and every non-report source/protected manifest against
   the authenticated R bundle. Each original receipt must remain ordered,
   fresh, passing and byte/authentication-valid. A report-independence claim
   cannot cover a changed non-report input.
9. Run only uncovered required selected checks freshly at H. Bind their
   receipts to their full configured order indices and H, then return complete
   ordered accounting that preserves original R rows, fresh H rows, selected
   profile identity and all default dispositions. A proper subset is not a
   passing full-profile aggregate; a failed original aggregate cannot be
   rehabilitated by omitting its failed row.
10. Adapt delivery to consume the two-revision qualification object. Require
    local HEAD H before and after proof/provider reads, the same OPEN PR branch
    and headRefOid H, then pass --match-head-commit H. Revalidate the
    qualification's R and H evidence at the final gate; do not run baseline-only
    validate_joined at H. Preserve existing reviews, CI, platform protections
    and the no-CI requirement for validated local evidence.
11. Add consumer-owned profile, receipt, subset, history, moved-head and
    provider-race regressions in .codex/tests/test_verification_profiles.py,
    test_verification_receipts.py and test_session_delivery.py (or the nearest
    dedicated runtime suites). Canonical helper tests do not replace consumer
    schema-2 integration tests.
12. Quick-task report owners are unsupported by the canonical phase-only
    attestor. Do not claim Whiskance quick reports or receipts qualify, and do
    not grandfather old quick receipts. Supporting them requires a separately
    reviewed explicit quick-owner eligibility implementation and its own
    tests; this adapter does not add that exception.

A complete fresh schema-2 baseline is required after the adopted
validator/helper, runtime, profile, contract or configuration changes. Original
R evidence stays immutable, and a later change to any bound identity requires
fresh evidence for the affected baseline. The canonical template remains
phase-report-only and schema-1; this adapter recipe does not make consumer
adoption or quick-report support an implemented feature.

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

## Compensating a failed final verification

Success bookkeeping is provisional until the final verifier reviews the new
revision. Before changing any success records, require a clean worktree confirmed
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
