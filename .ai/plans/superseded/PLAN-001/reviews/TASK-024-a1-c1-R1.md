# TASK-024-a1 / cycle 1 / R1 implementation review

**Verdict: FAIL.** Three major defects affect required recovery proposal behavior. No R2 exists or is authorized by this report.

- Candidate: `8805c35ec655ac5c1a8fef24ede1fec1e2bb7129`; review base: `67e41a2d16040f860a5d716a82ddccc7e3d0d3f4`.
- Manifest: `.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-024-a1-8805c35ec655.json`; fingerprint: `16a689e22f0a424685c0b1c0b04abaf8488571da42855c897ff106a88bd18f38`.
- Owner FINAL: `c1423e43b872caa25537fac3cb2641f0b9bf8009`, original base `17595809d6ee74b2585265d94535cb1630d3a900`. The three scoped files are unchanged from owner FINAL after the coordinator metadata merge.
- Checklist: `PLAN-001-v1`; request `request-TASK-024-a1-c1-R1-8bd592c0`; invocation `manual-review-TASK-024-a1-c1-R1-8bd592c0`.
- Fresh independent session `/root/review_024_c1_r1`; implementation session `/root/implement_024`, invocation 73. Coordinator-observed native review submission: OpenAI `gpt-6-astra` / `xhigh`, `review_high`, rank 4; implementation: `gpt-5.6-sol` / `xhigh`, rank 3. These are observed native configurations, with no separate provider-returned effective model/effort claim, per `evidence/effort-provenance-clarification.md`.

## Evidence and validation

Read candidate instructions/state, implementation-reviewer role, selected task/plan/spec, current graph and r4 isolation, frozen service/recovery/review contracts, explicit ADR-001–005, accepted TASK-013/014/039 handoffs and source, candidate source/tests/handoff and raw Git diff. The tracked coordinator focus note was treated as a question, not a verdict.

- Independently verified exact ROOT base and clean candidate head/ancestry, raw binary diff SHA-256, all 14 committed context hashes, both ROOT validation hashes, raw policy-plus-model digest and canonical candidate fingerprint. The r4 structural digest recomputed from all 39 records matches the passing isolation report: `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`.
- Reconstructed changed paths: `src/recovery_proposals.py`, `tests/unit/planning_recovery_proposals/test_recovery_proposals.py`, and the TASK-024 handoff only. Verified owner FINAL and all three dependency acceptance commits are ancestors.
- Independently ran declared leaf discovery using `ROOT/.ai/local/full-plan-venv/Scripts/python.exe` from the candidate cwd with candidate `src` explicitly first: **13 tests, 0 failures, 0 errors, OK**. Verified actual origins of recovery, graph, scope and orchestration modules. Manifest evidence independently hashes to passing 13-test Windows Python 3.12 and 3.11 runs. No Linux repetition was needed for this pure behavior review.
- Ran [independent diagnostic probes](TASK-024-a1-c1-R1-probes.py), exit 0; [actual output](TASK-024-a1-c1-R1-probes.txt). Assertions reproduce the three defects and passing controls; exit 0 is diagnostic success, not product acceptance. They use actual accepted contracts/graph/scope/readiness, with tracked owner-test builders only for fixture construction.
- Required runtime source, tests and usage handoff are tracked. The existing local interpreter is execution infrastructure; no runtime behavior or required helper depends on ignored `.ai/local`, the ROOT editable source, or session-created fixture code. Review diagnostics are retained under this report prefix.

## Checklist

| Check | Result | Decisive evidence |
| --- | --- | --- |
| R1-01 | fail | AC1 is not met: permitted ownership reassignment is rejected, split exits can omit required successor completion, and preserved augment criteria block the next rewrite. AC2 guards have meaningful passing evidence. |
| R1-02 | fail | REQ-06/AC-06 and the frozen recovery workflow require bounded prerequisite/follow-up recovery and repeated lineage-preserving rewrites; F1 and F3 prevent these. Pure TASK-025 exclusions are respected. |
| R1-03 | fail | The source-subset predicate rejects legitimate ownership changes; dependency targets lack successor-completion coverage; the criterion index discards identical repeated IDs before consulting mapped owners. |
| R1-04 | pass | Observed failures return immutable typed issues. Overshoot remains representable and rejects without clamping. This pure module owns no process, file, lease or cleanup effects. |
| R1-05 | fail | The independent early-exit and second-rewrite probes expose boundary failures despite valid typed inputs, full graphs and remaining rewrite budget. Historical namespaces and completed identity have passing controls. |
| R1-06 | fail | The candidate-local 13-test suite passed and exercises meaningful negatives, but it misses exit-set completeness and successive recovery, and its resource-fixture corrections encode the F1 restriction. |
| R1-07 | pass | Changes remain in TASK-024 ownership; no frozen DTO/schema edits, unaccepted implementations, isolation approval, state mutation or TASK-025 effects were introduced. |
| R1-08 | pass | Raw Git diff contains exactly the new recovery module, declared test leaf and handoff. All three files match owner FINAL; accepted dependency commits remain ancestors. |
| R1-09 | pass | The explicit flat-module API uses detached frozen full records and accepted typed contracts, graph and scope services. Required source/tests/handoff are tracked; no runtime dependency on ignored local helpers or an editable ROOT source was found. |
| R1-10 | pass | Caller-verified byte/content provenance is an explicit producer boundary. Permission-set expansion, increased limits, lowered counters and premature approval are rejected; actual accepted scope conflicts consume graph-derived reachability. |
| R1-11 | fail | The handoff accurately exposes the single-source assumption but calls it required authority and claims complete recovery acceptance; F1-F3 require corrected behavior, tracked regressions and updated boundary guidance. |

