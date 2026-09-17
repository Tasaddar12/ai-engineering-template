# Retained artifact templates

Read the selected template in full, including examples, counterexamples, field
explanations and consumer guidance. Generate the assigned project record from its
**File Template** or corresponding artifact block; do not copy the whole
instructional document into a phase result. Apply the
[runtime contract](../runtime/TEMPLATE-CONTRACT.md) to executable phase artifacts.

The [template guide](../guides/ARTIFACT-GUIDE.md) maps every retained source to
its producer, consumer and destination. The selected [agent methods](../agents/README.md)
connect those artifacts through the existing [procedures](../commands/README.md).

| Purpose | Complete authoring sources |
|---|---|
| Project intent and continuity | [project](project.md), [requirements](requirements.md), [roadmap](roadmap.md), [state](state.md) |
| Phase decisions and requirements | [context](context.md), [spec](spec.md), [discussion log](discussion-log.md) |
| Research and preparation | [research](research.md), [phase prompt](phase-prompt.md), [planner prompt](planner-subagent-prompt.md), [validation](VALIDATION.md) |
| Results, acceptance and continuation | [summary](summary.md), [verification](verification-report.md), [UAT](UAT.md), [continue here](continue-here.md), [user setup](user-setup.md) |
| Current contracts and rationale | [current SPEC](CURRENT-SPEC.md), [ADR](ADR.md) |
| Inspected codebase maps | [architecture](codebase/architecture.md), [stack](codebase/stack.md) |
| Project research | [architecture](research-project/ARCHITECTURE.md), [features](research-project/FEATURES.md), [pitfalls](research-project/PITFALLS.md), [stack](research-project/STACK.md), [summary](research-project/SUMMARY.md) |

These 25 artifact templates are the available sources. Configuration belongs in
[config.yaml](../../.planning/config.yaml). Removed variants and specialty templates
are not required dependencies, and a template does not create records or register
a command. Keep adopting-project identity unfilled until actual onboarding.

## Handoff checklist

- Read the selected full template before authoring or checking its output.
- Fill concrete values; preserve locked decisions and canonical source paths.
- Keep examples as examples. Do not execute sample deletion, deployment or commit commands.
- Add only the adapter fields required by the operation, following the contract.
- Give the next agent the artifact, applicable methods, exact source revision and relevant dependency summaries.
- Check both the semantic outcome and executable readiness; either can fail independently.
- Record a newly discovered incompatibility in this project's affected phase.
  Correct the actual producer and consumer together; upstream history is attribution,
  not this project's change log or an instruction to maintain the source template.
