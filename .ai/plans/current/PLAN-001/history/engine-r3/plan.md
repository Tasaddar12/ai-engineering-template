# PLAN-001 — Local deterministic workflow engine

Status: isolation. Graph revision 3 is proposed after repository realignment and has no current isolation approval. Do not resume implementation until a fresh independent isolation review passes against the exact graph and structural task digest.

The working `src/install.py`, `src/ai.py`, and `src/validate_foundation.py` files are corrective bootstrap tools. They install reusable guidance, create plan/task records, and validate them. The autonomous execution, review, recovery, delivery, and completion engine in this plan remains unimplemented.

## Completed foundation to preserve

The original repository correction is integrated. Its 13 passing tests, independent Astra code/documentation reviews, and cleanup are recorded in [review evidence](evidence/repository-realignment-reviews.md). The subsequent provider namespace and agent model correction is tracked in [current correction evidence](evidence/provider-namespace-model-defaults.md). The following bootstrap behavior is the starting point for this plan:

| Area | Required existing behavior |
| --- | --- |
| Reusable product files | Real source files live in `docs/agents/`, `docs/templates/`, `docs/workflows/`, and `docs/defaults/`, including `planner.md` and `PLAN.md`. |
| Fresh installation | An empty target needs no existing AI folder. The installer creates a self-contained `.codex/` for OpenAI or `.claude/` for Claude, with role guides, templates, workflows, tools, schemas, and empty records. Preserve existing project files, native provider settings, dry-run behavior, repeat installation, and failure recovery. Existing `.ai/` records remain readable but are not automatically migrated or duplicated. |
| Repository boundaries | Scripts stay directly under `src/`. This toolkit's own plans, tasks, decisions, reviews, and development history remain under its existing `.ai/`; provider installations use `.codex/` or `.claude/`. Development records are never copied into a fresh installation. |
| Multiple plans and context | Each plan owns its tasks, commands, reviews, evidence, and history. Current, completed, and archived folders are separate. Load the selected role, plan/task, and explicit references; keep unrelated and archived material out of default context. |
| Agent models | Every role has editable OpenAI and Anthropic defaults, with higher tiers for planning/reviews and lower-cost research/development. Install `project/agent-models.json`, prefill unverified policy profiles, preserve overrides, and record actual model/effort at each gate. Defaults do not implement automatic dispatch or prove model access. |
| Worktree cleanup | Active worktrees belong under the repository's `.worktrees/`. Remove clean merged worktrees through Git and remove the container when empty; preserve unaccepted work through branches or commits. |

TASK-031 extends the existing installer with coordinated initialization/adoption, TASK-034 extends the working record CLI, and TASK-037 packages the complete runtime and document payload. Their remaining work does not require rebuilding the delivered bootstrap. TASK-004, TASK-009, TASK-030, and TASK-036 cover the logical references, transitions, provenance, and verification still needed for whole-plan completion and archival. The current kit supports only the documented bounded manual task-completion move.

The 39 task records below describe remaining engine work; the separate completed correction does not mark those tasks accepted or grant graph isolation approval.

## Canonical bundle

- [Specification](spec.md) and [machine specification](spec.json)
- [Machine plan](plan.json) and [proposed graph r3](graph.json)
- `tasks/current/` for all 39 unimplemented task records
- `commands/` for this plan's future task validation definitions
- `reviews/` for current candidate reviews; empty until graph r3 is reviewed
- `evidence/` for corrective and future task evidence
- `history/` for immutable superseded foundation snapshots and reports

## Tasks

