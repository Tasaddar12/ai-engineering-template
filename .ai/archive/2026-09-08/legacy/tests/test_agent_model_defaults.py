"""Check installed model recommendations, overrides, and invalid routing."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import install
import validate_foundation


class AgentModelDefaultsTests(unittest.TestCase):
    def test_each_provider_installs_complete_routing_and_unverified_gate_defaults(self) -> None:
        roles = {path.stem for path in (ROOT / "docs/agents").glob("*.md") if path.stem != "README"}
        with tempfile.TemporaryDirectory() as temporary:
            for assistant, namespace, provider, provider_name in (
                ("codex", ".codex", "openai", "OpenAI"),
                ("chatgpt", ".codex", "openai", "OpenAI"),
                ("claude", ".claude", "anthropic", "Anthropic"),
            ):
                with self.subTest(assistant=assistant):
                    target = Path(temporary) / assistant
                    install.install(str(target), assistant)
                    project = target / namespace / "project"
                    models = json.loads((project / "agent-models.json").read_text(encoding="utf-8"))
                    policy = json.loads((project / "policy.json").read_text(encoding="utf-8"))
                    self.assertEqual(models["active_provider"], provider)
                    self.assertEqual(set(models["roles"]), roles)
                    for key in ("openai", "anthropic"):
                        profiles = models["providers"][key]["profiles"]
                        for role in roles:
                            self.assertIn(models["roles"][role][key], profiles)
                        self.assertGreater(profiles["review_high"]["capability_rank"], profiles["implementation"]["capability_rank"])
                        self.assertGreater(profiles["planning"]["capability_rank"], profiles["research"]["capability_rank"])
                    for gate in policy["model_profiles"]:
                        profile = models["providers"][provider]["profiles"][models["policy_profile_map"][gate["name"]]]
                        self.assertEqual(gate["provider"], provider_name)
                        self.assertEqual(gate["model_id"], profile["model_id"])
                        self.assertEqual(gate["capability_rank"], profile["capability_rank"])
                        self.assertFalse(gate["configured"])
                    self.assertEqual(validate_foundation.validate(target)["plans"], 0)

    def test_reinstallation_preserves_custom_role_selection_and_verified_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            install.install(str(target), "codex")
            models_path = target / ".codex/project/agent-models.json"
            policy_path = target / ".codex/project/policy.json"
            models = json.loads(models_path.read_text(encoding="utf-8"))
            models["roles"]["implementer"]["openai"] = "implementation_escalated"
            models_path.write_text(json.dumps(models, indent=2) + "\n", encoding="utf-8")
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            gate = next(item for item in policy["model_profiles"] if item["name"] == "implementation")
            gate.update(model_id="gpt-5.6-sol", capability_rank=3, configured=True)
            policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
            before = (models_path.read_bytes(), policy_path.read_bytes())
            install.install(str(target), "chatgpt")
            self.assertEqual((models_path.read_bytes(), policy_path.read_bytes()), before)
            validate_foundation.validate(target)

    def test_validator_rejects_incomplete_ambiguous_or_unsafe_model_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            install.install(str(target), "codex")
            path = target / ".codex/project/agent-models.json"
            baseline = json.loads(path.read_text(encoding="utf-8"))
            corruptions = []
            bad = copy.deepcopy(baseline)
            del bad["roles"]["planner"]
            corruptions.append(("missing role", bad))
            bad = copy.deepcopy(baseline)
            bad["roles"]["researcher"]["anthropic"] = "missing-profile"
            corruptions.append(("unresolved inactive-provider profile", bad))
            bad = copy.deepcopy(baseline)
            bad["providers"]["openai"]["profiles"]["review_high"]["capability_rank"] = 2
            corruptions.append(("review downgrade", bad))
            bad = copy.deepcopy(baseline)
            bad["providers"]["anthropic"]["profiles"]["research"]["reasoning_effort"] = "medium"
            corruptions.append(("wrong provider effort", bad))
            bad = copy.deepcopy(baseline)
            bad["active_provider"] = "anthropic"
            corruptions.append(("namespace-provider mismatch", bad))
            bad = copy.deepcopy(baseline)
            bad["policy_profile_map"]["planning"] = "missing-profile"
            corruptions.append(("unresolved gate profile", bad))
            for label, data in corruptions:
                with self.subTest(label=label):
                    path.write_text(json.dumps(data) + "\n", encoding="utf-8")
                    with self.assertRaises(validate_foundation.ValidationFailure):
                        validate_foundation.validate(target)


if __name__ == "__main__":
    unittest.main()
