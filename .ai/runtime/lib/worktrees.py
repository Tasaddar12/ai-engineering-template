"""Worktree isolation for parallel plan execution.

A wave dispatches one agent per plan. Without isolation they all edit one
working tree and interleave their commits into one history, so a plan cannot be
attributed or reverted and two agents editing the same file race. Isolation
gives each plan its own checkout on its own branch, and the wave is integrated
afterwards through an explicit merge with a deletion guard.

Three isolation models, matching what the host can actually do:

- ``harness-worktree`` -- the host creates and binds the worktree itself (Claude
  Code's ``isolation="worktree"`` dispatch argument). The runtime runs no git to
  set up; it records the branch the harness reports so the wave can be merged
  and cleaned up.
- ``orchestrator-worktree`` -- the runtime creates the worktree and the workflow
  binds an executor to it. Every git operation belongs to the runtime.
- ``none`` -- plans run inline, sequentially.

Resolution fails closed to ``none``. A host whose capability cannot be
determined runs sequentially rather than dispatching agents unisolated while the
workflow believes they are isolated.

Cleanup is never destructive by default: a worktree whose branch is not proven
merged is preserved for inspection.
"""
import json
import re
from datetime import datetime
from pathlib import Path

from . import gitops
from .config import get as config_get
from .paths import write_text
from .results import require

#: The only isolation values the workflows may branch on.
ISOLATION_MODES = ("harness-worktree", "orchestrator-worktree", "none")

#: Branches a worktree may never be created on or merged into.
PROTECTED_BRANCH = re.compile(r"^(main|master|develop|trunk|release/.*)$")

#: Branch namespaces an isolated executor is allowed to commit on. `agent-*`
#: and `worktree-agent-*` are what Claude Code names its own worktrees; the
#: rest are what this runtime creates.
ISOLATION_BRANCH = re.compile(
    r"^((worktree-)?agent-|worktree-wf_|phase-|quick-|review-|verify-)[A-Za-z0-9._/-]+$")

STATE_DIR = "ai-phase"
IGNORE_PROBE = ".phase-ignore-probe"


# --- locations ------------------------------------------------------------

def common_dir(workspace):
    """The repository's shared git directory, identical from every worktree."""
    raw = gitops.output(workspace, "rev-parse", "--git-common-dir") or ".git"
    path = Path(raw)
    if not path.is_absolute():
        path = workspace.root / path
    return path.resolve()


def state_dir(workspace):
    """Runtime bookkeeping that is neither committed nor a planning record.

    It lives in the shared git directory so every linked worktree reads the same
    wave manifest, and so `git status` never shows it.
    """
    return common_dir(workspace) / STATE_DIR


def primary_checkout(workspace):
    """The main working tree. `git worktree list` always names it first."""
    listed = gitops.git(workspace, "worktree", "list", "--porcelain", check=False)
    for line in listed.stdout.splitlines():
        if line.startswith("worktree "):
            return Path(line[len("worktree "):].strip()).resolve()
    return workspace.root


def configured_root(workspace):
    return str(config_get(workspace, "worktree.root", ".worktrees") or ".worktrees")


def worktree_root(workspace):
    """Directory every runtime-created worktree is an immediate child of."""
    return (primary_checkout(workspace) / configured_root(workspace)).resolve()


def root_is_ignored(workspace):
    """Whether the worktree root is gitignored in the primary checkout.

    An un-ignored root turns every checkout into untracked files in the parent,
    so creation refuses until it is ignored.
    """
    probe = configured_root(workspace).rstrip("/") + "/" + IGNORE_PROBE
    return gitops.git(workspace, "check-ignore", "-q", "--", probe,
                      check=False, cwd=primary_checkout(workspace)).returncode == 0


# --- isolation resolution -------------------------------------------------

