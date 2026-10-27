"""Exact approval snapshots; revalidate each integrated resource before deletion."""
from pathlib import Path
import hashlib
import json
import secrets
import os
import stat
from . import config, gitops, records, worktrees, repository, delivery, sessions
from .core import Failure, load_json, now, planning_lock, root, run, safe_path, write_json


def aliased_path(path):
    """Inspect raw path components before canonicalization hides a junction."""
    candidate = Path(os.path.abspath(path))
    for part in [candidate, *candidate.parents]:
        if part.is_symlink():
            return True
        if part.exists() and getattr(part.lstat(), "st_file_attributes", 0) & 0x400:
            return True
    return False


def provider_evidence(branch, head, allow_local=False):
    from urllib.parse import quote, urlencode
    if allow_local and run(["git", "remote", "get-url", "origin"], root(), check=False).returncode:
        return {"kind": "recorded-local-integration", "head": head}
    origin = repository.identity()
    hostname = origin["hostname"]
    full_name = origin["owner"]+"/"+origin["repository"]
    gitlab = "gitlab" in hostname
    executable = "glab" if gitlab else "gh"
    def get(endpoint):
        response = run([executable, "api", "--hostname", hostname, "--method", "GET", endpoint], root(), check=False)
        if response.returncode:
            raise Failure("cleanup-provider-unavailable", "Canonical provider cleanup lookup did not succeed")
        try:
            return json.loads(response.stdout)
        except (ValueError, RecursionError) as exc:
            raise Failure("cleanup-provider-incomplete", "Canonical provider cleanup lookup returned malformed evidence") from exc
    project = None
    if gitlab:
        project = get("projects/"+quote(full_name, safe=""))
        if not isinstance(project, dict) or project.get("path_with_namespace") != full_name or not isinstance(project.get("id"), int):
            raise Failure("cleanup-provider-identity", "GitLab project lookup differs from origin")
    rows = []
    for page in range(1, 102):
        query = {"state": "all", "per_page": 100, "page": page}
        if gitlab:
            query["source_branch"] = branch
            endpoint = "projects/"+str(project["id"])+"/merge_requests?"+urlencode(query)
        else:
            query["head"] = origin["owner"]+":"+branch
            endpoint = "repos/"+full_name+"/pulls?"+urlencode(query)
        batch = get(endpoint)
        if not isinstance(batch, list) or len(batch) > 100:
            raise Failure("cleanup-provider-incomplete", "Provider cleanup lookup is incomplete")
        rows.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise Failure("cleanup-provider-incomplete", "Provider cleanup lookup exceeded its safe pagination bound")
    relevant = []
    for row in rows:
        if not isinstance(row, dict):
            raise Failure("cleanup-provider-incomplete", "Provider returned malformed cleanup evidence")
        if gitlab:
            if row.get("source_branch") != branch:
                continue
            if row.get("source_project_id") != project["id"] or row.get("target_project_id") != project["id"] or row.get("sha") != head or not isinstance(row.get("iid"), int):
                raise Failure("cleanup-provider-identity", "GitLab merge request is foreign or differs from the owned head")
            if row.get("state") not in ("closed", "merged"):
                raise Failure("cleanup-provider-live", "Open or unverifiable provider work is preserved")
        else:
            source, target = row.get("head", {}), row.get("base", {})
            if source.get("ref") != branch:
                continue
            if source.get("repo", {}).get("full_name") != full_name or target.get("repo", {}).get("full_name") != full_name or source.get("sha") != head or not isinstance(row.get("number"), int):
                raise Failure("cleanup-provider-identity", "GitHub pull request is foreign or differs from the owned head")
            if row.get("state") != "closed":
                raise Failure("cleanup-provider-live", "Open or unverifiable provider work is preserved")
        relevant.append(row)
    if not relevant and not allow_local:
        raise Failure("cleanup-provider-missing", "No canonical provider disposition is available for the owned session")
    return {"origin": origin, "pull_requests": relevant}

