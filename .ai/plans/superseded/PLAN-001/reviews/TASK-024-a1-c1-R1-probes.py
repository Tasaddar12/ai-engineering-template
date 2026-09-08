"""Independent R1 diagnostics for the exact TASK-024 candidate; no source writes.

Run with the dispatched Python from the candidate cwd. Tracked owner-test helpers
construct frozen DTOs only; every validation/readiness call uses accepted source.
Assertions below preserve the observed candidate defects, not desired regressions.
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys

CANDIDATE = Path.cwd().resolve()
ROOT = CANDIDATE.parents[1]
PREFIX = ".ai/plans/current/PLAN-001/reviews/TASK-024-a1-c1-R1"
sys.path[:0] = [str(CANDIDATE / "src"), str(CANDIDATE / "tests/unit/planning_recovery_proposals")]
import contracts
import orchestration_ports
import plan_graph
import recovery_proposals
import scope
from test_recovery_proposals import (
    ProposalFactory, budget, criterion, evidence, graph_record, issue_codes,
    task_contract, task_record, verified,
)
from domain_values import EntityId, GraphStatus, PlanId, RecoveryStatus, Revision, Sha256Digest
from orchestration_ports import AcceptanceMapping, GitFacts, RecoveryAction, RecoveryRecord, RecoveryRequest
from plan_graph import AcceptedDependency
from recovery_proposals import RecoveryProposalInput, TaskSuccessorMapping, validate_recovery_proposal
from workflow_ports import ContentRef


def git(*args, cwd=CANDIDATE):
    return subprocess.check_output(["git", *args], cwd=cwd)


manifest_path = ".ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-024-a1-8805c35ec655.json"
manifest = json.loads((ROOT / manifest_path).read_bytes())
assert git("rev-parse", "HEAD").decode().strip() == manifest["head_oid"]
assert git("rev-parse", "HEAD", cwd=ROOT).decode().strip() == manifest["base_oid"]
assert git("status", "--porcelain") == b""
assert subprocess.run(["git", "merge-base", "--is-ancestor", manifest["base_oid"], manifest["head_oid"]], cwd=CANDIDATE).returncode == 0
assert hashlib.sha256(git("diff", "--binary", manifest["base_oid"], manifest["head_oid"])).hexdigest() == manifest["diff_sha256"]
for ref in manifest["context_refs"]:
    assert hashlib.sha256(git("show", manifest["head_oid"] + ":" + ref["path"])).hexdigest() == ref["sha256"]
for ref in manifest["validation_refs"]:
    assert hashlib.sha256((ROOT / ref["path"]).read_bytes()).hexdigest() == ref["sha256"]
assert hashlib.sha256((ROOT / ".ai/project/policy.json").read_bytes() + (ROOT / ".ai/project/agent-models.json").read_bytes()).hexdigest() == manifest["policy_model_digest"]
unsigned = {key: value for key, value in manifest.items() if key != "fingerprint"}
assert hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest() == manifest["fingerprint"]
print(f"IDENTITY: exact base/head, clean candidate, ancestry, raw diff, {len(manifest['context_refs'])} context refs, {len(manifest['validation_refs'])} validation refs, policy/model digest and fingerprint verified")
print("HEAD:", manifest["head_oid"], "BASE:", manifest["base_oid"])
print("FINGERPRINT:", manifest["fingerprint"])
print("CHANGED PATHS:\n" + git("diff", "--name-status", manifest["base_oid"], manifest["head_oid"]).decode().strip())
for module in (contracts, orchestration_ports, plan_graph, recovery_proposals, scope):
    assert Path(module.__file__).resolve().is_relative_to(CANDIDATE / "src")
    print("ORIGIN:", module.__name__, module.__file__)
registry = contracts.load_contract_registry(CANDIDATE / "schemas/v1")
factory = ProposalFactory(registry)


def observe(name, proposal):
    result = validate_recovery_proposal(proposal, registry=registry)
    print(name, json.dumps({"admissible": result.admissible, "issues": [
        {"code": str(item.details["code"]), "message": item.message} for item in result.issues
    ]}, sort_keys=True))
    return result


# F1: Actual PLAN-001 r4 plus a fresh acceptance-validation follow-up task.
plan = json.loads((CANDIDATE / ".ai/plans/current/PLAN-001/plan.json").read_bytes())
wire = json.loads((CANDIDATE / ".ai/plans/current/PLAN-001/graph.json").read_bytes())
records = [json.loads(next((CANDIDATE / ".ai/plans/current/PLAN-001/tasks").glob("*/" + task_id + ".json")).read_bytes()) for task_id in plan["task_ids"]]
isolation = json.loads((CANDIDATE / plan["isolation_review_ref"]).read_bytes())
assert contracts.structural_task_digest(records) == wire["task_set_sha256"] == isolation["task_set_sha256"]
assert wire["revision"] == isolation["graph_revision"] == 4 and isolation["verdict"] == "pass"
print("ISOLATION:", wire["revision"], wire["task_set_sha256"], "39 live task records")
source = next(record for record in records if record["id"] == "TASK-024")


def actual_follow_up(write_path, resources):
    fresh = deepcopy(source)
    fresh.update(id="TASK-100", title="Preserve recovery acceptance during rewrites",
                 objective="Implement the acceptance-preservation slice of TASK-024 with unchanged success criteria",
                 status="backlog", depends_on=["TASK-024"], attempt_ids=[], superseded_by=[], resume_state=None)
    fresh["scope"] = {"write_paths": [write_path], "read_paths": [],
                      "prohibited_paths": deepcopy(source["scope"]["prohibited_paths"]), "resources": resources}
    proposed_records = records + [fresh]
    next_plan = deepcopy(plan)
    next_plan["task_ids"].append("TASK-100")
    old_graph = graph_record(records, revision=4, status=GraphStatus.APPROVED, review_ref=wire["review_ref"], plan_id="PLAN-001")
    new_graph = graph_record(proposed_records, revision=5, status=GraphStatus.PROPOSED, review_ref=None, plan_id="PLAN-001")
    old_ref = verified(wire, ".ai/plans/current/PLAN-001/history/r4/graph.json").content_ref
    next_wire = deepcopy(wire)
    next_wire.update(id="PLAN-001-r5", revision=5, status="proposed", review_ref=None,
                     nodes=[{"task_id": record["id"], "depends_on": record["depends_on"]} for record in proposed_records],
                     task_set_sha256=new_graph.task_set_sha256.value)
    new_ref = verified(next_wire, ".ai/plans/current/PLAN-001/graph.json").content_ref
    old_snapshots = tuple(verified(record) for record in records)
    new_snapshots = old_snapshots + (verified(fresh),)
    original_mapping = tuple(AcceptanceMapping(item["id"], (EntityId("TASK-024"),)) for item in source["acceptance_criteria"])
    new_mapping = tuple(AcceptanceMapping(item.original_id, (EntityId("TASK-100"),)) for item in original_mapping)
    request = RecoveryRequest(
        project_id=EntityId("ai-engineering-framework"), plan_id=PlanId("PLAN-001"),
        run_id=EntityId("r1-probe-run"), operation_id=EntityId("r1-probe-op"), request_id=EntityId("r1-probe-request"),
        expected_generation=Revision(39), trigger="A missing acceptance helper requires a separate task owner",
        failed_task_ids=(EntityId("TASK-024"),), graph=old_graph,
        tasks=tuple(task_contract(record, snapshot) for record, snapshot in zip(records, old_snapshots)),
        original_acceptance_mapping=original_mapping, review_1_history=(), review_2_history=(),
        lineage_budget=budget(), git_facts=GitFacts((), (), (), (evidence(),)),
        permission_subset=("local_execute",), failure_evidence_refs=(evidence(),))
    recovery = RecoveryRecord(
        id=EntityId("RECOVERY-R1-PROBE"), plan_id=request.plan_id, run_id=request.run_id,
        trigger=request.trigger, failed_task_ids=request.failed_task_ids, review_refs=(),
        old_graph_ref=old_ref.path, new_graph_ref=new_ref.path, action=RecoveryAction.AUGMENT,
        new_task_ids=(EntityId("TASK-100"),), superseded_task_ids=(), acceptance_mapping=new_mapping,
        rationale="Same PLAN-001 recovery acceptance, new isolated local owner", salvage=(),
        status=RecoveryStatus.PROPOSED, isolation_review_ref=None, lineage_rewrite_count=2)
    return RecoveryProposalInput(
        request=request, record=recovery, current_plan=verified(plan, ".ai/plans/current/PLAN-001/plan.json"),
        proposed_plan=verified(next_plan, ".ai/plans/current/PLAN-001/proposed-plan.json"),
        current_graph_ref=old_ref, proposed_graph=new_graph, proposed_graph_ref=new_ref,
        current_task_records=old_snapshots, proposed_task_records=new_snapshots,
        proposed_task_contracts=tuple(task_contract(record, snapshot) for record, snapshot in zip(proposed_records, new_snapshots)),
        historical_task_records=(), successor_mapping=(TaskSuccessorMapping("TASK-024", ("TASK-100",), ("TASK-100",)),),
        proposed_permission_subset=request.permission_subset, proposed_lineage_budget=request.lineage_budget)


within = "tests/unit/planning_recovery_proposals/acceptance_helper.py"
assert observe("F1 control, inherited ownership", actual_follow_up(within, source["scope"]["resources"])).admissible
for name, proposal in (
    ("F1 new exact source path", actual_follow_up("src/recovery_proposal_acceptance.py", source["scope"]["resources"])),
    ("F1 new ownership resource", actual_follow_up(within, ["component:planning/recovery_proposal_acceptance"])),
):
    result = observe(name, proposal)
    assert not result.admissible and issue_codes(result) == {"permission_expansion"}
    assert len(result.proposed_graph.nodes) == 40
    assert proposal.request.permission_subset == proposal.proposed_permission_subset
    assert all(key == "task_ids" or proposal.current_plan.record[key] == proposal.proposed_plan.record[key] for key in proposal.current_plan.record)

# F2: The exit may be an early node, even while a later successor owns AC2.
original = task_record("TASK-100", write_paths=["work/source/"], criteria=[criterion("TASK-100-AC1"), criterion("TASK-100-AC2")])
dependent = task_record("TASK-200", depends_on=["TASK-100"], status="backlog")
first = task_record("TASK-300", write_paths=["work/source/first.py"], resources=["component:task-100"], criteria=[criterion("TASK-100-AC1")], status="backlog")
last = task_record("TASK-301", depends_on=["TASK-300"], write_paths=["work/source/last.py"], resources=["component:task-100"], criteria=[criterion("TASK-100-AC2")], status="backlog")
redirected = deepcopy(dependent)
redirected["depends_on"] = ["TASK-300"]
split = factory.make(RecoveryAction.SPLIT, [original, dependent], [first, last, redirected],
                     (TaskSuccessorMapping("TASK-100", ("TASK-300", "TASK-301"), ("TASK-300",)),),
                     target_by_acceptance={"TASK-100-AC1": ("TASK-300",), "TASK-100-AC2": ("TASK-301",)})
split_result = observe("F2 incomplete exit closure", split)
assert split_result.admissible
first_ref = next(node.task for node in split_result.proposed_graph.nodes if node.task.local_id.value == "TASK-300")
ready = split_result.proposed_graph.ready_frontier(accepted_integrated=(AcceptedDependency(first_ref, "a" * 40),))
print("F2 accepted only TASK-300; ready:", [item.task.local_id.value for item in ready])
assert {item.task.local_id.value for item in ready} == {"TASK-200", "TASK-301"}

# F3: An admitted augmentation makes an ordinary subsequent replacement fail.
follow = task_record("TASK-300", depends_on=["TASK-100"], write_paths=["work/source/follow.py"], resources=["component:task-100"], criteria=deepcopy(original["acceptance_criteria"]))
augment = factory.make(RecoveryAction.AUGMENT, [original], [original, follow],
                       (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),),
                       target_by_acceptance={"TASK-100-AC1": ("TASK-300",), "TASK-100-AC2": ("TASK-300",)})
assert observe("F3 first augmentation", augment).admissible
replacement = deepcopy(follow)
replacement["id"] = "TASK-400"
next_rewrite = factory.make(RecoveryAction.REPLACE, [original, follow], [original, replacement],
                            (TaskSuccessorMapping("TASK-300", ("TASK-400",), ("TASK-400",)),),
                            failed_task_id="TASK-300", current_budget=budget(used_rewrites=2), proposed_budget=budget(used_rewrites=2),
                            target_by_acceptance={"TASK-100-AC1": ("TASK-400",), "TASK-100-AC2": ("TASK-400",)})
next_rewrite = replace(next_rewrite,
    request=replace(next_rewrite.request, graph=replace(augment.proposed_graph, status=GraphStatus.APPROVED, review_ref="reviews/rewrite-r2.json")),
    proposed_graph=replace(next_rewrite.proposed_graph, id=EntityId("PLAN-900-r3"), revision=Revision(3)))
result = observe("F3 next replacement, third rewrite within max 3", next_rewrite)
assert not result.admissible and issue_codes(result) == {"ambiguous_original_acceptance"}

# Independent negative controls: completed identity, budget overshoot and real authority.
over = replace(augment, proposed_lineage_budget=replace(augment.proposed_lineage_budget, used_tokens=100001))
assert "lineage_budget_exhausted" in issue_codes(observe("control token overshoot", over))
assert over.proposed_lineage_budget.used_tokens == 100001
authority = replace(augment, proposed_permission_subset=("local_execute", "remote_publish"))
assert "permission_expansion" in issue_codes(observe("control broadened permission", authority))
completed = deepcopy(original)
completed["status"] = "completed"
immutable = factory.make(RecoveryAction.AUGMENT, [completed], [completed, follow],
                         (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),),
                         target_by_acceptance={"TASK-100-AC1": ("TASK-300",), "TASK-100-AC2": ("TASK-300",)})
assert observe("control completed source plus new work", immutable).admissible
changed_snapshot = replace(immutable.proposed_task_records[0], content_ref=ContentRef("moved/completed.json", Sha256Digest("a" * 64)))
changed = replace(immutable, proposed_task_records=(changed_snapshot, immutable.proposed_task_records[1]),
                  proposed_task_contracts=(task_contract(completed, changed_snapshot), immutable.proposed_task_contracts[1]))
assert "completed_task_changed" in issue_codes(observe("control completed content reference changed", changed))
print("All independent diagnostic assertions reproduced; three product findings remain.")
assert git("rev-parse", "HEAD").decode().strip() == manifest["head_oid"] and git("status", "--porcelain") == b""
