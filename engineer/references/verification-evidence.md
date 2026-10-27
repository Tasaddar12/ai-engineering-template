# Frozen verification evidence

A passing verdict requires evidence for the exact integrated source and required acceptance, not worker self-attestation. The coordinator owns freeze, dispatch, join, reconciliation and final publication gates.

## Freeze and capture

1. Wait for every source-changing worker to stop positively; integrate authorized committed slices.
2. Capture repository, branch, full HEAD and clean/dirty state. No writer may mutate the captured source during the batch.
3. Read configured check argv and required PLAN checks, documentation obligations, integration flows, security findings and human judgments.
4. Dispatch required read-only specialists and configured checks against that same captured revision. They may inspect it concurrently; wait for every assigned result before accepting evidence or repairing anything.
5. If source changes, stop accepting that batch as current. Preserve diagnostic results and rerun affected evidence only after establishing a new freeze.

## Check receipts

`engineer_run query verification.run-checks` executes configured argv without a shell. An omitted inputs list covers nonplanning Git-visible files. Record the tested revision, exact argv, exit/result, output and receipt identity. A passing receipt is reusable only when command/configuration and input digest match and its revision is in current history. A failed, missing or malformed receipt never implies success. Drift during execution fails the frozen run.

Use `verification.check-status` to inspect current receipts. Use `verification.fingerprint N` to bind covered PLAN/SUMMARY and sources; keep `covered_digest: "v4:sha256:..."`. The report itself is excluded from the digest. `verification.current N` verifies clean source, fingerprint, revision and current receipts. A matching hash proves content correspondence, not behavioral correctness.

## Join and classify

| Evidence | Required disposition |
|----------|----------------------|
| Acceptance demonstrated at covered revision | Verified, with exact supporting result |
| Reproducible failure | Blocking gap |
| Present/wired source without exercised behavior | PRESENT_BEHAVIOR_UNVERIFIED |
| Backstop truth with insufficient evidence | human_needed, insufficient_spec |
| Required human judgment | Pending until actual human decision |
| Unsupported preference | Advisory with its limits |

Join verifier, code review, document verification, integration and security packets when applicable. Resolve every required finding or record the exact blocker. Counts, mode flags and repeated review cycles do not waive gates. A changed decision requires owning-record reconciliation, not an acceptance override.

## Final-report lifecycle

The verifier is read-only and returns an external report; the coordinator alone writes and commits the tracked phase report. The report's `revision` is the exact commit the verifier reviewed, never the later report-only commit.

On the initial pass, start the provisional verifier, configured checks and applicable independent specialists together against one frozen revision. The provisional verifier receives no future results and cannot finalize status. Join the whole batch, then resume the verifier with check receipts/results and bounded specialist findings so it can reconcile shared evidence and inspect only gaps or conflicts.

If that joined result provisionally passes, first require a clean worktree, including untracked files, and save `pre_bookkeeping_revision=$(git rev-parse HEAD)`. Apply the authorized success bookkeeping and commit only `.planning/ROADMAP.md`, `.planning/STATE.md`, and `.planning/REQUIREMENTS.md` together as one coordinator-created `bookkeeping_commit`. Do not include the verification report, source files, or user files. Capture that new HEAD and run the configured checks and final read-only verifier against this exact revision; the verifier reviews the actual bookkeeping diff and source/acceptance coverage. Wait for the complete final batch before persisting the report.

If final reconciliation returns `gaps_found` or `human_needed`, follow the exact guarded compensation below. After successful compensation, record nonpass status with `state.record-session`, commit that STATE-only update, and run a new frozen read-only verifier/check batch at the compensated-status revision. Persist the final report alone after that batch joins, naming the exact revision it tested. Never repeat `phase.complete`, requirement closure, or success bookkeeping on the nonpass path.

Persist the final report alone only after the final batch has joined. Do not replace the tested `revision` with the report-only commit's hash. A refresh-only verification does not repeat completion, requirement or session writes and does not invoke `/ship` again. A source repair invalidates applicable evidence and starts a new verification batch; it is not report-only publication.

## Coordinator report currentness

Use this rule for `/verify-work` report reuse and `/ship` preflight. Let `tested_revision` be the report's `revision`, `HEAD` the current session tip, and `report_path` the exact phase `NN-VERIFICATION.md` path returned by `verification.resolve-file`.

