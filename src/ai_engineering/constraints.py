"""Token-based command authority and repository-relative edit constraints.

Rules use ``argv_prefix``, ``effect`` (allow/approval/forbid), optional ``roles``
and ``action``. Every matching approval/action must be satisfied; forbid wins.
This checks framework tool calls, not the internals of a trusted provider process.
"""

from __future__ import annotations

import fnmatch
import re
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from .errors import FrameworkError, PolicyError
from .io import safe_path

_SHELLS = {"sh", "bash", "zsh", "fish", "cmd", "powershell", "pwsh", "wscript", "cscript"}
_GIT_READ = {
    "status",
    "diff",
    "log",
    "rev-parse",
    "merge-base",
    "show-ref",
    "check-ref-format",
    "ls-files",
}


def command_tokens(argv: Sequence[str]) -> list[str]:
    if (
        isinstance(argv, (str, bytes))
        or not argv
        or any(not isinstance(token, str) or "\x00" in token for token in argv)
    ):
        raise PolicyError("Commands require a nonempty argv list of strings without NUL")
    tokens = list(argv)
    executable = tokens[0]
    stem = Path(executable).stem.lower()
    if stem in _SHELLS or executable.lower().endswith((".cmd", ".bat", ".ps1", ".sh")):
        raise PolicyError("Shell/batch indirection is forbidden")
    if executable == sys.executable or executable.lower() in {"python", "python.exe", "python3"}:
        tokens[0] = "python"
    elif executable.lower() in {"git.exe", "gh.exe"}:
        tokens[0] = stem
    # An arbitrary absolute executable never inherits a same-basename allow rule.
    return tokens


def _prefix(tokens: list[str], prefix: list[str], *, forbidden: bool = False) -> bool:
    if tokens[: len(prefix)] == prefix:
        return True
    # Forbids on options must also match options after operands/other switches.
    if forbidden and len(prefix) >= 3 and prefix[2].startswith("-"):
        return tokens[:2] == prefix[:2] and all(
            any(token == option or token.startswith(option + "=") for token in tokens[2:])
            for option in prefix[2:]
        )
    return False


def _git_guard(tokens: list[str]) -> None:
    if Path(tokens[0]).stem.lower() != "git":
        return
    if len(tokens) < 2 or tokens[1].startswith("-"):
        raise PolicyError("Git global options/aliases are not accepted; select cwd explicitly")
    command, args = tokens[1], tokens[2:]
    if any(
        token.startswith(("--exec-path", "--config-env", "--git-dir", "--work-tree"))
        for token in args
    ):
        raise PolicyError("Git execution/context overrides are forbidden")
    push_flags = {
        "--",
        "--porcelain",
        "--set-upstream",
        "-u",
        "--dry-run",
        "-n",
        "--atomic",
        "--verbose",
        "-v",
        "--tags",
    }
    if command == "push" and any(
        token.startswith(("+", ":")) or (token.startswith("-") and token not in push_flags)
        for token in args
    ):
        raise PolicyError("Forced or destructive pushes are forbidden")
    if command == "reset":
        raise PolicyError("Hard reset is forbidden")
    if command in {"clean", "checkout", "restore"}:
        raise PolicyError("Destructive checkout/clean operations require a dedicated workflow")
    branch_flags = {
        "--",
        "--list",
        "--all",
        "--remotes",
        "--show-current",
        "--verbose",
        "-v",
        "-vv",
        "-a",
        "-r",
        "-l",
    }
    if command == "branch" and any(
        token.startswith("-") and token not in branch_flags for token in args
    ):
        raise PolicyError("Branch deletion/replacement is forbidden")
    worktree_flags = {"--", "--porcelain", "-z", "-b", "--reason"}
    if command == "worktree" and (
        not args
        or args[0] not in {"list", "add", "remove", "lock", "unlock"}
        or any(token.startswith("-") and token not in worktree_flags for token in args)
    ):
        raise PolicyError("Forced worktree operations are forbidden")
    if command in _GIT_READ and any(
        token.startswith("--")
        and len(token) > 2
        and any(
            option.startswith(token.split("=", 1)[0]) or token.startswith(option)
            for option in ("--output", "--ext-diff", "--textconv", "--no-index")
        )
        for token in args
    ):
        raise PolicyError("Read commands may not redirect output or invoke external diff drivers")


