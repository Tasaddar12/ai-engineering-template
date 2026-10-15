"""Conservative comparison metadata must never weaken reviewed-byte guards."""
import base64
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_install_update import git, load, seed_source

ROOT = Path(__file__).resolve().parents[1]
update = load("line_ending_update", ROOT / ".ai/update.py")
legacy = load("line_ending_legacy", ROOT / ".ai/install_update.py")
installer = update.installer


class ComparisonTests(unittest.TestCase):
    def test_conservative_comparison_matrix(self):
        cases = [
            (b"same\xff\x00\r", b"same\xff\x00\r", "unchanged"),
            (b"a\nb\n", b"a\r\nb\r\n", "line-ending-only"),
            (b"a\r\nb\n", b"a\nb\r\n", "line-ending-only"),
            ("caf\u00e9\r\n".encode(), "caf\u00e9\n".encode(), "line-ending-only"),
            (b"a\r\nb\r", b"a\nb\r", "substantive"),
            (b"\xff\r\n", b"\xff\n", "substantive"),
            (b"\x00\r\n", b"\x00\n", "substantive"),
            (b"a\n", b"b\n", "substantive"),
            (b"a\n", b"a", "substantive"),
            (b"a \n", b"a\n", "substantive"),
            (b"\xef\xbb\xbfa\r\n", b"a\n", "substantive"),
            (None, b"", "added"), (b"", None, "retired"),
            (b"", b"", "unchanged"), (None, None, "unchanged"),
        ]
        for current, candidate, expected in cases:
            with self.subTest(current=current, candidate=candidate):
                self.assertEqual(expected, legacy.compare_content(current, candidate))
                if current is not None and candidate is not None:
                    self.assertEqual(expected in ("unchanged", "line-ending-only"),
                                     legacy.same_text(current, candidate))


class ReviewedLineEndings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory(prefix="line-ending-source-")
        cls.source = Path(cls.fixture.name) / "source"
        cls.source.mkdir()
        seed_source(cls.source)
        git("config", "core.autocrlf", "false", cwd=cls.source)
        (cls.source / ".ai/workflows/newlines.md").write_bytes(b"first\nsecond\n")
        (cls.source / ".ai/workflows/retired.md").write_bytes(b"retired\n")
        cls.commit("baseline")
        cls.first = git("rev-parse", "HEAD", cwd=cls.source)
        cls.baseline = Path(cls.fixture.name) / "baseline"
        update.fetch(str(cls.source), cls.first, cls.baseline)
        rules = cls.source / ".ai/RULES.md"
        rules.write_bytes(rules.read_bytes() + b"\nSubstantive upstream fixture change.\n")
        (cls.source / ".ai/workflows/retired.md").unlink()
        (cls.source / ".ai/workflows/added.md").write_bytes(b"added\n")
        cls.commit("upstream")
        cls.second = git("rev-parse", "HEAD", cwd=cls.source)

    @classmethod
    def commit(cls, message):
        git("add", ".", cwd=cls.source)
        git("-c", "user.name=Fixture", "-c", "user.email=test@example.invalid",
            "commit", "--quiet", "-m", message, cwd=cls.source)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="line-ending-target-")
        self.addCleanup(self.temporary.cleanup)
        self.target = Path(self.temporary.name) / "project"

    def install(self, host="codex"):
        result = subprocess.run([sys.executable, str(ROOT / ".ai/install.py"),
                                 "--source", str(self.source), "--ref", self.first,
                                 "--target", str(self.target), "--host", host,
                                 "--skip-deps", "--no-hooks"], capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        return self.target / ("." + host) / "update.py"

    def write(self, name, data):
        path = self.target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def snapshot(self):
        return {p.relative_to(self.target).as_posix(): p.read_bytes()
                for p in self.target.rglob("*") if p.is_file() and ".git" not in p.parts}

    def plan(self, host="codex", baseline=None):
        return update.build_plan(self.source, self.target, host, False, str(self.source),
                                 self.second, baseline or self.baseline)

    def row(self, plan, name):
        return next(e for e in plan["entries"] if e["path"] == name)

    def cli(self, entry, *arguments):
        return subprocess.run([sys.executable, str(entry), *map(str, arguments)],
                              capture_output=True, text=True, encoding="utf-8")

    def test_installed_review_tracer_is_read_only_and_distinguishes_changes(self):
        entry = self.install()
        self.write(".codex/workflows/newlines.md", b"first\r\nsecond\n")
        before = self.snapshot()
        saved = Path(self.temporary.name) / "review.json"
        result = self.cli(entry, "--target", self.target, "--source", self.source,
                          "--ref", self.second, "--no-hooks", "--plan", saved)
        self.assertEqual(0, result.returncode, result.stderr)
        plan = json.loads(saved.read_bytes())
        self.assertEqual(before, self.snapshot())
        self.assertIn("line-ending-only", result.stdout)
        self.assertIn("substantive", result.stdout)
        self.assertIn("Substantive upstream fixture change", result.stdout)
        row = self.row(plan, ".codex/workflows/newlines.md")
        self.assertEqual("line-ending-only", row["comparison"])
        self.assertEqual("customized", row["classification"])
        self.assertTrue(row["conflict"])
        self.assertEqual("added", self.row(plan, ".codex/workflows/added.md")["comparison"])
        self.assertEqual("retired", self.row(plan, ".codex/workflows/retired.md")["comparison"])


if __name__ == "__main__":
    unittest.main()