def direct_head(branch):
    reference = "refs/heads/"+branch
    if run(["git", "symbolic-ref", "-q", reference], root(), check=False).returncode == 0:
        raise Failure("cleanup-symbolic-ref", "Symbolic branch refs are never cleanup candidates")
    return run(["git", "rev-parse", "--verify", reference], root()).stdout.strip()


def ownership():
    owners = {}
    for manifest in (records.planning()/"worktrees").glob("*.json"):
        for entry in load_json(manifest, {}).get("workers", []):
            if entry.get("merged") and not entry.get("cleaned"):
                owners.setdefault((str(Path(entry["path"]).resolve()), entry["branch"]), []).append({"kind": "worker", "record": entry})
    for entry in load_json(sessions.store(), {}).get("sessions", []):
        if entry.get("status") != "closed":
            owners.setdefault((str(Path(entry["worktree"]).resolve()), entry["branch"]), []).append({"kind": "session", "record": entry})
    return owners


def backup_owners():
    """Only an explicit resource recorded by a single eligible owner can retire."""
    result = {}
    for owners in ownership().values():
        for owner in owners:
            for value in owner["record"].get("backups", []):
                value = value.get("path") if isinstance(value, dict) else value
                if not isinstance(value, str):
                    continue
                raw = Path(value)
                raw = raw if raw.is_absolute() else root()/raw
                result.setdefault(str(Path(os.path.abspath(raw))), []).append(owner)
    return result


def backup_inventory():
    """Capture unowned siblings too: new content cannot inherit an old approval."""
    base = root()/".workflow-backups"
    if not base.exists() and not base.is_symlink():
        return []
    if aliased_path(base):
        raise Failure("cleanup-aliased-backup", "Backup storage is aliased")
    result = []
    def visit(path):
        if aliased_path(path):
            raise Failure("cleanup-aliased-backup", "Symlink or junction backup content is preserved")
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) and not stat.S_ISREG(info.st_mode):
            raise Failure("cleanup-special-backup", "Special backup content is preserved")
        row = {"path": str(path.relative_to(base)), "directory": stat.S_ISDIR(info.st_mode),
               "identity": [info.st_dev, info.st_ino], "mode": info.st_mode}
        if row["directory"]:
            result.append(row)
            for child in sorted(path.iterdir(), key=lambda child: child.name):
                visit(child)
        else:
            row.update({"size": info.st_size, "mtime_ns": info.st_mtime_ns,
                        "digest": hashlib.sha256(path.read_bytes()).hexdigest()})
            after = path.lstat()
            if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                raise Failure("cleanup-backup-race", "Backup changed while capturing its content")
            result.append(row)
    visit(base)
    return result


def backup_tree(path, inventory):
    prefix = str(path.relative_to(root()/".workflow-backups"))
    return [row for row in inventory if row["path"] == prefix or Path(row["path"]).is_relative_to(prefix)]


