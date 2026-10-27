"""Specification shape coverage and evidence for already-selected prohibitions.

Prohibition recall remains a model prose pass. Projection does not infer intent,
and a resolution tier is never a substitute for observed machine evidence.
"""
import json
import math
import os
import re
import subprocess
import xml.etree.ElementTree as ET

from .core import Failure, read, root, safe_path


SHAPE_CUES = {
    "numeric-range": r"\b(?:numbers?|numeric|integers?|floats?|decimals?|round(?:ing|ed)?|amounts?|prices?|money|precision|overflow|thresholds?|minimum|maximum|min|max|limits?|ranges?|percent(?:age)?s?)\b",
    "collection": r"\b(?:lists?|arrays?|collections?|items?|elements?|sets?|intervals?|merge|merging|overlap(?:ping)?|dedup(?:e|licate|lication)?|duplicates?|sort(?:ing|ed)?)\b",
    "text": r"\b(?:strings?|text|characters?|unicode|graphemes?|encod(?:ing|ed)|bytes?|truncate|truncation|normaliz(?:e|ed|ation))\b",
    "stateful": r"\b(?:state(?:ful)?|persist(?:ent|ence|s|ed)?|sav(?:e|es|ed|ing)|updat(?:e|es|ed|ing)|delet(?:e|es|ed|ing)|creat(?:e|es|ed|ing)|counters?|sessions?|transactions?|reminders?|retries|retry|idempotent)\b",
    "io": r"\b(?:i/o|io|files?|read(?:s|ing)?|writ(?:e|es|ing)|network|requests?|responses?|http|api|fetch(?:es|ing)?|send(?:s|ing)?|receiv(?:e|es|ing)|upload(?:s|ing)?|download(?:s|ing)?|streams?|sockets?)\b",
}

# Ordering is part of the stable projection contract (and the reference oracles).
PROBES = {
    "boundary": ({"numeric-range"}, "What happens exactly at each min/max/threshold — and one step either side?"),
    "adjacency": ({"collection"}, "When two things are exactly equal or just touch, do they merge, collide, or separate?"),
    "empty": ({"collection", "text"}, "What is the result for empty, single-element, or null input?"),
    "encoding": ({"text"}, "Whose definition of length/equality applies — bytes, code points, grapheme clusters, or normalized form?"),
    "ordering": ({"collection"}, "When elements compare equal, is output order specified and stable?"),
    "precision": ({"numeric-range"}, "Where can precision loss, overflow, or rounding/tie-breaking occur — and what is the exact contract (e.g. half-up vs half-to-even, ceil/floor/truncate)?"),
    "idempotency": ({"stateful"}, "What happens if this runs twice on the same input?"),
    "concurrency": ({"stateful", "io"}, "If interrupted or run in parallel, what is guaranteed?"),
}
UNCLASSIFIED_PROBE = "Unclassified — review manually"
CHECK_KEYS = ("check_kind", "check_target", "check_rule", "check_violation_fixture", "check_clean_fixture")


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _json_file(value):
    try:
        return json.loads(read(safe_path(value)))
    except (ValueError, TypeError, OSError) as exc:
        raise Failure("invalid-probe-input", str(exc), 2) from exc


def _lifecycle(item, tiers, require_resolution=False):
    status = item.get("status", "unresolved")
    if status not in ("resolved", "dismissed", "unresolved"):
        raise Failure("invalid-resolution", "Unknown resolution status", 2)
    for key in ("resolution", "reason"):
        if item.get(key) is not None and not isinstance(item[key], str):
            raise Failure("invalid-resolution", f"{key} must be a string or null", 2)
    if status == "resolved" and (item.get("verification") not in tiers or
                                  (require_resolution and not _nonempty(item.get("resolution")))):
        raise Failure("invalid-resolution", "Resolved probes require a valid tier and edge resolution", 2)
    if status == "dismissed" and not _nonempty(item.get("reason")):
        raise Failure("invalid-resolution", "Dismissed probes require a nonempty reason", 2)
    return {"status": status, "verification": item.get("verification") if status == "resolved" else None,
            "resolution": item.get("resolution"), "reason": item.get("reason")}


def _coverage(items, tiers):
    closed = sum(item["status"] in ("resolved", "dismissed") for item in items)
    return {"applicable": len(items), "resolved": closed, "unresolved": len(items) - closed,
            "byVerification": {tier: sum(item["status"] == "resolved" and item["verification"] == tier
                                          for item in items) for tier in tiers}}


