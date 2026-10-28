"""Behavior contracts for runtime name policy (port of upstream tests/runtime-name-policy.test.cjs).

The getGlobalConfigDir cases of the upstream file belong to runtime-homes, which is not
part of this module; the three accessors that live here carry the retired/unknown-id
assertions.
"""
import importlib
import importlib.util
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


policy = _load("runtime_name_policy")
registry = _load("capability_registry")

RETIRED = "gem" + "ini"
ACCESSORS = {
    "get_runtime_label": policy.get_runtime_label,
    "get_project_instruction_file": policy.get_project_instruction_file,
    "get_global_config_home_fragment": policy.get_global_config_home_fragment,
    "get_dir_name": policy.get_dir_name,
}


class CanonicalIds(unittest.TestCase):
    def test_kimi_without_extra_aliases(self):
        self.assertEqual("kimi", policy.canonicalize_runtime_name("kimi"))
        self.assertEqual("kimi", policy.canonicalize_runtime_name(" KIMI "))
        self.assertEqual("kimi", policy.resolve_runtime_name_from_candidates("", None, "kimi"))
        self.assertIsNone(policy.canonicalize_runtime_name("kimi-cli"))

    def test_devin_desktop_is_windsurf(self):
        self.assertEqual("windsurf", policy.canonicalize_runtime_name("devin-desktop"))
        self.assertEqual("windsurf", policy.canonicalize_runtime_name("DEVIN-DESKTOP"))
        self.assertEqual("windsurf", policy.resolve_runtime_name_from_candidates("devin-desktop"))

    def test_token_normalization(self):
        self.assertEqual("codex", policy.canonicalize_runtime_name("Codex_Desktop"))
        self.assertEqual("codex", policy.canonicalize_runtime_name("codex desktop"))
        self.assertEqual("kimi-code", policy.canonicalize_runtime_name("kimi_code"))
        self.assertEqual("claude", policy.canonicalize_runtime_name("claude-code"))

    def test_non_string_is_none(self):
        for value in (None, 3, [], {}, True):
            self.assertIsNone(policy.canonicalize_runtime_name(value))

    def test_every_alias_row_round_trips(self):
        for canonical, aliases in policy._FALLBACK_ALIASES.items():
            for alias in (canonical, *aliases):
                self.assertEqual(canonical, policy.canonicalize_runtime_name(alias), alias)

    def test_fallback_windsurf_aliases_match_manifest(self):
        self.assertEqual(["windsurf", "windsurf-cli", "windsurf-next", "devin-desktop"],
                         policy._FALLBACK_ALIASES["windsurf"])

    def test_resolve_candidates_precedence(self):
        resolve = policy.resolve_runtime_name_from_candidates
        self.assertEqual("codex", resolve("codex-cli", "claude"))
        self.assertEqual("claude", resolve(None, 5, "   ", "Claude-Code"))
        self.assertEqual("future-runtime", resolve("Future_Runtime"))
        self.assertIsNone(resolve())
        self.assertIsNone(resolve("", "  ", None))


class ProjectInstructionFile(unittest.TestCase):
    def test_mapping_table(self):
        get = policy.get_project_instruction_file
        self.assertEqual(".claude/CLAUDE.md", get("claude"))
        for runtime in ("codex", "opencode", "kilo", "kimi"):
            self.assertEqual("AGENTS.md", get(runtime), runtime)
        self.assertEqual(".github/copilot-instructions.md", get("copilot"))
        self.assertEqual("GEMINI.md", get("antigravity"))

    def test_unknown_and_empty_default_to_agents_md(self):
        for value in ("future-runtime-xyz", "", None):
            self.assertEqual("AGENTS.md", policy.get_project_instruction_file(value))
        self.assertEqual("AGENTS.md", policy.get_project_instruction_file(42))

    def test_aliases_normalize_first(self):
        get = policy.get_project_instruction_file
        self.assertEqual("AGENTS.md", get("codex-cli"))
        self.assertEqual("AGENTS.md", get("opencode-cli"))
        self.assertEqual(".github/copilot-instructions.md", get("github-copilot"))
        self.assertEqual(".claude/CLAUDE.md", get("Claude-Code"))
        self.assertEqual("GEMINI.md", get("antigravity-cli"))

    def test_retired_ids_are_refused(self):
        with self.assertRaisesRegex(policy.RetiredRuntimeError, "retired by #1928"):
            policy.get_project_instruction_file(RETIRED)
        with self.assertRaisesRegex(policy.RetiredRuntimeError, "retired by #1928"):
            policy.get_project_instruction_file(RETIRED + "-cli")


