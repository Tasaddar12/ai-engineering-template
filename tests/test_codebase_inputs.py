"""Codebase captures discover their checkout once, regardless of file count."""
import contextlib
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from test_engineer_runtime import RuntimeCase
from test_misc_verbs import _load


class CodebaseInputs(RuntimeCase):
    @contextlib.contextmanager
    def discover_checkout(self):
        previous = Path.cwd()
        with patch.dict(os.environ):
            os.environ.pop("ENGINEER_ROOT", None)
            os.chdir(self.root)
            try:
                yield
            finally:
                os.chdir(previous)

    def capture(self, callback):
        core = _load("core")
        with self.discover_checkout(), patch.object(core, "run", wraps=core.run) as calls:
            result = callback()
        commands = [call.args[0] for call in calls.call_args_list]
        discoveries = commands.count(["git", "rev-parse", "--show-toplevel"])
        return result, discoveries

    def test_root_discovery_is_constant_for_source_paths_and_inputs(self):
        codebase, core = _load("codebase"), _load("core")
        for count in (1, 64):
            for index in range(count):
                self.put(f"src/file-{index:03d}.py", f"value = {index}\n")
            with self.subTest(files=count):
                paths, discoveries = self.capture(codebase.source_paths)
                self.assertEqual(1, discoveries)
                captured, discoveries = self.capture(codebase.inputs)
                self.assertEqual(1, discoveries)
                self.assertEqual([p.relative_to(self.root).as_posix() for p in paths], captured["paths"])
                self.assertEqual(core.digest(paths, self.root), captured["digest"])
                self.assertEqual(count + 1, len(paths))

    def test_git_selection_prefixes_and_digest_are_preserved(self):
        codebase = _load("codebase")
        self.put("src/tracked.py", "original\n")
        self.put("src/deleted.py", "removed\n")
        self.put(".gitignore", "ignored/\n")
        self.git("add", "--", "src", ".gitignore")
        self.git("commit", "-m", "source fixture")
        (self.root/"src/deleted.py").unlink()
        self.put("src/tracked.py", "dirty\n")
        self.put("src/space ü.py", "untracked\n")
        self.put("src-other/file.py", "excluded by prefix\n")
        self.put("ignored/file.py", "ignored\n")
        self.put(".planning/source.py", "planning is excluded\n")
        selected, discoveries = self.capture(lambda: codebase.inputs(["src"]))
        self.assertEqual(1, discoveries)
        self.assertEqual(["src/space ü.py", "src/tracked.py"], selected["paths"])
        exact, _ = self.capture(lambda: codebase.inputs(["src/tracked.py"]))
        self.assertEqual(["src/tracked.py"], exact["paths"])
        all_inputs, _ = self.capture(codebase.inputs)
        dot_inputs, _ = self.capture(lambda: codebase.inputs(["."]))
        self.assertEqual(all_inputs, dot_inputs)
        self.assertEqual([".gitignore", "README.md", "src-other/file.py", *selected["paths"]], all_inputs["paths"])
        self.put("src/tracked.py", "changed again\n")
        changed, _ = self.capture(lambda: codebase.inputs(["src"]))
        self.assertNotEqual(selected["digest"], changed["digest"])

    def test_explicit_base_is_used_for_git_and_containment_without_discovery(self):
        codebase, planning = _load("codebase"), _load("planning")
        self.put("src/file.py", "source\n")
        with patch.object(codebase, "root", side_effect=AssertionError("unexpected discovery")), \
                patch.object(planning, "root", side_effect=AssertionError("unexpected discovery")):
            paths = codebase.source_paths(["src"], base=self.root)
        self.assertEqual([self.root/"src/file.py"], paths)

    def test_safe_keeps_traversal_absolute_and_link_guards_with_explicit_base(self):
        planning, core = _load("planning"), _load("core")
        self.put("src/file.py", "source\n")
        self.assertEqual(self.root/"src/file.py", planning.safe("src/file.py", base=self.root))
        for value, code in (("src/../README.md", "unsafe-planning-path"),
                            (self.root.parent/"outside.py", "planning-path-outside-root")):
            with self.subTest(path=str(value)), self.assertRaises(core.Failure) as caught:
                planning.safe(value, base=self.root)
            self.assertEqual(code, caught.exception.code)
        with self.discover_checkout():
            self.assertEqual(self.root/"README.md", planning.safe("README.md"))

    def test_safe_rejects_symlinks_with_explicit_base(self):
        planning, core = _load("planning"), _load("core")
        target = self.put("src/file.py", "source\n")
        link = self.root/"linked.py"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        with self.assertRaises(core.Failure) as caught:
            planning.safe(link, base=self.root)
        self.assertEqual("linked-planning-path", caught.exception.code)

    @unittest.skipUnless(os.name == "nt", "Windows junction guard")
    def test_safe_rejects_windows_junction_with_explicit_base(self):
        planning, core = _load("planning"), _load("core")
        self.put("src/file.py", "source\n")
        junction = self.root/"linked-src"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(self.root/"src")],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        try:
            with self.assertRaises(core.Failure) as caught:
                planning.safe(junction/"file.py", base=self.root)
            self.assertEqual("linked-planning-path", caught.exception.code)
        finally:
            junction.rmdir()

    def test_stamp_records_fresh_manifest_with_constant_discovery(self):
        codebase, core = _load("codebase"), _load("core")
        self.put(".planning/codebase/STRUCTURE.md", "# Structure\n\nFixture source.\n")
        counts = []
        for count in (1, 64):
            for index in range(count):
                self.put(f"src/file-{index:03d}.py", f"value = {index}\n")
            result, discoveries = self.capture(lambda: codebase.stamp(core.Args([])))
            self.assertIsInstance(result, dict)
            self.assertEqual(["STRUCTURE.md"], result["stamped"])
            manifest = json.loads((self.root/".planning/codebase/.freshness.json").read_text())
            self.assertEqual(result["input_hash"], manifest["maps"]["STRUCTURE.md"]["input_hash"])
            self.assertEqual(count + 1, len(manifest["maps"]["STRUCTURE.md"]["input_paths"]))
            status, _ = self.capture(lambda: codebase.command(core.Args([]), "status"))
            self.assertTrue(status["fresh"])
            counts.append(discoveries)
        self.assertEqual(counts[0], counts[1])

    def test_stamp_still_rejects_source_changes_between_captures(self):
        codebase, core = _load("codebase"), _load("core")
        self.put(".planning/codebase/STRUCTURE.md", "# Structure\n")
        source = self.put("src/file.py", "original\n")
        original = codebase.inputs
        captures = []

        def capture_then_change(prefixes):
            result = original(prefixes)
            captures.append(result)
            if len(captures) == 1:
                source.write_text("changed\n", encoding="utf-8")
            return result

        with patch.object(codebase, "inputs", side_effect=capture_then_change):
            result, _ = self.capture(lambda: codebase.stamp(core.Args([])))
        packet, status = result
        self.assertEqual(69, status)
        self.assertEqual("stamp-unavailable", packet["reason"])
        self.assertEqual(2, len(captures))
        self.assertNotEqual(captures[0]["digest"], captures[1]["digest"])
        self.assertFalse((self.root/".planning/codebase/.freshness.json").exists())


if __name__ == "__main__":
    unittest.main()
