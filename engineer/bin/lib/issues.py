"""Origin-bound GitHub lifecycle, reviewed publication and durable reconciliation."""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
import re
import tempfile
import time
from . import delivery, issue_format, models, records, repository
from .core import Args, Failure, digest, load_json, now, planning_lock, read, safe_path, slug, write, write_json
from .text import join_frontmatter, split_frontmatter

FIELDS = "number,url,title,body,state,labels"
_deadline = ContextVar("issue_provider_deadline", default=None)


@contextmanager
def budget(seconds):
    """Bound all provider calls in this context; nesting cannot extend a budget."""
    deadline = time.monotonic()+float(seconds)
    current = _deadline.get()
    token = _deadline.set(min(current, deadline) if current is not None else deadline)
    try:
        yield
    finally:
        _deadline.reset(token)


def enabled(args, key):
    return args.has(key) and str(args.get(key)).lower() in ("true", "1", "yes")


def todo_path(value):
    path = Path(value)
    if not path.is_absolute() and len(path.parts) == 1:
        path = records.planning()/"todos/pending"/path
    path = safe_path(path)
    if not path.is_relative_to(records.planning()/"todos/pending") or not path.is_file():
        raise Failure("todo-not-found", str(path))
    return path


def validate(title, body, variant=None):
    if not title.strip() or not body.strip():
        raise Failure("invalid-issue", "Issue title and body must be nonempty")
    template = models.NAMESPACE/"engineer/templates/issue.md"
    if variant is None:
        matches = []
        for name in issue_format.VARIANTS:
            try:
                issue_format.validate(body, name, template)
                matches.append(name)
            except Failure as exc:
                if exc.code != "issue-format":
                    raise
        if len(matches) != 1:
            raise Failure("issue-variant", "Supply --variant with the exact canonical variant")
        variant = matches[0]
    issue_format.validate(body, variant, template)
    lines = issue_format.visible_lines(body)
    section = []
    for line in [*lines, "## END"]:
        if re.match(r"^ {0,3}## ", line):
            if section and not any(value.strip() for value in section[1:]):
                raise Failure("invalid-issue", "Every issue section requires concrete content", section=section[0])
            section = [line]
        elif section:
            section.append(line)
    placeholders = re.findall(r"\[(?![ xX]\])[^\]\n]+\]", "\n".join(lines))
    if any(value in body for value in ("[Concrete ", "[Observable ", "[Actual ", "[Source ")) or any(
            value in read(template) and not re.search(r"\]\(|^\[(?:REQ|THR|UAT)-", value) for value in placeholders):
        raise Failure("invalid-issue", "Replace canonical template placeholders with reviewed facts")
    return template if template.is_file() else Path(issue_format.__file__)


def provider(argv, origin):
    deadline = _deadline.get()
    if deadline is not None and deadline <= time.monotonic():
        raise Failure("issue-budget-exhausted", "Issue provider time budget exhausted")
    if repository.identity() != origin:
        raise Failure("issue-origin-drift", "Repository origin changed during issue operation")
    remaining = min(60, deadline-time.monotonic()) if deadline is not None else 60
    if remaining <= 0:
        raise Failure("issue-budget-exhausted", "Issue provider time budget exhausted")
    return delivery.gh(argv, timeout=remaining)


def issue_get(value, origin):
    value = str(value)
    if value.isdecimal():
        value = "https://"+origin["slug"]+"/issues/"+value
    repository.require_url(value, "issues")
    issue = json.loads(provider(["issue", "view", value, "--json", FIELDS], origin).stdout)
    if issue.get("url") != value:
        raise Failure("issue-readback-mismatch", "Provider returned a different canonical issue", url=value)
    return issue


def candidates(title, origin, limit=200):
    query = '"'+title.replace('"', ' ').replace("\n", " ")+'"'
    issues = json.loads(provider(["issue", "list", "--state", "all", "--search", query,
                                  "--limit", str(limit), "--json", FIELDS], origin).stdout)
    prs = json.loads(provider(["pr", "list", "--state", "all", "--search", query,
                               "--limit", str(limit), "--json", "number,url,title,body,state"], origin).stdout)
    for item in issues:
        repository.require_url(item["url"], "issues")
    for item in prs:
        repository.require_url(item["url"], "pull")
    return {"issues": issues, "pull_requests": prs, "query": query,
            "possibly_truncated": len(issues) >= limit or len(prs) >= limit}