def validate_backup(entry, inventory=None):
    target = Path(entry["path"])
    base = root()/".workflow-backups"
    if not target.is_absolute() or aliased_path(target) or target.resolve() != target or target == base or not target.is_relative_to(base) or not target.is_dir():
        raise Failure("cleanup-unsafe-backup", "Only a physical recorded backup below repository backup storage can retire")
    candidates = backup_owners()
    owners = candidates.get(str(target), [])
    if len(owners) != 1 or owners[0] != entry["owner"]:
        raise Failure("cleanup-owner-drift", "Backup ownership changed or is ambiguous")
    for name in candidates:
        other = Path(name)
        if other != target and (other.is_relative_to(target) or target.is_relative_to(other)):
            raise Failure("cleanup-nested-ownership", "Overlapping recorded backup ownership is preserved")
    record = owners[0]["record"]
    branch = record["branch"]
    if direct_head(branch) != entry["head"] or run(["git", "merge-base", "--is-ancestor", entry["head"], "HEAD"], root(), check=False).returncode:
        raise Failure("cleanup-not-integrated", "Backup owner branch is not integrated")
    worker = owners[0]["kind"] == "worker"
    if worker and (not record.get("integration_revision") or run(["git", "merge-base", "--is-ancestor", record["integration_revision"], "HEAD"], root(), check=False).returncode):
        raise Failure("cleanup-integration-drift", "Backup owner integration is unavailable")
    if provider_evidence(branch, entry["head"], worker) != entry["provider"]:
        raise Failure("cleanup-provider-drift", "Backup owner provider evidence changed")
    tracked = run(["git", "ls-files", "--", str(target)], root()).stdout
    if tracked:
        raise Failure("cleanup-tracked-backup", "Tracked repository content cannot be a disposable backup")
    # A repository/worktree or administration folder must never be hidden inside
    # a backup tree, even if its owner recorded the parent path.
    inventory = backup_inventory() if inventory is None else inventory
    rows = backup_tree(target, inventory)
    if any(Path(row["path"]).name in (".git", ".planning") for row in rows):
        raise Failure("cleanup-repository-backup", "Nested repository or planning content is preserved")
    if rows != entry["tree"]:
        raise Failure("cleanup-backup-drift", "Backup identity or content changed since approval")


def remove_backup(entry):
    """Delete exactly captured regular files, never follow a child alias."""
    target = Path(entry["path"])
    base = root()/".workflow-backups"
    # All resolved recursive targets are checked before any removal (including
    # Windows reparse points), then again at each individual filesystem action.
    validate_backup(entry)
    for row in sorted(entry["tree"], key=lambda row: len(Path(row["path"]).parts), reverse=True):
        path = base/row["path"]
        if not path.is_relative_to(target) or aliased_path(path) or path.resolve() != path:
            raise Failure("cleanup-backup-race", "Backup path changed before removal")
        info = path.lstat()
        if [info.st_dev, info.st_ino] != row["identity"] or info.st_mode != row["mode"]:
            raise Failure("cleanup-backup-race", "Backup node identity changed before removal")
        if row["directory"]:
            path.rmdir()  # Fails on newly introduced content; never recursively follows it.
        else:
            if info.st_size != row["size"] or info.st_mtime_ns != row["mtime_ns"] or hashlib.sha256(path.read_bytes()).hexdigest() != row["digest"]:
                raise Failure("cleanup-backup-race", "Backup content changed before removal")
            path.unlink()
    if target.exists() or target.is_symlink():
        raise Failure("cleanup-removal-unconfirmed", "Backup removal lacks absent-path readback")


def validate_entry(entry, require_worktree=True):
    target = Path(entry["path"])
    if aliased_path(target) or target.resolve() == root():
        raise Failure("cleanup-aliased-resource", "Active and aliased paths are preserved")
    protected = config.lookup(config.load(), "git.protected_branches", ["main", "master"])
    if entry["branch"] in protected or any(item.get("branch") == entry["branch"] and Path(item["path"]).resolve() != target.resolve() for item in worktrees.list_worktrees()):
        raise Failure("cleanup-protected-resource", "Protected branches and branches owned by another checkout are preserved")
    owners = ownership().get((str(target.resolve()), entry["branch"]), [])
    if len(owners) != 1 or owners[0] != entry["owner"]:
        raise Failure("cleanup-owner-drift", "Exact resource ownership changed")
    worker = owners[0]["kind"] == "worker"
    if worker:
        record = owners[0]["record"]
        integrated = record.get("integration_revision")
        if record.get("head") != entry["head"] or not integrated or run(["git", "merge-base", "--is-ancestor", integrated, "HEAD"], root(), check=False).returncode:
            raise Failure("cleanup-integration-drift", "Recorded worker merge evidence is unavailable")
    if direct_head(entry["branch"]) != entry["head"]:
        raise Failure("cleanup-head-drift", "Owned branch head changed")
    if run(["git", "merge-base", "--is-ancestor", entry["head"], "HEAD"], root(), check=False).returncode:
        raise Failure("cleanup-not-integrated", "Owned head is no longer in integration ancestry")
    if provider_evidence(entry["branch"], entry["head"], worker) != entry["provider"]:
        raise Failure("cleanup-provider-drift", "Provider origin or disposition changed")
    if require_worktree:
        items = [item for item in worktrees.list_worktrees() if Path(item["path"]).resolve() == target.resolve()]
        if len(items) != 1 or items[0].get("locked") or items[0].get("branch") != entry["branch"] or items[0].get("head") != entry["head"]:
            raise Failure("cleanup-worktree-drift", "Registered worktree identity changed")
        if run(["git", "status", "--porcelain", "--untracked-files=all", "--ignored=matching"], target).stdout:
            raise Failure("cleanup-dirty-resource", "Tracked, untracked and ignored content must be preserved")


