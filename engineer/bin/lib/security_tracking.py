"""Canonical risk review and preview-bound checklist/standalone publication.

Shape checks are not a semantic security audit. Authors supply assessment and
canonical-match review evidence; independent issue-link review remains required.
"""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile
from . import delivery, issues, models, records, repository
from .core import Failure, digest, load_json, now, planning_lock, read, root, run, safe_path, write_json

LABEL = "phase-security-checklist"
FIELDS = ("Entry identity", "Canonical risk key", "Aliases / occurrences", "PLAN / Threat ID", "Owner", "Scope / acceptance",
          "Assessment / uncertainty", "Lifecycle / outcome", "Next action", "Revision / check evidence", "Canonical reference")
RISK_HEADINGS = ("Security concern", "Affected surface and behavior", "Impact", "Risk assessment and lifecycle", "Safe evidence",
                 "Requested remediation", "Scope and acceptance", "Related links")
REGISTER = ("Threat ID", "Category", "Component", "Severity", "Disposition", "Mitigation Plan")


def plan_registers(directory):
    registers = []
    for path in sorted(directory.glob("*-PLAN.md")):
        content = read(path)
        for block in re.findall(r"<threat_model\b[^>]*>(.*?)</threat_model>", content, re.S):
            rows = [tuple(cell.strip() for cell in line.strip().strip("|").split("|")) for line in block.splitlines() if line.strip().startswith("|")]
            if not rows or rows[0] != REGISTER:
                raise Failure("security-register-shape", "Keep the canonical six-column register in each PLAN", plan=str(path), columns=REGISTER)
            for row in rows[1:]:
                if all(re.fullmatch(r"[-: ]+", cell or "-") for cell in row):
                    continue
                if len(row) != 6:
                    raise Failure("security-register-shape", "Threat row must have six columns", plan=str(path))
                registers.append({"plan": str(path), "row": row, "threat_id": re.search(r"\bT-[A-Za-z0-9.-]+", row[0])[0] if re.search(r"\bT-[A-Za-z0-9.-]+", row[0]) else row[0]})
    return registers


def query(args):
    result = run(["gh", *args], root()) if args[0] == "api" else delivery.gh(args)
    return json.loads(result.stdout)


def issue_search(search, label=None):
    argv = ["issue", "list", "--state", "all", "--limit", "100", "--search", search,
            "--json", "url,title,body,state,labels"]
    if label:
        argv += ["--label", label]
    items = query(argv)
    if not isinstance(items, list) or len(items) >= 100:
        raise Failure("security-lookup-incomplete", "Issue lookup reached its bound")
    for item in items:
        repository.require_url(item["url"], "issues")
    return items


def load_entries(args):
    path = safe_path(args.get("entries-file"))
    entries = load_json(path)
    if not isinstance(entries, list) or not entries:
        raise Failure("security-entries-required", "entries-file must contain a nonempty JSON risk array")
    required = ("key", "heading", "plan", "threat_id", "owner", "scope_acceptance", "assessment_uncertainty",
                "lifecycle_outcome", "next_action", "revision_check_evidence", "aliases_occurrences", "match_review")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or any(not entry.get(key) for key in required):
            raise Failure("security-entry-incomplete", "Every risk needs identity, PLAN, assessment, lifecycle and match-review evidence", required=required)
        entry.setdefault("id", entry["heading"])
        if any(not isinstance(entry[field], str) or "\n" in entry[field] for field in ("key", "id", "heading", "plan", "threat_id")) or entry["key"] in seen or not isinstance(entry.get("planned"), bool):
            raise Failure("security-entry-identity", "Risk keys must be unique; planned must be boolean; headings must be single lines")
        seen.add(entry["key"])
        review = entry["match_review"]
        if not isinstance(review, dict) or review.get("disposition") not in ("existing", "no-match", "pending") or not review.get("evidence"):
            raise Failure("security-match-review-required", "Each risk needs an explicit reviewed disposition and cited evidence")
        if not entry["planned"] and review["disposition"] == "no-match":
            body = str(entry.get("standalone_body", ""))
            headings = re.findall(r"(?m)^## (.+)$", body)
            if headings != list(RISK_HEADINGS):
                raise Failure("security-risk-body-shape", "Standalone security risk headings must follow canonical order", headings=RISK_HEADINGS)
            if entry["key"] not in body or entry["owner"] not in body or entry["threat_id"] not in body:
                raise Failure("security-risk-body-shape", "Standalone body must carry risk key, owner and source alias")
            sections = re.split(r"(?m)^## [^\n]+\n", body)[1:]
            if any(not section.strip() for section in sections):
                raise Failure("security-risk-body-shape", "Security risk sections must contain supplied evidence or Pending dependencies")
    return path, entries


