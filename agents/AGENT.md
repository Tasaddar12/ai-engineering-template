# Agent catalog

Read [the engineering rules](../engineer/RULES.md) and [agent adaptation](../engineer/references/agent-adaptation.md) before dispatch. This catalog defines the shared roles for Claude and Codex. The selected command and workflow own procedure; the role method owns the worker's behavior. See the [reference catalog](../engineer/references/REFERENCE.md) for detailed methods.

## Roles and evidence flow

| Role | Dispatcher | Input → result → consumer |
|---|---|---|
| [Coordinator](coordinator.md) | Human's selected command/workflow | Authorized outcome and records → assignments, joined evidence, shared-record updates and delivery → human |
| [Executor](executor.md) | execute-phase / quick coordinator | Assigned PLAN, isolated checkout and owned paths → committed implementation plus SUMMARY → coordinator |
| [Planner](planner.md) | plan-phase / quick coordinator | Approved CONTEXT, requirements and research → committed PLAN/VALIDATION and shared-record proposals → coordinator and plan-checker |
| [Plan checker](plan-checker.md) | plan-phase coordinator | Captured plans and authority evidence → PLAN REVIEW, approved or needs-revision → coordinator |
| [Phase researcher](phase-researcher.md) | plan-phase / next coordinator | Bounded questions and repository scope → committed RESEARCH, sources and unresolved choices → planner via coordinator |
| [Verifier](verifier.md) | verify-work / execute-phase coordinator | Captured revision, acceptance and receipts → provisional goal-backward report → coordinator for joined verdict |
| [Code reviewer](code-reviewer.md) | execute-phase / code-review coordinator | Captured revision and explicit diff base → complete review with stable findings → coordinator for capture |
| [Debugger](debugger.md) | next / verify-work coordinator | Symptom and scoped evidence → demonstrated root cause and bounded correction proposal → coordinator |
| [Doc writer](doc-writer.md) | execute-phase / documentation coordinator | Assigned documentation paths and source interfaces → committed documents and SUMMARY → coordinator |
| [Doc verifier](doc-verifier.md) | verification coordinator | Documentation and captured source revision → complete claim JSON with FAIL/UNVERIFIABLE evidence → coordinator |
| [Integration checker](integration-checker.md) | verification coordinator | Component boundaries and acceptance → traced success/error/empty paths and UNVERIFIED scope → coordinator |
| [Codebase mapper](codebase-mapper.md) | onboard / research coordinator | Validated source scope and owned map paths → committed repository map and SUMMARY → coordinator |
| [UI researcher](ui-researcher.md) | ui-phase coordinator | Approved UI decisions and assigned output → committed UI-SPEC and SUMMARY → coordinator and ui-checker |
| [UI checker](ui-checker.md) | ui-phase coordinator | Captured UI-SPEC and CONTEXT → evidenced read-only verdict → coordinator |
| [UI auditor](ui-auditor.md) | ui-review coordinator | Running UI, acceptance and optional external capture_dir → returned UI-REVIEW and external captures → coordinator |
| [DOM verifier](dom-verifier.md) | verify-work coordinator | Running URL and live-DOM criteria → returned DOM-VERIFY observations → coordinator |
| [Security auditor](security-auditor.md) | secure-phase coordinator | Threat register and captured implementation → SECURED / OPEN_THREATS / ESCALATE evidence → coordinator, which writes SECURITY |
| [Nyquist auditor](nyquist-auditor.md) | Validation-gap coordinator | Assigned test gaps, test/fixture paths and optional VALIDATION path → committed behavioral tests and SUMMARY → coordinator |
| [Pattern mapper](pattern-mapper.md) | plan-phase coordinator | Scoped pattern question and assigned artifact path → committed PATTERNS and SUMMARY → planner via coordinator |
| [Code fixer](code-fixer.md) | code-review --fix coordinator | Assigned review findings → committed fixes and REVIEW-FIX report → coordinator |

Pattern-mapper is read-only for source inspection; its explicitly assigned evidence artifact is its sole write scope. Debugger is read-only unless an owned debug-record or source repair assignment supplies write authority. 

## Compatibility aliases

The canonical dispatch names are the filename stems in the table. Historical local names are aliases in this catalog only:

| Historical name | Canonical role |
|---|---|
| coder | executor |
| phase-preparer / preparer | planner |
| phase-checker | plan-checker |
| researcher | phase-researcher |

Do not send an alias as a host-native role name. Do not substitute a generic agent for a known exact role.

## Routing

The coordinator owns worker lifecycle, integration, shared-record mutations and publication. After dispatching work, it waits before touching that worker's owned paths or integrating its commits. A timeout is not proof that a worker has stopped; reassignment requires confirmed exit.

Other roles may request only workflow-permitted named packets; they must not recreate the coordinator's worker tree.

Use a fresh code-reviewer for independent implementation review. The author may self-check claims but cannot supply its own independent review. Plan-checker evaluates plan outcomes and dependencies; verifier evaluates delivered behavior. Doc-verifier inspects claims without executing the documented commands. Integration-checker traces real boundaries; grep counts do not prove flow.