1. Require a clean worktree, including untracked files. Dirty state means the delivered tree differs from the tested commit, so the report cannot be reused.
2. If `tested_revision` equals `HEAD`, the report is current.
3. Otherwise, require `tested_revision` to be an ancestor of `HEAD`.
4. Enumerate every commit in `tested_revision..HEAD` in ancestry order. For every commit, run `git diff-tree --no-commit-id --name-only --no-renames -r -m "$commit"` and compare every output line with the exact `report_path`. Quote revision, commit and path values. Disable rename detection and compare merge commits against every parent. Every changed path in every commit must equal `report_path`; any source, config, planning or other path makes the report stale. This catches a source edit later reverted, which a final-tree comparison would miss.
5. If ancestry is missing, any changed path differs, or the repository is dirty, require fresh verification. Never change the report's tested revision to make currentness pass.

The equality case preserves the exact-revision fast path. The sole later-report exception is publication of the exact phase report path after the read-only verifier has finished; that publication cannot change the already tested product/source. This per-commit rule is also required at ship preflight. `verification.status` exposes report metadata but does not enforce currentness.

## Compensating a failed final verification

Success bookkeeping is provisional until the final verifier reviews the new revision. Before changing any success records, require a clean worktree confirmed with `git status --porcelain --untracked-files=all` and save `pre_bookkeeping_revision=$(git rev-parse HEAD)`. Save the exact coordinator-created bookkeeping commit SHA as `bookkeeping_commit`.

If final reconciliation returns `gaps_found` or `human_needed`, compensate only when every guard below passes:

1. `git status --porcelain --untracked-files=all` is empty.
2. `git rev-parse HEAD` equals the saved `bookkeeping_commit`.
3. `git rev-parse "${bookkeeping_commit}^"` equals `pre_bookkeeping_revision`.
4. `bookkeeping_commit` is an ordinary single-parent commit.
5. `git diff-tree --no-commit-id --name-only --no-renames -r "$bookkeeping_commit"` returns a nonempty set, and every path is one of exactly `.planning/ROADMAP.md`, `.planning/STATE.md`, or `.planning/REQUIREMENTS.md`.

When every guard passes, run `git revert --no-edit "$bookkeeping_commit"`. Never use soft/hard reset, restore planning files by hand, force-move refs, or revert source/worker commits. If a guard fails, preserve all work and retain the nonpass result. If the revert conflicts, abort only that revert and preserve the original bookkeeping commit. If the tree is not clean after successful compensation, stop without overwriting it.

After successful compensation, use the runtime `state.record-session` operation to record the nonpass status and commit only `.planning/STATE.md`. Then capture that compensated-status revision and run a new frozen read-only verifier/check batch there. The final report uses the last tested revision and status, and is persisted alone only after the batch joins. Do not call `phase.complete` or repeat requirement closure/success bookkeeping on this path.

This `git revert` is the sole narrow exception to runtime-only structural authoring. It may reverse only the exact guarded coordinator-created bookkeeping-only commit from this attempt. It does not authorize manual planning edits or reverting worker/source commits.

## Quick verification

Use `verification.status --quick ID`, `verification.resolve-file --quick ID`, `verification.fingerprint --quick ID` and `verification.current --quick ID` for genuine quick records. Their report has `quick: NNN`, status, covered_files, fingerprint, revision and issue_refs. Do not fabricate a phase identifier to reuse a phase gate. Required human acceptance and finding links still apply.

## Historical gap reconciliation and final human evidence

A historical `result: issue` may stop blocking only through the preserved resolved-gap path: valid stable `gap_id`, `resolved_by` and `resolved_at`; an executed resolving PLAN; a complete matching committed SUMMARY with specific evidence for that gap; and final actual Human acceptance of the covered build. Every remaining required current action must pass. Skipped, not-testable, blocked and pending required actions remain blocking.

If explicit human retest is required, record that actual retest pass; never assume it from a SUMMARY. Diagnosis, a relabeled status, a checked item or a resolving commit alone is insufficient. This narrow historical effective-resolution path preserves the original issue evidence and does not manufacture final human acceptance.

## Receipt input and environment completeness

Receipt reuse also binds generated dependencies and the effective execution environment. Identify source inputs, generated artifact inputs/producer revision, dependency lockfiles, configured argv/working directory, relevant nonsecret environment stamps, runtime/tool versions and fixtures. Do not print secret values; record safe presence/version/reference identities only. A changed generator output, dependency resolution, environment stamp, configuration or input invalidates the affected receipt even when the top-level command text is unchanged.

Volatile external services are not durably covered by a file digest. Record the actual service/target, observation time, applicable freshness window and known state dependencies. Reuse only when the acceptance permits that age/state and current evidence establishes applicability; otherwise rerun the authorized bounded observation. Never describe a previous external response as proving the current deployment or live provider state. User-deferred execution remains pending and cannot be replaced by a matching hash.
