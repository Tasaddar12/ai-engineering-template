"""Independent R1 probes; candidate read-only, temporary fixtures self-cleaning."""
from __future__ import annotations

import copy
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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


def git(*args):
    return subprocess.run(["git", *args], cwd=TREE, capture_output=True, check=True, shell=False).stdout


candidate = read(BUNDLE / "reviews/candidates/CANDIDATE-TASK-004-a1-7d92dda5237b.json")
assert Path(contracts.__file__).resolve() == (TREE / "src/contracts.py").resolve()
assert git("rev-parse", "HEAD").decode().strip() == candidate["head_oid"] == "7d92dda5237b57087a4c7e869deb72c9028ab82e"
assert candidate["base_oid"] == "6098dcdc58b667d14f1847dbf7b6c2990abb8453"
assert not git("status", "--porcelain")
assert git("branch", "--show-current").decode().strip() == "ai/PLAN-001/TASK-004/a1"
git("merge-base", "--is-ancestor", candidate["base_oid"], candidate["head_oid"])
git("merge-base", "--is-ancestor", "d1fc917466410febc6238479e65816dd39591a4f", candidate["base_oid"])
assert hashlib.sha256(git("diff", "--binary", candidate["base_oid"], candidate["head_oid"])).hexdigest() == candidate["diff_sha256"]
for key, root in (("context_refs", TREE), ("validation_refs", ROOT)):
    for ref in candidate[key]:
        assert hashlib.sha256((root / ref["path"]).read_bytes()).hexdigest() == ref["sha256"], ref["path"]