A bounded correction carries a stable finding ID, its authority and required property. The fix hint is advisory: any permitted smaller repair satisfying the property is acceptable. The coordinator applies [bounded correction dispatch](../engineer/references/bounded-correction-dispatch.md) and chooses code-fixer when scope is already known.

## Dispatching an agent

1. Load the selected workflow and exact role method.
2. Establish user authorization, outcome, exclusions and applicable constraints.
3. Resolve the model and effort at dispatch time with the installed shim.
4. Prepare the full assignment contract, including checkout identity and output consumer.
5. Dispatch the exact role with concrete resolved host parameters inline.
6. Wait for completion or a confirmed stop before integration or reassignment.
7. Inspect returned evidence and commits, join required specialists and apply shared-record operations as coordinator.

From the repository root:

```bash
. engineer/workflows/_runtime-launcher.snippet.sh
engineer_run query resolve-model executor
engineer_run query resolve-effort executor
```

Each tool shell is independent. Source the portable launcher in the same shell call before invoking engineer_run. Use dotted query verbs documented by the runtime; never invoke an old Node tool or silently replace an unavailable operation with a success result.

Pass the resolved model and effort directly in the native dispatch call. If a resolution is `inherit`, omit that parameter so the parent's configured value applies. Do not write it into a shared role file or assume a particular model from the role's description.

Every source-changing assignment includes:

- Absolute isolated checkout root, exact branch and expected starting revision.
- Required reading, approved outcome, acceptance IDs and excluded scope.
- Exact owned source/artifact paths and assigned SUMMARY path.
- Dependency interfaces and resources requiring serialization.
- Grounded checks, working directory, expected outcome and any authorized execution ordering.
- Required return fields, consumer and continuation/handoff contract.

A worker verifies root, branch and HEAD before mutation. It never creates its own worktree, switches branches or merges. Missing or mismatched assignment data returns the exact discrepancy; it does not authorize reconstructing the assignment. All shared STATE, ROADMAP, REQUIREMENTS, decisions, todo, quick-task and milestone structures remain coordinator-owned and runtime-written.

Source-changing workers commit owned changes and their assigned SUMMARY before returning complete. Use exact-path staging and preserve unrelated dirty files. Return status, base identity, commit hashes, summary path, actual checks and Remaining. A partial artifact writer preserves useful committed work and states uncovered scope instead of claiming completion.

Read-only specialists return their complete cited packet or report with captured revision and examined scope. They write no commit or SUMMARY. A coordinator-assigned external capture path is permitted only for the explicitly assigned report or browser evidence; it must resolve outside the checkout.

## Native hosts

Only Claude and Codex integration is supported. Shared Markdown methods are host-neutral and contain no `model:`, `effort:` or `maxTurns:` frontmatter. The installer produces host-native definitions and configuration from the shared source.

### Claude

Use the installed exact role definition and dispatch with resolved model settings. Installer defaults, before project overrides, are:

| Role | Claude default | Effort |
|---|---|---|
| executor | sonnet | Inherit |
| planner | opus | medium |
| Other roles | Resolve project/default policy | Resolve project/default policy |

Only the installer export for planner supplies its default medium effort. Defaults belong in generated native definitions; they must not be copied into shared role frontmatter. Project-configured overrides are resolved at dispatch time.

### Codex

Use Codex native agent dispatch with the exact role method and resolved model/effort arguments. The runtime owns the supported concrete model names and validates the current host policy. Do not hardcode a model alias into shared instructions or silently swap providers.

| Role group | Codex resolution policy |
|---|---|
| executor | Project agents.executor override, then runtime profile/default |
| planner | Project agents.planner override, then runtime profile/default |
| phase-researcher | Project agents.phase-researcher override, then runtime profile/default |
| plan-checker | Project agents.plan-checker override, then runtime profile/default |
| Review, documentation, mapping, UI and security roles | Exact role override, then runtime profile/default |

Resolve each role separately even if another role in the same batch appears similar. A supported host's default model is a runtime concern, not authority to skip resolution.
## Verification and continuation

A frozen verification batch captures one revision. Configured checks and independent specialists may inspect it concurrently, but the coordinator waits for every result before accepting evidence, repairing files or capturing another batch. A provisional specialist pass does not establish the joined phase verdict.

Receipts identify revision, root, command, environment, covered scope, exit status and observed outcome. Reuse only applicable evidence and avoid duplicate checks. Missing, timed-out, skipped or explicitly deferred execution cannot be described as passing.

At a context limit, reviewers return examined and unreached scope. Source workers converge on a safe committed boundary, write blocked SUMMARY with Remaining and return a continuation digest through `engineer_run query handoff.write`. Artifact writers can return useful partial coverage with named gaps. Context exhaustion never authorizes success or a fabricated human checkpoint.

Consequential decisions and shared progress are returned as coordinator proposals. The coordinator records them through runtime operations after inspecting the evidence. Publication follows the selected workflow and canonical Git rules; merging always requires the user's explicit instruction.
