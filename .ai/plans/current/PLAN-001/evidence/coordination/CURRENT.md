# PLAN-001 current checkpoint

**HALTED at the user's request: "Store current progress and halt processing".**
Do not resume implementation, reviews, tests or integration until the user asks.
All worker activity is stopped: repair_009_c1 was interrupted; the other live
workers/reviewers are completed. No batch-workflow approval or completion is claimed.

Progress was saved before stopping:
- Integration baseline:9d8fa977a7f1c4157740438eea7e4e26d22e7bdd;15/39 accepted,
  canonical state generation53. This checkpoint commit adds no task acceptance.
- Unfinished manual tooling edits are preserved in isolated branch
  `ai/PLAN-001/manual-batch-workflow`, checkout `.worktrees/manual-batch-workflow`,
  WIP commit `50545ef509eadd34811327f560805750812f926c`.
  Only coordinator.py changed (15 additions,9 deletions). This is an unvalidated
  partial implementation, not an approved candidate; no new batch tests or
  independent tooling review have run. Instructions/tooling work remains.
- TASK-009 repair is stable at fa77907a1981a436f5a8499a38c3a0a8026763d0;
  TASK-015 repair is stable at edbc147a7dcff4f1b76b6909d689516a2ef6ecc4.
  Both retain their tests/handoffs and await the new batch approval process.
- TASK-016's completed rejection is preserved and its two scoped repairs remain
  pending. TASK-005-a2 and TASK-020 are also stable pending batch review.
- Native invocation budget remains121/300 used,179 remaining; rewrites3/3 used.

On an explicit resume: finish the isolated manual coordinator/instruction change,
test member coverage, stale/failed approval rejection and unchanged-evidence reuse,
obtain one fresh Astra/xhigh independent review of that change, then integrate and
update canonical workflow resume metadata. Preserve historical reports/decisions,
runtime two-stage contracts and external authority. Select further PLAN work only
under the new batch workflow. Do not restart the superseded per-task review loop.

The full 39-task implementation remains pending: **15/39 accepted**;
state generation **53**, integration branch `ai/PLAN-001/integration`.
Current user priority: implement and verify small-batch manual coordination,
superseding per-task independent invocations and automatic unchanged-test reruns.
ROOT is unfrozen at `9d8fa977a7f1c4157740438eea7e4e26d22e7bdd` after016 closed.
The final batch review must also assess the assembled whole plan after full
integration/E2E/clean build-install checks; no duplicate final review invocation.
Main remains `501b51276a4d07826afcaa1c0cbf09a24a466587`.
No remote merge, CI execution, production-provider operation or plan completion
is claimed. Earlier checkpoints and immutable reports remain in Git.

## Standing user decisions

The latest user request supersedes the earlier
[per-task single-stage decision](single-stage-review-decision.md), which remains
immutable history. Use small dependency-compatible batches, one Sol/xhigh worker
by default, one fresh Astra/xhigh reviewer for every included task and combined
behavior, and focused repair continuation preferably with the same pair. Preserve
task scopes, dependency ordering and isolated worktrees. Reuse verified tests for
unchanged material; rerun affected checks for changes, conflicts or insufficient
evidence. Approval binds every member and exact corrected candidate; preserve
per-task acceptance, cumulative budgets and existing external authority. This is
manual coordination only; frozen runtime two-stage review contracts stay intact.

Implementation of that workflow is now halted in `/root/repair_009_c1`, inherited
Sol/xhigh rank3, native `call_ZFPRFEGLGdbSnEukmGuTYWxi`, charge121, after its009
repair FINAL. Only manual instructions/coordinator
tool and one tracked regression test file are authorized; CURRENT/state remain
ROOT-owned. No additional per-task reviews or new task dispatches while this
change is implemented. Finish this user request with verified changes, a short
workflow table, actual validation and limits; do not claim all39 tasks complete.
Tooling checkout: `.worktrees/manual-batch-workflow`, branch
`ai/PLAN-001/manual-batch-workflow`, base9d8fa977a7f1c4157740438eea7e4e26d22e7bdd.
No PLAN task/schema is added for this direct manual-workflow change. One fresh
Astra/xhigh independent review will assess it before ROOT integration/removal.
Design: explicit validate/prepare-batch/accept-batch, max3 accepted-frontier tasks,
isolated combined candidate, one existing-format report covering every task AC
and all11 checks plus combined behavior. Test reuse is separate from review
context so bookkeeping changes do not force unchanged code tests to rerun.

