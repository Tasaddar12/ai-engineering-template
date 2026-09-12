---
name: context-handoff
description: Prepare a focused worker assignment, blocked-result handoff or pause/resume note. Preserve decisions, revision-specific evidence and the next action without copying the whole conversation.
---

# Hand off only the context needed to act

Follow the assigned role and [worker handoff contract](../../../.ai/references/worker-handoff.md).
Use existing phase artifacts and result paths; this skill does not start agents
or authorize restarting processes.

## Match the handoff to its reader

| Reader | Useful context | Existing destination |
|---|---|---|
| Fresh component worker | Objective, acceptance, decisions, ownership, interfaces, prerequisites, required source/skills, checks and result path | IMPLEMENT and runtime assignment |
| Coordinator or dependent worker | Actual changes, commits, results, deviations and unresolved needs | SUMMARY |
| Returning coordinator | Current revision, completed scope, uncertain processes/results, pending decisions and next safe action | Optional .continue-here.md and existing phase evidence |

Link authoritative files and source locations with a short reason to read them.
Include only decisions and findings that affect the assignment. Avoid repeating
large documents, loading all skill bodies, or forwarding an entire earlier
agent conversation. An excerpt is useful when it identifies the relevant
contract; it should retain the source and not become a competing owner.

## Preserve the facts that prevent repeated work

Name the assigned checkout and branch, the input or tested revision, what is
integrated versus merely committed in another branch, and what the next step
actually depends on. Include real command outcomes and limits, not just
"tests passed." Retain eliminated debugging hypotheses or a decisive research
finding when rediscovering them would waste work.

Separate an actual human decision from a recommendation, and distinguish pending,
blocked, verified, published and merged evidence. A required gap stays required
after the handoff. Record a precise blocker instead of leaving a vague request
to "finish the rest."

## Make resumption safe

Treat process IDs, working-tree cleanliness, PR checks and remote merge state as
observations that must be checked again. Reconcile saved notes with current Git
and process evidence before acting. A pause note cannot prove a worker stopped
or authorize replaying interrupted edits.

Return valid committed results for coordinator inspection and reuse where
possible. Preserve incomplete work and follow [phase-resume](../../../.ai/commands/phase-resume.md)
for reconciliation. A worker writes only its assigned result; shared context,
status and scheduling remain coordinator responsibilities.
