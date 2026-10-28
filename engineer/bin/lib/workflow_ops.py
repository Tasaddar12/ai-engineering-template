"""Deterministic workflow dispatch ledgers and cited evidence reports."""
import ast
import fnmatch
import hashlib
import json
from pathlib import Path
import re
import sys
from . import config, models, records
from .core import Args, Failure, digest, load_json, now, planning_lock, read, root, run, safe_path, slug, write_json
from .text import split_frontmatter


def _payload(args):
    if args.has("stdin"):
        return json.loads(sys.stdin.read())
    if args.has("input"):
        return load_json(safe_path(args.get("input")))
    return args.json("payload", {})


def review_flags(args):
    supplied = args.all("_body")
    parsed = args
    if supplied:
        parsed = Args([])
        index = 0
        while index < len(supplied):
            token = supplied[index]
            if token.startswith("--"):
                key, separator, value = token[2:].partition("=")
                if key in ("fix", "all", "auto", "claude", "codex", "text"):
                    parsed.opts[key] = [value] if separator else []
                elif key in ("depth", "files", "phase", "since", "max-commits"):
                    if not separator:
                        index += 1
                        if index >= len(supplied) or supplied[index].startswith("--"):
                            raise Failure("review-flag-value", "Missing value for --"+key, 2)
                        value = supplied[index]
                    parsed.opts.setdefault(key, []).append(value)
                else:
                    raise Failure("unknown-review-flag", key, 2)
            else:
                parsed.pos.append(token)
            index += 1
    true = lambda key: parsed.has(key) and str(parsed.get(key)).lower() in ("true", "1", "yes")
    explicit = [name for name in ("claude", "codex") if true(name)]
    allowed_flags = {"fix", "all", "auto", "claude", "codex", "text", "depth", "files", "phase", "since", "max-commits", "raw", "json", "pick", "_body"}
    errors = ["Unsupported review flag: --"+name for name in sorted(set(parsed.opts)-allowed_flags)]
    return {"ok": not errors, "phase": parsed.arg(0, ""), "fix": true("fix") or true("all") or true("auto"),
            "all": true("all"), "auto": true("auto"), "depth": str(parsed.get("depth", "")),
            "files": ",".join(parsed.all("files")), "explicit": ",".join(explicit), "errors": errors}


def review_depth(args):
    from .code_review_depth import resolve_code_review_depth
    payload = _payload(args)
    if not isinstance(payload, dict):
        raise Failure("invalid-depth-input", "Depth input must be a mapping", 2)
    files = payload.get("files", args.all("files"))
    if args.has("files-file"):
        files = read(safe_path(args.get("files-file"))).splitlines()
    if not isinstance(files, list) or any(not isinstance(path, str) for path in files):
        raise Failure("invalid-depth-files", "Depth files must be a string array", 2)
    files = [str(safe_path(path).relative_to(root())).replace("\\", "/") for path in files if path]
    settings = config.load()
    flag = str(payload.get("flagDepth", args.get("flag-depth", args.get("depth", ""))))
    configured = str(payload.get("configDepth", args.get("config-depth", config.lookup(settings, "workflow.code_review_depth", "standard"))))
    overrides = payload.get("overrides", args.json("overrides", config.lookup(settings, "workflow.code_review_depth_overrides", [])))
    return resolve_code_review_depth({"flagDepth": flag, "configDepth": configured,
                                      "overrides": overrides, "files": files,
                                      "repoRoot": str(root())})


def review_field(args):
    if args.has("report"):
        value, _ = split_frontmatter(read(safe_path(args.get("report"))))
    else:
        value = _payload(args)
    field = str(args.get("field", args.arg(0, "")))
    if not field:
        raise Failure("missing-review-field", "Supply --field with a dotted JSON/frontmatter path", 2)
    try:
        for part in field.split("."):
            value = value[int(part)] if isinstance(value, list) else value[part]
    except (KeyError, IndexError, ValueError, TypeError):
        if args.has("default"):
            return args.get("default")
        raise Failure("review-field-missing", field)
    if args.has("raw") and isinstance(value, list) and all(isinstance(item, (str, int, float, bool)) for item in value):
        return "\n".join(str(item).lower() if isinstance(item, bool) else str(item) for item in value)
    return value


