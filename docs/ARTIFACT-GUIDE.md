# Artifact guide

The reusable authoring templates live under [`engineer/templates/`](../engineer/templates/). Read the full selected template, including its frontmatter, teaching text, detailed examples, counterexamples and consumer notes. This guide helps select and connect artifacts; it does not replace their instructions. Keep the adopting project's identity unfilled until onboarding.

Source attribution and revision history live in [third-party notices](../THIRD-PARTY-NOTICES.md). The [agent catalog](../agents/AGENT.md) supplies the assigned methods. The [truth map](../engineer/truth-map.md) identifies authoritative owners. Project decisions belong in project records, not copied guide text.

## Authoring sequence

1. Select the artifact that answers the current question; do not create the whole catalog automatically.
2. Read its purpose, complete fields, lifecycle and downstream consumers before filling anything.
3. Copy the template's designated output skeleton into the path named by the workflow. Keep all applicable sections and guidance for the author. A completed project record should contain actual project evidence; it is not a place to paste the source template's tutorial text wholesale.
4. Follow the full field guidance and worked examples. Replace placeholders only with known facts or recorded decisions; label genuinely unresolved questions as unresolved.
5. Read the assigned producer's method and the relevant local adaptation. A template's reference to an upstream tool does not prove that tool is installed or that its operation ran.
6. For Python-runtime artifacts, apply the additive [template contract](../engineer/references/template-contract.md) in the same artifact. Preserve the template's required authoring content and all runtime-required metadata.
7. Check both narrative quality and required runtime structure at the workflow's authorized point. Commit the record before the execution boundary that consumes it.

Do not shorten source templates, discard unfamiliar sections, silently remove references, invent evidence, or use a completed heading as proof of a completed outcome. If a local contract needs adaptation, record the reason in the owning phase artifact and preserve all unaffected guidance.

## Complete template catalog

The navigation catalog is separate from the artifact templates. Select only what the actual outcome needs.

### Project identity and continuity

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [README.md](../engineer/templates/README.md) | Canonical artifact registry | Template maintainers → agents locating fact owners |
| [project.md](../engineer/templates/project.md) | `.planning/PROJECT.md`: project identity and living context | Onboarding coordinator → every project and phase planning session |
| [requirements.md](../engineer/templates/requirements.md) | `.planning/REQUIREMENTS.md`: checkable outcomes and traceability | Coordinator → planner, checker and verifier |
| [roadmap.md](../engineer/templates/roadmap.md) | `.planning/ROADMAP.md`: phases, dependencies and milestone views | Coordinator/runtime → phase selection and progress tracking |
| [state.md](../engineer/templates/state.md) | `.planning/STATE.md`: living session memory and derived position | Coordinator/state updater → returning sessions |

The project runtime configuration, current specifications and linked rationale are intentional local records. Use supported runtime operations and actual configured checks to validate their applicable structure; an unavailable upstream health command is not a check.

### Phase definition, research and execution

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [spec.md](../engineer/templates/spec.md) | `NN-SPEC.md`: locked desired requirements, boundaries, edge cases and negative coverage | Specification discussion → discuss, planner and verifier |
| [context.md](../engineer/templates/context.md) | `NN-CONTEXT.md`: implementation choices, canonical references and local authority | Discussion coordinator → researcher/planner; runner reads authorization |
| [discussion-log.md](../engineer/templates/discussion-log.md) | `NN-DISCUSSION-LOG.md`: required question/answer audit trail | Discussion coordinator → human audit; excluded from routine worker required reading |
| [research.md](../engineer/templates/research.md) | `NN-RESEARCH.md`: relevant ecosystem research at a revision | Phase researcher → planner and implementation workers |
| [phase-prompt.md](../engineer/templates/phase-prompt.md) | `NN-CC-PLAN.md`: complete executable task instructions | Planner → checker, scheduler and assigned executor |
| [planner-subagent-prompt.md](../engineer/templates/planner-subagent-prompt.md) | Context envelope for a fresh planning agent | Coordinator → planner; methods live in the referenced role guidance |
| [VALIDATION.md](../engineer/templates/VALIDATION.md) | `NN-VALIDATION.md`: requirement-to-test strategy, sampling and feedback coverage | Preparation/validation workflow → executor and verifier |
| [continue-here.md](../engineer/templates/continue-here.md) | Phase `.continue-here.md`: exact resumption context | Interrupted session → returning coordinator |

