# PLAN-001 / TASK-009 a1 c1 — independent implementation review

**FAIL: six major defects prevent acceptance.** All eleven applicable implementation checks were completed, including accepted-interface and consumer compatibility. No check was stopped or left unreviewed because of an earlier finding. This is the user's single independent task stage; scoped corrections require focused continuation on a newly validated exact candidate, with no separate R2.

| Category | Location | Exact issue | Required fix |
| --- | --- | --- | --- |
| Bug — 001 | `src/state.py:831-859` | A project-only event with no evidence commits an existing task from `backlog` straight to `accepted`. Only event-to-projection matching is checked; a lifecycle-changing projection needs no applicable event. | Require every lifecycle mutation to match the appropriate entity kind/from/to event and existing legal transition/gate semantics; preserve zero-plan initialization. Add a rejection regression. |
| Contract — 002 | `src/state.py:1112-1136,2321-2387` | A passing **implementation** review for `PLAN-002/TASK-999` and an unrelated fingerprint commits `PLAN-001/TASK-001` from `review_2` to `accepted`. Real/schema-valid bytes are counted without checking applicability. | Bind available plan/task, stage and current candidate/content identities to the affected qualified record; require its applicable artifacts. Use existing fields, without adding event `plan_id`. |
| Bug — 003 | `src/state.py:1138-1193,2347-2356` | An unrelated exit-zero command plus the required test command with **exit 1**, `Ran 2 tests` and `FAILED` commits `review_1`. Different records satisfy success and command/count checks. | Check the required command's complete success conditions on the **same** evidence record. Add mixed-evidence rejection and genuine passing controls. |
| Bug — 004 | `src/state.py:687-829,861-931` | A plan move to `archived` commits while it remains in `active_plans`, is absent from `archived_plans`, and its moved task points to the deleted current spec. The spec existed before relocation. | Validate the complete resulting registry, lifecycle locations/fields, affected references and manifest consequences; apply permitted changes or reject omissions before publication. |
| Bug — 005 | `src/state.py:992-1049` | Using unrelated `.codex/evidence/keep.txt` as a task's relocation source deletes that evidence, leaves the real current task, creates the completed task, and acknowledges the result. | Require the source to be the qualified record's authoritative file or exact owning bundle; validate destination identity/collisions. Reject before publication and retain unrelated bytes. |
| Contract — 006 | `src/state.py:1052-1083,1215-1222,2266-2318` | A schema-valid archive entry `TASK-001.json`, relative to its snapshot, cannot be admitted: a repository-relative effect fails entry equality; a snapshot-relative effect fails namespace validation. Both fail at generation 0. | Resolve archive entries under their immutable snapshot root and translate effect paths there. Keep asset-manifest semantics separate; add valid archive add/retain/relocation regressions. |

These are existing TASK-009 admission requirements, not a request to implement another task, add a port or schema field, or invent remote/provider observations. All six structured findings are in [the v1 report](TASK-009-a1-c1-R1.json). Update the owned implementation handoff after fixes; its current gate/lifecycle/manifest claims exceed demonstrated behavior.

## Candidate, scope and provenance

Frozen ROOT/base: `1e6477285d37c59a35dee4c9951a3c1bfe4be3f1`. Clean candidate: `44d9481dc6e65a8ae33e2e472c131852813ba913`. [Candidate manifest](candidates/CANDIDATE-TASK-009-a1-44d9481dc6e6.json) fingerprint: `8f38ee9238f404798b4031d08c7724fdfda2286cdad831b0d6d36ede9ffe5abf`.

Raw binary diff SHA-256: `dda1f63c5fd69045c716d00f175f0a8b2786473e8526e7d5614018d38d45ec42`. It contains exactly the three additions `src/state.py`, `tests/unit/state_checkpoints/test_state.py`, and `.ai/plans/current/PLAN-001/evidence/implementation/TASK-009.md`. The complete added source/test/handoff was read. All three blobs plus direct source dependencies equal owner-tested head `cee6a8261431876c50fd4a64f0c7884992bf4c8d`; the newer integration base also contains other accepted source and documents, so the merge is not described as metadata-only.

All context and validation hashes and raw policy+model digest `b8d895be89333b372c65f1f95c3e7e2b911b850a44be3ec8f64dc344ca806a42` were recomputed. Graph r4 remains approved with all 39 tasks and task digest `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`. Structural graph digest is `5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337`, hashing the seven structural fields and excluding approval metadata. Full canonical graph digest `0ebfff61512855aea359537c2d24926a8c4e0894cb3decf419ca6b6b7e12ef78` is distinct. Accepted TASK-002/004/007/008 report/candidate identities, ancestry and current source blobs were verified. Exact details are in [the identity and relocation observations](TASK-009-a1-c1-R1-relocation.json.txt).

Reviewer: independent `/root/review_009_c1`, native invocation `call_Uw0t13fyfLrfCRrb11YQ2YMq`; coordinator-observed OpenAI Astra/xhigh, profile `review_high`, rank 4, conservative cumulative charge 113/300. Implementer: `/root/implement_009`, native `call_EM2WqkcoNZGoyRMqV57EffPI`, Sol/xhigh rank 3, charge 100 at dispatch. These are observed native submission settings. There is **no separately exposed provider-effective model or effort observation**. The structured model fields use that observed native selection under the existing [effort clarification](../evidence/effort-provenance-clarification.md), without inventing new v1 fields. The [single-stage decision](../evidence/coordination/single-stage-review-decision.md) supersedes the old manual R1/R2 schedule, not the product's frozen gates.

