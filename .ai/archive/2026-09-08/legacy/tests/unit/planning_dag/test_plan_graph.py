from __future__ import annotations

import copy
import random
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from contracts import ContractRegistry, structural_task_digest
from domain_values import DomainException, ErrorCategory, PlanId, RecordKind, RecordRef, EntityId
from plan_graph import AcceptedDependency, build_dependency_graph


OID_1 = "1" * 40
OID_2 = "2" * 40


def task_record(
    plan_id: str,
    number: int,
    *,
    dependencies: tuple[int, ...] = (),
    coverage: tuple[str, ...] = ("AC-01",),
    status: str = "backlog",
) -> dict[str, object]:
    task_id = f"TASK-{number:03d}"
    return {
        "schema_version": "1.0",
        "kind": "task",
        "id": task_id,
        "plan_id": plan_id,
        "title": f"Task {number}",
        "status": status,
        "archived": False,
        "objective": f"Implement task {number}",
        "depends_on": [f"TASK-{item:03d}" for item in dependencies],
        "scope": {
            "write_paths": [f"src/task_{number}.py"],
            "read_paths": [],
            "prohibited_paths": [],
            "resources": [],
        },
        "acceptance_criteria": [
            {
                "id": f"{task_id}-AC1",
                "description": "Observable behavior",
                "verification": "Focused tests",
            }
        ],
        "plan_acceptance_ids": list(coverage),
        "spec_refs": [f".ai/plans/current/{plan_id}/spec.json"],
        "adr_refs": [],
        "research_refs": [],
        "input_contracts": [],
        "output_contracts": [],
        "validation_commands": [f"test.{task_id}"],
        "estimated_production_files": 1,
        "size_rationale": "One bounded output",
        "out_of_scope": ["Other modules"],
        "handoff_requirements": ["Test evidence"],
        "attempt_ids": [],
        "superseded_by": [],
        "resume_state": None,
    }


def plan_record(
    plan_id: str,
    tasks: list[dict[str, object]],
    *,
    criteria: tuple[str, ...] = ("AC-01",),
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "kind": "plan",
        "id": plan_id,
        "title": f"Plan {plan_id}",
        "status": "running",
        "archived": False,
        "spec_refs": [f".ai/plans/current/{plan_id}/spec.json"],
        "adr_refs": [],
        "research_refs": [],
        "document_ref": f".ai/plans/current/{plan_id}/plan.md",
        "acceptance_criteria": [
            {
                "id": criterion,
                "description": f"Acceptance {criterion}",
                "verification": "Mapped behavior tests",
            }
            for criterion in criteria
        ],
        "task_ids": [str(task["id"]) for task in tasks],
        "graph_ref": f".ai/plans/current/{plan_id}/graph.json",
        "isolation_review_ref": None,
        "resume_state": None,
        "integration_branch": f"ai/{plan_id}/integration",
        "target_branch": "main",
        "merge_evidence_ref": None,
    }


