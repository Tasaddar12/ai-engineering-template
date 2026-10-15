"""Destructive preflight attacks; commands under test are never executed."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import test_install
installer = test_install.installer

ROOT = Path(__file__).resolve().parents[1]


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", check=True).stdout.strip()


class RegisteredGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="guard café ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        git(self.root, "init", "-q", "-b", "main")
        (self.root / "tracked").write_text("safe\n", encoding="utf-8")
        git(self.root, "add", "tracked")
        git(self.root, "-c", "user.name=Guard", "-c", "user.email=g@example.invalid",
            "commit", "-qm", "fixture")
        self.cwd = self.root / "nested directory"
        self.cwd.mkdir()
        self.launcher = test_install.InstallerTests(methodName="test_registered_hooks_execute_from_installed_subdirectory")
        for host in ("codex", "claude"):
            shutil.copytree(ROOT / ".ai", self.root / ("." + host),
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    def pipeline(self, command, host="codex", tool="exec_command", cwd=None):
        payload = {"cwd": str(cwd or self.cwd), "tool_name": tool,
                   "hook_event_name": "PreToolUse", "tool_input": {"command": command, "cmd": command}}
        results = []
        for group in installer.hook_settings(host)["hooks"].get("PreToolUse", []):
            if re.search(group.get("matcher", ".*"), tool):
                for handler in group["hooks"]:
                    results.append(subprocess.run(self.launcher.launcher_argv(host, handler),
                        cwd=cwd or self.cwd, input=json.dumps(payload).encode(), capture_output=True))
        return results

    def assertDenied(self, command, **kwargs):
        results = self.pipeline(command, **kwargs)
        denied = [r for r in results if r.returncode == 2]
        self.assertTrue(denied, f"expected registered refusal, actual allow: {command}; "
                        + repr([(r.returncode, r.stdout, r.stderr) for r in results]))
        body = json.loads(denied[0].stdout)
        self.assertEqual("deny", body["hookSpecificOutput"]["permissionDecision"])
        self.assertTrue(body["reason_code"])

    def test_registered_pipeline_denies_primary_switch(self):
        for host, tool in (("codex", "exec_command"), ("codex", "shell_command"),
                           ("codex", "shell"), ("claude", "Bash")):
            with self.subTest(host=host, tool=tool):
                self.assertDenied("git switch topic", host=host, tool=tool)

    def test_registered_attack_matrix_refuses_before_mutation(self):
        attacks = [
            "git checkout topic", "git checkout -b topic", "git checkout -B topic",
            "git checkout --orphan topic", "git switch -c topic", "git switch -C topic",
            "git switch --detach HEAD", '"git" switch "topic"',
            "git status && git switch topic", "git status || git switch topic",
            "git status; git switch topic", "git status\ngit switch topic",
            "git status | git switch topic", "env MODE=x git switch topic",
            "git branch -D topic", "git branch -df topic", "git branch --delete a b",
            "git push origin --delete topic", "git push origin :topic",
            "git update-ref -d refs/heads/topic", "git branch -M topic",
            "git worktree remove --force ../unknown", "git --work-tree=. switch topic",
            "bash -c 'git switch topic'", "sh script.sh", "pwsh -Command 'git switch topic'",
            "powershell -File script.ps1", "cmd /c git switch topic", "eval 'git switch topic'",
            "source script.sh", "git switch $BRANCH", "git switch $(echo topic)",
            "git switch `echo topic`", "for x in topic; do git switch $x; done",
            "git switch 'unterminated", "rm -rf ../.workflow-backups",
            "rm -- ../.workflow-backups/a", "Remove-Item -LiteralPath '../.workflow-backups/a' -Recurse -Force",
            "rm -rf ..", "rm -rf ../.workflow-*", "GIT_DIR=/tmp/other git switch topic",
        ]
        for command in attacks:
            with self.subTest(command=command):
                self.assertDenied(command)
        self.assertEqual("main", git(self.root, "branch", "--show-current"))

    def test_registered_precision_matrix_allows_literal_data_and_restores(self):
        commands = ["git status", "git show HEAD", "git diff", "git branch --list",
                    "git branch -a", "git show-ref", "git worktree list", "git worktree add ../new",
                    "git checkout -- tracked", "git checkout HEAD -- 'topic file'",
                    "git checkout -- -b", "git checkout -- main", "git checkout HEAD -- --orphan",
                    "echo 'git switch topic'", "printf '%s' 'git switch topic'", "rm ordinary.txt",
                    "Get-Content ../.workflow-backups/a", "ls ../.workflow-backups"]
        for command in commands:
            with self.subTest(command=command):
                for result in self.pipeline(command):
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual(b"", result.stdout)


if __name__ == "__main__":
    unittest.main()
