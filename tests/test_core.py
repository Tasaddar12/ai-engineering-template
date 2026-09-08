from threading import Thread

import pytest

from ai_engineering.artifacts import ArtifactStore, read_artifact, write_artifact
from ai_engineering.errors import FrameworkError
from ai_engineering.io import parse_yaml, read_yaml, safe_path, write_yaml
from ai_engineering.state import StateStore, reconcile, refresh_index
from ai_engineering.templates import asset_root, render


@pytest.fixture
def project(tmp_path):
    seed = read_yaml(asset_root() / "project/STATE.yaml")
    write_yaml(tmp_path / ".ai/STATE.yaml", seed)
    return tmp_path


def test_yaml_rejects_silent_duplicate_alias_and_object_construction():
    for text in (
        "a: 1\na: 2",
        "a: &a [1]\nb: *a",
        "x: !!python/object/apply:os.system ['echo bad']",
        "[1, 2]",
    ):
        with pytest.raises(FrameworkError):
            parse_yaml(text)
    assert parse_yaml("title: CafÃ©\nitems: [one, two]")["title"] == "CafÃ©"


def test_scope_rejects_absolute_traversal_and_links(tmp_path):
    for name in ("../out", "/tmp/out", "C:\\out", "a/../b", "a:stream", "//host/share", "a/./b"):
        with pytest.raises(FrameworkError):
            safe_path(tmp_path, name)
    assert safe_path(tmp_path, "a/b") == tmp_path / "a/b"
    target = tmp_path / "outside"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Host does not grant symlink creation")
    with pytest.raises(FrameworkError):
        safe_path(tmp_path, "link/file")


def test_markdown_lifecycle_and_duplicate_ids(project):
    store = ArtifactStore(project)
    plan = store.create("plans", "PLAN-001", "A plan", "ready")
    assert plan.path == project / ".ai/plans/active/PLAN-001.md"
    assert plan.metadata["tasks"] == plan.metadata["features"] == []
    task = store.create("tasks", "TASK-001", "A task", "ready", plan=plan.id)
    body = task.body
    moved = store.transition(task.id, "in-progress")
    assert not task.path.exists()
    assert moved.body == body
    with pytest.raises(FrameworkError):
        store.create("tasks", "TASK-001", "Duplicate", "ready", plan=plan.id)
    store.transition(task.id, "completed")
    with pytest.raises(FrameworkError):
        store.transition(task.id, "ready")
    assert store.next_id("TASK") == "TASK-002"
    assert read_artifact(plan.path).metadata["tasks"] == []


def test_plan_hard_requirement_and_escaped_artifact_save(project):
    store = ArtifactStore(project)
    artifact = store.create("plans", "PLAN-001", "Plan", "ready")
    artifact.metadata.pop("features")
    with pytest.raises(FrameworkError, match="features"):
        store.save(artifact)
    artifact.metadata["features"] = []
    artifact.path = project / "docs/PLAN-001.md"
    with pytest.raises(FrameworkError, match=".ai"):
        store.save(artifact)


def test_templates_are_strict_and_project_editable(project):
    with pytest.raises(FrameworkError, match="Missing template"):
        render(project, "plans/plan.md", {"id": "PLAN-001"})
    override = project / ".ai/templates/tasks/task.md"
    override.parent.mkdir(parents=True)
    override.write_text("# {{ title }}\n", encoding="utf-8")
    assert render(project, "tasks/task.md", {"title": "User template"}) == "# User template\n"
    with pytest.raises(FrameworkError):
        render(project, "../STATE.yaml", {})


def test_state_serialization_and_optimistic_generation(project):
    store = StateStore(project)
    first = store.load()
    stale = store.load()
    with store.lock():
        StateStore(project).save(first)  # Same coordinator may enter through another service.
        errors = []

        def contend():
            try:
                with StateStore(project).lock():
                    pass
            except FrameworkError as exc:
                errors.append(str(exc))

        thread = Thread(target=contend)
        thread.start()
        thread.join()
        assert errors
    with pytest.raises(FrameworkError, match="Stale"):
        store.save(stale)


