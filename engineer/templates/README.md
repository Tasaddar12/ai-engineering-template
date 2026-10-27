# Canonical Artifact Registry

This directory contains the template files for every artifact that engineering workflows officially produce. The table below is the authoritative index: the registry describes artifact identity and producers; the Python runtime planning validator reports supported current schema findings.

Agents should query this file before treating a `.planning/` file as authoritative. If the file name does not appear below, it is not a canonical engineering artifact.

---

## `.planning/` Root Artifacts

These files live directly at `.planning/` — not inside phase subdirectories.

| File | Template | Produced by | Purpose |
|------|----------|-------------|---------|
| `PROJECT.md` | `project.md` | `/onboard` | Project identity, goals, requirements summary |
| `ROADMAP.md` | `roadmap.md` | `/onboard`, `/phase`, `/new-milestone` | Phase plan with milestones and progress tracking |
| `STATE.md` | `state.md` | `/onboard` and runtime session/phase operations | Current session state, active phase and derived position |
| `REQUIREMENTS.md` | `requirements.md` | `/onboard` | Functional requirements with traceability |
| `MILESTONES.md` | `milestone.md` | `/complete-milestone` | Log of completed milestones with accomplishments |
| `config.yaml` | `config.yaml` | `/onboard` and direct project configuration | Project-specific workflow configuration and verification commands |

There is no version-stamped milestone-audit producer in the retained command
catalog. Completed milestones are recorded through the `milestone.complete`
runtime operation and the `MILESTONES.md` template above.

---

## Phase Subdirectory Artifacts (`.planning/phases/NN-name/`)

These files live inside a phase directory and are inspected by the current runtime according to their artifact schema.

| File Pattern | Template | Produced by | Purpose |
|-------------|----------|-------------|---------|
| `NN-MM-PLAN.md` | `phase-prompt.md` | `/plan-phase` | Executable implementation plan |
| `NN-MM-SUMMARY.md` | `summary.md` | `/execute-phase` | Post-execution summary with learnings |
| `NN-CONTEXT.md` | `context.md` | `/discuss-phase` | Scoped discussion decisions for the phase |
| `NN-SPEC.md` | `spec.md` | `/spec-phase` | Approved phase behavior and acceptance contract |
| `NN-RESEARCH.md` | `research.md` | `/plan-phase --research` or planning coordinator | Technical research for the phase |
| `NN-VALIDATION.md` | `VALIDATION.md` | `/plan-phase` (Nyquist) | Validation architecture (Nyquist method) |
| `NN-UAT.md` | `UAT.md` | `/verify-work` and the coordinator | Human actions, observations and acceptance status |
| `NN-PATTERNS.md` | *(inline)* | `/plan-phase` (pattern mapper) | Analog file mapping for the phase |
| `NN-UI-SPEC.md` | `UI-SPEC.md` | `/ui-phase` | UI design contract |
| `NN-SECURITY.md` | `SECURITY.md` | `/secure-phase` | Security threat model |

---

## Milestone Archive (`.planning/milestones/`)

Files archived by `/complete-milestone`. Archive manifests preserve their source identities and evidence.

| File Pattern | Source |
|-------------|--------|
| `vX.Y-ROADMAP.md` | Snapshot of ROADMAP.md at milestone close |
| `vX.Y-REQUIREMENTS.md` | Snapshot of REQUIREMENTS.md at milestone close |
| `vX.Y-phases/` | Archived phase directories (if `--archive-phases` used) |

---

## Runtime-recognized frontmatter schemas

The runtime currently recognizes four artifact schemas for frontmatter checks:

| Schema | Filename suffix | Template | Required consumer contract |
|--------|-----------------|----------|----------------------------|
| `plan` | `-PLAN.md` | `phase-prompt.md` | Executable plan metadata, ownership and checks |
| `summary` | `-SUMMARY.md` | `summary.md` | Worker result, status and reconciled outcomes |
| `context` | `CONTEXT.md` | `context.md` | Discussion and issue references |
| `verification` | `-VERIFICATION.md` | `verification-report.md` | Verification status and covered-input identity |

Other rows in this registry are real workflow artifacts but do not imply a
runtime frontmatter schema. Their templates and workflows remain the authority
for required content.

## Adding a New Canonical Artifact

When a new workflow produces a `.planning/` artifact:

1. Identify the actual producer and every consumer from the workflow and runtime source. Confirm the artifact's path, naming rule, lifecycle and authoritative owner; do not infer these from an old registry row or a filename.
2. Decide whether runtime-owned structure or a gate needs a frontmatter schema. If so, add and document the schema with its real consumers. Otherwise, document the owning workflow and template without claiming parser support.
3. Add a row to the **`.planning/` Root Artifacts** table or the appropriate phase, milestone, additional-record or quick-record table. State the real producer and purpose, preserving the distinction between canonical tracked artifacts and optional authored records.
4. Add a complete template to `engineer/templates/` when authors need reusable fields, examples and consumer guidance. Update every workflow that reads or creates the artifact, then reconcile the table against those sources.

## Additional current records

| Path | Template | Producer | Purpose |
|------|----------|----------|---------|
| `NN-DISCUSSION-LOG.md` | `discussion-log.md` | discuss-phase | Incremental audit trail |
| `NN-REVIEW.md` | *(review report contract in `code-reviewer.md`)* | code-review / execute-phase | Fresh source review findings at a captured revision |
| `NN-REVIEW-DISPOSITION.md` | *(runtime disposition contract)* | execute-phase review-disposition | Durable disposition of review findings across review passes |
| `NN-UI-REVIEW.md` | *(returned report captured by coordinator)* | `/ui-review` or verify-work | Visual audit evidence and findings |
| `.continue-here.md` | `continue-here.md` | handoff | Continuation context |
| `.planning/specs/SPEC-*.md` | `CURRENT-SPEC.md` | spec-phase | Approved behavior contract |
| `.planning/decisions/ADR-*.md` | `ADR.md` | coordinator | Optional rationale linked from PROJECT Key Decisions |
| Canonical issue | `issue.md` | coordinator | Defect, threat, UAT and scope tracking |
| Draft pull request | `pull-request.md` | coordinator | Reviewable delivery and exact validation evidence |

## Quick records

| Path | Template | Producer | Purpose |
|------|----------|----------|---------|
| `.planning/quick/YYMMDD-NNN-slug/QUICK.md` | *(runtime-owned record)* | `quick.create` / `/quick` | Genuine bounded quick-task identity, scope and lifecycle |
| `.planning/quick/YYMMDD-NNN-slug/YYMMDD-NNN-slug-VERIFICATION.md` | `verification-report.md` adapted with quick identity | quick coordinator | Genuine quick evidence; quick identity, status, covered_files, fingerprint, revision and issue_refs |
| `.planning/quick/batches/{batch-id}.json` | *(runtime-owned manifest)* | `quick-batch.create` / `/quick-batch` | Batch task identities, dependencies and lifecycle state |

Quick verification uses --quick ID on status/resolve-file/fingerprint/current and ready/merge gates. Never invent a phase identifier.

## Runtime ownership and optional upstream artifacts

The registry preserves upstream artifact categories and the current project's complete templates. A registry row is not a claim that every upstream producer or optional artifact has a Python implementation. Use the retained command catalog and current runtime API before invoking a producer. In particular retired profile/intelligence/AI-integration artifacts do not grant new workflow or host integrations. Add or change a current parser schema together with its full template and consumers; never treat registry membership as behavioral verification.
