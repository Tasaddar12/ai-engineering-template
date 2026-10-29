"""Real process execution with deterministic local substitutes for paid host CLIs."""
import importlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import unittest
from unittest import mock

try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE

LIB = SOURCE / "engineer/bin/lib"
if "engineer_bin_lib" not in sys.modules:
    spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB / "__init__.py", submodule_search_locations=[str(LIB)])
    package = importlib.util.module_from_spec(spec)
    sys.modules["engineer_bin_lib"] = package
    spec.loader.exec_module(package)
processes = importlib.import_module("engineer_bin_lib.processes")

FAKE_HOST = r'''
import json, os, pathlib, re, subprocess, sys, time
prompt = sys.stdin.read()
if "SLEEP_HOST" in prompt:
    time.sleep(60)
if "FAIL_HOST" in prompt:
    print("deliberate host failure", file=sys.stderr)
    raise SystemExit(7)
if "pipeline_id" not in prompt:
    print("FAKE_HOST_OK:" + prompt)
    raise SystemExit(0)
line = next(line for line in prompt.splitlines() if line.startswith('{"pipeline_id":'))
identity = json.loads(line)
pathlib.Path(identity["task_id"] + ".txt").write_text("implemented local fixture\n", encoding="utf-8")
subprocess.run(["git", "add", "--", identity["task_id"] + ".txt"], check=True)
subprocess.run(["git", "commit", "-m", "test: committed fake host work"], check=True)
head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
print("ENGINEER_OUTCOME:" + json.dumps({**{k: identity[k] for k in ("pipeline_id", "task_id", "attempt_token")},
    "status": "implemented", "head": head, "reason": "Committed deterministic fixture work",
    "verification": {"status": "unverified", "evidence": []}}))
'''


