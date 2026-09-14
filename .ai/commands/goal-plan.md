# Plan project goals

A goal describes a result you want for the project. The workflow turns that result
into requirements, bounded phases and component plans, then checks the implemented
behavior against the original acceptance. A goal does not register a new runtime
object or command. Its context lives in the project's existing planning records.

Read [RULES](../RULES.md), PROJECT, REQUIREMENTS, ROADMAP, STATE and existing
relevant phase records. Write authorized changes in an [assigned worktree](worktree.md).
Use the first-goal or ordered-goals prompts below. If project purpose and baseline
are unclear, start with [onboard](onboard.md). You can discuss several goals at
once while preparing only the next useful phase.

## Give the agent a useful starting point

Describe who needs the outcome, the problem they face, and one concrete example
of success. Add constraints, exclusions, relevant reference paths and any decisions
already made. Unknowns can remain explicit. The agent should inspect what it can
and ask about choices that require your intent.

For several goals, give your preferred order and explain why it matters. Priority,
technical dependency and an unresolved decision are different reasons for waiting.
One goal may span several phases; closely related goals may share one phase when
they form a coherent outcome. Neither the number of goals nor a template's sample
phase count dictates the implementation plan.

State the task's boundary: discussion only, committed preparation, implementation,
PR publication, or delivery including an authorized merge. A planning request
authorizes the requested records, not automatic implementation of everything
mentioned. Earlier explicit authorization remains valid within its scope.

## Build the context in order

| Step | Work to do | Durable result and readiness evidence |
|---|---|---|
| Inspect the starting point | Read actual project intent, relevant source, guides, tests, recent history and existing phase records | Canonical source references and an observed baseline; useful codebase maps when needed |
| Define the outcome | Resolve included behavior, exclusions, users, compatibility and material choices | Checkable requirements; confirmed decisions and explicit questions |
| Choose phase boundaries | Group coherent outcomes and identify what each phase needs from earlier work | ROADMAP order and phase mapping, with reasons for dependencies |
| Capture phase context | Record the exact goal, acceptance, decisions, references and authorization | Complete `NN-CONTEXT.md`; phase `NN-SPEC.md` when detailed desired behavior needs one |
| Resolve technical uncertainty | Inspect or research only what affects the selected scope | Relevant evidence and decisions linked from CONTEXT; unresolved dependent work remains blocked |
| Prepare and check components | Specify bounded tasks, interfaces, ownership, dependencies, checks and documentation | Complete `NN-CC-PLAN.md` files, independent preparation findings for substantial scope, and structural readiness results |
| Implement and verify | Execute authorized prepared work, integrate checked commits, correct gaps and verify behavior | Committed changes and SUMMARY files, current independent VERIFICATION, and passing required UAT |
| Continue to the next goal | Compare the next proposed scope with what was actually implemented and delivered | Updated context and prerequisites; a freshly assessed next phase |

These steps use the existing [phase procedures](README.md) and
[runtime contract](../runtime/TEMPLATE-CONTRACT.md). Preparation can revisit
discussion when inspection reveals a real missing choice. That should block its
dependent scope while independent work continues.

## Keep each fact in its owner

| Record | What belongs there |
|---|---|
| `.planning/PROJECT.md` | Project purpose, users, core value, boundaries and enduring context |
| `.planning/REQUIREMENTS.md` | Identified desired outcomes and traceability to phases |
| `.planning/ROADMAP.md` | Goal-to-phase mapping, phase order, dependencies and navigation |
| Phase `NN-CONTEXT.md` | Exact acceptance, decisions, canonical references, open questions and actual authorization |
| Phase `NN-SPEC.md`, when useful | Detailed desired behavior, boundaries and falsifiable criteria, referenced by CONTEXT |
| Phase `NN-CC-PLAN.md` | One component's executable assignment and acceptance coverage |
| Phase SUMMARY / VERIFICATION / UAT | Observed results and evidence at the relevant revision |
| `.planning/STATE.md` | Compact continuation context grounded in current records and observations |
| `.planning/specs/` | Verified current behavior; proposed future behavior stays in its phase |

Follow the [truth map](../truth-map.md) and complete authoring templates.
Reference existing decisions and specifications rather than copying their full
contents into every phase. A transcript preserves a discussion; CONTEXT records
what was actually decided. A new conversation should load that context before
asking the same questions again.

## Write acceptance that can decide whether the goal worked

Describe an action or input, its conditions, and the observable result. Include
relevant failure paths and compatibility requirements. Give criteria stable IDs
and connect them to implementation, checks and documentation ownership.

For example, **if the agreed goal is exporting existing records**, "add export"
does not establish enough detail. Useful questions include which records are
included, the output format, ordering, empty results, invalid input and failure
behavior. Record the answers as acceptance; do not choose product behavior just
to fill the example. Check the complete path from the existing records through
the export entry point to the resulting output.

The presence of an export module does not prove that users can export. Likewise,
a successful worker exit or a passing parser check does not prove acceptance.
The independent verifier assesses connected behavior at the integrated revision.
Human-only criteria require actual observations, not an agent's prediction.

