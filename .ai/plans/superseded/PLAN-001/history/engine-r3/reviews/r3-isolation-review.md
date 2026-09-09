# PLAN-001 graph r3 independent isolation review

Verdict: **fail — required bounded rewrite before implementation**. The graph is acyclic, its declared task digest is correct, and all nine plan acceptance IDs are mapped. One bootstrap dependency-ownership gap prevents approval of this exact graph. No runnable subset is approved.

## Provenance and reviewed identity

- Reviewer: independent fresh invocation `/root/isolation_review`; no graph, task, source, policy, or canonical-state authorship in this review.
- Coordinator-confirmed invocation configuration: `fork_turns=none`, `model=gpt-6-astra`, `reasoning_effort=xhigh`; repository role/profile `task-isolation-reviewer` / `review_high`, configured capability rank 4. The spawn tool returned the canonical task name only. No provider-returned model ID or separate provider invocation UUID was exposed; this is invocation configuration provenance, not a production adapter verification claim.
- Repository HEAD observed: `501b51276a4d07826afcaa1c0cbf09a24a466587`.
- Graph: `PLAN-001-r3`, revision 3, proposed.
- Exact graph file SHA-256: `f2a9d441a28fc884d582fb2e4eb6312b020150105d75f7fabc7a49be07c0f065`.
- Canonical full graph JSON SHA-256: `999ba9ce149b52a264a59f559afc2567390aa3084c1ba1120dac5258a4367e6e`.
- Recomputed structural task SHA-256: `79f1137d5bfc5cb0a5148b4d0f3d67487d5a7ff43ab218ea00e04c3bad315883`, matching `graph.json`.
- Specification JSON SHA-256: `f1d763caf0ab6662ba5c9677162fc30dd8816d5c17b64375e2217f26f5ee35bc`.
- Plan JSON SHA-256: `993792abaaf6ea80c5d4d70ec8ddc5d166ab53cb5755cb34293cbc4dd33a5327`.

The raw graph digest hashes the exact file bytes. The canonical graph digest hashes UTF-8 JSON with sorted keys, compact separators, and `ensure_ascii=False`, including the current proposal status and null review reference. The structural digest uses the current `src/ai.py:structural_task_digest`: sort tasks by ID, project exactly `STRUCTURAL_TASK_FIELDS`, then use the same canonical JSON encoding and SHA-256. Lifecycle status, attempts, and task-record file locations are excluded; physical references inside structural fields are currently included. These different identities must not be confused.

Inputs read: repository instructions/state; role index and isolation reviewer guide; plan/spec/graph; all 39 current task records and all command definitions; all five accepted ADRs; policy/model configuration; architecture/service contracts/Python/CLI/validation strategy; state persistence/transitions/invariants; isolation/execution/delivery/project-lifecycle workflows; security design; referenced research record; representative schema fields; bootstrap source inventory and actual installer/CLI/validator code. Historical implementation was not reused as accepted work.

## Blocking finding R3-ISO-001 — installed helper dependency closure has no early owner

Severity/category: blocking structural. Affected acceptance: AC-01, AC-08, AC-09. Affected tasks: TASK-004, TASK-034; ownership sequencing also concerns TASK-005, TASK-031, TASK-037.

TASK-004 owns the new `src/contracts.py` and `src/validate_foundation.py`, and must expose the lifecycle-neutral contract consumed by the validator. That introduces at least `contracts.py` and its domain-value dependency into the standalone installed validator's runtime closure. However, `src/install.py` currently constructs its helper catalog from only `ai.py` and `validate_foundation.py` (line 205), and TASK-004 cannot edit the installer. The first installer writer is TASK-031, substantially downstream. TASK-034 later expands `ai.py` into a runtime composition entry point before TASK-037's final packaging update, presenting the same problem again if the installer list remains fixed.

The concrete trigger is a fresh installation from an accepted intermediate implementation: executing the installed validator or CLI outside the source checkout cannot import newly required modules. That regresses the explicitly preserved self-contained bootstrap and would force an out-of-scope installer fix or a hidden fallback implementation. Deferring final wheel/build packaging to TASK-037 does not permit breaking the working source installer at earlier task acceptance.

Required rewrite: grant TASK-004 narrowly described write ownership of `src/install.py` for the helper-module dependency catalog, and add acceptance covering a deterministic complete flat-module dependency closure for installed CLI/validator helpers as their imports grow. Require an owned regression test that installs into a fresh target and runs helpers without source-checkout import availability. Explicitly preserve provider namespaces, dry-run, idempotence, conflicts, and project-owned content. Keep coordinated adoption in TASK-031 and final build/release packaging in TASK-037. Existing transitive edges already place all relevant installer readers and later writers after TASK-004; verify overlaps again after changing scopes. An alternative is a clearly specified staged migration that proves the validator remains self-contained until the catalog owner acts, but it must not invent an incomplete fallback to hide missing dependencies.

## Required clarification R3-ISO-002 — lifecycle digest compatibility

