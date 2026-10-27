# Workflow catalog and shared execution contract

Commands select workflows; workflows define the actual procedure, exact role packets, runtime mutations and completion boundary. Read commands/COMMAND.md for entry points and flags. Read engineer/RULES.md and truth-map.md for authority and fact ownership. Do not create a competing procedure from a command description or a shortened checklist.

## Source and installed layout

The canonical source tree uses agents/, commands/, engineer/workflows/, engineer/references/, engineer/templates/, engineer/bin/, hooks/, bin/ and skills/. Project evidence lives in .planning; reusable policy and runtime assets do not become project records. Claude and Codex installations preserve this tree under their managed host namespaces. The installer manifest owns exact host-specific destinations and registrations.

## Shared launcher

Read the complete engineer/workflows/_runtime-launcher.snippet.sh and execute it in the shell used for runtime calls. Each fresh shell needs that launcher again; do not assume a function from another tool invocation persisted. It honors ENGINEER_RUN, checks the exact engineer-runtime identity, and resolves only source or installed Claude/Codex candidates. Preserve quoted absolute worktree paths and each argv value. Use `engineer_run query <verb> ...`; standard-library Python may parse already captured JSON when --pick on a producing read query does not suffice. Do not repeat a mutation just to obtain another field. Never eval arguments or interpolate public body text into executable code.

Read actual init keys from the pinned runtime contract. Check phase_found/found before dependent phase fields. A missing field is not false, zero or permission to proceed. Resolve optional configuration with config-get and an explicit intentional default. Only runtime verbs own planning structures; narrative prose follows its template and authoritative evidence.

## Core progression

| Procedure | Scope | Required boundary |
|---|---|---|
| new-project | Actual project intent, complete record templates and runtime roadmap | No adopting identity before explicit onboarding |
| new-milestone | Approved next requirement scope and continuous phases | No plans or implementation |
| add/insert/remove/edit-phase | Runtime phase record management | Concrete destructive confirmation and stable history |
| discuss-phase | Real decisions and discussion log | No inferred planning/execution permission |
| plan-phase | Warranted research, planner, independent plan-checker | Complete coverage; implementation awaits instruction |
| execute-phase | Authorized isolated dependency waves | Committed owned workers, deletion guards and issue handoff |
| verify-work | One frozen read-only evidence batch | Every result joined before verdict or source repair |
| ship | Current canonical evidence and existing phase session | Full draft PR; merge only on explicit instruction |
| quick | One scoped outcome and runtime quick record | Real isolated work and --quick verification for readiness/merge |
| progress | Current evidence report | One recommendation; no mutation |
| next | Evidence-based selected workflow | Implementation authority remains explicit |
| add-todo/check-todos | Selected pending work and canonical issues | No completion from selection/routing alone |
| cleanup | Exact captured worktree/branch deletion list | Token-bound exact human approval and per-resource revalidation |
| clean-planning | Safe record repair and explicit retirement | Digest guards; no invented project intent or evidence |
| complete-milestone | Actual accepted shipped work | Honest readiness; preserved phase evidence |
| milestone-summary | Complete evidence-backed explanation | Response by default; file write only on --write |
| update | Pinned workflow change | Full reviewed plan SHA-256 and per-path guards |

Feature workflows remain owned by their complete command/procedure files and use the same authority, isolation, record, issue and verification contracts. Read them only when selected or explicitly named by an applicable plan/reference.

## Sessions and worker ownership

Locate a phase before initialization and operate from its returned session checkout. Open or adopt sessions only at the selected workflow's initialization boundary; ship resolves an existing session and does not create one. Shared records and publication are coordinator-owned. Each source-changing worker has an exact role, base, branch/root, complete plan, files_modified/files_deleted/resources and a required committed SUMMARY. Read-only specialists return cited evidence without a source commit or fabricated summary.

Resolve exact model and effort inline for each dispatch; omit inherited values. A wait timeout is not worker exit. After dispatch, do not touch its owned paths or integrate its changes until confirmed stop. In a frozen batch, configured checks and independent specialists may read the same captured revision concurrently, but every result must join before a verdict, repair or new batch. A source edit invalidates provisional evidence. Worktree isolation has no opt-out and no primary-checkout fallback. Deletion permission comes only from explicit files_deleted and is rechecked at integration and cleanup.

## Canonical threat procedure

Read the complete _canonical-threat-tracking.md when planning, execution, verification or shipping reconciles phase risks. It applies the authoritative Git workflow policy with the runtime's exact entries schema, deterministic planned-risk container, full standalone variant, guarded preview/publish and actual rendered-anchor audit.

## Evidence, publication and stopping

A plan or summary is a claim to verify against actual artifacts, code and committed history. Check receipts bind argv/configuration, input fingerprints and revision lineage; stale receipts do not pass. Real human acceptance stays pending until an actual accepted reply/evidence exists. Unknown, failed, unavailable and deferred checks remain explicit.

Public issues and PRs use the complete canonical File Templates and provider readback. Planned risks follow the canonical deterministic threat checklist/container policy; distinct unplanned risks use their own issues. Preview tokens bind exact source/public content, labels and explicit reviewed existing-match/no-match disposition. Inspect an uncertain create before retrying. Open a draft on first authorized push and keep it current after each integrated slice. Do not merge without an explicit instruction for the concrete current PR.

Fix demonstrated in-scope defects through bounded isolated correction; retain out-of-scope findings in the complete closing Deferred record; block only work requiring an actual human decision. Never create new todos from execution/verification findings. A loop cap is not an acceptance waiver. End at the selected workflow's boundary and never infer authorization to implement the next phase.
