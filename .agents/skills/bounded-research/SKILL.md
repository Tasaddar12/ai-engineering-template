---
name: bounded-research
description: Resolve a technical uncertainty that affects a phase's implementation or validation. Compare source-backed options, compatibility and failure modes without reopening settled product decisions.
---

# Bounded technical research

Follow the assigned role and [shared rules](../../../.ai/RULES.md).
Research should change a decision or remove a concrete implementation unknown.

## Frame the question

State what is unknown, which acceptance or component it affects, the constraints
already settled, and what evidence would let work proceed. Investigate an
already selected technology on its merits within the assignment; do not restart
technology selection unless the evidence exposes a relevant incompatibility.

Inspect the project's actual versions, call sites and existing patterns first.
For external facts, use current primary documentation or source appropriate to
those versions. Verify exact option names, enum values and path conventions at
their definitions, not just in a search result or tutorial.

## Separate evidence from inference

| Observation | Appropriate conclusion |
|---|---|
| An explicit supported-version constraint excludes this version | A documented incompatibility |
| Compatibility metadata omits a version | Support is unknown until stronger evidence exists |
| A controlled probe fails at the relevant operation | A reproduced limit under the recorded conditions |
| Search found no example | No example was found; absence is not proof of impossibility |

Record contrary evidence and the conditions under which a recommendation would
change. For migrations, account for relevant stored data, external configuration
and installed artifacts, not only tracked files.

If documentation leaves an important uncertainty, use a small isolated probe
within existing authorization. Keep its inputs and actual result. Do not install
new services, change accounts or substitute reduced behavior merely because a
preferred tool is unavailable.

## Return the decision material

Put useful findings in the assigned RESEARCH or return them to the coordinator:
the question, recommendation, source/version evidence, tradeoffs, integration
and checking implications, and remaining uncertainty. Link substantial sources
instead of copying them. Stop when the question is answered sufficiently for
the next step; expand research only when a discovered dependency warrants it.

Research supports [phase decisions](../../../.ai/references/phase-artifacts.md).
It does not approve new scope, turn uncertain compatibility into a guarantee,
or justify claiming implementation is complete.
