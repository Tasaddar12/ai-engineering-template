"""Validated, immutable dependency graphs for one plan namespace.

The graph builder consumes v1 schema-shaped records but exposes plan-qualified
values.  Dependency readiness requires explicit accepted integration facts;
task lifecycle status alone never proves that prerequisite code is present on
the integration branch.
"""
from __future__ import annotations

import heapq
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import cast

from contracts import ContractRegistry, structural_task_digest
from domain_values import (
    DomainError,
    DomainException,
    EntityId,
    ErrorCategory,
    GraphStatus,
    PlanId,
    RecordKind,
    RecordRef,
    Revision,
    Sha256Digest,
    TaskStatus,
)


_TASK_ID = re.compile(r"TASK-[0-9]{3,}\Z")
_GIT_OID = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})\Z")
_DISPATCHABLE_STATUSES = frozenset({TaskStatus.BACKLOG, TaskStatus.READY})


def _failure(message: str, *, details: Mapping[str, object] | None = None) -> DomainException:
    return DomainException(
        DomainError(
            category=ErrorCategory.VALIDATION_FAILED,
            message=message,
            details={} if details is None else details,
        )
    )


def _input_failure(message: str, *, details: Mapping[str, object] | None = None) -> DomainException:
    return DomainException(
        DomainError(
            category=ErrorCategory.INVALID_INPUT,
            message=message,
            details={} if details is None else details,
        )
    )


def _task_ref(plan_id: PlanId, task_id: str) -> RecordRef:
    return RecordRef(
        kind=RecordKind.TASK,
        plan_id=plan_id,
        local_id=EntityId(task_id),
    )


def _task_ref_id(reference: RecordRef, *, plan_id: PlanId) -> str:
    if not isinstance(reference, RecordRef) or reference.kind != RecordKind.TASK.value:
        raise _input_failure("task reference must be a plan-qualified task RecordRef")
    if reference.plan_id != plan_id:
        raise _input_failure(
            f"task reference {reference} belongs to another plan namespace",
            details={"expected_plan_id": plan_id.value, "task_ref": str(reference)},
        )
    return reference.local_id.value


def _tuple_input(values: Iterable[object], *, label: str) -> tuple[object, ...]:
    if isinstance(values, (str, bytes, bytearray, Mapping)):
        raise _input_failure(f"{label} must be an iterable, not a scalar or mapping")
    try:
        return tuple(values)
    except TypeError as exc:
        raise _input_failure(f"{label} must be iterable") from exc


@dataclass(frozen=True, slots=True)
class DependencyNode:
    """One task and its direct dependencies in a plan-qualified namespace."""

    task: RecordRef
    dependencies: tuple[RecordRef, ...]
    status: TaskStatus
    plan_acceptance_ids: tuple[EntityId, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.task, RecordRef) or self.task.kind != RecordKind.TASK.value:
            raise TypeError("task must be a task RecordRef")
        if not self.task.is_plan_qualified:
            raise ValueError("task must be plan-qualified")
        dependencies = tuple(self.dependencies)
        if not all(isinstance(item, RecordRef) for item in dependencies):
            raise TypeError("dependencies must contain RecordRef values")
        if any(item.kind != RecordKind.TASK.value for item in dependencies):
            raise ValueError("dependencies must contain task references")
        if any(item.plan_id != self.task.plan_id for item in dependencies):
            raise ValueError("dependencies must share the task plan namespace")
        if self.task in dependencies:
            raise ValueError("a task cannot depend on itself")
        if len(set(dependencies)) != len(dependencies):
            raise ValueError("dependencies must be unique")
        status = self.status if isinstance(self.status, TaskStatus) else TaskStatus(self.status)
        acceptance_ids = tuple(
            item if isinstance(item, EntityId) else EntityId(item)
            for item in self.plan_acceptance_ids
        )
        object.__setattr__(self, "dependencies", dependencies)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "plan_acceptance_ids", acceptance_ids)


