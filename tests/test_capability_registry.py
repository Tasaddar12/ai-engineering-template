"""Behavior contracts for the generated capability registry data module.

Ported subset of upstream tests/capability-registry.test.cjs (the cases that read the
live generated registry: requiresClosure, byLoopPoint points, config key ownership,
the planning feature capabilities). The generator/validator cases are not ported
because scripts/gen-capability-registry.cjs is not part of this port.
"""
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

SOURCE = Path(__file__).resolve().parents[1]
LIB = SOURCE/"engineer/bin/lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package (`lib` also names .ai/runtime/lib)."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib."+name)


registry = _load("capability_registry")


class RegistryShape(unittest.TestCase):
    def test_version_and_export_keys(self):
        self.assertEqual("1", registry.VERSION)
        self.assertEqual(
            {"version", "capabilities", "bySkill", "byAgent", "byLoopPoint", "configKeys", "configSchema",
             "runtimes", "commandFamilies", "capabilityClusters", "profileMembership"},
            set(registry.REGISTRY))
        self.assertIs(registry.CAPABILITIES, registry.REGISTRY["capabilities"])
        self.assertIs(registry.RUNTIMES, registry.REGISTRY["runtimes"])

    def test_table_cardinalities_match_the_pinned_upstream_module(self):
        counts = {name: len(value) for name, value in registry.REGISTRY.items() if name != "version"}
        self.assertEqual(
            {"capabilities": 45, "bySkill": 10, "byAgent": 15, "byLoopPoint": 12, "configKeys": 86,
             "configSchema": 86, "runtimes": 19, "commandFamilies": 14, "capabilityClusters": 8,
             "profileMembership": 8},
            counts)

    def test_every_capability_row_is_self_consistent(self):
        for capability_id, row in registry.CAPABILITIES.items():
            with self.subTest(capability=capability_id):
                self.assertEqual(capability_id, row["id"])
                self.assertIn(row["role"], ("feature", "runtime", "reviewer"))
                self.assertIsInstance(row["requires"], list)

    def test_roles_partition_capabilities_and_runtimes(self):
        runtime_ids = {key for key, row in registry.CAPABILITIES.items() if row["role"] == "runtime"}
        self.assertEqual(runtime_ids, set(registry.RUNTIMES))
        for runtime_id, row in registry.RUNTIMES.items():
            self.assertEqual(runtime_id, row["id"])
            self.assertIn("configHome", row["runtime"])

    def test_json_round_trip_is_lossless(self):
        self.assertEqual(registry.RUNTIMES, json.loads(json.dumps(registry.RUNTIMES)))


class LoopPoints(unittest.TestCase):
    def test_by_loop_point_contains_all_twelve_points(self):
        expected = ["discuss:pre", "discuss:post", "plan:pre", "plan:post", "execute:pre", "execute:wave:pre",
                    "execute:wave:post", "execute:post", "verify:pre", "verify:post", "ship:pre", "ship:post"]
        self.assertEqual(sorted(expected), sorted(registry.BY_LOOP_POINT))
        for point in expected:
            self.assertEqual({"steps", "contributions", "gates"}, set(registry.BY_LOOP_POINT[point]), point)

    def test_planning_feature_capabilities_register_plan_pre_hooks(self):
        point = registry.BY_LOOP_POINT["plan:pre"]
        hooks = point["steps"] + point["contributions"] + point["gates"]
        for capability_id in ("research", "ai-integration", "pattern-mapper"):
            self.assertTrue(any(hook["capId"] == capability_id for hook in hooks), capability_id)


