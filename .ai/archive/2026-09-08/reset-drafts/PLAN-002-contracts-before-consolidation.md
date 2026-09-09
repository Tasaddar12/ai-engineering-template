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
