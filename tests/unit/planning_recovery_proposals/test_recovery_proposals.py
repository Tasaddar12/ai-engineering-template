from __future__ import annotations

import hashlib
import json
import sys
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from contracts import load_contract_registry, structural_task_digest
from domain_values import (
    EntityId,
    ErrorCategory,
    EvidenceRef,
    GraphStatus,
    PlanId,
    RecoveryStatus,
    Revision,
    ScopeClaim,
    ScopePath,
    Sha256Digest,
)
from orchestration_ports import (
    AcceptanceMapping,
    GitFacts,
    GraphNode,
    LineageBudget,
    RecoveryAction,
    RecoveryRecord,
    RecoveryRequest,
    TaskContractSnapshot,
    TaskGraphRecord,
)
from recovery_proposals import (
    RecoveryProposalInput,
    RecoveryProposalValidationStatus,
    TaskSuccessorMapping,
    VerifiedRecordSnapshot,
    validate_recovery_proposal,
)
from workflow_ports import ContentRef


ZERO = "0" * 64
ONE = "1" * 64
TWO = "2" * 64
PLAN_ID = "PLAN-900"


def digest_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def content(path: str, value: object, *, digest: str | None = None) -> ContentRef:
    return ContentRef(path, Sha256Digest(digest or digest_json(value)))


def verified(record: dict[str, object], path: str | None = None) -> VerifiedRecordSnapshot:
    selected = path or f".ai/plans/current/{record['plan_id']}/tasks/current/{record['id']}.json"
    return VerifiedRecordSnapshot(record, content(selected, record))


def criterion(identifier: str, description: str | None = None) -> dict[str, str]:
    return {
        "id": identifier,
        "description": description or f"Preserve {identifier}",
        "verification": f"Verify {identifier}",
    }


def task_record(
    task_id: str,
    *,
    depends_on: list[str] | None = None,
    write_paths: list[str] | None = None,
    resources: list[str] | None = None,
    criteria: list[dict[str, str]] | None = None,
    status: str = "running",
    plan_id: str = PLAN_ID,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "kind": "task",
        "id": task_id,
        "plan_id": plan_id,
        "title": f"Task {task_id}",
        "status": status,
        "archived": False,
        "objective": f"Implement {task_id}",
        "depends_on": list(depends_on or []),
        "scope": {
            "write_paths": list(write_paths or [f"work/{task_id}.py"]),
            "read_paths": [],
            "prohibited_paths": ["private/"],
            "resources": list(resources) if resources is not None else [f"component:{task_id.lower()}"],
        },
        "acceptance_criteria": deepcopy(criteria or [criterion(f"{task_id}-AC1")]),
        "plan_acceptance_ids": ["AC-01"],
        "spec_refs": [f".ai/plans/current/{plan_id}/spec.json"],
        "adr_refs": [],
        "research_refs": [],
        "input_contracts": [],
        "output_contracts": [f"component:{task_id.lower()}"],
        "validation_commands": [f"test.{task_id}"],
        "estimated_production_files": 1,
        "size_rationale": "One bounded task",
        "out_of_scope": ["Other task files"],
        "handoff_requirements": ["Validation evidence"],
        "attempt_ids": [],
        "superseded_by": [],
        "resume_state": None,
    }


def plan_record(task_ids: list[str], *, plan_id: str = PLAN_ID) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "kind": "plan",
        "id": plan_id,
        "title": "Recovery fixture",
        "status": "running",
        "archived": False,
        "spec_refs": [f".ai/plans/current/{plan_id}/spec.json"],
        "adr_refs": [],
        "research_refs": [],
        "document_ref": f".ai/plans/current/{plan_id}/plan.md",
        "acceptance_criteria": [
            {
                "id": "AC-01",
                "description": "All required behavior remains covered",
                "verification": "Mapped task tests",
            }
        ],
        "task_ids": list(task_ids),
        "graph_ref": f".ai/plans/current/{plan_id}/graph.json",
        "isolation_review_ref": f".ai/plans/current/{plan_id}/reviews/r1.json",
        "resume_state": "Recovery in progress",
        "integration_branch": f"ai/{plan_id}/integration",
        "target_branch": "main",
        "merge_evidence_ref": None,
    }