@dataclass(frozen=True, slots=True)
class AcceptanceCoverage:
    """The plan-qualified tasks that cover one plan acceptance criterion."""

    acceptance_id: EntityId
    tasks: tuple[RecordRef, ...]

    def __post_init__(self) -> None:
        acceptance_id = (
            self.acceptance_id
            if isinstance(self.acceptance_id, EntityId)
            else EntityId(self.acceptance_id)
        )
        tasks = tuple(self.tasks)
        if not tasks or not all(isinstance(item, RecordRef) for item in tasks):
            raise ValueError("acceptance coverage requires task RecordRef values")
        if any(item.kind != RecordKind.TASK.value or not item.is_plan_qualified for item in tasks):
            raise ValueError("acceptance coverage tasks must be plan-qualified task references")
        if any(item.plan_id != tasks[0].plan_id for item in tasks):
            raise ValueError("acceptance coverage tasks must share one plan namespace")
        if len(set(tasks)) != len(tasks):
            raise ValueError("acceptance coverage tasks must be unique")
        object.__setattr__(self, "acceptance_id", acceptance_id)
        object.__setattr__(self, "tasks", tasks)


@dataclass(frozen=True, slots=True)
class AcceptedDependency:
    """Observed accepted task code integrated at a concrete Git commit."""

    task: RecordRef
    integration_commit: str

    def __post_init__(self) -> None:
        if not isinstance(self.task, RecordRef) or self.task.kind != RecordKind.TASK.value:
            raise TypeError("accepted dependency task must be a task RecordRef")
        if not self.task.is_plan_qualified:
            raise ValueError("accepted dependency task must be plan-qualified")
        if not isinstance(self.integration_commit, str) or _GIT_OID.fullmatch(
            self.integration_commit
        ) is None:
            raise ValueError("integration_commit must be a full lowercase Git object ID")


