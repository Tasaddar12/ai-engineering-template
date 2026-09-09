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
| [FEATURE-001](../../features/completed/FEATURE-001.md) — Artifact, configuration and state foundation | [TASK-040](../../tasks/completed/TASK-040.md), [TASK-041](../../tasks/completed/TASK-041.md), [TASK-042](../../tasks/completed/TASK-042.md) | None | 7 |
| [FEATURE-002](../../features/completed/FEATURE-002.md) — Constrained commands and managed Git worktrees | [TASK-043](../../tasks/completed/TASK-043.md), [TASK-044](../../tasks/completed/TASK-044.md), [TASK-045](../../tasks/completed/TASK-045.md) | FEATURE-001 | 8 |
| [FEATURE-003](../../features/completed/FEATURE-003.md) — Validated task decomposition and feature graphs | [TASK-046](../../tasks/completed/TASK-046.md), [TASK-047](../../tasks/completed/TASK-047.md), [TASK-048](../../tasks/completed/TASK-048.md) | FEATURE-001 | 8 |
| [FEATURE-004](../../features/completed/FEATURE-004.md) — Configured agents, durable handoffs and critical review | [TASK-049](../../tasks/completed/TASK-049.md), [TASK-050](../../tasks/completed/TASK-050.md), [TASK-051](../../tasks/completed/TASK-051.md) | FEATURE-002 | 8 |
| [FEATURE-005](../../features/in-progress/FEATURE-005.md) — Concurrent implementation, repair and delivery | [TASK-052](../../tasks/in-progress/TASK-052.md), [TASK-053](../../tasks/in-progress/TASK-053.md), [TASK-054](../../tasks/in-progress/TASK-054.md), [TASK-055](../../tasks/in-progress/TASK-055.md) | FEATURE-003, FEATURE-004 | 8 |
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

## Approved contract clarification - structured agent outputs

TASK-050 / FEATURE-004 also owns packaged handoff templates and agent definitions, serialized after core through FEATURE-002. Expected output Markdown uses small YAML front matter for machine-readable results, with narrative evidence below. The bridge returns AgentResult.metadata containing role-specific result data consistent with that artifact. Work decomposition returns feature proposals and optional complete task/revision proposals; recovery uses `{reason, replacements, tasks, stopped_features, features?}`. Implementation returns completion or structural issues. No ad-hoc extraction of prose replaces these contracts. The Work Decomposition Agent checked this ownership clarification on 2026-09-08: no coverage, dependency, batch-limit or concurrent-conflict change.

## Approved contract clarification - bug state evidence

TASK-058 / FEATURE-006 additionally owns `src/ai_engineering/state.py` solely to index bug review and PR metadata alongside feature evidence. Regression coverage remains in `tests/test_workflows.py`. Independent decomposition approved this on 2026-09-08: serialized after core and orchestration; unchanged 23-task/seven-feature graph and FEATURE-006 effort 7.

## Approved contract clarification - installed seed and platform typing

Independent decomposition approved TASK-059 / FEATURE-007 ownership of only `src/ai_engineering/templates/plans/plan.md` to repair its misdecoded title separator. The coordinator synchronizes the project copy. TASK-058 / FEATURE-006 may add narrow type annotations to guarded Windows locking calls in its already approved state.py scope. No behavioral expansion, effort increase, dependency or concurrency change.

## Coordinator execution details

All agent outputs are Markdown with small YAML front matter matching AgentResult.metadata. Common output identity is subject/session/status; critical reviews use reviewer_session and implementer_session. Each unique dispatch directory has deterministic request, response, invocation, result and output paths. Resume reuses validated evidence for identical bindings; an uncertain invocation is reported without blind redispatch. Structured assignment scope and the output-only write exception accompany role permissions.

The coordinator owns STATE and lifecycle transitions. Concurrent feature workers own separate run evidence and return outcomes to that coordinator. Worktree creation intent precedes Git changes. All ready graph ownership/dependency checks occur before scheduling. Validation and review bind to the committed complete feature revision; source or branch drift invalidates that evidence. Stable implementation sessions receive repairs; new review attempts use distinct sessions.

Initial task creation may use an approved semantic revision with empty replacements, fresh tasks and feature proposals through the same validated planning transaction. Existing approved graphs are reused only with current bindings; semantic decomposition never silently disappears behind a deterministic heuristic. Structural recovery waits for affected running assignments to stop, validates scope and budgets, redecomposes, then resumes the scheduler. Ordinary exhausted code repairs remain explicit blockers.

PR bodies are prepared as durable templated artifacts before external action checks. Delivery journals distinguish pending, confirmed and uncertain effects. Approved or published features stay in review until the reviewed commit is observed on the selected base; only then are tasks/features completed and clean, unreferenced worktrees eligible for removal. Dry runs read artifacts and report proposed work without provider calls, process launches, state writes or checkout mutations.

## Approved review-integrity prerequisite repair

