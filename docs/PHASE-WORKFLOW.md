# Project and phase workflow

The workflow turns a project outcome into checked, documented implementation. Project records live in `.planning/`; reusable instructions, workflows, templates and tools live under `engineer/`, while host-facing commands and agent methods live under `commands/` and `agents/`. An orchestrator carries the request through the user's authorized boundary and dispatches fresh agents for bounded assignments.

| Reference | Owns |
|---|---|
| [Shared rules](../engineer/RULES.md) | Authority, work boundaries, fact ownership and completion policy |
| [Truth map](../engineer/truth-map.md) | Each fact's authoritative record |
| [Runtime guide](../engineer/bin/README.md) | The `engineer_run query` verb interface used by workflows |
| [Template contract](../engineer/references/template-contract.md) | How complete templates meet the Python runtime |
| [Artifact guide](ARTIFACT-GUIDE.md) | Artifact selection, producers, consumers and lifecycle |
| [Feature guide](WORKFLOW-FEATURES.md) | Capability inventory, safeguards and evidence limits |

## How a command becomes work

```text
command (commands/) ── user-facing entry; routes to a workflow
  └─ workflow (engineer/workflows/) ── procedure: context, roles, gates and runtime calls
       ├─ runtime (engineer/bin/) ── structured planning-record reads and writes
       └─ agent (agents/) ── bounded role with its own context and write boundary
```

A command is a thin router. The workflow owns the procedure: what to load, which role to dispatch, what to ask, which runtime verbs to call, and what evidence completes the route. The Python runtime owns structured planning-record changes: phase numbering, ROADMAP, STATE, PROJECT Key Decisions, REQUIREMENTS traceability, todos, quick tasks, milestones and archive structures. Do not make those structural edits by hand. Narrative prose stays in its owning artifact. The runtime launcher selects the installed host layout; only the supported Codex and Claude adapters are documented.

## 1. Onboard a new or existing project

`/onboard` is the entry point that initializes the records later workflows read. It is also available as the natural-language request “Set up this project.” Keep the template's adopting-project identity blank until actual user intent and observed evidence fill it.

| Step | New project | Existing project | Saved result |
|---|---|---|---|
| Inspect the baseline | Identify starter files, environment and available checks | Use `codebase-mapper` to inspect entry points, architecture, data flow, tests and conventions | `.planning/codebase/` maps when appropriate |
| Establish intent | Ask until the product purpose, users, core value and constraints are concrete | Confirm purpose against the actual product and user's intended change | `.planning/PROJECT.md` |
| Identify outcomes | Turn intended capabilities into observable requirement IDs | Record requested outcomes and evidence-backed gaps; preserve confirmed scope | `.planning/REQUIREMENTS.md` |
| Order the work | Group outcomes into coherent phases and dependencies | Respect existing interfaces, delivered work and real dependencies | `.planning/ROADMAP.md` |
| Configure execution | Select the project's actual checks; do not invent runnable commands | Run real baseline commands only when authorized and record their actual result | `.planning/config.yaml` |

Questioning follows the user's answers and unresolved threads rather than mechanically walking a questionnaire; use the [questioning method](../engineer/references/questioning.md). A record containing `CHANGEME` or bracketed identity placeholders is still a copied skeleton, not completed onboarding. Configure `verification.commands` with the project's real checks. If no meaningful check is configured, verification must report that limitation instead of implying that source reading proves behavior.

For an existing repository, maps describe what was inspected, not automatically approved product truth. Keep project research about possible approaches distinct from maps of code that actually exists. Onboarding establishes project intent and scope; it does not itself authorize implementation of a phase.

## 2. Shape the work

Use the phase and milestone entries to change the roadmap through the runtime:

| Command | Effect |
|---|---|
| `/phase "<description>"` | Append the next integer phase to the current milestone |
| `/phase --insert {N} "<description>"` | Insert urgent work as a decimal phase after the selected phase without renumbering existing phases |
| `/phase --remove {N}` | Remove an eligible future, unstarted phase and apply the requested numbering disposition |
| `/phase --edit {N}` | Change an existing phase's title, goal, dependencies or requirements in place |
| `/new-milestone "<name>"` | Open a milestone and allocate its phases from approved scope |
| `/complete-milestone` | Audit and close a fully shipped milestone |