## Order several goals without planning too far ahead

At the project level, establish enough detail to understand each goal's value,
boundary, likely phase outcomes, shared constraints and real prerequisites.
Maintain an explicit mapping in ROADMAP and requirement traceability. Detail the
next useful scope; future component tasks can remain undecided until their source
and interfaces are known.

Consider an illustrative sequence: record entries, export entries, then schedule
exports. Export consumes a defined record interface; scheduling consumes a working
export capability. Those are real dependencies if the intended behavior requires
them. A separate visual adjustment may be lower priority without depending on
either capability. Agree shared contracts before trying to parallelize their
implementations. Do not turn every earlier item into a dependency of every later
item merely because it appears first in the list.

Within a phase, component `depends_on` identifies other component IDs. The runtime
starts a dependent component after its own prerequisites are integrated and
checked. Overlapping paths and exclusive resources serialize work separately;
wave labels do not create a global scheduling barrier.

Across phases, CONTEXT `depends_on` names prerequisite phase directories. The
runtime requires their verified behavior to be delivered to the configured remote
base branch. An open PR or verified local commit alone does not satisfy that
requirement. When the delivery boundary stops at an open PR, report the dependent
phase's remaining prerequisite; do not merge without authorization. The runtime
never performs merges. Use stable integer `NN-slug` phase names with this runtime;
decimal examples in upstream templates are not executable phase identifiers here.

After a phase, carry forward the actual interfaces, decisions, validation results,
documentation and remaining questions. Refresh the next phase against that
revision. If evidence changes its required approach within approved scope, record
the adjustment. If the outcome itself needs to change, resolve that decision with
the user before implementing dependent work.

## Know when preparation is ready to execute

The [preparation procedure](phase-prepare.md) requires concrete
assignments and meaningful project checks. Every acceptance outcome needs an
implementation owner and evidence, including the connections between components.
Assign required documentation to the component that will actually complete it.

Substantial scope receives an independent preparation check of coverage,
feasibility, interfaces and source evidence. The Python runtime's `check` command
also validates structure and dependencies. These are separate assessments.
Neither supplies user authorization or proves the future implementation works.

Before execution, the inputs are committed, the assigned worktree is clean,
relevant decisions are resolved, actual worker routes and checks are configured,
and prerequisite behavior is available. Non-autonomous checkpoint plans and
unresolved external setup cannot simply be launched by `run`; the coordinator
must resolve their prerequisites and prepare an autonomous continuation.

Use [phase-start](phase-start.md) for authorized execution, then
[phase-verify](phase-verify.md) for independent assessment and
corrections. Keep required documentation and acceptance evidence with the phase.
Publication, observed delivery and cleanup follow the user's actual boundary.

## Ask for a useful handoff

After planning, expect the agreed goal, current-versus-target evidence, requirement
and phase mapping, decisions, open questions, prepared files, committed revision,
check results and exact next action. Unresolved questions should identify the work
they block. Later goals should retain enough context to resume without being
presented as executable assignments before their prerequisites are known.

After implementation, expect the behavior achieved, relevant checks and results,
updated documentation, independent verification, unresolved acceptance and the
actual publication/delivery state. Preserve incomplete work and failed evidence.
A goal is complete because its agreed outcome is demonstrated, not because every
planned file or heading exists.

## Complete authoring sources

Read the complete [context](../templates/context.md) and, when needed,
[phase specification](../templates/spec.md) templates before writing phase records.
Preparation uses the complete [phase prompt](../templates/phase-prompt.md) and
[planner prompt](../templates/planner-subagent-prompt.md), with the local
[runtime contract](../runtime/TEMPLATE-CONTRACT.md). Preserve their applicable
artifact sections and teaching guidance; fill records with actual project facts.
The [phase-decomposition skill](../../.agents/skills/phase-decomposition/SKILL.md)
provides the method for choosing boundaries and mapping acceptance to components.
These authoring sources support the procedure above; their examples do not
establish this project's decisions or execution authorization.

## Copy-ready goal requests

### Define project direction without implementation

> Help define desired outcomes and group them into coherent phases. Use the full
> project, requirements, roadmap and relevant phase specification/context
> templates. Record agreed direction in `.planning/`, with falsifiable acceptance,
> boundaries, dependencies and unresolved decisions. Detail the next useful phase.
> Do not begin implementation yet.

### Define the first goal

Use this after onboarding when you have a useful outcome in mind but need enough
context and detail to make it implementable. A goal can fit one phase or require
several; the agent should justify that choice from the actual work.

