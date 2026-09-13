# Workflow features and storage

The repository combines complete detailed authoring templates with a Python
runtime for bounded parallel execution. This guide lists available capabilities,
their evidence owners and their operational limits. For the end-to-end procedure,
read [Project and phase workflow](PHASE-WORKFLOW.md).

## Capability inventory

| Feature | What it provides | Owner or entry point | Boundary |
|---|---|---|---|
| Greenfield onboarding | Establish real product intent, outcomes, phase order and executable checks | [onboard](../.ai/commands/onboard.md) | No fictional project identity is filled during template maintenance |
| Brownfield adoption | Inspect existing code, preserve useful docs and establish the baseline | [codebase-recon](../.agents/skills/codebase-recon/SKILL.md) | Maps are evidence from inspection, not automatic truth |
| Phase selection | Stable phase directory and requirement/dependency mapping | PROJECT, REQUIREMENTS, ROADMAP, STATE in `.planning/` | State summaries require current source/process/PR observations |
| Rich authoring templates | Purpose, consumers, fillable structure, examples and quality guidance | [Template guide](TEMPLATE-GUIDE.md) | Optional specialty artifacts do not imply an installed automated workflow |
| Discuss and specify | Falsifiable scope, decisions, boundaries and explicit unresolved questions | Phase SPEC and CONTEXT | Recorded requirements do not prove implementation |
| Bounded research | Resolve technical uncertainties with source evidence | [bounded-research](../.agents/skills/bounded-research/SKILL.md) | Research cannot authorize a new product direction |
| Detailed phase plans | Concrete tasks, checks, ownership, dependencies and must-haves | `NN-CC-PLAN.md`; [template contract](../.ai/runtime/TEMPLATE-CONTRACT.md) | Full template guidance plus local runtime metadata |
| Human checkpoints and setup | Preserve explicit decisions, observations and external prerequisites | Full PLAN/context/setup guidance | Python dispatch blocks non-autonomous plans or unresolved setup; coordinator resolves and prepares autonomous continuation |
| Independent preparation check | Examine feasibility, coverage, interfaces and task quality | [Phase checker](../.ai/agents/phase-checker.md) | Coordinator arranges this; structural runtime check is insufficient alone |
| Fresh implementation workers | Focused coder or documentor per ready assignment | [Runtime](../.ai/runtime/README.md) | Workers stay inside assigned write scope and do not dispatch more agents |
| Parallel scheduling | Start ready independent components up to configured capacity | `execution.max_parallel` | Shared paths/resources serialize; worktree isolation does not isolate services |
| Dependency integration | Make prerequisites available only after audit, integration and checks | Runtime coordinator | Worker exit alone cannot release dependents |
| Documentation coverage | Keep guides/current contracts attached to changed behavior | [Documentation reference](../.ai/references/documentation.md) | Required unresolved coverage blocks completion |
| Independent outcome verification | Inspect connected behavior, errors, negative guarantees and documentation | [Verifier](../.ai/agents/verifier.md) | A report must match the checked content and come from an unchanged verifier checkout |
| Human acceptance | Persistent observed pass/fail/blocked/skipped cases when required | Runtime `uat` | Agent assumptions are not human observations |
| Recovery and explicit replanning | Preserve attempts and reuse valid committed results | Runtime `resume` and `run --replan` | No blind restart of possibly live writers |
| Draft progress visibility | Frequent committed slices pushed to an authorized draft PR | Coordinator's forge workflow | Runtime publish still requires verification; draft status is not a bypass |
| Verified publication | Push/create/update phase PR and inspect required remote checks | Runtime `publish` | Publishing does not merge or declare pending checks passed |
| Authorized final delivery | Review, merge, confirm, synchronize and clean exact merged targets | Coordinator, outside the runtime merge boundary | Preserve unrelated, dirty, unmerged and ignored data |
| Advisory hooks | Warn about common workflow mistakes | [Hook guide](../.ai/hooks/README.md) | Return success; neither sandbox nor permission enforcement |

