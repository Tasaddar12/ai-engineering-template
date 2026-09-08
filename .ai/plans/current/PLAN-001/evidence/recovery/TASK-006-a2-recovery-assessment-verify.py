"""Read-only TASK-006 a2 recovery identity and retained-observation checks.

This does not run command fixtures, modify their source, or certify a repair.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[6]
TREE = ROOT / ".worktrees/TASK-006-a2"
A1_TREE = ROOT / ".worktrees/TASK-006-a1"
PLAN = ".ai/plans/current/PLAN-001/"
CHECKPOINT = "60f8801ac5679b4233aebdcb58f291e51a672e39"
HEAD = "4fe9e7a30378e13b43dc51745593adae2bb8b051"
BASE = "17595809d6ee74b2585265d94535cb1630d3a900"
OWNER = "5e455de46416758f0438c95ecda71c0630dc64a8"
DISPATCH = "a0c6b0c2f8691e1280c1d1272c8124d6a98edaeb"
A1 = "ce4c8edb86b02268a856a5f870932ade0e7e9b91"
PRODUCTION_BLOB = "39828108eb7d198d81d810c8fd9e136e3f64f8f0"
PRODUCTION_SHA = "700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0"
STEM = PLAN + "evidence/recovery/TASK-006-a2-recovery-assessment"
sys.path.insert(0, str(ROOT / "src"))
from contracts import ContractRegistry, structural_task_digest


def git(*args: str, cwd: Path = ROOT) -> bytes:
    return subprocess.check_output(
        ["git", *args], cwd=cwd, shell=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: str, root: Path = ROOT) -> dict:
    return json.loads((root / path).read_bytes())


def blob(oid: str, path: str) -> bytes:
    return git("show", oid + ":" + path)


assert git("rev-parse", "HEAD").decode().strip() == CHECKPOINT
assert not git("diff", "HEAD", "--name-only")
for tree, oid, branch in ((TREE, HEAD, "ai/PLAN-001/TASK-006/a2"),
                          (A1_TREE, A1, "ai/PLAN-001/TASK-006/a1")):
    assert git("rev-parse", "HEAD", cwd=tree).decode().strip() == oid
    assert git("rev-parse", branch).decode().strip() == oid
    assert not git("status", "--porcelain=v1", "--untracked-files=all", cwd=tree)
    print("PASS clean retained branch/worktree", branch, oid)
assert git("merge-base", BASE, HEAD).decode().strip() == BASE
for ancestor, descendant in ((OWNER, HEAD), (BASE, CHECKPOINT), (DISPATCH, OWNER),
                             ("64a48f6bde98f5a09db25ca8ae3e8fd3798ba4d1", A1)):
    git("merge-base", "--is-ancestor", ancestor, descendant)
print("PASS ROOT checkpoint and source/base/owner/failed-c1 ancestry", CHECKPOINT, BASE, OWNER)

owned = {"src/commands.py", "tests/unit/commands/test_commands.py",
         PLAN + "evidence/implementation/TASK-006.md"}
paths = set(git("diff", "--name-only", BASE, HEAD).decode().splitlines())
assert paths == owned
diff = git("diff", "--binary", BASE, HEAD)
assert sha(diff) == "7e50dd79d2a38622fa380ab2f7a31c7f258a701006cb9cd8b11716c7a765488d"
assert set(git("diff", "--name-only", OWNER + "^", OWNER).decode().splitlines()) == owned - {"src/commands.py"}
for path in owned:
    assert blob(OWNER, path) == blob(HEAD, path) == (TREE / path).read_bytes()
assert git("diff", "--name-only", BASE, HEAD, "--", "src").decode().splitlines() == ["src/commands.py"]
production = blob(HEAD, "src/commands.py")
assert production == blob(A1, "src/commands.py")
assert sha(production) == PRODUCTION_SHA
assert git("rev-parse", HEAD + ":src/commands.py").decode().strip() == PRODUCTION_BLOB
assert not git("ls-tree", "--name-only", CHECKPOINT, "src/commands.py")
print("PASS three-path exact binary diff", sha(diff), sorted(paths))
print("PASS a2 repair only test/handoff, owner bytes unchanged by metadata merge; production", PRODUCTION_BLOB, PRODUCTION_SHA)
salvage = git("log", "--format=%H", "--reverse", DISPATCH + ".." + HEAD, "--", *sorted(owned)).decode().splitlines()
assert salvage == ["60953e6aa33ad45680e1bb7e9873289fbb1d1186", "1403be69fdab0e753a608bd815b29d8f540a7067", "e58bb0c699df063c9577ccd8811dce4adb6984c1", OWNER]
print("PASS ordered unaccepted a2 source salvage", salvage)

registry = ContractRegistry(ROOT / "schemas/v1")
tasks = [read(str(path.relative_to(ROOT))) for path in sorted((ROOT / (PLAN + "tasks/current")).glob("TASK-*.json"))]
task_map = {task["id"]: task for task in tasks}
graph = read(PLAN + "graph.json")
isolation = read(PLAN + "reviews/r4-isolation-review.json")
digest = structural_task_digest(tasks)
assert len(tasks) == 39 and graph["revision"] == isolation["graph_revision"] == 4
assert graph["status"] == "approved" and isolation["verdict"] == "pass"
assert digest == graph["task_set_sha256"] == isolation["task_set_sha256"] == "c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e"
assert structural_task_digest([task_map["TASK-006"]]) == structural_task_digest([read(PLAN + "tasks/current/TASK-006.json", TREE)])
for path in (".ai/project/policy.json", ".ai/project/agent-models.json", ".ai/shared/architecture/service-contracts.md", PLAN + "graph.json", PLAN + "plan.json", PLAN + "spec.json", PLAN + "commands/test.TASK-006.json"):
    assert blob(CHECKPOINT, path) == blob(HEAD, path) == blob(A1, path)
assert not git("diff", "--name-only", BASE, HEAD, "--", "schemas", "src/local_ports.py", "src/config.py", "src/contracts.py")
print("PASS frozen task structure, policy/models, plan/spec, command, schemas/ports/config and r4 digest", digest)
for task_id, oid, source in (
    ("TASK-002", "460ab567d01912167557f2f671ed07c63f0a31e7", "src/local_ports.py"),
    ("TASK-004", "e3c1177f993ee74815639a83ef3333faa4ba3957", "src/contracts.py"),
    ("TASK-038", "6f2b12c3283ed7d6e3d4876020fe690c6e0061a3", "src/config.py"),
):
    assert task_map[task_id]["status"] == "accepted"
    git("merge-base", "--is-ancestor", oid, BASE)
    for path in (source, PLAN + "evidence/implementation/" + task_id + ".md"):
        assert blob(oid, path) == blob(HEAD, path) == blob(CHECKPOINT, path)
    print("PASS accepted dependency ancestry/source/handoff", task_id, oid)

candidate = read(PLAN + "reviews/candidates/CANDIDATE-TASK-006-a1-ce4c8edb86b0.json")
registry.validate(candidate)
for item in candidate["context_refs"]:
    assert sha(blob(A1, item["path"])) == item["sha256"]
for item in candidate["validation_refs"]:
    assert sha((ROOT / item["path"]).read_bytes()) == item["sha256"]
for suffix, verdict in (("c1-R1", "fail"), ("c2-R1", "pass"), ("c2-R2", "fail")):
    report = read(PLAN + "reviews/TASK-006-a1-" + suffix + ".json")
    registry.validate(report)
    assert report["verdict"] == verdict
    print("PASS preserved formal review", suffix, verdict)
history = git("ls-tree", "-r", "--name-only", DISPATCH, "--", PLAN + "reviews", PLAN + "evidence/validation", PLAN + "evidence/recovery").decode().splitlines()
history = [path for path in history if "TASK-006" in Path(path).name]
for path in history:
    assert (ROOT / path).read_bytes() == blob(DISPATCH, path)
print("PASS immutable earlier TASK-006 history files", len(history), "; old candidate context", len(candidate["context_refs"]), "and validations", len(candidate["validation_refs"]))
assert not list((ROOT / (PLAN + "reviews/candidates")).glob("CANDIDATE-TASK-006-a2-*"))
assert not list((ROOT / (PLAN + "reviews")).glob("TASK-006-*-c3-*.json"))

log_records = {}
for suffix, expected_sha, exit_value in (("", "9f9a9ac0269d508461dbfb85eb3abb2f80388029766bf2d243f34f35220c8700", 0), ("-linux", "e7033e14f5ec0287797d127b12c798eb2c6c86f694768e09085dcb5add0f011d", 1)):
    path = PLAN + "evidence/validation/TASK-006-a2-4fe9e7a30378" + suffix + ".txt"
    raw = (ROOT / path).read_bytes()
    assert sha(raw) == expected_sha
    text = raw.decode()
    assert "Head: " + HEAD in text and f"Exit code: {exit_value}" in text
    assert "Runtime/origin probe exit: 0" in text and "Ran 22 tests" in text
    records = [json.loads(line.removeprefix("TASK-006-FIXTURE ")) for line in text.splitlines() if line.startswith("TASK-006-FIXTURE ")]
    assert len(records) == 4
    for record in records:
        assert record["parent_pid"] and record["child_pid"]
        assert all(record[key] for key in ("parent_gone", "child_gone", "reader_threads_settled"))
        assert not record["watchdog_intervened"] and record["native_termination_calls"] == 1
    log_records[suffix] = records
    print("PASS retained raw validation identity/count/cleanup records", path, expected_sha, "exit", exit_value)
linux = (ROOT / (PLAN + "evidence/validation/TASK-006-a2-4fe9e7a30378-linux.txt")).read_text()
assert "0.10913950300891884 not greater than or equal to 0.15" in linux
assert "FAILED (failures=1, skipped=1)" in linux
observed = next(record for record in log_records["-linux"] if record["phase"] == "inherited_after_parent_exit" and record["mode"] == "cancellation")
assert observed["startup_seconds"] == 0.051996
assert observed["cancellation_response_seconds"] == 0.057143
print("RETAINED OBSERVATION ONLY", json.dumps(observed, sort_keys=True))
test_path = "tests/unit/commands/test_commands.py"
old_ast = ast.parse(blob(A1, test_path))
new_ast = ast.parse(blob(HEAD, test_path))
name = "test_inherited_pipe_descendant_cannot_block_timeout_or_cancellation_return"
def method(tree: ast.Module) -> ast.FunctionDef:
    return next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name)
def floor(tree: ast.Module) -> ast.Call:
    return next(node for node in ast.walk(method(tree)) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "assertGreaterEqual" and len(node.args) == 2 and isinstance(node.args[1], ast.IfExp))
old_floor, new_floor = floor(old_ast), floor(new_ast)
assert ast.dump(old_floor) == ast.dump(new_floor)
assert new_floor.lineno == 799
assert isinstance(new_floor.args[1].body, ast.Constant) and new_floor.args[1].body.value == 0.75
assert isinstance(new_floor.args[1].orelse, ast.Constant) and new_floor.args[1].orelse.value == 0.15
print("PASS AST confirms unchanged obsolete dual-mode floor at a2 line", new_floor.lineno)
print("DIAGNOSIS: raw 0.10913950300891884 fails the retained 0.15 cancellation floor. Readiness/response facts alone do not establish unexecuted later status/EOF/schema assertions. No modified test or candidate suite executed by this script.")

descendants = {"TASK-006"}
while True:
    expanded = descendants | {task["id"] for task in tasks if descendants.intersection(task["depends_on"])}
    if expanded == descendants:
        break
    descendants = expanded
descendants.remove("TASK-006")
assert len(descendants) == 23
for task_id in descendants:
    assert task_map[task_id]["status"] != "accepted" and not task_map[task_id]["attempt_ids"]
state = read(".ai/STATE.json")
assert state["generation"] == 33 and not state["active_runs"]
assert sum(task["status"] == "accepted" for task in tasks) == 9
print("PASS generation33, nine accepted, no runtime active_run; 23 descendants fenced", sorted(descendants))
budget_raw = (ROOT / (PLAN + "evidence/recovery/TASK-006-a2-native-invocations-74.txt")).read_bytes()
assert sha(budget_raw) == "138b44d899472f7e8d9b88db5f652ce34e4e815769af6befb6e0c674ae1c74c1"
calls = json.loads(budget_raw)
assert len(calls) == len({call["call_id"] for call in calls}) == 73
assert calls[-1] == {"call_id": "call_k8j0CnC7m99QUnjtTbjyaNnW", "name": "spawn_agent", "task_name": "recovery_006_a2", "model": "gpt-6-astra", "reasoning_effort": "xhigh"}
policy = read(".ai/project/policy.json")
assert (policy["max_review_cycles"], policy["max_rewrites"], policy["max_agent_invocations"]) == (2, 3, 300)
print("PASS whitelist native snapshot", sha(budget_raw), "73 calls + 1 continuing ROOT =74/300, 226 remaining; proposed owner+R1+R2 would reserve77/300,223 remaining; no policy edits")
print("OBSERVED SUBMISSION ONLY", calls[-1], "; recovery rank4, no provider-effective confirmation")
git("diff", "--check", BASE, HEAD)
git("diff", "--check", OWNER + "^", OWNER)
assert git("rev-parse", "HEAD").decode().strip() == CHECKPOINT
assert not git("diff", "HEAD", "--name-only")
for tree, oid in ((TREE, HEAD), (A1_TREE, A1)):
    assert git("rev-parse", "HEAD", cwd=tree).decode().strip() == oid
    assert not git("status", "--porcelain=v1", "--untracked-files=all", cwd=tree)
untracked = git("ls-files", "--others", "--exclude-standard").decode().splitlines()
assert all(path.startswith(STEM) or path == PLAN + "evidence/recovery/TASK-006-a2-native-invocations-74.txt" for path in untracked), untracked
print("PASS final exact-diff whitespace, unchanged ROOT/a1/a2 and allowed recovery-only untracked files; verification performed no source/refs/canonical writes")
