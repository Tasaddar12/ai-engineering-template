# Onboard

Read [RULES](../RULES.md). Inspect first; write in an
[assigned worktree](worktree.md) only when adoption or changes are authorized.

## How to use this command

Use this procedure to establish a new project's context or adopt the workflow in
an existing project. The detailed prompts below authorize inspection, setup and
preparation; replace their input fields with your information. Write "not decided"
for unknowns. Existing instructions and useful project records remain authoritative.

If the workflow is not installed, follow [install](install.md) first. Agent-written
setup uses an assigned worktree. An initial installation in the primary checkout
needs the human bootstrap commit described in that command.

1. Use **Start a new project** for a new product, or **Onboard an existing project**
   for an established codebase. The optional inspection prompt produces a read-only
   assessment when that is all you want; it is not a required approval stage.
2. Describe intended users, their problem, an example of success, constraints,
   relevant reference paths and the work authorized for this task.
3. Resolve consequential questions while independent inspection and preparation
   continue. Preserve decisions and authorization already supplied.
4. Review the resulting project context, observed baseline and remaining decisions.
   Continue with [goal-plan](goal-plan.md) to define the first goal or several
   ordered goals, or [phase-prepare](phase-prepare.md) for an existing decided phase.

These are ordinary-language requests. Markdown commands describe local procedures;
they do not automatically register host slash commands. Setup alone does not
authorize product implementation, publication or delivery.

## Procedure for a new or existing project

1. Inspect the source layout, languages, entry points, tests, configuration,
   recent history and existing guides. For substantial existing code, assign a
   [codebase mapper](../agents/codebase-mapper.md) a bounded focus and read its
   evidence before choosing follow-up research or documentation work. Do not
   invent a product from this template.
2. Preserve existing PROJECT context and complete missing purpose, success,
   boundaries and confirmed decisions from the user and source evidence. Resolve
   missing intent; record existing explicit authorization without asking again.
3. Configure actual required checks and available worker commands in config.yaml.
   Run the checks and report their real baseline. Missing routes/checks are
   configuration gaps, not permission to claim readiness.
4. Inventory existing documents and compare relevant claims to code. Preserve
   useful guides. Propose specific retirement/move actions only where needed,
   within the user's authorized scope. Do not bulk-convert transcripts into
   requirements or invent historical ADR rationale.
5. Preserve existing requirement IDs, phases and delivery history. Record agreed
   desired outcomes in REQUIREMENTS and order coherent capabilities as
   phases in ROADMAP. Detail only the next useful scope. Known defects, unknown
   failures and documentation corrections use the same phase process.
6. Use phase CONTEXT for incoming information, exact acceptance, choices and
   unresolved questions. Create codebase maps only where they save later work.
   Draft current SPECs only from inspected implementation evidence.
7. Confirm AGENTS points to the active rules, commands and roles. Check setup
   records and configured commands against the actual repository. Commit authorized
   setup, then report what is ready and what still needs a decision or setup.

## Returning session

Read PROJECT, STATE, ROADMAP and the selected phase's context/evidence. Run
[phase-status](phase-status.md), inspect relevant code and continue the user's
authorized work. Do not restructure the project merely because onboarding was
invoked. Report drift with evidence in its affected phase.

## Complete authoring sources

Use the full [project](../templates/project.md), [requirements](../templates/requirements.md),
[roadmap](../templates/roadmap.md) and [state](../templates/state.md) templates when
onboarding. Read their examples and update rules before creating real records in
`.planning/`. Existing-project mapping uses the complete [codebase templates](../templates/codebase/).
Preserve existing project guidance and migrate old data explicitly; do not maintain
both `.ai/PROJECT.md` and `.planning/PROJECT.md` as competing owners.

The [codebase mapper](../agents/codebase-mapper.md) supplies the full mapping
method. Route technical unknowns to [research](phase-research.md) and unsupported
documentation claims through [documentation coverage](../references/documentation.md).
Apply [agent adaptation](../references/agent-adaptation.md) for host capabilities,
worktree placement and handoff boundaries.

## Copy-ready onboarding prompts

### Start a new project

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

### Inspect an existing project before adoption

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

### Onboard an existing project

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
