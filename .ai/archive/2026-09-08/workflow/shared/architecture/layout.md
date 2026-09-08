# Repository layouts and ownership

## Toolkit source repository

| Path | Purpose |
| --- | --- |
| `src/*.py` | Directly runnable CLI, installer, validator, and future flat runtime modules |
| `schemas/v1/` | Canonical JSON Schema wire contracts |
| `docs/agents/` | Canonical reusable index and individual workflow role guides |
| `docs/templates/` | Copyable record templates installed into other projects |
| `docs/workflows/` | Reusable focused workflow guidance installed into other projects |
| `docs/defaults/` | Clean initial state, policy, entry, and installation defaults |
| `.ai/shared/` | This repository's internal architecture and workflow design |
| `.ai/plans/` | This repository's plan-local tasks, commands, reviews, evidence, and history |
| `tests/` | Executable behavior and failure tests |
| `pyproject.toml` | Flat-module package metadata |

## Installed project

```text
.codex/
  STATE.json  framework.json  requirements.txt
  AGENTS.md                         explicit Codex/ChatGPT entry guidance
  agents/                           reusable index and individual role guides copied from `docs/agents/`
  project/{policy.json,agent-models.json}
  decisions/  research/  templates/  workflows/
  framework/{manifest.json,schemas/v1/}
  tools/{ai.py,validate_foundation.py}
  plans/
    current/PLAN-NNN/
      plan.json  plan.md  spec.json  spec.md  graph.json
      tasks/{current,completed,archived}/
      commands/  reviews/  evidence/  history/
    completed/
    archived/
  local/                            ignored host-local state
.worktrees/                         active linked Git worktrees only
```

Every plan is a self-contained namespace. Task IDs, command IDs, reviews, evidence, and references resolve through `(plan_id, local_id)`, so separate plans may each own `TASK-001`. Plan specification, graph, task, command, review, and evidence references must stay within the plan bundle. Project policy, decisions, research, schemas, and reusable operating guidance are shared.

Lifecycle directories make current, completed, and archived work immediately visible; explicit status and archived fields must agree with location. The bootstrap only reserves these directories. TASK-009 must implement transactional relocation before TASK-030 exposes completion/archive behavior. Historical snapshots stay in the owning plan's `history/` with content hashes. Generated views remain nonauthoritative.

Actual linked worktrees use `.worktrees/<plan>/<task-attempt>` beneath the repository base. Host-specific absolute paths and process IDs remain untracked under the selected namespace's `local/` directory (`.ai/local/` in this source repository). Remove clean merged worktrees through Git, retain failed or unmerged commits through branches, and remove `.worktrees/` when empty.

The installer creates exactly one self-contained `.codex` namespace for OpenAI or `.claude` for Claude. Source and legacy `.ai` records remain readable; the installer refuses implicit migration or a second managed namespace. Native provider settings can coexist and are preserved. Framework-owned installed assets have manifest hashes. Project-owned state and instructions are preserved on repeat installation; conflicting managed assets fail instead of being overwritten.
