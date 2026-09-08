"""Independent read-only verification of the cycle-2 TASK-001 candidate."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / ".worktrees/TASK-001-a2"
BUNDLE = ROOT / ".ai/plans/current/PLAN-001"
CANDIDATE = BUNDLE / "reviews/candidates/CANDIDATE-TASK-001-a2-d1fc91746641.json"
sys.path.insert(0, str(TREE / "src"))
import domain_values as dv
import ai


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=TREE, capture_output=True, check=True, shell=False).stdout


candidate = read(CANDIDATE)
assert Path(dv.__file__).resolve() == (TREE / "src/domain_values.py").resolve()
assert git("rev-parse", "HEAD").decode().strip() == candidate["head_oid"] == "d1fc917466410febc6238479e65816dd39591a4f"
assert candidate["base_oid"] == "1a5e4ad2c0f476edcec3d55ca0ccc37d4c914751"
assert not git("status", "--porcelain")
assert git("branch", "--show-current").decode().strip() == "ai/PLAN-001/TASK-001/a2"
git("merge-base", "--is-ancestor", candidate["base_oid"], candidate["head_oid"])
diff = git("diff", "--binary", candidate["base_oid"], candidate["head_oid"])
assert hashlib.sha256(diff).hexdigest() == candidate["diff_sha256"]
for key, root in (("context_refs", TREE), ("validation_refs", ROOT)):
    for ref in candidate[key]:
        assert hashlib.sha256((root / ref["path"]).read_bytes()).hexdigest() == ref["sha256"], ref["path"]
policy_bytes = (ROOT / ".ai/project/policy.json").read_bytes() + (ROOT / ".ai/project/agent-models.json").read_bytes()
assert hashlib.sha256(policy_bytes).hexdigest() == candidate["policy_model_digest"]
fingerprinted = {key: value for key, value in candidate.items() if key != "fingerprint"}
fingerprint = hashlib.sha256(json.dumps(fingerprinted, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
assert fingerprint == candidate["fingerprint"] == "34f8bc7eb179c08bae4d4f60593927bcb61fe65dfdf5072a61b54540cd708926"
graph = read(TREE / ".ai/plans/current/PLAN-001/graph.json")
isolation = read(ROOT / graph["review_ref"])
tasks = [read(path) for path in (TREE / ".ai/plans/current/PLAN-001/tasks/current").glob("TASK-*.json")]
assert ai.structural_task_digest(tasks) == graph["task_set_sha256"] == isolation["task_set_sha256"]
assert graph["revision"] == candidate["graph_revision"] == isolation["graph_revision"] == 4
assert graph["status"] == "approved" and isolation["verdict"] == "pass"
task = next(task for task in tasks if task["id"] == "TASK-001")
assert task["depends_on"] == []
expected_paths = {
    "src/domain_values.py", "tests/unit/domain_values/test_domain_values.py",
    ".ai/plans/current/PLAN-001/evidence/implementation/TASK-001.md",
}
changed = git("diff", "--name-status", "-M", candidate["base_oid"], candidate["head_oid"]).decode()
assert set(changed.splitlines()) == {"A\t" + path for path in expected_paths}
scope = dv.ScopeClaim(**task["scope"])
assert all(scope.permits_write(path) for path in expected_paths)
assert not git("diff", "--check", candidate["base_oid"], candidate["head_oid"])
print("IDENTITY PASS: clean candidate", candidate["head_oid"], "base", candidate["base_oid"])
print("FINGERPRINT PASS:", fingerprint)
print("GRAPH PASS: r4 structural task digest", graph["task_set_sha256"])
print("SCOPE PASS: exactly three permitted additions; no renames, deletions or prohibited changes")
print(changed, end="")

for args, expected in [
    (["-m", "unittest", "discover", "-s", "tests/unit/domain_values/", "-p", "test_*.py"], "Ran 15 tests"),
    (["src/validate_foundation.py"], ""),
]:
    command = [sys.executable, *args]
    run = subprocess.run(command, cwd=TREE, capture_output=True, text=True, shell=False)
    print("COMMAND:", repr(command), "CWD:", TREE)
    print("EXIT:", run.returncode)
    print(run.stdout + run.stderr, end="")
    assert run.returncode == 0 and expected in run.stdout + run.stderr

schema_cases = [
    ("plan", ["properties", "status"], dv.PlanStatus),
    ("task", ["properties", "status"], dv.TaskStatus),
    ("task-graph", ["properties", "status"], dv.GraphStatus),
    ("spec", ["properties", "status"], dv.SpecStatus),
    ("workflow-run", ["properties", "status"], dv.WorkflowRunStatus),
    ("agent-run", ["properties", "status"], dv.AgentRunStatus),
    ("agent-output", ["properties", "status"], dv.AgentOutputStatus),
    ("worktree", ["properties", "status"], dv.WorktreeStatus),
    ("pr-state", ["properties", "status"], dv.PullRequestStatus),
    ("pr-state", ["properties", "checks", "items", "properties", "conclusion"], dv.CheckConclusion),
    ("pr-state", ["properties", "review_decision"], dv.PullRequestReviewDecision),
    ("review-result", ["properties", "verdict"], dv.ReviewVerdict),
    ("review-result", ["properties", "checks", "items", "properties", "status"], dv.ReviewCheckStatus),
    ("handoff", ["properties", "validation", "items", "properties", "status"], dv.ValidationStatus),
    ("command-evidence", ["properties", "status"], dv.CommandStatus),
    ("recovery", ["properties", "status"], dv.RecoveryStatus),
    ("framework-installation", ["properties", "installation_status"], dv.InstallationStatus),
    ("research-item", ["properties", "status"], dv.ResearchStatus),
    ("adr-index", ["properties", "decisions", "items", "properties", "status"], dv.DecisionStatus),
    ("workflow-run", ["properties", "pending_operations", "items", "properties", "status"], dv.PendingOperationStatus),
    ("project-state", ["properties", "phase"], dv.ProjectPhase),
]
for schema_name, keys, enum_type in schema_cases:
    value = read(TREE / f"schemas/v1/{schema_name}.schema.json")
    for key in keys:
        value = value[key]
    assert set(value["enum"]) == {member.value for member in enum_type}, enum_type.__name__
assert {member.value for member in dv.ExecutionStatus} == {"progress", "waiting", "tasks_accepted", "paused", "failed", "cancelled"}
assert {member.value for member in dv.CompletionStatus} == {"progress", "waiting", "delivery_ready", "completed", "paused", "failed"}
assert {member.value for member in dv.ErrorCategory} == {
    "invalid_input", "policy_denied", "unsupported_capability", "state_conflict", "scope_conflict",
    "git_conflict", "validation_failed", "review_failed", "transient_provider", "ambiguous_side_effect",
    "budget_exhausted", "internal_error",
}
print("VOCABULARY PASS:", len(schema_cases), "direct schema comparisons, 2 service status sets, 12 shared error categories")
syntax = ast.parse((TREE / "src/domain_values.py").read_text(encoding="utf-8"))
imports = sorted({node.module for node in ast.walk(syntax) if isinstance(node, ast.ImportFrom)} | {alias.name for node in ast.walk(syntax) if isinstance(node, ast.Import) for alias in node.names})
assert set(imports) <= {"__future__", "math", "re", "unicodedata", "collections.abc", "dataclasses", "enum", "typing"}
print("PURE DOMAIN IMPORTS PASS:", ", ".join(imports))

original = {"nested": [{"value": 1}]}
frozen = dv.FrozenJsonObject(original)
original["nested"][0]["value"] = 2
thawed = frozen.to_dict()
thawed["nested"][0]["value"] = 3
assert frozen.to_dict() == {"nested": [{"value": 1}]}
assert hash(frozen) == hash(dv.FrozenJsonObject({"nested": [{"value": 1}]}))
assert dv.RecordRef("task", "TASK-001", "PLAN-001") != dv.RecordRef("task", "TASK-001", "PLAN-002")
for kind in ("task", "command", "review", "evidence", "custom-record"):
    try:
        dv.RecordRef(kind, "TASK-001")
    except ValueError:
        pass
    else:
        raise AssertionError((kind, "bare reference accepted"))
print("IMMUTABILITY AND QUALIFICATION PASS: original/returned JSON detached; equal hashes; plan identities distinct; bare local refs rejected")

cases = [
    ("src/generated", "src/generated/value.py", True),
    ("SRC/Generated", "src/generated/nested/", True),
    ("src/generated/", "src/generated", True),
    ("src/caf\u00e9", "SRC/cafe\u0301/nested/", True),
    ("src/\uff27enerated", "src/generated/file.py", True),
    ("src/Stra\u00dfe", "SRC/STRASSE/child", True),
    ("src/generated", "src/generator/value.py", False),
    ("src/generated/value.py", "src/generated_other/value.py", False),
    ("src/generated/a.py", "src/generated/b.py", False),
]
comparisons = 0
for left, right, expected in cases:
    for first, second in ((left, right), (right, left)):
        assert dv.ScopePath(first).overlaps(second) is expected, (first, second)
        comparisons += 1
        for first_access, second_access in (("write_paths", "write_paths"), ("write_paths", "read_paths"), ("read_paths", "write_paths")):
            assert dv.ScopeClaim(**{first_access: [first]}).conflicts_with(dv.ScopeClaim(**{second_access: [second]})) is expected
            comparisons += 1
        assert not dv.ScopeClaim(read_paths=[first]).conflicts_with(dv.ScopeClaim(read_paths=[second]))
        comparisons += 1
    print("OVERLAP PROBE:", ascii(left), ascii(right), "expected=", expected)
exact = dv.ScopePath("src/generated")
assert exact.contains("src/generated")
assert not exact.contains("src/generated/child")
assert not exact.contains("src/generated/")
assert not dv.ScopePath("src/generated/").contains("src/generated")
assert not dv.ScopeClaim(write_paths=[exact]).permits_write("src/generated/child")
assert not dv.ScopeClaim(read_paths=[exact]).permits_read("src/generated/child")
assert dv.ScopeClaim(write_paths=["src/"], prohibited_paths=["src/secret/"]).permits_write("src/public.txt")
assert not dv.ScopeClaim(write_paths=["src/"], prohibited_paths=["src/secret/"]).permits_write("src/secret/key.txt")
print("REPAIR PASS:", comparisons, "overlap/access/read-only matrix assertions; exact permission containment preserved")
assert not git("status", "--porcelain")
print("FINAL PASS: candidate stayed clean and unchanged")