## What is installed, executable or supplied as guidance

| Layer | Present behavior | How to use it |
|---|---|---|
| Python runtime | Parses phase records; dispatches code/docs/verifier processes; schedules, audits, integrates, recovers and publishes | `python .ai/runtime/phase.py`; follow its documented dependencies/configuration |
| Local `.ai/commands/` | Markdown procedures for the coordinator | Ask in ordinary language or read the named file; these do not register slash commands |
| Local `.ai/agents/` | Role responsibilities and write boundaries | Supply the applicable role in a bounded assignment |
| `.agents/skills/` | Focused reusable engineering methods | Select relevant skills and list required exact paths in plan inputs |
| `.ai/templates/` | All 40 complete adapted templates, with local extensions | Copy the fillable artifact portion and follow all authoring guidance |
| `.ai/library/` | Pinned supporting agent, command, workflow, reference and context documents | Read through the [support route map](../.ai/library/README.md); heed executable boundaries |
| Documented host commands/tools | Referenced where a documented workflow requires a separate installation | Do not assume available merely because their documentation is vendored |

The wider native skills/commands/agents/workflows expansion is a subsequent stage.
The current import keeps its teaching and dependencies visible so that expansion
can be accurate. It does not claim a live autonomous implementation of every
specialty library workflow.

## Tracked project data

```text
.planning/
  PROJECT.md                    Purpose, users, boundaries and confirmed intent
  REQUIREMENTS.md               Desired outcomes and identifiers
  ROADMAP.md                    Phase goals, order and dependencies
  STATE.md                      Living session memory plus derived Runtime Status
  config.yaml                   Python runtime workers, capacity and real checks
  config.json                   Optional library settings when its workflow is used
  codebase/                     Inspected architecture and stack maps
  research/                     Cross-phase/project research when useful
  phases/NN-name/
    NN-SPEC.md                  Optional locked desired phase requirements
    NN-CONTEXT.md               Acceptance, choices, questions and authorization
    NN-DISCUSSION-LOG.md         Optional preserved discussion details
    NN-RESEARCH.md              Relevant phase investigation
    NN-VALIDATION.md            Checking strategy when useful
    NN-01-PLAN.md               Bounded executable component instructions
    NN-01-SUMMARY.md            Committed component result and actual evidence
    NN-02-PLAN.md               Another component
    NN-02-SUMMARY.md
    NN-VERIFICATION.md          Independent integrated outcome assessment
    NN-UAT.md                   Human observations when required
    .continue-here.md           Optional continuation note
  specs/                        Verified current behavior contracts
  decisions/                    Significant architectural rationale
  maintenance/                  Explicitly authorized template-maintenance records
```

Optional templates also describe milestone archives, debugging sessions,
preferences, profiles, security, UI/AI specifications and setup records. Their
own full templates define their output destinations and consumers. Do not create
every possible record during onboarding. Use the [template catalog](TEMPLATE-GUIDE.md)
to identify the right artifact.

`.planning/config.yaml` and the library `config.json` represent distinct
configuration contracts. The Python runtime reads YAML. JSON options are not
silently mapped, and setting a JSON option does not configure the Python runner.
The directory listing shows possible artifacts, not a requirement that every
project immediately creates all of them.

## Reusable instructions and human guides

```text
AGENTS.md                       Repository entry point
.ai/
  RULES.md                      Shared authority and completion rules
  truth-map.md                  Fact ownership and conflict routing
  agents/                       Local role responsibilities
  commands/                     Local coordinator procedures
  references/                   Local handoff, documentation and operation details
  templates/                    Complete templates plus local extensions
  library/                      Full supporting guidance and route map
  runtime/                      Executable runner and its template adapter contract
  hooks/                        Optional advisory hook implementations and tests
.agents/skills/                 Selected reusable engineering methods
docs/                          Human-facing workflow and feature guides
changes.log                    Recorded migration adaptations and their reasons
```