Before handoff, implementers run relevant tests and review the final diff for bugs,
contract mismatches and applicable edge cases. Fix in-scope issues, add regressions,
rerun affected checks and flag scope blockers promptly. Record actual results,
skips and self-review findings briefly in the existing handoff. No extra stage or
paperwork. Permanent project/implementer guides committed
`f4bce8ea8b0433e0491b1f29b5197a09f1c16977`.

Every rejection uses the existing review report and a concise table with exact
columns **Category | Location | Exact issue | Required fix**. Categories include
Bug, Contract, Tests, Documentation, Evidence and Scope. Complete all applicable
checks before the verdict, consolidating findings in one report. If a failure
prevents further checks, list what remains unreviewed and why. No separate stage
or schema field. Saved permanently in .ai/AGENTS.md, shared docs/agents/README.md
and the existing dispatch brief at `a9e1688113527230ecce9ae2675ada14d778ab06`.
Foundation validation passed: 27 schemas,203 artifacts,39 tasks,581 links.
Read-only current asset-catalog verification also passed for both .codex and
.claude: installed shared reviewer guidance retains the exact rejection columns
and blocked-check disclosure; installed implementer guidance retains self-review.
No installation or temporary script file was created for this check.

Required runtime helpers, regressions, build logic and reusable instructions must
be tracked in owned source/tests/docs and survive clean checkout/install. The
[local material audit](local-material-audit.md) records the tracked manual helpers,
briefs and dispatches. Do not create required runtime behavior in ignored .ai/local.
Read [agent-brief.md](agent-brief.md) and the selected next-*-dispatch reminder.

## Active and queued work

- **009 ready for focused verification**: `/root/repair_009_c1`, fresh Sol/xhigh rank3, native
  `call_7Ikkn0lCOhSdmqgGJNmoYbCE`, charge116/300. Tree TASK-009-a1, failed clean
  candidate `44d9481dc6e65a8ae33e2e472c131852813ba913`, reviewed base
  `1e6477285d37c59a35dee4c9951a3c1bfe4be3f1`, FP
  `8f38ee9238f404798b4031d08c7724fdfda2286cdad831b0d6d36ede9ffe5abf`.
  First review `/root/review_009_c1`, native `call_Uw0t13fyfLrfCRrb11YQ2YMq`,
  charge113, completed all11 checks with six major findings. Full report/table,
  JSON and diagnostic/closing results read; ROOT independently reverified all
  bound identities/hashes. Preserved `038174666608c3a1f9750a17147cb981a21516f7`.
  Findings: lifecycle event bypass; unrelated review identity; mixed command
  success/failure; incomplete registry/references after relocation; unrelated
  relocation source deletion; snapshot-relative archive manifest incompatibility.
  All fit existing009 scope; no prerequisite/graph change established. Actual
  accepted006/007 composition and038 savedsettings/policy roundtrip pass.
  Clean corrected FINAL `fa77907a1981a436f5a8499a38c3a0a8026763d0`, parent failed
  candidate44d9481d. ROOT read full updated handoff and verified exact three-path
  scope/status. Final17 tests pass Windows3.12,93.001s; affected7 pass Windows3.11,
 33.977s and Linux3.11,3.426s. Foundation/compile/diff pass. Self-check also corrected
  final-view validation after manifest materialization, checklist binding and a
  permitted nullable output stream. No blocker. Review009 next when016 closes.
