---
id: PLAN-003
kind: plans
title: Flat layout, explicit workflows and complete cleanup
status: draft
tasks:
- TASK-063
- TASK-064
- TASK-065
- TASK-066
- TASK-067
- TASK-068
- TASK-069
- TASK-070
- TASK-071
- TASK-072
- TASK-073
- TASK-074
- TASK-075
- TASK-076
- TASK-077
- TASK-078
- TASK-079
- TASK-080
- TASK-081
- TASK-082
- TASK-083
- TASK-084
- TASK-085
- TASK-086
- TASK-087
- TASK-088
- TASK-089
- TASK-090
- TASK-091
- TASK-092
features:
- FEATURE-008
- FEATURE-009
- FEATURE-010
- FEATURE-011
- FEATURE-012
- FEATURE-013
- FEATURE-014
- FEATURE-015
- FEATURE-016
- FEATURE-017
decomposition_status: proposed
execution_authorized: false
implementation_gate: Separate explicit instruction to implement PLAN-003; plan/decomposition
  approval is insufficient.
supersedes_on_implementation:
- PLAN-002
completion_blockers:
- TASK-091
- TASK-092
scope:
- src
- agents
- templates
- workflows
- constraints
- framework.yaml
- tests
- docs
- .ai
- .github
- AGENTS.md
- ARCHITECTURE.md
- README.md
- CONTRIBUTING.md
- SECURITY.md
- pyproject.toml
- .gitignore
context:
- AGENTS.md
- .ai/STATE.yaml
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
acceptance:
- All eight requested design changes are implemented and independently verified.
- Planning never implies implementation authority.
- All obsolete inventoried content and branches are actually deleted before completion.
- No blocked folders; explicitly authorized work continues through repair/recovery
  until completion, a proven hard block or explicit user stop. Obstacles are metadata
  and independent work continues.
- Explicit plan creation/revision has its own managed planning worktree and reviewed
  PR-to-main delivery; merged planning artifacts never authorize or start implementation.
implementation_blocked_by_user: true
continuation_policy: Continue authorized work; hard-block metadata only; no blocked
  folders; explicit stop instructions take precedence.
planning_delivery_authorized: true
merged_worktree_cleanup_authorized: true
obsolete_content_cleanup_authorized: false
planning_delivery_base: codex/plan-002-framework-reset
planning_delivery_mode: local_reviewed_merge
planning_worktree: .worktrees/plan-003-planning
change_lifecycle: Worktree -> changes -> validation and independent review -> merge
  -> delete merged worktree and branch
---
# PLAN-003 — Flat layout, explicit workflows and complete cleanup

## Status and authority

**Draft for discussion and revision. Latest explicit instruction: “Do not implement plan 3.” Implementation is prohibited and has not been started by this planning task.** The latest user instruction also authorizes delivering these planning changes through an actual dedicated worktree, validation, independent review, merge and required merged-worktree/branch cleanup. Approving the contents or decomposition does not authorize implementation. A separate explicit instruction to implement PLAN-003 is required.

**Latest lifecycle instruction: “Worktree, Changes, Review, Merge.... ALWAYS.” Merged worktrees and their Git branches must then be deleted.** This applies immediately to planning documents and workflow-rule changes, not only to future framework code. The former blanket no-deletion hold is superseded for merged-worktree/branch cleanup. Check the exact merged revision, stopped ownership, clean managed path and current branch/ref before removal; resolve genuine obstacles rather than asking for routine permission again. Historical-content purge remains part of the unimplemented PLAN-003 scope.

The latest user requirements take precedence over conflicting PLAN-002 preservation, packaging and model-profile rules for this proposed design. This delivery moves only the previously untracked planning artifacts into a dedicated checkout, commits the planning/operating-instruction diff, obtains independent review, merges it into the current development base and removes its merged worktree/branch. It does not implement PLAN-003 or resume PLAN-002. PLAN-002 execution state remains unchanged. PLAN-003 does not depend on finishing PLAN-002.

On explicit implementation, TASK-063 first reconciles existing work and establishes a reviewed retained baseline. Only then may the coordinator supersede the affected remaining PLAN-002 work. Do not automatically run its waiting features. Plan-specific scope, contracts and graphs remain in this PLAN document under .ai; each task and feature has its own explicit .ai artifact.

These artifacts are draft/unstarted specifications. Their legacy relative feature paths/status fields are preserved during transfer into the planning worktree; runtime schema migration remains outside this planning delivery. That legacy representation is explicitly rejected by the new requirement: implement a real draft lifecycle and store obstacles as metadata without any blocked folder. TASK-064/065 own the compatibility migration and its tests. Do not implement the lifecycle schema here; the exact existing planning artifacts are transferred without losing content and retain their relative paths until that migration is implemented. No ready feature or approved decomposition is published by this draft; implementation authority remains separate from lifecycle state.

## Desired outcome

