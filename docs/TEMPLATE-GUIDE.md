# Template guide

All 40 adapted template files are available under `.ai/templates/` with their
complete teaching content and stable artifact names. Read the selected template in
full, including examples, counterexamples, consumer notes and lifecycle guidance.
This guide helps select and connect them; it does not replace their instructions.

Source attribution and revision history live in
[third-party notices](../.ai/library/THIRD-PARTY-NOTICES.md) and the provenance records.
The [support route map](../.ai/library/README.md) resolves referenced methods and
execution boundaries. [changes.log](../changes.log) records local adaptations.

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
5. Read referenced guidance through the local support map. A reference to an
   library command or tool does not prove that executable is installed.
6. For Python-runtime artifacts, apply the additive
   [template contract](../.ai/runtime/TEMPLATE-CONTRACT.md) in the same artifact.
7. Check both content quality and the required runtime structure. Commit the
   record before the execution boundary that consumes it.

**Do not shorten the source templates, discard unfamiliar sections, silently
remove references, invent evidence, or use a completed heading as proof of a
completed outcome.** Conflicts require an explicit reasoned adaptation and a
`changes.log` entry during this migration.

## Complete template catalog

The tables account for all 40 files, including the canonical registry and JSON
configuration. Producer/consumer names below describe the supplied workflow
roles; consult the support map for local execution routes.

### Project identity and continuity — 9 files

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [README.md](../.ai/templates/README.md) | Canonical artifact registry | Template maintainers → agents locating fact owners |
| [project.md](../.ai/templates/project.md) | `.planning/PROJECT.md`: project identity and living context | Onboarding coordinator → every project/phase planning session |
| [requirements.md](../.ai/templates/requirements.md) | `.planning/REQUIREMENTS.md`: checkable outcomes and traceability | Coordinator → planner, checker and verifier |
| [roadmap.md](../.ai/templates/roadmap.md) | `.planning/ROADMAP.md`: phases, dependencies and milestone views | Coordinator → phase selection and progress tracking |
| [state.md](../.ai/templates/state.md) | `.planning/STATE.md`: living session memory | Coordinator/state updater → returning sessions |
| [config.json](../.ai/templates/config.json) | Library `.planning/config.json` settings | Library setup → library tools; Python runner uses YAML separately |
| [milestone.md](../.ai/templates/milestone.md) | Completed entry in `.planning/MILESTONES.md` | Milestone close procedure → future planning/history |
| [milestone-archive.md](../.ai/templates/milestone-archive.md) | Archive under `.planning/milestones/` | Milestone close procedure → historical review |
| [retrospective.md](../.ai/templates/retrospective.md) | Living milestone retrospective | Closing coordinator → future planning lessons |

The complete library registry describes library artifacts and library health
behavior. Local runtime configuration and current specifications/ADRs are
intentional local extensions, documented here and in the runtime/support route
maps. Do not assume an uninstalled library health command validates them.

### Phase definition, research and execution — 8 files

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [spec.md](../.ai/templates/spec.md) | `NN-SPEC.md`: locked desired requirements, boundaries, edge and negative coverage | Specification discussion → discuss/planner/verifier |
| [context.md](../.ai/templates/context.md) | `NN-CONTEXT.md`: implementation choices and applicable context | Discussion coordinator → researcher/planner; local authorization additions feed runner |
| [discussion-log.md](../.ai/templates/discussion-log.md) | `NN-DISCUSSION-LOG.md`: discussion audit trail | Discussion recorder → human audit; excluded from routine worker required reading |
| [research.md](../.ai/templates/research.md) | `NN-RESEARCH.md`: relevant ecosystem research | Phase researcher → planner and implementation workers |
| [phase-prompt.md](../.ai/templates/phase-prompt.md) | `NN-CC-PLAN.md`: executable task instructions | Planner → checker, scheduler and assigned worker |
| [planner-subagent-prompt.md](../.ai/templates/planner-subagent-prompt.md) | Context envelope for a fresh planning agent | Coordinator → planner; planning expertise resides in the referenced agent guidance |
| [VALIDATION.md](../.ai/templates/VALIDATION.md) | `NN-VALIDATION.md`: validation strategy and feedback coverage | Preparation/validation procedure → executor/verifier |
| [continue-here.md](../.ai/templates/continue-here.md) | Phase `.continue-here.md`: resumption context | Interrupted session → returning coordinator |

### Results and acceptance — 7 files

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [summary.md](../.ai/templates/summary.md) | Full `NN-CC-SUMMARY.md` guidance and skeleton | Component worker → integrator, dependents and verifier |
| [summary-standard.md](../.ai/templates/summary-standard.md) | Library standard summary variant | Library summary-selection flow → result readers |
| [summary-complex.md](../.ai/templates/summary-complex.md) | Library complex summary variant | Library summary-selection flow → result readers needing richer handoff |
| [summary-minimal.md](../.ai/templates/summary-minimal.md) | Library minimal summary variant | Library summary-selection flow → bounded result readers |
| [summary.compact.md](../.ai/templates/summary.compact.md) | Complete compact summary variant | Its referenced library flow → result readers |
| [verification-report.md](../.ai/templates/verification-report.md) | `NN-VERIFICATION.md`: independent goal evidence and findings | Verifier → coordinator and publication gate |
| [UAT.md](../.ai/templates/UAT.md) | `NN-UAT.md`: persistent acceptance session and gaps | Coordinator recording human observations → returning sessions and acceptance gate |

Every summary variant is retained as part of the complete template catalog. The Python
adapter currently instructs component workers to use the full `summary.md`
skeleton plus its local coverage/check fields. Retaining a compact library file
does not authorize replacing that contract or truncating the full template.

