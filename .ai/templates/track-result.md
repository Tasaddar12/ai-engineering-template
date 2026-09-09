---
tier: log
authority: agent
title: Track evidence
---
> Log: preserve evidence; append corrections.

# Track evidence

## Identity and authority

Run, track, assigned absolute worktree/branch, ID ranges and approved actions.

## Stage observations

Research, implementation, documentation and validation references from Git.
Record the stage observed when resuming instead of guessing from memory.

## Review rounds

Append each round: exact revision, reviewer independence, verdict, concrete
findings, triage decisions, FIX/INTAKE links and remaining blockers.
The reviewer does not read this history; triage uses it to detect recurrence.

## Terminal result

The last recorded terminal line uses the track-result protocol:
**TRACK STATE:** ready | stopped | failed
Replace the alternatives with one actual state. Stopped/failed requires a
reason, remaining work and a resume condition. Ready identifies the reviewed,
validated revision; it does not assert merge approval.

<!-- ORCH-{nnn}-{track}-evidence.md inside state/orchestration.
One track coordinator writes this append-only evidence file. -->
