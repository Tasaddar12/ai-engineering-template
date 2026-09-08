# PLAN-001 / TASK-005 future import-closure assessment

The suspected integration blocker is confirmed. The current repository assertion in
`tests/unit/templates/test_assets.py:136–142` rejects valid growth of the reachable flat-module
closure even though both accepted production implementations already support that growth.
This is a bounded TASK-005 test/handoff follow-up opportunity. The evidence does not establish
a need to redesign the graph, change a public API, or modify another task's source.

Assessment session: `/root/assess_005_closure`, 2026-09-08. Role: bounded coordinator/planning
assessment, with independent local reproduction. ROOT was frozen at
`43c8004c7313105f63d3b8d21726f8a056b96842`. Native Astra/xhigh, planning/review rank 4 was
coordinator-observed; no provider-returned effective model, effort, or invocation identity is
claimed. This report is not an R1/R2 verdict or approval of a new candidate.

## Contract and ownership findings

- [TASK-005](../../tasks/current/TASK-005.json) is accepted and owns `src/assets.py`,
  `tests/unit/templates/`, its implementation handoff, and `docs/defaults/FRAMEWORK.json`.
  Its AC1 requires deterministic discovery; AC2 requires manifest/hash and path integrity.
  Neither criterion imposes a permanent four-tool maximum.
- The [accepted handoff](../implementation/TASK-005.md) identifies the four current tools as
  the observed reachable closure, describes `assets.py` and `workflow_ports.py` as *unwired*,
  and explicitly leaves eventual complete runtime closure to TASK-037. The accepted
  [R1](../../reviews/TASK-005-a1-c1-R1.md) and [R2](../../reviews/TASK-005-a1-c1-R2.md) bind
  candidate `0216c03b18698a3ff4bc89c9b0ae9749255425ef`, fingerprint
  `e38bebfb47b00e775c3c8462a7051f21cd41313ebd268c7b6426852e27010e58`.
  R1's preserved `test_05_source_failures_and_transitive_tool_cycle` also explicitly expected
  six reachable modules and excluded an unreachable fixture module. Its pass supports the
  dynamic API behavior; it did not run the unchanged owned suite against that grown fixture.
- `assets._tool_source_refs` (`src/assets.py:510–571`) and `install._tool_sources`
  (`src/install.py:174–215`) both walk absolute flat local imports transitively from `ai.py`
  and `validate_foundation.py`, deduplicate visited modules, and enforce the four required
  helpers as a floor. Neither implementation blacklists `assets.py` or `workflow_ports.py`.
  `build_owned_asset_catalog(source_root, provider_root, *, registry=None)` and the accepted
  installer payload already include the discovered modules. TASK-004's accepted handoff
  explicitly describes this required-module floor and exclusion of unrelated modules.
- [TASK-034](../../tasks/current/TASK-034.json) must wire the six CLI workflows using typed
  dependency composition. Its source/test scope is `src/ai.py` and `tests/unit/cli/`.
  [TASK-037](../../tasks/current/TASK-037.json) AC1 and output contract require the complete
  flat-module dependency closure, including every runtime dependency introduced through
  TASK-034. Its test scope is `tests/package/`; it may also change the installer, packaging,
  documentation, and CI. Neither task owns `tests/unit/templates/`.
- Approved graph `PLAN-001-r4` retains structural digest
  `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` and its passing isolation
  record. Its direct TASK-005 consumers, TASK-031 and TASK-032, are still recorded as backlog
  with no attempt IDs; TASK-034 and TASK-037 are also backlog. These records support a
  prospective prerequisite follow-up before consumer dispatch, subject to the coordinator's
  current lease and Git checks.

For any closure that retains the required four modules and gains at least one additional module,
the equality at line 136 necessarily fails. Relaxing only that equality is insufficient:
lines 140–142 still unconditionally reject the named modules when they become reachable.
The exact downstream module list is not yet implemented or asserted here. The contradiction
concerns valid closure growth, not every imaginable CLI implementation strategy.

## Executed reproduction

The [verified proof](TASK-005-future-closure-verified.py) and its
[complete command results](TASK-005-future-closure-verified.txt) are new assessment artifacts.
It copied `src`, canonical docs/schemas, and the owned test directory into a uniquely owned
directory beneath `.ai/local`. It used the existing development interpreter with bytecode
writes disabled. The owned test file remained byte-identical throughout.

