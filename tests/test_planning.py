from copy import deepcopy
from pathlib import Path

import pytest

from ai_engineering.artifacts import Artifact, ArtifactStore
from ai_engineering.errors import FrameworkError
from ai_engineering.planning import (
    apply_revision,
    decompose,
    parallel_waves,
    persist_decomposition,
    validate_features,
    validate_tasks,
)


def task(number, *, batch="backend", deps=(), scope=None, resources=(), effort=2):
    identifier = f"TASK-{number:03}"
    return Artifact(
        Path(f".ai/tasks/ready/{identifier}.md"),
        {
            "id": identifier,
            "title": f"Implement behavior {number}",
            "status": "ready",
            "plan": "PLAN-001",
            "depends_on": list(deps),
            "batch": batch,
            "effort": effort,
            "scope": scope or [f"src/{batch}/{number}.py"],
            "resources": list(resources),
            "acceptance": [f"Behavior {number} handles the specified failure"],
            "validation": ["tests"],
            "context": ["ARCHITECTURE.md"],
        },
        f"# {identifier}\n",
    )


def installed(tmp_path, tasks):
    store = ArtifactStore(tmp_path)
    store.create(
        "plans", "PLAN-001", "Plan", "ready", tasks=[t.id for t in tasks], scope=["src", "tests"]
    )
    for t in tasks:
        data = deepcopy(t.metadata)
        identifier, title, status = (data.pop(k) for k in ("id", "title", "status"))
        store.create("tasks", identifier, title, status, **data)
    return store, [store.find(t.id) for t in tasks]


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*.md")}


def test_task_validator_reports_malformed_records_cycles_and_unknown_prerequisites():
    first = task(1, deps=["TASK-002"])
    second = task(2, deps=["TASK-001"])
    assert any("cycle" in x.lower() for x in validate_tasks([first, second]))
    second.metadata["depends_on"] = ["TASK-999"]
    assert any("Missing" in x for x in validate_tasks([first, second]))
    for field, value in [
        ("acceptance", []),
        ("effort", 4),
        ("effort", True),
        ("scope", ["../escape"]),
        ("resources", ["api", "api"]),
        ("validation", "pytest"),
        ("status", "superseded"),
    ]:
        malformed = task(1)
        malformed.metadata[field] = value
        assert validate_tasks([malformed]), field
    assert any("duplicate" in x for x in validate_tasks([task(1), task(1)]))
    assert validate_tasks([])


def test_batches_group_coherent_work_preserving_both_dependency_graphs():
    tasks = [
        task(1),
        task(2, deps=["TASK-001"]),
        task(3, batch="frontend"),
        task(4, batch="frontend", deps=["TASK-003"]),
    ]
    features = decompose(tasks)
    assert [f["tasks"] for f in features] == [["TASK-001", "TASK-002"], ["TASK-003", "TASK-004"]]
    assert parallel_waves(features) == [["FEATURE-001", "FEATURE-002"]]
    assert validate_features(tasks, features) == []


def test_interleaved_ownership_does_not_contract_a_dag_into_a_cycle():
    tasks = [task(1), task(2, batch="interface", deps=["TASK-001"]), task(3, deps=["TASK-002"])]
    features = decompose(tasks)
    assert len(features) == 3
    assert parallel_waves(features) == [["FEATURE-001"], ["FEATURE-002"], ["FEATURE-003"]]


def test_batch_limits_are_computed_from_tasks_and_cannot_be_hidden_by_proposal():
    tasks = [task(i, effort=3) for i in range(1, 7)]
    features = decompose(tasks)
    assert len(features) == 3
    assert all(len(f["tasks"]) == 2 and f["effort"] == 6 for f in features)
    assert len(decompose(tasks, max_tasks=1)) == 6
    with pytest.raises(FrameworkError, match="limit"):
        decompose(tasks, max_effort=2)
    features[0]["effort"] = 1
    assert any("effort differs" in x for x in validate_features(tasks, features))


