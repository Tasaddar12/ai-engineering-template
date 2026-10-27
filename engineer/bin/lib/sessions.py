"""Session worktrees are recorded in Git's shared administrative directory."""
from pathlib import Path
import contextlib
import os
import re
import time
from . import config, records, worktrees
from .core import Failure, load_json, now, root, run, slug, write_json


def store():
    common = Path(run(["git", "rev-parse", "--git-common-dir"], root()).stdout.strip())
    if not common.is_absolute():
        common = root()/common
    return common.resolve()/"engineer/sessions.json"


def phase_identity(value):
    whole, dot, fraction = str(value).split("-", 1)[0].partition(".")
    fraction = fraction.rstrip("0") if dot else ""
    return str(int(whole)).zfill(2)+("."+fraction if fraction else "")


@contextlib.contextmanager
def shared_lock():
    path = store().parent/"resources.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic()+10
    while True:
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise Failure("resources-locked", "Shared repository resource mutation is already active")
            time.sleep(0.05)
    try:
        os.write(descriptor, str(os.getpid()).encode())
        yield
    finally:
        os.close(descriptor)
        path.unlink()


def registered(entry):
    target = Path(entry["worktree"])
    if target.is_symlink() or not target.is_dir() or hasattr(target, "is_junction") and target.is_junction():
        raise Failure("missing-session-worktree", str(target))
    matching = [item for item in worktrees.list_worktrees() if Path(item["path"]).resolve() == target.resolve()]
    if len(matching) != 1:
        raise Failure("unregistered-session-worktree", "Recorded path must match one registered Git worktree", entry=entry)
    if matching[0]["branch"] != entry["branch"]:
        raise Failure("session-branch-mismatch", "Recorded branch differs from registered branch", entry=entry, actual_branch=matching[0]["branch"])
    actual = run(["git", "branch", "--show-current"], target).stdout.strip()
    if actual != entry["branch"]:
        raise Failure("session-branch-mismatch", actual)
    return target.resolve()


def phase_in(target, identifier):
    directory = target/".planning/phases"
    candidates = [path for path in directory.iterdir() if path.is_dir() and path.name[0:1].isdigit() and phase_identity(path.name) == identifier] if directory.is_dir() else []
    if len(candidates) > 1:
        raise Failure("ambiguous-phase-directory", identifier)
    if not candidates:
        return None
    # A name alone is not a phase record. An explicitly authored roadmap entry
    # or a phase artifact supplies evidence in the selected checkout.
    from .core import read
    headings = re.findall(r"(?m)^#{2,4}\s+Phase\s+(\d+(?:\.\d+)?)\s*:", read(target/".planning/ROADMAP.md"))
    evidenced = any(phase_identity(label) == identifier for label in headings)
    evidenced = evidenced or any(path.is_file() and path.name.endswith(("-CONTEXT.md", "-PLAN.md", "-SPEC.md", "-VERIFICATION.md")) for path in candidates[0].iterdir())
    return candidates[0] if evidenced else None


def command(args, action):
    if action == "status":
        return session_command(args, action)
    with shared_lock():
        return session_command(args, action)


