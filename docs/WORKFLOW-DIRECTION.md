# Proposed workflow direction

**Status: proposed next-stage design.** This captures the user's requested
direction for three ways to start work. It does not describe three newly
implemented commands or dispatch engines. Current executable behavior remains
in the [runtime guide](../.ai/runtime/README.md).

## The user's proposal

- Provide entry workflows for **feature changes**, **bug fixes** and **small
  changes**.
- Start from the request, investigate the relevant project context, resolve
  questions, and derive useful phase goals before implementation planning.
- Consider grouping a larger feature into multiple phases, possibly using a
  feature or milestone record to explain their shared outcome.
- Build our own workflow and terminology while retaining the complete teaching
  content and useful methods in the template library.

The tables below develop that direction as a proposal. Workflow names, grouping
records and detailed routing rules remain open for the next implementation stage.

## Three entry paths, shared execution machinery

| Entry path | Typical request | First investigation | Planning result | Scope adjustment |
|---|---|---|---|---|
| Feature change | Add a capability or change a substantial existing behavior | Trace current behavior, users, interfaces and technical uncertainties; discuss consequential choices | One coherent phase or an ordered group of phase goals, then detailed plans for the next useful phase | Split when outcomes, dependencies or verification need separate phases |
| Bug fix | A behavior fails, regresses or differs from its valid contract | Reproduce the failure, establish expected behavior, compare hypotheses and isolate the cause | A bounded repair phase with regression evidence and affected documentation | Expand deliberately if evidence reveals a shared architectural cause |
| Small change | A precise, limited adjustment with a known outcome | Inspect the affected source and relevant contract; check that scope is actually small | One bounded phase/plan using the applicable complete artifact structure | Route into feature discovery or diagnosis if uncertainty or impact grows |

These paths should differ in the questions and investigation they need. They
should share the same ownership, dependency scheduler, worktree isolation,
committed results, documentation coverage, verification, recovery and delivery
rules. Three entry paths do not require three competing execution systems.

## Proposed request-to-phase flow

| Step | Action | Durable result | When it is complete |
|---|---|---|---|
| Understand the request | Identify the desired outcome, affected users and authorization boundary | Relevant project/phase context | The request can be stated without inventing scope |
| Inspect existing reality | Read relevant source, current specifications, tests, configuration and useful history | Findings or codebase references | The current baseline and affected interfaces are understood |
| Research and resolve questions | Investigate material technical uncertainty; obtain missing consequential product decisions | Bounded findings and recorded decisions | Dependent planning no longer hides a missing decision as an assumption |
| Define phase goals | Connect outcomes to falsifiable acceptance, boundaries and genuine prerequisites | Roadmap goals and phase context/specification as applicable | Each selected phase has a coherent observable outcome |
| Prepare the next phase | Write concrete tasks, ownership, dependencies, resources, checks and documentation | Full PLAN artifacts; independent preparation findings | A fresh worker has sufficient instructions and substantial preparation has been checked |
| Execute and verify | Run ready bounded workers, integrate checked results, assess the full outcome and close gaps | Commits, summaries, verification and required UAT | Current evidence supports acceptance and required documentation |
| Finish the delivery boundary | Publish progress/final results and perform authorized merge/cleanup | PR and observed delivery evidence | The user's actual requested boundary is reached |

“Research first” should mean evidence before commitments. It should not force an
external research report for a one-line correction whose behavior is already
clear. A short source inspection can resolve a small change; an uncertain bug
may need controlled experiments; a feature may need both product questions and
technical research. Record only the investigation artifacts that serve the work.

Questions should block their dependent choices. Independent, decided work can
continue. Preserve authorization already supplied rather than asking again at
every internal transition.

## Possible grouping for a larger feature

| Concept | Would explain | Proposed relationship |
|---|---|---|
| Feature or milestone group | The user-visible outcome spanning multiple phases | Links related phase goals and their completion criteria |
| Phase | A coherent outcome that can be implemented and verified together | Keeps context, detailed plans, results and verification attached |
| Component plan | One bounded worker assignment within a phase | Declares actual prerequisite components, owned paths, checks and handoffs |

A group should add a useful overview without duplicating phase status or moving
phase folders to indicate progress. Milestone templates are not retained in the
current catalog. Choosing a group structure, name and canonical storage location
requires an explicit next-stage design decision; no new group directory or
runtime registry is introduced by this document.

## Current support and work still to build

| Area | Available now | Proposed next-stage work |
|---|---|---|
| Request handling | Coordinator-led onboarding and phase procedures | Clear selection between feature, bug and small-change entry workflows |
| Investigation | Coordinator-assigned mapping, research, debugging and verification roles | Tailored question/research sequences and escalation rules for each entry path |
| Phase design | Roadmap, context/specification templates and decomposition method | Consistent handoff from request investigation to phase goals; optional feature grouping |
| Detailed preparation | Full plan template, local runtime contract and independent checker role | Explicit workflow orchestration and revision loop for each entry path |
| Parallel implementation | Runtime readiness, ownership/resource scheduling and checked integration | Reuse this machinery; change only where the new workflows demonstrate a concrete need |
| Outcome assurance | Documentation obligations, independent verification, UAT and recovery | Exercise the complete new entry flows with representative real assignments |

## Choices to settle before implementation

- **Names and entry points:** ordinary-language routing, named procedures or host
  commands; avoid claiming command registration until it exists.
- **Feature grouping:** whether a feature record, milestone record or roadmap
  grouping provides enough value to justify another artifact.
- **Small-change boundary:** observable criteria for staying small and triggers
  for returning to discussion or diagnosis.
- **Research handoff:** what a preparer must receive, how unanswered decisions
  remain visible, and when a separate research record helps.
- **Correction loop:** who checks preparation, how findings return to the author,
  and what demonstrates that an inadequate plan has been corrected.
- **Validation:** representative feature, bug and small-change requests, including
  an interruption and a scope escalation, to test the complete user experience.

## How to evaluate the next stage

| Demonstration | Useful evidence |
|---|---|
| Feature request with an unresolved decision | Relevant investigation, resolved or explicitly blocking decision, coherent phase goals and executable preparation |
| Reproducible bug | Evidence distinguishing causes, a bounded correction and a regression check that fails before the repair |
| Precise small change | Proportionate investigation and documentation with no unnecessary discovery loop |
| Work that expands during investigation | Explicit transition to the appropriate path while preserving the original request and decisions |
| Parallel implementation | Independent components overlap in execution; true prerequisites and shared resources remain protected |
| Interrupted work | Resumption uses durable decisions and valid committed results without blind replay |

Do not mark the next stage complete merely because three workflow files exist.
The intended result is a dependable path from the user's request to verified
delivery, demonstrated with actual assignments and their evidence.