@unittest.skipUnless(os.name == "nt" or sys.platform == "linux", "Owned supervision requires Linux or Windows")
class RuntimeProcessExecution(RuntimeCase):
    def setUp(self):
        super().setUp()
        directory = self.root / "fake-host"
        directory.mkdir()
        self.binary = directory / ("codex.exe" if os.name == "nt" else "codex")
        # A real interpreter executable with the allowed host name: no shell,
        # subprocess mocking, host credentials, network calls, or provider charges.
        if os.name == "nt":
            executable = Path(sys.base_prefix) / "python.exe"
            if not executable.is_file():
                executable = Path(sys.executable)
            shutil.copy2(executable, self.binary)
            for pattern in ("python*.dll", "vcruntime*.dll"):
                for dependency in executable.parent.glob(pattern):
                    shutil.copy2(dependency, directory / dependency.name)
        else:
            self.binary.symlink_to(sys.executable)
        self.env["PYTHONHOME"] = sys.prefix
        self.argv = [str(self.binary), "-c", FAKE_HOST, "exec", "-"]

    def test_pipeline_commits_two_tasks_in_dependency_order_and_reuses_terminal_state(self):
        tasks = [{"id": "first", "prompt": "First local implementation"},
                 {"id": "second", "prompt": "Second local implementation", "depends_on": ["first"]}]
        created = self.cli("pipeline.create", "--id", "positive", "--tasks", json.dumps(tasks))
        result = self.cli("pipeline.run", "positive", "--host", "codex", "--command-json", json.dumps(self.argv))
        self.assertEqual("completed_unverified", result["status"], result)
        self.assertNotEqual(created["head"], result["head"])
        self.assertEqual(["implemented_unverified"] * 2, [task["status"] for task in result["tasks"]])
        for task in result["tasks"]:
            attempt = task["attempts"][0]
            self.assertTrue(attempt["process_terminal"]["tree_stopped"])
            self.assertEqual(task["head"], json.loads(Path(attempt["receipt"]).read_text(encoding="utf-8"))["head"])
            self.assertEqual("", self.git("-C", attempt["path"], "status", "--porcelain"))
        resumed = self.cli("pipeline.resume", "positive")
        self.assertEqual([1, 1], [len(task["attempts"]) for task in resumed["tasks"]])
        self.assertEqual(result["head"], resumed["head"])

    def test_pipeline_nonzero_host_blocks_dependent_work_with_terminal_proof(self):
        tasks = [{"id": "first", "prompt": "FAIL_HOST"}, {"id": "second", "prompt": "Must remain unlaunched", "depends_on": ["first"]}]
        self.cli("pipeline.create", "--id", "failure", "--tasks", json.dumps(tasks))
        result = self.cli("pipeline.run", "failure", "--host", "codex", "--command-json", json.dumps(self.argv))
        self.assertEqual(["failed", "blocked"], [task["status"] for task in result["tasks"]])
        attempt = result["tasks"][0]["attempts"][0]
        self.assertEqual(7, attempt["exit_code"])
        self.assertTrue(attempt["retry_safe"])
        self.assertTrue(attempt["process_terminal"]["tree_stopped"])
        self.assertEqual([], result["tasks"][1]["attempts"])

    def test_host_exec_runs_owned_request_and_rejects_duplicate_launch(self):
        worker = self.root / "worker"
        self.git("worktree", "add", "-b", "fixture-worker", str(worker))
        self.put(".planning/config.yaml", json.dumps({"agents": {"executor": {"model": "inherit", "effort": "inherit"}},
            "execution": {"hosts": {"codex": {"command": str(self.binary), "args": self.argv[1:]}}}}))
        packet = self.cli("dispatch-isolation", "--host", "codex", "--cwd-target", worker, "--prompt", "Owned café prompt")
        execution = packet["exec"]
        self.assertIsNotNone(execution, packet)
        request = json.loads(Path(execution["request"]).read_text(encoding="utf-8"))
        self.assertEqual(self.binary.resolve(), Path(request["command"]).resolve())
        result = subprocess.run([execution["command"], *execution["args"]], cwd=worker, env=self.env,
                                text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("FAKE_HOST_OK:Owned café prompt", result.stdout)
        receipt = json.loads(Path(execution["terminal_receipt"]).read_text(encoding="utf-8"))
        self.assertEqual(0, receipt["exit_code"])
        self.assertTrue(receipt["process_terminal"]["tree_stopped"])
        duplicate = subprocess.run([execution["command"], *execution["args"]], cwd=worker, env=self.env,
                                   text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertNotEqual(0, duplicate.returncode)
        self.assertIn("dispatch-already-started", duplicate.stderr)

    def test_wrong_config_suffix_cannot_pass_fake_host_launch_guard(self):
        worker = self.root / "worker"
        self.git("worktree", "add", "-b", "fixture-worker", str(worker))
        self.put(".planning/config.json", json.dumps({"execution": {"hosts": {"codex": {"command": str(self.binary)}}}}))
        packet = self.cli("dispatch-isolation", "--host", "codex", "--cwd-target", worker, "--prompt", "No host may launch")
        if packet["exec"] is not None:
            request = json.loads(Path(packet["exec"]["request"]).read_text(encoding="utf-8"))
            self.assertNotEqual(self.binary.resolve(), Path(request["command"]).resolve())
        # Deliberately no execution: a missing/wrong config cannot satisfy the
        # explicit fake-executable assertion used before the positive launch.

    def test_owned_timeout_and_explicit_stop_confirm_descendant_termination(self):
        for mode in ("timeout", "cancelled"):
            with self.subTest(mode=mode), (self.root / (mode + ".out")).open("wb") as output:
                child = processes.start_owned([sys.executable, "-c", "import time; time.sleep(60)"], self.root,
                    env=self.env, stdout=output, stderr=output, timeout=0.3 if mode == "timeout" else 10)
                try:
                    if mode == "cancelled":
                        child.stop()
                    child.wait()
                    proof = processes.terminal(child.ownership)
                    self.assertEqual(mode, proof["reason"])
                    self.assertTrue(proof["tree_stopped"])
                finally:
                    child.close()

    def test_stop_reaps_live_grandchild_before_terminal_receipt(self):
        heartbeat = self.root / "grandchild-heartbeat"
        grandchild = "import pathlib,time; p=pathlib.Path(" + repr(str(heartbeat)) + "); " + "\nwhile True:\n p.write_text(str(time.time_ns())); time.sleep(0.03)\n"
        parent = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(grandchild) + "]); time.sleep(60)"
        with (self.root / "descendant.out").open("wb") as output:
            child = processes.start_owned([sys.executable, "-c", parent], self.root, env=self.env, stdout=output, stderr=output, timeout=10)
            try:
                deadline = time.monotonic() + 5
                while not heartbeat.exists() and time.monotonic() < deadline:
                    time.sleep(0.03)
                self.assertTrue(heartbeat.exists(), "Grandchild did not become active")
                child.stop()
                self.assertTrue(processes.terminal(child.ownership)["tree_stopped"])
                snapshot = heartbeat.read_bytes()
                time.sleep(0.15)
                self.assertEqual(snapshot, heartbeat.read_bytes(), "Grandchild continued after terminal proof")
            finally:
                child.close()

    @unittest.skipUnless(sys.platform == "linux", "Linux supervisor bootstrap regression")
    def test_stop_during_supervisor_bootstrap_preserves_terminal_proof(self):
        ready = self.root / "supervisor-bootstrap-ready"
        # Delay the real supervisor before it can install signal handlers. The
        # subprocess and supervisor remain real; only startup order is controlled.
        bootstrap = r'''
import pathlib, runpy, sys, time
script, request, ready = sys.argv[1:]
pathlib.Path(ready).touch()
deadline = time.monotonic() + 5
while not pathlib.Path(request).with_name("cancel.json").exists() and time.monotonic() < deadline:
    time.sleep(0.01)
time.sleep(0.1)
sys.argv = [script, request]
runpy.run_path(script, run_name="__main__")
'''
        real_popen = subprocess.Popen

        def launch(argv, **kwargs):
            self.assertEqual("process_supervisor.py", Path(argv[2]).name)
            return real_popen([argv[0], "-I", "-c", bootstrap, *argv[2:], str(ready)], **kwargs)

        with (self.root / "bootstrap.out").open("wb") as output:
            with mock.patch.object(processes.subprocess, "Popen", side_effect=launch):
                child = processes.start_owned([sys.executable, "-c", "import time; time.sleep(60)"], self.root,
                    env=self.env, stdout=output, stderr=output, timeout=10)
            try:
                deadline = time.monotonic() + 5
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(ready.exists(), "Supervisor bootstrap did not become active")
                child.stop()
                proof = processes.terminal(child.ownership)
                self.assertEqual("cancelled", proof["reason"])
                self.assertTrue(proof["tree_stopped"])
                self.assertIsNone(proof["error"])
                self.assertEqual(0, child.process.wait(timeout=5))
            finally:
                # Missing proof must retain the uncertain attempt and expose the
                # original stop failure rather than replace it with close().
                if (child.directory / "terminal.json").exists():
                    child.close()

    @unittest.skipUnless(sys.platform == "linux", "Linux supervisor cancellation protocol")
    def test_supervisor_ignores_cancellation_for_another_attempt(self):
        for changed in ("token", "request_hash"):
            with self.subTest(changed=changed), (self.root / (changed + ".out")).open("wb") as output:
                child = processes.start_owned([sys.executable, "-c", "import time; time.sleep(60)"], self.root,
                    env=self.env, stdout=output, stderr=output, timeout=0.3)
                try:
                    packet = {key: child.ownership[key] for key in ("token", "request_hash")}
                    packet.update({changed: "another-attempt", "reason": "cancelled"})
                    processes._new(child.directory / "cancel.json", processes._encoded(packet))
                    child.wait()
                    proof = processes.terminal(child.ownership)
                    self.assertEqual("timeout", proof["reason"])
                    self.assertTrue(proof["tree_stopped"])
                finally:
                    child.close()

    @unittest.skipUnless(sys.platform == "linux", "Linux supervisor cancellation protocol")
    def test_supervisor_ignores_invalid_cancellation_envelopes_until_timeout(self):
        envelopes = (("malformed", b"{"), ("list", b"[]"), ("null", b"null"), ("encoding", b"\xff"),
            ("integer-limit", b"9" * 5000), ("recursion-limit", b"[" * 10000 + b"0" + b"]" * 10000))
        for name, content in envelopes:
            with self.subTest(envelope=name), (self.root / (name + ".out")).open("wb") as output:
                child = processes.start_owned([sys.executable, "-c", "import time; time.sleep(5)"], self.root,
                    env=self.env, stdout=output, stderr=output, timeout=0.5)
                try:
                    processes._new(child.directory / "cancel.json", content)
                    child.wait()
                    proof = processes.terminal(child.ownership)
                    self.assertEqual("timeout", proof["reason"], proof)
                    self.assertGreaterEqual(time.monotonic(), child.deadline)
                    self.assertEqual(124, proof["exit_code"])
                    self.assertIsNone(proof["error"])
                    self.assertTrue(proof["tree_stopped"])
                finally:
                    child.close()

    @unittest.skipUnless(sys.platform == "linux", "Linux supervisor cancellation protocol")
    def test_supervisor_accepts_valid_cancellation_after_invalid_envelope(self):
        envelopes = (b"{", b"9" * 5000, b"[" * 10000 + b"0" + b"]" * 10000)
        for index, content in enumerate(envelopes):
            with self.subTest(envelope=index), (self.root / (str(index) + "-replacement.out")).open("wb") as output:
                child = processes.start_owned([sys.executable, "-c", "import time; time.sleep(5)"], self.root,
                    env=self.env, stdout=output, stderr=output, timeout=10)
                try:
                    cancellation = child.directory / "cancel.json"
                    processes._new(cancellation, content)
                    time.sleep(0.2)
                    self.assertIsNone(child.poll(), "Invalid envelope terminated the live attempt")
                    cancellation.unlink()
                    child.stop()
                    proof = processes.terminal(child.ownership)
                    self.assertEqual("cancelled", proof["reason"])
                    self.assertIsNone(proof["error"])
                    self.assertTrue(proof["tree_stopped"])
                finally:
                    child.close()


if __name__ == "__main__":
    unittest.main()