def test_reconciliation_reports_git_drift_without_deletion(project):
    state = StateStore(project)
    value = state.load()
    value["worktrees"] = [
        {"path": ".worktrees/known", "branch": "codex/known", "head": "old"},
        {"path": ".worktrees/missing"},
    ]
    state.save(value)

    class GitFacts:
        def list_worktrees(self):
            return [
                {"path": str(project), "head": "root"},
                {"path": str(project / ".worktrees/unknown"), "head": "new"},
            ]

        def is_ancestor(self, commit, target="HEAD"):
            return False

    before = state.path.read_bytes()
    result = reconcile(project, GitFacts())
    assert len(result["issues"]) == 3
    assert state.path.read_bytes() == before
    reconcile(project, GitFacts(), apply=True)
    assert state.load()["worktrees"] == value["worktrees"]
    assert "reconciliation" in state.load()


def test_refresh_retains_worktree_observations(project):
    store = ArtifactStore(project)
    store.create("plans", "PLAN-001", "Plan", "ready")
    store.create("features", "FEATURE-001", "Feature", "ready", plan="PLAN-001")
    data = refresh_index(project)
    assert data["waiting_features"] == ["FEATURE-001"]
    assert data["worktrees"] == []


def test_low_level_writes_cannot_bypass_planning_location(project):
    metadata = {"id": "PLAN-999", "title": "Plan", "status": "ready", "tasks": [], "features": []}
    with pytest.raises(FrameworkError, match=".ai"):
        write_artifact(project / "docs/PLAN-999.md", metadata, "# Plan")
    assert not (project / "docs").exists()
    metadata.pop("tasks")
    with pytest.raises(FrameworkError, match="tasks"):
        write_artifact(project / ".ai/plans/active/PLAN-999.md", metadata, "# Plan")


def test_save_and_low_level_write_preserve_completed_history(project):
    store = ArtifactStore(project)
    task = store.create("tasks", "TASK-001", "Task", "ready", plan="PLAN-001")
    task = store.transition(task.id, "completed")
    before = task.path.read_bytes()
    task.metadata["status"] = "ready"
    with pytest.raises(FrameworkError, match="immutable"):
        store.save(task)
    task.metadata["status"] = "completed"
    with pytest.raises(FrameworkError, match="immutable"):
        write_artifact(task.path, task.metadata, "Changed history")
    assert task.path.read_bytes() == before


def test_decomposed_plan_requires_tasks_and_features(project):
    store = ArtifactStore(project)
    plan = store.create("plans", "PLAN-001", "Draft", "ready")
    with pytest.raises(FrameworkError, match="nonempty"):
        store.transition(plan.id, "in-progress")
    assert store.find(plan.id).status == "ready"
    plan.metadata.update(tasks=["TASK-001"], decomposition="HANDOFF-001")
    with pytest.raises(FrameworkError, match="features"):
        store.save(plan)


def test_current_git_head_invalidates_two_matching_stale_metadata_heads(project):
    store = ArtifactStore(project)
    store.create(
        "features",
        "FEATURE-001",
        "Feature",
        "review",
        plan="PLAN-001",
        head="old",
        worktree=".worktrees/feature",
        review={"status": "PASS", "head": "old"},
    )
    state = StateStore(project)
    value = state.load()
    value["worktrees"] = [{"path": ".worktrees/feature", "subject": "FEATURE-001", "head": "old"}]
    value["active_features"] = ["FEATURE-001"]
    state.save(value)

    class Facts:
        def list_worktrees(self):
            return [{"path": str(project / ".worktrees/feature"), "head": "new"}]

        def is_ancestor(self, commit, target="HEAD"):
            return False

    result = reconcile(project, Facts())
    assert "Stale feature review: FEATURE-001" in result["issues"]


def test_windows_reserved_names_and_aliases_are_not_portable_paths(project):
    for relative in ("CON", "NUL.txt", "a/COM1", "LPT9.log", "a./b", "b ", "a|b", "a\x01b"):
        with pytest.raises(FrameworkError):
            safe_path(project, relative)


def test_misplaced_record_and_cross_id_save_are_rejected(project):
    store = ArtifactStore(project)
    first = store.create("tasks", "TASK-001", "One", "ready", plan="PLAN-001")
    second = store.create("tasks", "TASK-002", "Two", "ready", plan="PLAN-001")
    first.path = second.path
    with pytest.raises(FrameworkError, match="Duplicate|different"):
        store.save(first)
    assert store.find(second.id).metadata["title"] == "Two"
    misplaced = project / ".ai/tasks/blocked/TASK-002.md"
    misplaced.parent.mkdir(parents=True)
    second.path.rename(misplaced)
    with pytest.raises(FrameworkError, match="misplaced"):
        store.list("tasks")