def source_record(args, family):
    if family == "todo":
        source = todo_path(args.need())
    else:
        directory = records.phase_dir(args.need())
        source = safe_path(directory/args.need(1))
        if source.parent != directory or not source.is_file():
            raise Failure("finding-record-not-found", str(source))
    metadata, content = split_frontmatter(read(source))
    finding = None
    if family == "phase":
        matches = [entry for entry in metadata.get("issue_refs", [])
                   if isinstance(entry, dict) and entry.get("id") == args.need(2)]
        if len(matches) != 1:
            raise Failure("finding-not-found", args.need(2))
        finding = matches[0]
    return source, metadata, content, finding


def linked_url(metadata, finding):
    owner = finding if finding is not None else metadata
    return owner.get("issue_url") or owner.get("url") or (metadata.get("issue") if finding is None else None)


def link_record(args, family, url, expected_digest=None):
    with planning_lock():
        source, metadata, content, finding = source_record(args, family)
        if expected_digest and digest([source]) != expected_digest:
            raise Failure("issue-source-drift", "Source changed; reconcile the verified URL", url=url)
        existing = linked_url(metadata, finding)
        if existing and existing != url:
            raise Failure("issue-already-linked", "Refusing to replace another issue relationship", url=existing)
        if finding is None:
            metadata.update({"issue_url": url, "issue_published": now()})
        else:
            finding.update({"issue_url": url, "url": url, "published": now()})
        write(source, join_frontmatter(metadata, content))
    return source


def reconcile(intent, origin):
    # Enumerate all states without search indexing: exact durable markers are
    # the only automated duplicate match. Absence never authorizes a retry.
    items = json.loads(provider(["issue", "list", "--state", "all", "--limit", "10000",
                                 "--json", FIELDS], origin).stdout)
    matches = [item for item in items if intent["marker"] in item.get("body", "")]
    for item in matches:
        repository.require_url(item["url"], "issues")
    if len(matches) != 1:
        raise Failure("issue-publication-uncertain", "Creation is never repeated after an uncertain attempt; reconcile its durable marker",
                      marker=intent["marker"], candidates=[item["url"] for item in matches], possibly_truncated=len(items) >= 10000)
    return issue_get(matches[0]["url"], origin)


