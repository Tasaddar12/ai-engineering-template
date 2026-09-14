# Artifact guide

The retained template files are available under `.ai/templates/` with their
complete teaching content and stable artifact names. Read the selected template in
full, including examples, counterexamples, consumer notes and lifecycle guidance.
This guide helps select and connect them; it does not replace their instructions.

Source attribution and revision history live in
[third-party notices](../THIRD-PARTY-NOTICES.md). The
[agent catalog](../agents/README.md) supplies selected full methods and
[agent adaptation](../references/agent-adaptation.md) resolves host boundaries.
The notices link upstream Git history; project decisions belong in this
project's phase records.

## Authoring sequence

1. Select the artifact that answers the current question; do not create the
   entire catalog automatically.
2. Read its purpose and downstream consumers before filling fields.
3. Copy its **File Template** or designated output skeleton into the stated
   destination. Keep all applicable output sections. The teaching text stays
   available in the source template; completed project records contain actual
   project evidence instead of pasted authoring instructions.
4. Follow the full field guidance and examples. Replace placeholders with known
   facts, recorded decisions or explicitly unresolved questions.
5. Read the assigned agent method and local adaptation. A reference to an
   upstream command or tool does not prove that executable is installed.
6. For Python-runtime artifacts, apply the additive
   [template contract](../runtime/TEMPLATE-CONTRACT.md) in the same artifact.
7. Check both content quality and the required runtime structure. Commit the
   record before the execution boundary that consumes it.

**Do not shorten the source templates, discard unfamiliar sections, silently
remove references, invent evidence, or use a completed heading as proof of a
completed outcome.** Conflicts require an explicit reasoned adaptation recorded
in the affected project phase.

## Complete template catalog

The tables list retained authoring sources and their producing/consuming roles.
The navigation catalog is separate from the 25 artifact templates. Select only
the artifacts needed for the current project outcome.

### Project identity and continuity

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [README.md](../templates/README.md) | Canonical artifact registry | Template maintainers → agents locating fact owners |
| [project.md](../templates/project.md) | `.planning/PROJECT.md`: project identity and living context | Onboarding coordinator → every project/phase planning session |
| [requirements.md](../templates/requirements.md) | `.planning/REQUIREMENTS.md`: checkable outcomes and traceability | Coordinator → planner, checker and verifier |
| [roadmap.md](../templates/roadmap.md) | `.planning/ROADMAP.md`: phases, dependencies and milestone views | Coordinator → phase selection and progress tracking |
| [state.md](../templates/state.md) | `.planning/STATE.md`: living session memory | Coordinator/state updater → returning sessions |

Local runtime configuration and current specifications/ADRs are intentional
local extensions. Use the runtime contract and configured checks to validate
their applicable structure; an unavailable upstream health command is not a check.

### Phase definition, research and execution

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [spec.md](../templates/spec.md) | `NN-SPEC.md`: locked desired requirements, boundaries, edge and negative coverage | Specification discussion → discuss/planner/verifier |
| [context.md](../templates/context.md) | `NN-CONTEXT.md`: implementation choices and applicable context | Discussion coordinator → researcher/planner; local authorization additions feed runner |
| [discussion-log.md](../templates/discussion-log.md) | `NN-DISCUSSION-LOG.md`: discussion audit trail | Discussion recorder → human audit; excluded from routine worker required reading |
| [research.md](../templates/research.md) | `NN-RESEARCH.md`: relevant ecosystem research | Phase researcher → planner and implementation workers |
| [phase-prompt.md](../templates/phase-prompt.md) | `NN-CC-PLAN.md`: executable task instructions | Planner → checker, scheduler and assigned worker |
| [planner-subagent-prompt.md](../templates/planner-subagent-prompt.md) | Context envelope for a fresh planning agent | Coordinator → planner; planning expertise resides in the referenced agent guidance |
| [VALIDATION.md](../templates/VALIDATION.md) | `NN-VALIDATION.md`: validation strategy and feedback coverage | Preparation/validation procedure → executor/verifier |
| [continue-here.md](../templates/continue-here.md) | Phase `.continue-here.md`: resumption context | Interrupted session → returning coordinator |

### Results and acceptance

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [summary.md](../templates/summary.md) | Full `NN-CC-SUMMARY.md` guidance and skeleton | Component worker → integrator, dependents and verifier |
| [verification-report.md](../templates/verification-report.md) | `NN-VERIFICATION.md`: independent goal evidence and findings | Verifier → coordinator and publication gate |
| [UAT.md](../templates/UAT.md) | `NN-UAT.md`: persistent acceptance session and gaps | Coordinator recording human observations → returning sessions and acceptance gate |

The Python adapter instructs component workers to use the full `summary.md`
skeleton plus its local coverage/check fields. Compact and alternative summary
files are not retained; the complete result remains the normal handoff contract.

