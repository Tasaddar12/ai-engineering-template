---
workflow: code-review-fix
roles: [coordinator, targeted-fixer, code-reviewer, debugger]
produces: [per-repair SUMMARY.md, REVIEW-FIX.md, refreshed REVIEW.md]
---

@engineer/references/response-language-directive.md

<purpose>
Repair grounded REVIEW findings independently, one finding per isolated worker
and repair commit, using the complete code-fixer method. Re-review the repaired
revision and preserve accurate partial-failure/disposition evidence. --auto is
only a capped repair loop; it never chains phases or grants merge authority.
</purpose>

<required_reading>
Read code-review.md initialization/scope contracts; engineer/RULES.md; complete
bounded-correction-dispatch, worker-handoff, worktree-sessions, worktree-path-safety,
git-workflow, template-contract, verification-evidence references; the complete
agents/targeted-fixer.md and agents/code-fixer.md methods; full SUMMARY template;
source REVIEW and owning CONTEXT/PLAN/QUICK. Use the identity-checked Python
runtime selected by the invoking workflow. All runtime verbs use query and dotted
names. No missing helper, host-native adapter or provider lane is a prerequisite.
</required_reading>

<process>
<step name="initialize_and_authorize">
Consume the structured invocation from dispatch-fix; a direct invocation must
repeat the identity validation and session/revision/scope steps of code-review.md.
Validate actual phase/quick before config gating. Read
`config-get workflow.code_review --raw`; explicitly disabled skips; errors remain
errors. Missing REVIEW is an explicit prerequisite failure; do not silently run a
new review or begin blind repair.

Require the user's explicit --fix invocation or the already recorded applicable
implementation instruction. Preserve its exact scope/limits in owning CONTEXT or
quick record through the proper owner. A review, plan/design approval, readiness
or report request does not authorize repairs. Existing authority is persistent;
do not ask again at each finding/pass. New acceptance/locked decision conflicts
block only their dependent correction. Continue independent authorized findings.

Use the owning phase/quick isolated session and real session base. Read REVIEW
frontmatter through `frontmatter.get PATH`; validate the complete body using the
code-fixer fence-aware parser. status clean/skipped yields no fixes; malformed or
unknown status blocks mutation (never warn-and-proceed). Extract exact original
files_reviewed_list, depth, base_revision, head/revision and digest. An absent file
list or revision is a missing input; reconcile through a fresh scoped review,
never silently fall back to the entire repository/phase. Require a current
report before repair; inspect source drift and re-ground every finding.

Default scope is Critical (CR/BL IDs) and Warning; all adds Info. Sort severity
then document order, deduplicate stable IDs and preserve aliases. Parse full Fix
content including inline/fenced/prose and every referenced file, but those
references are discovery evidence, NOT new write authority. Include classification,
required_property, authority and source revision in every packet. Fix suggestions
are advisory; unknown causal diagnosis routes an exact debugger assignment before
repair, not a speculative targeted-fixer patch.
</step>

<step name="dispatch_per_finding">
Freeze producer output and wait for confirmed stop before assigning paths. Join
review evidence; reject unsupported claims with cited counterevidence. For each
grounded selected finding prepare the complete bounded correction packet:

- Actual repository/session/branch, input SHA and artifact digest.
- Stable ID, classification/severity, source evidence, authority, required_property.
- Exact owned source/test/fixture paths, explicit files_deleted and forbidden
  paths/resources; smallest full contract reading set and consuming template.
- Concrete affected check argv, cwd/expected result, reusable receipts, pending
  decisions and actual user check-ordering constraints.
- Required committed SUMMARY destination and first bounded continuation.

Do not let the worker rediscover the repository. Collect multi-file evidence and
resolve scope before dispatch. An essential path outside authority blocks that
repair until coordinator reconciliation; --all selects severity, not unlimited
ownership. Assign one worker per finding per pass, sequentially when dependencies,
shared resources or paths overlap. Retry only with changed hypothesis/input and
preserve earlier attempt evidence; never repeat the identical failed attempt.

Always create and own the isolated repair checkout in the coordinator. Inspect
`dispatch-isolation --force-isolation orchestrator-worktree --raw`; this explicit
mode is supported on both Claude and Codex and pins this procedure to coordinator
ownership. Do not ask the worker to create/switch/merge a checkout. Create via:

```sh
engineer_run query worktree.create REPAIR_ID --phase OWNER_KEY --base INPUT_SHA --branch REPAIR_BRANCH --files PATH1 PATH2 --deletions DELETED_PATH
engineer_run query resolve-model targeted-fixer --raw
engineer_run query resolve-effort targeted-fixer --raw
```

