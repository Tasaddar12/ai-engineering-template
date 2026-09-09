"""Exact managed-worktree retirement and explicitly inventoried obsolete deletion."""

from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path
from typing import Any, Iterable

from .config import load_config
from .errors import FrameworkError, PolicyError
from .git import Git
from .io import is_link, read_yaml, safe_path, utc_now, write_yaml
from .runner import CommandRunner

_OID = re.compile(r"[a-f0-9]{40}(?:[a-f0-9]{24})?\Z")
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9/_.-]*\Z")
_PROTECTED = {
    ".git",
    ".ai/STATE.yaml",
    ".ai/plans/active/PLAN-003.md",
    ".ai/local/runtime",
}
_SECRET_PATTERNS = {".env", ".env.*", "*.pem", "*.key"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def _deletion_path(root: Path, relative: str) -> Path:
    path = safe_path(root, relative)
    normalized = path.relative_to(root).as_posix()
    if any(
        normalized == protected or normalized.startswith(protected.rstrip("/") + "/")
        for protected in _PROTECTED
    ):
        raise PolicyError(f"Obsolete deletion cannot target current protected data: {relative}")
    if normalized == ".git" or "/.git/" in f"/{normalized}/":
        raise PolicyError("Obsolete deletion cannot target Git administration data")
    if any(path.match(pattern) for pattern in _SECRET_PATTERNS):
        raise PolicyError("Obsolete deletion cannot target a secret-bearing path")
    if is_link(path):
        raise PolicyError("Obsolete deletion refuses links and junctions")
    return path


def inventory_obsolete(root: Path, paths: Iterable[str]) -> list[dict[str, Any]]:
    """Observe exact candidate paths without inferring or recursively expanding scope."""

    root = Path(root).absolute()
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for relative in paths:
        if not isinstance(relative, str) or relative in seen:
            raise FrameworkError("Obsolete inventory paths must be unique strings")
        seen.add(relative)
        path = _deletion_path(root, relative)
        if path.is_file():
            result.append(
                {
                    "path": relative,
                    "kind": "file",
                    "sha256": _sha256(path),
                    "observed": "present",
                }
            )
        elif path.is_dir():
            children = sorted(child.name for child in path.iterdir())
            result.append(
                {
                    "path": relative,
                    "kind": "directory",
                    "children": children,
                    "observed": "present",
                }
            )
        elif path.exists():
            raise FrameworkError(f"Unsupported obsolete candidate type: {relative}")
        else:
            result.append({"path": relative, "kind": "absent", "observed": "absent"})
    return result


def delete_obsolete(
    root: Path,
    inventory: Iterable[dict[str, Any]],
    *,
    authority: bool = False,
) -> dict[str, Any]:
    """Delete only unchanged, quiescent entries from an explicit reviewed inventory.

    Directories are removed only after their individually inventoried children and
    only when empty. There is intentionally no recursive deletion primitive here.
    """

    root = Path(root).absolute()
    records = list(inventory)
    if not records or not all(isinstance(record, dict) for record in records):
        raise FrameworkError("Obsolete deletion requires a nonempty structured inventory")
    constraints = load_config(root, "constraints")
    runner = CommandRunner(
        root,
        constraints,
        grants={"obsolete_content_deletion"} if authority else (),
    )
    paths = [record.get("path") for record in records]
    if not all(isinstance(path, str) for path in paths) or len(set(paths)) != len(paths):
        raise FrameworkError("Obsolete inventory paths must be unique strings")
    runner.policy.check_cleanup("obsolete_content_deletion", paths)
    checked: list[tuple[Path, dict[str, Any]]] = []
    for record in records:
        if set(record) - {
            "path",
            "kind",
            "sha256",
            "children",
            "observed",
            "replacement",
            "owner",
            "quiescent",
            "disposition",
        }:
            raise FrameworkError(f"Unknown obsolete inventory fields for {record.get('path')}")
        relative = record["path"]
        if record.get("quiescent") is not True or record.get("owner") not in {None, "stopped"}:
            raise FrameworkError(f"Obsolete candidate is not quiescent: {relative}")
        if not isinstance(record.get("replacement"), str) or not record["replacement"].strip():
            raise FrameworkError(f"Obsolete candidate lacks a retained replacement: {relative}")
        path = _deletion_path(root, relative)
        kind = record.get("kind")
        if kind == "absent":
            if path.exists():
                raise FrameworkError(f"Previously absent obsolete candidate appeared: {relative}")
        elif kind == "file":
            if not path.is_file() or not isinstance(record.get("sha256"), str):
                raise FrameworkError(f"Obsolete file observation changed: {relative}")
            if _sha256(path) != record["sha256"]:
                raise FrameworkError(f"Obsolete file changed after inventory: {relative}")
        elif kind == "directory":
            if not path.is_dir() or not isinstance(record.get("children"), list):
                raise FrameworkError(f"Obsolete directory observation changed: {relative}")
            if sorted(child.name for child in path.iterdir()) != sorted(record["children"]):
                raise FrameworkError(f"Obsolete directory changed after inventory: {relative}")
        else:
            raise FrameworkError(f"Unsupported obsolete inventory kind for {relative}")
        checked.append((path, record))
    receipt = safe_path(root, f".ai/local/cleanup/purge-{uuid.uuid4().hex}.yaml")
    write_yaml(
        receipt,
        {
            "status": "deleting",
            "authorized": True,
            "checked_at": utc_now(),
            "inventory": records,
        },
    )
    removed: list[str] = []
    for path, record in checked:
        if record["kind"] == "file":
            path.unlink()
            removed.append(record["path"])
    directories = sorted(
        ((path, record) for path, record in checked if record["kind"] == "directory"),
        key=lambda item: len(item[0].parts),
        reverse=True,
    )
    for path, record in directories:
        try:
            path.rmdir()
        except OSError as exc:
            write_yaml(
                receipt,
                {
                    "status": "incomplete",
                    "authorized": True,
                    "checked_at": utc_now(),
                    "inventory": records,
                    "removed": removed,
                    "error": str(exc),
                },
            )
            raise FrameworkError(f"Obsolete directory is not empty: {record['path']}") from exc
        removed.append(record["path"])
    write_yaml(
        receipt,
        {
            "status": "complete",
            "authorized": True,
            "checked_at": utc_now(),
            "completed_at": utc_now(),
            "inventory": records,
            "removed": removed,
        },
    )
    return {"status": "complete", "removed": removed, "receipt": str(receipt)}


def retire_worktree(
    root: Path,
    worktree: Path,
    branch: str,
    merged_revision: str,
    *,
    base: str = "main",
    remote: bool = True,
) -> dict[str, Any]:
    """Retire one verified merged checkout and its exact local/remote branch."""

    root = Path(root).absolute()
    if not isinstance(branch, str) or not _REF.fullmatch(branch) or branch == base:
        raise PolicyError("Retirement requires an exact non-base branch")
    if not branch.startswith("codex/") or not _OID.fullmatch(merged_revision):
        raise PolicyError("Retirement requires a managed branch and full merged revision")
    constraints = load_config(root, "constraints")
    runner = CommandRunner(root, constraints, grants={"branch_retirement", "push"})
    runner.policy.check_cleanup("merged_worktree_retirement", [str(worktree), branch])
    git = Git(root, runner)
    path = git._managed(worktree)
    ownership_receipt = git._receipt(path)
    if not path.exists() and ownership_receipt.exists():
        previous = read_yaml(ownership_receipt)
        if (
            previous.get("status") == "removed"
            and previous.get("branch") == branch
            and previous.get("head") == merged_revision
            and previous.get("merge_confirmed") is True
        ):
            if git.branch() != base or git.status():
                raise FrameworkError(
                    "Local integration checkout must remain clean for retirement reconciliation"
                )
            local_removed = git.delete_local_branch(branch, merged_revision, base=base)
            remote_name = load_config(root, "framework").get("delivery", {}).get(
                "remote", "origin"
            )
            remote_removed = True
            if remote:
                if not isinstance(remote_name, str):
                    raise FrameworkError("Delivery remote must be a Git remote name")
                remote_removed = git.delete_remote_branch(remote_name, branch, merged_revision)
            if not local_removed or not remote_removed:
                raise FrameworkError("Previously removed worktree still has an exact branch")
            return {
                "status": "already_retired",
                "worktree": str(path),
                "branch": branch,
                "merged_revision": merged_revision,
                "local_branch_removed": True,
                "remote_branch_removed": True,
            }
    record = git._owned(path)
    if not record or record.get("branch") != branch or record.get("owner_status") != "stopped":
        raise FrameworkError("Retirement requires an exact stopped owned worktree")
    if git.head(path) != merged_revision or git.branch(path) != branch:
        raise FrameworkError("Retirement target moved after merge")
    if git.branch() != base or git.status():
        raise FrameworkError("Coordinator checkout must be clean and on the integration branch")
    if not git.is_ancestor(merged_revision, base):
        raise FrameworkError("Reviewed revision is not present on the integration branch")
    if not git.cleanup(path, base=base, active=False):
        raise FrameworkError("Merged worktree could not be removed safely")
    local_removed = git.delete_local_branch(branch, merged_revision, base=base)
    remote_removed = True
    remote_name = load_config(root, "framework").get("delivery", {}).get("remote", "origin")
    if remote:
        if not isinstance(remote_name, str):
            raise FrameworkError("Delivery remote must be a Git remote name")
        remote_removed = git.delete_remote_branch(remote_name, branch, merged_revision)
    status = "complete" if local_removed and remote_removed else "incomplete"
    result = {
        "status": status,
        "worktree": str(path),
        "branch": branch,
        "merged_revision": merged_revision,
        "local_branch_removed": local_removed,
        "remote_branch_removed": remote_removed,
    }
    write_yaml(
        safe_path(root, f".ai/local/cleanup/retired-{path.name}-{merged_revision[:12]}.yaml"),
        {**result, "observed_at": utc_now()},
    )
    if status != "complete":
        raise FrameworkError("Merged worktree retirement remains incomplete")
    return result