def review_scope(args):
    from .scope import evaluation
    return evaluation(args)


def review_disposition(args):
    path = safe_path(args.get("report", args.arg(0, "")))
    if not path.is_file():
        raise Failure("review-report-missing", str(path))
    metadata, body = split_frontmatter(read(path))
    findings = metadata.get("findings", [])
    counts = findings if isinstance(findings, dict) else None
    if counts is not None:
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts.values()):
            raise Failure("invalid-review-findings", "Finding counts must be nonnegative integers")
        findings = []
    elif not isinstance(findings, list):
        raise Failure("invalid-review-findings", "Frontmatter findings must be an array or count mapping")
    # Preserve authored table cells; never infer resolved/open from prose tone.
    table_findings = []
    header = None
    for line in body.splitlines():
        if not line.lstrip().startswith("|"):
            header = None
            continue
        cells = [cell.strip().replace("**", "") for cell in line.strip().strip("|").split("|")]
        normalized = [cell.casefold().replace(" ", "_") for cell in cells]
        if "id" in normalized and "status" in normalized:
            header = normalized
        elif header and len(cells) == len(header) and not all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            row = dict(zip(header, cells))
            if row.get("id"):
                table_findings.append(row)
    rows = findings or table_findings
    identifiers = [row.get("id") for row in rows if isinstance(row, dict) and row.get("id") and row.get("type", "code") != "documentation"]
    return {"status": metadata.get("status", "unknown"), "depth": metadata.get("depth", "standard"),
            "files_reviewed_list": metadata.get("files_reviewed_list", []), "findings": rows,
            "code_issue_ids": identifiers, "has_status": "status" in metadata,
            "finding_counts": counts,
            "frontmatter": metadata, "source": str(path), "digest": digest([path]), "behaviorVerified": False}


def _tdd_checkpoint(args, directory, reports):
    from . import tdd
    obligations = []
    for plan in sorted(directory.glob("*-PLAN.md")):
        check_args = Args([str(plan)])
        if tdd.applicable(check_args)["applicable"]:
            obligations.append(plan.stem.removesuffix("-PLAN"))
    evidence, gaps = [], []
    for report in reports:
        entries = report["metadata"].get("tdd_evidence", [])
        if not isinstance(entries, list):
            gaps.append({"path": report["path"], "reason": "tdd_evidence must be a list"})
            continue
        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("plan") or not entry.get("red") or not entry.get("green"):
                gaps.append({"path": report["path"], "reason": "Each TDD entry needs plan, red and green report paths"})
                continue
            red, status = tdd.red(Args([str(entry["red"])]))
            green = load_json(safe_path(entry["green"]))
            if status or not isinstance(green, dict) or type(green.get("exitCode")) is not int or green.get("exitCode") != 0 or not green.get("command") or not isinstance(green.get("output"), str) or green.get("revision") != _head():
                gaps.append({"plan": entry["plan"], "reason": "Missing valid RED and current recorded GREEN evidence", "red": red})
            else:
                evidence.append(entry)
    covered = {entry["plan"] for entry in evidence}
    missing = [plan for plan in obligations if plan not in covered]
    return {"block": bool(missing or gaps), "missing_plans": missing, "gaps": gaps,
            "recorded_evidence": evidence, "behaviorVerified": False, "executesTests": False}


def _phase(args):
    value = args.get("phase-dir", args.arg(0, args.get("phase")))
    if value is not None:
        candidate = safe_path(value)
        if candidate.is_dir():
            return candidate
    return records.phase_dir(value)


def _head():
    return run(["git", "rev-parse", "HEAD"], root()).stdout.strip()


