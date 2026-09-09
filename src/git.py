"""Checked Git primitives for fixed managed worktrees and exact ref lifecycle."""

from __future__ import annotations

import re
import shlex
import shutil
import os
import stat
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .constraints import ConstraintPolicy
from .errors import FrameworkError, PolicyError
from .io import read_yaml, safe_path, utc_now, write_yaml
from .runner import CommandResult, CommandRunner

_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,99}\Z")
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9/_.-]*\Z")
_OID = re.compile(r"[a-f0-9]{40}(?:[a-f0-9]{24})?\Z")
_SESSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{7,127}\Z")


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


def _oid(value: str) -> str:
    if not isinstance(value, str) or not _OID.fullmatch(value):
        raise FrameworkError(f"Expected a full Git object ID, got {value!r}")
    return value


def _repository_url(value: str) -> str:
    if not isinstance(value, str) or not value or any(char in value for char in "\r\n\0"):
        raise FrameworkError("Repository identity is empty or malformed")
    if "://" in value:
        parsed = urlsplit(value)
        if parsed.username or parsed.password or not parsed.hostname:
            raise FrameworkError("Repository identity must not contain credentials")
        path = parsed.path.strip("/").removesuffix(".git")
        if not path:
            raise FrameworkError("Repository URL has no repository path")
        return f"{parsed.hostname.casefold()}/{path}"
    scp = re.fullmatch(r"(?:[^@/:]+@)?([^:/]+):(.+)", value)
    if scp:
        return f"{scp.group(1).casefold()}/{scp.group(2).strip('/').removesuffix('.git')}"
    path = Path(value)
    if path.is_absolute():
        return str(path.absolute())
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        return value.removesuffix(".git")
    raise FrameworkError("Repository identity must be an owner/name, safe URL, or absolute path")


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
            detail = result.stderr.strip() or result.stdout.strip()
            raise FrameworkError(f"Git {args[0]} {result.status}: {detail}")
        if result.stdout_truncated or result.stderr_truncated or not result.output_complete:
            raise FrameworkError("Git output was incomplete; refusing an unverified observation")
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
                current = {"path": value, "branch": "", "head": "", "locked": False, "prunable": False}
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
            if record["branch"]:
                _ref(record["branch"])
        return results

    def head(self, path: Path | None = None) -> str:
        return _oid(self._run(["rev-parse", "--verify", "HEAD"], path).stdout.strip())

    def resolve(self, revision: str, path: Path | None = None) -> str:
        revision = _ref(revision)
        return _oid(
            self._run(["rev-parse", "--verify", f"{revision}^{{commit}}"], path).stdout.strip()
        )

    def branch(self, path: Path | None = None) -> str:
        value = self._run(["rev-parse", "--abbrev-ref", "HEAD"], path).stdout.strip()
        return "" if value == "HEAD" else _ref(value)

    def status(self, path: Path | None = None, *, ignored: bool = False) -> str:
        args = ["status", "--porcelain=v1", "-z", "--untracked-files=all"]
        if ignored:
            args.append("--ignored")
        return self._run(args, path).stdout

    def diff(self, path: Path, base: str) -> str:
        return self._run(["diff", "--no-ext-diff", "--no-textconv", _ref(base), "--"], path).stdout

    def changed_files(self, path: Path, base: str) -> list[str]:
        output = self._run(["diff", "--name-only", "--no-renames", "-z", _ref(base), "--"], path).stdout
        untracked = self._run(["ls-files", "--others", "--exclude-standard", "-z"], path).stdout
        files = sorted(set(filter(None, (output + untracked).split("\0"))))
        for name in files:
            safe_path(path, name)
        return files

    def dirty_files(self, path: Path | None = None) -> list[str]:
        return self.changed_files(path or self.root, "HEAD")

    def clean_except(self, paths: set[str], path: Path | None = None) -> bool:
        return set(self.dirty_files(path)) <= paths

    def is_ancestor(self, commit: str, target: str = "HEAD") -> bool:
        return self._run(
            ["merge-base", "--is-ancestor", _ref(commit), _ref(target)], expected=(0, 1)
        ).returncode == 0

    def repository_identity(self, remote: str = "origin") -> str:
        remote = _ref(remote)
        observed = self._run(["remote", "get-url", remote], expected=(0, 2)).stdout.strip()
        if observed:
            return _repository_url(observed)
        common = self._run(["rev-parse", "--path-format=absolute", "--git-common-dir"]).stdout.strip()
        path = Path(common)
        if not path.is_absolute():
            raise FrameworkError("Git common directory is not absolute")
        return str(path.absolute())

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

    def create_worktree(
        self,
        name: str,
        branch: str,
        base: str = "HEAD",
        *,
        purpose: str | None = None,
        subject: str | None = None,
        session_id: str | None = None,
        remote: str = "origin",
    ) -> Path:
        if not _NAME.fullmatch(name):
            raise PolicyError("Invalid worktree name")
        path = self._managed(self.root / ".worktrees" / name)
        branch, base, remote = _ref(branch), _ref(base), _ref(remote)
        if not branch.startswith("codex/"):
            raise PolicyError("Managed branches must start with codex/")
        if purpose is not None and purpose not in {"planning", "implementation", "bugfix", "recovery"}:
            raise PolicyError("Managed worktree has an unsupported purpose")
        if subject is not None and (not isinstance(subject, str) or not subject.strip()):
            raise FrameworkError("Managed worktree subject must be nonempty")
        if session_id is not None and not _SESSION.fullmatch(session_id):
            raise FrameworkError("Managed worktree session has an invalid identity")
        if path.exists():
            raise FrameworkError(f"Worktree path already exists: {path}")
        if self.runner.dry_run:
            self.runner.run(["git", "worktree", "add", "-b", branch, str(path), base])
            return path
        facts = self.list_worktrees()
        if any(Path(fact["path"]) == path or fact["branch"] == branch for fact in facts):
            raise FrameworkError("Worktree path or branch is already checked out")
        if self._run(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], expected=(0, 1)).returncode == 0:
            raise FrameworkError("Managed branch already exists; reconcile instead of replacing it")
        base_head = self.resolve(base)
        receipt = self._receipt(path)
        record = {
            "path": str(path),
            "branch": branch,
            "base": base_head,
            "repository": self.repository_identity(remote),
            "purpose": purpose,
            "subject": subject,
            "session_id": session_id,
            "owner_status": "unassigned",
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

    def _owned(self, path: Path) -> dict[str, Any] | None:
        path = self._managed(path)
        receipt = self._receipt(path)
        if not receipt.exists():
            return None
        record = read_yaml(receipt)
        if record.get("path") != str(path) or record.get("status") not in {"created", "creating", "removing"}:
            return None
        matches = [fact for fact in self.list_worktrees() if Path(fact["path"]) == path]
        if len(matches) != 1 or matches[0]["branch"] != record.get("branch"):
            return None
        common = self._run(["rev-parse", "--path-format=absolute", "--git-common-dir"], path).stdout.strip()
        root_common = self._run(["rev-parse", "--path-format=absolute", "--git-common-dir"]).stdout.strip()
        if Path(common).absolute() != Path(root_common).absolute():
            return None
        return {**record, **matches[0]}

    def verify_assignment(
        self,
        path: Path,
        *,
        branch: str,
        repository: str,
        purpose: str,
        session_id: str,
    ) -> dict[str, Any]:
        path = self._managed(path)
        record = self._owned(path)
        if not record:
            raise FrameworkError("Assignment worktree is not a registered owned checkout")
        expected = {
            "branch": _ref(branch),
            "repository": _repository_url(repository),
            "purpose": purpose,
            "session_id": session_id,
        }
        actual = {
            "branch": record.get("branch"),
            "repository": record.get("repository"),
            "purpose": record.get("purpose"),
            "session_id": record.get("session_id"),
        }
        if (
            record.get("owner_status") == "unassigned"
            and actual["branch"] == expected["branch"]
            and actual["repository"] == expected["repository"]
            and actual["purpose"] is None
            and actual["session_id"] is None
        ):
            # Older create_worktree callers use the preserved three-argument API.
            # Bind its otherwise-unassigned receipt exactly once before provider launch.
            record = {**record, "purpose": purpose, "session_id": session_id}
            write_yaml(self._receipt(path), record)
            actual = expected
        if actual != expected or record.get("locked") or record.get("prunable"):
            raise FrameworkError("Assignment no longer matches its fixed worktree ownership")
        if self.branch(path) != expected["branch"]:
            raise FrameworkError("Managed worktree branch drift detected")
        return record

    def mark_owner(self, path: Path, session_id: str, status: str) -> None:
        path = self._managed(path)
        if status not in {"running", "stopped"} or not _SESSION.fullmatch(session_id):
            raise FrameworkError("Invalid worktree owner transition")
        record = self._owned(path)
        if not record or record.get("session_id") != session_id:
            raise FrameworkError("Cannot update an unbound worktree owner")
        write_yaml(
            self._receipt(path),
            {**record, "owner_status": status, "owner_observed_at": utc_now()},
        )

    def commit(self, path: Path, message: str) -> str:
        path = self._managed(path)
        if not message.strip() or "\0" in message or not self._owned(path):
            raise FrameworkError("Commit requires an owned worktree and nonempty message")
        self.runner.policy.check_action("commit")
        paths = self._run(["diff", "--name-only", "--no-renames", "-z", "HEAD", "--"], path).stdout
        paths += self._run(["ls-files", "--others", "--exclude-standard", "-z"], path).stdout
        policy = ConstraintPolicy(self.runner.policy.config, self.runner.policy.grants)
        policy.root = path
        policy.check_paths(filter(None, paths.split("\0")), ["."])
        deletions = self._run(["diff", "--name-only", "--no-renames", "--diff-filter=D", "-z", "HEAD", "--"], path).stdout
        policy.check_deletions(filter(None, deletions.split("\0")))
        self._run(["add", "--all", "--", "."], path, action="commit")
        self._run(["commit", "-m", message], path, action="commit")
        return self.head(path)

    def fetch(self, remote: str, branch: str) -> str:
        remote, branch = _ref(remote), _ref(branch)
        self._run(["fetch", "--no-tags", remote, branch], action="push")
        return self.resolve(f"{remote}/{branch}")

    def _push(self, remote: str, arguments: list[str], path: Path, *, action: str) -> CommandResult:
        """Use existing GitHub CLI auth only for this exact authorized push."""
        identity = self.repository_identity(remote)
        if not identity.casefold().startswith("github.com/"):
            return self.runner.run(["git", "push", "--porcelain", remote, *arguments], cwd=path, action=action)
        repository = identity.partition("/")[2]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise FrameworkError("GitHub push requires an exact owner/repository")
        self.runner.policy.check_action("credentials")
        helper = Path(self.runner._executable(["gh"])[0]).resolve(strict=True)
        if helper.is_relative_to(self.root.resolve(strict=True)):
            raise PolicyError("GitHub credential helper must be installed outside the project")
        argv = ["git", "push", "--porcelain", f"https://github.com/{repository}.git", *arguments]
        helper_command = "!" + shlex.quote(helper.as_posix()) + " auth git-credential"

        class AuthenticatedPush(CommandRunner):
            def _environment(self, tokens: list[str]) -> dict[str, str]:
                env = super()._environment(tokens)
                if tokens != argv:
                    return env
                count = int(env.get("GIT_CONFIG_COUNT", "0"))
                for key, value in (
                    ("credential.https://github.com.helper", helper_command),
                    ("credential.https://github.com.useHttpPath", "true"),
                ):
                    env[f"GIT_CONFIG_KEY_{count}"] = key
                    env[f"GIT_CONFIG_VALUE_{count}"] = value
                    count += 1
                env["GIT_CONFIG_COUNT"] = str(count)
                return env

        runner = AuthenticatedPush(self.root, self.runner.policy.config, run_dir=self.runner.run_dir,
                                   dry_run=self.runner.dry_run, grants=self.runner.policy.grants)
        return runner.run(argv, cwd=path, action=action)

    def push_branch(self, path: Path, remote: str, branch: str, expected_head: str) -> None:
        path = self._managed(path)
        remote, branch, expected_head = _ref(remote), _ref(branch), _oid(expected_head)
        if self.branch(path) != branch or self.head(path) != expected_head:
            raise FrameworkError("Refusing to push a moved worktree branch")
        result = self._push(remote, [f"{expected_head}:refs/heads/{branch}"], path, action="push")
        observed = self.remote_head(remote, branch)
        if observed != expected_head:
            detail = result.stderr.strip() or result.stdout.strip()
            raise FrameworkError(
                "Pushed branch is not confirmed at the expected head; "
                f"reconcile before another write ({detail})"
            )

    def remote_head(self, remote: str, branch: str) -> str | None:
        remote, branch = _ref(remote), _ref(branch)
        output = self._run(
            ["ls-remote", "--heads", "--refs", remote, f"refs/heads/{branch}"], action="push"
        ).stdout
        if not output:
            return None
        lines = output.splitlines()
        expected_ref = f"refs/heads/{branch}"
        if len(lines) != 1:
            raise FrameworkError("Remote branch observation was ambiguous")
        observed, separator, refname = lines[0].partition("\t")
        if separator != "\t" or refname != expected_ref:
            raise FrameworkError("Remote branch observation returned an unexpected ref")
        return _oid(observed)

    def coordinator_changes(self) -> set[str]:
        controls = (".ai/plans/", ".ai/tasks/", ".ai/features/", ".ai/bugs/", ".ai/reviews/", ".ai/handoffs/")
        return {name for name in self.dirty_files()
                if name == ".ai/STATE.yaml" or name.startswith(controls)}

    def has_product_changes(self) -> bool:
        return bool(set(self.dirty_files()) - self.coordinator_changes())

    def _clear_owned_scratch(self, path: Path) -> bool:
        ignored = self._run(["ls-files", "--others", "--ignored", "--exclude-standard", "-z"], path).stdout
        targets: set[Path] = set()
        for name in filter(None, ignored.split("\0")):
            item = Path(name)
            if item.name.startswith(".env") or item.suffix.lower() in {".key", ".pem"}:
                return False
            parts = item.parts
            if name.startswith(".ai/local/"):
                relative = Path(".ai/local")
            elif parts[0] in {".pytest_cache", ".mypy_cache", ".ruff_cache"}:
                relative = Path(parts[0])
            elif "__pycache__" in parts:
                relative = Path(*parts[:parts.index("__pycache__") + 1])
            else:
                return False
            targets.add(safe_path(path, relative))
        for target in sorted(targets, key=lambda value: len(value.parts), reverse=True):
            if not target.exists():
                continue
            checked = target.resolve(strict=True)
            if checked == path.resolve(strict=True) or not checked.is_relative_to(path.resolve(strict=True)):
                raise PolicyError("Owned scratch cleanup escaped its managed worktree")
            def retry(func: Any, candidate: str, error: Any) -> None:
                if not isinstance(error[1], PermissionError) or not Path(candidate).absolute().is_relative_to(checked):
                    raise error[1]
                os.chmod(candidate, stat.S_IREAD | stat.S_IWRITE)
                func(candidate)
            shutil.rmtree(checked, onerror=retry)
        return True

    def synchronize(
        self,
        base: str,
        remote: str = "origin",
        *,
        allowed_dirty: set[str] | None = None,
    ) -> str:
        base, remote = _ref(base), _ref(remote)
        remote_head = self.fetch(remote, base)
        permitted = allowed_dirty or set()
        dirty = set(self.dirty_files())
        if self.branch() != base or not dirty <= permitted:
            raise FrameworkError(
                "Local integration checkout has unexpected changes or is not on the base branch"
            )
        local = self.head()
        if local != remote_head:
            if not self.is_ancestor(local, f"{remote}/{base}"):
                raise FrameworkError("Local integration branch has diverged from its remote")
            changed = set(
                filter(
                    None,
                    self._run(
                        ["diff", "--name-only", "-z", local, remote_head, "--"]
                    ).stdout.split("\0"),
                )
            )
            if dirty & changed:
                raise FrameworkError(
                    "Remote integration changes overlap coordinator-owned local state"
                )
            self._run(["merge", "--ff-only", f"{remote}/{base}"], action="merge")
        if self.head() != remote_head:
            raise FrameworkError("Local integration branch did not synchronize exactly")
        return remote_head

    def delete_local_branch(self, branch: str, expected_head: str, *, base: str = "main") -> bool:
        branch, base, expected_head = _ref(branch), _ref(base), _oid(expected_head)
        if branch == base or not branch.startswith("codex/"):
            raise PolicyError("Only an exact merged managed branch may be retired")
        observed = self._run(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], expected=(0, 1))
        if observed.returncode == 1:
            return True
        if self.resolve(branch) != expected_head or not self.is_ancestor(expected_head, base):
            raise FrameworkError("Local branch moved or is not merged into the integration branch")
        self._run(["branch", "-d", "--", branch], action="branch_retirement")
        return self._run(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], expected=(0, 1)).returncode == 1

    def delete_remote_branch(self, remote: str, branch: str, expected_head: str) -> bool:
        remote, branch, expected_head = _ref(remote), _ref(branch), _oid(expected_head)
        if not branch.startswith("codex/"):
            raise PolicyError("Only an exact managed remote branch may be retired")
        observed = self.remote_head(remote, branch)
        if observed is None:
            return True
        if observed != expected_head:
            raise FrameworkError("Remote branch advanced after merge; refusing deletion")
        result = self._push(remote, ["--delete", branch], self.root, action="branch_retirement")
        remaining = self.remote_head(remote, branch)
        if remaining is None:
            return True
        if remaining != expected_head:
            raise FrameworkError("Remote branch advanced during retirement")
        detail = result.stderr.strip() or result.stdout.strip()
        raise FrameworkError(
            "Remote branch deletion is not confirmed; reconcile before retry " f"({detail})"
        )

    def cleanup(
        self,
        path: Path,
        *,
        base: str = "HEAD",
        disposition: str | None = None,
        active: bool = False,
        merged_revision: str | None = None,
    ) -> bool:
        """Remove only an owned, clean, stopped, merged worktree; retain its branch."""

        path, base = self._managed(path), _ref(base)
        if active or self.runner.dry_run:
            return False
        receipt = self._receipt(path)
        if not path.exists() and receipt.exists():
            interrupted = read_yaml(receipt)
            if interrupted.get("path") == str(path) and interrupted.get("status") == "removing" and not any(
                Path(fact["path"]) == path for fact in self.list_worktrees()
            ):
                write_yaml(receipt, {**interrupted, "status": "removed", "removed_at": utc_now(), "reconciled_absence": True})
                return True
        record = self._owned(path)
        if not record or record["locked"] or record["prunable"] or record.get("owner_status") == "running":
            return False
        if self.branch(path) != record.get("branch"):
            return False
        index_flags = self._run(["ls-files", "-v", "-z"], path).stdout
        if any(item and (item[0].islower() or item[0] == "S") for item in index_flags.split("\0")):
            return False
        if self.dirty_files(path):
            return False
        head = self.head(path)
        if merged_revision is not None and head != _oid(merged_revision):
            return False
        merged = self.is_ancestor(head, base)
        if not merged and disposition not in {"superseded", "abandoned"}:
            return False
        audit = {
            **record,
            "head": head,
            "status": "removing",
            "merge_confirmed": merged,
            "base_checked": base,
            "disposition": disposition,
            "checked_at": utc_now(),
        }
        if not self._clear_owned_scratch(path):
            return False
        write_yaml(receipt, audit)
        self._run(["worktree", "remove", str(path)])
        write_yaml(receipt, {**audit, "status": "removed", "removed_at": utc_now()})
        return True
