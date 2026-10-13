"""Declared phase issue gates using the existing reviewed TODO publisher.

The coordinator supplies completeness and acceptance judgments. These guards
validate the selected records and provider evidence, never infer omitted prose.
"""
import copy
import json
import re
import tempfile
import uuid
from pathlib import Path

from . import delivery, issue_format, phases, todo_issues, todos, worktrees
from .paths import read_text
from .results import VerbError, require
from .roadmap import Roadmap, as_number
from .text import section_body

STATES = {"unresolved", "pending-human", "resolved", "blocked-publication"}
RELATIONSHIPS = {"resolving", "followup"}


def directory(workspace, number):
    phase = Roadmap(workspace).require_phase(number)
    require(not phase.archived, "Historical phase cannot be changed", "phase-archived")
    path = phases.find_directory(workspace, number, include_archived=False)
    require(path is not None, "Selected phase has no execution records", "phase-issues")
    todos.safe_directory(workspace, path)
    return path


def selected(workspace, number, name):
    require(isinstance(name, str) and name.strip() and "\\" not in name
            and not Path(name).is_absolute() and ".." not in Path(name).parts,
            "Select an exact in-phase record path", "path-escape")
    root = directory(workspace, number)
    path = workspace.root / name
    if len(Path(name).parts) == 1:
        path = root / name
    require(path.parent == root and not todos.linked_path(path),
            "Selected record is outside the active phase", "path-escape")
    require(path.is_file() and (phases.SUMMARY_FILE.fullmatch(path.name)
                              or path.name == phases.pad(number) + "-CONTEXT.md"),
            "Select one execution SUMMARY or phase CONTEXT", "phase-issues")
    return path


