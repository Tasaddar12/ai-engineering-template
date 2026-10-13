"""Declared phase issue gates using the existing reviewed TODO publisher.

The coordinator supplies completeness and acceptance judgments. These guards
validate the selected records and provider evidence, never infer omitted prose.
"""
import copy
import re
import tempfile
import uuid
from pathlib import Path

from . import issue_format, phases, todo_issues, todos
from .paths import read_text
from .results import VerbError, require
from .roadmap import Roadmap, as_number

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