def session_command(args, action):
    path = store()
    data = load_json(path, {"sessions": []})
    if action == "status":
        opened = [{**s, "exists": Path(s["worktree"]).is_dir()} for s in data["sessions"] if s.get("status") != "closed"]
        return {"sessions": data["sessions"], "count": len(data["sessions"]), "open": opened, "open_count": len(opened)}
    if action == "close":
        branch = args.need()
        matching = [s for s in data["sessions"] if s["branch"] == branch and s.get("status") != "closed"]
        if len(matching) != 1:
            raise Failure("session-not-found", branch)
        entry = matching[0]
        target = registered(entry)
        if target.resolve() == root():
            raise Failure("active-session", "Close a session from a different checkout")
        actual = run(["git", "branch", "--show-current"], target).stdout.strip()
        if actual != branch:
            raise Failure("session-identity-drift", actual)
        head = run(["git", "rev-parse", "HEAD"], target).stdout.strip()
        evidence = {"evidence": "ancestry", "merged": False, "head": head}
        if run(["git", "status", "--porcelain", "--untracked-files=all", "--ignored=matching"], target).stdout:
            return {"closed": False, "preserved": True, "reason": "dirty-session", "evidence": evidence}
        if run(["git", "merge-base", "--is-ancestor", head, "HEAD"], root(), check=False).returncode:
            return {"closed": False, "preserved": True, "reason": "session-not-integrated", "evidence": evidence}
        reference = "refs/heads/"+branch
        if run(["git", "symbolic-ref", "-q", reference], root(), check=False).returncode == 0:
            raise Failure("symbolic-session-branch", branch)
        if run(["git", "rev-parse", reference], root()).stdout.strip() != head:
            raise Failure("session-head-drift", branch)
        run(["git", "worktree", "remove", str(target)], root())
        if target.exists() or any(Path(item["path"]).resolve() == target for item in worktrees.list_worktrees()):
            raise Failure("session-close-uncertain", "Checkout removal lacks absent-path readback")
        if run(["git", "symbolic-ref", "-q", reference], root(), check=False).returncode == 0 or run(["git", "rev-parse", reference], root()).stdout.strip() != head:
            raise Failure("session-head-drift", "Session branch changed after checkout removal")
        run(["git", "update-ref", "--no-deref", "-d", reference, head], root())
        if run(["git", "show-ref", "--verify", "--quiet", reference], root(), check=False).returncode == 0 or run(["git", "symbolic-ref", "-q", reference], root(), check=False).returncode == 0:
            raise Failure("session-close-uncertain", "Branch removal lacks absent-ref readback")
        entry.update({"status": "closed", "closed": now()})
        write_json(path, data)
        return {"closed": True, "evidence": {**evidence, "merged": True}, **entry}
    kind, label = args.need(), args.need(1)
    if kind not in ("phase", "quick", "milestone", "onboard"):
        raise Failure("invalid-session-kind", kind, 2)
    label = phase_identity(label) if kind == "phase" else slug(label)
    if action == "adopt" and kind == "phase" and not phase_in(root(), label):
        raise Failure("phase-not-found", label)
    opened = [s for s in data["sessions"] if s.get("status") != "closed"]
    matching = [s for s in opened if s["kind"] == kind and (phase_identity(s["label"]) if kind == "phase" else s["label"]) == label]
    if action == "adopt":
        current_branch = run(["git", "branch", "--show-current"], root()).stdout.strip()
        if len(matching) > 1:
            raise Failure("ambiguous-phase-session", label, candidates=matching)
        conflicts = [s for s in opened if (s["branch"] == current_branch or Path(s["worktree"]).resolve() == root()) and s not in matching]
        if conflicts:
            raise Failure("session-adopt-conflict", "Another open session owns the selected branch or path", candidates=conflicts)
    if matching:
        if len(matching) != 1:
            raise Failure("ambiguous-session", "Multiple open sessions have the same kind and label")
        entry = matching[0]
        target = registered(entry)
        if action == "adopt" and target != root():
            raise Failure("session-adopt-wrong-checkout", "A different checkout already owns this phase")
        if action == "adopt" and kind == "phase" and not phase_in(target, label):
            raise Failure("phase-not-found", label)
        return {**entry, "reused": True}
    common = path.parent.parent
    primary = common.parent if common.name == ".git" else root()
    base_branch = str(args.get("base", config.lookup(config.load(), "git.base_branch", "main")))
    if run(["git", "rev-parse", "--verify", base_branch+"^{commit}"], root(), check=False).returncode:
        base_branch = run(["git", "branch", "--show-current"], primary).stdout.strip()
    base = run(["git", "rev-parse", args.get("base", "HEAD")+"^{commit}"], root()).stdout.strip()
    if action == "adopt":
        if root() == primary:
            raise Failure("session-adopt-not-linked", "Adopt an isolated worktree")
        branch = run(["git", "branch", "--show-current"], root()).stdout.strip()
        if not branch:
            raise Failure("session-adopt-detached", "Adoption requires a named branch")
        target = root()
        if branch in config.lookup(config.load(), "git.protected_branches", ["main", "master"]):
            raise Failure("protected-branch", "Adopt a non-protected isolated branch")
        registered({"worktree": str(target), "branch": branch})
        if kind == "phase" and not phase_in(target, label):
            raise Failure("phase-not-found", label)
        base = run(["git", "merge-base", "HEAD", base_branch], root()).stdout.strip()
    else:
        branch = config.lookup(config.load(), "worktree.branch_prefix", "codex/")+kind+"-"+label
        target = primary/str(config.lookup(config.load(), "worktree.directory", ".worktrees"))/slug(branch)
        target = target.resolve()
        if not target.is_relative_to(primary.resolve()) or target == primary.resolve():
            raise Failure("unsafe-session-path", str(target))
        ignored = run(["git", "check-ignore", "--quiet", "--", str(target)], primary, check=False)
        if ignored.returncode:
            raise Failure("root-not-ignored", "Ignore the configured worktree root before creating sessions")
        if target.exists():
            raise Failure("session-path-exists", str(target))
        run(["git", "worktree", "add", "-b", branch, str(target), base], primary)
    entry = {"kind": kind, "label": label, "branch": branch, "worktree": str(target), "base": base,
             "base_branch": base_branch, "status": "open", "created": now(), "created_at": now(),
             "adopted": action == "adopt", "synced": None, "pr": None}
    data["sessions"].append(entry)
    write_json(path, data)
    return {**entry, "reused": False}


