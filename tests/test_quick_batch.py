"""Real batch scheduling and persistence regressions; execution deferred by user."""
import json
from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class QuickBatchChecks(RuntimeCase):
    def create_batch(self, tasks=None, identifier="batch-one"):
        path = self.put("tasks.json", json.dumps(tasks or ["First fix", "Second fix"]))
        return self.cli("quick-batch.create", "--file", path, "--base-revision", self.git("rev-parse", "HEAD"), "--id", identifier)

    def update(self, updates, status=0):
        return self.cli("quick-batch.update", "batch-one", "--updates", json.dumps(updates), status=status, raw=status != 0)

    def test_create_validates_entire_input_before_allocating(self):
        path = self.put("tasks.json", json.dumps(["Good title", {"title": ""}]))
        self.cli("quick-batch.create", "--file", path, "--id", "bad", status=2, raw=True)
        self.assertEqual([], list((self.root/".planning/quick").glob("*/QUICK.md")))
        self.assertFalse((self.root/".planning/quick/batches/bad.json").exists())

    def test_one_task_is_not_a_batch(self):
        path = self.put("tasks.json", '["Only one"]')
        self.cli("quick-batch.create", "--file", path, status=2, raw=True)

    def test_graph_and_update_atomicity(self):
        batch = self.create_batch()
        a, b = [item["quickId"] for item in batch["items"]]
        record = Path(batch["path"])
        before = record.read_bytes()
        self.update([{"quickId": a, "dependsOn": [b]}, {"quickId": b, "dependsOn": [a]}], status=2)
        self.assertEqual(before, record.read_bytes())
        self.update([{"quickId": a, "plannedFiles": ["src/a.py"]}, {"quickId": "missing", "status": "failed"}], status=1)
        self.assertEqual(before, record.read_bytes())
        self.update([{"quickId": a, "expectDigest": "stale", "status": "failed"}], status=1)
        self.assertEqual(before, record.read_bytes())

    def test_overlap_and_resources_force_later_waves(self):
        batch = self.create_batch([{"title": "First", "files_modified": ["src/"], "resources": ["db:test"]},
                                   {"title": "Second", "files_modified": ["src/app.py"]},
                                   {"title": "Third", "files_modified": ["docs/a.md"], "resources": ["db:test"]}])
        waves = [item["wave"] for item in batch["items"]]
        self.assertEqual([1, 2, 2], waves)
        a, b, c = [item["quickId"] for item in batch["items"]]
        changed = self.update([{"quickId": c, "dependsOn": [b]}])
        self.assertEqual(3, changed["items"][2]["wave"])

    def test_scope_rejects_traversal_globs_and_whole_repository(self):
        batch = self.create_batch()
        identifier = batch["items"][0]["quickId"]
        record = Path(batch["path"])
        before = record.read_bytes()
        for path in (".", "./", "../elsewhere", "src/*.py", "/absolute", "C:/absolute", "src/../other"):
            self.update([{"quickId": identifier, "plannedFiles": [path]}], status=2)
            self.assertEqual(before, record.read_bytes())

    def test_resume_preserves_partial_and_does_not_count_presence_as_success(self):
        batch = self.create_batch()
        a, b = batch["items"]
        self.put(str(Path(a["directory"])/(a["quickId"]+"-SUMMARY.md")), "---\nstatus: partial\n---\nUnfinished\n")
        self.update([{"quickId": b["quickId"], "dependsOn": [a["quickId"]]}])
        resumed = self.cli("quick-batch.resume", "batch-one", "--current-base-revision", self.git("rev-parse", "HEAD"))
        self.assertEqual([], resumed["eligible"])
        self.assertEqual([a["quickId"]], resumed["reconcile"])
        self.assertFalse(resumed["evidence"][a["quickId"]]["source_complete"])
        self.assertEqual("pending", resumed["items"][0]["status"])
        self.cli("quick-batch.complete", "batch-one", status=1, raw=True)

    def test_cannot_claim_completion_or_release_unknown_worker(self):
        batch = self.create_batch()
        identifier = batch["items"][0]["quickId"]
        self.update([{"quickId": identifier, "plannedFiles": ["src/a.py"], "status": "complete"}], status=1)
        self.update([{"quickId": identifier, "plannedFiles": ["src/a.py"], "status": "executing"}], status=1)
        # Recovery state left by an interrupted coordinator must retain ownership.
        path = Path(batch["path"])
        data = json.loads(path.read_text())
        data["items"][0].update(status="unknown", plannedFiles=["src/a.py"], dispatchedWorktree=".worktrees/worker", dispatchedBranch="codex/worker", dispatchedBase="abc")
        path.write_text(json.dumps(data))
        self.update([{"quickId": identifier, "status": "pending"}], status=1)
        self.assertEqual("unknown", json.loads(path.read_text())["items"][0]["status"])

    def test_terminal_failures_produce_partial_not_complete(self):
        batch = self.create_batch()
        self.update([{"quickId": i["quickId"], "status": "failed", "failureReason": "Planner failed"} for i in batch["items"]])
        self.assertEqual("partial", self.cli("quick-batch.complete", "batch-one")["status"])

    def test_committed_source_result_requires_scope_and_explicit_deletions(self):
        self.put("src/old.py", "old\n")
        self.git("add", "src/old.py")
        self.git("commit", "-m", "old source")
        batch = self.create_batch()
        item = batch["items"][0]
        identifier = item["quickId"]
        plan = self.put(str(Path(item["directory"])/(identifier+"-PLAN.md")), "---\nfiles_modified: [src/new.py]\n---\nBounded plan\n")
        worker = self.root/".worktrees/result"
        base = self.git("rev-parse", "HEAD")
        self.git("worktree", "add", "-b", "codex/result", str(worker), base)
        self.update([{"quickId": identifier, "status": "executing", "plannedFiles": ["src/new.py"],
                      "dispatchedWorktree": str(worker), "dispatchedBranch": "codex/result", "dispatchedBase": base}])
        (worker/"src/new.py").write_text("new\n")
        (worker/"src/old.py").unlink()
        relative = Path(item["directory"]).relative_to(self.root)/(identifier+"-SUMMARY.md")
        (worker/relative).parent.mkdir(parents=True, exist_ok=True)
        (worker/relative).write_text("---\nstatus: complete\n---\nConcrete source result\n")
        self.git("-C", str(worker), "add", "src", str(relative))
        self.git("-C", str(worker), "commit", "-m", "worker result")
        # A complete marker and commits do not authorize a removed source path.
        self.update([{"quickId": identifier, "status": "executed", "workerState": "stopped"}], status=1)
        # The coordinator must obtain explicit deletion scope, then reconcile the stopped assignment.
        self.update([{"quickId": identifier, "status": "executed", "workerState": "stopped", "filesDeleted": ["src/old.py"]}])
        self.update([{"quickId": identifier, "status": "merged"}], status=1)
        self.git("merge", "--no-ff", "codex/result", "-m", "integrate owned worker")
        updated = self.update([{"quickId": identifier, "status": "merged"}])
        self.assertEqual("merged", updated["items"][0]["status"])

    def test_deterministic_scheduler_and_real_cleanup_evidence(self):
        self.assertEqual(3, self.cli("dispatch-capacity"))
        self.assertEqual(2, self.cli("quick-batch.effective-concurrency", "--jobs", "8", "--task-count", "2")["concurrency"])
        self.assertEqual(2, self.cli("quick-batch.effective-concurrency", "--jobs", "auto", "--task-count", "2", "--mutating", "--isolation", "orchestrator-worktree")["concurrency"])
        self.cli("quick-batch.effective-concurrency", "--jobs", "8", "--task-count", "2", "--mutating", "--isolation", "none", status=1, raw=True)
        self.assertEqual(["b"], self.cli("quick-batch.filter-executed", "--eligible", '["a","b"]', "--executed", '["a"]')["spawnEligible"])
        self.assertEqual(["a"], self.cli("quick-batch.merge-eligible", "--wave-order", '["a","b","c"]', "--ready", '["a","c"]')["mergeable"])
        self.assertEqual(["a"], self.cli("quick-batch.spawn-plan", "--eligible", '["a","b"]', "--capacity", "2", "--in-flight", "1")["spawn"])
        self.assertEqual("block", self.cli("quick-batch.merge-routing", "--kind", "scope_violation")["action"])
        self.assertEqual("human", self.cli("quick-batch.verification-routing", "--status", "human_needed")["route"])
        self.cli("quick-batch.cleanup-entry", "001", "--path", "worktree", "--branch", "worker", status=1, raw=True)
        worker = self.root/".worktrees/worker"
        self.git("worktree", "add", "-b", "codex/worker", str(worker))
        evidence = self.cli("quick-batch.cleanup-entry", "001", "--path", worker, "--branch", "codex/worker")
        self.assertTrue(evidence["merged"])
        (worker/"dirty.txt").write_text("preserve me")
        evidence = self.cli("quick-batch.cleanup-entry", "001", "--path", worker, "--branch", "codex/worker")
        self.assertTrue(evidence["preserveWorktree"])
        self.assertTrue(worker.exists())

    def test_argument_parser_preserves_items_and_rejects_bad_jobs(self):
        result = self.cli("quick-batch.parse-args", "--stdin", stdin="--jobs auto --validate\n- First multiword fix\n- Literal $(touch nope) `text` *.py")
        self.assertEqual(["First multiword fix", "Literal $(touch nope) `text` *.py"], result["tasks"])
        self.assertEqual("auto", result["jobs"])
        self.assertTrue(result["validate"])
        for text in ("--jobs 0", "--jobs -1", "--jobs nope", "--unknown", "--discuss", "--full", "--resume a --file tasks.json"):
            self.cli("quick-batch.parse-args", "--stdin", stdin=text, status=1 if text in ("--unknown", "--discuss", "--full") else 2, raw=True)