def edge(args):
    requirements = _json_file(args.arg(0, args.get("requirements")))
    resolutions = _json_file(args.get("resolutions")) if args.has("resolutions") else []
    if not isinstance(requirements, list) or not isinstance(resolutions, list):
        raise Failure("invalid-probe-input", "Requirements and resolutions must be arrays", 2)
    indexed = {}
    for item in resolutions:
        if (not isinstance(item, dict) or not _nonempty(item.get("requirement_id")) or
                item.get("category") not in (*PROBES, "unclassified")):
            raise Failure("invalid-resolution", "Resolution requires requirement_id and recognized category", 2)
        key = (item["requirement_id"], item["category"])
        if key in indexed:
            raise Failure("invalid-resolution", "Duplicate resolution", 2)
        indexed[key] = _lifecycle(item, ("explicit", "backstop"), require_resolution=True)
    items, ids = [], set()
    for requirement in requirements:
        if (not isinstance(requirement, dict) or not _nonempty(requirement.get("id")) or
                not isinstance(requirement.get("text"), str)):
            raise Failure("invalid-requirement", "Each requirement requires nonempty string id and string text", 2)
        identity = requirement["id"]
        if identity in ids:
            raise Failure("invalid-requirement", "Duplicate requirement id", 2)
        ids.add(identity)
        prose = requirement.get("text_en")
        if prose is not None and not isinstance(prose, str):
            raise Failure("invalid-requirement", "text_en must be a string or null", 2)
        prose = requirement["text"] if prose is None else prose
        if "shapes" in requirement:
            shapes = requirement["shapes"]
            if (not isinstance(shapes, list) or
                    any(not isinstance(shape, str) or shape not in SHAPE_CUES for shape in shapes)):
                raise Failure("invalid-shapes", "shapes must be an array of recognized shapes", 2)
            shapes = set(shapes)
        else:
            shapes = {shape for shape, pattern in SHAPE_CUES.items() if re.search(pattern, prose, re.I)}
        categories = [category for category, (applies, _) in PROBES.items() if applies & shapes]
        if not shapes and "shapes" not in requirement and prose.strip():
            categories = ["unclassified"]
        for category in categories:
            item = {"requirement_id": identity, "category": category,
                    "status": "unresolved", "verification": None, "resolution": None, "reason": None,
                    "probe": UNCLASSIFIED_PROBE if category == "unclassified" else PROBES[category][1]}
            item.update(indexed.get((identity, category), {}))
            items.append(item)
    raised = {(item["requirement_id"], item["category"]) for item in items}
    if indexed.keys() - raised:
        raise Failure("invalid-resolution", "Resolution names an edge that was not raised", 2)
    coverage = _coverage(items, ("explicit", "backstop"))
    coverage["unclassified"] = sum(item["category"] == "unclassified" for item in items)
    return {"items": items, "coverage": coverage}


def prohibition_project(args):
    """Project selected rows only; never perform deterministic moral recall."""
    selected = _json_file(args.need())
    if isinstance(selected, dict) and set(selected) <= {"items", "coverage"}:
        selected = selected.get("items")
    if not isinstance(selected, list):
        raise Failure("invalid-probe-input", "Selected prohibitions must be an array", 2)
    items = []
    for row in selected:
        if (not isinstance(row, dict) or
                any(not _nonempty(row.get(key)) for key in ("requirement_id", "category", "statement"))):
            raise Failure("invalid-prohibition", "Prohibitions require requirement_id, category and statement", 2)
        if "check" in row or any(key in row and not isinstance(row[key], str) for key in CHECK_KEYS):
            raise Failure("invalid-prohibition", "Check descriptors must use flat string scalars", 2)
        item = {key: row[key] for key in ("requirement_id", "category")}
        item.update(_lifecycle(row, ("test", "judgment")))
        item["statement"] = row["statement"]
        kind = row.get("check_kind")
        wired = (kind in ("test-command", "lint-rule") and _nonempty(row.get("check_target")) and
                 (kind != "lint-rule" or _nonempty(row.get("check_rule"))))
        if item["status"] == "resolved" and item["verification"] == "test" and wired:
            for key in CHECK_KEYS:
                if _nonempty(row.get(key)) and (key != "check_rule" or kind == "lint-rule"):
                    item[key] = row[key]
        items.append(item)
    return {"items": items, "coverage": _coverage(items, ("test", "judgment"))}