def graph_record(
    plan_id: str,
    tasks: list[dict[str, object]],
    *,
    nodes: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    if nodes is None:
        nodes = [
            {
                "task_id": task["id"],
                "depends_on": list(task["depends_on"]),
            }
            for task in tasks
        ]
    return {
        "schema_version": "1.0",
        "kind": "task-graph",
        "id": f"{plan_id}-r1",
        "plan_id": plan_id,
        "revision": 1,
        "status": "proposed",
        "nodes": nodes,
        "task_set_sha256": structural_task_digest(tasks),
        "review_ref": None,
    }


def task_ref(plan_id: str, number: int) -> RecordRef:
    return RecordRef(
        kind=RecordKind.TASK,
        plan_id=PlanId(plan_id),
        local_id=EntityId(f"TASK-{number:03d}"),
    )


class PlanGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = ContractRegistry(ROOT / "schemas" / "v1")

    def build(
        self,
        tasks: list[dict[str, object]],
        *,
        plan_id: str = "PLAN-100",
        criteria: tuple[str, ...] = ("AC-01",),
        nodes: list[dict[str, object]] | None = None,
    ):
        plan = plan_record(plan_id, tasks, criteria=criteria)
        graph = graph_record(plan_id, tasks, nodes=nodes)
        return build_dependency_graph(plan, graph, tasks, registry=self.registry)

    def assert_failure(self, action, text: str) -> DomainException:
        with self.assertRaises(DomainException) as raised:
            action()
        self.assertEqual(raised.exception.category, ErrorCategory.VALIDATION_FAILED)
        self.assertIn(text, str(raised.exception))
        return raised.exception

    def test_multiple_plans_can_reuse_local_task_ids_without_identity_collision(self) -> None:
        tasks_a = [task_record("PLAN-100", 1), task_record("PLAN-100", 2, dependencies=(1,))]
        tasks_b = [task_record("PLAN-200", 1), task_record("PLAN-200", 2, dependencies=(1,))]

        graph_a = self.build(tasks_a, plan_id="PLAN-100")
        graph_b = self.build(tasks_b, plan_id="PLAN-200")

        self.assertNotEqual(graph_a.nodes[0].task, graph_b.nodes[0].task)
        self.assertEqual(graph_a.nodes[0].task.local_id, graph_b.nodes[0].task.local_id)
        self.assertEqual(str(graph_a.nodes[0].task), "task:PLAN-100:TASK-001")
        self.assertEqual(str(graph_b.nodes[0].task), "task:PLAN-200:TASK-001")

    def test_cross_plan_task_with_same_bare_id_is_rejected(self) -> None:
        tasks = [task_record("PLAN-200", 1)]
        plan = plan_record("PLAN-100", [task_record("PLAN-100", 1)])
        graph = graph_record("PLAN-100", [task_record("PLAN-100", 1)])

        self.assert_failure(
            lambda: build_dependency_graph(plan, graph, tasks, registry=self.registry),
            "another plan namespace",
        )

    def test_topological_order_and_values_are_deterministic_for_shuffled_inputs(self) -> None:
        tasks = [
            task_record("PLAN-100", 1),
            task_record("PLAN-100", 2),
            task_record("PLAN-100", 3, dependencies=(2, 1)),
            task_record("PLAN-100", 4, dependencies=(3,)),
        ]
        nodes = [
            {"task_id": task["id"], "depends_on": list(reversed(task["depends_on"]))}
            for task in tasks
        ]
        shuffled_tasks = list(tasks)
        shuffled_nodes = list(nodes)
        random.Random(17).shuffle(shuffled_tasks)
        random.Random(29).shuffle(shuffled_nodes)

        first = self.build(tasks, nodes=nodes)
        plan = plan_record("PLAN-100", tasks)
        second_graph_record = graph_record("PLAN-100", tasks, nodes=shuffled_nodes)
        second = build_dependency_graph(
            plan,
            second_graph_record,
            shuffled_tasks,
            registry=self.registry,
        )

        expected = ("TASK-001", "TASK-002", "TASK-003", "TASK-004")
        self.assertEqual(tuple(item.local_id.value for item in first.topological_order), expected)
        self.assertEqual(first, second)
        tasks[0]["id"] = "TASK-999"
        self.assertEqual(first.nodes[0].task.local_id.value, "TASK-001")

    def test_unknown_nodes_dependencies_and_duplicate_membership_fail_closed(self) -> None:
        task = task_record("PLAN-100", 1)
        cases = {
            "unknown local dependencies": (
                [dict(task, depends_on=["TASK-999"])],
                [{"task_id": "TASK-001", "depends_on": ["TASK-999"]}],
            ),
            "membership differ": (
                [task],
                [
                    {"task_id": "TASK-001", "depends_on": []},
                    {"task_id": "TASK-999", "depends_on": []},
                ],
            ),
            "duplicate graph node": (
                [task],
                [
                    {"task_id": "TASK-001", "depends_on": []},
                    {"task_id": "TASK-001", "depends_on": []},
                ],
            ),
        }
        for expected, (tasks, nodes) in cases.items():
            with self.subTest(expected=expected):
                self.assert_failure(lambda: self.build(tasks, nodes=nodes), expected)

    def test_self_dependencies_and_cycles_are_rejected(self) -> None:
        self_task = task_record("PLAN-100", 1, dependencies=(1,))
        self.assert_failure(lambda: self.build([self_task]), "cannot depend on itself")

        cyclic = [
            task_record("PLAN-100", 1, dependencies=(2,)),
            task_record("PLAN-100", 2, dependencies=(1,)),
        ]
        self.assert_failure(lambda: self.build(cyclic), "dependency cycle")

    def test_task_and_graph_edges_must_agree_as_relationships(self) -> None:
        tasks = [task_record("PLAN-100", 1), task_record("PLAN-100", 2, dependencies=(1,))]
        inconsistent = [
            {"task_id": "TASK-001", "depends_on": []},
            {"task_id": "TASK-002", "depends_on": []},
        ]
        self.assert_failure(
            lambda: self.build(tasks, nodes=inconsistent),
            "task and graph dependencies differ",
        )

    def test_duplicate_dependencies_are_rejected(self) -> None:
        tasks = [task_record("PLAN-100", 1), task_record("PLAN-100", 2, dependencies=(1,))]
        duplicate = [
            {"task_id": "TASK-001", "depends_on": []},
            {"task_id": "TASK-002", "depends_on": ["TASK-001", "TASK-001"]},
        ]
        self.assert_failure(lambda: self.build(tasks, nodes=duplicate), "duplicate dependencies")

    def test_acceptance_coverage_is_complete_exact_and_plan_qualified(self) -> None:
        tasks = [
            task_record("PLAN-100", 1, coverage=("AC-01",)),
            task_record("PLAN-100", 2, coverage=("AC-02",)),
        ]
        graph = self.build(tasks, criteria=("AC-01", "AC-02"))
        self.assertEqual(
            tuple(
                (item.acceptance_id.value, tuple(str(task) for task in item.tasks))
                for item in graph.acceptance_coverage
            ),
            (
                ("AC-01", ("task:PLAN-100:TASK-001",)),
                ("AC-02", ("task:PLAN-100:TASK-002",)),
            ),
        )

        gap_tasks = [task_record("PLAN-100", 1, coverage=("AC-01",))]
        raised = self.assert_failure(
            lambda: self.build(gap_tasks, criteria=("AC-01", "AC-02")),
            "acceptance coverage",
        )
        self.assertEqual(raised.error.details["missing_acceptance_ids"], ("AC-02",))

        unknown_tasks = [task_record("PLAN-100", 1, coverage=("AC-99",))]
        raised = self.assert_failure(
            lambda: self.build(unknown_tasks, criteria=("AC-01",)),
            "acceptance coverage",
        )
        self.assertEqual(raised.error.details["unknown_acceptance_ids"], ("AC-99",))

    def test_stale_task_set_digest_is_rejected(self) -> None:
        tasks = [task_record("PLAN-100", 1)]
        plan = plan_record("PLAN-100", tasks)
        graph = graph_record("PLAN-100", tasks)
        graph["task_set_sha256"] = "0" * 64
        self.assert_failure(
            lambda: build_dependency_graph(plan, graph, tasks, registry=self.registry),
            "digest is stale",
        )

    def test_ready_frontier_requires_and_preserves_integration_facts(self) -> None:
        tasks = [
            task_record("PLAN-100", 1, status="accepted"),
            task_record("PLAN-100", 2, dependencies=(1,)),
            task_record("PLAN-100", 3, dependencies=(1,)),
            task_record("PLAN-100", 4, dependencies=(2, 3)),
        ]
        graph = self.build(tasks)

        self.assertEqual(graph.ready_frontier(), ())
        accepted_one = AcceptedDependency(task_ref("PLAN-100", 1), OID_1)
        frontier = graph.ready_frontier([accepted_one])
        self.assertEqual(
            tuple(item.task.local_id.value for item in frontier),
            ("TASK-002", "TASK-003"),
        )
        self.assertTrue(all(item.dependency_facts == (accepted_one,) for item in frontier))

        accepted_two = AcceptedDependency(task_ref("PLAN-100", 2), OID_2)
        frontier = graph.ready_frontier([accepted_two, accepted_one])
        self.assertEqual(tuple(item.task.local_id.value for item in frontier), ("TASK-003",))

        accepted_three = AcceptedDependency(task_ref("PLAN-100", 3), "3" * 64)
        frontier = graph.ready_frontier([accepted_three, accepted_one, accepted_two])
        self.assertEqual(tuple(item.task.local_id.value for item in frontier), ("TASK-004",))
        self.assertEqual(frontier[0].dependency_facts, (accepted_two, accepted_three))

    def test_root_frontier_uses_task_id_order_and_excludes_nondispatchable_statuses(self) -> None:
        tasks = [
            task_record("PLAN-100", 2),
            task_record("PLAN-100", 1),
            task_record("PLAN-100", 3, status="running"),
        ]
        graph = self.build(tasks)
        self.assertEqual(
            tuple(item.task.local_id.value for item in graph.ready_frontier()),
            ("TASK-001", "TASK-002"),
        )

    def test_ready_frontier_rejects_unknown_cross_plan_and_duplicate_facts(self) -> None:
        graph = self.build([task_record("PLAN-100", 1)])
        known = AcceptedDependency(task_ref("PLAN-100", 1), OID_1)
        unknown = AcceptedDependency(task_ref("PLAN-100", 2), OID_2)
        foreign = AcceptedDependency(task_ref("PLAN-200", 1), OID_2)

        for facts, expected in (
            ([known, known], "duplicate accepted integration fact"),
            ([unknown], "unknown task"),
            ([foreign], "another plan namespace"),
        ):
            with self.subTest(expected=expected):
                with self.assertRaises(DomainException) as raised:
                    graph.ready_frontier(facts)
                self.assertEqual(raised.exception.category, ErrorCategory.INVALID_INPUT)
                self.assertIn(expected, str(raised.exception))

    def test_schema_failures_use_the_accepted_contract_registry(self) -> None:
        tasks = [task_record("PLAN-100", 1)]
        tasks[0]["unexpected"] = True
        plan = plan_record("PLAN-100", tasks)
        graph = graph_record("PLAN-100", tasks)
        with self.assertRaises(DomainException) as raised:
            build_dependency_graph(plan, graph, tasks, registry=self.registry)
        self.assertEqual(raised.exception.category, ErrorCategory.VALIDATION_FAILED)
        self.assertIn("contract violation", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
