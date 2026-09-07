# Repository realignment report

Status: corrective implementation candidate; bootstrap behavior and repository structure validated, final product-document review pending. The future engine graph remains proposed and requires fresh isolation approval.

The repository now separates reusable product code from its own AI development records. Executable modules are flat under `src/`; internal plans, tasks, decisions, workflows, reviews, and evidence live under `.ai/`; provider entry guidance is limited to `.ai/AGENTS.md` and `.claude/CLAUDE.md` in installed projects.

## Migration map

| Previous | Current |
| --- | --- |
| `src/ai_engineering/` and `scripts/` entry points | `src/ai.py`, `src/install.py`, `src/validate_foundation.py` |
| Global `.ai/tasks`, `.ai/graphs`, `.ai/specs`, `.ai/reviews`, task commands | Plan-local directories under `.ai/plans/current/PLAN-001/` |
| Repository-development plans, decisions, reviews, state, and workflow design | `.ai/shared/`, `.ai/decisions/`, and the owning plan bundle |
| Reusable role lists and abstract install assets | Concrete product files in `docs/agents/`, `docs/templates/`, `docs/workflows/`, and `docs/defaults/` |
| Root `AGENTS.md` | `.ai/AGENTS.md` with explicit kickoff instruction |
| Sibling worktree directory | Repository-local `.worktrees/`, created only for active work and removed when empty |
| Approved foundation graph r2 | Immutable `history/foundation-r2/`; revised active graph r3 is proposed |

The installer now copies one complete docs-first payload into `.ai` for ChatGPT/Codex or `.claude` for Claude Code. Each namespace has its own entry instructions, first-run workflow, detailed role guides, record templates, default state/policy, helper tools, schemas, and validator dependency. It creates no root instruction file, no second workflow namespace, and no empty `.worktrees/` directory. Repeat installation preserves project-owned records and rejects changed framework-owned bytes.

The active structural task digest is `79f1137d5bfc5cb0a5148b4d0f3d67487d5a7ff43ab218ea00e04c3bad315883`. It includes task identity, title/objective, dependencies, scope, acceptance mappings, references, contracts, command IDs, size rationale, exclusions, and handoff requirements. It excludes lifecycle-only `status`, `archived`, `attempt_ids`, `superseded_by`, and `resume_state` fields. The current manual kit supports a reviewed task move from current to completed without a structural change. Whole-plan and archive relocation remain future work because current physical plan paths still occur in structural references.

Historical manifests use snapshot-root-relative paths and content hashes. The approved foundation r2 snapshot remains immutable history; its review does not apply to the active r3 graph. The rejected TASK-001 attempt remains only on branch `ai/PLAN-001/TASK-001/a1` at `f8a6f040fc48e8a237d412379322c5eed66d8cab`; its physical retained worktree was removed after clean retention checks.

## Validation

- `python -B -m unittest discover -s tests -v`: 13 tests passed on Python 3.13.14 with jsonschema 4.26.0. Coverage includes both standalone provider namespaces, fresh and populated destinations, dry-run, idempotence, conflict rejection, Git checkout persistence, multiple plans with plan-local task IDs, installed subprocess execution, write-failure rollback, Windows path rejection, record references, and discovery pruning.
- `python -B src/validate_foundation.py`: passed with 26 schemas, 119 validated artifacts, 39 tasks, 280 unordered task pairs, 3 archive manifests, and 120 local Markdown links.

No prior failed or interrupted review is represented as a pass. Final corrective review evidence is recorded separately from this implementation report.