## Local work and operational storage

| Location | Contents | Persistence and recovery |
|---|---|---|
| Primary checkout | Inspection and verified fast-forward synchronization | Tracked edits and commits happen in assigned worktrees |
| Primary `.worktrees/<assigned-name>/` | Integration or component checkout on its assigned branch | Preserve clean unmerged and dirty/incomplete work; cleanup needs exact scope and merge evidence |
| Git common directory `ai/phases/` | Coordinator lock, phase/checkout attempt state, immutable-input evidence, process records, prompts and logs | Shared across linked worktrees; machine-local and not cloned |
| Committed phase SUMMARY/VERIFICATION/UAT | Durable results and evidence | Travels with commits and PRs; names checked source/relevant limits |
| Host environment | Credentials, executable availability and permissions | Not supplied by a template or guaranteed by a worker prompt |

Resolve the Git common directory from Git itself. In a linked worktree, `.git`
is normally a pointer file, so appending paths to the worktree's `.git` as though
it were the primary metadata directory is incorrect.

## Safety and failure behavior

| Failure or risk | Protection | Remaining responsibility |
|---|---|---|
| Workers edit the same tracked file | Declared ownership overlap serializes; committed output is audited | Plans must assign all relevant files accurately |
| Workers share a port/database/service | Exclusive resource declarations serialize known conflicts | Worktrees cannot sandbox arbitrary external writes |
| Two coordinators alter shared Git state | Repository-wide common-directory lock | One coordinator runs at a time; bounded component concurrency remains available |
| A worker claims success without committing | Runtime checks result, commits, ancestry, paths and cleanliness | Outcome verification still must establish actual behavior |
| Required documentation is missing | Explicit obligations and SUMMARY coverage checked | Verifier checks truth, not just file presence |
| A prerequisite fails checks | Dependents remain waiting | Coordinator repairs/rechecks without discarding unrelated successful output |
| Coordinator stops around process launch | Supervisor and worker identities retained for reconciliation | Inspect ambiguous/live process evidence; do not assume restart is safe |
| Check changes tracked content | Inspection failure preserves changed state | Resolve/commit deliberately before explicit retry/replan |
| Phase inputs change during execution | Recorded inputs/fingerprints prevent silent reinterpretation | Reconcile stopped work and explicitly replan within authorization |
| Verification becomes stale | Revision/content attestation checked | Material changed behavior needs current independent evidence |
| Human acceptance is incomplete | Required current UAT passes and notes checked | Failed/blocked/skipped is unresolved, not waived |
| PR exists but checks are pending | Required remote checks observed separately | Do not declare ready or delivered from PR existence |
| Cleanup might delete unrelated work | Exact path, clean state, merge and authorization checks | Preserve uncertain or ignored data instead of forcing removal |

## Checks and evidence limits

| Check type | Establishes | Does not establish alone |
|---|---|---|
| Runtime structural check | Parseable inputs, valid ownership/dependency structure and required settings | Feasible product design or correct task detail |
| Real Git/process regression | The exercised scheduler, audit, integration or recovery behavior | Quality of live model reasoning or live external account permissions |
| Component/project tests | Outcomes exercised by actual assertions in the stated environment | Untested deployments or omitted failure paths |
| Documentation audit | Claims match inspected code and observed evidence | Implementation correctness beyond that evidence |
| Independent outcome review | Acceptance traced through integrated behavior at a known revision | Human judgment that was never observed |
| UAT | Actual recorded human observation for current cases | Unobserved cases or changed content after the observation |
| Remote status checks | Observed CI/review status for the published revision | Delivery of newer unpushed commits |

Configured checks begin empty for a new adopting project until meaningful
commands are selected. Installing dependencies or parsing a template does not
establish readiness. Reports identify actual commands, results, skipped checks,
mocked boundaries and material limitations.