class PlanningFeatures(unittest.TestCase):
    def test_declares_research_ai_integration_and_pattern_mapper(self):
        for capability_id in ("research", "ai-integration", "pattern-mapper"):
            self.assertIn(capability_id, registry.CAPABILITIES)
            self.assertEqual("feature", registry.CAPABILITIES[capability_id]["role"])

    def test_config_keys_are_owned(self):
        self.assertEqual("research", registry.CONFIG_KEYS["workflow.research"])
        self.assertEqual("ai-integration", registry.CONFIG_KEYS["workflow.ai_integration_phase"])
        self.assertEqual("pattern-mapper", registry.CONFIG_KEYS["workflow.pattern_mapper"])

    def test_config_schema_defaults(self):
        for key, owner in registry.CONFIG_KEYS.items():
            self.assertEqual(owner, registry.CONFIG_SCHEMA[key]["owner"], key)
        self.assertEqual("ui", registry.CONFIG_SCHEMA["workflow.ui_safety_gate"]["owner"])
        self.assertEqual("boolean", registry.CONFIG_SCHEMA["workflow.ui_safety_gate"]["type"])
        self.assertIs(True, registry.CONFIG_SCHEMA["workflow.ui_safety_gate"]["default"])

    def test_skill_and_agent_indexes_point_at_declared_capabilities(self):
        for skill, owner in registry.BY_SKILL.items():
            self.assertIn(owner, registry.CAPABILITIES)
            self.assertIn(skill, registry.CAPABILITIES[owner]["skills"])
        for owner in registry.BY_AGENT.values():
            self.assertTrue(owner)


class RequiresClosure(unittest.TestCase):
    def test_capability_without_requires_has_empty_closure(self):
        self.assertEqual(set(), registry.requires_closure("ui"))

    def test_unknown_id_has_empty_closure(self):
        self.assertEqual(set(), registry.requires_closure("no-such-capability"))

    def test_direct_requirement(self):
        self.assertEqual({"research"}, registry.requires_closure("pattern-mapper"))

    def test_closure_matches_the_declared_requires_for_every_capability(self):
        for capability_id, row in registry.CAPABILITIES.items():
            closure = registry.requires_closure(capability_id)
            self.assertTrue(set(row["requires"]) <= closure, capability_id)
            for required in row["requires"]:
                self.assertTrue(registry.requires_closure(required) <= closure, capability_id)

    def test_transitive_closure_with_a_patched_graph(self):
        original = dict(registry._REQUIRES_GRAPH)
        self.addCleanup(lambda: (registry._REQUIRES_GRAPH.clear(), registry._REQUIRES_GRAPH.update(original)))
        registry._REQUIRES_GRAPH.update({"cap-a": ["cap-b"], "cap-b": ["cap-c"], "cap-c": []})
        self.assertEqual({"cap-b", "cap-c"}, registry.requires_closure("cap-a"))

    def test_cycles_terminate(self):
        original = dict(registry._REQUIRES_GRAPH)
        self.addCleanup(lambda: (registry._REQUIRES_GRAPH.clear(), registry._REQUIRES_GRAPH.update(original)))
        registry._REQUIRES_GRAPH.update({"cap-x": ["cap-y"], "cap-y": ["cap-x"]})
        self.assertEqual({"cap-x", "cap-y"}, registry.requires_closure("cap-x"))


class RuntimeDescriptors(unittest.TestCase):
    def test_runtime_ids_are_the_upstream_nineteen(self):
        self.assertEqual(
            sorted(["antigravity", "augment", "claude", "cline", "codebuddy", "codex", "copilot", "cursor", "hermes",
                    "kilo", "kimi", "kimi-code", "opencode", "pi", "qwen", "trae", "vscode", "windsurf", "zcode"]),
            sorted(registry.RUNTIMES))

    def test_config_home_kinds_are_closed(self):
        kinds = {row["runtime"]["configHome"]["kind"] for row in registry.RUNTIMES.values()}
        self.assertTrue(kinds <= {"dot-home", "dot-home-nested", "xdg", "generic-agents-root", "none"}, kinds)

    def test_reference_runtime_descriptor(self):
        claude = registry.RUNTIMES["claude"]["runtime"]
        self.assertEqual({"kind": "dot-home", "name": ".claude", "env": ["CLAUDE_CONFIG_DIR"]}, claude["configHome"])
        self.assertEqual(".claude", claude["localConfigDir"])
        self.assertEqual("slash-hyphen", claude["commandStyle"])
        self.assertEqual("shell-var", registry.RUNTIMES["codex"]["runtime"]["commandStyle"])

    def test_antigravity_declares_its_project_instruction_file(self):
        host = registry.RUNTIMES["antigravity"]["runtime"]["hostBehaviors"]
        self.assertEqual("GEMINI.md", host["projectInstructionFile"])


if __name__ == "__main__":
    unittest.main()