def publication(args, action, family="todo"):
    source, metadata, content, finding = source_record(args, family)
    origin = repository.identity()
    title = str(args.get("title", (finding or {}).get("summary", metadata.get("title", source.stem))))
    body = read(safe_path(args.get("body-file"))) if args.has("body-file") else str(args.get("body", content))
    template = validate(title, body, args.get("variant"))
    snapshot = {"source": str(source), "source_digest": digest([source, template]), "title": title, "body": body,
                "labels": sorted(set(args.all("labels"))), "family": family, "finding": args.arg(2), "origin": origin}
    token = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
    preview = records.planning()/"issue-previews"/(token+".json")
    existing = linked_url(metadata, finding)
    if action == "preview":
        context = candidates(title, origin)
        context["source_context"] = candidates(source.name, origin)
        context["possibly_truncated"] = context["possibly_truncated"] or context["source_context"]["possibly_truncated"]
        with planning_lock():
            previous = load_json(preview, {})
            write_json(preview, {**snapshot, "created": previous.get("created", now()),
                                 "used": previous.get("used", False), "candidates": context})
        return {"previewToken": token, "preview_token": token, "title": title, "body": body,
                "labels": snapshot["labels"], "source": str(source), "snapshotDigest": snapshot["source_digest"],
                "origin": origin, "candidates": context, "linked_url": existing}
    if action not in ("publish", "update"):
        raise Failure("unsupported-issue-action", action, 2)
    supplied = str(args.get("preview-token", ""))
    saved_path = records.planning()/"issue-previews"/(supplied+".json") if re.fullmatch(r"[a-f0-9]{64}", supplied) else None
    saved = load_json(saved_path) if saved_path else None
    # A completed publication changes its own local source digest. An identical
    # token retry reads the linked issue instead of creating another tracker.
    if saved and existing and action == "publish":
        comparable = ("source", "title", "body", "labels", "family", "finding", "origin")
        if all(saved.get(key) == snapshot.get(key) for key in comparable):
            issue = issue_get(existing, origin)
            completed_identity = {"origin": origin, "source": str(source.relative_to(records.planning())), "family": family, "finding": args.arg(2)}
            completed_key = hashlib.sha256(json.dumps(completed_identity, sort_keys=True).encode()).hexdigest()
            expected_body = body.rstrip()+"\n\n<!-- engineer-issue-intent:"+completed_key+" -->"
            labels = {label["name"] if isinstance(label, dict) else label for label in issue.get("labels", [])}
            if issue["title"] != title or issue["body"].strip() != expected_body.strip() or not set(snapshot["labels"]) <= labels:
                raise Failure("issue-readback-mismatch", "Completed publication changed at provider", url=existing)
            return {"published": True, "url": existing, "issue": issue, "source": str(source), "reconciled": True}
    saved = saved if supplied == token else None
    if not saved or saved.get("source_digest") != snapshot["source_digest"]:
        raise Failure("stale-issue-preview", "Preview token is absent or no longer matches the reviewed issue")
    if action == "update" and not existing:
        raise Failure("issue-not-linked", str(source))
    if existing:
        repository.require_url(str(existing), "issues")
    # Source identity binds all preview variants to one create intent. Changed
    # title/body cannot create a second issue after an uncertain first attempt.
    identity = {"origin": origin, "source": str(source.relative_to(records.planning())),
                "family": family, "finding": args.arg(2)}
    intent_key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    intent_path = records.planning()/"issue-intents"/(intent_key+".json")
    marker = "<!-- engineer-issue-intent:"+intent_key+" -->"
    published_body = body.rstrip()+"\n\n"+marker if action == "publish" else body
    source_digest = digest([source])
    with planning_lock():
        intent = load_json(intent_path, {})
        if action == "publish" and existing and intent.get("url") != existing:
            raise Failure("issue-already-linked", str(existing))
        retry = action == "publish" and bool(intent)
        if retry and intent.get("token") != token:
            raise Failure("issue-intent-conflict", "Reconcile the prior create intent before changing its reviewed body", intent=intent)
        if not retry:
            intent = {**identity, "marker": marker, "token": token, "state": "publishing", "attempted": now()}
            if action == "publish":
                write_json(intent_path, intent)
        saved.update({"used": "publishing", "attempted": now()})
        write_json(preview, saved)
    if retry:
        issue = issue_get(intent["url"], origin) if intent.get("url") else reconcile(intent, origin)
    else:
        with tempfile.TemporaryDirectory(prefix="engineer-issue-") as directory:
            path = Path(directory)/"body.md"
            path.write_text(published_body, encoding="utf-8")
            argv = (["issue", "create", "--title", title] if action == "publish" else
                    ["issue", "edit", str(existing), "--title", title]) + ["--body-file", str(path)]
            for label in snapshot["labels"]:
                argv += ["--label" if action == "publish" else "--add-label", label]
            result = provider(argv, origin)
        urls = re.findall(r"https://[^\s]+/issues/\d+", result.stdout)
        url = existing if action == "update" else (urls[-1] if urls else None)
        if not url:
            issue = reconcile(intent, origin)
        else:
            issue = issue_get(url, origin)
    url = issue["url"]
    if action == "publish":
        with planning_lock():
            intent.update({"url": url, "state": "readback"})
            write_json(intent_path, intent)
    actual_labels = {label["name"] if isinstance(label, dict) else label for label in issue.get("labels", [])}
    if issue.get("title") != title or issue.get("body", "").strip() != published_body.strip() or not set(snapshot["labels"]) <= actual_labels:
        raise Failure("issue-readback-mismatch", "Published issue differs from reviewed title, body or labels", url=url)
    if digest([source, template]) != snapshot["source_digest"]:
        # A completed retry can legitimately encounter the URL linked by itself.
        if not (retry and existing == url and saved.get("url") == url):
            raise Failure("issue-source-drift", "Issue exists but source changed; reconcile the URL", url=url)
    link_record(args, family, url, source_digest)
    with planning_lock():
        saved.update({"used": True, "url": url})
        write_json(preview, saved)
        if action == "publish":
            intent.update({"state": "complete", "completed": now()})
            write_json(intent_path, intent)
    return {"published": True, "url": url, "issue": issue, "source": str(source), "reconciled": retry}


