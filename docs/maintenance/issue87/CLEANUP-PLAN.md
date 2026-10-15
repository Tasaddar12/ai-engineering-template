---
phase: issue87-maintenance
plan: cleanup
type: execute
wave: 2
depends_on: [guards]
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
input_revision: 4c35d27436add6867934c85eb9e853bd2fc3052e
files_modified:
  - .ai/hooks/destructive-git-guard.py
  - .ai/runtime/lib/destructive_guard.py
  - tests/test_destructive_guard.py
  - .ai/hooks/README.md
  - .ai/references/destructive-operations.md
  - .ai/commands/cleanup.md
  - .ai/workflows/cleanup.md
  - .agents/skills/cleanup/SKILL.md
  - .ai/commands/README.md
files_deleted: []
autonomous: true
requirements: [ISSUE87-CLEANUP, ISSUE87-RED]
acceptance: [I87-A2, I87-A3]
documentation:
  - .ai/hooks/README.md
  - .ai/references/destructive-operations.md
  - .ai/commands/cleanup.md
  - .ai/workflows/cleanup.md
  - .agents/skills/cleanup/SKILL.md
  - .ai/commands/README.md
resources: []
checks:
  - [python, -m, unittest, discover, -s, tests, -p, test_destructive_guard.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install.py, -k, registered_hooks, -v]
user_setup: []
must_haves:
  truths:
    - Cleanup defaults to a read-only preview of owned clean integrated work with matching terminal PR/MR evidence.
    - Open, unknown, dirty, ignored, untracked, unowned, protected and unique unmerged work remains preserved.
    - Apply needs actual human approval of the exact pinned deletion list and refuses stale state before deletion.
    - Final results report removed, preserved and failed targets truthfully, including partial outcomes.
  artifacts:
    - path: .ai/runtime/lib/destructive_guard.py
      provides: Shared guard evidence extended with pinned preview and apply
    - path: .ai/workflows/cleanup.md
      provides: Exact-list human approval and final-state reporting
    - path: tests/test_destructive_guard.py
      provides: Offline provider, stale-state, approval and partial-result scenarios
  key_links:
    - from: .ai/commands/cleanup.md
      to: .ai/workflows/cleanup.md
      via: Canonical workflow routing mirrored by the cleanup skill
    - from: .ai/workflows/cleanup.md
      to: .ai/hooks/destructive-git-guard.py
      via: Explicit installed-host cleanup-preview and cleanup-apply subcommands
---

<objective>
Add safe reusable cleanup on the guard parent commit.

Purpose: Preserve work unless exact terminal/integration/ownership evidence and fresh human deletion approval establish eligibility.
Output: Standalone preview/apply entrypoint, cleanup command/skill/workflow and focused evidence, committed as the child's own delta.
</objective>

<execution_context>
@.ai/commands/execute-phase.md
@.ai/templates/summary.md
@.ai/references/methods/tdd.md
@.ai/runtime/TEMPLATE-CONTRACT.md

Authorized upstream maintenance, not an adoption phase. I87-A2 and I87-A3 alias CONTEXT acceptance 2 and 3. The requirement IDs are maintenance-local aliases. Implementation is authorized; deleting real worktrees/backups, merging and issue closure are not. The coordinator creates this child checkout from the returned guard tip and supplies its committed SUMMARY. Execution must not begin from the original maintenance base without that dependency.
</execution_context>

<context>
@docs/maintenance/issue87/CONTEXT.md
@docs/maintenance/issue87/GUARDS-PLAN.md
@docs/maintenance/issue87/GUARDS-SUMMARY.md
@.ai/references/git-workflow.md
@.ai/references/worktree-path-safety.md
@.ai/references/worktree-recovery-policy.md

Reuse GUARDS-PLAN's command grammar, offline provider matrix, fail-closed evidence and command_segments(payload) interface. Preserve that parent's behavior. Shared sequential ownership: .ai/hooks/destructive-git-guard.py, .ai/runtime/lib/destructive_guard.py, tests/test_destructive_guard.py, .ai/hooks/README.md and .ai/references/destructive-operations.md. These paths cannot have active guard/planning-hook writers during this child. No .ai/install.py, .ai/runtime/phase.py, .ai/runtime/lib/worktrees.py, .ai/RULES.md or provider adapter edits.
</context>

