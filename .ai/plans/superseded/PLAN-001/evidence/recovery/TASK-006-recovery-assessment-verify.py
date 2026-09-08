"""Read-only verification for the bounded TASK-006 recovery assessment."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[6]
TREE = ROOT / ".worktrees/TASK-006-a1"
PLAN = ".ai/plans/current/PLAN-001/"
CHECKPOINT = "a31474b0927bf85895ec44ef9695bb3a14e05605"
HEAD = "ce4c8edb86b02268a856a5f870932ade0e7e9b91"
BASE = "3acfcb0d700b05fbf78233b575e77db556cd9bcc"
sys.path.insert(0, str(TREE / "src"))
from contracts import ContractRegistry, structural_task_digest


def git(*args, cwd=ROOT):
    return subprocess.check_output(
        ["git", *args], cwd=cwd,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path, root=ROOT):
    return json.loads((root / path).read_bytes())


assert git("rev-parse", "HEAD").decode().strip() == CHECKPOINT
assert git("rev-parse", "HEAD", cwd=TREE).decode().strip() == HEAD
assert git("rev-parse", "ai/PLAN-001/TASK-006/a1").decode().strip() == HEAD
assert not git("status", "--porcelain=v1", "--untracked-files=all", cwd=TREE)
assert not git("diff", "HEAD", "--name-only")
git("merge-base", "--is-ancestor", BASE, CHECKPOINT)
assert git("merge-base", BASE, HEAD).decode().strip() == BASE
git("merge-base", "--is-ancestor", "64a48f6bde98f5a09db25ca8ae3e8fd3798ba4d1", HEAD)
print("PASS ROOT checkpoint, retained clean a1 branch/head, base and failed-c1 ancestry:", CHECKPOINT, HEAD, BASE)

ref = PLAN + "reviews/candidates/CANDIDATE-TASK-006-a1-ce4c8edb86b0.json"
candidate = read(ref)
registry = ContractRegistry(TREE / "schemas/v1")
registry.validate(candidate)
assert candidate["head_oid"] == HEAD and candidate["base_oid"] == BASE
diff = git("diff", "--binary", BASE, HEAD)
assert sha(diff) == candidate["diff_sha256"]
paths = git("diff", "--name-only", BASE, HEAD).decode().splitlines()
assert set(paths) == {"src/commands.py", "tests/unit/commands/test_commands.py", PLAN + "evidence/implementation/TASK-006.md"}
print("PASS raw binary diff", sha(diff), "owned paths", paths)
production = git("show", HEAD + ":src/commands.py")
assert production == (TREE / "src/commands.py").read_bytes()
assert not git("ls-tree", "--name-only", CHECKPOINT, "src/commands.py")
blob = git("rev-parse", HEAD + ":src/commands.py").decode().strip()
assert blob == "39828108eb7d198d81d810c8fd9e136e3f64f8f0"
print("Production preservation anchors: raw SHA256", sha(production), "Git blob", blob, "; ROOT source absent")
salvage = git("log", "--format=%H", "--reverse", "e9bb424e9fadaa1845b5f5b146cbb4c576b7b10f.." + HEAD, "--", "src/commands.py", "tests/unit/commands/test_commands.py", PLAN + "evidence/implementation/TASK-006.md").decode().splitlines()
assert salvage == ["c3c2ba21c6441abde52f6e340b29d0bf65910f8e", "86bc27af026d8b7b00303fa6d62b12218e0947b8", "530cd085166ab51e2814486f4967ab52203375c2"]
print("PASS retained ordered unaccepted source salvage commits", salvage)
for item in candidate["context_refs"]:
    assert sha(git("show", HEAD + ":" + item["path"])) == item["sha256"]
for item in candidate["validation_refs"]:
    assert sha((ROOT / item["path"]).read_bytes()) == item["sha256"]
print("PASS all", len(candidate["context_refs"]), "committed context hashes and", len(candidate["validation_refs"]), "retained validation hashes; no tests rerun")
canonical = {k: v for k, v in candidate.items() if k != "fingerprint"}
assert sha(json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()) == candidate["fingerprint"]
print("PASS candidate fingerprint", candidate["fingerprint"])
assert sha((ROOT / ".ai/project/policy.json").read_bytes() + (ROOT / ".ai/project/agent-models.json").read_bytes()) == candidate["policy_model_digest"]
for path in (".ai/project/policy.json", ".ai/project/agent-models.json", ".ai/shared/architecture/service-contracts.md", PLAN + "graph.json", PLAN + "spec.json", PLAN + "plan.json"):
    assert git("show", HEAD + ":" + path) == git("show", CHECKPOINT + ":" + path)
print("PASS policy/model digest and unchanged graph/spec/plan/frozen service contract")

tasks = [read(str(path.relative_to(ROOT))) for path in sorted((ROOT / (PLAN + "tasks/current")).glob("TASK-*.json"))]
task_map = {task["id"]: task for task in tasks}
graph = read(PLAN + "graph.json")
isolation = read(PLAN + "reviews/r4-isolation-review.json")
digest = structural_task_digest(tasks)
assert len(tasks) == 39 and graph["revision"] == isolation["graph_revision"] == 4
assert graph["status"] == "approved" and isolation["verdict"] == "pass"
assert digest == graph["task_set_sha256"] == isolation["task_set_sha256"]
assert structural_task_digest([task_map["TASK-006"]]) == structural_task_digest([read(PLAN + "tasks/current/TASK-006.json", TREE)])
print("PASS r4 / 39-task structural digest and unchanged TASK-006 structure", digest)
for task_id, oid, source in (
    ("TASK-002", "460ab567d01912167557f2f671ed07c63f0a31e7", "src/local_ports.py"),
    ("TASK-004", "e3c1177f993ee74815639a83ef3333faa4ba3957", "src/contracts.py"),
    ("TASK-038", "6f2b12c3283ed7d6e3d4876020fe690c6e0061a3", "src/config.py"),
):
    assert task_map[task_id]["status"] == "accepted"
    git("merge-base", "--is-ancestor", oid, BASE)
    for path in (source, PLAN + "evidence/implementation/" + task_id + ".md"):
        assert git("show", oid + ":" + path) == git("show", HEAD + ":" + path) == git("show", CHECKPOINT + ":" + path)
    print("PASS accepted dependency ancestry/source/handoff", task_id, oid)

for suffix, verdict in (("c1-R1", "fail"), ("c2-R1", "pass"), ("c2-R2", "fail")):
    path = PLAN + "reviews/TASK-006-a1-" + suffix + ".json"
    report = read(path)
    registry.validate(report)
    assert report["verdict"] == verdict
    if suffix != "c1-R1":
        assert report["candidate_fingerprint"] == candidate["fingerprint"]
    print("PASS report schema, verdict, committed SHA256", suffix, verdict, sha((ROOT / path).read_bytes()))
preserved = git("ls-tree", "-r", "--name-only", CHECKPOINT, "--", PLAN + "reviews", PLAN + "evidence/validation").decode().splitlines()
preserved = [path for path in preserved if "TASK-006" in Path(path).name]
for path in preserved:
    assert (ROOT / path).read_bytes() == git("show", CHECKPOINT + ":" + path), path
print("PASS preserved TASK-006 review/candidate/validation companion bytes", len(preserved))
assert not list((ROOT / (PLAN + "reviews")).glob("TASK-006-a1-c1-R2.*"))
descendants = {"TASK-006"}
while True:
    expanded = descendants | {task["id"] for task in tasks if descendants.intersection(task["depends_on"])}
    if expanded == descendants:
        break
    descendants = expanded
descendants.remove("TASK-006")
for task_id in descendants:
    assert task_map[task_id]["status"] != "accepted" and not task_map[task_id]["attempt_ids"]
assert not read(".ai/STATE.json")["active_runs"]
print("PASS", len(descendants), "descendants unaccepted with no attempt IDs:", sorted(descendants))
print("PASS no c1 R2 report, no active runtime run identity")
budget_path = PLAN + "evidence/recovery/TASK-006-native-invocations-69.txt"
budget_raw = (ROOT / budget_path).read_bytes()
calls = json.loads(budget_raw)
assert len(calls) == 68 and len({call["call_id"] for call in calls}) == 68
assert sha(budget_raw) == "99e0185db75a00af417851078cdc41da27337362a96a2a3c688329d17837c567"
assert calls[-1]["task_name"] == "recovery_006"
assert calls[-1]["model"] == "gpt-6-astra" and calls[-1]["reasoning_effort"] == "xhigh"
print("PASS coordinator native snapshot", sha(budget_raw), "68 calls + 1 continuing coordinator = 69/300; reserve 3 = 72/300")
print("Native submission record only; provider-returned effective model/effort unavailable:", calls[-1])
git("diff", "--check", BASE, HEAD)
assert not git("status", "--porcelain=v1", "--untracked-files=all", cwd=TREE)
print("PASS final candidate diff whitespace and clean worktree; recovery verification performed no writes")
