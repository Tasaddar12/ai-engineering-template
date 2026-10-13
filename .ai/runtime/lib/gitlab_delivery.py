"""GitLab adapter for the existing PR/session contract; no credential writes."""
import hashlib
import json
import re
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote, urlencode

from . import delivery, gitops, worktrees
from .config import get as config_get
from .results import VerbError, require


def glab(workspace, *args, cwd=None, payload=None):
    try:
        return subprocess.run(["glab", *args], cwd=str(cwd or workspace.root),
                              capture_output=True, text=True,
                              input=json.dumps(payload) if payload is not None else None,
                              timeout=delivery.TIMEOUT)
    except FileNotFoundError:
        raise VerbError("GitLab delivery requires glab", "glab-missing")
    except (OSError, subprocess.TimeoutExpired):
        # Never expose command/body/provider diagnostics or assume a write failed.
        raise VerbError("GitLab operation unavailable; read back before retrying",
                        "glab-unavailable")


def availability(workspace, target):
    try:
        version = glab(workspace, "--version")
        if version.returncode != 0:
            return dict(available=False, authenticated=False, provider="gitlab",
                        host=target["host"], reason="glab is unavailable")
        auth = glab(workspace, "auth", "status", "--hostname", target["host"])
    except VerbError as exc:
        return dict(available=False, authenticated=False, provider="gitlab",
                    host=target["host"], reason=str(exc))
    return dict(available=True, authenticated=auth.returncode == 0,
                provider="gitlab", host=target["host"],
                version=version.stdout.strip().splitlines()[0] if version.stdout.strip() else "",
                reason=None if auth.returncode == 0 else "glab is not authenticated for the configured host")


def require_provider(workspace, target):
    state = availability(workspace, target)
    require(state["available"], state["reason"], "glab-missing")
    require(state["authenticated"], state["reason"], "glab-unauthenticated")


def endpoint(target):
    return "projects/" + quote(target["project"], safe="") + "/merge_requests"


def api(workspace, target, path, method="GET", payload=None, cwd=None):
    args = ["api", path, "--hostname", target["host"], "--method", method]
    if payload is not None:
        args += ["--input", "-"]
    result = glab(workspace, *args, cwd=cwd, payload=payload)
    require(result.returncode == 0, "GitLab operation failed; readback required",
            "mr-provider")
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise VerbError("GitLab returned malformed JSON", "mr-response")


def normalize(target, raw, branch):
    from . import providers
    require(isinstance(raw, dict), "Invalid merge request response", "mr-response")
    number = providers.item_number(target, raw.get("web_url"), kind="merge_requests")
    require(type(raw.get("iid")) is int and raw["iid"] == number
            and raw.get("source_branch") == branch
            and type(raw.get("source_project_id")) is int
            and raw["source_project_id"] == raw.get("target_project_id"),
            "Merge request ownership differs from the configured project/branch", "mr-ownership")
    require(raw.get("state") in ("opened", "closed", "merged", "locked"),
            "Unknown merge request state", "mr-response")
    require(isinstance(raw.get("title"), str) and isinstance(raw.get("target_branch"), str)
            and isinstance(raw.get("sha"), str) and bool(raw["sha"]),
            "Incomplete merge request response", "mr-response")
    draft = raw.get("draft", raw.get("work_in_progress"))
    require(type(draft) is bool, "Missing merge request draft state", "mr-response")
    status = raw.get("detailed_merge_status") or raw.get("merge_status") or "unknown"
    return dict(number=number, url=raw["web_url"], state={"opened": "OPEN", "closed": "CLOSED",
                "merged": "MERGED", "locked": "LOCKED"}[raw["state"]], isDraft=draft,
                baseRefName=raw["target_branch"], headRefName=branch,
                mergeable="MERGEABLE" if status in ("mergeable", "can_be_merged") else "UNKNOWN",
                mergeStateStatus=status, title=raw["title"], body=raw.get("description"),
                sha=raw["sha"], head_pipeline=raw.get("head_pipeline"), provider="gitlab")


