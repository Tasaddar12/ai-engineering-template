# Starting requests

These prompts invoke the documented procedures in ordinary language. Markdown
command files are not automatically installed slash commands. Adapt the request
to the project's actual intent and authorization.

## Start a new project

> Use this template to establish the project described in my request. Record the
> purpose, users, success and boundaries in PROJECT; desired outcomes in
> REQUIREMENTS; and coherent phase goals and dependencies in ROADMAP. Configure
> real worker routes and checks, then prepare the next phase in an assigned
> worktree. Identify consequential decisions that are still missing. Do not
> invent product requirements or start implementation unless I have authorized it.

## Inspect before adoption

> Inspect this repository and our existing documentation. Use the onboarding
> procedure to report what is implemented, how it is checked, and what is missing
> before we adopt the phase workflow. Keep this read-only.

## Adopt the workflow

> Set up this repository for the phase workflow in an assigned worktree. Inspect
> the code first. Record the intent and constraints I have already supplied,
> configure actual verification commands, and identify any consequential decisions
> you still need from me. Preserve useful existing guides and do not invent project
> requirements or historical decisions. Commit the authorized setup.

## Define project direction

> Help define the project's desired outcomes and break them into coherent phases.
> Record the agreed purpose and boundaries in PROJECT, desired outcomes in
> REQUIREMENTS, and phase order/dependencies in ROADMAP. Detail the next phase's
> context and acceptance. Do not begin implementation yet.

## Prepare a feature

> Discuss and research the selected phase, then prepare bounded component
> instructions with ownership, interfaces, dependencies, acceptance and required
> documentation. Have the preparation independently checked. Report readiness
> and unresolved decisions before implementation.

## Implement and open a PR

> Implement the approved phase in an assigned worktree. Start fresh coder agents
> for independent components, integrate and check their results, update required
> documentation, obtain independent verification, and fix actionable findings.
> Commit and push a pull request. Do not merge; tell me when it is ready.

## Merge an approved PR and clean up

> Finish the authorized changes and documentation in the existing assigned
> worktree, review and fix actionable findings, commit and push the existing PR.
> Verify its final revision and required checks, then merge it through the normal
> repository process. Confirm the merge, fast-forward the primary checkout and
> remove only this work's clean merged worktrees and branches. Preserve unrelated
> or incomplete work and report the final outcome.

## Repair a small defect

> Investigate this failure and use a small phase to repair the confirmed defect.
> Preserve reproduction evidence, implement the bounded correction, run its
> regression checks and verify affected documentation. Commit the result in an
> assigned worktree and report the outcome.

## Resume or report

> Inspect the selected phase's saved state, processes, commits and summaries.
> Resume the previously authorized work after reconciling any interruption.
> Preserve incomplete work and the original acceptance.

For a report without continuation, ask for phase status instead. The
[command catalog](../.ai/commands/README.md) and
[workflow guide](PHASE-WORKFLOW.md) describe the exact boundaries.
