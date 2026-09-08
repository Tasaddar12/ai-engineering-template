"""Independent R2 identity and frozen-consumer compatibility evidence; no source edits."""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys

import jsonschema

ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / ".worktrees/TASK-001-a2"
BUNDLE = ROOT / ".ai/plans/current/PLAN-001"
sys.path.insert(0, str(TREE / "src"))
import ai
import domain_values as dv


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(["git", *args], cwd=TREE, check=True, capture_output=True, shell=False).stdout


candidate_path = BUNDLE / "reviews/candidates/CANDIDATE-TASK-001-a2-d1fc91746641.json"
candidate = read(candidate_path)
r1_path = BUNDLE / "reviews/TASK-001-a2-c2-R1.json"
r1 = read(r1_path)
schema = read(TREE / "schemas/v1/review-result.schema.json")
jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(r1)
assert r1["verdict"] == "pass" and r1["stage"] == "implementation"
assert r1["candidate_ref"] == candidate_path.relative_to(ROOT).as_posix()
assert r1["candidate_fingerprint"] == candidate["fingerprint"]
assert r1["independent_session_id"] == "/root/r1_001_cycle2"
assert r1["implementation_session_id"] == "/root/implement_001"
assert r1["reviewer"]["capability_rank"] == 4
assert [check["id"] for check in r1["checks"]] == [f"R1-{number:02}" for number in range(1, 12)]
assert all(check["status"] == "pass" for check in r1["checks"])
assert not any(not finding["resolved"] and finding["severity"] in {"blocking", "major"} for finding in r1["findings"])
assert git("rev-parse", "HEAD").decode().strip() == candidate["head_oid"] == "d1fc917466410febc6238479e65816dd39591a4f"
assert candidate["base_oid"] == "1a5e4ad2c0f476edcec3d55ca0ccc37d4c914751"
assert git("branch", "--show-current").decode().strip() == "ai/PLAN-001/TASK-001/a2"
assert not git("status", "--porcelain")
git("merge-base", "--is-ancestor", candidate["base_oid"], candidate["head_oid"])
assert hashlib.sha256(git("diff", "--binary", candidate["base_oid"], candidate["head_oid"])).hexdigest() == candidate["diff_sha256"]
line_ending_only = []
for reference in candidate["context_refs"]:
    assert digest(TREE / reference["path"]) == reference["sha256"]
    if digest(ROOT / reference["path"]) != reference["sha256"]:
        assert (ROOT / reference["path"]).read_bytes().replace(b"\r\n", b"\n") == (TREE / reference["path"]).read_bytes().replace(b"\r\n", b"\n"), reference["path"]
        line_ending_only.append(reference["path"])
for reference in candidate["validation_refs"]:
    assert digest(ROOT / reference["path"]) == reference["sha256"]
