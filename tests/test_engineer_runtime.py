"""Behavior contracts for the fresh stdlib runtime; fixtures execute only in tests."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
RUNTIME = SOURCE/"engineer/bin/engineer.py"


class RuntimeCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.env = {**os.environ, "ENGINEER_ROOT": str(self.root), "ENGINEER_HOST": "codex"}
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Runtime Test")
        self.git("config", "user.email", "runtime@example.invalid")
        self.put("README.md", "# Fixture\n")
        self.git("add", ".")
        self.git("commit", "-m", "fixture")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=True).stdout.strip()

    def put(self, path, content):
        destination = self.root/path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        return destination

    def cli(self, *args, status=0, raw=False, stdin=None):
        process = subprocess.run([sys.executable, "-I", str(RUNTIME), "query", *map(str, args)],
                                 cwd=self.root, env=self.env, input=stdin, text=True, capture_output=True)
        self.assertEqual(status, process.returncode, process.stderr or process.stdout)
        return process.stdout.strip() if raw else json.loads(process.stdout)

    def phase(self, name="Behavior"):
        return self.cli("phase.add", name)["directory"]

    def plan(self, directory, body=None, extra=""):
        path = Path(directory)/"01-01-PLAN.md"
        content = """---
phase: "01"
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified: ["src/app.py"]
autonomous: true
must_haves:
  truths: ["A behavior exists"]
  artifacts: []
  key_links: []
""" + extra + "---\n" + (body or """<tasks>
<task type="auto"><name>Add behavior</name><files>src/app.py</files>
<read_first>README.md</read_first><action>Implement behavior</action>
<verify>python -m unittest discover</verify><done>Behavior is observable</done></task>
</tasks>
""")
        path.write_text(content, encoding="utf-8")
        return path


class RecordBehavior(RuntimeCase):
    def test_phase_state_and_roadmap_stay_queryable(self):
        directory = self.phase()
        self.assertEqual("01", self.cli("find-phase", "1")["number"])
        self.cli("state.patch", '{"Phase":"01","Status":"Planning"}')
        self.assertEqual("Planning", self.cli("state.get", "status"))
        self.cli("phase.edit", "01", "--goal", "A revised goal")
        self.assertEqual("A revised goal", self.cli("roadmap.get-phase", "1")["goal"])

    def test_remove_archives_instead_of_deleting_artifacts(self):
        directory = self.phase()
        self.plan(directory)
        self.cli("phase.remove", "1", status=1, raw=True)
        result = self.cli("phase.remove", "1", "--force")
        self.assertTrue(Path(result["archive"]).joinpath("01-01-PLAN.md").exists())

    def test_quick_and_todo_records(self):
        quick = self.cli("quick.create", "Repair the login")
        self.cli("quick.update", quick["quick_id"], "--status", "complete")
        self.assertEqual("complete", self.cli("quick.get", quick["quick_id"])["status"])
        todo = self.cli("todo.add", "Inspect a boundary", "--phase", "1")
        self.assertEqual(1, self.cli("todo.match-phase", "1")["count"])
        self.cli("todo.complete", todo["path"])
        self.assertEqual(0, self.cli("todo.list")["count"])
