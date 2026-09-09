# Rules of engagement

## Report first: a hard requirement

For every new problem, bug, drift item or change request:

1. Inspect read-only and capture a report in `plans/intake` using `templates/intake.md`.
2. Draft a plan only when requested; use `templates/plan.md` and keep its scope small.
3. Return `templates/decision-summary.md`, naming the exact next action and its limits.
4. Wait for the user's yes, no, or requested alterations. A no stops the action;
   alterations require a revised report and another summary.

Before approval, only read-only inspection and report/plan drafting are allowed.
Do not implement, install dependencies, run validation, dispatch agents, create
worktrees, commit, push or merge. A yes approves only the action named in the summary.
Approval to draft or accept a plan is not approval to implement it. Approval to push
is not approval to merge. New scope needs a new decision.

An explicit user instruction that directly names the action, scope and destination
is authority for that exact action; do not ask for the same approval again. The
current instruction to create this isolated scaffold and push its branch is such an
authorization. It grants no merge or future implementation authority.

## One owner per fact

Follow `truth-map.md`. Put a fact in its owner and link to it elsewhere. Specs describe
what exists in the checked-out revision; intent describes what is wanted. Plans hold
proposed work, decisions hold rationale, and STATE holds current coordination.
Paths and ID formats belong only to `config.yaml`. Never invent evidence.

## Mutability tiers

| Tier | Records | Change rule |
| --- | --- | --- |
| Working | Intake, draft plans, intent, STATE, proposed decisions | Update within approved scope; preserve material decisions in the journal. |
| Maintained | Current specs, accepted plan execution notes | Keep accurate as approved work changes; amend a contract before changing its meaning. |
| Contract | RULES, truth-map, config, agent and workflow contracts, accepted ADRs | Propose an AMD and obtain user approval before changing an accepted obligation. |
| Historical | Journal entries, accepted AMDs, retired ADRs, done/abandoned plans | Do not rewrite; append a correction or a new linked record. |

Templates follow the contract tier when an edit changes required fields or meaning.
Typo/link corrections that do not alter meaning can be recorded as corrections under
an approved documentation action. This initial scaffold is a draft baseline; its
contract proposals remain subject to user review.

## Amendment protocol

Create an AMD from `templates/amendment.md`. Link the owning contract and its ADR if
there is one; state the old obligation, proposed obligation, reason and impact.
Present a decision summary and wait. Once approved, update the maintained contract,
accept the AMD and append a journal entry in the same change. Preserve an accepted
ADR's original reasoning: record a new superseding ADR and move the old file to
`decisions/retired`, repairing links without changing its body. Rejected proposals
remain records of rejection; they never change the contract.

## Records and plan lifecycle

Use the filename and ID rules in config. Allocate the next unused ID across all
folders of its kind, including retired/abandoned records. Keep IDs and slugs stable;
never reuse an ID. YAML metadata must agree with the filename and lifecycle folder.
Fill each template section; use `Unknown` or `Not applicable` with a reason when needed.

Intake captures unplanned work. Plans move through backlog, active, review and done.
Blocked plans record the obstacle, owner, previous phase and resume condition.
Abandoned plans record why work stopped. See `plans/README.md` for transitions.
A plan's checklist is sufficient for small tasks; do not add another tracking system.

## Execution, evidence and delivery

After explicit execution approval, use the fixed assigned worktree and the relevant
command document. Make only the approved changes. Run the agreed validation at the
end, report actual results and limits, then seek any still-required delivery decision.
No check is PASS unless it ran and passed. Review is tied to the reviewed revision.

Update the affected SPEC files in every feature/fix PR before review; record current
behavior and limitations, not aspirations. The same merge updates implementation
and specs. For a documentation-only PR, describe the documentation change in the
relevant current spec. Git is the owner of commit and merge identities.

Every commit must have a nonempty descriptive message. Push only the approved branch;
never force-push or merge without authority. After an authorized and verified merge,
synchronize the target, confirm the worktree is clean and its tip has no unmerged work,
then retire that exact worktree and local branch. Do not delete unrelated branches.
This draft is push-only: retain its branch and worktree for review.

Append dated journal entries; do not edit earlier entries. Corrections are new entries
that reference the earlier timestamp. Keep STATE concise and point to durable records.