def view(workspace, target, branch, cwd=None):
    # Explicit pagination keeps compatibility with older glab JSON output.
    candidates = []
    for page in range(1, 101):
        query = urlencode(dict(source_branch=branch, state="all", scope="all", per_page=100, page=page))
        rows = api(workspace, target, endpoint(target) + "?" + query, cwd=cwd)
        require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows),
                "Invalid merge request listing", "mr-response")
        candidates += [row for row in rows if row.get("source_branch") == branch
                       and row.get("source_project_id") == row.get("target_project_id")]
        if len(rows) < 100:
            break
    else:
        raise VerbError("Merge request lookup exceeded pagination limit", "mr-response")
    opened = [row for row in candidates if row.get("state") == "opened"]
    require(len(opened) <= 1, "Multiple open merge requests for branch", "mr-ambiguous")
    if not candidates:
        return None
    require(all(type(row.get("iid")) is int for row in candidates),
            "Invalid merge request number", "mr-response")
    chosen = opened[0] if opened else max(candidates, key=lambda row: row.get("iid", 0))
    selected = normalize(target, chosen, branch)
    raw = api(workspace, target, endpoint(target) + "/" + str(selected["number"]), cwd=cwd)
    pull = normalize(target, raw, branch)
    require(pull["number"] == selected["number"], "Merge request readback changed identity", "mr-ownership")
    return pull


def draft_title(title, draft):
    clean = re.sub(r"^(?:Draft:|WIP:|\[Draft\]|\(Draft\))\s*", "", title, flags=re.I)
    return "Draft: " + clean if draft else clean


@contextmanager
def publication(workspace, target, branch):
    # Intent survives process interruption, including a successful write whose
    # response was lost. The shared Git directory isolates it from source commits.
    key = hashlib.sha256((target["repository"] + "\n" + branch).encode()).hexdigest()
    directory = worktrees.state_dir(workspace) / "mr-publication"
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / (key + ".lock")
    try:
        handle = lock.open("x")
    except FileExistsError:
        raise VerbError("MR publication lock held; reconcile the prior attempt", "mr-locked")
    try:
        yield directory / (key + ".json")
    finally:
        handle.close()
        lock.unlink()


def matches(pull, fields):
    names = {"title": "title", "description": "body", "target_branch": "baseRefName",
             "source_branch": "headRefName"}
    return pull is not None and all(pull.get(names[key]) == value for key, value in fields.items())


def intent_digest(fields):
    return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()


def resolved_intent(pull, saved):
    names = {"title": "title", "description": "body", "target_branch": "baseRefName",
             "source_branch": "headRefName"}
    observed = {key: pull.get(names[key]) for key in saved["fields"]}
    return intent_digest(observed) == saved["digest"]


def open_pr(workspace, target, branch, base=None, title=None, body=None, body_file=None,
            draft=True, cwd=None):
    require_provider(workspace, target)
    if body_file:
        try:
            body = Path(body_file).read_text(encoding="utf-8")
        except OSError:
            raise VerbError("Cannot read MR body file", "mr-body")
    with publication(workspace, target, branch) as intent:
        existing = view(workspace, target, branch, cwd=cwd)
        unresolved = False
        if intent.exists():
            # A later successful read resolves uncertainty. An absent MR never
            # proves the earlier POST did not land; preserve intent and stop.
            saved = json.loads(intent.read_text(encoding="utf-8"))
            require(existing is not None and (saved["number"] is None
                    or saved["number"] == existing["number"]),
                    "Prior MR write is uncertain; reconcile it before creating another", "mr-uncertain")
            unresolved = not resolved_intent(existing, saved)
        require(not existing or existing["state"] == "OPEN",
                "Existing merge request is not OPEN", "pr-not-open")
        fields = {}
        if base is not None:
            fields["target_branch"] = base
        if title:
            fields["title"] = draft_title(title, existing["isDraft"] if existing else draft)
        if body is not None:
            fields["description"] = body
        if not existing:
            fields.update(source_branch=branch, target_branch=base or gitops.base_branch(workspace),
                          title=draft_title(title or branch, draft), description=body or "")
        if not fields:
            require(not unresolved, "Prior MR edit is not confirmed; retry its explicit fields",
                    "mr-uncertain")
            if intent.exists():
                intent.unlink()
            return dict(existing, created=False, updated=False)
        intent.write_text(json.dumps(dict(number=existing["number"] if existing else None,
                                         fields=list(fields), digest=intent_digest(fields))), encoding="utf-8")
        path = endpoint(target) + ("/" + str(existing["number"]) if existing else "")
        try:
            api(workspace, target, path, method="PUT" if existing else "POST", payload=fields, cwd=cwd)
        except VerbError:
            pass  # The attempted write may have succeeded. Readback owns success.
        for attempt in range(3):
            try:
                refreshed = view(workspace, target, branch, cwd=cwd)
            except VerbError:
                refreshed = None
            if matches(refreshed, fields) and (not existing or refreshed["number"] == existing["number"]):
                intent.unlink()
                return dict(refreshed, created=not bool(existing), updated=bool(existing))
            if attempt < 2:
                time.sleep(1)
        raise VerbError("MR write is uncertain; intent retained for readback on retry", "mr-uncertain")


