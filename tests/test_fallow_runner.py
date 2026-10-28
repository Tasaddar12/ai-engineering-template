"""Ported from gsd-core tests/fallow-runner.test.cjs (pinned d37ff11b).

Rows F1-F15 and P3 exercise binary resolution; the win32 rows (F7-F10) run
against the private ``_resolve_executable_binary`` with ``platform="win32"``
exactly as upstream projects them. Report normalisation is covered with the
upstream ``tests/fixtures/fallow`` sample reports inlined below.
"""
import contextlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"engineer/bin"))

from lib import fallow_runner  # noqa: E402
from lib.fallow_runner import (  # noqa: E402
    normalize_fallow_report, normalize_fallow_report_file, require_fallow_binary, resolve_fallow_binary,
)

NO_BINARY = ("Fallow is enabled but no binary was found. "
             "Please install fallow via `npm install -D fallow` or `cargo install fallow`.")
_PATHEXT = os.environ.get("PATHEXT") or ".EXE;.CMD;.BAT;.COM"
WIN32_CMD_EXT = next((ext for ext in _PATHEXT.split(";") if ext.lower() == ".cmd"), ".CMD")
FALLOW_FIXTURE = f"fallow{WIN32_CMD_EXT}" if sys.platform == "win32" else "fallow"

SAMPLE_FINDINGS = {
    "schema_version": 3, "version": "2.70.0", "command": "audit", "verdict": "fail",
    "dead_code": {
        "schema_version": 6,
        "unused_files": [{"path": "src/orphan.ts", "introduced": True, "actions": []}],
        "unused_exports": [{"path": "sdk/src/query/commit.ts", "export_name": "commitToSubrepo", "is_type_only": False,
                            "line": 289, "col": 16, "span_start": 1234, "is_re_export": False, "introduced": True, "actions": []}],
        "circular_dependencies": [{"files": ["src/a.ts", "src/b.ts"], "length": 2, "line": 1, "col": 9, "introduced": True, "actions": []}],
    },
    "duplication": {"clone_groups": [{"instances": [
        {"file": "gsd-core/bin/lib/config-schema.cjs", "start_line": 14, "end_line": 22, "start_col": 0, "end_col": 1, "fragment": "..."},
        {"file": "sdk/src/query/config-schema.ts", "start_line": 9, "end_line": 17, "start_col": 0, "end_col": 1, "fragment": "..."}]}]},
    "complexity": {"findings": []},
}
SAMPLE_EDGE_CASES = {
    "schema_version": 3, "command": "audit",
    "dead_code": {
        "unused_files": [],
        "unused_exports": [{"path": "src/café/résumé.ts", "export_name": "naïveHelper", "line": 0, "col": 0}],
        "circular_dependencies": [{"files": ["src/a.ts", "src/b.ts", "src/c.ts"], "length": 3, "line": 2, "col": 4}],
    },
    "duplication": {"clone_groups": [{"instances": [{"file": "src/only-one.ts", "start_line": 5, "end_line": 30}]}]},
}
SAMPLE_EMPTY = {
    "schema_version": 3, "command": "audit", "verdict": "pass",
    "dead_code": {"unused_files": [], "unused_exports": [], "circular_dependencies": []},
    "duplication": {"clone_groups": []},
}
EMPTY_REPORT = {"summary": {"unused_exports": 0, "unused_files": 0, "duplicates": 0, "circular_dependencies": 0, "total": 0}, "findings": []}


class FallowCase(unittest.TestCase):
    def tmp(self):
        handle = tempfile.TemporaryDirectory()
        self.addCleanup(handle.cleanup)
        return handle.name

    def bin_dir(self, cwd):
        directory = os.path.join(cwd, "node_modules", ".bin")
        os.makedirs(directory, exist_ok=True)
        return directory

    @staticmethod
    def touch(path):
        Path(path).write_text("", encoding="utf-8")
        return path

    @contextlib.contextmanager
    def executable(self, allowed=True):
        with mock.patch.object(fallow_runner.os, "access", return_value=allowed):
            yield

    @contextlib.contextmanager
    def env(self, **values):
        with mock.patch.dict(os.environ, values):
            yield