def _test_evidence(report, report_format):
    """Read actual executed assertions, distinguishing failures from infrastructure errors."""
    if report_format == "unittest":
        summaries = re.findall(r"(?m)^Ran (\d+) tests? in [0-9.]+s\s*$", report)
        finals = re.findall(r"(?m)^(OK|FAILED)(?: \(([^\n]*)\))?\s*$", report)
        if len(summaries) != 1 or len(finals) != 1:
            raise ValueError("Missing or ambiguous unittest summary")
        tests = int(summaries[0])
        outcome, details = finals[0]
        count_pairs = [(name.strip(), int(count)) for name, count in re.findall(r"([a-zA-Z ]+)=(\d+)", details)]
        counts = dict(count_pairs)
        if len(counts) != len(count_pairs):
            raise ValueError("Duplicate unittest counters")
        if details and not re.fullmatch(r"[a-zA-Z ]+=\d+(?:, [a-zA-Z ]+=\d+)*", details):
            raise ValueError("Malformed unittest counts")
        if set(counts) - {"failures", "errors", "skipped", "expected failures", "unexpected successes"}:
            raise ValueError("Unrecognized unittest counters")
        failures, errors = counts.get("failures", 0), counts.get("errors", 0)
        skipped = counts.get("skipped", 0) + counts.get("expected failures", 0)
        if tests <= 0 or skipped > tests or failures + errors + skipped > tests:
            raise ValueError("No non-vacuous executed tests or inconsistent counts")
        if errors or counts.get("unexpected successes", 0):
            raise ValueError("Test error or unexpected success is not prohibition evidence")
        if (outcome == "FAILED") != bool(failures):
            raise ValueError("Inconsistent unittest disposition")
        if failures and (not re.search(r"(?m)^FAIL: ", report) or "AssertionError" not in report):
            raise ValueError("RED was not a genuine assertion failure")
        return {"tests": tests, "asserted": tests - skipped, "failures": failures, "errors": errors,
                "skipped": skipped}
    if report_format == "junit":
        tree = ET.fromstring(report)
        if tree.tag not in ("testsuite", "testsuites"):
            raise ValueError("Unrecognized JUnit root")
        cases = list(tree.iter("testcase"))
        if not cases:
            raise ValueError("JUnit report contains no test cases")
        suites = list(tree.iter("testsuite"))
        if not suites or sum(len(suite.findall("testcase")) for suite in suites) != len(cases):
            raise ValueError("Malformed JUnit suite/case structure")
        for case in cases:
            outcomes = [child for child in case if child.tag in ("failure", "error", "skipped")]
            if len(outcomes) > 1:
                raise ValueError("Ambiguous JUnit case outcome")
            failure = case.find("failure")
            if failure is not None and failure.get("type") and not re.search(
                    r"assert|compar|fail", failure.get("type"), re.I):
                raise ValueError("JUnit RED was not a recognized assertion failure")
        failures = sum(case.find("failure") is not None for case in cases)
        errors = sum(case.find("error") is not None for case in cases)
        skipped = sum(case.find("skipped") is not None for case in cases)
        if errors or any(not case.get("name") for case in cases):
            raise ValueError("JUnit report has infrastructure errors or unnamed cases")
        # Count from actual cases, never trust a caller-supplied summary alone.
        for suite in suites + ([tree] if tree.tag == "testsuites" else []):
            descendants = list(suite.iter("testcase"))
            for name, count in (("tests", len(descendants)),
                                ("failures", sum(c.find("failure") is not None for c in descendants)),
                                ("errors", sum(c.find("error") is not None for c in descendants)),
                                ("skipped", sum(c.find("skipped") is not None for c in descendants))):
                if suite.get(name) is not None and int(suite.get(name)) != count:
                    raise ValueError("Inconsistent JUnit counters")
        return {"tests": len(cases), "asserted": len(cases) - skipped, "failures": failures,
                "errors": errors, "skipped": skipped}
    raise ValueError("Unsupported test report format")


