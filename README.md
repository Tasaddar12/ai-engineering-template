# AI engineering contracts

This repository is a Markdown/YAML scaffold for running approved engineering
work with clear roles, current contracts and evidence of what actually works.
Start at [AGENTS.md](AGENTS.md).

It addresses a common trap: an agent meets a document that contradicts the
work in front of it, then either refuses, bends the implementation to satisfy
stale prose, or changes the code and leaves the document behind. The operating
rules give the agent a supported correction route inside approved work.

## Why the structure matters

| Failure | Design response |
| --- | --- |
| A role has no usable write scope | Name what it may read and write. |
| A prohibition has no correction route | Use tiers and evidenced amendments. |
| Tool restrictions are mistaken for intent | Disclose actual enforcement limits. |
| Several documents repeat one requirement | Give the fact one owner and link it. |
| Specs dictate incidental implementation | Specify observable behavior. |
| Specs mix history, wishes and current truth | Separate plans, contracts and logs. |
| Done means a completed checklist | Require observed behavior and proof. |

The [Rules](.ai/RULES.md) explains how to establish which
side of a contradiction is wrong. A bug in code does not make its requirement
wrong. A tested result is evidence to inspect, not permission to redefine
what the user wanted.

## What lives where

| Need | Read or write |
| --- | --- |
| Purpose and human boundaries | [PROJECT](.ai/state/PROJECT.md) |
| Engagement and authority | [RULES](.ai/RULES.md) |
| Current correct behavior | [SPEC template](.ai/templates/SPEC.md) |
| Why an approach was chosen | [Decisions](.ai/decisions) |
| Why a contract changed | [Amendment template](.ai/templates/AMENDMENT.md) |
| Uncertainty and waiting questions | [Intake](.ai/plans/intake) |
| Proposed changes and dependencies | [Plans](.ai/plans/README.md) |
| Confirmed defects and regression proof | [FIX](.ai/commands/fix.md) |
| Current coordination and historical events | [State](.ai/state/STATE.md) |
| Sources and inspected evidence | [Research](.ai/research/README.md) |

[Truth map](.ai/truth-map.md) is the ownership index.
[Config](.ai/config.yaml) owns the actual paths and ID formats.

## Work one change at a time

A plan explains the desired outcome and the exact contract wording that will
land with it. Its route can change as evidence improves. Proposed behavior
stays in the plan until implementation makes it true in a current SPEC.

A fix restores an existing contract. Its useful artifact is a symptom, a
cause, a bounded change and a guard that fails before and passes after.
The [fix command](.ai/commands/fix.md) keeps behavior changes from slipping
through as small repairs.

The [commands](.ai/commands/README.md) cover initialization, reporting,
planning, implementation, blocking, review, verification and closure.
They are Markdown entry points whose linked commands own the steps.
You can provide the selected file to an agent in the assigned repository;
there is no installation or registered slash-command runtime here.

## Roles with useful boundaries

The [agent index](.ai/agents/README.md) covers coordination, research,
planning, plan checking, implementation, documentation, independent review
and defect triage.

Each role says what it may write and where its authority ends. The worker
doing approved implementation can correct a stale contract with an amendment;
the independent reviewer reports defects without editing its own answer.
Cold review keeps research and previous discussion out of the review packet
so the reviewer can challenge the premise. Any reduced isolation is reported.

## Several changes at once

[Parallel execution](.ai/commands/orchestrate.md) distinguishes
dependency waves from tracks sharing files or contracts. A track runs its
colliding plans sequentially in one worktree; independent tracks can proceed
together only after their prerequisites land.

A run board reserves IDs before branching and assigns shared state to one
writer. Each track keeps durable review and terminal evidence. Review rounds
are bounded; a stopped track does not erase independent progress.
[Cleanup](.ai/commands/orchestrate-clean.md) uses actual merge, ancestry,
cleanliness and ownership evidence before removing an exact worktree/branch.

These procedures describe coordination; they do not dispatch processes.
Runtime-specific launch and confinement must be chosen for the consuming
project. Prompt wording does not enforce a filesystem boundary.

## Adopt it into an existing project

Inspect existing instructions and fact owners before copying or changing
anything. Keep useful project knowledge, reconcile contradictions, and write
specs only for behavior you can establish now. Do not invent project intent.

Use [onboard](.ai/commands/onboard.md) for that reconciliation.
Use [harvest](.ai/commands/harvest.md) for discussion notes: what was said,
decided and built are different facts. A decision that has no implementation
belongs in a plan, not a claim of current behavior.

## Review and delivery

The [agent entry point](AGENTS.md) preserves the user's report,
summary and decision boundary. An exact instruction already
authorizes its stated action; ordinary steps inside it need no repeated ask.

[Verification](.ai/agents/verifier.md) checks current behavior,
invariants and the plan's promised contract changes. Missing required evidence
cannot become PASS. [Delivery](.ai/commands/onboard-pr.md) distinguishes an
authorized draft push from acceptance, PR creation, merge and cleanup.

The scaffold is documentation and configuration. It has no application,
dependency installer, executable dispatcher, automatic hooks or CI service.