## Findings

### R1-TASK-024-001 — major

The single-source scope-subset gate rejects an allowed recovery ownership change. On the actual 39-node PLAN-001 r4 records, augmenting TASK-024 with fresh TASK-100 and unchanged TASK-024 acceptance, plan content, local_execute permission and ordered scopes passes with inherited ownership. Changing only its path to src/recovery_proposal_acceptance.py, or only its resource to component:planning/recovery_proposal_acceptance, produces only permission_expansion despite a valid 40-node DAG. Frozen recovery workflow lines 3, 7, 9 and 16 permits required out-of-scope prerequisites/follow-ups within unchanged product/permissions, and recovery-replanner responsibility 6 explicitly reassigns path/resource ownership. A proposed task scope is not an authority grant or isolation approval.

Location: `src/recovery_proposals.py:461`, `src/recovery_proposals.py:910`, `.ai/plans/current/PLAN-001/evidence/implementation/TASK-024.md:134`. Reproduction: `.ai/plans/current/PLAN-001/reviews/TASK-024-a1-c1-R1-probes.txt`.

Required correction: Validate reassigned task ownership against the unchanged product/permission authority rather than requiring every fresh claim to fit one predecessor. Make any needed bounded authority facts explicit in the scoped proposal input or collaborator without changing frozen contracts; retain prohibited-path, permission-subset, whole-graph conflict and fresh-isolation checks. Add positive new exact-path/resource regressions and retain genuine authority-expansion negatives.

### R1-TASK-024-002 — major

Dependency redirection trusts dependency_target_ids without checking whether they cover completion of required successors. Split TASK-100 (AC1, AC2) into TASK-300 (AC1) then TASK-301 (AC2, depends on TASK-300), map the exit to TASK-300, and redirect the former dependent TASK-200 to TASK-300. The validator returns admissible with no issues. With only TASK-300 integrated, the actual TASK-013 ready_frontier returns both TASK-200 and TASK-301, so TASK-200 can run before the required AC2 successor finishes.

Location: `src/recovery_proposals.py:142`, `src/recovery_proposals.py:933`, `src/recovery_proposals.py:951`. Reproduction: `.ai/plans/current/PLAN-001/reviews/TASK-024-a1-c1-R1-probes.txt`.

Required correction: Require the declared dependency targets to cover completion of all required successor work through the validated graph: each required successor must be a target or a transitive prerequisite of a target. Reject early/incomplete exit sets while retaining the valid last-node and multiple-exit cases. Add a regression using actual accepted graph readiness.

### R1-TASK-024-003 — major

An admissible augmentation makes a subsequent recovery fail on its own preserved acceptance. AUGMENT TASK-100 with TASK-300 retaining identical AC1/AC2 content and mapping the criteria to TASK-300; this passes. Carry that graph forward as approved, advance used_rewrites from 1 to 2 (max 3), and replace TASK-300 with fresh TASK-400 preserving its content, prerequisites and permissions. Both criteria now exist on retained TASK-100 and TASK-300, so _criterion_index drops them globally and validation rejects only ambiguous_original_acceptance. The explicit original mapping already identifies TASK-300, and the duplicated content is identical.

Location: `src/recovery_proposals.py:411`, `src/recovery_proposals.py:770`. Reproduction: `.ai/plans/current/PLAN-001/reviews/TASK-024-a1-c1-R1-probes.txt`.

Required correction: Resolve criterion content through the explicit plan-local original acceptance owners/mapping, accepting identical preserved copies created by earlier valid recovery while rejecting missing owners or conflicting content. Add a multi-rewrite augment-then-replace regression with cumulative budgets/history preserved.

## Scope-question resolution and handoff

The frozen workflow distinguishes task decomposition from expanded product scope: `.ai/shared/workflows/recovery.md:3` triggers recovery for required out-of-scope edits; lines 7, 9 and 16 allow prerequisite/follow-up proposals while preserving product scope and permissions. `docs/agents/recovery-replanner.md:23` explicitly requires reassignment of path/resource ownership. The source-subset rule is therefore an implementation restriction, not a frozen requirement. F1 changes only ownership for the already-required TASK-024 acceptance behavior, preserves the actual plan and all prior task records, and remains a proposed graph awaiting fresh isolation. A new semantic ownership label alone grants no external permission. Correcting this does not authorize arbitrary product expansion.

TASK-025 remains responsible for quiescence, isolation invocation, durable application and resume. No finding requires those effects in TASK-024. Return the three defects to a fresh implementation attempt with tracked regressions; a material repair needs new candidate evidence and fresh R1 before R2. Reports and diagnostics become immutable at FINAL.
