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


VARIANTS = ("Bug", "Enhancement", "Decision required", "Security risk", "UAT")


def variant_template(template, variant):
    if variant not in VARIANTS:
        raise Failure("issue-variant-required", "Select an exact canonical issue variant", variants=VARIANTS)
    return file_template(template, variant)


def file_template(template, variant=None):
    catalog, selected, fence, body = False, False, None, []
    for line in read(template).splitlines(keepends=True):
        stripped = line.strip()
        if fence:
            if stripped == fence:
                if selected:
                    return "".join(body)
                fence = None
            elif selected:
                body.append(line)
            continue
        opening = re.fullmatch(r"(`{3,}|~{3,})[^\s]*", stripped)
        if opening:
            fence = opening[1]
            continue
        if stripped.startswith("## "):
            catalog = stripped == "## File Template"
            selected = catalog and variant is None
        elif catalog and variant is not None and stripped.startswith("### "):
            selected = stripped == "### "+variant
    raise Failure("issue-template-variant-missing", "Canonical variant has no fenced File Template body", variant=variant)


def validate(title, body, variant):
    if not title.strip() or not body.strip():
        raise Failure("invalid-issue", "Issue title and body must be nonempty")
    template = models.NAMESPACE/"engineer/templates/issue.md"
    from . import issue_format
    issue_format.validate(body, variant, template)
    if variant == "UAT":
        normalized = "\n".join(line.strip() for line in issue_format.visible_lines(body)).replace("**", "")
        normalized = re.sub(r"(?m)^- (?=(?:Status|Reviewer|Date|Decision|Evidence):)", "", normalized)
        if re.search(r"(?mi)^Status:\s*ACCEPTED\s*$", normalized):
            from .phase_issues import accepted_human
            if not accepted_human(normalized):
                raise Failure("invalid-uat-issue", "Accepted UAT requires actual reviewer/date/decision/evidence")
    return template


def validate_command(args):
    body = read(safe_path(args.get("body-file"))) if args.has("body-file") else str(args.get("body", ""))
    template = validate(str(args.get("title", "Issue structural review")), body, args.get("variant"))
    return {"valid": True, "variant": args.get("variant"), "template": str(template),
            "limitations": "Shape only; semantic safety, links and human acceptance require independent evidence"}


def semantic_key(title, body):
    body = re.sub(r"<!-- engineer-issue:[a-f0-9]{64} -->", "", body)
    problem = re.search(r"(?ms)^## (?:Problem|Summary)\s*\n(.*?)(?=^## |\Z)", body)
    return re.sub(r"\s+", " ", title.strip().casefold())+"\n"+re.sub(r"\s+", " ", (problem[1] if problem else body).strip().casefold())


def candidates(title, body, provenance):
    """Search open AND closed records; ambiguity blocks all publication writes."""
    matches = {}
    for query in (provenance, title):
        result = json.loads(delivery.gh(["issue", "list", "--state", "all", "--limit", "100", "--search", query,
                                        "--json", "url,title,body,state,number"]).stdout)
        if not isinstance(result, list) or len(result) >= 100:
            raise Failure("issue-search-incomplete", "Narrow issue identity before publication; search reached its bound")
        for issue in result:
            if provenance in issue.get("body", "") or semantic_key(title, body) == semantic_key(issue.get("title", ""), issue.get("body", "")):
                repository.require_url(str(issue.get("url", "")), "issues")
                issue["identity_match"] = "provenance" if provenance in issue.get("body", "") else "semantic"
                matches[issue["url"]] = issue
    return list(matches.values())


