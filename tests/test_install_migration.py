"""Preserve adopting projects while replacing their workflow implementation."""

import importlib.util
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("migration_installer", ROOT / ".ai/install.py")
migration = load("install_migration", ROOT / ".ai/install_migration.py")


class MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_temp = tempfile.TemporaryDirectory(prefix="migration-source-")
        cls.source = Path(cls.source_temp.name)
        for name in (".ai", ".agents", ".planning"):
            shutil.copytree(ROOT / name, cls.source / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        subprocess.run(["git", "init", "--quiet", str(cls.source)], check=True)
        subprocess.run(["git", "add", "."], cwd=cls.source, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        cls.source_temp.cleanup()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="migration-target-")
        self.addCleanup(temporary.cleanup)
        self.target = Path(temporary.name)
        self.write(".ai/RULES.md", b"# Rules\r\nCustom approval rule. Read .ai/commands/worktree.md\r\n")
        self.write(".ai/runtime/phase.py", b"# customized old runtime\n")
        self.write(".ai/private/archive.bin", b"\x00\xff\x01.ai/original\r\n")
        self.write(".planning/PROJECT.md", b"# Real customer identity\r\n")
        self.write(".planning/phases/04-running/04-01-SUMMARY.md", b"Shipped .ai/runtime/phase.py\r\n")
        self.write(".planning/specs/spec.bin", b"\xfe\xffprivate data\0")
        self.write(".planning/config.yaml", b"# My model and checks\r\nworker: [python, .ai/runtime/custom.py]\r\ncheck: [npm, test]\r\n")
        self.write(".ai/runtime/custom.py", b"# custom implementation kept\r\n")
        self.write(".agents/skills/custom/SKILL.md", b"---\nname: custom\ndescription: Local behavior\n---\nRead .ai/RULES.md\n")
        self.write(".agents/skills/custom/data.bin", b"\0private skill support")
        self.write("AGENTS.md", b"Customer preface\r\n" + installer.AGENT_MARKER.encode()
                   + b"\nOld managed workflow\n" + installer.AGENT_END.encode() + b"\r\nCustomer footer\r\n")
        self.write(".ai-venv/keep.txt", b"old environment is not migration-owned")
        self.write(".git/ai-checkpoints/attempt.bin", b"checkpoint must not change")
        self.write(".worktrees/active/unfinished.txt", b"unfinished work")

    def write(self, name, content):
        path = self.target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def snapshot(self):
        return {path.relative_to(self.target).as_posix(): path.read_bytes()
                for path in self.target.rglob("*") if path.is_file()}

    def plan(self, host="codex", hooks=True):
        return migration.plan_migration(self.source, self.target, host, hooks, installer)

    def apply(self, changes):
        for path, content in changes:
            if content is None:
                path.rmdir() if path.is_dir() else path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

    def test_both_hosts_preserve_real_data_refresh_runtime_and_remove_old_tree(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                before = self.snapshot()
                changes, backups, notes = self.plan(host)
                self.assertEqual(before, self.snapshot(), "preflight must be read-only")
                recoverable = {path.relative_to(self.target).as_posix(): path.read_bytes() for path in backups}
                self.assertEqual(before[".ai/runtime/phase.py"], recoverable[".ai/runtime/phase.py"])
                self.assertFalse(any(".git" in path.relative_to(self.target).parts for path in backups))
                self.assertFalse(any(".worktrees" in path.relative_to(self.target).parts for path in backups))
                self.apply(changes)
                namespace = "." + host
                self.assertFalse((self.target / ".ai").exists())
                self.assertEqual(before[".ai/private/archive.bin"], (self.target / namespace / "private/archive.bin").read_bytes())
                self.assertEqual((self.source / ".ai/runtime/phase.py").read_bytes(), (self.target / namespace / "runtime/phase.py").read_bytes())
                self.assertEqual(before[".ai/runtime/custom.py"], (self.target / namespace / "runtime/custom.py").read_bytes())
                self.assertIn(f"{namespace}/workflows/worktree.md".encode(), (self.target / namespace / "RULES.md").read_bytes())
                for name, original in before.items():
                    if name.startswith(".planning/") and name != ".planning/config.yaml":
                        self.assertEqual(original, (self.target / name).read_bytes(), name)
                    if name.startswith((".git/", ".worktrees/", ".ai-venv/")):
                        self.assertEqual(original, (self.target / name).read_bytes(), name)
                self.assertEqual(before[".planning/config.yaml"].replace(b".ai/runtime/", namespace.encode() + b"/runtime/"), (self.target / ".planning/config.yaml").read_bytes())
                self.assertIn("original versions remain in backup", " ".join(notes))
                self.assertIn(b"Customer preface\r\n", (self.target / ("AGENTS.md" if host == "codex" else "CLAUDE.md")).read_bytes())
                self.assertIn(b"Customer footer\r\n", (self.target / ("AGENTS.md" if host == "codex" else "CLAUDE.md")).read_bytes())
                self.assertIn(b"Local behavior", (self.target / namespace / "skills/custom/SKILL.md").read_bytes())
                self.assertEqual(before[".agents/skills/custom/data.bin"], (self.target / namespace / "skills/custom/data.bin").read_bytes())
                if host == "codex":
                    self.assertIn(b".codex/skills/custom/SKILL.md", (self.target / ".agents/skills/custom/SKILL.md").read_bytes())
                    self.assertFalse((self.target / ".agents/skills/custom/data.bin").exists())
                else:
                    self.assertFalse((self.target / ".agents/skills").exists())
                    self.assertNotIn(b"Old managed workflow", (self.target / "AGENTS.md").read_bytes())
                # Restore the isolated fixture, preserving the first host's assertions.
                for path in sorted(self.target.rglob("*"), key=lambda p: len(p.parts), reverse=True):
                    path.rmdir() if path.is_dir() else path.unlink()
                for name, content in before.items():
                    self.write(name, content)

    def test_collision_refuses_without_any_target_changes(self):
        self.write(".codex/RULES.md", b"Independent existing host workflow")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "destination conflicts"):
            self.plan()
        self.assertEqual(before, self.snapshot())

    def test_custom_settings_are_merged_and_backed_up(self):
        current = b'{"model":"chosen", "hooks":{"Stop":[]}}\n'
        self.write(".claude/settings.json", current)
        changes, backups, _ = self.plan("claude")
        self.assertIn(self.target / ".claude/settings.json", backups)
        self.apply(changes)
        settings = (self.target / ".claude/settings.json").read_text()
        self.assertIn('"chosen"', settings)
        self.assertIn('"Stop"', settings)
        self.assertIn('"PreToolUse"', settings)

    def test_unmarked_entry_is_preserved_with_historical_path_mapping(self):
        custom = b"Custom .ai instructions without a managed block\r\n"
        self.write("AGENTS.md", custom)
        changes, _, _ = self.plan("claude", hooks=False)
        self.apply(changes)
        self.assertEqual(custom, (self.target / "AGENTS.md").read_bytes())
        entry = (self.target / "CLAUDE.md").read_bytes()
        self.assertIn(custom, entry)
        self.assertIn(b"`.ai/commands/` to `.claude/workflows/`", entry)
        self.assertIn(b"current managed entry and its delivery rules", entry)

    def test_existing_hook_commands_move_even_when_new_hooks_are_disabled(self):
        self.write(".codex/hooks.json", b'{"other":".ai/hooks/keep", "hooks":{"Stop":[{"hooks":[{"type":"command","command":"python .ai/hooks/local.py","commandWindows":"python .ai\\\\hooks\\\\local.py"}]}]}}')
        changes, backups, _ = self.plan(hooks=False)
        self.assertIn(self.target / ".codex/hooks.json", backups)
        self.apply(changes)
        import json
        settings = json.loads((self.target / ".codex/hooks.json").read_bytes())
        self.assertEqual(".ai/hooks/keep", settings["other"])
        command = settings["hooks"]["Stop"][0]["hooks"][0]
        self.assertEqual("python .codex/hooks/local.py", command["command"])
        self.assertEqual("python .codex\\hooks\\local.py", command["commandWindows"])
        self.assertNotIn("PreToolUse", settings["hooks"])

    def test_old_open_marker_preserves_appended_customer_instructions(self):
        current = (installer.AGENT_MARKER.encode() + b"\nOriginal entry\n"
                   b"Customer appended .ai migration rules\r\n")
        self.write("AGENTS.md", current)
        changes, _, _ = self.plan()
        self.apply(changes)
        self.assertIn(current, (self.target / "AGENTS.md").read_bytes())
        self.assertIn(installer.AGENT_END.encode(), (self.target / "AGENTS.md").read_bytes())

    def test_existing_managed_hooks_relocate_without_duplicate_registration(self):
        settings = installer.json_bytes(installer.hook_settings("codex")).replace(b"/.codex/hooks/", b"/.ai/hooks/")
        self.write(".codex/hooks.json", settings)
        changes, _, _ = self.plan()
        self.apply(changes)
        import json
        result = json.loads((self.target / ".codex/hooks.json").read_bytes())
        for event in ("PreToolUse", "PostToolUse"):
            self.assertEqual(1, len(result["hooks"][event]))
            self.assertNotIn("/.ai/hooks/", str(result["hooks"][event]))

    def test_two_old_paths_mapping_to_same_destination_are_rejected(self):
        self.write(".ai/skills/custom/SKILL.md", b"Different custom content")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "both map to"):
            self.plan()
        self.assertEqual(before, self.snapshot())

    def test_legacy_records_fail_without_reinterpreting_attempts(self):
        self.write(".ai/phases/01/attempt.txt", b"old schema")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "compatible original runtime"):
            self.plan()
        self.assertEqual(before, self.snapshot())

    def test_backup_location_file_and_parent_file_fail_preflight(self):
        self.write(".workflow-backups", b"keep")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "backup location"):
            self.plan()
        self.assertEqual(before, self.snapshot())
        (self.target / ".workflow-backups").unlink()
        self.write(".codex/runtime", b"a file, not a directory")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "parent is not a directory"):
            self.plan()
        self.assertEqual(before, self.snapshot())

    def test_link_in_original_tree_is_refused(self):
        link = self.target / ".ai/linked"
        try:
            link.symlink_to(self.target / ".planning", target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            command = f'New-Item -ItemType Junction -Path "{link}" -Target "{self.target / ".planning"}" | Out-Null'
            subprocess.run(["powershell", "-NoProfile", "-Command", command], check=True)
        try:
            with self.assertRaisesRegex(ValueError, "linked path"):
                self.plan()
        finally:
            link.rmdir() if os.name == "nt" and not link.is_symlink() else link.unlink()


if __name__ == "__main__":
    unittest.main()
