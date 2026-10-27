# Workflow features and evidence

The repository combines complete detailed authoring templates, procedures that coordinate bounded agents, and a Python runtime that owns structured planning records. This guide inventories the main capabilities, the evidence each one owns and the limits on interpreting it. Read [Project and phase workflow](PHASE-WORKFLOW.md) for the end-to-end route, [the runtime guide](../engineer/bin/README.md) for actual verbs and arguments, and the [complete template registry](../engineer/templates/README.md) before authoring records.

## Capability inventory

| Feature | What it provides | Owner or entry point | Boundary |
|---|---|---|---|
| Greenfield onboarding | Establish real product intent, outcomes, phase order and executable checks | [onboard](../commands/onboard.md), `new-project` workflow | Product intent comes from the user and observed evidence, never from the skeleton |
| Brownfield adoption | Inspect existing code and establish a source-backed baseline | [codebase-mapper](../agents/codebase-mapper.md) | Maps describe inspected code; they do not automatically define approved product intent |
| Roadmap phase operations | Add, insert, remove or edit phases while keeping numbering, directories and checklists aligned | [phase](../commands/phase.md) and the selected add/insert/edit/remove workflow | The runtime allocates numbers; decimal insertions preserve existing numbering |
| Milestone cycles | Group phases and close with a truthful record of shipped outcomes | [new-milestone](../commands/new-milestone.md), [complete-milestone](../commands/complete-milestone.md) | Closeout audits open phases; no force path turns incomplete evidence into shipped work |
| Discussion and specification | Clarify falsifiable scope, lock decisions, retain canonical refs and record deferred ideas | [discuss-phase](../commands/discuss-phase.md), [spec-phase](../commands/spec-phase.md) | Discussion and an approved specification do not prove implementation or grant phase authority |
| Todo capture and routing | Preserve an idea mid-session, list pending items and match relevant items during discussion | [capture](../commands/capture.md), `todo.*` runtime operations | A match does not authorize implementation; new findings are not automatically todos |
| Quick tasks | Deliver one bounded outcome with its own plan, isolated work and tracked state outside the roadmap | [quick](../commands/quick.md) | A quick request is not a shortcut around acceptance, ownership or merge authority |
| Quick batches | Run a bounded set of compatible small tasks with explicit records and lifecycle | [quick-batch](../commands/quick-batch.md) | Batch limits do not turn unrelated capabilities into one outcome |
| Bounded research | Resolve technical uncertainty with source and primary-documentation evidence before planning | [phase-researcher](../agents/phase-researcher.md), plan-phase | Research cannot authorize a new product direction; recommendations need a real validation check when required |
| Detailed phase plans | Give workers concrete actions, read-first inputs, ownership, dependencies, acceptance and checks | [plan-phase](../commands/plan-phase.md), [plan template](../engineer/templates/phase-prompt.md) | Every check is an argv list with a stated failure signal; a plan is not implementation evidence |
| TDD when assigned | Establish RED evidence before behavior changes, then GREEN evidence after implementation | [executor](../agents/executor.md), [TDD method](../engineer/references/tdd.md) | Only when the runtime/workflow marks TDD applicable; preserve actual commands and results in SUMMARY |
| Independent plan check | Examine goal coverage, interfaces, dependencies and task usability from the goal backward | [planner/checker workflow](../engineer/workflows/plan-phase.md), `plan-checker` | Findings are fixed within bounded rounds or returned unresolved; they are not waived into readiness |
| Fresh implementation workers | Assign a focused executor to each ready plan with its own context and owned paths | [execute-phase](../commands/execute-phase.md), [executor](../agents/executor.md) | Workers stay within declared ownership; they do not dispatch children or write shared records |
| Dependency and overlap scheduling | Run independent ready plans concurrently while serializing real path or resource conflicts | `execute-phase` workflow and runtime worktree records | Declared wave is descriptive; dependencies and overlap govern actual scheduling |
| Human checkpoints | Escalate decisions, observations or actions that truly require the human | Executor checkpoint protocol | Human-verify, decision and human-action have distinct meanings; a guess or mode setting is not a human reply |
| Code review | Obtain a fresh independent review of changed source | [code-review](../commands/code-review.md), [code-reviewer](../agents/code-reviewer.md) | Author self-check is not independent review; actionable findings need dispositions |
| Outcome verification | Inspect integrated behavior against phase acceptance at one frozen revision | [verify-work](../commands/verify-work.md), [verifier](../agents/verifier.md) | Reports become stale as source or covered inputs change |
| Requirement validation architecture | Map requirement claims to behavior, tests, negative cases and evidence coverage | [validate-phase](../commands/validate-phase.md), [VALIDATION template](../engineer/templates/VALIDATION.md) | A filename match or generated test alone does not demonstrate coverage |
| Honest abstention | Preserve `human_needed` when a criterion lacks evidence or actual human judgment | Verification workflow and [verification evidence](../engineer/references/verification-evidence.md) | Silence, source inspection, issue closure or an agent cannot supply human acceptance |
| Gap correction | Route in-scope findings to bounded isolated repair and return to verification | [verify-work](../commands/verify-work.md), executor/debugger/planner as applicable | A repair needs current evidence at a new freeze; gaps are not automatically todos or new scope |
| Canonical security tracking | Preserve planned threat identities, mitigations, outcomes and canonical provider tracking | `secure-phase`, [security-auditor](../agents/security-auditor.md), [canonical threat method](../engineer/workflows/_canonical-threat-tracking.md) | Keep each PLAN register and observed outcome distinct; no duplicate tracker or invented anchor |
| UI specification and review | Assess real UI scope and record an approved visual/interaction contract | `ui-phase`, `ui-review`, [UI-SPEC](../engineer/templates/UI-SPEC.md) | An enabled assessment does not invent UI for a CLI/backend-only phase |
| Verified publication | Push and open/update a draft, inspect provider state and report actual check outcomes | [ship](../commands/ship.md), [PR template](../engineer/templates/pull-request.md) | Readiness requires current passed verification and required gates; merge requires explicit instruction |
| Situational awareness | Derive current position and recommend one next action | [progress](../commands/progress.md), [next](../commands/next.md) | Both detect unfinished work; progress only reports, and next stays within existing authority |
| Durable continuation | Preserve an interrupted assignment's exact goal, authority, revisions, commits, dirty paths, gates and next action | [worker handoff](../engineer/references/worker-handoff.md), `handoff.*` runtime verbs | A continuation resumes existing authority and cannot discard dirty work or fabricate a completed boundary |
| Planning-record review and repair | Find drift and apply guarded structural corrections from current evidence | [clean-planning](../commands/clean-planning.md) and runtime planning operations | Validation is warn-only; repair requires current digest and approved exact paths |
| Exact cleanup | Preview and then remove only owned, integrated work after fresh exact approval | [cleanup](../commands/cleanup.md), cleanup reference | A successful check, branch name or apparent PR is not integration evidence |
| Advisory hooks | Warn about common workflow mistakes | [hook guide](../engineer/hooks/README.md) | Hooks are advisory, not a sandbox, permission gate or worker-stop proof |
| Host installation profiles | Install commands, workflows and agents for a supported host with discoverable skills | [install](../commands/install.md) | Existing settings stay authoritative; documented host tools are not guaranteed installed |

