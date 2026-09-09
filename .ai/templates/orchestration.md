---
tier: status
authority: agent
id: ORCH-{{ nnn }}
base_branch: {{ resolved_branch }}
started: {{ timestamp }}
links: []
title: {{ title }}
---
> Status: replace stale coordination with current observations.

# {{ title }}

## Authority and selected work

Exact approved run scope, delivery limits and plans included/excluded.

## Dependencies and contention

| Plan / task | Depends on | Evidence / confidence | Shared files/specs |
| --- | --- | --- | --- |
| {{ plan }} | {{ dependency }} | {{ evidence }} | {{ ownership }} |

## Reserved IDs

Track, record kind and inclusive numeric block. Never compute IDs
independently from the same base or reuse a reserved block.

## Waves and tracks

Each track's absolute worktree, branch, plans, prerequisite results, allowed
writes, return location and expected validation. Distinguish facts from
inferred dependencies. Estimate role calls and explain real parallelism.

## Observations and review rounds

Dated Git observations and links to track evidence. These are snapshots;
Git owns revision, branch and merge facts.

## Needs a human

| Track | Blocker / decision | Recommendation / resume condition |
| --- | --- | --- |
| {{ track }} | {{ issue }} | {{ next_action }} |

## Completion and cleanup

Delivered, stopped and excluded tracks; exact cleanup evidence and remaining
work. Preserve this board when closing the run.

<!-- ORCH-{nnn}.md. The run orchestrator is its sole writer.
Never treat a snapshot column as more authoritative than Git. -->
