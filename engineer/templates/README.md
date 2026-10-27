# GSD Canonical Artifact Registry

This directory contains the template files for every artifact that GSD workflows officially produce. The table below is the authoritative index: **if a `.planning/` root file is not listed here, `gsd-health` will flag it as W019** (unrecognized artifact).

Agents should query this file before treating a `.planning/` file as authoritative. If the file name does not appear below, it is not a canonical GSD artifact.

---

## `.planning/` Root Artifacts

These files live directly at `.planning/` — not inside phase subdirectories.

| File | Template | Produced by | Purpose |
|------|----------|-------------|---------|
| `PROJECT.md` | `project.md` | `/new-project` | Project identity, goals, requirements summary |
| `ROADMAP.md` | `roadmap.md` | `/new-milestone`, `/new-project` | Phase plan with milestones and progress tracking |
| `STATE.md` | `state.md` | `/new-project`, `/health --repair` | Current session state, active phase, last activity |
| `REQUIREMENTS.md` | `requirements.md` | `/new-milestone` | Functional requirements with traceability |
| `MILESTONES.md` | `milestone.md` | `/complete-milestone` | Log of completed milestones with accomplishments |
| `BACKLOG.md` | *(inline)* | `/capture --backlog` | Pending ideas and deferred work |
| `LEARNINGS.md` | *(inline)* | `/extract-learnings`, `/execute-phase` (gated: `features.global_learnings`) | Phase retrospective learnings for future plans |
| `THREADS.md` | *(inline)* | `/thread` | Persistent discussion threads |
| `config.json` | `config.json` | `/new-project`, `/health --repair` | Project-specific GSD configuration |
| `CLAUDE.md` | *(inline)* | `/gsd-profile` | Auto-assembled Claude Code context file |
| `RETROSPECTIVE.md` | *(inline)* | `/complete-milestone` | Living milestone retrospective updated at each milestone close |
| `WINDOWS.md` | *(none)* | broken-windows ledger (`src/broken-windows.cts`) | Tracked known-broken items pending resolution (#3224) |
| `STATE-ARCHIVE.md` | *(none)* | `state.cts`'s `cmdStatePrune` | Pruned historical STATE.md entries |
| `milestone.lock` | *(none)* | `src/milestone-lock.cts` | Persistent milestone (phase + session) claim, unlike the transient `STATE.md.lock`/`WAITING.json` (#3311) |
| `state.json` | *(none)* | `src/state-contract.cts` | Machine-readable state contract published at step boundaries (#3227) |
| `skill-manifest.json` | *(none)* | `init.cts`'s `cmdSkillManifest --write` | Project-scoped skill manifest (#3964) |
| `PATTERNS.md` | *(inline)* | `/extract-learnings` (graduation, `workflows/graduation.md`, `patterns` target) | Graduated cross-phase patterns -- distinct from the per-phase `NN-PATTERNS.md` below (#4282) |

### Version-stamped artifacts (pattern: `vX.Y-*.md`)

| Pattern | Produced by | Purpose |
|---------|-------------|---------|
| `vX.Y-MILESTONE-AUDIT.md` | `/audit-milestone` | Milestone audit report before archiving |

These files are archived to `.planning/milestones/` by `/complete-milestone`. Finding them at the `.planning/` root after completion indicates the archive step was skipped.

---

## Phase Subdirectory Artifacts (`.planning/phases/NN-name/`)

These files live inside a phase directory. They are NOT checked by W019 (which only inspects the `.planning/` root).

| File Pattern | Template | Produced by | Purpose |
|-------------|----------|-------------|---------|
| `NN-MM-PLAN.md` | `phase-prompt.md` | `/plan-phase` | Executable implementation plan |
| `NN-MM-SUMMARY.md` | `summary.md` | `/execute-phase` | Post-execution summary with learnings |
| `NN-CONTEXT.md` | `context.md` | `/discuss-phase` | Scoped discussion decisions for the phase |
| `NN-RESEARCH.md` | `research.md` | `/plan-phase`, `/plan-phase --research-phase <N>` | Technical research for the phase |
| `NN-VALIDATION.md` | `VALIDATION.md` | `/plan-phase` (Nyquist) | Validation architecture (Nyquist method) |
| `NN-UAT.md` | `UAT.md` | `/validate-phase` | User acceptance test results |
| `NN-PATTERNS.md` | *(inline)* | `/plan-phase` (pattern mapper) | Analog file mapping for the phase |
| `NN-UI-SPEC.md` | `UI-SPEC.md` | `/ui-phase` | UI design contract |
| `NN-SECURITY.md` | `SECURITY.md` | `/secure-phase` | Security threat model |
| `NN-AI-SPEC.md` | `AI-SPEC.md` | `/ai-integration-phase` | AI integration spec with eval strategy |
| `NN-DEBUG.md` | `DEBUG.md` | `/debug` | Debug session log |
| `NN-REVIEWS.md` | *(inline)* | `/review` | Cross-AI review feedback |

---

## Milestone Archive (`.planning/milestones/`)

Files archived by `/complete-milestone`. These are never checked by W019.

| File Pattern | Source |
|-------------|--------|
| `vX.Y-ROADMAP.md` | Snapshot of ROADMAP.md at milestone close |
| `vX.Y-REQUIREMENTS.md` | Snapshot of REQUIREMENTS.md at milestone close |
| `vX.Y-MILESTONE-AUDIT.md` | Moved from `.planning/` root |
| `vX.Y-phases/` | Archived phase directories (if `--archive-phases` used) |

---

## Adding a New Canonical Artifact

When a new workflow produces a `.planning/` root file:

1. Add the file name to `CANONICAL_EXACT` in `gsd-core/bin/lib/artifacts.cjs`
2. Add a row to the **`.planning/` Root Artifacts** table above
3. Add the template to `engineer/templates/` if one exists
