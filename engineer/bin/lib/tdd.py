"""Conservative RED evidence classification for supported report formats."""
import json
import re
import subprocess
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
        # Nested TAP suite summaries are not assertion evidence. Preserve leaf
        # failures and accept either exact emitted name or qualified subtest path.
        names = []
        all_results = list(re.finditer(r"(?m)^(\s*)(not ok|ok)\s+\d+\s*(?:-\s*)?(.+)$", output))
        subtests = list(re.finditer(r"(?m)^(\s*)# Subtest:\s*(.+)$", output))
        for index, match in enumerate(all_results):
            end = all_results[index+1].start() if index+1 < len(all_results) else len(output)
            diagnostic = output[match.end():end]
            name = match[3].strip()
            if match[2] != "not ok" or re.search(r"#\s*(?:SKIP|TODO)\b", name, re.I):
                continue
            if re.search(r"subtestsFailed|type:\s*['\"]?suite", diagnostic):
                continue
            parents = {}
            for declaration in subtests:
                if declaration.start() >= match.start():
                    break
                indentation = len(declaration[1])
                if indentation < len(match[1]):
                    parents[indentation] = declaration[2].strip()
                    parents = {level: text for level, text in parents.items() if level <= indentation}
            qualified = " > ".join([parents[level] for level in sorted(parents)]+[name])
            names.append([name, qualified])
        failures = names
    elif re.search(r"Ran \d+ tests? in", output):
        total = int(re.search(r"Ran (\d+) tests? in", output)[1])
        summary = re.search(r"FAILED \(([^)]+)\)", output)
        headers = re.findall(r"(?m)^(FAIL|ERROR): (\S+)(?: \(([^)]+)\))?", output)
        if any(kind == "ERROR" for kind, _, _ in headers):
            return invalid("fixture_or_load_failure")
        expected = sum(int(x) for x in re.findall(r"(?:failures|errors)=(\d+)", summary[1])) if summary else 0
        if not summary or len(headers) != expected:
            return invalid("invalid_record", ["unittest counters do not match failure headers"])
        failures = [list(item) for item in dict.fromkeys((method, cls+"."+method if cls and not cls.endswith(method) else cls) for _, method, cls in headers)]
    elif "--- FAIL:" in output or re.search(r"(?m)^FAIL\s+\S+", output):
        packages = re.findall(r"(?m)^FAIL\s+(\S+)(?:\s+[\d.]+s)?\s*$", output)
        failed_names = re.findall(r"(?m)^\s*--- FAIL: (\S+) \(", output)
        if not packages:
            return invalid("invalid_record", ["Missing go package summary"])
        total = max(len(failed_names), 1)
        pending = []
        for line in output.splitlines():
            failed = re.match(r"\s*--- FAIL: (\S+) \(", line)
            if failed:
                pending.append(failed[1])
            package = re.match(r"^FAIL\s+(\S+)(?:\s+[\d.]+s)?\s*$", line)
            if package:
                failures.extend([name, package[1]+"."+name] for name in pending)
                pending = []
        if pending:
            return invalid("invalid_record", ["Missing package summary for failed tests"])
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
    test_commit = record.get("testCommit")
    implementation_commit = record.get("implementationCommit")
    if not isinstance(test_commit, str) or not re.fullmatch(r"[a-f0-9]{40,64}", test_commit):
        return invalid("invalid_record", ["A full committed RED test revision is required"])
    if implementation_commit is not None and (not isinstance(implementation_commit, str) or not re.fullmatch(r"[a-f0-9]{40,64}", implementation_commit)):
        return invalid("invalid_record", ["Implementation revision must be a full commit ID"])
    head_result = run(["git", "rev-parse", "HEAD"], root(), check=False)
    head = head_result.stdout.strip()
    if head_result.returncode:
        return invalid("invalid_record", ["Current repository revision is unavailable"])
    endpoint = implementation_commit or head
    for earlier, later in ((test_commit, endpoint), (endpoint, head)):
        if run(["git", "merge-base", "--is-ancestor", earlier, later], root(), check=False).returncode:
            return invalid("invalid_record", ["RED and implementation commits must belong to current history"])
    if implementation_commit == test_commit:
        return invalid("invalid_record", ["RED test commit must precede implementation"])
    changed = run(["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "-z", "-r", test_commit], root(), check=False)
    try:
        test_path = safe_path(record["targetFile"])
        relative = test_path.relative_to(root()).as_posix()
        current_test = test_path.read_bytes()
    except (Failure, ValueError, TypeError, OSError):
        return invalid("invalid_record", ["Target test must be a readable repository file"])
    if changed.returncode or relative not in changed.stdout.split("\0"):
        return invalid("invalid_record", ["Target test is absent from RED commit"])
    committed_test = subprocess.run(["git", "show", test_commit+":"+relative], cwd=root(), capture_output=True)
    if committed_test.returncode or committed_test.stdout != current_test:
        return invalid("invalid_record", ["Target test differs from its committed RED bytes"])
    return {"verdict": "RED_EVIDENCE_OK", "evidence": {"target": target, "tests": total, "report_errors": [],
            "testCommit": test_commit, "implementationCommit": implementation_commit, "checkedRevision": head}}, 0
