"""Manual coordination helpers for this implementation session, not product code."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
BUNDLE = ROOT / ".ai/plans/current/PLAN-001"
PYTHON = Path(sys.executable)
DISPATCH = BUNDLE / "evidence/coordination/dispatch"

def git(*args, cwd=ROOT):
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, shell=False)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout.strip()

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def runtime_metadata(prefix, cwd, task_id):
    task = read(BUNDLE / "tasks/current" / f"{task_id}.json")
    modules = [Path(path).stem for path in task["scope"]["write_paths"]
               if path.startswith("src/") and path.endswith(".py") and "/" not in path[4:]]
    script = (
        "import sys, platform, importlib, importlib.metadata; from pathlib import Path; "
        "src=(Path.cwd()/'src').resolve(); sys.path.insert(0,str(src)); "
        "print('Python:',sys.version); print('Executable:',sys.executable); "
        "print('Platform:',platform.platform()); print('jsonschema:',importlib.metadata.version('jsonschema')); "
        f"modules=[importlib.import_module(name) for name in {modules!r}]; "
        "print('Origins:',[(item.__name__,item.__file__) for item in modules]); "
        "assert all(Path(item.__file__).resolve().parent == src for item in modules), 'Wrong candidate source origin'"
    )
    result = subprocess.run([*prefix, "-c", script], cwd=cwd, text=True, capture_output=True,
                            encoding="utf-8", errors="replace", timeout=30, shell=False)
    return result.returncode, f"Runtime/origin probe exit: {result.returncode}\n{result.stdout}\n{result.stderr}\n"

def status():
    tasks = [read(path) for path in sorted((BUNDLE / "tasks/current").glob("TASK-*.json"))]
    accepted = {task["id"] for task in tasks if task["status"] == "accepted"}
    ready = [task for task in tasks if task["status"] in {"backlog", "ready", "blocked"} and set(task["depends_on"]) <= accepted]
    active = [task for task in tasks if task["status"] not in {"backlog", "ready", "blocked", "accepted"}]
    return {"accepted": len(accepted), "total": len(tasks),
            "ready": [{"id": task["id"], "title": task["title"], "depends_on": task["depends_on"]} for task in ready],
            "active": [{"id": task["id"], "status": task["status"]} for task in active]}

def approve():
    graph = read(BUNDLE / "graph.json")
    report_path = BUNDLE / "reviews" / f"r{graph['revision']}-isolation-review.json"
    report = read(report_path)
    assert report["verdict"] == "pass"
    assert report["task_set_sha256"] == graph["task_set_sha256"]
    assert report["graph_revision"] == graph["revision"]
    assert {c["id"] for c in report["checks"]} == {f"ISO-{n:02d}" for n in range(1, 13)}
    assert all(c["status"] in {"pass", "not_applicable"} for c in report["checks"])
    assert not any(f["severity"] in {"blocking", "major"} and not f["resolved"] for f in report["findings"])
    graph.update(status="approved", review_ref=report_path.relative_to(ROOT).as_posix())
    write(BUNDLE / "graph.json", graph)
    plan = read(BUNDLE / "plan.json")
    plan.update(status="approved", isolation_review_ref=graph["review_ref"],
                resume_state="Independent isolation review passed; begin dependency-ready tasks through the manual coordinator with separate worktrees and two task reviews.")
    write(BUNDLE / "plan.json", plan)
    state = read(ROOT / ".ai/STATE.json")
    state["generation"] += 1
    state["known_blockers"] = []
    state["summary"] = "PLAN-001 graph r4 independently approved. Manual coordination is implementing the local deterministic engine; bootstrap behavior remains verified."
    state["next_actions"] = ["Implement dependency-ready tasks and accept only after actual validation plus independent implementation and consistency reviews"]
    state["updated_at"] = datetime.now(UTC).isoformat()
    write(ROOT / ".ai/STATE.json", state)
    return {"approved": graph["id"], "review": graph["review_ref"]}

def begin(task_id, attempt):
    graph = read(BUNDLE / "graph.json")
    assert graph["status"] == "approved"
    approval = read(ROOT / graph["review_ref"])
    assert approval["verdict"] == "pass" and approval["task_set_sha256"] == graph["task_set_sha256"]
    path = BUNDLE / "tasks/current" / f"{task_id}.json"
    task = read(path)
    for dependency in task["depends_on"]:
        assert read(BUNDLE / "tasks/current" / f"{dependency}.json")["status"] == "accepted", dependency
    assert task["status"] in {"backlog", "ready", "blocked"}
    task["status"] = "running"
    identity = f"{task_id}-a{attempt}"
    task["attempt_ids"].append(identity)
    task["resume_state"] = "Manual coordinator dispatched an isolated implementation; acceptance requires both fresh independent reviews."
    write(path, task)
    git("add", str(path.relative_to(ROOT)))
    git("commit", "-m", f"Dispatch PLAN-001 {identity}")
    base = git("rev-parse", "HEAD")
    branch = f"ai/PLAN-001/{task_id}/a{attempt}"
    worktree = ROOT / ".worktrees" / identity
    git("worktree", "add", "-b", branch, str(worktree), base)
    record = {"task_id": task_id, "attempt_id": identity, "branch": branch,
              "worktree": str(worktree), "base_oid": base, "graph_revision": graph["revision"],
              "task_set_sha256": graph["task_set_sha256"]}
    write(DISPATCH / f"{identity}.json.txt", record)
    return record

def candidate(task_id, attempt, *, linux=False, py311=False, linux_py311=False):
    identity = f"{task_id}-a{attempt}"
    dispatch = read(DISPATCH / f"{identity}.json.txt")
    worktree = Path(dispatch["worktree"])
    assert not git("status", "--porcelain", cwd=worktree), "Candidate must be committed and clean"
    base = git("rev-parse", "HEAD")
    git("merge", "--no-edit", base, cwd=worktree)
    head = git("rev-parse", "HEAD", cwd=worktree)
    command = read(BUNDLE / "commands" / f"test.{task_id}.json")
    argv = [str(PYTHON), *command["argv"][1:]]
    metadata_code, metadata = runtime_metadata([str(PYTHON)], worktree, task_id)
    result = subprocess.run(argv, cwd=worktree, text=True, capture_output=True,
                            timeout=command["timeout_seconds"], shell=False)
    evidence = BUNDLE / "evidence/validation" / f"{identity}-{head[:12]}.txt"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(f"Task: PLAN-001/{task_id}\nHead: {head}\nCommand: {command['argv']}\n"
                        f"Exit code: {result.returncode}\n\n{metadata}\n{result.stdout}\n{result.stderr}", encoding="utf-8")
    assert metadata_code == 0, str(evidence)
    assert result.returncode == 0, str(evidence)
    import re
    counts = re.findall(r"Ran (\d+) tests?", result.stdout + result.stderr)
    assert counts and int(counts[-1]) > 0, "No observed passing tests"
    validation_evidence = [evidence]
    linux_count = None
    if linux:
        linux_root = "/mnt/d/Codex Projects/ai-engineering-template"
        linux_worktree = linux_root + "/.worktrees/" + identity
        linux_python = linux_root + "/.ai/local/full-plan-linux-venv/bin/python"
        linux_argv = ["wsl.exe", "-d", "Ubuntu-24.04", "--cd", linux_worktree,
                      "--exec", linux_python, *command["argv"][1:]]
        linux_metadata_code, linux_metadata = runtime_metadata(linux_argv[:7], ROOT, task_id)
        linux_result = subprocess.run(linux_argv, cwd=ROOT, text=True, capture_output=True,
                                      encoding="utf-8", errors="replace",
                                      timeout=command["timeout_seconds"], shell=False)
        linux_evidence = BUNDLE / "evidence/validation" / f"{identity}-{head[:12]}-linux.txt"
        linux_evidence.write_text(
            f"Task: PLAN-001/{task_id}\nHead: {head}\nPlatform: Ubuntu-24.04 via WSL --exec\n"
            f"Command: {command['argv']}\nExit code: {linux_result.returncode}\n\n"
            f"{linux_metadata}\n{linux_result.stdout}\n{linux_result.stderr}", encoding="utf-8")
        assert linux_metadata_code == 0, str(linux_evidence)
        assert linux_result.returncode == 0, str(linux_evidence)
        linux_counts = re.findall(r"Ran (\d+) tests?", linux_result.stdout + linux_result.stderr)
        assert linux_counts and int(linux_counts[-1]) > 0, "No observed passing Linux tests"
        linux_count = int(linux_counts[-1])
        validation_evidence.append(linux_evidence)
    py311_count = None
    if py311:
        py311_python = ROOT / ".ai/local/full-plan-py311-venv/Scripts/python.exe"
        minimum_metadata_code, minimum_metadata = runtime_metadata([str(py311_python)], worktree, task_id)
        py311_result = subprocess.run([str(py311_python), *command["argv"][1:]], cwd=worktree,
                                     text=True, capture_output=True,
                                     timeout=command["timeout_seconds"], shell=False)
        py311_evidence = BUNDLE / "evidence/validation" / f"{identity}-{head[:12]}-python311.txt"
        py311_evidence.write_text(
            f"Task: PLAN-001/{task_id}\nHead: {head}\nPlatform: Windows Python3.11.16\n"
            f"Command: {command['argv']}\nExit code: {py311_result.returncode}\n\n"
            f"{minimum_metadata}\n{py311_result.stdout}\n{py311_result.stderr}", encoding="utf-8")
        assert minimum_metadata_code == 0, str(py311_evidence)
        assert py311_result.returncode == 0, str(py311_evidence)
        py311_counts = re.findall(r"Ran (\d+) tests?", py311_result.stdout + py311_result.stderr)
        assert py311_counts and int(py311_counts[-1]) > 0, "No observed passing Python3.11 tests"
        py311_count = int(py311_counts[-1])
        validation_evidence.append(py311_evidence)
    linux_py311_count = None
    if linux_py311:
        linux_root = "/mnt/d/Codex Projects/ai-engineering-template"
        linux_argv = ["wsl.exe", "-d", "Ubuntu-24.04", "--cd", linux_root + "/.worktrees/" + identity,
                      "--exec", linux_root + "/.ai/local/full-plan-linux-py311-venv/bin/python",
                      *command["argv"][1:]]
        linux_minimum_metadata_code, linux_minimum_metadata = runtime_metadata(linux_argv[:7], ROOT, task_id)
        minimum_result = subprocess.run(linux_argv, cwd=ROOT, text=True, capture_output=True,
                                        encoding="utf-8", errors="replace",
                                        timeout=command["timeout_seconds"], shell=False)
        minimum_evidence = BUNDLE / "evidence/validation" / f"{identity}-{head[:12]}-linux-python311.txt"
        minimum_evidence.write_text(
            f"Task: PLAN-001/{task_id}\nHead: {head}\nPlatform: Ubuntu-24.04 Python3.11.16 via WSL --exec\n"
            f"Command: {command['argv']}\nExit code: {minimum_result.returncode}\n\n"
            f"{linux_minimum_metadata}\n{minimum_result.stdout}\n{minimum_result.stderr}", encoding="utf-8")
        assert linux_minimum_metadata_code == 0, str(minimum_evidence)
        assert minimum_result.returncode == 0, str(minimum_evidence)
        minimum_counts = re.findall(r"Ran (\d+) tests?", minimum_result.stdout + minimum_result.stderr)
        assert minimum_counts and int(minimum_counts[-1]) > 0, "No observed passing Linux Python3.11 tests"
        linux_py311_count = int(minimum_counts[-1])
        validation_evidence.append(minimum_evidence)
    task = read(BUNDLE / "tasks/current" / f"{task_id}.json")
    refs = [BUNDLE / "plan.json", BUNDLE / "spec.json", BUNDLE / "graph.json", BUNDLE / "tasks/current" / f"{task_id}.json",
            ROOT / ".ai/shared/architecture/service-contracts.md", ROOT / ".ai/shared/workflows/reviews.md"]
    refs += [ROOT / ref for ref in task["adr_refs"] + task["research_refs"]]
    refs += [BUNDLE / "evidence/implementation" / f"{dep}.md" for dep in task["depends_on"]]
    def hashrefs(paths, *, committed_context=False):
        result = []
        for path in paths:
            relative = path.relative_to(ROOT)
            source = worktree / relative if committed_context else path
            result.append({"path": relative.as_posix(), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
        return result
    diff = subprocess.run(["git", "diff", "--binary", base, head], cwd=worktree, capture_output=True, check=True).stdout
    graph = read(BUNDLE / "graph.json")
    policy = hashlib.sha256((ROOT / ".ai/project/policy.json").read_bytes() + (ROOT / ".ai/project/agent-models.json").read_bytes()).hexdigest()
    value = {"schema_version": "1.0", "kind": "candidate", "id": f"CANDIDATE-{identity}-{head[:12]}",
             "task_id": task_id, "plan_id": "PLAN-001", "graph_revision": graph["revision"],
             "base_oid": base, "head_oid": head, "diff_sha256": hashlib.sha256(diff).hexdigest(),
             "context_refs": hashrefs(refs, committed_context=True), "validation_refs": hashrefs(validation_evidence),
             "checklist_version": "PLAN-001-v1", "policy_model_digest": policy}
    value["fingerprint"] = digest(value)
    path = BUNDLE / "reviews/candidates" / f"{value['id']}.json"
    write(path, value)
    return {"candidate": str(path), "worktree": str(worktree), "tests": int(counts[-1]),
            "linux_tests": linux_count, "py311_tests": py311_count, "linux_py311_tests": linux_py311_count,
            "base_oid": base, "head_oid": head, "fingerprint": value["fingerprint"]}

def accept(task_id, attempt):
    from jsonschema import Draft202012Validator, FormatChecker
    identity = f"{task_id}-a{attempt}"
    dispatch = read(DISPATCH / f"{identity}.json.txt")
    worktree = Path(dispatch["worktree"])
    head = git("rev-parse", "HEAD", cwd=worktree)
    candidates = [(path, read(path)) for path in (BUNDLE / "reviews/candidates").glob("*.json")]
    matches = [(path, value) for path, value in candidates if value["task_id"] == task_id and value["head_oid"] == head]
    assert len(matches) == 1, "Exactly one current candidate is required"
    candidate_path, value = matches[0]
    Draft202012Validator(read(ROOT / "schemas/v1/candidate.schema.json"), format_checker=FormatChecker()).validate(value)
    assert value["fingerprint"] == digest({key: item for key, item in value.items() if key != "fingerprint"})
    for ref in value["context_refs"]:
        assert hashlib.sha256((worktree / ref["path"]).read_bytes()).hexdigest() == ref["sha256"], ref["path"]
    for ref in value["validation_refs"]:
        assert hashlib.sha256((ROOT / ref["path"]).read_bytes()).hexdigest() == ref["sha256"], ref["path"]
    assert value["base_oid"] == git("rev-parse", "HEAD"), "Integration base changed; form and review a fresh candidate"
    assert not git("status", "--porcelain", cwd=worktree)
    task_path = BUNDLE / "tasks/current" / f"{task_id}.json"
    task = read(task_path)
    import unicodedata
    normalize = lambda text: unicodedata.normalize("NFC", text.replace("\\", "/")).casefold()
    def covers(claim, path):
        claim, path = normalize(claim), normalize(path)
        return path.startswith(claim) if claim.endswith("/") else path == claim
    raw_paths = subprocess.run(["git", "diff", "--name-only", "--no-renames", "-z", value["base_oid"], head], cwd=worktree, check=True, capture_output=True).stdout
    changed = [path.decode("utf-8") for path in raw_paths.split(b"\0") if path]
    assert changed, "No task changes to accept"
    for path in changed:
        assert any(covers(claim, path) for claim in task["scope"]["write_paths"]), f"Out-of-scope change: {path}"
        assert not any(covers(claim, path) for claim in task["scope"]["prohibited_paths"]), f"Prohibited change: {path}"
    stages = {}
    for path in (BUNDLE / "reviews").rglob("*.json"):
        review = read(path)
        if review.get("kind") != "review-result" or review.get("candidate_fingerprint") != value["fingerprint"]:
            continue
        if review["verdict"] != "pass":
            continue
        Draft202012Validator(read(ROOT / "schemas/v1/review-result.schema.json"), format_checker=FormatChecker()).validate(review)
        assert review["candidate_ref"] == candidate_path.relative_to(ROOT).as_posix()
        assert review["reviewer"]["model_id"] == "gpt-6-astra"
        assert review["reviewer"]["capability_rank"] > 3
        assert review["independent_session_id"] != review["implementation_session_id"]
        prefix, count = ("R1", 11) if review["stage"] == "implementation" else ("R2", 12)
        assert len(review["checks"]) == count
        assert {check["id"] for check in review["checks"]} == {f"{prefix}-{n:02d}" for n in range(1, count + 1)}
        assert all(check["status"] in {"pass", "not_applicable"} and check["rationale"] and (check["evidence"] or check["status"] == "not_applicable") for check in review["checks"])
        assert not any(finding["severity"] in {"blocking", "major"} and not finding["resolved"] for finding in review["findings"])
        assert review["stage"] not in stages, "Ambiguous passing reviews"
        stages[review["stage"]] = (path, review)
    assert set(stages) == {"implementation", "consistency"}, "Both independent reviews are required"
    r1_path, r1 = stages["implementation"]
    r2_path, r2 = stages["consistency"]
    assert r2["review_1_ref"] == r1_path.relative_to(ROOT).as_posix()
    assert r1["independent_session_id"] != r2["independent_session_id"]
    assert r1["reviewer"]["invocation_id"] != r2["reviewer"]["invocation_id"]
    git("merge", "--ff-only", head)
    task.update(status="accepted", resume_state=f"Candidate {head} passed actual task validation and independent R1/R2, then integrated locally. Plan completion still requires the final integrated gate and observed merge.")
    write(task_path, task)
    state_path = ROOT / ".ai/STATE.json"
    state = read(state_path)
    state["generation"] += 1
    accepted = [read(path)["id"] for path in (BUNDLE / "tasks/current").glob("*.json") if read(path)["status"] == "accepted"]
    state["summary"] = f"PLAN-001 graph r4 implementation: {len(accepted)} of 39 tasks accepted after validation and separate R1/R2. Remaining engine work is in progress; completion is not yet established."
    state["updated_at"] = datetime.now(UTC).isoformat()
    write(state_path, state)
    paths = [task_path, state_path, candidate_path, r1_path, r2_path]
    paths += [ROOT / ref["path"] for ref in value["validation_refs"]]
    paths += [p for p in (r1_path.with_suffix(".md"), r2_path.with_suffix(".md")) if p.exists()]
    for report_path in (r1_path, r2_path):
        paths += [path for path in report_path.parent.glob(report_path.stem + "*") if path.is_file()]
    paths = list(dict.fromkeys(paths))
    git("add", *[path.relative_to(ROOT).as_posix() for path in paths])
    git("commit", "-m", f"Accept PLAN-001 {task_id} after independent task reviews")
    assert worktree.resolve().parent == (ROOT / ".worktrees").resolve()
    git("merge-base", "--is-ancestor", head, "HEAD")
    git("worktree", "remove", str(worktree))
    return {"accepted": task_id, "candidate": head, "accepted_count": len(accepted), "integration": git("rev-parse", "HEAD")}

def fail(task_id, attempt):
    from jsonschema import Draft202012Validator, FormatChecker
    identity = f"{task_id}-a{attempt}"
    dispatch = read(DISPATCH / f"{identity}.json.txt")
    worktree = Path(dispatch["worktree"])
    head = git("rev-parse", "HEAD", cwd=worktree)
    matches = [(path, read(path)) for path in (BUNDLE / "reviews/candidates").glob("*.json")
               if read(path)["task_id"] == task_id and read(path)["head_oid"] == head]
    assert len(matches) == 1
    candidate_path, value = matches[0]
    assert value["base_oid"] == git("rev-parse", "HEAD")
    reports = [(path, read(path)) for path in (BUNDLE / "reviews").glob("*.json")
               if read(path).get("kind") == "review-result" and read(path).get("candidate_fingerprint") == value["fingerprint"]]
    assert any(report["verdict"] == "fail" for _, report in reports)
    validator = Draft202012Validator(read(ROOT / "schemas/v1/review-result.schema.json"), format_checker=FormatChecker())
    for _, report in reports:
        validator.validate(report)
    findings = [finding["id"] for _, report in reports for finding in report["findings"] if not finding["resolved"]]
    task_path = BUNDLE / "tasks/current" / f"{task_id}.json"
    task = read(task_path)
    task.update(status="repairing", resume_state="Failed review preserved; repair " + ", ".join(findings) + "; form a new candidate and rerun both independent reviews.")
    write(task_path, task)
    state_path = ROOT / ".ai/STATE.json"
    state = read(state_path)
    state["generation"] += 1
    state["summary"] = f"PLAN-001 graph r4 implementation: {status()['accepted']} of 39 tasks accepted. {task_id} is repairing preserved independent review findings; remaining work continues."
    state["updated_at"] = datetime.now(UTC).isoformat()
    write(state_path, state)
    paths = [task_path, state_path, candidate_path]
    paths += [ROOT / ref["path"] for ref in value["validation_refs"]]
    for report_path, _ in reports:
        paths += [path for path in report_path.parent.glob(report_path.stem + "*") if path.is_file()]
    git("add", *[path.relative_to(ROOT).as_posix() for path in dict.fromkeys(paths)])
    git("commit", "-m", f"Preserve failed review and repair state for PLAN-001 {task_id}")
    return {"task": task_id, "status": "repairing", "findings": findings, "integration": git("rev-parse", "HEAD")}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["approve", "begin", "candidate", "accept", "fail", "status"])
    parser.add_argument("task_id", nargs="?")
    parser.add_argument("attempt", type=int, nargs="?")
    parser.add_argument("--linux", action="store_true", help="Include Linux validation in a new candidate")
    parser.add_argument("--py311", action="store_true", help="Include minimum-version Windows validation in a new candidate")
    parser.add_argument("--linux-py311", action="store_true", help="Include minimum-version Linux validation in a new candidate")
    args = parser.parse_args()
    if (args.linux or args.py311 or args.linux_py311) and args.action != "candidate":
        parser.error("Platform validation options apply only to candidate")
    result = (candidate(args.task_id, args.attempt, linux=args.linux, py311=args.py311, linux_py311=args.linux_py311) if args.action == "candidate"
              else globals()[args.action]() if args.action in {"approve", "status"}
              else globals()[args.action](args.task_id, args.attempt))
    print(json.dumps(result, indent=2))