### Specialty contracts, debugging, setup and host preferences — 9 files

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [UI-SPEC.md](../.ai/templates/UI-SPEC.md) | Phase visual and interaction contract | UI research/check guidance → planner, implementer and UI review |
| [AI-SPEC.md](../.ai/templates/AI-SPEC.md) | Phase AI design and evaluation contract | AI integration guidance → planner/evaluation auditor |
| [SECURITY.md](../.ai/templates/SECURITY.md) | Phase threat register, accepted risks and audit trail | Security workflow → planner and security review |
| [DEBUG.md](../.ai/templates/DEBUG.md) | Active debug session; template names `.planning/debug/[slug].md` | Debugger → resumed investigation and repair verification |
| [user-setup.md](../.ai/templates/user-setup.md) | `NN-USER-SETUP.md`: setup requiring actual human action | Implementer/coordinator → user and continuation |
| [user-setup.compact.md](../.ai/templates/user-setup.compact.md) | Complete compact setup variant | Its library flow → user and continuation |
| [user-profile.md](../.ai/templates/user-profile.md) | Developer profile with stated evidence/confidence | Explicit profiling workflow → profile consumers |
| [dev-preferences.md](../.ai/templates/dev-preferences.md) | Generated preference directives | Profile workflow → compatible host session |
| [copilot-instructions.md](../.ai/templates/copilot-instructions.md) | Copilot-specific entry-point instructions | Host installation/adaptation → compatible Copilot session |

Specialty templates remain complete. Their named agents, commands, tools and
host integrations need the routes described in the support library; template
presence alone does not start profiling, security scanning, evaluation or a
Copilot feedback loop. Current user instructions govern authorization and
preferences. Never invent profile observations or treat sample risk acceptance
as an actual user decision.

### Codebase maps and project research — 7 files

| Template | Artifact or use | Producer → consumer |
|---|---|---|
| [codebase/architecture.md](../.ai/templates/codebase/architecture.md) | `.planning/codebase/ARCHITECTURE.md`: inspected conceptual organization | Reconnaissance → planner/researcher/worker |
| [codebase/stack.md](../.ai/templates/codebase/stack.md) | `.planning/codebase/STACK.md`: technologies actually executing | Reconnaissance → setup and implementation planning |
| [research-project/ARCHITECTURE.md](../.ai/templates/research-project/ARCHITECTURE.md) | `.planning/research/ARCHITECTURE.md`: domain architecture research | Project researcher → research synthesis and roadmap |
| [research-project/FEATURES.md](../.ai/templates/research-project/FEATURES.md) | `.planning/research/FEATURES.md`: domain feature landscape | Project researcher → requirements/roadmap discussion |
| [research-project/PITFALLS.md](../.ai/templates/research-project/PITFALLS.md) | `.planning/research/PITFALLS.md`: likely mistakes and prevention | Project researcher → planner/checker |
| [research-project/STACK.md](../.ai/templates/research-project/STACK.md) | `.planning/research/STACK.md`: source-backed technology recommendations | Project researcher → architecture and setup choices |
| [research-project/SUMMARY.md](../.ai/templates/research-project/SUMMARY.md) | `.planning/research/SUMMARY.md`: synthesis with roadmap implications | Research synthesizer → coordinator/planner |

Codebase maps describe inspected current code. Project research describes possible
approaches in the domain. Recommendations become constraints only through the
recorded decision process; neither category invents product requirements.

## Additional local templates

| Template | Output | Why it exists |
|---|---|---|
| [ADR.md](../.ai/templates/ADR.md) | `.planning/decisions/ADR-NNN-name.md` | Preserve significant rationale, alternatives, tradeoffs and supersession history |
| [CURRENT-SPEC.md](../.ai/templates/CURRENT-SPEC.md) | `.planning/specs/SPEC-NNN-capability.md` | Describe evidenced current behavior separately from desired phase requirements |

Both follow the teaching design of the library templates: complete output
skeleton, purpose, producer/consumer map, authoring steps, good/bad examples with
reasons, completion criteria and downstream handoff. Ordinary progress belongs
in SUMMARY and Git rather than a new architectural decision record.

## Connect a full template to the Python runtime

| Artifact | Local additions and interpretation |
|---|---|
| CONTEXT | Phase number, approval, phase dependencies and UAT setting; identified Acceptance and actual Authorization |
| PLAN | Kind, exclusive resources, phase acceptance mapping, documentation obligations and argv checks; explicit documentation handoff |
| SUMMARY | Acceptance/documentation coverage and actual check evidence alongside full template summary content |
| VERIFICATION | Exact assigned revision and local acceptance/integration/documentation/findings evidence; runtime attestation remains distinct from library metadata |
| UAT | Runtime source/case/history receipts alongside library session sections |

Use one YAML frontmatter block per artifact. Keep the template `requirements`,
`files_modified`, `files_deleted`, tasks, verification and must-have guidance.
Use a finer local `acceptance` mapping when phase acceptance IDs differ from the
requirements list. Exact details and examples belong to the
[template contract](../.ai/runtime/TEMPLATE-CONTRACT.md).

**Checkpoint boundary:** Non-autonomous plans and unresolved `user_setup` remain
valid planning records but block Python `run`. The coordinator handles the actual
checkpoint with the human, records the result and prepares an autonomous
continuation. Never remove a checkpoint simply to satisfy the runner.

**Parallelism boundary:** `depends_on` drives readiness after successful
integration and checks. `wave` is descriptive. Shared paths/resources still
serialize even if template `coupling_justified` explains a same-wave coupling.

**Configuration boundary:** `.planning/config.yaml` configures Python execution.
The complete JSON template remains available for its separate documented
consumer. No silent conversion connects these settings.

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