def locate(args):
    identifier = phase_identity(args.need())
    data = load_json(store(), {"sessions": []})
    matches = [entry for entry in data["sessions"] if entry.get("kind") == "phase" and entry.get("status") != "closed" and phase_identity(entry["label"]) == identifier]
    if len(matches) > 1:
        raise Failure("ambiguous-phase-session", "Multiple recorded sessions own this phase", candidates=matches)
    if matches:
        entry = matches[0]
        target = registered(entry)
        directory = phase_in(target, identifier)
        if not directory:
            raise Failure("session-phase-missing", f"Phase session exists but its phase directory is absent: {identifier}")
        return {"found": True, "phase_found": True, "source": "session", "padded_phase": identifier, "worktree": str(target), "branch": entry["branch"], "session": entry, "phase_dir": str(directory)}
    directory = phase_in(root(), identifier)
    if directory:
        return {"found": True, "phase_found": True, "source": "current-checkout", "padded_phase": identifier, "worktree": str(root()), "branch": run(["git", "branch", "--show-current"], root()).stdout.strip(), "phase_dir": str(directory), "session": None}
    from .archive import catalog, guarded
    archived = [entry for entry in catalog() if entry["kind"] == "phase" and phase_identity(entry["id"]) == identifier]
    if len(archived) > 1:
        raise Failure("phase-ambiguous", "Multiple archived phase identities")
    if archived:
        directory = guarded(archived[0]["archived_path"])
        return {"found": True, "phase_found": True, "archived": True, "source": "archive", "padded_phase": identifier, "worktree": str(root()), "branch": run(["git", "branch", "--show-current"], root()).stdout.strip(), "phase_dir": str(directory), "session": None}
    candidates = []
    for item in worktrees.list_worktrees():
        target = Path(item["path"])
        if not target.is_dir() or target.is_symlink() or hasattr(target, "is_junction") and target.is_junction():
            continue
        directory = phase_in(target, identifier)
        if directory:
            candidates.append({"found": True, "phase_found": True, "source": "registered-worktree", "padded_phase": identifier, "worktree": str(target.resolve()), "branch": item["branch"], "phase_dir": str(directory), "session": None})
    if len(candidates) > 1:
        raise Failure("ambiguous-phase-worktree", "Multiple registered checkouts contain this phase", candidates=candidates)
    return candidates[0] if candidates else {"found": False, "phase_found": False, "source": "none", "padded_phase": identifier, "worktree": None, "branch": None, "session": None}
