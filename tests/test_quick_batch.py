import json
from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class QuickBatchChecks(RuntimeCase):
    def test_create_update_resume_complete(self):
        tasks = self.put("tasks.json", '["First fix", "Second fix"]')
        batch = self.cli("quick-batch.create", "--file", tasks, "--base-revision", "abc", "--id", "batch-one")
        ids = [item["quickId"] for item in batch["items"]]
        self.assertEqual(2, len(ids))
        self.cli("quick-batch.complete", "batch-one", status=1, raw=True)
        updates = [{"quickId": identifier, "status": "merged"} for identifier in ids]
        self.cli("quick-batch.update", "batch-one", "--updates", json.dumps(updates))
        resumed = self.cli("quick-batch.resume", "batch-one", "--current-base-revision", "changed")
        self.assertTrue(resumed["base_drift"])
        self.assertEqual(2, len(resumed["done"]))
        self.assertEqual("complete", self.cli("quick-batch.complete", "batch-one")["status"])
        self.assertEqual([], self.cli("init.quick-batch")["open_batches"])

    def test_deterministic_scheduler_and_routing(self):
        self.assertEqual(3, self.cli("dispatch-capacity"))
        self.assertEqual(2, self.cli("quick-batch.effective-concurrency", "--jobs", "8", "--task-count", "2")["concurrency"])
        self.assertEqual(1, self.cli("quick-batch.effective-concurrency", "--jobs", "8", "--task-count", "2", "--mutating", "--isolation", "none")["concurrency"])
        filtered = self.cli("quick-batch.filter-executed", "--eligible", '["a","b"]', "--executed", '["a"]')
        self.assertEqual(["b"], filtered["spawnEligible"])
        self.assertEqual(["a"], self.cli("quick-batch.merge-eligible", "--wave-order", '["a","b","c"]', "--ready", '["a","c"]')["mergeable"])
        self.assertEqual(["a"], self.cli("quick-batch.spawn-plan", "--eligible", '["a","b"]', "--capacity", "2", "--in-flight", "1")["spawn"])
        self.assertEqual("block", self.cli("quick-batch.merge-routing", "--kind", "scope_violation")["action"])
        self.assertEqual("human", self.cli("quick-batch.verification-routing", "--status", "human_needed")["route"])
        self.assertTrue(self.cli("quick-batch.cleanup-entry", "001", "--path", "worktree", "--branch", "worker")["merged"])

    def test_argument_parser_rejects_unknown_flags(self):
        result = self.cli("quick-batch.parse-args", "--stdin", stdin='"First fix" --jobs 2 --research --validate')
        self.assertEqual(["First fix"], result["tasks"])
        self.assertTrue(result["validate"])
        self.cli("quick-batch.parse-args", "--stdin", stdin="--unknown", status=2, raw=True)
