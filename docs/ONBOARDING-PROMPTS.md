<!-- generated-by: doc-writer -->
# Starting requests

First [install the workflow](INSTALL.md) into the new project or an assigned
worktree of the existing project. Then use the matching prompt below.

Use these prompts in ordinary language. Local Markdown procedures and agent
methods do not automatically register host slash commands. Copy the appropriate
prompt into the project's task and replace its input fields. Write "not decided"
for unknowns; the agent should investigate and ask focused questions where your
intent is still needed. You do not need to select a technology stack in advance.

Project records belong in `.planning/`; reusable instructions and templates stay
in `.ai/`. Agents should read the complete relevant template, including its
examples and downstream consumer guidance, before authoring an artifact.

## Choose a starting point

1. Install the workflow and follow the installation guide's bootstrap instructions.
   Agent-written setup belongs in an assigned worktree; an initial installation
   in the primary checkout needs the human bootstrap commit described there.
2. For a new product, use **Start a new project**. For an existing product, use
   **Onboard an existing project**. The optional inspection prompt produces a
   report when you want to understand the work before authorizing setup.
3. Answer consequential questions as they arise. The agent should continue work
   that does not depend on those answers and preserve decisions already supplied.
4. Read the resulting project context, baseline and proposed next phase. Use
   **Define the first goal** or **Define several goals in order** to build the
   context for upcoming work. Use one of the implementation prompts below when
   you want to authorize building it.
   Setup alone does not authorize product implementation, publication or delivery.

Useful inputs include your intended users, the problem they face, one concrete
example of a successful outcome, important constraints, relevant document paths
and what you want the agent to finish in this task. Existing projects also benefit
from known failure reports, setup commands and areas that must remain compatible.
Provide references to existing information instead of transcribing the repository.
The [goal planning guide](GOAL-PLANNING.md) explains how these requests become
requirements, phase context, checked component plans and verified outcomes.

## Start a new project

Use this after installation when you are establishing a new product. This prompt
authorizes discovery, project records, workflow configuration and preparation of
the next useful phase. If you want application scaffolding built in the same task,
add that explicit outcome and its delivery boundary to the authorization field.

```text
Set up this project for useful engineering work around the product described below.

My inputs:
- Product name or working name: [name, or not decided]
- Problem and intended users: [who needs what, and why]
- Example of success: [a concrete user action and the result they should get]
- First useful outcome: [what would make an initial version worth using]
- Constraints and exclusions: [platform, compatibility, budget, timing, or boundaries]
- Existing assets and references: [repository paths, designs, notes, or none known]
- Decisions already made: [choices to preserve, or none yet]
- Authorization: discovery, setup records/configuration and next-phase preparation.
  Commit setup locally. Product implementation and publication are outside this task
  unless I explicitly add them here: [additional authorized scope, or none].

Work through the following sequence:

1. Read AGENTS.md, the shared rules, onboarding procedure and current planning
   records. Verify the absolute repository root, branch and assigned worktree before
   writes. Inspect what is already present, including any application skeleton,
   README, dependencies, tests, configuration and Git history. Preserve useful work.
   The installed workflow is tooling for my project, not the project's identity.

2. Establish the product context in my language. Clarify users, their main workflow,
   the first useful outcome, success criteria, exclusions and material constraints.
   Ask focused questions where my intent is needed; continue independent inspection
   and preparation while answers are pending. Do not turn illustrative requirements
   or default configuration into product decisions.

3. Investigate technical choices that affect the agreed outcome. Reuse sound choices
   already present. For undecided choices, explain the relevant alternatives,
   compatibility and consequences, and distinguish recommendations from decisions.
   Research only uncertainties that affect this setup or its next phase. Record
   unresolved decisions with the specific work they block.

4. Read the complete project, requirements, roadmap and state authoring templates.
   Create or complete .planning/PROJECT.md with the real purpose, users, core value,
   constraints and confirmed decisions. Record checkable desired outcomes in
   REQUIREMENTS.md and organize them into coherent phases in ROADMAP.md. Use the
   number and order justified by this product; never copy the sample phases,
   authentication features, dates or metrics. Keep STATE.md grounded in actual work.

5. Configure .planning/config.yaml for this host and project. Verify available
   executables and retain supported worker, documentor and verifier routes; inspect
   their invocation requirements and choose suitable capacity. Select meaningful
   project verification commands from the actual stack and available checks, and
   record observed results. Installing the workflow or checking that files exist
   does not prove product behavior. If the application has no runnable checks yet,
   report that gap and give the first implementation phase an explicit obligation
   to establish them; do not invent passing commands or claim execution readiness.
   Confirm publication settings only from the actual repository and my intent.

6. Prepare only the next useful phase using the local phase procedures. Give its
   CONTEXT an observable goal, exact acceptance, scope, confirmed decisions,
   unresolved questions and the authorization actually supplied. Where decisions
   are resolved, prepare bounded component instructions with real dependencies,
   ownership, meaningful checks and required documentation. Use independent
   preparation checking for substantial scope. Do not dispatch implementation
   workers merely because a plan exists.

7. Check that setup documents, links and configured commands agree with the actual
   repository. Commit the completed authorized setup with a descriptive message.
   Return the files and commit, the product understanding and decisions recorded,
   actual baseline checks/results, unresolved questions, and the next phase with
   its acceptance and remaining prerequisites. Clearly distinguish setup complete
   from ready to execute; do not claim that the product was implemented or shipped.
```

