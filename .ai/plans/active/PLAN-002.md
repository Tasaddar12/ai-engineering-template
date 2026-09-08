---
id: PLAN-002
title: Streamlined autonomous Python engineering framework
status: in-progress
tasks:
- TASK-040
- TASK-041
- TASK-042
- TASK-043
- TASK-044
- TASK-045
- TASK-046
- TASK-047
- TASK-048
- TASK-049
- TASK-050
- TASK-051
- TASK-052
- TASK-053
- TASK-054
- TASK-055
- TASK-056
- TASK-057
- TASK-058
- TASK-059
- TASK-060
- TASK-061
- TASK-062
context:
- ARCHITECTURE.md
- docs/workflows.md
- .ai/decisions/ADR-006.md
acceptance:
- Fresh YAML state excludes PLAN-001 and preserves historical evidence.
- Approved decomposition covers every fresh task in bounded conflict-safe batches.
- Package CLI drives real Git feature worktrees, configured agent providers, validation,
  one critical review and bounded repair/recovery.
- Lightweight bugs, templates, independent model profiles and enforced constraints
  are supported.
- Local tests demonstrate concurrency, recovery, state reconciliation, delivery gates
  and safe installation/cleanup.
scope:
- src/ai_engineering
- tests
- docs
- .ai
- README.md
- ARCHITECTURE.md
- SECURITY.md
- CONTRIBUTING.md
- pyproject.toml
- .github
features:
- FEATURE-001
- FEATURE-002
- FEATURE-003
- FEATURE-004
- FEATURE-005
- FEATURE-006
- FEATURE-007
decomposition: .ai/handoffs/PLAN-002-decomposition.md
decomposition_status: approved
kind: plans
---
# PLAN-002 — Streamlined autonomous Python engineering framework

Authority: 2026-09-08 user reset. PLAN-001 is superseded in full. Build a coherent package around readable state, task-to-feature batching, constrained execution, independent critical review and automatic structural recovery. Preserve useful algorithms and evidence without importing obsolete task-engine contracts.

## Execution sequence

Core artifacts/configuration → commands/worktrees and planning in parallel → agents/review → orchestration → bugfix/recovery → CLI/installation/acceptance. Decomposition may revise this proposed sequence before implementation. Public Python boundaries are in `.ai/plans/active/PLAN-002.md`.

## External boundary

Local commits and reversible work are authorized. This plan does not authorize remote publishing, paid providers or credential use. Implement and test provider/PR integrations with controlled adapters; real execution requires configured authority. Leave unmerged delivery state honest.

## Validation

Behavioral tests in temporary Git repositories, lint, formatting, public typing, wheel asset/install smoke test, and one independent Critical Change Review of the full change. Record real results and platform limitations.

## Approved implementation graph

Planning location is a hard requirement: this PLAN document and all task, feature and plan-specific contract artifacts live under `.ai/`. Product documentation links here and must not contain the plan's implementation task lists, contracts or feature graph.

The Work Decomposition Agent approved exact coverage of 23 tasks in seven batches. See [decomposition evidence](../../handoffs/PLAN-002-decomposition.md). `ready` means a validated batch; launch still waits for dependencies and available code.

| Feature | Tasks | Prerequisites | Effort |
| --- | --- | --- | --- |
| [FEATURE-001](../../features/ready/FEATURE-001.md) — Artifact, configuration and state foundation | [TASK-040](../../tasks/ready/TASK-040.md), [TASK-041](../../tasks/ready/TASK-041.md), [TASK-042](../../tasks/ready/TASK-042.md) | None | 7 |
| [FEATURE-002](../../features/ready/FEATURE-002.md) — Constrained commands and managed Git worktrees | [TASK-043](../../tasks/ready/TASK-043.md), [TASK-044](../../tasks/ready/TASK-044.md), [TASK-045](../../tasks/ready/TASK-045.md) | FEATURE-001 | 8 |
| [FEATURE-003](../../features/ready/FEATURE-003.md) — Validated task decomposition and feature graphs | [TASK-046](../../tasks/ready/TASK-046.md), [TASK-047](../../tasks/ready/TASK-047.md), [TASK-048](../../tasks/ready/TASK-048.md) | FEATURE-001 | 8 |
| [FEATURE-004](../../features/ready/FEATURE-004.md) — Configured agents, durable handoffs and critical review | [TASK-049](../../tasks/ready/TASK-049.md), [TASK-050](../../tasks/ready/TASK-050.md), [TASK-051](../../tasks/ready/TASK-051.md) | FEATURE-002 | 8 |
| [FEATURE-005](../../features/ready/FEATURE-005.md) — Concurrent implementation, repair and delivery | [TASK-052](../../tasks/ready/TASK-052.md), [TASK-053](../../tasks/ready/TASK-053.md), [TASK-054](../../tasks/ready/TASK-054.md), [TASK-055](../../tasks/ready/TASK-055.md) | FEATURE-003, FEATURE-004 | 8 |
| [FEATURE-006](../../features/ready/FEATURE-006.md) — Lightweight bugfix and structural recovery | [TASK-056](../../tasks/ready/TASK-056.md), [TASK-057](../../tasks/ready/TASK-057.md), [TASK-058](../../tasks/ready/TASK-058.md) | FEATURE-005 | 7 |
| [FEATURE-007](../../features/ready/FEATURE-007.md) — Project installation, CLI and acceptance | [TASK-059](../../tasks/ready/TASK-059.md), [TASK-060](../../tasks/ready/TASK-060.md), [TASK-061](../../tasks/ready/TASK-061.md), [TASK-062](../../tasks/ready/TASK-062.md) | FEATURE-006 | 8 |

