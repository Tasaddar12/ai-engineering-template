"""Reviewed, repository-pinned GitHub linkage for one pending TODO.

Callers hold the planning lock for the complete operation, including provider
reads and attempted-intent persistence. This is coordinator-serialized work.
"""
import hashlib
import json
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from . import delivery, gitops, issue_format, todos
from .paths import read_text
from .results import VerbError, require

HOST = "github.com"
REPO_FIELDS = "nameWithOwner,url,hasIssuesEnabled"
MARKER = "<!-- todo-id: {} -->"


def digest(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def call(workspace, *args):
    """Keep provider diagnostics (which may contain public/private input) local."""
    try:
        result = delivery.gh(workspace, *args)
    except VerbError:
        raise VerbError("GitHub operation unavailable; pending TODO preserved",
                        "issue-provider")
    require(result.returncode == 0,
            "GitHub operation failed; pending TODO preserved", "issue-provider")
    return result.stdout


def json_call(workspace, *args):
    try:
        return json.loads(call(workspace, *args))
    except ValueError:
        raise VerbError("GitHub returned malformed JSON; pending TODO preserved",
                        "issue-response")


def target(workspace):
    origin = gitops.git(workspace, "remote", "get-url", "origin", check=False)
    require(origin.returncode == 0, "GitHub origin required", "issue-repository")
    value = origin.stdout.strip()
    match = re.fullmatch(r"git@github\.com:([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?", value)
    if not match:
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError:
            raise VerbError("Invalid GitHub origin", "issue-repository")
        require(parsed.scheme in ("https", "ssh") and parsed.hostname == HOST
                and not parsed.query and not parsed.fragment and not port
                and (parsed.username is None or
                     (parsed.scheme == "ssh" and parsed.username == "git"))
                and parsed.password is None,
                "Only a GitHub HTTPS or SSH origin is supported", "issue-repository")
        match = re.fullmatch(r"/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?",
                             parsed.path)
    require(match is not None, "Invalid GitHub origin repository", "issue-repository")
    owner, name = match.groups()
    require(owner not in (".", "..") and name not in (".", ".."),
            "Invalid GitHub repository", "issue-repository")
    repository = HOST + "/" + owner + "/" + name
    call(workspace, "--version")
    call(workspace, "auth", "status", "--hostname", HOST)
    remote = json_call(workspace, "repo", "view", repository, "--json", REPO_FIELDS)
    require(isinstance(remote, dict)
            and isinstance(remote.get("nameWithOwner"), str)
            and isinstance(remote.get("url"), str)
            and remote.get("nameWithOwner", "").lower() == (owner + "/" + name).lower()
            and remote.get("url", "").lower() == ("https://" + repository).lower()
            and remote.get("hasIssuesEnabled") is True,
            "Origin repository verification failed or issues are disabled",
            "issue-repository")
    return repository


def number_from_url(repository, url, kind="issues"):
    require(isinstance(url, str), "A verified GitHub URL is required", "issue-url")
    match = re.fullmatch(re.escape("https://" + repository + "/" + kind + "/")
                         + r"([1-9][0-9]*)", url, re.IGNORECASE)
    require(match is not None, "URL must identify an item in the origin repository",
            "issue-url")
    return int(match.group(1))


def endpoint(repository, suffix):
    return "repos/" + repository.split("/", 1)[1] + "/" + suffix


def api(workspace, repository, suffix, pages=False):
    args = ["api", endpoint(repository, suffix), "--hostname", HOST, "--method", "GET"]
    if pages:
        args += ["--paginate", "--slurp"]
    return json_call(workspace, *args)


def record(repository, value, kind="issues"):
    require(isinstance(value, dict), "Invalid GitHub item", "issue-response")
    number = value.get("number")
    require(isinstance(number, int) and not isinstance(number, bool) and number > 0,
            "Invalid GitHub item number", "issue-response")
    url = value.get("html_url")
    require(number_from_url(repository, url, kind) == number,
            "GitHub item URL/number mismatch", "issue-response")
    require(isinstance(value.get("title"), str)
            and (value.get("body") is None or isinstance(value.get("body"), str))
            and value.get("state") in ("open", "closed"),
            "Incomplete GitHub item context", "issue-response")
    require(kind != "issues" or "pull_request" not in value,
            "A pull request cannot be linked as an issue", "issue-response")
    return {"number": number, "url": url, "title": value["title"],
            "body": value.get("body") or "", "state": value["state"].upper()}


def collection(workspace, repository, kind):
    pages = api(workspace, repository, kind + "?state=all&per_page=100", pages=True)
    require(isinstance(pages, list) and bool(pages)
            and all(isinstance(page, list) and len(page) <= 100 for page in pages)
            and all(len(page) == 100 for page in pages[:-1]),
            "Incomplete paginated GitHub collection", "issue-response")
    result, seen = [], set()
    for page in pages:
        for item in page:
            require(isinstance(item, dict), "Invalid GitHub collection item", "issue-response")
            if kind == "issues" and "pull_request" in item:
                continue
            item_record = record(repository, item, "pull" if kind == "pulls" else "issues")
            require(item_record["number"] not in seen,
                    "Ambiguous GitHub pagination", "issue-response")
            seen.add(item_record["number"])
            if kind == "pulls":
                head = item.get("head")
                require(isinstance(head, dict) and isinstance(head.get("ref"), str),
                        "Incomplete pull request context", "issue-response")
                item_record["headRef"] = head["ref"]
            result.append(item_record)
    return result


def issue_view(workspace, repository, url):
    number = number_from_url(repository, url)
    item = record(repository, api(workspace, repository, "issues/" + str(number)))
    require(item["number"] == number, "Issue readback mismatch", "issue-response")
    return item


def lookup(workspace, repository, related_pr=None):
    issues = collection(workspace, repository, "issues")
    pulls = collection(workspace, repository, "pulls")
    branch = gitops.current_branch(workspace)
    selected = [pull for pull in pulls if pull["headRef"] == branch]
    if related_pr:
        number = number_from_url(repository, related_pr, "pull")
        remote = record(repository, api(workspace, repository, "pulls/" + str(number)), "pull")
        require(remote["number"] == number, "Related PR readback mismatch", "issue-response")
        selected = [pull for pull in selected if pull["number"] != number] + [remote]
    return sorted(issues, key=lambda item: item["number"]), sorted(
        selected, key=lambda item: item["number"])


def snapshot(metadata, body):
    return digest({"metadata": {key: value for key, value in metadata.items()
                                if key not in ("issuePublication", "issueURL", "issueNumber")},
                   "body": body})


def current(workspace, name):
    path = todos.resolve_pending(workspace, name)
    metadata, body = todos.read_record(path)
    return path, metadata, body


def prepare_identity(workspace, path, metadata, body, repository):
    require(not metadata.get("issueRepo") or (isinstance(metadata["issueRepo"], str)
            and metadata["issueRepo"].lower() == repository.lower()),
            "TODO is pinned to another repository", "issue-repository")
    metadata["todoId"] = todos.identity(metadata.get("todoId"))
    metadata["issueRepo"] = repository
    todos.save_record(path, metadata, body)


def preview(workspace, name, related_pr=None):
    path, metadata, body = current(workspace, name)
    repository = target(workspace)
    prepare_identity(workspace, path, metadata, body, repository)
    local_snapshot = snapshot(metadata, body)
    candidates, context = lookup(workspace, repository, related_pr)
    path, metadata, body = unchanged(workspace, name, local_snapshot)
    token = digest({"todo": snapshot(metadata, body), "repository": repository,
                    "candidates": candidates, "context": context, "relatedPR": related_pr})
    publication = metadata.get("issuePublication") or {}
    require(isinstance(publication, dict), "Invalid publication metadata", "issue-unresolved")
    publication = dict(publication, previewToken=token, relatedPR=related_pr)
    publication.setdefault("state", "prepared")
    metadata["issuePublication"] = publication
    todos.save_record(path, metadata, body)
    return {"file": workspace.relative(path), "todoId": metadata["todoId"],
            "repository": repository, "previewToken": token,
            "privateLocal": {"label": "PRIVATE LOCAL REVIEW INPUT",
                             "title": metadata.get("title") or path.stem,
                             "body": body, "metadata": json.loads(json.dumps(metadata, default=str))},
            "candidates": candidates, "relatedPRs": context}


def reviewed_body(body_file, todo_id, selected_path):
    require(isinstance(body_file, str) and bool(body_file.strip()),
            "A separately reviewed public body file is required", "issue-review")
    path = Path(body_file)
    require(path.resolve() != selected_path.resolve(),
            "Public body must be a separate reviewed file, not the private TODO",
            "issue-review")
    try:
        content = read_text(path)
    except (VerbError, OSError, UnicodeError):
        raise VerbError("Reviewed public body file cannot be read", "issue-review")
    require(content.strip(), "Reviewed public body cannot be empty", "issue-review")
    require("<!-- todo-id:" not in content,
            "Reviewed body must not contain a retry marker", "issue-review")
    return content.rstrip() + "\n\n" + MARKER.format(todo_id) + "\n"


def linked_result(workspace, path, metadata, body, issue, created=False, recovered=False):
    metadata["issueURL"], metadata["issueNumber"] = issue["url"], issue["number"]
    publication = dict(metadata.get("issuePublication") or {}, state="linked")
    metadata["issuePublication"] = publication
    todos.save_record(path, metadata, body)
    return {"file": workspace.relative(path), "todoId": metadata["todoId"],
            "repository": metadata["issueRepo"], "issueURL": issue["url"],
            "issueNumber": issue["number"], "linked": True, "created": created,
            "recovered": recovered}


def unchanged(workspace, name, expected):
    path, metadata, body = current(workspace, name)
    require(snapshot(metadata, body) == expected,
            "Selected TODO changed; pending context preserved", "stale-preview")
    return path, metadata, body


def publish(workspace, name, preview_token, title, body_file,
            existing_issue=None, no_match=False, variant=None):
    require(isinstance(preview_token, str) and bool(preview_token.strip()),
            "A current reviewed preview token is required", "issue-review")
    require(isinstance(title, str) and bool(title.strip()),
            "A separately reviewed public title is required", "issue-review")
    require(isinstance(no_match, bool) and bool(existing_issue) != no_match,
            "Choose exactly one existing issue or explicit --no-match", "issue-review")
    path, metadata, body = current(workspace, name)
    publication = metadata.get("issuePublication") or {}
    require(isinstance(publication, dict), "Invalid publication metadata", "issue-unresolved")
    require(metadata.get("todoId") and metadata.get("issueRepo")
            and publication.get("previewToken"), "Preview this TODO first", "issue-review")
    public_body = reviewed_body(body_file, metadata["todoId"], path)
    issue_format.validate(public_body, variant)
    intent = digest({"title": title, "body": public_body})
    repository = target(workspace)
    require(isinstance(metadata["issueRepo"], str)
            and metadata["issueRepo"].lower() == repository.lower(),
            "TODO origin repository changed", "issue-repository")
    require(not metadata.get("issueURL") or publication.get("state") == "linked",
            "An unresolved existing linkage cannot authorize creation", "issue-unresolved")
    if metadata.get("issueURL") and publication.get("state") == "linked":
        issue = issue_view(workspace, repository, metadata["issueURL"])
        require(issue["number"] == metadata.get("issueNumber"),
                "Linked issue number mismatch", "issue-response")
        return {"file": workspace.relative(path), "todoId": metadata["todoId"],
                "repository": repository, "issueURL": issue["url"],
                "issueNumber": issue["number"], "linked": True, "created": False,
                "recovered": False}
    candidates, context = lookup(workspace, repository, publication.get("relatedPR"))
    local_snapshot = snapshot(metadata, body)
    token = digest({"todo": local_snapshot, "repository": repository,
                    "candidates": candidates, "context": context,
                    "relatedPR": publication.get("relatedPR")})
    require(preview_token == publication.get("previewToken") == token,
            "TODO or candidate/context snapshot changed; renew review", "stale-preview")
    marker = MARKER.format(metadata["todoId"])
    matches = [candidate for candidate in candidates
               if marker in candidate["body"].splitlines()]
    require(len(matches) <= 1, "Multiple exact TODO markers require human resolution",
            "issue-unresolved")
    state = publication.get("state")
    if state == "attempted":
        require(publication.get("intentDigest") == intent
                and publication.get("publicTitle") == title
                and publication.get("snapshotDigest") == local_snapshot,
                "Attempted publication intent changed; human resolution required",
                "issue-unresolved")
        require(len(matches) == 1,
                "Attempted publication unresolved; creation will not be retried",
                "issue-unresolved")
        issue = issue_view(workspace, repository, matches[0]["url"])
        require(digest({"title": issue["title"], "body": issue["body"]}) == intent,
                "Recovered marker does not match stored public intent", "issue-unresolved")
        path, metadata, body = unchanged(workspace, name, local_snapshot)
        return linked_result(workspace, path, metadata, body, issue, recovered=True)
    require(state == "prepared"
            and not any(publication.get(key) for key in
                        ("intentDigest", "snapshotDigest", "publicTitle")),
            "Unresolved publication state", "issue-unresolved")
    if matches or existing_issue:
        selected = matches[0]["url"] if matches else existing_issue
        require(not existing_issue or not matches
                or existing_issue.lower() == selected.lower(),
                "Exact marker must be reused; conflicting selection", "issue-unresolved")
        reviewed = next((candidate for candidate in candidates
                         if candidate["url"].lower() == selected.lower()), None)
        require(reviewed is not None,
                "Selected issue was not in the reviewed candidate set", "issue-review")
        issue = issue_view(workspace, repository, selected)
        require(issue == reviewed,
                "Selected issue changed after review; renew review", "stale-preview")
        path, metadata, body = unchanged(workspace, name, local_snapshot)
        return linked_result(workspace, path, metadata, body, issue)
    path, metadata, body = unchanged(workspace, name, local_snapshot)
    metadata["issuePublication"] = dict(publication, state="attempted", publicTitle=title,
                                       intentDigest=intent, snapshotDigest=local_snapshot)
    todos.save_record(path, metadata, body)
    # A distinct reviewed file avoids accidentally publishing the private TODO.
    with tempfile.TemporaryDirectory(prefix="todo-public-") as directory:
        public_path = Path(directory) / "body.md"
        public_path.write_text(public_body, encoding="utf-8", newline="\n")
        url = call(workspace, "issue", "create", "--repo", repository,
                   "--title", title, "--body-file", str(public_path)).strip()
    issue = issue_view(workspace, repository, url)
    require(digest({"title": issue["title"], "body": issue["body"]}) == intent,
            "Created issue does not match reviewed public intent", "issue-unresolved")
    path, metadata, body = unchanged(workspace, name, local_snapshot)
    return linked_result(workspace, path, metadata, body, issue, created=True)


def require_closed(workspace, metadata):
    publication = metadata.get("issuePublication") or {}
    require(isinstance(publication, dict)
            and publication.get("state") in (None, "prepared", "linked"),
            "Attempted or unresolved publication prevents completion", "issue-unresolved")
    require(publication.get("state") == "linked"
            or not any(publication.get(key) for key in
                       ("intentDigest", "snapshotDigest", "publicTitle")),
            "Unresolved publication intent prevents completion", "issue-unresolved")
    if publication.get("state") == "linked":
        require(metadata.get("issueURL"), "Linked publication has no verified URL",
                "issue-unresolved")
    if metadata.get("issueURL"):
        repository = target(workspace)
        require(isinstance(metadata.get("issueRepo"), str)
                and metadata["issueRepo"].lower() == repository.lower(),
                "Linked TODO repository mismatch", "issue-repository")
        issue = issue_view(workspace, repository, metadata["issueURL"])
        require(issue["number"] == metadata.get("issueNumber")
                and issue["state"] == "CLOSED",
                "Only a verified closed linked issue permits completion", "issue-open")