class ResolveFallowBinary(FallowCase):
    def test_f1_bin_only(self):
        cwd = self.tmp()
        fallow = self.touch(os.path.join(self.bin_dir(cwd), FALLOW_FIXTURE))
        with self.executable():
            self.assertEqual(fallow, resolve_fallow_binary(cwd, ""))

    def test_f2_path_only(self):
        cwd, path_dir = self.tmp(), self.tmp()
        fallow = self.touch(os.path.join(path_dir, FALLOW_FIXTURE))
        with self.executable():
            self.assertEqual(fallow, resolve_fallow_binary(cwd, path_dir))

    def test_f3_bin_wins_over_path(self):
        cwd, path_dir = self.tmp(), self.tmp()
        bin_fallow = self.touch(os.path.join(self.bin_dir(cwd), FALLOW_FIXTURE))
        path_fallow = self.touch(os.path.join(path_dir, FALLOW_FIXTURE))
        with self.executable():
            resolved = resolve_fallow_binary(cwd, path_dir)
        self.assertEqual(bin_fallow, resolved)
        self.assertNotEqual(path_fallow, resolved)

    def test_f4_access_failure(self):
        cwd = self.tmp()
        fallow = self.touch(os.path.join(self.bin_dir(cwd), FALLOW_FIXTURE))
        with self.executable(False):
            resolved = resolve_fallow_binary(cwd, "")
        # win32: requireExecutable is a documented no-op; POSIX: the X_OK check nulls it out.
        self.assertEqual(fallow if sys.platform == "win32" else None, resolved)

    def test_f4_access_raising(self):
        cwd = self.tmp()
        fallow = self.touch(os.path.join(self.bin_dir(cwd), FALLOW_FIXTURE))
        with mock.patch.object(fallow_runner.os, "access", side_effect=PermissionError("EACCES")):
            resolved = resolve_fallow_binary(cwd, "")
        self.assertEqual(fallow if sys.platform == "win32" else None, resolved)

    def test_f5_absent(self):
        self.assertIsNone(resolve_fallow_binary(self.tmp(), ""))

    def test_f6_env_path_defaults_to_ambient(self):
        cwd = self.tmp()
        fallow = self.touch(os.path.join(self.bin_dir(cwd), FALLOW_FIXTURE))
        with self.executable(), self.env(PATH=""):
            self.assertEqual(fallow, resolve_fallow_binary(cwd))

    def test_f11_require_returns_path(self):
        cwd = self.tmp()
        fallow = self.touch(os.path.join(self.bin_dir(cwd), FALLOW_FIXTURE))
        with self.executable():
            self.assertEqual(fallow, require_fallow_binary(cwd, ""))

    def test_f12_require_raises_install_message(self):
        with self.assertRaises(RuntimeError) as caught:
            require_fallow_binary(self.tmp(), "")
        self.assertEqual(NO_BINARY, str(caught.exception))

    def test_f13_no_node_modules_falls_through_to_ambient_path(self):
        cwd, path_dir = self.tmp(), self.tmp()
        fallow = self.touch(os.path.join(path_dir, FALLOW_FIXTURE))
        with self.executable(), self.env(PATH=path_dir):
            self.assertEqual(fallow, resolve_fallow_binary(cwd))

    def test_f14_bin_is_a_file(self):
        cwd, path_dir = self.tmp(), self.tmp()
        os.makedirs(os.path.join(cwd, "node_modules"))
        self.touch(os.path.join(cwd, "node_modules", ".bin"))
        fallow = self.touch(os.path.join(path_dir, FALLOW_FIXTURE))
        with self.executable():
            self.assertEqual(fallow, resolve_fallow_binary(cwd, path_dir))

    def test_f15_directory_named_fallow_is_not_resolved(self):
        cwd = self.tmp()
        os.makedirs(os.path.join(self.bin_dir(cwd), FALLOW_FIXTURE))
        with self.executable():
            self.assertIsNone(resolve_fallow_binary(cwd, ""))

    def test_p3_ambient_pathext_governs_win32_resolution(self):
        cwd, path_dir = self.tmp(), self.tmp()
        distinctive = self.touch(os.path.join(path_dir, "fallow.XYZ"))
        with self.env(PATHEXT=".XYZ"):
            resolved = resolve_fallow_binary(cwd, path_dir)
        self.assertEqual(distinctive if sys.platform == "win32" else None, resolved)


