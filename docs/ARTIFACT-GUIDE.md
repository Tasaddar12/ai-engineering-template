# Artifact guide

Read the complete [template-use contract](../engineer/templates/TEMPLATE.md) and [registry](../engineer/templates/README.md) before authoring. Templates preserve full fields, methods, examples and producer/consumer guidance; do not replace them with a compact synopsis.

## Project records

| Artifact | Owns | Mutation boundary |
|----------|------|-------------------|
| PROJECT narrative | Identity, intent, constraints | Onboard / approved authored changes |
| PROJECT Key Decisions | Consequential decisions | state.add-decision while deciding |
| REQUIREMENTS wording | Approved observable obligations | Authored scope; no silent changes |
| REQUIREMENTS Traceability | Requirement-phase/status relationships | Runtime operations |
| ROADMAP | Phase numbering, scope and progress | Runtime operations |
| STATE | Position, continuity and active blockers | Runtime operations; closed section set |
| MILESTONES | Audited shipped outcomes | Milestone runtime/coordinator |
| config.yaml | Actual project configuration | Supported runtime YAML operations |

## Phase records

| Artifact | Producer | Consumer / evidence |
|----------|----------|---------------------|
| NN-CONTEXT.md | Discussion coordinator | Locked choices and actual implementation authority |
| NN-DISCUSSION-LOG.md | Discussion coordinator | Incremental audit and recommendation checks |
| NN-RESEARCH.md | phase-researcher | Manifest, source and primary documentation evidence |
| NN-MM-PLAN.md | planner | Ownership, dependencies, acceptance, docs, checks argv, issues |
| NN-MM-SUMMARY.md | executor | Actual requirements, commits, checks, threats, Remaining |
| NN-VALIDATION.md | Assigned planner/auditor | Test architecture and 2-in-3 sampling |
| NN-VERIFICATION.md | Coordinator from verifier packets | Frozen verdict and v4 digest |
| NN-UAT.md | Coordinator and human | Actions, actual results and final human acceptance |
| NN-SECURITY.md | Coordinator from auditor | Mitigation evidence and risk lifecycle |
| NN-UI-SPEC.md | ui-researcher/coordinator | Approved visual/interaction contract |

A quick task has its own record and .planning/quick/NNN-slug/NNN-VERIFICATION.md with quick: NNN. Do not fabricate a phase ID for verification/publication gates.

## Specifications and rationale

Use CURRENT-SPEC for .planning/specs/SPEC-*.md when required. An approved specification does not grant implementation authority. PROJECT Key Decisions owns the choice; .planning/decisions/ADR-*.md provides optional linked rationale. Preserve history in Git and Key Decisions.

## Issues and pull requests

Read the complete templates and [Git workflow](../engineer/references/git-workflow.md). Source identity, provider readback, semantic scope and safe content matter beyond headings. Planned risks retain each PLAN's six-column register and use the deterministic checklist or canonical full-scope tracker; distinct unplanned risks need standalone tracking. Fresh independent issue-link audit precedes readiness.

## Completion and repair

A SUMMARY reports delivered evidence rather than automatically completing planned requirements. Verification does not pass human acceptance by inspection. resolved_by requires an executed plan with matching SUMMARY and does not fabricate acceptance.

Use planning.review, planning.repair with its current digest, and explicit-path archive operations. Do not strike through history or hand-edit runtime tables. Read [phase artifacts](../engineer/references/phase-artifacts.md) for producer/consumer boundaries.
