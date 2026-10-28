import json
from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class QuickBatchChecks(RuntimeCase):
    def integrate_item(self, item, number):
        """Land a real source commit plus the PLAN and SUMMARY evidence the runtime requires for one item."""
        source = "src/item%d.py" % number
        self.put(source, "VALUE = %d\n" % number)
        self.git("add", source)
        self.git("commit", "-m", "implement item %d" % number)
        commit = self.git("rev-parse", "HEAD")
        directory = Path(item["directory"])
        identifier = item["quickId"]
        self.put((directory/(identifier+"-PLAN.md")).relative_to(self.root).as_posix(),
                 '---\nfiles_modified: ["%s"]\n---\n# Plan\n' % source)
        self.put((directory/(identifier+"-SUMMARY.md")).relative_to(self.root).as_posix(),
                 "---\nstatus: complete\n---\n# Summary\n\nImplemented item %d.\n\n## Task Commits\n\n- %s\n" % (number, commit))
        return commit

    def test_create_update_resume_complete(self):
        self.cli("project.init", "--fields", json.dumps({"project": {"name": "Fixture", "description": "Fixture project", "core_value": "Observable behavior"}}))
        tasks = self.put("tasks.json", '["First fix", "Second fix"]')
        base = self.git("rev-parse", "HEAD")
        batch = self.cli("quick-batch.create", "--file", tasks, "--base-revision", base, "--id", "batch-one")
        items = batch["items"]
        ids = [item["quickId"] for item in items]
        self.assertEqual(2, len(ids))
        # Completion requires integrated source and summary evidence; a pending item has none.
        self.cli("quick-batch.complete", "batch-one", "--quick-id", ids[0], status=1, raw=True)
        commits = [self.integrate_item(item, number) for number, item in enumerate(items, 1)]
        updates = [{"quickId": identifier, "status": "merged", "mergeCommit": commit} for identifier, commit in zip(ids, commits)]
        self.cli("quick-batch.update", "batch-one", "--updates", json.dumps(updates))
        self.assertEqual(0, len(self.cli("quick-batch.resume", "batch-one", "--current-base-revision", base)["done"]))
        for identifier in ids:
            self.cli("quick-batch.complete", "batch-one", "--quick-id", identifier)
        self.put("advance.txt", "base advanced\n")
        self.git("add", "advance.txt")
        self.git("commit", "-m", "advance base")
        resumed = self.cli("quick-batch.resume", "batch-one", "--current-base-revision", self.git("rev-parse", "HEAD"))
        self.assertTrue(resumed["base_drift"])
        self.assertEqual(2, len(resumed["done"]))
        self.assertEqual("complete", self.cli("quick-batch.get", "batch-one")["status"])
        self.assertEqual([], self.cli("init.quick-batch")["open_batches"])

    def test_deterministic_scheduler_and_routing(self):
        self.assertEqual(3, self.cli("dispatch-capacity"))
        self.assertEqual(2, self.cli("quick-batch.effective-concurrency", "--jobs", "8", "--task-count", "2")["concurrency"])
        self.assertEqual(1, self.cli("quick-batch.effective-concurrency", "--jobs", "8", "--task-count", "2", "--mutating", "--isolation", "none")["concurrency"])
        filtered = self.cli("quick-batch.filter-executed", "--eligible", '["a","b"]', "--executed", '["a"]')
        self.assertEqual(["b"], filtered["spawnEligible"])
        self.assertEqual(["a"], self.cli("quick-batch.merge-eligible", "--wave-order", '["a","b","c"]', "--ready", '["a","c"]')["mergeable"])
        self.assertEqual(["a"], self.cli("quick-batch.spawn-plan", "--eligible", '["a","b"]', "--capacity", "2", "--in-flight", "1")["spawn"])
        self.assertEqual("retry", self.cli("quick-batch.merge-routing", "--kind", "merge_failed")["action"])
        for kind in ("conflict", "scope_violation"):
            routed = self.cli("quick-batch.merge-routing", "--kind", kind)
            self.assertEqual("block", routed["action"])
            self.assertTrue(routed["preserveWorktree"])
        self.assertEqual("human_needed", self.cli("quick-batch.verification-routing", "--status", "human_needed")["action"])
        self.assertEqual("complete", self.cli("quick-batch.verification-routing", "--status", "passed")["action"])
        self.assertEqual("fail", self.cli("quick-batch.verification-routing", "--status", "gaps_found")["action"])

    def test_cleanup_entry_binds_the_recorded_worktree_to_the_fresh_plan_scope(self):
        self.put(".gitignore", ".worktrees/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "chore: ignore worktrees")
        worker = self.cli("worktree.create", "01-01", "--phase", "1", "--base", "HEAD", "--files", "src/app.py")
        plan = '---\nfiles_modified: ["src/app.py"]\n---\n# Plan\n'
        arguments = ("--worktree-path", worker["path"], "--branch", worker["branch"], "--expected-base", worker["base"],
                     "--allowed-bases", json.dumps([worker["base"]]))
        # merge-wave.md passes PLAN content, which begins with YAML `---`, as a separate token.
        entry = self.cli("quick-batch.cleanup-entry", *arguments, "--plan-content", plan)
        self.assertEqual(worker["branch"], entry["branch"])
        self.assertEqual(["src/app.py"], entry["files_modified"])
        drifted = '---\nfiles_modified: ["src/other.py"]\n---\n# Plan\n'
        self.cli("quick-batch.cleanup-entry", *arguments, "--plan-content", drifted, status=1, raw=True)

    def test_argument_parser_rejects_unknown_flags(self):
        result = self.cli("quick-batch.parse-args", "--stdin", stdin='"First fix" --jobs 2 --research --validate')
        self.assertEqual(["First fix"], result["tasks"])
        self.assertTrue(result["validate"])
        self.cli("quick-batch.parse-args", "--stdin", stdin="--unknown", status=2, raw=True)
