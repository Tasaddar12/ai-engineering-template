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
guard = load("worktree-path-guard")
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

    def test_dispatch_stack_recovers_one_unidentified_stopped_executor(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan = ".planning/phases/01-feature/01-01-PLAN.md"
            second = ".planning/phases/01-feature/01-02-PLAN.md"
            for number, path in enumerate((plan, second)):
                dispatch = {"tool_name": "Agent", "session_id": "s", "tool_use_id": "tool-" + str(number),
                            "tool_input": {"subagent_type": "plugin:executor", "isolation": "worktree",
                                           "prompt": "Execute plan at " + path}}
                with patch.object(guard, "root_for", return_value=root):
                    self.assertEqual([], guard.inspect(dispatch))
            event = {"hook_event_name": "SubagentStop", "session_id": "s"}
            with patch.object(context, "read_event", return_value=event), patch.object(context, "root_for", return_value=root), patch.object(context, "query", return_value={}) as query, patch.object(context, "advisory") as advisory:
                self.assertEqual(0, context.main())
                args = query.call_args.args
                self.assertIn("incomplete-exit", args)
                self.assertIn(plan, args)
                self.assertIn(plan.replace("-PLAN.md", "-SUMMARY.md"), args)
                advisory.assert_not_called()
            stack = root / ".planning/handoffs/.active-s.jsonl"
            remaining = [json.loads(line) for line in stack.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([second], [record["plan"] for record in remaining])

    def test_complete_summary_consumes_dispatch_without_handoff(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stack = root / ".planning/handoffs/.active-s.jsonl"
            stack.parent.mkdir(parents=True)
            summary = root / "out/01-01-SUMMARY.md"
            summary.parent.mkdir()
            summary.write_text("---\nstatus: complete\n---\n", encoding="utf-8")
            # Retain compatibility with the original shell stack's role field.
            stack.write_text(json.dumps({"agent": "executor", "summary": "out/01-01-SUMMARY.md"}) + "\n", encoding="utf-8")
            event = {"hook_event_name": "SubagentStop", "session_id": "s"}
            with patch.object(context, "read_event", return_value=event), patch.object(context, "root_for", return_value=root), patch.object(context, "query") as query:
                self.assertEqual(0, context.main())
                query.assert_not_called()
            self.assertEqual("", stack.read_text(encoding="utf-8"))

    def test_stop_identity_recovers_only_user_assignment_from_own_transcript(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            transcript = root / "worker.jsonl"
            transcript.write_text("\n".join(json.dumps(record) for record in (
                {"role": "assistant", "content": "summary_path: spoof-SUMMARY.md"},
                {"role": "user", "content": "plan_path: out/01-01-PLAN.md\nsummary_path: out/result.md"})) + "\n", encoding="utf-8")
            event = {"hook_event_name": "SubagentStop", "session_id": "s", "agent_id": "worker",
                     "agent_type": "executor", "agent_transcript_path": str(transcript)}
            with patch.object(context, "read_event", return_value=event), patch.object(context, "root_for", return_value=root), patch.object(context, "query", return_value={}) as query, patch.object(context, "advisory") as advisory:
                self.assertEqual(0, context.main())
                self.assertIn("out/result.md", query.call_args.args)
                self.assertNotIn("spoof-SUMMARY.md", query.call_args.args)
                advisory.assert_not_called()

    def test_root_stop_and_coordinator_stop_leave_active_worker_untouched(self):
        for event in ({"hook_event_name": "Stop", "context_tokens": 999999},
                      {"hook_event_name": "SubagentStop", "agent_type": "coordinator", "agent_id": "root"}):
            with patch.object(context, "read_event", return_value=event), patch.object(context, "root_for", return_value=ROOT), patch.object(context, "query") as query, patch.object(context, "safe_state") as state:
                self.assertEqual(0, context.main())
                query.assert_not_called()
                state.assert_not_called()

    def test_unavailable_runtime_and_malformed_event_fail_open(self):
        with patch.object(context, "read_event", side_effect=ValueError("bad input")), patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(0, context.main())

    def test_disabled_or_below_threshold_meter_does_not_write_handoff(self):
        for limits, tokens in (({"enabled": False, "threshold_tokens": 50}, 100),
                               ({"enabled": True, "threshold_tokens": 50}, 49)):
            event = {"role": "executor", "agent_id": "worker", "context_tokens": tokens}
            with patch.object(context, "read_event", return_value=event), patch.object(context, "root_for", return_value=ROOT), patch.object(context, "query", return_value=limits) as query, patch.object(context, "advisory") as advisory:
                self.assertEqual(0, context.main())
                self.assertEqual(1, query.call_count)
                advisory.assert_not_called()

    def test_transcript_meter_uses_latest_usage_not_cumulative_history(self):
        with tempfile.TemporaryDirectory() as folder:
            transcript = Path(folder) / "meter.jsonl"
            records = [{"usage": {"input_tokens": 999999}}, {"message": {"usage": {
                "input_tokens": 10, "cache_creation_input_tokens": 20,
                "cache_read_input_tokens": 30, "output_tokens": 40}}}]
            transcript.write_text("\n".join(json.dumps(record) for record in records) + "\nmalformed tail\n")
            self.assertEqual(100, context.context_tokens({"transcript_path": str(transcript)}))

    def test_each_worker_kind_receives_its_own_continuation_method(self):
        for role, expected in (("executor", "safe committed boundary"),
                               ("planner", "partial assigned artifact"),
                               ("code-reviewer", "examined scope")):
            event = {"role": role, "agent_id": "worker", "session_id": "../unsafe/id", "context_tokens": 100}
            with patch.object(context, "read_event", return_value=event), patch.object(context, "root_for", return_value=ROOT), patch.object(context, "query", side_effect=[{"enabled": True, "threshold_tokens": 100}, {"written": True}]) as query, patch.object(context, "advisory") as advisory:
                self.assertEqual(0, context.main())
                args = query.call_args_list[1].args
                self.assertNotIn("/", args[2])
                self.assertIn(role, args)
                self.assertIn(expected, advisory.call_args.args[1])

    def test_bad_meter_or_runtime_failure_is_warning_only(self):
        event = {"role": "executor", "agent_id": "worker", "usage": "invalid"}
        for failure in (ValueError("runtime unavailable"), {"enabled": True, "threshold_tokens": "invalid"}):
            with patch.object(context, "read_event", return_value=event), patch.object(context, "root_for", return_value=ROOT), patch.object(context, "query", side_effect=failure if isinstance(failure, Exception) else None, return_value=failure), patch("sys.stderr", new=io.StringIO()) as stderr:
                self.assertEqual(0, context.main())
                self.assertIn("NOTICE", stderr.getvalue())

    def test_prefixed_reviewer_uses_review_handoff_and_invalid_direct_meter_fails_open(self):
        event = {"agent_type": "plugin:workflow:code-reviewer", "agent_id": "worker", "context_tokens": 100}
        with patch.object(context, "read_event", return_value=event), patch.object(context, "root_for", return_value=ROOT), patch.object(context, "query", side_effect=[{"enabled": True, "threshold_tokens": 100}, {}]) as query, patch.object(context, "advisory") as advisory:
            self.assertEqual(0, context.main())
            self.assertIn("code-reviewer", query.call_args_list[1].args)
            self.assertIn("examined scope", advisory.call_args.args[1])
        for value in (True, -1, float("inf"), "100"):
            event["context_tokens"] = value
            with patch.object(context, "read_event", return_value=event), patch.object(context, "root_for", return_value=ROOT), patch.object(context, "query", return_value={"enabled": True, "threshold_tokens": 100}) as query, patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(0, context.main())
                self.assertEqual(1, query.call_count)


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
        with patch.object(integrity, "read_event", return_value=event), patch.object(integrity, "root_for", return_value=ROOT), patch.object(integrity, "snapshot"), patch.object(integrity, "query", side_effect=[{"valid": True}, {"warnings": ["drift"]}]), patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(0, integrity.main())

    def test_unavailable_or_malformed_integrity_result_never_authorizes_commit(self):
        event = {"tool_name": "Bash", "tool_input": {"command": "git commit -m bounded"}}
        for result in ({}, [], {"valid": "true"}, {"valid": True, "errors": ["schema"]}):
            with self.subTest(result=result), patch.object(integrity, "read_event", return_value=event), patch.object(integrity, "root_for", return_value=ROOT), patch.object(integrity, "snapshot"), patch.object(integrity, "query", return_value=result), patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(2, integrity.main())

    def test_quoted_examples_and_non_commit_subcommands_are_not_gates(self):
        for command in ("echo git commit", "printf '%s' 'git commit'", "git show commit", "git -c alias.c=commit status", "git log --grep commit"):
            self.assertFalse(integrity.prospective_commit(command), command)
        self.assertTrue(integrity.prospective_commit(["git", "-C", "..", "commit", "--only", "--", ".planning/STATE.md"]))
        self.assertTrue(integrity.prospective_commit("git status && git commit -am bounded"))

    def test_commit_selection_distinguishes_index_all_only_and_include(self):
        cases = ((["-m", "bounded"], (False, False, False, [])),
                 (["-am", "bounded"], (False, False, True, [])),
                 (["--only", "-m", "bounded", "--", ".planning/STATE.md"], (True, False, False, [".planning/STATE.md"])),
                 (["-m", "bounded", ".planning/STATE.md"], (True, False, False, [".planning/STATE.md"])),
                 (["--include", "--", ".planning/STATE.md"], (False, True, False, [".planning/STATE.md"])))
        for arguments, expected in cases:
            self.assertEqual(expected, integrity.commit_selection(arguments))
        with self.assertRaises(ValueError):
            integrity.commit_selection(["--pathspec-from-file=unreviewed"])


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

    def test_remove_refuses_a_different_worktree_without_git_mutation(self):
        event = {"name": "worker", "hook_event_name": "WorktreeRemove", "worktree_path": str(ROOT.parent / "outside")}
        with tempfile.TemporaryDirectory() as folder, patch.object(location, "read_event", return_value=event), patch.object(location, "root_for", return_value=Path(folder)), patch.object(location.subprocess, "run") as run, patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(2, location.main())
            run.assert_not_called()

    def test_reparse_location_refuses_before_creating_any_directory(self):
        event = {"name": "worker", "hook_event_name": "WorktreeCreate"}
        with tempfile.TemporaryDirectory() as folder, patch.object(location, "read_event", return_value=event), patch.object(location, "root_for", return_value=Path(folder)), patch.object(location, "reparse", return_value=True), patch.object(location.subprocess, "run") as run, patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(2, location.main())
            self.assertEqual([], list(Path(folder).iterdir()))
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