def scope_for(args, kind):
    if kind == "quick":
        from .verification import quick_dir
        directory = quick_dir(args.need())
        identifier = directory.name.split("-")[0]
    else:
        identifier = records.number(args.need())
        directory = records.phase_dir(identifier)
    return {"kind": kind, "id": identifier, "directory": str(directory), "key": kind+":"+identifier}


def review(args, kind="phase"):
    scope = scope_for(args, kind)
    source, entries = load_entries(args)
    identity = repository.identity()
    if any(identity["slug"].casefold() not in entry["key"].casefold() for entry in entries):
        raise Failure("security-risk-key-origin", "Canonical risk keys must include the pinned repository identity", repository=identity["slug"])
    directory = Path(scope["directory"])
    registers = plan_registers(directory)
    for entry in entries:
        plan = safe_path(directory/entry["plan"])
        if plan.parent != directory or not plan.is_file() or entry["threat_id"] not in read(plan):
            raise Failure("security-plan-reference", "Entry must cite an actual PLAN and threat occurrence", key=entry["key"])
        if entry["planned"] and not any(Path(row["plan"]) == plan and row["threat_id"] == entry["threat_id"] for row in registers):
            raise Failure("security-plan-reference", "Planned threat must occur in its own six-column PLAN register", key=entry["key"])
    title = "chore(security): "+kind+" "+scope["id"]+" security checklist"
    label = "quick-security-checklist" if kind == "quick" else LABEL
    pending, risks = [], []
    try:
        checklists = [item for item in issue_search('"'+title+'"', label) if item["title"] == title]
        if len(checklists) > 1:
            pending.append("Multiple canonical checklist containers; reconcile before publication")
    except Failure as exc:
        checklists = []
        pending.append("Checklist lookup unavailable: "+exc.message)
    for entry in entries:
        key = entry["key"]
        failures = []
        try:
            candidates = [item for item in issue_search('"'+key+'"') if item.get("title") != title]
            prs = query(["pr", "list", "--state", "all", "--limit", "100", "--search", '"'+key+'"', "--json", "url,title,body,state"])
            if not isinstance(prs, list) or len(prs) >= 100:
                raise Failure("security-pr-lookup-incomplete", "PR lookup reached its bound")
            # Linked issues may omit the key. They still belong in the reviewed
            # evidence set; inspect them before accepting a no-match declaration.
            linked = set(re.findall(r"https://[^\s)>]+/issues/\d+", "\n".join(item.get("body", "") for item in prs)))
            for url in linked:
                repository.require_url(url, "issues")
                if not any(item["url"] == url for item in candidates):
                    candidates.append(query(["issue", "view", url, "--json", "url,title,body,state"]))
            match = entry["match_review"]
            reviewed_issues = set(match.get("reviewed_issue_urls", []))
            reviewed_prs = set(match.get("reviewed_pr_urls", []))
            if not {item["url"] for item in candidates}.issubset(reviewed_issues) or not {item["url"] for item in prs}.issubset(reviewed_prs):
                failures.append("Canonical issue/current+linked PR candidates lack explicit review evidence")
            if match["disposition"] == "pending":
                failures.append("Semantic match review is Pending")
            if match["disposition"] == "existing":
                url = str(match.get("url", ""))
                repository.require_url(url, "issues")
                chosen = query(["issue", "view", url, "--json", "url,title,body,state"])
                if chosen.get("url") != url:
                    failures.append("Canonical selected issue readback differs")
                if str(chosen.get("state", "")).upper() == "CLOSED" and entry["lifecycle_outcome"].lower() not in ("mitigated", "resolved"):
                    failures.append("Unresolved closed match requires separate reopening authority")
            else:
                chosen = None
                actionable = [item for item in candidates if key in item.get("body", "")]
                if actionable:
                    failures.append("Existing full-key issue identity takes precedence over a new entry")
        except Failure as exc:
            candidates, prs, chosen = [], [], None
            failures.append("Canonical match lookup unavailable: "+exc.message)
        pending.extend(key+": "+failure for failure in failures)
        risks.append({"key": key, "entry": entry, "candidates": candidates, "prs": prs, "canonical": chosen, "pending": failures})
    return {kind: scope["id"], "scope": scope, "title": title, "label": label, "checklists": checklists, "risks": risks,
            "pending": pending, "ready": not pending, "source": str(source),
            "semantic_security_audit": "required independently; structural and provider checks do not prove semantic safety"}


