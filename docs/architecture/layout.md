# Repository layouts and ownership

## Central framework repository

| Path | Owner / purpose |
| --- | --- |
| `src/ai_engineering/` | Python package; CLI, domain services, ports and adapters |
| `schemas/v1/` | Canonical JSON Schema wire contracts shipped in package |
| `templates/` | Installable framework assets and seed-only project examples |
| `docs/` | Framework architecture, workflows, checklists and implementation design |
| `.ai/` | This framework's own project records, exercising the installed conventions |
| `tests/` | Future behavior tests separated by task/component |
| `scripts/validate_foundation.py` | Phase-one artifact integrity check |
| `pyproject.toml` | Single-owner package metadata |

`docs/plans/PLAN-001.md` is the human guide; `.ai/plans/PLAN-001.json` is machine intent and references that guide. Neither duplicates executable task definitions: `.ai/tasks/` is canonical for those.

## Installed project

| Path | Ownership and behavior |
| --- | --- |
| `.ai/STATE.json` | Project-owned current summary and entity references |
| `.ai/framework.json` | Version, schema compatibility and install-manifest reference |
| `.ai/framework/` | Framework-owned schemas, role rules, checklists, templates; hash manifest |
| `.ai/project/` | Project-owned commands, model bindings, autonomy policy and conventions |
| `.ai/specs/`, `.ai/plans/`, `.ai/tasks/` | Stable IDs, explicit statuses |
| `.ai/research/`, `.ai/decisions/` | Sourced findings and ADRs |
| `.ai/worktrees/` | Portable worktree records, not checked-out source directories |
| `.ai/reviews/{implementation,consistency,integration,isolation}/` | Immutable, revision-bound reviews |
| `.ai/handoffs/`, `.ai/runs/`, `.ai/agents/` | Structured results and checkpoints |
| `.ai/context/`, `.ai/graphs/`, `.ai/recovery/` | Hashed context manifests, graph revisions and rewrite decisions |
| `.ai/archive/` | Historical manifests; no deletion of referenced evidence |
| `.ai/prs/` | Remote delivery intent and observed status |

Actual linked worktrees default to a configurable sibling directory `../<repo>-ai-worktrees/<short-run>/<short-task>`. This avoids recursive Git checkouts, long Windows paths, and tracking code copies. Host-specific absolute paths and process IDs live in `<git-common-dir>/ai-engineering/local/`; portable records use logical IDs and relative location hints.

Generated indexes and status views are rebuildable and nonauthoritative. No `.agent-state/` mirror is introduced; adoption may import older state with provenance and an explicit migration record. Existing AGENTS.md is project-owned: insert a bounded managed pointer only through a reviewed three-way merge, never overwrite it.

Schemas use `.json` intentionally: standard-library parsing, unambiguous types, and no YAML tags. Markdown is for narrative. YAML input can be a future import adapter; do not create competing authoritative representations.