## What is executable, and what is guidance

| Layer | Present behavior | How to use it |
|---|---|---|
| Python runtime | Reads and writes structured planning records, including phases, roadmap/state, todos, quick tasks, milestones, verification status and model resolution | Use the repository's `engineer_run query <verb>` interface; see the [runtime guide](../engineer/bin/README.md) for actual argv and result shapes |
| `commands/` | User-facing routes that name the owning workflow and authority boundary | Ask in ordinary language or read the selected command entry |
| `engineer/workflows/` | Procedures for loading context, dispatching roles, calling runtime operations and handling outcomes | Read the complete selected workflow before acting; the command is only a router |
| `agents/` | Role methods, responsibilities, evidence contracts and write boundaries | Dispatch the exact role named in the workflow with resolved model/effort and bounded inputs |
| `.agents/skills/` | Skills mirroring command routes and focused reusable methods | Select applicable skills and preserve their stated host and project boundaries |
| `engineer/templates/` | Complete authoring templates with teaching content and local runtime extensions | Read the [registry](../engineer/templates/README.md) and the selected template fully; preserve its fields, examples and consumer guidance |
| Documented host/provider tools | Routes referenced by workflows for Git, PRs, checks and human interaction | Confirm the actual tool is available and report observed results; documentation alone does not establish installation or execution |

Specialist roles connect to existing procedures: codebase mapping supports onboarding and research; planning feeds an independent check; doc-writer authors assigned documentation and doc-verifier checks its claims; integration-checker traces boundaries; code-reviewer and verifier provide independent evidence. Agent files define methods; they do not by themselves install a route or prove that the method ran.

## Tracked project data

```text
.planning/
  PROJECT.md                    Purpose, users, boundaries and confirmed intent
  REQUIREMENTS.md               Desired outcomes with REQ IDs, and out-of-scope
  ROADMAP.md                    Phase goals, order, plan checklists and milestones
  STATE.md                      Living session memory; derived counters and blockers
  MILESTONES.md                 Audited outcomes for shipped milestones
  milestones/                   Long-form milestone summaries when requested
  config.yaml                   Commit behavior, model/effort overrides and real checks
  codebase/                     Inspected architecture and stack maps
  todos/pending|completed/      Captured ideas awaiting a home or disposition
  quick/YYMMDD-NNN-slug/        Bounded changes tracked outside the roadmap
  phases/NN-slug/
    NN-SPEC.md                  Optional locked desired phase requirements
    NN-CONTEXT.md               Decisions, authority, refs and deferred ideas
    NN-DISCUSSION-LOG.md        Questions and answers; audit only
    NN-RESEARCH.md              Relevant cited investigation
    NN-CC-PLAN.md               Bounded executable instructions
    NN-CC-SUMMARY.md            Committed result and actual evidence
    NN-VALIDATION.md            Validation strategy and coverage mapping
    NN-VERIFICATION.md          Independent integrated outcome assessment
    NN-UAT.md                   Human actions, observations and final acceptance
    NN-SECURITY.md              Threat evidence and risk lifecycle when applicable
    .continue-here.md           Optional exact continuation note
  specs/                        Evidence-backed current behavior contracts
  decisions/                    Optional linked architectural rationale
```

