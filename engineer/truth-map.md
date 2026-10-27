# Fact ownership map

Each fact has one owner; consumers link to it. Resolve disagreement with approved intent and observed behavior, then repair the owning fact and affected references.

| Fact | Owner | Consumer / boundary |
|------|-------|---------------------|
| Project identity, intent, constraints | .planning/PROJECT.md narrative | Onboard; leave unfilled in reusable template |
| Consequential decision | PROJECT Key Decisions via state.add-decision | Phase CONTEXT and implementation |
| Significant rationale | PROJECT Key Decisions; optional linked .planning/decisions/ADR-*.md | ADR is rationale only |
| Requirement wording | .planning/REQUIREMENTS.md | Approved scope and acceptance |
| Requirement traceability | Runtime requirements operations | Roadmap, verification and progress |
| Phase numbering/scope/progress | Runtime ROADMAP operations | Discuss/plan/execute/complete |
| Session position and continuity | Runtime STATE operations | Every selected workflow |
| Phase decisions/authority | NN-CONTEXT.md | Planner/executor; actual user instruction required |
| Discussion alternatives/answers | NN-DISCUSSION-LOG.md | Audit reconstruction; not replacement implementation input |
| Executable plan contract | NN-MM-PLAN.md | Exact ownership, dependencies, acceptance/docs/checks/issues |
| Delivered outcomes/evidence | NN-MM-SUMMARY.md | Coordinator/verifier |
| Verification verdict/currentness | NN-VERIFICATION.md and valid runtime evidence | Ready/ship gates |
| Actual human acceptance | NN-UAT.md Human acceptance and actual responses | Completion; never inferred |
| Canonical issue/provider state | Read-back provider tracker and independent audit | Source references; no fabricated anchors |
| Security planned assessment/mitigation | Each PLAN six-column threat register | Canonical checklist entry links to PLAN |
| Optional reusable specification | .planning/specs/SPEC-*.md | Approved observable contract |
| Shared authority and gates | engineer/RULES.md | Every command/workflow/role |
| Role ownership/return contract | agents/ and agents/README.md | Host dispatch |
| User-facing entry and procedure name | commands/ | Skill mirrors and user |
| Step ordering and routing | engineer/workflows/ | Commands and coordinator |
| Reusable method | engineer/references/ | Consuming role/workflow |
| Complete artifact schema | engineer/templates/ and registry README | Producer and consumer/runtime |
| Configuration schema/defaults | engineer/templates/config.yaml and runtime config owner | .planning/config.yaml overrides |
| Actual runtime CLI and result shape | engineer/bin/README.md and implementation | engineer_run query callers |
| Installed host adaptation | bin/install-assets, installer and native Claude/Codex files | Only supported two hosts |
| Human workflow guidance | docs/ | Links to authoritative procedure, not duplicate owner |
| Historical provenance/license | THIRD-PARTY-NOTICES.md and Git import | No invented upstream snapshot pin |

The Python runtime owns structured planning mutations. Narrative and rationale are authored in their owner. `planning.validate` reports drift; a warn-only report is not permission to silently rewrite scope.
