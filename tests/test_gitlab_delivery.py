"""Offline glab API tests; shared resolver integration runs when installed.

The delivery PR depends on the provider resolver PR. Unit tests isolate that
contract; integration tests below require the exact real resolver in the tree.
No test contacts a provider or reads credentials.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".ai" / "runtime"))
from lib import delivery, gitlab_delivery as adapter, worktrees
from lib.paths import Workspace
from lib.results import VerbError, require

try:
    from lib import providers
except ImportError:
    providers = None

TARGET = dict(provider="gitlab", host="gitlab.example.test:8443", project="group/sub/project",
              remote="origin", repository="gitlab.example.test:8443/group/sub/project",
              web_url="https://gitlab.example.test:8443/group/sub/project")


def contract_number(target, url, kind):
    """Unit seam only. Exact resolver integration uses its real validator."""
    prefix = target["web_url"] + "/-/merge_requests/"
    require(isinstance(url, str) and url.startswith(prefix) and url[len(prefix):].isdigit(),
            "Wrong URL ownership", "provider-url")
    return int(url[len(prefix):])


class GitLabDelivery(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.workspace = Workspace(self.root)
        self.workspace.planning.mkdir()
        self.workspace.config.write_text("delivery:\n  provider: gitlab\n", encoding="utf-8")
        self.pull = self.mr()
        self.calls = []
        self.write_mode = "ok"
        self.authenticated = True
        self.hidden = False
        self.bad_json = False
        self.extra = []
        self.start_patch(patch.object(adapter, "glab", side_effect=self.fake_glab))
        self.dispatch = patch.object(delivery, "gitlab_target", return_value=TARGET)
        self.start_patch(self.dispatch)
        self.start_patch(patch.object(delivery.gitops, "base_branch", return_value="main"))
        self.start_patch(patch.object(adapter.time, "sleep"))
        if providers is None:
            from types import ModuleType
            seam = ModuleType("lib.providers")
            seam.item_number = contract_number
            self.start_patch(patch.dict(sys.modules, {"lib.providers": seam}))

    def start_patch(self, item):
        item.start()
        self.addCleanup(item.stop)

    def mr(self, **fields):
        result = dict(iid=7, web_url=TARGET["web_url"] + "/-/merge_requests/7", state="opened",
                      draft=True, title="Draft: feat(delivery): original", description="Original body",
                      target_branch="parent", source_branch="feature/child", source_project_id=3,
                      target_project_id=3, sha="a" * 40, detailed_merge_status="mergeable",
                      head_pipeline=dict(id=1, status="success", sha="a" * 40,
                                         web_url=TARGET["web_url"] + "/-/pipelines/1"))
        result.update(fields)
        return result

    def fake_glab(self, workspace, *args, cwd=None, payload=None):
        self.calls.append((args, payload))
        if args == ("--version",):
            return subprocess.CompletedProcess(args, 0, "glab test\n", "")
        if args[:2] == ("auth", "status"):
            self.assertEqual(args[2:], ("--hostname", TARGET["host"]))
            return subprocess.CompletedProcess(args, 0 if self.authenticated else 1, "", "")
        self.assertEqual(args[0], "api")
        self.assertEqual(args[2:6], ("--hostname", TARGET["host"], "--method", args[5]))
        path, method = args[1], args[5]
        self.assertTrue(path.startswith("projects/group%2Fsub%2Fproject/merge_requests"))
        if method == "GET":
            if self.bad_json:
                return subprocess.CompletedProcess(args, 0, "not-json", "")
            if "?" in path:
                query = parse_qs(urlsplit(path).query)
                self.assertEqual(query["source_branch"], ["feature/child"])
                data = ([] if self.hidden or self.pull is None else [self.pull]) + self.extra
            else:
                data = self.pull
            return subprocess.CompletedProcess(args, 0, json.dumps(data), "")
        self.assertEqual(args[6:], ("--input", "-"))
        if self.write_mode == "lost-before":
            raise VerbError("timeout", "glab-unavailable")
        if method == "POST":
            self.assertIsNone(self.pull)
            self.pull = self.mr(iid=8, web_url=TARGET["web_url"] + "/-/merge_requests/8")
        if path.endswith("/merge"):
            if payload["sha"] != self.pull["sha"]:
                return subprocess.CompletedProcess(args, 1, "", "sha mismatch")
            self.pull["state"] = "merged"
        else:
            for name in ("title", "description", "source_branch", "target_branch"):
                if name in payload:
                    self.pull[name] = payload[name]
            self.pull["draft"] = self.pull["title"].startswith("Draft:")
        if self.write_mode == "lost-after":
            raise VerbError("timeout", "glab-unavailable")
        if self.write_mode == "hidden-after":
            self.hidden = True
        return subprocess.CompletedProcess(args, 0, json.dumps(self.pull), "")

    def writes(self):
        return [(args, body) for args, body in self.calls if args[0] == "api" and args[5] != "GET"]

    def test_existing_edit_preserves_target_draft_and_body_bytes(self):
        body = self.root / "canonical body.md"
        text = "## Goal\n\nfeat(delivery): title\n\n## Known gaps\n\n- Pending CI\n"
        body.write_text(text, encoding="utf-8")
        result = delivery.open_pr(self.workspace, "feature/child", title="feat(delivery): updated",
                                  body="ignored", body_file=body, draft=False)
        self.assertEqual(result["body"], text)
        self.assertEqual(result["baseRefName"], "parent")
        self.assertTrue(result["isDraft"])
        self.assertEqual(self.writes()[0][1], dict(title="Draft: feat(delivery): updated", description=text))
        self.assertTrue(result["updated"])
        self.assertFalse(result["created"])

    def test_ready_edit_stays_ready_and_explicit_base_retargets_same_mr(self):
        self.pull.update(draft=False, title="feat(delivery): original")
        result = delivery.open_pr(self.workspace, "feature/child", base="main", title="feat(delivery): next")
        self.assertEqual(result["number"], 7)
        self.assertEqual(result["baseRefName"], "main")
        self.assertFalse(result["isDraft"])

    def test_no_fields_does_not_write(self):
        result = delivery.open_pr(self.workspace, "feature/child")
        self.assertFalse(result["updated"])
        self.assertEqual(self.writes(), [])

    def test_create_then_retry_updates_same_mr(self):
        self.pull = None
        first = delivery.open_pr(self.workspace, "feature/child", title="feat(delivery): create", body="canonical")
        self.assertTrue(first["created"])
        self.assertEqual(first["baseRefName"], "main")
        second = delivery.open_pr(self.workspace, "feature/child", body="current")
        self.assertEqual(first["number"], second["number"])
        self.assertEqual([args[5] for args, _ in self.writes()], ["POST", "PUT"])

    def test_runtime_records_normalized_mr_in_existing_session_metadata(self):
        import phase
        worktrees.save_sessions(self.workspace, dict(sessions=[dict(branch="feature/child", pr=None)]))
        result = phase.verb_pr_open(self.workspace, ["feature/child"], dict(body="current"))
        stored = worktrees.load_sessions(self.workspace)["sessions"][0]["pr"]
        self.assertEqual(stored, dict(url=result["url"], number=7))

    def test_create_ready_and_default_title(self):
        self.pull = None
        result = delivery.open_pr(self.workspace, "feature/child", draft=False)
        self.assertEqual(result["title"], "feature/child")
        self.assertFalse(result["isDraft"])

    def test_lost_write_response_succeeds_only_after_matching_readback(self):
        self.pull = None
        self.write_mode = "lost-after"
        result = delivery.open_pr(self.workspace, "feature/child", title="feat(delivery): create", body="body")
        self.assertTrue(result["created"])
        self.assertEqual(len(self.writes()), 1)

    def test_unresolved_create_blocks_second_post_across_retries(self):
        self.pull = None
        self.write_mode = "lost-before"
        with self.assertRaises(VerbError) as first:
            delivery.open_pr(self.workspace, "feature/child", title="feat(delivery): create")
        self.assertEqual(first.exception.code, "mr-uncertain")
        self.write_mode = "ok"
        with self.assertRaises(VerbError) as second:
            delivery.open_pr(self.workspace, "feature/child", title="feat(delivery): create")
        self.assertEqual(second.exception.code, "mr-uncertain")
        self.assertEqual(len(self.writes()), 1)

    def test_hidden_create_recovered_by_later_readback_without_second_post(self):
        self.pull = None
        self.write_mode = "hidden-after"
        with self.assertRaises(VerbError):
            delivery.open_pr(self.workspace, "feature/child", body="canonical")
        self.hidden, self.write_mode = False, "ok"
        result = delivery.open_pr(self.workspace, "feature/child")
        self.assertEqual(result["number"], 8)
        self.assertEqual(len(self.writes()), 1)

    def test_uncertain_edit_never_returns_stale_success(self):
        self.write_mode = "lost-before"
        with self.assertRaises(VerbError) as raised:
            delivery.open_pr(self.workspace, "feature/child", body="new")
        self.assertEqual(raised.exception.code, "mr-uncertain")
        self.assertEqual(self.pull["description"], "Original body")
        self.write_mode = "ok"
        with self.assertRaises(VerbError) as stale:
            delivery.open_pr(self.workspace, "feature/child")
        self.assertEqual(stale.exception.code, "mr-uncertain")
        result = delivery.open_pr(self.workspace, "feature/child", body="new")
        self.assertEqual(result["body"], "new")

    def test_wrong_owner_or_branch_blocks_mutation(self):
        for field, value in (("web_url", "https://other.test/group/sub/project/-/merge_requests/7"),
                             ("iid", 9), ("draft", None), ("state", "unknown")):
            with self.subTest(field=field):
                self.pull = self.mr(**{field: value})
                with self.assertRaises(VerbError):
                    delivery.open_pr(self.workspace, "feature/child", body="new")
                self.assertEqual(self.writes(), [])

    def test_malformed_listing_and_duplicate_open_mrs_block_create(self):
        self.bad_json = True
        with self.assertRaises(VerbError):
            delivery.open_pr(self.workspace, "feature/child")
        self.bad_json = False
        self.extra = [self.mr(iid=8)]
        with self.assertRaises(VerbError) as raised:
            delivery.open_pr(self.workspace, "feature/child")
        self.assertEqual(raised.exception.code, "mr-ambiguous")
        self.assertEqual(self.writes(), [])

    def test_closed_mr_is_readable_but_not_edited(self):
        self.pull["state"] = "closed"
        self.assertEqual(delivery.view(self.workspace, "feature/child")["state"], "CLOSED")
        with self.assertRaises(VerbError) as raised:
            delivery.open_pr(self.workspace, "feature/child", body="new")
        self.assertEqual(raised.exception.code, "pr-not-open")

    def test_preflight_is_host_scoped_and_never_writes_credentials(self):
        self.authenticated = False
        result = delivery.availability(self.workspace)
        self.assertTrue(result["available"])
        self.assertFalse(result["authenticated"])
        self.assertEqual(result["host"], TARGET["host"])
        with self.assertRaises(VerbError):
            delivery.open_pr(self.workspace, "feature/child")
        self.assertEqual(self.writes(), [])

    def test_pipeline_gate_states_and_stale_sha(self):
        for status, expected in (("success", "passing"), ("running", "pending"),
                                 ("failed", "failing"), ("canceled", "failing"),
                                 ("manual", "failing"), ("skipped", "failing"),
                                 ("unknown", "failing")):
            with self.subTest(status=status):
                self.pull["head_pipeline"]["status"] = status
                self.assertEqual(delivery.checks(self.workspace, "feature/child")["state"], expected)
        self.pull["head_pipeline"].update(status="success", sha="b" * 40)
        self.assertEqual(delivery.checks(self.workspace, "feature/child")["state"], "pending")

    def test_no_pipeline_is_none_but_required_or_unknown_ci_blocks(self):
        self.pull["head_pipeline"] = None
        self.assertEqual(delivery.checks(self.workspace, "feature/child")["state"], "none")
        self.pull["detailed_merge_status"] = "ci_must_pass"
        self.assertEqual(delivery.checks(self.workspace, "feature/child")["state"], "pending")
        self.pull["detailed_merge_status"] = "unknown"
        self.assertEqual(delivery.checks(self.workspace, "feature/child")["state"], "failing")

    def test_pending_checks_wait_and_settle(self):
        self.pull["head_pipeline"]["status"] = "running"
        now = [0]
        def sleep(seconds):
            now[0] += seconds
            self.pull["head_pipeline"]["status"] = "success"
        result = adapter.checks(self.workspace, TARGET, "feature/child", wait=30,
                                sleep=sleep, clock=lambda: now[0])
        self.assertEqual(result["state"], "passing")
        self.assertEqual(result["waited"], 30)

    def test_merge_gates_block_failed_pending_and_absent_evidence(self):
        for status, code in (("failed", "checks-failing"), ("running", "checks-pending"),
                             (None, "no-evidence")):
            with self.subTest(status=status):
                self.pull = self.mr(head_pipeline=None if status is None else
                                    dict(status=status, sha="a" * 40))
                with self.assertRaises(VerbError) as raised:
                    delivery.merge_pr(self.workspace, "feature/child")
                self.assertEqual(raised.exception.code, code)
                self.assertEqual(self.writes(), [])

    def test_merge_is_sha_guarded_and_confirmed_in_offline_fake_only(self):
        result = delivery.merge_pr(self.workspace, "feature/child")
        self.assertTrue(result["merged"])
        self.assertEqual(self.writes()[-1][1]["sha"], "a" * 40)
        self.assertEqual(result["pr_state"], "MERGED")


@unittest.skipIf(providers is None, "Requires separate provider-resolver PR; run in integration tree")
class ExactResolverIntegration(GitLabDelivery):
    def setUp(self):
        super().setUp()
        # Remove only the dispatch seam, so this suite drives the actual config
        # and SSH-to-web authority resolver, followed by the offline glab adapter.
        self.dispatch.stop()
        self.workspace.config.write_text("delivery:\n  provider: auto\n  gitlab_hosts:\n"
                                         "    gitlab.example.test: https://gitlab.example.test:8443\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "remote", "add", "origin",
                        "ssh://git@gitlab.example.test:2222/group/sub/project.git"], check=True)


if __name__ == "__main__":
    unittest.main()