def _citations(items):
    if not isinstance(items, list) or not items:
        raise Failure("missing-evidence", "Supply actual source citations", 2)
    result = []
    for item in items:
        if isinstance(item, str):
            item = {"path": item}
        if not isinstance(item, dict) or not item.get("path"):
            raise Failure("invalid-evidence", "Evidence requires a repository path", 2)
        path = safe_path(item["path"])
        if not path.is_file():
            raise Failure("missing-evidence", str(path), 2)
        lines = read(path).splitlines()
        start, end = int(item.get("line", 1)), int(item.get("end_line", item.get("line", len(lines))))
        if not 1 <= start <= end <= len(lines):
            raise Failure("invalid-evidence-range", str(path), 2)
        result.append({**item, "path": str(path), "line": start, "end_line": end, "digest": digest([path])})
    return result


def predicate(args):
    value = args.json("predicate")
    directory = _phase(args)
    def evaluate(item, depth=0):
        if depth > 12 or not isinstance(item, dict):
            raise Failure("invalid-predicate", "Predicate nesting or shape is invalid", 2)
        kind = item.get("kind", item.get("type"))
        if kind in ("all", "any"):
            children = item.get("items", item.get("predicates"))
            if not isinstance(children, list) or not children:
                raise Failure("invalid-predicate", "Boolean predicates need nonempty children", 2)
            results = [evaluate(child, depth+1) for child in children]
            return {"kind": kind, "satisfied": all(child["satisfied"] for child in results) if kind == "all" else any(child["satisfied"] for child in results), "children": results}
        if kind not in ("file-exists", "frontmatter-equals", "frontmatter-nonempty"):
            raise Failure("unsupported-predicate", "Only retained record predicates are executable", kind=kind)
        target = str(item.get("path", "")).replace("${PHASE_DIR}", str(directory)).replace("${PHASE_NUMBER}", str(args.get("phase-number", directory.name.split("-")[0])))
        if not target:
            raise Failure("invalid-predicate", "Record predicate requires a path", 2)
        path = safe_path(target, directory) if not Path(target).is_absolute() else safe_path(target)
        if not path.is_relative_to(directory):
            raise Failure("predicate-outside-phase", str(path), 2)
        exists = path.is_file()
        if kind == "file-exists":
            satisfied = exists
        else:
            metadata, _ = split_frontmatter(read(path))
            key = item.get("field")
            if not isinstance(key, str) or not key:
                raise Failure("invalid-predicate", "Frontmatter predicate requires field", 2)
            actual = metadata
            for part in key.split("."):
                actual = actual.get(part) if isinstance(actual, dict) else None
            satisfied = exists and (actual == item.get("value") if kind == "frontmatter-equals" else actual not in (None, "", [], {}))
        return {"kind": kind, "path": str(path), "satisfied": satisfied, "digest": digest([path])}
    result = evaluate(value)
    return {"block": not result["satisfied"], "predicate": result, "structuralOnly": True}


def auto_mode(args):
    value = config.lookup(config.load(), "workflow.auto_advance", False)
    return {"active": value is True, "implementationAuthorized": False}


def check(args):
    """Compatibility dispatcher for copied `check ${hook.check.query}` calls."""
    selector = args.need().replace(".", "-")
    tail = Args([])
    tail.pos, tail.opts = args.pos[1:], dict(args.opts)
    from . import decisions, plans, quality, scope, tdd, ui
    routes = {
        "auto-mode": auto_mode, "predicate": predicate, "ui-plan-gate": ui.plan_gate,
        "ui-safety-gate": ui.safety_gate, "evaluation-scope": scope.evaluation,
        "tdd-red-evidence": tdd.red, "tdd-review-checkpoint": lambda a: command(a, "tdd-review-checkpoint"),
        "security-status": lambda a: command(a, "security"), "validation-coverage": lambda a: command(a, "validation"),
        "decision-coverage-plan": lambda a: decisions.coverage(a, "plan"),
        "decision-coverage-verify": lambda a: decisions.coverage(a, "verify"),
        "verify-command-paths": lambda a: plans.check(a, "paths"),
        "verify-failure-directions": lambda a: plans.check(a, "failure-directions"),
        "windows-status": lambda a: quality.command(a, "status"),
    }
    if selector not in routes:
        raise Failure("unsupported-check", "Dynamic checks are restricted to retained record/evidence operations", query=selector)
    result = routes[selector](tail)
    packet = result[0] if isinstance(result, tuple) else result
    if isinstance(packet, dict) and "block" not in packet and "passed" in packet:
        packet["block"] = not packet["passed"]
    return result