Critical review of FEATURE-004 reproduced truncation hidden by redaction in the execution adapter. Independent decomposition approved TASK-051 / FEATURE-004 ownership of `runner.py` and `git.py` solely to add a backward-compatible raw completeness/truncation signal and reject incomplete Git observations. The signal must be determined before redaction; a post-redaction length sentinel is insufficient. Tests stay in `tests/test_agents.py`. The feature also owns `templates/reviews/critical-review.md` to serialize complete YAML front matter with safe multiline issues. All ownership follows completed FEATURE-002/core and is serialized; unchanged 23 tasks, seven features and effort bounds. This is a repair in the same single critical review stage.

## Shared subject execution contract

`Orchestrator.execute_subject(subject: Artifact | str, *, role='implementation', phase=None, session_id=None, investigation: Path | None=None) -> dict` owns locking and subject lifecycle transitions. The bug workflow supplies `role='bugfix'`, `phase='fix'`, its stable investigation session and the durable investigation reference. The implementation/review/delivery loop is shared with features.

The late recovery hook is `workflows.recover(root, subject: Artifact, reason: str, reviews: list[Path], provider: AgentProvider) -> list[Artifact]`, returning the validated revised feature graph. Before calling it, the coordinator drains running workers, records which assignments have stopped, blocks affected active work and persists the plan-wide recovery budget. Recovery verifies that evidence; a model's `stopped_features` assertion cannot itself authorize replacing active work. The scheduler reloads and validates the resulting graph before resuming.

The coordinator's quiescence receipt binds the plan, run, recovery attempt, state generation, confirmed stopped feature IDs and invocation outcomes. Recovery substitutes verified IDs from that receipt for model claims and refuses uncertain invocations. Blocked artifact status alone does not prove quiescence.

Bug investigation is read-only and assigns no artificial tasks. Its escalation proposal states the reason, proposed scope, expected behavior and whether the change materially expands authorized product scope. In-scope structural work may become a normal plan automatically. Material expansion creates a blocked draft with explicit task/feature lists and a visible authorization requirement. Persist `bug.escalated_plan` before dispatch; retries reuse that plan and escalation does not mark the bug fixed.

Project initialization may seed a directory without Git, but must report that worktree execution requires a Git repository with a committed base. Plan creation captures scope and acceptance before readiness; draft lists may be empty until semantic decomposition. CLI status labels ancestry observations separately from independently approved, merged completion.

## Approved installed proposal schema clarification

Independent decomposition approved TASK-052 / FEATURE-005 ownership of `templates/handoffs/agent-decomposition.md` to document nested feature/task/revision fields for installed agents. TASK-058 / FEATURE-006 owns `templates/handoffs/agent-recovery.md` for revision lineage and trusted quiescence guidance. These are reusable runtime contracts; PLAN-002-specific planning stays here. Keep the existing template variables unchanged and align documentation with actual validators. Exact task coverage, feature dependencies, effort bounds and concurrency are unchanged.

## Approved remote observation prerequisite

Independent decomposition approved TASK-055 / FEATURE-005 ownership of the packaged constraints seed solely to allow the exact `git ls-remote --heads` prefix for the orchestrator role with the existing credentials action requirement. Delivery supplies a validated configured remote and exact branch reference. This permits reconciliation of an uncertain push after configured authority; it performs no network action during implementation. Forbidden operations still win. The coordinator synchronizes the installed seed only after verifying its unchanged prior copy. No task, dependency, effort or concurrency change.

## Approved coordinator control protection

The same TASK-055 / FEATURE-005 seed ownership also protects `.ai/plans`, `.ai/tasks`, `.ai/features`, `.ai/bugs`, `.ai/runs`, `.ai/reviews` and `.ai/handoffs` from implementation writes, even within broad `.ai` scope. Independent decomposition confirmed that review approval does not transfer coordinator authority. The trusted bridge retains only the single assigned output-file exception. Decisions, research and templates remain authorable within declared scope. No graph or batch change.

## Merge observation boundary

The selected local base must contain the exact independently reviewed commit. This version neither fetches remote refs nor treats a hosting-service PR status as proof that local dependencies are available. Ancestry-preserving merges are recognized; squash/rebase merges that discard the reviewed commit need explicit reconciliation support before they can be considered complete. Public operating documentation must state this boundary and the resume command, rather than imply background remote merge watching.

## Approved installed bridge context base

Independent decomposition approved TASK-060 / FEATURE-007 ownership of `agents.py` solely to add `project_root: str(root)` to serialized provider request records, without changing the AgentRequest constructor. Handoff references resolve against this read-only coordinator context base; source edits and commands use worktree. The output path remains the exact return-file exception. This grants no root-write authority. CLI/acceptance coverage must include `.ai` absent from the worktree. Old persisted bindings that differ remain fail-closed rather than being silently replayed. Dependencies serialize this narrow prerequisite after FEATURE-004; no task/batch change.
