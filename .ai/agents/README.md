---
tier: contract
authority: agent
title: Agent roles
---

# Agent roles

These role prompts define responsibilities, allowed writes, steps and report
formats. `tools` and optional model fields are descriptive; a host must map them
to actual capabilities. The role body narrows broad tool access. The main
session is the coordinator; the orchestrator role designs schedules, while
orchestrate and orchestrate-track are the two coordinating command procedures.

| Name | Purpose |
| --- | --- |
| [bug-reviewer](bug-reviewer.md) | Triages evidence into confirmed defects, unanswered questions or contract changes without repairing them. |
| [decoupler](decoupler.md) | Separates dependency from contention and proposes bounded tasks with clear interfaces and ownership. |
| [e2e](e2e.md) | Checks agreed user journeys across system boundaries and records observable end-to-end outcomes. |
| [implementor](implementor.md) | Builds what an active plan describes. Use when a plan in .ai/plans/active/ is ready to implement. Has authority to amend specs it finds to be wrong — this is the agent that does the actual work. |
| [orchestrator](orchestrator.md) | Works out which plans can be built at the same time and which have to wait. Produces the wave and track plan for an /orchestrate run. Read-only over the codebase — it schedules work, it never does it. |
| [plan-checker](plan-checker.md) | Reviews a plan for internal consistency and conflicts with specs, intent, and the existing code before any implementation starts. Read-only. Use after planner, before implementor, on anything non-trivial. |
| [planner](planner.md) | Turns a request or backlog item into an executable plan in .ai/plans/. Use when work needs breaking down before implementation, or when an existing plan has gone stale. Writes plans and specs; does not write code. |
| [pr-agent](pr-agent.md) | Prepares reviewable delivery and performs only the granted commit, push, PR or merge actions. |
| [researcher](researcher.md) | Gathers bounded evidence about the actual code and records useful findings without deciding behavior. |
| [reviewer](reviewer.md) | Independently reviews the actual result against current contracts and reports actionable defects. |
| [scribe](scribe.md) | Keeps human-facing documentation true after the code has changed, and hunts duplicated facts. Use after work lands, or when docs are suspected of being stale. |
| [tester](tester.md) | Verifies approved outcomes and invariants using actual checks on an identified revision. |
| [track-documentor](track-documentor.md) | Makes the record true before a track's work is reviewed — specs describe what shipped, docs describe how to use it — then validates its own output against the code. Runs inside the track worktree, after the implementor and after every round of fixes. |
| [track-fixer](track-fixer.md) | Fixes the defects triage recorded for a track, working from the original plan and research brief with no memory of the review. Adds the regression check for each, tests only what it changed, and commits per fix. |
| [track-implementor](track-implementor.md) | Builds the plans of one orchestration track inside its worktree, committing each finished step slice, then self-reviews the whole diff and runs only the tests the change affects. The implementor's job, scoped to a worktree and a branch. |
| [track-researcher](track-researcher.md) | Researches one plan inside its orchestration worktree and writes the brief the implementor and later the bug-fixer both work from. Read-only over code — it investigates, it never changes anything. |
| [track-reviewer](track-reviewer.md) | Reviews a track's pull request cold — the plan, the contracts, the documentation and the diff, and deliberately nothing else. Never sees the research or the implementor's reasoning. Read-only; it reports findings and does not fix them. |
| [track-triage](track-triage.md) | Turns a reviewer's findings into fix records a fresh agent can act on, separating what blocks the merge from what gets captured. Runs inside the track worktree, between the reviewer and the fixer. Writes records, never code. |
| [verifier](verifier.md) | Grades finished work against specs and observed behavior — never against the plan that produced it. Use on plans in .ai/plans/review/ before marking them done. |