These are possible artifacts, not a checklist to create all of them at onboarding. Select only the records needed for the approved outcome using the [artifact guide](ARTIFACT-GUIDE.md). `STATE.md` has a bounded digest role; its derived counters come from ROADMAP and cannot be corrected by editing the counters. Blockers and deferrals have explicit owners and disposition paths. Retire entries through the runtime, not a strike-through or in-place `Closed` label. `planning.validate` reports structural or narrative drift as warn-only; a warning is still evidence to reconcile where relevant.

## Reusable instructions and host layouts

The repository keeps host-facing command and agent definitions at their stable paths. Installer profiles place them and supporting reusable files into the selected Codex or Claude layout. Project records remain under `.planning/`.

| Content | Codex installation | Claude installation |
|---|---|---|
| Root instructions | `AGENTS.md` | `CLAUDE.md` |
| Rules and fact ownership | `.codex/RULES.md`, `.codex/truth-map.md` | `.claude/RULES.md`, `.claude/truth-map.md` |
| Agents | `.codex/agents/` | `.claude/agents/` |
| Commands | `.codex/commands/` | `.claude/commands/` |
| Workflows | `.codex/workflows/` | `.claude/workflows/` |
| Guides, references and templates | `.codex/guides/`, `.codex/references/`, `.codex/templates/` | `.claude/guides/`, `.claude/references/`, `.claude/templates/` |
| Runtime and hooks | `.codex/runtime/`, `.codex/hooks/` | `.claude/runtime/`, `.claude/hooks/` |
| Skills, discovered directly | `.agents/skills/` | `.claude/skills/` |
| Hook registration | `.codex/config.toml` | `.claude/settings.json` |

The runtime launcher resolves the supported installed layout. Do not assume that a provider CLI, hook, model or host feature is available merely because a guide describes how the workflow uses it.

## Safety and failure behavior

| Failure or risk | Protection | Remaining responsibility |
|---|---|---|
| Two agents edit the same tracked file | Declared path overlap separates work into different integration waves | Plans must declare every path and shared resource they touch |
| The orchestrator edits while agents run | Workflow waits for assigned workers and respects their ownership | Confirm positive worker stop before integration, correction or reassignment |
| Concurrent writers corrupt a planning record | Runtime locking and re-derived fields serialize supported mutations | Use runtime operations; agents do not write shared records |
| An executor claims completion without a commit or full SUMMARY | Required worker return contract and integration checks reject incomplete slices | A read-only role returns its assigned cited report, not a fake source commit |
| A phase is advanced while plans remain unfinished | Routing checks actual plans and complete summaries before advancing | A stale or advanced STATE pointer does not override files and roadmap evidence |
| Required documentation is missing or inaccurate | Plan documentation obligations and independent doc review | File presence is not evidence that claims are true |
| Verification becomes stale | Report revision and covered inputs are compared with current source | Materially changed behavior needs affected current evidence |
| Unverified work is published | Ship is gated on current passed verification and provider state | Preserve the blocker; no bypass turns pending evidence into a pass |
| A PR exists while its checks are pending | Provider checks are read and reported for the actual head | PR existence is not delivery or readiness evidence |
| Scope creeps during discussion | ROADMAP/locked specification bound the phase; new capability is deferred or separately captured | Do not silently append new acceptance |
| A checkpoint blocks one part of a wave | The exact decision or human action is reported; independent work may continue | Do not resolve it by guessing or let a mode flag stand for human input |
| A cleanup target appears merged by name only | Runtime requires ownership and integration evidence plus fresh approval | Verify actual ancestry/provider state and preserve dirty or unintegrated work |

## Checks and evidence limits

| Evidence type | Establishes | Does not establish alone |
|---|---|---|
| Runtime verb result | The supported record operation returned its observed result | Feasible product design or correctness of task detail |
| Real Git/subprocess tests | The runtime contract those exact tests exercised | Quality of model reasoning or behavior outside tested inputs |
| Project checks in `verification.commands` | The outcomes asserted by commands actually run in the stated environment | Untested deployment conditions, omitted failure paths or unconfigured checks |
| Documentation audit | Claims match inspected source and supplied observations within the review scope | Implementation correctness beyond that evidence |
| Independent outcome review | Acceptance traced through connected behavior at a known revision | Human judgment that was not actually observed |
| Provider status checks | Actual reported CI/review state for the published revision | Delivery of newer unpushed commits or user acceptance |
| Template/schema validation | Required structural form and recognized metadata | Safe content, complete semantic coverage, provider state or authorization |

Configured project checks begin empty for a new adopting project until meaningful commands are selected. Installing dependencies, parsing templates, reading source or seeing a success-shaped file does not establish readiness. Reports name actual commands, results, skipped checks and material limitations. “Not run,” “not configured,” “failed” and “unverifiable” must remain distinct.
