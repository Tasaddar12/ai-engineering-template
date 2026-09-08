from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import ai
import contracts
import install
import validate_foundation
from domain_values import (
    DomainException,
    EntityId,
    ErrorCategory,
    FrozenJsonObject,
    PlanId,
    RecordKind,
    RecordRef,
)


SCHEMAS = ROOT / "schemas" / "v1"
EXAMPLES = ROOT / "schemas" / "examples"
APPROVED_TASK_DIGEST = "c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e"


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected object in {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_strings(value: object, old: str, new: str) -> object:
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [replace_strings(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: replace_strings(item, old, new) for key, item in value.items()}
    return value


class OfflineContractRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = contracts.load_contract_registry(SCHEMAS)

    def test_registry_loads_every_v1_schema_and_validates_all_examples(self) -> None:
        expected = {
            path.name.removesuffix(".schema.json")
            for path in SCHEMAS.glob("*.schema.json")
        }
        self.assertEqual(set(self.registry.kinds), expected)
        self.assertEqual(len(self.registry.schema_ids), len(expected))
        for path in sorted(EXAMPLES.glob("*.json")):
            with self.subTest(path=path.name):
                self.registry.validate(read_json(path), source=path.name)

    def test_unknown_top_level_and_nested_fields_are_rejected(self) -> None:
        artifact = read_json(EXAMPLES / "task.json")
        for mutate in (
            lambda value: value.__setitem__("unknown", True),
            lambda value: value["scope"].__setitem__("unknown", True),
        ):
            with self.subTest(mutate=mutate):
                changed = copy.deepcopy(artifact)
                mutate(changed)
                with self.assertRaises(DomainException) as raised:
                    self.registry.validate(changed)
                self.assertEqual(raised.exception.category, ErrorCategory.VALIDATION_FAILED)

    def test_immutable_shared_json_values_validate_with_typed_value_parity(self) -> None:
        artifact = read_json(EXAMPLES / "spec.json")
        self.registry.validate(FrozenJsonObject(artifact))

    def test_returned_schema_is_detached_from_the_live_validator(self) -> None:
        schema = self.registry.schema("spec")
        schema["properties"]["title"]["type"] = "integer"
        changed = read_json(EXAMPLES / "spec.json")
        changed["title"] = 7
        with self.assertRaises(DomainException) as raised:
            self.registry.validate(changed)
        self.assertEqual(raised.exception.category, ErrorCategory.VALIDATION_FAILED)

    def test_unsupported_versions_and_kinds_fail_with_typed_errors(self) -> None:
        artifact = read_json(EXAMPLES / "task.json")
        for field, value in (("schema_version", "2.0"), ("kind", "future-record")):
            with self.subTest(field=field):
                changed = copy.deepcopy(artifact)
                changed[field] = value
                with self.assertRaises(DomainException) as raised:
                    self.registry.validate(changed)
                self.assertEqual(raised.exception.category, ErrorCategory.UNSUPPORTED_CAPABILITY)

    def test_registry_rejects_nonlocal_schema_references_without_network_access(self) -> None:
        with tempfile.TemporaryDirectory(prefix="offline-schema-test-") as temporary:
            schema_root = Path(temporary) / "v1"
            shutil.copytree(SCHEMAS, schema_root)
            path = schema_root / "agent-models.schema.json"
            schema = read_json(path)
            schema["properties"]["providers"]["properties"]["openai"]["$ref"] = (
                "https://schemas.example.invalid/provider.json"
            )
            write_json(path, schema)
            with patch("socket.create_connection") as connect:
                with self.assertRaises(DomainException) as raised:
                    contracts.load_contract_registry(schema_root)
            connect.assert_not_called()
            self.assertEqual(raised.exception.category, ErrorCategory.UNSUPPORTED_CAPABILITY)

    def test_dynamic_and_broken_local_references_raise_typed_errors(self) -> None:
        with tempfile.TemporaryDirectory(prefix="schema-reference-test-") as temporary:
            schema_root = Path(temporary) / "v1"
            shutil.copytree(SCHEMAS, schema_root)
            path = schema_root / "spec.schema.json"
            schema = read_json(path)
            schema["$dynamicRef"] = "https://schemas.example.invalid/unavailable"
            write_json(path, schema)
            with self.assertRaises(DomainException) as raised:
                contracts.load_contract_registry(schema_root)
            self.assertEqual(raised.exception.category, ErrorCategory.UNSUPPORTED_CAPABILITY)

            del schema["$dynamicRef"]
            schema["allOf"] = [{"$ref": "#/$defs/does-not-exist"}]
            write_json(path, schema)
            registry = contracts.load_contract_registry(schema_root)
            with self.assertRaises(DomainException) as raised:
                registry.validate(read_json(EXAMPLES / "spec.json"))
            self.assertEqual(raised.exception.category, ErrorCategory.VALIDATION_FAILED)

    def test_foundation_validator_discovers_review_subdirectory_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="artifact-discovery-test-") as temporary:
            project = Path(temporary) / "project"
            install.install(str(project), "codex")
            self.assertEqual(
                ai.main(
                    [
                        "--project",
                        str(project),
                        "plan",
                        "create",
                        "PLAN-101",
                        "--title",
                        "Artifact discovery",
                    ]
                ),
                0,
            )
            candidate = read_json(EXAMPLES / "candidate.json")
            candidate["plan_id"] = "PLAN-101"
            path = project / ".codex/plans/current/PLAN-101/reviews/candidates/CANDIDATE.json"
            path.parent.mkdir(parents=True)
            write_json(path, candidate)
            validate_foundation.validate(project)

            candidate["unexpected"] = True
            write_json(path, candidate)
            with self.assertRaisesRegex(
                validate_foundation.ValidationFailure,
                "Additional properties are not allowed",
            ):
                validate_foundation.validate(project)


class LogicalReferenceTests(unittest.TestCase):
    def test_parser_has_shared_value_parity(self) -> None:
        parsed = contracts.parse_record_ref(
            "task:PLAN-101:TASK-001",
            expected_plan_id="PLAN-101",
            expected_kind=RecordKind.TASK.value,
        )
        self.assertEqual(
            parsed,
            RecordRef(
                kind=RecordKind.TASK,
                plan_id=PlanId("PLAN-101"),
                local_id=EntityId("TASK-001"),
            ),
        )
        self.assertEqual(str(parsed), "task:PLAN-101:TASK-001")

    def test_plan_owned_reference_cannot_be_unqualified(self) -> None:
        with self.assertRaises(DomainException) as raised:
            contracts.parse_record_ref("task:TASK-001")
        self.assertEqual(raised.exception.category, ErrorCategory.INVALID_INPUT)

    def test_same_local_id_in_two_plans_does_not_collide(self) -> None:
        first = contracts.parse_record_ref("task:PLAN-101:TASK-001")
        second = contracts.parse_record_ref("task:PLAN-102:TASK-001")
        self.assertNotEqual(first.key, second.key)
        with self.assertRaises(DomainException) as raised:
            contracts.parse_record_ref(first.__str__(), expected_plan_id="PLAN-102")
        self.assertEqual(raised.exception.category, ErrorCategory.INVALID_INPUT)


class StructuralDigestTests(unittest.TestCase):
    def test_current_records_preserve_the_approved_bootstrap_digest_exactly(self) -> None:
        tasks = [
            read_json(path)
            for path in (ROOT / ".ai/plans/current/PLAN-001/tasks/current").glob("TASK-*.json")
        ]
        self.assertEqual(ai.structural_task_digest(tasks), APPROVED_TASK_DIGEST)
        self.assertEqual(contracts.structural_task_digest(tasks), APPROVED_TASK_DIGEST)

    def test_only_known_plan_and_task_lifecycle_locations_are_canonicalized(self) -> None:
        task = read_json(EXAMPLES / "task.json")
        task["spec_refs"] = [".codex/plans/current/PLAN-101/spec.json"]
        task["input_contracts"] = [
            ".codex/plans/current/PLAN-101/tasks/current/TASK-001.json"
        ]
        task["scope"]["read_paths"] = [
            ".codex/plans/current/PLAN-101/tasks/current/"
        ]
        current = contracts.structural_task_digest([task])
        moved = replace_strings(task, ".codex/plans/current/PLAN-101", ".codex/plans/completed/PLAN-101")
        moved = replace_strings(moved, "/tasks/current/TASK-001", "/tasks/archived/TASK-001")
        moved = replace_strings(moved, "/tasks/current/", "/tasks/completed/")
        self.assertEqual(contracts.structural_task_digest([moved]), current)

        changed = copy.deepcopy(moved)
        changed["scope"]["write_paths"][0] = "src/changed_structure.py"
        self.assertNotEqual(contracts.structural_task_digest([changed]), current)

        unrelated = copy.deepcopy(task)
        unrelated["title"] = "src/.codex/plans/current/PLAN-101/spec.json"
        unrelated_moved = copy.deepcopy(unrelated)
        unrelated_moved["title"] = "src/.codex/plans/completed/PLAN-101/spec.json"
        self.assertNotEqual(
            contracts.structural_task_digest([unrelated_moved]),
            contracts.structural_task_digest([unrelated]),
        )

        url = copy.deepcopy(task)
        url["title"] = "https://example.invalid/.codex/plans/current/PLAN-101/spec.json"
        url_moved = copy.deepcopy(url)
        url_moved["title"] = "https://example.invalid/.codex/plans/completed/PLAN-101/spec.json"
        self.assertNotEqual(
            contracts.structural_task_digest([url_moved]),
            contracts.structural_task_digest([url]),
        )

        prose = copy.deepcopy(task)
        prose["objective"] = (
            ".codex/plans/current/PLAN-101/spec.json must remain the selected active specification."
        )
        changed_prose = copy.deepcopy(prose)
        changed_prose["objective"] = prose["objective"].replace("/current/", "/completed/")
        self.assertNotEqual(
            contracts.structural_task_digest([changed_prose]),
            contracts.structural_task_digest([prose]),
        )

    def test_approved_graph_rejects_lifecycle_like_objective_prose_change(self) -> None:
        with tempfile.TemporaryDirectory(prefix="approved-digest-test-") as temporary:
            project = Path(temporary) / "project"
            install.install(str(project), "codex")
            self.assertEqual(
                ai.main(
                    [
                        "--project",
                        str(project),
                        "plan",
                        "create",
                        "PLAN-101",
                        "--title",
                        "Approval boundary",
                    ]
                ),
                0,
            )
            bundle = project / ".codex/plans/current/PLAN-101"
            task_path = bundle / "tasks/current/TASK-001.json"
            task = read_json(task_path)
            task["objective"] = (
                ".codex/plans/current/PLAN-101/spec.json must remain the selected active specification."
            )
            write_json(task_path, task)

            graph_path = bundle / "graph.json"
            graph = read_json(graph_path)
            graph["status"] = "approved"
            graph["task_set_sha256"] = contracts.structural_task_digest([task])
            graph["review_ref"] = (
                ".codex/plans/current/PLAN-101/reviews/isolation-review.json"
            )
            write_json(graph_path, graph)
            review = read_json(EXAMPLES / "isolation-review.json")
            review["plan_id"] = "PLAN-101"
            review["graph_revision"] = graph["revision"]
            review["task_set_sha256"] = graph["task_set_sha256"]
            review["verdict"] = "pass"
            write_json(project / graph["review_ref"], review)
            plan_path = bundle / "plan.json"
            plan = read_json(plan_path)
            plan["isolation_review_ref"] = graph["review_ref"]
            write_json(plan_path, plan)
            validate_foundation.validate(project)

            task["objective"] = task["objective"].replace("/current/", "/completed/")
            write_json(task_path, task)
            with self.assertRaisesRegex(
                validate_foundation.ValidationFailure,
                "stale structural task digest",
            ):
                validate_foundation.validate(project)

    def test_relocated_bundle_retains_approval_but_structure_change_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="digest-relocation-test-") as temporary:
            project = Path(temporary) / "project"
            install.install(str(project), "codex")
            self.assertEqual(
                ai.main(
                    [
                        "--project",
                        str(project),
                        "plan",
                        "create",
                        "PLAN-101",
                        "--title",
                        "Relocation plan",
                    ]
                ),
                0,
            )
            current = project / ".codex/plans/current/PLAN-101"
            task_path = current / "tasks/current/TASK-001.json"
            task = read_json(task_path)
            task["input_contracts"] = [
                ".codex/plans/current/PLAN-101/tasks/current/TASK-001.json"
            ]
            task["scope"]["read_paths"] = [
                ".codex/plans/current/PLAN-101/tasks/current/"
            ]
            write_json(task_path, task)
            graph_path = current / "graph.json"
            graph = read_json(graph_path)
            graph["task_set_sha256"] = ai.structural_task_digest([task])
            write_json(graph_path, graph)
            validate_foundation.validate(project)

            completed = project / ".codex/plans/completed/PLAN-101"
            completed.parent.mkdir(parents=True, exist_ok=True)
            current.rename(completed)
            for path in sorted(completed.rglob("*.json")):
                value = replace_strings(
                    read_json(path),
                    ".codex/plans/current/PLAN-101",
                    ".codex/plans/completed/PLAN-101",
                )
                write_json(path, value)
            plan_path = completed / "plan.json"
            plan = read_json(plan_path)
            plan["status"] = "completed"
            write_json(plan_path, plan)
            old_task = completed / "tasks/current/TASK-001.json"
            moved_task = completed / "tasks/completed/TASK-001.json"
            moved_task.parent.mkdir(parents=True, exist_ok=True)
            task = read_json(old_task)
            task["status"] = "completed"
            task = replace_strings(task, "/tasks/current/TASK-001", "/tasks/completed/TASK-001")
            write_json(old_task, task)
            old_task.rename(moved_task)
            state_path = project / ".codex/STATE.json"
            state = read_json(state_path)
            state["active_plans"] = []
            state["completed_plans"] = ["PLAN-101"]
            write_json(state_path, state)

            self.assertEqual(validate_foundation.validate(project)["tasks"], 1)
            task = read_json(moved_task)
            task["scope"]["write_paths"][0] = "src/structural_change.py"
            write_json(moved_task, task)
            with self.assertRaisesRegex(
                validate_foundation.ValidationFailure,
                "stale structural task digest",
            ):
                validate_foundation.validate(project)