def review_dispatch(args):
    if args.has("explicit"):
        if args.has("fix"):
            raise Failure("review-execution-read-only", "Independent CLI reviews cannot apply fixes; use a separate bounded repair assignment")
        from .review_execution import command as execute_review
        return execute_review(args, "run")
    base = args.get("base-sha", args.get("base"))
    if not base:
        raise Failure("review-base-required", "Independent review requires an explicit base revision", 2)
    base = run(["git", "rev-parse", str(base)+"^{commit}"], root()).stdout.strip()
    head = _head()
    depth = args.get("depth", "standard")
    if depth not in ("quick", "standard", "deep"):
        raise Failure("invalid-review-depth", str(depth), 2)
    paths = args.all("files") or run(["git", "diff", "--name-only", base, head, "--"], root()).stdout.splitlines()
    paths = [str(safe_path(path).relative_to(root())) for path in paths]
    role = "targeted-fixer" if args.has("fix") else "code-reviewer"
    assignment = {"role": role, "host": models.resolve_host(), "model": models.resolve(role, "model"),
                  "effort": models.resolve(role, "effort"), "root": str(root()), "base": base, "head": head,
                  "files": sorted(set(paths)), "depth": depth, "sourceMutation": role == "targeted-fixer",
                  "method": str(models.agents_dir()/(role+".md")),
                  "required_return": ["captured_revision", "base_revision", "examined_scope", "unreached_scope", "findings"],
                  "finding_fields": ["id", "severity", "required_property", "citations", "status"],
                  "instructions": "Use the complete role method. Review claims against actual source at the captured revision. A repair requires explicit owned paths and an isolated checkout supplied by the coordinator. Do not fabricate an independent pass or execute checks without authority."}
    key = hashlib.sha256(json.dumps(assignment, sort_keys=True).encode()).hexdigest()
    path = records.planning()/"reviews"/(key+".json")
    with planning_lock():
        previous = load_json(path)
        if previous and previous.get("assignment") != assignment:
            raise Failure("review-ledger-conflict", str(path))
        if not previous:
            write_json(path, {"id": key, "state": "awaiting-dispatch", "created": now(), "assignment": assignment})
    return {"dispatch_id": key, "ledger": str(path), "assignment": assignment, "dispatched": False,
            "requiresNativeDispatch": True, "reviewVerified": False}


def review_record(args):
    key = args.need()
    if not re.fullmatch(r"[a-f0-9]{64}", key):
        raise Failure("invalid-review-id", key, 2)
    path = records.planning()/"reviews"/(key+".json")
    packet = load_json(safe_path(args.get("input", args.get("report-file", ""))))
    with planning_lock():
        ledger = load_json(path)
        if not ledger:
            raise Failure("review-not-found", key)
        if not isinstance(packet, dict) or not isinstance(packet.get("findings"), list) or not isinstance(packet.get("examined_scope"), list) or not isinstance(packet.get("unreached_scope"), list):
            raise Failure("invalid-review-report", "Review requires findings and explicit examined/unreached scope", 2)
        assignment = ledger["assignment"]
        if packet.get("captured_revision") != assignment["head"] or packet.get("base_revision") != assignment["base"]:
            raise Failure("review-revision-drift", "Review must identify the exact captured base/head")
        if not packet.get("reviewer") or not packet.get("author") or packet.get("reviewer") == packet.get("author"):
            raise Failure("review-independence-missing", "Record distinct actual reviewer and author identities")
        known = set()
        for finding in packet["findings"]:
            if not isinstance(finding, dict) or not finding.get("id") or not finding.get("required_property") or finding.get("severity") not in ("critical", "warning", "high", "medium", "low", "info"):
                raise Failure("invalid-review-finding", "Findings need stable id, severity and required property", 2)
            if finding["id"] in known:
                raise Failure("duplicate-review-finding", finding["id"], 2)
            known.add(finding["id"])
            finding["citations"] = _citations(finding.get("citations"))
        if set(packet["examined_scope"]) | set(packet["unreached_scope"]) != set(assignment["files"]):
            raise Failure("review-scope-mismatch", "Report must account for every assigned file and no unrelated files")
        if set(packet["examined_scope"]) & set(packet["unreached_scope"]):
            raise Failure("review-scope-overlap", "A file cannot be both examined and unreached")
        ledger.update({"state": "reported", "recorded": now(), "report": packet, "current": _head() == assignment["head"]})
        write_json(path, ledger)
    return ledger