Phase numbers are allocated by the runtime; do not choose or renumber them manually. Integer phases represent normal planned work. Decimal phases represent urgent insertions and preserve existing numbers. A phase edit changes roadmap scope, not implementation authority. A milestone is a grouping and closeout boundary, not permission to implement its phases. Milestone closeout audits every phase and its accepted requirements, records what shipped, and refuses an open phase; it does not merge branches, delete evidence, or start another milestone.

## 3. Take a phase through the loop

### Discuss — `/discuss-phase {N}`

Discussion identifies the choices that could change the result, lets the user select what needs discussion, and records answers incrementally in `NN-DISCUSSION-LOG.md` and the canonical decisions/context in `NN-CONTEXT.md`. Existing decisions and references are loaded before new questions. The phase's scope boundary comes from ROADMAP and any applicable locked specification; discussion clarifies how to deliver that scope and cannot silently add capability.

The workflow may match existing todos to the phase. Only actual explicit assignments or a real emitted qualifying score count as a match. It presents matches for a choice where required, records folded and reviewed items in CONTEXT, and keeps folded items pending through implementation and verification. Reconciliation occurs only at the workflow's guarded post-merge point with the required provider and human-acceptance evidence. A todo is not a substitute for a decision or an undocumented scope expansion.

Canonical references accumulate from ROADMAP and from documents the user brings into discussion. Resolve each to an existing full path before handing off. Decisions recorded in CONTEXT are locked inputs for later research and planning unless concrete conflicting evidence requires the coordinator to resolve the conflict. Discussion does not authorize phase implementation; its closing report states that planning and implementation await the applicable instruction.

### Plan — `/plan-phase {N}`

Planning researches only genuine technical uncertainty, using cited source and primary-documentation evidence. It produces complete `NN-CC-PLAN.md` assignments from the full template, then obtains an independent goal-backward plan check. A plan specifies concrete actions, read-first inputs, exclusive owned paths, dependencies and resources, acceptance mapping, documentation obligations, issue references, checks as argument arrays, and must-haves. A runnable check states both its command and the failure signal it is intended to expose. Dependencies and path/resource overlap determine safe execution groups; a descriptive wave label does not override actual overlap.

The checker asks whether executing exactly the plans would achieve the approved phase goal and whether task contracts are usable by fresh workers. The workflow permits bounded correction rounds; unresolved findings are returned rather than waived to declare readiness. A checkpoint records a real unresolved decision and blocks only dependent planning. Research cannot add, remove, or defer approved requirements. Planning readiness does not grant implementation authority.

### Execute — `/execute-phase {N}`

Execution begins only after the user explicitly instructs implementation of that phase and scope. Record the actual instruction and its boundary in CONTEXT. The coordinator verifies the isolated checkout's root, branch and base, then assigns one fresh executor per ready plan with exact inputs and owned paths. Plans with unmet dependencies or overlapping owned files/resources wait for later waves. The coordinator waits for each writer to stop before integration or touching its owned paths.

An executor completes a source-changing assignment only with its owned commit(s), full required SUMMARY and actual evidence. A read-only specialist returns its assigned cited report without a source commit. The coordinator integrates only complete, committed slices through the guarded runtime workflow; undeclared deletions, conflicts, ownership mismatches or base drift block integration. It runs the current required checks and fresh code review under the authorized check order, reconciles canonical issues and threat tracking, and preserves exact blocked or deferred outcomes. Existing folded todos remain pending here. New findings do not automatically become todos.

Checkpoint handling depends on the actual blocker. A human-verify checkpoint requests observation of a concrete result; a decision checkpoint needs a consequential choice not already delegated; a human-action checkpoint requires an action the agent cannot perform. Resolve choices already inside delegated discretion from approved context and evidence, and record consequential outcomes using the runtime. A checkpoint resolved by guessing is a defect. It blocks only dependent work; independent authorized plans can continue. Explicit human checkpoints cannot be satisfied by a mode flag, an agent's guess or a status message.

Execution does not automatically mean the phase is verified or shipped. The current workflow carries completed work into verification and, when authorized and gates pass, the same-session publication route. It never starts the next phase. A partial wave returns exact remaining plans and evidence without claiming phase completion.

### Verify — `/verify-work {N}`

Verification checks the actual phase goal backward from observable acceptance using one frozen source revision. The coordinator prepares required validation architecture and inputs before freezing the revision. Configured checks and independent read-only specialists may run against that same freeze as authorized; every assigned result must join before a verdict, repair or shared-record change. The verifier independently examines integrated behavior, documentation and supplied summaries. A summary is a claim under review, not proof by itself.