class RetiredIds(unittest.TestCase):
    def test_every_accessor_throws_for_a_retired_id(self):
        for label, call in ACCESSORS.items():
            with self.subTest(accessor=label), self.assertRaises(policy.RetiredRuntimeError):
                call(RETIRED)

    def test_message_names_id_successor_and_issue(self):
        with self.assertRaises(policy.RetiredRuntimeError) as caught:
            policy.get_runtime_label(RETIRED)
        message = str(caught.exception)
        self.assertRegex(message, RETIRED)
        self.assertRegex(message, "Antigravity")
        self.assertRegex(message, "#1928")
        self.assertRegex(message, "2026-06-18")

    def test_error_has_machine_checkable_discriminators(self):
        with self.assertRaises(policy.RetiredRuntimeError) as caught:
            policy.get_runtime_label(RETIRED)
        self.assertEqual("GSD_RETIRED_RUNTIME", caught.exception.code)
        self.assertEqual("RetiredRuntimeError", caught.exception.name)
        self.assertEqual(RETIRED, caught.exception.runtime_id)
        self.assertIsInstance(caught.exception, Exception)

    def test_case_and_alias_spellings_all_throw(self):
        spellings = [RETIRED, RETIRED + "-cli", RETIRED.upper(), "  " + RETIRED + "  ", RETIRED.capitalize(),
                     RETIRED + "_cli", RETIRED + ".cli", RETIRED + "cli", "ｇｅｍｉｎｉ"]
        for spelling in spellings:
            for label, call in ACCESSORS.items():
                with self.subTest(spelling=spelling, accessor=label), self.assertRaises(policy.RetiredRuntimeError) as caught:
                    call(spelling)
                self.assertEqual("GSD_RETIRED_RUNTIME", caught.exception.code)

    def test_membership_not_substring_match(self):
        not_retired = [RETIRED + "-2.5-pro", RETIRED + "-3.1-pro-preview", RETIRED + "-2.5-flash-lite", RETIRED + "x",
                       RETIRED[:-1], "__proto__", "constructor", "  CONSTRUCTOR  "]
        for value in not_retired:
            with self.subTest(value=value):
                self.assertFalse(policy.is_retired_runtime_id(value))
                for label, call in ACCESSORS.items():
                    try:
                        call(value)
                    except policy.RetiredRuntimeError:
                        self.fail(f"{label} raised the retirement error for {value!r}")
                    except policy.UnknownRuntimeError as exc:
                        self.assertEqual("GSD_UNKNOWN_RUNTIME", exc.code)

    def test_retired_set_is_well_formed(self):
        self.assertIsInstance(policy.RETIRED_RUNTIME_IDS, frozenset)
        self.assertIn(RETIRED, policy.RETIRED_RUNTIME_IDS)
        self.assertTrue(all(item == item.lower() for item in policy.RETIRED_RUNTIME_IDS))

    def test_is_retired_runtime_id(self):
        self.assertTrue(policy.is_retired_runtime_id(RETIRED))
        self.assertTrue(policy.is_retired_runtime_id("  " + RETIRED.upper() + "  "))
        self.assertFalse(policy.is_retired_runtime_id(RETIRED + "-2.5-pro"))
        for value in ("", None, "__proto__", "constructor", "hasOwnProperty", 3):
            self.assertFalse(policy.is_retired_runtime_id(value), value)

    def test_predicate_and_assertion_agree(self):
        for value in (RETIRED, "x", "", None, RETIRED + "-cli", "__proto__", 7):
            if policy.is_retired_runtime_id(value):
                with self.assertRaises(policy.RetiredRuntimeError):
                    policy.assert_not_retired_runtime(value)
            else:
                self.assertIsNone(policy.assert_not_retired_runtime(value))