def host_capability():
    """The isolation primitive the installed host namespace provides.

    The installed namespace is the honest signal available to the runtime:
    `.claude` means Claude Code, which binds worktrees itself; `.codex` and the
    uninstalled template both mean the runtime has to create them.
    """
    namespace = Path(__file__).resolve().parents[2].name
    if namespace == ".claude":
        return "harness-worktree", "claude code binds worktrees at dispatch"
    if namespace == ".codex":
        return "orchestrator-worktree", "codex has no dispatch isolation argument"
    return ("orchestrator-worktree",
            "no host namespace installed; the runtime creates worktrees")


def resolve_isolation(workspace, force=None, phase=None, plan=None):
    """How this dispatch should be isolated, recorded as a side effect.

    Recording is not optional: this is the only call that tells a workflow what
    its isolation is, so the persisted value can never drift from the one the
    workflow acted on.
    """
    if force is not None:
        forced = str(force)
        require(forced in ISOLATION_MODES,
                "unknown isolation: " + forced, "bad-isolation")
        mode, reason, resolved = forced, "forced by the caller", True
    elif config_get(workspace, "workflow.use_worktrees", True) is False:
        mode, reason, resolved = "none", "workflow.use_worktrees is false", True
    else:
        configured = str(config_get(workspace, "workflow.isolation", "auto") or "auto")
        if configured == "auto":
            mode, reason = host_capability()
            resolved = True
        elif configured in ISOLATION_MODES:
            mode = configured
            reason = "workflow.isolation is " + configured
            resolved = True
        else:
            mode, reason, resolved = "none", "workflow.isolation is not a known mode", False

    if mode != "none" and not gitops.supports_worktrees(workspace):
        mode, reason, resolved = "none", "this git does not support worktrees", True
    if mode == "orchestrator-worktree" and not root_is_ignored(workspace):
        mode = "none"
        reason = (configured_root(workspace) + " is not gitignored in the primary "
                  "checkout; runtime-created worktrees would appear as untracked files")
        resolved = True

    payload = {
        "isolation": mode,
        "resolved": resolved,
        "reason": reason,
        # What the workflow passes on its dispatch call. Only the harness model
        # has one; the other two are the runtime's work or nobody's.
        "harness_flag": "worktree" if mode == "harness-worktree" else None,
        "phase": str(phase) if phase not in (None, "", True) else None,
        "plan": str(plan) if plan not in (None, "", True) else None,
        "use_worktrees": config_get(workspace, "workflow.use_worktrees", True),
        "worktree_root": workspace.relative(worktree_root(workspace)),
    }
    record_isolation(workspace, payload)
    return payload


def record_isolation(workspace, payload):
    """Persist the resolved isolation. Best effort: never fail a dispatch."""
    try:
        target = state_dir(workspace) / "isolation.json"
        body = dict(payload, recorded_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        write_text(target, json.dumps(body, ensure_ascii=False, indent=2) + "\n")
    except OSError:
        pass
    return payload


def base_check(workspace, mode="harness-worktree"):
    """Whether HEAD has diverged from the base a new worktree would fork from.

    A harness forks its worktree from the fork point with the base branch, not
    from HEAD. When HEAD carries commits the base does not, an isolated executor
    would start from a tree missing them and its own branch check would halt.
    Degrading to sequential execution is correct until HEAD is merged;
    `worktree.base_ref: head` opts out where the host forks from HEAD instead.
    """
    head = gitops.head_revision(workspace)
    base_ref = str(config_get(workspace, "worktree.base_ref", "fork-point")
                   or "fork-point")
    result = {"mode": mode, "head": head, "base_ref": base_ref,
              "should_degrade": False, "message": None}
    if base_ref == "head":
        result["reason"] = "worktree.base_ref is head; worktrees fork from HEAD"
        return result
    base = gitops.base_branch(workspace)
    reference = ""
    for candidate in ("origin/" + base, base):
        reference = gitops.rev_parse(workspace, candidate)
        if reference:
            result["compared_to"] = candidate
            break
    if not reference or not head:
        result["reason"] = "no base revision to compare against"
        return result
    fork = gitops.merge_base(workspace, head, reference)
    result["fork_base"] = fork
    if fork and fork != head:
        ahead = gitops.output(workspace, "rev-list", "--count", reference + "..HEAD")
        result["should_degrade"] = True
        result["commits_ahead"] = int(ahead) if ahead.isdigit() else None
        result["message"] = (
            "HEAD is " + (ahead or "?") + " commit(s) ahead of "
            + result.get("compared_to", base)
            + "; an isolated executor would fork from " + fork[:8]
            + " and miss them. Running sequentially. Merge or push HEAD, or set "
            "worktree.base_ref: head, to restore isolated execution.")
        result["reason"] = "head diverged from the fork base"
        return result
    result["reason"] = "head matches the fork base"
    return result


# --- wave manifest --------------------------------------------------------

def manifest_path(workspace, phase):
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(phase or "current")).strip("-")
    return state_dir(workspace) / "waves" / ((slug or "current") + ".json")


