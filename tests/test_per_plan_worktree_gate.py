import base64
from pathlib import Path
import re
import shutil
import subprocess
import unittest
import shlex


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "engineer/workflows/execute-phase/steps/per-plan-worktree-gate.md"


def extract_gate():
    text = DOC.read_text(encoding="utf-8")
    match = re.search(r"Then run the per-plan gate:\s*```bash\n(.*?)\n```", text, re.S)
    if not match:
        raise AssertionError("per-plan bash gate block was not found")
    return text, match.group(1)


@unittest.skipUnless(shutil.which("bash"), "bash is required to execute the documented gate")
class PerPlanWorktreeGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc, cls.gate = extract_gate()

    def run_gate(self, files="", deletions="", submodule=True):
        lines = [
            'work=$(mktemp -d) || exit 2',
            'trap \'rm -rf "$work"\' EXIT',
            'cd "$work" || exit 2',
        ]
        if submodule:
            lines.append("git config --file .gitmodules submodule.library.path vendor/library || exit 2")
        lines.extend((
            f"export PLAN_FILES={shlex.quote(files)} PLAN_DELETIONS={shlex.quote(deletions)} plan_id=03-01",
            "{",
            self.gate,
            "}",
        ))
        payload = "\n".join(lines).encode("utf-8")
        command = "printf %s " + base64.b64encode(payload).decode("ascii") + " | base64 -d | bash"
        result = subprocess.run(
            [shutil.which("bash"), "-c", command],
            capture_output=True,
        )
        result.stdout = result.stdout.decode("utf-8", errors="replace")
        result.stderr = result.stderr.decode("utf-8", errors="replace")
        return result

    def test_normal_plan_paths_pass_the_gate(self):
        result = self.run_gate(files="src/app.py")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("blocking dispatch", result.stdout)

    def test_modified_submodule_intersection_blocks_dispatch(self):
        result = self.run_gate(files="vendor/library/src.c")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("submodule paths are unsupported", result.stdout)

    def test_deletion_only_submodule_intersection_blocks_dispatch(self):
        result = self.run_gate(deletions="vendor/library/old.c")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("submodule paths are unsupported", result.stdout)

    def test_unknown_scope_fails_closed_when_submodules_exist(self):
        result = self.run_gate()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("submodule scope cannot be established", result.stdout)

    def test_gate_keeps_worktree_isolation_mandatory(self):
        self.assertIn("Worktree isolation is mandatory for every executor", self.doc)
        self.assertIn('engineer_run query dispatch-isolation --raw --phase "${PHASE_NUMBER:-}" --plan "$plan_id"', self.doc)
        self.assertNotIn("USE_WORKTREES_FOR_PLAN=false", self.doc)
        self.assertNotIn("--force-isolation none", self.doc)


if __name__ == "__main__":
    unittest.main()