Safe waves: FEATURE-001 → FEATURE-002 + FEATURE-003 → FEATURE-004 → FEATURE-005 → FEATURE-006 → FEATURE-007.

FEATURE-004 may start once FEATURE-002 is integrated even if FEATURE-003 is still running; no ownership overlap exists. FEATURE-005 waits for both. Shared packaging metadata is changed by FEATURE-001 and then FEATURE-007, never concurrently. No database schema is introduced; named API resources model exclusive interface ownership.

State reconciliation is built against the agreed Git interface before its real adapter exists. FEATURE-005 defines and tests the recovery hook; FEATURE-006 supplies it by late import. Runtime model resolution belongs to FEATURE-004, while FEATURE-001 packages validated role/profile references. These explicit boundaries avoid hidden implementation cycles.

# Runtime boundaries for PLAN-002

Implementation agreement after decomposition. Use dictionaries for YAML records, typed public Python functions and `FrameworkError` for actionable failures. Avoid recreating the legacy port hierarchy.

## Shared core (FEATURE-001)

- `errors.FrameworkError(Exception)` and `PolicyError(FrameworkError)`.
- `io.read_yaml(path) -> dict`, `write_yaml(path, data)`, `atomic_write(path, text)`, `safe_path(root, relative) -> Path` (reject escapes/links), `utc_now() -> str`.
- `artifacts.Artifact(path: Path, metadata: dict, body: str)` has `id`, `status`; `read_artifact(path)`, `write_artifact(path, metadata, body)`. `ArtifactStore(root)` exposes `find(id)`, `list(kind, status=None)`, `create(kind, id, title, status, **metadata)`, `save(artifact)`, `transition(id, status, **updates)`, `next_id(prefix)`. IDs are project-unique. Kinds: plans/tasks/features/bugs/research/decisions/reviews/handoffs. Task metadata: plan, depends_on, scope (list of relative file/directory roots), resources (exclusive schema/interface names), acceptance (list), validation (command names), batch (ownership label), effort (integer 1..3), context (list of refs). Feature metadata adds tasks, dependencies; same scope/resources/acceptance/validation/context fields.
- `state.StateStore(root)` exposes `load() -> dict`, `save(dict)`, `lock()` context manager; `refresh_index(root)` rebuilds artifact-derived indexes while preserving Git observations. `reconcile(root, git, apply=False) -> dict` returns `issues`, `worktrees`, `merged` without deleting or authorizing work.
- `config.load_config(root, name) -> dict` loads `.ai/{name}.yaml`; project seeds are installed before use.
- `templates.render(root, relative_template, values) -> str` uses strict `{{ name }}` variables, prefers `.ai/templates/`, falls back to packaged assets. `templates.asset_root() -> Path`.

## Execution (FEATURE-002)

- `constraints.ConstraintPolicy(config, grants=())`: `check_command(argv, role, action=None)`, `check_action(action)`, `check_paths(paths, allowed_scope)`. Deny-by-default token-prefix command rules; forbidden wins. Grants satisfy approval-required actions and never override forbidden rules. No shell strings. Scope is path containment; protected paths and secrets always checked.
- `runner.CommandRunner(root, constraints: dict, run_dir=None, dry_run=False, grants=())`; `run(argv, cwd=None, *, timeout=120, expected_exit_codes=(0,), role='orchestrator', action=None, input_text=None) -> CommandResult`. Result fields: argv, cwd, started_at, finished_at, returncode, stdout, stderr, status; `ok` true only for success/expected_failure. Status: success, expected_failure, failed, timeout, dry_run, denied, error. Policy denial raises PolicyError. Persist YAML evidence. Only runner.py imports subprocess. Bound/redact evidence, stop timed-out processes. Reject symlink/junction cwd and implicit batch/shell execution.
- `git.Git(root, runner)`: `list_worktrees() -> list[dict]` (path, branch, head, locked/prunable); `head(path=None) -> str`; `branch(path=None) -> str`; `status(path=None) -> str`; `diff(path, base) -> str`; `changed_files(path, base) -> list[str]`; `is_ancestor(commit, target='HEAD') -> bool`; `create_worktree(name, branch, base='HEAD') -> Path`; `commit(path, message) -> str`; `cleanup(path, *, base='HEAD', disposition=None, active=False) -> bool`. Branch prefix `codex/`. Cleanup preserves branches; refuses dirty/unowned/locked/unmerged trees unless explicitly superseded/abandoned. Validate names/refs/paths before Git. Coordinator persists intent before mutations.