def audit_plan_links(directory):
    """Verify exact declared targets without pretending to assess risk semantics."""
    failures = []
    for entry in plan_registers(directory):
        first = entry["row"][0]
        match = re.search(r"\[[^\]]+\]\((https://[^)]+)\)", first)
        if not match or "Pending:" in first:
            failures.append({"plan": entry["plan"], "id": entry["threat_id"], "reason": "Canonical threat reference is Pending"})
            continue
        url = match[1]
        base_url, _, fragment = url.partition("#")
        try:
            number = repository.require_url(base_url, "issues")
            identity = repository.identity()
            issue = query(["api", "repos/"+identity["owner"]+"/"+identity["repository"]+"/issues/"+str(number),
                           "--hostname", identity["hostname"], "--header", "Accept: application/vnd.github.full+json"])
            if issue.get("html_url") != base_url:
                raise Failure("security-readback-mismatch", "Risk URL readback differs")
            if fragment:
                parsed = RenderedHeadings()
                parsed.feed(issue.get("body_html", ""))
                headings = [heading for heading, anchors in parsed.results.items() if fragment in anchors]
                sections = [section for heading in headings for section in re.findall(r"(?ms)^### "+re.escape(heading)+r"\n(.*?)(?=^### |\Z)", issue.get("body", ""))]
                if len(sections) != 1 or entry["threat_id"] not in sections[0] or Path(entry["plan"]).name not in sections[0]:
                    raise Failure("security-anchor-mismatch", "Heading URL must target exactly this PLAN/threat entry")
                if any(not re.search(r"(?m)^"+re.escape(field)+r":\s*\S", sections[0]) for field in FIELDS):
                    raise Failure("security-entry-incomplete", "Canonical entry fields are incomplete")
            elif re.findall(r"(?m)^## (.+)$", issue.get("body", "")) != list(RISK_HEADINGS) or entry["threat_id"] not in issue.get("body", ""):
                raise Failure("security-risk-body-shape", "Standalone risk must carry assessment, mitigation, checks and the source alias")
        except Failure as exc:
            failures.append({"plan": entry["plan"], "id": entry["threat_id"], "reason": exc.message})
    return failures


def entry_body(entry, canonical):
    values = (entry["heading"], entry["key"], entry["aliases_occurrences"], entry["plan"]+" / "+entry["threat_id"], entry["owner"],
              entry["scope_acceptance"], entry["assessment_uncertainty"], entry["lifecycle_outcome"], entry["next_action"],
              entry["revision_check_evidence"], canonical or "This canonical planned checklist entry; PLAN owns assessment and mitigation")
    return "### "+entry["heading"]+"\n\n"+"\n".join(field+": "+str(value) for field, value in zip(FIELDS, values))+"\n"


