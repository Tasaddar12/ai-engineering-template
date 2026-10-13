"""Repository-pinned GitLab issue reads/create for the reviewed TODO lifecycle."""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote

from . import gitops, providers
from .results import VerbError, require


class Repository(str):
    """A string-compatible state-machine identity with verified provider context."""
    def __new__(cls, target, project_id):
        value = super().__new__(cls, target["repository"])
        value.target, value.project_id = target, project_id
        return value


def call(workspace, *args):
    try:
        # Explicit host/API selectors defeat inherited repository/host overrides.
        env = dict(os.environ)
        for key in ("GITLAB_REPO", "GLAB_REPO", "GITLAB_HOST", "GITLAB_API_HOST",
                    "GITLAB_API_PROTOCOL", "GLAB_API_PROTOCOL", "API_PROTOCOL"):
            env.pop(key, None)
        if "--hostname" in args:
            host = args[args.index("--hostname") + 1]
            env.update(GITLAB_HOST=host, GITLAB_API_HOST=host,
                       GLAB_API_PROTOCOL="https", API_PROTOCOL="https",
                       GITLAB_SUBFOLDER="/", GLAB_ENABLE_CI_AUTOLOGIN="false",
                       GLAB_DEBUG="false", GLAB_DEBUG_HTTP="false", GLAB_CHECK_UPDATE="false")
        result = subprocess.run(["glab", *args], cwd=str(workspace.root), env=env,
                                capture_output=True, text=True, encoding="utf-8", timeout=300)
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        raise VerbError("GitLab operation unavailable; pending TODO preserved", "issue-provider")
    require(result.returncode == 0, "GitLab operation failed; pending TODO preserved", "issue-provider")
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise VerbError("GitLab returned malformed JSON; pending TODO preserved", "issue-response")


def api(workspace, target, suffix="", method="GET", input_file=None):
    endpoint = "projects/" + quote(target["project"], safe="") + ("/" + suffix if suffix else "")
    args = ["api", endpoint, "--hostname", target["host"], "--method", method]
    if input_file:
        args += ["--input", str(input_file)]
    return call(workspace, *args)


def verify(workspace, target):
    # The authenticated project read verifies host, full namespace and capability.
    # No CLI-specific default repository or placeholder is ever consumed.
    value = api(workspace, target)
    require(isinstance(value, dict)
            and value.get("path_with_namespace") == target["project"]
            and value.get("web_url") == target["web_url"]
            and value.get("issues_enabled") is True
            and isinstance(value.get("id"), int) and not isinstance(value["id"], bool)
            and value["id"] > 0,
            "Origin repository verification failed or issues are disabled", "issue-repository")
    return Repository(target, value["id"])


def record(repository, value, kind="issues"):
    require(isinstance(value, dict), "Invalid GitLab item", "issue-response")
    number = value.get("iid")
    require(isinstance(number, int) and not isinstance(number, bool) and number > 0,
            "Invalid GitLab item number", "issue-response")
    require(value.get("project_id") == repository.project_id
            and isinstance(value.get("project_id"), int)
            and not isinstance(value["project_id"], bool),
            "GitLab item project mismatch", "issue-response")
    url = value.get("web_url")
    require(providers.item_number(repository.target, url, kind) == number,
            "GitLab item URL/number mismatch", "issue-response")
    states = ("opened", "closed") if kind == "issues" else ("opened", "closed", "merged")
    require(isinstance(value.get("title"), str)
            and (value.get("description") is None or isinstance(value.get("description"), str))
            and value.get("state") in states,
            "Incomplete GitLab item context", "issue-response")
    result = {"number": number, "url": url, "title": value["title"],
              "body": value.get("description") or "",
              "state": "OPEN" if value["state"] == "opened" else "CLOSED"}
    if kind == "merge_requests":
        require(isinstance(value.get("source_branch"), str),
                "Incomplete merge request context", "issue-response")
        result.update(headRef=value["source_branch"], merged=value["state"] == "merged")
    return result


def collection(workspace, repository, kind):
    result, seen, page = [], set(), 1
    while True:
        values = api(workspace, repository.target,
                     kind + "?state=all&per_page=100&page=" + str(page))
        require(isinstance(values, list) and len(values) <= 100,
                "Incomplete paginated GitLab collection", "issue-response")
        for value in values:
            item = record(repository, value, kind)
            require(item["number"] not in seen, "Ambiguous GitLab pagination", "issue-response")
            seen.add(item["number"])
            result.append(item)
        if len(values) < 100:
            return result
        page += 1


def issue_view(workspace, repository, url):
    number = providers.item_number(repository.target, url)
    result = record(repository, api(workspace, repository.target, "issues/" + str(number)))
    require(result["number"] == number, "Issue readback mismatch", "issue-response")
    return result


def lookup(workspace, repository, related_pr=None):
    issues = collection(workspace, repository, "issues")
    requests = collection(workspace, repository, "merge_requests")
    branch = gitops.current_branch(workspace)
    selected = [item for item in requests if item["headRef"] == branch]
    if related_pr:
        number = providers.item_number(repository.target, related_pr, "merge_requests")
        remote = record(repository, api(workspace, repository.target,
                                        "merge_requests/" + str(number)), "merge_requests")
        require(remote["number"] == number, "Related MR readback mismatch", "issue-response")
        selected = [item for item in selected if item["number"] != number] + [remote]
    return sorted(issues, key=lambda item: item["number"]), sorted(selected, key=lambda item: item["number"])


def create(workspace, repository, title, public_body):
    with tempfile.TemporaryDirectory(prefix="todo-public-") as directory:
        payload = Path(directory) / "issue.json"
        payload.write_text(json.dumps({"title": title, "description": public_body}, ensure_ascii=False),
                           encoding="utf-8", newline="\n")
        created = record(repository, api(workspace, repository.target, "issues", "POST", payload))
    return created["url"]