@dataclass(frozen=True, slots=True)
class ReadyTask:
    """A dispatchable task with the exact facts satisfying its dependencies."""

    task: RecordRef
    dependency_facts: tuple[AcceptedDependency, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.task, RecordRef) or self.task.kind != RecordKind.TASK.value:
            raise TypeError("ready task must be a task RecordRef")
        if not self.task.is_plan_qualified:
            raise ValueError("ready task must be plan-qualified")
        facts = tuple(self.dependency_facts)
        if not all(isinstance(item, AcceptedDependency) for item in facts):
            raise TypeError("dependency_facts must contain AcceptedDependency values")
        if any(item.task.plan_id != self.task.plan_id for item in facts):
            raise ValueError("dependency facts must share the ready task plan namespace")
        object.__setattr__(self, "dependency_facts", facts)


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    """A schema-valid, acceptance-complete DAG for exactly one plan."""

    plan_id: PlanId
    graph_id: EntityId
    revision: Revision
    status: GraphStatus
    task_set_digest: Sha256Digest
    nodes: tuple[DependencyNode, ...]
    topological_order: tuple[RecordRef, ...]
    acceptance_coverage: tuple[AcceptanceCoverage, ...]
    _node_ids: frozenset[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        plan_id = self.plan_id if isinstance(self.plan_id, PlanId) else PlanId(self.plan_id)
        graph_id = self.graph_id if isinstance(self.graph_id, EntityId) else EntityId(self.graph_id)
        revision = self.revision if isinstance(self.revision, Revision) else Revision(self.revision)
        status = self.status if isinstance(self.status, GraphStatus) else GraphStatus(self.status)
        digest = (
            self.task_set_digest
            if isinstance(self.task_set_digest, Sha256Digest)
            else Sha256Digest(self.task_set_digest)
        )
        nodes = tuple(self.nodes)
        order = tuple(self.topological_order)
        coverage = tuple(self.acceptance_coverage)
        if not all(isinstance(node, DependencyNode) for node in nodes):
            raise TypeError("nodes must contain DependencyNode values")
        if not all(isinstance(item, RecordRef) for item in order):
            raise TypeError("topological_order must contain RecordRef values")
        if not all(isinstance(item, AcceptanceCoverage) for item in coverage):
            raise TypeError("acceptance_coverage must contain AcceptanceCoverage values")
        if any(node.task.plan_id != plan_id for node in nodes):
            raise ValueError("all graph nodes must share plan_id")
        node_ids = frozenset(node.task.local_id.value for node in nodes)
        if len(node_ids) != len(nodes):
            raise ValueError("graph nodes must be unique")
        if {item.local_id.value for item in order} != node_ids or len(order) != len(nodes):
            raise ValueError("topological_order must contain every graph task exactly once")
        if any(item.plan_id != plan_id or item.kind != RecordKind.TASK.value for item in order):
            raise ValueError("topological_order tasks must share the graph plan namespace")
        positions = {item.local_id.value: index for index, item in enumerate(order)}
        for node in nodes:
            for dependency in node.dependencies:
                dependency_id = dependency.local_id.value
                if dependency_id not in node_ids:
                    raise ValueError("graph dependencies must refer to graph nodes")
                if positions[dependency_id] >= positions[node.task.local_id.value]:
                    raise ValueError("topological_order must place dependencies before dependents")
        if any(
            task.plan_id != plan_id or task.local_id.value not in node_ids
            for item in coverage
            for task in item.tasks
        ):
            raise ValueError("acceptance coverage must refer to tasks in this graph")
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "graph_id", graph_id)
        object.__setattr__(self, "revision", revision)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "task_set_digest", digest)
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "topological_order", order)
        object.__setattr__(self, "acceptance_coverage", coverage)
        object.__setattr__(self, "_node_ids", node_ids)

    def node(self, task: RecordRef) -> DependencyNode:
        """Return one node, requiring its fully qualified task identity."""
        task_id = _task_ref_id(task, plan_id=self.plan_id)
        for node in self.nodes:
            if node.task.local_id.value == task_id:
                return node
        raise _input_failure(
            f"unknown task reference {task}",
            details={"plan_id": self.plan_id.value, "task_id": task_id},
        )

    def ready_frontier(
        self,
        accepted_integrated: Iterable[AcceptedDependency] = (),
    ) -> tuple[ReadyTask, ...]:
        """Return dispatchable nodes whose dependencies are integrated.

        Explicit integration facts are authoritative for dependency satisfaction.
        Accepted or completed task status without such a fact cannot unlock a
        dependent task.  Each result retains the direct facts that made it ready.
        """
        raw_facts = _tuple_input(accepted_integrated, label="accepted_integrated")
        facts_by_id: dict[str, AcceptedDependency] = {}
        for fact in raw_facts:
            if not isinstance(fact, AcceptedDependency):
                raise _input_failure(
                    "accepted_integrated must contain AcceptedDependency values"
                )
            task_id = _task_ref_id(fact.task, plan_id=self.plan_id)
            if task_id not in self._node_ids:
                raise _input_failure(
                    f"accepted integration fact references unknown task {fact.task}",
                    details={"plan_id": self.plan_id.value, "task_id": task_id},
                )
            if task_id in facts_by_id:
                raise _input_failure(
                    f"duplicate accepted integration fact for {fact.task}",
                    details={"plan_id": self.plan_id.value, "task_id": task_id},
                )
            facts_by_id[task_id] = fact

        ready: list[ReadyTask] = []
        for node in self.nodes:
            task_id = node.task.local_id.value
            if task_id in facts_by_id or node.status not in _DISPATCHABLE_STATUSES:
                continue
            dependency_ids = tuple(item.local_id.value for item in node.dependencies)
            if all(task_id in facts_by_id for task_id in dependency_ids):
                ready.append(
                    ReadyTask(
                        task=node.task,
                        dependency_facts=tuple(facts_by_id[item] for item in dependency_ids),
                    )
                )
        return tuple(ready)