## Inspect an existing project before adoption

Choose this when you want an assessment without changing the project. It is an
alternative to authorizing onboarding immediately, not a required approval stage.

```text
Inspect this repository for workflow adoption. Keep this task read-only: do not
edit records, create worktrees, commit, start workers or publish.

My goal for the project is [desired next outcome, or assess current state first].
Important references and constraints are [paths and constraints, or inspect them].

Read existing instructions and relevant documentation, then trace the actual entry
points, important behavior, data boundaries and checks using the codebase-recon
method. Inspect Git status, planning records and any saved runtime state without
changing them. Treat shipped capabilities, proposed work and uncertain claims
separately. Identify concrete disagreements between documentation and code.

Return a concise project map with source evidence, existing records/guides to
preserve, available validation commands and whether they were actually run,
configuration gaps, unresolved product decisions and a bounded onboarding scope.
Do not infer a fresh project, reset existing progress or propose a broad rewrite
merely because the workflow has just been installed.
```

## Onboard an existing project

Use this for an established codebase, including one that already has its own
documentation and planning records. An earlier inspection can supply context,
but the agent still needs to check the current revision. This prompt authorizes
workflow adoption and evidence-based setup corrections; application changes need
their own stated scope.

```text
Onboard this existing project into the installed engineering workflow while
preserving its identity, behavior, documentation, decisions and history.

My inputs:
- Current project and users: [brief description, or discover from these references]
- Desired next outcome: [feature, repair, maintenance goal, or onboarding only]
- Authoritative references: [README, guides, specifications, decisions, issue links]
- Known setup/check commands and failures: [commands or reports, or inspect them]
- Compatibility and operational constraints: [interfaces, environments, data, users]
- Work or files to preserve: [uncommitted work, active branches, special constraints]
- Authorization: inspect, reconcile workflow setup, complete missing project
  records/configuration, prepare the next agreed scope and commit setup locally.
  Additional authorized changes or delivery actions: [explicit scope, or none].

Work through the following sequence:

1. Read the repository's AGENTS.md, shared rules and onboarding procedure. Verify
   the primary root, current branch, worktree layout and Git status. Reuse the
   assigned worktree or create the required immediate-child worktree before tracked
   writes. Preserve unrelated changes and incomplete work. Inspect existing
   PROJECT, REQUIREMENTS, ROADMAP, STATE, configuration, phase records and current
   specifications before deciding what needs to be added or changed.

2. Map enough of the real system to understand the next work: purpose, users,
   source entry points, major components, data flow, external dependencies,
   configuration, build/test paths and deployment boundaries. Use codebase-recon;
   for substantial code, have the coordinator assign a bounded codebase mapper
   and inspect its evidence. Read relevant guides and recent history. Trace
   important claims to source and tests rather than accepting headings or a
   previous summary as proof. Record useful maps only where they help future work.

3. Reconcile what the project does today with what I want next. Preserve established
   names, requirements, exclusions, decisions, phase identifiers and delivery
   history. Separate observed implementation, verified outcomes, desired changes
   and unresolved claims. Ask about missing intent or conflicting human decisions;
   do not ask again for authorization already supplied. Existing functionality is
   not automatically proof of deployment, user acceptance or business value.

4. Read the complete authoring templates before updating .planning/ records.
   Complete missing context and correct specific unsupported claims with evidence.
   Keep useful existing guides in their current locations and link to their fact
   owners. Do not replace a populated PROJECT, ROADMAP or STATE with blank setup
   records, restart phase numbering, turn transcripts into approved requirements,
   or invent historical decision rationale. If legacy records need migration,
   identify exact source/destination paths and preserve their information; do not
   silently create competing owners or perform an unrequested bulk reorganization.

5. Inspect .planning/config.yaml and the project's actual build, lint, type and
   behavior checks. Preserve working project configuration; change only what this
   adoption requires. Configure meaningful verification commands as argument lists,
   available worker/documentor/verifier routes, appropriate capacity and timeouts.
   Verify command availability and run the relevant baseline in the assigned
   environment. Report exact commands, results, existing failures, unavailable
   dependencies and unexercised boundaries. A failing baseline is not permission
   to weaken checks or silently expand this task into application repairs. Keep
   missing checks explicit; source-workflow tests are not this project's test suite.
   Verify remote/base/check settings against the repository if publication is needed.

6. Reconcile current phase/runtime status with observed Git and process evidence.
   Do not restart an interrupted worker or mark old work complete from STATE alone.
   Record desired next outcomes in REQUIREMENTS and ROADMAP without erasing existing
   progress. Prepare the next agreed phase's CONTEXT and, where decisions allow,
   bounded instructions with acceptance, ownership, dependencies, validation and
   documentation coverage. Use independent preparation checking for substantial
   scope. If I requested onboarding only, report the recommended next action
   without inventing feature work or launching implementation.

7. Verify the adoption changes and commit completed setup with a descriptive
   message. Return the project understanding and source references, records and
   guides preserved/updated, configuration changes, baseline results, known defects
   and unresolved questions, plus the exact next action and its prerequisites.
   State what is ready and what remains blocked. Keep product implementation,
   publication, merge and cleanup within the authorization I actually provided.
```

