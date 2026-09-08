from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import config  # noqa: E402
from contracts import load_contract_registry  # noqa: E402
from domain_values import DomainException, ErrorCategory  # noqa: E402


SCHEMAS = ROOT / "schemas" / "v1"
DEFAULTS = ROOT / "docs" / "defaults"


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected an object in {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class InstalledProjectFixture:
    def __init__(self, root: Path, namespace: str = ".codex") -> None:
        self.root = root
        self.namespace = namespace
        shutil.copytree(SCHEMAS, root / namespace / "framework" / "schemas" / "v1")
        self.installation = read_json(DEFAULTS / "FRAMEWORK.json")
        self.models = read_json(DEFAULTS / "AGENT_MODELS.json")
        self.policy = read_json(DEFAULTS / "POLICY.json")
        if namespace != ".codex":
            self.installation = self._replace_namespace(self.installation, namespace)
        self.models["active_provider"] = (
            "anthropic" if namespace == ".claude" else "openai"
        )
        self._fill_policy_hints()
        self.write()

    @staticmethod
    def _replace_namespace(value: object, namespace: str) -> object:
        if isinstance(value, str):
            return value.replace(".codex", namespace)
        if isinstance(value, list):
            return [InstalledProjectFixture._replace_namespace(item, namespace) for item in value]
        if isinstance(value, dict):
            return {
                key: InstalledProjectFixture._replace_namespace(item, namespace)
                for key, item in value.items()
            }
        return value

    def _fill_policy_hints(self) -> None:
        provider = self.models["active_provider"]
        label = "OpenAI" if provider == "openai" else "Anthropic"
        provider_profiles = self.models["providers"][provider]["profiles"]
        profile_map = self.models["policy_profile_map"]
        for raw_profile in self.policy["model_profiles"]:
            catalog = provider_profiles[profile_map[raw_profile["name"]]]
            raw_profile["provider"] = label
            raw_profile["model_id"] = catalog["model_id"]
            raw_profile["capability_rank"] = catalog["capability_rank"]

    def write(self) -> None:
        write_json(self.root / self.namespace / "framework.json", self.installation)
        write_json(
            self.root / self.namespace / "project" / "agent-models.json", self.models
        )
        write_json(self.root / self.namespace / "project" / "policy.json", self.policy)


class ProjectConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = InstalledProjectFixture(self.root)

    def load(self) -> config.ProjectSettings:
        installation = config.load_installation_record(self.root)
        return config.load_project_settings(self.root, installation)

    def assert_category(self, expected: ErrorCategory, callable_) -> DomainException:
        with self.assertRaises(DomainException) as raised:
            callable_()
        self.assertEqual(raised.exception.category, expected)
        self.assertFalse(raised.exception.retryable)
        return raised.exception

    def test_loads_normalized_immutable_installation_policy_and_models(self) -> None:
        settings = self.load()

        self.assertEqual(settings.namespace, ".codex")
        self.assertEqual(settings.project_root, self.root.resolve())
        self.assertEqual(settings.installation.schema_compatibility, "1.0")
        self.assertEqual(settings.policy.max_parallel, 4)
        self.assertIsInstance(settings.policy.autonomous_actions, tuple)
        self.assertEqual(settings.models.active_provider, "openai")
        self.assertEqual(settings.model_for_role("implementer").name, "implementation")
        self.assertEqual(settings.model_for_role("implementer").reasoning_effort, "high")
        with self.assertRaises(FrozenInstanceError):
            settings.policy.max_parallel = 9

    def test_unconfigured_policy_hint_is_not_an_automatic_binding(self) -> None:
        native = self.root / ".codex" / "config.toml"
        native.write_text('model = "gpt-6-astra"\nreasoning_effort = "xhigh"\n', encoding="utf-8")
        before = native.read_bytes()

        settings = self.load()

        profile = settings.policy.model_profile("implementation")
        self.assertEqual(profile.provider, "openai")
        self.assertEqual(profile.model_id, "gpt-5.6-terra")
        self.assertFalse(profile.configured)
        self.assertIsNone(settings.configured_model("implementation"))
        self.assertEqual(native.read_bytes(), before)

    def test_configured_policy_binding_must_match_active_catalog(self) -> None:
        for profile in self.fixture.policy["model_profiles"]:
            profile["configured"] = True
        self.fixture.write()

        settings = self.load()

        binding = settings.configured_model("implementation")
        self.assertIsNotNone(binding)
        self.assertEqual(binding.provider, "openai")
        self.assertEqual(binding.model_id, "gpt-5.6-terra")

    def test_configured_policy_binding_rejects_mismatched_model(self) -> None:
        profile = self.fixture.policy["model_profiles"][0]
        profile["configured"] = True
        profile["model_id"] = "gpt-unlisted"
        self.fixture.write()

        self.assert_category(ErrorCategory.INVALID_INPUT, self.load)

    def test_action_classes_are_closed_and_do_not_grant_authority(self) -> None:
        settings = self.load()

        self.assertEqual(
            settings.policy.action_requirement("tests"),
            config.ActionRequirement.AUTONOMOUS,
        )
        self.assertEqual(
            settings.policy.action_requirement("remote_push"),
            config.ActionRequirement.APPROVAL,
        )
        self.assertEqual(
            settings.policy.action_requirement("unlisted_operation"),
            config.ActionRequirement.DENIED,
        )

    def test_rejects_sensitive_action_in_autonomous_class(self) -> None:
        self.fixture.policy["autonomous_actions"].append("remote_push")
        self.fixture.policy["approval_actions"].remove("remote_push")
        self.fixture.write()

        self.assert_category(ErrorCategory.POLICY_DENIED, self.load)

    def test_rejects_unknown_action(self) -> None:
        self.fixture.policy["autonomous_actions"].append("execute_anything")
        self.fixture.write()

        self.assert_category(ErrorCategory.INVALID_INPUT, self.load)

    def test_rejects_unknown_nested_policy_field(self) -> None:
        self.fixture.policy["model_profiles"][0]["token"] = "secret"
        self.fixture.write()

        self.assert_category(ErrorCategory.VALIDATION_FAILED, self.load)

    def test_rejects_external_grant_for_non_approval_action(self) -> None:
        self.fixture.policy["external_grants"] = [
            {
                "action": "tests",
                "resource": "repository:local",
                "authority_ref": "grant:RUN-001",
            }
        ]
        self.fixture.write()

        self.assert_category(ErrorCategory.INVALID_INPUT, self.load)

    def test_rejects_duplicate_or_incomplete_policy_profiles(self) -> None:
        duplicate = copy.deepcopy(self.fixture.policy["model_profiles"][0])
        self.fixture.policy["model_profiles"].append(duplicate)
        self.fixture.write()
        self.assert_category(ErrorCategory.INVALID_INPUT, self.load)

        self.fixture.policy["model_profiles"].pop()
        self.fixture.policy["model_profiles"].pop()
        self.fixture.write()
        self.assert_category(ErrorCategory.INVALID_INPUT, self.load)

    def test_rejects_policy_with_insufficient_review_rank(self) -> None:
        profiles = {
            profile["name"]: profile for profile in self.fixture.policy["model_profiles"]
        }
        profiles["review_high"]["capability_rank"] = profiles["implementation"][
            "capability_rank"
        ]
        self.fixture.write()

        self.assert_category(ErrorCategory.INVALID_INPUT, self.load)

    def test_rejects_provider_specific_parameter_cross_wiring(self) -> None:
        self.fixture.models["providers"]["openai"]["profiles"]["implementation"][
            "effort"
        ] = "high"
        self.fixture.write()

        self.assert_category(ErrorCategory.UNSUPPORTED_CAPABILITY, self.load)

    def test_rejects_unknown_profile_reference_from_role(self) -> None:
        self.fixture.models["roles"]["implementer"]["openai"] = "missing"
        self.fixture.write()

        self.assert_category(ErrorCategory.UNSUPPORTED_CAPABILITY, self.load)

    def test_codex_namespace_requires_openai_as_active_provider(self) -> None:
        self.fixture.models["active_provider"] = "anthropic"
        self.fixture.write()

        self.assert_category(ErrorCategory.UNSUPPORTED_CAPABILITY, self.load)

    def test_rejects_unknown_fields_through_accepted_contract_registry(self) -> None:
        self.fixture.policy["credentials"] = {"token": "do-not-read"}
        self.fixture.write()

        self.assert_category(ErrorCategory.VALIDATION_FAILED, self.load)

    def test_rejects_incompatible_or_upgrade_pending_installation(self) -> None:
        cases = (("schema_compatibility", "2.0"), ("installation_status", "upgrade_pending"))
        for field, value in cases:
            with self.subTest(field=field):
                original = self.fixture.installation[field]
                self.fixture.installation[field] = value
                self.fixture.write()
                self.assert_category(
                    ErrorCategory.UNSUPPORTED_CAPABILITY,
                    lambda: config.load_installation_record(self.root),
                )
                self.fixture.installation[field] = original

    def test_rejects_unsafe_or_overlapping_installation_roots(self) -> None:
        registry = load_contract_registry(SCHEMAS)
        cases = []
        traversal = copy.deepcopy(self.fixture.installation)
        traversal["project_owned_roots"].append(".codex/../outside/")
        cases.append(traversal)
        overlap = copy.deepcopy(self.fixture.installation)
        overlap["owned_roots"].append(".codex/project/")
        cases.append(overlap)
        for artifact in cases:
            with self.subTest(artifact=artifact):
                self.assert_category(
                    ErrorCategory.INVALID_INPUT,
                    lambda artifact=artifact: config.decode_installation_record(
                        artifact, registry
                    ),
                )

    def test_normalizes_portable_installation_paths(self) -> None:
        registry = load_contract_registry(SCHEMAS)
        artifact = InstalledProjectFixture._replace_namespace(
            self.fixture.installation, ".claude"
        )
        artifact["manifest_ref"] = artifact["manifest_ref"].replace("/", "\\")
        artifact["owned_roots"] = [value.replace("/", "\\") for value in artifact["owned_roots"]]
        artifact["project_owned_roots"] = [
            value.replace("/", "\\") for value in artifact["project_owned_roots"]
        ]

        installation = config.decode_installation_record(artifact, registry)

        self.assertEqual(installation.namespace, ".claude")
        self.assertTrue(all("\\" not in value for value in installation.owned_roots))
        self.assertEqual(installation.manifest_ref, ".claude/framework/manifest.json")

    def test_installation_argument_must_match_tracked_record(self) -> None:
        installation = config.load_installation_record(self.root)
        stale = config.InstallationRecord(
            schema_version=installation.schema_version,
            framework_version="0.2.1",
            schema_compatibility=installation.schema_compatibility,
            installation_status=installation.installation_status,
            manifest_ref=installation.manifest_ref,
            owned_roots=installation.owned_roots,
            project_owned_roots=installation.project_owned_roots,
        )

        self.assert_category(
            ErrorCategory.STATE_CONFLICT,
            lambda: config.load_project_settings(self.root, stale),
        )

    def test_ignores_native_provider_namespace_but_rejects_two_installations(self) -> None:
        native = self.root / ".claude" / "settings.json"
        write_json(native, {"permissions": {"allow": ["read"]}})
        self.assertEqual(config.load_installation_record(self.root).namespace, ".codex")

        write_json(self.root / ".claude" / "framework.json", self.fixture.installation)
        self.assert_category(
            ErrorCategory.INVALID_INPUT,
            lambda: config.load_installation_record(self.root),
        )

    def test_source_foundation_uses_repository_schema_root(self) -> None:
        source_root = self.root / "source"
        shutil.copytree(SCHEMAS, source_root / "schemas" / "v1")
        source_fixture = InstalledProjectFixture(source_root, namespace=".ai")
        shutil.rmtree(source_root / ".ai" / "framework" / "schemas")
        source_fixture.installation["installation_status"] = "source_foundation"
        source_fixture.installation["manifest_ref"] = None
        source_fixture.write()

        settings = config.load_project_settings(
            source_root, config.load_installation_record(source_root)
        )

        self.assertEqual(settings.namespace, ".ai")

    def test_run_precedence_is_defaults_then_project_then_restrictive_override(self) -> None:
        self.fixture.policy["max_parallel"] = 3
        self.fixture.policy["max_review_cycles"] = 2
        self.fixture.policy["max_rewrites"] = 2
        self.fixture.policy["max_agent_invocations"] = 40
        self.fixture.write()
        settings = self.load()

        project = settings.resolve_run()
        narrowed = settings.resolve_run(
            config.RunOverrides(
                max_parallel=2,
                max_review_cycles=1,
                max_rewrites=1,
                max_agent_invocations=20,
                required_sandbox=True,
            )
        )

        self.assertEqual(project.max_parallel, 3)
        self.assertEqual(project.max_agent_invocations, 40)
        self.assertEqual(narrowed.max_parallel, 2)
        self.assertEqual(narrowed.max_review_cycles, 1)
        self.assertTrue(narrowed.required_sandbox)

    def test_run_can_explicitly_disable_new_agent_invocations(self) -> None:
        settings = self.load()

        stopped = settings.resolve_run(
            config.RunOverrides(max_agent_invocations=0)
        )

        self.assertEqual(stopped.max_agent_invocations, 0)
        self.assertEqual(config.decode_run_settings(stopped.to_payload()), stopped)

    def test_run_override_cannot_broaden_policy_or_disable_sandbox(self) -> None:
        settings = self.load()
        self.assert_category(
            ErrorCategory.POLICY_DENIED,
            lambda: settings.resolve_run(config.RunOverrides(max_parallel=5)),
        )
        self.fixture.policy["required_sandbox"] = True
        self.fixture.write()
        settings = self.load()
        self.assert_category(
            ErrorCategory.POLICY_DENIED,
            lambda: settings.resolve_run(
                config.RunOverrides(required_sandbox=False)
            ),
        )

    def test_saved_run_payload_round_trips_and_wins_on_resume(self) -> None:
        settings = self.load()
        original = settings.resolve_run(config.RunOverrides(max_parallel=1))
        payload = original.to_payload()
        effective = settings.effective_policy(
            config.RunOverrides(max_parallel=1)
        )
        self.assertEqual(effective.max_parallel, 1)
        self.assertEqual(settings.policy.max_parallel, 4)
        load_contract_registry(SCHEMAS).validate(effective.to_wire())

        self.fixture.policy["max_parallel"] = 2
        self.fixture.write()
        changed_settings = self.load()
        hydrated = config.decode_run_settings(payload)
        resumed = changed_settings.resolve_run(saved=hydrated)

        self.assertEqual(resumed, original)
        self.assertEqual(resumed.max_parallel, 1)
        self.assertIsNot(resumed, changed_settings.resolve_run())

    def test_saved_run_payload_is_closed_and_resume_rejects_new_overrides(self) -> None:
        payload = self.load().resolve_run().to_payload()
        payload["provider_token"] = "secret"
        self.assert_category(
            ErrorCategory.INVALID_INPUT,
            lambda: config.decode_run_settings(payload),
        )
        saved = self.load().resolve_run()
        self.assert_category(
            ErrorCategory.INVALID_INPUT,
            lambda: self.load().resolve_run(
                config.RunOverrides(max_parallel=1), saved=saved
            ),
        )

    def test_loading_is_read_only(self) -> None:
        tracked = [
            self.root / ".codex" / "framework.json",
            self.root / ".codex" / "project" / "policy.json",
            self.root / ".codex" / "project" / "agent-models.json",
        ]
        before = {path: path.read_bytes() for path in tracked}

        self.load()

        self.assertEqual({path: path.read_bytes() for path in tracked}, before)


if __name__ == "__main__":
    unittest.main()
