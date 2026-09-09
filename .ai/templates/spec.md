---
tier: contract
authority: agent
id: SPEC-{{ nnn }}
scope: {{ owned_behavior }}
links: []
verification_refs: []
title: {{ title }}
---
> Contract: amend with evidence inside the approved scope.

# {{ title }}

## Requirement

Describe current correct behavior in present tense, bounded by this SPEC's
declared scope. Keep implementation mechanics in their code owner.

## Acceptance criteria

- Given {{ precondition }}, when {{ action }}, then {{ observable_result }}.

## Invariants

Properties that hold across valid paths, errors and boundaries.

## Explicitly out of scope

Current unsupported behavior and the boundary owned by another SPEC.

## Verification

Link current repeatable checks and explain what they establish.
Do not narrate prior states or introduce planned behavior.

<!-- SPEC-{nnn}-{slug}.md. Each sentence describes today's behavior.
No TODO, history or future promises. Keep details that define correctness;
link incidental implementation rather than reproducing it. -->