Severity/category: major structural clarification. Affected acceptance: AC-01, AC-03, AC-07. TASK-004's new lifecycle-neutral digest must not silently invalidate the active approval or treat an arbitrary old digest as trusted. Existing `src/ai.py` keeps physical plan paths in its structural projection, and TASK-034 preserves that public symbol until deliberate migration. State/graph/archive consumers need one defined interpretation during the interval.

Make TASK-004's output contract explicit: reproduce the digest of unchanged current records; normalize only recognized record-location components when comparing equivalent lifecycle relocations; retain scope/dependency/acceptance/contract content in the hash; reject genuinely changed structures. Preserve the compatibility entry point until its consumers migrate. If the new format cannot reproduce a reviewed identity, record a versioned migration with fresh approval rather than waiving a mismatch. Schema reference strings can carry logical encodings, so this review does not require speculative schema edits merely to add `RecordRef`.

## Checklist

| Check | Result | Evidence and reasoning |
| --- | --- | --- |
| ISO-01 Size | pass | 39 component tasks, each with two acceptance checks; declared production estimates 3–6. Test-only TASK-035/036 estimates are conservative rather than required source edits. |
| ISO-02 Clarity | fail | Inputs, outputs, exclusions, commands, and handoffs are present, but TASK-004's compatibility transition needs the explicit clarification above. |
| ISO-03 Scope | pass | Exact source files and task-specific test/evidence prefixes. TASK-037's `docs/` scope is a named final product payload, not general repository write authority. |
| ISO-04 File overlap | pass | 280 unordered pairs checked: no declared write/write, write/read, or semantic resource collision. TASK-037 follows all consumers before final docs/installer edits. |
| ISO-05 API/contracts | fail | Core values, local ports, workflow ports, and orchestration ports have distinct prerequisite owners. The bootstrap helper dependency contract has the missing early owner described in R3-ISO-001. |
| ISO-06 Schema/data | pass | Existing schemas are frozen shared inputs; no proposed concurrent schema writer. Logical references can be represented by existing string fields with typed decoding. |
| ISO-07 Hidden dependencies | fail | Static installed-helper inventory omits new dependency closure before its later catalog owners run. |
| ISO-08 Sequencing | pass | All 39 nodes exist, task and graph dependencies agree, no cycles; prerequisites name real handoffs. Later execution completion is injected through TASK-039 rather than a reverse import. |
| ISO-09 Coupling | fail | TASK-004 cannot satisfy installed-validator preservation without the bounded ownership change or an explicit migration strategy. |
| ISO-10 Split/merge | pass | Value/port/service/test boundaries are independently reviewable. No mandatory decomposition change beyond the bounded ownership rewrite. |
| ISO-11 Shared groundwork | fail | Main shared contracts are early owned prerequisites; installed runtime dependency closure and digest compatibility must also be settled early. |
| ISO-12 Coverage | pass | All AC-01–09 map to implementation and verification work. TASK-035 covers parallel/dependency/resume/review composition; TASK-036 recovery/delivery/lifecycle; TASK-031/032 verify state/assets/worktrees during initialization and upgrades; TASK-037 verifies installed closure/platform packaging. |

## Commands actually executed and results

Working directory: `D:/Codex Projects/ai-engineering-template`.

1. Read-only PowerShell `Get-Content`, `rg --files`, and focused `rg -n` inspections of the inputs named above: succeeded. Some combined outputs were truncated; current task records were reread in complete compact JSON batches before the verdict.
2. `.ai/local/full-plan-venv/Scripts/python.exe src/validate_foundation.py`: exit 0; 27 schemas, 121 validated artifacts, 1 plan, 39 tasks, 280 unordered pairs, 3 archive manifests, 173 local links.
3. Read-only Python identity/command/schema inspection using the same interpreter: exit 0; recomputed the identities above, checked all 39 command definitions use owned test directories and `unittest_nonzero_count`, and inspected plan-qualified reference representation.
4. `git status --short` and `git rev-parse HEAD`: exit 0; status output was empty at that observation, HEAD recorded above.
5. `.ai/local/full-plan-venv/Scripts/python.exe .ai/plans/current/PLAN-001/reviews/r3-isolation-reproduction.py`: executed with output retained in `r3-isolation-reproduction.txt`; asserts graph/task edge equality, acyclicity, normalized path/resource isolation, mapped acceptance, and all task command checks. It also records raw hashes for graph/spec/plan/tasks/commands and the relevant bootstrap/contracts files.

The validator is a foundation structural validator, not an implementation proof. The 39 task test commands describe future tests and were not executed as implemented behavior. The coordinator separately reported 24 passing bootstrap tests; this reviewer does not relabel that report as a personally executed test run. No Linux CI, production provider, remote hosting, publishing, or runtime completion was exercised or claimed.

## Handoff

Preserve this failed report as immutable r3 evidence. Apply the smallest task/scope/contract clarification, advance the graph revision, recompute the structural digest, and obtain independent review of the complete new graph before any task implementation. The amended graph can reuse the acyclic dependency design, but this report approves neither r3 nor a future revision. Actual task implementation should use the user's Sol/xhigh override, with fresh Astra/xhigh implementation and consistency reviews bound to each exact candidate.