def entries(metadata, required=False):
    require(not required or "issue_refs" in metadata,
            "Execution SUMMARY requires reviewed issue_refs (use [] when empty)", "phase-issues")
    refs = metadata.get("issue_refs", [])
    require(isinstance(refs, list), "issue_refs must be an explicit list", "phase-issues")
    seen = set()
    for item in refs:
        require(isinstance(item, dict), "Issue declaration must be a mapping", "phase-issues")
        identifier = item.get("id")
        require(isinstance(identifier, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", identifier)
                and identifier not in seen, "Issue IDs must be stable and unique per record", "phase-issues")
        seen.add(identifier)
        require(isinstance(item.get("summary"), str) and item["summary"].strip()
                and isinstance(item.get("variant"), str) and item["variant"] in issue_format.schema()
                and isinstance(item.get("state"), str) and item["state"] in STATES
                and isinstance(item.get("relationship"), str) and item["relationship"] in RELATIONSHIPS,
                "Incomplete issue declaration", "phase-issues")
        require(item["state"] != "pending-human" or item["relationship"] == "followup",
                "Pending human acceptance must remain followup", "phase-issues")
        if item["state"] in {"resolved", "blocked-publication"}:
            require(isinstance(item.get("reason"), str) and item["reason"].strip(),
                    "Resolved and blocked-publication entries require a reason", "phase-issues")
        if item["relationship"] == "resolving":
            require(item["state"] == "resolved" and isinstance(item.get("reason"), str)
                    and item["reason"].strip(),
                    "Resolving references require recorded demonstrated acceptance", "phase-issues")
        publication = item.get("issuePublication", {})
        require(isinstance(publication, dict), "Invalid publication metadata", "phase-issues")
    return refs


def declare(workspace, number, name, entries_file=None, expected=None):
    """Coordinator review amendment; preserve canonical publication ownership."""
    path = selected(workspace, number, name)
    original = read_text(path)
    metadata, body = todos.read_record(path)
    snapshot = todo_issues.digest(original)
    if entries_file is None:
        return {"record": workspace.relative(path), "snapshotDigest": snapshot,
                "issue_refs": metadata.get("issue_refs"), "privateLocal": True}
    require(expected == snapshot, "Phase record changed; renew declaration review", "stale-preview")
    require(Path(entries_file).resolve() != path.resolve(), "Use a separate declaration draft", "issue-review")
    try:
        refs = json.loads(read_text(entries_file))
    except (VerbError, OSError, ValueError, UnicodeError):
        raise VerbError("Reviewed declaration draft cannot be read", "phase-issues") from None
    entries({"issue_refs": refs}, required=True)
    old_refs = metadata.get("issue_refs", [])
    require(isinstance(old_refs, list), "Existing declarations must be a list", "phase-issues")
    for old in old_refs:
        require(isinstance(old, dict), "Existing declaration is malformed", "phase-issues")
        updated = next((item for item in refs if item["id"] == old.get("id")), None)
        owned = ("issueRepo", "issueURL", "issueNumber", "issuePublication")
        if any(key in old for key in owned):
            require(updated is not None, "Retain existing publication identity in declarations", "phase-issues")
        if updated is not None:
            require(updated["variant"] == old.get("variant"), "Preserve the selected issue variant", "issue-variant")
            for key in owned:
                if key in old:
                    require(key not in updated or updated[key] == old[key], "Publication linkage belongs to the issue adapter", "phase-issues")
                    updated[key] = copy.deepcopy(old[key])
    entries({"issue_refs": refs}, required=True)
    require(selected(workspace, number, name) == path and read_text(path) == original,
            "Phase record changed; renew declaration review", "stale-preview")
    metadata["issue_refs"] = refs
    todos.save_record(path, metadata, body)
    return {"record": workspace.relative(path), "declared": True, "count": len(refs),
            "snapshotDigest": todo_issues.digest(read_text(path))}


def linkage(item, repository):
    require(isinstance(item.get("issueRepo"), str)
            and item["issueRepo"].lower() == repository.lower(),
            "Issue declaration repository mismatch", "issue-repository")
    number = todo_issues.number_from_url(repository, item.get("issueURL"))
    require(isinstance(item.get("issueNumber"), int) and not isinstance(item["issueNumber"], bool)
            and item["issueNumber"] == number, "Issue URL/number mismatch", "issue-url")
    return number


def handoff(workspace, number):
    root = directory(workspace, number)
    names = phases.artifacts(root, number)
    require(names["summaries"], "Phase handoff requires execution SUMMARY records", "phase-issues")
    records = names["summaries"] + ([names["context"]] if names["context"] else [])
    declarations, blocked = [], []
    repository = None
    for name in records:
        path = selected(workspace, number, name)
        metadata, _ = todos.read_record(path)
        for item in entries(metadata, required=name in names["summaries"]):
            record = dict(item, record=workspace.relative(path))
            if item["state"] == "blocked-publication":
                blocked.append(record)
            elif item["state"] != "resolved" or item.get("issueURL"):
                require(item.get("issueURL"), "Unresolved phase problem needs a canonical issue", "phase-issues")
                repository = repository or todo_issues.target(workspace)
                linkage(item, repository)
                require(item.get("issuePublication", {}).get("state") in (None, "linked"),
                        "Uncertain publication must be recovered before handoff", "phase-issues")
            declarations.append(record)
    return {"phase": str(number), "ready": not blocked, "declarations": declarations,
            "blocked": blocked, "retryable": bool(blocked), "structuralOnly": True}


class Source:
    """Adapt one entry to existing publisher callbacks, with whole-record CAS."""
    def __init__(self, workspace, number, name, identifier):
        self.workspace, self.number, self.name, self.identifier = workspace, number, name, identifier
        self.path = selected(workspace, number, name)
        self.loaded = None

    def read(self):
        path = selected(self.workspace, self.number, self.name)
        metadata, body = todos.read_record(path)
        refs = entries(metadata, required=bool(phases.SUMMARY_FILE.fullmatch(path.name)))
        matches = [item for item in refs if item["id"] == self.identifier]
        require(len(matches) == 1, "Select one declared stable issue ID", "phase-issues")
        return metadata, body, matches[0]

    def current(self):
        metadata, body, entry = self.read()
        self.loaded = copy.deepcopy((metadata, body))
        adapted = {key: copy.deepcopy(value) for key, value in entry.items()
                   if key not in {"state", "reason"}}
        publication = entry.get("issuePublication", {})
        if entry["state"] == "blocked-publication":
            adapted["relationship"] = publication.get("blockedFromRelationship", "followup")
        adapted["phaseDisposition"] = {
            "state": publication.get("blockedFromState", "unresolved") if entry["state"] == "blocked-publication" else entry["state"],
            "reason": publication.get("blockedFromReason") if entry["state"] == "blocked-publication" else entry.get("reason")}
        adapted["todoId"] = str(uuid.uuid5(uuid.NAMESPACE_URL,
            self.workspace.relative(self.path) + "#" + self.identifier))
        # Changes elsewhere in the private record invalidate the public review.
        rest = copy.deepcopy(metadata)
        rest["issue_refs"] = [item for item in rest["issue_refs"] if item["id"] != self.identifier]
        adapted["phaseRecordDigest"] = todo_issues.digest({"metadata": rest, "body": body})
        return self.path, adapted, body

    def save(self, adapted, body):
        metadata, current_body, entry = self.read()
        require(self.loaded == (metadata, current_body) and current_body == body,
                "Phase record changed; renew review", "stale-preview")
        for key in ("issueRepo", "issueURL", "issueNumber", "issuePublication"):
            if key in adapted:
                entry[key] = copy.deepcopy(adapted[key])
        if entry["state"] == "blocked-publication" and adapted.get("issuePublication", {}).get("state") == "linked":
            publication = adapted["issuePublication"]
            entry["state"] = publication.get("blockedFromState", "unresolved")
            entry["relationship"] = publication.get("blockedFromRelationship", "followup")
            if publication.get("blockedFromReason"):
                entry["reason"] = publication["blockedFromReason"]
            else:
                entry.pop("reason", None)
        todos.save_record(self.path, metadata, body)
        self.loaded = copy.deepcopy((metadata, body))

    def validate_issue(self, issue):
        _, _, entry = self.read()
        issue_format.validate(issue["body"], entry["variant"])

    def blocked(self):
        metadata, body, entry = self.read()
        require(self.loaded == (metadata, body), "Phase record changed; retry review", "stale-preview")
        if entry["state"] != "blocked-publication":
            entry["issuePublication"] = dict(entry.get("issuePublication", {}),
                blockedFromState=entry["state"], blockedFromReason=entry.get("reason"),
                blockedFromRelationship=entry["relationship"])
        entry.update(state="blocked-publication", relationship="followup",
                     reason="Provider publication unavailable; retry phase.issue-preview then phase.issue-publish with the same reviewed intent")
        todos.save_record(self.path, metadata, body)
        return {"linked": False, "state": "blocked-publication", "retryable": True,
                "record": self.workspace.relative(self.path), "id": self.identifier,
                "reason": entry["reason"]}


def preview(workspace, number, name, identifier, related_pr=None):
    source = Source(workspace, number, name, identifier)
    try:
        return todo_issues.preview(workspace, name, related_pr, source=source)
    except VerbError as exc:
        if exc.code == "issue-provider":
            return source.blocked()
        raise


def publish(workspace, number, name, identifier, token, title, body_file,
            existing_issue=None, no_match=False, variant=None):
    source = Source(workspace, number, name, identifier)
    _, _, entry = source.read()
    require(variant == entry["variant"], "Preserve the selected issue variant", "issue-variant")
    try:
        return todo_issues.publish(workspace, name, token, title, body_file,
                                  existing_issue, no_match, variant, source=source)
    except VerbError as exc:
        if exc.code == "issue-provider":
            return source.blocked()
        raise


def update(workspace, number, name, identifier, token, title, body_file, variant):
    source = Source(workspace, number, name, identifier)
    path, metadata, body = source.current()
    require(variant == metadata["variant"], "Preserve the selected issue variant", "issue-variant")
    require(isinstance(title, str) and title.strip(), "Reviewed public title required", "issue-review")
    public_body = todo_issues.reviewed_body(body_file, metadata["todoId"], path)
    issue_format.validate(public_body, variant)
    repository = todo_issues.target(workspace)
    number_id = linkage(metadata, repository)
    candidates, context = todo_issues.lookup(workspace, repository, metadata.get("issuePublication", {}).get("relatedPR"))
    snapshot = todo_issues.snapshot(metadata, body)
    publication = metadata.get("issuePublication", {})
    expected = todo_issues.digest({"todo": snapshot, "repository": repository,
        "candidates": candidates, "context": context, "relatedPR": publication.get("relatedPR")})
    require(token and token == publication.get("previewToken") == expected,
            "Phase issue update review is stale", "stale-preview")
    issue = todo_issues.issue_view(workspace, repository, metadata["issueURL"])
    require(issue["number"] == number_id and issue in candidates,
            "Issue changed after review", "stale-preview")
    # The selected shape must remain recognizable before and after the edit.
    issue_format.validate(issue["body"], variant)
    todo_issues.unchanged(workspace, name, snapshot, source)
    with tempfile.TemporaryDirectory(prefix="phase-public-") as temporary:
        public_path = Path(temporary) / "body.md"
        public_path.write_text(public_body, encoding="utf-8")
        todo_issues.call(workspace, "issue", "edit", metadata["issueURL"], "--repo", repository,
                         "--title", title, "--body-file", str(public_path))
    refreshed = todo_issues.issue_view(workspace, repository, metadata["issueURL"])
    require(refreshed["title"] == title and refreshed["body"] == public_body,
            "Issue update could not be verified; retry readback", "issue-unresolved")
    todo_issues.unchanged(workspace, name, snapshot, source)
    return {"updated": True, "issueURL": refreshed["url"], "variant": variant}


def sessions(workspace):
    """Do not let a corrupt session manifest silently disable phase gates."""
    path = worktrees.sessions_path(workspace)
    if not path.exists():
        return []
    try:
        data = json.loads(read_text(path))
    except (OSError, ValueError, UnicodeError):
        raise VerbError("Session identity cannot be read", "phase-session") from None
    require(isinstance(data, dict) and isinstance(data.get("sessions"), list)
            and all(isinstance(item, dict) for item in data["sessions"]),
            "Session identity is malformed", "phase-session")
    return data["sessions"]


def phase_session(workspace, branch, explicit=None):
    matching = [entry for entry in sessions(workspace) if entry.get("branch") == branch]
    require(len(matching) <= 1, "Ambiguous branch session identity", "phase-session")
    entry = matching[0] if matching else None
    if not entry or entry.get("kind") != "phase":
        require(explicit is None, "Explicit phase requires its existing phase session", "phase-session")
        return None
    require(isinstance(entry.get("label"), str) and entry["label"].strip(),
            "Phase session has no identity", "phase-session")
    if explicit is not None:
        require(as_number(explicit) == as_number(entry["label"]),
                "Explicit phase conflicts with branch session", "phase-session")
    require(isinstance(entry.get("worktree"), str)
            and Path(entry["worktree"]).resolve() == workspace.root.resolve(),
            "Use the branch's existing phase session worktree", "phase-session")
    return entry


CLOSING = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s*"
                     r"((?:https://[^\s,;]+/issues/[1-9][0-9]*|(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#[1-9][0-9]*)"
                     r"(?:\s*(?:,|and|&)\s*(?:https://[^\s,;]+/issues/[1-9][0-9]*|(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#[1-9][0-9]*))*)", re.I)