## Validation and acceptance assessment

All executions used candidate-first imports and native disposable Git repositories. Windows interpreter: `ROOT/.ai/local/full-plan-venv/Scripts/python.exe`, CPython 3.12.14. The reviewer made no source, candidate, state, policy, task, graph or historical-evidence changes.

| Executed check | Observed result |
| --- | --- |
| `python -B -m unittest discover -s tests/unit/state_checkpoints/ -p test_*.py` | Exit 0; **11 tests**, no skips, **60.205 s**, `OK`. Coordinator's separately bound run reports 11 passing tests in 62.210 s. |
| `python -B src/validate_foundation.py` in candidate | Exit 0; 27 schemas, 201 artifacts, 1 plan, 39 tasks, 280 pairs, 4 archive manifests, 570 links. |
| [Single diagnostic program](TASK-009-a1-c1-R1-probe.py), default run | Six defect scenarios reproduced. Exit 1 solely because its real-runner setup passed inherited Windows environment names rejected by the accepted runner; [initial observations and traceback retained](TASK-009-a1-c1-R1-windows.json.txt). |
| Same program, `--real-ports-only`, after restricting its base environment to explicit allowed names | Exit 0. Actual accepted `LocalCommandRunner`, `FileContentReader`, and `LocalGitRepository` compose; committed read/dedup and actual `RunSettings` plus effective-policy hydration pass; exact developer HEAD, raw index, tracked and untracked bytes remain unchanged. [Results](TASK-009-a1-c1-R1-real-ports.json.txt). |
| Same program, `--relocation-only`, with an actually existing source spec | Exit 0 as a diagnostic: confirms defect 004 still commits stale registry and now-broken task references. Includes expanded final identity/prerequisite verification. [Results](TASK-009-a1-c1-R1-relocation.json.txt). |
| Raw `git diff --check BASE HEAD` and exact candidate status | Exit 0; candidate clean. |

AC1 has passing mechanical evidence for zero-plan transactions, separate plan-qualified repeated local IDs, expected generation, full-tenure OS exclusion, timestamp non-takeover, owner death, direct state-ref/actual-parent checks, isolated owned-path index/CAS and operation deduplication after journal loss. The generic payload path works with actual saved settings and schema-valid policy bytes; `state.py` does not import configuration. The six defects prevent an AC1 pass because invalid decisions and incomplete lifecycle moves are still durably accepted, and valid archive semantics are blocked.

AC2's five explicit seams were reviewed and rerun in the declared suite: before projections, after the first fsynced private projection, before ref publication, after ref publication, and before acknowledgment. Pre-publication retries retain the old authoritative ref; post-publication retries return the original checkpoint/generation. These injected crash signals are in-process abrupt-stop seams; the ownership-death case uses a separate killed process. A staged file or commit object alone does not acknowledge success. The actual-ref CAS race and developer preservation checks pass. Findings 004/005 additionally show why physical atomicity does not establish a semantically complete lifecycle generation.

The prior Windows/Linux 3.11 matrices and final affected reruns were assessed against unchanged owner-tested blobs; unchanged platform suites were not repeated. No remote CI or production provider verification is claimed. There is no required check blocked by identity, access or scope.

## All eleven checklist outcomes

| Check | Result | Assessment |
| --- | --- | --- |
| R1-01 acceptance | Fail | AC1 defects 001-006; mechanical AC2 evidence assessed. |
| R1-02 specification/exclusions | Fail | Existing guard/lifecycle/archive requirements violated; exclusions preserved. |
| R1-03 correctness | Fail | All six defects traced and reproduced. |
| R1-04 errors/cleanup | Fail | Invalid source/consequence claims reach committed effects; normal lock/crash/CAS cleanup paths checked. |
| R1-05 boundaries | Fail | Required negative gate and lifecycle cases fail. |
| R1-06 tests | Fail | Eleven meaningful tests pass, but the reproduced mandatory cases and correct archive-path meaning need tracked regressions. |
| R1-07 scope | Pass | Exactly declared component scope; no established prerequisite gap. |
| R1-08 unrelated changes | Pass | Exact diff and all identities/hashes verified. |
| R1-09 interfaces/maintainability | Pass | Explicit immutable ports; accepted 006/007 and generic 038 composition works. Correctness defects remain separate. |
| R1-10 trust boundaries | Fail | Inapplicable facts authorize state; unrelated committed evidence can be deleted. |
| R1-11 documentation | Fail | Revise existing handoff claims with actual fixes/regressions. |

The same diagnostic's `--verify-reports` mode passed v1 schema, evidence-link and frozen-identity checks; [closing results](TASK-009-a1-c1-R1-closing-final.json.txt) are retained. Its first link check found that the unmerged TASK-009 handoff exists only in the candidate, so the report evidence reference was corrected to the frozen candidate manifest; this was a review-link error, not a candidate failure. The [initial closing observation](TASK-009-a1-c1-R1-closing-initial.txt) is retained. Historical reports and initial diagnostic failures remain immutable. ROOT's disclosed `CURRENT.md` update is outside candidate context; the candidate remains unchanged. The next action is the owner's scoped correction followed by current validation and focused continuation of this review stage.
