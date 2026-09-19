# Workflow features and storage

The repository combines complete detailed authoring templates, workflow
procedures that orchestrate subagents, and a Python runtime that owns every
planning record. This guide lists the available capabilities, their evidence
owners and their operational limits. For the end-to-end procedure, read
[Project and phase workflow](PHASE-WORKFLOW.md).

## Capability inventory

| Feature | What it provides | Owner or entry point | Boundary |
|---|---|---|---|
| Greenfield onboarding | Establish real product intent, outcomes, phase order and executable checks | [onboard](../commands/onboard.md) | Project intent comes from the user and observed evidence, never from the template |
| Brownfield adoption | Inspect existing code and establish the baseline before scoping | [codebase-mapper](../agents/codebase-mapper.md) | Maps are evidence from inspection, not automatic truth |
| Roadmap phase CRUD | Add, insert, remove or edit phases with numbering, directories and checklists kept consistent | [phase](../commands/phase.md) | The runtime allocates every number; decimal phases avoid renumbering |
| Milestone cycles | Group phases, then close with an honest record of what shipped | [new-milestone](../commands/new-milestone.md), [complete-milestone](../commands/complete-milestone.md) | Closing refuses while any phase is open — deliberately no force path |
| Discuss and specify | Falsifiable scope, locked decisions, canonical refs and explicit deferred ideas | [discuss-phase](../commands/discuss-phase.md) | Recorded decisions do not prove implementation |
| Todo capture | Park an idea mid-session without derailing the work, and fold it into the phase it belongs to | [capture](../commands/capture.md) | Severity is confirmed with the user, never silently assigned |
| Quick tasks | One small change with a plan, atomic commits and tracked state, outside the roadmap | [quick](../commands/quick.md) | Work needing more than three tasks is a phase |
| Bounded research | Resolve technical uncertainty with source evidence before planning | [researcher](../agents/researcher.md) | Research cannot authorize a new product direction |
| Detailed phase plans | Concrete tasks with read-first inputs, acceptance, ownership, dependencies and must-haves | [plan-phase](../commands/plan-phase.md); [template contract](../runtime/TEMPLATE-CONTRACT.md) | Every runnable verify command must state its failure signal |
| Independent plan check | Goal-backward examination of coverage, interfaces and task quality | [phase-checker](../agents/phase-checker.md) | Capped at three revision rounds, then escalated rather than approved |
| Fresh implementation agents | A focused coder per ready plan, with its own context | [execute-phase](../commands/execute-phase.md) | Agents stay inside their plan's declared paths and do not dispatch more agents |
| Wave scheduling | Plans with no unmet dependencies run concurrently | [execute-phase](../commands/execute-phase.md) | Plans declaring overlapping files are separated into later waves regardless of declared wave |
| Checkpoint escalation | A decision an agent cannot make reaches the user | [checkpoints](../references/methods/checkpoints.md) | A checkpoint resolved by guessing is a defect, not progress |
| Code review gate | A fresh reviewer judges the changed source before the phase closes | [code-reviewer](../agents/code-reviewer.md) | Critical findings block; a coder's self-check does not substitute |
| Independent outcome verification | Goal-backward inspection of connected behavior, errors and documentation | [verify-work](../commands/verify-work.md), [verifier](../agents/verifier.md) | A report is stale once its recorded revision falls behind HEAD |
| Honest abstention | A criterion that cannot be confirmed reports `human_needed` rather than passing | [honest-verifier](../references/methods/honest-verifier.md) | Only the user converts an abstention into acceptance |
| Gap closure | Plan and execute only the verification gaps, then re-verify | [verify-work](../commands/verify-work.md) | Gap closure that is not re-verified is more unverified work |
| Verified publication | Push and open or update the phase PR, reporting observed check state | [ship](../commands/ship.md) | Gated on `status: passed`; publishing neither merges nor implies checks passed |
| Situational awareness | Progress derived from the roadmap, with one recommended next step | [progress](../commands/progress.md), [next](../commands/next.md) | Both resume unfinished execution before starting new work |
| Advisory hooks | Warn about common workflow mistakes | [Hook guide](../hooks/README.md) | Return success; neither a sandbox nor permission enforcement |
| Host installation profiles | Commands, workflows and agents in the selected `.codex` or `.claude` directory, skills at discovery paths | [Installer](../commands/install.md), `--host codex\|claude` | No separate `.ai` in fresh installs; existing settings stay authoritative |

## What is executable, and what is guidance

| Layer | Present behavior | How to use it |
|---|---|---|
| Python runtime | Reads and writes every planning record: phases, roadmap, state, todos, quick tasks, milestones, verification status, model resolution | `python .ai/runtime/phase.py query <verb>`; see the [runtime guide](../runtime/README.md) |
| `.ai/commands/` | Thin routers naming a workflow, mirrored one-for-one by `.agents/skills/` | Ask in ordinary language or read the named file |
| `.ai/workflows/` | The procedures themselves: context loading, agent dispatch, runtime calls, user interaction | Read the workflow end to end before acting; the command file is a summary |
| `.ai/agents/` | Complete agent methods, responsibilities and write boundaries | Spawn by exact name; resolve the model with `resolve-model` |
| `.agents/skills/` | Command skills plus focused reusable engineering methods | Select relevant skills and name their exact paths in plan inputs |
| `.ai/templates/` | Retained complete templates with local extensions | Use the [catalog](ARTIFACT-GUIDE.md), copy the fillable portion, follow all authoring guidance |
| Documented host tools | Referenced where a workflow requires a separate installation | Do not assume `gh` or a host feature is available merely because it is documented |

