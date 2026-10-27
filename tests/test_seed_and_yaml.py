"""Unfilled source seeds and valid historical YAML survive the runtime cutover."""
from pathlib import Path
import re
import sys
import unittest

from test_engineer_runtime import RuntimeCase, SOURCE

sys.path.insert(0, str(SOURCE/"engineer/bin"))
from lib.core import Failure
from lib.text import yaml_load


class SeedRoadmapPreservation(RuntimeCase):
    def assert_seed(self, seed):
        path = self.put(".planning/ROADMAP.md", seed)
        original = path.read_bytes()
        self.assertEqual(0, self.cli("roadmap.analyze")["phase_count"])
        self.assertFalse(self.cli("phase.locate", "01")["found"])
        self.assertEqual(original, path.read_bytes(), "read-only queries changed an unfilled source seed")
        phase = self.cli("phase.add", "Installed runtime")
        self.assertEqual("01", phase["phase"])
        self.assertEqual("Installed runtime", phase["name"])
        self.assertEqual("installed-runtime", phase["slug"])
        self.assertEqual("01-installed-runtime", Path(phase["directory"]).name)
        self.assertEqual("Installed runtime", self.cli("find-phase", "01")["name"])
        self.assertEqual("Installed runtime", self.cli("roadmap.get-phase", "01")["name"])
        self.assertEqual(1, self.cli("roadmap.analyze")["phase_count"])

    def test_full_copied_instructional_seed_is_not_five_real_phases(self):
        seed = (SOURCE/"engineer/templates/roadmap.md").read_text(encoding="utf-8")
        self.assert_seed(seed)
        saved = (self.root/".planning/ROADMAP.md").read_text(encoding="utf-8")
        self.assertTrue(saved.startswith(seed.rstrip()), "adding a real phase rewrote the copied instructional source")

    def test_unfilled_initial_roadmap_example_is_not_real_project_scope(self):
        source = (SOURCE/"engineer/templates/roadmap.md").read_text(encoding="utf-8")
        seed = re.search(r"```markdown\n(.*?)\n```", source, re.S)[1]
        self.assert_seed(seed)

    def test_real_authored_phase_with_example_in_body_keeps_its_human_name(self):
        self.put(".planning/ROADMAP.md", "# Roadmap: Real project\n\n### Phase 1: HTTP API & UAT\n"
                 "**Goal:** Ship the API\n\n```markdown\n### Phase 99: Example\n```\n")
        (self.root/".planning/phases/01-http-api-uat").mkdir(parents=True)
        self.assertEqual(1, self.cli("roadmap.analyze")["phase_count"])
        self.assertEqual("HTTP API & UAT", self.cli("find-phase", "01")["name"])
        added = self.cli("phase.add", "Second human Label")
        self.assertEqual("02", added["phase"])
        self.assertEqual("Second human Label", self.cli("find-phase", "02")["name"])