| Task | Outcome | Dependencies |
| --- | --- | --- |
| [TASK-001](tasks/current/TASK-001.json) | Immutable domain values | None |
| [TASK-002](tasks/current/TASK-002.json) | Local persistence/process ports | TASK-001, TASK-004 |
| [TASK-003](tasks/current/TASK-003.json) | Agent/workflow service ports | TASK-001 |
| [TASK-004](tasks/current/TASK-004.json) | Offline contract validation | TASK-001 |
| [TASK-005](tasks/current/TASK-005.json) | Owned asset catalog | TASK-004 |
| [TASK-006](tasks/current/TASK-006.json) | Command execution evidence | TASK-002, TASK-004, TASK-038 |
| [TASK-007](tasks/current/TASK-007.json) | Observed Git operations | TASK-002, TASK-006 |
| [TASK-008](tasks/current/TASK-008.json) | Guarded transitions | TASK-001, TASK-004 |
| [TASK-009](tasks/current/TASK-009.json) | Serialized state checkpoints and lifecycle relocation | TASK-002, TASK-004, TASK-007, TASK-008 |
| [TASK-010](tasks/current/TASK-010.json) | Interrupted-effect reconciliation | TASK-009 |
| [TASK-011](tasks/current/TASK-011.json) | Worktree lifecycle | TASK-007, TASK-010 |
| [TASK-012](tasks/current/TASK-012.json) | Worktree reconciliation | TASK-011 |
| [TASK-013](tasks/current/TASK-013.json) | Dependency graph | TASK-001, TASK-004 |
| [TASK-014](tasks/current/TASK-014.json) | Scope conflict detection | TASK-001, TASK-004 |
| [TASK-015](tasks/current/TASK-015.json) | Isolation review gate | TASK-003, TASK-013, TASK-014, TASK-017, TASK-039 |
| [TASK-016](tasks/current/TASK-016.json) | Context bundles | TASK-003, TASK-004, TASK-038 |
| [TASK-017](tasks/current/TASK-017.json) | Agent contract and fake adapter | TASK-003, TASK-004, TASK-038 |
| [TASK-018](tasks/current/TASK-018.json) | Validation suites | TASK-003, TASK-006 |
| [TASK-019](tasks/current/TASK-019.json) | Candidate fingerprints | TASK-001, TASK-004 |
| [TASK-020](tasks/current/TASK-020.json) | Independent review gates | TASK-003, TASK-017, TASK-018, TASK-019, TASK-038 |
| [TASK-021](tasks/current/TASK-021.json) | Fenced task dispatch | TASK-010, TASK-011, TASK-016, TASK-017, TASK-039 |
| [TASK-022](tasks/current/TASK-022.json) | Parallel scheduling | TASK-013, TASK-014, TASK-021, TASK-039 |
| [TASK-023](tasks/current/TASK-023.json) | Candidate integration | TASK-007, TASK-011, TASK-018, TASK-020, TASK-039 |
| [TASK-024](tasks/current/TASK-024.json) | Recovery proposal validation | TASK-013, TASK-014, TASK-039 |
| [TASK-025](tasks/current/TASK-025.json) | Recovery application | TASK-010, TASK-015, TASK-021, TASK-024, TASK-039 |
| [TASK-026](tasks/current/TASK-026.json) | Resumable execution steps | TASK-012, TASK-015, TASK-018, TASK-020, TASK-022, TASK-023, TASK-025, TASK-039 |
| [TASK-027](tasks/current/TASK-027.json) | Combined plan gate | TASK-018, TASK-019, TASK-020, TASK-025, TASK-026, TASK-039 |
| [TASK-028](tasks/current/TASK-028.json) | Delivery intent and fake hosting | TASK-003, TASK-010 |
| [TASK-029](tasks/current/TASK-029.json) | CI and remote repair handling | TASK-025, TASK-027, TASK-028, TASK-039 |
| [TASK-030](tasks/current/TASK-030.json) | Completion reconciliation and archive provenance | TASK-004, TASK-009, TASK-012, TASK-029, TASK-039 |
| [TASK-031](tasks/current/TASK-031.json) | Coordinated project init/adopt built on bootstrap installer | TASK-005, TASK-009, TASK-038 |
| [TASK-032](tasks/current/TASK-032.json) | Owned asset upgrades | TASK-005, TASK-009, TASK-011, TASK-031 |
| [TASK-033](tasks/current/TASK-033.json) | Research/decision/plan persistence | TASK-004, TASK-009, TASK-013 |
| [TASK-034](tasks/current/TASK-034.json) | Full CLI workflows preserving bootstrap commands | TASK-026, TASK-027, TASK-030, TASK-031, TASK-032, TASK-033, TASK-039 |
| [TASK-035](tasks/current/TASK-035.json) | Parallel/resume verification | TASK-034 |
| [TASK-036](tasks/current/TASK-036.json) | Recovery/delivery/lifecycle verification | TASK-004, TASK-009, TASK-030, TASK-034 |
| [TASK-037](tasks/current/TASK-037.json) | Flat-module packaging and platform CI | TASK-035, TASK-036 |
| [TASK-038](tasks/current/TASK-038.json) | Project settings decoding | TASK-004 |
| [TASK-039](tasks/current/TASK-039.json) | Orchestration service contracts | TASK-003 |

All tasks are backlog. TASK-001's earlier implementation attempt is retained only through Git branch `ai/PLAN-001/TASK-001/a1` at commit `f8a6f040fc48e8a237d412379322c5eed66d8cab`; it is interrupted, unaccepted, and incompatible with the flat source layout. See [attempt evidence](evidence/TASK-001-a1.md).