1. Put authored Python files directly in src/, without src/ai_engineering/ or a replacement wrapper directory.
2. Keep reusable base assets visibly at the repository root: agents/, templates/, workflows/, constraints/ and framework.yaml; install copies into a target project's .ai/.
3. Treat discussing, creating, editing and approving a plan as planning only. Implementation needs its own explicit instruction.
4. Deliver feature changes through PRs to main after all required checks. Confirm merge, synchronize main, then delete merged feature branches and worktrees.
5. Confine each feature agent to one worktree for its entire session, including repairs. It cannot switch branches or reach another checkout.
6. Provide a dedicated Markdown file for each workflow.
7. Use a constraints/ folder for coding standards, scoped acceptable commands, permissions and limits.
8. Put each agent's model, provider, reasoning and related settings in YAML front matter in that agent's Markdown file.
9. Require actual deletion of obsolete project content and branches before PLAN-003 is complete. Archiving is not an acceptable substitute.
10. Never use blocked as a folder. Once implementation is explicitly authorized, keep processing through repair and recovery until completion; only a genuine hard block or an explicit user stop can halt affected work. Draft plans are unstarted, not blocked.
11. Give every explicitly created or revised plan its own planning worktree and deliver its reviewed artifact changes through a PR to main using the same check, merge and authorized retirement lifecycle as feature implementation. Merging a plan never authorizes implementing it.

## Proposed source repository layout

All paths below are relative to the framework repository root, not the filesystem drive root.

```text
/
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── agents.py
│   ├── artifacts.py
│   ├── config.py
│   ├── constraints.py
│   ├── runner.py
│   ├── git.py
│   ├── planning.py
│   ├── orchestrator.py
│   ├── delivery.py
│   ├── project.py
│   ├── workflows.py
│   ├── state.py
│   ├── review.py
│   ├── handoffs.py
│   ├── templates.py
│   ├── io.py
│   ├── errors.py
│   ├── containment_linux.py
│   ├── containment_windows.py
│   └── cleanup.py
├── agents/
│   ├── orchestrator.md
│   ├── work-decomposition.md
│   ├── implementation.md
│   ├── bugfix.md
│   ├── research.md
│   ├── critical-review.md
│   └── recovery.md
├── templates/
│   ├── plans/
│   ├── tasks/
│   ├── features/
│   ├── bugs/
│   ├── research/
│   ├── decisions/
│   ├── reviews/
│   ├── handoffs/
│   ├── pull_requests/
│   └── project/
├── workflows/
│   ├── project-init.md
│   ├── research.md
│   ├── planning.md
│   ├── implementation.md
│   ├── validation.md
│   ├── critical-review.md
│   ├── delivery.md
│   ├── cleanup.md
│   ├── bugfix.md
│   ├── recovery.md
│   └── state-reconciliation.md
├── constraints/
│   ├── coding.yaml
│   ├── commands.yaml
│   ├── permissions.yaml
│   └── limits.yaml
├── framework.yaml
├── .ai/                         # This repository's current work only
├── .worktrees/                  # Separate planning and feature checkouts
├── tests/
├── docs/                        # Optional reusable reference documentation
├── .github/
├── AGENTS.md
├── ARCHITECTURE.md
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
└── pyproject.toml
```

This is the target inventory, not a statement that unimplemented modules already exist. Python remains 3.11+ and the public import/CLI namespace remains ai_engineering. Use explicit build configuration to map that namespace onto flat src; verify editable, sdist and wheel behavior. Built distribution resources may use internal packaging paths, but root assets remain their single authored source. Do not keep synchronized editable copies under src.

## Installation contract

