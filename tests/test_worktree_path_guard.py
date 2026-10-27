"""Warn-only worktree dispatch/write guards and shared role inventory regressions."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
sys.path.insert(0, str(HOOKS))
spec = importlib.util.spec_from_file_location("worktree_path_guard", HOOKS / "worktree-path-guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class WorktreePathGuard(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(guard, "root_for", return_value=self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_writer_without_isolation_warns_and_records_exact_dispatch(self):
        event = {"tool_name": "Agent", "session_id": "session", "tool_use_id": "call-1", "tool_input": {"subagent_type": "executor", "agent_id": "worker"}}
        warning = guard.inspect(event)
        self.assertTrue(any("isolation=worktree" in text for text in warning))
        record = json.loads((self.root / ".planning/handoffs/.active-session.jsonl").read_text())
        self.assertEqual("worker", record["agent_id"])
        self.assertEqual("executor", record["role"])
        self.assertEqual("call-1", record["tool_use_id"])
        self.assertEqual("active", record["status"])

    def test_isolated_writer_and_read_only_scout_do_not_warn(self):
        for role in ("executor", "scout"):
            event = {"tool_name": "Task", "tool_input": {"role": role, "isolation": "worktree"}}
            self.assertEqual([], guard.inspect(event))

    def test_primary_scratch_and_outside_paths_remain_advisory(self):
        (self.root / ".git").mkdir()
        event = {"tool_name": "Write", "tool_input": {"file_path": str(self.root.parent / "scratchpad/value.txt")}}
        warnings = guard.inspect(event)
        self.assertTrue(any("primary checkout" in value for value in warnings))
        self.assertTrue(any("outside" in value for value in warnings))
        self.assertTrue(any("scratchpad" in value for value in warnings))
        with patch.object(guard, "read_event", return_value=event), patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(0, guard.main())

    def test_apply_patch_paths_receive_the_same_containment_advice(self):
        event = {"tool_name": "apply_patch", "tool_input": {"patch": "*** Begin Patch\n*** Update File: ../outside.py\n*** End Patch"}}
        self.assertTrue(any("outside" in value for value in guard.inspect(event)))

    def test_malformed_json_never_blocks(self):
        with patch("sys.stdin", new=io.StringIO("not-json")), patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(0, guard.main())

    def test_reparse_state_directory_is_not_followed(self):
        outside = self.root / "outside"
        outside.mkdir()
        try:
            (self.root / ".planning").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation unavailable")
        event = {"tool_name": "Agent", "tool_input": {"role": "executor"}}
        with patch.object(guard, "read_event", return_value=event), patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(0, guard.main())
        self.assertEqual([], list(outside.iterdir()))

    def test_inventory_has_exact_canonical_roles_and_no_legacy_aliases(self):
        roles = guard.roles()
        self.assertIn("executor", roles["WRITE_ROLES"])
        self.assertIn("planner", roles["ARTIFACT_ROLES"])
        self.assertIn("dom-verifier", roles["REVIEW_ROLES"])
        all_roles = set.union(*roles.values())
        self.assertTrue({"coder", "phase-preparer", "phase-checker", "researcher"}.isdisjoint(all_roles))


if __name__ == "__main__":
    unittest.main()