def task_contract(record: dict[str, object], snapshot: VerifiedRecordSnapshot) -> TaskContractSnapshot:
    scope = record["scope"]
    assert isinstance(scope, dict)
    criteria = record["acceptance_criteria"]
    assert isinstance(criteria, list)
    return TaskContractSnapshot(
        task_id=EntityId(str(record["id"])),
        depends_on=tuple(EntityId(str(value)) for value in record["depends_on"]),
        scope=ScopeClaim(
            write_paths=scope["write_paths"],
            read_paths=scope["read_paths"],
            prohibited_paths=scope["prohibited_paths"],
            resources=scope["resources"],
        ),
        acceptance_ids=tuple(str(value["id"]) for value in criteria),
        plan_acceptance_ids=tuple(str(value) for value in record["plan_acceptance_ids"]),
        input_contracts=tuple(str(value) for value in record["input_contracts"]),
        output_contracts=tuple(str(value) for value in record["output_contracts"]),
        estimated_production_files=int(record["estimated_production_files"]),
        content_ref=snapshot.content_ref,
    )


def graph_record(
    records: list[dict[str, object]],
    *,
    revision: int,
    status: GraphStatus,
    review_ref: str | None,
    plan_id: str = PLAN_ID,
) -> TaskGraphRecord:
    return TaskGraphRecord(
        id=EntityId(f"{plan_id}-r{revision}"),
        plan_id=PlanId(plan_id),
        revision=Revision(revision),
        status=status,
        nodes=tuple(
            GraphNode(
                EntityId(str(record["id"])),
                tuple(EntityId(str(value)) for value in record["depends_on"]),
            )
            for record in records
        ),
        task_set_sha256=Sha256Digest(structural_task_digest(records)),
        review_ref=review_ref,
    )


def budget(**changes: int | None) -> LineageBudget:
    values: dict[str, int | None] = {
        "max_agent_invocations": 300,
        "used_agent_invocations": 5,
        "max_rewrites": 3,
        "used_rewrites": 1,
        "max_elapsed_seconds": 3600,
        "elapsed_seconds": 120,
        "max_review_cycles_per_stage": 2,
        "used_review_1_cycles": 2,
        "used_review_2_cycles": 1,
        "max_tokens": 100000,
        "used_tokens": 9000,
    }
    values.update(changes)
    return LineageBudget(**values)


def evidence() -> EvidenceRef:
    return EvidenceRef(ScopePath.exact_file("evidence/failure.txt"), Sha256Digest(ZERO))


def issue_codes(result) -> set[str]:
    return {str(item.details["code"]) for item in result.issues}


