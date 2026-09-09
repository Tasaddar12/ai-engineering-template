"""Checked Git primitives; workflow intent remains the coordinator's responsibility.

Ownership receipts in .ai/local/worktrees survive restarts. Cleanup preserves the
branch and records its evidence; unknown, dirty, locked or active trees stay put.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .constraints import ConstraintPolicy
from .errors import FrameworkError, PolicyError
from .io import read_yaml, safe_path, utc_now, write_yaml
from .runner import CommandResult, CommandRunner

_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,99}\Z")
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9/_.-]*\Z")
_OID = re.compile(r"[a-f0-9]{40}(?:[a-f0-9]{24})?\Z")


def _ref(value: str) -> str:
    if (
        not isinstance(value, str)
        or not _REF.fullmatch(value)
        or any(token in value for token in ("..", "//", "@{"))
        or any(part.startswith(".") or part.endswith((".", ".lock")) for part in value.split("/"))
        or value.endswith("/")
    ):
        raise PolicyError(f"Invalid Git reference: {value!r}")
    return value


class Git:
    def __init__(self, root: Path, runner: CommandRunner):
        self.root = Path(root).absolute()
        if self.root != runner.root:
            raise FrameworkError("Git and runner must share the project root")
        self.runner = runner

    def _run(
        self,
        args: list[str],
        path: Path | None = None,
        *,
        expected: tuple[int, ...] = (0,),
        action: str | None = None,
    ) -> CommandResult:
        result = self.runner.run(
            ["git", *args], cwd=path or self.root, expected_exit_codes=expected, action=action
        )
        if not result.ok:
            raise FrameworkError(f"Git {args[0]} {result.status}: {result.stderr.strip()}")
        if result.stdout_truncated or result.stderr_truncated:
            raise FrameworkError(
                "Git output exceeded evidence limit; refusing incomplete observation"
            )
        if not result.output_complete:
            raise FrameworkError("Git output capture incomplete; refusing unverified observation")
        return result

    def list_worktrees(self) -> list[dict[str, Any]]:
        output = self._run(["worktree", "list", "--porcelain", "-z"]).stdout
        results: list[dict[str, Any]] = []
        current: dict[str, Any] = {}
        for field in output.split("\0"):
            if not field:
                if current:
                    results.append(current)
                    current = {}
                continue
            key, _, value = field.partition(" ")
            if key == "worktree":
                if current:
                    raise FrameworkError("Malformed Git worktree observation")
                current = {
                    "path": value,
                    "branch": "",
                    "head": "",
                    "locked": False,
                    "prunable": False,
                }
            elif key == "HEAD":
                current["head"] = value
            elif key == "branch":
                current["branch"] = value.removeprefix("refs/heads/")
            elif key in {"locked", "prunable"}:
                current[key] = True
                if value:
                    current[f"{key}_reason"] = value
            elif key not in {"detached", "bare"}:
                raise FrameworkError(f"Unknown Git worktree field: {key}")
        if current:
            results.append(current)
        for record in results:
            if not Path(record["path"]).is_absolute() or not _OID.fullmatch(record["head"]):
                raise FrameworkError("Invalid Git worktree path/revision")
        return results

    def head(self, path: Path | None = None) -> str:
        value = self._run(["rev-parse", "--verify", "HEAD"], path).stdout.strip()
        if not _OID.fullmatch(value):
            raise FrameworkError("Git did not return a commit object ID")
        return value

    def branch(self, path: Path | None = None) -> str:
        value = self._run(["rev-parse", "--abbrev-ref", "HEAD"], path).stdout.strip()
        return "" if value == "HEAD" else _ref(value)

    def status(self, path: Path | None = None) -> str:
        return self._run(["status", "--porcelain=v1", "-z", "--untracked-files=all"], path).stdout

    def diff(self, path: Path, base: str) -> str:
        return self._run(["diff", "--no-ext-diff", "--no-textconv", _ref(base), "--"], path).stdout

    def changed_files(self, path: Path, base: str) -> list[str]:
        output = self._run(
            ["diff", "--name-only", "--no-renames", "-z", _ref(base), "--"], path
        ).stdout
        untracked = self._run(["ls-files", "--others", "--exclude-standard", "-z"], path).stdout
        files = sorted(set(filter(None, (output + untracked).split("\0"))))
        for name in files:
            safe_path(path, name)
        return files

    def is_ancestor(self, commit: str, target: str = "HEAD") -> bool:
        return (
            self._run(
                ["merge-base", "--is-ancestor", _ref(commit), _ref(target)], expected=(0, 1)
            ).returncode
            == 0
        )

    def _managed(self, path: Path) -> Path:
        path = Path(path)
        if not path.is_absolute():
            path = self.root / path
        try:
            relative = path.relative_to(self.root / ".worktrees")
        except ValueError as exc:
            raise PolicyError("Worktree must be under the project's .worktrees directory") from exc
        if len(relative.parts) != 1 or not _NAME.fullmatch(relative.name):
            raise PolicyError("Managed worktree requires one portable lower-case directory name")
        return safe_path(self.root, Path(".worktrees") / relative)

    def _receipt(self, path: Path) -> Path:
        return safe_path(self.root, f".ai/local/worktrees/{path.name}.yaml")

    def create_worktree(self, name: str, branch: str, base: str = "HEAD") -> Path:
        if not _NAME.fullmatch(name):
            raise PolicyError("Invalid worktree name")
        path = self._managed(self.root / ".worktrees" / name)
        branch = _ref(branch)
        base = _ref(base)
        if not branch.startswith("codex/"):
            raise PolicyError("Managed branches must start with codex/")
        if path.exists():
            raise FrameworkError(f"Worktree path already exists: {path}")
        if self.runner.dry_run:
            self.runner.run(["git", "worktree", "add", "-b", branch, str(path), base])
            return path
        facts = self.list_worktrees()
        if any(Path(fact["path"]) == path or fact["branch"] == branch for fact in facts):
            raise FrameworkError("Worktree path or branch is already checked out")
        found = self._run(
            ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], expected=(0, 1)
        )
        if found.returncode == 0:
            raise FrameworkError("Managed branch already exists; reconcile instead of replacing it")
        base_head = self._run(["rev-parse", "--verify", f"{base}^{{commit}}"]).stdout.strip()
        if not _OID.fullmatch(base_head):
            raise FrameworkError("Base is not a commit")
        receipt = self._receipt(path)
        record = {
            "path": str(path),
            "branch": branch,
            "base": base_head,
            "status": "creating",
            "created_at": utc_now(),
        }
        if receipt.exists() and read_yaml(receipt).get("status") != "removed":
            raise FrameworkError("Existing ownership receipt requires reconciliation")
        write_yaml(receipt, record)
        self._run(["worktree", "add", "-b", branch, str(path), base_head])
        if self.head(path) != base_head or self.branch(path) != branch:
            raise FrameworkError("Created worktree differs from requested branch/base")
        write_yaml(receipt, {**record, "status": "created"})
        return path

    def commit(self, path: Path, message: str) -> str:
        path = self._managed(path)
        if not message.strip() or "\x00" in message:
            raise FrameworkError("Commit requires a nonempty message")
        if not self._owned(path):
            raise PolicyError("Commit requires a known managed worktree")
        self.runner.policy.check_action("commit")
        paths = self._run(["diff", "--name-only", "--no-renames", "-z", "HEAD", "--"], path).stdout
        paths += self._run(["ls-files", "--others", "--exclude-standard", "-z"], path).stdout
        # The coordinator separately checks feature scope; this prevents committing secrets
        # and protected control files even when a provider bypassed its own edit tools.
        policy = ConstraintPolicy(self.runner.policy.config, self.runner.policy.grants)
        policy.root = path
        policy.check_paths(filter(None, paths.split("\0")), ["."])
        deletions = self._run(
            ["diff", "--name-only", "--no-renames", "--diff-filter=D", "-z", "HEAD", "--"], path
        ).stdout
        policy.check_deletions(filter(None, deletions.split("\0")))
        self._run(["add", "--all", "--", "."], path, action="commit")
        self._run(["commit", "-m", message], path, action="commit")
        return self.head(path)

    def _owned(self, path: Path) -> dict[str, Any] | None:
        receipt = self._receipt(path)
        if not receipt.exists():
            return None
        record = read_yaml(receipt)
        if record.get("path") != str(path) or record.get("status") not in {
            "created",
            "creating",
            "removing",
        }:
            return None
        matches = [fact for fact in self.list_worktrees() if Path(fact["path"]) == path]
        if len(matches) != 1 or matches[0]["branch"] != record.get("branch"):
            return None
        # Reject a swapped .git file pointing at another repository.
        common = self._run(
            ["rev-parse", "--path-format=absolute", "--git-common-dir"], path
        ).stdout.strip()
        root_common = self._run(
            ["rev-parse", "--path-format=absolute", "--git-common-dir"]
        ).stdout.strip()
        if Path(common) != Path(root_common):
            return None
        return {**record, **matches[0]}

    def cleanup(
        self,
        path: Path,
        *,
        base: str = "HEAD",
        disposition: str | None = None,
        active: bool = False,
    ) -> bool:
        path = self._managed(path)
        _ref(base)
        if active or self.runner.dry_run:
            return False
        receipt = self._receipt(path)
        if not path.exists() and receipt.exists():
            interrupted = read_yaml(receipt)
            if (
                interrupted.get("path") == str(path)
                and interrupted.get("status") == "removing"
                and not any(Path(fact["path"]) == path for fact in self.list_worktrees())
            ):
                # The uncertain remove already happened. Record observation only.
                write_yaml(
                    receipt,
                    {
                        **interrupted,
                        "status": "removed",
                        "removed_at": utc_now(),
                        "reconciled_absence": True,
                    },
                )
                return True
        record = self._owned(path)
        if not record or record["locked"] or record["prunable"]:
            return False
        state_path = safe_path(self.root, ".ai/STATE.yaml")
        if state_path.exists():
            state = read_yaml(state_path)
            active_subjects = {*state.get("active_features", []), *state.get("open_bugs", [])}
            for entry in state.get("worktrees", []):
                if not isinstance(entry, dict) or not entry.get("path"):
                    continue
                candidate = Path(entry["path"])
                candidate = candidate if candidate.is_absolute() else self.root / candidate
                if candidate == path and (
                    entry.get("subject") in active_subjects
                    or entry.get("status")
                    not in {
                        "completed",
                        "superseded",
                        "abandoned",
                        "merged",
                    }
                ):
                    return False
        index_flags = self._run(["ls-files", "-v", "-z"], path).stdout
        if any(
            record and (record[0].islower() or record[0] == "S")
            for record in index_flags.split("\0")
        ):
            # Git status can hide edited files marked assume-unchanged/skip-worktree.
            return False
        dirty = self._run(
            ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored"], path
        ).stdout
        if dirty:
            return False
        merged = self.is_ancestor(record["head"], base)
        if not merged and disposition not in {"superseded", "abandoned"}:
            return False
        audit = {
            **record,
            "status": "removing",
            "merge_confirmed": merged,
            "base_checked": base,
            "disposition": disposition,
            "checked_at": utc_now(),
        }
        write_yaml(self._receipt(path), audit)
        self._run(["worktree", "remove", str(path)])
        write_yaml(self._receipt(path), {**audit, "status": "removed", "removed_at": utc_now()})
        return True