def snapshot():
    items = []
    active = root()
    allowed_root = safe_path(config.lookup(config.load(), "worktree.directory", ".worktrees"))
    owned = ownership()
    for item in worktrees.list_worktrees():
        raw = Path(item["path"])
        if aliased_path(raw):
            continue
        target = raw.resolve()
        if target == active or not target.is_relative_to(active) or not target.is_relative_to(allowed_root):
            continue
        if item.get("locked") or not item.get("branch"):
            continue
        owners = owned.get((str(target), item["branch"]), [])
        if len(owners) != 1:
            continue
        try:
            entry = {"kind": "worktree_remove", "path": str(target), "branch": item["branch"], "head": item["head"], "owner": owners[0],
                     "provider": provider_evidence(item["branch"], item["head"], owners[0]["kind"] == "worker")}
            validate_entry(entry)
        except (Failure, OSError, ValueError, KeyError, TypeError):
            continue
        items.append(entry)
        items.append({**entry, "kind": "branch_delete"})
    # A previously removed checkout does not make its recorded integrated direct
    # branch unowned. Never infer branch ownership from a naming convention.
    registered_paths = {str(Path(item["path"]).resolve()) for item in worktrees.list_worktrees()}
    for (name, branch), owners in owned.items():
        target = Path(name)
        if len(owners) != 1 or name in registered_paths or target.exists() or aliased_path(target) or not target.is_relative_to(allowed_root) or target == active:
            continue
        try:
            head = direct_head(branch)
            entry = {"kind": "branch_delete", "path": name, "branch": branch, "head": head, "owner": owners[0],
                     "provider": provider_evidence(branch, head, owners[0]["kind"] == "worker")}
            validate_entry(entry, require_worktree=False)
            items.append(entry)
        except (Failure, OSError, ValueError, KeyError, TypeError):
            continue
    backups = []
    try:
        inventory = backup_inventory()
        for name, owners in sorted(backup_owners().items()):
            if len(owners) != 1:
                continue
            try:
                owner = owners[0]
                head = direct_head(owner["record"]["branch"])
                entry = {"kind": "backup", "path": name, "owner": owner, "head": head,
                         "provider": provider_evidence(owner["record"]["branch"], head, owner["kind"] == "worker"),
                         "tree": backup_tree(Path(name), inventory)}
                validate_backup(entry, inventory)
                backups.append(entry)
            except (Failure, OSError, ValueError, KeyError, TypeError):
                continue
    except (Failure, OSError, ValueError):
        # Aliased or unreadable backup storage grants no backup deletion rights.
        pass
    return backups+items


def command(args, action):
    with sessions.shared_lock():
        return cleanup_command(args, action)


