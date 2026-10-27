# Agent catalog

Read [the engineering rules](../engineer/RULES.md) and [agent adaptation](../engineer/references/agent-adaptation.md) before dispatch. This catalog defines the shared roles for Claude and Codex. The selected command and workflow own procedure; the role method owns the worker's behavior. See the [reference catalog](../engineer/references/REFERENCE.md) for detailed methods.

## Roles and evidence flow

| Role | Dispatcher | Input â†’ result â†’ consumer |
|---|---|---|
| [Coordinator](coordinator.md) | Human's selected command/workflow | Authorized outcome and records â†’ assignments, joined evidence, shared-record updates and delivery â†’ human |
| [Executor](executor.md) | execute-phase / quick coordinator | Assigned PLAN, isolated checkout and owned paths â†’ committed implementation plus SUMMARY â†’ coordinator |
| [Planner](planner.md) | plan-phase / quick coordinator | Approved CONTEXT, requirements and research â†’ committed PLAN/VALIDATION and shared-record proposals â†’ coordinator and plan-checker |
| [Plan checker](plan-checker.md) | plan-phase coordinator | Captured plans and authority evidence â†’ PLAN REVIEW, approved or needs-revision â†’ coordinator |
| [Phase researcher](phase-researcher.md) | plan-phase / next coordinator | Bounded questions and repository scope â†’ committed RESEARCH, sources and unresolved choices â†’ planner via coordinator |
| [Verifier](verifier.md) | verify-work / execute-phase coordinator | Captured revision, acceptance and receipts â†’ provisional goal-backward report â†’ coordinator for joined verdict |
| [Code reviewer](code-reviewer.md) | execute-phase / code-review coordinator | Captured revision and explicit diff base â†’ complete review with stable findings â†’ coordinator for capture |
| [Debugger](debugger.md) | next / verify-work coordinator | Symptom and scoped evidence â†’ demonstrated root cause and bounded correction proposal â†’ coordinator |
| [Doc writer](doc-writer.md) | execute-phase / documentation coordinator | Assigned documentation paths and source interfaces â†’ committed documents and SUMMARY â†’ coordinator |
| [Doc verifier](doc-verifier.md) | verification coordinator | Documentation and captured source revision â†’ complete claim JSON with FAIL/UNVERIFIABLE evidence â†’ coordinator |
| [Integration checker](integration-checker.md) | verification coordinator | Component boundaries and acceptance â†’ traced success/error/empty paths and UNVERIFIED scope â†’ coordinator |
| [Codebase mapper](codebase-mapper.md) | onboard / research coordinator | Validated source scope and owned map paths â†’ committed repository map â†’ coordinator |
| [Scout](scout.md) | Coordinator or specifically permitted role | One named discovery question â†’ cited read-only evidence packet â†’ named consumer |
| [Targeted fixer](targeted-fixer.md) | Bounded correction coordinator | Stable finding and required property, isolated assignment â†’ committed bounded repair and SUMMARY â†’ coordinator |
| [UI researcher](ui-researcher.md) | ui-phase coordinator | Approved UI decisions and assigned output â†’ committed UI-SPEC â†’ coordinator and ui-checker |
| [UI checker](ui-checker.md) | ui-phase coordinator | Captured UI-SPEC and CONTEXT â†’ evidenced read-only verdict â†’ coordinator |
| [UI auditor](ui-auditor.md) | ui-review coordinator | Running UI, acceptance and optional external capture_dir â†’ returned UI-REVIEW and external captures â†’ coordinator |
| [DOM verifier](dom-verifier.md) | verify-work coordinator | Running URL and live-DOM criteria â†’ returned DOM-VERIFY observations â†’ coordinator |
| [Security auditor](security-auditor.md) | secure-phase coordinator | Threat register and captured implementation â†’ SECURED / OPEN_THREATS / ESCALATE evidence â†’ coordinator, which writes SECURITY |
| [Nyquist auditor](nyquist-auditor.md) | Validation-gap coordinator | Assigned test gaps, test/fixture paths and optional VALIDATION path â†’ committed behavioral tests and SUMMARY â†’ coordinator |
| [Pattern mapper](pattern-mapper.md) | plan-phase coordinator | Scoped pattern question and assigned artifact path â†’ committed PATTERNS â†’ planner via coordinator |
| [Code fixer method](code-fixer.md) | Loaded by targeted-fixer for code-review --fix | Assigned review findings â†’ parsing, bounded repair and REVIEW-FIX method â†’ coordinator |

Pattern-mapper is read-only for source inspection; its explicitly assigned evidence artifact is its sole write scope. Debugger is read-only unless an owned debug-record or source repair assignment supplies write authority. Code-fixer is method source rather than an extra dispatch identity: dispatch targeted-fixer for bounded review repairs.

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

Unknown source location calls for one discovery scout with a named question, scoped search and cited packet. Additional scouts require separately named questions and distinct outputs. Scouts and targeted-fixer are leaves and cannot create children. Other supported non-scout roles may dispatch only workflow-permitted named read-only scout packets when the host supports the exact scout registration and has capacity; otherwise return the full scout_request through the coordinator. They must not recreate the coordinator's worker tree or dispatch generic/source-changing children.