def generated_body(args, variant):
    """Render only supplied report facts; unknown evidence stays explicit."""
    problem = str(args.get("problem", args.get("description", args.need())))
    unknown = "Unknown; investigation must establish this before acceptance."
    related = "\n".join(args.all("source-links") + args.all("links")) or "No source links supplied; local capture is the source record."
    if variant == "Bug":
        fields = {
            "Problem": problem,
            "Expected behavior": str(args.get("expected", unknown)),
            "Actual behavior": str(args.get("actual", problem)),
            "Reproduction": "- Build/version: "+str(args.get("revision", "Unknown"))+"\n- Environment: "+str(args.get("environment", "Unknown"))+"\n- Entry point: "+str(args.get("entry-point", "Unknown"))+"\n- Prepared setup: "+str(args.get("setup", "Unknown"))+"\n\n"+str(args.get("reproduction", "Unknown; retain the original report and establish a safe reproduction.")),
            "Safe evidence": str(args.get("evidence", "No execution evidence supplied; this is a captured report, not a verified diagnosis.")),
            "Impact": str(args.get("impact", "Unknown; triage affected users and severity.")),
            "Acceptance": "- [ ] "+str(args.get("acceptance", "Establish the expected behavior, correct the reported failure and record regression evidence at the corrected revision.")),
            "Scope": str(args.get("scope", "Investigate and resolve this reported defect. No unrelated implementation or closure is authorized by capture.")),
            "Related links": related,
        }
    elif variant == "Enhancement":
        fields = {"User need": problem, "Proposed outcome": str(args.get("expected", problem)),
                  "Current limitation and evidence": str(args.get("evidence", unknown)),
                  "Impact": str(args.get("impact", unknown)),
                  "Scope": str(args.get("scope", "Capture and triage this idea; implementation requires its own authority.")),
                  "Acceptance": "- [ ] "+str(args.get("acceptance", "Define and deliver an observable outcome within approved scope.")),
                  "Related links": related}
    else:
        raise Failure("reviewed-body-required", "This variant requires a reviewed body preserving actual decisions and human fields")
    return "\n\n".join("## "+heading+"\n\n"+fields[heading] for heading in issue_format.FALLBACK_HEADINGS[variant])+"\n"


def capture(args, action):
    """Local capture by default. Pipeline callers supply reviewed public body."""
    local = Args([])
    local.pos, local.opts = list(args.pos), dict(args.opts)
    title = args.need()
    capture_inputs = {key: args.opts[key] for key in sorted(args.opts)
                      if key not in {"publish", "execution-authorized", "preview-token", "reuse-url", "source", "raw", "json"}}
    if args.has("body-file"):
        capture_inputs["body-file"] = read(safe_path(args.get("body-file")))
    fingerprint = hashlib.sha256(json.dumps({"title": title, "action": action, "inputs": capture_inputs}, sort_keys=True).encode()).hexdigest()
    if args.has("source"):
        path = todo_path(args.get("source"))
        metadata, content = split_frontmatter(read(path))
        if metadata.get("title") != title or metadata.get("issue_capture_fingerprint") != fingerprint:
            raise Failure("capture-conflict", "The pinned source differs from the original capture inputs")
        record = {"created": False, "path": str(path), **metadata}
    else:
        try:
            record = records.todo(local, "add")
            with planning_lock():
                path = Path(record["path"])
                metadata, content = split_frontmatter(read(path))
                metadata["issue_capture_fingerprint"] = fingerprint
                write(path, join_frontmatter(metadata, content))
                record.update(metadata)
        except Failure as exc:
            if exc.code != "todo-exists":
                raise
            path = records.planning()/"todos/pending"/(now()[:10]+"-"+slug(title)+".md")
            metadata, content = split_frontmatter(read(path))
            if metadata.get("title") != title or metadata.get("issue_capture_fingerprint") != fingerprint:
                raise Failure("capture-conflict", "Existing capture differs; select its exact todo record")
            record = {"created": False, "path": str(path), **metadata}
    if not (enabled(args, "publish") or enabled(args, "execution-authorized")):
        return {"captured": True, "published": False, "todo": record}
    existing = record.get("issue_url") or record.get("issue")
    if existing:
        return {"captured": True, "published": True, "todo": record, "issue": issue_get(existing, repository.identity()), "url": existing}
    publication_args = Args([])
    publication_args.pos, publication_args.opts = [record["path"]], dict(args.opts)
    variant = str(args.get("variant", "Bug" if action == "finding" else "Enhancement"))
    publication_args.opts["variant"] = [variant]
    if not (args.has("body-file") or args.has("body")):
        publication_args.opts["body"] = [generated_body(args, variant)]
    if args.has("reuse-url"):
        issue = issue_get(args.get("reuse-url"), repository.identity())
        link_record(publication_args, "todo", issue["url"], digest([Path(record["path"])]))
        return {"captured": True, "published": False, "linked": True, "todo": record, "issue": issue, "url": issue["url"]}
    # An uncertain create can already appear in search. Resume its exact durable
    # intent first, without querying candidates or allowing another create.
    identity = {"origin": repository.identity(),
                "source": str(Path(record["path"]).relative_to(records.planning())),
                "family": "todo", "finding": None}
    intent_key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    intent = load_json(records.planning()/"issue-intents"/(intent_key+".json"))
    if intent:
        if any(intent.get(key) != value for key, value in identity.items()) or not intent.get("token"):
            raise Failure("issue-intent-conflict", "Stored capture intent does not match its source and origin")
        publication_args.opts["preview-token"] = [intent["token"]]
        return {"captured": True, "todo": record, **publication(publication_args, "publish")}
    preview = publication(publication_args, "preview")
    # Pipeline authorization replaces a repeated human prompt, not deduplication:
    # matching candidates require a caller-selected canonical reuse/link action.
    context = preview["candidates"]
    if (context["issues"] or context["pull_requests"] or context["source_context"]["issues"]
            or context["source_context"]["pull_requests"] or context["possibly_truncated"]):
        return {"captured": True, "published": False, "needs_reconciliation": True, "todo": record, **preview}
    publication_args.opts["preview-token"] = [preview["preview_token"]]
    return {"captured": True, "todo": record, **publication(publication_args, "publish")}