def classify_pipeline(pull):
    pipeline = pull.get("head_pipeline")
    status = pull.get("mergeStateStatus")
    if pipeline is None:
        if status in ("ci_must_pass", "ci_still_running", "checking", "unchecked", "preparing"):
            return delivery.classify_checks([dict(name="GitLab pipeline", status="PENDING")])
        if status in ("unknown", "status_checks_must_pass"):
            return delivery.classify_checks([dict(name="GitLab merge status",
                                                  status="COMPLETED", conclusion="UNKNOWN")])
        return delivery.classify_checks([])
    require(isinstance(pipeline, dict), "Invalid pipeline response", "mr-response")
    current = pipeline.get("sha") == pull["sha"]
    state = pipeline.get("status")
    if not current or state in ("created", "waiting_for_resource", "preparing", "pending", "running", "scheduled"):
        entry = dict(name="GitLab pipeline", status="PENDING")
    else:
        # A skipped/manual/unknown pipeline is not successful execution.
        entry = dict(name="GitLab pipeline", status="COMPLETED",
                     conclusion="SUCCESS" if state == "success" else "FAILURE")
    entry["detailsUrl"] = pipeline.get("web_url")
    return delivery.classify_checks([entry])


def checks(workspace, target, branch, cwd=None, wait=0, interval=30,
           sleep=time.sleep, clock=time.monotonic):
    require_provider(workspace, target)
    started = clock()
    while True:
        pull = view(workspace, target, branch, cwd=cwd)
        require(pull is not None, "No merge request for branch", "no-pr")
        verdict = classify_pipeline(pull)
        if verdict["state"] != "pending" or clock() - started + interval > wait:
            break
        sleep(interval)
    return dict(verdict, branch=branch, number=pull["number"], url=pull["url"],
                pr_state=pull["state"], draft=pull["isDraft"], mergeable=pull["mergeable"],
                merge_state=pull["mergeStateStatus"], waited=int(clock() - started), sha=pull["sha"])


def merge_pr(workspace, target, branch, local_checks_passed=None, cwd=None):
    verdict = checks(workspace, target, branch, cwd=cwd)
    require(verdict["pr_state"] == "OPEN", "Merge request is not OPEN", "pr-not-open")
    require(verdict["state"] not in ("pending", "failing"),
            "Merge request checks " + verdict["state"], "checks-" + verdict["state"])
    require(verdict["state"] != "none" or local_checks_passed is True,
            "No passing verification for unchecked MR", "no-evidence")
    method = delivery.merge_method(workspace)
    require(method != "rebase", "GitLab rebase merge strategy is project-managed; select squash or merge",
            "bad-merge-method")
    pull = view(workspace, target, branch, cwd=cwd)
    require(pull and pull["sha"] == verdict["sha"], "MR source changed after checks", "mr-changed")
    if pull["isDraft"]:
        # Metadata edits deliberately preserve draft; only an explicit merge
        # operation may clear it, after evidence has passed.
        api(workspace, target, endpoint(target) + "/" + str(pull["number"]), method="PUT",
            payload=dict(title=draft_title(pull["title"], False)), cwd=cwd)
    deleted = bool(config_get(workspace, "delivery.delete_branch", True))
    try:
        api(workspace, target, endpoint(target) + "/" + str(pull["number"]) + "/merge",
            method="PUT", payload=dict(sha=verdict["sha"], squash=method == "squash",
                                        should_remove_source_branch=deleted), cwd=cwd)
    except VerbError:
        pass
    merged = view(workspace, target, branch, cwd=cwd)
    require(merged and merged["number"] == pull["number"] and merged["state"] == "MERGED",
            "Merge not confirmed by GitLab readback; session preserved", "merge-refused")
    return dict(branch=branch, merged=True, method=method,
                evidence=verdict["state"] if verdict["state"] != "none" else "local-verification",
                number=pull["number"], url=pull["url"], pr_state="MERGED",
                remote_branch_deleted=deleted)
