"""Small, local plan-record CLI for the foundation repository layout.

This module creates plan and task records. It does not execute plans, approve
reviews, or mark work complete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "0.2.0.dev0"
PLAN_ID = re.compile(r"^PLAN-[0-9]{3,}$")
TASK_ID = re.compile(r"^TASK-[0-9]{3,}$")
PLAN_BUCKETS = ("current", "completed", "archived")
TASK_BUCKETS = ("current", "completed", "archived")
RECORD_NAMESPACES = (".codex", ".claude", ".ai")
STRUCTURAL_TASK_FIELDS = (
    "id",
    "plan_id",
    "title",
    "objective",
    "depends_on",
    "scope",
    "acceptance_criteria",
    "plan_acceptance_ids",
    "spec_refs",
    "adr_refs",
    "research_refs",
    "input_contracts",
    "output_contracts",
    "validation_commands",
    "estimated_production_files",
    "size_rationale",
    "out_of_scope",
    "handoff_requirements",
)


class CliError(RuntimeError):
    """An expected command-line failure."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CliError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CliError(f"Expected a JSON object in {path}")
    return value


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _replace_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_write(path: Path, content: bytes) -> None:
    _replace_bytes(path, content)


def _is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def _ensure_managed_path(root: Path, path: Path) -> None:
    resolved_root = root.resolve(strict=False)
    resolved_path = path.resolve(strict=False)
    if not resolved_path.is_relative_to(resolved_root):
        raise CliError(f"managed path escapes project: {path}")
    current = path
    while current != root and current != current.parent:
        if _is_link(current):
            raise CliError(f"managed path traverses a link or junction: {current}")
        current = current.parent


def _records_root(root: Path) -> Path:
    matches = [
        root / name
        for name in RECORD_NAMESPACES
        if (root / name / "STATE.json").is_file()
        and (root / name / "framework.json").is_file()
    ]
    if not matches:
        raise CliError(f"{root} has no installed .codex, .claude, or legacy .ai workflow records")
    if len(matches) > 1:
        raise CliError(f"{root} has multiple workflow namespaces; select a project with exactly one")
    records = matches[0]
    _ensure_managed_path(root, records)
    return records


