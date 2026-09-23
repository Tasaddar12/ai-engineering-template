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


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("update_installer", ROOT / ".ai/install.py")
update = load("install_update", ROOT / ".ai/install_update.py")


def seed_source(directory):
    for name in (".ai", ".agents", ".planning"):
        shutil.copytree(ROOT / name, directory / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    subprocess.run(["git", "init", "--quiet", str(directory)], check=True)
    subprocess.run(["git", "add", "."], cwd=directory, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class UpdateTests(unittest.TestCase):
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
        return update.plan_update(self.source, self.target, self.host, True,
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


if __name__ == "__main__":
    unittest.main()