| Copied-source case | Unchanged TASK-005 discovery | Independent behavioral checks |
| --- | --- | --- |
| Baseline | Exit 0; 10 tests; OK | Original accepted four-tool state |
| Add a real `ai.py` import of a new helper, whose import reaches a new leaf; add an unreachable sentinel | Exit 1; 10 tests; exactly one failure at line 136 naming the helper and leaf | Six-module exact closure; sentinel absent; Codex/Claude managed bytes match installer; seed destinations match; manifests and tool hashes verify; emitted CLI help exits 0 |
| Additionally import the existing `assets` and `workflow_ports` modules from copied `ai.py` | Exit 1; 10 tests; exactly one failure at line 136 naming the four added modules | Eight-module exact closure; same provider parity, manifest/hash checks, and emitted CLI smoke pass; both fixed exclusions are now false requirements |

The copied entry-point imports were inserted after the future import, so they execute during
CLI startup. Only copied source was changed. The independent probe used explicit expected
fixture module sets, checked the required floor, and checked that the unused sentinel did not
ship. Its implementation imports resolved to the copied source. The CLI smoke ran from an
unrelated directory under `-I -B`, explicitly exposing only the emitted tools directory for
local flat imports. This demonstrates executable fixture growth; it does not claim that the
future six workflows or platform packaging matrix have been implemented.

The [initial proof](TASK-005-future-closure.py) and [initial results](TASK-005-future-closure.txt)
are retained unchanged. That run already reproduced the baseline/growth result and provider
parity, then failed an optional smoke because it invoked a flat script directly with `-I`,
which removes the script directory from the import search path. The verified proof corrects
only that smoke harness by inserting the emitted directory explicitly. Both owned temporary
directories were containment-checked and removed. No initial failure is represented as a pass.

## Minimal correction and verification recommendation

Have the TASK-005 owner make a bounded follow-up in its already owned test/handoff paths after
the coordinator releases the frozen integration baseline. No production change is necessary
for this finding.

1. Retain the real-tree Codex/Claude managed-byte and seed-destination parity assertions and
   the existing ownership, manifest, hash, path, and immutability coverage. Replace the
   four-module equality on the live repository with the accepted required-module floor.
   Remove unconditional live-repository exclusions based solely on current module names.
2. Keep exact inclusion/exclusion coverage in a controlled, test-owned flat-module fixture
   whose entry-point imports are explicitly authored. Assert the exact baseline set there,
   then assert direct and transitive helper inclusion after adding a reachable import, and
   exclusion of an explicitly unreachable sentinel. Named modules can be asserted absent
   only while that fixture leaves them unwired. This prevents a blanket "copy every module"
   implementation from passing and prevents a shared omission in both production walkers
   from being hidden by parity alone. Do not replace independent expectations with the
   production walker's output as the sole oracle.
3. Record in the follow-up handoff that the four-tool count was a baseline observation and
   that the required floor, reachability, payload parity, and ownership are the lasting
   guarantees. Preserve accepted candidate/review history and the existing evidence bytes;
   identify the new test/handoff candidate separately.

Verification should run the nonempty declared TASK-005 suite on the new candidate, exercise
the controlled growth/unreachable fixture, and repeat the unchanged-suite reproduction on
a copy of that candidate with a new valid reachable import. The latter should now pass,
while deliberate reachable-helper omission or accidental sentinel inclusion should still
be detected. Run the existing bootstrap regression command and repository foundation
validation, and record the actual new results. The new candidate requires fresh independent
R1 and R2; the historical passes do not approve the material test change. None of these
future checks or reviews is claimed to have occurred in this assessment.

This recommendation stays within TASK-005's declared ownership and accepted dynamic API.
There is no demonstrated structural reason to assign the test to TASK-034/TASK-037 or rewrite
the graph. The coordinator owns the bounded follow-up dispatch, review/integration sequencing,
and any lifecycle record decision. This assessor has made none of those decisions or edits.

## Remaining risk and preservation

Until corrected, an integration gate that executes TASK-005 after valid wiring growth will
fail on this historical cardinality assertion. Deferring it to TASK-034/TASK-037 would leave
those owners unable to repair the test within their approved paths. After the test correction,
TASK-031 still owns installer/catalog integration, TASK-034 still owns real runtime wiring,
and TASK-037 still owns final closure packaging and platform verification. This assessment
does not preapprove those integrations or rule out unrelated later API/parity changes.

The verified proof checked 124 existing review/source/control/handoff files before and after:
all snapshotted bytes were unchanged, including all then-existing review files. ROOT stayed
at the dispatched commit and `git diff --exit-code HEAD --` passed before and after. Existing
TASK-002 review outputs were left untouched; additional concurrent review files are not this
assessment's outputs. Only this new report and same-stem proof files were written outside
the removed `.ai/local` fixtures. No task worktree was accessed, and no source, task status,
policy, graph, accepted handoff, accepted review, or failed review was modified.

FINAL: bounded assessment complete; source access stops here.