REFERENCE = re.compile(r"https://[^\s,;]+/issues/[1-9][0-9]*|(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#[1-9][0-9]*")


def pr_identity(repository, branch, pull):
    require(isinstance(pull, dict), "PR readback is malformed", "issue-response")
    number = todo_issues.number_from_url(repository, pull.get("url"), "pull")
    require(isinstance(pull.get("number"), int) and not isinstance(pull["number"], bool)
            and pull["number"] == number and pull.get("headRefName") == branch,
            "PR readback identity mismatch", "issue-response")


def require_accepted_uat(body):
    issue_format.validate(body, "UAT")
    visible = "\n".join(issue_format.visible_lines(body))
    acceptance = section_body(visible, "Human acceptance", level=2)
    status = re.search(r"^Status:\s*(.*?)\s*$", acceptance, re.M | re.I)
    require(status is not None and re.fullmatch(r"(?:ACCEPTED|PASSED|APPROVED)(?: HUMAN acceptance)?", status[1], re.I),
            "Pending or unknown human UAT acceptance cannot close or retire", "phase-issues")


def pr_body(workspace, number, body):
    result = handoff(workspace, number)
    require(result["ready"], "Phase issue publication is blocked; retry publication", "phase-issues")
    require(isinstance(body, str), "Effective PR body must be read before phase publication", "phase-issues")
    linked = [entry for entry in result["declarations"] if entry.get("issueURL")]
    if not linked:
        return result
    repository = todo_issues.target(workspace)
    remote_cache = {}
    closing_text = re.sub(r"\[[^\]\n]*\]\((https://[^)\s]+)\)", r"\1", body)
    closing = {ref.lower() for match in CLOSING.finditer(closing_text) for ref in REFERENCE.findall(match[1])}
    for entry in linked:
        number_id = linkage(entry, repository)
        url = entry["issueURL"]
        require(re.search(re.escape(url) + r"(?![0-9A-Za-z_/?#=])", body, re.I),
                "Effective PR body requires every canonical issue URL", "phase-issues")
        if url not in remote_cache:
            remote_cache[url] = todo_issues.issue_view(workspace, repository, url)
        remote = remote_cache[url]
        issue_format.validate(remote["body"], entry["variant"])
        references = {url.lower(), "#" + str(number_id), repository.split("/", 1)[1].lower() + "#" + str(number_id)}
        if entry["relationship"] == "followup":
            require(not references & closing, "Followup issues cannot use closing references", "phase-issues")
        elif entry["variant"] == "UAT":
            require_accepted_uat(remote["body"])
    return result