class Win32Resolution(FallowCase):
    def resolve(self, cwd, env_path=""):
        return fallow_runner._resolve_executable_binary(
            "fallow", platform="win32", prepend_paths=[os.path.join(cwd, "node_modules", ".bin")],
            env={"PATH": env_path, "PATHEXT": os.environ.get("PATHEXT", "")}, require_executable=True)

    def test_f7_cmd_in_bin(self):
        cwd = self.tmp()
        fallow_cmd = self.touch(os.path.join(self.bin_dir(cwd), "fallow.CMD"))
        self.assertEqual(fallow_cmd, self.resolve(cwd))

    def test_f8_exe_beats_cmd(self):
        cwd, path_dir = self.tmp(), self.tmp()
        exe = self.touch(os.path.join(path_dir, "fallow.EXE"))
        self.touch(os.path.join(path_dir, "fallow.CMD"))
        self.assertEqual(exe, self.resolve(cwd, path_dir))

    def test_f9_extensionless_shim_never_resolved(self):
        cwd, path_dir = self.tmp(), self.tmp()
        self.touch(os.path.join(path_dir, "fallow"))
        cmd = self.touch(os.path.join(path_dir, "fallow.CMD"))
        self.assertEqual(cmd, self.resolve(cwd, path_dir))

    def test_f10_only_extensionless_is_null(self):
        cwd, path_dir = self.tmp(), self.tmp()
        self.touch(os.path.join(path_dir, "fallow"))
        self.assertIsNone(self.resolve(cwd, path_dir))

    def test_name_carrying_known_extension_is_tried_as_is(self):
        directory = self.tmp()
        exe = self.touch(os.path.join(directory, "tool.exe"))
        resolved = fallow_runner._resolve_executable_binary(
            "tool.exe", platform="win32", env={"PATH": directory, "PATHEXT": ".EXE;.CMD"})
        self.assertEqual(exe, resolved)

    def test_default_pathext_and_case_insensitive_env_names(self):
        directory = self.tmp()
        cmd = self.touch(os.path.join(directory, "fallow.CMD"))
        self.assertEqual(cmd, fallow_runner._resolve_executable_binary(
            "fallow", platform="win32", env={"Path": directory}))

    def test_path_like_name_bypasses_search(self):
        directory = self.tmp()
        target = self.touch(os.path.join(directory, "fallow"))
        self.assertEqual(target, fallow_runner._resolve_executable_binary("%s" % target, platform="win32", env={}))
        self.assertIsNone(fallow_runner._resolve_executable_binary(os.path.join(directory, "missing"), platform="win32", env={}))

    def test_empty_name_is_null(self):
        self.assertIsNone(fallow_runner._resolve_executable_binary("", env={}))
        self.assertIsNone(fallow_runner._resolve_executable_binary(None, env={}))

    def test_path_override_empty_string_means_empty_search_path(self):
        directory = self.tmp()
        self.touch(os.path.join(directory, "fallow.EXE"))
        self.assertIsNone(fallow_runner._resolve_executable_binary(
            "fallow", platform="win32", env={"PATH": directory}, path_override=""))


class PosixResolution(FallowCase):
    def test_bare_name_resolves_and_pathext_is_ignored(self):
        directory = self.tmp()
        plain = self.touch(os.path.join(directory, "fallow"))
        self.touch(os.path.join(directory, "other.EXE"))
        self.assertEqual(plain, fallow_runner._resolve_executable_binary(
            "fallow", platform="linux", env={"PATH": directory, "PATHEXT": ".EXE"}))
        self.assertIsNone(fallow_runner._resolve_executable_binary(
            "other", platform="linux", env={"PATH": directory, "PATHEXT": ".EXE"}))

    def test_require_executable_consults_access(self):
        directory = self.tmp()
        plain = self.touch(os.path.join(directory, "fallow"))
        env = {"PATH": directory}
        with self.executable(False):
            self.assertIsNone(fallow_runner._resolve_executable_binary("fallow", platform="linux", env=env, require_executable=True))
            self.assertEqual(plain, fallow_runner._resolve_executable_binary("fallow", platform="linux", env=env))
        with self.executable(True):
            self.assertEqual(plain, fallow_runner._resolve_executable_binary("fallow", platform="linux", env=env, require_executable=True))


