import importlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
LIB = SOURCE / "engineer" / "bin" / "lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package; `.ai/runtime/lib` also claims the name `lib`."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB / "__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib." + name)


shell = _load("posix_shell")


class WslLauncherRejection(unittest.TestCase):
    def test_system_directories_are_launchers(self):
        for path in (r"C:\Windows\System32\bash.exe", "C:/Windows/system32/bash.exe", r"C:\Windows\SysWOW64\bash.exe",
                     r"C:\Windows\Sysnative\bash.exe", r"C:\Users\x\AppData\Local\Microsoft\WindowsApps\bash.exe"):
            with self.subTest(path=path):
                self.assertTrue(shell.is_wsl_launcher(path))

    def test_git_for_windows_is_not_a_launcher(self):
        for path in (r"C:\Program Files\Git\bin\bash.exe", "C:/Program Files/Git/usr/bin/sh.exe", "/usr/bin/bash"):
            with self.subTest(path=path):
                self.assertFalse(shell.is_wsl_launcher(path))


class WindowsResolution(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()

    def touch(self, *parts):
        path = self.base.joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
        return path

    def test_system32_candidate_is_rejected_even_when_listed_first(self):
        launcher = self.touch("Windows", "System32", "bash.exe")
        git_bash = self.touch("Git", "bin", "bash.exe")
        self.assertEqual(str(git_bash), shell.find_posix_shell("bash", [launcher, git_bash], windows=True))

    def test_only_a_launcher_means_no_shell(self):
        launcher = self.touch("Windows", "System32", "bash.exe")
        self.assertIsNone(shell.find_posix_shell("bash", [launcher], windows=True))

    def test_missing_candidates_are_skipped(self):
        git_bash = self.touch("Git", "usr", "bin", "bash.exe")
        found = shell.find_posix_shell("bash", [self.base / "absent" / "bash.exe", git_bash], windows=True)
        self.assertEqual(str(git_bash), found)

    def test_git_roots_yield_ordered_candidates_before_path_matches(self):
        root = self.base / "Git"
        listed = shell.windows_candidates("bash", [root], [r"C:\Windows\System32\bash.exe"])
        self.assertEqual([root / "bin" / "bash.exe", root / "usr" / "bin" / "bash.exe", Path(r"C:\Windows\System32\bash.exe")], listed)
        self.assertEqual([root / "usr" / "bin" / "sh.exe", root / "bin" / "sh.exe"], shell.windows_candidates("sh", [root]))

    def test_program_files_git_is_a_root(self):
        roots = shell.git_roots({"ProgramFiles": str(self.base)}, which=lambda name: None)
        self.assertIn(self.base / "Git", roots)


class HostResolution(unittest.TestCase):
    def test_resolved_shell_is_absolute_and_never_a_launcher(self):
        for name in ("bash", "sh"):
            with self.subTest(name=name):
                found = shell.find_posix_shell(name)
                if found is None:
                    self.skipTest(name + " unavailable")
                self.assertTrue(os.path.isabs(found))
                self.assertFalse(shell.is_wsl_launcher(found))


if __name__ == "__main__":
    unittest.main()