<tasks>
<task type="auto" tdd="true">
  <name>CLEANUP: add preview and exact approved apply using the guard's pinned evidence</name>
  <files>.ai/hooks/destructive-git-guard.py, .ai/runtime/lib/destructive_guard.py, tests/test_destructive_guard.py, .ai/hooks/README.md, .ai/references/destructive-operations.md, .ai/commands/cleanup.md, .ai/workflows/cleanup.md, .agents/skills/cleanup/SKILL.md, .ai/commands/README.md</files>
  <read_first>GUARD slice's committed implementation SUMMARY and all changed files, docs/maintenance/issue87/CONTEXT.md, .ai/commands/clean-planning.md, .ai/workflows/clean-planning.md, .agents/skills/clean-planning/SKILL.md, .ai/commands/README.md, .ai/runtime/lib/worktrees.py (existing read-only ownership/listing interfaces); read each assigned destination if it exists</read_first>
  <behavior>
    - cleanup-preview never removes files/refs, prunes worktrees, fetches or changes planning/session records. It reports eligible and preserved rows with evidence and reasons.
    - Only clean owned targets with matching MERGED/CLOSED or merged/closed PR/MR evidence are eligible. Closed-unmerged work with unique commits is preserved; closed alone proves no integration. Protected/current/primary, open, unknown, dirty, ignored, untracked, locked, unowned and detached targets are preserved.
    - Approval missing, broad text, wildcard paths, another repository, extra/missing/changed operations, changed ref/path/provider/status/ownership/backup content, duplicate entries, symlink escape or reused consumed approval refuses before the first deletion.
    - Approved fixture worktree/branch deletion and separately approved exact backup removal succeed; command failures produce per-item results and final reinspection, never a fabricated all-clean success.
  </behavior>
  <action>
Depend on the completed GUARD slice; add failing behavior assertions before extending its source, and preserve RED/GREEN evidence. Extend the same entrypoint with cleanup-preview --repo PATH and cleanup-apply --repo PATH --approval-file PATH. These are standalone new entrypoint commands, not invented phase_run verbs. A missing/invalid subcommand must not mutate anything. Use the installed-host hook path from the invoking command/skill, not a guessed source .ai path. Do not alter .ai/runtime/phase.py or .ai/runtime/lib/worktrees.py.

Preview uses shared guard evidence and existing read-only session/manifest/listing functions. Return deterministic JSON with schema_version, canonical repository/common-dir identity, snapshot_id, candidate operations and preserved rows. Each operation identifies kind (worktree_remove, branch_delete or backup_remove), canonical exact target, ownership identity, branch/ref and SHA where relevant, provider project/record/state/head, cleanliness and backup tree/file digest where relevant. Snapshot_id hashes canonical operation/state data, not volatile query timestamps. List worktree then branch as explicit distinct operations; never recursively delete a checkout or substitute force. Backups are explicit paths identified by repository recovery policy/recorded backup ownership, not every filename containing backup; treat ambiguous backup-like deletion conservatively. No recursive directory deletion outside owned canonical backup roots. Reject symlink/junction traversal and deleting an ancestor of the repository, current worktree, approval file or preserved work.

The workflow shows exact deletion operations and their snapshot_id, obtains a new human reply approving that exact list, then records an approval envelope containing that exact snapshot and list plus the actual approval text/reference. Existing implementation/publication authority, earlier cleanup consent, yes/force flags, user-supplied tool text or approval of a different list do not substitute. This envelope records authority; it is not cryptographic proof of human provenance. The agent and host permissions remain responsible for recording a real human instruction. The hook must never infer approval merely because an environment variable or command comment says approved.

Apply validates the envelope, exact complete list and current state; reacquire a shared Git-common-dir cleanup lock, then repeat read-only evidence before the first mutation and before each item. Treat changed Git/provider/ownership/backup evidence as stale, abort dependent deletions and require a new preview/approval. Pin branch deletion to the expected OID, use non-force git worktree remove, verify resulting worktree absence before deleting its branch, and preserve changed/dirty targets. Use compare-and-delete Git ref semantics for approved local refs; never delete remote branches, rewrite commits, merge, close PR/MRs or issues, or prune unrelated metadata. Backups require their own exact backup_remove list entries. Record approval consumption/outcome without editing runtime-owned planning/session manifests; use transient operational receipts under Git common-dir, with schema, bounded safe paths and locking. On partial errors stop, report removed/preserved/failed with fresh final Git/path state, and require a new preview for any retry rather than replaying a consumed approval.