- **015 corrected and ready for a batch**: `/root/repair_019_c1`, inherited Sol/xhigh rank3, native
  `call_ekxbBrQrt3pjDgWB8NqULBg8`, charge119. Same TASK-015-a1 tree, owned three
  paths only. Two major findings: malformed/wrong-kind spec and omitted spec
  document can pass; unchecked N/A can waive every ISO check in new/prior reports.
  All11 checks completed, independent14 tests pass, four bug reproductions plus
  seven positive/negative controls through accepted017. No unreviewed area/blocker.
  Full report/JSON/diagnostic/closing read, ROOT reverified identities and hashes,
  three closing companion hashes. Preserved c34ce82a9ea3871c2449dbe58a8dae62e452d732.
  Original reviewer `/root/review_015_c1`, fresh Astra/xhigh rank4,
  native `call_EzmYq7oQsFHPFn5UhSgNWULo`, charge118. Prefix TASK-015-a1-c1-R1.
  Candidate `d57d1ad29462c44d0156f1b7c74c3256a339b1c7`, FP
  `6477f34e30bb3e5eab397898a72489d6edf77b68c62f1711a02f89cf0f86013e`.
  Coordinator14 tests pass, no skips,8.058s, exact candidate origin.
  Owner `/root/implement_015`, Sol/xhigh rank3, native
  `call_pRwRtyYBRXrXGA7RqWAlbPzz`, charge110. Tree TASK-015-a1, dispatch base
  `17fb6fff9ffa6b160dc1a09da286e3876ea2d5b6`, clean FINAL head
  `9dba72717218d0e7c2bca394da40f5fce2f991b7`.14 tests pass on Windows3.12,
  Windows3.11 and Linux3.11; source origins, compile, foundation and diff pass.
  Self-check fixed output scope and protected prior review inputs; all context
  revalidated after completion. No scope blocker. Full handoff and scope read.
  Corrected FINAL `edbc147a7dcff4f1b76b6909d689516a2ef6ecc4`, clean exact three-path
  diff; full updated handoff read.20 tests pass Win3.12(13.965s), Win3.11(12.159s),
  Linux3.11(15.999s), no skips. Source origins/compile/diff pass. Spec/research
  schema/kind and bounded reference closure now validated; all12 checks must pass
  for new/prior approval; nonapproving N/A remains representable. No further task
  review dispatched; evidence reuse is subject to the new batch verification rules.
- **020 ready for first review**: `/root/repair_019_c1`, inherited Sol/xhigh rank3,
  native `call_IPv5ufcfti6YvOGo5ZGB0pOB`, charge115. Tree TASK-020-a1, dispatch
  base `9614bbf0380b09c4839f340c370538a84279486b`. Clean FINAL
  `3f5d8ab11bc7722f81b8cfd3fa0fc68885a5221b`;18 tests pass Windows3.12,
  Windows3.11 and Linux3.11, no skips. Owner reports final scope/compile/diff
  checks and self-review regressions in the existing handoff. ROOT read the full
  handoff and verified exact clean head and three-path scope; no known blocker.
  Read next-review-gates-dispatch.md.
- **024 accepted after focused c2 PASS**: `/root/verify_024_c2`, fresh Astra/xhigh
  rank4, native `call_IKsYkc5furZCNJo3U3iLcouk`, charge117. Prefix TASK-024-a1-c2-R1.
  Candidate `58cc78312451d7954a4c29b6ba85b6ceec353171`, FP
  `8f2ba197a56ab71a60729dc62f23fde758f305bb70759b55e33d35369816083d`.
  Coordinator current16 tests pass, zero skips,0.803s, exact candidate origin.
  All11 review checks pass, independent16 tests and41 diagnostic checks pass.
  ROOT reconciled frozen identities, raw diff, context/validation/policy hashes,
  owned/dependency bytes, preserved c1 history and3 closing companion hashes.
  Integrated `02ad385c19aa8ad0209a6c4548bdab496aa2a06a`; clean tree removed.
  Existing full review is reconciled and affected corrections verified; no R2.
  Prior clean tested owner head
  `e3770010b6a7d56deda3c851ed6458a8a53d3091`. Existing c1 findings repaired;
  prehandoff self-check also fixed duplicate original acceptance-owner collapse.
 16 tests pass Win3.12/3.11 and clean tracked export; three owned paths. Latest
  owner followup `call_oae5lrvRcmpc86kaUarnJskQ`, charge109. Final diff read.
