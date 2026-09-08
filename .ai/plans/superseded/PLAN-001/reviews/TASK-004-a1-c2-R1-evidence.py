"""Independent cycle-2 R1 evidence; candidate files remain read-only."""
from __future__ import annotations

import copy
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / ".worktrees/TASK-004-a1"
BUNDLE = ROOT / ".ai/plans/current/PLAN-001"
sys.path.insert(0, str(TREE / "src"))
import ai
import contracts
import domain_values as dv
import install
import validate_foundation


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def git(*args):
    return subprocess.run(["git", *args], cwd=TREE, capture_output=True, check=True, shell=False).stdout


candidate = read(BUNDLE / "reviews/candidates/CANDIDATE-TASK-004-a1-248f4dedf5d3.json")
assert Path(contracts.__file__).resolve() == (TREE / "src/contracts.py").resolve()
assert git("rev-parse", "HEAD").decode().strip() == candidate["head_oid"] == "248f4dedf5d37d09eb27a3ef08bb63a570359666"
assert candidate["base_oid"] == "77502377774bd5294ae0857035d40fe1698742c0"
assert not git("status", "--porcelain")
assert git("branch", "--show-current").decode().strip() == "ai/PLAN-001/TASK-004/a1"
git("merge-base", "--is-ancestor", candidate["base_oid"], candidate["head_oid"])
git("merge-base", "--is-ancestor", "d1fc917466410febc6238479e65816dd39591a4f", candidate["base_oid"])
assert hashlib.sha256(git("diff", "--binary", candidate["base_oid"], candidate["head_oid"])).hexdigest() == candidate["diff_sha256"]
for key, root in (("context_refs", TREE), ("validation_refs", ROOT)):
    for ref in candidate[key]:
        raw = (root / ref["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == ref["sha256"], ref["path"]
        if key == "context_refs":
            blob = git("show", candidate["head_oid"] + ":" + ref["path"])
            assert raw.replace(b"\r\n", b"\n") == blob.replace(b"\r\n", b"\n"), ref["path"]
            root_raw = (ROOT / ref["path"]).read_bytes()
            if root_raw != raw:
                print("ROOT/FROZEN BYTE DIFFERENCE", ref["path"], "CRLF-only", root_raw.replace(b"\r\n", b"\n") == raw.replace(b"\r\n", b"\n"))
policy = (ROOT / ".ai/project/policy.json").read_bytes() + (ROOT / ".ai/project/agent-models.json").read_bytes()
assert hashlib.sha256(policy).hexdigest() == candidate["policy_model_digest"]
fingerprinted = {k: v for k, v in candidate.items() if k != "fingerprint"}
fingerprint = hashlib.sha256(json.dumps(fingerprinted, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
assert fingerprint == candidate["fingerprint"] == "900aecdaa2a27efbe2bc869df51a5f07f846d492b0523c77ab5673848ef72fec"
tasks = [read(p) for p in (TREE / ".ai/plans/current/PLAN-001/tasks/current").glob("TASK-*.json")]
graph = read(TREE / ".ai/plans/current/PLAN-001/graph.json")
isolation = read(ROOT / graph["review_ref"])
assert ai.structural_task_digest(tasks) == contracts.structural_task_digest(tasks) == graph["task_set_sha256"] == isolation["task_set_sha256"] == "c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e"
assert graph["revision"] == candidate["graph_revision"] == isolation["graph_revision"] == 4
assert graph["status"] == "approved" and isolation["verdict"] == "pass"
expected = {"src/contracts.py", "src/install.py", "src/validate_foundation.py", "tests/unit/schemas/test_contracts.py", ".ai/plans/current/PLAN-001/evidence/implementation/TASK-004.md"}
changed = git("diff", "--name-status", "-M", candidate["base_oid"], candidate["head_oid"]).decode()
assert set(line.split("\t")[-1] for line in changed.splitlines()) == expected
task = next(t for t in tasks if t["id"] == "TASK-004")
assert all(dv.ScopeClaim(**task["scope"]).permits_write(p) for p in expected)
assert not git("diff", "--check", candidate["base_oid"], candidate["head_oid"])
print("IDENTITY, FROZEN CONTEXT, VALIDATION HASH, POLICY HASH, FINGERPRINT, R4 DIGEST, ACCEPTED TASK-001, SCOPE: PASS")
print("base", candidate["base_oid"], "head", candidate["head_oid"], "fingerprint", fingerprint)
print(changed, end="")

registry = contracts.ContractRegistry(TREE / "schemas/v1")
examples = list((TREE / "schemas/examples").glob("*.json"))
examples.append(TREE / ".ai/project/agent-models.json")
assert len(registry.kinds) == len(examples) == 27
assert {read(path)["kind"] for path in examples} == set(registry.kinds)
for path in examples:
    record = read(path)
    registry.validate(dv.FrozenJsonObject(record))
    bad = copy.deepcopy(record)
    bad["unexpected"] = True
    try:
        registry.validate(bad)
    except dv.DomainException as exc:
        assert exc.category == dv.ErrorCategory.VALIDATION_FAILED and not exc.error.retryable
    else:
        raise AssertionError(path)
for value in ["task:TASK-001", "task:PLAN-001:TASK-001:extra", "task:PLAN-001:TASK-001\n", "task:bad:TASK-001", "task:PLAN-001:bad", "command:CMD", "review:REV", "evidence:EVID", 1, None]:
    try:
        contracts.parse_record_ref(value)
    except dv.DomainException as exc:
        assert exc.category == dv.ErrorCategory.INVALID_INPUT
    else:
        raise AssertionError(value)
for kind, plan, local in [("task", "PLAN-001", "TASK-001"), ("command", "PLAN-001", "test.TASK-001"), ("review", "PLAN-001", "R1"), ("evidence", "PLAN-001", "E1"), ("plan", None, "PLAN-001")]:
    direct = dv.RecordRef(kind=kind, plan_id=None if plan is None else dv.PlanId(plan), local_id=dv.EntityId(local))
    assert contracts.parse_record_ref(str(direct)) == direct
print("ALL 27 V1 KINDS: immutable values and unknown-field typed failures PASS; LOGICAL REF constructor/failure parity PASS")

sample = read(TREE / "schemas/examples/task.json")
for namespace in [".ai", ".codex", ".claude"]:
    for sep in ["/", chr(92)]:
        first = copy.deepcopy(sample)
        first["input_contracts"] = [f"{namespace}/plans/current/PLAN-101/tasks/current/TASK-001.json".replace("/", sep)]
        first["scope"]["read_paths"] = [f"{namespace}/plans/current/PLAN-101/tasks/current/".replace("/", sep)]
        current = contracts.structural_task_digest([first])
        assert current == ai.structural_task_digest([first])
        for plan_bucket in ["current", "completed", "archived"]:
            for task_bucket in ["current", "completed", "archived"]:
                moved = copy.deepcopy(first)
                for collection in [moved["input_contracts"], moved["scope"]["read_paths"]]:
                    collection[0] = collection[0].replace(f"{sep}plans{sep}current{sep}", f"{sep}plans{sep}{plan_bucket}{sep}").replace(f"{sep}tasks{sep}current{sep}", f"{sep}tasks{sep}{task_bucket}{sep}")
                assert contracts.structural_task_digest([moved]) == current
                moved["scope"]["read_paths"].append("src/new_scope.py")
                assert contracts.structural_task_digest([moved]) != current
print("54 PROVIDER/SEPARATOR/PLAN/TASK BUCKET COMBINATIONS: record and directory relocation neutral; real scope mutation invalidates PASS")

objective = ".codex/plans/current/PLAN-101/spec.json must remain the selected active specification."
prose = ".codex/plans/current/PLAN-101/spec.json: required shape comes from docs/contract.md"
for field, text in [("objective", objective), ("input_contracts", prose)]:
    with tempfile.TemporaryDirectory(prefix="r1-c2-approval-") as directory:
        project = Path(directory) / "project"
        with contextlib.redirect_stdout(io.StringIO()):
            install.install(str(project), "codex")
            assert ai.main(["--project", str(project), "plan", "create", "PLAN-101", "--title", "R1 approval probe"]) == 0
        bundle = project / ".codex/plans/current/PLAN-101"
        task_path = bundle / "tasks/current/TASK-001.json"
        task = read(task_path)
        task[field] = text if field == "objective" else [text]
        write(task_path, task)
        graph_path = bundle / "graph.json"
        graph = read(graph_path)
        graph.update(status="approved", task_set_sha256=contracts.structural_task_digest([task]), review_ref=".codex/plans/current/PLAN-101/reviews/isolation.json")
        write(graph_path, graph)
        review = read(TREE / "schemas/examples/isolation-review.json")
        review.update(plan_id="PLAN-101", graph_revision=graph["revision"], task_set_sha256=graph["task_set_sha256"], verdict="pass")
        write(project / graph["review_ref"], review)
        plan_path = bundle / "plan.json"
        plan = read(plan_path)
        plan["isolation_review_ref"] = graph["review_ref"]
        write(plan_path, plan)
        validate_foundation.validate(project)
        replacement = text.replace("/current/", "/completed/")
        task[field] = replacement if field == "objective" else [replacement]
        registry.validate(task)
        write(task_path, task)
        try:
            validate_foundation.validate(project)
        except validate_foundation.ValidationFailure as exc:
            assert field == "objective" and "stale structural task digest" in str(exc)
            print("OLD OBJECTIVE PROSE REPRO: approved graph now rejects mutation PASS")
        else:
            assert field == "input_contracts"
            assert contracts.structural_task_digest([task]) == graph["task_set_sha256"]
            print("REMAINING DEFECT: approved graph ACCEPTS input_contracts prose mutation with unchanged graph/review digest")
            print("before", text)
            print("after ", replacement)
            print("unchanged digest", graph["task_set_sha256"])

with tempfile.TemporaryDirectory(prefix="r1-c2-closure-") as directory:
    fixture = Path(directory)
    src = fixture / "src"
    src.mkdir()
    sources = {"ai.py": "import contracts\nimport install\n", "validate_foundation.py": "import contracts\n", "contracts.py": "import domain_values\n", "domain_values.py": "pass\n", "install.py": "import helper\n", "helper.py": "import second\n", "second.py": "import install\n", "unrelated.py": "pass\n"}
    for name, content in sources.items():
        (src / name).write_text(content, encoding="utf-8")
    assert {p.name for p in install._tool_sources(fixture)} == set(sources) - {"unrelated.py"}
print("TRANSITIVE CLOSURE: reachable install.py, helper chain, cycle retained; unrelated source excluded PASS")

with tempfile.TemporaryDirectory(prefix="r1-c2-installed-") as directory:
    base = Path(directory)
    project = base / "fresh project"
    unrelated = base / "unrelated cwd"
    unrelated.mkdir()
    with contextlib.redirect_stdout(io.StringIO()):
        install.install(str(project), "codex")
    tools = project / ".codex/tools"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    probe = f"import pathlib,sys; sys.path.insert(0,{str(tools)!r}); import ai,contracts,domain_values,validate_foundation; root=pathlib.Path({str(tools)!r}).resolve(); assert all(pathlib.Path(m.__file__).resolve().parent==root for m in (ai,contracts,domain_values,validate_foundation)); print('ALL IMPORT ORIGINS INSTALLED')"
    for argv in [[sys.executable, "-I", "-B", "-c", probe], [sys.executable, "-B", str(tools / "validate_foundation.py"), "--project", str(project)]]:
        result = subprocess.run(argv, cwd=unrelated, env=env, capture_output=True, text=True, shell=False)
        assert result.returncode == 0, result.stdout + result.stderr
        print(result.stdout.strip())
print("FRESH INSTALLED TOOLS: isolated imports and standalone validator from unrelated cwd PASS")
assert not git("status", "--porcelain")
print("CANDIDATE REMAINS CLEAN; EXPECTED DEFECT REPRODUCED")