@pytest.mark.parametrize(
    "left,right",
    [
        (["src/Auth"], ["src/auth/session.py"]),
        (["src/auth"], ["src/auth"]),
        (["src/a.py"], ["src/b.py"]),
    ],
)
def test_file_and_schema_interface_conflicts_are_serialized(left, right):
    tasks = [
        task(1, batch="a", scope=left, resources=["schema:account"]),
        task(2, batch="b", scope=right, resources=["schema:account"]),
    ]
    features = decompose(tasks)
    assert parallel_waves(features) == [["FEATURE-001"], ["FEATURE-002"]]
    features[1]["dependencies"] = []
    assert any("ownership conflict" in x for x in validate_features(tasks, features))
    # Scheduling an unapproved proposal still cannot create an unsafe wave.
    assert len(parallel_waves(features)) == 2


def test_path_conflict_is_detected_without_shared_resource_names():
    features = decompose(
        [task(1, batch="a", scope=["src/Api"]), task(2, batch="b", scope=["src/api/request.py"])]
    )
    assert len(parallel_waves(features)) == 2
    independent = decompose(
        [task(1, batch="a", scope=["src/auth"]), task(2, batch="b", scope=["src/authentication"])]
    )
    assert len(parallel_waves(independent)) == 1


def test_proposals_cannot_omit_tasks_requirements_or_dependencies():
    tasks = [task(1), task(2, batch="ui", deps=["TASK-001"])]
    features = decompose(tasks)
    assert validate_features(tasks, features[:-1])
    malformed = deepcopy(features)
    malformed[1]["tasks"].append("TASK-001")
    assert any("exactly once" in x for x in validate_features(tasks, malformed))
    for field, value in [
        ("dependencies", []),
        ("scope", ["src/elsewhere"]),
        ("acceptance", ["Something else"]),
        ("validation", ["unrelated"]),
        ("scope", ["../escape"]),
        ("scope", ["src"]),
    ]:
        malformed = deepcopy(features)
        malformed[1][field] = value
        assert validate_features(tasks, malformed), field
    features[0]["dependencies"] = ["FEATURE-002"]
    assert any("cycle" in x.lower() for x in validate_features(tasks, features))
    with pytest.raises(FrameworkError, match="cycle"):
        parallel_waves(features)


def test_persistence_is_idempotent_and_records_explicit_ai_plan_references(tmp_path):
    store, tasks = installed(tmp_path, [task(1), task(2)])
    proposal = decompose(tasks)
    first = persist_decomposition(store, "PLAN-001", proposal)
    before = snapshot(tmp_path)
    second = persist_decomposition(store, "PLAN-001", proposal)
    assert [f.id for f in first] == [f.id for f in second]
    assert snapshot(tmp_path) == before
    plan = store.find("PLAN-001")
    assert plan.metadata["features"] == ["FEATURE-001"]
    assert plan.metadata["decomposition"].startswith(".ai/handoffs/")
    assert "TASK-001" in first[0].body and "To be defined" not in first[0].body
    assert len(store.list("handoffs")) == 1
    assert not (tmp_path / "docs").exists()


@pytest.mark.parametrize("status", ["in-progress", "review", "blocked", "completed"])
def test_started_features_are_reused_unchanged_but_never_overwritten(tmp_path, status):
    store, tasks = installed(tmp_path, [task(1), task(2)])
    proposals = decompose(tasks)
    first = persist_decomposition(store, "PLAN-001", proposals)[0]
    store.transition(first.id, status)
    before = snapshot(tmp_path)
    assert persist_decomposition(store, "PLAN-001", proposals)[0].status == status
    assert snapshot(tmp_path) == before
    proposals[0]["title"] = "Changed contract"
    with pytest.raises(FrameworkError, match="started/completed"):
        persist_decomposition(store, "PLAN-001", proposals)
    assert snapshot(tmp_path) == before


def test_ready_rebatching_reserves_ids_preserves_history_and_remaps_downstream(tmp_path):
    store, tasks = installed(
        tmp_path,
        [
            task(1),
            task(2, batch="ui", deps=["TASK-001"]),
            task(3, batch="delivery", deps=["TASK-002"]),
        ],
    )
    proposals = decompose(tasks)
    persist_decomposition(store, "PLAN-001", proposals)
    proposals[0]["title"] = "Revised root"
    revised = persist_decomposition(store, "PLAN-001", list(reversed(proposals)))
    assert all(int(f.id.split("-")[-1]) > 3 for f in revised)
    assert all(store.find(f"FEATURE-{n:03}").status == "superseded" for n in range(1, 4))
    assert validate_features(tasks, revised) == []
    assert len(store.list("handoffs")) == 2