def review_lane(args, action):
    if action == "flags":
        return "--claude --codex"
    if action == "sections":
        return "claude\tIndependent Claude read-only review\ncodex\tIndependent Codex read-only review"
    if action == "explicit-from-argv":
        values = args.all("_body") or args.pos
        selected = []
        for value in values:
            if value in ("--claude", "--codex"):
                selected.append(value[2:])
            elif value.startswith(("--claude=", "--codex=")):
                name, active = value[2:].split("=", 1)
                if active not in ("true", "false"):
                    raise Failure("invalid-review-selection", "Reviewer flag values must be true or false", 2)
                if active == "true":
                    selected.append(name)
        return ",".join(dict.fromkeys(selected))
    if action != "dispatch-step":
        raise Failure("unknown-review-lane-action", action, 2)
    from .review_execution import command as execute_review
    return execute_review(args, "dispatch-step")


def _health(args):
    errors, warnings, info = [], [], []
    for name in ("PROJECT.md", "REQUIREMENTS.md", "ROADMAP.md", "STATE.md", "config.yaml"):
        if not (records.planning()/name).is_file():
            errors.append({"code": "missing-record", "path": str(records.planning()/name)})
    try:
        config.load()
    except Failure as exc:
        errors.append({"code": exc.code, "message": exc.message})
    for directory in sorted((records.planning()/"phases").glob("*")):
        if not directory.is_dir():
            continue
        if not re.fullmatch(r"\d+(?:\.\d+)?-[a-z0-9-]+", directory.name):
            warnings.append({"code": "phase-name", "path": str(directory)})
        for plan in directory.glob("*-PLAN.md"):
            summary = plan.with_name(plan.name.replace("-PLAN.md", "-SUMMARY.md"))
            if not summary.exists():
                info.append({"code": "plan-without-summary", "path": str(plan), "meaning": "May be unexecuted or in progress"})
        for summary in directory.glob("*-SUMMARY.md"):
            if not summary.with_name(summary.name.replace("-SUMMARY.md", "-PLAN.md")).exists():
                warnings.append({"code": "orphan-summary", "path": str(summary)})
    if args.has("repair") or args.has("backfill"):
        raise Failure("health-repair-requires-planning-review", "Health never rewrites identity or acceptance; use guarded planning repair", errors=errors, warnings=warnings)
    return {"status": "broken" if errors else "degraded" if warnings else "healthy", "errors": errors, "warnings": warnings, "info": info,
            "counts": {"errors": len(errors), "warnings": len(warnings), "info": len(info)}, "structuralOnly": True}