- **016 repair pending; review closed FAIL**: `/root/review_016_c1`, fresh Astra/xhigh rank4,
  native `call_HdCiOZGmqwHKAE7E7lvfgzu4`, charge120. Prefix TASK-016-a1-c1-R1.
  Candidate `e88e7950fb6bce3656d3de8dad54ace21074d252`, FP
  `160170998f8906e5c944f91cb0e8c60c92fda221d515e2e5d21f9aabc848a5cc`.
  Coordinator18 discovered tests, one Windows symlink privilege skip,0.354s.
  Tree TASK-016-a1, clean owner head
  `0cb81d179b7ffd76012f05f216010ae444f11f98`. Prehandoff self-check fixed visible
  role/acceptance metadata leakage.18 discovered tests on both Windows runtimes
  with1 actual symlink privilege skip; Linux3.11 executes18. Three owned paths.
  Latest owner followup `call_NKsLx2ySQMvDK71Z8WIk7daz`, charge112. Final diff read.
  All11 checks complete; no unreviewed area. Two findings: malformed handoff/R1
  schema fragments count as complete context; unsupported surrogate metadata
  escapes the typed error boundary. Full report/JSON and closing evidence read;
  frozen candidate/context/validation/policy/fingerprint and two report hashes
  independently reconciled. Preserved9d8fa977a7f1c4157740438eea7e4e26d22e7bdd.
  Existing18-test Windows suite and actual Linux1-test link guard pass. No owner
  dispatched for this repair yet; include in the next compatible implementation batch.
- **005 a2 ready for review**: tree TASK-005-a2, clean owner head
  `af3e6e5dabc083bd201114f23a9c71efa715a7bc`. No additional self-check defect;
 11 tests pass Win3.12 andLinux3.11. Cumulative scope only owned test and handoff.
  Latest owner followup `call_MdVuOCsWEPqrMvrrgiTLDAlq`, charge114.

After the manual workflow change is verified, select the next compatible small
batch from stable candidates and pending scoped repairs.009/005/020 are stable;
015 is finishing and016 needs repair. Preserve task ownership and evidence.

## Recent integrations, cleanup and counters

Accepted IDs:001,002,003,004,006,007,008,013,014,017,018,019,024,038,039.
017 c4 accepted `2c0748444f4982118a04b086bfa6d42d418fd1bd` after all11 checks,
36 declared tests and focused both-host checks; seven companion hashes verified.
019 c2 accepted `606acb8b1047b1a23e93a62778e74933a151b353` after all11 checks,
16 tests and focused immutable Mapping checks; six companion hashes verified.
Both exact candidates integrated and their clean worktrees removed.

Clean superseded017a1/a2 checkouts removed through nonforce Git after resolved-path,
cleanliness and retained-branch checks. Heads e79df3b8d071a7e3a3c7874cf0cacb6e704c0205
and b7593f11961aa6f5c3a927f3c49af32c4fa93971 remain on their named branches.
All remaining task checkout copies correspond to pending work; history preserved.

**121/300 conservative invocations used,179 remain. Structural rewrites3/3 used.**
Use tracked count-native-invocations.py against the current root session; count
rejected calls and inherited followups honestly. No runtime active_run is fabricated.
Use coordinator.py status/begin/candidate/accept/fail; preserve failed reports.

Graph r4 task digest: c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e.
Structural graph digest5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337
is SHA256 of sorted compact JSON restricted to schema_version,kind,id,plan_id,
revision,nodes,task_set_sha256. Full compact approved graph digest0ebfff61512855aea359537c2d24926a8c4e0894cb3decf419ca6b6b7e12ef78 differs by approval metadata.

A prior automatic approval review rejected cleanup of temporary clean-export
C:/Users/killi/AppData/Local/Temp/plan001-tracked-cdc76829b83a4c929b47162ea4f7b2c4
with reason only "blocked by policy". Do not bypass or retry that rejected cleanup.
The useful clean-export evidence is tracked. If unresolved at final delivery,
retain the required short separate explanation of the rejection and stated reason.
