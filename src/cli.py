"""Command-line entry point for installed coordinator workflows."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Sequence

from .errors import FrameworkError
from .io import read_yaml
from .workflows import route


def _parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", type=Path, default=Path.cwd(), help="project root")
    parser = argparse.ArgumentParser(
        prog="ai", description="Run constrained AI engineering workflows", parents=[common]
    )
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="initialize or adopt a project")
    init.add_argument("path", nargs="?", type=Path, default=Path.cwd())
    init.add_argument("--name")
    init.add_argument("--adopt", action="store_true")
    init.add_argument("--dry-run", action="store_true")

    commands.add_parser("status", help="show durable lifecycle status")

    plan = commands.add_parser("plan", help="plan and implementation operations")
    plan_commands = plan.add_subparsers(dest="plan_command", required=True)
    create = plan_commands.add_parser("create", help="create a planning worktree")
    create.add_argument("title")
    create.add_argument("--scope", action="append", required=True, metavar="PATH")
    revise = plan_commands.add_parser("revise", help="create a forward planning revision")
    revise.add_argument("plan_id")
    revise.add_argument("--title")
    revise.add_argument("--scope", action="append", metavar="PATH")
    revise.add_argument("--changes", type=Path, help="YAML mapping of plan changes")
    for name in ("implement", "resume"):
        operation = plan_commands.add_parser(name, help=f"{name} an explicitly authorized plan")
        operation.add_argument("plan_id")
        operation.add_argument("--validate", action="store_true")
        operation.add_argument("--no-deliver", action="store_true")

    bugfix = commands.add_parser("bugfix", help="investigate and implement a canonical bug")
    bugfix.add_argument("bug_id")
    bugfix.add_argument("--validate", action="store_true")
    bugfix.add_argument("--no-deliver", action="store_true")

    validation = commands.add_parser("validate", help="run configured named validation")
    validation.add_argument("subject", nargs="?")
    validation.add_argument("--command", action="append", dest="validation_commands")
    validation.add_argument("--cwd", type=Path)
    validation.add_argument("--dry-run", action="store_true")
    validation.add_argument("--grant", action="append", default=[])

    def dispatch_parser(name: str, help_text: str) -> argparse.ArgumentParser:
        operation = commands.add_parser(name, help=help_text)
        operation.add_argument("subject")
        operation.add_argument("--assignment", type=Path, required=True)
        operation.add_argument("--worktree", type=Path, required=True)
        operation.add_argument("--run-dir", type=Path, required=True)
        operation.add_argument("--session-id")
        return operation

    dispatch_parser("review", "dispatch a fresh independent critical review")
    dispatch_parser("recovery", "dispatch structural recovery")
    dispatch_parser("research", "dispatch bounded read-only research")

    delivery = commands.add_parser("delivery", help="deliver a reviewed branch to main")
    delivery.add_argument("worktree", type=Path)
    delivery.add_argument("branch")
    delivery.add_argument("--base", default="main")
    delivery.add_argument("--repository")
    delivery.add_argument("--run-tests", action="store_true")

    cleanup = commands.add_parser("cleanup", help="retire an exact merged worktree and branch")
    cleanup.add_argument("worktree", type=Path)
    cleanup.add_argument("branch")
    cleanup.add_argument("merged_revision")
    cleanup.add_argument("--base", default="main")
    cleanup.add_argument("--local-only", action="store_true")

    reconcile = commands.add_parser("reconcile", help="compare or repair state from facts")
    reconcile.add_argument("--apply", action="store_true")
    reconcile.add_argument("--dry-run", action="store_true")
    reconcile.add_argument("--grant", action="append", default=[])
    return parser


def _changes(args: argparse.Namespace) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    if args.changes:
        changes.update(read_yaml(args.changes.absolute()))
    if args.title is not None:
        changes["title"] = args.title
    if args.scope is not None:
        changes["scope"] = args.scope
    if not changes:
        raise FrameworkError("Plan revision requires --title, --scope or --changes")
    return changes


def _dispatch_options(args: argparse.Namespace) -> dict[str, Any]:
    options = {
        "assignment": args.assignment,
        "worktree": args.worktree,
        "run_dir": args.run_dir,
    }
    if args.session_id:
        options["session_id"] = args.session_id
    return options


def _execute(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.expanduser().absolute()
    if args.command == "init":
        return route(
            args.path.expanduser().absolute(),
            "project-init",
            name=args.name,
            adopt=args.adopt,
            dry_run=args.dry_run,
        )
    if args.command == "status":
        return route(root, "status")
    if args.command == "plan":
        if args.plan_command == "create":
            return route(root, "plan-create", title=args.title, scope=args.scope)
        if args.plan_command == "revise":
            return route(root, "plan-revise", args.plan_id, **_changes(args))
        return route(
            root,
            "plan-resume" if args.plan_command == "resume" else "plan-implement",
            args.plan_id,
            validate=args.validate,
            deliver=not args.no_deliver,
        )
    if args.command == "bugfix":
        return route(
            root,
            "bugfix",
            args.bug_id,
            validate=args.validate,
            deliver=not args.no_deliver,
        )
    if args.command == "validate":
        return route(
            root,
            "validation",
            args.subject,
            commands=args.validation_commands,
            cwd=args.cwd or root,
            dry_run=args.dry_run,
            grants=args.grant,
        )
    if args.command in {"review", "recovery", "research"}:
        return route(root, args.command, args.subject, **_dispatch_options(args))
    if args.command == "delivery":
        return route(
            root,
            "delivery",
            worktree=args.worktree,
            branch=args.branch,
            base=args.base,
            repository=args.repository,
            run_tests=args.run_tests,
        )
    if args.command == "cleanup":
        return route(
            root,
            "cleanup",
            worktree=args.worktree,
            branch=args.branch,
            merged_revision=args.merged_revision,
            base=args.base,
            remote=not args.local_only,
        )
    if args.command == "reconcile":
        return route(
            root,
            "state-reconciliation",
            apply=args.apply,
            dry_run=args.dry_run,
            grants=args.grant,
        )
    raise FrameworkError(f"Unsupported command: {args.command}")


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    try:
        result = _execute(parser.parse_args(argv))
    except (FrameworkError, OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, default=_json_default))
    return 0