def _intel(args):
    files = args.all("files")
    if not files:
        files = run(["git", "ls-files", "--", "*.py"], root()).stdout.splitlines()
    query = str(args.get("query", "")).casefold()
    symbols, errors = [], []
    for value in files:
        path = safe_path(value)
        if path.suffix != ".py" or not path.is_file():
            continue
        try:
            tree = ast.parse(read(path))
        except SyntaxError as exc:
            errors.append({"path": str(path), "line": exc.lineno, "error": exc.msg})
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                symbol = {"path": str(path), "name": node.name, "line": node.lineno, "kind": type(node).__name__, "digest": digest([path])}
                if not query or query in json.dumps(symbol).casefold():
                    symbols.append(symbol)
    return {"symbols": symbols, "errors": errors, "scope": "Tracked Python declarations only; dynamic exports and other languages require specialist inspection", "behaviorVerified": False}


def _learnings(args, action):
    directory = records.planning()/"learnings"
    if action == "learnings-query":
        query = str(args.get("query", args.arg(0, ""))).casefold()
        items = [load_json(safe_path(path)) for path in sorted(directory.glob("*.json"))]
        return {"items": [item for item in items if query in json.dumps(item).casefold()]}
    packet = load_json(safe_path(args.get("input", "")))
    if not isinstance(packet, dict) or not isinstance(packet.get("items"), list):
        raise Failure("invalid-learnings", "Supply authored items; source interpretation belongs to the specialist", 2)
    for item in packet["items"]:
        if not isinstance(item, dict) or item.get("category") not in ("decisions", "lessons", "patterns", "surprises") or not item.get("text"):
            raise Failure("invalid-learning", "Each item needs an allowed category, actual text and citations", 2)
        item["citations"] = _citations(item.get("citations"))
    key = hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest()
    destination = safe_path(args.get("destination"))/ (key+".json") if action == "learnings-copy" and args.has("destination") else directory/(key+".json")
    with planning_lock():
        write_json(destination, {**packet, "id": key, "recorded": now()})
    return {"stored": True, "copied": action == "learnings-copy", "id": key, "path": str(destination), "globalCopy": False}