### Human setup

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [user-setup.md](../templates/user-setup.md) | `NN-USER-SETUP.md`: setup requiring actual human action | Implementer/coordinator → user and continuation |

The setup template records concrete prerequisites requiring human action.
Current user instructions govern authorization; preserve an actual pending
prerequisite instead of inventing completion or removing it to permit dispatch.

### Codebase maps and project research

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [codebase/architecture.md](../templates/codebase/architecture.md) | `.planning/codebase/ARCHITECTURE.md`: inspected conceptual organization | Reconnaissance → planner/researcher/worker |
| [codebase/stack.md](../templates/codebase/stack.md) | `.planning/codebase/STACK.md`: technologies actually executing | Reconnaissance → setup and implementation planning |
| [research-project/ARCHITECTURE.md](../templates/research-project/ARCHITECTURE.md) | `.planning/research/ARCHITECTURE.md`: domain architecture research | Project researcher → research synthesis and roadmap |
| [research-project/FEATURES.md](../templates/research-project/FEATURES.md) | `.planning/research/FEATURES.md`: domain feature landscape | Project researcher → requirements/roadmap discussion |
| [research-project/PITFALLS.md](../templates/research-project/PITFALLS.md) | `.planning/research/PITFALLS.md`: likely mistakes and prevention | Project researcher → planner/checker |
| [research-project/STACK.md](../templates/research-project/STACK.md) | `.planning/research/STACK.md`: source-backed technology recommendations | Project researcher → architecture and setup choices |
| [research-project/SUMMARY.md](../templates/research-project/SUMMARY.md) | `.planning/research/SUMMARY.md`: synthesis with roadmap implications | Research synthesizer → coordinator/planner |

Codebase maps describe inspected current code. Project research describes possible
approaches in the domain. Recommendations become constraints only through the
recorded decision process; neither category invents product requirements.

## Additional local templates

| Template | Output | Why it exists |
|---|---|---|
| [ADR.md](../templates/ADR.md) | `.planning/decisions/ADR-NNN-name.md` | Preserve significant rationale, alternatives, tradeoffs and supersession history |
| [CURRENT-SPEC.md](../templates/CURRENT-SPEC.md) | `.planning/specs/SPEC-NNN-capability.md` | Describe evidenced current behavior separately from desired phase requirements |

Both follow the teaching design of the retained templates: complete output
skeleton, purpose, producer/consumer map, authoring steps, good/bad examples with
reasons, completion criteria and downstream handoff. Ordinary progress belongs
in SUMMARY and Git rather than a new architectural decision record.

## Connect a full template to the Python runtime

| Artifact | Local additions and interpretation |
|---|---|
| CONTEXT | Phase number, approval, phase dependencies and UAT setting; identified Acceptance and actual Authorization |
| PLAN | Kind, exclusive resources, phase acceptance mapping, documentation obligations and argv checks; explicit documentation handoff |
| SUMMARY | Acceptance/documentation coverage and actual check evidence alongside full template summary content |
| VERIFICATION | Exact assigned revision and local acceptance/integration/documentation/findings evidence; runtime attestation remains distinct from upstream metadata |
| UAT | Runtime source/case/history receipts alongside full session sections |

Use one YAML frontmatter block per artifact. Keep the template `requirements`,
`files_modified`, `files_deleted`, tasks, verification and must-have guidance.
Use a finer local `acceptance` mapping when phase acceptance IDs differ from the
requirements list. Exact details and examples belong to the
[template contract](../runtime/TEMPLATE-CONTRACT.md).

**Checkpoint boundary:** Non-autonomous plans and unresolved `user_setup` remain
valid planning records but block Python `run`. The coordinator handles the actual
checkpoint with the human, records the result and prepares an autonomous
continuation. Never remove a checkpoint simply to satisfy the runner.

**Parallelism boundary:** `depends_on` drives readiness after successful
integration and checks. `wave` is descriptive. Shared paths/resources still
serialize even if template `coupling_justified` explains a same-wave coupling.

**Configuration boundary:** `.planning/config.yaml` configures Python execution.
No JSON configuration template is supplied. Upstream JSON examples do not
configure the Python runtime.

## What a useful handoff looks like

| Weak artifact | Useful artifact | Why |
|---|---|---|
| “Implement authentication” | Concrete task inputs, interface, error behavior, denied-access check and completion condition | A fresh worker can act and verify without guessing |
| “All tests passed” | Actual command, relevant scenario, result, tested revision and untested boundary | A verifier can assess evidence strength |
| “Same as the last plan” | References only prerequisites supplying required types, decisions or exports | Dependency context reflects a real need |
| “User approved” | Actual instruction, scope and recorded boundary | Authority can be traced without invented permission |
| “Everything is complete” | Outcome coverage, verified documentation, remaining gaps and next consumer | Completion follows evidence instead of a label |

These examples supplement the full source templates. They do not replace or
weaken their more detailed criteria.
