"""Context, planning and worktree lifecycle contracts; no external packages required."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "hooks"))


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "hooks" / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


context = load("context-handoff")
integrity = load("planning-integrity")
location = load("worktree-location")


class ContextContracts(unittest.TestCase):
    def test_coordinator_never_receives_stop_or_handoff_request(self):
        for event in ({"role": "coordinator", "agent_id": "root", "context_tokens": 999999}, {"context_tokens": 999999}):
            with patch.object(context, "read_event", return_value=event), patch.object(context, "query") as query:
                self.assertEqual(0, context.main())
                query.assert_not_called()

    def test_configured_threshold_writes_digest_and_returns_advice_only(self):
        event = {"role": "executor", "agent_id": "worker", "session_id": "s", "context_tokens": 600}
        limits = {"enabled": True, "threshold_tokens": 600, "binding": "percent"}
        with tempfile.TemporaryDirectory() as folder, patch.object(context, "read_event", return_value=event), patch.object(context, "root_for", return_value=Path(folder)), patch.object(context, "query", side_effect=[limits, {"ok": True}]) as query, patch.object(context, "advisory") as advisory:
            self.assertEqual(0, context.main())
            self.assertEqual("handoff.limits", query.call_args_list[0].args[1])
            self.assertEqual("handoff.write", query.call_args_list[1].args[1])
            self.assertIn("--reason", query.call_args_list[1].args)
            self.assertIn("status: blocked", advisory.call_args.args[1])
            self.assertNotIn("decision", advisory.call_args.args[1])

    def test_unavailable_runtime_and_malformed_event_fail_open(self):
        with patch.object(context, "read_event", side_effect=ValueError("bad input")), patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(0, context.main())


class IntegrityContracts(unittest.TestCase):
    def test_only_actual_git_commit_subcommands_are_prospective_commits(self):
        self.assertTrue(integrity.prospective_commit("git -C project commit -m repair"))
        self.assertFalse(integrity.prospective_commit("git status --short"))
        self.assertFalse(integrity.prospective_commit("echo 'git commit -m example'"))

    def test_strict_integrity_failure_returns_two(self):
        event = {"tool_name": "Bash", "tool_input": {"command": "git commit -m repair"}}
        with patch.object(integrity, "read_event", return_value=event), patch.object(integrity, "root_for", return_value=ROOT), patch.object(integrity, "query", return_value={"ok": False, "errors": ["malformed record"]}), patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(2, integrity.main())

    def test_validation_warning_does_not_block_a_valid_commit(self):
        event = {"tool_name": "exec_command", "tool_input": {"cmd": "git commit -m repair"}}
        with patch.object(integrity, "read_event", return_value=event), patch.object(integrity, "root_for", return_value=ROOT), patch.object(integrity, "query", side_effect=[{"ok": True}, {"warnings": ["drift"]}]), patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(0, integrity.main())


class LocationContracts(unittest.TestCase):
    def test_escaping_name_refuses_without_git_mutation(self):
        with patch.object(location, "read_event", return_value={"name": "../outside", "hook_event_name": "WorktreeCreate"}), patch.object(location, "root_for", return_value=ROOT), patch.object(location.subprocess, "run") as run, patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(2, location.main())
            run.assert_not_called()

    def test_remove_uses_no_force_and_no_recursive_delete(self):
        event = {"name": "worker", "hook_event_name": "WorktreeRemove"}
        with tempfile.TemporaryDirectory() as folder, patch.object(location, "read_event", return_value=event), patch.object(location, "root_for", return_value=Path(folder)), patch.object(location.subprocess, "run") as run:
            self.assertEqual(0, location.main())
            self.assertEqual(["git", "worktree", "remove", str(Path(folder) / ".worktrees/worker")], run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