class ProposalFactory:
    def __init__(self, registry) -> None:
        self.registry = registry

    def make(
        self,
        action: RecoveryAction,
        current_records: list[dict[str, object]],
        proposed_records: list[dict[str, object]],
        successors: tuple[TaskSuccessorMapping, ...],
        *,
        failed_task_id: str = "TASK-100",
        original_acceptance_ids: tuple[str, ...] | None = None,
        target_by_acceptance: dict[str, tuple[str, ...]] | None = None,
        historical: tuple[VerifiedRecordSnapshot, ...] = (),
        current_budget: LineageBudget | None = None,
        proposed_budget: LineageBudget | None = None,
        permissions: tuple[str, ...] = ("local_execute",),
        proposed_permissions: tuple[str, ...] | None = None,
    ) -> RecoveryProposalInput:
        current_snapshots = tuple(verified(item) for item in current_records)
        proposed_snapshots = tuple(verified(item) for item in proposed_records)
        current_graph = graph_record(
            current_records,
            revision=1,
            status=GraphStatus.APPROVED,
            review_ref=f".ai/plans/current/{PLAN_ID}/reviews/r1.json",
        )
        new_graph = graph_record(
            proposed_records,
            revision=2,
            status=GraphStatus.PROPOSED,
            review_ref=None,
        )
        current_by_id = {str(item["id"]): item for item in current_records}
        source_record = current_by_id[failed_task_id]
        all_source_ids = tuple(
            str(value["id"]) for value in source_record["acceptance_criteria"]
        )
        selected_ids = original_acceptance_ids or all_source_ids
        original_mapping = tuple(
            AcceptanceMapping(identifier, (EntityId(failed_task_id),))
            for identifier in selected_ids
        )
        proposed_index = {str(item["id"]): item for item in proposed_records}
        if target_by_acceptance is None:
            target_by_acceptance = {}
            for identifier in selected_ids:
                matches = tuple(
                    task_id
                    for task_id, item in proposed_index.items()
                    if any(
                        str(value["id"]) == identifier
                        for value in item["acceptance_criteria"]
                    )
                )
                target_by_acceptance[identifier] = matches[:1]
        new_mapping = tuple(
            AcceptanceMapping(identifier, tuple(EntityId(value) for value in target_by_acceptance[identifier]))
            for identifier in selected_ids
        )
        active_budget = current_budget or budget()
        next_budget = proposed_budget or active_budget
        graph_ref = ContentRef(f".ai/plans/current/{PLAN_ID}/history/r1/graph.json", Sha256Digest(ONE))
        proposed_graph_ref = ContentRef(f".ai/plans/current/{PLAN_ID}/graph.json", Sha256Digest(TWO))
        request = RecoveryRequest(
            project_id=EntityId("project-fixture"),
            plan_id=PlanId(PLAN_ID),
            run_id=EntityId("run-1"),
            operation_id=EntityId("operation-1"),
            request_id=EntityId("request-1"),
            expected_generation=Revision(4),
            trigger="Structural review failure",
            failed_task_ids=(EntityId(failed_task_id),),
            graph=current_graph,
            tasks=tuple(
                task_contract(record, snapshot)
                for record, snapshot in zip(current_records, current_snapshots, strict=True)
            ),
            original_acceptance_mapping=original_mapping,
            review_1_history=(),
            review_2_history=(),
            lineage_budget=active_budget,
            git_facts=GitFacts((), (), (), (evidence(),)),
            permission_subset=permissions,
            failure_evidence_refs=(evidence(),),
        )
        current_ids = {str(item["id"]) for item in current_records}
        proposed_ids = {str(item["id"]) for item in proposed_records}
        recovery = RecoveryRecord(
            id=EntityId("RECOVERY-001"),
            plan_id=PlanId(PLAN_ID),
            run_id=EntityId("run-1"),
            trigger="Structural review failure",
            failed_task_ids=(EntityId(failed_task_id),),
            review_refs=(),
            old_graph_ref=graph_ref.path,
            new_graph_ref=proposed_graph_ref.path,
            action=action,
            new_task_ids=tuple(EntityId(value) for value in sorted(proposed_ids - current_ids)),
            superseded_task_ids=tuple(EntityId(value) for value in sorted(current_ids - proposed_ids)),
            acceptance_mapping=new_mapping,
            rationale="Preserve acceptance while repairing structure",
            salvage=(),
            status=RecoveryStatus.PROPOSED,
            isolation_review_ref=None,
            lineage_rewrite_count=active_budget.used_rewrites + 1,
        )
        current_plan = plan_record([str(item["id"]) for item in current_records])
        next_plan = deepcopy(current_plan)
        next_plan["task_ids"] = [str(item["id"]) for item in proposed_records]
        return RecoveryProposalInput(
            request=request,
            record=recovery,
            current_plan=verified(current_plan, f".ai/plans/current/{PLAN_ID}/plan.json"),
            proposed_plan=verified(next_plan, f".ai/plans/current/{PLAN_ID}/proposed-plan.json"),
            current_graph_ref=graph_ref,
            proposed_graph=new_graph,
            proposed_graph_ref=proposed_graph_ref,
            current_task_records=current_snapshots,
            proposed_task_records=proposed_snapshots,
            proposed_task_contracts=tuple(
                task_contract(record, snapshot)
                for record, snapshot in zip(proposed_records, proposed_snapshots, strict=True)
            ),
            historical_task_records=historical,
            successor_mapping=successors,
            proposed_permission_subset=(
                proposed_permissions if proposed_permissions is not None else permissions
            ),
            proposed_lineage_budget=next_budget,
        )


class RecoveryProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_contract_registry(ROOT / "schemas" / "v1")
        cls.factory = ProposalFactory(cls.registry)

    def validate(self, proposal: RecoveryProposalInput):
        return validate_recovery_proposal(proposal, registry=self.registry)

    def base_tasks(self) -> tuple[dict[str, object], dict[str, object]]:
        source = task_record(
            "TASK-100",
            write_paths=["work/source/"],
            criteria=[criterion("TASK-100-AC1"), criterion("TASK-100-AC2")],
        )
        dependent = task_record("TASK-200", depends_on=["TASK-100"])
        return source, dependent

    def test_split_preserves_acceptance_and_redirects_dependents(self) -> None:
        source, dependent = self.base_tasks()
        first = task_record(
            "TASK-300",
            write_paths=["work/source/first.py"],
            resources=["component:task-100"],
            criteria=[criterion("TASK-100-AC1")],
        )
        second = task_record(
            "TASK-301",
            depends_on=["TASK-300"],
            write_paths=["work/source/second.py"],
            resources=["component:task-100"],
            criteria=[criterion("TASK-100-AC2")],
        )
        replacement_dependent = deepcopy(dependent)
        replacement_dependent["depends_on"] = ["TASK-301"]
        mapping = TaskSuccessorMapping("TASK-100", ("TASK-300", "TASK-301"), ("TASK-301",))
        proposal = self.factory.make(
            RecoveryAction.SPLIT,
            [source, dependent],
            [first, second, replacement_dependent],
            (mapping,),
            target_by_acceptance={
                "TASK-100-AC1": ("TASK-300",),
                "TASK-100-AC2": ("TASK-301",),
            },
        )

        result = self.validate(proposal)

        self.assertTrue(result.admissible, [(item.details["code"], item.message) for item in result.issues])
        self.assertTrue(result.requires_isolation_review)
        self.assertEqual(result.status, RecoveryProposalValidationStatus.ADMISSIBLE)
        self.assertEqual(result.retained_task_history[-1].record["id"], "TASK-100")

    def test_replace_and_augment_are_admissible(self) -> None:
        source, dependent = self.base_tasks()
        replacement = task_record(
            "TASK-300",
            write_paths=["work/source/replacement.py"],
            resources=["component:task-100"],
            criteria=deepcopy(source["acceptance_criteria"]),
        )
        redirected = deepcopy(dependent)
        redirected["depends_on"] = ["TASK-300"]
        replace_proposal = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, redirected],
            (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),),
            target_by_acceptance={
                "TASK-100-AC1": ("TASK-300",),
                "TASK-100-AC2": ("TASK-300",),
            },
        )
        augment = task_record(
            "TASK-300",
            depends_on=["TASK-100"],
            write_paths=["work/source/follow-up.py"],
            resources=["component:task-100"],
            criteria=deepcopy(source["acceptance_criteria"]),
        )
        augment_proposal = self.factory.make(
            RecoveryAction.AUGMENT,
            [source, dependent],
            [source, dependent, augment],
            (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),),
            target_by_acceptance={
                "TASK-100-AC1": ("TASK-300",),
                "TASK-100-AC2": ("TASK-300",),
            },
        )

        replace_result = self.validate(replace_proposal)
        augment_result = self.validate(augment_proposal)
        self.assertTrue(replace_result.admissible, [(item.details["code"], item.message) for item in replace_result.issues])
        self.assertTrue(augment_result.admissible, [(item.details["code"], item.message) for item in augment_result.issues])

    def test_sequence_uses_graph_reachability_to_resolve_scope_conflict(self) -> None:
        first = task_record("TASK-100", write_paths=["shared/value.py"])
        second = task_record("TASK-200", write_paths=["SHARED/value.py"])
        sequenced = deepcopy(second)
        sequenced["depends_on"] = ["TASK-100"]
        proposal = self.factory.make(
            RecoveryAction.SEQUENCE,
            [first, second],
            [first, sequenced],
            (),
            target_by_acceptance={"TASK-100-AC1": ("TASK-100",)},
        )

        result = self.validate(proposal)

        self.assertTrue(result.admissible)
        self.assertEqual(
            tuple(item.local_id.value for item in result.proposed_graph.topological_order),
            ("TASK-100", "TASK-200"),
        )

    def test_rejects_cycle_and_stale_structural_digest(self) -> None:
        source, dependent = self.base_tasks()
        replacement = task_record(
            "TASK-300",
            depends_on=["TASK-200"],
            write_paths=["work/source/new.py"],
            resources=["component:task-100"],
            criteria=deepcopy(source["acceptance_criteria"]),
        )
        cycle_dependent = deepcopy(dependent)
        cycle_dependent["depends_on"] = ["TASK-300"]
        proposal = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, cycle_dependent],
            (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),),
            target_by_acceptance={
                "TASK-100-AC1": ("TASK-300",),
                "TASK-100-AC2": ("TASK-300",),
            },
        )
        cycle_result = self.validate(proposal)
        stale = replace(
            proposal,
            proposed_graph=replace(proposal.proposed_graph, task_set_sha256=Sha256Digest(ZERO)),
        )

        self.assertIn("invalid_proposed_graph", issue_codes(cycle_result))
        self.assertIn("invalid_proposed_graph", issue_codes(self.validate(stale)))

    def test_rejects_reused_id_but_allows_same_local_id_in_other_plan(self) -> None:
        source, dependent = self.base_tasks()
        replacement = task_record(
            "TASK-300",
            write_paths=["work/source/new.py"],
            resources=["component:task-100"],
            criteria=deepcopy(source["acceptance_criteria"]),
        )
        redirected = deepcopy(dependent)
        redirected["depends_on"] = ["TASK-300"]
        mapping = (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),)
        kwargs = {
            "target_by_acceptance": {
                "TASK-100-AC1": ("TASK-300",),
                "TASK-100-AC2": ("TASK-300",),
            }
        }
        same_plan_history = task_record("TASK-300", status="superseded")
        reused = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, redirected],
            mapping,
            historical=(verified(same_plan_history, ".ai/history/TASK-300.json"),),
            **kwargs,
        )
        other_plan_history = task_record("TASK-300", status="superseded", plan_id="PLAN-901")
        namespaced = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, redirected],
            mapping,
            historical=(verified(other_plan_history, ".ai/history/PLAN-901/TASK-300.json"),),
            **kwargs,
        )

        self.assertIn("task_id_reuse", issue_codes(self.validate(reused)))
        namespaced_result = self.validate(namespaced)
        self.assertTrue(namespaced_result.admissible, [(item.details["code"], item.message) for item in namespaced_result.issues])

    def test_rejects_changed_or_superseded_completed_task(self) -> None:
        completed = task_record("TASK-100", write_paths=["shared/value.py"], status="completed")
        peer = task_record("TASK-200", write_paths=["SHARED/value.py"])
        changed_completed = deepcopy(completed)
        changed_completed["title"] = "Changed completed work"
        sequenced_peer = deepcopy(peer)
        sequenced_peer["depends_on"] = ["TASK-100"]
        changed = self.factory.make(
            RecoveryAction.SEQUENCE,
            [completed, peer],
            [changed_completed, sequenced_peer],
            (),
            target_by_acceptance={"TASK-100-AC1": ("TASK-100",)},
        )
        replacement = task_record(
            "TASK-300",
            write_paths=["shared/replacement.py"],
            resources=["component:task-100"],
            criteria=deepcopy(completed["acceptance_criteria"]),
        )
        replaced = self.factory.make(
            RecoveryAction.REPLACE,
            [completed, peer],
            [replacement, peer],
            (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),),
            target_by_acceptance={"TASK-100-AC1": ("TASK-300",)},
        )

        self.assertIn("completed_task_changed", issue_codes(self.validate(changed)))
        self.assertIn("completed_task_superseded", issue_codes(self.validate(replaced)))

    def test_rejects_changed_acceptance_text_and_omitted_criteria(self) -> None:
        source, dependent = self.base_tasks()
        changed = task_record(
            "TASK-300",
            write_paths=["work/source/new.py"],
            resources=["component:task-100"],
            criteria=[
                criterion("TASK-100-AC1", "Weakened meaning"),
                criterion("TASK-100-AC2"),
            ],
        )
        redirected = deepcopy(dependent)
        redirected["depends_on"] = ["TASK-300"]
        mapping = (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),)
        altered = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [changed, redirected],
            mapping,
            target_by_acceptance={
                "TASK-100-AC1": ("TASK-300",),
                "TASK-100-AC2": ("TASK-300",),
            },
        )
        replacement = deepcopy(changed)
        replacement["acceptance_criteria"][0] = criterion("TASK-100-AC1")
        omitted = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, redirected],
            mapping,
            original_acceptance_ids=("TASK-100-AC1",),
            target_by_acceptance={"TASK-100-AC1": ("TASK-300",)},
        )

        self.assertIn("acceptance_content_changed", issue_codes(self.validate(altered)))
        self.assertIn("acceptance_mapping_incomplete", issue_codes(self.validate(omitted)))

    def test_rejects_incomplete_dependent_redirection(self) -> None:
        source, dependent = self.base_tasks()
        replacement = task_record(
            "TASK-300",
            write_paths=["work/source/new.py"],
            resources=["component:task-100"],
            criteria=deepcopy(source["acceptance_criteria"]),
        )
        detached = deepcopy(dependent)
        detached["depends_on"] = []
        proposal = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, detached],
            (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),),
            target_by_acceptance={
                "TASK-100-AC1": ("TASK-300",),
                "TASK-100-AC2": ("TASK-300",),
            },
        )

        self.assertIn("dependency_mapping_incomplete", issue_codes(self.validate(proposal)))

    def test_rejects_scope_and_permission_expansion(self) -> None:
        source, dependent = self.base_tasks()
        replacement = task_record(
            "TASK-300",
            write_paths=["outside/new.py"],
            resources=["component:task-100"],
            criteria=deepcopy(source["acceptance_criteria"]),
        )
        redirected = deepcopy(dependent)
        redirected["depends_on"] = ["TASK-300"]
        proposal = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, redirected],
            (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),),
            target_by_acceptance={
                "TASK-100-AC1": ("TASK-300",),
                "TASK-100-AC2": ("TASK-300",),
            },
            proposed_permissions=("local_execute", "remote_publish"),
        )

        result = self.validate(proposal)

        self.assertIn("permission_expansion", issue_codes(result))
        self.assertTrue(any(item.category is ErrorCategory.POLICY_DENIED for item in result.issues))

    def test_rejects_budget_reset_and_preserves_over_limit_usage(self) -> None:
        source, dependent = self.base_tasks()
        replacement = task_record(
            "TASK-300",
            write_paths=["work/source/new.py"],
            resources=["component:task-100"],
            criteria=deepcopy(source["acceptance_criteria"]),
        )
        redirected = deepcopy(dependent)
        redirected["depends_on"] = ["TASK-300"]
        mapping = (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),)
        targets = {
            "TASK-100-AC1": ("TASK-300",),
            "TASK-100-AC2": ("TASK-300",),
        }
        current = budget(used_agent_invocations=8)
        reset = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, redirected],
            mapping,
            target_by_acceptance=targets,
            current_budget=current,
            proposed_budget=replace(current, used_agent_invocations=7),
        )
        expanded_limit = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, redirected],
            mapping,
            target_by_acceptance=targets,
            current_budget=current,
            proposed_budget=replace(current, max_agent_invocations=301),
        )
        over = budget(max_rewrites=3, used_rewrites=4, used_agent_invocations=301)
        over_limit = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, redirected],
            mapping,
            target_by_acceptance=targets,
            current_budget=over,
            proposed_budget=over,
        )

        self.assertIn("budget_usage_reset", issue_codes(self.validate(reset)))
        self.assertIn("budget_limit_changed", issue_codes(self.validate(expanded_limit)))
        over_result = self.validate(over_limit)
        self.assertIn("lineage_budget_exhausted", issue_codes(over_result))
        self.assertEqual(over_limit.request.lineage_budget.used_rewrites, 4)
        self.assertEqual(over_limit.proposed_lineage_budget.used_agent_invocations, 301)

    def test_rejects_unsequenced_conflict_and_unsupported_merge(self) -> None:
        source, dependent = self.base_tasks()
        replacement = task_record(
            "TASK-300",
            write_paths=["work/source/new.py"],
            resources=["component:task-100"],
            criteria=deepcopy(source["acceptance_criteria"]),
        )
        conflict = deepcopy(dependent)
        conflict["depends_on"] = ["TASK-300"]
        conflict["scope"]["write_paths"] = ["work/source/new.py"]
        base = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, conflict],
            (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),),
            target_by_acceptance={
                "TASK-100-AC1": ("TASK-300",),
                "TASK-100-AC2": ("TASK-300",),
            },
        )
        # The direct dependency sequences this collision; remove it while keeping
        # the old edge redirected to an independent successor to isolate scope.
        extra = task_record(
            "TASK-301",
            write_paths=["work/source/exit.py"],
            resources=["component:task-100"],
            criteria=[],
        )
        # A schema-valid task needs one criterion; it need not own the transferred IDs.
        extra["acceptance_criteria"] = [criterion("TASK-301-AC1")]
        unsequenced_conflict = deepcopy(conflict)
        unsequenced_conflict["depends_on"] = ["TASK-301"]
        proposal = self.factory.make(
            RecoveryAction.SPLIT,
            [source, dependent],
            [replacement, extra, unsequenced_conflict],
            (TaskSuccessorMapping("TASK-100", ("TASK-300", "TASK-301"), ("TASK-301",)),),
            target_by_acceptance={
                "TASK-100-AC1": ("TASK-300",),
                "TASK-100-AC2": ("TASK-300",),
            },
        )
        self.assertIn("unsequenced_scope_conflict", issue_codes(self.validate(proposal)))
        for action in (RecoveryAction.REPAIR, RecoveryAction.MERGE):
            with self.subTest(action=action):
                unsupported = replace(base, record=replace(base.record, action=action))
                self.assertIn(
                    "unsupported_recovery_action", issue_codes(self.validate(unsupported))
                )

    def test_admissible_result_never_claims_isolation_approval(self) -> None:
        source, dependent = self.base_tasks()
        replacement = task_record(
            "TASK-300",
            write_paths=["work/source/new.py"],
            resources=["component:task-100"],
            criteria=deepcopy(source["acceptance_criteria"]),
        )
        redirected = deepcopy(dependent)
        redirected["depends_on"] = ["TASK-300"]
        proposal = self.factory.make(
            RecoveryAction.REPLACE,
            [source, dependent],
            [replacement, redirected],
            (TaskSuccessorMapping("TASK-100", ("TASK-300",), ("TASK-300",)),),
            target_by_acceptance={
                "TASK-100-AC1": ("TASK-300",),
                "TASK-100-AC2": ("TASK-300",),
            },
        )
        approved_graph = replace(
            proposal.proposed_graph,
            status=GraphStatus.APPROVED,
            review_ref=f".ai/plans/current/{PLAN_ID}/reviews/r2.json",
        )
        premature = replace(proposal, proposed_graph=approved_graph)

        self.assertIn("premature_graph_approval", issue_codes(self.validate(premature)))


class ActualAcceptedGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_contract_registry(ROOT / "schemas" / "v1")

    def test_actual_r4_graph_supports_a_scoped_augmentation(self) -> None:
        plan_path = ROOT / ".ai" / "plans" / "current" / "PLAN-001" / "plan.json"
        graph_path = ROOT / ".ai" / "plans" / "current" / "PLAN-001" / "graph.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        records: list[dict[str, object]] = []
        snapshots: list[VerifiedRecordSnapshot] = []
        for task_id in plan["task_ids"]:
            matches = list(
                (ROOT / ".ai" / "plans" / "current" / "PLAN-001" / "tasks").glob(
                    f"*/{task_id}.json"
                )
            )
            self.assertEqual(len(matches), 1)
            path = matches[0]
            record = json.loads(path.read_text(encoding="utf-8"))
            records.append(record)
            snapshots.append(
                VerifiedRecordSnapshot(
                    record,
                    ContentRef(
                        path.relative_to(ROOT).as_posix(),
                        Sha256Digest(hashlib.sha256(path.read_bytes()).hexdigest()),
                    ),
                )
            )
        source = next(item for item in records if item["id"] == "TASK-024")
        follow_up = deepcopy(source)
        follow_up.update(
            {
                "id": "TASK-100",
                "title": "Retain recovery validation evidence",
                "status": "backlog",
                "objective": "Exercise a scoped recovery augmentation",
                "depends_on": ["TASK-024"],
                "scope": {
                    "write_paths": [
                        "tests/unit/planning_recovery_proposals/retained-evidence.py"
                    ],
                    "read_paths": [],
                    "prohibited_paths": [],
                    "resources": [],
                },
                "acceptance_criteria": deepcopy(source["acceptance_criteria"]),
                "attempt_ids": [],
                "superseded_by": [],
                "resume_state": None,
            }
        )
        proposed_records = records + [follow_up]
        proposed_snapshots = snapshots + [verified(follow_up)]
        proposed_plan = deepcopy(plan)
        proposed_plan["task_ids"] = list(plan["task_ids"]) + ["TASK-100"]
        proposed_graph_wire = deepcopy(graph)
        proposed_graph_wire.update(
            {
                "id": "PLAN-001-r5",
                "revision": 5,
                "status": "proposed",
                "review_ref": None,
                "nodes": list(graph["nodes"])
                + [{"task_id": "TASK-100", "depends_on": ["TASK-024"]}],
                "task_set_sha256": structural_task_digest(proposed_records),
            }
        )
        current_graph = graph_record(
            records,
            revision=4,
            status=GraphStatus.APPROVED,
            review_ref=str(graph["review_ref"]),
            plan_id="PLAN-001",
        )
        proposed_graph = graph_record(
            proposed_records,
            revision=5,
            status=GraphStatus.PROPOSED,
            review_ref=None,
            plan_id="PLAN-001",
        )
        source_acceptance = tuple(
            str(item["id"]) for item in source["acceptance_criteria"]
        )
        active_budget = budget()
        request = RecoveryRequest(
            project_id=EntityId("ai-engineering-framework"),
            plan_id=PlanId("PLAN-001"),
            run_id=EntityId("run-actual-graph"),
            operation_id=EntityId("operation-actual-graph"),
            request_id=EntityId("request-actual-graph"),
            expected_generation=Revision(32),
            trigger="Representative augmentation",
            failed_task_ids=(EntityId("TASK-024"),),
            graph=current_graph,
            tasks=tuple(
                task_contract(record, snapshot)
                for record, snapshot in zip(records, snapshots, strict=True)
            ),
            original_acceptance_mapping=tuple(
                AcceptanceMapping(identifier, (EntityId("TASK-024"),))
                for identifier in source_acceptance
            ),
            review_1_history=(),
            review_2_history=(),
            lineage_budget=active_budget,
            git_facts=GitFacts((), (), (), (evidence(),)),
            permission_subset=("local_execute",),
            failure_evidence_refs=(evidence(),),
        )
        current_graph_ref = ContentRef(
            graph_path.relative_to(ROOT).as_posix(),
            Sha256Digest(hashlib.sha256(graph_path.read_bytes()).hexdigest()),
        )
        proposed_graph_ref = ContentRef(
            ".ai/plans/current/PLAN-001/evidence/proposed-r5-graph.json",
            Sha256Digest(digest_json(proposed_graph_wire)),
        )
        recovery = RecoveryRecord(
            id=EntityId("RECOVERY-ACTUAL-001"),
            plan_id=PlanId("PLAN-001"),
            run_id=EntityId("run-actual-graph"),
            trigger="Representative augmentation",
            failed_task_ids=(EntityId("TASK-024"),),
            review_refs=(),
            old_graph_ref=current_graph_ref.path,
            new_graph_ref=proposed_graph_ref.path,
            action=RecoveryAction.AUGMENT,
            new_task_ids=(EntityId("TASK-100"),),
            superseded_task_ids=(),
            acceptance_mapping=tuple(
                AcceptanceMapping(identifier, (EntityId("TASK-100"),))
                for identifier in source_acceptance
            ),
            rationale="Exercise accepted graph, scope and orchestration boundaries",
            salvage=(),
            status=RecoveryStatus.PROPOSED,
            isolation_review_ref=None,
            lineage_rewrite_count=active_budget.used_rewrites + 1,
        )
        proposal = RecoveryProposalInput(
            request=request,
            record=recovery,
            current_plan=VerifiedRecordSnapshot(
                plan,
                ContentRef(
                    plan_path.relative_to(ROOT).as_posix(),
                    Sha256Digest(hashlib.sha256(plan_path.read_bytes()).hexdigest()),
                ),
            ),
            proposed_plan=verified(
                proposed_plan,
                ".ai/plans/current/PLAN-001/evidence/proposed-plan.json",
            ),
            current_graph_ref=current_graph_ref,
            proposed_graph=proposed_graph,
            proposed_graph_ref=proposed_graph_ref,
            current_task_records=tuple(snapshots),
            proposed_task_records=tuple(proposed_snapshots),
            proposed_task_contracts=tuple(
                task_contract(record, snapshot)
                for record, snapshot in zip(
                    proposed_records, proposed_snapshots, strict=True
                )
            ),
            historical_task_records=(),
            successor_mapping=(
                TaskSuccessorMapping("TASK-024", ("TASK-100",), ("TASK-100",)),
            ),
            proposed_permission_subset=("local_execute",),
            proposed_lineage_budget=active_budget,
        )

        result = validate_recovery_proposal(proposal, registry=self.registry)

        self.assertTrue(result.admissible, [item.message for item in result.issues])
        self.assertEqual(result.current_graph.task_set_digest.value, graph["task_set_sha256"])
        self.assertEqual(len(result.proposed_graph.nodes), 40)


if __name__ == "__main__":
    unittest.main()
