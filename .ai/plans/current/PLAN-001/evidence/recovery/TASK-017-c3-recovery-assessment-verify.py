"""One independent provenance restart reproduction plus immutable lineage audit.

Assessment evidence only. Does not import or execute historical evidence helpers,
modify product code, or authorize a repair. Run once before the final handoff.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import fields, is_dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
TREE = ROOT / ".worktrees/TASK-017-a2"
OUT = Path(__file__).parent
PREFIX = "TASK-017-c3-recovery-assessment"
PLAN = ".ai/plans/current/PLAN-001"
HEAD = "e054fc9f37a157713d7ff910128dfb2995b597ae"
CANDIDATE = "b7593f11961aa6f5c3a927f3c49af32c4fa93971"
BASE = "b90556d92e0f37e664d685b4af85c43fc8143d81"
sys.path.insert(0, str(TREE / "src"))
import agents
import config
import contracts
import domain_values as dv
import workflow_ports as wp


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str, cwd: Path = ROOT) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          capture_output=True, shell=False).stdout


def wire(value: object) -> object:
    if isinstance(value, dv.ScopePath):
        return value.as_wire()
    if isinstance(value, dv.ScopeClaim):
        return value.to_wire()
    if isinstance(value, (dv.EntityId, dv.PlanId, dv.Revision, dv.Sha256Digest)):
        return value.value
    if isinstance(value, dv.FrozenJsonObject):
        return value.to_dict()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: wire(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, tuple):
        return [wire(v) for v in value]
    return value


def encoded(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def make_fixture(folder: Path) -> None:
    shutil.copytree(TREE / "schemas/v1", folder / "schemas/v1")
    (folder / ".ai/project").mkdir(parents=True)
    shutil.copyfile(TREE / ".ai/framework.json", folder / ".ai/framework.json")
    models = json.loads((TREE / ".ai/project/agent-models.json").read_bytes())
    policy = json.loads((TREE / ".ai/project/policy.json").read_bytes())
    models["active_provider"] = "openai"
    for catalog in models["providers"].values():
        selected = copy.deepcopy(catalog["profiles"]["review_high"])
        selected["model_id"] = "assessment-review-caf\u00e9"
        catalog["profiles"]["assessment_selected_review"] = selected
    models["policy_profile_map"]["review_high"] = "assessment_selected_review"
    for profile in policy["model_profiles"]:
        selected = models["providers"]["openai"]["profiles"][
            models["policy_profile_map"][profile["name"]]]
        profile.update(configured=True, provider="openai",
                       model_id=selected["model_id"],
                       capability_rank=selected["capability_rank"])
    (folder / ".ai/project/policy.json").write_bytes(encoded(policy))
    (folder / ".ai/project/agent-models.json").write_bytes(encoded(models))


def child(folder: Path, phase: str) -> None:
    settings = config.load_project_settings(folder, config.load_installation_record(folder))
    request = wp.AgentRequest(
        id="recovery-c3-request", workflow_id="assessment-workflow", run_id="assessment-run",
        attempt_id="TASK-017-a2", task_id="TASK-017", plan_id="PLAN-001",
        spec_refs=("spec:PLAN-001:SPEC-001",), role="consistency-reviewer", graph_revision=4,
        base_oid=BASE, current_oid=CANDIDATE, worktree_id="TASK-017-a2",
        scope=dv.ScopeClaim(write_paths=("assessment-output.txt",)),
        context_ref="assessment-context", allowed_command_ids=(),
        acceptance_criteria=(wp.AcceptanceCriterion("AC-04", "Preserve exact identity", "Restart"),),
        dependency_handoffs=("handoff:TASK-003", "handoff:TASK-004", "handoff:TASK-038"),
        checklist_ids=("R2-04",), model_profile="review_high", policy_ref=settings.policy_ref,
        permission_subset=("read",), lease_generation=41, idempotency_key="assessment-c3-key")
    registry = contracts.ContractRegistry(TREE / "schemas/v1")
    registry.validate(wire(request))
    state_path = folder / "private-provider.json"
    store = agents.FakeAgentProviderState(state_path)
    api = agents.DeterministicFakeAgentAdapter(
        project_id="assessment-project", settings=settings, provider_state=store,
        capabilities=agents.AgentAdapterCapabilities(
            roles=("consistency-reviewer",), permissions=("read",), command_ids=(),
            model_profiles=settings.models.provider().profiles))
    handle = api.start(request, request.idempotency_key)
    expected = api.expected_model(handle)
    if phase == "first":
        observed = replace(expected, model_id="assessment-review-cafe\u0301")
        assert observed != expected
        output = wp.AgentOutputRecord(
            id="assessment-output", request_id=handle.request_id, attempt_id=handle.attempt_id,
            status=dv.AgentOutputStatus.SUCCEEDED, actual_model=observed,
            artifact_refs=(), command_evidence_refs=(), discoveries=(),
            scope_change_requests=(), error_category=None, summary="Exact provenance control")
        now = datetime(2026, 9, 8, 12, tzinfo=timezone.utc)
        run = wp.AgentRunRecord(
            id="assessment-observed-run", request_ref="agent-request:PLAN-001:recovery-c3-request",
            attempt_id=handle.attempt_id, status=dv.AgentRunStatus.SUCCEEDED,
            adapter_id=handle.adapter_id, external_handle=handle.external_handle,
            actual_model=observed, started_at=now, finished_at=now,
            output_ref="agent-output:PLAN-001:assessment-output", error_category=None,
            lease_generation=handle.lease_generation)
        registry.validate(wire(output))
        registry.validate(wire(run))
        store.script(handle, polls=(wp.AgentObservation(
            dv.AgentRunStatus.SUCCEEDED, handle, run, output,
            (dv.EvidenceRef("assessment-evidence.txt", "6" * 64),)),))
    before = state_path.read_bytes()
    result = {
        "phase": phase, "pid": os.getpid(), "runtime": sys.version,
        "executable": sys.executable,
        "module_origins": {m.__name__: m.__file__ for m in
                           (agents, config, contracts, dv, wp)},
        "settings_sha256": sha((folder / ".ai/project/policy.json").read_bytes()
                               + (folder / ".ai/project/agent-models.json").read_bytes()),
        "handle": handle.external_handle, "effect_count": store.effect_count,
        "requested_profile": request.model_profile,
        "resolved_profile": settings.configured_model(request.model_profile).name,
        "expected_model_id": expected.model_id,
        "saved_script_model_id": json.loads(before)["effects"][0]["poll_script"][0]["run"]["actual_model"]["model_id"],
        "before_sha256": sha(before), "schema_valid_request": True,
    }
    try:
        observation = api.poll(handle)
        result.update(outcome=observation.status.value,
                      returned_model_id=observation.run.actual_model.model_id)
    except dv.DomainException as exc:
        result.update(outcome="rejected", category=exc.category.value, message=str(exc))
    after = state_path.read_bytes()
    result.update(bytes_unchanged=before == after,
                  poll_position=json.loads(after)["effects"][0]["poll_position"],
                  cancel_position=json.loads(after)["effects"][0]["cancel_position"])
    print(json.dumps(result, ensure_ascii=True))


def audit() -> dict[str, object]:
    assert git("rev-parse", "HEAD").decode().strip() == HEAD
    assert git("rev-parse", "HEAD", cwd=TREE).decode().strip() == CANDIDATE
    assert git("status", "--porcelain", cwd=TREE) == b""
    manifest = json.loads((ROOT / PLAN / "reviews/candidates/CANDIDATE-TASK-017-a2-b7593f11961a.json").read_bytes())
    assert git("merge-base", BASE, CANDIDATE).decode().strip() == BASE
    assert sha(git("diff", "--binary", BASE, CANDIDATE)) == manifest["diff_sha256"]
    assert sha(encoded({k: v for k, v in manifest.items() if k != "fingerprint"})) == manifest["fingerprint"]
    for entry in manifest["context_refs"]:
        assert sha(git("show", f'{CANDIDATE}:{entry["path"]}')) == entry["sha256"]
    for entry in manifest["validation_refs"]:
        assert sha((ROOT / entry["path"]).read_bytes()) == entry["sha256"]
    assert sha((ROOT / ".ai/project/policy.json").read_bytes() +
               (ROOT / ".ai/project/agent-models.json").read_bytes()) == manifest["policy_model_digest"]
    historical: dict[str, str] = {}
    checkpoints = {
        "TASK-017-a1-c1-R1": "10e27db6472bbf6d9a5a5023233ede12fae5d52d",
        "TASK-017-a1-c2-R1": "8ebe9629f0eb7870933623af87cd10e93677dd4b",
        "TASK-017-a2-c3-R1": HEAD,
        "TASK-017-a2-c3-R2": "d41cf4d088d744a72930c5e7660362764d99038e",
    }
    for prefix, checkpoint in checkpoints.items():
        for path in sorted((ROOT / PLAN / "reviews").glob(prefix + "*")):
            rel = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            assert data == git("show", f"{checkpoint}:{rel}")
            historical[rel] = sha(data)
        if prefix.endswith(("c3-R1", "c3-R2")):
            final = (ROOT / PLAN / "reviews" / (prefix + "-final.txt")).read_text()
            for name, digest in re.findall(r"SHA256 (\S+): ([0-9a-f]{64})", final):
                assert sha((ROOT / PLAN / "reviews" / name).read_bytes()) == digest
    original = json.loads((OUT / "TASK-017-recovery-assessment-verification.json.txt").read_bytes())
    for rel, digest in original["historical_files_unchanged"].items():
        assert sha((ROOT / rel).read_bytes()) == digest
    preserved_recovery = {}
    for path in sorted(OUT.glob("TASK-017-*")):
        if path.name.startswith(PREFIX) or not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        assert path.read_bytes() == git("show", f"{HEAD}:{rel}")
        preserved_recovery[rel] = sha(path.read_bytes())
    assert sha((OUT / "TASK-017-recovery-assessment.md.txt").read_bytes()) == "64f3b3bfb6a0949efcd9a37741f8f84fc743d24ab751fec3c0c0a01139a83605"
    assert sha((OUT / "TASK-017-recovery-assessment-verification.json.txt").read_bytes()) == "814e4c7c567cba5477b9a91479b34dc3826a57c5df78126dd2ab946f0db0c3f0"
    owned = ["src/agents.py", "tests/unit/agents/test_agents.py",
             PLAN + "/evidence/implementation/TASK-017.md"]
    chain = ["ce1776adb42a06b5a02c7c7e7047e03c8a7f30c2",
             "3cdb41e5698f2cb0c7fc08c36c08d57a28ea1d16",
             "f5e21518f50e96b421ed68175d51acf253053a18"]
    originals = ["71e0ccf697c132082bb17f7f3814ffb6abee5df6",
                 "7e5bd5fd5d1b36a14cbee6ae911b68a4ec9ffbf8"]
    salvage = []
    for index, oid in enumerate(chain):
        parents = git("rev-list", "--parents", "-n", "1", oid).decode().split()[1:]
        assert len(parents) == 1
        if index:
            assert parents[0] == chain[index - 1]
        changed = git("diff-tree", "--no-commit-id", "--name-only", "-r", oid).decode().splitlines()
        assert set(changed) == set(owned)
        patch = git("diff", "--binary", parents[0], oid)
        if index < 2:
            original_patch = git("diff", "--binary", originals[index] + "^", originals[index])
            assert patch == original_patch
        salvage.append({"commit": oid, "parent": parents[0], "paths": changed,
                        "patch_sha256": sha(patch),
                        "original": originals[index] if index < 2 else "a2 mapping correction"})
    for path in owned:
        assert git("show", f"{chain[1]}:{path}") == git("show", f"e79df3b8d071a7e3a3c7874cf0cacb6e704c0205:{path}")
        assert git("show", f"{chain[2]}:{path}") == git("show", f"{CANDIDATE}:{path}")
        assert not git("ls-tree", HEAD, "--", path)
    assert set(git("rev-list", "--reverse", "--no-merges", f"{HEAD}..{CANDIDATE}").decode().split()) == set(chain)
    dependency_sources = ["src/workflow_ports.py", "src/contracts.py", "src/config.py", "src/domain_values.py"]
    for path in dependency_sources:
        assert git("show", f"{HEAD}:{path}") == git("show", f"{CANDIDATE}:{path}")
    tasks = [json.loads(p.read_bytes()) for p in (ROOT / PLAN / "tasks/current").glob("TASK-*.json")]
    graph = json.loads((ROOT / PLAN / "graph.json").read_bytes())
    digest = contracts.structural_task_digest(tasks)
    assert digest == "c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e"
    assert graph["revision"] == 4
    by_id = {task["id"]: task for task in tasks}
    descendants = {"TASK-017"}
    while True:
        grown = descendants | {t["id"] for t in tasks if set(t["depends_on"]) & descendants}
        if grown == descendants:
            break
        descendants = grown
    descendants.remove("TASK-017")
    assert len(descendants) == 14
    assert all(by_id[t]["status"] == "backlog" and not by_id[t]["attempt_ids"] for t in descendants)
    assert all(by_id[t]["status"] == "accepted" for t in ("TASK-003", "TASK-004", "TASK-038"))
    state = json.loads((ROOT / ".ai/STATE.json").read_bytes())
    assert state["generation"] == 41 and state["active_runs"] == []
    assert sum(t["status"] == "accepted" for t in tasks) == 10
    # Only manifests/records for 017 and accepted contracts are inspected; 007 source/reviews are excluded.
    relevant = [".ai/STATE.json", ".ai/project/policy.json", ".ai/project/agent-models.json",
                PLAN + "/plan.json", PLAN + "/spec.json", PLAN + "/graph.json",
                PLAN + "/tasks/current/TASK-017.json", *dependency_sources,
                *historical, *preserved_recovery]
    return {"root_head": HEAD, "candidate_head": CANDIDATE, "base": BASE,
            "candidate_clean": True, "fingerprint": manifest["fingerprint"],
            "diff_sha256": manifest["diff_sha256"], "contexts_verified": 14,
            "validation_refs_verified": manifest["validation_refs"],
            "historical_files": historical, "preserved_recovery": preserved_recovery,
            "salvage": salvage, "owned_blobs": {p: sha(git("show", f"{CANDIDATE}:{p}")) for p in owned},
            "retained_branches": {oid: git("branch", "--contains", oid).decode().splitlines()
                                  for oid in (CANDIDATE, "e79df3b8d071a7e3a3c7874cf0cacb6e704c0205")},
            "structural_task_digest": digest, "graph": graph,
            "generation": 41, "accepted": "10/39", "active_runs": [],
            "descendants_fenced": sorted(descendants),
            "relevant_snapshot": {p: sha((ROOT / p).read_bytes()) for p in relevant}}


def main() -> None:
    report = audit()
    report["assessed_at"] = datetime.now(timezone.utc).isoformat()
    report["runtime"] = {"python": sys.version, "executable": sys.executable, "platform": platform.platform()}
    report["native_invocation"] = {"call_id": "call_eZzyti7aTEGoUlIDbA6ciTXC", "charge": 93,
                                   "limit": 300, "remaining": 207,
                                   "selected_model": "gpt-6-astra", "selected_effort": "xhigh",
                                   "provider_effective_identity": None}
    with tempfile.TemporaryDirectory(prefix=PREFIX + "-fixture-", dir=OUT) as tmp:
        folder = Path(tmp)
        make_fixture(folder)
        rows = []
        for phase in ("first", "reopened"):
            run = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                                  "--child", str(folder), phase], cwd=TREE,
                                 capture_output=True, text=True, check=True, shell=False)
            rows.append(json.loads(run.stdout))
        assert rows[0]["pid"] != rows[1]["pid"]
        assert rows[0]["settings_sha256"] == rows[1]["settings_sha256"]
        assert rows[0]["handle"] == rows[1]["handle"]
        assert rows[0]["outcome"] == "rejected" and rows[0]["category"] == "validation_failed"
        assert rows[0]["bytes_unchanged"] and rows[0]["poll_position"] == 0
        assert rows[1]["outcome"] == "succeeded" and rows[1]["poll_position"] == 1
        assert rows[0]["before_sha256"] == rows[1]["before_sha256"]
        for row in rows:
            assert row["effect_count"] == 1
            assert all(Path(p).resolve().parent == (TREE / "src").resolve()
                       for p in row["module_origins"].values())
        report["independent_reproduction"] = rows
    for path, digest in report["relevant_snapshot"].items():
        assert sha((ROOT / path).read_bytes()) == digest
    assert git("rev-parse", "HEAD").decode().strip() == HEAD
    assert git("status", "--porcelain", cwd=TREE) == b""
    report["post_checks"] = "Identities and relevant bytes unchanged; fixture removed; no prior generator run."
    (OUT / (PREFIX + "-verification.json.txt")).write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print("Verified identities, 42 immutable review companions, recovery packaging, exact three-commit salvage, and 14 fenced descendants.")
    print("One independent two-process reproduction: invalid unconsumed model rejects with cursor 0; unchanged saved bytes reopen and poll succeeds with normalized model/cursor 1.")
    print("Exit 0 captures the defect; it is not a task acceptance pass.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child(Path(sys.argv[2]), sys.argv[3])
    else:
        main()
