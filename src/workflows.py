"""Installed workflow discovery and callable routing across framework APIs."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from .errors import FrameworkError
from .io import safe_path
from .templates import asset_text, iter_asset_files

WORKFLOWS = {
    path.removeprefix("workflows/").removesuffix(".md")
    for path in iter_asset_files("workflows")
    if path.endswith(".md")
}


def _workflow_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise FrameworkError("Workflow name must be a nonempty string")
    normalized = name.strip().lower().replace("_", "-")
    aliases = {
        "init": "project-init",
        "adopt": "project-init",
        "status": "state-reconciliation",
        "reconcile": "state-reconciliation",
        "review": "critical-review",
        "plan-create": "planning",
        "plan-revise": "planning",
        "plan-implement": "implementation",
        "plan-resume": "implementation",
    }
    selected = aliases.get(normalized, normalized)
    if selected not in WORKFLOWS:
        raise FrameworkError(f"Unknown workflow: {name}")
    return selected


def workflow_text(root: Path, name: str) -> str:
    selected = _workflow_name(name)
    installed = safe_path(Path(root).absolute(), f".ai/workflows/{selected}.md")
    if installed.is_file():
        try:
            return installed.read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise FrameworkError(f"Cannot read installed workflow: {selected}") from exc
    return asset_text(f"workflows/{selected}.md")


def available(root: Path) -> list[str]:
    """List shipped workflow names; installed projects may override their contents."""
    for name in sorted(WORKFLOWS):
        workflow_text(root, name)
    return sorted(WORKFLOWS)


def _required(options: dict[str, Any], name: str) -> Any:
    value = options.pop(name, None)
    if value is None:
        raise FrameworkError(f"Workflow requires {name}")
    return value


def _dispatch(
    root: Path, role: str, options: dict[str, Any], subject: str | None = None
) -> dict[str, Any]:
    from .agents import dispatch
    from .handoffs import contained, read_markdown

    assignment = Path(_required(options, "assignment"))
    if not assignment.is_absolute():
        assignment = root / assignment
    assignment = contained(root, assignment, directory=".ai")
    metadata, _ = read_markdown(assignment)
    if subject is not None and metadata.get("subject") != subject:
        raise FrameworkError("CLI subject differs from the assigned workflow subject")
    worktree = Path(_required(options, "worktree"))
    run_dir = Path(_required(options, "run_dir"))
    result = dispatch(
        root,
        role,
        assignment,
        worktree,
        run_dir,
        options.pop("provider", None),
        options.pop("session_id", None),
        phase=options.pop("phase", None),
    )
    if options:
        raise FrameworkError(f"Unknown dispatch options: {', '.join(sorted(options))}")
    return {
        "status": result.status,
        "output": str(result.output),
        "session_id": result.session_id,
        "metadata": result.metadata,
    }


def validate(root: Path, subject: str | None = None, **options: Any) -> dict[str, Any]:
    """Run configured named validation commands through the central runner."""
    from .config import load_config
    from .runner import CommandRunner

    dry_run = options.pop("dry_run", False)
    grants = options.pop("grants", ())
    selected = options.pop("commands", None)
    cwd_value = options.pop("cwd", root)
    role = options.pop("role", "orchestrator")
    tasks = options.pop("tasks", ())
    if options:
        raise FrameworkError(f"Unknown validation options: {', '.join(sorted(options))}")
    if not isinstance(dry_run, bool):
        raise FrameworkError("Validation dry_run must be boolean")
    if (
        not isinstance(role, str)
        or isinstance(tasks, (str, bytes))
        or not isinstance(tasks, (list, tuple, set))
        or any(not isinstance(task, str) for task in tasks)
    ):
        raise FrameworkError("Validation role/tasks are malformed")
    config = load_config(root, "project/commands")
    named = config.get("commands", config)
    if not isinstance(named, dict) or not named:
        raise FrameworkError("No named validation commands are configured")
    names = list(named) if selected is None else list(selected)
    if not names or any(not isinstance(name, str) or name not in named for name in names):
        raise FrameworkError("Validation commands must be configured names")
    run_dir = Path(root) / ".ai/local/validation" / uuid4().hex
    runner = CommandRunner(
        Path(root), load_config(root, "constraints"), run_dir=run_dir, dry_run=dry_run, grants=grants
    )
    results: list[dict[str, Any]] = []
    for name in names:
        command = named[name]
        if not isinstance(command, dict):
            raise FrameworkError(f"Named command {name} must be a mapping")
        if command.get("roles") and role not in command["roles"]:
            raise FrameworkError(f"Named command {name} is not allowed for role {role}")
        if command.get("workflows") and "validation" not in command["workflows"]:
            raise FrameworkError(f"Named command {name} is not allowed for validation")
        if command.get("tasks") and not set(tasks).intersection(command["tasks"]):
            raise FrameworkError(f"Named command {name} is not allowed for the assigned tasks")
        argv = command.get("argv")
        timeout = command.get("timeout", 120)
        if not isinstance(argv, list) or not all(isinstance(token, str) for token in argv):
            raise FrameworkError(f"Named command {name} requires argv")
        result = runner.run(argv, cwd=Path(cwd_value), timeout=timeout, role=role)
        results.append({"name": name, **asdict(result)})
        if result.status not in {"success", "expected_failure", "dry_run"}:
            break
    complete = len(results) == len(names) and all(
        result["status"] in {"success", "expected_failure", "dry_run"} for result in results
    )
    return {
        "status": "DRY_RUN" if dry_run else "PASS" if complete else "FAILED",
        "subject": subject,
        "commands": results,
    }


def review(root: Path, subject: str | None = None, **options: Any) -> dict[str, Any]:
    """Dispatch a fresh independent critical-review session."""
    return _dispatch(Path(root).absolute(), "critical_review", dict(options), subject)


def recover(root: Path, subject: str | None = None, **options: Any) -> dict[str, Any]:
    """Dispatch structural recovery without expanding implementation authority."""
    return _dispatch(Path(root).absolute(), "recovery", dict(options), subject)


def route(root: Path, name: str, subject: str | None = None, **options: Any) -> dict[str, Any]:
    """Route one explicit workflow name to its coordinator/runtime operation."""
    root = Path(root).expanduser().absolute()
    normalized = name.strip().lower().replace("_", "-") if isinstance(name, str) else name
    selected = _workflow_name(name)
    workflow_text(root, selected)  # Missing installed/shipped contracts fail before effects.

    if selected == "project-init":
        from .project import initialize

        return initialize(root, **options)
    if normalized == "status":
        from .orchestrator import status

        if options:
            raise FrameworkError(f"Unknown status options: {', '.join(sorted(options))}")
        return status(root)
    if selected == "planning":
        from . import orchestrator

        action = options.pop("action", None)
        if normalized == "plan-create":
            action = "create"
        elif normalized == "plan-revise":
            action = "revise"
        if action == "create":
            return orchestrator.create_plan(
                root, _required(options, "title"), _required(options, "scope")
            )
        if action == "revise":
            plan_id = subject or _required(options, "plan_id")
            return orchestrator.revise_plan(root, plan_id, **options)
        if action == "decompose":
            return _dispatch(root, "work_decomposition", options, subject)
        raise FrameworkError("Planning workflow requires create, revise or decompose action")
    if selected == "implementation":
        from .orchestrator import implement_plan

        plan_id = subject or _required(options, "plan_id")
        resume = normalized == "plan-resume" or options.pop("resume", False)
        unknown = sorted(options)
        validate_option = options.pop("validate", False)
        deliver_option = options.pop("deliver", True)
        if unknown and set(unknown) - {"validate", "deliver"}:
            raise FrameworkError(
                "Unknown implementation options: "
                + ", ".join(sorted(set(unknown) - {"validate", "deliver"}))
            )
        return implement_plan(
            root,
            plan_id,
            validate=validate_option,
            deliver=deliver_option,
            resume=resume,
        )
    if selected == "bugfix":
        from .orchestrator import implement_bug

        bug_id = subject or _required(options, "bug_id")
        unknown = sorted(set(options) - {"validate", "deliver"})
        if unknown:
            raise FrameworkError(f"Unknown bugfix options: {', '.join(unknown)}")
        return implement_bug(
            root,
            bug_id,
            validate=options.pop("validate", False),
            deliver=options.pop("deliver", True),
        )
    if selected == "validation":
        return validate(root, subject, **options)
    if selected == "critical-review":
        return review(root, subject, **options)
    if selected == "recovery":
        return recover(root, subject, **options)
    if selected == "research":
        return _dispatch(root, "research", options, subject)
    if selected == "delivery":
        from .delivery import deliver

        return deliver(
            root,
            Path(_required(options, "worktree")),
            _required(options, "branch"),
            **options,
        )
    if selected == "cleanup":
        from .cleanup import retire_worktree

        return retire_worktree(
            root,
            Path(_required(options, "worktree")),
            _required(options, "branch"),
            _required(options, "merged_revision"),
            **options,
        )
    if selected == "state-reconciliation":
        from .config import load_config
        from .git import Git
        from .runner import CommandRunner
        from .state import reconcile

        apply = options.pop("apply", False)
        grants = options.pop("grants", ())
        dry_run = options.pop("dry_run", False)
        if options:
            raise FrameworkError(f"Unknown reconciliation options: {', '.join(sorted(options))}")
        if dry_run:
            return {
                "status": "DRY_RUN",
                "apply": apply,
                "effects": [],
                "message": "Reconciliation would inspect current Git and artifact facts",
            }
        runner = CommandRunner(root, load_config(root, "constraints"), grants=grants)
        return reconcile(root, Git(root, runner), apply=apply)
    raise FrameworkError(f"Workflow is documented but not callable: {selected}")