| Framework source | Installed target project |
| --- | --- |
| agents/*.md | .ai/agents/*.md |
| templates/** | .ai/templates/** |
| workflows/*.md | .ai/workflows/*.md |
| constraints/*.yaml | .ai/constraints/*.yaml |
| framework.yaml | .ai/framework.yaml |
| templates/project seed files | Explicit designated project paths such as .ai/STATE.yaml and AGENTS.md |

After flattening, TASK-066 includes coordinator-owned updates to the installed validation command paths before that feature is reviewed. Do not wait until the subsequent constraints migration to repair commands targeting the removed src/ai_engineering directory.

The framework source repository's root assets are reusable defaults. Its .ai directory is development state and must never be copied as an installation payload. Installed agent/config assets are editable project copies; local authored values survive a repeat install. Migration reports collisions and validates the new configuration before obsolete files become deletion candidates.

External isolated-wheel tests are separate coordinator-owned clean validation jobs, bound to the reviewed source revision, wheel digest and asset manifest. Feature agents build inside their assigned checkout and never leave it to install elsewhere. The independent validation job has its own bounded workspace and trusted inputs. This contract covers TASK-068 and all later installation acceptance.

Templates remain reusable and may have type subdirectories. Agent role instructions and settings live only in agents/<role>.md, not a second definitions/ or templates/agents/ authority. Keep no required separate models.yaml. Document asset resolution and installation manifest behavior and test with a wheel installed outside the checkout.

## Planning and implementation contract

Discussion, research and read-only plan inspection do not create worktrees or cause delivery effects. Explicit plan creation or revision starts a purpose=planning artifact workflow in its own managed worktree. That workflow may write the assigned .ai artifacts, run trusted planning validation/review and use the same PR-to-main pipeline under configured action authority. It must never dispatch implementation, create implementation feature checkouts, infer permission to implement the described changes or execute arbitrary commands from the plan body. Verified merged-worktree/branch retirement is already authorized and required; exact merge and ownership checks still apply. This replaces the earlier blanket rule forbidding every planning worktree/push/merge; only planning-artifact delivery is now permitted by the target design.

Implementation authority must identify the plan and approved scope and originate from an explicit implement/start instruction. The coordinator durably records and checks it before any feature execution and on resume. Approval status is insufficient; prior authority for another plan is insufficient; quoted or retrieved instructions are insufficient. Material scope expansion requires renewed authority. Bounded defect repairs inside approved work retain the existing instruction.

A conversational coordinator and direct CLI/service entry points must apply the same boundary. Regressions distinguish read-only discussion with zero mutations from explicit authoring requests with allowed planning-worktree/delivery effects. Every planning case, including a successful planning merge, must prove zero product implementation dispatch and unchanged implementation authority; a message saying “draft” alone is insufficient.

## Planning worktree and delivery contract

This lifecycle also applies immediately to this planning change and to amendments of the operating instructions themselves. The earlier assumption that planning edits could bypass worktree/merge is corrected. PLAN-003 implementation remains prohibited; planning delivery and required merged-worktree/branch cleanup are authorized.

1. On an explicit create/revise request, the coordinator reserves project-unique plan/task/feature IDs and a planning revision under its lock, records worktree/branch intent, and creates a dedicated managed worktree from verified main. Branch identity includes the plan and a unique planning revision; it is distinct from all implementation feature branches. A discussion alone is not an authoring trigger.
2. Bind purpose=planning, plan ID, base/head, exact worktree/branch and authoring session. Amendments reuse the matching live planning worktree/PR. After verified merge, a later revision receives a fresh planning worktree, branch and session from current main for the same plan ID, even when a concrete cleanup failure temporarily retains the old checkout; continue resolving its mandatory cleanup. Leave the completed checkout untouched; never append to a merged PR, switch its branch or reuse its completed session.
3. Author only the assigned PLAN document, referenced tasks/features and necessary planning evidence under that worktree's .ai. Keep product source and unrelated plans out of the diff. Planning/decomposition agents are confined to their worktree and return structured proposals/output there; the coordinator alone persists canonical control artifacts, STATE, ID reservations and operational journals. No authoring-agent exception grants root-checkout control writes or branch switching.
4. Commit through the coordinator, run trusted checks appropriate to the artifact diff (front matter, links, scope, exact task coverage, graph/ownership validity and consistency), and obtain one independent critical review of the complete planning revision. Honor all required repository/host checks and protections. Commands proposed for future implementation in the plan body are data, not authorization to run them.
5. Deliver the planning branch through a PR to main using the same destination binding, exact-head checks, review invalidation, repair/recovery, uncertain-effect reconciliation and merge gates as a feature. Repair returns to the same authoring session. Push/PR/merge operations require configured action authority; planning authority alone cannot bypass that requirement.
6. Confirm merge, synchronize main safely and register only that reviewed revision as the canonical delivered plan. Keep planning authoring/delivery status separate from the plan's implementation status and execution_authorized flag. A merged plan can remain draft or ready with implementation unstarted. Unmerged planning data cannot replace execution inputs or bypass semantic decomposition approval.
7. After verified merge and owner shutdown, apply the same clean/managed worktree and exact local/remote branch retirement checks. Retirement is already required by the standing user instruction. After exact merge/ownership/cleanliness checks, remove the worktree and local/remote branch. If a genuine obstacle prevents removal, record evidence, continue remediation and unaffected work, and do not report the change lifecycle complete until cleanup succeeds.
8. Later implementation requires its own explicit instruction bound to the approved merged plan revision/scope and creates separate feature worktrees. The planning worktree is not reused as an implementation checkout. Concurrent plan revisions cannot silently change an active implementation's approved inputs.

The coordinator tracks planning runs/ID reservations/delivery separately from active implementation features and keys records by plan ID plus planning revision/purpose. Multiple retained merged worktrees can coexist with a current authoring revision without ambiguous ownership or receipt collisions. Pending retirement alone never blocks a separately requested planning revision. Serializing ID allocation prevents concurrent planning worktrees from allocating the same identifiers, while only completed planning merges change the canonical available revision. Keep plan-specific design contracts here; operational receipts remain evidence under .ai/runs.

TASK-064/065 own intent/purpose, ID-reservation and eligibility boundaries; TASK-075/076/077 own planning-worktree lifecycle and regressions; TASK-078/079/080 apply confinement; TASK-081/082 document the workflow; TASK-084/085/086 share the delivery and retirement engine; TASK-087/089 expose and verify the installed flow; TASK-090 inventories obsolete planning worktrees. These are additions to the declared ownership; FEATURE-012 effort becomes eight. All other batch limits and dependencies remain unchanged.

## Lifecycle folders and hard-block-only stopping

The latest user requirement supersedes the earlier use of blocked folders and automatic stopping on repair-budget exhaustion. The runtime lifecycle design remains unimplemented; this planning delivery does not start either plan or resume feature workers. Transferring its own artifacts and cleaning up its own merged worktree/branch are authorized lifecycle operations.

### Lifecycle and obstacle representation

Use lifecycle folders for work phase: feature draft, ready, in-progress, review and completed; preserve other meaningful historical phases where applicable. Tasks retain backlog for unstarted work. Never create a blocked directory for plans, tasks, features, bugs, runs, handoffs or any other workflow artifact. A hard block is metadata attached to the work in its existing phase/location, not a lifecycle transition or file move. Draft/unstarted, ordinary dependency waiting and repair-needed states are not hard blocks.

The coordinator records reason, concrete evidence, attempted or ruled-out remedies, affected subjects/actions, next action and resume condition for a real hard block. A plan/run-level halt additionally states why no safe authorized work remains. Clearing a hard block does not require moving the artifact. TASK-064 adds draft support and compatible readers/indexing, then the coordinator migrates legacy paths and references atomically without duplicates or lost content under the applicable authority. TASK-065 verifies this behavior. No migration is performed by this planning amendment.

### Continue authorized work

Once implementation is explicitly started, ordinary failing tests, CHANGES_REQUIRED, fixable defects, shared-file conflicts and incomplete prerequisites route to repair, investigation, prerequisite work or structural recovery. Repairs return to the same implementer and obtain fresh validation/full review. A discussion or draft of a different plan does not cancel existing execution authority. In particular, keeping PLAN-003 unimplemented is not a reason to stop already-authorized PLAN-002 repairs.

A per-attempt timeout or review/repair count limits one strategy; exhausting it requires diagnosis and another viable authorized approach or decomposition. It is not by itself a hard block. Do not repeat identical failed attempts indefinitely, ignore actual resource limits, weaken review checks or replay uncertain external writes. Preserve enforceable global resource/authority boundaries and report a concrete hard block if those leave no viable next step.

Continue other dependency-ready work when an item waits for checks, merge, a resource or an external prerequisite. Required checks still gate merging; their failure directs repair rather than suspending the whole run. Verified merged code can release code-only dependents even if a concrete cleanup failure remains pending, provided ownership is clear and the dependency contract does not require cleanup itself. The required cleanup completion gate stays open. If all useful work is waiting, persist the pending state and use bounded condition rechecks or an actionable resume trigger; never manufacture completed work or an arbitrary need for user permission.

### What qualifies as a hard block

A hard block is a specific obstacle that prevents further safe progress on the affected work within existing authority after reasonable available repair/recovery alternatives are exhausted or shown infeasible. Examples are an unavailable required enforced execution boundary with no supported alternative, essential missing input or permission, an externally unavailable prerequisite with no independent work left, or a genuinely non-overridable exhausted resource. Record evidence and the exact condition needed to proceed. A bug, review rejection, retry counter, pending normal check or change of discussion topic is not sufficient evidence by itself.

An explicit user stop, revoked authority and “Do not implement plan 3” remain controlling boundaries. The latest instruction requires merged-worktree/branch cleanup and supersedes the prior blanket no-deletion hold for that lifecycle. Honor them immediately for the named plan/actions; persistence cannot override them. Unstarted draft work is not an implementation run that needs to keep going. Finishing this planning amendment does not imply permission to implement it.

### Acceptance ownership

TASK-064/065 own lifecycle representation, legacy migration and authorization isolation. TASK-069 owns strategy/resource limit semantics. TASK-081/082 own workflow documentation. TASK-087 owns truthful CLI/install states. TASK-088 owns repair/recovery/scheduling continuity and hard-block evidence. TASK-089 owns end-to-end regressions and clear distinction between local test fixtures and real remote effects. TASK-091/092 apply the same metadata-only, action-scoped hold and recovery rules to cleanup and post-merge verification. Existing task/feature counts and serial dependencies are unchanged; these requirements refine their existing state, intent and workflow boundaries.

## Agent file contract

Each agent is one Markdown file with YAML front matter followed by behavior instructions. Illustrative configuration shape:

```yaml
---
name: implementation
provider: command
model: "<explicit provider-valid model ID>"
reasoning: medium
permissions:
  modify_files: true
  run_commands: true
  spawn_agents: false
constraints:
  - coding
  - commands
  - permissions
  - limits
workflows:
  - implementation
  - validation
assignment_template: handoffs/orchestrator-to-feature-agent.md
output_template: handoffs/agent-completion.md
max_concurrency: 1
---
```

The illustrative model placeholder is not a runnable default. Shipped unconfigured files must clearly require a concrete model selection and fail before dispatch; no silent model fallback or inferred paid-service authorization. Migration places existing resolved model/provider/reasoning values into each role's front matter and validates provider compatibility. Preserve role permissions and independent reviewer identity even if different agents use the same model.

## Constraints contract

- coding.yaml: supported Python, formatting, typing, testing and documentation standards.
- commands.yaml: named validation commands and strict argv rules scoped to role, workflow and the assigned task.
- permissions.yaml: read/write scopes, coordinator-only state, branch/control restrictions and external action authority.
- limits.yaml: concurrency, task/feature size, durations, output caps and bounded retry/recovery budgets.

The effective permission is the intersection of trusted project policy, role permissions, workflow limits and assigned task scope. Task content can narrow trusted command permissions; it cannot grant commands or privileged actions. Forbidden rules win. Unknown/missing policy fails closed. The future runtime policy must distinguish obsolete-content deletion from verified merged-worktree/branch retirement. Until that runtime migration exists, the coordinator may perform exact lifecycle operations under the direct user instruction with recorded checks, without enabling generic destructive commands. Keep other destructive operations scope-controlled and bind allowed actions to exact verified paths/refs. The user has explicitly authorized required merged-worktree/branch retirement. Historical-content purge remains an unimplemented task; this planning-delivery authorization does not execute that purge. Every product subprocess uses the central runner with existing redaction, timeout and completeness protections.

## Worktree confinement contract

The coordinator creates and owns the branch/worktree mapping for both planning and feature work. Each authoring or implementation assignment receives a fixed canonical worktree, branch, repository and session identity. It edits declared scope in that checkout throughout implementation and repair. Validation and review must not change that binding.

A fixed cwd or prompt instruction is insufficient. The provider/tool host and OS boundary must prevent outside-project traversal and writes, including child processes, symlinks/junctions, environment-based path changes and shared Git metadata attacks. Feature agents cannot switch/check out branches, mutate HEAD/refs, manage worktrees or use alternate Git directories. The coordinator performs commits and administrative Git changes.

Supply needed planning context as a read-only snapshot inside the assigned checkout. Write returned handoffs inside it and have the coordinator collect them. Remove the existing arbitrary root-context access and outside-worktree output exception for feature agents. Explicit read-only toolchain/runtime resources are the only outside-root execution dependencies; they grant no access to other project checkouts or coordinator data. Writable scratch remains inside the worktree.

The future framework provider dispatch must enforce confinement for feature implementation and planning authoring sessions. Select a supported enforced mechanism on each platform and demonstrate native denial probes on Linux and Windows. Do not claim unrestricted subprocesses or a self-declared permission flag satisfy the requirement. If the supported mechanism is unavailable, implementation visibly blocks rather than silently weakening isolation.

For runtime provider dispatch this also applies to bootstrap features before FEATURE-013 exists. They require an already enforced execution host with the same worktree and branch restrictions; the coordinator verifies that boundary before launch. If none is available, the first implementation launch is blocked. There is no temporary unrestricted-agent exemption while building the confinement adapters. Existing/manual coordinator delivery may supply the PR/check/merge gates before FEATURE-015 automates them, but cannot waive them.

## PR, merge and branch lifecycle contract

This delivery engine also serves purpose=planning subjects with the planning-specific checks and authority separation above. Replace feature identity with the plan and its planning revision when delivering artifacts; successful planning delivery never marks product implementation complete.

1. Establish a current verified main baseline. At transition, reconcile the existing reset branch and retained code through a reviewed baseline PR before dependent feature execution; do not assume main already contains PLAN-002.
2. Create each feature branch/worktree from verified main after dependencies have reached it.
3. Implement, commit through the coordinator, run applicable validation and obtain one independent Critical Change Review of the entire feature diff at the exact revision.
4. Create/update the explicitly targeted PR to main under configured external authority.
5. Require current critical PASS, local validation, configured required CI, approvals, branch protection and mergeability. Pending/missing checks block. No admin bypass. Changed code and conflict repairs require new validation and full review.
6. Merge with exact-head protection. Reconcile an uncertain merge rather than issuing blind duplicates. Default support is an ancestry-preserving PR merge; incompatible squash/rebase-only policies prevent merge until equivalent reviewed-content verification exists, while authorized repair and independent work continue.
7. Confirm remote merge result, synchronize local main safely and prove the reviewed code is available there before releasing dependencies.
8. Once workers have stopped and the managed checkout is clean, remove its worktree and delete its exact local and remote feature branch. Already-deleted host branches are reconciled. A moved branch tip, dirty files, unknown ownership or ongoing worker blocks removal.

The coordinator never changes a feature agent's branch. It also never switches a dirty user checkout to main or deletes the branch it currently occupies. Cutover is an explicit coordinator operation once all current work is safely merged. Completion distinguishes merged code from pending cleanup; the plan cannot close with required cleanup outstanding.

This planning request runs no remote operation. Implementation uses configured fetch/push/PR/merge/remote-deletion authority; absence of authority is an explicit blocker, not evidence that delivery succeeded.

## Old content deletion and the blocking cleanup gate

**TASK-091 is a mandatory gate when PLAN-003 implementation is explicitly started; TASK-092 verifies its result.** Historical-content purge is not performed by this planning delivery. Cleanup of this delivery’s own merged worktree/branch is already authorized and required. Cleanup occurs after the replacement works and before completion, so legacy files are not removed while still needed for migration. TASK-063 handles initial reconciliation; TASK-090 produces the exact final removal inventory and identifies required reference/state repairs without performing them. TASK-091 owns those repairs, coordinator-applied state migration and every source/test change before the cleanup revision is reviewed.

Delete obsolete PLAN-001 and PLAN-002 records, reset archives, old research/reviews/handoffs/run evidence with no live purpose, superseded schemas/source/tests/docs, duplicate installed defaults, unused local/generated tooling, stale worktree directories and obsolete local/remote branches. Explicitly include .ai/archive and old plan bundles once their active references have been removed. Root legacy provider/config folders, if found, belong in the inventory too.

Do not archive, rename to legacy, copy into another backup folder or retain replacement branch copies. Keep current root assets, current project state/configuration, PLAN-003 and its live completion evidence, active toolchain dependencies and unrelated user content. Cleanup targets old content, not every file merely because it predates this plan. No .git history rewrite, object purge, secret deletion or unrelated-repository cleanup is included.

Deletion inventory entries bind exact canonical paths or repository/ref names, observed revisions/status, current owner, retained replacement and disposition. Identify uncommitted/unique work; retain the needed changes by integration or record an explicit discard disposition under the authorized scope before deleting. Unknown or active ownership, dirty work, changed refs, unsafe links and unresolved retention decisions remain blockers. They are not an excuse to declare cleanup complete with leftovers.

Tracked file removal is a reviewed cleanup PR. The coordinator handles protected .ai control records and administrative cleanup from its own context; the implementation agent never escapes confinement to perform deletion. The exact manifest and result receipts live under .ai/runs/plan-003 as current execution evidence, with no deleted contents copied into them. Recheck absolute path containment immediately before any recursive removal, use one shell end to end on Windows, and never delete by unbounded branch-name patterns.

After the cleanup PR merges, the coordinator removes that change’s worktree and branch under the standing required-merge-cleanup instruction. Verify no inventory candidates, stale registrations or broken current references remain, then rerun installation/import/status and validation on main. An inability or lack of authority to delete a required item keeps the cleanup gate open and PLAN-003 incomplete.

TASK-092 is coordinator-owned post-merge verification from synchronized main, with source and tests read-only. All test/reference repairs must be included in TASK-091 before review. It writes only state and current result evidence. If post-retirement verification fails, keep the gate open. A code repair requires a newly bounded task/feature under this PLAN, current implementation authority, a fresh confined checkout/session from main, full validation/review and a new PR. Do not reopen a deleted checkout, reuse its retired session, or perform unreviewed fixes directly on main. Administrative re-observation may retry only after resolving uncertain outcomes and checking current authority.

## Proposed tasks and feature graph

Thirty tasks are grouped into ten bounded batches. Every task is effort 1..3; every batch is at most five tasks and eight effort. Dependencies are deliberately serial because source moves, loaders, agent dispatch, runner policy, installation and lifecycle changes share interfaces and file ownership. This is a draft proposal; semantic decomposition must be approved before execution and cannot itself authorize implementation.

| Feature | Task references | Prerequisite | Effort |
| --- | --- | --- | --- |
| [FEATURE-008](../../features/blocked/FEATURE-008.md) — Explicit implementation intent and baseline transition | [TASK-063](../../tasks/backlog/TASK-063.md), [TASK-064](../../tasks/backlog/TASK-064.md), [TASK-065](../../tasks/backlog/TASK-065.md) | Explicit implementation instruction; no PLAN-002 completion dependency | 7 |
| [FEATURE-009](../../features/blocked/FEATURE-009.md) — Flat source tree and root installation assets | [TASK-066](../../tasks/backlog/TASK-066.md), [TASK-067](../../tasks/backlog/TASK-067.md), [TASK-068](../../tasks/backlog/TASK-068.md) | FEATURE-008 | 8 |
| [FEATURE-010](../../features/blocked/FEATURE-010.md) — Constraint folders and task-specific command limits | [TASK-069](../../tasks/backlog/TASK-069.md), [TASK-070](../../tasks/backlog/TASK-070.md), [TASK-071](../../tasks/backlog/TASK-071.md) | FEATURE-009 | 8 |
| [FEATURE-011](../../features/blocked/FEATURE-011.md) — Markdown agent definitions with inline model settings | [TASK-072](../../tasks/backlog/TASK-072.md), [TASK-073](../../tasks/backlog/TASK-073.md), [TASK-074](../../tasks/backlog/TASK-074.md) | FEATURE-010 | 7 |
| [FEATURE-012](../../features/blocked/FEATURE-012.md) — Fixed worktree ownership and branch restrictions | [TASK-075](../../tasks/backlog/TASK-075.md), [TASK-076](../../tasks/backlog/TASK-076.md), [TASK-077](../../tasks/backlog/TASK-077.md) | FEATURE-011 | 8 |
| [FEATURE-013](../../features/blocked/FEATURE-013.md) — Enforced provider and filesystem confinement | [TASK-078](../../tasks/backlog/TASK-078.md), [TASK-079](../../tasks/backlog/TASK-079.md), [TASK-080](../../tasks/backlog/TASK-080.md) | FEATURE-012 | 8 |
| [FEATURE-014](../../features/blocked/FEATURE-014.md) — Dedicated workflow Markdown and installed routing | [TASK-081](../../tasks/backlog/TASK-081.md), [TASK-082](../../tasks/backlog/TASK-082.md), [TASK-083](../../tasks/backlog/TASK-083.md) | FEATURE-013 | 6 |
| [FEATURE-015](../../features/blocked/FEATURE-015.md) — Verified PR merges to main and branch removal | [TASK-084](../../tasks/backlog/TASK-084.md), [TASK-085](../../tasks/backlog/TASK-085.md), [TASK-086](../../tasks/backlog/TASK-086.md) | FEATURE-014 | 8 |
| [FEATURE-016](../../features/blocked/FEATURE-016.md) — Installed workflow continuity and full acceptance | [TASK-087](../../tasks/backlog/TASK-087.md), [TASK-088](../../tasks/backlog/TASK-088.md), [TASK-089](../../tasks/backlog/TASK-089.md) | FEATURE-015 | 8 |
| [FEATURE-017](../../features/blocked/FEATURE-017.md) — Blocking deletion of obsolete content and branches | [TASK-090](../../tasks/backlog/TASK-090.md), [TASK-091](../../tasks/backlog/TASK-091.md), [TASK-092](../../tasks/backlog/TASK-092.md) | FEATURE-016 | 7 |

Sequence: FEATURE-008 → FEATURE-009 → FEATURE-010 → FEATURE-011 → FEATURE-012 → FEATURE-013 → FEATURE-014 → FEATURE-015 → FEATURE-016 → FEATURE-017. Tasks within each batch execute in numeric order, with explicit coordinator validation jobs where noted. FEATURE-017 has a pre-merge implementation/review phase for TASK-090/091 and a separate coordinator-owned post-merge TASK-092 phase; it is not three implementation tasks inside a checkout that no longer exists. Feature artifacts aggregate their task scopes and acceptance; shared file ownership across different features is serialized by this graph.

### Requirement coverage

| Request | Tasks |
| --- | --- |
| Flat src | TASK-066, TASK-068 |
| Root base assets and installation | TASK-067, TASK-068, TASK-087 |
| Planning never starts implementation | TASK-063 through TASK-065, TASK-081, TASK-087 |
| PR checks, merge to main and branch deletion | TASK-084 through TASK-086 |
| Fixed worktree and enforced confinement | TASK-075 through TASK-080 |
| Dedicated workflow Markdown | TASK-081 through TASK-083 |
| Constraint folders and scoped commands | TASK-069 through TASK-071 |
| Inline agent model settings | TASK-072 through TASK-074 |
| Blocking actual cleanup | TASK-090 through TASK-092 |
| No blocked folders; stop only at hard blocks or explicit user direction | TASK-064/065, TASK-069, TASK-081/082, TASK-087 through TASK-089 |
| Dedicated planning worktree and reviewed PR merge without implementation | TASK-064/065, TASK-075 through TASK-087, TASK-089/090 |

## Validation and acceptance

Planning validation checks canonical .ai placement, front matter, task/feature references, exact coverage, acyclic task and feature graphs, effort bounds, scope/resource serialization, linked files and a complete independent review of this planning diff. It does not exercise or claim approval of unimplemented behavior.

Each implementation batch inspects the source, records actual meaningful commands/results and receives one independent full-diff critical review. Repairs return to the same implementer. Existing command names tests/lint/format/types remain the common verification set while their definitions migrate. Broaden tests only for affected behavior and required acceptance; keep tests in temporary projects.

Release gates include flat-source editable/wheel imports; root-only authored assets; fresh/repeat/migrated installation; planning requests with no implementation effects; model/permission fidelity; native Windows/Linux confinement denial; stable repair/worktree sessions; check/merge/ref drift handling; post-merge branch deletion; working bugfix/recovery; and successful purge followed by validation from main. Controlled providers/hosting test contract logic, not real remote success. Report missing platform/provider authority honestly and leave corresponding required gates open.

## Baseline evidence and decisions still to resolve during implementation

At drafting, current branch is codex/plan-002-framework-reset and STATE still focuses on PLAN-002: FEATURE-005 in progress with CHANGES_REQUIRED; FEATURE-006/007 waiting. Managed execution/planning/agents/orchestration checkouts and many PLAN-001 branches exist. Re-read Git and state at implementation; this observation is not a deletion manifest.

The required initial command python -m ai_engineering status failed with No module named ai_engineering under the system Python. The local virtual environment can import the current source package via an explicit src path. This failure is baseline evidence and is covered by the installation/CLI tasks; no runtime fix was attempted during planning.

Implementation selects a supported confinement backend on each platform, explicit provider-valid model IDs, required hosted checks and repository external-action settings. These choices may refine the draft through decomposition without relaxing the eight requirements or actual-deletion completion gate. A missing capability is surfaced before dispatch; a material scope change returns for explicit authorization.

## Planning validation record

The local virtual environment ran the existing ArtifactStore and planning.validate_tasks / validate_features / parallel_waves against all 41 new plan/task/feature artifacts: PASS, 30 tasks, ten features, exact coverage, bounded effort, both acyclic graphs, serialized ownership and zero broken Markdown file links. All tasks are backlog, all features are blocked, the plan is draft, and execution_authorized is false throughout. TASK-091 is explicitly marked blocking. These structural checks do not approve semantic decomposition or authorize execution.

The first attempt to pass the complete document payload on a command line failed before process creation because of the Windows command-length limit. The coordinator then used a temporary local payload and the existing canonical artifact writer under StateStore.lock; 41 artifacts were created successfully without saving STATE. No dependency was installed. The temporary staging payload is removed after use.

git diff --check passed for tracked changes; separate inspection of the newly created documents is required because they are untracked. At the first validation snapshot, git status showed only the three new planning locations, the current branch stayed codex/plan-002-framework-reset, and git diff -- .ai/STATE.yaml was empty. Later read-only inspection found concurrent PLAN-002 activity updating STATE and FEATURE-005 review artifacts. This planning pass did not start that activity or write those records; do not claim the final shared workspace has no concurrent changes. No product implementation tests or remote operations were run for this planning-only change. Independent planning review evidence is recorded separately under .ai/reviews; it is not approval of implementation or of runtime behavior.

The first independent planning review returned CHANGES_REQUIRED (CR-001 through CR-004); its immutable report is .ai/reviews/PLAN-003-critical-1.md. Repairs clarify transitional command ownership, isolated validation jobs, inventory-only scope and coordinator post-merge verification/recovery. A snapshot-verification command also failed before launch because its generated command contained a NUL byte; the subsequent read-only Python stdin script succeeded. Revalidate the updated artifact graph and obtain the same reviewer’s full-diff verdict before delivering this draft.

## Continued-processing amendment evidence

This amendment adds requirement 10 and updates its existing task/feature acceptance only. The initial system-Python status command again failed with No module named ai_engineering; that is recorded tooling baseline, not a reason to stop this planning edit. Existing local source readers and validators remain available. No product source, current STATE, branch or worktree is changed; no files are moved or deleted. The earlier review snapshots remain historical evidence and do not approve this amended draft. Obtain a fresh independent complete planning review after structural validation.

The FEATURE-005 review used example.invalid URLs with temporary local repositories and a non-network SSH stub. Its report explicitly states no network, hosting-service, credential or paid-provider call occurred. It found a repairable distinction between home-relative and absolute remote paths; it did not identify or connect to a real SSH repository belonging to the user. A code repair can continue while unsafe delivery stays gated.

## Planning-worktree amendment evidence

At the preceding requirement-11 amendment, planning-worktree/PR behavior was specified with zero implementation dispatch and the then-recorded deletion hold; that amendment performed no Git worktree/branch or remote changes. The immediate-delivery correction below supersedes that hold and now carries these artifacts through an actual worktree, review, local merge and required cleanup. TASK-075 effort increases from two to three and FEATURE-012 from seven to eight; the graph remains 30 tasks in ten serial batches. The system-Python status command failed with No module named ai_engineering; source-based document validation remains available. Earlier review snapshots describe earlier drafts; obtain a fresh complete independent planning review for this amendment.

## Immediate planning delivery correction

The user corrected the earlier interpretation: every repository edit, including this PLAN and workflow instructions, follows **worktree → changes → validation/independent review → merge → delete the merged worktree and branch**. Pure discussion/read-only inspection performs no edit. Coordinator administrative receipts and Git/state observations are recorded outside the authoring checkout as lifecycle evidence; they are not a bypass for product/document editing.

This repository has no Git remote configured. Its current development base is codex/plan-002-framework-reset at 461e2a5710e6591e03b08d1cb537fdf1b9389c9b; main is 217 commits behind that development base. This correction therefore uses a reviewed local merge into that development branch, without importing the unrelated 1,327-file PLAN-002 reset into main or claiming a hosted PR occurred. Normal configured delivery remains PR-to-main. A hosted PR requires an actual configured destination; none is invented for this correction.

The 41 plan/task/feature documents and four historical planning reviews are transferred intact into .worktrees/plan-003-planning on codex/plan-003-planning before further changes. Root and .ai operating indexes are updated there to apply the lifecycle immediately. PLAN-003 stays draft, implementation authority remains false, planning delivery and merged-worktree cleanup are authorized, and historical-content purge stays unimplemented. Fresh review binds the complete committed diff; earlier reviews remain evidence of earlier drafts only.
