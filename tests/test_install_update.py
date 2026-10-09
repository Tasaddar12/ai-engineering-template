"""Refresh an installed workflow onto a newer revision without losing the project.

An update is the one mode that runs against a tree the project has been living
in, so every test here is really the same question asked about a different file:
did the project's own material survive the refresh?
"""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("update_installer", ROOT / ".ai/install.py")
legacy_update = load("install_update", ROOT / ".ai/install_update.py")


def seed_source(directory):
    for name in (".ai", ".agents", ".planning"):
        shutil.copytree(ROOT / name, directory / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    subprocess.run(["git", "init", "--quiet", str(directory)], check=True)
    subprocess.run(["git", "add", "."], cwd=directory, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class UpdateTests(unittest.TestCase):
    host = "codex"

    def test_scout_metadata_export_is_host_specific_and_update_is_idempotent(self):
        path = self.namespace + "/agents/scout.md"
        self.write(path, b'---\nname: scout\nmodel: wrong\neffort: max\n---\nOld adapter.\n')
        changes, backups, _ = self.plan()
        self.assertIn(self.target / path, backups)
        self.apply(changes)
        exported = self.read(path).decode("utf-8")
        metadata = yaml.safe_load(exported.split("---", 2)[1])
        if self.host == "claude":
            self.assertEqual("haiku", metadata["model"])
        else:
            self.assertNotIn("model", metadata)
        self.assertNotIn("effort", metadata)
        shared = (self.source / ".ai/agents/scout.md").read_bytes()
        expected = installer.render_asset(".ai/agents/scout.md", shared, self.host)
        self.assertEqual(expected, self.read(path))
        self.assertEqual([], self.plan()[0])

    def test_update_payload_excludes_source_only_maintenance_history(self):
        self.assertTrue((self.source / ".ai/maintenance/agent-scout-SUMMARY.md").is_file())
        self.assertFalse(any(name.startswith(self.namespace + "/maintenance/") for name in self.installed))
        changes, _, _ = self.plan()
        self.assertFalse(any(path.relative_to(self.target).as_posix().startswith(self.namespace + "/maintenance/")
                             for path, _ in changes))

    def test_no_hooks_update_canonicalizes_codex_settings_and_preserves_hooks(self):
        if self.host != "codex":
            self.skipTest("Codex project setting")
        original = (b'\xef\xbb\xbf# custom\r\nmodel = "keep"\r\n[agents]\r\n'
                    b'max_threads = 4 # retained comment\r\n'
                    b'max_concurrent_threads_per_session = 5\r\n[hooks]\r\nStop = []\r\n')
        path = self.write(".codex/config.toml", original)
        changes, backups, _ = legacy_update.plan_update(self.source, self.target, "codex", False, installer)
        self.assertIn(path, backups)
        self.apply(changes)
        content = path.read_bytes()
        self.assertTrue(content.startswith(b'\xef\xbb\xbf# custom\r\nmodel = "keep"\r\n'))
        self.assertIn(b'[hooks]\r\nStop = []\r\n', content)
        settings = installer.tomllib.loads(content.decode("utf-8-sig"))
        self.assertEqual(12, settings["agents"]["max_concurrent_threads_per_session"])
        self.assertNotIn("max_threads", settings["agents"])
        self.assertEqual([], legacy_update.plan_update(self.source, self.target, "codex", False, installer)[0])

    def test_no_hooks_update_invalid_codex_settings_are_preflight_only(self):
        if self.host != "codex":
            self.skipTest("Codex project setting")
        self.write(".codex/config.toml", b'agents = {max_threads = 4}\n')
        before = {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        with self.assertRaisesRegex(ValueError, "inline agents.*nothing was installed"):
            legacy_update.plan_update(self.source, self.target, "codex", False, installer)
        after = {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    @classmethod
    def setUpClass(cls):
        cls.source_temp = tempfile.TemporaryDirectory(prefix="update-source-")
        cls.source = Path(cls.source_temp.name)
        seed_source(cls.source)

    @classmethod
    def tearDownClass(cls):
        cls.source_temp.cleanup()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="update-target-")
        self.addCleanup(temporary.cleanup)
        self.target = Path(temporary.name)
        self.namespace = "." + self.host
        # An installed project at the current revision, which the tests then age
        # by editing files back to an "older" state.
        self.installed = installer.payload(self.source, self.host, True)
        for name, content in self.installed.items():
            self.write(name, content)
        self.write(".gitignore", installer.IGNORE_BLOCK.replace(
            ".ai-venv", self.namespace + "-venv").encode())

    def write(self, name, content):
        path = self.target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def entry(self):
        return "CLAUDE.md" if self.host == "claude" else "AGENTS.md"

    def plan(self, prune=False, previous=None):
        return legacy_update.plan_update(self.source, self.target, self.host, True,
                                  installer, prune=prune, previous=previous)

    def apply(self, changes):
        for path, content in changes:
            if content is None:
                path.rmdir() if path.is_dir() else path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

    def read(self, name):
        return (self.target / name).read_bytes()

    # --- the project's own material -----------------------------------------

    def test_project_records_are_never_rewritten(self):
        """Intent, history and configuration outrank any template revision."""
        records = {
            ".planning/PROJECT.md": b"# Real customer identity\n",
            ".planning/REQUIREMENTS.md": b"- the actual requirements\n",
            ".planning/ROADMAP.md": b"- the actual roadmap\n",
            ".planning/STATE.md": b"phase: 7\n",
            ".planning/config.yaml": b"context_window: 999999\nverification:\n  commands: [[npm, test]]\n",
        }
        for name, content in records.items():
            self.write(name, content)
        evidence = self.write(".planning/phases/04-x/04-01-SUMMARY.md", b"shipped\n")
        changes, backups, _ = self.plan()
        self.apply(changes)
        for name, content in records.items():
            self.assertEqual(content, self.read(name), name)
        self.assertEqual(b"shipped\n", evidence.read_bytes())
        for path in backups:
            self.assertNotIn(".planning/", path.relative_to(self.target).as_posix())

    def test_an_aged_shipped_file_is_refreshed(self):
        rules = self.namespace + "/RULES.md"
        self.write(rules, b"# an older revision of the rules\n")
        changes, backups, notes = self.plan()
        self.apply(changes)
        self.assertEqual(self.installed[rules], self.read(rules))
        self.assertIn(self.target / rules, backups)
        self.assertTrue(any("Refresh" in note for note in notes))

    def test_an_update_adds_only_the_ignore_rules_a_project_lacks(self):
        """Handoff records must stay out of commits in projects installed before
        `.planning/handoffs/` was a rule, without duplicating the rules they have."""
        older = ("\n# AI engineering workflow (local only)\n" + self.namespace + "-venv/\n"
                 ".workflow-backups/\n__pycache__/\n*.pyc\n").encode()
        self.write(".gitignore", older)
        changes, backups, _ = self.plan()
        self.apply(changes)
        lines = self.read(".gitignore").decode("utf-8").splitlines()
        self.assertTrue(self.read(".gitignore").startswith(older))
        self.assertEqual(1, lines.count(".planning/handoffs/"))
        self.assertEqual(1, lines.count(".workflow-backups/"))
        self.assertEqual(1, lines.count("# AI engineering workflow (local only)"))
        self.assertIn(self.target / ".gitignore", backups)

    def test_a_second_update_changes_nothing(self):
        self.write(self.namespace + "/RULES.md", b"# older\n")
        self.apply(self.plan()[0])
        changes, backups, _ = self.plan()
        self.assertEqual([], changes)
        self.assertEqual([], backups)

    # --- files that are merged rather than replaced --------------------------

    def test_entry_file_swaps_only_the_managed_block(self):
        managed = self.installed[self.entry()]
        self.write(self.entry(), b"# House style\nkeep this\n\n"
                   + installer.AGENT_MARKER.encode() + b"\nan older block\n"
                   + installer.AGENT_END.encode() + b"\n\n## Footer\nkeep this too\n")
        self.apply(self.plan()[0])
        rebuilt = self.read(self.entry())
        self.assertIn(b"# House style", rebuilt)
        self.assertIn(b"## Footer", rebuilt)
        self.assertNotIn(b"an older block", rebuilt)
        self.assertIn(managed.strip(), rebuilt)
        self.assertEqual(1, rebuilt.count(installer.AGENT_MARKER.encode()))
        self.assertEqual(1, rebuilt.count(installer.AGENT_END.encode()))

    def test_an_ambiguous_managed_block_stops_the_update(self):
        marker = installer.AGENT_MARKER.encode()
        end = installer.AGENT_END.encode()
        self.write(self.entry(), marker + b"\na\n" + end + b"\n" + marker + b"\nb\n" + end + b"\n")
        with self.assertRaises(ValueError) as caught:
            self.plan()
        self.assertIn("Ambiguous", str(caught.exception))

    def test_user_hooks_in_host_settings_survive(self):
        settings = ".codex/config.toml" if self.host == "codex" else ".claude/settings.json"
        if self.host == "codex":
            current = (b'[[hooks.PreToolUse]]\nmatcher = "MyTool"\n'
                       b'[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
                       b'command = "my-own-hook"\n')
        else:
            current = (b'{\n  "hooks": {\n    "PreToolUse": [\n      {\n'
                       b'        "matcher": "MyTool",\n        "hooks": [\n'
                       b'          {"type": "command", "command": "my-own-hook"}\n'
                       b'        ]\n      }\n    ]\n  }\n}\n')
        self.write(settings, current)
        self.apply(self.plan()[0])
        merged = self.read(settings)
        self.assertIn(b"my-own-hook", merged)
        self.assertIn(b"worktree-guard.sh", merged)

    def settings_name(self):
        return ".codex/config.toml" if self.host == "codex" else ".claude/settings.json"

    def aged_settings(self, user_hook):
        """Host settings as an older revision wrote them, beside a user hook."""
        events = installer.hook_settings(self.host)["hooks"]
        for groups in events.values():
            for group in groups:
                handler = group["hooks"][0]
                if "commandWindows" in handler:
                    handler["commandWindows"] = handler["commandWindows"].replace(
                        "; exit $LASTEXITCODE", "")
                else:
                    handler["timeout"] = 5
        events.setdefault("PreToolUse", []).insert(0, user_hook)
        if self.host == "codex":
            return (b"# project settings\nmodel = \"x\"\n\n"
                    + installer.hooks_toml(events))
        return installer.json_bytes({"model": "x", "hooks": events})

    def test_an_aged_managed_hook_registration_is_replaced(self):
        user_hook = {"matcher": "MyTool",
                     "hooks": [{"type": "command", "command": "my-own-hook"}]}
        settings = self.settings_name()
        self.write(settings, self.aged_settings(user_hook))
        changes, backups, _ = self.plan()
        self.assertIn(self.target / settings, backups)
        self.apply(changes)
        merged = self.read(settings)
        parsed = (installer.tomllib.loads(merged.decode()) if self.host == "codex"
                  else installer.json.loads(merged))
        self.assertEqual("x", parsed["model"])
        expected = installer.hook_settings(self.host)["hooks"]
        for event, groups in expected.items():
            present = [group for group in parsed["hooks"][event] if group != user_hook]
            self.assertEqual(groups, present, event)
        self.assertIn(user_hook, parsed["hooks"]["PreToolUse"])
        if self.host == "codex":
            self.assertTrue(merged.startswith(b"# project settings\n"))
        self.assertNotIn(self.target / settings,
                         [path for path, _ in self.plan()[0]])

    def test_a_managed_registration_sharing_a_group_with_a_user_hook_stops(self):
        events = installer.hook_settings(self.host)["hooks"]
        group = events["PostToolUse"][0]
        group["hooks"][0]["timeout"] = 5
        group["hooks"].append({"type": "command", "command": "my-own-hook"})
        content = (installer.hooks_toml(events) if self.host == "codex"
                   else installer.json_bytes({"hooks": events}))
        self.write(self.settings_name(), content)
        with self.assertRaises(ValueError) as caught:
            self.plan()
        self.assertIn("differs", str(caught.exception))

    # --- files this revision no longer ships ---------------------------------

    def test_an_unshipped_file_is_reported_and_kept(self):
        mine = self.write(self.namespace + "/commands/my-own.md", b"mine\n")
        changes, backups, notes = self.plan()
        self.apply(changes)
        self.assertTrue(mine.is_file())
        self.assertNotIn(mine, backups)
        self.assertTrue(any("my-own.md" in note for note in notes), notes)
        self.assertTrue(any("--prune" in note for note in notes), notes)

    def test_prune_removes_it_after_backing_it_up(self):
        mine = self.write(self.namespace + "/commands/my-own.md", b"mine\n")
        changes, backups, notes = self.plan(prune=True)
        self.assertIn(mine, backups)
        self.apply(changes)
        self.assertFalse(mine.exists())
        self.assertTrue(any("Prune" in note for note in notes), notes)

    def test_incidental_files_are_never_orphaned_or_pruned(self):
        """Build artefacts and per-machine settings were not installed by us."""
        noise = [
            self.write(self.namespace + "/runtime/lib/__pycache__/config.cpython-313.pyc", b"\x00"),
            self.write(self.namespace + "/settings.local.json", b"{}\n"),
        ]
        changes, backups, notes = self.plan(prune=True)
        self.apply(changes)
        for path in noise:
            self.assertTrue(path.is_file(), path)
            self.assertNotIn(path, backups)
        self.assertFalse(any("settings.local" in note or "__pycache__" in note
                             for note in notes), notes)

    # --- telling a local edit from an upstream change ------------------------

    def test_a_baseline_names_the_customization_it_replaces(self):
        with tempfile.TemporaryDirectory(prefix="update-previous-") as previous_dir:
            previous = Path(previous_dir)
            seed_source(previous)
            # Upstream changed RULES.md between the two revisions; the project
            # changed an agent role. Only the second is a local edit.
            rules = self.namespace + "/RULES.md"
            baseline = installer.payload(previous, self.host, True)
            self.write(rules, baseline[rules] + b"\n<!-- upstream moved on -->\n")
            (previous / ".ai/RULES.md").write_bytes(
                (previous / ".ai/RULES.md").read_bytes() + b"\n<!-- upstream moved on -->\n")
            subprocess.run(["git", "add", "."], cwd=previous, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            role = self.namespace + "/agents/coder.md"
            self.write(role, self.installed[role] + b"\nMY LOCAL RULE\n")

            _, _, notes = self.plan(previous=previous)
            review = [note for note in notes if note.startswith("REVIEW")]
            self.assertEqual(1, len(review), notes)
            self.assertIn("coder.md", review[0])
            self.assertNotIn("RULES.md", review[0])

    def test_without_a_baseline_the_report_says_it_cannot_tell(self):
        self.write(self.namespace + "/agents/coder.md", b"# local\n")
        _, _, notes = self.plan()
        self.assertTrue(any("--from-ref" in note for note in notes), notes)

    # --- refusals ------------------------------------------------------------

    def test_update_requires_an_existing_installation(self):
        shutil.rmtree(self.target / self.namespace)
        with self.assertRaises(ValueError) as caught:
            self.plan()
        self.assertIn("requires an existing " + self.namespace, str(caught.exception))

    def test_a_legacy_ai_tree_must_be_migrated_first(self):
        self.write(".ai/runtime/phase.py", b"# legacy\n")
        with self.assertRaises(ValueError) as caught:
            self.plan()
        self.assertIn("--migrate-existing", str(caught.exception))

    def test_a_second_host_stops_the_update(self):
        other = ".claude" if self.host == "codex" else ".codex"
        self.write(other + "/runtime/phase.py", b"# the other host\n")
        with self.assertRaises(ValueError) as caught:
            self.plan()
        self.assertIn("reconcile dual cores", str(caught.exception))

    def test_a_link_in_the_installed_tree_is_refused(self):
        link = self.target / self.namespace / "linked"
        try:
            link.symlink_to(self.target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is not permitted here")
        with self.assertRaises(ValueError) as caught:
            self.plan()
        self.assertIn("Refusing linked path", str(caught.exception))


class ClaudeUpdateTests(UpdateTests):
    """The same contract, on the host whose entry file and skill root differ."""
    host = "claude"




"""Offline Git fixtures for reviewed workflow updates and ownership provenance."""
from pathlib import Path
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("workflow_update", ROOT / ".ai/update.py")
update = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(update)
installer = update.installer


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout.strip()


class ReviewedUpdates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="update-fixture-")
        cls.source = Path(cls.temp.name) / "source"
        cls.source.mkdir()
        for folder in (".ai", ".agents", ".planning"):
            shutil.copytree(ROOT / folder, cls.source / folder,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        git("init", "--quiet", cwd=cls.source)
        git("add", ".", cwd=cls.source)
        git("-c", "user.name=Fixture", "-c", "user.email=test@example.invalid", "commit", "--quiet", "-m", "baseline", cwd=cls.source)
        cls.first = git("rev-parse", "HEAD", cwd=cls.source)
        cls.baseline = Path(cls.temp.name) / "baseline"
        update.fetch(str(cls.source), cls.first, cls.baseline)
        rules = cls.source / ".ai/RULES.md"
        rules.write_bytes(rules.read_bytes() + b"\nPinned upstream fixture addition.\n")
        optional = cls.source / ".planning/config.yaml"
        optional.write_bytes(optional.read_bytes() + b"\nnew_optional: example\n")
        git("add", ".", cwd=cls.source)
        git("-c", "user.name=Fixture", "-c", "user.email=test@example.invalid", "commit", "--quiet", "-m", "upstream change", cwd=cls.source)
        cls.second = git("rev-parse", "HEAD", cwd=cls.source)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="update-target-")
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / "project"
        result = subprocess.run([sys.executable, str(ROOT / ".ai/install.py"), "--source", str(self.source),
                                 "--ref", self.first, "--target", str(self.target), "--skip-deps", "--no-hooks"],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)

    def plan(self, host="codex", hooks=False):
        return update.build_plan(self.source, self.target, host, hooks, str(self.source), self.second, self.baseline)

    def entry(self, plan, name):
        return next(e for e in plan["entries"] if e["path"] == name)

    def snapshot(self):
        return {p.relative_to(self.target).as_posix(): p.read_bytes() for p in self.target.rglob("*")
                if p.is_file() and ".git" not in p.parts}

    def test_manifest_ownership_and_content_diff_not_version_stamp(self):
        manifest = update.load_manifest(self.target, "codex")
        self.assertEqual(manifest["current"]["revision"], self.first)
        self.assertEqual(manifest["files"][".codex/RULES.md"]["classification"], "upstream-managed")
        manifest["current"]["revision"] = self.second  # A false stamp cannot hide changed bytes.
        (self.target / ".codex/workflow-ownership.json").write_bytes(installer.json_bytes(manifest))
        plan = self.plan()
        entry = self.entry(plan, ".codex/RULES.md")
        self.assertEqual(entry["action"], "write")
        self.assertIn("Pinned upstream fixture addition", entry["diff"])

    def test_dry_run_preserves_every_byte_and_reports_optional(self):
        before = self.snapshot()
        plan = self.plan()
        self.assertEqual(self.snapshot(), before)
        config = self.entry(plan, ".planning/config.yaml")
        self.assertIn("new_optional", config["optional_defaults"])
        self.assertNotIn("new_optional", yaml.safe_load(__import__('base64').b64decode(config["candidate_base64"])))

    def test_apply_preserves_project_history_hooks_and_models_and_provenance(self):
        (self.target / "code.py").write_text("user code\n")
        (self.target / ".planning/phases").mkdir(exist_ok=True)
        (self.target / ".planning/phases/plan.md").write_text("user plan\n")
        settings = self.target / ".codex/config.toml"
        settings.write_text('model = "project-model"\n[agents]\nmax_concurrent_threads_per_session = 4\n')
        plan = self.plan(hooks=True)
        changed = update.apply_plan(plan, self.source, self.baseline)
        self.assertIn(".codex/RULES.md", changed)
        parsed = tomllib.loads(settings.read_text())
        self.assertEqual(parsed["model"], "project-model")
        self.assertEqual(parsed["agents"]["max_concurrent_threads_per_session"], 4)
        self.assertTrue(parsed["hooks"])
        self.assertEqual((self.target / "code.py").read_text(), "user code\n")
        self.assertEqual((self.target / ".planning/phases/plan.md").read_text(), "user plan\n")
        manifest = update.load_manifest(self.target, "codex")
        self.assertEqual(manifest["current"]["revision"], self.second)
        self.assertEqual(manifest["previous"]["revision"], self.first)
        self.assertEqual(manifest["files"][".codex/RULES.md"]["installed_sha256"], update.digest((self.target / ".codex/RULES.md").read_bytes()))
        # Repeat is a byte no-op and does not overwrite previous provenance.
        again = update.build_plan(self.source, self.target, "codex", True, str(self.source), self.second, self.source)
        self.assertEqual(update.apply_plan(again, self.source, self.source), [])

    def test_customization_requires_review_and_keep_remains_customized(self):
        path = self.target / ".codex/RULES.md"
        path.write_bytes(path.read_bytes() + b"\nUser rule.\n")
        plan = self.plan()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Unresolved conflict"):
            update.apply_plan(plan, self.source, self.baseline)
        self.assertEqual(before, self.snapshot())
        plan["resolutions"][".codex/RULES.md"] = {"action": "keep", "classification": "customized"}
        update.apply_plan(plan, self.source, self.baseline)
        self.assertIn(b"User rule", path.read_bytes())
        self.assertEqual(update.load_manifest(self.target, "codex")["files"][".codex/RULES.md"]["classification"], "customized")

    def test_nested_missing_required_config_preserves_existing_values(self):
        config = self.target / ".planning/config.yaml"
        old = {"workflow": {"auto_advance": True}, "agents": {"coder": {"model": "custom"}},
               "handoff": {"context_tokens": 30000}, "verification": {"commands": [["python", "check.py"]]}}
        config.write_text(yaml.safe_dump(old))
        plan = self.plan()
        row = self.entry(plan, ".planning/config.yaml")
        self.assertIn("workflow.isolation", row["required_config"])
        update.apply_plan(plan, self.source, self.baseline)
        result = yaml.safe_load(config.read_text())
        self.assertTrue(result["workflow"]["auto_advance"])
        self.assertEqual(result["workflow"]["isolation"], "auto")
        self.assertEqual(result["agents"], old["agents"])
        self.assertEqual(result["verification"]["commands"], old["verification"]["commands"])
        self.assertEqual(result["handoff"]["context_tokens"], 30000)

    def test_config_wrong_types_enums_are_conflicts_and_never_reset(self):
        for value in ({"workflow": "custom"}, {"workflow": {"isolation": "none"}},
                      {"handoff": {"context_tokens": "oops"}}, {"commit_docs": "yes"},
                      {"delivery": {"merge_method": "force"}}):
            with self.subTest(value=value):
                config = self.target / ".planning/config.yaml"
                config.write_text(yaml.safe_dump(value))
                plan = self.plan()
                self.assertTrue(self.entry(plan, ".planning/config.yaml")["conflict"])
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    update.apply_plan(plan, self.source, self.baseline)
                self.assertEqual(before, self.snapshot())

    def test_legacy_can_upgrade_after_reviewed_classification(self):
        (self.target / ".codex/workflow-ownership.json").unlink()
        plan = self.plan()
        row = self.entry(plan, ".codex/RULES.md")
        self.assertEqual(row["classification"], "unproven")
        self.assertTrue(row["conflict"])
        with self.assertRaises(ValueError):
            update.apply_plan(plan, self.source, self.baseline)
        for entry in plan["entries"]:
            if entry["classification"] == "unproven":
                plan["resolutions"][entry["path"]] = {"action": entry["action"], "classification": "upstream-managed"}
        update.apply_plan(plan, self.source, self.baseline)
        self.assertIn(b"Pinned upstream fixture addition", (self.target / ".codex/RULES.md").read_bytes())

    def test_stale_plan_candidate_tampering_and_changed_manifest_fail_before_writes(self):
        plan = self.plan()
        forged = copy.deepcopy(plan)
        self.entry(forged, ".codex/RULES.md")["candidate_base64"] = "dGFtcGVyZWQ="
        with self.assertRaisesRegex(ValueError, "stale"):
            update.apply_plan(forged, self.source, self.baseline)
        path = self.target / ".codex/RULES.md"
        path.write_bytes(path.read_bytes() + b"concurrent edit")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "stale"):
            update.apply_plan(plan, self.source, self.baseline)
        self.assertEqual(before, self.snapshot())

    def test_project_additions_are_preserved_and_not_pruned(self):
        path = self.target / ".codex/local-command.md"
        path.write_text("project addition")
        plan = self.plan()
        self.assertEqual(self.entry(plan, ".codex/local-command.md")["classification"], "project")
        update.apply_plan(plan, self.source, self.baseline)
        self.assertEqual(path.read_text(), "project addition")

    def test_portable_traversal_and_project_code_ownership_rejected(self):
        for name in ("../escape", "C:/escape", ".git/config", "/absolute", "x\\y", "a/../../b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                update.destination(self.target, name)
        manifest = update.load_manifest(self.target, "codex")
        manifest["files"]["code.py"] = {"classification": "upstream-managed", "installed_sha256": None, "upstream_sha256": None}
        (self.target / ".codex/workflow-ownership.json").write_bytes(installer.json_bytes(manifest))
        with self.assertRaisesRegex(ValueError, "project code"):
            self.plan()

    def test_link_destination_rejected(self):
        with patch.object(installer, "safe_path", side_effect=ValueError("Refusing linked path")):
            with self.assertRaisesRegex(ValueError, "linked"):
                self.plan()

    def test_cli_default_dry_run_and_reviewed_hash_required(self):
        before = self.snapshot()
        plan_path = Path(self.temp.name) / "review.json"
        result = subprocess.run([sys.executable, str(ROOT / ".ai/update.py"), "--target", str(self.target),
                                 "--source", str(self.source), "--ref", self.second, "--no-hooks", "--plan", str(plan_path)],
                                text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Pinned upstream fixture addition", result.stdout)
        self.assertEqual(before, self.snapshot())
        result = subprocess.run([sys.executable, str(ROOT / ".ai/update.py"), "--apply", str(plan_path)],
                                text=True, encoding="utf-8", capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, self.snapshot())
        result = subprocess.run([sys.executable, str(ROOT / ".ai/update.py"), "--apply", str(plan_path),
                                 "--reviewed-plan-sha256", update.digest(plan_path.read_bytes())],
                                text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_preexisting_equal_workflow_file_not_claimed_on_fresh_install(self):
        target = Path(self.temp.name) / "existing"
        target.mkdir()
        incoming = installer.payload(self.baseline, "codex", False)
        path = target / ".codex/RULES.md"
        path.parent.mkdir()
        path.write_bytes(incoming[".codex/RULES.md"])
        result = subprocess.run([sys.executable, str(ROOT / ".ai/install.py"), "--source", str(self.source),
                                 "--ref", self.first, "--target", str(target), "--skip-deps", "--no-hooks"], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(update.load_manifest(target, "codex")["files"][".codex/RULES.md"]["classification"], "customized")


if __name__ == "__main__":
    unittest.main()
