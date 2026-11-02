"""Main PR109 merge-head and provider-race regressions on the installed runtime API."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE

sys.path.insert(0, str(SOURCE / "engineer/bin"))
from lib import delivery
from lib.core import Args, Failure


class MergeHeadGuard(RuntimeCase):
    def setUp(self):
        super().setUp()
        self.env_patch = patch.dict("os.environ", self.env)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.head = self.git("rev-parse", "HEAD")
        self.pull = dict(number=12, url="https://github.com/example/project/pull/12", state="OPEN",
                         isDraft=False, headRefName="worker", headRefOid=self.head,
                         statusCheckRollup=[{"name": "validate", "conclusion": "SUCCESS"}], mergeable="MERGEABLE")
        self.merged = {**self.pull, "state": "MERGED"}
        self.views = patch.object(delivery, "view", side_effect=lambda _: self.pull).start()
        self.provider = patch.object(delivery, "gh", return_value=SimpleNamespace(returncode=0, stderr="", stdout="")).start()
        patch.object(delivery.verification, "status", return_value={"status": "passed"}).start()
        self.evidence = patch.object(delivery.verification, "current_evidence", return_value={"current": True}).start()
        self.configured = patch.object(delivery.verification, "configured_checks", return_value=[{"id": "unit"}]).start()
        self.addCleanup(patch.stopall)

    def merge(self, expected=True, extra=()):
        values = ["worker", "--phase", "1", "--confirm"]
        if expected is not False:
            values += ["--expected-head", self.head if expected is True else expected]
        return delivery.command(Args(values + list(extra)), "merge")

    def test_expected_head_binds_provider_mutation_and_matching_readback(self):
        self.views.side_effect = [self.pull, self.merged]
        result, status = self.merge()
        self.assertTrue(result["merged"])
        self.assertEqual(0, status)
        argv = self.provider.call_args.args[0]
        self.assertEqual(self.head, argv[argv.index("--match-head-commit") + 1])
        self.assertNotIn("--admin", argv)

    def test_stale_local_or_provider_head_closed_and_malformed_expected_block(self):
        for expected in ("b" * 40, "HEAD", "bad", ""):
            with self.subTest(expected=expected), self.assertRaises(Failure):
                self.merge(expected)
        for field, value in (("headRefOid", "b" * 40), ("headRefOid", None), ("state", "CLOSED")):
            original = self.pull[field]
            self.pull[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(Failure):
                self.merge()
            self.pull[field] = original
        self.provider.assert_not_called()

    def test_provider_race_refuses_and_changed_readback_is_uncertain(self):
        self.provider.return_value.returncode = 1
        self.provider.return_value.stderr = "head did not match"
        with self.assertRaises(Failure):
            self.merge()
        self.provider.return_value.returncode = 0
        self.views.side_effect = [self.pull, {**self.merged, "headRefOid": "b" * 40}]
        result, status = self.merge()
        self.assertFalse(result["merged"])
        self.assertTrue(result["retryable"])
        self.assertEqual(1, status)

    def test_legacy_call_keeps_provider_arguments_unchanged(self):
        self.views.side_effect = [self.pull, self.merged]
        result, status = self.merge(False)
        self.assertTrue(result["merged"])
        self.assertNotIn("--match-head-commit", self.provider.call_args.args[0])

    def test_local_movement_after_draft_ready_blocks_merge(self):
        self.pull["isDraft"] = True
        def ready(argv, **kwargs):
            self.git("commit", "--allow-empty", "-m", "move")
            return SimpleNamespace(returncode=0, stderr="", stdout="")
        self.provider.side_effect = ready
        with self.assertRaises(Failure):
            self.merge()
        self.assertEqual(1, self.provider.call_count)
        self.assertEqual(["pr", "ready", "12"], self.provider.call_args.args[0])

    def test_missing_pull_request_blocks_before_provider_mutation(self):
        self.views.side_effect = None
        self.views.return_value = None
        with self.assertRaises(Failure):
            self.merge()
        self.provider.assert_not_called()

    def test_missing_ci_requires_nonempty_local_checks(self):
        self.pull["statusCheckRollup"] = []
        self.configured.return_value = []
        with self.assertRaises(Failure):
            self.merge()
        self.provider.assert_not_called()

    def test_qualification_requires_expected_head_and_is_revalidated(self):
        with self.assertRaises(Failure):
            self.merge(False, ("--evidence-file", "external.json"))
        self.evidence.side_effect = [{"current": True}, {"current": False, "reasons": ["evidence moved"]}]
        with self.assertRaises(Failure):
            self.merge(extra=("--evidence-file", "external.json"))
        self.assertEqual(2, self.evidence.call_count)
        self.provider.assert_not_called()

    def test_dispatch_forwards_expected_head_and_view_requests_provider_identity(self):
        spec = importlib.util.spec_from_file_location("delivery_head_runtime", SOURCE / "engineer/bin/engineer.py")
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        with patch.object(delivery, "command", return_value={"merged": False}) as command:
            runtime.VERBS["pr.merge"](Args(["worker", "--expected-head", self.head]))
        self.assertEqual(self.head, command.call_args.args[0].get("expected-head"))
        self.assertIn("headRefOid", delivery.PR_FIELDS.split(","))
