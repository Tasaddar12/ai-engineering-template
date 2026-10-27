"""Exact approval snapshots; revalidate each integrated resource before deletion."""
from pathlib import Path
import hashlib
import json
import secrets
import os
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


def validate_entry(entry, require_worktree=True):
    target = Path(entry["path"])
    if aliased_path(target) or target.resolve() == root():
        raise Failure("cleanup-aliased-resource", "Active and aliased paths are preserved")
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
            entry = {"path": str(target), "branch": item["branch"], "head": item["head"], "owner": owners[0],
                     "provider": provider_evidence(item["branch"], item["head"], owners[0]["kind"] == "worker")}
            validate_entry(entry)
        except (Failure, OSError, ValueError, KeyError, TypeError):
            continue
        items.append(entry)
    return items


def command(args, action):
    with sessions.shared_lock():
        return cleanup_command(args, action)


def cleanup_command(args, action):
    store = records.planning()/"cleanup"
    if action == "preview":
        entries = snapshot()
        payload = {"entries": entries, "nonce": secrets.token_hex(16)}
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
    payload = {"entries": approved.get("entries"), "nonce": approved["nonce"]} if "nonce" in approved else approved.get("entries")
    expected = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    if expected != token:
        raise Failure("cleanup-preview-corrupt", "Stored entries no longer match exact approval")
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
        validate_entry(entry)
        target = safe_path(entry["path"])
        run(["git", "worktree", "remove", str(target)], root())
        if target.exists() or any(Path(item["path"]).resolve() == target for item in worktrees.list_worktrees()):
            raise Failure("cleanup-removal-unconfirmed", "Worktree removal did not remove the actual owned checkout", removed=removed)
        validate_entry(entry, require_worktree=False)
        reference = "refs/heads/"+entry["branch"]
        run(["git", "update-ref", "--no-deref", "-d", reference, entry["head"]], root())
        if run(["git", "show-ref", "--verify", "--quiet", reference], root(), check=False).returncode == 0 or run(["git", "symbolic-ref", "-q", reference], root(), check=False).returncode == 0:
            raise Failure("cleanup-removal-unconfirmed", "Branch removal has no absent-ref readback", removed=removed)
        removed.append(entry)
        approved["removed"] = removed
        write_json(path, approved)
    approved.update({"consumed": True, "completed": now()})
    write_json(path, approved)
    return {"removed": removed, "count": len(removed)}