def _lint_evidence(report, subject, rule):
    entries = json.loads(report)
    if not isinstance(entries, list) or not entries:
        raise ValueError("Lint report must contain processed files")
    processed, selected, errors = [], [], 0
    for entry in entries:
        if not isinstance(entry, dict) or not _nonempty(entry.get("filePath")):
            raise ValueError("Malformed lint file entry")
        try:
            processed.append(str(safe_path(entry["filePath"])))
        except Failure as exc:
            raise ValueError("Lint report names a file outside the project") from exc
        messages = entry.get("messages")
        if not isinstance(messages, list) or entry.get("fatalErrorCount", 0):
            raise ValueError("Lint report has a fatal error or malformed messages")
        for message in messages:
            if (not isinstance(message, dict) or message.get("fatal") or
                    message.get("severity") not in (1, 2) or not _nonempty(message.get("ruleId"))):
                raise ValueError("Lint message is malformed or an infrastructure error")
            errors += message["severity"] == 2
            if message["ruleId"] == rule and processed[-1] == str(subject):
                selected.append(message)
        actual_errors = sum(message["severity"] == 2 for message in messages)
        actual_warnings = sum(message["severity"] == 1 for message in messages)
        if entry.get("errorCount") != actual_errors or entry.get("warningCount") != actual_warnings:
            raise ValueError("Inconsistent lint counters")
    if processed != [str(subject)]:
        raise ValueError("Lint report did not process exactly the actual injected subject")
    rule_errors = sum(message["severity"] == 2 for message in selected)
    return {"processed_files": processed, "rule_id": rule, "rule_hits": len(selected),
            "errors": errors, "other_rule_errors": errors - rule_errors}


