"""Run advisory hook events against disposable real Git worktrees."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks/worktree-path-guard.py"


class PythonHook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-b", "main", str(self.root)], capture_output=True, check=True)
        self.env = {key: value for key, value in os.environ.items() if key not in ("ENGINEER_ROOT", "ENGINEER_WORKTREE_ROOT")}

    def event(self, payload):
        result = subprocess.run([sys.executable, "-I", str(HOOK), "--host", "codex"], input=payload,
                                capture_output=True, text=True, env=self.env, cwd=self.root, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        return result

    def test_malformed_event_is_advisory(self):
        result = self.event("not json")
        self.assertIn("could not establish safety", result.stderr)

    def test_reads_are_quiet_and_primary_writes_warn(self):
        self.assertEqual("", self.event(json.dumps({"tool_name": "Read"})).stdout)
        result = self.event(json.dumps({"tool_name": "Write", "tool_input": {"file_path": "app.py"}}))
        self.assertIn("primary checkout", result.stderr)
        self.assertEqual("PreToolUse", json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"])

    def test_dispatch_classification_and_durable_activity(self):
        read = self.event(json.dumps({"tool_name": "Agent", "session_id": "read-session", "tool_input": {"subagent_type": "scout"}}))
        self.assertEqual("", read.stderr)
        write = self.event(json.dumps({"tool_name": "Agent", "session_id": "write-session", "tool_input": {"subagent_type": "coder"}}))
        self.assertIn("lacks isolation", write.stderr)
        records = [json.loads(path.read_text(encoding="utf-8").strip()) for path in (self.root / ".planning/handoffs").glob("*.jsonl")]
        self.assertEqual({"read-only", "write"}, {record["category"] for record in records})


if __name__ == "__main__":
    unittest.main()
