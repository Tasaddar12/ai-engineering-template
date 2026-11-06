"""Quick delivery selection preserves verification and exact provider-head gates.

These are delivery-owner unit tests: verification verdicts are controlled at the
module boundary; the provider seam records all simulated ready/merge operations.
"""
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


class QuickDelivery(RuntimeCase):
    def setUp(self):
        super().setUp()
        environment = patch.dict("os.environ", self.env)
        environment.start()
        self.addCleanup(environment.stop)
        self.git("remote", "add", "origin", "https://github.com/example/project.git")
        self.directory = self.root / ".planning/quick/001-repair"
        self.directory.mkdir(parents=True)
        self.head = self.git("rev-parse", "HEAD")
        self.pull = dict(number=12, url="https://github.com/example/project/pull/12", state="OPEN",
                         isDraft=True, headRefName="worker", headRefOid=self.head,
                         statusCheckRollup=[{"name": "validate", "conclusion": "SUCCESS"}],
                         mergeable="MERGEABLE")
        self.mutations = []
        self.provider = patch.object(delivery, "gh", side_effect=self.fake_provider).start()
        # Context validation and currentness have their own real-runtime tests.
        self.resolver = patch.object(delivery.verification, "verification_dir", create=True,
                                     return_value=self.directory).start()
        self.status = patch.object(delivery.verification, "status", return_value={"status": "passed"}).start()
        self.evidence = patch.object(delivery.verification, "current_evidence", return_value={"current": True}).start()
        self.configured = patch.object(delivery.verification, "configured_checks", return_value=[{"id": "unit"}]).start()
        self.addCleanup(patch.stopall)

    def fake_provider(self, argv, **kwargs):
        if argv[:2] == ["pr", "view"]:
            return SimpleNamespace(returncode=0, stderr="", stdout=json.dumps(self.pull))
        self.mutations.append(list(argv))
        if argv[:2] == ["pr", "ready"]:
            self.pull["isDraft"] = False
        elif argv[:2] == ["pr", "merge"]:
            self.pull["state"] = "MERGED"
        else:
            raise AssertionError(argv)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    def invoke(self, action, extra=(), expected=True, confirm=True):
        values = ["worker", "--quick", str(self.directory)]
        if expected is not False:
            values += ["--expected-head", self.head if expected is True else expected]
        if action == "merge" and confirm:
            values += ["--confirm"]
        return delivery.command(Args(values + list(extra)), action)

    def test_quick_ready_confirms_same_pr_head_and_forwards_evidence(self):
        flags = ("--evidence-file", "baseline.json", "--fresh-evidence-file", "fresh.json")
        result = self.invoke("ready", flags)
        self.assertTrue(result["ready"])
        self.assertEqual(self.head, result["expected_head"])
        self.assertEqual([["pr", "ready", "12"]], self.mutations)
        self.assertEqual(3, self.evidence.call_count)
        for call in self.evidence.call_args_list:
            self.assertEqual(str(self.directory), call.args[0])
            self.assertEqual("baseline.json", call.args[1].get("evidence-file"))
            self.assertEqual("fresh.json", call.args[1].get("fresh-evidence-file"))

    def test_quick_merge_requires_confirmation_and_binds_provider_head(self):
        with self.assertRaises(Failure) as rejected:
            self.invoke("merge", confirm=False)
        self.assertEqual("merge-not-authorized", rejected.exception.code)
        self.assertEqual([], self.mutations)
        result, code = self.invoke("merge")
        self.assertTrue(result["merged"])
        self.assertEqual(0, code)
        self.assertEqual(["pr", "merge", "12", "--squash", "--match-head-commit", self.head], self.mutations[-1])
        self.assertNotIn("--admin", self.mutations[-1])
        for call in self.evidence.call_args_list:
            self.assertEqual(str(self.directory), call.args[0])
            self.assertEqual(str(self.directory), call.args[1].get("quick"))

    def test_quick_requires_exact_expected_head_and_unambiguous_owner(self):
        for action in ("ready", "merge"):
            for expected in (False, "HEAD", "", "b" * 40):
                with self.subTest(action=action, expected=expected), self.assertRaises(Failure):
                    self.invoke(action, expected=expected)
            with self.subTest(action=action), self.assertRaises(Failure) as rejected:
                self.invoke(action, ("--phase", "1"))
            self.assertEqual("ambiguous-verification-owner", rejected.exception.code)
        self.assertEqual([], self.mutations)

    def test_phase_selector_cannot_select_quick_directory(self):
        for action in ("ready", "merge"):
            for value in (str(self.directory), self.directory.relative_to(self.root).as_posix()):
                with self.subTest(action=action, value=value), self.assertRaises(Failure) as rejected:
                    delivery.command(Args(["worker", "--phase", value, "--confirm"]), action)
                self.assertEqual("invalid-phase-directory", rejected.exception.code)
        self.assertEqual([], self.mutations)

    def test_quick_selector_rejects_phase_owner(self):
        self.resolver.return_value = self.root / ".planning/phases/01-repair"
        for action in ("ready", "merge"):
            with self.subTest(action=action), self.assertRaises(Failure) as rejected:
                self.invoke(action)
            self.assertEqual("invalid-quick-directory", rejected.exception.code)
        self.assertEqual([], self.mutations)

    def test_missing_failed_or_stale_verification_never_mutates_provider(self):
        for action in ("ready", "merge"):
            for state in ("missing", "stale", "gaps_found", "human_needed", "unparseable"):
                self.status.return_value = {"status": state}
                with self.subTest(action=action, status=state), self.assertRaises(Failure):
                    self.invoke(action)
            self.status.return_value = {"status": "passed"}
            self.evidence.return_value = {"current": False, "reasons": ["missing receipt"]}
            with self.subTest(action=action, current=False), self.assertRaises(Failure):
                self.invoke(action)
            self.evidence.return_value = {"current": True}
        self.assertEqual([], self.mutations)

    def test_closed_wrong_branch_wrong_head_or_invalid_identity_never_mutates(self):
        for action in ("ready", "merge"):
            for field, value in (("state", "CLOSED"), ("headRefName", "another-worker"),
                                 ("headRefOid", "b" * 40), ("headRefOid", None),
                                 ("number", True), ("number", 0), ("number", "12")):
                original = self.pull[field]
                self.pull[field] = value
                with self.subTest(action=action, field=field, value=value), self.assertRaises(Failure):
                    self.invoke(action)
                self.pull[field] = original
        self.assertEqual([], self.mutations)

    def test_missing_pull_request_never_mutates_provider(self):
        self.provider.side_effect = lambda argv, **kwargs: SimpleNamespace(
            returncode=1, stderr="no pull requests found for branch", stdout="")
        for action in ("ready", "merge"):
            with self.subTest(action=action), self.assertRaises(Failure) as rejected:
                self.invoke(action)
            self.assertEqual("pr-not-found", rejected.exception.code)
        self.assertEqual([], self.mutations)

    def test_failed_pending_conflicting_or_absent_checks_never_mutate(self):
        for action in ("ready", "merge"):
            for conclusion in ("FAILURE", "PENDING", "IN_PROGRESS"):
                self.pull["statusCheckRollup"] = [{"name": "validate", "conclusion": conclusion}]
                with self.subTest(action=action, conclusion=conclusion), self.assertRaises(Failure):
                    self.invoke(action)
            self.pull["statusCheckRollup"] = []
            self.configured.return_value = []
            with self.subTest(action=action, absent=True), self.assertRaises(Failure):
                self.invoke(action)
            self.configured.return_value = [{"id": "unit"}]
            self.pull["mergeable"] = "CONFLICTING"
            with self.subTest(action=action, conflict=True), self.assertRaises(Failure):
                self.invoke(action)
            self.pull["mergeable"] = "MERGEABLE"
        self.assertEqual([], self.mutations)

    def test_evidence_or_local_head_movement_before_provider_write_blocks(self):
        for action in ("ready", "merge"):
            self.evidence.side_effect = [{"current": True}, {"current": False}]
            self.pull["isDraft"] = False
            with self.subTest(action=action), self.assertRaises(Failure):
                self.invoke(action)
            self.assertEqual([], self.mutations)
            self.evidence.side_effect = None
        def moved(*args):
            self.git("commit", "--allow-empty", "-m", "move during evidence")
            return {"current": True}
        self.evidence.side_effect = moved
        with self.assertRaises(Failure):
            self.invoke("ready")
        self.assertEqual([], self.mutations)

    def test_ready_refusal_and_changed_readback_never_certify_ready(self):
        def refuse(argv, **kwargs):
            if argv[:2] == ["pr", "ready"]:
                return SimpleNamespace(returncode=1, stderr="provider denied", stdout="")
            return self.fake_provider(argv, **kwargs)
        self.provider.side_effect = refuse
        with self.assertRaises(Failure) as rejected:
            self.invoke("ready")
        self.assertEqual("ready-refused", rejected.exception.code)
        def moved(argv, **kwargs):
            result = self.fake_provider(argv, **kwargs)
            if argv[:2] == ["pr", "ready"]:
                self.pull["headRefOid"] = "b" * 40
            return result
        self.provider.side_effect = moved
        with self.assertRaises(Failure) as rejected:
            self.invoke("ready")
        self.assertEqual("head-mismatch", rejected.exception.code)

    def test_ready_rechecks_evidence_after_actual_provider_readback(self):
        self.evidence.side_effect = [{"current": True}, {"current": True}, {"current": False}]
        with self.assertRaises(Failure) as rejected:
            self.invoke("ready")
        self.assertEqual("verification-stale", rejected.exception.code)
        self.assertEqual([["pr", "ready", "12"]], self.mutations)
