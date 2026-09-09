"""Independent, read-only verification of the frozen TASK-001 a2 R1 candidate."""
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
CANDIDATE = BUNDLE / "reviews/candidates/CANDIDATE-TASK-001-a2-9f3b2b4b233b.json"
sys.path.insert(0, str(TREE / "src"))
import domain_values as dv
import ai


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=TREE, capture_output=True, check=True, shell=False).stdout


candidate = read(CANDIDATE)
assert str(Path(dv.__file__).resolve()).casefold() == str((TREE / "src/domain_values.py").resolve()).casefold()
assert git("rev-parse", "HEAD").decode().strip() == candidate["head_oid"]
assert not git("status", "--porcelain")
diff = git("diff", "--binary", candidate["base_oid"], candidate["head_oid"])
assert hashlib.sha256(diff).hexdigest() == candidate["diff_sha256"]
for key, root in (("context_refs", TREE), ("validation_refs", ROOT)):
    for ref in candidate[key]:
        assert hashlib.sha256((root / ref["path"]).read_bytes()).hexdigest() == ref["sha256"], ref["path"]
policy_bytes = (ROOT / ".ai/project/policy.json").read_bytes() + (ROOT / ".ai/project/agent-models.json").read_bytes()
assert hashlib.sha256(policy_bytes).hexdigest() == candidate["policy_model_digest"]
fingerprinted = {key: value for key, value in candidate.items() if key != "fingerprint"}
fingerprint = hashlib.sha256(json.dumps(fingerprinted, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
assert fingerprint == candidate["fingerprint"]
graph = read(TREE / ".ai/plans/current/PLAN-001/graph.json")
isolation = read(ROOT / graph["review_ref"])
tasks = [read(path) for path in (TREE / ".ai/plans/current/PLAN-001/tasks/current").glob("TASK-*.json")]
assert ai.structural_task_digest(tasks) == graph["task_set_sha256"] == isolation["task_set_sha256"]
assert graph["revision"] == candidate["graph_revision"] == isolation["graph_revision"] == 4
assert graph["status"] == "approved" and isolation["verdict"] == "pass"
assert not git("diff", "--check", candidate["base_oid"], candidate["head_oid"])
print("IDENTITY PASS: clean frozen head", candidate["head_oid"])
print("FINGERPRINT PASS:", fingerprint)
print("GRAPH PASS: r4 structural task digest", graph["task_set_sha256"])
print("CHANGED PATHS:")
print(git("diff", "--name-status", "-M", candidate["base_oid"], candidate["head_oid"]).decode(), end="")

run = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests/unit/domain_values/", "-p", "test_*.py"], cwd=TREE, capture_output=True, text=True, shell=False)
print("FOCUSED SUITE EXIT:", run.returncode)
print(run.stdout + run.stderr, end="")
assert run.returncode == 0 and "Ran 14 tests" in run.stdout + run.stderr

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
print("SCHEMA VOCABULARY PASS:", len(schema_cases), "direct schema comparisons")

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
assert not dv.ScopeClaim(read_paths=["src/"]).conflicts_with(dv.ScopeClaim(read_paths=["src/"]))
assert dv.ScopeClaim(write_paths=["src/"]).conflicts_with(dv.ScopeClaim(read_paths=["src/a.py"]))
print("IMMUTABILITY AND QUALIFICATION PASS: detached source/returned JSON, equal hashes, cross-plan identity")

for parent, child in [("src/generated", "src/generated/value.py"), ("SRC/Generated", "src/generated/nested/")]:
    overlap = dv.ScopePath(parent).overlaps(child)
    ww = dv.ScopeClaim(write_paths=[parent]).conflicts_with(dv.ScopeClaim(write_paths=[child]))
    wr = dv.ScopeClaim(write_paths=[parent]).conflicts_with(dv.ScopeClaim(read_paths=[child]))
    print(f"ANCESTOR PROBE: parent={parent!r}, child={child!r}, overlap={overlap}, write/write={ww}, write/read={wr}")
    assert not overlap and not ww and not wr
print("REPRODUCED DEFECT: exact-file ancestor claims are reported disjoint from descendants.")
