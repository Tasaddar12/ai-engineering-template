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

## Bookkeeping and final currentness

The coordinator applies authorized structured bookkeeping after joining evidence. Distinguish preliminary phase status from final verification and shipping approval. Reconcile the final report against the resulting revision, then call currentness again before ready/ship. If bookkeeping changes covered inputs, generate valid affected evidence; do not claim the old report covers changed source.

## Compensating a failed final verification

A failed final gate does not authorize resetting history. The sole guarded compensation exception is a coordinator-created, bookkeeping-only commit from this same verification attempt.

1. Identify its exact SHA and immediate parent, recording both before any compensation.
2. Confirm it is current HEAD, unpushed, created by this coordinator, and contains only the exact runtime-owned bookkeeping paths from the attempted success reconciliation.
3. Confirm all workers stopped, the worktree/index are clean, no unrelated user/source changes or extra commits exist, and no other session owns those paths.
4. Preserve the failed report and evidence outside the compensation set. If any condition is uncertain, do not compensate; report the blocker and retain the history.
5. Compare `git diff-tree --no-commit-id --name-only -r "$BOOKKEEPING_COMMIT"` with the exact bookkeeping path list captured before the commit. Verify HEAD equals that SHA, its sole parent equals BOOKKEEPING_PARENT, the clean index/worktree match it, and no remote branch contains the commit. Do not infer an approved set from its subject.
6. With every guard established, run `git reset --soft "$BOOKKEEPING_PARENT"`, then `git restore --source="$BOOKKEEPING_PARENT" --staged --worktree -- "${BOOKKEEPING_PATHS[@]}"` using only the exact captured bookkeeping paths. The first command preserves content/index; the second compensates only those structures. Never use hard reset, broad restore, a computed unreviewed path list or pushed-history rewrite.
7. Confirm the retained source/report/evidence remain intact and the resulting revision equals the captured parent. If an operation is rejected or its outcome is uncertain, preserve state and report it; do not repeat destructive recovery blindly.
8. Re-establish a clean captured revision and record that final verification failed. Preserve the gaps; do not issue a success or shipping claim.

This exception is not a general reset/revert permission and never substitutes for human authorization required by the actual host.

## Quick verification

Use `verification.status --quick ID`, `verification.resolve-file --quick ID`, `verification.fingerprint --quick ID` and `verification.current --quick ID` for genuine quick records. Their report has `quick: NNN`, status, covered_files, fingerprint, revision and issue_refs. Do not fabricate a phase identifier to reuse a phase gate. Required human acceptance and finding links still apply.

## Historical gap reconciliation and final human evidence

A historical `result: issue` may stop blocking only through the preserved resolved-gap path: valid stable gap_id, resolved_by and resolved_at; an executed resolving PLAN; a complete matching committed SUMMARY with specific evidence for that gap; and final actual Human acceptance of the covered build. Every remaining required current action must pass. Skipped, not-testable, blocked and pending required actions remain blocking.

If explicit human retest is required, record that actual retest pass; never assume it from a SUMMARY. Diagnosis, a relabeled status, a checked item or a resolving commit alone is insufficient. This narrow historical effective-resolution path preserves the original issue evidence and does not manufacture final human acceptance.