def test_invalid_revision_leaves_every_durable_artifact_unchanged(tmp_path):
    store, tasks = installed(tmp_path, [task(1), task(2, batch="ui", deps=["TASK-001"])])
    persist_decomposition(store, "PLAN-001", decompose(tasks))
    before = snapshot(tmp_path)
    invalid = task(3).metadata
    invalid["depends_on"] = ["TASK-999"]
    with pytest.raises(FrameworkError, match="Missing"):
        apply_revision(
            store,
            "PLAN-001",
            {
                "reason": "Hidden prerequisite",
                "replacements": {"TASK-001": ["TASK-003"]},
                "tasks": [invalid],
            },
        )
    assert snapshot(tmp_path) == before
    invalid["depends_on"] = []
    invalid["scope"] = ["private"]
    with pytest.raises(FrameworkError, match="expand"):
        apply_revision(
            store,
            "PLAN-001",
            {"reason": "Expansion", "replacements": {"TASK-001": ["TASK-003"]}, "tasks": [invalid]},
        )
    assert snapshot(tmp_path) == before


def test_split_preserves_completed_work_redirects_edges_and_adds_prerequisites(tmp_path):
    initial = [
        task(1, batch="core"),
        task(2, deps=["TASK-001"]),
        task(3, batch="ui", deps=["TASK-002"]),
    ]
    store, tasks = installed(tmp_path, initial)
    features = persist_decomposition(store, "PLAN-001", decompose(tasks))
    store.transition("TASK-001", "completed")
    completed = store.transition(features[0].id, "completed")
    evidence = {p: p.read_bytes() for p in [completed.path, store.find("TASK-001").path]}
    revision = {
        "reason": "Separate data and API with migration prerequisite",
        "replacements": {"TASK-002": ["TASK-004", "TASK-005"]},
        "tasks": [
            task(4, batch="data", deps=["TASK-006"]).metadata,
            task(5, batch="api", deps=["TASK-004"]).metadata,
            task(6, batch="migration", deps=["TASK-001"]).metadata,
        ],
    }
    result = apply_revision(store, "PLAN-001", revision)
    assert all(p.read_bytes() == content for p, content in evidence.items())
    assert store.find("TASK-002").status == "superseded"
    assert store.find("TASK-002").metadata["replaced_by"] == ["TASK-004", "TASK-005"]
    assert store.find("TASK-003").metadata["depends_on"] == ["TASK-004", "TASK-005"]
    assert set(store.find("TASK-004").metadata["depends_on"]) == {"TASK-001", "TASK-006"}
    plan = store.find("PLAN-001")
    assert set(plan.metadata["tasks"]) == {
        "TASK-001",
        "TASK-003",
        "TASK-004",
        "TASK-005",
        "TASK-006",
    }
    assert validate_features([store.find(t) for t in plan.metadata["tasks"]], result) == []


def test_merge_keeps_external_prerequisites_without_self_dependency(tmp_path):
    store, tasks = installed(
        tmp_path, [task(1, batch="core"), task(2, deps=["TASK-001"]), task(3, deps=["TASK-002"])]
    )
    persist_decomposition(store, "PLAN-001", decompose(tasks))
    result = apply_revision(
        store,
        "PLAN-001",
        {
            "reason": "Tiny related units",
            "replacements": {"TASK-002": ["TASK-004"], "TASK-003": ["TASK-004"]},
            "tasks": [task(4).metadata],
        },
    )
    assert store.find("TASK-004").metadata["depends_on"] == ["TASK-001"]
    assert store.find("TASK-004").metadata["replaces"] == ["TASK-002", "TASK-003"]
    assert validate_features([store.find("TASK-001"), store.find("TASK-004")], result) == []


def test_replacing_adjacent_tasks_preserves_their_original_order(tmp_path):
    store, tasks = installed(tmp_path, [task(1), task(2, batch="api", deps=["TASK-001"])])
    persist_decomposition(store, "PLAN-001", decompose(tasks))
    apply_revision(
        store,
        "PLAN-001",
        {
            "reason": "Rework both boundaries",
            "replacements": {"TASK-001": ["TASK-003"], "TASK-002": ["TASK-004"]},
            "tasks": [task(3).metadata, task(4, batch="api").metadata],
        },
    )
    assert store.find("TASK-004").metadata["depends_on"] == ["TASK-003"]