Use a fresh code-reviewer for every source-changing phase and its independent implementation review. The author may self-check claims but cannot supply its own independent review. Plan-checker evaluates plan outcomes and dependencies; verifier evaluates delivered behavior. Doc-verifier inspects claims without executing the documented commands. Integration-checker traces real boundaries; grep counts do not prove flow.

A bounded correction carries a stable finding ID, its authority and required property. The fix hint is advisory: any permitted smaller repair satisfying the property is acceptable. The coordinator applies [bounded correction dispatch](../engineer/references/bounded-correction-dispatch.md) and chooses targeted-fixer when scope is already known.

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

Every assignment that writes includes:

- Absolute isolated checkout root, exact branch and expected starting revision.
- Required reading, approved outcome, acceptance IDs and excluded scope.
- Exact owned paths; source-changing assignments also name the required SUMMARY path. Artifact-only roles return their assigned artifact without manufacturing a SUMMARY.
- Dependency interfaces and resources requiring serialization.
- Grounded checks, working directory, expected outcome and any authorized execution ordering.
- Required return fields, consumer and continuation/handoff contract.

A worker verifies root, branch and HEAD before mutation. It never creates its own worktree, switches branches or merges. Missing or mismatched assignment data returns the exact discrepancy; it does not authorize reconstructing the assignment. All shared STATE, ROADMAP, REQUIREMENTS, decisions, todo, quick-task and milestone structures remain coordinator-owned and runtime-written.

Source-changing workers commit owned changes and their assigned SUMMARY before returning complete. Use exact-path staging and preserve unrelated dirty files. Return status, base identity, commit hashes, summary path, actual checks and Remaining. Artifact-only producers commit and return their assigned artifact; they do not create an unassigned SUMMARY. A partial artifact writer preserves useful committed work and states uncovered scope instead of claiming completion.

Read-only scouts and specialists return their complete cited packet or report with captured revision and examined scope. They write no commit or SUMMARY. A coordinator-assigned external capture path is permitted only for the explicitly assigned report or browser evidence; it must resolve outside the checkout.

## Native hosts

Only Claude and Codex integration is supported. Shared Markdown methods are host-neutral and contain no `model:`, `effort:` or `maxTurns:` frontmatter. The installer produces host-native definitions and configuration from the shared source.

### Claude

Use the installed exact role definition and dispatch with resolved model settings. Installer defaults, before project overrides, are:

| Role | Claude default | Effort |
|---|---|---|
| scout | haiku | Inherit |
| targeted-fixer | haiku | Inherit |
| executor | sonnet | Inherit |
| planner | opus | medium |
| Other roles | Resolve project/default policy | Resolve project/default policy |

Only the installer export for planner supplies its default medium effort. Defaults belong in generated native definitions; they must not be copied into shared role frontmatter. Project-configured overrides are resolved at dispatch time.

### Codex

The installer owns generated Codex native TOML role registrations and their model policy; shared Markdown is the method source, not the native registration. Use Codex native agent dispatch with the exact installed role registration and resolved model/effort arguments. The runtime owns the supported concrete model names and validates the current host policy. Do not hardcode a model alias into shared instructions or silently swap providers.

| Role | Codex native default | Effort |
|---|---|---|
| scout | Curated Luna, fixed | high |
| targeted-fixer | Curated Luna, fixed | high |
| codebase-mapper | Curated Luna | high |
| doc-writer | Curated Luna | high |
| doc-verifier | Curated Luna | medium |
| integration-checker | Curated Luna | medium |
| executor | Curated Sol | medium |
| Other registered ordinary roles | Curated Sol | high |

The installer/runtime owns the exact supported concrete model identifiers and generated TOML. Codex uses this curated native policy rather than broad project YAML model overrides. Resolve both actual model and effort at dispatch; these display family names are not literal host arguments. Fixed scout/targeted-fixer policy stays fixed.

Resolve each role separately even if another role in the same batch appears similar. A supported host's default model is a runtime concern, not authority to skip resolution. Preserve the runtime's fixed scout and targeted-fixer rules and never expand the shared catalog to unsupported hosts.

## Verification and continuation

A frozen verification batch captures one revision. Configured checks and independent specialists may inspect it concurrently, but the coordinator waits for every result before accepting evidence, repairing files or capturing another batch. A provisional specialist pass does not establish the joined phase verdict.

Receipts identify revision, root, command, environment, covered scope, exit status and observed outcome. Reuse only applicable evidence and avoid duplicate checks. Missing, timed-out, skipped or explicitly deferred execution cannot be described as passing.

At a context limit, reviewers return examined and unreached scope. Source workers converge on a safe committed boundary, write blocked SUMMARY with Remaining and return a continuation digest through `engineer_run query handoff.write`. Artifact writers can return useful partial coverage with named gaps. Context exhaustion never authorizes success or a fabricated human checkpoint.

Consequential decisions and shared progress are returned as coordinator proposals. The coordinator records them through runtime operations after inspecting the evidence. Publication follows the selected workflow and canonical Git rules; merging always requires the user's explicit instruction.
