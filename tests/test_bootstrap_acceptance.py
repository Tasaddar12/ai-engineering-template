"""Exercise the reusable docs payload in empty and populated projects."""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE_ROOT / "src"))

import ai
import install
import validate_foundation


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def create_plan(root: Path, plan_id: str) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        ai.main(["--project", str(root), "plan", "create", plan_id, "--title", "Example change"])


class BootstrapAcceptanceTests(unittest.TestCase):
    def test_provider_modes_preserve_host_and_support_independent_plans(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workload-install-test-") as temporary:
            for assistant in ("claude", "chatgpt"):
                with self.subTest(assistant=assistant):
                    root = Path(temporary) / assistant
                    namespace = ".claude" if assistant == "claude" else ".ai"
                    workspace = root / namespace
                    install.install(str(root), assistant, dry_run=True)
                    self.assertFalse(root.exists())

                    (root / "src").mkdir(parents=True)
                    (root / "schemas" / "v1").mkdir(parents=True)
                    host_files = {
                        "src/app.py": b'print("existing application")\n',
                        "schemas/v1/host.schema.json": b"{}\n",
                        "README.md": b"[Unrelated host link](missing-host-file.md)\n",
                        "AGENTS.md": b"Existing host instructions\n",
                        "CLAUDE.md": b"Existing host memory\n",
                    }
                    for relative, content in host_files.items():
                        (root / relative).write_bytes(content)

                    install.install(str(root), assistant)
                    for relative, content in host_files.items():
                        self.assertEqual((root / relative).read_bytes(), content)
                    entry = "CLAUDE.md" if assistant == "claude" else "AGENTS.md"
                    self.assertTrue((workspace / entry).is_file())
                    self.assertFalse((root / (".ai" if assistant == "claude" else ".claude")).exists())
                    state = json.loads((workspace / "STATE.json").read_text())
                    self.assertEqual(state["active_plans"], [])
                    for bucket in ("current", "completed", "archived"):
                        self.assertEqual(
                            [path.name for path in (workspace / "plans" / bucket).iterdir()
                             if path.name != ".gitkeep"], [],
                        )
                    decisions = json.loads((workspace / "decisions" / "index.json").read_text())
                    self.assertEqual(decisions["decisions"], [])
                    self.assertFalse((root / ".worktrees").exists())
                    for section in ("agents", "templates", "workflows"):
                        documents = sorted((SOURCE_ROOT / "docs" / section).rglob("*.md"))
                        self.assertTrue(documents, f"Missing copyable docs/{section} payload")
                        for document in documents:
                            installed = workspace / section / document.relative_to(SOURCE_ROOT / "docs" / section)
                            expected = document.read_text(encoding="utf-8").replace(".ai", namespace)
                            if assistant == "claude":
                                expected = expected.replace("AGENTS.md", "CLAUDE.md")
                            self.assertEqual(installed.read_text(encoding="utf-8"), expected)
                    self.assertTrue((workspace / "templates" / "PLAN.md").is_file())
                    self.assertTrue((workspace / "templates" / "TASK.md").is_file())
                    self.assertTrue((workspace / "agents" / "planner.md").is_file())

                    create_plan(root, "PLAN-101")
                    create_plan(root, "PLAN-102")
                    with contextlib.redirect_stdout(io.StringIO()):
                        ai.main([
                            "--project", str(root), "task", "create", "PLAN-101", "TASK-002",
                            "--title", "Dependent change", "--objective", "Verify behavior",
                            "--depends-on", "TASK-001",
                        ])
                    result = validate_foundation.validate(root)
                    self.assertEqual((result["plans"], result["tasks"]), (2, 3))
                    for plan_id in ("PLAN-101", "PLAN-102"):
                        bundle = workspace / "plans" / "current" / plan_id
                        task = json.loads((bundle / "tasks" / "current" / "TASK-001.json").read_text())
                        self.assertEqual(task["plan_id"], plan_id)
                        self.assertTrue((bundle / "commands" / "test.TASK-001.json").is_file())

                    before = snapshot(root)
                    install.install(str(root), assistant)
                    self.assertEqual(snapshot(root), before)

    def test_copied_tools_run_from_an_unrelated_working_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workload-portability-test-") as temporary:
            for assistant, namespace in (("chatgpt", ".ai"), ("claude", ".claude")):
                with self.subTest(assistant=assistant):
                    root = Path(temporary) / (assistant + " project with spaces")
                    self.assertFalse(root.exists())
                    install.install(str(root), assistant)
                    self.assertFalse((root / "AGENTS.md").exists())
                    self.assertFalse((root / "CLAUDE.md").exists())
                    self.assertFalse((root / (".ai" if assistant == "claude" else ".claude")).exists())
                    creation = subprocess.run(
                        [sys.executable, "-B", str(root / namespace / "tools/ai.py"), "--project", str(root),
                         "plan", "create", "PLAN-201", "--title", "Installed tool"],
                        cwd=temporary, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(creation.returncode, 0, creation.stderr)
                    validation = subprocess.run(
                        [sys.executable, "-B", str(root / namespace / "tools/validate_foundation.py")],
                        cwd=temporary, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(validation.returncode, 0, validation.stderr)
                    result = json.loads(validation.stdout)
                    self.assertEqual((result["plans"], result["tasks"]), (1, 1))

    def test_persistent_task_write_failure_restores_project_bytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workload-rollback-test-") as temporary:
            root = Path(temporary) / "project"
            install.install(str(root), "chatgpt")
            create_plan(root, "PLAN-301")
            before = snapshot(root)
            original_write = ai._atomic_write

            def fail_graph(path: Path, content: bytes) -> None:
                if path.name == "graph.json":
                    raise OSError("Persistent simulated graph write error")
                original_write(path, content)

            with patch.object(ai, "_atomic_write", side_effect=fail_graph):
                with self.assertRaises((OSError, ai.CliError)):
                    with contextlib.redirect_stdout(io.StringIO()):
                        ai.main([
                            "--project", str(root), "task", "create", "PLAN-301", "TASK-002",
                            "--title", "Failure check", "--objective", "Verify rollback",
                        ])
            self.assertEqual(snapshot(root), before)
            self.assertEqual(validate_foundation.validate(root)["tasks"], 1)

    def test_empty_lifecycle_directories_survive_a_git_commit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workload-git-roundtrip-") as temporary:
            temporary_root = Path(temporary)
            for assistant in ("chatgpt", "claude"):
                with self.subTest(assistant=assistant):
                    root = temporary_root / assistant
                    install.install(str(root), assistant)

                    def git(*args: str) -> None:
                        result = subprocess.run(
                            ["git", "-C", str(root), "-c", "commit.gpgsign=false",
                             "-c", f"core.hooksPath={temporary_root / 'unused-hooks'}", *args],
                            check=False, capture_output=True, text=True,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)

                    git("init", "--quiet")
                    for generation in (0, 1):
                        if generation:
                            create_plan(root, "PLAN-401")
                        git("add", ".")
                        git("-c", "user.name=Bootstrap Test", "-c", "user.email=bootstrap@example.invalid",
                            "commit", "--quiet", "-m", f"Test installation generation {generation}")
                        exported = temporary_root / f"{assistant}-{generation}-exported"
                        git("-c", "core.autocrlf=true", "checkout-index", "--all",
                            f"--prefix={exported.as_posix()}/")
                        result = validate_foundation.validate(exported)
                        self.assertEqual((result["plans"], result["tasks"]), (generation, generation))

    def test_local_edits_are_preserved_and_asset_conflicts_write_nothing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workload-conflict-test-") as temporary:
            root = Path(temporary) / "project"
            install.install(str(root), "chatgpt")
            policy_path = root / ".ai/project/policy.json"
            policy = json.loads(policy_path.read_text())
            policy["max_parallel"] = 1
            policy_path.write_text(json.dumps(policy) + "\n", encoding="utf-8")
            guidance = root / ".ai/AGENTS.md"
            guidance.write_bytes(guidance.read_bytes() + b"\nAdditional local guidance.\n")
            before_repeat = snapshot(root)
            install.install(str(root), "chatgpt")
            self.assertEqual(snapshot(root), before_repeat)

            owned_tool = root / ".ai/tools/ai.py"
            owned_tool.write_bytes(owned_tool.read_bytes() + b"\n# Local modification\n")
            before_conflict = snapshot(root)
            with self.assertRaises(install.InstallError):
                install.install(str(root), "chatgpt")
            self.assertEqual(snapshot(root), before_conflict)

if __name__ == "__main__":
    unittest.main()