assert hashlib.sha256((ROOT / ".ai/project/policy.json").read_bytes() + (ROOT / ".ai/project/agent-models.json").read_bytes()).hexdigest() == candidate["policy_model_digest"]
canonical = json.dumps({key: value for key, value in candidate.items() if key != "fingerprint"}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
assert hashlib.sha256(canonical).hexdigest() == candidate["fingerprint"] == "34f8bc7eb179c08bae4d4f60593927bcb61fe65dfdf5072a61b54540cd708926"
print("IDENTITY PASS: clean exact branch/head/base; diff, all frozen context hashes, validation and policy/model hashes, fingerprint match")
print("CURRENT CONTEXT PASS: same content; root CRLF-only differences:", line_ending_only)
print("R1 PASS: schema-valid matching pass, 11 passing checks, distinct invocation and no unresolved blocking/major finding")
print("R1_JSON_SHA256", digest(r1_path))
print("R1_OBSERVED_OUTPUT_SHA256", digest(BUNDLE / "reviews/TASK-001-a2-c2-R1-verified.txt"))

tasks = [read(path) for path in sorted((BUNDLE / "tasks/current").glob("TASK-*.json"))]
by_id = {task["id"]: task for task in tasks}
graph = read(BUNDLE / "graph.json")
isolation = read(ROOT / graph["review_ref"])
assert ai.structural_task_digest(tasks) == graph["task_set_sha256"] == isolation["task_set_sha256"]
assert graph["revision"] == isolation["graph_revision"] == candidate["graph_revision"] == 4
assert graph["status"] == "approved" and isolation["verdict"] == "pass"
assert all(node["depends_on"] == by_id[node["task_id"]]["depends_on"] for node in graph["nodes"])
assert by_id["TASK-001"]["depends_on"] == []
assert not any(task["status"] in {"accepted", "completed"} for task in tasks)
assert not list((BUNDLE / "tasks/completed").glob("TASK-*.json"))
changed = git("diff", "--name-status", "-M", candidate["base_oid"], candidate["head_oid"]).decode().splitlines()
expected = {"src/domain_values.py", "tests/unit/domain_values/test_domain_values.py", ".ai/plans/current/PLAN-001/evidence/implementation/TASK-001.md"}
assert set(changed) == {"A\t" + path for path in expected}
assert not git("diff", "--check", candidate["base_oid"], candidate["head_oid"])
scope = dv.ScopeClaim(**by_id["TASK-001"]["scope"])
assert all(scope.permits_write(path) for path in expected)
scopes = {task["id"]: dv.ScopeClaim(**task["scope"]) for task in tasks}
assert all(scopes[task["id"]].to_wire() == task["scope"] for task in tasks)


def ancestors(task_id):
    parents = by_id[task_id]["depends_on"]
    return set(parents).union(*(ancestors(parent) for parent in parents))


unordered = 0
for left, right in itertools.combinations(by_id, 2):
    if left in ancestors(right) or right in ancestors(left):
        continue
    unordered += 1
    assert not scopes[left].conflicts_with(scopes[right]), (left, right)
assert unordered == 280
print("GRAPH PASS:", graph["id"], "structural task digest", graph["task_set_sha256"])
print("COMPATIBILITY PASS: 39 task scopes round-trip unchanged; 280 unordered graph pairs remain disjoint under repaired domain comparison")
print("SIBLING/SCOPE PASS: no accepted engine siblings or prerequisites; exactly three allowed additions")

# Frozen local/workflow/orchestration port names remain unowned by this common module.
port_names = {"StateStore", "TransactionRequest", "TransactionResult", "AgentAdapter", "ReviewRequest", "SchedulingSnapshot", "ExecutionStep", "CompletionStep"}
assert not any(hasattr(dv, name) for name in port_names)
syntax = ast.parse((TREE / "src/domain_values.py").read_text(encoding="utf-8"))
imports = {node.module for node in ast.walk(syntax) if isinstance(node, ast.ImportFrom)} | {alias.name for node in ast.walk(syntax) if isinstance(node, ast.Import) for alias in node.names}
assert imports <= {"__future__", "math", "re", "unicodedata", "collections.abc", "dataclasses", "enum", "typing"}
assert "tasks_accepted" in {value.value for value in dv.ExecutionStatus}
assert "completed" not in {value.value for value in dv.ExecutionStatus}
assert "completed" in {value.value for value in dv.CompletionStatus}
plans = [dv.PlanId("PLAN-001"), dv.PlanId("PLAN-002")]
assert len({dv.RecordRef("task", "TASK-001", plan) for plan in plans}) == 2
for kind, entity_id in [("project-state", "ai-engineering-framework"), ("framework-installation", "FRAMEWORK-001"), ("policy", "POLICY-001"), ("agent-models", "AGENT-MODELS-001"), ("asset-manifest", "ASSETS-001"), ("research-item", "RES-001"), ("decision", "ADR-001"), ("adr-index", "ADR-INDEX-001")]:
    assert not dv.RecordRef(kind, entity_id).is_plan_qualified

# A project initialization event is a typed transaction value, not a required
# plan-qualified RecordRef lookup. No service implementation is supplied here.
@dataclass(frozen=True)
class EventBoundaryProbe:
    id: dv.EntityId
    entity_id: dv.EntityId
    generation: dv.Revision
    evidence: tuple[dv.EvidenceRef, ...]


event = EventBoundaryProbe(dv.EntityId("EVENT-INIT-001"), dv.EntityId("ai-engineering-framework"), dv.Revision(0), (dv.EvidenceRef(".ai/evidence/init.json", "a" * 64),))
wire_event = {"schema_version": "1.0", "kind": "state-event", "id": str(event.id), "operation_id": "OP-INIT-001", "generation": int(event.generation), "entity_id": str(event.entity_id), "event_type": "project_initialized", "from_state": None, "to_state": "foundation", "evidence_refs": [str(ref.path) for ref in event.evidence], "created_at": "2026-09-08T00:00:00Z", "payload_ref": None}
jsonschema.Draft202012Validator(read(TREE / "schemas/v1/state-event.schema.json"), format_checker=jsonschema.FormatChecker()).validate(wire_event)
assert "plan_id" not in wire_event
print("BOUNDARIES PASS: pure standard-library imports; separate port ownership; execution/completion distinction; cross-plan identity; project projections remain unqualified")
print("PROJECT EVENT COMPATIBILITY PASS: common EntityId/Revision/EvidenceRef values can form a schema-valid event before any plan; this probe does not implement StateStore or claim end-to-end execution")

command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
run = subprocess.run(command, cwd=TREE, capture_output=True, text=True, shell=False)
print("COMMAND", repr(command), "CWD", TREE)
print("EXIT", run.returncode)
print(run.stdout + run.stderr, end="")
assert run.returncode == 0 and "Ran 24 tests" in run.stdout + run.stderr
assert not git("status", "--porcelain")
assert git("rev-parse", "HEAD").decode().strip() == candidate["head_oid"]
print("FINAL PASS: candidate stayed clean and unchanged")
