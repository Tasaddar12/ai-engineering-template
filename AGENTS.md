# Agent entry point

This repository is a reusable engineering workflow template. Keep the adopting
project's identity unfilled until onboarding. Create project-specific records for
template maintenance only when the user asks.

Read [.ai/RULES.md](.ai/RULES.md), [PROJECT](.planning/PROJECT.md),
[STATE](.planning/STATE.md), the selected phase and your
[role](.ai/agents/README.md). Load the selected
[command](.ai/commands/README.md) and the references it names.
[Truth map](.ai/truth-map.md) locates each fact's owner.

## How work flows

A command names a workflow. The workflow is the procedure: it decides what to
load, which agents to spawn with what context, and which runtime verbs to call.
The [runtime](.ai/runtime/README.md) performs every planning-record change — phase
numbering, the roadmap, STATE.md, PROJECT.md's Key Decisions, REQUIREMENTS.md's
Traceability, todos, quick tasks, milestones. Do not edit those structures by
hand; `python .ai/runtime/phase.py query <verb>` owns them, and hand edits drift
from them.

Prose the runtime does not own — a project's narrative sections, a requirement's
wording, an ADR's argument — is written by hand, and `planning.validate` reports
where either kind has drifted. It is warn-only, so it never stalls a session.

Retirement has a path, and it is never a strikethrough or an in-place "Closed":
see [retiring an entry](.ai/RULES.md#retiring-an-entry).

```
/onboard                   initialize the project    → PROJECT / REQUIREMENTS / ROADMAP
/phase "<description>"     add a phase to the roadmap
  → /discuss-phase {N}     capture decisions         → NN-CONTEXT.md
  → /plan-phase {N}        research and plan         → NN-MM-PLAN.md
  → /execute-phase {N}     implement                 → NN-MM-SUMMARY.md
  → /verify-work {N}       confirm the goal is met   → NN-VERIFICATION.md
  → /ship {N}              publish                   → pull request
  → /complete-milestone    when the milestone's phases are done
```

`/progress` reports where things stand and recommends one next step; `/next`
decides and proceeds. `/quick` handles changes too small for a phase, and
`/capture` parks an idea without derailing the current work.

Decisions that outlive a phase go in PROJECT.md's Key Decisions table, written by
`state.add-decision` while deciding rather than while building. A technology
choice is validated by a check that was actually run before it is recommended.

When the user asks to discuss a phase — including "let's discuss phase 01" —
load [discuss-phase](.ai/commands/discuss-phase.md) directly and follow it. Do not
require a slash command or an exact procedure name. A discussion request does not
grant implementation permission.

## Authority

NEVER start implementing a phase unless the user explicitly tells you to implement
that phase. Phase creation, planning, design approval and readiness do not grant
implementation permission. Follow
[phase authority](.ai/RULES.md#phase-authority).

Report when asked to report; implement the scope already authorized. Do not ask
again for an approval already supplied. Record consequential decisions in the
phase's CONTEXT. When code and documents disagree, establish which side is wrong
with evidence and preserve approved outcomes.

## Dispatch

The orchestrator routes; it does not do the work it dispatched. After spawning an
agent, wait for it — reading files, editing code or running tests while an agent
is active conflicts with that agent's edits.

Spawn agents by their exact name (`researcher`, `phase-preparer`, `phase-checker`,
`coder`, `verifier`, `code-reviewer`, `doc-writer`, `doc-verifier`,
`integration-checker`, `codebase-mapper`, `debugger`). Resolve the model with
`phase_run query resolve-model <agent>` and the effort with
`phase_run query resolve-effort <agent>`, and pass both inline on the dispatch
call — agent files carry neither as frontmatter, and a resolved `inherit` means
omit that argument. Never fall back to a generic agent type.

An agent that returns "complete" with no SUMMARY.md, or with no commits, did not
complete. Treat it as blocked.

## Skills

The skills under `.agents/skills/` mirror `.ai/commands/` one-for-one; a host
that discovers skills and a host that registers slash commands behave
identically. Load the skills that match the work, plus those named in the plan's
`read_first` section — do not read every skill body.

## Delivery

Commit each completed meaningful slice immediately with a descriptive message,
including agent summaries. Push when delivery is authorized, and open a draft PR
on the first push for tracking. Keep that draft current after every slice rather
than waiting until the work is finished.

[ship](.ai/commands/ship.md) publishes verified work; it does not merge, and it
has no bypass for a phase whose verification is not `passed`. Explicit user limits
override these defaults; read-only work needs no commit or publication. Follow
[delivery rules](.ai/RULES.md#session-and-authorization).

Start at [onboard](.ai/commands/onboard.md) for a new project, or
[progress](.ai/commands/progress.md) to see where an existing one stands.