## Define project direction without implementation

> Help define desired outcomes and group them into coherent phases. Use the full
> project, requirements, roadmap and relevant phase specification/context
> templates. Record agreed direction in `.planning/`, with falsifiable acceptance,
> boundaries, dependencies and unresolved decisions. Detail the next useful phase.
> Do not begin implementation yet.

## Define the first goal

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

## Define several goals in order

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

To proceed after either planning prompt, use **Implement and open a verified PR**
with the actual selected phase and acceptance, or the delivery prompt when you
want merge and cleanup as well. If you authorize an ordered series for execution,
state which goals are included and its delivery boundary; the agent should carry
valid context forward, verify each result and reassess the next phase against
the resulting code instead of replaying stale future plans.

## Prepare a feature for parallel work

> Discuss and research the selected phase, then use the complete phase-prompt
> template to create `NN-CC-PLAN.md` assignments. Include concrete task actions,
> source inputs, interfaces, real dependencies, exact ownership, exclusive
> resources, meaningful verification, completion conditions and documentation.
> Apply the Python runtime's additive template contract. Arrange an independent
> preparation checker, correct findings within scope and report readiness and
> unresolved decisions before implementation.

## Implement and open a verified PR

> Implement the authorized phase in its assigned worktree. Start fresh bounded
> coder and documentor agents for independent plans, integrate and check their
> committed results, keep required docs attached to the phase, and obtain
> independent outcome verification. Fix actionable findings, complete required
> acceptance observations, commit and push a PR, and observe required remote
> checks. Do not merge; report when the final revision is ready.

## Show progress continuously and finish delivery

> Complete this scope in an assigned worktree with fresh bounded workers for
> independent components. Commit after each meaningful slice and push frequent
> updates to a draft PR so I can review progress. Preserve the full template
> guidance and record consequential deviations in phase context. Once the scope
> and documentation are complete, independently review the integrated result,
> fix findings and verify the final revision and required checks. Merge through
> the normal repository process, confirm the merge, safely synchronize the
> primary checkout, and remove only this work's identified clean merged worktrees
> and branches. Preserve unrelated, incomplete, dirty and ignored data.

Draft progress pushes and final verified publication are different steps.
The runtime's `publish --draft` still requires verification; the coordinator
handles authorized earlier draft snapshots through the forge workflow. The
runtime never merges; the coordinator performs an authorized final merge.

## Merge an already authorized PR and clean up

> Finish the remaining authorized changes and documentation in the existing
> assigned worktree. Review and fix actionable findings, commit and push the
> existing PR, and verify the final revision and required checks. Merge through
> the normal repository process. Confirm the merge, safely fast-forward the
> primary checkout and remove only this work's clean merged worktrees and
> branches. Preserve unrelated or incomplete work and report the final result.

## Repair a defect

> Investigate this failure with the hypothesis-debugging skill. Preserve a
> representative reproduction, prepare a bounded phase plan for the authorized
> repair, and use regression-design for checks that reject plausible wrong fixes.
> Implement the correction, reconcile affected current specifications and guides,
> independently verify the outcome and commit the result in an assigned worktree.
> Report actual evidence and remaining limitations.

## Resume interrupted work

> Inspect the selected phase's saved records, runtime attempts, supervisor/worker
> processes, checkouts, commits and summaries. Reconcile any interruption before
> restarting work. Reuse valid committed output where possible and preserve dirty
> or incomplete results. Continue previously authorized work with the original
> acceptance; record and explicitly replan any required input changes.

## Report status without continuing

> Report the selected phase's current readiness, running work, integrated results,
> blockers, verification and publication state. Inspect current PR checks when
> relevant, name the revision covered by evidence and identify the next action.
> Keep this read-only; do not start workers, update records or publish.

The [workflow guide](PHASE-WORKFLOW.md), [template guide](TEMPLATE-GUIDE.md),
[feature inventory](WORKFLOW-FEATURES.md) and
[command catalog](../.ai/commands/README.md) explain the exact boundaries.
Name a relevant [repository skill](AGENT-SKILLS.md) when its method matters; the
request still determines scope and authority.
