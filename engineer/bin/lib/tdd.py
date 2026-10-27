"""Conservative RED evidence classification for supported report formats."""
import json
import re
import xml.etree.ElementTree as ET
from . import config, plans
from .core import Failure, read, root, run, safe_path
from .text import split_frontmatter


def applicable(args):
    path = safe_path(args.arg(0, args.get("plan", "")))
    if not path.is_file():
        raise Failure("unreadable-plan", str(path))
    metadata, body = split_frontmatter(read(path))
    selected = metadata.get("type") == "tdd" or any(task["tdd"] for task in plans.tasks(body))
    enabled = config.lookup(config.load(), "workflow.tdd_mode", False)
    return {"applicable": bool(selected and enabled), "plan_tdd": selected, "enabled": bool(enabled)}


def behavior(args):
    value = args.arg(0, args.get("task", "{}"))
    try:
        task = json.loads(value)
    except ValueError:
        task = {"action": value, "files": args.all("files")}
    files = task.get("files", [])
    if isinstance(files, str):
        files = re.split(r"[,\s]+", files)
    runtime = [p for p in files if p and not re.search(r"(?:^|/)(?:tests?|docs?|fixtures?)/|(?:^|[._-])test[._-]|\.(?:md|txt|json|ya?ml|toml|ini|cfg)$", p, re.I)]
    verbs = bool(re.search(r"\b(?:add|implement|handle|support|change|fix)\b", task.get("action", ""), re.I))
    return {"is_behavior_adding": bool(runtime or verbs), "reason": "runtime files" if runtime else "behavior action" if verbs else "documentation, tests or configuration only"}


def red(args):
    try:
        path = safe_path(args.need())
        record = json.loads(read(path))
    except (Failure, ValueError, OSError):
        return {"verdict": "INVALID_RED:unreadable_record", "evidence": {"report_errors": ["Unreadable evidence record"]}}, 69
    def invalid(reason, errors=None):
        return {"verdict": "INVALID_RED:"+reason, "evidence": {"report_errors": errors or []}}, 1
    required = ("command", "exitCode", "output", "targetTest", "targetFile", "expected", "actual")
    if not isinstance(record, dict) or any(k not in record for k in required) or not isinstance(record.get("output"), str) or not isinstance(record.get("exitCode"), int):
        return invalid("invalid_record")
    if record["exitCode"] == 0:
        return invalid("unexpected_green")
    output, target = record["output"], str(record["targetTest"])
    if re.search(r"build failed|setup failed|error: could not compile|BUILD FAILURE", output, re.I):
        return invalid("build_failure")
    if re.search(r"ImportError|ModuleNotFoundError|SyntaxError|_FailedTest|collection error|beforeAll|beforeEach|setUpClass|setUp \(", output):
        return invalid("fixture_or_load_failure")
    failures, total, errors = [], None, []
    if output.lstrip().startswith("<"):
        try:
            document = ET.fromstring(output)
        except ET.ParseError as exc:
            return invalid("invalid_record", [str(exc)])
        cases = list(document.iter("testcase"))
        total = len(cases)
        for case in cases:
            if case.find("error") is not None:
                return invalid("fixture_or_load_failure")
            if case.find("failure") is not None:
                name, cls = case.get("name", ""), case.get("classname", "")
                failures.append([name, cls, cls+"#"+name, cls.rsplit(".", 1)[-1]])
        if not all(record.get(k) for k in ("reportPath", "runStartedAt", "reportModifiedAt")):
            return invalid("invalid_record", ["JUnit requires report path and run timestamps"])
        if str(record["reportModifiedAt"]) < str(record["runStartedAt"]):
            return invalid("invalid_record", ["Stale JUnit report"])
    elif re.match(r"(?:TAP version \d+\s*\n)?(?:#|ok|not ok|1\.\.)", output):
        plan = re.findall(r"(?m)^1\.\.(\d+)\s*$", output)
        if len(plan) != 1:
            return invalid("invalid_record", ["Expected a complete TAP plan"])
        total = int(plan[0])
        results = re.findall(r"(?m)^(not ok|ok)\s+\d+\s*(?:-\s*)?(.+)$", output)
        if len(results) != total:
            return invalid("invalid_record", ["TAP plan/result mismatch"])
        failures = [[name.strip()] for status, name in results if status == "not ok" and not re.search(r"#\s*(?:SKIP|TODO)\b", name, re.I)]
    elif re.search(r"Ran \d+ tests? in", output):
        total = int(re.search(r"Ran (\d+) tests? in", output)[1])
        summary = re.search(r"FAILED \(([^)]+)\)", output)
        headers = re.findall(r"(?m)^(FAIL|ERROR): (\S+)(?: \(([^)]+)\))?", output)
        if any(kind == "ERROR" for kind, _, _ in headers):
            return invalid("fixture_or_load_failure")
        expected = sum(int(x) for x in re.findall(r"(?:failures|errors)=(\d+)", summary[1])) if summary else 0
        if not summary or len(headers) != expected:
            return invalid("invalid_record", ["unittest counters do not match failure headers"])
        failures = [[method, cls+"."+method if cls and not cls.endswith(method) else cls] for _, method, cls in headers]
    elif "--- FAIL:" in output or re.search(r"(?m)^FAIL\s+\S+", output):
        packages = re.findall(r"(?m)^FAIL\s+(\S+)(?:\s+[\d.]+s)?\s*$", output)
        failed_names = re.findall(r"(?m)^\s*--- FAIL: (\S+) \(", output)
        if not packages:
            return invalid("invalid_record", ["Missing go package summary"])
        total = max(len(failed_names), 1)
        failures = [[name, packages[0]+"."+name] for name in failed_names]
    elif re.search(r"Test run with \d+ tests?", output):
        total = int(re.search(r"Test run with (\d+) tests?", output)[1])
        results = re.findall(r'(?:Test "([^"]+)"|Test (\S+\(\))) (passed|failed|skipped|cancelled)', output)
        if len(results) != total:
            return invalid("invalid_record", ["swift-testing counter mismatch"])
        failures = [[display or name] for display, name, status in results if status == "failed"]
    else:
        return invalid("invalid_record", ["Unsupported report format"])
    if total == 0:
        return invalid("zero_tests_discovered")
    if not failures:
        return invalid("nonzero_exit_without_test_failure")
    matching = [item for item in failures if target in item]
    if len(matching) != 1:
        return invalid("no_target_test_failure", ["Target is missing or ambiguous"])
    if record.get("testCommit") or record.get("implementationCommit"):
        if not record.get("testCommit") or not record.get("implementationCommit"):
            return invalid("invalid_record", ["Both test and implementation commits are required"])
        ancestor = run(["git", "merge-base", "--is-ancestor", record["testCommit"], record["implementationCommit"]], root(), check=False)
        if ancestor.returncode or record["testCommit"] == record["implementationCommit"]:
            return invalid("invalid_record", ["RED test commit must precede implementation"])
        changed = run(["git", "show", "--format=", "--name-only", record["testCommit"]], root()).stdout.splitlines()
        if record["targetFile"] not in changed:
            return invalid("invalid_record", ["Target test is absent from RED commit"])
    return {"verdict": "RED_EVIDENCE_OK", "evidence": {"target": target, "tests": total, "report_errors": []}}, 0
