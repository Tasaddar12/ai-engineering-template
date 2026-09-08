# PLAN-001 graph r4 independent isolation review

Verdict: **pass** for the complete 39-task graph identified below. Both required r3 rewrites are resolved. No blocking finding or required rewrite remains. The coordinator may record this approval and begin dependency-ready task implementation under the existing task, review, worktree, and authorization rules.

## Provenance and exact approval identity

- Reviewer: `/root/isolation_review`, independent of the coordinator/graph author; this is a new revision-specific review turn by the reviewer who examined r3. The reviewer has edited only review reports and reproduction evidence.
- Coordinator-confirmed original launch: `fork_turns=none`, `model=gpt-6-astra`, `reasoning_effort=xhigh`. Repository role/profile: `task-isolation-reviewer` / `review_high`, capability rank 4. The tool exposed the canonical task name, but no provider-returned model ID or provider invocation UUID. These are actual coordinator invocation settings, not a claim of production-adapter provenance verification.
- Observed integration HEAD: `363dca24a5b6fea722e99d096ebe9741b96d61da`; working tree was clean before this review's new evidence files.
- Reviewed graph: `PLAN-001-r4`, revision 4.
- Structural task SHA-256: **`c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`**, independently recomputed and matching the proposal.
- Structural graph SHA-256: **`5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337`**.
- Exact proposed graph file SHA-256: `080296e0b87d6970289d5ad303999ab63b526512e0b4f6f3b41426918292d903`.
- Canonical complete proposed graph JSON SHA-256: `8651be7fca5fe37ffa5190ea8ec492a9f264822fb121c3a661a5410d4d26df77`.
- Specification JSON SHA-256: `f1d763caf0ab6662ba5c9677162fc30dd8816d5c17b64375e2217f26f5ee35bc`.
- Plan JSON SHA-256: `7ebe18ef5137b04a440ce1f281335b5ec3ac23248cb4c7e116c9d3ec14a97217`.

The task digest is the existing `src/ai.py:structural_task_digest`: sort by task ID, project exactly `STRUCTURAL_TASK_FIELDS`, encode JSON with sorted keys, compact separators, `ensure_ascii=False`, UTF-8, and SHA-256. The structural graph digest applies that encoding to `schema_version`, `kind`, `id`, `plan_id`, `revision`, `nodes`, and `task_set_sha256`. Graph approval status and review pointer are administrative attestations and excluded from that structural graph identity; the full raw/canonical proposal hashes above retain the exact reviewed pre-attestation bytes. Any graph topology, task scope, dependency, acceptance, or contract change requires another isolation review.

## Review scope and r3 resolution

Reviewed the current state, complete plan/spec/graph and all 39 current task contracts, command mappings, normalized file/resource claims, shared contract ownership, prerequisites, acceptance coverage, and bootstrap preservation. A complete semantic comparison against the retained r3 snapshot confirms that only TASK-004 changed: `scope`, `acceptance_criteria`, `output_contracts`, and `size_rationale`. All other task records and all graph nodes/dependencies are unchanged. The accepted schema/architecture/decision contracts and bootstrap source are unchanged from the full r3 review, verified with Git. That established context remains applicable to the complete r4 graph.

**R3-ISO-001 resolved.** TASK-004 now owns `src/install.py` specifically for a bounded helper catalog change. TASK-004-AC3 and its output contract require the full standalone installed flat-module dependency closure throughout implementation, including later CLI growth, and a fresh-target test without source-tree imports. Project-owned content and native provider settings must remain unchanged. Its existing bootstrap regression reference and plan-wide preservation requirements continue to cover provider behavior, dry-run, repeat installation, conflicts, and recovery. TASK-005's installer/catalog reads and TASK-031/037's later installer writes are already downstream, so the new ownership introduces no unordered overlap. Coordinated adoption remains TASK-031; final release packaging remains TASK-037.

**R3-ISO-002 resolved.** TASK-004-AC3 explicitly restricts canonicalization to known plan/task lifecycle locations, requires current-location records to reproduce the bootstrap digest and equivalent moved records to retain approval, and requires actual structural changes to invalidate it. The output contract prohibits stale-hash fallback. TASK-034 continues to preserve the public compatibility symbol until deliberate migration. The task now has an implementable, testable compatibility obligation rather than permission to bypass approval mismatches.

The prior failed review remains failed immutable evidence. The archived r3 graph/spec/plan bytes match the identities recorded by that review. All 90 entries in `history/engine-r3/manifest.json` match their content hashes, and the retained failed Markdown report is byte-identical to its original review-area copy. `.ai/.gitattributes` disables newline transformation under historical snapshots. The archived snapshot was read specifically to verify supersession, change boundaries, and retained evidence.

## Isolation checklist