class InstalledClosureTests(unittest.TestCase):
    def test_dependency_catalog_excludes_unrelated_source_modules(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tool-catalog-test-") as temporary:
            source = Path(temporary)
            source_root = source / "src"
            source_root.mkdir()
            (source_root / "ai.py").write_text("VALUE = 1\n", encoding="utf-8")
            (source_root / "validate_foundation.py").write_text(
                "import contracts\n", encoding="utf-8"
            )
            (source_root / "contracts.py").write_text(
                "from domain_values import VALUE\n", encoding="utf-8"
            )
            (source_root / "domain_values.py").write_text("VALUE = 1\n", encoding="utf-8")
            (source_root / "unrelated.py").write_text("raise RuntimeError('not a tool')\n", encoding="utf-8")
            names = {path.name for path in install._tool_sources(source)}
            self.assertEqual(
                names,
                {"ai.py", "contracts.py", "domain_values.py", "validate_foundation.py"},
            )

    def test_installed_tools_run_with_only_their_own_flat_modules(self) -> None:
        with tempfile.TemporaryDirectory(prefix="installed-contract-test-") as temporary:
            temporary_root = Path(temporary)
            project = temporary_root / "project with spaces"
            unrelated_cwd = temporary_root / "unrelated cwd"
            unrelated_cwd.mkdir()
            install.install(str(project), "codex")
            tools = project / ".codex/tools"
            self.assertTrue((tools / "contracts.py").is_file())
            self.assertTrue((tools / "domain_values.py").is_file())
            environment = dict(os.environ)
            environment.pop("PYTHONPATH", None)
            probe = (
                "import pathlib,sys; "
                f"sys.path.insert(0, {str(tools)!r}); "
                "import ai,contracts,domain_values,validate_foundation; "
                f"root=pathlib.Path({str(tools)!r}).resolve(); "
                "mods=(ai,contracts,domain_values,validate_foundation); "
                "assert all(pathlib.Path(m.__file__).resolve().parent == root for m in mods)"
            )
            imported = subprocess.run(
                [sys.executable, "-I", "-B", "-c", probe],
                cwd=unrelated_cwd,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(imported.returncode, 0, imported.stderr)
            validated = subprocess.run(
                [sys.executable, "-B", str(tools / "validate_foundation.py")],
                cwd=unrelated_cwd,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(json.loads(validated.stdout)["plans"], 0)


if __name__ == "__main__":
    unittest.main()