def prohibition_proof(args):
    """Execute a configured argv on bad, clean and real subjects, without a shell.

    Descriptor argv must name its existing target (or use {target}); lint argv
    must also use {subject}. reportFormat is unittest, junit, or eslint-json.
    File reports must be rewritten by every invocation; stale reports never prove
    a check. argv/reportFile may contain {subject}, {target}, {stage}; argv may
    contain {report} when reportFile is configured. Both subject environment
    variable spellings are provided for project checks.
    """
    descriptor = _json_file(args.need())
    observations = []
    located = False

    def fail(reason):
        raise Failure("unprovable-prohibition", reason, 2, located=located, proved=False,
                      valid=False, disposition="flagged", observations=observations, reason=reason)

    def proof_path(value):
        try:
            return safe_path(value)
        except Failure as exc:
            fail(exc.message)

    if not isinstance(descriptor, dict):
        fail("Descriptor must be an object")
    aliases = {"kind": "check_kind", "target": "check_target", "rule": "check_rule",
               "violationFixture": "check_violation_fixture", "cleanFixture": "check_clean_fixture"}
    descriptor = dict(descriptor)
    for name, alias in aliases.items():
        if name in descriptor and alias in descriptor and descriptor[name] != descriptor[alias]:
            fail(f"Conflicting descriptor fields: {name} and {alias}")
        if name not in descriptor and alias in descriptor:
            descriptor[name] = descriptor[alias]
    kind, rule = descriptor.get("kind"), descriptor.get("rule")
    if kind not in ("test-command", "lint-rule") or not _nonempty(descriptor.get("target")):
        fail("Missing recognized kind and existing configured check target")
    try:
        target = proof_path(descriptor["target"])
        subject = proof_path(args.get("subject"))
        if not target.is_file() or not subject.is_file():
            fail("Check target and real subject must exist as files")
        located = True
        controls = [proof_path(descriptor.get(key)) for key in ("violationFixture", "cleanFixture")]
        if any(not path.is_file() for path in controls):
            fail("Known-bad and known-clean control files are mandatory")
        if len({*controls, subject}) != 3 or controls[0].read_bytes() == controls[1].read_bytes():
            fail("Bad, clean and real paths must be distinct; control contents must differ")
        timeout = float(args.get("timeout", "30"))
        if not math.isfinite(timeout) or timeout <= 0:
            fail("Timeout must be a finite positive number")
    except (ValueError, TypeError, OSError) as exc:
        fail(f"Invalid proof input: {exc}")
    argv = descriptor.get("argv")
    if not isinstance(argv, list) or not argv or any(not _nonempty(token) or "\x00" in token for token in argv):
        fail("Configured project argv must be a nonempty array of strings")
    if argv[0].lower().endswith((".bat", ".cmd")):
        fail("Batch launchers require shell evaluation; configure the underlying executable argv")
    if not any("{target}" in token or token == descriptor["target"] or token == str(target) for token in argv):
        fail("Configured argv must name the check target")
    if kind == "lint-rule" and (not _nonempty(rule) or not any("{subject}" in token for token in argv)):
        fail("Lint proof requires rule and actual subject argv injection")
    report_format = descriptor.get("reportFormat", "eslint-json" if kind == "lint-rule" else "unittest")
    if report_format not in (("eslint-json",) if kind == "lint-rule" else ("unittest", "junit")):
        fail("Unrecognized report format for check kind")
    report_file = descriptor.get("reportFile")
    if report_file is not None and not _nonempty(report_file):
        fail("reportFile must be a nonempty path")
    if report_format == "junit" and not report_file:
        fail("JUnit proof requires a reportFile rewritten by the configured check")
    for stage, injected in zip(("violation", "clean", "subject"), (*controls, subject)):
        replacements = {"{target}": str(target), "{subject}": str(injected), "{stage}": stage}

        def expand(token):
            for marker, value in replacements.items():
                token = token.replace(marker, value)
            return token

        report_path, before = None, None
        if report_file:
            report_path = proof_path(expand(report_file))
            if report_path in {target, subject, *controls}:
                fail("Report path cannot overwrite a check or subject")
            try:
                if report_path.exists():
                    stat = report_path.stat()
                    before = (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size, report_path.read_bytes())
            except OSError as exc:
                fail(f"{stage}: report path is unavailable: {exc}")
            replacements["{report}"] = str(report_path)
        command = [expand(token) for token in argv]
        if any(re.search(r"\{(?:target|subject|stage|report)\}", token) for token in command):
            fail("Unexpanded report placeholder")
        env = {**os.environ, "ENGINEER_PROHIB_SUBJECT": str(injected), "GSD_PROHIB_SUBJECT": str(injected)}
        observation = {"stage": stage, "argv": command, "subject": str(injected),
                       "exit_code": None, "timed_out": False}
        observations.append(observation)
        try:
            result = subprocess.run(command, cwd=root(), env=env, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=timeout, shell=False)
            observation["exit_code"] = result.returncode
        except subprocess.TimeoutExpired:
            observation["timed_out"] = True
            fail(f"{stage}: configured check timed out")
        except OSError as exc:
            fail(f"{stage}: check could not execute: {exc}")
        try:
            if report_path:
                stat = report_path.stat()
                after = (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size, report_path.read_bytes())
                if after == before:
                    fail(f"{stage}: stale report")
                report = after[3].decode("utf-8-sig")
            else:
                report = result.stdout if kind == "lint-rule" else result.stdout + "\n" + result.stderr
            evidence = (_lint_evidence(report, injected, rule) if kind == "lint-rule" else
                        _test_evidence(report, report_format))
            observation.update(evidence)
        except (ValueError, TypeError, OSError, ET.ParseError) as exc:
            fail(f"{stage}: malformed or unavailable report: {exc}")
        if kind == "test-command":
            if evidence["asserted"] <= 0:
                fail(f"{stage}: no non-vacuous executed tests")
            red = result.returncode == 1 and evidence["failures"] > 0
            green = result.returncode == 0 and evidence["failures"] == 0
        else:
            red = result.returncode == 1 and evidence["rule_hits"] > 0 and evidence["other_rule_errors"] == 0
            green = result.returncode == 0 and evidence["rule_hits"] == 0 and evidence["errors"] == 0
        if not (red if stage == "violation" else green):
            fail(f"{stage}: expected {'genuine assertion/rule RED' if stage == 'violation' else 'non-vacuous GREEN'}")
    return {"located": True, "proved": True, "valid": True, "disposition": "green", "kind": kind,
            "target": str(target), "rule": rule if kind == "lint-rule" else None, "subject": str(subject),
            "observations": observations, "reason": "Known violation RED, clean control GREEN, real subject GREEN"}


def section(args):
    path, kind = safe_path(args.need()), args.need(1)
    if kind not in ("edges", "prohibitions"):
        raise Failure("unknown-spec-section", kind, 2)
    content = read(path)
    heading = r"edge(?: cases?)?|boundar" if kind == "edges" else r"prohibition|must.not|non.goals|forbidden"
    match = re.search(r"(?mi)^(#{1,6})\s+[^\n]*(?:"+heading+r")[^\n]*$", content)
    if not match:
        return {"supplied": False, "items": []}
    end = re.search(r"(?m)^#{1,"+str(len(match[1]))+r"}\s", content[match.end():])
    body = content[match.end():match.end()+end.start() if end else len(content)]
    items = [m.group(1).strip() for m in re.finditer(r"(?m)^\s*(?:[-*]|\d+[.)])\s+(.+)$", body)]
    return {"supplied": True, "items": items}