def build_dependency_graph(
    plan: Mapping[str, object],
    graph: Mapping[str, object],
    tasks: Iterable[Mapping[str, object]],
    *,
    registry: ContractRegistry,
) -> DependencyGraph:
    """Validate records and build one deterministic plan dependency graph."""
    if not isinstance(registry, ContractRegistry):
        raise _input_failure("registry must be an accepted ContractRegistry")
    if not isinstance(plan, Mapping) or not isinstance(graph, Mapping):
        raise _input_failure("plan and graph must be record mappings")
    raw_tasks = _tuple_input(tasks, label="tasks")
    if not raw_tasks:
        raise _failure("a dependency graph requires at least one task")
    if not all(isinstance(task, Mapping) for task in raw_tasks):
        raise _input_failure("tasks must contain record mappings")

    registry.validate(plan, source="plan")
    registry.validate(graph, source="task graph")
    for index, task in enumerate(raw_tasks):
        registry.validate(task, source=f"task[{index}]")

    plan_id = PlanId(str(plan["id"]))
    graph_plan_id = PlanId(str(graph["plan_id"]))
    if graph_plan_id != plan_id:
        raise _failure(
            f"graph belongs to {graph_plan_id}, expected {plan_id}",
            details={"graph_plan_id": graph_plan_id.value, "plan_id": plan_id.value},
        )

    task_records: dict[str, Mapping[str, object]] = {}
    for task in raw_tasks:
        task_id = str(task["id"])
        task_plan_id = PlanId(str(task["plan_id"]))
        if task_plan_id != plan_id:
            raise _failure(
                f"task {task_id} belongs to another plan namespace {task_plan_id}",
                details={
                    "expected_plan_id": plan_id.value,
                    "task_id": task_id,
                    "task_plan_id": task_plan_id.value,
                },
            )
        if task_id in task_records:
            raise _failure(
                f"duplicate task record {plan_id}/{task_id}",
                details={"plan_id": plan_id.value, "task_id": task_id},
            )
        if bool(task["archived"]) or str(task["status"]) == TaskStatus.SUPERSEDED.value:
            raise _failure(
                f"graph cannot contain excluded task {plan_id}/{task_id}",
                details={"plan_id": plan_id.value, "task_id": task_id},
            )
        task_records[task_id] = task

    declared_task_ids = tuple(str(item) for item in plan["task_ids"])
    if len(set(declared_task_ids)) != len(declared_task_ids):
        raise _failure(f"plan {plan_id} declares duplicate task IDs")

    graph_edges: dict[str, tuple[str, ...]] = {}
    raw_nodes = cast(Iterable[Mapping[str, object]], graph["nodes"])
    for node in raw_nodes:  # registry validation established the mapping shape
        task_id = str(node["task_id"])
        dependencies = tuple(str(item) for item in cast(Iterable[object], node["depends_on"]))
        if task_id in graph_edges:
            raise _failure(
                f"duplicate graph node {plan_id}/{task_id}",
                details={"plan_id": plan_id.value, "task_id": task_id},
            )
        if len(set(dependencies)) != len(dependencies):
            raise _failure(
                f"graph node {plan_id}/{task_id} has duplicate dependencies",
                details={"plan_id": plan_id.value, "task_id": task_id},
            )
        graph_edges[task_id] = dependencies

    expected_ids = set(declared_task_ids)
    actual_ids = set(task_records)
    graph_ids = set(graph_edges)
    if expected_ids != actual_ids or expected_ids != graph_ids:
        raise _failure(
            f"plan, task, and graph membership differ for {plan_id}",
            details={
                "graph_only": sorted(graph_ids - expected_ids),
                "missing_graph_nodes": sorted(expected_ids - graph_ids),
                "missing_task_records": sorted(expected_ids - actual_ids),
                "task_records_not_in_plan": sorted(actual_ids - expected_ids),
            },
        )

    canonical_edges: dict[str, tuple[str, ...]] = {}
    for task_id in sorted(actual_ids):
        task_dependencies = tuple(str(item) for item in task_records[task_id]["depends_on"])
        graph_dependencies = graph_edges[task_id]
        if len(set(task_dependencies)) != len(task_dependencies):
            raise _failure(
                f"task {plan_id}/{task_id} has duplicate dependencies",
                details={"plan_id": plan_id.value, "task_id": task_id},
            )
        if task_id in task_dependencies or task_id in graph_dependencies:
            raise _failure(
                f"task {plan_id}/{task_id} cannot depend on itself",
                details={"plan_id": plan_id.value, "task_id": task_id},
            )
        unknown = (set(task_dependencies) | set(graph_dependencies)) - actual_ids
        if unknown:
            raise _failure(
                f"task {plan_id}/{task_id} references unknown local dependencies",
                details={
                    "plan_id": plan_id.value,
                    "task_id": task_id,
                    "unknown_dependencies": sorted(unknown),
                },
            )
        if set(task_dependencies) != set(graph_dependencies):
            raise _failure(
                f"task and graph dependencies differ for {plan_id}/{task_id}",
                details={
                    "graph_dependencies": sorted(graph_dependencies),
                    "plan_id": plan_id.value,
                    "task_dependencies": sorted(task_dependencies),
                    "task_id": task_id,
                },
            )
        canonical_edges[task_id] = tuple(sorted(task_dependencies))

    topological_ids = _topological_order(plan_id, canonical_edges)

    raw_criteria = cast(Iterable[Mapping[str, object]], plan["acceptance_criteria"])
    criteria = tuple(str(item["id"]) for item in raw_criteria)
    if len(set(criteria)) != len(criteria):
        raise _failure(f"plan {plan_id} declares duplicate acceptance criteria")
    coverage: dict[str, list[str]] = {criterion: [] for criterion in criteria}
    unknown_criteria: set[str] = set()
    for task_id in sorted(actual_ids):
        mapped = tuple(str(item) for item in task_records[task_id]["plan_acceptance_ids"])
        if len(set(mapped)) != len(mapped):
            raise _failure(
                f"task {plan_id}/{task_id} repeats a plan acceptance mapping",
                details={"plan_id": plan_id.value, "task_id": task_id},
            )
        for criterion in mapped:
            if criterion in coverage:
                coverage[criterion].append(task_id)
            else:
                unknown_criteria.add(criterion)
    missing_criteria = sorted(item for item, task_ids in coverage.items() if not task_ids)
    if missing_criteria or unknown_criteria:
        raise _failure(
            f"acceptance coverage is incomplete or inconsistent for {plan_id}",
            details={
                "missing_acceptance_ids": missing_criteria,
                "unknown_acceptance_ids": sorted(unknown_criteria),
            },
        )

    computed_digest = Sha256Digest(structural_task_digest(raw_tasks))
    declared_digest = Sha256Digest(str(graph["task_set_sha256"]))
    if computed_digest != declared_digest:
        raise _failure(
            f"task graph digest is stale for {plan_id}",
            details={
                "computed_digest": computed_digest.value,
                "declared_digest": declared_digest.value,
                "plan_id": plan_id.value,
            },
        )

    references = {task_id: _task_ref(plan_id, task_id) for task_id in sorted(actual_ids)}
    nodes = tuple(
        DependencyNode(
            task=references[task_id],
            dependencies=tuple(references[item] for item in canonical_edges[task_id]),
            status=TaskStatus(str(task_records[task_id]["status"])),
            plan_acceptance_ids=tuple(
                EntityId(str(item)) for item in task_records[task_id]["plan_acceptance_ids"]
            ),
        )
        for task_id in sorted(actual_ids)
    )
    acceptance_coverage = tuple(
        AcceptanceCoverage(
            acceptance_id=EntityId(criterion),
            tasks=tuple(references[task_id] for task_id in coverage[criterion]),
        )
        for criterion in criteria
    )
    return DependencyGraph(
        plan_id=plan_id,
        graph_id=EntityId(str(graph["id"])),
        revision=Revision(int(graph["revision"])),
        status=GraphStatus(str(graph["status"])),
        task_set_digest=declared_digest,
        nodes=nodes,
        topological_order=tuple(references[item] for item in topological_ids),
        acceptance_coverage=acceptance_coverage,
    )


def _topological_order(
    plan_id: PlanId,
    dependencies: Mapping[str, tuple[str, ...]],
) -> tuple[str, ...]:
    dependents: dict[str, list[str]] = {task_id: [] for task_id in dependencies}
    remaining = {task_id: len(items) for task_id, items in dependencies.items()}
    for task_id, prerequisites in dependencies.items():
        for prerequisite in prerequisites:
            dependents[prerequisite].append(task_id)

    ready = [task_id for task_id, count in remaining.items() if count == 0]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        task_id = heapq.heappop(ready)
        ordered.append(task_id)
        for dependent in sorted(dependents[task_id]):
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                heapq.heappush(ready, dependent)

    if len(ordered) != len(dependencies):
        cycle_nodes = sorted(task_id for task_id, count in remaining.items() if count > 0)
        raise _failure(
            f"dependency cycle detected in {plan_id}",
            details={"cycle_nodes": cycle_nodes, "plan_id": plan_id.value},
        )
    return tuple(ordered)


__all__ = [
    "AcceptanceCoverage",
    "AcceptedDependency",
    "DependencyGraph",
    "DependencyNode",
    "ReadyTask",
    "build_dependency_graph",
]