class UnknownIds(unittest.TestCase):
    def test_unknown_id_refuses_on_label_fragment_and_dir_accessors(self):
        for call in (policy.get_runtime_label, policy.get_global_config_home_fragment, policy.get_dir_name):
            with self.assertRaises(policy.UnknownRuntimeError) as caught:
                call("notarealruntime")
            self.assertEqual("GSD_UNKNOWN_RUNTIME", caught.exception.code)
            self.assertEqual("UnknownRuntimeError", caught.exception.name)
            self.assertEqual("notarealruntime", caught.exception.runtime_id)
            self.assertIn("not registered in the capability registry", str(caught.exception))

    def test_unknown_id_keeps_cross_agent_default(self):
        self.assertEqual("AGENTS.md", policy.get_project_instruction_file("notarealruntime"))

    def test_empty_id_keeps_documented_branch(self):
        self.assertEqual("Claude Code", policy.get_runtime_label(""))
        self.assertEqual("AGENTS.md", policy.get_project_instruction_file(""))
        self.assertEqual("'.claude'", policy.get_global_config_home_fragment(""))
        self.assertEqual(".claude", policy.get_dir_name(""))

    def test_assert_known_runtime(self):
        self.assertIsNone(policy.assert_known_runtime(""))
        self.assertIsNone(policy.assert_known_runtime(None))
        self.assertIsNone(policy.assert_known_runtime(5))
        self.assertIsNone(policy.assert_known_runtime("claude"))
        self.assertIsNone(policy.assert_known_runtime("grok"))
        with self.assertRaises(policy.UnknownRuntimeError):
            policy.assert_known_runtime("nope")
        with self.assertRaises(policy.RetiredRuntimeError):
            policy.assert_known_runtime(RETIRED)

    def test_assert_known_runtime_degrades_when_registry_fails_to_load(self):
        original = policy._load_registry_runtimes
        policy._load_registry_runtimes = lambda: None
        self.addCleanup(setattr, policy, "_load_registry_runtimes", original)
        self.assertIsNone(policy.assert_known_runtime("nope"))
        with self.assertRaises(policy.RetiredRuntimeError):
            policy.assert_known_runtime(RETIRED)

    def test_is_known_runtime_id(self):
        for value in ("claude", "codex", "pi", "vscode", "grok"):
            self.assertTrue(policy.is_known_runtime_id(value), value)
        for value in ("", None, 3, "nope", "__proto__", "constructor", "Claude", " claude"):
            self.assertFalse(policy.is_known_runtime_id(value), value)


class CanonicalRuntimesDoNotRegress(unittest.TestCase):
    def test_a_spread_of_canonical_ids_resolve_everywhere(self):
        for runtime in ("claude", "codex", "opencode", "antigravity", "copilot", "cursor", "kimi", "pi"):
            for label, call in ACCESSORS.items():
                try:
                    call(runtime)
                except Exception as exc:  # noqa: BLE001
                    self.fail(f"{label}({runtime!r}) raised {exc!r}")

    def test_fragments_are_byte_stable(self):
        fragment = policy.get_global_config_home_fragment
        self.assertEqual("'.claude'", fragment("claude"))
        self.assertEqual("'.codex'", fragment("codex"))
        self.assertEqual("'.config', 'opencode'", fragment("opencode"))
        self.assertEqual("'.pi', 'agent'", fragment("pi"))
        self.assertEqual("'.config', 'agents'", fragment("kimi"))
        self.assertEqual("'.claude'", fragment("antigravity"))

    def test_labels(self):
        label = policy.get_runtime_label
        self.assertEqual("Claude Code", label("claude"))
        self.assertEqual("Kimi CLI", label("kimi"))
        self.assertEqual("Cline", label("cline"))
        self.assertEqual("VS Code", label("vscode"))
        self.assertEqual("pi", label("pi"))
        self.assertEqual("Qwen Code", label("qwen"))

    def test_label_table_ids_equal_registry_runtime_ids(self):
        self.assertEqual(set(registry.RUNTIMES), set(policy._RUNTIME_LABELS))

    def test_fragment_table_ids_are_registered(self):
        self.assertTrue(set(policy._GLOBAL_CONFIG_HOME_FRAGMENTS) <= set(registry.RUNTIMES))

    def test_alias_canonical_ids_are_registered_runtimes(self):
        self.assertEqual(set(registry.RUNTIMES) - {"vscode"} - {"pi", "zcode"}, set(policy._FALLBACK_ALIASES))


