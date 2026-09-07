from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import ai
import install
import validate_foundation


class ValidatorSafetyTests(unittest.TestCase):
    def create_project(self, parent: Path, name: str = "project") -> Path:
        project = parent / name
        install.install(str(project), "chatgpt")
        result = subprocess.run(
            [
                sys.executable,
                str(project / ".ai" / "tools" / "ai.py"),
                "--project",
                str(project),
                "plan",
                "create",
                "PLAN-101",
                "--title",
                "Safety plan",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return project

    def test_task_filename_must_match_local_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.create_project(Path(temporary))
            task = project / ".ai/plans/current/PLAN-101/tasks/current/TASK-001.json"
            task.rename(task.with_name("TASK-999.json"))
            with self.assertRaisesRegex(validate_foundation.ValidationFailure, "filename/ID mismatch"):
                validate_foundation.validate(project)

    def test_structural_digest_ignores_lifecycle_and_detects_scope_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.create_project(Path(temporary))
            task_path = project / ".ai/plans/current/PLAN-101/tasks/current/TASK-001.json"
            graph_path = project / ".ai/plans/current/PLAN-101/graph.json"
            original_digest = json.loads(graph_path.read_text(encoding="utf-8"))["task_set_sha256"]
            task = json.loads(task_path.read_text(encoding="utf-8"))
            task["status"] = "running"
            task["attempt_ids"] = ["TASK-001-a1"]
            task["resume_state"] = "local lifecycle update"
            task_path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
            validate_foundation.validate(project)
            self.assertEqual(original_digest, ai.structural_task_digest([task]))

            task["scope"]["write_paths"][0] = "src/materially_changed.py"
            task_path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(validate_foundation.ValidationFailure, "stale structural task digest"):
                validate_foundation.validate(project)

    def test_pruning_is_relative_to_root_inside_dot_worktrees(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.create_project(Path(temporary) / ".worktrees", "candidate")
            ignored = [project / ".worktrees" / "nested", project / ".venv", project / "generated"]
            for directory in ignored:
                directory.mkdir(parents=True)
                (directory / "broken.json").write_text("not json", encoding="utf-8")
                (directory / "broken.md").write_text("[missing](absent)", encoding="utf-8")
            result = validate_foundation.validate(project)
            self.assertEqual(result["plans"], 1)

    def test_installed_missing_dependency_message_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            install.install(str(project), "chatgpt")
            result = subprocess.run(
                [sys.executable, "-S", str(project / ".ai/tools/validate_foundation.py")],
                cwd=project,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(".ai/requirements.txt", result.stderr)
            self.assertTrue((project / ".ai/requirements.txt").is_file())


class DestinationValidationTests(unittest.TestCase):
    def test_rejects_windows_devices_and_invalid_characters(self) -> None:
        invalid = [
            r"C:\work\CON .txt",
            r"C:\work\CONIN$",
            r"C:\work\CONOUT$",
            r"C:\work\bad<name",
            r"C:\work\bad>name",
            r"C:\work\bad|name",
            'C:\\work\\bad"name',
        ]
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(install.InstallError):
                    install._validate_destination(value)


class MutationSafetyTests(unittest.TestCase):
    def test_partial_new_task_or_command_write_is_removed(self) -> None:
        class PartialWrite:
            def __init__(self, stream: object) -> None:
                self.stream = stream

            def __enter__(self) -> PartialWrite:
                return self

            def __exit__(self, *args: object) -> None:
                self.stream.close()

            def write(self, content: bytes) -> int:
                self.stream.write(content[:7])
                raise OSError("simulated partial write")

        for failing_name in ("TASK-002.json", "test.TASK-002.json"):
            with self.subTest(failing_name=failing_name), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary) / "project"
                install.install(str(project), "chatgpt")
                self.assertEqual(
                    ai.main(["--project", str(project), "plan", "create", "PLAN-501", "--title", "Plan"]),
                    0,
                )
                before = {
                    path.relative_to(project).as_posix(): path.read_bytes()
                    for path in project.rglob("*")
                    if path.is_file()
                }
                original_open = Path.open

                def partial_open(path: Path, *args: object, **kwargs: object) -> object:
                    stream = original_open(path, *args, **kwargs)
                    mode = args[0] if args else kwargs.get("mode", "r")
                    if path.name == failing_name and mode == "xb":
                        return PartialWrite(stream)
                    return stream

                with patch.object(Path, "open", new=partial_open), self.assertRaises(OSError):
                    ai.main(
                        [
                            "--project",
                            str(project),
                            "task",
                            "create",
                            "PLAN-501",
                            "TASK-002",
                            "--title",
                            "Partial write",
                            "--objective",
                            "Verify cleanup",
                        ]
                    )
                after = {
                    path.relative_to(project).as_posix(): path.read_bytes()
                    for path in project.rglob("*")
                    if path.is_file()
                }
                self.assertEqual(after, before)
                self.assertEqual(validate_foundation.validate(project)["tasks"], 1)

    def test_installer_failure_removes_owned_directories_and_retry_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "populated"
            project.mkdir()
            host_file = project / "app.txt"
            host_file.write_text("preserve me\n", encoding="utf-8")
            with patch.object(install, "_atomic_write", side_effect=OSError("simulated write failure")):
                with self.assertRaises(OSError):
                    install.install(str(project), "chatgpt")
            self.assertEqual(host_file.read_text(encoding="utf-8"), "preserve me\n")
            self.assertFalse((project / ".ai").exists())
            install.install(str(project), "chatgpt")
            self.assertEqual(validate_foundation.validate(project)["plans"], 0)

    def test_state_and_decision_references_must_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            install.install(str(project), "chatgpt")
            state_path = project / ".ai" / "STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["policy_ref"] = ".ai/project/missing-policy.json"
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(validate_foundation.ValidationFailure, "policy_ref"):
                validate_foundation.validate(project)

            state["policy_ref"] = ".ai/project/policy.json"
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            decisions_path = project / ".ai" / "decisions" / "index.json"
            decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
            decisions["decisions"] = [
                {
                    "id": "ADR-001",
                    "status": "accepted",
                    "document_ref": ".ai/decisions/missing.md",
                    "supersedes": [],
                    "superseded_by": None,
                }
            ]
            decisions_path.write_text(json.dumps(decisions, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(validate_foundation.ValidationFailure, "missing reference"):
                validate_foundation.validate(project)


if __name__ == "__main__":
    unittest.main()