def load_manifest(workspace, phase):
    path = manifest_path(workspace, phase)
    empty = {"phase": str(phase or "current"), "entries": []}
    if not path.is_file():
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return empty
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        return empty
    return data


def save_manifest(workspace, phase, manifest):
    write_text(manifest_path(workspace, phase),
               json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def scope_list(value):
    """Declared paths from a flag, given comma or whitespace separated."""
    if value in (None, True, False):
        return []
    if isinstance(value, (list, tuple)):
        items = [str(item) for item in value]
    else:
        items = re.split(r"[,\s]+", str(value))
    cleaned = []
    for item in items:
        text = item.strip()
        if not text:
            continue
        if text.startswith("./"):
            text = text[2:]
        cleaned.append(text.rstrip("/"))
    return cleaned


def put_entry(workspace, phase, entry):
    """Insert or replace this plan's manifest entry."""
    manifest = load_manifest(workspace, phase)
    manifest["entries"] = [item for item in manifest["entries"]
                           if item.get("plan") != entry.get("plan")]
    manifest["entries"].append(entry)
    save_manifest(workspace, phase, manifest)
    return entry


def validate_branch(branch):
    require(bool(branch), "a worktree needs its own named branch", "bad-branch")
    require(not PROTECTED_BRANCH.match(branch),
            "refusing to isolate work on the protected branch " + branch,
            "protected-branch")
    require(bool(ISOLATION_BRANCH.match(branch)),
            "branch " + branch + " is outside the isolation namespaces "
            "(agent-*, phase-*, quick-*, review-*, verify-*)", "bad-branch")
    return branch


# --- creation -------------------------------------------------------------

def create(workspace, plan, phase=None, base=None, branch=None, files=None,
           deletions=None):
    """Create a runtime-owned worktree for one plan and record it."""
    require(gitops.is_repository(workspace), "not a git repository", "not-a-repo")
    require(gitops.supports_worktrees(workspace),
            "this git does not support worktrees", "no-worktree-support")
    parent = primary_checkout(workspace)
    require(root_is_ignored(workspace),
            configured_root(workspace) + " must be gitignored in the primary "
            "checkout before worktrees are created", "root-not-ignored")

    dirty = [line for line in gitops.porcelain(workspace)
             if not line[3:].strip().startswith(".planning/")]
    require(not dirty,
            "commit or stash changes outside .planning/ before isolating a wave: "
            + ", ".join(line[3:].strip() for line in dirty[:5]), "dirty-tree")

    base = base or gitops.head_revision(workspace)
    require(bool(gitops.rev_parse(workspace, base + "^{commit}")),
            "base revision does not resolve: " + str(base), "bad-base")

    token = datetime.now().strftime("%H%M%S%f")[:9]
    label = re.sub(r"[^A-Za-z0-9._-]+", "-", str(plan)).strip("-") or "plan"
    branch = validate_branch(branch or "phase-" + label + "-" + token)
    require(not gitops.rev_parse(workspace, "refs/heads/" + branch),
            "branch already exists: " + branch, "branch-exists")

    root = worktree_root(workspace)
    path = (root / (label + "-" + token)).resolve()
    require(path.parent == root,
            "a worktree must be an immediate child of " + str(root),
            "bad-worktree-path")
    require(not path.exists(), "worktree path already exists: " + str(path),
            "path-exists")

    root.mkdir(parents=True, exist_ok=True)
    gitops.git(workspace, "worktree", "add", "-b", branch, str(path), base)
    require(not path.is_symlink(),
            "worktree path resolved to a link: " + str(path), "bad-worktree-path")

    entry = {
        "plan": str(plan),
        "phase": str(phase) if phase not in (None, "", True) else None,
        "isolation": "orchestrator-worktree",
        "worktree": str(path),
        "branch": branch,
        "base": base,
        "files": scope_list(files),
        "deletions": scope_list(deletions),
        "status": "active",
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
    put_entry(workspace, phase, entry)
    return dict(entry, worktree_relative=workspace.relative(path),
                parent=str(parent))


def record_agent(workspace, plan, branch, phase=None, base=None, files=None,
                 deletions=None, path=None):
    """Record a worktree the host created, so the wave can integrate it.

    The harness owns the checkout in this model; the runtime only needs the
    branch, the base it forked from, and the scope the plan declared.
    """
    entry = {
        "plan": str(plan),
        "phase": str(phase) if phase not in (None, "", True) else None,
        "isolation": "harness-worktree",
        "worktree": str(path) if path not in (None, True) else None,
        "branch": validate_branch(str(branch)),
        "base": base or gitops.head_revision(workspace),
        "files": scope_list(files),
        "deletions": scope_list(deletions),
        "status": "active",
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
    put_entry(workspace, phase, entry)
    return entry


# --- integration ----------------------------------------------------------

def changed_paths(workspace, base, branch):
    """`(status, path)` pairs a branch changed relative to its base."""
    raw = gitops.git(workspace, "diff", "--name-status", base + "..." + branch,
                     check=False)
    changes = []
    for line in raw.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].strip():
            changes.append((parts[0].strip()[0], parts[-1].strip()))
    return changes


def undeclared_deletions(entry, changes):
    """Deleted paths the plan never declared. Matching is exact, per path.

    A deletion authorization is never inferred from a general scope
    declaration: `files` says what a plan may edit, and `deletions` is the only
    thing that authorizes a removal.
    """
    declared = set(entry.get("deletions") or [])
    return sorted(path for status, path in changes
                  if status == "D" and path not in declared)


def out_of_scope(entry, changes):
    """Paths outside the plan's declared scope. Advisory only, never blocking."""
    declared = entry.get("files") or []
    if not declared:
        return []
    prefixes = [item.split("*", 1)[0].rstrip("/") for item in declared]
    stray = []
    for _, path in changes:
        inside = False
        for prefix in prefixes:
            if not prefix or path == prefix or path.startswith(prefix + "/"):
                inside = True
                break
        if not inside:
            stray.append(path)
    return sorted(set(stray))


def merge_wave(workspace, phase, plan=None):
    """Merge each recorded branch into the current branch, one at a time.

    A branch that deletes a path its plan did not declare is blocked rather than
    merged, and a conflicting merge is aborted with its worktree preserved. A
    blocked entry never counts as a successful wave.
    """
    require(gitops.is_repository(workspace), "not a git repository", "not-a-repo")
    manifest = load_manifest(workspace, phase)
    target = gitops.current_branch(workspace)
    require(not PROTECTED_BRANCH.match(target),
            "refusing to merge a wave into the protected branch " + target,
            "protected-branch")
    require(not gitops.porcelain(workspace),
            "commit or stash the working tree before merging a wave", "dirty-tree")

    results = []
    for entry in manifest["entries"]:
        if plan and entry.get("plan") != str(plan):
            continue
        if entry.get("status") in ("merged", "blocked", "cleaned"):
            results.append({"plan": entry.get("plan"), "branch": entry.get("branch"),
                            "status": entry.get("status"),
                            "skipped": "already " + str(entry.get("status"))})
            continue
        branch = entry.get("branch") or ""
        outcome = {"plan": entry.get("plan"), "branch": branch}
        if not gitops.rev_parse(workspace, "refs/heads/" + branch):
            entry["status"] = "missing"
            outcome.update(status="missing",
                           reason="branch does not exist; the executor never committed")
            results.append(outcome)
            continue
        base = entry.get("base") or gitops.merge_base(workspace, target, branch)
        ahead = gitops.output(workspace, "rev-list", "--count", base + ".." + branch)
        if ahead in ("", "0"):
            entry["status"] = "empty"
            outcome.update(status="empty", reason="no commits on the branch")
            results.append(outcome)
            continue
        changes = changed_paths(workspace, base, branch)
        stray_deletions = undeclared_deletions(entry, changes)
        if stray_deletions:
            entry["status"] = "blocked"
            entry["blocked_reason"] = "undeclared deletions"
            outcome.update(status="blocked", undeclared_deletions=stray_deletions,
                           reason="deletes paths the plan did not declare")
            results.append(outcome)
            continue
        merge = gitops.git(workspace, "merge", "--no-ff", "-m",
                           "merge(" + str(entry.get("plan"))
                           + "): integrate isolated plan", branch, check=False)
        if merge.returncode != 0:
            gitops.git(workspace, "merge", "--abort", check=False)
            entry["status"] = "conflict"
            outcome.update(status="conflict",
                           reason="merge conflict; the worktree is preserved",
                           detail=(merge.stderr or merge.stdout).strip()[:2000])
            results.append(outcome)
            continue
        entry["status"] = "merged"
        entry["merged_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        outcome.update(status="merged",
                       commits=int(ahead) if ahead.isdigit() else None,
                       revision=gitops.head_revision(workspace),
                       out_of_scope=out_of_scope(entry, changes))
        results.append(outcome)

    save_manifest(workspace, phase, manifest)
    # `empty` and `missing` both mean the executor committed nothing, which is a
    # plan that did not complete -- not a clean wave with less in it.
    blocked = [item for item in results
               if item.get("status") in ("blocked", "conflict", "missing", "empty")]
    return {
        "phase": manifest.get("phase"),
        "target_branch": target,
        "merged": [item for item in results if item.get("status") == "merged"],
        "blocked": blocked,
        "results": results,
        "wave_clean": not blocked,
    }


def cleanup_wave(workspace, phase, force=False):
    """Remove worktrees whose work is proven merged; preserve everything else.

    Merge evidence is checked against the repository, not against the manifest's
    own claim: a branch is removed only when git agrees HEAD contains it.
    """
    manifest = load_manifest(workspace, phase)
    removed, preserved = [], []
    for entry in manifest["entries"]:
        branch = entry.get("branch") or ""
        path = entry.get("worktree")
        if entry.get("status") == "cleaned":
            continue
        reason = None
        if entry.get("status") != "merged":
            reason = "status is " + str(entry.get("status"))
        elif branch and gitops.git(workspace, "merge-base", "--is-ancestor", branch,
                                   "HEAD", check=False).returncode != 0:
            reason = "branch is not an ancestor of HEAD; no merge evidence"
        if reason and not force:
            preserved.append({"plan": entry.get("plan"), "branch": branch,
                              "worktree": path, "reason": reason})
            continue
        if path and Path(path).exists():
            arguments = ["worktree", "remove", str(path)]
            if force:
                arguments.append("--force")
            result = gitops.git(workspace, *arguments, check=False)
            if result.returncode != 0:
                preserved.append({
                    "plan": entry.get("plan"), "branch": branch, "worktree": path,
                    "reason": (result.stderr or result.stdout).strip()[:500]})
                continue
        if branch:
            gitops.git(workspace, "branch", "-D" if force else "-d", branch,
                       check=False)
        entry["status"] = "cleaned"
        removed.append({"plan": entry.get("plan"), "branch": branch,
                        "worktree": path})

    gitops.git(workspace, "worktree", "prune", check=False)
    save_manifest(workspace, phase, manifest)
    return {"phase": manifest.get("phase"), "removed": removed,
            "preserved": preserved, "forced": bool(force)}


# --- inspection -----------------------------------------------------------

def listing(workspace):
    """Every linked worktree git knows about, with its branch and state."""
    raw = gitops.git(workspace, "worktree", "list", "--porcelain", check=False)
    entries, current = [], {}
    for line in raw.stdout.splitlines():
        if not line.strip():
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            if current:
                entries.append(current)
            current = {"path": value.strip()}
        elif key == "branch":
            current["branch"] = value.strip().replace("refs/heads/", "")
        elif key in ("bare", "detached", "locked", "prunable"):
            current[key] = value.strip() or True
    if current:
        entries.append(current)
    primary = primary_checkout(workspace)
    root = worktree_root(workspace)
    for entry in entries:
        # git emits forward slashes on Windows while every path this module
        # derives is a resolved Path, so normalize before any comparison.
        path = Path(entry.get("path", "")).resolve()
        entry["path"] = str(path)
        entry["exists"] = path.is_dir()
        entry["is_primary"] = path == primary
        entry["managed"] = path != root and root in path.parents
    return {"primary": str(primary), "worktree_root": str(root),
            "root_ignored": root_is_ignored(workspace), "worktrees": entries,
            "count": len(entries)}


def reap_orphans(workspace):
    """Prune stale worktree metadata. Non-destructive: never removes a checkout.

    Registered worktrees whose directory is gone leave metadata behind after a
    crashed session, and that metadata makes later `worktree add` calls fail.
    Directories that still exist are reported, never deleted: an unmerged
    checkout is somebody's work in progress.
    """
    before = listing(workspace)
    prunable = [entry for entry in before["worktrees"]
                if entry.get("prunable")
                or (not entry["exists"] and not entry["is_primary"])]
    result = gitops.git(workspace, "worktree", "prune", "-v", check=False)
    after = listing(workspace)
    return {
        "pruned": [entry.get("path") for entry in prunable],
        "pruned_count": len(prunable),
        "detail": result.stdout.strip() or None,
        "remaining": after["count"],
        "preserved": [entry.get("path") for entry in after["worktrees"]
                      if entry.get("managed") and not entry.get("is_primary")],
    }


def health(workspace):
    """Findings a diagnostic should surface about the worktree setup."""
    view = listing(workspace)
    findings = []
    if not view["root_ignored"]:
        findings.append({
            "severity": "warning", "code": "root-not-ignored",
            "detail": configured_root(workspace) + " is not gitignored; "
                      "runtime-created worktrees would show up as untracked "
                      "files in the primary checkout",
        })
    for entry in view["worktrees"]:
        if entry.get("is_primary"):
            continue
        if not entry["exists"]:
            findings.append({"severity": "warning", "code": "orphan-metadata",
                             "path": entry.get("path"),
                             "detail": "registered but the directory is gone; "
                                       "run worktree.reap-orphans"})
            continue
        branch = entry.get("branch")
        if branch and gitops.git(workspace, "merge-base", "--is-ancestor", branch,
                                 "HEAD", check=False).returncode != 0:
            findings.append({"severity": "info", "code": "unmerged",
                             "path": entry.get("path"), "branch": branch,
                             "detail": "holds commits not in HEAD; preserve "
                                       "until merged"})
        if entry.get("locked"):
            findings.append({"severity": "info", "code": "locked",
                             "path": entry.get("path"),
                             "detail": "locked: " + str(entry.get("locked"))})
    return {
        "ok_to_isolate": not any(item["severity"] == "warning" for item in findings),
        "findings": findings,
        "worktrees": view["count"],
    }