Specialist agents fit the existing procedures: mapping feeds onboarding and
research; planning feeds independent checking; doc-writer produces documentation
and doc-verifier checks its claims; integration-checker and code-reviewer feed
verification. Findings go back to the responsible author, then the affected review
repeats. Agent files supply methods; they do not install runtime routes.

## Tracked project data

```text
.planning/
  PROJECT.md                    Purpose, users, boundaries and confirmed intent
  REQUIREMENTS.md               Desired outcomes with REQ ids, and out-of-scope
  ROADMAP.md                    Phase goals, order, plan checklists, milestones, progress
  STATE.md                      Living session memory; counters derived from the roadmap
  MILESTONES.md                 What each milestone shipped
  milestones/                   Long-form milestone summaries, on `--write`
  config.yaml                   Commit behavior, model overrides and the project's real checks
  codebase/                     Inspected architecture and stack maps
  todos/pending|completed/      Captured ideas awaiting a home
  quick/YYMMDD-NNN-slug/        Small changes tracked outside the roadmap
  phases/NN-slug/
    NN-SPEC.md                  Optional locked desired phase requirements
    NN-CONTEXT.md               Decisions, canonical refs, deferred ideas
    NN-DISCUSSION-LOG.md        What was asked and answered; audit only
    NN-RESEARCH.md              Relevant phase investigation
    NN-01-PLAN.md               Bounded executable instructions
    NN-01-SUMMARY.md            Committed result and actual evidence
    NN-VERIFICATION.md          Independent integrated outcome assessment
    .continue-here.md           Optional continuation note
  specs/                        Verified current behavior contracts
  decisions/                    Significant architectural rationale
```

The listing shows possible artifacts, not a requirement that a project create all
of them. Do not create every possible record during onboarding; use the
[template catalog](ARTIFACT-GUIDE.md) to identify the right one.

STATE.md's frontmatter counters are re-derived from ROADMAP.md on every write, so
they cannot be corrected by editing them — correct the roadmap.

## Reusable instructions and human guides

The installer places commands, workflows and agents inside the selected host
directory. Skills use each host's discovery location. Project records stay under
`.planning`.

| Content | Codex installation | Claude installation |
|---|---|---|
| Root instructions | `AGENTS.md` | `CLAUDE.md` |
| Rules and fact ownership | `.codex/RULES.md`, `.codex/truth-map.md` | `.claude/RULES.md`, `.claude/truth-map.md` |
| Agents | `.codex/agents` | `.claude/agents` |
| Commands | `.codex/commands` | `.claude/commands` |
| Workflows | `.codex/workflows` | `.claude/workflows` |
| Guides, references and templates | `.codex/guides`, `.codex/references`, `.codex/templates` | `.claude/guides`, `.claude/references`, `.claude/templates` |
| Runtime and hooks | `.codex/runtime`, `.codex/hooks` | `.claude/runtime`, `.claude/hooks` |
| Skills, discovered directly | `.agents/skills` | `.claude/skills` |
| Hook registration | `.codex/config.toml` | `.claude/settings.json` |

The workflow launcher resolves the runtime from whichever of these layouts is
installed, so a workflow file is portable between hosts unchanged.

## Safety and failure behavior

| Failure or risk | Protection | Remaining responsibility |
|---|---|---|
| Two agents edit the same tracked file | Declared file overlap separates plans into different waves | Plans must declare all the files they touch |
| The orchestrator works while agents run | Workflows stop after dispatch and wait for returns | An orchestrator that edits during a wave conflicts with its own agents |
| Concurrent writers corrupt a planning record | `.planning/.lock` serializes the read-modify-write; frontmatter is re-derived | One orchestrator at a time; agents do not write shared records |
| An agent claims success without committing | A plan with no SUMMARY.md or no commits is treated as blocked | Verification still must establish actual behavior |
| A phase is ticked without executing | The plans-without-summaries invariant is checked before routing | An advanced STATE.md position never overrides the artifacts on disk |
| Required documentation is missing | Explicit obligations and summary coverage are checked | doc-verifier checks truth, not just file presence |
| Verification becomes stale | The report's recorded revision is compared to HEAD | Materially changed behavior needs current independent evidence |
| Unverified work is published | Ship is gated on `status: passed` with no bypass | Preserve the branch and report blockers rather than shipping around them |
| A PR exists but its checks are pending | Check state is reported as observed from `gh` | Do not declare ready or delivered from PR existence |
| Scope creeps during discussion | New capability becomes a deferred idea or a todo | The phase boundary comes from the roadmap and is fixed |
| A checkpoint stalls a wave | The decision escalates to the user | Resolving one by guessing to finish the wave is a defect |

## Checks and evidence limits

| Check type | Establishes | Does not establish alone |
|---|---|---|
| Runtime verb result | That the record changed as instructed | Feasible product design or correct task detail |
| Real Git and subprocess tests | The exercised runtime contract the workflows depend on | Quality of live model reasoning |
| Project tests (`verification.commands`) | Outcomes exercised by actual assertions in the stated environment | Untested deployments or omitted failure paths |
| Documentation audit | Claims match inspected code and observed evidence | Implementation correctness beyond that evidence |
| Independent outcome review | Acceptance traced through integrated behavior at a known revision | Human judgment that was never observed |
| Remote status checks | Observed CI and review status for the published revision | Delivery of newer unpushed commits |

Configured checks begin empty for a new adopting project until meaningful commands
are selected. Installing dependencies or parsing a template does not establish
readiness. Reports identify actual commands, results, skipped checks and material
limitations.