### Results and acceptance

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [summary.md](../engineer/templates/summary.md) | Full `NN-CC-SUMMARY.md` guidance and skeleton | Component executor → integrator, dependents and verifier |
| [verification-report.md](../engineer/templates/verification-report.md) | `NN-VERIFICATION.md`: independent goal evidence, findings and revision | Verifier → coordinator and publication gate |
| [UAT.md](../engineer/templates/UAT.md) | `NN-UAT.md`: persistent acceptance session, actions and gaps | Coordinator records actual human observations → returning sessions and acceptance gate |
| [milestone.md](../engineer/templates/milestone.md) | One `.planning/MILESTONES.md` entry: what a milestone shipped | `milestone.complete` and closing coordinator → returning sessions and onboarding readers |

The Python adapter adds local coverage and check fields to the complete `summary.md` skeleton. Compact or alternative summaries are not retained: the full result remains the normal handoff contract.

### Human setup

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [user-setup.md](../engineer/templates/user-setup.md) | `NN-USER-SETUP.md`: setup that requires actual human action | Implementer/coordinator → user and continuation |

The setup template records concrete prerequisites a human must perform. Current user instructions govern authority. Preserve a real pending prerequisite instead of inventing its completion or removing it to permit dispatch.

### Codebase maps and project research

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [codebase/architecture.md](../engineer/templates/codebase/architecture.md) | `.planning/codebase/ARCHITECTURE.md`: inspected conceptual organization and flow | `codebase-mapper` → planner, researcher and worker; refreshed by planning when runtime freshness says stale |
| [codebase/stack.md](../engineer/templates/codebase/stack.md) | `.planning/codebase/STACK.md`: technologies actually executing | `codebase-mapper` → setup and implementation planning; freshness follows relevant manifest changes |
| [research-project/ARCHITECTURE.md](../engineer/templates/research-project/ARCHITECTURE.md) | `.planning/research/ARCHITECTURE.md`: domain architecture research | Project researcher → research synthesis and roadmap discussion |
| [research-project/FEATURES.md](../engineer/templates/research-project/FEATURES.md) | `.planning/research/FEATURES.md`: domain feature landscape | Project researcher → requirements and roadmap discussion |
| [research-project/PITFALLS.md](../engineer/templates/research-project/PITFALLS.md) | `.planning/research/PITFALLS.md`: likely mistakes and evidence-backed prevention | Project researcher → planner and checker |
| [research-project/STACK.md](../engineer/templates/research-project/STACK.md) | `.planning/research/STACK.md`: source-backed technology recommendations | Project researcher → architecture and setup decisions |
| [research-project/SUMMARY.md](../engineer/templates/research-project/SUMMARY.md) | `.planning/research/SUMMARY.md`: synthesis and roadmap implications | Research synthesizer → coordinator and planner |

Codebase maps describe inspected current source. Project research describes possible approaches in the domain. Recommendations become project constraints only through the recorded decision process; neither category invents requirements. Map freshness is computed from the commits touching mapped source since its last write, so an analysis date alone does not keep a map current.

## Additional local templates