class ConstraintPolicy:
    def __init__(self, config: dict[str, Any], grants: Iterable[str] = ()):
        self.config = config
        self.grants = frozenset(grants)
        self.root = Path.cwd()

    def check_action(self, action: str) -> None:
        effect = self.config.get("external_actions", {}).get(action, "approval")
        if effect == "allow":
            return
        if effect in {"approval", "restricted"} and action in self.grants:
            return
        raise PolicyError(f"Action {action!r} requires configured authority ({effect})")

    def check_command(self, argv: Sequence[str], role: str, action: str | None = None) -> None:
        tokens = command_tokens(argv)
        _git_guard(tokens)
        permissions = self.config.get("roles", {}).get(role, {})
        if permissions.get("run_commands") is False:
            raise PolicyError(f"Role {role!r} may not run commands")
        # A reviewer never gets arbitrary interpreter/formatter/source-writing commands.
        if (role == "critical_review" or permissions.get("modify_files") is False) and (
            tokens[0] != "git" or len(tokens) < 2 or tokens[1] not in _GIT_READ
        ):
            raise PolicyError("Read-only roles may only inspect Git through this runner")
        if tokens[:2] == ["git", "worktree"] and tokens[2:3] != ["list"] and role != "orchestrator":
            raise PolicyError("Only the coordinator may change worktrees")
        rules = self.config.get("commands", {}).get("rules", [])
        matches: list[dict[str, Any]] = []
        for rule in rules:
            prefix = rule.get("argv_prefix")
            effect = rule.get("effect")
            if (
                not isinstance(prefix, list)
                or not prefix
                or effect not in {"allow", "approval", "forbid"}
            ):
                raise PolicyError("Invalid command policy rule")
            if rule.get("roles") and role not in rule["roles"]:
                continue
            if _prefix(tokens, command_tokens(prefix), forbidden=effect == "forbid"):
                matches.append(rule)
        if not matches or any(rule["effect"] == "forbid" for rule in matches):
            raise PolicyError(f"Command is not allowed for {role}: {tokens[:2]}")
        actions = {action} if action else set()
        for rule in matches:
            if rule.get("action"):
                actions.add(rule["action"])
            if rule["effect"] == "approval" and not rule.get("action"):
                raise PolicyError("Approval command rule requires an action name")
        semantic = [Path(tokens[0]).stem.lower(), *tokens[1:]]
        if semantic[:2] in (["git", "push"], ["git", "commit"], ["git", "merge"]):
            actions.add(tokens[1])
        if semantic[:3] == ["gh", "pr", "create"]:
            actions.add("pull_request")
        for requested in actions:
            self.check_action(requested)

    def check_paths(self, paths: Iterable[str | Path], allowed_scope: Iterable[str]) -> None:
        """Check edit scope. Call check_deletions for the known deletion set as well.

        Scope entries are relative file/directory roots; '.' explicitly permits the
        whole checkout, still subject to protected paths and secret patterns.
        """
        scope = list(allowed_scope)
        scope_paths = [
            self.root if value == "." else safe_path(self.root, value) for value in scope
        ]
        rules = self.config.get("files", {})
        protected = [".git", *rules.get("read_only", []), *rules.get("generated", [])]
        forbidden = [".env", ".env.*", "**/*.pem", "**/*.key", *rules.get("forbidden", [])]
        for value in paths:
            try:
                path = safe_path(self.root, value)
            except FrameworkError as exc:
                raise PolicyError(str(exc)) from exc
            relative = path.relative_to(self.root).as_posix()
            folded = relative.casefold()
            if not any(path == root or path.is_relative_to(root) for root in scope_paths):
                raise PolicyError(f"Edit outside declared scope: {relative}")
            if any(
                folded == p.casefold() or folded.startswith(p.casefold().rstrip("/") + "/")
                for p in protected
            ):
                raise PolicyError(f"Read-only/generated path: {relative}")
            if any(
                fnmatch.fnmatchcase(folded, pattern.casefold())
                or fnmatch.fnmatchcase(path.name.casefold(), pattern.casefold().removeprefix("**/"))
                for pattern in forbidden
            ):
                raise PolicyError(f"Secret/forbidden path: {relative}")
            if re.search(r"(^|/)\.git(/|$)", folded):
                raise PolicyError(f"Git administrative path: {relative}")

    def check_deletions(self, paths: Iterable[str | Path]) -> None:
        """Refuse deletion of preserved files while allowing new files and edits.

        Callers must supply actual deleted paths (for example Git's diff-filter D),
        since a nonexistent proposed path alone cannot distinguish addition/deletion.
        """
        preserve = self.config.get("files", {}).get("preserve", [])
        for value in paths:
            try:
                path = safe_path(self.root, value)
            except FrameworkError as exc:
                raise PolicyError(str(exc)) from exc
            relative = path.relative_to(self.root).as_posix().casefold()
            if any(
                relative == pattern.casefold().rstrip("/")
                or relative.startswith(pattern.casefold().rstrip("/") + "/")
                or fnmatch.fnmatchcase(relative, pattern.casefold())
                for pattern in preserve
            ):
                raise PolicyError(f"Deletion of preserved path: {value}")
