"""Refresh an installed workflow onto a newer revision without losing the project.

An update is the one mode that runs against a tree the project has been living
in, so every test here is really the same question asked about a different file:
did the project's own material survive the refresh?
"""

import importlib.util
import os
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


installer = load("update_installer", ROOT / "bin/install.py")
legacy_update = load("install_update", ROOT / "bin/update.py")


def seed_source(directory):
    for name in ("agents", "commands", "engineer", "hooks", "scripts", "skills", "bin"):
        if not (ROOT / name).exists():
            continue
        shutil.copytree(ROOT / name, directory / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (directory / ".planning").mkdir(exist_ok=True)
    (directory / ".planning/config.yaml").write_text("fixture: true\n", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet", str(directory)], check=True)
    subprocess.run(["git", "add", "."], cwd=directory, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class UpdateTests(unittest.TestCase):
    """Retained update protections expressed through explicit reviewed plans."""
    host = "codex"

    @classmethod
    def setUpClass(cls):
        cls.source_temp = tempfile.TemporaryDirectory(prefix="update-source-")
        cls.source = Path(cls.source_temp.name)
        seed_source(cls.source)

    @classmethod
    def tearDownClass(cls):
        cls.source_temp.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="update-target-")
        self.addCleanup(self.temporary.cleanup)
        self.target = Path(self.temporary.name)
        self.namespace = "." + self.host
        self.installed = installer.payload(self.source, self.host, True)
        installer.write_changes(self.target, [(self.target / name, data) for name, data in self.installed.items()])
        legacy_update.record_install(self.target, self.host, str(self.source), "baseline", self.installed)

    def write(self, name, content):
        path = self.target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def read(self, name):
        return (self.target / name).read_bytes()

    @unittest.skipIf(os.name == "nt", "native POSIX permissions")
    def test_reviewed_update_repairs_unchanged_launcher_execute_mode(self):
        name = self.namespace + "/engineer/bin/engineer_run"
        path = self.target / name
        before = path.read_bytes()
        path.chmod(0o640)
        plan = self.plan()
        self.assertFalse(self.row(plan, name)["conflict"])
        self.assertIn(name, self.apply(plan))
        self.assertEqual(before, path.read_bytes())
        self.assertEqual(0o111, path.stat().st_mode & 0o111)
        self.assertEqual([], self.apply(self.plan()))

    def entry_name(self):
        return "CLAUDE.md" if self.host == "claude" else "AGENTS.md"

    def plan(self, hooks=True):
        return legacy_update.build_plan(self.source, self.target, self.host, hooks,
                                        str(self.source), "candidate", self.source)

    def row(self, plan, name):
        return next(row for row in plan["entries"] if row["path"] == name)

    def snapshot(self):
        return {p.relative_to(self.target).as_posix(): p.read_bytes()
                for p in self.target.rglob("*") if p.is_file()}

    def apply(self, plan):
        return legacy_update.apply_plan(plan, self.source, self.source)

    def approve_replacement(self, plan, name):
        self.assertTrue(self.row(plan, name)["conflict"])
        plan["resolutions"][name] = {"action": "write", "classification": "upstream-managed"}

    def test_scout_metadata_export_is_host_specific_and_update_is_idempotent(self):
        self.review_role("scout")

    def test_targeted_fixer_export_and_native_update_are_idempotent(self):
        self.review_role("targeted-fixer")
        if self.host == "codex":
            native = installer.tomllib.loads(self.read(".codex/agents/targeted-fixer.toml").decode())
            self.assertEqual("gpt-6-luna", native["model"])
            self.assertEqual("high", native["model_reasoning_effort"])
            self.assertIn(self.read(".codex/agents/targeted-fixer.md").decode(), native["developer_instructions"])

    def review_role(self, name):
        path = self.namespace + "/agents/" + name + ".md"
        old = ("---\nname: " + name + "\nmodel: wrong\neffort: max\n---\nCustom old body.\n").encode()
        self.write(path, old)
        before = self.snapshot()
        plan = self.plan()
        with self.assertRaisesRegex(ValueError, "Unresolved conflict"):
            self.apply(plan)
        self.assertEqual(before, self.snapshot())
        self.approve_replacement(plan, path)
        self.apply(plan)
        expected = installer.render_asset("agents/" + name + ".md", (self.source / "agents" / (name + ".md")).read_bytes(), self.host)
        self.assertEqual(expected, self.read(path))
        saved = list((self.target / ".workflow-backups").glob("*/files/" + path))
        self.assertEqual([old], [p.read_bytes() for p in saved])
        self.assertEqual([], self.apply(self.plan()))

    def test_worker_defaults_update_preserves_config_and_is_idempotent(self):
        config = self.read(".planning/config.yaml") + b"\nproject_model: custom\n"
        self.write(".planning/config.yaml", config)
        for name in ("executor", "planner"):
            self.review_role(name)
        self.assertEqual(config, self.read(".planning/config.yaml"))

    def test_update_payload_excludes_source_only_maintenance_history(self):
        source_history = self.source / ".ai/maintenance/never-install.md"
        source_history.parent.mkdir(parents=True, exist_ok=True)
        source_history.write_bytes(b"source-only history")
        self.assertFalse(any("maintenance/" in row["path"] for row in self.plan()["entries"]))

    def test_no_hooks_update_canonicalizes_codex_settings_and_preserves_hooks(self):
        if self.host != "codex":
            self.skipTest("Codex project setting")
        original = (b'\xef\xbb\xbf# custom\r\nmodel = "keep"\r\n[agents]\r\n'
                    b'max_threads = 4 # retained comment\r\nmax_concurrent_threads_per_session = 5\r\n'
                    b'[hooks]\r\nStop = []\r\n')
        self.write(".codex/config.toml", original)
        self.apply(self.plan(hooks=False))
        content = self.read(".codex/config.toml")
        self.assertTrue(content.startswith(b'\xef\xbb\xbf# custom\r\nmodel = "keep"\r\n'))
        self.assertIn(b'[hooks]\r\nStop = []\r\n', content)
        settings = installer.tomllib.loads(content.decode("utf-8-sig"))
        self.assertEqual(12, settings["agents"]["max_concurrent_threads_per_session"])
        self.assertNotIn("max_threads", settings["agents"])
        self.assertEqual([], self.apply(self.plan(hooks=False)))

    def test_no_hooks_update_invalid_codex_settings_are_preflight_only(self):
        if self.host != "codex":
            self.skipTest("Codex project setting")
        self.write(".codex/config.toml", b'agents = {max_threads = 4}\n')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "inline agents"):
            self.plan(hooks=False)
        self.assertEqual(before, self.snapshot())

    def test_project_records_are_never_rewritten(self):
        records = {".planning/" + name + ".md": ("Authored " + name + "\r\n").encode()
                   for name in ("PROJECT", "REQUIREMENTS", "ROADMAP", "STATE")}
        records[".planning/phases/04-x/04-01-SUMMARY.md"] = b"shipped evidence\r\n"
        for name, data in records.items():
            self.write(name, data)
        self.apply(self.plan())
        for name, data in records.items():
            self.assertEqual(data, self.read(name))

    def test_user_language_and_checkpoint_overrides_remain_byte_identical(self):
        config = self.read(".planning/config.yaml").replace(b"response_language: null", b"response_language: French")
        config = config.replace(b"human_verify_mode: end-of-phase", b"human_verify_mode: mid-flight")
        config = config.replace(b"discuss_mode: discuss", b"discuss_mode: project-discussion")
        self.write(".planning/config.yaml", config)
        plan = self.plan()
        self.assertIsNone(self.row(plan, ".planning/config.yaml")["conflict"])
        self.apply(plan)
        self.assertEqual(config, self.read(".planning/config.yaml"))

    def test_an_aged_shipped_file_is_refreshed_only_after_review(self):
        self.review_role("executor")

    def test_an_update_adds_only_the_ignore_rules_a_project_lacks(self):
        older = b"# local rules\nprivate/\n.workflow-backups/\n"
        self.write(".gitignore", older)
        self.apply(self.plan())
        lines = self.read(".gitignore").decode().splitlines()
        self.assertTrue(self.read(".gitignore").startswith(older))
        self.assertEqual(1, lines.count(".workflow-backups/"))
        self.assertEqual(1, lines.count(".planning/handoffs/"))

    def test_a_second_update_changes_nothing(self):
        self.apply(self.plan())
        before = self.snapshot()
        self.assertEqual([], self.apply(self.plan()))
        self.assertEqual(before, self.snapshot())

    def test_entry_file_swaps_only_the_managed_block(self):
        name = self.entry_name()
        prefix, suffix = b"House style\r\n", b"Footer\r\n"
        self.write(name, prefix + self.read(name) + suffix)
        self.apply(self.plan())
        rebuilt = self.read(name)
        self.assertTrue(rebuilt.startswith(prefix))
        self.assertTrue(rebuilt.endswith(suffix))
        self.assertEqual(1, rebuilt.count(installer.AGENT_MARKER.encode()))
        self.assertEqual(1, rebuilt.count(installer.AGENT_END.encode()))

    def test_an_ambiguous_managed_block_stops_the_update(self):
        name = self.entry_name()
        self.write(name, self.read(name) * 2)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            self.plan()
        self.assertEqual(before, self.snapshot())

    def test_user_hooks_in_host_settings_survive(self):
        user = {"matcher": "MyTool", "hooks": [{"type": "command", "command": "my-own-hook"}]}
        events = installer.hook_settings(self.host)["hooks"]
        events["PreToolUse"].append(user)
        name = self.namespace + ("/config.toml" if self.host == "codex" else "/settings.json")
        self.write(name, installer.hooks_toml(events) if self.host == "codex" else installer.json_bytes({"hooks": events}))
        self.apply(self.plan())
        self.assertIn(b"my-own-hook", self.read(name))
        self.assertIn(b"worktree-path-guard.py", self.read(name))

    def test_an_aged_managed_hook_registration_is_replaced(self):
        events = installer.hook_settings(self.host)["hooks"]
        for groups in events.values():
            for group in groups:
                group["hooks"][0]["timeout"] = 5
        name = self.namespace + ("/config.toml" if self.host == "codex" else "/settings.json")
        old = installer.hooks_toml(events) if self.host == "codex" else installer.json_bytes({"hooks": events})
        self.write(name, old)
        self.apply(self.plan())
        parsed = installer.tomllib.loads(self.read(name).decode()) if self.host == "codex" else installer.json.loads(self.read(name))
        self.assertEqual(installer.hook_settings(self.host)["hooks"], parsed["hooks"])
        self.assertTrue(any(p.read_bytes() == old for p in (self.target / ".workflow-backups").glob("*/files/" + name)))

    def test_a_managed_registration_sharing_a_group_with_a_user_hook_stops(self):
        events = installer.hook_settings(self.host)["hooks"]
        events["PostToolUse"][0]["hooks"].append({"type": "command", "command": "my-own-hook"})
        name = self.namespace + ("/config.toml" if self.host == "codex" else "/settings.json")
        self.write(name, installer.hooks_toml(events) if self.host == "codex" else installer.json_bytes({"hooks": events}))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "shares a group"):
            self.plan()
        self.assertEqual(before, self.snapshot())

    def test_an_unshipped_file_is_reported_and_kept(self):
        name = self.namespace + "/commands/my-own.md"
        self.write(name, b"mine\n")
        plan = self.plan()
        self.assertEqual("project", self.row(plan, name)["classification"])
        self.apply(plan)
        self.assertEqual(b"mine\n", self.read(name))

    def test_reviewed_retirement_removes_only_owned_file_after_backup(self):
        name = self.namespace + "/commands/retired.md"
        self.write(name, b"retired\n")
        manifest_path = legacy_update.manifest_path(self.target, self.host)
        manifest = legacy_update.load_manifest(self.target, self.host)
        manifest["files"][name] = {"classification": "upstream-managed", "installed_sha256": installer.digest(b"retired\n"), "upstream_sha256": installer.digest(b"retired\n")}
        manifest_path.write_bytes(installer.json_bytes(manifest))
        plan = self.plan()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Unresolved conflict"):
            self.apply(plan)
        self.assertEqual(before, self.snapshot())
        plan["resolutions"][name] = {"action": "delete", "classification": "upstream-managed"}
        self.apply(plan)
        self.assertFalse((self.target / name).exists())
        self.assertEqual([b"retired\n"], [p.read_bytes() for p in (self.target / ".workflow-backups").glob("*/files/" + name)])

    def test_incidental_files_are_never_orphaned_or_pruned(self):
        names = [self.namespace + "/engineer/bin/lib/__pycache__/config.cpython-313.pyc", self.namespace + "/settings.local.json"]
        for name in names:
            self.write(name, b"incidental")
        plan = self.plan()
        self.assertTrue(set(names).isdisjoint(row["path"] for row in plan["entries"]))
        self.apply(plan)
        for name in names:
            self.assertEqual(b"incidental", self.read(name))

    def test_a_baseline_names_the_customization_it_replaces(self):
        name = self.namespace + "/agents/executor.md"
        self.write(name, self.read(name) + b"Local rule\n")
        plan = self.plan()
        self.assertEqual("customized", self.row(plan, name)["classification"])
        self.assertEqual("upstream-managed", self.row(plan, self.namespace + "/engineer/RULES.md")["classification"])

    def test_without_ownership_equal_bytes_are_unproven(self):
        legacy_update.manifest_path(self.target, self.host).unlink()
        row = self.row(self.plan(), self.namespace + "/agents/executor.md")
        self.assertEqual("unproven", row["classification"])
        self.assertEqual("unchanged", row["comparison"])

    def test_update_requires_an_existing_installation(self):
        (self.target / self.namespace / "engineer/bin/engineer.py").unlink()
        with self.assertRaisesRegex(ValueError, "existing installation"):
            self.plan()

    def test_a_legacy_ai_tree_must_be_migrated_first(self):
        self.write(".ai/runtime/phase.py", b"legacy")
        with self.assertRaisesRegex(ValueError, "migrate"):
            self.plan()

    def test_a_second_host_stops_the_update(self):
        other = ".claude" if self.host == "codex" else ".codex"
        self.write(other + "/engineer/bin/engineer.py", b"second host")
        with self.assertRaisesRegex(ValueError, "second host"):
            self.plan()

    def test_a_link_in_the_installed_tree_is_refused(self):
        link = self.target / self.namespace / "linked"
        try:
            link.symlink_to(self.target, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation unavailable")
        with self.assertRaisesRegex(ValueError, "linked path"):
            self.plan()


class ClaudeUpdateTests(UpdateTests):
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
_spec = importlib.util.spec_from_file_location("workflow_update", ROOT / "bin/update.py")
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
        for folder in ("agents", "commands", "engineer", "hooks", "scripts", "skills", "bin"):
            if not (ROOT / folder).exists():
                continue
            shutil.copytree(ROOT / folder, cls.source / folder,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        git("init", "--quiet", cwd=cls.source)
        git("add", ".", cwd=cls.source)
        git("-c", "user.name=Fixture", "-c", "user.email=test@example.invalid", "commit", "--quiet", "-m", "baseline", cwd=cls.source)
        cls.first = git("rev-parse", "HEAD", cwd=cls.source)
        cls.baseline = Path(cls.temp.name) / "baseline"
        update.fetch(str(cls.source), cls.first, cls.baseline)
        rules = cls.source / "engineer/RULES.md"
        rules.write_bytes(rules.read_bytes() + b"\nPinned upstream fixture addition.\n")
        (cls.source / ".planning").mkdir(exist_ok=True)
        (cls.source / ".planning/config.yaml").write_text("fixture: true\n", encoding="utf-8")
        optional = cls.source / "engineer/templates/config.yaml"
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
        result = subprocess.run([sys.executable, str(ROOT / "bin/install.py"), "--source", str(self.source),
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
        self.assertEqual(manifest["files"][".codex/engineer/RULES.md"]["classification"], "upstream-managed")
        manifest["current"]["revision"] = self.second  # A false stamp cannot hide changed bytes.
        (self.target / ".codex/workflow-ownership.json").write_bytes(installer.json_bytes(manifest))
        plan = self.plan()
        entry = self.entry(plan, ".codex/engineer/RULES.md")
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
        self.assertIn(".codex/engineer/RULES.md", changed)
        parsed = tomllib.loads(settings.read_text())
        self.assertEqual(parsed["model"], "project-model")
        self.assertEqual(parsed["agents"]["max_concurrent_threads_per_session"], 12)
        self.assertTrue(parsed["hooks"])
        self.assertEqual((self.target / "code.py").read_text(), "user code\n")
        self.assertEqual((self.target / ".planning/phases/plan.md").read_text(), "user plan\n")
        manifest = update.load_manifest(self.target, "codex")
        self.assertEqual(manifest["current"]["revision"], self.second)
        self.assertEqual(manifest["previous"]["revision"], self.first)
        self.assertEqual(manifest["files"][".codex/engineer/RULES.md"]["installed_sha256"], update.digest((self.target / ".codex/engineer/RULES.md").read_bytes()))
        # Repeat is a byte no-op and does not overwrite previous provenance.
        again = update.build_plan(self.source, self.target, "codex", True, str(self.source), self.second, self.source)
        self.assertEqual(update.apply_plan(again, self.source, self.source), [])

    def test_customization_requires_review_and_keep_remains_customized(self):
        path = self.target / ".codex/engineer/RULES.md"
        path.write_bytes(path.read_bytes() + b"\nUser rule.\n")
        plan = self.plan()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Unresolved conflict"):
            update.apply_plan(plan, self.source, self.baseline)
        self.assertEqual(before, self.snapshot())
        plan["resolutions"][".codex/engineer/RULES.md"] = {"action": "keep", "classification": "customized"}
        update.apply_plan(plan, self.source, self.baseline)
        self.assertIn(b"User rule", path.read_bytes())
        self.assertEqual(update.load_manifest(self.target, "codex")["files"][".codex/engineer/RULES.md"]["classification"], "customized")

    def managed_block_upgrade_fixture(self, host):
        target = Path(self.temp.name) / ("managed-block-" + host)
        result = subprocess.run([sys.executable, str(ROOT / "bin/install.py"),
                                 "--source", str(self.source), "--ref", self.first,
                                 "--target", str(target), "--host", host,
                                 "--skip-deps", "--no-hooks"], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        later = Path(self.temp.name) / ("later-source-" + host)
        update.fetch(str(self.source), self.second, later)
        asset = later / "bin/install-assets/agent-entry.txt"
        asset.write_bytes(asset.read_bytes() + b"\nNew upstream instruction.\n")
        git("add", ".", cwd=later)
        git("-c", "user.name=Fixture", "-c", "user.email=test@example.invalid",
            "commit", "--quiet", "-m", "later managed block", cwd=later)
        return target, later, git("rev-parse", "HEAD", cwd=later)

    def test_kept_managed_block_customization_remains_conflicted_for_both_hosts(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                target, later, third = self.managed_block_upgrade_fixture(host)
                entry_name = "AGENTS.md" if host == "codex" else "CLAUDE.md"
                entry_path = target / entry_name
                original = entry_path.read_bytes()
                customized = original.replace(installer.AGENT_END.encode(),
                                              b"Keep this local instruction.\n" + installer.AGENT_END.encode())
                preserved = b"Project guidance before.\n" + customized + b"Project guidance after.\n"
                entry_path.write_bytes(preserved)
                plan = update.build_plan(self.source, target, host, False, str(self.source),
                                         self.second, self.baseline)
                self.assertTrue(self.entry(plan, entry_name)["conflict"])
                plan["resolutions"][entry_name] = {"action": "keep", "classification": "customized"}
                update.apply_plan(plan, self.source, self.baseline)
                self.assertEqual(entry_path.read_bytes(), preserved)
                record = update.load_manifest(target, host)["files"][entry_name]
                self.assertEqual(record["installed_sha256"], update.digest(preserved))
                for candidate, revision, baseline in ((self.source, self.second, self.source),
                                                      (later, third, self.source)):
                    repeated = update.build_plan(candidate, target, host, False, str(candidate),
                                                 revision, baseline)
                    # Recording kept installed bytes must not prove upstream ownership.
                    self.assertTrue(self.entry(repeated, entry_name)["conflict"])
                    before = entry_path.read_bytes()
                    with self.assertRaisesRegex(ValueError, "Unresolved conflict"):
                        update.apply_plan(repeated, candidate, baseline)
                    self.assertEqual(entry_path.read_bytes(), before)
                    repeated["resolutions"][entry_name] = {"action": "keep", "classification": "customized"}
                    update.apply_plan(repeated, candidate, baseline)
                    self.assertEqual(entry_path.read_bytes(), preserved)
                # Even after provenance advances, another update still requires review.
                final = update.build_plan(later, target, host, False, str(later), third, later)
                self.assertTrue(self.entry(final, entry_name)["conflict"])

    def test_unchanged_managed_block_upgrades_preserving_surrounding_guidance_for_both_hosts(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                target, later, third = self.managed_block_upgrade_fixture(host)
                entry_name = "AGENTS.md" if host == "codex" else "CLAUDE.md"
                entry_path = target / entry_name
                prefix, suffix = b"Project guidance before.\n", b"Project guidance after.\n"
                entry_path.write_bytes(prefix + entry_path.read_bytes() + suffix)
                plan = update.build_plan(later, target, host, False, str(later), third,
                                         self.baseline)
                self.assertIsNone(self.entry(plan, entry_name)["conflict"])
                update.apply_plan(plan, later, self.baseline)
                content = entry_path.read_bytes()
                self.assertTrue(content.startswith(prefix))
                self.assertTrue(content.endswith(suffix))
                self.assertIn(b"New upstream instruction.", content)
                repeat = update.build_plan(later, target, host, False, str(later), third, later)
                self.assertIsNone(self.entry(repeat, entry_name)["conflict"])
                self.assertEqual(update.apply_plan(repeat, later, later), [])

    def test_nested_missing_required_config_preserves_existing_values(self):
        config = self.target / ".planning/config.yaml"
        old = {"workflow": {"auto_advance": True}, "agents": {"executor": {"model": "custom"}},
               "handoff": {"context_tokens": 30000}, "verification": {"commands": [["python", "check.py"]]}}
        config.write_text("workflow:\n  auto_advance: true\nagents:\n  executor:\n    model: custom\nhandoff:\n  context_tokens: 30000\nverification:\n  commands: [[python, check.py]]\n")
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

    def test_missing_required_keys_extend_flow_parents_and_json_without_resetting_values(self):
        old = {"workflow": {"auto_advance": True}, "handoff": {"context_tokens": 30000},
               "agents": {"executor": {"model": "custom"}}, "verification": {"commands": [["python", "check.py"]]}}
        documents = ("# project comment\nworkflow: {auto_advance: true} # keep this comment\n"
                     "handoff: {context_tokens: 30000}\nagents: {executor: {model: custom}}\n"
                     "verification: {commands: [[python, check.py]]}\n", json.dumps(old))
        for document in documents:
            with self.subTest(document=document):
                config = self.target / ".planning/config.yaml"
                config.write_text(document)
                plan = self.plan()
                self.assertIsNone(self.entry(plan, ".planning/config.yaml")["conflict"])
                update.apply_plan(plan, self.source, self.baseline)
                result = yaml.safe_load(config.read_text())
                self.assertEqual("auto", result["workflow"]["isolation"])
                self.assertTrue(result["workflow"]["auto_advance"])
                self.assertEqual(old["agents"], result["agents"])
                self.assertEqual(old["verification"]["commands"], result["verification"]["commands"])
                self.assertEqual(30000, result["handoff"]["context_tokens"])
                if document.startswith("#"):
                    self.assertIn("# project comment", config.read_text())
                    self.assertIn("# keep this comment", config.read_text())

    def test_legacy_can_upgrade_after_reviewed_classification(self):
        (self.target / ".codex/workflow-ownership.json").unlink()
        plan = self.plan()
        row = self.entry(plan, ".codex/engineer/RULES.md")
        self.assertEqual(row["classification"], "unproven")
        self.assertTrue(row["conflict"])
        with self.assertRaises(ValueError):
            update.apply_plan(plan, self.source, self.baseline)
        for entry in plan["entries"]:
            if entry["classification"] == "unproven":
                plan["resolutions"][entry["path"]] = {"action": "write" if entry["conflict"] else entry["action"], "classification": "upstream-managed"}
        update.apply_plan(plan, self.source, self.baseline)
        self.assertIn(b"Pinned upstream fixture addition", (self.target / ".codex/engineer/RULES.md").read_bytes())

    def test_target_path_aliases_have_identical_review_plan_identity(self):
        aliases = [self.target / ".." / self.target.name]
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes
            get_short_path = ctypes.WinDLL("kernel32", use_last_error=True).GetShortPathNameW
            get_short_path.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
            get_short_path.restype = wintypes.DWORD
            buffer = ctypes.create_unicode_buffer(32768)
            length = get_short_path(str(self.target), buffer, len(buffer))
            self.assertGreater(length, 0, ctypes.get_last_error())
            aliases.append(Path(buffer.value))
        for alias in aliases:
            with self.subTest(alias=str(alias)):
                plan = update.build_plan(self.source, alias, "codex", False,
                                         str(self.source), self.second, self.baseline)
                self.assertEqual(plan["target"], str(self.target.resolve()))
                update.apply_plan(plan, self.source, self.baseline)
                self.assertIn(b"Pinned upstream fixture addition",
                              (self.target / ".codex/engineer/RULES.md").read_bytes())
                # Alias normalization must not weaken the actual content guard.
                forged = copy.deepcopy(plan)
                self.entry(forged, ".codex/engineer/RULES.md")["candidate_base64"] = "dGFtcGVyZWQ="
                with self.assertRaisesRegex(ValueError, "stale"):
                    update.apply_plan(forged, self.source, self.baseline)

    def test_stale_plan_candidate_tampering_and_changed_manifest_fail_before_writes(self):
        plan = self.plan()
        forged = copy.deepcopy(plan)
        self.entry(forged, ".codex/engineer/RULES.md")["candidate_base64"] = "dGFtcGVyZWQ="
        with self.assertRaisesRegex(ValueError, "stale"):
            update.apply_plan(forged, self.source, self.baseline)
        path = self.target / ".codex/engineer/RULES.md"
        path.write_bytes(path.read_bytes() + b"concurrent edit")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "stale"):
            update.apply_plan(plan, self.source, self.baseline)
        self.assertEqual(before, self.snapshot())

    def test_invalid_resolution_schema_and_backup_parent_fail_before_any_write(self):
        for resolution in ([], {"action": "force"}, {"action": "write", "candidate_base64": "dGFtcGVyZWQ="}):
            with self.subTest(resolution=resolution):
                plan = self.plan()
                plan["resolutions"][".codex/engineer/RULES.md"] = resolution
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    update.apply_plan(plan, self.source, self.baseline)
                self.assertEqual(before, self.snapshot())
        obstruction = self.target / ".workflow-backups"
        obstruction.write_bytes(b"project-owned file")
        plan = self.plan()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "file used as parent"):
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
        with patch.object(installer, "destination", side_effect=ValueError("Refusing linked path")):
            with self.assertRaisesRegex(ValueError, "linked"):
                self.plan()

    def test_cli_default_dry_run_and_reviewed_hash_required(self):
        before = self.snapshot()
        plan_path = Path(self.temp.name) / "review.json"
        result = subprocess.run([sys.executable, str(ROOT / "bin/update.py"), "--target", str(self.target),
                                 "--source", str(self.source), "--ref", self.second, "--no-hooks", "--plan", str(plan_path)],
                                text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Pinned upstream fixture addition", result.stdout)
        self.assertEqual(before, self.snapshot())
        result = subprocess.run([sys.executable, str(ROOT / "bin/update.py"), "--apply", str(plan_path)],
                                text=True, encoding="utf-8", capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, self.snapshot())
        result = subprocess.run([sys.executable, str(ROOT / "bin/update.py"), "--apply", str(plan_path),
                                 "--reviewed-plan-sha256", update.digest(plan_path.read_bytes())],
                                text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_preexisting_equal_workflow_file_not_claimed_on_fresh_install(self):
        target = Path(self.temp.name) / "existing"
        target.mkdir()
        incoming = installer.payload(self.baseline, "codex", False)
        path = target / ".codex/engineer/RULES.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(incoming[".codex/engineer/RULES.md"])
        result = subprocess.run([sys.executable, str(ROOT / "bin/install.py"), "--source", str(self.source),
                                 "--ref", self.first, "--target", str(target), "--skip-deps", "--no-hooks"], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(update.load_manifest(target, "codex")["files"][".codex/engineer/RULES.md"]["classification"], "customized")


if __name__ == "__main__":
    unittest.main()