policy = (ROOT / ".ai/project/policy.json").read_bytes() + (ROOT / ".ai/project/agent-models.json").read_bytes()
assert hashlib.sha256(policy).hexdigest() == candidate["policy_model_digest"]
fingerprinted = {k: v for k, v in candidate.items() if k != "fingerprint"}
fingerprint = hashlib.sha256(json.dumps(fingerprinted, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
assert fingerprint == candidate["fingerprint"] == "a34899768c50111a454417f76f134e803790bd6625a100ed1b7f04b7d5e5e0d3"
tasks = [read(p) for p in (TREE / ".ai/plans/current/PLAN-001/tasks/current").glob("TASK-*.json")]
graph = read(TREE / ".ai/plans/current/PLAN-001/graph.json")
isolation = read(ROOT / graph["review_ref"])
assert ai.structural_task_digest(tasks) == contracts.structural_task_digest(tasks) == graph["task_set_sha256"] == isolation["task_set_sha256"]
assert graph["revision"] == candidate["graph_revision"] == isolation["graph_revision"] == 4
assert graph["status"] == "approved" and isolation["verdict"] == "pass"
expected = {
    "src/contracts.py", "src/install.py", "src/validate_foundation.py",
    "tests/unit/schemas/test_contracts.py", ".ai/plans/current/PLAN-001/evidence/implementation/TASK-004.md",
}
changed = git("diff", "--name-status", "-M", candidate["base_oid"], candidate["head_oid"]).decode()
assert set(line.split("\t")[-1] for line in changed.splitlines()) == expected
task = next(t for t in tasks if t["id"] == "TASK-004")
assert all(dv.ScopeClaim(**task["scope"]).permits_write(p) for p in expected)
assert not git("diff", "--check", candidate["base_oid"], candidate["head_oid"])
print("IDENTITY, CONTEXT HASHES, VALIDATION HASH, POLICY HASH, FINGERPRINT, R4 DIGEST, ACCEPTED DEPENDENCY, SCOPE: PASS")
print("base", candidate["base_oid"], "head", candidate["head_oid"], "fingerprint", fingerprint)
print(changed, end="")

registry = contracts.ContractRegistry(TREE / "schemas/v1")
for path in sorted((TREE / "schemas/examples").glob("*.json")):
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
print("ALL 27 KINDS: immutable example validation and unknown-field rejection PASS")
for value in ["task:TASK-001", "task:PLAN-001:TASK-001:extra", "task:PLAN-001:TASK-001\n", "task:bad:TASK-001", "task:PLAN-001:bad", "command:CMD", "review:REV", "evidence:EVID", 1, None]:
    try:
        contracts.parse_record_ref(value)
    except dv.DomainException as exc:
        assert exc.category == dv.ErrorCategory.INVALID_INPUT
    else:
        raise AssertionError(value)
for value in ["task:PLAN-001:TASK-001", "command:PLAN-001:test.TASK-001", "review:PLAN-001:R1", "evidence:PLAN-001:E1", "plan:PLAN-001"]:
    parsed = contracts.parse_record_ref(value)
    assert str(parsed) == value
print("LOGICAL REF MATRIX: typed valid identity round trips and malformed/bare-local failures PASS")

with tempfile.TemporaryDirectory(prefix="r1-task004-imports-") as directory:
    fixture = Path(directory)
    src = fixture / "src"
    src.mkdir()
    sources = {
        "ai.py": "import contracts\n",
        "validate_foundation.py": "import contracts\n",
        "contracts.py": "import domain_values\n",
        "domain_values.py": "pass\n",
        "install.py": "import helper\n",
        "helper.py": "import second\n",
        "second.py": "import install\n",
        "unrelated.py": "pass\n",
    }
    for name, content in sources.items():
        (src / name).write_text(content, encoding="utf-8")
    assert {p.name for p in install._tool_sources(fixture)} == set(install.REQUIRED_TOOL_MODULES)
    (src / "ai.py").write_text("import contracts\nimport install\n", encoding="utf-8")
    assert {p.name for p in install._tool_sources(fixture)} == set(sources) - {"unrelated.py"}
print("TRANSITIVE INSTALLER CLOSURE: reachable install.py + two new modules + cycle included; unreachable excluded PASS")

sample = read(TREE / "schemas/examples/task.json")
for namespace in [".ai", ".codex", ".claude"]:
    for sep in ["/", "\\"]:
        first = copy.deepcopy(sample)
        first["input_contracts"] = [f"{namespace}/plans/current/PLAN-101/tasks/current/TASK-001.json".replace("/", sep)]
        for bucket in ["completed", "archived"]:
            moved = copy.deepcopy(first)
            moved["input_contracts"] = [first["input_contracts"][0].replace(f"{sep}current{sep}", f"{sep}{bucket}{sep}")]
            assert contracts.structural_task_digest([first]) == contracts.structural_task_digest([moved])
print("RECORD LOCATION MATRIX: all 3 provider roots, both separators, completed/archived PASS")

first = copy.deepcopy(sample)
first["scope"]["read_paths"] = [".codex/plans/current/PLAN-101/tasks/current/"]
moved = copy.deepcopy(first)
moved["scope"]["read_paths"] = [".codex/plans/completed/PLAN-101/tasks/completed/"]
print("DIRECTORY LOCATION PROBE:", first["scope"]["read_paths"], "->", moved["scope"]["read_paths"])
print("directory_only_lifecycle_change_retains_digest", contracts.structural_task_digest([first]) == contracts.structural_task_digest([moved]))
first = copy.deepcopy(sample)
first["objective"] = ".codex/plans/current/PLAN-101/spec.json must remain the selected active specification."
changed = copy.deepcopy(first)
changed["objective"] = ".codex/plans/completed/PLAN-101/spec.json must remain the selected active specification."
registry.validate(first)
registry.validate(changed)
print("PROSE PROBE:", first["objective"], "->", changed["objective"])
print("changed_objective_prose_retains_digest", contracts.structural_task_digest([first]) == contracts.structural_task_digest([changed]))

with tempfile.TemporaryDirectory(prefix="r1-task004-approval-") as directory:
    project = Path(directory) / "project"
    with contextlib.redirect_stdout(io.StringIO()):
        install.install(str(project), "codex")
        assert ai.main(["--project", str(project), "plan", "create", "PLAN-101", "--title", "R1 approval probe"]) == 0
    bundle = project / ".codex/plans/current/PLAN-101"
    task_path = bundle / "tasks/current/TASK-001.json"
    task = read(task_path)
    task["objective"] = first["objective"]
    def write(path, value):
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    write(task_path, task)
    graph_path = bundle / "graph.json"
    graph = read(graph_path)
    graph["status"] = "approved"
    graph["task_set_sha256"] = contracts.structural_task_digest([task])
    graph["review_ref"] = ".codex/plans/current/PLAN-101/reviews/isolation.json"
    write(graph_path, graph)
    review = read(TREE / "schemas/examples/isolation-review.json")
    review.update(plan_id="PLAN-101", graph_revision=graph["revision"], task_set_sha256=graph["task_set_sha256"], verdict="pass")
    write(project / graph["review_ref"], review)
    plan_path = bundle / "plan.json"
    plan = read(plan_path)
    plan["isolation_review_ref"] = graph["review_ref"]
    write(plan_path, plan)
    validate_foundation.validate(project)
    task["objective"] = changed["objective"]
    write(task_path, task)
    validate_foundation.validate(project)
    print("APPROVED GRAPH PROBE: validator ACCEPTS changed objective prose with unchanged graph/review digest")

assert not git("status", "--porcelain")
print("CANDIDATE REMAINS CLEAN")
