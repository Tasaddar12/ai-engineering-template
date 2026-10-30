"""Behavioral checks for retained learning, prohibition and native review routes."""
import json
from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class RetainedRuntime(RuntimeCase):
    def test_retained_global_learnings_copy_query_and_refresh(self):
        self.init_records()
        store = self.root / "global-knowledge"
        self.env["ENGINEER_KNOWLEDGE_DIR"] = str(store)
        artifact = self.put(".planning/phases/01-fixture/01-LEARNINGS.md",
                            "---\nproject: Source Project\ntags: [worktrees]\n---\n# Lessons\nKeep fixes isolated.\n")
        disabled = self.cli("learnings.copy", "--phase", "1")
        self.assertFalse(disabled["copied"])
        self.assertFalse(store.exists())
        self.cli("config-set", "features.global_learnings", "true")
        self.assertEqual("debug-session-manager", self.cli("resolve-agent", "debug-session-manager")["name"])
        copied = self.cli("learnings.copy", "--phase", "1")
        self.assertTrue(copied["globalCopy"])
        destination = store / (Path(copied["paths"][0]).name)
        self.assertEqual(artifact.read_bytes(), destination.read_bytes())
        found = self.cli("learnings.query", "--tag", "worktrees", "--limit", "1")["items"]
        self.assertEqual("Source Project", found[0]["project"])
        self.assertIn("Keep fixes isolated.", found[0]["text"])
        self.assertEqual([], self.cli("learnings.query", "--tag", "unrelated")["items"])
        artifact.write_text(artifact.read_text() + "Use a fresh branch.\n", encoding="utf-8")
        self.assertEqual(copied["paths"], self.cli("learnings.copy", "--phase", "1")["paths"])
        self.assertEqual(1, len(list(store.glob("*.md"))))
        self.assertEqual(artifact.read_bytes(), destination.read_bytes())
        self.cli("learnings.query", "--limit", "0", status=2, raw=True)
        self.cli("learnings.query", "--limit", "invalid", status=2, raw=True)
        self.cli("config-set", "features.global_learnings", "false")
        self.assertEqual([], self.cli("learnings.query", "--tag", "worktrees")["items"])

    def test_retained_learning_extraction_requires_real_citations(self):
        self.init_records()
        packet = {"items": [{"category": "lessons", "text": "Retain user-approved behavior.",
                             "citations": ["README.md"]}]}
        source = self.put("learning-input.json", json.dumps(packet))
        result = self.cli("learnings.extract", "--input", source)
        self.assertTrue(result["stored"])
        self.assertEqual(1, len(self.cli("learnings.query", "--query", "user-approved")["items"]))
        packet["items"][0]["citations"] = ["missing.md"]
        source.write_text(json.dumps(packet), encoding="utf-8")
        self.cli("learnings.extract", "--input", source, status=2, raw=True)

    def test_prohibition_gate_does_not_accept_a_caller_claim_as_proof(self):
        request = {"prohibition": {"statement": "Must not leak credentials"}, "check": None}
        result = self.cli("check.prohibition-enforcement", "--payload", json.dumps(request))
        self.assertTrue(result["payload"]["flagged"])
        self.assertEqual("unverified", result["payload"]["status"])
        self.assertEqual([], result["payload"]["evidence"])
        self.cli("check.prohibition-enforcement", "--payload", "not json", status=2, raw=True)

    def test_prohibition_input_selection_is_independent_of_json_output(self):
        request = {"prohibition": {"statement": "Must not leak credentials"}, "check": None, "mode": "manual"}
        payload = json.dumps(request)
        source = self.put("prohibition-request.json", payload)
        expected = self.cli("check.prohibition-enforcement", "--payload", payload)
        for input_args in (("--payload", payload), (str(source),), ("--input", str(source))):
            for output_args in ((), ("--json",)):
                with self.subTest(input=input_args[0], json_output=bool(output_args)):
                    actual = self.cli("check.prohibition-enforcement", *input_args, *output_args)
                    self.assertEqual(expected, actual)
        self.assertEqual("manual", expected["payload"]["mode"])
        self.assertTrue(expected["payload"]["flagged"])
        self.assertEqual("unverified", expected["payload"]["status"])

    def test_prohibition_malformed_file_fails_with_or_without_json_output(self):
        source = self.put("malformed-prohibition.json", "not json")
        for input_args in ((str(source),), ("--input", str(source))):
            for output_args in ((), ("--json",)):
                with self.subTest(input=input_args[0], json_output=bool(output_args)):
                    self.cli("check.prohibition-enforcement", *input_args, *output_args, status=2, raw=True)

    def test_native_review_records_actual_scope_and_enforces_revision(self):
        self.init_records()
        revision = self.git("rev-parse", "HEAD")
        dispatch = self.cli("review.dispatch", "--base", revision, "--files", "README.md")
        self.assertTrue(dispatch["requiresNativeDispatch"])
        report = {"captured_revision": revision, "base_revision": revision,
                  "examined_scope": ["README.md"], "unreached_scope": [], "findings": [],
                  "reviewer": "independent reviewer", "author": "source author"}
        source = self.put("review.json", json.dumps(report))
        recorded = self.cli("review.record", dispatch["dispatch_id"], "--input", source)
        self.assertEqual("reported", recorded["state"])
        self.assertTrue(self.cli("review.status", dispatch["dispatch_id"])["current"])
        report["captured_revision"] = "0" * 40
        source.write_text(json.dumps(report), encoding="utf-8")
        self.cli("review.record", dispatch["dispatch_id"], "--input", source, status=1, raw=True)
