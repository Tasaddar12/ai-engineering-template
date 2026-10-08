"""Real Git and subprocess regressions for provisional parallel chunk gates."""
import concurrent.futures
import json
import os
import shutil
import stat
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

RUNTIME = Path(__file__).resolve().parents[1] / ".ai" / "runtime"
sys.path.insert(0, str(RUNTIME))
from lib import pipeline
from lib.paths import Workspace
from lib.results import VerbError


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.git("init", "-b", "phase-test")
        self.git("config", "user.name", "Pipeline Test")
        self.git("config", "user.email", "pipeline@example.invalid")
        self.git("config", "core.hooksPath", str(self.root / "absent-hooks"))
        (self.root / ".gitignore").write_text("requests/\n__pycache__/\n")
        (self.root / "seed.txt").write_text("seed\n")
        self.git("add", ".gitignore", "seed.txt")
        self.git("commit", "-m", "base")
        self.base = self.git("rev-parse", "HEAD")
        self.ws = Workspace(self.root)

    def git(self, *args, cwd=None):
        result = subprocess.run(["git", *args], cwd=cwd or self.root,
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def spec(self, name="one", deps=None, resources=None, command=None):
        path = name + ".txt"
        (self.root / path).write_text(name + "\n")
        self.git("add", path)
        self.git("commit", "-m", name)
        return {"schema": 1, "chunk_id": name, "assignment_id": "assignment-" + name,
                "plan_id": "plan-" + name, "base": self.base,
                "head": self.git("rev-parse", "HEAD"), "owned_paths": [path],
                "deletions": [], "depends_on": deps or [], "acceptance": ["AC-1"],
                "resources": resources or [], "checks": [{"id": "check", "argv": command or
                [sys.executable, "-c", "print('observed check')"], "cwd": ".", "inputs": [path], "timeout": 10}]}

    def next_spec(self, name, **kwargs):
        self.base = self.git("rev-parse", "HEAD")
        return self.spec(name, **kwargs)

    def review(self, spec, **changes):
        report = {"schema": 1, "chunk_id": spec["chunk_id"], "assignment_id": spec["assignment_id"],
                  "sha": spec["head"], "base_sha": spec["base"], "status": "passed",
                  "acceptance": spec["acceptance"], "scope": spec["owned_paths"], "findings": [],
                  "evidence": ["checked chunk diff"], "provenance": {"source": "host", "reviewer": "independent"}}
        report.update(changes)
        return report

    def complete(self, spec):
        pipeline.prepare(self.ws, spec["chunk_id"])
        checks = pipeline.run_checks(self.ws, spec["chunk_id"], "test-host")
        self.assertTrue(checks["passed"], checks)
        pipeline.record_review(self.ws, spec["chunk_id"], self.review(spec))
        pipeline.integrate(self.ws, spec["chunk_id"], spec["head"])

    def test_paired_snapshots_are_immutable_as_author_advances(self):
        spec = self.spec()
        pipeline.register(self.ws, spec)
        prepared = pipeline.prepare(self.ws, "one")
        self.assertNotEqual(prepared["snapshots"]["test"], prepared["snapshots"]["reviewer"])
        for root in prepared["snapshots"].values():
            self.assertEqual(self.git("rev-parse", "HEAD", cwd=root), spec["head"])
            self.assertEqual(self.git("branch", "--show-current", cwd=root), "")
        self.next_spec("two")
        checks = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertTrue(checks["passed"], checks)
        result = pipeline.record_review(self.ws, "one", self.review(spec))
        self.assertIn("did not observe", result["provenance"])
        pipeline.integrate(self.ws, "one", self.git("rev-parse", "HEAD"))

    def test_dependency_requires_integration_and_passing_current_gates(self):
        first = self.spec()
        pipeline.register(self.ws, first)
        second = self.next_spec("two", deps=["one"])
        pipeline.register(self.ws, second)
        self.assertEqual(pipeline.status(self.ws, "two")["status"], "wait")
        with self.assertRaises(VerbError):
            pipeline.prepare(self.ws, "two")
        pipeline.prepare(self.ws, "one")
        pipeline.run_checks(self.ws, "one", "test-host")
        pipeline.record_review(self.ws, "one", self.review(first))
        self.assertEqual(pipeline.status(self.ws, "two")["status"], "wait")
        pipeline.integrate(self.ws, "one", first["head"])
        self.assertEqual(pipeline.status(self.ws, "two")["status"], "ready")
        pipeline.record_review(self.ws, "one", self.review(first, status="failed"))
        self.assertEqual(pipeline.status(self.ws, "two")["status"], "blocked")

    def test_resource_conflict_only_blocks_linked_chunks(self):
        first = self.spec(resources=["database"])
        pipeline.register(self.ws, first)
        second = self.next_spec("two", resources=["database"])
        pipeline.register(self.ws, second)
        third = self.next_spec("three")
        pipeline.register(self.ws, third)
        self.assertEqual(pipeline.status(self.ws, "two")["status"], "wait")
        self.assertEqual(pipeline.status(self.ws, "three")["status"], "ready")
        self.complete(first)
        self.assertEqual(pipeline.status(self.ws, "two")["status"], "ready")

    def test_route_gates_coding_and_persisted_reservations(self):
        first = self.spec()
        pipeline.register(self.ws, first)
        def task(name, paths, deps=None, state="pending", resources=None):
            return {"id": name, "owned_paths": paths, "depends_on": deps or [],
                    "resources": resources or [], "state": state}
        tasks = [task("coder", ["source/"], state="active", resources=["db"]),
                 task("linked", ["source/child.py"]), task("dependent", ["next.py"], ["one"]),
                 task("independent", ["else.py"]), task("resource", ["other.py"], resources=["db"])]
        result = pipeline.route(self.ws, {"schema": 1, "tasks": tasks})
        self.assertEqual([x["status"] for x in result["tasks"]], ["ready", "wait", "wait", "ready", "wait"])
        with pipeline.transaction(self.ws) as state:
            self.assertEqual(state["tasks"], tasks)
        missing = pipeline.route(self.ws, {"schema": 1, "tasks": [task("bad", ["a"], ["unknown"]),
                                                                  task("unrelated", ["b"])]})
        self.assertEqual([x["status"] for x in missing["tasks"]], ["wait", "ready"])
        cycles = pipeline.route(self.ws, {"schema": 1, "tasks": [task("a", ["a"], ["b"]),
            task("b", ["b"], ["a"]), task("unrelated", ["c"])]})
        self.assertEqual([x["status"] for x in cycles["tasks"]], ["blocked", "blocked", "ready"])

    def test_invalid_and_stale_reviews_are_preserved_and_fail_closed(self):
        spec = self.spec()
        pipeline.register(self.ws, spec)
        pipeline.prepare(self.ws, "one")
        invalid = [self.review(spec, sha=self.base), self.review(spec, acceptance=[]),
                   self.review(spec, scope=["else.txt"]), self.review(spec, evidence=[]),
                   self.review(spec, findings=[{"severity": "high", "evidence": "security bug"}])]
        for report in invalid:
            with self.assertRaises(VerbError):
                pipeline.record_review(self.ws, "one", report)
        with pipeline.transaction(self.ws) as state:
            self.assertEqual(len([a for a in state["chunks"]["one"]["attempts"] if a["kind"] == "review"]), 5)
        self.assertEqual(pipeline.status(self.ws, "one")["status"], "blocked")

    def test_failed_and_timeout_checks_preserve_full_logs(self):
        spec = self.spec(command=[sys.executable, "-c", "print('failure log'); raise SystemExit(7)"])
        pipeline.register(self.ws, spec)
        pipeline.prepare(self.ws, "one")
        result = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertFalse(result["passed"])
        self.assertEqual(result["checks"][0]["exit_code"], 7, result)
        self.assertIn("failure log", result["checks"][0]["stdout_tail"])
        self.assertTrue((pipeline.store_root(self.ws) / result["checks"][0]["stdout_log"]).is_file())
        with self.assertRaises(VerbError):
            pipeline.integrate(self.ws, "one", spec["head"])
        again = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertNotEqual(result["attempt"], again["attempt"])
        two = self.next_spec("two", command=[sys.executable, "-c", "import time; time.sleep(2)"])
        two["checks"][0]["timeout"] = 0.05
        pipeline.register(self.ws, two)
        pipeline.prepare(self.ws, "two")
        self.assertFalse(pipeline.run_checks(self.ws, "two", "test-host")["passed"])

    def test_empty_checks_ownership_and_deletion_rejected(self):
        spec = self.spec()
        for changes in ({"checks": []}, {"owned_paths": ["other.txt"]}, {"deletions": ["one.txt"]},
                        {"base": spec["head"]}, {"owned_paths": ["../escape"]}):
            with self.assertRaises(VerbError):
                pipeline.register(self.ws, dict(spec, **changes))
        self.git("rm", "seed.txt")
        self.git("commit", "-m", "delete")
        spec["head"] = self.git("rev-parse", "HEAD")
        spec["owned_paths"].append("seed.txt")
        with self.assertRaises(VerbError):
            pipeline.register(self.ws, spec)
        spec["deletions"] = ["seed.txt"]
        pipeline.register(self.ws, spec)

    def test_snapshot_dirty_revision_and_foreign_identity_rejected(self):
        spec = self.spec()
        pipeline.register(self.ws, spec)
        prepared = pipeline.prepare(self.ws, "one")
        test = Path(prepared["snapshots"]["test"])
        (test / "one.txt").write_text("dirty")
        with self.assertRaises(VerbError):
            pipeline.run_checks(self.ws, "one", "test-host")
        self.assertEqual(pipeline.status(self.ws, "one")["status"], "blocked")

    def test_check_mutation_cannot_pass(self):
        spec = self.spec(command=[sys.executable, "-c", "from pathlib import Path; Path('one.txt').write_text('mutated')"])
        pipeline.register(self.ws, spec)
        pipeline.prepare(self.ws, "one")
        result = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"][0]["snapshot_valid"])

    def test_log_and_state_corruption_fail_closed(self):
        spec = self.spec()
        pipeline.register(self.ws, spec)
        self.complete(spec)
        with pipeline.transaction(self.ws) as state:
            receipt = pipeline.latest(state["chunks"]["one"], "checks")
        log = pipeline.store_root(self.ws) / receipt["checks"][0]["stdout_log"]
        log.write_text("tampered")
        self.assertEqual(pipeline.status(self.ws, "one")["status"], "blocked")
        (pipeline.store_root(self.ws) / "state.json").write_text('{"state":')
        with self.assertRaises(VerbError):
            pipeline.status(self.ws)

    def test_exact_revision_receipt_reuse_and_invalidation(self):
        spec = self.spec()
        pipeline.register(self.ws, spec)
        pipeline.prepare(self.ws, "one")
        first = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertFalse(first["reused"])
        reused = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertTrue(reused["reused"], reused)
        self.assertEqual(reused["attempt"], first["attempt"])
        self.assertEqual(reused["tested_revision"], spec["head"])
        forced = pipeline.run_checks(self.ws, "one", "test-host", reuse=False)
        self.assertFalse(forced["reused"])
        self.assertNotEqual(forced["attempt"], first["attempt"])
        log = pipeline.store_root(self.ws) / forced["checks"][0]["stdout_log"]
        log.write_text("corrupt")
        fresh = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertFalse(fresh["reused"])
        self.assertNotEqual(fresh["attempt"], forced["attempt"])
        with mock.patch.dict(os.environ, {"PIPELINE_TEST_ENVIRONMENT": "changed"}):
            changed = pipeline.run_checks(self.ws, "one", "test-host")
            self.assertFalse(changed["reused"])
        identity = pipeline.run_checks(self.ws, "one", "new-explicit-host")
        self.assertFalse(identity["reused"])

    def test_committed_symlink_scope_rejected_without_host_privilege(self):
        spec = self.spec()
        result = subprocess.run(["git", "hash-object", "-w", "--stdin"], input="../outside\n",
                                cwd=self.root, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.git("update-index", "--add", "--cacheinfo", "120000," + result.stdout.strip() + ",linked.txt")
        self.git("commit", "-m", "tracked link")
        spec["head"] = self.git("rev-parse", "HEAD")
        spec["owned_paths"].append("linked.txt")
        with self.assertRaises(VerbError):
            pipeline.validate_spec(self.ws, spec)

    def test_mismatched_snapshot_revision_and_partial_receipt_fail_closed(self):
        spec = self.spec()
        pipeline.register(self.ws, spec)
        prepared = pipeline.prepare(self.ws, "one")
        pipeline.run_checks(self.ws, "one", "test-host")
        with pipeline.transaction(self.ws) as state:
            pipeline.latest(state["chunks"]["one"], "checks")["checks"] = []
        self.assertEqual(pipeline.status(self.ws, "one")["status"], "blocked")
        self.git("checkout", "--detach", self.base, cwd=prepared["snapshots"]["reviewer"])
        with self.assertRaises(VerbError):
            pipeline.record_review(self.ws, "one", self.review(spec))

    def test_missing_state_does_not_reset_existing_evidence(self):
        spec = self.spec()
        pipeline.register(self.ws, spec)
        pipeline.prepare(self.ws, "one")
        (pipeline.store_root(self.ws) / "state.json").unlink()
        with self.assertRaises(VerbError):
            pipeline.status(self.ws)

    def test_review_import_can_overlap_same_chunk_checks(self):
        spec = self.spec(command=[sys.executable, "-c", "import time; time.sleep(1); print('checked')"])
        pipeline.register(self.ws, spec)
        pipeline.prepare(self.ws, "one")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(pipeline.run_checks, self.ws, "one", "test-host")
            import time
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                with pipeline.transaction(self.ws) as state:
                    running = (pipeline.latest(state["chunks"]["one"], "checks") or {}).get("running")
                if running:
                    break
                time.sleep(0.02)
            self.assertTrue(running, future.result(timeout=20) if future.done() else "check did not enter running state")
            self.assertTrue(pipeline.record_review(self.ws, "one", self.review(spec))["passed"])
            checks = future.result(timeout=20)
            self.assertTrue(checks["passed"], checks)

    def test_dependency_chunk_must_be_in_registered_base(self):
        first = self.spec()
        pipeline.register(self.ws, first)
        second = self.next_spec("two", deps=["one"])
        second["base"] = first["base"]
        second["owned_paths"].append("one.txt")
        pipeline.register(self.ws, second)
        self.complete(first)
        result = pipeline.status(self.ws, "two")
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("registered base" in x for x in result["reasons"]))

    def test_changed_prerequisite_scope_blocks_only_linked_work(self):
        first = self.spec()
        pipeline.register(self.ws, first)
        self.complete(first)
        second = self.next_spec("two", deps=["one"])
        pipeline.register(self.ws, second)
        third = self.next_spec("three")
        pipeline.register(self.ws, third)
        self.assertEqual(pipeline.status(self.ws, "two")["status"], "ready")
        # An unrelated committed chunk above leaves prerequisite evidence valid.
        (self.root / "one.txt").write_text("corrected prerequisite\n")
        self.git("add", "one.txt")
        self.git("commit", "-m", "affected correction")
        dependent = pipeline.status(self.ws, "two")
        self.assertEqual(dependent["status"], "blocked")
        self.assertTrue(any("scope/inputs/config" in x for x in dependent["reasons"]))
        self.assertEqual(pipeline.status(self.ws, "three")["status"], "ready")
        tasks = [{"id": "linked", "depends_on": ["one"], "owned_paths": ["next.py"],
                  "resources": [], "state": "pending"},
                 {"id": "independent", "depends_on": [], "owned_paths": ["else.py"],
                  "resources": [], "state": "pending"}]
        self.assertEqual([x["status"] for x in pipeline.route(self.ws, {"schema": 1, "tasks": tasks})["tasks"]],
                         ["blocked", "ready"])
        with self.assertRaises(VerbError):
            pipeline.prepare(self.ws, "two")

    def test_changed_check_input_and_configuration_invalidate_dependency(self):
        first = self.spec()
        first["checks"][0]["inputs"].append("seed.txt")
        pipeline.register(self.ws, first)
        self.complete(first)
        second = self.next_spec("two", deps=["one"])
        pipeline.register(self.ws, second)
        (self.root / "seed.txt").write_text("changed input\n")
        self.assertEqual(pipeline.status(self.ws, "two")["status"], "blocked")
        (self.root / "seed.txt").write_text("seed\n")
        self.assertEqual(pipeline.status(self.ws, "two")["status"], "ready")
        planning = self.root / ".planning"
        planning.mkdir()
        (planning / "config.yaml").write_text("verification: changed\n")
        self.assertEqual(pipeline.status(self.ws, "two")["status"], "blocked")

    def test_affected_correction_cannot_be_attested_by_old_chunk_gates(self):
        first = self.spec()
        pipeline.register(self.ws, first)
        pipeline.prepare(self.ws, "one")
        pipeline.run_checks(self.ws, "one", "test-host")
        pipeline.record_review(self.ws, "one", self.review(first))
        (self.root / "one.txt").write_text("correction after frozen test\n")
        self.git("add", "one.txt")
        self.git("commit", "-m", "correction")
        with self.assertRaises(VerbError):
            pipeline.integrate(self.ws, "one", self.git("rev-parse", "HEAD"))
        with pipeline.transaction(self.ws) as state:
            self.assertIsNone(state["chunks"]["one"]["integrated"])

    def test_absolute_executable_with_forward_slashes_is_external_not_source_scope(self):
        # This exercises the Linux absolute-interpreter branch on Windows too.
        executable = Path(sys.executable).as_posix()
        spec = self.spec(command=[executable, "-c", "print('portable interpreter')"])
        pipeline.register(self.ws, spec)
        pipeline.prepare(self.ws, "one")
        checks = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertTrue(checks["passed"], checks)
        identity = checks["checks"][0]["execution_identity"]
        self.assertTrue(Path(identity["executable"]).is_absolute(), identity)
        self.assertEqual(len(identity["executable_sha256"]), 64, identity)
        self.assertTrue(pipeline.run_checks(self.ws, "one", "test-host")["reused"])

    def test_external_executable_symlink_is_canonicalized_without_relaxing_source_paths(self):
        if os.name == "nt":
            self.skipTest("external executable symlink fixture runs on Linux CI")
        executable = Path(self.temp.name) / "python-alias"
        executable.symlink_to(Path(sys.executable).resolve())
        spec = self.spec(command=[str(executable), "-c", "print('canonical interpreter')"])
        pipeline.register(self.ws, spec)
        pipeline.prepare(self.ws, "one")
        checks = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertTrue(checks["passed"], checks)
        self.assertEqual(checks["checks"][0]["execution_identity"]["executable"], str(Path(sys.executable).resolve()))
        with self.assertRaises(VerbError):
            pipeline.safe(executable.parent, executable.name)

    def directory_spec(self):
        spec = self.spec(command=[sys.executable, "-c", "from pathlib import Path; assert not Path('src/new-empty').exists()"])
        source = self.root / "src"
        source.mkdir()
        (source / "tracked.txt").write_text("tracked source\n")
        self.git("add", "src/tracked.txt")
        self.git("commit", "-m", "directory input")
        spec["head"] = self.git("rev-parse", "HEAD")
        spec["owned_paths"].append("src/")
        spec["checks"][0]["inputs"] = ["src/"]
        return spec

    def test_empty_directory_invalidates_receipt_and_dependency_integration(self):
        spec = self.directory_spec()
        pipeline.register(self.ws, spec)
        prepared = pipeline.prepare(self.ws, "one")
        first = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertTrue(first["passed"], first)
        # Snapshot-only directory additions are cache misses before integration.
        empty = Path(prepared["snapshots"]["test"]) / "src" / "new-empty"
        empty.mkdir()
        second = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertFalse(second["reused"], second)
        self.assertFalse(second["passed"], second)
        self.assertNotEqual(first["attempt"], second["attempt"])
        with pipeline.transaction(self.ws) as state:
            inputs = pipeline.latest(state["chunks"]["one"], "checks")["checks"][0]["inputs"]
        self.assertEqual(inputs["src/new-empty"]["kind"], "directory")
        empty.rmdir()
        restored = pipeline.run_checks(self.ws, "one", "test-host")
        self.assertTrue(restored["passed"], restored)
        pipeline.record_review(self.ws, "one", self.review(spec))
        pipeline.integrate(self.ws, "one", spec["head"])
        dependent = self.next_spec("two", deps=["one"])
        pipeline.register(self.ws, dependent)
        (self.root / "src" / "new-empty").mkdir()
        self.assertEqual(self.git("status", "--porcelain"), "")
        blocked = pipeline.status(self.ws, "two")
        self.assertEqual(blocked["status"], "blocked", blocked)
        self.assertTrue(any("directory topology" in reason for reason in blocked["reasons"]), blocked)

    def test_nonregular_input_metadata_is_rejected_before_reading(self):
        path = (self.root / "seed.txt").resolve()
        special = os.stat_result((stat.S_IFIFO | 0o600, 0, 0, 1, 0, 0, 0, 0, 0, 0))
        original = Path.lstat
        def metadata(candidate):
            return special if candidate == path else original(candidate)
        with mock.patch.object(Path, "lstat", metadata), mock.patch.object(Path, "read_bytes") as read:
            for root in (self.root, self.root / ".." / self.root.name):
                with self.subTest(root=str(root)), self.assertRaisesRegex(VerbError, "nonregular"):
                    pipeline.hashed_inputs(root, {"inputs": ["seed.txt"]})
            read.assert_not_called()

    def test_input_root_alias_has_identical_canonical_fingerprint(self):
        root_alias = self.root / ".." / self.root.name
        self.assertNotEqual(str(root_alias), str(self.root.resolve()))
        original = pipeline.hashed_inputs(self.root, {"inputs": ["seed.txt"]})
        aliased = pipeline.hashed_inputs(root_alias, {"inputs": ["seed.txt"]})
        self.assertEqual(aliased, original)
        self.assertEqual(set(aliased), {"seed.txt"})

    def test_native_fifo_in_directory_input_is_rejected_without_opening(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("native FIFO fixture runs on Linux CI")
        source = self.root / "src"
        source.mkdir()
        os.mkfifo(source / "pipe")
        with self.assertRaisesRegex(VerbError, "nonregular"):
            pipeline.hashed_inputs(self.root, {"inputs": ["src/"]})

    def test_relative_path_resolves_and_executes_tool_in_snapshot_cwd(self):
        spec = self.spec()
        name = "pipeline-checker.exe" if os.name == "nt" else "pipeline-checker"
        system_tool = Path(os.environ["SystemRoot"]) / "System32" / "hostname.exe" if os.name == "nt" else Path("/bin/echo")
        spec["checks"][0]["argv"] = [name] if os.name == "nt" else [name, "snapshot-tool"]
        pipeline.register(self.ws, spec)
        prepared = pipeline.prepare(self.ws, "one")
        # Executable identity is an explicit receipt input even when executable
        # setup is ignored by Git; its canonical path and bytes must match launch.
        exclude = self.root / ".git" / "info" / "exclude"
        with exclude.open("a") as handle:
            handle.write("\ntools/\n")
        author_tools = self.root / "tools"
        snapshot_tools = Path(prepared["snapshots"]["test"]) / "tools"
        author_tools.mkdir()
        snapshot_tools.mkdir()
        (author_tools / name).write_bytes(b"wrong executable from coordinator cwd")
        (author_tools / name).chmod(0o755)
        shutil.copy2(system_tool, snapshot_tools / name)
        (snapshot_tools / name).chmod(0o755)
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with mock.patch.dict(os.environ, {"PATH": "tools" + os.pathsep + os.environ.get("PATH", "")}):
                checks = pipeline.run_checks(self.ws, "one", "test-host")
                self.assertTrue(checks["passed"], checks)
                observed = checks["checks"][0]
                self.assertEqual(observed["execution_identity"]["executable"], str((snapshot_tools / name).resolve()))
                self.assertEqual(observed["executed_argv"][0], observed["execution_identity"]["executable"])
                self.assertEqual(observed["command"], spec["checks"][0]["argv"])
                self.assertTrue(pipeline.run_checks(self.ws, "one", "test-host")["reused"])
        finally:
            os.chdir(previous)

    def test_symlink_and_path_escape_rejected(self):
        spec = self.spec()
        for path in ("a/../outside", "/absolute", "C:/outside", "a\\b", ".git/state", "./one.txt"):
            with self.assertRaises(VerbError, msg=path):
                pipeline.register(self.ws, dict(spec, owned_paths=[path]))
        outside = Path(self.temp.name) / "outside.txt"
        outside.write_text("outside")
        try:
            (self.root / "linked.txt").symlink_to(outside)
        except OSError:
            self.skipTest("host does not grant symlink privilege")
        with self.assertRaises(VerbError):
            pipeline.safe(self.root, "linked.txt")

    def test_concurrent_process_registration_has_no_lost_writes(self):
        specs = [self.spec("z-first")]
        specs += [self.next_spec("a-second"), self.next_spec("m-third")]
        requests = self.root / "requests"
        requests.mkdir()
        files = []
        for spec in specs:
            path = requests / (spec["chunk_id"] + ".json")
            path.write_text(json.dumps(spec))
            files.append(path)
        def invoke(path):
            result = subprocess.run([sys.executable, str(RUNTIME / "phase.py"), "query",
                "pipeline.register", "--spec", "requests/" + path.name], cwd=self.root,
                text=True, capture_output=True, timeout=30)
            return result
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(invoke, files))
        for result in results:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with pipeline.transaction(self.ws) as state:
            self.assertEqual(len(state["chunks"]), 3)
            self.assertEqual({x["order"] for x in state["chunks"].values()}, {0, 1, 2})
        result = subprocess.run([sys.executable, str(RUNTIME / "phase.py"), "query", "pipeline.status"],
                                cwd=self.root, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["chunks"]), 3)


if __name__ == "__main__":
    unittest.main()
