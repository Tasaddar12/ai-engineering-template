"""Reusable check evidence exercised through real runtime subprocesses and Git."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".ai/runtime/phase.py"

CHECK = '''import json, os, pathlib, sys, time
root = pathlib.Path.cwd()
out = root / ".generated"
out.mkdir(exist_ok=True)
name, mode = sys.argv[1:3]
counter = out / (name + ".count")
counter.write_text(str(int(counter.read_text()) + 1 if counter.exists() else 1))
start = time.time()
if mode == "parallel":
    (out / (name + ".started")).write_text("yes")
    deadline = time.time() + 5
    while not (out / (sys.argv[3] + ".started")).exists():
        if time.time() > deadline: sys.exit(3)
        time.sleep(0.02)
if mode == "resource":
    lock = out / "resource.lock"
    with lock.open("x") as handle: handle.write(name)
    time.sleep(0.15)
    lock.unlink()
if mode == "sleep": time.sleep(float(sys.argv[3]))
if mode == "mutate": (root / "input.txt").write_text("changed")
if mode == "conditional-mutate" and (out / "mutation-enabled").exists():
    (root / "input.txt").write_text("changed")
if mode == "restore":
    original = (root / "input.txt").read_text()
    (root / "input.txt").write_text("temporary change")
    time.sleep(0.01)
    (root / "input.txt").write_text(original)
if mode == "mutate-dependency": (out / "deps/package").write_text("changed")
if mode == "output":
    print("A" * 12000 + "stdout-end", flush=True)
    print("B" * 11000 + "stderr-end", file=sys.stderr, flush=True)
else:
    print("ran " + name, flush=True)
    print("environment=" + os.environ.get("CHECK_ENV", "unset"), flush=True)
if mode == "timeout":
    print("before timeout", flush=True)
    time.sleep(5)
(out / (name + ".interval")).write_text(json.dumps([start, time.time()]))
if mode == "fail": sys.exit(7)
'''


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Receipt Test")
        self.git("config", "user.email", "receipt@example.invalid")
        (self.root / ".planning").mkdir()
        self.write(".gitignore", ".generated/\n.planning/verification-receipts/\n")
        self.write("input.txt", "initial")
        self.write("check.py", CHECK)
        self.configure([self.command()])
        self.git("add", "--", ".gitignore", "input.txt", "check.py", ".planning/config.yaml")
        self.git("commit", "-qm", "initial")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True,
                              check=True, text=True).stdout.strip()

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def command(self, name="check", mode="pass", *args):
        return [sys.executable, "check.py", name, mode, *args]

    def configure(self, commands, **options):
        self.write(".planning/config.yaml", yaml.safe_dump({"verification": dict(commands=commands, **options)}))

    def run_checks(self, environment=None, ok=True):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        if environment:
            env.update(environment)
        process = subprocess.run([sys.executable, str(RUNTIME), "query", "verification.run-checks"],
                                 cwd=self.root, env=env, capture_output=True, text=True,
                                 encoding="utf-8", timeout=30)
        self.assertNotIn("Traceback", process.stderr)
        payload = json.loads(process.stdout)
        self.assertEqual(payload["ok"], ok, process.stdout + process.stderr)
        self.assertEqual(process.returncode, 0 if ok else 1)
        return payload

    def count(self, name="check"):
        return int((self.root / ".generated" / (name + ".count")).read_text())

    def receipt(self, result):
        return self.root / result["checks"][0]["receipt"]

    def test_legacy_reuse_retains_logs_and_original_revision(self):
        first = self.run_checks()
        second = self.run_checks()
        self.assertTrue(first["passed"])
        self.assertFalse(first["checks"][0]["reused"])
        self.assertTrue(second["checks"][0]["reused"])
        self.assertEqual(self.count(), 1)
        self.assertEqual(first["checks"][0]["tested_revision"], self.git("rev-parse", "HEAD"))
        self.assertEqual(first["checks"][0]["stdout_log"], second["checks"][0]["stdout_log"])

    def test_empty_configuration_preserved(self):
        self.configure([])
        result = self.run_checks()
        self.assertFalse(result["configured"])
        self.assertEqual(result["checks"], [])
        self.assertFalse((self.root / ".planning/verification-receipts").exists())

    def test_legacy_string_and_list_commands(self):
        self.configure(["git --version", ["git", "--version"]])
        self.assertTrue(self.run_checks()["passed"])
        self.assertTrue(all(check["reused"] for check in self.run_checks()["checks"]))

    def test_tracked_edit_add_delete_and_untracked_changes_invalidate(self):
        self.run_checks()
        for path, content in [("input.txt", "edited"), ("new.txt", "new"), ("new.txt", "edit")]:
            self.write(path, content)
            self.assertFalse(self.run_checks()["checks"][0]["reused"])
        (self.root / "input.txt").unlink()
        self.assertFalse(self.run_checks()["checks"][0]["reused"])
        (self.root / "new.txt").unlink()
        self.assertFalse(self.run_checks()["checks"][0]["reused"])
        self.assertEqual(self.count(), 6)

    def test_ignored_outputs_do_not_invalidate(self):
        self.run_checks()
        self.write(".generated/new-output", "output")
        self.assertTrue(self.run_checks()["checks"][0]["reused"])

    def test_installed_runtime_creates_local_receipt_ignore(self):
        self.write(".gitignore", ".generated/\n")
        result = self.run_checks()
        self.assertTrue(result["passed"])
        receipt = result["checks"][0]["receipt"]
        self.assertEqual(self.git("check-ignore", receipt), receipt)
        self.assertEqual(self.git("check-ignore", result["checks"][0]["stdout_log"]),
                         result["checks"][0]["stdout_log"])
        self.assertTrue(self.run_checks()["checks"][0]["reused"])

    def test_tracked_ignored_file_still_invalidates(self):
        self.write(".generated/dependency", "first")
        self.git("add", "-f", "--", ".generated/dependency")
        self.run_checks()
        self.write(".generated/dependency", "second")
        self.assertFalse(self.run_checks()["checks"][0]["reused"])

    def test_full_environment_changes_invalidate_without_exposing_values(self):
        first = self.run_checks({"CHECK_ENV": "private-first"})
        self.assertTrue(self.run_checks({"CHECK_ENV": "private-first"})["checks"][0]["reused"])
        self.assertFalse(self.run_checks({"CHECK_ENV": "private-second"})["checks"][0]["reused"])
        # Environment values belong in a log only if the command itself prints them.
        document = json.loads(self.receipt(first).read_text())
        self.assertNotIn("private-first", json.dumps(document["receipt"]["inputs"]))

    def test_scoped_sources_and_environment_allow_only_declared_reuse(self):
        self.configure([{"command": self.command(), "sources": ["input.txt"], "environment": ["CHECK_ENV"]}])
        self.run_checks({"CHECK_ENV": "same", "UNRELATED_ENV": "a"})
        self.write("other.txt", "irrelevant")
        self.assertTrue(self.run_checks({"CHECK_ENV": "same", "UNRELATED_ENV": "b"})["checks"][0]["reused"])
        self.assertFalse(self.run_checks({"CHECK_ENV": "changed"})["checks"][0]["reused"])
        self.write("input.txt", "relevant")
        self.assertFalse(self.run_checks({"CHECK_ENV": "changed"})["checks"][0]["reused"])

    def test_explicit_directory_includes_ignored_dependencies_and_additions(self):
        self.configure([{"command": self.command(), "sources": [".generated/deps"]}])
        self.write(".generated/deps/package", "v1")
        self.run_checks()
        self.write(".generated/deps/package", "v2")
        self.assertFalse(self.run_checks()["checks"][0]["reused"])
        self.write(".generated/deps/new", "new")
        self.assertFalse(self.run_checks()["checks"][0]["reused"])

    def test_configuration_change_invalidates_same_argv_with_scoped_sources(self):
        entry = {"command": self.command(), "sources": ["input.txt"]}
        self.configure([entry], max_parallel=2)
        self.run_checks()
        self.configure([entry], max_parallel=3)
        self.assertFalse(self.run_checks()["checks"][0]["reused"])

    def test_exact_revision_option_invalidates_empty_commit(self):
        self.configure([{"command": self.command(), "revision": True}])
        self.run_checks()
        self.git("commit", "--allow-empty", "-qm", "new revision")
        self.assertFalse(self.run_checks()["checks"][0]["reused"])

    def test_content_reuse_preserves_original_revision_on_empty_commit(self):
        original = self.run_checks()["checks"][0]["tested_revision"]
        self.git("commit", "--allow-empty", "-qm", "new revision")
        result = self.run_checks()
        self.assertTrue(result["checks"][0]["reused"])
        self.assertEqual(result["checks"][0]["tested_revision"], original)
        self.assertNotEqual(result["tested_revision"], original)

    def test_changed_argv_invalidates(self):
        self.run_checks()
        self.configure([self.command("different")])
        self.assertFalse(self.run_checks()["checks"][0]["reused"])
        self.assertEqual(self.count("different"), 1)

    def test_corrupt_receipt_and_changed_logs_are_cache_misses(self):
        first = self.run_checks()
        self.receipt(first).write_text("{corrupt", encoding="utf-8")
        second = self.run_checks()
        self.assertFalse(second["checks"][0]["reused"])
        self.write(second["checks"][0]["stdout_log"], "tampered")
        third = self.run_checks()
        self.assertFalse(third["checks"][0]["reused"])
        self.assertEqual(self.count(), 3)
        self.assertTrue((self.root / first["checks"][0]["stderr_log"]).exists())

    def test_missing_log_and_receipt_checksum_mismatch_are_cache_misses(self):
        first = self.run_checks()
        (self.root / first["checks"][0]["stdout_log"]).unlink()
        second = self.run_checks()
        document = json.loads(self.receipt(second).read_text())
        document["receipt"]["result"]["stdout_tail"] = "modified"
        self.receipt(second).write_text(json.dumps(document), encoding="utf-8")
        self.assertFalse(self.run_checks()["checks"][0]["reused"])
        self.assertEqual(self.count(), 3)

    def test_failures_are_logged_and_never_reused(self):
        self.configure([self.command(mode="fail")])
        for _ in range(2):
            result = self.run_checks()
            self.assertFalse(result["passed"])
            check = result["checks"][0]
            self.assertEqual(check["exit_code"], 7)
            self.assertFalse(check["reused"])
            self.assertTrue((self.root / check["stdout_log"]).is_file())
        self.assertEqual(self.count(), 2)

    def test_timeout_retains_partial_output_and_reruns(self):
        self.configure([{"command": self.command(mode="timeout"), "timeout": 0.3}])
        for _ in range(2):
            result = self.run_checks()
            self.assertFalse(result["passed"])
            self.assertIsNone(result["checks"][0]["exit_code"])
            self.assertIn("timed out", result["checks"][0]["error"])
            self.assertIn("before timeout", (self.root / result["checks"][0]["stdout_log"]).read_text())
        self.assertEqual(self.count(), 2)

    def test_missing_executable_is_failure_with_logs(self):
        self.configure([["nonexistent-verification-executable-42"]])
        result = self.run_checks()
        self.assertFalse(result["passed"])
        self.assertIn("error", result["checks"][0])
        self.assertTrue((self.root / result["checks"][0]["stderr_log"]).is_file())

    def test_full_logs_and_compact_tails(self):
        self.configure([self.command(mode="output")])
        result = self.run_checks()["checks"][0]
        for stream, end in [("stdout", "stdout-end"), ("stderr", "stderr-end")]:
            self.assertGreater((self.root / result[stream + "_log"]).stat().st_size, 10000)
            self.assertLessEqual(len(result[stream + "_tail"]), 2000)
            self.assertIn(end, result[stream + "_tail"])

    def test_independent_checks_really_overlap_and_return_in_config_order(self):
        self.configure([{"command": self.command("a", "parallel", "b"), "independent": True},
                        {"command": self.command("b", "parallel", "a"), "independent": True}])
        result = self.run_checks()
        self.assertTrue(result["passed"], result)
        self.assertEqual([c["command"][2] for c in result["checks"]], ["a", "b"])
        a, b = [json.loads((self.root / ".generated" / (name + ".interval")).read_text()) for name in ("a", "b")]
        self.assertLess(max(a[0], b[0]), min(a[1], b[1]))

    def test_shared_resources_prevent_overlap(self):
        self.configure([{"command": self.command(name, "resource"), "independent": True,
                         "resources": ["database"]} for name in ("a", "b")])
        self.assertTrue(self.run_checks()["passed"])
        a, b = [json.loads((self.root / ".generated" / (name + ".interval")).read_text()) for name in ("a", "b")]
        self.assertLessEqual(a[1], b[0])

    def test_legacy_commands_form_serial_barriers(self):
        self.configure([{"command": self.command("a", "sleep", "0.1"), "independent": True},
                        self.command("legacy", "sleep", "0.1"),
                        {"command": self.command("b", "sleep", "0.1"), "independent": True}])
        self.assertTrue(self.run_checks()["passed"])
        intervals = [json.loads((self.root / ".generated" / (name + ".interval")).read_text())
                     for name in ("a", "legacy", "b")]
        self.assertLessEqual(intervals[0][1], intervals[1][0])
        self.assertLessEqual(intervals[1][1], intervals[2][0])

    def test_joined_failure_prevents_batch_acceptance(self):
        self.configure([{"command": self.command("a", "fail"), "independent": True},
                        {"command": self.command("b", "sleep", "0.15"), "independent": True}])
        result = self.run_checks()
        self.assertFalse(result["passed"])
        self.assertTrue(result["checks"][1]["passed"])
        self.assertTrue((self.root / ".generated/b.interval").exists())

    def test_mutation_invalidates_all_checks_including_previously_cached_pass(self):
        entries = [{"command": self.command("a"), "sources": ["check.py"]},
                   {"command": self.command("b", "conditional-mutate"), "independent": True}]
        self.configure(entries)
        self.assertTrue(self.run_checks()["passed"])
        # Rerun the mutator, preserving the first receipt; the full config remains unchanged.
        result = self.run_checks()
        (self.root / result["checks"][1]["receipt"]).unlink()
        self.write(".generated/mutation-enabled", "yes")
        result = self.run_checks()
        self.assertFalse(result["snapshot_valid"])
        self.assertTrue(all(not c["passed"] for c in result["checks"]))
        self.assertTrue(result["checks"][0]["reused"])

    def test_disable_reuse_forces_real_execution(self):
        self.configure([self.command()], reuse=False)
        self.run_checks()
        self.assertFalse(self.run_checks()["checks"][0]["reused"])
        self.assertEqual(self.count(), 2)

    def test_source_rewritten_to_original_content_invalidates_execution(self):
        self.configure([self.command(mode="restore")])
        result = self.run_checks()
        self.assertFalse(result["passed"])
        self.assertFalse(result["snapshot_valid"])
        self.assertEqual((self.root / "input.txt").read_text(), "initial")

    def test_explicit_ignored_dependency_mutation_invalidates_execution(self):
        self.write(".generated/deps/package", "initial")
        self.configure([{"command": self.command(mode="mutate-dependency"),
                         "sources": [".generated/deps"]}])
        result = self.run_checks()
        self.assertFalse(result["passed"])
        self.assertFalse(result["snapshot_valid"])

    def test_max_parallel_one_serializes_independent_checks(self):
        self.configure([{"command": self.command(name, "sleep", "0.1"), "independent": True}
                        for name in ("a", "b")], max_parallel=1)
        self.assertTrue(self.run_checks()["passed"])
        a, b = [json.loads((self.root / ".generated" / (name + ".interval")).read_text()) for name in ("a", "b")]
        self.assertLessEqual(a[1], b[0])

    def test_per_check_reuse_false_reruns_only_volatile_check(self):
        self.configure([{"command": self.command("stable")},
                        {"command": self.command("volatile"), "reuse": False}])
        self.run_checks()
        result = self.run_checks()
        self.assertTrue(result["checks"][0]["reused"])
        self.assertFalse(result["checks"][1]["reused"])
        self.assertEqual(self.count("stable"), 1)
        self.assertEqual(self.count("volatile"), 2)

    def test_invalid_mapping_configuration_is_handled(self):
        for entry in [{"command": self.command(), "sources": ["../escape"]},
                      {"command": self.command(), "sources": []},
                      {"command": self.command(), "independent": "true"},
                      {"command": self.command(), "timeout": -1},
                      {"command": self.command(), "unknown": True}]:
            with self.subTest(entry=entry):
                self.configure([entry])
                self.assertEqual(self.run_checks(ok=False)["code"], "bad-config")


if __name__ == "__main__":
    unittest.main()
