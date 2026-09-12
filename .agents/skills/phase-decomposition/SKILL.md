---
name: phase-decomposition
description: Turn agreed project outcomes into phase goals, or prepare a substantial phase as bounded components with interfaces, dependencies, ownership, acceptance coverage and realistic checks.
---

# Decompose outcomes into executable scope

Use the coordinator or preparer responsibility under the
[shared rules](../../../.ai/RULES.md). This method prepares work; it does not
dispatch agents or create another work-item lifecycle.

## Choose the right level

For project direction, identify desired outcomes and boundaries, group coherent
capabilities into phase goals, and order genuine prerequisites in ROADMAP.
Detail the next useful scope. Do not prematurely specify every future component.

For a selected phase, translate each agreed acceptance outcome into observable
behavior and evidence. Clarify only missing decisions that would change the
result; preserve instructions and authority already supplied. Keep unresolved
dependent scope out of executable assignments.

Build a coverage map while preparing:

| Acceptance | Observable result | Implementing component | Real check | Documentation owner |
|---|---|---|---|---|

Use this to expose missing behavior and handoffs, then retain the facts in their
existing owners. A separate permanent coverage registry is unnecessary.

## Split at useful boundaries

Prefer a bounded outcome a fresh worker can implement and check. Use a thin
end-to-end component when integration is the principal unknown; use parallel
components against a settled interface when their boundaries are already clear.
Neither a fixed file count nor a fixed number of components establishes quality.

For each boundary, specify the producer, consumer, input/output shape, failure
behavior and who owns the interface. Point to current source definitions and
their revision. If a new shared contract must exist first, give it an explicit
owner and prerequisite; a skeleton is not completed product behavior.

Distinguish three reasons work may wait:

- A consumer needs another component's integrated, checked output: dependency.
- Workers touch the same file or exclusive external resource: contention.
- The product behavior remains undecided: a decision affecting that scope.

Inspect databases, ports, migrations, configuration and shared services as well
as files. Worktrees do not isolate those resources. Specify exact Git path case;
overlapping ownership is scheduled conservatively across platforms. Within-phase
dependencies use component IDs; cross-phase prerequisites require delivered
behavior. Waves describe readiness, not a barrier for unrelated work.

## Make the instructions executable

Fill [IMPLEMENT](../../../.ai/templates/IMPLEMENT.md) with the objective, owned
paths, resources, prerequisites, acceptance IDs, read-first sources and needed
skill paths. Ground checks in the real project and execution directory; do not
guess a command or reference a test path that no component will create.

Assign each required guide or SPEC to the component that will actually cover it.
A later documentor can depend on implemented code; its predecessor must not claim
that future documentation as already complete.

Return components, interface agreements, coverage, dependency reasoning and
unresolved choices for [preparation checking](../../../.ai/commands/phase-prepare.md).
Preserve completed instructions when corrections are needed; add corrective
components through the coordinator's existing replan procedure.