class PreservedProjectSettings(RuntimeCase):
    def test_canonical_local_defaults_and_native_host_boundary(self):
        self.put(".planning/config.yaml", "{}\n")
        for key, value in (("context_window", 1000000), ("worktree.root", ".worktrees"),
                           ("codebase.staleness.stack", 1), ("codebase.staleness.architecture", 15),
                           ("verification.reuse", True), ("verification.max_parallel", 4),
                           ("workflow.ui_safety_gate", True)):
            with self.subTest(key=key):
                self.assertEqual(value, self.cli("config-get", key))
        for role, model, effort in (("executor", "sonnet", "high"),
                                    ("planner", "opus", "medium"),
                                    ("phase-researcher", "opus", "high")):
            with self.subTest(role=role):
                resolved = self.cli("resolve-agent", role, "--host", "claude")
                self.assertEqual(model, resolved["model"])
                self.assertEqual(effort, resolved["effort"])
        self.assertEqual("gpt-6.1-sol", self.cli("resolve-model", "executor", "--host", "codex")["model"])

    def test_legacy_project_role_and_worktree_keys_remain_effective_without_writes(self):
        original = "agents:\n  coder:\n    model: opus\n    effort: max\nworktree:\n  root: owned-workers\n"
        path = self.put(".planning/config.yaml", original)
        resolved = self.cli("resolve-agent", "executor", "--host", "claude")
        self.assertEqual(("opus", "max"), (resolved["model"], resolved["effort"]))
        self.assertEqual("owned-workers", self.cli("config-get", "worktree.directory"))
        self.assertEqual(original, path.read_text(encoding="utf-8"))
        self.cli("config-set", "worktree.directory", "next-workers")
        saved = yaml_load(path.read_text(encoding="utf-8"))
        self.assertEqual("next-workers", saved["worktree"]["root"])
        self.assertEqual("next-workers", saved["worktree"]["directory"])

    def test_explicit_final_role_override_precedes_legacy_alias(self):
        self.put(".planning/config.yaml", "agents:\n  coder: opus\n  executor:\n    model: sonnet\n    effort: low\n")
        resolved = self.cli("resolve-agent", "coder", "--host", "claude")
        self.assertEqual(("sonnet", "low"), (resolved["model"], resolved["effort"]))


class YamlCompatibility(unittest.TestCase):
    def test_indentationless_nested_argv_sequences_and_mapping_siblings(self):
        text = """verification:
  commands:
  - - python
    - -m
    - unittest
  - - python
    - second.py
  timeout: 30
workflow:
  tdd_mode: false
"""
        data = yaml_load(text)
        self.assertEqual([["python", "-m", "unittest"], ["python", "second.py"]], data["verification"]["commands"])
        self.assertEqual(30, data["verification"]["timeout"])
        self.assertFalse(data["workflow"]["tdd_mode"])

    def test_indentationless_sequences_inside_command_mappings(self):
        text = """verification:
  commands:
  - argv:
    - python
    - check.py
    inputs:
    - src/app.py
    - tests/test_app.py
    timeout: 10
  - argv: [python, next.py]
    timeout: 20
"""
        commands = yaml_load(text)["verification"]["commands"]
        self.assertEqual(["python", "check.py"], commands[0]["argv"])
        self.assertEqual(["src/app.py", "tests/test_app.py"], commands[0]["inputs"])
        self.assertEqual(10, commands[0]["timeout"])
        self.assertEqual(["python", "next.py"], commands[1]["argv"])
        self.assertEqual(20, commands[1]["timeout"])

    def test_mapping_merge_preserves_explicit_overrides_and_independent_aliases(self):
        data = yaml_load("defaults: &base {timeout: 10, inputs: [src/app.py]}\n"
                         "first: {<<: *base, timeout: 20}\nsecond: *base\n")
        self.assertEqual(20, data["first"]["timeout"])
        self.assertEqual(10, data["second"]["timeout"])
        data["first"]["inputs"].append("tests/test_app.py")
        self.assertEqual(["src/app.py"], data["second"]["inputs"])
        self.assertEqual(["src/app.py"], data["defaults"]["inputs"])

    def test_block_anchor_merge_and_merge_sequence_precedence(self):
        data = yaml_load("""base: &base
  timeout: 10
  inputs: [src/app.py]
fallback: &fallback {timeout: 30, cwd: .}
command:
  <<: [*base, *fallback]
  timeout: 20
""")
        self.assertEqual({"timeout": 20, "inputs": ["src/app.py"], "cwd": "."}, data["command"])

    def test_merges_cannot_hide_duplicate_explicit_keys_or_unsafe_aliases(self):
        for text in ("base: &base {timeout: 1, timeout: 2}\n",
                     "base: &base {timeout: 1}\ncommand: {<<: *base, timeout: 2, timeout: 3}\n",
                     "base: &base {self: *base}\n", "base: *missing\n",
                     "base: !!python/object:module.Type {}\n"):
            with self.subTest(text=text), self.assertRaises(Failure):
                yaml_load(text)


if __name__ == "__main__":
    unittest.main()
