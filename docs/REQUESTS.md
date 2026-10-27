# Requests for prepared work

Use these ordinary-language prompts after [onboarding](../commands/onboard.md), or to continue an existing phase. Name the real phase when one exists, the outcome you want, relevant source context and the delivery boundary. Shared defaults include committing each completed meaningful slice and opening or updating a draft PR on the first authorized push; state a different limit when you want one. Existing decisions and authorization persist for their covered scope. The examples below are instructional prompts, not project facts or permission to exceed the stated boundary.

## Discuss an existing phase

> Let's discuss phase 01.

Route this directly to [discuss-phase](../commands/discuss-phase.md). Resolve the selected phase from the roadmap, load its records and referenced source, then follow the workflow's adaptive questioning and discussion-log order. The user does not need to supply a slash command or file inventory. Record actual choices and unresolved decisions in the owning records.

**This request does not authorize implementation.** Discussion can clarify decisions within the roadmap boundary and can identify deferred ideas; it cannot expand the phase by assumption.

## Add work to the roadmap

> Add a phase for API key session hardening. We want sessions issued and managed through an IDP rather than static keys. Keep the existing API behavior compatible during the migration, and put it after the account migration work.

Route this to [phase](../commands/phase.md). Confirm the requested goal, dependencies and requirement relationships, and use runtime-owned phase operations so numbering, directory and roadmap stay aligned. The runtime allocates the next number. For urgent work that must land between two existing phases, request insertion after a named phase so existing phases are not renumbered. A phase-add or edit request updates scope; it does not authorize implementation.

## Plan a phase for execution

> Research and plan the selected phase. Produce complete `NN-CC-PLAN.md` assignments with concrete task actions, the exact files each task must read first and own, real dependencies and resources, observable acceptance criteria, required documentation, and verification commands that state the failure each command should catch. Arrange an independent goal-backward plan check, correct findings within scope, and report readiness and unresolved decisions. Do not implement the phase.

Route to [plan-phase](../commands/plan-phase.md). Use the selected phase's approved scope and decisions, and complete the full plan templates. The independent check asks whether the plans together achieve the phase goal. Report genuine unresolved decisions rather than silently assuming a choice. Planning readiness never grants implementation permission.

## Implement and leave a verified PR open (explicit no-merge boundary)

> Implement phase 01 within its approved scope. Dispatch fresh isolated executors for independent plans, integrate their committed results, preserve required documentation and complete summaries, and obtain independent outcome verification. Fix actionable in-scope findings, commit each meaningful slice and push an updated draft PR so I can review progress. Observe the required remote checks and report the final revision and evidence. Do not merge.

Route to [execute-phase](../commands/execute-phase.md), then [verify-work](../commands/verify-work.md), then [ship](../commands/ship.md) with the explicit no-merge boundary. The quoted implementation instruction authorizes only the named phase and scope. Execution does not authorize a different phase. Publication and merge are distinct: the draft can be updated while work proceeds, but readiness requires current passed verification and required provider gates. The PR remains open because this request explicitly says not to merge.

## Show progress and continue authorized work

> Complete the authorized scope in phase 01 with fresh agents for independent plans. Commit after each meaningful slice and push frequent updates to the draft PR so I can review the progress. Preserve the full template guidance and record consequential deviations in the phase context. Once the scope and documentation are complete, review the integrated result, fix findings, verify the final revision and required checks, then publish the verified result. Do not merge unless I explicitly ask.

Use the active execute/verify/ship workflow and its existing authority. A follow-up status question steers the active work; it does not automatically cancel it. Keep the draft current on each authorized push. Verification is tied to its captured revision, and publication or merge must obey the current provider gates and explicit merge instruction.

## Repair a defect

> Investigate this failure in the selected phase. Preserve a representative reproduction and trace the cause before choosing the smallest appropriate route. If it is one bounded outcome, use a quick task; if it needs phase decisions or several coordinated tasks, propose or insert a phase for the repair. Add checks that reject plausible wrong fixes. Implement only the authorized repair, reconcile affected specifications and guides, independently verify the outcome, commit the result, and report actual evidence and remaining limitations.

Route a small, single-outcome change to [quick](../commands/quick.md). A phase-sized repair belongs in the roadmap and requires its own scope and implementation authority. Preserve the observed failure and competing hypotheses. Do not label a guess as a reproduction, add unrelated capabilities or close the defect from source presence alone. If the requested scope authorizes the repair, proceed through the applicable workflow without requesting the same authorization again.

## Capture an idea without acting on it

> Note that we should rotate service account keys quarterly. Don't work on it now; capture it with the account area and the reason that rotation reduces exposure if a credential leaks.

Route to [capture](../commands/capture.md). Capture records the stated context and returns to the active work; it does not implement or prioritize the item. Pending items can be reviewed with `/capture --list [area]` and matched against a phase during discussion. A match does not automatically mean the item should be folded in.

## Resume interrupted work

> Inspect phase 01's saved records, plans, summaries and commits. Reconcile the interruption before restarting. Reuse valid committed output, preserve incomplete results, and continue previously authorized work with the original acceptance. If the actual inputs changed, identify the affected plans and evidence, then replan only what is necessary. Report dirty paths, worker/process state, missing evidence and the first bounded action.

`/next` and `/progress` detect unfinished execution, but use the exact owning workflow to resume it. Confirm worker stop before touching its paths or assigning overlapping work; a wait timeout is not proof that a worker exited. Preserve base/head and committed work. A continuation does not create new implementation authority or discard pending user decisions.

## Report status without continuing

> Report phase 01's current readiness, integrated results, blockers, verification and publication state. Inspect the current PR checks when relevant, name the exact revision covered by each item of evidence, and identify the single next action. Keep this read-only: do not start agents, update records, repair findings, push or publish.

Route to [progress](../commands/progress.md). Report only observed state: not run, not configured, failed and unverifiable are distinct. A file, summary, PR or roadmap checkmark alone does not prove acceptance. The recommended next action is a report, not permission to start it.

## Requests that change the delivery boundary

> Investigate and prepare the complete change, but do not run tests, checks, compilation, lint, probes or installs until I ask. You may read source and Git history, edit only the assigned documentation paths, and commit those changes.

State ordering and limits in the request itself. Follow them while preserving independent work. A request to defer checks leaves required evidence pending; it does not allow a report to imply the check passed. A report-only request is read-only, even if the normal workflow would continue to another stage.

---

The [phase workflow](PHASE-WORKFLOW.md), [artifact guide](ARTIFACT-GUIDE.md), [feature inventory](WORKFLOW-FEATURES.md) and [command catalog](../commands/COMMAND.md) explain the exact boundaries. The request determines the authorized scope and delivery limits. Examples and phase numbers on this page are instructional only; onboarding supplies the adopting project's actual identity and plan.