OWNER_KEY is the actual phase worker group, or a collision-free quick-ID group
(the --phase option is a manifest grouping key, not a fictional phase record).
REPAIR_ID must uniquely identify the finding/pass and match its assigned SUMMARY
basename. For a phase repair, allocate a unique numeric plan identity through
the owning runtime/planner contract so phase/plan/basename agree; do not use a
CR-01 string where the SUMMARY schema requires a numeric plan. If that allocation
cannot be established, return the missing input before worker creation.
--files enumerates exact actual paths; omit --deletions unless explicitly
authorized and list each exact removal, including old rename paths. Never send
empty ownership (the runtime otherwise permits broad changes). Record returned
path/branch/base; verify branch/root/HEAD before dispatch. Commit coordinator-owned
worker bookkeeping as required before integration; do not bury unrelated changes.

Use the full SUMMARY schema: actual phase or quick identity, plan/repair identity,
status, requirements-completed, acceptance, documentation, issue_refs and every
required body section, plus the complete REVIEW-FIX body from code-fixer. Choose
a valid unique basename matching identity; do not overwrite an earlier execution
SUMMARY or copy fictional template values. The source-only code-fixer method is
agents/code-fixer.md; installed Claude reads engineer/references/code-fixer.md;
Codex reads the method Markdown directly. It is never independently dispatched.

```text
Agent(subagent_type="targeted-fixer", model="{resolved_model}", effort="{resolved_effort}", prompt="
Follow the complete targeted-fixer role and code-fixer method.
checkout: {coordinator_created_absolute_root}
branch: {returned_branch}; revision: {returned_base}
owned_paths: {exact_authorized_paths}; files_deleted: {exact_authorized_deletions}
forbidden_paths/resources: {explicit_boundaries}
summary_path: {unique_actual_repair_SUMMARY}
finding: {one_stable_ID_and_complete_grounded_packet}
checks: {actual_argv_cwd_expected_result_and_execution_order}
Verify identity before editing. Satisfy required_property; fix_hint is advisory.
Commit this finding's repair atomically and commit complete SUMMARY before complete.
Never create/switch/merge a checkout, publish, spawn children or edit shared records.
Return actual check evidence and unresolved obligations; unrun is never passing.
")
```

Resolve model/effort inline, omit inherited values, and wait for confirmed stop.
During the assignment do not touch its owned files or integrate its incomplete
work. Host timeout is not exit. On failure preserve worktree, commits and dirty
paths, return exact process state and use the confirmed-stop/continuation contract.
A missing report does not prove no repair commit exists: inspect actual history.
</step>

<step name="integrate_and_verify">
After each assigned writer stops inspect actual committed paths, ownership,
deletions, branch ancestry, full SUMMARY and actual evidence. Integrate only
complete valid repairs from the owning session via
`worktree.merge-wave --phase OWNER_KEY`. Dirty/incomplete workers, undeclared
paths/deletions and conflicts block integration; preserve them, never bypass
with reset/clean/hand merge. Required checks judge the integrated tree.

Capture the new frozen HEAD. Run affected configured checks using
`verification.run-checks --checks CHECK_ID...`; omit selection only when the full
configured set is required. The API selects configured IDs, not arbitrary shell
commands. Check returned revision, receipts, exact argv/cwd/input fingerprints,
exit status and nonempty required coverage. An empty checks list/all([]) is not
passing evidence for required checks. Reuse only receipts whose revision ancestry
and exact inputs/configuration match; use --force when fresh execution is needed.
Additional assigned checks preserve exact argv/root/SHA/output separately.

User ordering takes precedence: if all tests/checks/compile/lint/smoke are deferred
until all draft PRs exist, do not execute them here, including example syntax
checks. Record unrun with that authority and carry pending gates to the final
batch. Never silently downgrade required checks to a source reread or mark all_fixed
while required check/review evidence is missing.

Obtain fresh independent code-reviewer evidence on the repaired frozen revision
using code-review.md's exact dispatch/model/effort/capture contract. Keep the
original complete review scope/depth plus explicitly authorized affected paths;
never lose scope between iterations or make the fixer verify itself. Review is
read-only; coordinator writes updated REVIEW. Re-review is required after EVERY
repair pass, including a non-auto single pass and the last auto pass. Confirm
writers stopped and join all checks/review results before accepting the batch.
A logic fix needs behavioral evidence or remains unverified; human judgment is
required only where actual acceptance requires it, never invented routinely.
</step>