def publication(args, action, family="todo"):
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
        identifier = args.need(2)
        entries = metadata.get("issue_refs", [])
        matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("id") == identifier]
        if len(matches) != 1:
            raise Failure("finding-not-found", identifier)
        finding = matches[0]
    title = str(args.get("title", (finding or {}).get("summary", metadata.get("title", source.stem))))
    body = read(safe_path(args.get("body-file"))) if args.has("body-file") else str(args.get("body", content))
    if not args.has("title") or not str(args.get("title", "")).strip() or not args.has("body-file"):
        raise Failure("reviewed-public-content-required", "Supply an explicit reviewed public title and separate body file")
    if safe_path(args.get("body-file")) == source:
        raise Failure("private-source-body-refused", "Prepare the reviewed public issue body separately from its source")
    variant = args.get("variant")
    template = validate(title, body, variant)
    origin = repository.identity()
    identity = family+":"+str(source.relative_to(root())).replace("\\", "/")+":"+str(args.arg(2, ""))
    provenance = "engineer-issue:"+hashlib.sha256((origin["slug"]+":"+identity).encode()).hexdigest()
    marker = "<!-- "+provenance+" -->"
    if marker not in body:
        body = body.rstrip()+"\n\n"+marker+"\n"
    matches = candidates(title, body, provenance)
    selection = args.get("existing-issue")
    linked = (finding or metadata).get("issue_url", (finding or metadata).get("url", metadata.get("issue")))
    if action == "update" and linked:
        if selection and str(selection) not in (str(linked), str(linked).rsplit("/", 1)[-1]):
            raise Failure("issue-identity-conflict", "Update selection differs from the linked canonical issue")
        selection = linked
    if selection and args.has("no-match"):
        raise Failure("issue-disposition-conflict", "Select --existing-issue or --no-match, never both")
    if selection:
        if str(selection).isdigit():
            selection = "https://"+origin["slug"]+"/issues/"+str(selection)
        repository.require_url(str(selection), "issues")
        chosen = json.loads(delivery.gh(["issue", "view", str(selection), "--json", "url,title,body,state,number"]).stdout)
        if chosen.get("url") != selection:
            raise Failure("issue-readback-mismatch", "Selected canonical issue readback differs")
        chosen["identity_match"] = "reviewed-existing"
        matches = [chosen]
    if len(matches) > 1:
        raise Failure("issue-identity-ambiguous", "Multiple issues match this finding; reconcile before publication", candidates=matches)
    disposition = "create" if not matches else "reuse-"+str(matches[0].get("state", "unknown")).lower()+"-"+matches[0]["identity_match"]
    for candidate in matches:
        validate(str(candidate.get("title", "")), str(candidate.get("body", "")), variant)
        if candidate.get("number") != repository.require_url(str(candidate.get("url", "")), "issues") or str(candidate.get("state", "")).upper() not in ("OPEN", "CLOSED"):
            raise Failure("issue-candidate-invalid", "Canonical candidate identity or state is unavailable")
    candidate_snapshot = [{key: candidate.get(key) for key in ("url", "number", "title", "body", "state", "identity_match")} for candidate in matches]
    snapshot = {"source": str(source), "source_digest": digest([source, template]), "title": title, "body": body,
                "labels": args.all("labels"), "family": family, "finding": args.arg(2), "origin": origin,
                "provenance": provenance, "existing_issue": selection, "no_match": args.has("no-match"), "variant": variant,
                "candidates": candidate_snapshot}
    supplied = args.get("preview-token")
    prior_supplied = load_json(records.planning()/"issue-previews"/(str(supplied)+".json")) if re.fullmatch(r"[a-f0-9]{64}", str(supplied)) else None
    if prior_supplied and prior_supplied.get("used") and len(matches) == 1 and matches[0]["identity_match"] == "provenance":
        # Recovery may discover the issue produced by the consumed create. It
        # may not reinterpret reviewed source/title/body/labels/origin/variant.
        snapshot["candidates"] = prior_supplied.get("candidates", [])
    token = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
    preview = records.planning()/"issue-previews"/(token+".json")
    prior_attempt = load_json(preview)
    if args.has("no-match") and matches and not (prior_attempt and prior_attempt.get("used") and len(matches) == 1 and matches[0]["identity_match"] == "provenance"):
        raise Failure("issue-match-exists", "The no-match declaration conflicts with canonical issue search", candidates=matches)
    if action == "preview":
        with planning_lock():
            prior = load_json(preview)
            if not prior:
                write_json(preview, {**snapshot, "created": now(), "used": False})
        return {"previewToken": token, "preview_token": token, "title": title, "body": body,
                "source": str(source), "snapshotDigest": snapshot["source_digest"], "disposition": disposition,
                "candidates": matches, "prior_attempt": prior.get("used") if prior else False}
    saved = load_json(records.planning()/"issue-previews"/(str(supplied)+".json")) if re.fullmatch(r"[a-f0-9]{64}", str(supplied)) else None
    if supplied != token or not saved or saved.get("source_digest") != snapshot["source_digest"]:
        raise Failure("stale-issue-preview", "Preview token is absent, consumed, or no longer matches the issue")
    recovering = bool(saved.get("used"))
    if recovering and (len(matches) != 1 or matches[0]["identity_match"] != "provenance"):
        raise Failure("issue-publication-uncertain", "Inspect the consumed attempt; no unique provenance readback is available")
    existing = (finding or metadata).get("issue_url", (finding or metadata).get("url", metadata.get("issue")))
    if action == "publish" and not selection and not args.has("no-match") and not recovering:
        raise Failure("issue-disposition-required", "Review canonical matches and preview with --existing-issue URL|NUMBER or --no-match before publication")
    if action == "publish" and existing:
        raise Failure("issue-already-linked", str(existing))
    if action == "update" and not existing:
        raise Failure("issue-not-linked", str(source))
    if existing:
        repository.require_url(str(existing), "issues")
    reused = matches[0] if action == "publish" and matches else None
    if existing and matches and matches[0]["url"] != existing:
        raise Failure("issue-identity-conflict", "Linked issue and identity search disagree")
    # A provider timeout can mean the issue was created. Consume before calling
    # the provider so an uncertain outcome cannot create a duplicate on retry.
    with planning_lock():
        current = load_json(preview)
        if repository.identity() != origin or digest([source, template]) != snapshot["source_digest"]:
            raise Failure("issue-preview-drift", "Origin or source changed before publication")
        if current.get("used") and not recovering:
            raise Failure("issue-preview-consumed", "Inspect the prior publication attempt before retrying")
        current.update({"used": "publishing", "attempted": now()})
        write_json(preview, current)
    with tempfile.TemporaryDirectory(prefix="engineer-issue-") as directory:
        path = Path(directory)/"body.md"
        path.write_text(body, encoding="utf-8")
        command = ["issue", "create", "--title", title, "--body-file", str(path)] if action == "publish" else ["issue", "edit", str(existing), "--title", title, "--body-file", str(path)]
        for label in args.all("labels"):
            command += ["--label" if action == "publish" else "--add-label", label]
        if not reused:
            if recovering:
                raise Failure("issue-publication-uncertain", "A consumed attempt can only recover a read-back issue")
            try:
                result = delivery.gh(command)
            except (Failure, OSError) as exc:
                recovered = candidates(title, body, provenance)
                if len(recovered) != 1 or recovered[0]["identity_match"] != "provenance":
                    raise Failure("issue-publication-uncertain", "Provider outcome is uncertain; consumed preview prevents duplicate creation") from exc
                reused = recovered[0]
    url = reused["url"] if reused else existing if action == "update" else (result.stdout.strip().splitlines() or [""])[-1]
    if not re.match(r"https://[^/]+/[^/]+/[^/]+/issues/\d+$", str(url)):
        recovered = candidates(title, body, provenance)
        if len(recovered) != 1 or recovered[0]["identity_match"] != "provenance":
            raise Failure("issue-publication-uncertain", "Provider returned no issue URL and no unique provenance readback; inspect before retrying")
        reused = recovered[0]
        url = reused["url"]
    repository.require_url(str(url), "issues")
    issue = json.loads(delivery.gh(["issue", "view", str(url), "--json", "url,title,body,state,labels,number"]).stdout)
    if (not reused or recovering or reused.get("identity_match") == "provenance") and (issue.get("title") != title or issue.get("body", "").strip() != body.strip()):
        raise Failure("issue-readback-mismatch", "Published issue differs from the validated preview", url=url)
    if issue.get("url") != url:
        raise Failure("issue-readback-mismatch", "Readback URL does not match selected issue", url=url)
    actual_labels = {label.get("name") if isinstance(label, dict) else label for label in issue.get("labels", [])}
    if (not reused or recovering or reused.get("identity_match") == "provenance") and not set(args.all("labels")).issubset(actual_labels):
        raise Failure("issue-readback-mismatch", "Requested labels are absent from provider readback", url=url)
    if str(issue.get("state", "")).upper() not in ("OPEN", "CLOSED"):
        raise Failure("issue-readback-mismatch", "Provider state is unavailable", url=url)
    if issue.get("number") != repository.require_url(str(url), "issues"):
        raise Failure("issue-readback-mismatch", "Provider number does not match canonical URL", url=url)
    with planning_lock():
        if repository.identity() != origin or digest([source, template]) != snapshot["source_digest"]:
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
    return {"published": True, "url": url, "issue": issue, "source": str(source), "reused": bool(reused),
            "disposition": disposition, "requires_reconciliation": bool(reused and str(issue.get("state", "")).upper() == "CLOSED")}
