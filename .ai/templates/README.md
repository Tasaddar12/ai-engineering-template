# Workflow Canonical Artifact Registry

This directory contains the template files for every artifact that Workflow workflows officially produce. The table below is the authoritative index: **if a `.planning/` root file is not listed here, `workflow-health` will flag it as W019** (unrecognized artifact).

Agents should query this file before treating a `.planning/` file as authoritative. If the file name does not appear below, it is not a canonical Workflow artifact.

---

## `.planning/` Root Artifacts

These files live directly at `.planning/` — not inside phase subdirectories.

| File | Template | Produced by | Purpose |
|------|----------|-------------|---------|
| `PROJECT.md` | `project.md` | `/workflow:new-project` | Project identity, goals, requirements summary |
| `ROADMAP.md` | `roadmap.md` | `/workflow:new-milestone`, `/workflow:new-project` | Phase plan with milestones and progress tracking |
| `STATE.md` | `state.md` | `/workflow:new-project`, `/workflow:health --repair` | Current session state, active phase, last activity |
| `REQUIREMENTS.md` | `requirements.md` | `/workflow:new-milestone` | Functional requirements with traceability |
| `MILESTONES.md` | `milestone.md` | `/workflow:complete-milestone` | Log of completed milestones with accomplishments |
| `BACKLOG.md` | *(inline)* | `/workflow-add-backlog` | Pending ideas and deferred work |
| `LEARNINGS.md` | *(inline)* | `/workflow:extract-learnings`, `/workflow:execute-phase` (gated: `features.global_learnings`) | Phase retrospective learnings for future plans |
| `THREADS.md` | *(inline)* | `/workflow:thread` | Persistent discussion threads |
| `config.json` | `config.json` | `/workflow:new-project`, `/workflow:health --repair` | Project-specific Workflow configuration |
| `CLAUDE.md` | *(inline)* | `/workflow-profile` | Auto-assembled Claude Code context file |
| `RETROSPECTIVE.md` | *(inline)* | `/workflow:complete-milestone` | Living milestone retrospective updated at each milestone close |
| `WINDOWS.md` | *(none)* | broken-windows ledger (`.ai/library/SOURCES.md#source-f65d25ed51045404`) | Tracked known-broken items pending resolution (#3224) |
| `STATE-ARCHIVE.md` | *(none)* | `.ai/library/SOURCES.md#source-07e94caf648b696e`'s `cmdStatePrune` | Pruned historical STATE.md entries |
| `milestone.lock` | *(none)* | `.ai/library/SOURCES.md#source-fd94de8f36787b63` | Persistent milestone (phase + session) claim, unlike the transient `STATE.md.lock`/`WAITING.json` (#3311) |
| `state.json` | *(none)* | `.ai/library/SOURCES.md#source-6e351bb6c65afe7b` | Machine-readable state contract published at step boundaries (#3227) |
| `skill-manifest.json` | *(none)* | `.ai/library/SOURCES.md#source-54d829576bcb08ec`'s `cmdSkillManifest --write` | Project-scoped skill manifest (#3964) |
| `PATTERNS.md` | *(inline)* | `/workflow:extract-learnings` (graduation, `.ai/library/workflows/graduation.md`, `patterns` target) | Graduated cross-phase patterns -- distinct from the per-phase `NN-PATTERNS.md` below (#4282) |

### Version-stamped artifacts (pattern: `vX.Y-*.md`)

| Pattern | Produced by | Purpose |
|---------|-------------|---------|
| `vX.Y-MILESTONE-AUDIT.md` | `/workflow:audit-milestone` | Milestone audit report before archiving |

These files are archived to `.planning/milestones/` by `/workflow:complete-milestone`. Finding them at the `.planning/` root after completion indicates the archive step was skipped.

---

## Phase Subdirectory Artifacts (`.planning/phases/NN-name/`)

These files live inside a phase directory. They are NOT checked by W019 (which only inspects the `.planning/` root).

| File Pattern | Template | Produced by | Purpose |
|-------------|----------|-------------|---------|
| `NN-MM-PLAN.md` | `phase-prompt.md` | `/workflow:plan-phase` | Executable implementation plan |
| `NN-MM-SUMMARY.md` | `summary.md` | `/workflow:execute-phase` | Post-execution summary with learnings |
| `NN-CONTEXT.md` | `context.md` | `/workflow:discuss-phase` | Scoped discussion decisions for the phase |
| `NN-RESEARCH.md` | `research.md` | `/workflow:plan-phase`, `/workflow:plan-phase --research-phase <N>` | Technical research for the phase |
| `NN-VALIDATION.md` | `VALIDATION.md` | `/workflow:plan-phase` (Nyquist) | Validation architecture (Nyquist method) |
| `NN-UAT.md` | `UAT.md` | `/workflow:validate-phase` | User acceptance test results |
| `NN-PATTERNS.md` | *(inline)* | `/workflow:plan-phase` (pattern mapper) | Analog file mapping for the phase |
| `NN-UI-SPEC.md` | `UI-SPEC.md` | `/workflow:ui-phase` | UI design contract |
| `NN-SECURITY.md` | `SECURITY.md` | `/workflow:secure-phase` | Security threat model |
| `NN-AI-SPEC.md` | `AI-SPEC.md` | `/workflow:ai-integration-phase` | AI integration spec with eval strategy |
| `NN-DEBUG.md` | `DEBUG.md` | `/workflow:debug` | Debug session log |
| `NN-REVIEWS.md` | *(inline)* | `/workflow:review` | Cross-AI review feedback |

---

## Milestone Archive (`.planning/milestones/`)

Files archived by `/workflow:complete-milestone`. These are never checked by W019.

| File Pattern | Source |
|-------------|--------|
| `vX.Y-ROADMAP.md` | Snapshot of ROADMAP.md at milestone close |
| `vX.Y-REQUIREMENTS.md` | Snapshot of REQUIREMENTS.md at milestone close |
| `vX.Y-MILESTONE-AUDIT.md` | Moved from `.planning/` root |
| `vX.Y-phases/` | Archived phase directories (if `--archive-phases` used) |

---

## Adding a New Canonical Artifact

When a new workflow produces a `.planning/` root file:

1. Add the file name to `CANONICAL_EXACT` in `.ai/library/SOURCES.md#source-f061ca1d64623747`
2. Add a row to the **`.planning/` Root Artifacts** table above
3. Add the template to `.ai/templates/` if one exists


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