class NormalizeFallowReport(unittest.TestCase):
    def test_none_and_non_objects_yield_empty_report(self):
        for report in (None, [], "text", 5, {}, {"dead_code": "x", "duplication": []}):
            self.assertEqual(EMPTY_REPORT, normalize_fallow_report(report), repr(report))

    def test_empty_sample(self):
        self.assertEqual(EMPTY_REPORT, normalize_fallow_report(SAMPLE_EMPTY))

    def test_findings_sample(self):
        self.assertEqual({
            "summary": {"unused_exports": 1, "unused_files": 1, "duplicates": 1, "circular_dependencies": 1, "total": 4},
            "findings": [
                {"type": "unused_export", "message": "Unused export commitToSubrepo", "file": "sdk/src/query/commit.ts", "line": 289},
                {"type": "unused_file", "message": "Unused file src/orphan.ts", "file": "src/orphan.ts", "line": None},
                {"type": "circular_dependency", "message": "Circular dependency: src/a.ts -> src/b.ts", "file": "src/a.ts", "line": 1},
                {"type": "duplicate_block", "message": "Duplicate block (2 instances)", "file": "gsd-core/bin/lib/config-schema.cjs",
                 "line": 14, "related_file": "sdk/src/query/config-schema.ts"},
            ],
        }, normalize_fallow_report(SAMPLE_FINDINGS))

    def test_edge_case_sample(self):
        report = normalize_fallow_report(SAMPLE_EDGE_CASES)
        self.assertEqual({"unused_exports": 1, "unused_files": 0, "duplicates": 1, "circular_dependencies": 1, "total": 3}, report["summary"])
        export, circular, duplicate = report["findings"]
        self.assertEqual({"type": "unused_export", "message": "Unused export naïveHelper",
                          "file": "src/café/résumé.ts", "line": 0}, export)
        self.assertEqual("Circular dependency: src/a.ts -> src/b.ts -> src/c.ts", circular["message"])
        self.assertEqual({"type": "duplicate_block", "message": "Duplicate block (1 instances)", "file": "src/only-one.ts",
                          "line": 5, "related_file": ""}, duplicate)

    def test_missing_fields_use_defaults(self):
        report = normalize_fallow_report({
            "dead_code": {"unused_exports": [{}, {"export_name": None, "path": None, "line": None}],
                          "unused_files": [{}], "circular_dependencies": [{}, {"files": "nope"}]},
            "duplication": {"clone_groups": [{}, {"instances": [None, {}]}]}})
        self.assertEqual([
            {"type": "unused_export", "message": "Unused export <unknown>", "file": "", "line": None},
            {"type": "unused_export", "message": "Unused export <unknown>", "file": "", "line": None},
            {"type": "unused_file", "message": "Unused file <unknown>", "file": "", "line": None},
            {"type": "circular_dependency", "message": "Circular dependency: ", "file": "", "line": None},
            {"type": "circular_dependency", "message": "Circular dependency: ", "file": "", "line": None},
            {"type": "duplicate_block", "message": "Duplicate block (0 instances)", "file": "", "line": None, "related_file": ""},
            {"type": "duplicate_block", "message": "Duplicate block (2 instances)", "file": "", "line": None, "related_file": ""},
        ], report["findings"])
        self.assertEqual(7, report["summary"]["total"])

    def test_non_object_entries_are_dropped_but_arrays_are_kept(self):
        report = normalize_fallow_report({"dead_code": {"unused_exports": [None, 1, "x", [], {"export_name": "a"}],
                                                        "unused_files": "not-a-list"}})
        self.assertEqual(2, report["summary"]["unused_exports"])
        self.assertEqual(0, report["summary"]["unused_files"])
        self.assertEqual(["Unused export <unknown>", "Unused export a"], [f["message"] for f in report["findings"]])

    def test_non_string_values_stringify_like_javascript(self):
        report = normalize_fallow_report({"dead_code": {
            "unused_exports": [{"export_name": 5}, {"export_name": 1.5}, {"export_name": True}, {"export_name": 2.0}],
            "circular_dependencies": [{"files": ["a", None, 3, ["x", "y"], {}]}]}})
        messages = [finding["message"] for finding in report["findings"]]
        self.assertEqual(["Unused export 5", "Unused export 1.5", "Unused export true", "Unused export 2",
                          "Circular dependency: a ->  -> 3 -> x,y -> [object Object]"], messages)

    def test_summary_counts_filtered_lists(self):
        report = normalize_fallow_report(SAMPLE_FINDINGS)
        self.assertEqual(len(report["findings"]), report["summary"]["total"])


class NormalizeFallowReportFile(FallowCase):
    def write(self, name, content, binary=False):
        path = Path(self.tmp())/name
        if binary:
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return str(path)

    def test_valid_file(self):
        path = self.write("report.json", json.dumps(SAMPLE_FINDINGS))
        self.assertEqual(normalize_fallow_report(SAMPLE_FINDINGS), normalize_fallow_report_file(path))
        self.assertEqual(4, normalize_fallow_report_file(path)["summary"]["total"])

    def test_missing_file_yields_empty_report(self):
        self.assertEqual(EMPTY_REPORT, normalize_fallow_report_file(os.path.join(self.tmp(), "absent.json")))

    def test_invalid_json_yields_empty_report(self):
        self.assertEqual(EMPTY_REPORT, normalize_fallow_report_file(self.write("bad.json", "{not json")))
        self.assertEqual(EMPTY_REPORT, normalize_fallow_report_file(self.write("empty.json", "")))

    def test_bom_yields_empty_report(self):
        self.assertEqual(EMPTY_REPORT, normalize_fallow_report_file(self.write("bom.json", b"\xef\xbb\xbf{}", binary=True)))

    def test_non_object_json_yields_empty_report(self):
        self.assertEqual(EMPTY_REPORT, normalize_fallow_report_file(self.write("null.json", "null")))
        self.assertEqual(EMPTY_REPORT, normalize_fallow_report_file(self.write("list.json", "[1,2]")))

    def test_directory_path_yields_empty_report(self):
        self.assertEqual(EMPTY_REPORT, normalize_fallow_report_file(self.tmp()))


if __name__ == "__main__":
    unittest.main()