def test_active_recovery_requires_explicit_stopped_feature_and_keeps_other_agent(tmp_path):
    store, tasks = installed(tmp_path, [task(1), task(2, batch="ui")])
    features = persist_decomposition(store, "PLAN-001", decompose(tasks))
    for f in features:
        store.transition(f.id, "in-progress")
    revision = {
        "reason": "Incorrect backend boundary",
        "replacements": {"TASK-001": ["TASK-003"]},
        "tasks": [task(3).metadata],
    }
    before = snapshot(tmp_path)
    with pytest.raises(FrameworkError, match="started/completed"):
        apply_revision(store, "PLAN-001", revision)
    assert snapshot(tmp_path) == before
    revision["stopped_features"] = [features[0].id]
    result = apply_revision(store, "PLAN-001", revision)
    assert store.find(features[0].id).status == "superseded"
    assert store.find(features[1].id).status == "in-progress"
    assert features[1].id in [f.id for f in result]


def test_completed_tasks_cannot_be_replaced_even_with_stopped_assertion(tmp_path):
    store, tasks = installed(tmp_path, [task(1)])
    feature = persist_decomposition(store, "PLAN-001", decompose(tasks))[0]
    store.transition("TASK-001", "completed")
    store.transition(feature.id, "completed")
    before = snapshot(tmp_path)
    with pytest.raises(FrameworkError, match="lineage"):
        apply_revision(
            store,
            "PLAN-001",
            {
                "reason": "Retry",
                "replacements": {"TASK-001": ["TASK-002"]},
                "tasks": [task(2).metadata],
                "stopped_features": [feature.id],
            },
        )
    assert snapshot(tmp_path) == before


def test_invalid_agent_features_and_missing_template_fail_before_mutation(tmp_path):
    store, tasks = installed(tmp_path, [task(1)])
    persist_decomposition(store, "PLAN-001", decompose(tasks))
    before = snapshot(tmp_path)
    revision = {
        "reason": "Split",
        "replacements": {"TASK-001": ["TASK-002"]},
        "tasks": [task(2).metadata],
        "features": [],
    }
    with pytest.raises(FrameworkError, match="exactly once"):
        apply_revision(store, "PLAN-001", revision)
    assert snapshot(tmp_path) == before
    override = tmp_path / ".ai/templates/handoffs/decomposition.md"
    override.parent.mkdir(parents=True)
    override.write_text("{{ unknown_field }}", encoding="utf-8")
    before = snapshot(tmp_path)
    revision.pop("features")
    with pytest.raises(FrameworkError, match="Missing template values"):
        apply_revision(store, "PLAN-001", revision)
    assert snapshot(tmp_path) == before


def test_synchronous_write_failure_restores_original_artifacts(tmp_path, monkeypatch):
    from ai_engineering import planning

    store, tasks = installed(tmp_path, [task(1)])
    persist_decomposition(store, "PLAN-001", decompose(tasks))
    before = snapshot(tmp_path)
    original = planning.write_artifact
    count = 0

    def failing(*args, **kwargs):
        nonlocal count
        count += 1
        if count == 3:
            raise FrameworkError("Simulated write failure")
        original(*args, **kwargs)

    monkeypatch.setattr(planning, "write_artifact", failing)
    with pytest.raises(FrameworkError, match="Simulated"):
        apply_revision(
            store,
            "PLAN-001",
            {
                "reason": "Replace",
                "replacements": {"TASK-001": ["TASK-002"]},
                "tasks": [task(2).metadata],
            },
        )
    assert snapshot(tmp_path) == before


def test_invalid_provider_unicode_is_rejected_before_any_artifact_write(tmp_path):
    store, tasks = installed(tmp_path, [task(1)])
    persist_decomposition(store, "PLAN-001", decompose(tasks))
    before = snapshot(tmp_path)
    replacement = task(2).metadata
    replacement["title"] = "Bad provider text \ud800"
    with pytest.raises(FrameworkError, match="serialized"):
        apply_revision(
            store,
            "PLAN-001",
            {
                "reason": "Replace",
                "replacements": {"TASK-001": ["TASK-002"]},
                "tasks": [replacement],
            },
        )
    assert snapshot(tmp_path) == before
