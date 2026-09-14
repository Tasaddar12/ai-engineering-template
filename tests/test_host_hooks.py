"""Drive host advisory notices through subprocess stdin against real Git worktrees."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / ".ai/hooks/worktree-confine.sh"


class HostHookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="host hook fixtures ")
        cls.base = Path(cls.temporary.name).resolve()
        cls.primary = cls.base / "primary project"
        cls.primary.mkdir()
        cls.run_git("init", "--quiet", cwd=cls.primary)
        (cls.primary / "tracked.txt").write_text("original", encoding="utf-8")
        cls.run_git("add", "tracked.txt", cwd=cls.primary)
        cls.run_git("-c", "user.name=Hook Test", "-c", "user.email=test@example.invalid",
                    "commit", "--quiet", "-m", "Fixture", cwd=cls.primary)
        cls.assigned = cls.primary / ".worktrees" / "assigned task"
        cls.sibling = cls.primary / ".worktrees" / "sibling task"
        cls.external = cls.base / "external worktree"
        for number, target in enumerate((cls.assigned, cls.sibling, cls.external)):
            cls.run_git("worktree", "add", "--quiet", "-b", f"task-{number}", str(target), cwd=cls.primary)
        cls.nested = cls.assigned / "source directory"
        cls.nested.mkdir()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @staticmethod
    def run_git(*args, cwd):
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout

    def invoke(self, tool="Write", inputs=None, *, cwd=None, event="PreToolUse", raw=None, env=None,
               script=SCRIPT):
        payload = raw if raw is not None else json.dumps({
            "cwd": str(cwd or self.assigned), "hook_event_name": event,
            "tool_name": tool, "tool_input": inputs or {},
        }, ensure_ascii=False)
        environment = os.environ.copy()
        # A host project variable must not override payload cwd in a worktree.
        environment["CLAUDE_PROJECT_DIR"] = str(self.primary)
        environment.update(env or {})
        bash = shutil.which("bash")
        if os.name == "nt":
            bash = str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe")
        if script == SCRIPT and event == "PostToolUse":
            script = SCRIPT.with_name("ai-tier-notice.sh")
        result = subprocess.run([bash, str(script)], input=payload.encode("utf-8"),
                                capture_output=True, env=environment, cwd=self.primary)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(b"", result.stderr)
        if not result.stdout:
            return None
        self.assertNotIn(b"permissionDecision", result.stdout)
        if event == "PostToolUse":
            return result.stdout.decode("utf-8")
        notice = json.loads(result.stdout)
        self.assertTrue(notice["systemMessage"])
        return notice["systemMessage"]

    def test_claude_file_tools_resolve_from_payload_subdirectory(self):
        for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            key = "notebook_path" if tool == "NotebookEdit" else "file_path"
            with self.subTest(tool=tool):
                self.assertIsNone(self.invoke(tool, {key: "../new file.txt"}, cwd=self.nested))
                notice = self.invoke(tool, {key: str(self.primary / "tracked.txt")}, cwd=self.nested)
                self.assertIn("outside this checkout", notice)

    def test_siblings_and_metadata_warn_even_with_temporary_repository(self):
        for target in (self.sibling / "new.txt", self.external / "new.txt",
                       self.primary / ".git/config", self.assigned / ".git"):
            with self.subTest(target=target):
                self.assertIsNotNone(self.invoke(inputs={"file_path": str(target)}))
        self.assertIn("outside this checkout", self.invoke(inputs={"file_path": str(self.primary / ".git/config")}))

    def test_windows_separators_and_case_on_windows(self):
        target = str(self.sibling / "new file.txt").replace("/", "\\")
        self.assertIsNotNone(self.invoke(inputs={"file_path": target}))
        if os.name == "nt":
            self.assertIsNone(self.invoke(inputs={"file_path": str(self.assigned / "new.txt").upper()}))

    def test_utf8_payload_ignores_host_text_locale(self):
        unicode_cwd = self.assigned / "source résumé 東京"
        unicode_cwd.mkdir()
        target = self.sibling / "résumé 東京.txt"
        for cwd in (self.assigned, unicode_cwd):
            with self.subTest(cwd=cwd):
                notice = self.invoke(inputs={"file_path": str(target)}, cwd=cwd,
                                     env={"PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"})
                self.assertIsNotNone(notice)
                self.assertIn(str(target), notice)

    def test_relocated_hooks_use_their_host_rules_namespace(self):
        for namespace in (".codex", ".claude"):
            with self.subTest(namespace=namespace):
                installed = self.assigned / namespace / "hooks" / "ai-tier-notice.sh"
                installed.parent.mkdir(parents=True)
                installed.write_text(SCRIPT.with_name("ai-tier-notice.sh").read_text(encoding="utf-8").replace(".ai/", namespace + "/"), encoding="utf-8")
                for path in (namespace + "/RULES.md", ".planning/PROJECT.md",
                             ".planning/specs/SPEC-test.md", ".planning/decisions/ADR-test.md",
                             ".planning/phases/01-test/01-PLAN.md", ".planning/STATE.md"):
                    notice = self.invoke(inputs={"file_path": "../" + path}, cwd=self.nested,
                                         event="PostToolUse", script=installed)
                    self.assertIsNotNone(notice)
                    self.assertIn(namespace + "/RULES.md#", notice)
                    self.assertNotIn(".ai/RULES.md", notice)

    def test_temporary_and_environment_scratch_are_quiet(self):
        self.assertIsNone(self.invoke(inputs={"file_path": str(self.base / "temporary output.txt")}))
        # Targets need not exist; use a home path outside the fixture's temp
        # allowance to distinguish the explicit scratch exception.
        scratch = Path.home() / "workflow hook test scratch"
        self.assertIsNotNone(self.invoke(inputs={"file_path": str(scratch / "note.txt")}))
        self.assertIsNone(self.invoke(inputs={"file_path": str(scratch / "note.txt")},
                                      env={"CLAUDE_SCRATCHPAD_DIR": str(scratch)}))
        # A scratch variable pointing at another checkout cannot exempt it.
        self.assertIsNotNone(self.invoke(inputs={"file_path": str(self.sibling / "note.txt")},
                                         env={"CLAUDE_SCRATCHPAD_DIR": str(self.sibling)}))

    def test_codex_patch_checks_every_operation_and_rename_destination(self):
        for operation in ("Add File", "Update File", "Delete File", "Move to"):
            with self.subTest(operation=operation):
                patch = ("*** Begin Patch\n*** Update File: allowed.txt\n"
                         f"*** {operation}: {self.sibling / 'escaped.txt'}\n*** End Patch\n")
                self.assertIn("escaped.txt", self.invoke("apply_patch", {"command": patch}))
        patch = "*** Begin Patch\n*** Add File: ../new file.txt\n+hello\n*** End Patch\n"
        self.assertIsNone(self.invoke("apply_patch", {"command": patch}, cwd=self.nested))
        patch = "*** Begin Patch\r\n*** Update File: ../new file.txt\r\n*** End Patch\r\n"
        self.assertIsNone(self.invoke("apply_patch", {"command": patch}, cwd=self.nested))

    def test_simple_shell_redirects_and_stream_devices(self):
        for operator in (">", ">>", "2>"):
            notice = self.invoke("Bash", {"command": f'echo hello {operator} "{self.sibling / "output.txt"}"'})
            self.assertIn("output.txt", notice)
        for command in ('echo hello > "local file.txt"', "echo hello > /dev/null",
                        "git status", "echo hello 2>&1"):
            self.assertIsNone(self.invoke("Bash", {"command": command}))

    def test_post_tool_document_ownership_for_claude_and_codex(self):
        categories = {".planning/PROJECT.md": "intent ownership", ".ai/RULES.md": "intent ownership",
                      ".planning/specs/SPEC-test.md": "current behavior",
                      ".planning/decisions/ADR-test.md": "decision history",
                      ".planning/phases/01-test/01-PLAN.md": "phase evidence",
                      ".planning/STATE.md": "derived status"}
        for path, expected in categories.items():
            with self.subTest(path=path):
                self.assertIn(expected, self.invoke(inputs={"file_path": "../" + path}, cwd=self.nested,
                                                    event="PostToolUse"))
                patch = f"*** Begin Patch\n*** Update File: {path}\n*** End Patch\n"
                self.assertIn(expected, self.invoke("apply_patch", {"command": patch}, event="PostToolUse"))
        self.assertIsNone(self.invoke(inputs={"file_path": "src/main.py"}, event="PostToolUse"))

    def test_invalid_and_unknown_payloads_are_quiet_success(self):
        for raw in ("", "{broken", "null", "[]", "42", '"text"', '{}',
                    '{"cwd": [], "tool_input": null}',
                    json.dumps({"cwd": str(self.assigned), "hook_event_name": "PreToolUse",
                                "tool_name": "Write", "tool_input": []})):
            with self.subTest(raw=raw):
                self.assertIsNone(self.invoke(raw=raw))
        self.assertIsNone(self.invoke(inputs={"file_path": "file"}, cwd=self.base))


if __name__ == "__main__":
    unittest.main()