def command(args, action):
    if action == "security":
        from .security_tracking import command as security_command
        return security_command(args, "status")
    if action == "review-dispatch":
        return review_dispatch(args)
    if action == "review-record":
        return review_record(args)
    if action == "review-status":
        key = args.need()
        if not re.fullmatch(r"[a-f0-9]{64}", key):
            raise Failure("invalid-review-id", key, 2)
        packet = load_json(records.planning()/"reviews"/(key+".json"))
        if not packet:
            raise Failure("review-not-found", key)
        return {**packet, "current": packet["assignment"]["head"] == _head()}
    if action == "predicate":
        return predicate(args)
    if action == "context":
        used, window = int(args.get("tokens-used", -1)), int(args.get("context-window", 0))
        if used < 0 or window <= 0:
            raise Failure("invalid-context-measurement", "Supply actual nonnegative tokens-used and positive context-window", 2)
        percent = 100*used/window
        state = "critical" if percent >= 70 else "warning" if percent >= 60 else "healthy"
        return {"state": state, "utilization": percent, "tokensUsed": used, "contextWindow": window,
                "message": f"Context utilization: {percent:.1f}% ({state})"}
    if action == "health":
        return _health(args)
    if action in ("intel", "intel-query"):
        return _intel(args)
    if action.startswith("learnings-"):
        return _learnings(args, action)
    if action == "threadscan":
        path = safe_path(args.get("input", args.arg(0, "")))
        packet = load_json(path)
        messages = packet.get("messages") if isinstance(packet, dict) else packet
        if not isinstance(messages, list) or any(not isinstance(item, dict) or item.get("role") not in ("user", "assistant", "tool", "system") or not isinstance(item.get("content"), str) for item in messages):
            raise Failure("invalid-thread-export", "Supply an explicit exported message array with role/content", 2)
        query = str(args.get("query", "")).casefold()
        return {"source": str(path), "digest": digest([path]), "messages": [{"index": index, **item} for index, item in enumerate(messages) if not query or query in item["content"].casefold()], "claimsExtracted": False}
    if action in ("debug", "security", "validation", "tdd-review-checkpoint"):
        directory = _phase(args)
        suffix = {"debug": "DEBUG", "security": "SECURITY", "validation": "VALIDATION", "tdd-review-checkpoint": "SUMMARY"}[action]
        paths = sorted(directory.glob("*-"+suffix+".md"))
        reports = []
        for path in paths:
            metadata, body = split_frontmatter(read(path))
            reports.append({"path": str(path), "digest": digest([path]), "metadata": metadata, "body": body})
        # These are evidence inputs, never a semantic pass based on file presence.
        missing = not reports
        if action == "debug":
            return {"reports": reports, "missing": missing, "status": "missing" if missing else "recorded", "behaviorVerified": False}
        if action == "tdd-review-checkpoint":
            return _tdd_checkpoint(args, directory, reports)
        current = _head()
        claims, gaps = [], []
        for report in reports:
            metadata = report["metadata"]
            revision = metadata.get("source_revision", metadata.get("revision", metadata.get("commit")))
            if revision != current:
                gaps.append({"path": report["path"], "reason": "Report does not identify the current captured source revision"})
            try:
                citations = _citations(metadata.get("evidence"))
            except (Failure, TypeError, ValueError) as exc:
                citations = []
                gaps.append({"path": report["path"], "reason": "Report needs valid actual evidence citations", "detail": str(exc)})
            if action == "security":
                count = metadata.get("threats_open")
                if type(count) is not int or count != 0:
                    gaps.append({"path": report["path"], "reason": "threats_open must explicitly equal integer zero", "actual": count})
                if metadata.get("status") not in ("secured", "passed") or not metadata.get("reviewer"):
                    gaps.append({"path": report["path"], "reason": "Security auditor conclusion and identity are required"})
            else:
                if metadata.get("status") not in ("passed", "complete") or not metadata.get("reviewer") or not isinstance(metadata.get("coverage"), list) or not metadata.get("coverage"):
                    gaps.append({"path": report["path"], "reason": "Validation needs an actual reviewer conclusion and nonempty obligation coverage"})
                for row in metadata.get("coverage", []) if isinstance(metadata.get("coverage"), list) else []:
                    if not isinstance(row, dict) or not row.get("requirement") or not row.get("test") or row.get("status") != "passed":
                        gaps.append({"path": report["path"], "reason": "Coverage row lacks requirement, actual test and reported passed status"})
                    else:
                        try:
                            _citations(row.get("evidence"))
                        except (Failure, TypeError, ValueError) as exc:
                            gaps.append({"path": report["path"], "reason": "Coverage evidence is missing", "detail": str(exc)})
            claims.append({"path": report["path"], "reported_status": metadata.get("status"), "citations": citations})
        return {"reports": reports, "missing": missing, "block": missing or bool(gaps), "gaps": gaps,
                "status": "missing" if missing else "blocked" if gaps else "reported-evidence-current",
                "reported_claims": claims, "structuralOnly": True, "behaviorVerified": False}
    if action == "teams-status":
        host = models.resolve_host()
        runs = []
        for path in sorted((records.planning()/"worktrees").glob("*.json")):
            packet = load_json(safe_path(path))
            if not isinstance(packet, dict):
                raise Failure("invalid-worker-record", str(path))
            entries = packet.get("workers", [packet])
            if not isinstance(entries, list):
                raise Failure("invalid-worker-record", str(path))
            for entry in entries:
                if not isinstance(entry, dict):
                    raise Failure("invalid-worker-record", str(path))
                state = entry.get("status", entry.get("state"))
                if state in ("active", "running", "dispatched") or (state is None and entry.get("path") and not entry.get("merged") and not entry.get("cleaned")):
                    runs.append({**entry, "record": str(path), "recorded_state": state or "ownership-not-released"})
        result = {"host": host, "active": bool(runs), "runs": runs, "nativeLiveStatus": "unavailable", "evidence": "Coordinator-owned worker records; not proof of live process exit"}
        return (result, 0 if runs else 1) if args.has("active") else result
    raise Failure("unknown-workflow-operation", action, 2)
