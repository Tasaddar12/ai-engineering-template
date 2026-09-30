"""Preserve adopting projects while replacing their workflow implementation."""

import collections
import importlib.util
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import tomllib
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("migration_installer", ROOT / ".ai/install.py")
migration = load("install_migration", ROOT / ".ai/install_migration.py")
update = load("migration_followup_update", ROOT / ".ai/install_update.py")


class MigrationTests(unittest.TestCase):
    def test_migration_payload_excludes_source_only_maintenance_history(self):
        self.assertTrue((self.source / ".ai/maintenance/agent-scout-SUMMARY.md").is_file())
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                changes, _, _ = self.plan(host, hooks=False)
                self.assertFalse(any(path.relative_to(self.target).as_posix().startswith("." + host + "/maintenance/")
                                     for path, _ in changes))

    def test_legacy_migration_requires_update_and_preserves_custom_guidance_in_backups(self):
        # Inline excerpts from the assigned base; no historical Git object is
        # required in the shallow CI checkout. Custom additions must survive
        # migration and remain recoverable when the explicit update replaces them.
        legacy = (b'---\nname: coder\ndisallowedTools: Agent, Task\n'
                  b'description: Executes one assigned phase plan with atomic commits, deviation handling, checkpoint handoffs, and evidence summaries.\n'
                  b'tools: Read, Write, Edit, Bash, Grep, Glob, Skill, mcp__context7__*, mcp__plugin_context7_context7__*\n'
                  b'color: yellow\n---\n\n<local_workflow>\n'
                  b'Use only the paths, revision and result destination your plan names. Read the\n'
                  b'repository AGENTS.md and only the applicable skills. Only the orchestrator\n'
                  b'dispatches agents, ticks the roadmap, changes shared phase decisions or status,\n'
                  b'or publishes.\n</local_workflow>\n\nCustom worker instruction sentinel.\n')
        rules = (b'Agents edit only the paths their plan declares, plus their own SUMMARY. They do\n'
                 b'not spawn agents, switch branches, merge, publish or edit shared status.\n\n'
                 b'Custom approval instruction sentinel. Read .ai/RULES.md\n')
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.setUp()
                self.write(".ai/agents/coder.md", legacy)
                self.write(".ai/RULES.md", rules)
                changes, originals, notes = self.plan(host, hooks=False)
                self.assertIn("Scout activation is pending", " ".join(notes))
                migration_backup = installer.backup_migration(self.target, originals)
                self.apply(changes)
                namespace = "." + host
                coder = self.target / namespace / "agents/coder.md"
                migrated = coder.read_bytes()
                self.assertIn(b"disallowedTools: Agent, Task", migrated)
                self.assertIn(b"Custom worker instruction sentinel.", migrated)
                self.assertEqual(legacy, (migration_backup / "files/.ai/agents/coder.md").read_bytes())
                self.assertEqual(rules, (migration_backup / "files/.ai/RULES.md").read_bytes())
                migrated_rules = (self.target / namespace / "RULES.md").read_bytes()
                self.assertIn(b"Custom approval instruction sentinel.", migrated_rules)

                changes, originals, _ = update.plan_update(self.source, self.target, host, False, installer)
                update_backup = installer.backup_migration(self.target, originals)
                self.apply(changes)
                self.assertEqual(migrated, (update_backup / "files" / namespace / "agents/coder.md").read_bytes())
                self.assertEqual(migrated_rules, (update_backup / "files" / namespace / "RULES.md").read_bytes())
                for role in (self.target / namespace / "agents").glob("*.md"):
                    text = role.read_text(encoding="utf-8")
                    if not text.startswith("---\n") or role.stem == "scout":
                        continue
                    metadata = yaml.safe_load(text.split("---", 2)[1])
                    self.assertIn("Agent", metadata["tools"].split(", "))
                    self.assertNotIn("Agent", metadata.get("disallowedTools", "").split(", "))
                    self.assertNotIn("Task", metadata.get("disallowedTools", "").split(", "))
                    self.assertIn("scout-dispatch.md", text)
                    adapter = text.split("<local_workflow>", 1)[1].split("</local_workflow>", 1)[0]
                    self.assertNotRegex(adapter, r"Only the (?:coordinator|orchestrator)\s+dispatches\s+agents")
                current_rules = (self.target / namespace / "RULES.md").read_text(encoding="utf-8")
                self.assertIn("scout-dispatch.md", current_rules)
                self.assertNotIn("not spawn agents", current_rules)

    def test_no_hooks_migration_canonicalizes_existing_codex_settings(self):
        original = (b'\xef\xbb\xbf# custom\r\n"agents"."max_threads" = 3 # legacy\r\n'
                    b'model = "keep"\r\n[hooks]\r\nStop = []\r\n')
        self.write(".codex/config.toml", original)
        changes, backups, _ = self.plan("codex", hooks=False)
        path = self.target / ".codex/config.toml"
        self.assertIn(path, backups)
        self.apply(changes)
        content = path.read_bytes()
        self.assertTrue(content.startswith(b'\xef\xbb\xbf# custom\r\n# legacy\r\n'))
        self.assertIn(b'model = "keep"\r\n', content)
        self.assertIn(b'[hooks]\r\nStop = []\r\n', content)
        parsed = tomllib.loads(content.decode("utf-8-sig"))
        self.assertEqual(12, parsed["agents"]["max_concurrent_threads_per_session"])
        self.assertNotIn("max_threads", parsed["agents"])
        incoming = installer.host_payload({}, "codex", False)[".codex/config.toml"]
        self.assertEqual(content, installer.merge_codex_config(content, incoming, path))
        rules = self.target / ".codex/RULES.md"
        self.assertEqual(b"# Rules\nCustom approval rule. Read .codex/commands/worktree.md\n",
                         rules.read_bytes())
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, r"Existing files conflict;.*") as caught:
            installer.plan_install(self.source, self.target, "codex", hooks=False)
        self.assertIn(".codex/RULES.md", str(caught.exception).replace("\\", "/"))
        self.assertEqual(before, self.snapshot())

    def test_no_hooks_migration_invalid_settings_do_not_write_or_delete(self):
        for content in (b'agents = {max_threads = 3}\n', b'[agents\n'):
            with self.subTest(content=content):
                self.write(".codex/config.toml", content)
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "nothing was installed"):
                    self.plan("codex", hooks=False)
                self.assertEqual(before, self.snapshot())

    def test_custom_skill_links_preserve_angle_brackets_and_titles(self):
        content = (b'[Rules](<../../../.ai/RULES.md> "Project rules")\n'
                   b'[Local](<notes with spaces.md>)\n')
        moved = installer.render_asset(".agents/skills/custom/SKILL.md", content, "claude")
        self.assertEqual((b'[Rules](<../../RULES.md> "Project rules")\n'
                          b'[Local](<notes with spaces.md>)\n'), moved)

    def test_escaped_windows_routes_relocate_without_rewriting_urls(self):
        import yaml
        config = (b'# Keep formatting\r\nworker: ".ai\\\\workers\\\\custom.py"\r\n'
                  b'role: ".ai\\\\agents\\\\custom.py"\r\n'
                  b'url: https://example.invalid/.ai/source.py\r\n')
        moved = migration.relocate_paths(config, "claude")
        parsed = yaml.safe_load(moved)
        self.assertEqual(".claude\\workers\\custom.py", parsed["worker"])
        self.assertEqual(".claude\\agents\\custom.py", parsed["role"])
        self.assertEqual("https://example.invalid/.ai/source.py", parsed["url"])
        self.assertTrue(moved.startswith(b"# Keep formatting\r\n"))
        directories = yaml.safe_load(migration.relocate_paths(
            b'args: [.ai/agents, .ai/commands, .agents/skills, .ai/agents-custom]\n', "claude"))
        self.assertEqual([".claude/agents", ".claude/commands", ".claude/skills", ".claude/agents-custom"],
                         directories["args"])

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

    def test_claude_migration_preserves_custom_roles(self):
        """Agent bodies and frontmatter survive relocation untouched."""
        legacy = b"---\r\nname: coder\r\ndescription: My coding rules\r\n---\r\nKeep this custom body.\r\n"
        custom = b"---\nname: verifier\ndescription: Custom verifier\n---\nKeep my checks.\n"
        unusual = b'---\n{"name": "debugger"}\n---\nKeep my YAML.\n'
        unrelated = b"---\nname: custom\ndescription: Custom role\n---\nKeep unchanged.\n"
        for role, content in (("coder", legacy), ("verifier", custom),
                              ("debugger", unusual), ("custom", unrelated)):
            self.write(".ai/agents/" + role + ".md", content)
        before = self.snapshot()
        changes, backups, notes = self.plan("claude", hooks=False)
        self.assertEqual(before, self.snapshot())
        self.assertIn(self.target / ".ai/agents/coder.md", backups)
        self.apply(changes)
        coder = (self.target / ".claude/agents/coder.md").read_bytes()
        self.assertEqual(legacy.replace(b"\r\n", b"\n"), coder)
        # Markdown roles carry no model frontmatter; nothing is seeded into them.
        self.assertNotIn(b"model:", coder)
        for role, content in (("verifier", custom), ("debugger", unusual), ("custom", unrelated)):
            self.assertEqual(content, (self.target / ".claude/agents" / (role + ".md")).read_bytes())
        self.assertFalse(list((self.target / ".claude/agents").glob("*.toml")))

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
                self.assertIn(f"{namespace}/commands/worktree.md".encode(), (self.target / namespace / "RULES.md").read_bytes())
                for name, original in before.items():
                    if name.startswith(".planning/") and name != ".planning/config.yaml":
                        self.assertEqual(original, (self.target / name).read_bytes(), name)
                    if name.startswith((".git/", ".worktrees/", ".ai-venv/")):
                        self.assertEqual(original, (self.target / name).read_bytes(), name)
                self.assertEqual(before[".planning/config.yaml"].replace(b".ai/runtime/", namespace.encode() + b"/runtime/"), (self.target / ".planning/config.yaml").read_bytes())
                self.assertIn("original versions remain in backup", " ".join(notes))
                self.assertIn(b"Customer preface\r\n", (self.target / ("AGENTS.md" if host == "codex" else "CLAUDE.md")).read_bytes())
                self.assertIn(b"Customer footer\r\n", (self.target / ("AGENTS.md" if host == "codex" else "CLAUDE.md")).read_bytes())
                skills = ".agents/skills" if host == "codex" else ".claude/skills"
                self.assertIn(b"Local behavior", (self.target / skills / "custom/SKILL.md").read_bytes())
                self.assertEqual(before[".agents/skills/custom/data.bin"], (self.target / skills / "custom/data.bin").read_bytes())
                if host == "codex":
                    self.assertFalse((self.target / ".codex/skills").exists())
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
        self.assertIn('"PostToolUse"', settings)

    def test_unmarked_entry_preserves_customer_guidance(self):
        custom = b"Custom .ai instructions without a managed block\r\n"
        self.write("AGENTS.md", custom)
        changes, _, _ = self.plan("claude", hooks=False)
        self.apply(changes)
        self.assertEqual(custom, (self.target / "AGENTS.md").read_bytes())
        entry = (self.target / "CLAUDE.md").read_bytes()
        self.assertIn(custom, entry)
        self.assertNotIn(b"Historical plans", entry)
        self.assertIn(b".claude/commands/", entry)

    def test_existing_hook_commands_move_even_when_new_hooks_are_disabled(self):
        self.write(".claude/settings.json", b'{"other":".ai/hooks/keep", "hooks":{"Stop":[{"hooks":[{"type":"command","command":"python .ai/hooks/local.py","commandWindows":"python .ai\\\\hooks\\\\local.py"}]}]}}')
        changes, backups, _ = self.plan("claude", hooks=False)
        self.assertIn(self.target / ".claude/settings.json", backups)
        self.apply(changes)
        import json
        settings = json.loads((self.target / ".claude/settings.json").read_bytes())
        self.assertEqual(".ai/hooks/keep", settings["other"])
        command = settings["hooks"]["Stop"][0]["hooks"][0]
        self.assertEqual("python .claude/hooks/local.py", command["command"])
        self.assertEqual("python .claude\\hooks\\local.py", command["commandWindows"])
        self.assertNotIn("PreToolUse", settings["hooks"])

    def test_existing_managed_hooks_relocate_without_duplicate_registration(self):
        settings = installer.hooks_toml(installer.hook_settings("codex")["hooks"]).replace(b"/.codex/hooks/", b"/.ai/hooks/")
        self.write(".codex/config.toml", settings)
        changes, _, _ = self.plan()
        self.apply(changes)
        result = tomllib.loads((self.target / ".codex/config.toml").read_text())
        # Counted from MANAGED_HOOKS rather than written as a literal. The
        # assertion here is "relocated, not duplicated"; a hardcoded count means
        # the next hook added to an already-registered event fails this test for
        # a reason that has nothing to do with migration.
        expected = collections.Counter(event for event, _, _ in installer.MANAGED_HOOKS)
        for event, count in expected.items():
            self.assertEqual(count, len(result["hooks"][event]),
                             f"{event} registrations were duplicated rather than relocated")
            self.assertNotIn("/.ai/hooks/", str(result["hooks"][event]))

    def test_two_old_paths_mapping_to_same_destination_are_rejected(self):
        self.write(".ai/skills/custom/SKILL.md", b"Different custom content")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "both map to"):
            self.plan("claude")
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
