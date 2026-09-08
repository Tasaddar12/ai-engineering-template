"""Read-only TASK-017 recovery verification; writes only same-prefix evidence.

This is a recovery diagnostic, not an implementation/review gate. No candidate
source, historical report, Git index, or canonical workflow record is modified.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
ROOT = Path(__file__).resolve().parents[6]
CANDIDATE = ROOT / ".worktrees/TASK-017-a1"
BUNDLE = ROOT / ".ai/plans/current/PLAN-001"
ROOT_HEAD = "10b408fa0fd43eafa49acc88dec2c5976be05966"
HEAD = "e79df3b8d071a7e3a3c7874cf0cacb6e704c0205"
BASE = "e2faa2b8f3ce8f63119227edd35fa837b82d5ee8"
COMMITS = ["71e0ccf697c132082bb17f7f3814ffb6abee5df6", "7e5bd5fd5d1b36a14cbee6ae911b68a4ec9ffbf8"]
OWNED = [".ai/plans/current/PLAN-001/evidence/implementation/TASK-017.md", "src/agents.py", "tests/unit/agents/test_agents.py"]
REPORT = Path(__file__).with_suffix(".json")
sys.path.insert(0, str(CANDIDATE / "src"))
import agents
import config
import contracts
import domain_values
import workflow_ports


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def git(*args: str, cwd: Path = ROOT) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True, shell=False).stdout


def request() -> workflow_ports.AgentRequest:
    return workflow_ports.AgentRequest(
        id="recovery-request-17", workflow_id="recovery-workflow", run_id="recovery-run",
        attempt_id="TASK-017-a1", task_id="TASK-017", plan_id="PLAN-001",
        spec_refs=(".ai/plans/current/PLAN-001/spec.json",), role="implementer",
        graph_revision=4, base_oid=BASE, current_oid=HEAD, worktree_id="TASK-017-a1",
        scope=domain_values.ScopeClaim(write_paths=("src/agents.py",)),
        context_ref=".ai/context/recovery-17.json", allowed_command_ids=("test.TASK-017",),
        acceptance_criteria=(workflow_ports.AcceptanceCriterion("TASK-017-AC1", "Recover one fake effect", "Fresh processes"),),
        dependency_handoffs=("handoff:TASK-003", "handoff:TASK-004", "handoff:TASK-038"),
        checklist_ids=(), model_profile="implementation", policy_ref=".ai/project/policy.json",
        permission_subset=("edit_scope", "tests"), lease_generation=7,
        idempotency_key="recovery-profile-mapping-17",
    )


def child(project: Path) -> None:
    settings = config.load_project_settings(project, config.load_installation_record(project))
    req = request()
    binding = settings.configured_model(req.model_profile)
    assert binding is not None
    caps = agents.AgentAdapterCapabilities(
        roles=("implementer",), permissions=("edit_scope", "tests"),
        command_ids=("test.TASK-017",), model_profiles=settings.models.provider().profiles,
    )
    state_path = project / "state.json"
    before = state_path.read_bytes() if state_path.exists() else None
    facts = {
        "runtime": platform.python_version(), "pid": os.getpid(),
        "module_origins": {m.__name__: m.__file__ for m in (agents, config, contracts, workflow_ports, domain_values)},
        "loader": "load_installation_record + load_project_settings",
        "requested_policy_profile": req.model_profile, "resolved_provider_profile": binding.name,
        "settings_sha256": sha((project / ".ai/project/policy.json").read_bytes() + (project / ".ai/project/agent-models.json").read_bytes()),
    }
    stage = "provider_restore"
    try:
        provider = agents.FakeAgentProviderState(state_path)
        stage = "adapter_construction"
        adapter = agents.DeterministicFakeAgentAdapter(project_id="recovery-project", settings=settings, capabilities=caps, provider_state=provider)
        stage = "idempotent_start"
        handle = adapter.start(req, req.idempotency_key)
        assert adapter.start(req, req.idempotency_key) == handle
        stage = "queued_poll"
        observed = adapter.poll(handle)
        assert observed.status is domain_values.AgentRunStatus.QUEUED
        facts.update(outcome="admitted", external_handle=handle.external_handle,
                     effect_count=provider.effect_count, poll=observed.status.value,
                     simulated_expected_profile=adapter.expected_model(handle).profile)
    except domain_values.DomainException as exc:
        facts.update(outcome="rejected", stage=stage, category=exc.category.value, message=str(exc))
        assert before == state_path.read_bytes(), "rejection changed persisted bytes"
        facts["rejected_state_bytes_unchanged"] = True
    print(json.dumps(facts, sort_keys=True))


if len(sys.argv) > 1 and sys.argv[1] == "child":
    child(Path(sys.argv[2]))
    raise SystemExit(0)

assert git("rev-parse", "HEAD").decode().strip() == ROOT_HEAD
assert git("rev-parse", "HEAD", cwd=CANDIDATE).decode().strip() == HEAD
assert not git("status", "--porcelain=v1", cwd=CANDIDATE)
assert not git("diff", "--name-only", "HEAD")
assert git("merge-base", BASE, HEAD).decode().strip() == BASE
assert git("merge-base", ROOT_HEAD, HEAD).decode().strip() == BASE
manifest = json.loads((BUNDLE / "reviews/candidates/CANDIDATE-TASK-017-a1-e79df3b8d071.json").read_text())
assert manifest["head_oid"] == HEAD and manifest["base_oid"] == BASE
assert sha(git("diff", "--binary", BASE, HEAD)) == manifest["diff_sha256"]
assert git("diff", "--name-only", BASE, HEAD).decode().splitlines() == OWNED
assert not git("diff", "--check", BASE, HEAD)
assert sha(canonical({k: v for k, v in manifest.items() if k != "fingerprint"})) == manifest["fingerprint"]
for ref in manifest["context_refs"]:
    assert sha(git("show", f'{HEAD}:{ref["path"]}')) == ref["sha256"]
for ref in manifest["validation_refs"]:
    assert sha((ROOT / ref["path"]).read_bytes()) == ref["sha256"]
assert sha((ROOT / ".ai/project/policy.json").read_bytes() + (ROOT / ".ai/project/agent-models.json").read_bytes()) == manifest["policy_model_digest"]

history = {}
review_summaries = []
for cycle, checkpoint in ((1, "10e27db6472bbf6d9a5a5023233ede12fae5d52d"), (2, "8ebe9629f0eb7870933623af87cd10e93677dd4b")):
    for path in sorted((BUNDLE / "reviews").glob(f"TASK-017-a1-c{cycle}-R1*")):
        relative = path.relative_to(ROOT).as_posix()
        assert path.read_bytes() == git("show", f"{checkpoint}:{relative}"), relative
        history[relative] = sha(path.read_bytes())
    review = json.loads((BUNDLE / f"reviews/TASK-017-a1-c{cycle}-R1.json").read_text())
    assert review["verdict"] == "fail" and review["stage"] == "implementation"
    review_summaries.append({"id": review["id"], "verdict": review["verdict"], "findings": [f["id"] for f in review["findings"]], "fingerprint": review["candidate_fingerprint"]})
assert not list((BUNDLE / "reviews").glob("TASK-017-*-R2.json"))

actual_commits = git("rev-list", "--reverse", "--no-merges", f"{ROOT_HEAD}..{HEAD}").decode().splitlines()
assert actual_commits == COMMITS, actual_commits
salvage = []
for commit in COMMITS:
    parents = git("rev-list", "--parents", "-n", "1", commit).decode().split()
    assert len(parents) == 2, "not a single-parent owned commit"
    changed = git("diff", "--name-only", f"{commit}^", commit).decode().splitlines()
    assert changed == OWNED
    salvage.append({"commit": commit, "parent": parents[1], "paths": changed, "patch_sha256": sha(git("diff", "--binary", f"{commit}^", commit))})
for path in OWNED:
    assert not git("ls-tree", ROOT_HEAD, "--", path), ("fresh root owns conflicting path", path)
    assert git("show", f"{COMMITS[0]}:{path}") == git("show", f"{COMMITS[1]}^:{path}"), path
    assert git("show", f"{COMMITS[1]}:{path}") == git("show", f"{HEAD}:{path}"), path
retained = git("branch", "--contains", HEAD, "--format=%(refname)").decode().splitlines()
assert "refs/heads/ai/PLAN-001/TASK-017/a1" in retained

tasks = {p.stem: json.loads(p.read_text()) for p in (BUNDLE / "tasks/current").glob("TASK-*.json")}
graph = json.loads((BUNDLE / "graph.json").read_text())
isolation = json.loads((BUNDLE / "reviews/r4-isolation-review.json").read_text())
task_digest = contracts.structural_task_digest(list(tasks.values()))
assert task_digest == graph["task_set_sha256"] == isolation["task_set_sha256"] == "c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e"
assert graph["revision"] == isolation["graph_revision"] == 4 and isolation["verdict"] == "pass"
assert {n["task_id"]: n["depends_on"] for n in graph["nodes"]} == {k: v["depends_on"] for k, v in tasks.items()}
graph_digest = sha(canonical({k: graph[k] for k in ("schema_version", "kind", "id", "plan_id", "revision", "nodes", "task_set_sha256")}))
assert graph_digest == "5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337"
ancestors: dict[str, set[str]] = {}
def visit(task_id: str, trail: frozenset[str] = frozenset()) -> set[str]:
    assert task_id not in trail, f"cycle at {task_id}"
    if task_id not in ancestors:
        ancestors[task_id] = set()
        for dep in tasks[task_id]["depends_on"]:
            ancestors[task_id].update({dep} | visit(dep, trail | {task_id}))
    return ancestors[task_id]
for task_id in tasks:
    visit(task_id)
descendants = sorted(k for k, v in ancestors.items() if "TASK-017" in v)
assert descendants == [f"TASK-{n:03}" for n in (15, 20, 21, 22, 23, 25, 26, 27, 29, 30, 34, 35, 36, 37)]
assert all(tasks[t]["status"] == "backlog" and not tasks[t]["attempt_ids"] for t in descendants)
assert tasks["TASK-017"]["depends_on"] == ["TASK-003", "TASK-004", "TASK-038"]
assert all(tasks[t]["status"] == "accepted" for t in tasks["TASK-017"]["depends_on"])
assert sum(t["status"] == "accepted" for t in tasks.values()) == 10
state = json.loads((ROOT / ".ai/STATE.json").read_text())
assert state["generation"] == 38 and not state["active_runs"]
dependency_bytes = {}
for path in ("src/workflow_ports.py", "src/contracts.py", "src/config.py", "src/domain_values.py"):
    assert git("show", f"{ROOT_HEAD}:{path}") == git("show", f"{HEAD}:{path}")
    dependency_bytes[path] = sha(git("show", f"{ROOT_HEAD}:{path}"))

budget = {}
for count, expected in ((83, "aa8f04629fea070ac63bc2fbcf938cc4f4821aa3fa5e99251a8170c7324e446b"), (87, "2c1e97bbe540e1271d938ce9e14f5c426535c978b76772ff8c2f263b888cd7c6")):
    path = BUNDLE / f"evidence/recovery/TASK-017-native-invocations-{count}.txt"
    assert sha(path.read_bytes()) == expected
    calls = json.loads(path.read_text())
    assert len(calls) + 1 == count and len({c["call_id"] for c in calls}) == len(calls)
    budget[str(count)] = {"snapshot_sha256": expected, "native_calls": len(calls), "continuing_root": 1, "charged": count}
assert calls[-4]["call_id"] == "call_tYUwxLEP8iuLb3BTPBsGYqRA"
assert calls[-3]["call_id"] == "call_P6pZvnvZ6x4zAY6lvZxp2FUJ"
policy = json.loads((ROOT / ".ai/project/policy.json").read_text())
assert (policy["max_review_cycles"], policy["max_rewrites"], policy["max_agent_invocations"]) == (2, 3, 300)
assert all(not p["configured"] for p in policy["model_profiles"])
budget["current"] = {"charged": 87, "remaining": 213, "proposed_additional_implementation_R1_R2": 3, "charged_plus_reserved": 90, "remaining_after_reservation": 210, "rewrites_used": 3, "rewrites_remaining": 0, "usage_interrupted_recovery_invocation": 84, "recovery_continuation_invocation": 85}

reproductions = {}
with tempfile.TemporaryDirectory(prefix="TASK-017-recovery-assessment-fixture-", dir=REPORT.parent) as temp:
    fixture = Path(temp)
    shutil.copytree(CANDIDATE / "schemas/v1", fixture / "schemas/v1")
    (fixture / ".ai/project").mkdir(parents=True)
    shutil.copyfile(CANDIDATE / ".ai/framework.json", fixture / ".ai/framework.json")
    original_models = json.loads((CANDIDATE / ".ai/project/agent-models.json").read_text())
    original_policy = json.loads((CANDIDATE / ".ai/project/policy.json").read_text())
    for mapped in (False, True):
        models, fixture_policy = copy.deepcopy(original_models), copy.deepcopy(original_policy)
        for provider in models["providers"].values():
            provider["profiles"]["implementation_custom"] = copy.deepcopy(provider["profiles"]["implementation"])
        selected_name = "implementation_custom" if mapped else "implementation"
        models["policy_profile_map"]["implementation"] = selected_name
        selected = models["providers"][models["active_provider"]]["profiles"][selected_name]
        for p in fixture_policy["model_profiles"]:
            if p["name"] == "implementation":
                p.update(configured=True, provider="OpenAI", model_id=selected["model_id"], capability_rank=selected["capability_rank"])
            elif p["name"] == "review_high":
                p["configured"] = True
        (fixture / ".ai/project/agent-models.json").write_bytes(canonical(models))
        (fixture / ".ai/project/policy.json").write_bytes(canonical(fixture_policy))
        (fixture / "state.json").unlink(missing_ok=True)
        results = []
        for _ in range(2):
            run = subprocess.run([sys.executable, "-B", str(Path(__file__)), "child", str(fixture)], cwd=CANDIDATE, capture_output=True, text=True, shell=False)
            assert run.returncode == 0, run.stderr
            results.append(json.loads(run.stdout))
        first, second = results
        assert first["outcome"] == "admitted" and first["effect_count"] == 1
        assert first["settings_sha256"] == second["settings_sha256"]
        if mapped:
            assert second["outcome"] == "rejected" and second["category"] == "validation_failed" and second["stage"] == "provider_restore"
        else:
            assert second["outcome"] == "admitted" and second["effect_count"] == 1 and first["external_handle"] == second["external_handle"]
        reproductions["mapped" if mapped else "identity_control"] = results

assert not git("status", "--porcelain=v1", cwd=CANDIDATE)
assert git("rev-parse", "HEAD").decode().strip() == ROOT_HEAD
assert not git("diff", "--name-only", "HEAD")
for path, digest in history.items():
    assert sha((ROOT / path).read_bytes()) == digest
result = {
    "verified_at_utc": datetime.now(timezone.utc).isoformat(), "role": "independent_recovery_assessment",
    "runtime": {"python": sys.version, "executable": sys.executable, "platform": platform.platform(), "jsonschema": importlib.metadata.version("jsonschema")},
    "root_head": ROOT_HEAD, "candidate_head": HEAD, "review_base": BASE, "candidate_clean": True,
    "candidate_fingerprint": manifest["fingerprint"], "diff_sha256": manifest["diff_sha256"],
    "context_hashes_verified": len(manifest["context_refs"]), "validation_hashes_verified": manifest["validation_refs"],
    "failed_reports": review_summaries, "historical_files_unchanged": history, "R2_reports": 0,
    "salvage": salvage, "salvage_conclusion": "Exactly two owned nonmerge commits, first-parent repair preimages equal original commit blobs, candidate equals repaired blobs, fresh ROOT owns none of the three paths. No cherry-pick executed.",
    "retained_branches": retained, "owned_candidate_hashes": {p: sha(git("show", f"{HEAD}:{p}")) for p in OWNED},
    "graph": {"revision": 4, "structural_graph_sha256": graph_digest, "structural_task_sha256": task_digest, "generation": 38, "accepted": 10, "tasks": 39, "descendants_fenced_backlog_no_attempts": descendants, "accepted_dependencies": tasks["TASK-017"]["depends_on"], "dependency_source_hashes_unchanged": dependency_bytes},
    "budget": budget, "fresh_process_reproductions": reproductions,
    "limitations": "No source patch/cherry-pick or new R1/R2; no broad passing suite/matrix rerun; independently executed only identity and mapped real-loader recovery controls on Windows Python 3.12. Candidate-bound Windows 3.11/Linux 3.11 evidence was read and hash-verified, not newly rerun. Historical rewrite usage is retained ledger/coordinator evidence, not an inference that graph revision alone counts rewrites.",
    "post_checks": "Root/candidate OIDs unchanged, candidate clean, ROOT tracked bytes unchanged, all failed report companions unchanged; temporary fixture removed.",
}
REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"result": "PASS: recovery evidence verified; mapped-profile source defect independently reproduced", "report": str(REPORT), "historical_files_preserved": len(history), "budget_charged": 87, "descendants": descendants, "salvage_commits": COMMITS}, indent=2))