def reconcile_todos(workspace, number, pr, names):
    require(isinstance(names, list) and bool(names) and len(set(names)) == len(names),
            "Select explicit unique folded TODO filenames", "phase-issues")
    directory(workspace, number)
    context = selected(workspace, number, phases.pad(number) + "-CONTEXT.md")
    context_record = todos.read_record(context)
    folded = section_body(context_record[1], "Folded Todos", level=3)
    for name in names:
        require(isinstance(name, str) and Path(name).name == name and "/" not in name
                and "\\" not in name and name.endswith(".md")
                and re.search(r"(?<![A-Za-z0-9_.-])" + re.escape(name) + r"(?![A-Za-z0-9_.-])", folded),
                "Select exact filenames recorded under Folded Todos", "path-escape")
    items = [{"file": name, "state": "pending"} for name in names]
    retry = "phase.reconcile-todos " + str(number) + " --pr " + str(pr) + " --todos " + " ".join(names)
    try:
        repository = todo_issues.target(workspace)
        pr_number = todo_issues.number_from_url(repository, pr, "pull")
        matching = [entry for entry in sessions(workspace) if entry.get("kind") == "phase"
                    and as_number(entry.get("label", "")) == as_number(number)]
        require(len(matching) == 1, "Select the phase's unique existing session", "phase-session")
        session = matching[0]
        recorded = session.get("pr") or {}
        require(isinstance(recorded, dict) and recorded.get("url") == pr and recorded.get("number") == pr_number,
                "PR must match the selected phase session", "phase-session")
        pull = todo_issues.json_call(workspace, "pr", "view", pr, "--repo", repository, "--json", delivery.PR_FIELDS)
        pr_identity(repository, session.get("branch"), pull)
        require(isinstance(pull, dict) and pull.get("url") == pr
                and pull.get("number") == pr_number and pull.get("headRefName") == session.get("branch")
                and pull.get("state") == "MERGED", "Matching MERGED PR readback is pending", "merge-pending")
    except VerbError as exc:
        return {"phase": str(number), "items": [dict(item, reason=str(exc)) for item in items],
                "retryable": True, "retry": retry}
    for item in items:
        name = item["file"]
        try:
            require(todos.read_record(context) == context_record, "Folded CONTEXT changed; reselect TODOs", "stale-todo")
            pending = todos.safe_directory(workspace, workspace.pending_todos) / name
            completed = todos.safe_directory(workspace, workspace.completed_todos) / name
            require(not todos.linked_path(pending) and not todos.linked_path(completed),
                    "Linked TODO paths cannot be reconciled", "path-escape")
            if not pending.exists() and completed.is_file():
                linkage(todos.read_record(completed)[0], repository)
                item["state"] = "already-completed"
                continue
            require(pending.is_file(), "Selected folded TODO is missing", "todo-not-found")
            metadata, body = todos.read_record(pending)
            linkage(metadata, repository)
            remote = todo_issues.issue_view(workspace, repository, metadata["issueURL"])
            if "Human acceptance" in [heading for _, heading in issue_format.headings(issue_format.visible_lines(remote["body"]))]:
                require_accepted_uat(remote["body"])
            require(todos.read_record(pending) == (metadata, body), "Selected TODO changed before reconciliation", "stale-todo")
            result = todos.complete(workspace, name)
            item.update(state="completed", completed=result["completed"])
        except VerbError as exc:
            item["reason"] = str(exc)
    return {"phase": str(number), "pr": pr, "items": items,
            "retryable": any(item["state"] == "pending" for item in items), "retry": retry}