| Check | Result | Rationale |
| --- | --- | --- |
| ISO-01 Size | pass | Each task has a coherent component outcome and 2–3 acceptance checks. TASK-004's bounded catalog integration has an explicit rationale; all production estimates remain within six. |
| ISO-02 Clarity | pass | Inputs/outputs, owned paths, exclusions, command definitions, acceptance mappings and handoffs are explicit. Digest migration and installed helper preservation now have observable checks. |
| ISO-03 Scope | pass | Source edits use named flat files and task-specific tests/evidence; final reusable documentation is explicitly owned by TASK-037. Canonical state remains coordinator-owned. |
| ISO-04 File overlap | pass | All 280 unordered pairs are free of normalized write/write, write/read, and shared-resource overlap, including the new installer ownership. |
| ISO-05 API/contracts | pass | TASK-001 owns common values; TASK-002 local ports; TASK-003 workflow ports; TASK-039 orchestration ports; TASK-004 validation/digest/helper closure; consumers wait for their handoffs. |
| ISO-06 Schema/data | pass | Schemas are frozen shared inputs; typed logical references can use the existing serialized string fields. No unordered schema or shared-fixture writer is introduced. |
| ISO-07 Hidden dependencies | pass | TASK-004 now covers standalone helper import closure before consumers; TASK-034 owns wiring and TASK-037 owns final build/entry-point packaging. Completion is injected through frozen ports, avoiding reverse imports. |
| ISO-08 Sequencing | pass | Exactly 39 known nodes; graph/task dependency lists agree; no cycles. Prerequisites supply actual contract, code, state or evidence dependencies. |
| ISO-09 Coupling | pass | Existing edges serialize shared installer surfaces. Other task-owned modules, fixtures and evidence remain separate; new public-contract needs must trigger replanning. |
| ISO-10 Split/merge | pass | No mandatory further split or merge. Port owners, service implementations, lifecycle composition and E2E checks remain independent review boundaries. |
| ISO-11 Shared groundwork | pass | Common values, typed ports, schema/digest behavior, project settings and installed dependency handling all have explicit prerequisite owners. |
| ISO-12 Coverage | pass | All AC-01–09 map to implementation and verification. TASK-035 covers parallel/prerequisite/resume/review integration; TASK-036 recovery/delivery/archive; TASK-031/032 integrate init/adoption/upgrade with state/assets/worktrees; TASK-037 checks clean installed payload and platform build configuration. |

## Integration and verification obligations

Integrate dependencies before their consumers start; select eligible tasks by the documented topological order with task-ID tie breaking. Each task attempt uses its own branch/worktree. Serialize integration and renew candidate validation plus both reviews when its base or material context changes. TASK-035/036 consume the combined CLI composition; TASK-037 follows both and owns final packaging/doc payload. All current tasks remain backlog and no previous interrupted attempt is accepted by this graph approval.

The approved scope is the deterministic local engine with fake agent/hosting adapters. Production providers, credentials, paid services and remote publication remain outside these task scopes. Graph approval neither marks the engine implemented nor substitutes for required per-task and final integration reviews. Missing model capability/provenance at a future gate still follows policy; configured role defaults alone do not prove adapter access.

## Actual commands and evidence

Working directory: `D:/Codex Projects/ai-engineering-template`. Interpreter: `.ai/local/full-plan-venv/Scripts/python.exe`.

1. `src/validate_foundation.py`: exit 0; **27 schemas, 122 artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 archive manifests, 173 local links**.
2. Read-only Python semantic comparisons of all 39 task records with `history/engine-r3/tasks/current/`, graph node equality, and historical artifact hashes: exit 0; only the four named TASK-004 fields changed, graph edges unchanged, all 90 manifest entries valid, original graph/plan/spec identities preserved.
3. `git diff --quiet 501b512 HEAD -- schemas .ai/shared .ai/decisions src`: exit 0; reviewed shared contracts and bootstrap source unchanged.
4. `git status --short`, `git rev-parse HEAD`, and `git show --stat --oneline HEAD`: exit 0; observed clean initial tree and the HEAD above.
5. `reviews/r4-isolation-reproduction.py`: exit 0, output retained in `reviews/r4-isolation-reproduction.txt`; independently asserts the complete graph's acyclicity, task/edge equality, normalized scope/resource isolation, command test-path ownership/nonzero-count success rules, and mapped plan acceptance. It recomputes graph/task identities and records raw hashes of all tasks/commands plus plan/spec/contracts/bootstrap inputs.
6. Read-only Python calculation of the structural graph projection defined above: exit 0, digest recorded above.

The actual scripts in commands 1 and 5 are under `src/` and `.ai/plans/current/PLAN-001/` respectively. These checks validate a design and its evidence; future implementation tests, full runtime behavior, Linux CI, and real external integrations have not been executed by this review. No source/task/state mutation was performed.

## Handoff

Record the current approval pointer to `r4-isolation-review.json`, preserving the exact structural graph and task identities. Then implementation may begin with dependency-ready TASK-001 attempt a2 from the approved integration base. Retain the unaccepted earlier attempt through its existing branch/commit. No further planner rewrite is required for this graph.