class DirName(unittest.TestCase):
    def test_local_config_dirs_come_from_descriptors(self):
        self.assertEqual(".claude", policy.get_dir_name("claude"))
        self.assertEqual(".cursor", policy.get_dir_name("cursor"))
        self.assertEqual(".windsurf", policy.get_dir_name("windsurf"))
        self.assertEqual(".agents", policy.get_dir_name("antigravity"))

    def test_config_home_none_returns_sentinel(self):
        self.assertEqual("(no-local-config-dir)", policy.NO_LOCAL_CONFIG_DIR_SENTINEL)
        entry = registry.RUNTIMES["vscode"]["runtime"]
        if entry.get("localConfigDir"):
            self.assertEqual(entry["localConfigDir"], policy.get_dir_name("vscode"))
        else:
            self.assertEqual(policy.NO_LOCAL_CONFIG_DIR_SENTINEL, policy.get_dir_name("vscode"))

    def test_none_kind_without_local_dir_yields_sentinel(self):
        saved = registry.RUNTIMES["vscode"]["runtime"].pop("localConfigDir", None)
        kind = registry.RUNTIMES["vscode"]["runtime"]["configHome"]["kind"]
        self.addCleanup(lambda: saved is None or registry.RUNTIMES["vscode"]["runtime"].__setitem__("localConfigDir", saved))
        self.assertEqual("none", kind)
        self.assertEqual(policy.NO_LOCAL_CONFIG_DIR_SENTINEL, policy.get_dir_name("vscode"))

    def test_grok_is_known_but_has_no_descriptor(self):
        self.assertEqual(".claude", policy.get_dir_name("grok"))


class HostBehaviors(unittest.TestCase):
    def test_absent_ids_yield_empty(self):
        for value in ("", None, 3):
            self.assertEqual({}, policy.host_behaviors_for(value))

    def test_registered_id_yields_descriptor_bag(self):
        bag = policy.host_behaviors_for("antigravity")
        self.assertEqual("GEMINI.md", bag["projectInstructionFile"])
        self.assertEqual("antigravity", bag["globalDirResolver"])

    def test_unregistered_retired_and_prototype_ids_yield_empty(self):
        for value in ("grok", "notarealruntime", RETIRED, "__proto__", "constructor"):
            self.assertEqual({}, policy.host_behaviors_for(value), value)

    def test_registry_load_failure_uses_the_floor(self):
        floor = policy.host_behaviors_for("claude", None)
        self.assertEqual("claude", floor["permissionsSchema"])
        self.assertEqual({"globalDirResolver": "antigravity"}, dict(policy.host_behaviors_for("antigravity", None)))
        self.assertEqual({}, policy.host_behaviors_for("cursor", None))

    def test_injected_registry(self):
        registry_stub = {"runtimes": {"x": {"runtime": {"hostBehaviors": {"a": 1}}}, "claude": {"runtime": {}}, "y": {}}}
        self.assertEqual({"a": 1}, policy.host_behaviors_for("x", registry_stub))
        self.assertEqual(policy.FALLBACK_HOST_BEHAVIORS["claude"], policy.host_behaviors_for("claude", registry_stub))
        self.assertEqual({}, policy.host_behaviors_for("y", registry_stub))
        self.assertEqual({}, policy.host_behaviors_for("z", registry_stub))
        self.assertEqual({}, policy.host_behaviors_for("x", {"runtimes": {}}))
        self.assertEqual(policy.FALLBACK_HOST_BEHAVIORS["claude"], policy.host_behaviors_for("claude", {}))

    def test_fallback_table_is_read_only(self):
        with self.assertRaises(TypeError):
            policy.FALLBACK_HOST_BEHAVIORS["claude"]["x"] = 1
        with self.assertRaises(TypeError):
            policy.LEGACY_NON_REGISTRY_RUNTIME_HOMES["grok"]["env"] = "X"


class LegacyHomesAndFlags(unittest.TestCase):
    def test_legacy_homes(self):
        self.assertEqual({"grok"}, set(policy.LEGACY_NON_REGISTRY_RUNTIME_IDS))
        grok = policy.LEGACY_NON_REGISTRY_RUNTIME_HOMES["grok"]
        self.assertEqual("GROK_AGENTS_HOME", grok["env"])
        self.assertEqual((".agents",), tuple(grok["dir"]))

    def test_runtime_flags(self):
        flags = policy.runtime_flags("kimi-code")
        self.assertTrue(flags["isKimiCode"])
        self.assertFalse(flags["isKimi"])
        self.assertEqual(17, len(flags))
        self.assertEqual(1, sum(policy.runtime_flags("codex").values()))
        self.assertEqual(0, sum(policy.runtime_flags("claude").values()))
        self.assertEqual(0, sum(policy.runtime_flags("").values()))
        with self.assertRaises(TypeError):
            flags["isCodex"] = True

    def test_flag_names(self):
        self.assertEqual(
            ["isOpencode", "isKilo", "isCodex", "isCopilot", "isAntigravity", "isCursor", "isWindsurf", "isAugment",
             "isTrae", "isQwen", "isHermes", "isCodebuddy", "isCline", "isKimi", "isKimiCode", "isZcode", "isPi"],
            list(policy.runtime_flags("x")))


if __name__ == "__main__":
    unittest.main()