@contextmanager
def _mutation_lock(root: Path) -> Any:
    lock_path = _records_root(root) / "local" / "records.lock"
    _ensure_managed_path(root, lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise CliError(f"another record mutation is active: {lock_path}") from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        yield
    finally:
        os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def structural_task_digest(tasks: Sequence[dict[str, Any]]) -> str:
    """Hash review-relevant task contracts while excluding lifecycle fields."""
    projected = [
        {field: task[field] for field in STRUCTURAL_TASK_FIELDS}
        for task in sorted(tasks, key=lambda item: str(item["id"]))
    ]
    payload = json.dumps(projected, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _project_root(raw: str) -> Path:
    root = Path(raw).expanduser().resolve()
    _records_root(root)
    return root


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _find_plan(root: Path, plan_id: str) -> tuple[str, Path] | None:
    records = _records_root(root)
    matches = [
        (bucket, records / "plans" / bucket / plan_id)
        for bucket in PLAN_BUCKETS
        if (records / "plans" / bucket / plan_id).exists()
    ]
    if len(matches) > 1:
        raise CliError(f"{plan_id} appears in multiple lifecycle directories")
    return matches[0] if matches else None


def _task_record(
    root: Path,
    bundle: Path,
    plan_id: str,
    task_id: str,
    title: str,
    objective: str,
    depends_on: list[str],
    plan_acceptance_id: str,
) -> dict[str, Any]:
    records = _records_root(root)
    namespace = records.name
    token = f"{plan_id.lower().replace('-', '_')}_{task_id.lower().replace('-', '_')}"
    return {
        "schema_version": "1.0",
        "kind": "task",
        "id": task_id,
        "plan_id": plan_id,
        "title": title,
        "status": "backlog",
        "archived": False,
        "objective": objective,
        "depends_on": depends_on,
        "scope": {
            "write_paths": [
                f"src/{token}.py",
                f"tests/{plan_id}/{task_id}/",
                _relative(bundle / "evidence" / "implementation" / f"{task_id}.md", root),
            ],
            "read_paths": [
                _relative(bundle / "spec.json", root),
                f"{namespace}/agents/",
                f"{namespace}/workflows/",
            ],
            "prohibited_paths": [
                f"{namespace}/STATE.json",
                f"{namespace}/framework.json",
                f"{namespace}/CLAUDE.md" if namespace == ".claude" else f"{namespace}/AGENTS.md",
                f"{namespace}/project/",
                f"{namespace}/decisions/",
                f"{namespace}/research/",
                _relative(bundle / "plan.json", root),
                _relative(bundle / "graph.json", root),
                _relative(bundle / "spec.json", root),
            ],
            "resources": [f"component:{plan_id}/{task_id}"],
        },
        "acceptance_criteria": [
            {
                "id": f"{task_id}-AC1",
                "description": f"Deliver {objective.rstrip('.').lower()} with observable evidence",
                "verification": f"Run the plan-local command test.{task_id}",
            }
        ],
        "plan_acceptance_ids": [plan_acceptance_id],
        "spec_refs": [_relative(bundle / "spec.json", root)],
        "adr_refs": [],
        "research_refs": [],
        "input_contracts": [],
        "output_contracts": [f"Handoff for {plan_id}/{task_id}"],
        "validation_commands": [f"test.{task_id}"],
        "estimated_production_files": 2,
        "size_rationale": "One implementation file and one focused test area.",
        "out_of_scope": ["Unlisted paths and external side effects"],
        "handoff_requirements": ["Changed paths, actual command results, and remaining risks"],
        "attempt_ids": [],
        "superseded_by": [],
        "resume_state": None,
    }


def _command_record(plan_id: str, task_id: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "kind": "command-definition",
        "id": f"test.{task_id}",
        "argv": [
            "python",
            "-m",
            "unittest",
            "discover",
            "-s",
            f"tests/{plan_id}/{task_id}/",
            "-p",
            "test_*.py",
        ],
        "cwd_rule": "worktree",
        "timeout_seconds": 180,
        "max_output_bytes": 1048576,
        "permission_class": "local_execute",
        "environment_bindings": [],
        "shell": False,
        "platforms": ["linux", "windows"],
        "success_rule": "unittest_nonzero_count",
    }


def _write_plan_bundle(root: Path, args: argparse.Namespace) -> list[Path]:
    plan_id = args.plan_id
    if not PLAN_ID.fullmatch(plan_id):
        raise CliError("plan ID must match PLAN-NNN")
    if _find_plan(root, plan_id):
        raise CliError(f"{plan_id} already exists")

    records = _records_root(root)
    bundle = records / "plans" / "current" / plan_id
    spec_ref = _relative(bundle / "spec.json", root)
    plan_ref = _relative(bundle / "plan.md", root)
    graph_ref = _relative(bundle / "graph.json", root)
    task = _task_record(
        root,
        bundle,
        plan_id,
        "TASK-001",
        args.task_title,
        args.task_objective,
        [],
        "AC-01",
    )
    command = _command_record(plan_id, "TASK-001")
    plan = {
        "schema_version": "1.0",
        "kind": "plan",
        "id": plan_id,
        "title": args.title,
        "status": "draft",
        "archived": False,
        "spec_refs": [spec_ref],
        "adr_refs": [],
        "research_refs": [],
        "document_ref": plan_ref,
        "acceptance_criteria": [
            {"id": "AC-01", "description": args.acceptance, "verification": "Mapped task evidence"}
        ],
        "task_ids": ["TASK-001"],
        "graph_ref": graph_ref,
        "isolation_review_ref": None,
        "resume_state": "Draft specification and graph require explicit approval and isolation review",
        "integration_branch": f"ai/{plan_id}/integration",
        "target_branch": args.target_branch,
        "merge_evidence_ref": None,
    }
    graph = {
        "schema_version": "1.0",
        "kind": "task-graph",
        "id": f"{plan_id}-r1",
        "plan_id": plan_id,
        "revision": 1,
        "status": "proposed",
        "nodes": [{"task_id": "TASK-001", "depends_on": []}],
        "task_set_sha256": structural_task_digest([task]),
        "review_ref": None,
    }
    spec = {
        "schema_version": "1.0",
        "kind": "spec",
        "id": "SPEC-001",
        "title": args.title,
        "status": "draft",
        "document_ref": _relative(bundle / "spec.md", root),
        "requirements": [
            {
                "id": "REQ-001",
                "description": args.acceptance,
                "verification": "PLAN acceptance criterion AC-01 and mapped task evidence",
            }
        ],
        "adr_refs": [],
        "superseded_by": [],
    }
    plan_markdown = (
        f"# {plan_id}: {args.title}\n\n"
        "Status: isolation; the graph is proposed and cannot be implemented until an independent review passes.\n\n"
        "- [Specification](spec.md)\n"
        "- [Initial task](tasks/current/TASK-001.json)\n"
        "- [Validation command](commands/test.TASK-001.json)\n"
    ).encode("utf-8")
    spec_markdown = f"# SPEC-001: {args.title}\n\n{args.acceptance}\n".encode("utf-8")
    files = {
        bundle / "plan.json": _json_bytes(plan),
        bundle / "plan.md": plan_markdown,
        bundle / "spec.json": _json_bytes(spec),
        bundle / "spec.md": spec_markdown,
        bundle / "graph.json": _json_bytes(graph),
        bundle / "tasks" / "current" / "TASK-001.json": _json_bytes(task),
        bundle / "commands" / "test.TASK-001.json": _json_bytes(command),
    }
    directories = [bundle / "tasks" / bucket for bucket in TASK_BUCKETS]
    directories += [bundle / name for name in ("commands", "reviews", "evidence", "history")]
    directories.append(bundle / "evidence" / "implementation")
    for directory in [
        bundle / "tasks" / "completed",
        bundle / "tasks" / "archived",
        bundle / "reviews",
        bundle / "evidence" / "implementation",
        bundle / "history",
    ]:
        files[directory / ".gitkeep"] = b""
    if args.dry_run:
        return sorted([*directories, *files])

    state_path = records / "STATE.json"
    _ensure_managed_path(root, state_path)
    state = _read_json(state_path)
    active = list(state.get("active_plans", []))
    if plan_id in active:
        raise CliError(f"{plan_id} is already registered in STATE.json")
    active.append(plan_id)
    state["active_plans"] = sorted(active)
    state["generation"] = int(state.get("generation", 0)) + 1
    state["updated_at"] = datetime.now(UTC).isoformat()

    created_bundle = False
    try:
        _ensure_managed_path(root, bundle)
        bundle.mkdir()
        created_bundle = True
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=False)
        for path, content in files.items():
            if path.exists():
                raise CliError(f"Refusing to overwrite {path}")
            path.write_bytes(content)
        _atomic_write(state_path, _json_bytes(state))
    except Exception:
        if created_bundle and bundle.exists():
            shutil.rmtree(bundle)
        raise
    return sorted(files)


def _create_task(root: Path, args: argparse.Namespace) -> list[Path]:
    if not PLAN_ID.fullmatch(args.plan_id) or not TASK_ID.fullmatch(args.task_id):
        raise CliError("IDs must match PLAN-NNN and TASK-NNN")
    located = _find_plan(root, args.plan_id)
    if located is None or located[0] != "current":
        raise CliError(f"{args.plan_id} is not a current plan")
    bundle = located[1]
    _ensure_managed_path(root, bundle)
    for bucket in TASK_BUCKETS:
        if (bundle / "tasks" / bucket / f"{args.task_id}.json").exists():
            raise CliError(f"{args.plan_id}/{args.task_id} already exists")

    plan_path = bundle / "plan.json"
    graph_path = bundle / "graph.json"
    task_path = bundle / "tasks" / "current" / f"{args.task_id}.json"
    command_path = bundle / "commands" / f"test.{args.task_id}.json"
    for managed_path in (plan_path, graph_path, task_path, command_path):
        _ensure_managed_path(root, managed_path)
    plan = _read_json(plan_path)
    graph = _read_json(graph_path)
    if args.task_id in plan.get("task_ids", []):
        raise CliError(f"{args.plan_id}/{args.task_id} is already registered in plan.json")
    existing_tasks = [
        _read_json(path)
        for bucket in TASK_BUCKETS
        for path in sorted((bundle / "tasks" / bucket).glob("TASK-*.json"))
        if bucket != "archived"
    ]
    existing_ids = {str(task["id"]) for task in existing_tasks}
    dependencies = list(dict.fromkeys(args.depends_on))
    missing = sorted(set(dependencies) - existing_ids)
    if missing:
        raise CliError(f"Unknown dependencies in {args.plan_id}: {', '.join(missing)}")
    acceptance_ids = plan.get("acceptance_criteria", [])
    if not acceptance_ids:
        raise CliError(f"{args.plan_id} has no acceptance criteria")
    task = _task_record(
        root,
        bundle,
        args.plan_id,
        args.task_id,
        args.title,
        args.objective,
        dependencies,
        str(acceptance_ids[0]["id"]),
    )
    command = _command_record(args.plan_id, args.task_id)
    if command_path.exists():
        raise CliError(f"Refusing to overwrite {command_path}")

    plan["task_ids"] = [*plan.get("task_ids", []), args.task_id]
    plan["status"] = "draft" if plan.get("status") == "draft" else "isolation"
    plan["isolation_review_ref"] = None
    plan["resume_state"] = "Task contract changed; awaiting independent isolation review"
    graph["revision"] = int(graph.get("revision", 0)) + 1
    graph["id"] = f"{args.plan_id}-r{graph['revision']}"
    graph["status"] = "proposed"
    graph["review_ref"] = None
    graph["nodes"] = [*graph.get("nodes", []), {"task_id": args.task_id, "depends_on": dependencies}]
    graph["task_set_sha256"] = structural_task_digest([*existing_tasks, task])

    if args.dry_run:
        return [task_path, command_path, plan_path, graph_path]
    task_path.parent.mkdir(parents=True, exist_ok=True)
    command_path.parent.mkdir(parents=True, exist_ok=True)
    plan_before = plan_path.read_bytes()
    graph_before = graph_path.read_bytes()
    created: list[Path] = []
    try:
        task_stream = task_path.open("xb")
        created.append(task_path)
        with task_stream as stream:
            stream.write(_json_bytes(task))
        command_stream = command_path.open("xb")
        created.append(command_path)
        with command_stream as stream:
            stream.write(_json_bytes(command))
        _atomic_write(plan_path, _json_bytes(plan))
        _atomic_write(graph_path, _json_bytes(graph))
    except Exception as exc:
        repair_errors: list[str] = []
        for path, content in ((plan_path, plan_before), (graph_path, graph_before)):
            try:
                if not path.exists() or path.read_bytes() != content:
                    _replace_bytes(path, content)
            except Exception as repair_exc:
                repair_errors.append(f"restore {path.name}: {repair_exc}")
        for path in created:
            try:
                path.unlink(missing_ok=True)
            except Exception as repair_exc:
                repair_errors.append(f"remove {path.name}: {repair_exc}")
        if repair_errors:
            raise CliError(f"{exc}; rollback also reported: {'; '.join(repair_errors)}") from exc
        raise
    return [task_path, command_path, plan_path, graph_path]


def _list_plans(root: Path) -> int:
    records = _records_root(root)
    found = False
    for bucket in PLAN_BUCKETS:
        directory = records / "plans" / bucket
        for bundle in sorted(path for path in directory.glob("PLAN-*") if path.is_dir()):
            plan = _read_json(bundle / "plan.json")
            print(f"{bucket:9} {plan['id']}  {plan['status']}  {plan['title']}")
            found = True
    if not found:
        print("No plans")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and inspect local AI workload records")
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--project", default=".", help="installed project root")
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan", help="manage plan records")
    plan_commands = plan.add_subparsers(dest="plan_command", required=True)
    create_plan = plan_commands.add_parser("create", help="create a current plan with TASK-001")
    create_plan.add_argument("plan_id")
    create_plan.add_argument("--title", required=True)
    create_plan.add_argument("--acceptance", default="Deliver the plan objective with recorded validation evidence.")
    create_plan.add_argument("--task-title", default="Implement the first isolated slice")
    create_plan.add_argument("--task-objective", default="Implement the first isolated plan slice")
    create_plan.add_argument("--target-branch", default="main")
    create_plan.add_argument("--dry-run", action="store_true")
    plan_commands.add_parser("list", help="list plans by lifecycle directory")

    task = commands.add_parser("task", help="manage task records")
    task_commands = task.add_subparsers(dest="task_command", required=True)
    create_task = task_commands.add_parser("create", help="add a task to a current plan")
    create_task.add_argument("plan_id")
    create_task.add_argument("task_id")
    create_task.add_argument("--title", required=True)
    create_task.add_argument("--objective", required=True)
    create_task.add_argument("--depends-on", action="append", default=[])
    create_task.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        root = _project_root(args.project)
        if args.command == "plan" and args.plan_command == "list":
            return _list_plans(root)
        if args.command == "plan" and args.plan_command == "create":
            if args.dry_run:
                paths = _write_plan_bundle(root, args)
            else:
                with _mutation_lock(root):
                    paths = _write_plan_bundle(root, args)
        elif args.command == "task" and args.task_command == "create":
            if args.dry_run:
                paths = _create_task(root, args)
            else:
                with _mutation_lock(root):
                    paths = _create_task(root, args)
        else:
            raise CliError("Unsupported command")
        verb = "Would write" if args.dry_run else "Wrote"
        for path in paths:
            print(f"{verb} {_relative(path, root)}")
        return 0
    except CliError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
