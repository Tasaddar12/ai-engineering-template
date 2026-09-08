"""Focused independent c2 review diagnostics; writes only this review prefix.

Run from the frozen candidate. --closing checks the finished review and all
candidate evidence without repeating behavior tests or historical writers.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
CANDIDATE = Path.cwd().resolve()
ROOT = CANDIDATE.parents[1]
PREFIX = ".ai/plans/current/PLAN-001/reviews/TASK-024-a1-c2-R1"
MANIFEST = ".ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-024-a1-58cc78312451.json"
BASE = "8becdc7218d6292ed7d97371d2859783d6d4a097"
HEAD = "58cc78312451d7954a4c29b6ba85b6ceec353171"
OWNER = "e3770010b6a7d56deda3c851ed6458a8a53d3091"
OLD = "8805c35ec655ac5c1a8fef24ede1fec1e2bb7129"
PRESERVED = "476b878b51beed2b02a2bd3d41030ea576922661"
sys.path[:0] = [str(CANDIDATE / "src"), str(CANDIDATE / "tests/unit/planning_recovery_proposals")]
import contracts
import domain_values
import orchestration_ports
import plan_graph
import recovery_proposals
import scope
import workflow_ports
from domain_values import EntityId, GraphStatus, PlanId, RecoveryStatus, Revision, ScopeClaim, Sha256Digest
from orchestration_ports import AcceptanceMapping, GitFacts, RecoveryAction, RecoveryRecord, RecoveryRequest
from plan_graph import AcceptedDependency
from recovery_proposals import RecoveryProposalInput, RecoveryScopeAuthority, TaskSuccessorMapping, validate_recovery_proposal
from test_recovery_proposals import ProposalFactory, budget, criterion, evidence, graph_record, review_histories, task_contract, task_record, verified
from workflow_ports import ContentRef

REGISTRY = contracts.load_contract_registry(CANDIDATE / "schemas/v1")
FACTORY = ProposalFactory(REGISTRY)
RESULTS: dict[str, object] = {"started_at": datetime.now(timezone.utc).isoformat(), "head": HEAD, "base": BASE, "checks": []}


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str, cwd: Path = CANDIDATE) -> bytes:
    return subprocess.check_output(["git", *args], cwd=cwd, shell=False)


def check(name: str, operation) -> object:
    try:
        detail = operation()
        RESULTS["checks"].append({"name": name, "status": "pass", "detail": detail})
        return detail
    except Exception:
        RESULTS["checks"].append({"name": name, "status": "fail", "traceback": traceback.format_exc()})
        return None


def identity() -> dict[str, object]:
    manifest = json.loads((ROOT / MANIFEST).read_bytes())
    assert git("rev-parse", "HEAD", cwd=ROOT).decode().strip() == manifest["base_oid"] == BASE
    assert git("rev-parse", "HEAD").decode().strip() == manifest["head_oid"] == HEAD
    assert not git("status", "--porcelain")
    assert not git("diff", "--check", BASE, HEAD)
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE, HEAD], cwd=CANDIDATE, check=True, shell=False)
    assert sha(git("diff", "--binary", BASE, HEAD)) == manifest["diff_sha256"]
    changed = git("diff", "--name-status", "-M", BASE, HEAD).decode().splitlines()
    owned = [".ai/plans/current/PLAN-001/evidence/implementation/TASK-024.md", "src/recovery_proposals.py", "tests/unit/planning_recovery_proposals/test_recovery_proposals.py"]
    assert changed == ["A\t" + path for path in owned]
    hashes = {}
    root_context_hashes = {}
    for ref in manifest["context_refs"]:
        committed = git("show", HEAD + ":" + ref["path"])
        assert sha(committed) == ref["sha256"]
        root_bytes = (ROOT / ref["path"]).read_bytes()
        assert root_bytes.replace(b"\r\n", b"\n") == committed.replace(b"\r\n", b"\n"), ref["path"]
        assert (CANDIDATE / ref["path"]).read_bytes() == committed
        hashes[ref["path"]] = ref["sha256"]
        root_context_hashes[ref["path"]] = sha(root_bytes)
    for ref in manifest["validation_refs"]:
        assert sha((ROOT / ref["path"]).read_bytes()) == ref["sha256"]
        hashes[ref["path"]] = ref["sha256"]
    policy = (ROOT / ".ai/project/policy.json").read_bytes()
    models = (ROOT / ".ai/project/agent-models.json").read_bytes()
    assert sha(policy + models) == manifest["policy_model_digest"]
    assert sha(canonical({k: v for k, v in manifest.items() if k != "fingerprint"})) == manifest["fingerprint"] == "8f2ba197a56ab71a60729dc62f23fde758f305bb70759b55e33d35369816083d"
    dependencies = {"TASK-013": ("a089594df19d33250a6218126a6a3fea83ce49f8", "src/plan_graph.py"), "TASK-014": ("d6d3e6f94dd355994fb82d8e6a0c1c2546b6c3a3", "src/scope.py"), "TASK-039": ("bc8a5f47d8e1a66bc2b8929b099349cb199c0100", "src/orchestration_ports.py")}
    blobs = {}
    for path in owned:
        value = git("show", HEAD + ":" + path)
        assert value == git("show", OWNER + ":" + path) == (CANDIDATE / path).read_bytes()
        blobs[path] = sha(value)
    for task_id, (accepted, path) in dependencies.items():
        subprocess.run(["git", "merge-base", "--is-ancestor", accepted, BASE], cwd=CANDIDATE, check=True, shell=False)
        task = json.loads(next((CANDIDATE / ".ai/plans/current/PLAN-001/tasks").glob("*/" + task_id + ".json")).read_bytes())
        assert task["status"] == "accepted"
        value = git("show", HEAD + ":" + path)
        assert value == git("show", accepted + ":" + path) == git("show", OLD + ":" + path) == git("show", OWNER + ":" + path)
        blobs[path] = sha(value)
    for path in ["src/domain_values.py", "src/contracts.py", "src/workflow_ports.py"]:
        value = git("show", HEAD + ":" + path)
        assert value == git("show", OLD + ":" + path) == git("show", OWNER + ":" + path)
        blobs[path] = sha(value)
    retained = {}
    for path in sorted((ROOT / ".ai/plans/current/PLAN-001/reviews").glob("TASK-024-a1-c1-R1*")):
        value = path.read_bytes()
        historical_commit = git("show", PRESERVED + ":" + path.relative_to(ROOT).as_posix())
        assert value.replace(b"\r\n", b"\n") == historical_commit.replace(b"\r\n", b"\n")
        retained[path.name] = sha(value)
    plan = json.loads((CANDIDATE / ".ai/plans/current/PLAN-001/plan.json").read_bytes())
    wire = json.loads((CANDIDATE / plan["graph_ref"]).read_bytes())
    records = [json.loads(next((CANDIDATE / ".ai/plans/current/PLAN-001/tasks").glob("*/" + task + ".json")).read_bytes()) for task in plan["task_ids"]]
    isolation = json.loads((CANDIDATE / plan["isolation_review_ref"]).read_bytes())
    assert len(records) == 39 and wire["revision"] == isolation["graph_revision"] == 4 and isolation["verdict"] == "pass"
    assert contracts.structural_task_digest(records) == wire["task_set_sha256"] == isolation["task_set_sha256"] == "c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e"
    graph_sha = sha(canonical({k: wire[k] for k in ("schema_version", "kind", "id", "plan_id", "revision", "nodes", "task_set_sha256")}))
    assert graph_sha == "5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337"
    origins = {}
    for module in (contracts, domain_values, orchestration_ports, plan_graph, recovery_proposals, scope, workflow_ports):
        assert Path(module.__file__).resolve().is_relative_to(CANDIDATE / "src")
        origins[module.__name__] = module.__file__
    return {"fingerprint": manifest["fingerprint"], "diff_sha256": manifest["diff_sha256"], "context_and_validation_hashes": hashes, "root_context_raw_hashes": root_context_hashes, "root_EOL_note": "ROOT working copies may use CRLF; candidate and manifest bind exact committed LF bytes. ROOT content matches after only CRLF normalization.", "policy_model_digest": manifest["policy_model_digest"], "changed_paths": changed, "source_and_owned_sha256": blobs, "c1_preserved_sha256": retained, "graph_structural_sha256": graph_sha, "task_set_sha256": wire["task_set_sha256"], "origins": origins, "root_status": git("status", "--porcelain", cwd=ROOT).decode()}


def observe(name: str, proposal: RecoveryProposalInput, expected: set[str] = frozenset()) -> object:
    before = repr(proposal)
    result = validate_recovery_proposal(proposal, registry=REGISTRY)
    codes = {str(item.details["code"]) for item in result.issues}
    assert codes == expected, (name, codes, expected, [item.message for item in result.issues])
    assert result.admissible == (not expected)
    assert result.requires_isolation_review == result.admissible
    assert repr(proposal) == before
    assert proposal.record.status is RecoveryStatus.PROPOSED
    assert proposal.record.isolation_review_ref is None
    return {"admissible": result.admissible, "issues": sorted(codes), "requires_isolation_review": result.requires_isolation_review}


def mutate_tasks(proposal: RecoveryProposalInput, records: list[dict], *, current: bool = False) -> RecoveryProposalInput:
    snapshots = tuple(verified(record) for record in records)
    typed = tuple(task_contract(record, snap) for record, snap in zip(records, snapshots, strict=True))
    previous = proposal.request.graph if current else proposal.proposed_graph
    graph = graph_record(records, revision=previous.revision.value, status=previous.status, review_ref=previous.review_ref, plan_id=previous.plan_id.value)
    if current:
        return replace(proposal, current_task_records=snapshots, request=replace(proposal.request, tasks=typed, graph=graph))
    return replace(proposal, proposed_task_records=snapshots, proposed_task_contracts=typed, proposed_graph=graph)


def actual_augment() -> RecoveryProposalInput:
    plan = json.loads((CANDIDATE / ".ai/plans/current/PLAN-001/plan.json").read_bytes())
    wire = json.loads((CANDIDATE / plan["graph_ref"]).read_bytes())
    records = [json.loads(next((CANDIDATE / ".ai/plans/current/PLAN-001/tasks").glob("*/" + task + ".json")).read_bytes()) for task in plan["task_ids"]]
    source = next(item for item in records if item["id"] == "TASK-024")
    fresh = deepcopy(source)
    fresh.update(id="TASK-100", title="Recovery acceptance follow-up", objective="Preserve recovery acceptance", status="backlog", depends_on=["TASK-024"], attempt_ids=[], superseded_by=[], resume_state=None)
    fresh["scope"] = {"write_paths": ["src/recovery_proposal_acceptance.py"], "read_paths": [], "prohibited_paths": source["scope"]["prohibited_paths"], "resources": ["component:planning/recovery_proposal_acceptance"]}
    proposed = records + [fresh]
    next_plan = deepcopy(plan)
    next_plan["task_ids"].append("TASK-100")
    original_snaps = tuple(verified(item) for item in records)
    proposed_snaps = original_snaps + (verified(fresh),)
    old_graph = graph_record(records, revision=4, status=GraphStatus.APPROVED, review_ref=wire["review_ref"], plan_id="PLAN-001")
    new_graph = graph_record(proposed, revision=5, status=GraphStatus.PROPOSED, review_ref=None, plan_id="PLAN-001")
    old_ref = verified(wire, ".ai/plans/current/PLAN-001/history/r4/graph.json").content_ref
    new_wire = deepcopy(wire)
    new_wire.update(id="PLAN-001-r5", revision=5, status="proposed", review_ref=None, nodes=[{"task_id": r["id"], "depends_on": r["depends_on"]} for r in proposed], task_set_sha256=new_graph.task_set_sha256.value)
    new_ref = verified(new_wire, ".ai/plans/current/PLAN-001/graph.json").content_ref
    ids = [item["id"] for item in source["acceptance_criteria"]]
    request = RecoveryRequest(EntityId("project-c2"), PlanId("PLAN-001"), EntityId("run-c2"), EntityId("operation-c2"), EntityId("request-c2"), Revision(50), "Required local recovery follow-up", (EntityId("TASK-024"),), old_graph, tuple(task_contract(r, s) for r, s in zip(records, original_snaps)), tuple(AcceptanceMapping(i, (EntityId("TASK-024"),)) for i in ids), (), (), budget(), GitFacts((), (), (), (evidence(),)), ("local_execute",), (evidence(),))
    record = RecoveryRecord(EntityId("RECOVERY-C2"), request.plan_id, request.run_id, request.trigger, request.failed_task_ids, (), old_ref.path, new_ref.path, RecoveryAction.AUGMENT, (EntityId("TASK-100"),), (), tuple(AcceptanceMapping(i, (EntityId("TASK-100"),)) for i in ids), "Preserve the same product success criteria", (), RecoveryStatus.PROPOSED, None, 2)
    authority = RecoveryScopeAuthority(request.plan_id, ScopeClaim(write_paths=("src/recovery_proposal_acceptance.py",), read_paths=("docs/", "product-reference/"), prohibited_paths=source["scope"]["prohibited_paths"], resources=("component:planning/recovery_proposal_acceptance",)))
    return RecoveryProposalInput(request, record, verified(plan, ".ai/plans/current/PLAN-001/plan.json"), verified(next_plan, ".ai/plans/current/PLAN-001/proposed-plan.json"), old_ref, new_graph, new_ref, original_snaps, proposed_snaps, tuple(task_contract(r, s) for r, s in zip(proposed, proposed_snaps)), (), authority, (TaskSuccessorMapping("TASK-024", ("TASK-100",), ("TASK-100",)),), request.permission_subset, request.lineage_budget)


def controls() -> None:
    actual = actual_augment()
    check("F1 actual r4 fresh exact path and resource in unchanged product authority", lambda: observe("actual", actual))
    assert len(actual.proposed_graph.nodes) == 40
    for name, field, value, expected in (
        ("F1 unauthorized exact path", "write_paths", ["src/unowned.py"], {"product_scope_expansion"}),
        ("F1 unauthorized resource", "resources", ["external:production"], {"product_scope_expansion"}),
        ("F1 authorized read scope", "read_paths", ["product-reference/recovery.md"], set()),
        ("F1 authorized read still requires whole-graph ordering", "read_paths", ["docs/recovery.md"], {"unsequenced_scope_conflict"}),
        ("F1 unauthorized read scope", "read_paths", ["secrets/value.txt"], {"product_scope_expansion"}),
        ("F1 normalized resource alias", "resources", ["COMPONENT:PLANNING/RECOVERY_PROPOSAL_ACCEPTANCE"], set()),
    ):
        records = [s.to_record() for s in actual.proposed_task_records]
        records[-1]["scope"][field] = value
        proposal = mutate_tasks(actual, records)
        check(name, lambda p=proposal, e=expected: observe(name, p, e))
    check("F1 foreign plan authority", lambda: observe("foreign", replace(actual, scope_authority=replace(actual.scope_authority, plan_id=PlanId("PLAN-999"))), {"scope_authority_plan_mismatch"}))
    check("F1 external permission expansion", lambda: observe("permission", replace(actual, proposed_permission_subset=("local_execute", "remote_publish")), {"permission_expansion"}))
    source = task_record("TASK-100", write_paths=["work/source/"], resources=[], criteria=[criterion("TASK-100-AC1"), criterion("TASK-100-AC2")])
    dependent = task_record("TASK-200", depends_on=["TASK-100"], resources=[], status="backlog")
    first = task_record("TASK-300", write_paths=["work/reassigned/first.py"], resources=[], criteria=[criterion("TASK-100-AC1")], status="backlog")
    last = task_record("TASK-301", depends_on=["TASK-300"], write_paths=["work/reassigned/last.py"], resources=[], criteria=[criterion("TASK-100-AC2")], status="backlog")
    def split(targets: tuple[str, ...], successor_records=None) -> RecoveryProposalInput:
        redirected = deepcopy(dependent)
        redirected["depends_on"] = list(targets)
        successors = successor_records or [first, last]
        return FACTORY.make(RecoveryAction.SPLIT, [source, dependent], successors + [redirected], (TaskSuccessorMapping("TASK-100", tuple(r["id"] for r in successors), targets),), target_by_acceptance={"TASK-100-AC1": ("TASK-300",), "TASK-100-AC2": ("TASK-301",)})
    early = split(("TASK-300",))
    terminal = split(("TASK-301",))
    check("F2 early exit rejects", lambda: observe("early", early, {"incomplete_dependency_exit_set"}))
    check("F2 terminal exit admits", lambda: observe("terminal", terminal))
    def frontier(p, integrated):
        result = validate_recovery_proposal(p, registry=REGISTRY)
        refs = {node.task.local_id.value: node.task for node in result.proposed_graph.nodes}
        return sorted(node.task.local_id.value for node in result.proposed_graph.ready_frontier(tuple(AcceptedDependency(refs[i], "a" * 40) for i in integrated)))
    def readiness():
        assert frontier(early, ["TASK-300"]) == ["TASK-200", "TASK-301"]
        assert frontier(terminal, ["TASK-300"]) == ["TASK-301"]
        assert frontier(terminal, ["TASK-300", "TASK-301"]) == ["TASK-200"]
        return {"rejected_early_after_first": frontier(early, ["TASK-300"]), "admitted_terminal_after_first": frontier(terminal, ["TASK-300"]), "admitted_terminal_after_both": frontier(terminal, ["TASK-300", "TASK-301"])}
    check("F2 actual TASK-013 readiness", readiness)
    branch = deepcopy(last)
    branch["depends_on"] = []
    multi = split(("TASK-300", "TASK-301"), [first, branch])
    check("F2 multiple independent exits", lambda: observe("multi", multi))
    check("F2 independent missing exit", lambda: observe("missing", split(("TASK-300",), [first, branch]), {"incomplete_dependency_exit_set"}))
    middle = task_record("TASK-302", depends_on=["TASK-300"], write_paths=["work/reassigned/middle.py"], resources=[], status="backlog")
    transitive_last = deepcopy(last)
    transitive_last["depends_on"] = ["TASK-302"]
    check("F2 transitive successor exit coverage", lambda: observe("transitive", split(("TASK-301",), [first, middle, transitive_last])))
    conflict_last = deepcopy(branch)
    conflict_last["scope"]["write_paths"] = first["scope"]["write_paths"]
    check("F1 whole graph unsequenced conflicts remain rejected", lambda: observe("conflict", split(("TASK-300", "TASK-301"), [first, conflict_last]), {"unsequenced_scope_conflict"}))
    prohibited = deepcopy(first)
    prohibited["scope"]["write_paths"] = ["private/fresh.py"]
    prohibited["scope"]["prohibited_paths"] = []
    for label, authority_prohibitions in (("source", ()), ("authority and source", ("private/",))):
        p = split(("TASK-301",), [prohibited, last])
        p = replace(p, scope_authority=RecoveryScopeAuthority(p.request.plan_id, ScopeClaim(write_paths=("work/", "private/"), prohibited_paths=authority_prohibitions)))
        check("F1 inherited prohibition " + label, lambda p=p: observe("prohibition", p, {"product_scope_expansion"}))
    follow = task_record("TASK-300", depends_on=["TASK-100"], write_paths=["work/follow.py"], resources=[], criteria=deepcopy(source["acceptance_criteria"]))
    history = (verified(task_record("TASK-250", status="superseded")),)
    augmented = FACTORY.make(RecoveryAction.AUGMENT, [source], [source, follow], (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),), historical=history, target_by_acceptance={c["id"]: ("TASK-300",) for c in source["acceptance_criteria"]})
    check("F3 first augment", lambda: observe("augment", augmented))
    replacement = deepcopy(follow)
    replacement["id"] = "TASK-400"
    cumulative = budget(used_rewrites=2, used_agent_invocations=27, elapsed_seconds=500, used_tokens=19000)
    next_p = FACTORY.make(RecoveryAction.REPLACE, [source, follow], [source, replacement], (TaskSuccessorMapping("TASK-300", ("TASK-400",), ("TASK-400",)),), failed_task_id="TASK-300", historical=history, current_budget=cumulative, target_by_acceptance={c["id"]: ("TASK-400",) for c in source["acceptance_criteria"]})
    r1, r2 = review_histories()
    next_p = replace(next_p, request=replace(next_p.request, graph=replace(augmented.proposed_graph, status=GraphStatus.APPROVED, review_ref="evidence/approved-r2.json"), review_1_history=r1, review_2_history=r2), proposed_graph=replace(next_p.proposed_graph, id=EntityId("PLAN-900-r3"), revision=Revision(3)))
    check("F3 admitted augment then replace", lambda: observe("replace", next_p))
    def preserved_lineage():
        result = validate_recovery_proposal(next_p, registry=REGISTRY)
        assert next_p.request.lineage_budget == next_p.proposed_lineage_budget == cumulative
        assert next_p.request.review_1_history == r1 and next_p.request.review_2_history == r2
        assert result.retained_task_history == history + (next_p.current_task_records[1],)
        assert next_p.scope_authority == augmented.scope_authority
        assert next_p.request.permission_subset == next_p.proposed_permission_subset == augmented.request.permission_subset
        assert next_p.record.lineage_rewrite_count == 3
        return {"rewrite_ordinal": 3, "budget": repr(cumulative), "history_ids": [s.record["id"] for s in result.retained_task_history], "R1_history_count": len(r1), "R2_history_count": len(r2), "permissions": next_p.proposed_permission_subset}
    check("F3 cumulative immutable histories and authority", preserved_lineage)
    missing = tuple(AcceptanceMapping(item.original_id, (EntityId("TASK-999"),)) for item in next_p.request.original_acceptance_mapping)
    check("F3 missing mapped owners", lambda: observe("missing-owner", replace(next_p, request=replace(next_p.request, original_acceptance_mapping=missing)), {"invalid_original_acceptance_mapping"}))
    both = tuple(AcceptanceMapping(item.original_id, (EntityId("TASK-100"), EntityId("TASK-300"))) for item in next_p.request.original_acceptance_mapping)
    check("F3 identical multiple explicit owners", lambda: observe("both-owners", replace(next_p, request=replace(next_p.request, original_acceptance_mapping=both))))
    conflict_source = deepcopy(source)
    conflict_source["acceptance_criteria"][0]["description"] = "Conflicting meaning"
    conflict_p = mutate_tasks(next_p, [conflict_source, follow], current=True)
    conflict_p = mutate_tasks(conflict_p, [conflict_source, replacement])
    check("F3 conflicting retained copy without unrelated content mutation", lambda: observe("conflicting-copy", conflict_p, {"conflicting_original_acceptance"}))
    duplicate = (AcceptanceMapping("TASK-100-AC1", (EntityId("TASK-999"),)),) + next_p.request.original_acceptance_mapping
    check("Prehandoff hidden first owner rejects before dictionary collapse", lambda: observe("duplicate", replace(next_p, request=replace(next_p.request, original_acceptance_mapping=duplicate)), {"duplicate_original_acceptance_mapping"}))
    for field in ("used_agent_invocations", "used_rewrites", "elapsed_seconds", "used_review_1_cycles", "used_review_2_cycles", "used_tokens"):
        p = replace(next_p, proposed_lineage_budget=replace(cumulative, **{field: getattr(cumulative, field) - 1}))
        check("AC2 budget reset " + field, lambda p=p: observe("reset", p, {"budget_usage_reset"}))
    check("AC2 budget limit expansion", lambda: observe("limit", replace(next_p, proposed_lineage_budget=replace(cumulative, max_tokens=200000)), {"budget_limit_changed"}))
    check("AC2 actual token overshoot retained", lambda: observe("overshoot", replace(next_p, proposed_lineage_budget=replace(cumulative, used_tokens=100001)), {"lineage_budget_exhausted"}))
    reused = replace(next_p, historical_task_records=history + (verified(task_record("TASK-400", status="superseded")),))
    check("AC2 historical ID reuse rejects", lambda: observe("reuse", reused, {"task_id_reuse"}))
    other_plan = replace(next_p, historical_task_records=history + (verified(task_record("TASK-400", status="superseded", plan_id="PLAN-901")),))
    check("AC2 other-plan historical ID remains distinct", lambda: observe("namespace", other_plan))
    completed = deepcopy(source)
    completed["status"] = "completed"
    completed_p = mutate_tasks(augmented, [completed], current=True)
    completed_p = mutate_tasks(completed_p, [completed, follow])
    check("AC2 completed source unchanged during augment", lambda: observe("completed", completed_p))
    altered = replace(completed_p.proposed_task_records[0], content_ref=ContentRef("evidence/changed-completed.json", Sha256Digest("a" * 64)))
    completed_changed = replace(completed_p, proposed_task_records=(altered, completed_p.proposed_task_records[1]), proposed_task_contracts=(task_contract(completed, altered), completed_p.proposed_task_contracts[1]))
    check("AC2 completed reference mutation rejects", lambda: observe("completed-ref", completed_changed, {"completed_task_changed"}))


def command_check(argv: list[str]) -> dict[str, object]:
    proc = subprocess.run(argv, cwd=CANDIDATE, capture_output=True, text=True, shell=False)
    detail = {"argv": argv, "cwd": str(CANDIDATE), "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    RESULTS.setdefault("commands", []).append(detail)
    assert proc.returncode == 0, detail
    if "unittest" in argv:
        assert re.search(r"Ran 16 tests", proc.stderr) and "OK" in proc.stderr
        assert "skipped=" not in proc.stderr
    return detail


def closing() -> dict[str, object]:
    report = json.loads((ROOT / (PREFIX + ".json")).read_bytes())
    REGISTRY.validate(report, source=PREFIX + ".json")
    assert report["candidate_ref"] == MANIFEST
    assert report["candidate_fingerprint"] == "8f2ba197a56ab71a60729dc62f23fde758f305bb70759b55e33d35369816083d"
    assert report["stage"] == "implementation" and report["review_1_ref"] is None
    assert report["independent_session_id"] == "/root/verify_024_c2"
    assert [c["id"] for c in report["checks"]] == [f"R1-{i:02d}" for i in range(1, 12)]
    refs = []
    for item in report["checks"]:
        for ref in item["evidence"]:
            path = re.sub(r":\d+$", "", ref)
            assert path == PREFIX + "-closing.json.txt" or (ROOT / path).is_file() or (CANDIDATE / path).is_file(), ref
            refs.append(ref)
    text = (ROOT / (PREFIX + ".md")).read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        assert target == "TASK-024-a1-c2-R1-closing.json.txt" or ((ROOT / PREFIX).parent / target).is_file(), target
    behavior = json.loads((ROOT / (PREFIX + "-probes.json.txt")).read_bytes())
    assert all(c["status"] == "pass" for c in behavior["checks"])
    prior_identity = behavior["checks"][0]["detail"]
    current_identity = RESULTS["checks"][0]["detail"]
    for key in ("root_context_raw_hashes", "c1_preserved_sha256", "source_and_owned_sha256", "context_and_validation_hashes"):
        assert current_identity[key] == prior_identity[key], key
    return {"schema": "v1 review-result", "checks": 11, "evidence_links_checked": len(refs), "report_sha256": sha((ROOT / (PREFIX + ".json")).read_bytes()), "markdown_sha256": sha((ROOT / (PREFIX + ".md")).read_bytes()), "diagnostic_sha256": sha((ROOT / (PREFIX + "-probes.json.txt")).read_bytes())}


check("opening exact candidate, evidence, accepted prerequisites and preserved c1 identity", identity)
if "--closing" in sys.argv:
    check("finished review schema and evidence links", closing)
else:
    check("independent controls complete", controls)
    initial = ROOT / (PREFIX + "-initial.json.txt")
    if initial.is_file():
        prior = json.loads(initial.read_bytes())
        assert prior["head"] == HEAD and prior["base"] == BASE
        commands = prior["commands"]
        assert len(commands) == 2 and all(c["exit_code"] == 0 for c in commands)
        assert "Ran 16 tests" in commands[0]["stderr"] and "OK" in commands[0]["stderr"]
        RESULTS["commands"] = commands
        RESULTS["checks"].append({"name": "reuse actual passing candidate-bound leaf and foundation commands from initial diagnostic", "status": "pass", "detail": {"retained_output": PREFIX + "-initial.json.txt", "sha256": sha(initial.read_bytes()), "commands": commands}})
    else:
        check("exact declared Windows Python 3.12 leaf suite", lambda: command_check([sys.executable, "-m", "unittest", "discover", "-s", "tests/unit/planning_recovery_proposals/", "-p", "test_*.py"]))
        check("required foundation validation", lambda: command_check([sys.executable, "src/validate_foundation.py"]))
check("closing frozen identity and historical evidence", identity)
RESULTS["finished_at"] = datetime.now(timezone.utc).isoformat()
RESULTS["passed"] = all(c["status"] == "pass" for c in RESULTS["checks"])
output = ROOT / (PREFIX + ("-closing.json.txt" if "--closing" in sys.argv else "-probes.json.txt"))
output.write_text(json.dumps(RESULTS, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
assert output.is_file() and json.loads(output.read_bytes())["passed"] == RESULTS["passed"]
print(json.dumps({"output": str(output), "checks": len(RESULTS["checks"]), "passed": RESULTS["passed"], "failures": [c for c in RESULTS["checks"] if c["status"] == "fail"]}, indent=2))
sys.exit(0 if RESULTS["passed"] else 1)
