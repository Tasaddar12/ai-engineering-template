"""Behavioral checks for retired CLI rejection and retained native safety routes."""
import json
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class LegacyRuntimeRetirement(RuntimeCase):
    def test_retired_routes_are_unknown_and_do_not_mutate_records(self):
        self.init_records()
        state = (self.root / ".planning/STATE.md").read_bytes()
        retired = ["estimate-calibrate", "estimate-check", "research-plan", "research-store", "research-store.put",
                   "classify-confidence", "check", "check.predicate", "check.auto-mode", "check.unregistered",
                   "teams-status", "review-lane", "review.run", "review.collect", "resolve-package-manager",
                   "normalize-test-command", "detect-custom-files", "custom-files.backup", "restore-custom-files",
                   "verify.context-drift", "worktree.worker-record", "worktree.worker-status", "worktree.worker-complete",
                   "loop.render-hooks", "loop.events", "loop.list", "windows.append", "windows.status",
                   "intel.api-surface", "learnings.extract", "roadmap.annotate-dependencies", "quick-tasks-append",
                   "quick-tasks-migrate", "review.contributions"]
        verbs = self.cli("verbs")["verbs"]
        for verb in retired:
            with self.subTest(verb=verb):
                self.assertNotIn(verb, verbs)
                self.cli(verb, status=2, raw=True)
        self.assertEqual(state, (self.root / ".planning/STATE.md").read_bytes())

    def test_obsolete_configuration_is_rejected_and_host_is_resolved_directly(self):
        self.init_records()
        for key, value in (("runtime", "codex"), ("workflow.build_command", "make"),
                           ("workflow.test_command", "pytest"), ("workflow.code_review_point", "execute:post"),
                           ("workflow.test_gate_timeout", "600"), ("workflow.broken_windows", "true"),
                           ("workflow.context_drift_action", "warn"), ("review.timeout_seconds", "600"),
                           ("workflow.plan_chunked", "true")):
            with self.subTest(key=key):
                self.cli("config-set", key, value, status=2, raw=True)
        self.assertEqual("codex", self.cli("runtime-identity")["host"])
        self.assertEqual("AGENTS.md", self.cli("project-instruction-file"))

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