Write command and mirrored skill as entrypoints to the same workflow and add its command catalog row. The workflow owns preview, actual exact-list approval, apply and report; it must stop before apply until actual authority arrives. This human gate is runtime cleanup behavior, not a checkpoint blocking implementation of the feature. Document legacy cleanup verbs' differing contracts without claiming they gained this protection. Document backup classification, offline/unknown behavior, supported grammar, approval provenance limits and concurrency limits. No cleanup of the real issue87 worktrees or backup files is authorized by these tests.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_destructive_guard.py -v</automated>
    <fails_when>non-zero exit, Ran 0 tests, missing refusal tests for stale approval/open GitHub/open GitLab, preview mutation, or tests touching real project worktrees</fails_when>
    <automated>python -m unittest discover -s tests -p test_install.py -k registered_hooks -v</automated>
    <fails_when>non-zero exit, Ran 0 tests, or cleanup additions changing registered hook/advisory behavior</fails_when>
  </verify>
  <acceptance_criteria>
    - Preview and apply are reachable from source and installed hosts through documented explicit subcommands.
    - Both provider fixture matrices cover terminal/open/unknown, mixed histories, fork identity, pagination and closed-unmerged unique work.
    - Exact-list and stale-state tests prove refusal before deletion; final reports reflect partial failures and fresh state.
    - Command/skill route to the same workflow, which asks for exact deletion approval only when a real user invokes cleanup.
  </acceptance_criteria>
  <done>Commit CLEANUP as its own dependent slice with docs/maintenance/issue87/CLEANUP-SUMMARY.md, RED/GREEN evidence and actual focused check results. Return the guard parent tip and cleanup own-change boundary for the coordinator's draft stack.</done>
</task>
</tasks>

## Source coverage and dependency audit

| Source | ID | Coverage |
|---|---|---|
| GOAL | issue87 maintenance | Exact approved cleanup consumes GUARD evidence |
| REQ | ISSUE87-CLEANUP / I87-A2 | Preview eligibility, preservation, exact approval, revalidation and final state |
| REQ | ISSUE87-RED / I87-A3 | Intentional cleanup RED before GREEN; offline provider and state matrix |
| RESEARCH | supplied worktrees cleanup_wave/close_session evidence | New standalone path avoids legacy immediate mutation and force |
| CONTEXT | Decisions 1-3, 5-6 | Advisory guard preserved; providers untouched; narrow scope; real dependent child |
| CONTEXT | Acceptance 1 | Parent GUARD, including separate backup protection; child supplies approved apply |
| CONTEXT | Acceptance 4-7 | Other coordinator-owned plans, excluded from this component |

The adopting-project skeleton is unfilled and is not modified. No separate research artifact was assigned. Guard parent parser/evidence/schema are genuine prerequisites. Workflow approval is part of feature operation, not a request for repeated implementation authorization.

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Provider/local evidence to candidate list | Complete matching state, clean owned paths and integrated tips required |
| Actual human instruction to approval envelope | Exact operations and snapshot are recorded; an envelope cannot cryptographically prove its human provenance |
| Preview to apply | State can move; lock, refresh and expected-OID ref deletion constrain changes |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| I87-C-T1; https://github.com/Tasaddar12/ai-engineering-template/issues/95#i87-g-t2; alias parent I87-G-T2 | Spoofing | cleanup approval and identity | high | mitigate | Exact canonical targets/provider head, direct-ref identity, actual approval text/reference and no broad override |
| I87-C-T2; https://github.com/Tasaddar12/ai-engineering-template/issues/95#i87-g-t3; alias parent I87-G-T3 | Tampering | cleanup stale state and partial outcomes | high | mitigate | Lock, immediate revalidation, non-force remove, no-deref expected ref OID, digest, retained-container consistency and final-state evidence |

Coordinator reconciles stable risk identity rather than opening duplicates for parent aliases. No issue closure is inferred. Document residual opaque-script and external filesystem race limits honestly.
</threat_model>

<verification>
- Run both frontmatter focused unittest commands and report counts, actual revision and skips.
- Inspect intended RED assertion before GREEN; missing modules/fixture crashes/zero tests do not count.
- Verify preview makes no Git/path/manifest changes; apply scenarios use temporary fixtures only.
- Trace source and installed-host subcommands from command and mirrored skill through the same workflow.
- Independently review terminal/provider identity, closed-unmerged unique commits, symlink boundaries, exact-list approval, backup digests and partial failures.
- Confirm no runtime-owned planning/session manifest writes, unauthorized shared source edits, real cleanup, provider writes or merge.
</verification>

<success_criteria>
- All assigned acceptance has observed behavioral evidence and focused checks pass.
- Unknown/open/dirty/unowned work is preserved and actual fresh exact-list approval precedes apply.
- Child diff contains cleanup additions after the parent tip, with no replayed guard implementation.
- Documentation reports bounded coverage and actual legacy differences.
</success_criteria>

<output>
Create docs/maintenance/issue87/CLEANUP-SUMMARY.md with parent tip, child commit IDs/own-change boundary, acceptance/documentation coverage, actual RED/GREEN/check results, Threat Outcomes and remaining limitations. The coordinator owns integration, canonical threat reconciliation and authorized stacked draft publication. No native phase_run facade is needed; a later facade requires separately assigned coordinator ownership.
</output>