def cleanup_command(args, action):
    store = records.planning()/"cleanup"
    if action == "preview":
        entries = snapshot()
        try:
            inventory = backup_inventory()
        except (Failure, OSError, ValueError):
            inventory = None
        payload = {"entries": entries, "backup_inventory": inventory, "nonce": secrets.token_hex(16)}
        token = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        with planning_lock():
            write_json(store/(token+".json"), {**payload, "created": now()})
        return {"approval_token": token, "entries": entries, "count": len(entries)}
    if not args.has("confirm"):
        raise Failure("cleanup-not-approved", "Cleanup requires the exact preview token and --confirm")
    token = str(args.get("approval-token", args.arg(0, "")))
    if len(token) != 64 or any(char not in "0123456789abcdef" for char in token):
        raise Failure("invalid-cleanup-token", token)
    path = store/(token+".json")
    approved = load_json(path)
    if not approved or approved.get("consumed"):
        raise Failure("cleanup-preview-missing", "Create a fresh exact approval preview")
    payload = {"entries": approved.get("entries"), "backup_inventory": approved.get("backup_inventory"), "nonce": approved["nonce"]}
    expected = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    if expected != token:
        raise Failure("cleanup-preview-corrupt", "Stored entries no longer match exact approval")
    def validate_inventory(removed):
        original = approved.get("backup_inventory")
        if original is None:
            if any(entry.get("kind") == "backup" for entry in approved["entries"]):
                raise Failure("cleanup-backup-drift", "Backup inventory was unavailable")
            return
        deleted = [Path(entry["path"]).relative_to(root()/".workflow-backups") for entry in removed if entry.get("kind") == "backup"]
        expected_inventory = [row for row in original if not any(Path(row["path"]).is_relative_to(path) for path in deleted)]
        if backup_inventory() != expected_inventory:
            raise Failure("cleanup-backup-drift", "Backup storage changed outside the exact approved removals")
    # Refuse the whole stale approval before its first destructive action.
    validate_inventory([])
    for entry in approved["entries"]:
        if entry.get("kind") == "backup":
            validate_backup(entry)
        else:
            validate_entry(entry, require_worktree=entry.get("kind") == "worktree_remove")
    with planning_lock():
        current = load_json(path)
        if current != approved:
            raise Failure("cleanup-preview-drift", "Approval changed before consumption")
        approved.update({"consumed": True, "started": now(), "removed": []})
        write_json(path, approved)
    removed = []
    for entry in approved["entries"]:
        # Recompute the eligible resources before every deletion; earlier removals
        # cannot authorize later resources that drifted in the meantime.
        try:
            validate_inventory(removed)
            if entry.get("kind") == "backup":
                remove_backup(entry)
                removed.append(entry)
                approved["removed"] = removed
                write_json(path, approved)
                continue
            validate_entry(entry, require_worktree=entry.get("kind") == "worktree_remove")
        except (Failure, OSError) as exc:
            if not isinstance(exc, Failure):
                exc = Failure("cleanup-backup-race", "Backup filesystem changed during exact removal")
            exc.details.update({"removed": removed, "resource": entry})
            raise exc
        target = safe_path(entry["path"])
        try:
            if entry.get("kind") == "worktree_remove":
                run(["git", "worktree", "remove", str(target)], root())
                if target.exists() or any(Path(item["path"]).resolve() == target for item in worktrees.list_worktrees()):
                    raise Failure("cleanup-removal-unconfirmed", "Worktree removal did not remove the actual owned checkout")
            else:
                if target.exists() or any(Path(item["path"]).resolve() == target for item in worktrees.list_worktrees()):
                    raise Failure("cleanup-worktree-drift", "Branch still has checkout content")
                validate_entry(entry, require_worktree=False)
                reference = "refs/heads/"+entry["branch"]
                run(["git", "update-ref", "--no-deref", "-d", reference, entry["head"]], root())
                if run(["git", "show-ref", "--verify", "--quiet", reference], root(), check=False).returncode == 0 or run(["git", "symbolic-ref", "-q", reference], root(), check=False).returncode == 0:
                    raise Failure("cleanup-removal-unconfirmed", "Branch removal has no absent-ref readback")
        except Failure as exc:
            exc.details.update({"removed": removed, "resource": entry})
            raise
        removed.append(entry)
        approved["removed"] = removed
        write_json(path, approved)
    approved.update({"consumed": True, "completed": now()})
    write_json(path, approved)
    return {"removed": removed, "count": len(removed)}
