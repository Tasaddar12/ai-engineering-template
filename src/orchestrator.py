"""Durable coordinator workflows for planning, implementation and bug fixing.

The orchestrator owns control-state and artifact changes. Agent providers receive a
fixed worktree/session assignment; Git, validation, delivery and cleanup stay behind
their dedicated framework boundaries.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from .agents import AgentResult, dispatch
from .artifacts import Artifact, ArtifactStore
from .config import load_config
from .errors import FrameworkError
from .git import Git
from .handoffs import contained, read_markdown, scope_paths, write_handoff
from .io import utc_now
from .planning import apply_plan_changes, apply_revision
from .planning_intent import (
    grant_implementation,
    prepare_intent,
    record_existing_plan_delivery,
)
from .review import read_review, review_assignment
from .runner import CommandRunner
from .state import StateStore, refresh_index

Record = dict[str, Any]


def _root(path: Path | str) -> Path:
    root = Path(path).absolute()
    if not (root / ".ai/STATE.yaml").is_file():
        raise FrameworkError("Coordinator requires an initialized project with .ai/STATE.yaml")
    return root


def _change_state(root: Path, change: Callable[[Record], Any]) -> Any:
    state = StateStore(root)
    with state.lock():
        value = state.load()
        result = change(value)
        state.save(value)
        return result


def _relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise FrameworkError("Workflow path escapes the project") from exc


def _runtime(root: Path, evidence: str = "orchestrator") -> tuple[CommandRunner, Git]:
    runner = CommandRunner(
        root,
        load_config(root, "constraints"),
        run_dir=root / f".ai/local/commands/{evidence}",
    )
    return runner, Git(root, runner)


def _plan_scope(store: ArtifactStore, plan: Artifact) -> list[str]:
    raw = plan.metadata.get("scope")
    if isinstance(raw, list) and raw:
        return scope_paths(store.root, raw)
    combined: list[str] = []
    for identifier in plan.metadata.get("features", []):
        feature = store.find(identifier)
        for item in feature.metadata.get("scope", []):
            if item not in combined:
                combined.append(item)
    if not combined:
        raise FrameworkError("Implementation requires explicit PLAN or feature scope")
    return scope_paths(store.root, combined)


def _work_scope(root: Path, artifact: Artifact) -> list[str]:
    raw = artifact.metadata.get("implementation_scope", artifact.metadata.get("scope", []))
    scope = scope_paths(root, raw)
    control = (".ai", "AGENTS.md", "ARCHITECTURE.md")
    product = [
        item
        for item in scope
        if not any(item == boundary or item.startswith(boundary + "/") for boundary in control)
    ]
    if not product:
        raise FrameworkError(f"{artifact.id} has no implementation-owned product scope")
    return product


def _context_refs(root: Path, artifacts: Iterable[Artifact], extra: Iterable[str] = ()) -> list[str]:
    references: list[str] = []
    for artifact in artifacts:
        reference = _relative(root, artifact.path)
        if reference not in references:
            references.append(reference)
    for reference in extra:
        if isinstance(reference, str) and (root / reference.split("#", 1)[0]).is_file():
            if reference not in references:
                references.append(reference)
    return references


def status(root: Path | str) -> Record:
    """Return the durable workflow view without mutating state or invoking Git."""
    root = _root(root)
    value = StateStore(root).load()
    store = ArtifactStore(root)
    artifacts = {
        kind: [
            {
                "id": artifact.id,
                "status": artifact.status,
                "title": artifact.metadata.get("title"),
                "plan": artifact.metadata.get("plan"),
                "hard_block": artifact.metadata.get("hard_block"),
            }
            for artifact in store.list(kind)
        ]
        for kind in ("plans", "tasks", "features", "bugs")
    }
    return {
        "status": "ok",
        "project": value.get("project", {}),
        "generation": value.get("generation", 0),
        "current_focus": value.get("current_focus", {}),
        "artifacts": artifacts,
        "worktrees": value.get("worktrees", []),
        "active_runs": value.get("active_runs", []),
        "blockers": value.get("blockers", []),
        "implementation_authority": value.get("implementation_authority", {}),
        "next_actions": value.get("next_actions", []),
    }


def _register_worktree(
    root: Path,
    *,
    subject: str,
    path: Path,
    branch: str,
    purpose: str,
    session_id: str,
    base_revision: str,
    revision: str | None = None,
) -> None:
    def change(value: Record) -> None:
        records = value.setdefault("worktrees", [])
        if any(
            isinstance(record, dict)
            and (record.get("path") == _relative(root, path) or record.get("branch") == branch)
            for record in records
        ):
            raise FrameworkError("Worktree path or branch already has a workflow owner")
        records.append(
            {
                "path": _relative(root, path),
                "branch": branch,
                "subject": subject,
                "purpose": purpose,
                "session_id": session_id,
                "base_branch": "main",
                "base_revision": base_revision,
                "head": base_revision,
                "stage": "created",
                "planning_revision": revision,
                "status": "in-progress",
                "created_at": utc_now(),
            }
        )

    _change_state(root, change)


def _existing_worktree(root: Path, subject: str, purpose: str) -> Record | None:
    records = StateStore(root).load().get("worktrees", [])
    matches = [
        record
        for record in records
        if isinstance(record, dict)
        and record.get("subject") == subject
        and record.get("purpose") == purpose
        and record.get("status")
        in {
            "in-progress",
            "repair",
            "review",
            "delivery",
            "merged",
            "cleanup_failed",
            "blocked",
        }
    ]
    if len(matches) > 1:
        raise FrameworkError(f"Ambiguous worktree ownership for {subject}")
    return matches[0] if matches else None


def _verified_worktree(root: Path, record: Record) -> Path:
    raw = record.get("path")
    branch = record.get("branch")
    session_id = record.get("session_id")
    if (
        not isinstance(raw, str)
        or not isinstance(branch, str)
        or not branch.startswith("codex/")
        or not isinstance(session_id, str)
        or not session_id
    ):
        raise FrameworkError("Managed worktree ownership record is malformed")
    worktree = contained(root, raw, directory=".worktrees")
    _, git = _runtime(root, f"ownership-{record.get('subject', 'unknown')}")
    matches = [
        fact
        for fact in git.list_worktrees()
        if Path(str(fact.get("path", ""))).absolute() == worktree
    ]
    if (
        len(matches) != 1
        or matches[0].get("branch") != branch
        or matches[0].get("locked")
        or matches[0].get("prunable")
    ):
        raise FrameworkError("Managed worktree ownership or branch has drifted")
    return worktree


def _update_worktree(root: Path, subject: str, status: str, **updates: Any) -> Record:
    def change(value: Record) -> Record:
        matches = [
            record
            for record in value.setdefault("worktrees", [])
            if isinstance(record, dict)
            and record.get("subject") == subject
            and record.get("purpose") == "implementation"
        ]
        if len(matches) != 1:
            raise FrameworkError(f"Expected one implementation worktree for {subject}")
        matches[0].update(updates, status=status, updated_at=utc_now())
        return dict(matches[0])

    return _change_state(root, change)


def _forget_worktree(root: Path, subject: str, retirement: Any) -> None:
    def change(value: Record) -> None:
        records = value.setdefault("worktrees", [])
        matches = [
            record
            for record in records
            if isinstance(record, dict)
            and record.get("subject") == subject
            and record.get("purpose") == "implementation"
        ]
        if len(matches) > 1:
            raise FrameworkError(f"Ambiguous retired worktree ownership for {subject}")
        if matches:
            record = matches[0]
            records.remove(record)
            value.setdefault("retired_worktrees", []).append(
                {**record, "status": "retired", "retired_at": utc_now(), "retirement": retirement}
            )

    _change_state(root, change)


def _create_worktree(
    root: Path,
    subject: str,
    purpose: str,
    name: str,
    branch: str,
    *,
    revision: str | None = None,
) -> tuple[Path, str]:
    if _existing_worktree(root, subject, purpose) is not None:
        raise FrameworkError(f"{subject} already has an active {purpose} worktree")
    _, git = _runtime(root, f"worktree-{name}")
    session_id = uuid.uuid4().hex
    worktree = git.create_worktree(
        name,
        branch,
        "main",
        purpose=purpose,
        subject=subject,
        session_id=session_id,
    )
    base_revision = git.head(worktree)
    _register_worktree(
        root,
        subject=subject,
        path=worktree,
        branch=branch,
        purpose=purpose,
        session_id=session_id,
        base_revision=base_revision,
        revision=revision,
    )
    return worktree, session_id


def _mark_owner(root: Path, worktree: Path, session_id: str, status: str) -> None:
    _, git = _runtime(root, f"owner-{worktree.name}")
    git.mark_owner(worktree, session_id, status)


def create_plan(root: Path | str, title: str, scope: list[str]) -> Record:
    """Reserve and create a planning-only draft in a dedicated worktree."""
    root = _root(root)
    if not isinstance(title, str) or not title.strip():
        raise FrameworkError("Plan title must be nonempty")
    approved_scope = scope_paths(root, scope)
    if not approved_scope:
        raise FrameworkError("Plan scope must be nonempty")
    preparation = prepare_intent(StateStore(root), "create_plan", scope=approved_scope)
    reservation = preparation.reservation
    if reservation is None:
        raise FrameworkError("Planning reservation was not created")
    plan_id = reservation["plan"]
    suffix = reservation["revision"].rsplit("-", 1)[-1]
    name = f"{plan_id.lower()}-planning-{suffix}"
    branch = f"codex/{name}"
    worktree, session_id = _create_worktree(
        root,
        plan_id,
        "planning",
        name,
        branch,
        revision=reservation["revision"],
    )
    with StateStore(worktree).lock():
        plan = ArtifactStore(worktree).create(
            "plans",
            plan_id,
            title,
            "draft",
            scope=approved_scope,
            planning_revision=reservation["revision"],
            planning_purpose=True,
            tasks=[],
            features=[],
        )
    _mark_owner(root, worktree, session_id, "stopped")
    return {
        "status": "planning_worktree_ready",
        "plan": plan_id,
        "planning_revision": reservation["revision"],
        "worktree": str(worktree),
        "branch": branch,
        "session_id": session_id,
        "artifact": str(plan.path),
        "implementation_authorized": False,
    }


def _new_specifications(value: Any) -> int:
    if value is None:
        return 0
    if not isinstance(value, list):
        raise FrameworkError("Planning task/feature changes must be lists")
    return sum(isinstance(item, dict) and not item.get("id") for item in value)


def _delivered_revision(root: Path, plan: Artifact, scope: list[str]) -> str:
    state = StateStore(root)
    current = state.load().get("planning_intent", {}).get("delivered", {}).get(plan.id)
    if isinstance(current, dict):
        revision = current.get("delivery", {}).get("revision")
        if isinstance(revision, str):
            planning_revision = plan.metadata.get("planning_revision")
            if planning_revision is not None and planning_revision != current.get("revision"):
                raise FrameworkError("Canonical PLAN differs from its delivered planning revision")
            return revision
        raise FrameworkError("Delivered planning provenance is malformed")
    _, git = _runtime(root, f"plan-provenance-{plan.id.lower()}")
    revision = git.head()
    record_existing_plan_delivery(state, plan.id, revision, scope)
    return revision


def revise_plan(root: Path | str, plan_id: str, **changes: Any) -> Record:
    """Prepare a forward planning revision in a new dedicated worktree."""
    root = _root(root)
    store = ArtifactStore(root)
    plan = store.find(plan_id)
    if plan.metadata.get("kind") != "plans" or plan.status in {
        "completed",
        "archived",
        "superseded",
    }:
        raise FrameworkError("Planning revision requires a current PLAN")
    scope = scope_paths(root, changes.get("scope", _plan_scope(store, plan)))
    _delivered_revision(root, plan, _plan_scope(store, plan))
    preparation = prepare_intent(
        StateStore(root),
        "revise_plan",
        plan_id=plan_id,
        task_count=_new_specifications(changes.get("tasks")),
        feature_count=_new_specifications(changes.get("features")),
        scope=scope,
    )
    reservation = preparation.reservation
    if reservation is None:
        raise FrameworkError("Planning revision was not reserved")
    suffix = reservation["revision"].rsplit("-", 1)[-1]
    name = f"{plan_id.lower()}-planning-{suffix}"
    branch = f"codex/{name}"
    worktree, session_id = _create_worktree(
        root,
        plan_id,
        "planning",
        name,
        branch,
        revision=reservation["revision"],
    )
    normalized_changes = dict(changes)
    if "scope" in changes:
        normalized_changes["scope"] = scope
    revised = apply_plan_changes(
        ArtifactStore(worktree), plan_id, normalized_changes, reservation
    )
    _mark_owner(root, worktree, session_id, "stopped")
    return {
        "status": "planning_revision_ready",
        "plan": plan_id,
        "planning_revision": reservation["revision"],
        "worktree": str(worktree),
        "branch": branch,
        "session_id": session_id,
        "artifact": str(revised.path),
        "implementation_authorized": False,
    }


def _implementation_worktree(root: Path, subject: Artifact) -> tuple[Path, str, str]:
    existing = _existing_worktree(root, subject.id, "implementation")
    if existing is not None:
        worktree = _verified_worktree(root, existing)
        return worktree, str(existing["branch"]), str(existing["session_id"])
    name = subject.id.lower()
    branch = f"codex/{name}"
    worktree, session_id = _create_worktree(
        root, subject.id, "implementation", name, branch
    )
    return worktree, branch, session_id


def _record_run(root: Path, record: Record) -> None:
    def change(value: Record) -> None:
        runs = value.setdefault("active_runs", [])
        matches = [item for item in runs if isinstance(item, dict) and item.get("id") == record["id"]]
        if matches:
            matches[0].update(record)
        else:
            runs.append({**record, "started_at": utc_now()})

    _change_state(root, change)


def _finish_run(root: Path, run_id: str, result: AgentResult | None, error: str | None) -> None:
    def change(value: Record) -> None:
        for record in value.setdefault("active_runs", []):
            if isinstance(record, dict) and record.get("id") == run_id:
                record["status"] = result.status if result is not None else "failed"
                record["error"] = error
                record["finished_at"] = utc_now()
                if result is not None:
                    record["output"] = _relative(root, result.output)
                    record["session_id"] = result.session_id
                return
        raise FrameworkError(f"Active run disappeared: {run_id}")

    _change_state(root, change)


def _resume_record(root: Path, subject: str, action: str) -> Record | None:
    candidates = [
        record
        for record in StateStore(root).load().get("active_runs", [])
        if isinstance(record, dict)
        and record.get("subject") == subject
        and record.get("action") == action
        and record.get("status")
        in {
            "dispatching",
            "failed",
            "COMPLETE",
            "INVESTIGATED",
            "ESCALATE",
            "STRUCTURAL_FAILURE",
            "REPLAN",
            "PASS",
            "CHANGES_REQUIRED",
        }
    ]
    return candidates[-1] if candidates else None


def _dispatch_worktree(
    root: Path,
    role: str,
    worktree: Path,
    session_id: str | None,
    subject: str,
    phase: str | None,
) -> None:
    modifying = role == "implementation" or (role == "bugfix" and phase != "investigation")
    reviewing = role == "critical_review"
    if not modifying and not reviewing:
        return
    record = _existing_worktree(root, subject, "implementation")
    if record is None:
        raise FrameworkError(f"{subject} has no active implementation worktree owner")
    owned = _verified_worktree(root, record)
    if owned != Path(worktree).absolute():
        raise FrameworkError("Dispatch worktree differs from durable feature ownership")
    if modifying and record.get("session_id") != session_id:
        raise FrameworkError("Repair/resume must retain the assigned implementation session")


def _dispatch_assignment(
    root: Path,
    role: str,
    assignment: Path,
    worktree: Path,
    session_id: str | None,
    subject: str,
    action: str,
    *,
    phase: str | None = None,
    resume: bool = False,
) -> AgentResult:
    _dispatch_worktree(root, role, worktree, session_id, subject, phase)
    previous = _resume_record(root, subject, action) if resume else None
    if previous is not None:
        assignment = contained(root, previous["assignment"], directory=".ai")
        run_dir = contained(root, previous["run_dir"], directory=".ai/runs")
        recorded_worktree = contained(root, previous["worktree"], directory=".worktrees")
        if recorded_worktree != Path(worktree).absolute():
            raise FrameworkError("Resumed run belongs to a different worktree")
        if session_id is not None and previous.get("session_id") != session_id:
            raise FrameworkError("Resumed run belongs to a different implementation session")
        run_id = previous["id"]
    else:
        run_id = uuid.uuid4().hex
        run_dir = root / f".ai/runs/{subject.lower()}/{run_id}"
        _record_run(
            root,
            {
                "id": run_id,
                "subject": subject,
                "role": role,
                "action": action,
                "phase": phase,
                "session_id": session_id,
                "assignment": _relative(root, assignment),
                "run_dir": _relative(root, run_dir),
                "worktree": _relative(root, worktree),
                "status": "dispatching",
            },
        )
    try:
        result = dispatch(
            root,
            role,
            assignment,
            worktree,
            run_dir,
            None,
            session_id=session_id,
            phase=phase,
        )
    except Exception as exc:
        _finish_run(root, run_id, None, str(exc))
        raise
    _finish_run(root, run_id, result, None)
    return result


def _feature_assignment(
    root: Path,
    plan: Artifact,
    feature: Artifact,
    worktree: Path,
    branch: str,
    action: str,
    revision: str,
) -> Path:
    store = ArtifactStore(root)
    tasks = [store.find(identifier) for identifier in feature.metadata.get("tasks", [])]
    dependencies = [store.find(identifier) for identifier in feature.metadata.get("dependencies", [])]
    _, git = _runtime(root, f"assignment-{feature.id.lower()}")
    dependency_handoffs = [
        dependency.metadata["handoff"]
        for dependency in dependencies
        if isinstance(dependency.metadata.get("handoff"), str)
    ]
    return write_handoff(
        root,
        "handoffs/orchestrator-to-feature-agent.md",
        {
            "role": "implementation",
            "subject": feature.id,
            "feature": feature.id,
            "plan": plan.id,
            "action": action,
            "approved_revision": revision,
            "tasks": [task.id for task in tasks],
            "dependencies": [dependency.id for dependency in dependencies],
            "worktree": str(worktree),
            "branch": branch,
            "base": git.head(worktree),
            "allowed_scope": _work_scope(root, feature),
            "prohibited_scope": [".ai"],
            "context_refs": _context_refs(
                root,
                [plan, feature, *tasks],
                feature.metadata.get("context", []),
            ),
            "dependency_handoffs": dependency_handoffs,
            "acceptance": feature.metadata.get("acceptance", []),
            "validation": feature.metadata.get("validation", []),
        },
    )


def _run_validation(root: Path, worktree: Path, subject: Artifact) -> list[Record]:
    configured = load_config(root, "project/commands").get("commands", {})
    names = subject.metadata.get("validation") or [
        name for name in ("format", "lint", "types", "tests") if name in configured
    ]
    if (
        not isinstance(names, list)
        or not names
        or not all(isinstance(name, str) and name for name in names)
        or len(names) != len(set(names))
    ):
        raise FrameworkError("Validation requested but no named commands are configured")
    runner = CommandRunner(
        root,
        load_config(root, "constraints"),
        run_dir=root / f".ai/runs/{subject.id.lower()}/validation",
    )
    evidence = []
    for name in names:
        if not isinstance(name, str) or name not in configured:
            raise FrameworkError(f"Unknown validation command: {name}")
        argv, timeout = runner.policy.named_command(
            name,
            "orchestrator",
            workflow="validation",
            selected_commands=names,
        )
        result = runner.run(
            argv,
            cwd=worktree,
            timeout=timeout,
            workflow="validation",
            command_name=name,
            selected_commands=names,
        )
        item = {
            "command": name,
            "status": result.status,
            "returncode": result.returncode,
            "stdout_truncated": result.stdout_truncated,
            "stderr_truncated": result.stderr_truncated,
            "output_complete": result.output_complete,
        }
        evidence.append(item)
        if not result.ok or not result.output_complete:
            raise FrameworkError(f"Validation failed or was incomplete: {name}")
    return evidence


def _deferred_validation() -> list[Record]:
    return [{"command": "validation", "status": "DEFERRED_BY_USER"}]


def _scope_contains(scope: list[str], path: str) -> bool:
    normalized = tuple(path.replace("\\", "/").split("/"))
    for parent in scope:
        if parent == ".":
            return True
        prefix = tuple(parent.replace("\\", "/").split("/"))
        if normalized[: len(prefix)] == prefix:
            return True
    return False


def _commit_agent_changes(
    root: Path,
    subject: Artifact,
    worktree: Path,
    git: Git,
    base: str,
    message: str,
) -> str:
    dirty = git.status(worktree)
    current_head = git.head(worktree)
    record = _existing_worktree(root, subject.id, "implementation")
    if not dirty:
        if (
            record is not None
            and record.get("stage") == "committed"
            and record.get("head") == current_head
            and current_head != base
        ):
            return current_head
        raise FrameworkError("Agent completed without an uncommitted source change")
    changed = git.changed_files(worktree, base)
    allowed = _work_scope(root, subject)
    outside = [path for path in changed if not _scope_contains(allowed, path)]
    if outside:
        raise FrameworkError(
            "Agent changed files outside canonical work scope: " + ", ".join(outside)
        )
    head = git.commit(worktree, message)
    if git.status(worktree):
        raise FrameworkError("Coordinator commit left the managed worktree dirty")
    _update_worktree(
        root,
        subject.id,
        "in-progress",
        head=head,
        stage="committed",
    )
    return head


def _start_feature(root: Path, feature_id: str) -> Artifact:
    with StateStore(root).lock():
        store = ArtifactStore(root)
        feature = store.find(feature_id)
        if feature.status == "ready":
            feature = store.transition(feature.id, "in-progress")
        if feature.status not in {"in-progress", "review"}:
            raise FrameworkError(f"Feature phase cannot start implementation: {feature.status}")
        for task_id in feature.metadata.get("tasks", []):
            task = store.find(task_id)
            if task.metadata.get("hard_block") is not None:
                raise FrameworkError(f"Assigned task is hard-blocked: {task.id}")
            if task.status in {"backlog", "ready"}:
                store.transition(task.id, "in-progress")
            elif task.status not in {"in-progress", "completed"}:
                raise FrameworkError(f"Assigned task phase is ineligible: {task.id}/{task.status}")
    refresh_index(root)
    return ArtifactStore(root).find(feature_id)


def _clear_block(root: Path, identifier: str) -> None:
    with StateStore(root).lock():
        store = ArtifactStore(root)
        artifact = store.find(identifier)
        if artifact.metadata.get("hard_block") is not None:
            store.clear_hard_block(identifier)
        state = StateStore(root)
        value = state.load()
        blockers = value.setdefault("blockers", [])
        filtered = [
            item
            for item in blockers
            if not isinstance(item, dict) or item.get("subject") != identifier
        ]
        if filtered != blockers:
            value["blockers"] = filtered
            state.save(value)


def _review_feature(
    root: Path,
    feature: Artifact,
    worktree: Path,
    base: str,
    head: str,
    completion: Path,
    validation: list[Record],
    iteration: int,
) -> tuple[AgentResult, Path]:
    assignment = review_assignment(
        root, feature, worktree, base, head, completion, validation, iteration
    )
    result = _dispatch_assignment(
        root,
        "critical_review",
        assignment,
        worktree,
        None,
        feature.id,
        "review",
    )
    return result, assignment


def _repair_assignment(
    root: Path,
    plan: Artifact,
    feature: Artifact,
    worktree: Path,
    review_output: Path,
    action: str,
    revision: str,
    iteration: int,
    *,
    role: str = "implementation",
) -> Path:
    review, _ = read_markdown(review_output)
    issues = review.get("issues", [])
    required = [issue.get("required_change") for issue in issues if isinstance(issue, dict)]
    return write_handoff(
        root,
        "handoffs/review-to-implementation.md",
        {
            "role": role,
            "subject": feature.id,
            "feature": feature.id,
            "bug": feature.id if feature.id.startswith("BUG-") else None,
            "plan": plan.id,
            "action": action,
            "approved_revision": revision,
            "tasks": feature.metadata.get("tasks", []),
            "worktree": str(worktree),
            "allowed_scope": _work_scope(root, feature),
            "prohibited_scope": [".ai"],
            "review": _relative(root, review_output),
            "iteration": iteration,
            "issues": issues,
            "required_changes": required,
            "validation": feature.metadata.get("validation", []),
            "context_refs": _context_refs(root, [plan, feature], [_relative(root, review_output)]),
        },
    )


def _record_block(root: Path, subject: Artifact, error: Exception) -> Record:
    reason = str(error).strip() or error.__class__.__name__
    with StateStore(root).lock():
        store = ArtifactStore(root)
        current = store.find(subject.id)
        if current.metadata.get("hard_block") is None:
            current = store.set_hard_block(
                current.id,
                reason=reason,
                evidence=[f"{error.__class__.__name__}: {reason}"],
                remedies=["Resolve the reported boundary and resume the same workflow"],
                affected_work=[subject.id],
                next_action="Resume the durable workflow intent",
                resume_condition="The reported boundary succeeds under current authority",
            )
        state = StateStore(root)
        value = state.load()
        blocker = {
            "subject": subject.id,
            **current.metadata["hard_block"],
            "recorded_at": utc_now(),
        }
        value.setdefault("blockers", [])[:] = [
            item
            for item in value.get("blockers", [])
            if not isinstance(item, dict) or item.get("subject") != subject.id
        ]
        value["blockers"].append(blocker)
        state.save(value)
    if _existing_worktree(root, subject.id, "implementation") is not None:
        _update_worktree(root, subject.id, "blocked", error=reason)
    return blocker


def _recover_feature(
    root: Path,
    plan: Artifact,
    feature: Artifact,
    result: AgentResult,
) -> Record:
    assignment = write_handoff(
        root,
        "handoffs/orchestrator-to-recovery.md",
        {
            "role": "recovery",
            "subject": feature.id,
            "reason": result.metadata.get("structural_issues", []),
            "reviews": [],
            "plan": plan.id,
            "tasks": feature.metadata.get("tasks", []),
            "features": plan.metadata.get("features", []),
            "preserved_work": result.metadata.get("changed_files", []),
            "budget": 1,
            "context_refs": _context_refs(root, [plan, feature], [_relative(root, result.output)]),
            "allowed_scope": [],
            "prohibited_scope": ["."],
        },
    )
    recovery = _dispatch_assignment(
        root,
        "recovery",
        assignment,
        root,
        uuid.uuid4().hex,
        feature.id,
        "recovery",
    )
    revision = recovery.metadata.get("revision")
    if recovery.status != "REPLAN" or not isinstance(revision, dict):
        raise FrameworkError("Recovery provider did not return a valid replan")
    new_tasks = revision.get("tasks", [])
    proposed_features = revision.get("features", [])
    if not isinstance(new_tasks, list) or not isinstance(proposed_features, list):
        raise FrameworkError("Recovery replan requires task and feature proposal lists")
    preparation = prepare_intent(
        StateStore(root),
        "revise_plan",
        plan_id=plan.id,
        task_count=len(new_tasks),
        feature_count=max(
            len(proposed_features),
            len(plan.metadata.get("tasks", [])) + len(new_tasks),
        ),
        scope=_plan_scope(ArtifactStore(root), plan),
    )
    reservation = preparation.reservation
    if reservation is None:
        raise FrameworkError("Recovery planning revision was not reserved")
    suffix = reservation["revision"].rsplit("-", 1)[-1]
    name = f"{plan.id.lower()}-recovery-{suffix}"
    branch = f"codex/{name}"
    planning_worktree, planning_session = _create_worktree(
        root,
        plan.id,
        "planning",
        name,
        branch,
        revision=reservation["revision"],
    )
    revised = apply_revision(
        ArtifactStore(planning_worktree),
        plan.id,
        revision,
        reservation,
    )
    _mark_owner(root, planning_worktree, planning_session, "stopped")
    blocker = _record_block(
        root,
        feature,
        FrameworkError(
            f"Structural recovery prepared {reservation['revision']}; deliver it before resuming"
        ),
    )
    return {
        "status": "planning_revision_ready",
        "feature": feature.id,
        "replacement_features": [item.id for item in revised],
        "output": str(recovery.output),
        "planning_revision": reservation["revision"],
        "worktree": str(planning_worktree),
        "branch": branch,
        "session_id": planning_session,
        "implementation_authorized": False,
        "blocker": blocker,
    }


def _deliver_work(
    root: Path,
    worktree: Path,
    branch: str,
    *,
    review: Path | None,
) -> tuple[Record, str]:
    from .delivery import deliver

    outcome = deliver(
        root,
        worktree,
        branch,
        base="main",
        review=str(review) if review is not None else None,
        run_tests=False,
    )
    if not isinstance(outcome, dict):
        raise FrameworkError("Delivery must return structured merge evidence")
    merged = outcome.get("merged_revision") or outcome.get("merge_commit") or outcome.get("head")
    if not isinstance(merged, str):
        raise FrameworkError("Delivery did not return a merged revision")
    from .cleanup import retire_worktree

    retirement = retire_worktree(root, worktree, branch, merged, base="main", remote=True)
    return {**outcome, "cleanup": retirement}, merged


def _retire_work(
    root: Path,
    subject: str,
    worktree: Path,
    branch: str,
    merged_revision: str,
) -> Any:
    from .cleanup import retire_worktree

    retired = retire_worktree(
        root,
        worktree,
        branch,
        merged_revision,
        base="main",
        remote=True,
    )
    if retired is False or retired is None:
        raise FrameworkError("Merged worktree retirement did not complete")
    _forget_worktree(root, subject, retired)
    return retired


def _resume_cleanup(root: Path, plan: Artifact) -> list[Record]:
    subjects = set(plan.metadata.get("features", []))
    records = [
        record
        for record in StateStore(root).load().get("worktrees", [])
        if isinstance(record, dict)
        and record.get("subject") in subjects
        and record.get("purpose") == "implementation"
        and record.get("status") in {"merged", "cleanup_failed"}
    ]
    outcomes: list[Record] = []
    for record in records:
        subject = str(record["subject"])
        worktree = _verified_worktree(root, record)
        merged = record.get("merged_revision")
        branch = record.get("branch")
        if not isinstance(merged, str) or not isinstance(branch, str):
            raise FrameworkError(f"Cleanup evidence is incomplete for {subject}")
        retired = _retire_work(root, subject, worktree, branch, merged)
        outcomes.append({"subject": subject, "cleanup": retired})
    return outcomes


def _complete_feature(
    root: Path,
    plan: Artifact,
    feature: Artifact,
    revision: str,
    *,
    validate: bool,
    deliver_changes: bool,
    resume: bool,
) -> Record:
    feature = _start_feature(root, feature.id)
    worktree, branch, session_id = _implementation_worktree(root, feature)
    action = "resume" if resume else "implement"
    _update_worktree(root, feature.id, "in-progress", action=action)
    previous = _resume_record(root, feature.id, action) if resume else None
    assignment = (
        contained(root, previous["assignment"], directory=".ai")
        if previous is not None
        else _feature_assignment(root, plan, feature, worktree, branch, action, revision)
    )
    result = _dispatch_assignment(
        root,
        "implementation",
        assignment,
        worktree,
        session_id,
        feature.id,
        action,
        resume=resume,
    )
    if result.status == "STRUCTURAL_FAILURE":
        return _recover_feature(root, plan, feature, result)
    if result.status != "COMPLETE":
        raise FrameworkError(f"Implementation returned unsupported status: {result.status}")

    _, git = _runtime(root, f"complete-{feature.id.lower()}")
    ownership = _existing_worktree(root, feature.id, "implementation")
    if ownership is None:
        raise FrameworkError("Implementation worktree ownership disappeared")
    base = ownership.get("base_revision")
    if not isinstance(base, str):
        raise FrameworkError("Implementation worktree has no durable base revision")
    head = _commit_agent_changes(
        root,
        feature,
        worktree,
        git,
        base,
        f"Implement {feature.id}",
    )
    validation = _run_validation(root, worktree, feature) if validate else _deferred_validation()
    review_output: Path | None = None
    if validate:
        with StateStore(root).lock():
            current = ArtifactStore(root).find(feature.id)
            if current.status != "review":
                ArtifactStore(root).transition(
                    feature.id,
                    "review",
                    head=head,
                    validation=validation,
                )
        _update_worktree(root, feature.id, "review", head=head, stage="committed")
        review_limit = load_config(root, "constraints").get("strategies", {}).get(
            "review_iterations", 3
        )
        if not isinstance(review_limit, int) or isinstance(review_limit, bool):
            raise FrameworkError("Review iteration limit must be an integer")
        for iteration in range(1, review_limit + 1):
            review_result, _ = _review_feature(
                root, feature, worktree, base, head, result.output, validation, iteration
            )
            review_output = review_result.output
            if review_result.status == "PASS":
                read_review(
                    review_output,
                    expected_subject=feature.id,
                    expected_head=head,
                    implementer_session=session_id,
                )
                break
            if iteration == review_limit:
                raise FrameworkError("Critical review repair budget exhausted")
            grant_implementation(
                StateStore(root),
                plan.id,
                "repair",
                revision,
                _plan_scope(ArtifactStore(root), plan),
            )
            _update_worktree(root, feature.id, "repair", head=head, stage="reviewed")
            repair = _repair_assignment(
                root,
                plan,
                feature,
                worktree,
                review_output,
                "repair",
                revision,
                iteration,
            )
            result = _dispatch_assignment(
                root,
                "implementation",
                repair,
                worktree,
                session_id,
                feature.id,
                "repair",
            )
            if result.status != "COMPLETE":
                raise FrameworkError("Repair did not return COMPLETE")
            head = _commit_agent_changes(
                root,
                feature,
                worktree,
                git,
                base,
                f"Repair {feature.id} review {iteration}",
            )
            validation = _run_validation(root, worktree, feature)
            _update_worktree(root, feature.id, "review", head=head, stage="committed")

    delivery_evidence: Any = {"status": "DEFERRED_BY_USER"}
    cleanup: Any = {"status": "DEFERRED_BY_USER"}
    merged_revision: str | None = None
    if deliver_changes:
        _update_worktree(root, feature.id, "delivery", head=head, stage="committed")
        delivery_evidence, merged_revision = _deliver_work(
            root, worktree, branch, review=review_output
        )
        cleanup = delivery_evidence.get("cleanup")
        if not isinstance(cleanup, dict) or cleanup.get("status") not in {
            "complete",
            "already_retired",
        }:
            raise FrameworkError("Delivery did not return complete cleanup evidence")
        _update_worktree(
            root,
            feature.id,
            "merged",
            head=head,
            merged_revision=merged_revision,
            delivery=delivery_evidence,
            stage="merged",
        )
    else:
        _update_worktree(root, feature.id, "completed", head=head, stage="delivery_deferred")
    with StateStore(root).lock():
        store = ArtifactStore(root)
        for task_id in feature.metadata.get("tasks", []):
            task = store.find(task_id)
            if task.status not in {"completed", "archived", "superseded"}:
                store.transition(task_id, "completed", validation=validation)
        completed = store.transition(
            feature.id,
            "completed",
            head=head,
            handoff=_relative(root, result.output),
            validation=validation,
            review=_relative(root, review_output) if review_output else None,
            delivery=delivery_evidence,
            cleanup=cleanup,
        )
    refresh_index(root)
    if deliver_changes:
        _forget_worktree(root, feature.id, cleanup)
    return {
        "status": "completed",
        "feature": completed.id,
        "head": head,
        "validation": validation,
        "delivery": delivery_evidence,
        "cleanup": cleanup,
        "blocker": None,
    }


def implement_plan(
    root: Path | str,
    plan_id: str,
    *,
    validate: bool = False,
    deliver: bool = True,
    resume: bool = False,
) -> Record:
    """Execute dependency-ready features under an explicit current plan grant."""
    root = _root(root)
    store = ArtifactStore(root)
    plan = store.find(plan_id)
    if plan.metadata.get("kind") != "plans" or plan.status in {
        "draft",
        "archived",
        "superseded",
        "completed",
    }:
        raise FrameworkError("Implementation requires a current delivered non-draft PLAN")
    if plan.metadata.get("hard_block") is not None and not resume:
        raise FrameworkError("PLAN has unresolved hard-block metadata")
    scope = _plan_scope(store, plan)
    revision = _delivered_revision(root, plan, scope)
    action = "resume" if resume else "implement"
    grant_implementation(StateStore(root), plan.id, action, revision, scope)
    outcomes: list[Record] = []
    blockers: list[Record] = []
    cleanup_outcomes: list[Record] = []

    if resume:
        if plan.metadata.get("hard_block") is not None:
            _clear_block(root, plan.id)
        for feature_id in plan.metadata.get("features", []):
            feature = ArtifactStore(root).find(feature_id)
            if feature.metadata.get("hard_block") is not None:
                _clear_block(root, feature.id)
            for task_id in feature.metadata.get("tasks", []):
                task = ArtifactStore(root).find(task_id)
                if task.metadata.get("hard_block") is not None:
                    _clear_block(root, task.id)
        try:
            cleanup_outcomes = _resume_cleanup(root, plan)
        except Exception as exc:
            blocker = _record_block(
                root,
                ArtifactStore(root).find(plan.id),
                FrameworkError(f"Resumed cleanup failed: {exc}"),
            )
            return {
                "status": "hard_blocked",
                "plan": plan_id,
                "approved_revision": revision,
                "validation": "DEFERRED_BY_USER" if not validate else "not_started",
                "features": [],
                "remaining_features": list(plan.metadata.get("features", [])),
                "cleanup": cleanup_outcomes,
                "blockers": [blocker],
            }

    while True:
        plan = ArtifactStore(root).find(plan_id)
        if plan.metadata.get("hard_block") is not None:
            break
        features = [ArtifactStore(root).find(identifier) for identifier in plan.metadata["features"]]
        pending = [feature for feature in features if feature.status != "completed"]
        if not pending:
            break
        complete = {feature.id for feature in features if feature.status == "completed"}
        ready = [
            feature
            for feature in pending
            if feature.status in {"ready", "in-progress", "review"}
            and feature.metadata.get("hard_block") is None
            and set(feature.metadata.get("dependencies", [])) <= complete
        ]
        if not ready:
            break
        progressed = False
        stop = False
        for feature in ready:
            try:
                outcome = _complete_feature(
                    root,
                    plan,
                    feature,
                    revision,
                    validate=validate,
                    deliver_changes=deliver,
                    resume=resume,
                )
                outcomes.append(outcome)
                progressed = True
                if isinstance(outcome.get("blocker"), dict):
                    blockers.append(outcome["blocker"])
                    stop = True
                    break
            except Exception as exc:
                blockers.append(_record_block(root, feature, exc))
        if not progressed or stop:
            break

    current = ArtifactStore(root).find(plan_id)
    remaining = [
        identifier
        for identifier in current.metadata["features"]
        if ArtifactStore(root).find(identifier).status != "completed"
    ]
    known = {item.get("subject") for item in blockers}
    for identifier in [plan_id, *remaining]:
        artifact = ArtifactStore(root).find(identifier)
        block = artifact.metadata.get("hard_block")
        if isinstance(block, dict) and identifier not in known:
            blockers.append({"subject": identifier, **block})
            known.add(identifier)
    if not remaining and not blockers and current.metadata.get("hard_block") is None:
        plan_validation = (
            _deferred_validation()
            if not validate
            else [
                evidence
                for identifier in current.metadata["features"]
                for evidence in ArtifactStore(root).find(identifier).metadata.get("validation", [])
            ]
        )
        with StateStore(root).lock():
            ArtifactStore(root).transition(
                plan_id,
                "completed",
                validation=plan_validation,
            )
        refresh_index(root)
    workflow_status = (
        "hard_blocked"
        if blockers
        else "completed"
        if not remaining
        else "waiting"
    )
    return {
        "status": workflow_status,
        "plan": plan_id,
        "approved_revision": revision,
        "validation": "executed" if validate else "DEFERRED_BY_USER",
        "features": outcomes,
        "remaining_features": remaining,
        "cleanup": cleanup_outcomes,
        "blockers": blockers,
    }


def _bug_assignment(
    root: Path,
    bug: Artifact,
    worktree: Path,
    branch: str,
    *,
    phase: str,
    plan: str | None = None,
    revision: str | None = None,
    investigation: Record | None = None,
) -> Path:
    scope = bug.metadata.get("scope", []) if phase == "fix" else []
    return write_handoff(
        root,
        "handoffs/bug-to-bugfix-agent.md",
        {
            "role": "bugfix",
            "subject": bug.id,
            "bug": bug.id,
            "plan": plan,
            "action": "repair" if phase == "fix" else "inspection",
            "approved_revision": revision,
            "tasks": [],
            "phase": phase,
            "description": bug.metadata.get("description", bug.body),
            "worktree": str(worktree),
            "branch": branch,
            "allowed_scope": scope,
            "prohibited_scope": [".ai"],
            "expected_behavior": bug.metadata.get("expected_behavior", "Resolve the reported bug"),
            "investigation": investigation or {},
            "regression_strategy": (investigation or {}).get("regression_strategy", "Define during investigation"),
            "validation": bug.metadata.get("validation", []),
            "context_refs": _context_refs(root, [bug]),
        },
    )


def _saved_investigation(root: Path, bug: Artifact) -> tuple[Record, Path] | None:
    reference = bug.metadata.get("investigation")
    if not isinstance(reference, str):
        return None
    output = contained(root, reference, directory=".ai")
    metadata, _ = read_markdown(output)
    if metadata.get("status") != "INVESTIGATED" or metadata.get("subject") != bug.id:
        raise FrameworkError("Stored bug investigation is malformed or belongs to another bug")
    return metadata, output


def implement_bug(
    root: Path | str,
    bug_id: str,
    *,
    validate: bool = False,
    deliver: bool = True,
) -> Record:
    """Investigate, fix and optionally deliver one canonical bug."""
    root = _root(root)
    store = ArtifactStore(root)
    bug = store.find(bug_id)
    if bug.metadata.get("kind") != "bugs" or bug.status not in {"open", "in-progress", "review"}:
        raise FrameworkError("Bug implementation requires a current BUG artifact")
    try:
        if bug.metadata.get("hard_block") is not None:
            _clear_block(root, bug.id)
            bug = ArtifactStore(root).find(bug.id)
        saved = _saved_investigation(root, bug)
        if saved is None:
            previous = _resume_record(root, bug.id, "inspection")
            investigation_assignment = (
                contained(root, previous["assignment"], directory=".ai")
                if previous is not None
                else _bug_assignment(root, bug, root, "", phase="investigation")
            )
            investigation_session = (
                str(previous["session_id"]) if previous is not None else uuid.uuid4().hex
            )
            investigation = _dispatch_assignment(
                root,
                "bugfix",
                investigation_assignment,
                root,
                investigation_session,
                bug.id,
                "inspection",
                phase="investigation",
                resume=True,
            )
            if investigation.status == "ESCALATE":
                reason = investigation.metadata.get("escalation", {}).get(
                    "reason", "Bug investigation requires external direction"
                )
                blocker = _record_block(root, bug, FrameworkError(str(reason)))
                return {
                    "status": "escalated",
                    "bug": bug.id,
                    "investigation": investigation.metadata,
                    "blocker": blocker,
                }
            if investigation.status != "INVESTIGATED":
                raise FrameworkError("Bug investigation returned an unsupported result")
            investigation_metadata = investigation.metadata
            investigation_output = investigation.output
        else:
            investigation_metadata, investigation_output = saved
        scope = scope_paths(root, investigation_metadata.get("scope", []))
        if not scope:
            raise FrameworkError("Bug investigation did not produce a bounded fix scope")
        with StateStore(root).lock():
            bug = ArtifactStore(root).find(bug.id)
            bug.metadata.update(
                scope=scope,
                acceptance=investigation_metadata.get("acceptance", []),
                validation=investigation_metadata.get("validation", []),
                investigation=_relative(root, investigation_output),
            )
            ArtifactStore(root).save(bug)
            if bug.status == "open":
                bug = ArtifactStore(root).transition(bug.id, "in-progress")

        state_value = StateStore(root).load()
        plan_id = bug.metadata.get("plan") or state_value.get("current_focus", {}).get("plan")
        if not isinstance(plan_id, str):
            raise FrameworkError("Bug fix requires a current PLAN authority context")
        plan = ArtifactStore(root).find(plan_id)
        if plan.status not in {"ready", "in-progress"}:
            raise FrameworkError("Bug fix requires a current active PLAN authority context")
        if plan.metadata.get("hard_block") is not None:
            raise FrameworkError("Bug fix PLAN authority context is hard-blocked")
        plan_scope = _plan_scope(ArtifactStore(root), plan)
        revision = _delivered_revision(root, plan, plan_scope)
        grant_implementation(StateStore(root), plan_id, "repair", revision, plan_scope)
        worktree, branch, session_id = _implementation_worktree(root, bug)
        _update_worktree(root, bug.id, "in-progress", action="repair")
        previous = _resume_record(root, bug.id, "repair")
        fix_assignment = (
            contained(root, previous["assignment"], directory=".ai")
            if previous is not None
            else _bug_assignment(
                root,
                bug,
                worktree,
                branch,
                phase="fix",
                plan=plan_id,
                revision=revision,
                investigation=investigation_metadata,
            )
        )
        result = _dispatch_assignment(
            root,
            "bugfix",
            fix_assignment,
            worktree,
            session_id,
            bug.id,
            "repair",
            phase="fix",
            resume=True,
        )
        if result.status != "COMPLETE":
            raise FrameworkError("Bug fix did not return COMPLETE")
        _, git = _runtime(root, f"bug-{bug.id.lower()}")
        ownership = _existing_worktree(root, bug.id, "implementation")
        base = ownership.get("base_revision") if ownership is not None else None
        if not isinstance(base, str):
            raise FrameworkError("Bugfix worktree has no durable base revision")
        head = _commit_agent_changes(root, bug, worktree, git, base, f"Fix {bug.id}")
        validation = _run_validation(root, worktree, bug) if validate else _deferred_validation()
        review_output: Path | None = None
        if validate:
            with StateStore(root).lock():
                ArtifactStore(root).transition(
                    bug.id,
                    "review",
                    head=head,
                    validation=validation,
                )
            _update_worktree(root, bug.id, "review", head=head, stage="committed")
            review_limit = load_config(root, "constraints").get("strategies", {}).get(
                "review_iterations", 3
            )
            if not isinstance(review_limit, int) or isinstance(review_limit, bool):
                raise FrameworkError("Review iteration limit must be an integer")
            for iteration in range(1, review_limit + 1):
                review_result, _ = _review_feature(
                    root,
                    bug,
                    worktree,
                    base,
                    head,
                    result.output,
                    validation,
                    iteration,
                )
                review_output = review_result.output
                if review_result.status == "PASS":
                    read_review(
                        review_output,
                        expected_subject=bug.id,
                        expected_head=head,
                        implementer_session=session_id,
                    )
                    break
                if iteration == review_limit:
                    raise FrameworkError("Critical review repair budget exhausted")
                _update_worktree(root, bug.id, "repair", head=head, stage="reviewed")
                repair_assignment = _repair_assignment(
                    root,
                    plan,
                    bug,
                    worktree,
                    review_output,
                    "repair",
                    revision,
                    iteration,
                    role="bugfix",
                )
                result = _dispatch_assignment(
                    root,
                    "bugfix",
                    repair_assignment,
                    worktree,
                    session_id,
                    bug.id,
                    "repair",
                    phase="fix",
                )
                if result.status != "COMPLETE":
                    raise FrameworkError("Bug repair did not return COMPLETE")
                head = _commit_agent_changes(
                    root,
                    bug,
                    worktree,
                    git,
                    base,
                    f"Repair {bug.id} review {iteration}",
                )
                validation = _run_validation(root, worktree, bug)
                _update_worktree(root, bug.id, "review", head=head, stage="committed")

        delivery_evidence: Any = {"status": "DEFERRED_BY_USER"}
        cleanup: Any = {"status": "DEFERRED_BY_USER"}
        merged_revision: str | None = None
        if deliver:
            _update_worktree(root, bug.id, "delivery", head=head, stage="committed")
            delivery_evidence, merged_revision = _deliver_work(
                root,
                worktree,
                branch,
                review=review_output,
            )
            cleanup = delivery_evidence.get("cleanup")
            if not isinstance(cleanup, dict) or cleanup.get("status") not in {
                "complete",
                "already_retired",
            }:
                raise FrameworkError("Delivery did not return complete cleanup evidence")
            _update_worktree(
                root,
                bug.id,
                "merged",
                head=head,
                merged_revision=merged_revision,
                delivery=delivery_evidence,
                stage="merged",
            )
        else:
            _update_worktree(root, bug.id, "completed", head=head, stage="delivery_deferred")
        with StateStore(root).lock():
            completed = ArtifactStore(root).transition(
                bug.id,
                "completed",
                head=head,
                handoff=_relative(root, result.output),
                validation=validation,
                review=_relative(root, review_output) if review_output else None,
                delivery=delivery_evidence,
                cleanup=cleanup,
            )
        refresh_index(root)
        if deliver:
            _forget_worktree(root, bug.id, cleanup)
        return {
            "status": "completed",
            "bug": completed.id,
            "head": head,
            "validation": validation,
            "delivery": delivery_evidence,
            "cleanup": cleanup,
            "blocker": None,
        }
    except Exception as exc:
        return {
            "status": "hard_blocked",
            "bug": bug.id,
            "validation": "DEFERRED_BY_USER" if not validate else "incomplete",
            "blocker": _record_block(root, ArtifactStore(root).find(bug.id), exc),
        }
