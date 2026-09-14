# Starting requests

First [install the workflow](INSTALL.md) into the new project or an assigned
worktree of the existing project. Then use the matching prompt below.

Use these prompts in ordinary language. Local Markdown procedures and agent
methods do not automatically register host slash commands. Adapt the
project details and delivery boundary to the work you intend to authorize.

Project records belong in `.planning/`; reusable instructions and templates stay
in `.ai/`. Agents should read the complete relevant template, including its
examples and downstream consumer guidance, before authoring an artifact.

## Start a new project

> Use this template to establish the project described in my request. Read the
> complete project, requirements and roadmap templates. Record the real purpose,
> users, success and boundaries in `.planning/PROJECT.md`, desired outcomes in
> REQUIREMENTS, and coherent phase goals/dependencies in ROADMAP. Configure actual
> worker routes and verification commands in `.planning/config.yaml`, inspect
> their baseline, and prepare the next useful phase in an assigned worktree.
> Identify consequential decisions that are still missing. Do not invent product
> requirements or start implementation unless I have authorized it.

## Inspect an existing project before adoption

> Inspect this repository and its existing documentation using the onboarding
> procedure and codebase-recon skill. Report what is implemented, how it is
> checked, which claims conflict and what setup is missing before adoption. Keep
> this read-only; distinguish observed behavior from proposed improvements.

## Adopt the workflow into an existing project

> Adopt the workflow in an assigned immediate-child worktree under the primary
> checkout's `.worktrees/`. Inspect source and useful existing guides first.
> Establish `.planning/` project records from my stated intent and the complete
> templates, configure real checks and worker routes, and preserve useful
> documentation. Reconcile claims with implementation evidence. Identify missing
> consequential decisions, commit setup in reviewable slices, and report readiness.

## Define project direction without implementation

> Help define desired outcomes and group them into coherent phases. Use the full
> project, requirements, roadmap and relevant phase specification/context
> templates. Record agreed direction in `.planning/`, with falsifiable acceptance,
> boundaries, dependencies and unresolved decisions. Detail the next useful phase.
> Do not begin implementation yet.

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
