"""Exercise the native Claude boundary without authentication or model calls."""

import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("claude_worker", ROOT / ".ai/runtime/claude_worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def success(result="Complete report — café", **changes):
    value = {"type": "result", "subtype": "success", "is_error": False,
             "result": result, "permission_denials": []}
    value.update(changes)
    return json.dumps(value, ensure_ascii=False)


class ClaudeWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="claude adapter ")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.checkout = self.base / "assigned checkout"
        self.checkout.mkdir()
        self.cwd = patch.object(worker.Path, "cwd", return_value=self.checkout)
        self.cwd.start()
        self.addCleanup(self.cwd.stop)
        self.environment = patch.dict(os.environ, {"PHASE_MAX_TURNS": "40"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.result = self.base / "verification.md"
        self.prompt = "Full assignment\n\nUnicode: café 日本語\n" + "detail\n" * 12000

    def native(self, output=None, returncode=0, **kwargs):
        return patch.object(worker.subprocess, "run", return_value=subprocess.CompletedProcess(
            ["claude"], returncode, success() if output is None else output,
            "private native diagnostic"), **kwargs)

    def test_component_preserves_summary_and_forwards_full_assignment(self):
        summary = self.checkout / "SUMMARY.md"
        for kind in ("code", "documentation"):
            with self.subTest(kind=kind):
                summary.write_text("Committed component summary", encoding="utf-8")
                with self.native() as launch:
                    result = worker.execute(kind, str(summary), self.prompt)
                self.assertEqual(result, "Complete report — café")
                self.assertEqual(summary.read_text(encoding="utf-8"), "Committed component summary")
                argv = launch.call_args.args[0]
                self.assertEqual(argv, ["claude", "-p", "--output-format", "json",
                                        "--no-session-persistence", "--max-turns", "40",
                                        "--disallowedTools", "Agent,Task"])
                options = launch.call_args.kwargs
                self.assertTrue(options["input"].startswith(self.prompt))
                self.assertIn("40 agentic turns", options["input"][len(self.prompt):])
                self.assertEqual(options["cwd"], self.checkout)
                self.assertEqual(options["encoding"], "utf-8")
                self.assertNotIn("start_new_session", options)
                self.assertNotIn("creationflags", options)
                self.assertNotIn("shell", options)

    def test_component_does_not_create_summary_from_response(self):
        summary = self.checkout / "SUMMARY.md"
        with self.native():
            worker.execute("code", str(summary), self.prompt)
        self.assertFalse(summary.exists())

    def test_real_child_process_receives_utf8_stdin_and_assigned_cwd(self):
        native_run = subprocess.run
        program = ("import json, os, sys; "
                   "sys.stdin.reconfigure(encoding='utf-8'); "
                   "sys.stdout.reconfigure(encoding='utf-8'); "
                   "result=json.dumps({'prompt':sys.stdin.read(), 'cwd':os.getcwd(), "
                   "'argv':sys.argv[1:]}, ensure_ascii=False); "
                   "print(json.dumps({'type':'result', 'subtype':'success', "
                   "'is_error':False, 'result':result}, ensure_ascii=False))")
        def launch(argv, **kwargs):
            return native_run([sys.executable, "-c", program, *argv[1:]], **kwargs)
        with patch.object(worker.subprocess, "run", side_effect=launch):
            result = json.loads(worker.execute("code", str(self.result), self.prompt))
        self.assertTrue(result["prompt"].startswith(self.prompt))
        self.assertIn("40 agentic turns", result["prompt"][len(self.prompt):])
        self.assertEqual(Path(result["cwd"]), self.checkout)
        self.assertEqual(result["argv"], ["-p", "--output-format", "json",
                                          "--no-session-persistence", "--max-turns", "40",
                                          "--disallowedTools", "Agent,Task"])

    def test_managed_adapter_records_native_process_identity(self):
        import yaml
        receipt = self.base / "native.yaml"
        native_popen = subprocess.Popen
        program = "import json,sys; sys.stdin.read(); print(json.dumps({'type':'result','subtype':'success','is_error':False,'result':'done'}))"
        def launch(argv, **kwargs):
            return native_popen([sys.executable, "-c", program], **kwargs)
        with patch.dict(os.environ, {"PHASE_NATIVE_RECEIPT": str(receipt)}), \
                patch.object(sys, "path", [str(ROOT / ".ai/runtime"), *sys.path]), \
                patch.object(worker.subprocess, "Popen", side_effect=launch):
            self.assertEqual(worker.execute("code", str(self.result), self.prompt), "done")
        data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "finished")
        self.assertEqual(data["returncode"], 0)
        self.assertIsInstance(data["pid"], int)
        self.assertTrue(data["process_identity"])

    def test_stopped_adapter_does_not_hide_live_native_process(self):
        with patch.object(sys, "path", [str(ROOT / ".ai/runtime"), *sys.path]):
            from phase_runner import atomic_yaml, process_identity, require_stopped
            from phase_records import PhaseError
        receipt = self.base / "supervisor.yaml"
        atomic_yaml(receipt, {"status": "finished", "returncode": 1})
        native = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        try:
            atomic_yaml(receipt.with_suffix(".native.yaml"), {
                "status": "running", "pid": native.pid, "process_identity": process_identity(native.pid),
            })
            with self.assertRaisesRegex(PhaseError, "still running"):
                require_stopped({"status": "blocked", "receipt": str(receipt)})
        finally:
            native.kill()
            native.wait(timeout=10)
        require_stopped({"status": "blocked", "receipt": str(receipt)})

    def test_review_routes_capture_external_report_and_restrict_tools(self):
        for kind, status in (("verifier", "passed"), ("code-reviewer", "clean")):
            with self.subTest(kind=kind):
                result_path = self.base / (kind + ".md")
                report = f"---\nstatus: {status}\n---\n\n# Findings\n\nRévision verified.\n"
                with self.native(success(report)) as launch:
                    self.assertEqual(worker.execute(kind, str(result_path), self.prompt), report)
                self.assertEqual(result_path.read_bytes(), report.encode("utf-8"))
                argv = launch.call_args.args[0]
                self.assertEqual(argv[argv.index("--tools") + 1], "Read,Glob,Grep")
                self.assertEqual(argv[argv.index("--disallowedTools") + 1], "Agent,Task,mcp__*")
                self.assertIn("read-only reviewer", argv[-1])
                self.assertEqual(list(self.checkout.iterdir()), [])
                for forbidden in ("--bare", "--dangerously-skip-permissions", "--permission-mode",
                                  "--allowedTools", "--model", "--worktree"):
                    self.assertNotIn(forbidden, argv)

    def test_configured_turn_limit_is_forwarded_and_invalid_limits_do_not_launch(self):
        for limit in ("1", "80", "200"):
            with self.subTest(limit=limit), patch.dict(os.environ, {"PHASE_MAX_TURNS": limit}), self.native() as launch:
                worker.execute("code", str(self.result), self.prompt)
                argv = launch.call_args.args[0]
                self.assertEqual(argv[argv.index("--max-turns") + 1], limit)
                self.assertIn(limit + " agentic turns", launch.call_args.kwargs["input"])
        for limit in ("0", "201", "-1", "1.5", "", "true"):
            with self.subTest(limit=limit), patch.dict(os.environ, {"PHASE_MAX_TURNS": limit}), self.native() as launch:
                with self.assertRaisesRegex(worker.AdapterError, "PHASE_MAX_TURNS"):
                    worker.execute("code", str(self.result), self.prompt)
                launch.assert_not_called()

    def test_invalid_verifier_destinations_do_not_launch(self):
        self.result.write_text("Existing evidence", encoding="utf-8")
        for kind in ("verifier", "code-reviewer"):
            for result in (self.checkout / "report.md", self.result,
                           self.base / "missing" / "report.md", self.checkout):
                with self.subTest(kind=kind, result=result), self.native() as launch:
                    with self.assertRaises(worker.AdapterError):
                        worker.execute(kind, str(result), self.prompt)
                    launch.assert_not_called()
        self.assertEqual(self.result.read_text(encoding="utf-8"), "Existing evidence")

    def test_result_created_during_run_is_preserved(self):
        def native(*args, **kwargs):
            self.result.write_text("Other evidence", encoding="utf-8")
            return subprocess.CompletedProcess(args[0], 0, success(), "")
        with patch.object(worker.subprocess, "run", side_effect=native):
            with self.assertRaisesRegex(worker.AdapterError, "Could not save"):
                worker.execute("verifier", str(self.result), self.prompt)
        self.assertEqual(self.result.read_text(encoding="utf-8"), "Other evidence")

    def test_failed_native_results_never_create_report(self):
        examples = ["not JSON", "[]", "{}", success(is_error=True),
                    success(subtype="error_max_turns"), success(is_error="false"),
                    success(result="  \n"), success(result=None),
                    success(permission_denials=[{"tool_name": "Edit"}]),
                    success(permission_denials="invalid")]
        for output in examples:
            with self.subTest(output=output), self.native(output):
                with self.assertRaises(worker.AdapterError):
                    worker.execute("verifier", str(self.result), self.prompt)
                self.assertFalse(self.result.exists())
        with self.native(success(), returncode=7):
            with self.assertRaisesRegex(worker.AdapterError, "status 7"):
                worker.execute("verifier", str(self.result), self.prompt)
        self.assertFalse(self.result.exists())

    def test_missing_command_and_bad_encoding_are_actionable_failures(self):
        cases = [(FileNotFoundError(), "Install Claude Code"),
                 (UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"), "UTF-8")]
        for error, message in cases:
            with self.subTest(error=error), patch.object(worker.subprocess, "run", side_effect=error):
                with self.assertRaisesRegex(worker.AdapterError, message):
                    worker.execute("verifier", str(self.result), self.prompt)
                self.assertFalse(self.result.exists())

    def test_output_write_error_removes_partial_report(self):
        original_open = Path.open
        class FailingOutput:
            def __enter__(self):
                self.file = original_open(self_destination, "x", encoding="utf-8")
                return self
            def write(self, text):
                self.file.write("partial")
                raise OSError("disk full")
            def __exit__(self, *args):
                self.file.close()
        self_destination = self.result
        with self.native(), patch.object(worker.Path, "open", return_value=FailingOutput()):
            with self.assertRaisesRegex(worker.AdapterError, "Could not save"):
                worker.execute("verifier", str(self.result), self.prompt)
        self.assertFalse(self.result.exists())

    def test_empty_assignment_does_not_launch(self):
        with self.native() as launch:
            with self.assertRaisesRegex(worker.AdapterError, "assignment.*empty"):
                worker.execute("code", str(self.result), " \n")
            launch.assert_not_called()

    def test_main_emits_result_or_safe_error_with_exit_code(self):
        for returncode in (0, 12):
            with self.subTest(returncode=returncode), self.native(returncode=returncode), \
                    patch.object(worker.sys, "stdin", io.StringIO(self.prompt)), \
                    patch.object(worker.sys, "stdout", io.StringIO()) as stdout, \
                    patch.object(worker.sys, "stderr", io.StringIO()) as stderr:
                code = worker.main(["--kind", "code", "--result", str(self.result)])
                self.assertEqual(code, 0 if returncode == 0 else 1)
                prefix = "Claude usage (reported totals, not peak context): {}\n"
                if returncode == 0:
                    self.assertEqual(stdout.getvalue(), prefix + "Complete report — café\n")
                else:
                    self.assertEqual(stdout.getvalue(), prefix)
                    self.assertIn("status 12", stderr.getvalue())
                    self.assertNotIn("private native diagnostic", stderr.getvalue())
                    self.assertNotIn("Full assignment", stderr.getvalue())

    def test_usage_output_keeps_numeric_metrics_without_native_diagnostics(self):
        output = success(num_turns=3, duration_ms=1500, total_cost_usd=0.12,
                         usage={"input_tokens": 32, "output_tokens": 9,
                                "private": "private diagnostic", "invalid": True})
        with self.native(output), patch.object(worker.sys, "stdout", io.StringIO()) as stdout:
            worker.execute("code", str(self.result), self.prompt)
        payload = stdout.getvalue().split(": ", 1)[1]
        self.assertEqual(json.loads(payload), {"num_turns": 3, "duration_ms": 1500,
            "total_cost_usd": 0.12, "usage": {"input_tokens": 32, "output_tokens": 9}})

    def test_turn_exhaustion_returns_handoff_instead_of_failure(self):
        output = success(subtype="error_max_turns", is_error=True)
        for kind in ("code", "documentation"):
            with self.subTest(kind=kind), self.native(output, returncode=1), \
                    patch.object(worker.sys, "stdin", io.StringIO(self.prompt)), \
                    patch.object(worker.sys, "stdout", io.StringIO()), \
                    patch.object(worker.sys, "stderr", io.StringIO()):
                self.assertEqual(worker.main(["--kind", kind, "--result", str(self.result)]), 75)
                self.assertFalse(self.result.exists())

    def test_permission_denials_and_other_failures_are_not_capacity_handoffs(self):
        for output in (success(subtype="error_max_turns", is_error=True, permission_denials=[{"tool": "Write"}]),
                       success(subtype="error_during_execution", is_error=True), "invalid json"):
            with self.subTest(output=output), self.native(output, returncode=1), \
                    patch.object(worker.sys, "stdin", io.StringIO(self.prompt)), \
                    patch.object(worker.sys, "stdout", io.StringIO()), \
                    patch.object(worker.sys, "stderr", io.StringIO()):
                self.assertEqual(worker.main(["--kind", "code", "--result", str(self.result)]), 1)


if __name__ == "__main__":
    unittest.main()
