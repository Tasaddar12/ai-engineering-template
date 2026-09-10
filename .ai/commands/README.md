---
tier: contract
authority: agent
title: Command procedures
---

# Command procedures

Each file owns the detailed steps of its named operation. Slash-style names
refer to these Markdown procedures, not registered tools. Supply the input
placeholders explicitly. The root [AGENTS.md](../../AGENTS.md) governs action
scope; [roles](../agents/README.md) define who performs the assigned work.

## Common tasks

These routes link to the owning procedures; they do not grant action
authority or replace those instructions.

| Task | Entry points and handoff |
| --- | --- |
| Initialize or adopt | [onboard](onboard.md), with [ADOPTING](../../docs/ADOPTING.md); report the proposed changes, then use [onboard-pr](onboard-pr.md) for authorized publication. |
| Plan a change | Use [defer](defer.md) to capture findings, [fix](fix.md) for confirmed defects, or [plan-new](plan-new.md) for changed behavior. [Plan-checker](../agents/plan-checker.md) reviews proposals before [plan-start](plan-start.md). |
| Implement and close | [plan-start](plan-start.md) or [fix](fix.md); for plans, use [plan-review](plan-review.md), then [plan-done](plan-done.md). |
| Review or verify | [Plan-checker](../agents/plan-checker.md) reviews proposals; [verifier](../agents/verifier.md) checks implementations. [Track-reviewer](../agents/track-reviewer.md) reviews completed tracks. |
| Execute independent tracks | Follow the [orchestration guide](../../docs/ORCHESTRATION.md): [orchestrate](orchestrate.md), [orchestrate-track](orchestrate-track.md), [orchestrate-status](orchestrate-status.md), and [orchestrate-clean](orchestrate-clean.md). |

## Procedures

| Name | Purpose |
| --- | --- |
| [defer](defer.md) | Capture a problem you found but should not fix now, so it survives the session |
| [fix](fix.md) | Diagnose, record and fix a single defect, with the check that stops it coming back |
| [harvest](harvest.md) | Turn a meeting or design document into ADRs, intent changes and intake items |
| [onboard-pr](onboard-pr.md) | Review the onboarding change, commit it, and open a merge request |
| [onboard](onboard.md) | Set up the .ai/ structure for this project, or brief yourself on an existing one |
| [orchestrate-clean](orchestrate-clean.md) | Remove worktrees and branches left by an orchestration run, after checking nothing unmerged is lost |
| [orchestrate-status](orchestrate-status.md) | Show where an orchestration run stands — waves, tracks, review rounds and what is waiting on a human |
| [orchestrate-track](orchestrate-track.md) | Build one orchestration track in its worktree — research, implement, document, PR, review loop — then report ready or stopped |
| [orchestrate](orchestrate.md) | Build several plans at once — schedule them into dependency waves, run each track in its own worktree session, and merge as they clear |
| [plan-archive](plan-archive.md) | Sweep finished plans into their period folder, and abandon stale ones |
| [plan-block](plan-block.md) | Park a plan on a decision only a human can make |
| [plan-done](plan-done.md) | Close out a verified plan |
| [plan-new](plan-new.md) | Write a new plan into .ai/plans/backlog/ |
| [plan-review](plan-review.md) | Verify a finished plan against specs and observed behavior |
| [plan-start](plan-start.md) | Move a plan to active and implement it |
| [plan-status](plan-status.md) | Show every plan by stage, plus current state, blockers and suspected drift |
| [spec-amend](spec-amend.md) | Correct a spec or ADR that turns out to be wrong, with a recorded amendment |
