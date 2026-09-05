# AI Engineering Framework

A local-first Python framework for plan-driven engineering with isolated Git worktrees, durable repository memory, parallel agents, two independent higher-capability reviews, and autonomous replanning.

**Status: phase-one engineering foundation, version 0.1.0.dev0.** Architecture, schemas, review contracts, and the implementation backlog are present. The only executable CLI features are help and version. Agent execution, plan implementation, installation into other projects, and PR automation are designed but not implemented. No provider or remote repository is configured.

## Start here

1. Read [current state](.ai/STATE.json), [architecture](ARCHITECTURE.md), and [agent instructions](AGENTS.md).
2. Read [SPEC-001](.ai/specs/SPEC-001.md) and [PLAN-001](docs/plans/PLAN-001.md).
3. Read the [isolation review](docs/plans/PLAN-001-isolation-review.md) before starting a task.
4. Select a ready task from `.ai/tasks/`, reconcile Git, and create its dedicated worktree.

## Available now

Requires Python 3.11+ and Git. From the repository root:

```text
python -m pip install -e ".[dev]"
python -m ai_engineering --help
python -m ai_engineering --version
python scripts/validate_foundation.py
```

The validation command needs the declared `jsonschema` development dependency. PowerShell, Windows Command Prompt, and Linux shells use the same commands (use `py -3` in place of `python` if appropriate). No Bash automation is required.

## Target operator experience — not available yet

```text
python -m ai_engineering project init
python -m ai_engineering project adopt --dry-run
python -m ai_engineering plan implement PLAN-004
python -m ai_engineering run resume RUN-004
python -m ai_engineering state reconcile --dry-run
python -m ai_engineering framework upgrade --dry-run
```

The future `ai` command will be an optional equivalent entry point. Six major workflows cover project lifecycle, research/decision, planning, plan execution, delivery, and reconciliation. See [CLI design](docs/architecture/cli.md).

## What makes a run complete

An approved task graph is implemented in separate worktrees; all required validation and both task reviews pass on the same candidate; the combined plan passes integration review and CI. Completion and archival require observed merge evidence. An unmerged plan remains delivery-ready, never falsely completed.

## Navigation

- [Repository layout and ownership](docs/architecture/layout.md)
- [State and crash recovery](docs/state/persistence.md)
- [Workflow transitions](docs/state/transitions.md)
- [Agent contracts and model routing](docs/agents/contracts.md)
- [Review checklists](docs/workflows/reviews.md)
- [Recovery and replanning](docs/workflows/recovery.md)
- [Delivery roadmap](docs/plans/ROADMAP.md)
- [Schema catalog](docs/schemas/README.md)
- [Contribution guide](CONTRIBUTING.md) and [security policy](SECURITY.md)

Licensing and public distribution terms are not yet selected. Local design and development can proceed; no license grant is implied.
