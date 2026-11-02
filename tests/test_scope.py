try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class ScopeChecks(RuntimeCase):
    def add_commit(self, path, subject):
        self.put(path, subject+"\n")
        self.git("add", path)
        self.git("commit", "-m", subject)
        return self.git("rev-parse", "HEAD")

    def test_phase_plan_pathspec_and_commit_limit(self):
        first = self.add_commit("src/a.py", "feat(01-01): first behavior")
        self.add_commit("src/b.py", "feat(02-01): unrelated behavior")
        result = self.cli("check.evaluation-scope", "--phase", "1", "--plan", "1")
        self.assertEqual([first], [c["sha"] for c in result["commits"]])
        self.assertEqual(["src/a.py"], result["files"])
        self.assertEqual([first], [c["sha"] for c in self.cli("check.evaluation-scope", "--plan", "01-01")["commits"]])
        result = self.cli("check.evaluation-scope", "--phase", "1", "--pathspec", "src/b.py")
        self.assertEqual(0, result["count"])
        result = self.cli("check.evaluation-scope", "--phase", "1", "--max-commits", "1")
        self.assertEqual(0, result["count"])
        self.assertEqual(first, self.cli("check.evaluation-scope", "--phase", "1", "--commits-only", "--raw", raw=True))