## Planning (FEATURE-003)

- `planning.validate_tasks(tasks: list[Artifact], max_effort=3) -> list[str]` checks fields, missing IDs, cycles, sizing. `planning.decompose(tasks, max_tasks=5, max_effort=8) -> list[dict]` yields feature proposals with id (FEATURE-NNN assigned by persistence), title, tasks, dependencies, scope, resources, acceptance, validation, context. `planning.validate_features(tasks, features) -> list[str]` verifies exact coverage, task order reflected in feature edges, cycles, ownership conflicts serialized.
- `planning.parallel_waves(features) -> list[list[str]]` topological, conflict-safe waves. `planning.persist_decomposition(store, plan_id, proposals) -> list[Artifact]` assigns fresh IDs, writes ready features and an auditable decomposition handoff. Idempotent for unchanged active graph; never overwrites started features. `planning.apply_revision(store, plan_id, revision: dict) -> list[Artifact]` validates replacement tasks with lineage/rationale, supersedes old tasks/features, then redecomposes. Validate completely before mutations; preserve unaffected completed work and incoming/outgoing dependencies.
- Semantic splitting/prerequisite discovery belongs to the Work Decomposition Agent; deterministic functions validate its proposal. A heuristic must not claim it discovered all hidden dependencies.

## Agents and review (FEATURE-004)

- `agents.AgentRequest` dataclass: role, assignment: Path, output: Path, worktree: Path, session_id: str, model: dict, permissions: dict. `AgentResult` dataclass: status, output: Path, session_id: str, metadata: dict. `AgentProvider` protocol `invoke(request) -> AgentResult`.
- `agents.resolve_agent(root, role) -> dict` resolves definition/profile/permissions; checks reviewer independence and capability tier. `agents.CommandAgentProvider(root, runner)` invokes configured argv from framework.yaml providers using YAML request/response paths, via central runner. Require configured bridge and permission/tool-boundary attestation; no built-in fake PASS. Persist request/result metadata and validate output. `agents.dispatch(root, role, assignment, worktree, run_dir, provider, session_id=None) -> AgentResult` chooses UUID session, preserves repair sessions, uses new review sessions.
- `handoffs.write_handoff(root, template, values, *, name=None) -> Path`: strict immutable Markdown under `.ai/handoffs/`, relevant references/policy automatically supplied. `review.read_review(path, *, expected_subject, expected_head, implementer_session) -> dict`: only PASS/CHANGES_REQUIRED; revision binding and distinct reviewer identity; findings required on failure. `review.review_assignment(root, subject: Artifact, worktree, base, head, completion: Path, validation: list, iteration: int) -> Path` builds implementation-to-review artifact. Templates describe review fields; no second stage.

## Orchestration / delivery (FEATURE-005)

Coordinator owns transitions, run journals, ThreadPoolExecutor scheduling, worktree intents, validation and complete-diff review/repair. `Orchestrator(root, provider=None, dry_run=False, grants=())` with `implement(plan_id)` and `execute_subject(subject, ...)` reusable by bugs. Persist intents before Git/provider/delivery effects; uncertain external writes are reconciled rather than blindly repeated. Stable implementation sessions; new reviewer sessions; bounded repairs/recovery. Delivery runs git push/gh PR through runner, prepares PR body first, checks grants, persists branch/head/URL. No remote writes in this reset without authority. Dependencies wait for merge to selected base. PRs wait in review; review PASS does not mean completion.

## Bugfix / recovery (FEATURE-006)

`workflows.create_bug(root, description) -> Artifact`; `fix_bug(root, bug_or_description, *, provider=None, dry_run=False, grants=())`; investigation records root cause/expected behavior/regression strategy before fix dispatch. Structural escalation creates plan/tasks and decomposes. `recover(root, subject, reason, reviews, provider)`: asks recovery for revision, applies validated replacement graph through planning, returns scheduler-ready work. Orchestrator imports hooks at runtime to avoid cycles.

## CLI / installation (FEATURE-007)

`project.initialize(root, *, adopt=False, dry_run=False)` installs packaged templates, definitions and YAML seeds; never copies development history or overwrites user files. `cli.main(argv=None)` exposes project init/adopt, status, state reconcile, research create, plan create/decompose/implement and bug fix. Global `--project`, `--dry-run`, repeatable `--grant ACTION`. No external writes default. `ai` and `python -m ai_engineering` share entry point. Tests use temporary Git repositories and controlled providers, not the user's project.