class RenderedHeadings(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current, self.text, self.anchors, self.results, self.counts = False, [], [], {}, {}

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "h3":
            self.current, self.text, self.anchors = True, [], []
        if self.current:
            if values.get("id"):
                self.anchors.append(values["id"])
            if values.get("href", "").startswith("#"):
                self.anchors.append(values["href"][1:])

    def handle_data(self, data):
        if self.current:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "h3" and self.current:
            heading = "".join(self.text).strip()
            self.results[heading] = self.anchors[:]
            self.counts[heading] = self.counts.get(heading, 0)+1
            self.current = False


def render_readback(url, expected_body, entries, expected_title=None, expected_label=None):
    number = repository.require_url(url, "issues")
    identity = repository.identity()
    issue = query(["api", "repos/"+identity["owner"]+"/"+identity["repository"]+"/issues/"+str(number),
                   "--hostname", identity["hostname"], "--header", "Accept: application/vnd.github.full+json"])
    if issue.get("html_url") != url or issue.get("body", "").strip() != expected_body.strip():
        raise Failure("security-readback-mismatch", "Published risk content differs from its preview", url=url)
    if expected_title is not None and issue.get("title") != expected_title:
        raise Failure("security-readback-mismatch", "Published risk title differs from its preview", url=url)
    if issue.get("number") != number or str(issue.get("state", "")).upper() not in ("OPEN", "CLOSED"):
        raise Failure("security-readback-mismatch", "Provider identity/state is unavailable", url=url)
    labels = {label.get("name") if isinstance(label, dict) else label for label in issue.get("labels", [])}
    if expected_label and (expected_label not in labels or str(issue.get("state", "")).upper() != "OPEN"):
        raise Failure("security-readback-mismatch", "Canonical checklist label/open lifecycle differs from preview", url=url)
    parsed = RenderedHeadings()
    parsed.feed(issue.get("body_html", ""))
    links = []
    for entry in entries:
        anchors = parsed.results.get(entry["heading"], [])
        if not anchors or parsed.counts.get(entry["heading"]) != 1:
            raise Failure("security-anchor-pending", "Provider rendered no verifiable heading anchor; preserve Pending reference", url=url, key=entry["key"])
        supplied = entry.get("heading_url")
        targets = [url+"#"+anchor for anchor in anchors]
        if supplied and supplied not in targets:
            raise Failure("security-anchor-mismatch", "Supplied heading URL does not target the actual provider-rendered entry", url=supplied)
        links.append({"key": entry["key"], "id": entry["id"], "heading": entry["heading"], "url": supplied or targets[0], "plan": entry["plan"], "threat_id": entry["threat_id"]})
    return links


def command(args, action, kind="phase"):
    if action == "audit":
        scope = scope_for(args, kind)
        failures = audit_plan_links(Path(scope["directory"]))
        return {"ready": not failures, "pending": failures, "semantic_security_audit": "independent review required"}, int(bool(failures))
    packet = review(args, kind)
    if action == "review":
        return packet
    if args.get("variant") != "Security risk":
        raise Failure("issue-variant-required", "Security checklist and standalone previews/publication require --variant 'Security risk'")
    if not packet["ready"]:
        raise Failure("security-tracking-pending", "Canonical review remains Pending; no provider writes authorized", pending=packet["pending"])
    container = packet["checklists"][0] if packet["checklists"] else None
    if container and str(container.get("state", "")).upper() == "CLOSED" and any(item["entry"]["planned"] for item in packet["risks"]):
        raise Failure("security-checklist-closed", "Closed checklist requires independent reopen authority; never create a duplicate")
    body = container.get("body", "") if container else (
        "## Security concern\n\nTrack this "+kind+"'s planned security risks using canonical issue identities.\n\n"
        "## Affected surface and behavior\n\nSee each linked PLAN register and entry scope.\n\n"
        "## Impact\n\nSee each PLAN assessment; this container does not assign blanket severity.\n\n"
        "## Risk assessment and lifecycle\n\nPLAN registers own assessments and mitigations; entries retain lifecycle evidence.\n\n"
        "## Safe evidence\n\nSee entry revision/check evidence and linked public-safe PLAN evidence.\n\n"
        "## Requested remediation\n\nFollow each entry's next action within its approved PLAN scope.\n\n"
        "## Scope and acceptance\n\nSee each entry's owner and scope/acceptance. Acceptance never authorizes closure.\n\n"
        "## Related links\n\nEach entry links its PLAN and any existing full-scope canonical issue.\n")
    planned, standalone = [], []
    for risk in packet["risks"]:
        entry = risk["entry"]
        canonical = risk["canonical"]["url"] if risk["canonical"] else None
        if not entry["planned"]:
            if not canonical:
                standalone.append({"entry": entry, "body": entry["standalone_body"], "title": "Security risk: "+entry["heading"]})
            continue
        planned.append(entry)
        lifecycle = re.search(r"(?ms)^## Risk assessment and lifecycle\s*\n(.*?)(?=^## |\Z)", body)
        if not lifecycle:
            raise Failure("security-container-shape", "Canonical checklist requires the Security risk lifecycle section")
        section = lifecycle[1]
        prior = list(re.finditer(r"(?ms)^### ([^\n]+)\n(.*?)(?=^### |\Z)", section))
        matches = [match for match in prior if re.search(r"(?m)^Canonical risk key:\s*"+re.escape(entry["key"])+r"\s*$", match[2])]
        if len(matches) > 1:
            raise Failure("security-entry-duplicate", entry["key"])
        block = entry_body(entry, canonical)
        if matches:
            match = matches[0]
            if match[1] != entry["heading"]:
                raise Failure("security-heading-rename", "Preserve canonical heading until all references are repaired and read back")
            section = section[:match.start()]+block+"\n"+section[match.end():]
        else:
            if any(match[1] == entry["heading"] for match in prior):
                raise Failure("security-heading-collision", entry["heading"])
            section = section.rstrip()+"\n\n"+block+"\n"
        body = body[:lifecycle.start(1)]+section+body[lifecycle.end(1):]
    sources = [safe_path(packet["source"])]
    sources.extend(Path(packet["scope"]["directory"]).glob("*-PLAN.md"))
    if kind == "quick":
        sources.append(Path(packet["scope"]["directory"])/"QUICK.md")
    template = models.NAMESPACE/"engineer/templates/issue.md"
    if not template.is_file():
        raise Failure("issue-template-missing", "Install the canonical issue template before security publication")
    if planned:
        issues.validate(packet["title"], body, "Security risk")
    for item in standalone:
        issues.validate(item["title"], item["body"], "Security risk")
    sources.append(template)
    snapshot = {"origin": repository.identity(), "source_digest": digest(sources), "scope": packet["scope"],
                "title": packet["title"], "body": body, "container": container, "standalone": standalone, "planned": planned, "variant": "Security risk"}
    token = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
    path = records.planning()/"issue-previews"/(token+".json")
    if action == "preview":
        with planning_lock():
            if not path.exists():
                write_json(path, {**snapshot, "used": False, "created": now()})
        return {**packet, "previewToken": token, "body": body, "standalone": standalone}
    saved = load_json(path)
    if args.get("preview-token") != token or not saved or saved.get("used"):
        raise Failure("security-preview-stale", "Preview is absent, consumed or source/provider content drifted")
    with planning_lock():
        current = load_json(path)
        if current.get("used") or digest(sources) != snapshot["source_digest"]:
            raise Failure("security-preview-stale", "Preview changed before publication")
        saved.update({"used": "publishing", "attempted": now(), "published": []})
        write_json(path, saved)
    publications = []
    jobs = ([{"title": packet["title"], "body": body, "url": container["url"] if container else None, "planned": planned}] if planned else [])
    jobs.extend({**item, "url": None, "planned": []} for item in standalone)
    for job in jobs:
        if repository.identity() != snapshot["origin"] or digest(sources) != snapshot["source_digest"]:
            raise Failure("security-publication-drift", "Origin or source changed; preserve consumed attempt for reconciliation")
        with tempfile.TemporaryDirectory(prefix="engineer-security-") as directory:
            body_file = Path(directory)/"body.md"
            body_file.write_text(job["body"], encoding="utf-8")
            argv = ["issue", "edit", job["url"]] if job["url"] else ["issue", "create"]
            argv += ["--title", job["title"], "--body-file", str(body_file)]
            if job["planned"] and not job["url"]:
                argv += ["--label", packet["label"]]
            try:
                response = delivery.gh(argv)
                url = job["url"] or (response.stdout.strip().splitlines() or [""])[-1]
            except (Failure, OSError) as exc:
                found = [item for item in issue_search('"'+job["title"]+'"', packet["label"] if job["planned"] else None)
                         if item["title"] == job["title"] and item["body"].strip() == job["body"].strip()]
                if len(found) != 1:
                    raise Failure("security-publication-uncertain", "Inspect consumed attempt and provider readback before any retry") from exc
                url = found[0]["url"]
        links = render_readback(url, job["body"], job["planned"], job["title"], packet["label"] if job["planned"] else None)
        if repository.identity() != snapshot["origin"] or digest(sources) != snapshot["source_digest"]:
            raise Failure("security-publication-drift", "Published issue requires reconciliation after source/origin drift", url=url)
        publications.append({"url": url, "entries": links, "key": job.get("entry", {}).get("key")})
        saved["published"] = publications
        write_json(path, saved)
    saved["used"] = True
    write_json(path, saved)
    return {"published": publications, "previewToken": token, "independent_issue_link_audit_required": True,
            "note": "Update each PLAN reference from actual returned heading URLs; keep Pending until independently read back"}