| Template | Output | Why it exists |
|---|---|---|
| [ADR.md](../engineer/templates/ADR.md) | `.planning/decisions/ADR-NNN-name.md` | Preserve linked rationale, alternatives, tradeoffs and supersession history |
| [CURRENT-SPEC.md](../engineer/templates/CURRENT-SPEC.md) | `.planning/specs/SPEC-NNN-capability.md` | Describe evidenced current behavior separately from desired phase requirements |
| [issue.md](../engineer/templates/issue.md) | Provider issue authoring patterns | Keep issue type, scope, evidence and canonical relationships correct |
| [pull-request.md](../engineer/templates/pull-request.md) | Provider PR description and readback contract | Preserve review context, current evidence and safe publication |
| [rule.md](../engineer/templates/rule.md) | Reusable modular engineering rule | Specify exact scope, authority, actions, exceptions and evidence |
| [SECURITY.md](../engineer/templates/SECURITY.md) | Security evidence and risk lifecycle report | Record examined and unexamined scope, outcomes and dependencies |
| [UI-SPEC.md](../engineer/templates/UI-SPEC.md) | Approved visual and interaction contract | Keep actual UI behavior reviewable against an explicit specification |

These local templates retain complete purpose, producer/consumer guidance, authoring steps, worked examples and handoff expectations. Ordinary progress belongs in summaries and Git history, not in a new architectural decision record. PROJECT Key Decisions owns choices that constrain future work, recorded through the runtime while deciding. An ADR stores optional linked rationale; it does not itself approve a choice or own its decision lifecycle. A technology recommendation must reflect what an authorized validation check actually did; do not imply that reading a manifest or API documentation proves an implementation will work.

## Connect a full template to the Python runtime

Runtime fields add machine-readable integrity and coverage to the authoring artifact; they do not replace its human-readable method.

| Artifact | Local additions and interpretation |
|---|---|
| CONTEXT | Phase identity, approval/authority, dependencies, UAT setting and canonical refs; distinguish scoped acceptance from actual implementation instruction |
| PLAN | Kind, exclusive resources, phase acceptance mapping, documentation obligations, argv checks and issue references; preserve the explicit documentation handoff |
| SUMMARY | Acceptance/documentation coverage and actual check evidence alongside the complete template summary and remaining-work narrative |
| VERIFICATION | Exact assigned revision, covered inputs, current acceptance/integration/documentation findings; runtime attestation remains separate from author claims |
| UAT | Runtime source/case/history receipts alongside complete session sections and actual human decisions |

Use one YAML frontmatter block per artifact. Keep the template's requirements, modified/deleted files, tasks, verification and must-have guidance. Use a finer-grained local `acceptance` mapping when phase acceptance IDs differ from the requirements list. Exact fields, examples and semantics are in the [template contract](../engineer/references/template-contract.md).

**Checkpoint boundary:** Non-autonomous plans and unresolved `user_setup` can be valid plans but block Python execution that requires them to be ready. The coordinator handles the actual decision or human action, records the result and prepares an authorized autonomous continuation. Never erase a checkpoint just to satisfy the runner. A human-verify observation, a consequential decision and an action the agent cannot perform are different checkpoint types.

**Parallelism boundary:** `depends_on` controls readiness after successful integration and required checks. `wave` describes intended order; it does not prove two tasks can run together. Shared paths and resources serialize even if a coupling note explains why a plan expected same-wave work.

**Configuration boundary:** `.planning/config.yaml` configures the Python workflows. Do not treat upstream JSON examples as runtime configuration; use only configuration keys and values supported by the actual runtime.

## What a useful handoff looks like

| Weak artifact | Useful artifact | Why |
|---|---|---|
| “Implement authentication” | Task inputs, interface, error behavior, denied-access case and explicit completion evidence | A fresh worker can act and verify without guessing the intended behavior |
| “All tests passed” | Actual command, relevant scenario, observed result, tested revision and untested boundary | A verifier can judge evidence strength and currentness |
| “Same as the last plan” | Links only to the prerequisites that supply required types, decisions or exports | Dependency context communicates a real need rather than copying history |
| “User approved” | The actual instruction, named scope and recorded boundary | Authority can be traced without inventing permission |
| “Everything is complete” | Outcome coverage, verified documentation, remaining gaps and the next consumer | Completion follows evidence rather than a label |

These examples supplement the full source templates. They do not replace or weaken their detailed criteria. See [phase workflow](PHASE-WORKFLOW.md) for when each artifact is produced and [requests](REQUESTS.md) for worked prompts that invoke those procedures.
