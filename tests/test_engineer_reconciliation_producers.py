"""Documented reconciliation calls through real dispatch and offline provider seams."""
import json
from pathlib import Path
import re
import shlex
import subprocess
import unittest
from unittest.mock import patch

try:
    from . import test_engineer_publication_boundaries as fixtures
except ImportError:
    import test_engineer_publication_boundaries as fixtures

ROOT = Path(__file__).resolve().parents[1]
README = "engineer/bin/README.md"
WORKFLOW = "engineer/workflows/secure-phase.md"
security = fixtures.security


class ReconciliationProducers(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.AnchorReconciliation(methodName="runTest")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.old, self.old_path, self.intent_path, self.state_path = self.fixture.repair_fixture()

    def call(self, path, action, token="unused"):
        text = (ROOT / path).read_text(encoding="utf-8").replace("\\\n", "")
        calls = [line.strip() for line in text.splitlines()
                 if line.strip().startswith("engineer_run query security." + action + " ") and "--reconcile-token" in line]
        self.assertEqual(1, len(calls), "Document one exact reconciliation " + action + " call in " + path)
        values = {"PHASE": "04", "ORIGINAL_ENTRIES": "original-entries.json", "ORIGINAL_TOKEN": self.old, "NEW_TOKEN": token}
        command = re.sub(r"\$\{(\w+)\}", lambda match: values[match[1]], calls[0])
        arguments = shlex.split(command)
        self.assertEqual(["engineer_run", "query", "security." + action], arguments[:3])
        return security.command(security.Args(arguments[3:]), action)

    def check_pending_sequence(self, path):
        receipts = (self.old_path.read_bytes(), self.intent_path.read_bytes())
        preview = self.call(path, "threat-preview")
        self.assertTrue(preview["ready"])
        self.assertEqual("edit", preview["operations"][0]["action"])
        self.assertEqual(self.fixture.url, preview["operations"][0]["url"])
        token = preview["preview_token"]
        result = self.call(path, "threat-publish", token)
        self.assertTrue(result["published"])
        self.assertFalse(result["ready"])
        self.assertFalse(self.call(path, "threat-publish", token)["ready"])
        self.assertEqual(1, len(self.fixture.writes))
        reservation = security.load_json(self.state_path)["risk_intents"][fixtures.entry()["key"]]
        self.assertEqual(self.old, reservation["token"])
        self.assertEqual(receipts, (self.old_path.read_bytes(), self.intent_path.read_bytes()))
        return token

    def test_readme_sequence_stays_pending_until_actual_provider_html_proves_target(self):
        token = self.check_pending_sequence(README)
        risk = fixtures.entry()
        html = '<a name="actual-provider-address"></a><h3>' + risk["heading"] + '</h3><p>Canonical risk key: ' + risk["key"] + '</p>'
        with patch.object(security, "rendered_targets", side_effect=fixtures.REAL_RENDERED_TARGETS), \
                patch.object(security.repository, "require_url", return_value=526), \
                patch.object(security.issues, "provider", return_value=subprocess.CompletedProcess([], 0, json.dumps({"body_html": html}), "")) as provider:
            result = self.call(README, "threat-publish", token)
            self.assertTrue(result["ready"])
            self.assertEqual(self.fixture.url + "#actual-provider-address", result["targets"][risk["key"]])
            self.assertTrue(all(call.args[0][0] == "api" for call in provider.call_args_list))
        self.assertEqual(1, len(self.fixture.writes))

    def test_secure_phase_sequence_preserves_pending_receipts_and_reservations(self):
        self.check_pending_sequence(WORKFLOW)

    def test_documented_preview_refuses_changed_source_or_incomplete_original(self):
        before = self.state_path.read_bytes()
        with patch.object(security, "digest", return_value="changed-original-bytes"):
            with self.assertRaises(security.Failure) as error:
                self.call(README, "threat-preview")
            self.assertEqual("security-reconciliation-source-drift", error.exception.code)
        original = security.load_json(self.intent_path)
        for state in ("attempting", "denied", "known-not-executed"):
            with self.subTest(state=state):
                security.write_json(self.intent_path, {**original, "state": state})
                with self.assertRaises(security.Failure) as error:
                    self.call(README, "threat-preview")
                self.assertEqual("security-reconciliation-invalid", error.exception.code)
        security.write_json(self.intent_path, original)
        packet = security.load_json(self.old_path)
        security.write_json(self.old_path, {**packet, "results": []})
        with self.assertRaises(security.Failure) as error:
            self.call(README, "threat-preview")
        self.assertEqual("security-reconciliation-invalid", error.exception.code)
        self.assertEqual(before, self.state_path.read_bytes())
        self.assertEqual([], self.fixture.writes)
        self.assertEqual([self.intent_path], list((self.fixture.directory / "intents").glob("*.json")))

    def test_documented_consumed_retry_never_repeats_an_unknown_edit(self):
        token = self.call(README, "threat-preview")["preview_token"]
        with patch.object(security.issues, "provider", side_effect=TimeoutError("Unknown provider response")) as provider:
            with self.assertRaises(TimeoutError):
                self.call(README, "threat-publish", token)
            with self.assertRaises(security.Failure) as error:
                self.call(README, "threat-publish", token)
            self.assertEqual("security-readback-mismatch", error.exception.code)
            self.assertEqual(1, provider.call_count)
        self.assertEqual([], self.fixture.writes)


if __name__ == "__main__":
    unittest.main()