The report distinguishes passed, gaps found, human needed and blocked conditions. A criterion without enough evidence abstains; it does not pass by inference. Existing valid check receipts may be reused only when their command, configuration, inputs and ancestry still match. Required human acceptance remains a separate actual human response. A gap is routed to an authorized bounded correction or documented as unresolved; it is not silently closed or converted into a new todo. After a correction, affected evidence is refreshed at a new frozen revision. Only current passed evidence permits verified publication.

### Ship — `/ship {N}`

Shipping uses the complete pull-request template, the authorized session and canonical issue relationships. A draft is opened on the first authorized push and updated after each meaningful slice. Read provider state back; a local command or existing PR does not prove its head, checks, links or status. Readiness requires current passed verification, required provider checks and the independent issue-link audit. Threat records and issue references retain their canonical identities and evidence.

There is no bypass for a stale or non-passed verification. Shipping publishes and observes; it merges only when the user explicitly instructs merge for the specified PR and current gates pass. After provider-confirmed merge, closeout requires actual integrated ancestry and any guarded folded-todo reconciliation. If publication, checks, acceptance or merge is pending, preserve the open session and report the exact blocker. Completing this phase does not authorize another phase.

## 4. Close the milestone

`/complete-milestone` audits the selected milestone's phases, plans, summaries, verification, accepted requirement outcomes and known deferred work. The runtime owns the MILESTONES and roadmap/state mutations. The resulting entry records what actually shipped; it does not promote pending acceptance, close a branch, create release tags, delete source records or launch a follow-on milestone. `/milestone-summary` can turn the phase evidence into an onboarding-oriented narrative, but it does not replace the authoritative records.

## Work that is not a phase

| Situation | Command | Boundary |
|---|---|---|
| An idea surfaces during authorized work | `/capture "<description>"` | Records the requested idea with enough context for later routing; it does not derail current work |
| Review captured ideas | `/capture --list [area]` | Lists pending items and routes an explicitly selected item; does not assume all should be implemented |
| A small, single-outcome change | `/quick "<description>"` | Creates its own bounded plan, isolated execution, atomic commits and tracked verification outside ROADMAP |
| Several related quick outcomes need one bounded run | `/quick-batch` | Uses the documented batch boundary; it is not a way around phase scope or authority |
| Review or repair planning records | `/clean-planning` | Uses current review evidence and guarded structural operations |

Quick tasks deliberately stay outside ROADMAP and have their own runtime identity and verification record. A request with multiple independent outcomes, substantial discovery or phase-level coordination belongs in the roadmap. Do not create todos from gaps or findings unless the user explicitly requests capture.

## Knowing where you are

`/progress` reads current intent, authoritative requirements, roadmap position, recent completed summaries, decisions, blockers, pending todos, open quick work and record-health evidence. It reports one recommended next action and stops; it does not start the recommended workflow, repair records or infer delivery from a roadmap checkmark.

`/next` performs the same state-based routing and then proceeds through the selected workflow within existing authority. Both routes account for unfinished execution: when a phase has plans without corresponding complete summaries, that work must be inspected and resumed before unrelated advancement. The workflow also checks stale state pointers, checkpoints, failed verification and uncommitted planning records. A recommendation is never implementation authorization, and `/next` cannot override a phase's missing explicit instruction.

## Artifacts a phase accumulates

```text
.planning/phases/NN-slug/
  NN-CONTEXT.md          decisions, canonical refs, authority and deferred ideas (discuss)
  NN-DISCUSSION-LOG.md   questions and answers; discussion audit (discuss)
  NN-RESEARCH.md         cited technical findings at a revision (plan)
  NN-CC-PLAN.md          bounded tasks, ownership, dependencies and acceptance (plan)
  NN-CC-SUMMARY.md       delivered work and actual evidence (execute)
  NN-VALIDATION.md       requirement-to-test strategy and coverage (plan/verify)
  NN-VERIFICATION.md     frozen verdict, evidence and findings (verify)
  NN-UAT.md              runnable human actions and actual acceptance (verify)
  NN-SECURITY.md         threat coverage and evidence when applicable (verify)
  .continue-here.md      optional exact continuation context
```

Only create records required by the actual scope and workflow. Templates and the [truth map](../engineer/truth-map.md) identify who owns each fact. When source, records and documentation disagree, establish which claim is wrong using current evidence and approved decisions; do not silently reconcile the text. The [artifact guide](ARTIFACT-GUIDE.md) explains ownership and the [request guide](REQUESTS.md) shows complete natural-language examples.