```text
Help turn my first goal into an implementable scope for this project.

Goal: [the outcome I want and who benefits]
Example of done: [a concrete action/input and the observable result]
Known constraints or exclusions: [what must be preserved or omitted]
Relevant references: [paths, prior decisions, designs or reported failures]
Authorization: investigate, discuss, record context and prepare the next phase.
Commit preparation locally. Do not implement or publish in this task.

Read PROJECT, REQUIREMENTS, ROADMAP, STATE and relevant existing phases before
creating new records. Inspect the source and checks involved in the goal. Reuse
existing phase context when this is already tracked; preserve agreed project
constraints and authorization from earlier instructions.

First describe the observed starting point and the target behavior. Identify the
smallest useful complete outcome, affected users/components, integration points,
and meaningful success, failure and compatibility cases. Ask focused questions
about consequential unknowns. Research technical uncertainty only where it affects
the goal. Record confirmed decisions and their reasons separately from assumptions,
recommendations and open questions; say which work each open question blocks.

Translate the agreed goal into checkable requirements and phase goals. Use the
local phase procedures and full artifact templates. Keep PROJECT as project
context, REQUIREMENTS as outcome tracking, and ROADMAP as phase navigation/order.
Give each selected phase stable acceptance IDs, an exact boundary, dependencies,
canonical source references and actual authorization in its CONTEXT. Use a phase
SPEC when detailed desired behavior needs it, and reference it from CONTEXT.
Do not present the proposed behavior as a current verified specification.

Prepare the next useful phase in detail only when its decisions and prerequisites
support that work. Define bounded component plans with real ownership, interfaces,
dependencies, required reads, applicable skills, checks and documentation owners.
Map each acceptance outcome to implementation and evidence, including interactions
between components. Configure actual project checks and available worker routes;
leave unavailable prerequisites visible. Have substantial preparation independently
checked, resolve findings and run the runtime readiness check on committed inputs.
Distinguish structural readiness from the checker's semantic assessment.

Return the agreed goal, current-versus-target evidence, requirements and phase
mapping, decisions/open questions, prepared files and commit, coverage/check
results, and what must happen before implementation can start. Keep adjacent
ideas deferred with reasons; do not enlarge the goal to fill a template.
```

### Define several goals in order

Use this when you know several outcomes you want to pursue. Give the desired order
and explain whether it expresses priority or a real prerequisite. This prompt
builds a shared direction while detailing only the next useful scope.

```text
Help define this ordered set of goals and build the project context needed to
implement them through phases.

Goals in my preferred order:
1. [Outcome, intended user and example of done]
2. [Outcome, intended user and example of done]
3. [Outcome, intended user and example of done; remove/add lines as needed]

Why this order matters: [priority, deadlines, technical dependency, or not decided]
Shared constraints and exclusions: [compatibility, data, interfaces, other limits]
Existing references and decisions: [paths or previous agreed context]
Authorization: investigate, discuss, record the ordered goals and phase context,
and prepare the next useful phase. Commit this preparation locally. Do not start
implementation or publication in this task.

Read the actual project context, current implementation, tests and existing plans.
For every goal, identify current behavior, desired behavior, affected users and
interfaces, success evidence and unresolved decisions. Reuse settled context and
existing phases instead of duplicating work. Ask questions in focused groups;
continue analysis of independent goals while a dependent decision is unresolved.

Build one coherent mapping from goals to requirements and phase outcomes. Explain
when one goal needs multiple phases or when closely related goals belong in one
phase. Keep every phase independently understandable and verifiable. Separate my
priority order from actual dependency edges: name the specific behavior or contract
a dependent phase consumes. Identify shared decisions and establish their owners.
Do not invent dependencies merely to make the list sequential, and do not reorder
a consequential user priority without recording its resolution with me.

Record project-wide purpose/constraints in PROJECT, desired outcomes in
REQUIREMENTS, and the phase order and goal mapping in ROADMAP. Use existing
artifact owners rather than inventing a separate goal registry or new runtime.
For phases we agree to define now, record their boundaries, acceptance, relevant
decisions, canonical references, open questions and authorization in phase CONTEXT.
Use a phase SPEC where detailed desired behavior warrants it. Future possibilities
remain proposals or deferred ideas; their appearance in a roadmap is not approval
to implement them. Preserve existing phase IDs and execution history.

Prepare detailed component plans only for the next useful decided scope. Cover
its exact acceptance, source inputs, ownership, shared interfaces, integration
checks, exclusive resources, documentation and true prerequisites. Use actual
project checks and worker routes. Obtain independent preparation checking for
substantial work, resolve its findings, commit inputs and run structural readiness.
Leave later implementation details open when they depend on what earlier work
teaches us; record what evidence will be needed before preparing them.

Return the ordered goal/requirement/phase mapping, dependency reasons, shared
decisions, per-goal open questions, next prepared phase and check results, files
and commit, plus the next action. Explain any cross-phase delivery prerequisite:
a verified local commit or open PR is not automatically delivered behavior for
the runtime. Preserve my delivery boundary rather than silently merging to unblock
a later phase. Do not mark any goal achieved from plans alone.
```

To proceed after planning, identify the actual selected phase and acceptance and
authorize [phase-start](phase-start.md) with your delivery boundary. The
[implementation request examples](../guides/REQUESTS.md) include PR-only and
delivery-through-merge wording. If you authorize an ordered series for execution,
state which goals are included and its delivery boundary; the agent should carry
valid context forward, verify each result and reassess the next phase against
the resulting code instead of replaying stale future plans.
