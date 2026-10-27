"""Issue publication is bound to a validated preview and verified readback."""
import hashlib
import json
from pathlib import Path
import re
import tempfile
from . import delivery, models, records, repository
from .core import Failure, digest, load_json, now, planning_lock, read, root, safe_path, write, write_json
from .text import join_frontmatter, split_frontmatter


def todo_path(value):
    path = Path(value)
    if not path.is_absolute() and len(path.parts) == 1:
        path = records.planning()/"todos/pending"/path
    path = safe_path(path)
    if not path.is_relative_to(records.planning()/"todos/pending") or not path.is_file():
        raise Failure("todo-not-found", str(path))
    return path


def validate(title, body):
    if not title.strip() or not body.strip():
        raise Failure("invalid-issue", "Issue title and body must be nonempty")
    template = models.NAMESPACE/"engineer/templates/issue.md"
    if not template.is_file():
        raise Failure("issue-template-missing", "Install engineer/templates/issue.md before publishing")
    headings = re.findall(r"(?m)^##\s+(.+)$", read(template))
    missing = [heading for heading in headings if not re.search(r"(?m)^##\s+"+re.escape(heading)+r"\s*$", body)]
    if missing:
        raise Failure("invalid-issue", "Required issue sections missing", missing=missing)
    return template


def publication(args, action, family="todo"):
    if family == "todo":
        source = todo_path(args.need())
    else:
        directory = records.phase_dir(args.need())
        source = safe_path(directory/args.need(1))
        if not source.is_file():
            raise Failure("finding-record-not-found", str(source))
    metadata, content = split_frontmatter(read(source))
    finding = None
    if family == "phase":
        identifier = args.need(2)
        entries = metadata.get("issue_refs", [])
        matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("id") == identifier]
        if len(matches) != 1:
            raise Failure("finding-not-found", identifier)
        finding = matches[0]
    title = str(args.get("title", (finding or {}).get("summary", metadata.get("title", source.stem))))
    body = read(safe_path(args.get("body-file"))) if args.has("body-file") else str(args.get("body", content))
    template = validate(title, body)
    snapshot = {"source": str(source), "source_digest": digest([source, template]), "title": title, "body": body,
                "labels": args.all("labels"), "family": family, "finding": args.arg(2)}
    token = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
    preview = records.planning()/"issue-previews"/(token+".json")
    if action == "preview":
        with planning_lock():
            write_json(preview, {**snapshot, "created": now(), "used": False})
        return {"previewToken": token, "preview_token": token, "title": title, "body": body,
                "source": str(source), "snapshotDigest": snapshot["source_digest"]}
    supplied = args.get("preview-token")
    saved = load_json(records.planning()/"issue-previews"/(str(supplied)+".json")) if re.fullmatch(r"[a-f0-9]{64}", str(supplied)) else None
    if supplied != token or not saved or saved.get("used") or saved.get("source_digest") != snapshot["source_digest"]:
        raise Failure("stale-issue-preview", "Preview token is absent, consumed, or no longer matches the issue")
    existing = (finding or metadata).get("issue_url", (finding or metadata).get("url", metadata.get("issue")))
    if action == "publish" and existing:
        raise Failure("issue-already-linked", str(existing))
    if action == "update" and not existing:
        raise Failure("issue-not-linked", str(source))
    if existing:
        repository.require_url(str(existing), "issues")
    # A provider timeout can mean the issue was created. Consume before calling
    # the provider so an uncertain outcome cannot create a duplicate on retry.
    with planning_lock():
        current = load_json(preview)
        if current.get("used"):
            raise Failure("issue-preview-consumed", "Inspect the prior publication attempt before retrying")
        current.update({"used": "publishing", "attempted": now()})
        write_json(preview, current)
    with tempfile.TemporaryDirectory(prefix="engineer-issue-") as directory:
        path = Path(directory)/"body.md"
        path.write_text(body, encoding="utf-8")
        command = ["issue", "create", "--title", title, "--body-file", str(path)] if action == "publish" else ["issue", "edit", str(existing), "--title", title, "--body-file", str(path)]
        for label in args.all("labels"):
            command += ["--label" if action == "publish" else "--add-label", label]
        result = delivery.gh(command)
    url = existing if action == "update" else result.stdout.strip().splitlines()[-1]
    if not re.match(r"https://[^/]+/[^/]+/[^/]+/issues/\d+$", str(url)):
        raise Failure("issue-publication-uncertain", "Provider returned no issue URL; inspect before retrying", output=result.stdout)
    repository.require_url(str(url), "issues")
    issue = json.loads(delivery.gh(["issue", "view", str(url), "--json", "url,title,body,state"]).stdout)
    if issue.get("title") != title or issue.get("body", "").strip() != body.strip():
        raise Failure("issue-readback-mismatch", "Published issue differs from the validated preview", url=url)
    with planning_lock():
        if digest([source, template]) != snapshot["source_digest"]:
            raise Failure("issue-source-drift", "Issue published but source changed; reconcile the returned URL", url=url)
        metadata, content = split_frontmatter(read(source))
        if family == "phase":
            matches = [entry for entry in metadata.get("issue_refs", []) if entry.get("id") == args.need(2)]
            if len(matches) != 1:
                raise Failure("finding-drift", "Published finding declaration changed", url=url)
            matches[0].update({"issue_url": url, "url": url, "published": now()})
        else:
            metadata["issue_url"] = url
            metadata["issue_published"] = now()
        write(source, join_frontmatter(metadata, content))
        saved.update({"used": True, "url": url})
        write_json(preview, saved)
    return {"published": True, "url": url, "issue": issue, "source": str(source)}