def command(args, action):
    if action in ("capture", "finding"):
        return capture(args, action)
    if action == "validate":
        body = read(safe_path(args.get("body-file"))) if args.has("body-file") else str(args.get("body", ""))
        template = validate(str(args.get("title", "Issue")), body, args.get("variant"))
        return {"valid": True, "template": str(template), "structuralOnly": True}
    origin = repository.identity()
    if action in ("list", "search"):
        state = args.get("state", "all")
        if state not in ("all", "open", "closed"):
            raise Failure("invalid-issue-state", str(state), 2)
        limit = int(args.get("limit", 200))
        if not 1 <= limit <= 10000:
            raise Failure("invalid-limit", "Issue limit must be between 1 and 10000", 2)
        argv = ["issue", "list", "--state", state, "--limit", str(limit), "--json", FIELDS]
        query = args.get("query", args.arg())
        if query:
            argv += ["--search", str(query)]
        for label in args.all("labels"):
            argv += ["--label", label]
        items = json.loads(provider(argv, origin).stdout)
        for item in items:
            repository.require_url(item["url"], "issues")
        return {"issues": items, "count": len(items), "possibly_truncated": len(items) >= limit, "origin": origin}
    if action == "get":
        return issue_get(args.need(), origin)
    if action in ("close", "reopen"):
        if not enabled(args, "confirm"):
            raise Failure("issue-mutation-not-authorized", action+" requires explicit --confirm")
        before = issue_get(args.need(), origin)
        expected = "CLOSED" if action == "close" else "OPEN"
        if before["state"].upper() != expected:
            provider(["issue", action, before["url"]], origin)
        after = issue_get(before["url"], origin)
        if after["state"].upper() != expected:
            raise Failure("issue-readback-mismatch", "Issue state mutation was not confirmed", url=before["url"])
        return {"changed": before["state"] != after["state"], "issue": after}
    if action == "link":
        family = "phase" if args.has("phase") else "todo"
        target = Args([])
        target.pos = [str(args.get("phase")), str(args.get("artifact")), str(args.get("finding"))] if family == "phase" else [args.need()]
        source, metadata, content, finding = source_record(target, family)
        snapshot = digest([source])
        issue = issue_get(args.get("url") or args.need(1), origin)
        link_record(target, family, issue["url"], snapshot)
        return {"linked": True, "source": str(source), "issue": issue}
    raise Failure("unsupported-issue-action", action, 2)
