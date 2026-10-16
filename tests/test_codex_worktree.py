"""Codex startup and synchronous guard contracts.

The retained installed tracer dispatches generated hooks locally. It is not a
native Codex receipt; actual native generated-handler proof belongs to Task6B.
"""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".ai/runtime"))


def command(*argv, cwd=None, **kwargs):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", timeout=60, **kwargs)


class InstalledTracer(unittest.TestCase):
    def test_codex_worktree_installed_primary_shell_is_denied(self):
        with tempfile.TemporaryDirectory(prefix="codex-installed-tracer-") as temporary:
            target = Path(temporary).resolve() / "project with spaces"
            installed = command(sys.executable, str(ROOT / ".ai/install.py"),
                                "--source", str(ROOT), "--ref", "HEAD", "--target", str(target),
                                "--host", "codex", "--skip-deps")
            self.assertEqual(0, installed.returncode, installed.stderr)
            self.assertEqual(0, command("git", "init", "-q", str(target)).returncode)
            sentinel = target / "source.txt"
            sentinel.write_text("original\n", encoding="utf-8")
            for args in (("config", "user.name", "Tracer"),
                         ("config", "user.email", "tracer@example.invalid"),
                         ("add", "."), ("commit", "-qm", "installed fixture")):
                result = command("git", *args, cwd=target)
                self.assertEqual(0, result.returncode, result.stderr)
            settings = tomllib.loads((target / ".codex/config.toml").read_text(encoding="utf-8"))
            shell = 'python -c "from pathlib import Path; Path(\'source.txt\').write_text(\'MUTATED\')"'
            payload = json.dumps({"hook_event_name": "PreToolUse", "cwd": str(target),
                                  "tool_name": "Bash", "tool_input": {"command": shell}})
            environment = dict(os.environ)
            environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment["PATH"]
            denied = False
            dispatched = 0
            for group in settings["hooks"]["PreToolUse"]:
                matcher = group.get("matcher", "*")
                if matcher != "*" and not re.search(matcher, "Bash"):
                    continue
                for handler in group["hooks"]:
                    if os.name == "nt":
                        argv = ["powershell", "-NoProfile", "-Command",
                                handler.get("commandWindows", handler["command"])]
                    else:
                        argv = ["bash", "-c", handler["command"]]
                    observed = command(*argv, cwd=target, input=payload, env=environment)
                    self.assertIn(observed.returncode, (0, 2), "installed pipeline setup: " + observed.stderr)
                    dispatched += 1
                    if observed.returncode == 2:
                        denied = True
                        break
                if denied:
                    break
            self.assertGreater(dispatched, 0, "installed Bash dispatch must succeed")
            if not denied:
                bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else "bash"
                acted = command(bash, "-c", shell, cwd=target, env=environment)
                self.assertEqual(0, acted.returncode, acted.stderr)
            self.assertEqual("original\n", sentinel.read_text(encoding="utf-8"),
                             "installed primary Bash mutation proceeded after successful setup")


if __name__ == "__main__":
    unittest.main()