<step name="auto_iteration_loop">
Initial repair pass is iteration 1. Always re-review it. With auto=false, stop
further repairs after that single pass and record remaining findings. With
auto=true, continue only when current required findings remain grounded and
within existing authority; at most THREE repair passes total, each followed by
checks (when authorized) and independent re-review. New claims require evidence,
classification and exact scope, not automatic permission to widen a repair.

Before replacing REVIEW/aggregate REVIEW-FIX, capture immutable pass evidence
externally or explicitly assigned .iterN.md backups with source SHA/digest. Keep
original IDs/aliases even if the final clean review no longer lists early fixes.
On the final pass, test convergence before reporting the cap: a proven clean
final review with required checks passing is convergence, including pass 3.
A non-clean/unknown review, missing report, failed/unrun required check, process
uncertainty or blocked decision remains partial/blocked, never convergence.

At the cap preserve remaining findings and post-mortem evidence. No iteration
count permits unresolved required failures to pass. The bounded dispatch contract
can continue a separately grounded correction with changed input/authority, but
--auto itself never silently exceeds three passes.
</step>

<step name="record_and_commit">
Coordinator writes one final aggregate REVIEW-FIX.md after all passes. Retain
all per-finding committed SUMMARYs; the aggregate does not replace them. Use the
complete REVIEW-FIX body in code-fixer (Fixed Issues, Checks, Remaining, Skipped
Issues, each ID/files/commit/applied correction and exact skip reason). Add:

```yaml
---
phase: "actual owning phase" # use quick instead for genuine quick work
review_path: "actual report"
review_revision: "original reviewed SHA"
base_revision: "actual session base"
revision: "actual repaired SHA"
iteration: 1
findings_in_scope: 1
fixed: 0
skipped: 0
blocked: 1
status: blocked
repair_outcome: none_fixed
issue_refs: []
---
```

This is a template, not fabricated evidence. status complete requires full
supported repair obligations; repair_outcome is all_fixed/partial/none_fixed.
A committed patch may be implemented_pending_checks without counting it verified
fixed. Record original review digest, exact files/depth and each pass/check/review
revision. Each original and new stable ID gets fixed with supporting evidence,
unsupported with counterevidence, skipped with reason, or blocked with exact
owner/input. Required defects cannot be made complete by calling them deferred.

Read back and validate frontmatter/body/counts. Commit aggregate once after all
passes, together with the latest coordinator-written REVIEW so committed artifacts
agree. Use `engineer_run query commit MESSAGE --files REPORT REVIEW` and canonical
Why/Changes/Verification body. A missing/malformed report blocks that success;
preserve actual existing repair commits and report partial progress.

For phase disposition reconciliation read execute-phase/steps/code-review-disposition.md
only after aggregate and pass evidence are committed. It is advisory, must consume
all passes before backups are retired and must not execute unsupported/legacy
helpers. Invoke `engineer_run query review.disposition --phase PHASE_NUMBER
--phase-dir PHASE_DIR` using the actual validated phase inputs. Display every
dropped/stale/unparsed note and retain its consumed_passes exact paths/digests
and review_digest. It joins the final report and every numeric iteration backup
before any retirement. An advisory skip retains all passes and explicit aggregate
entries with stable ID/aliases, source and repair revision, disposition/reason
and commit/check/re-review evidence. The ledger never waives a required finding
or acceptance gate. Genuine quick has no
fictional phase ledger. Never hand-edit runtime-owned structures.
</step>

<step name="retain_evidence_and_present">
No broad cleanup/globs or suppressed recursive removal. After disposition reads
all passes, proven-converged scratch may be retired only as an exact owned list
with required deletion authority; otherwise retain backups. On degradation,
unknown status or failure preserve the post-mortem trail. Worker cleanup belongs
to coordinator lifecycle/integration evidence, never fixer teardown. Windows
reparse points must never be recursively removed.

Present source/repaired SHA, scope, depth, pass count, each finding's disposition,
repair/SUMMARY commits, integrated status, actual checks/re-review outcomes,
report paths, preserved worktrees and remaining first action. Distinguish all
fixed from partial/none fixed and missing evidence; do not infer success from
commit counts. Missing report means inspect actual commits, not assert no edits.

In-scope required gaps stay blocking. Out-of-scope work is Deferred with evidence
or an authorized canonical issue request; no todos. Unknown cause goes to debugger.
Public issue writes follow exact canonical variants, verified existing/no-match,
current digest/content-bound preview and actual provider readback. Pending access,
authority or human acceptance remains explicit. Preserve security tracking and
independent non-author issue-link audit. Publish only within existing delivery
scope; leave drafts open unless explicitly instructed to merge. No extra routine
approval menus, implicit phase chaining or automatic merge.
</step>
</process>
