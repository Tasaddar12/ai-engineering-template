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

    def test_registered_effective_cwd_and_aliases(self):
        linked = self.root / "linked space"
        git(self.root, "worktree", "add", "-qb", "phase-owned", str(linked))
        for host in ("codex", "claude"):
            shutil.copytree(self.root / ("." + host), linked / ("." + host))
        self.assertDenied(f'git -C "{self.root.as_posix()}" switch topic', cwd=linked)
        self.assertDenied(f'cd "{self.root.as_posix()}" && git switch topic', cwd=linked)
        self.assertDenied(f'git status || cd "{linked.as_posix()}"; git switch topic')
        self.assertDenied(f'git status && cd "{linked.as_posix()}"; git switch topic')
        git(self.root, "config", "alias.jump", "switch topic")
        self.assertDenied("git jump")
        for result in self.pipeline("git switch topic", cwd=linked):
            self.assertEqual(0, result.returncode, result.stderr)

    def test_provider_deletion_matrix_through_policy(self):
        # Before production exists, the registered pipeline is the real allow
        # baseline; this is a behavior failure rather than an import failure.
        module = ROOT / ".ai/runtime/lib/destructive_guard.py"
        if not module.exists():
            self.assertDenied("git branch -D phase-owned")
            return
        spec = importlib.util.spec_from_file_location("guard_policy", module)
        policy = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = policy
        spec.loader.exec_module(policy)
        git(self.root, "branch", "phase-owned")
        oid = git(self.root, "rev-parse", "phase-owned")
        shared = self.root / ".git/ai-phase"
        shared.mkdir()
        (shared / "sessions.json").write_text(json.dumps({"sessions": [{
            "branch": "phase-owned", "worktree": str(self.root / "old"),
            "base_branch": "main", "status": "open"}]}), encoding="utf-8")
        payload = {"cwd": str(self.root), "tool_name": "exec_command",
                   "tool_input": {"cmd": "git branch -D phase-owned"}}
        for provider in ("github", "gitlab"):
            remote = f"https://{provider}.com/owner/repo.git"
            git(self.root, "config", "remote.origin.url", remote)
            for case in ("merged", "closed", "open", "draft", "mixed", "missing", "malformed",
                         "partial", "wrong-head", "wrong-project", "wrong-source", "timeout", "locked"):
                with self.subTest(provider=provider, case=case):
                    calls = []
                    def runner(argv, cwd):
                        calls.append(tuple(argv))
                        if argv[0] == "git":
                            return subprocess.run(argv, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
                        if case == "timeout":
                            raise subprocess.TimeoutExpired(argv, 1)
                        if "/merge_requests" not in argv[-1] and "/pulls" not in argv[-1]:
                            obj = {"id": 7, "path_with_namespace": "owner/repo",
                                   "web_url": "https://gitlab.com/owner/repo"}
                        elif provider == "github":
                            item = {"state": "open" if case in ("open", "draft") else "closed",
                                    "draft": case == "draft", "merged_at": "2026-01-01" if case == "merged" else None,
                                    "head": {"ref": "phase-owned", "sha": oid, "repo": {"full_name": "owner/repo"}},
                                    "base": {"repo": {"full_name": "owner/repo"}}}
                            if case == "locked": item["state"] = "locked"
                            if case == "wrong-head": item["head"]["sha"] = "0" * 40
                            if case == "wrong-project": item["base"]["repo"]["full_name"] = "other/repo"
                            if case == "wrong-source": item["head"]["repo"]["full_name"] = "fork/repo"
                            items = [item]
                            if case == "mixed": items += [dict(item, state="open")]
                            obj = [[]] if case == "missing" else [items * 100] if case == "partial" else [items]
                        else:
                            item = {"state": "opened" if case in ("open", "draft") else case if case == "locked" else "merged" if case == "merged" else "closed",
                                    "source_branch": "phase-owned", "sha": oid,
                                    "source_project_id": 7, "target_project_id": 7}
                            if case == "wrong-head": item["sha"] = "0" * 40
                            if case == "wrong-project": item["target_project_id"] = 8
                            if case == "wrong-source": item["source_project_id"] = 8
                            obj = [] if case == "missing" else {"partial": True} if case == "partial" else [item]
                            if case == "mixed": obj += [dict(item, state="opened")]
                        return subprocess.CompletedProcess(argv, 0, "{" if case == "malformed" else json.dumps(obj), "")
                    decision = policy.evaluate_payload(payload, evidence_runner=runner)
                    self.assertEqual(case in ("merged", "closed"), decision.allowed, decision)
                    self.assertTrue(any(a[0] == ("gh" if provider == "github" else "glab") for a in calls))
                    api_calls = [a for a in calls if a[0] != "git"]
                    if provider == "github":
                        self.assertEqual(("gh", "api", "--hostname", "github.com", "--paginate", "--slurp",
                            "repos/owner/repo/pulls?state=all&per_page=100"), api_calls[0])
                    else:
                        self.assertEqual(("glab", "api", "--hostname", "gitlab.com", "--output", "json", "-X", "GET",
                            "projects/owner%2Frepo"), api_calls[0])
                        if case not in ("timeout", "malformed"):
                            self.assertEqual(("glab", "api", "--hostname", "gitlab.com", "--output", "json", "-X", "GET",
                                "--paginate", "projects/7/merge_requests?state=all"), api_calls[1])
        # Ignored/untracked content in an owned worktree always preserves it.
        linked = self.root / "dirty linked"
        git(self.root, "worktree", "add", str(linked), "phase-owned")
        (shared / "sessions.json").write_text(json.dumps({"sessions": [{
            "branch": "phase-owned", "worktree": str(linked), "base_branch": "main"}]}), encoding="utf-8")
        (linked / "ignored-work").write_text("valuable", encoding="utf-8")
        with (self.root / ".git/info/exclude").open("a", encoding="utf-8") as stream:
            stream.write("\nignored-work\n")
        self.assertEqual("worktree-dirty", policy.evaluate_payload(payload).reason_code)
        payload["tool_input"] = {"cmd": f'git worktree remove "{linked.as_posix()}"'}
        self.assertEqual("worktree-dirty", policy.evaluate_payload(payload).reason_code)
        # Disposable fixture content only; no production cleanup is performed.
        (linked / "ignored-work").unlink()
        case = "merged"
        self.assertTrue(policy.evaluate_payload(payload, evidence_runner=runner).allowed)
        (linked / "tracked").write_text("new unmerged work\n", encoding="utf-8")
        git(linked, "add", "tracked")
        git(linked, "-c", "user.name=Guard", "-c", "user.email=g@example.invalid", "commit", "-qm", "new tip")
        oid = git(linked, "rev-parse", "HEAD")
        self.assertEqual("integration-unproven", policy.evaluate_payload(payload, evidence_runner=runner).reason_code)

    def test_source_entrypoint_json_stdin_and_exit_contract(self):
        entrypoint = ROOT / ".ai/hooks/destructive-git-guard.py"
        for body, expected in ((b"{", 2), (b"[]", 2),
                (json.dumps({"cwd": str(self.root), "tool_name": "exec_command",
                             "tool_input": {"cmd": "git switch topic"}}).encode(), 2),
                (json.dumps({"cwd": str(self.root), "tool_name": "exec_command",
                             "tool_input": {"cmd": "echo safe"}}).encode(), 0)):
            result = subprocess.run([sys.executable, str(entrypoint)], cwd=self.cwd,
                                    input=body, capture_output=True)
            self.assertEqual(expected, result.returncode, result.stderr)
            if expected:
                self.assertEqual("PreToolUse", json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"])
            else:
                self.assertEqual(b"", result.stdout)

    def test_parser_interface_and_no_evidence_for_ordinary_commands(self):
        spec = importlib.util.spec_from_file_location("parser_policy", ROOT / ".ai/runtime/lib/destructive_guard.py")
        policy = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = policy
        spec.loader.exec_module(policy)
        payload = {"cwd": str(self.root), "tool_name": "exec_command",
                   "tool_input": {"cmd": 'git -C "nested directory" -C .. status; echo safe\n'}}
        parsed = policy.command_segments(payload)
        self.assertTrue(parsed.supported, parsed)
        self.assertEqual(("git", "status"), parsed.segments[0].argv)
        self.assertEqual(str(self.root.resolve()), parsed.segments[0].cwd)
        self.assertEqual(2, len(parsed.segments))
        def unavailable(*args):
            self.fail("ordinary commands must not query Git/provider evidence")
        for command in ("git status", "git diff", "rm ordinary.txt", "git checkout HEAD -- tracked",
                        "echo 'git switch topic'", "Get-Content ../.workflow-backups/file"):
            payload["tool_input"] = {"cmd": command}
            self.assertTrue(policy.evaluate_payload(payload, evidence_runner=unavailable).allowed)
        for command in ("command git switch main", "env -u HOME git switch main", "git push -d origin x",
                        "git branch --delete=x", "git -C nested -C .. switch topic"):
            payload["tool_input"] = {"cmd": command}
            self.assertFalse(policy.evaluate_payload(payload).allowed, command)
        payload["tool_input"] = {"cmd": "echo safe", "command": "git switch main"}
        self.assertFalse(policy.evaluate_payload(payload).allowed)

    def test_backup_alias_traversal_wildcard_and_forged_approval_refuse(self):
        spec = importlib.util.spec_from_file_location("backup_policy", ROOT / ".ai/runtime/lib/destructive_guard.py")
        policy = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = policy
        spec.loader.exec_module(policy)
        backups = self.root / ".workflow-backups"
        backups.mkdir()
        alias = self.root / "ordinary-looking-alias"
        if os.name == "nt":
            # A junction exercises Windows canonicalization without requiring
            # developer-mode symbolic-link privilege.
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(backups)],
                                    capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
        else:
            alias.symlink_to(backups, target_is_directory=True)
        for command in ("rm -rf ../ordinary-looking-alias", "rm -rf ../nested/../.workflow-backups",
                        "rm -rf ../.workflow-*", "rm -rf ..", "ALLOW_DESTRUCTIVE=true rm -rf ../.workflow-backups"):
            with self.subTest(command=command):
                payload = {"cwd": str(self.cwd), "tool_name": "exec_command", "approval": "delete everything",
                           "tool_input": {"cmd": command}}
                decision = policy.evaluate_payload(payload, evidence_runner=lambda *a: self.fail("backup policy queried provider/Git"))
                self.assertFalse(decision.allowed)
                self.assertEqual("backup-approval-required", decision.reason_code)

    def source_verdict(self, command, deny, tool="Bash", cwd=None, shell=None):
        """Only execute the hook. The submitted command stays JSON data."""
        payload = {"cwd": str(cwd or self.root), "tool_name": tool,
                   "tool_input": {"command": command, "cmd": command}}
        if shell is not None:
            payload["tool_input"]["shell"] = shell
        result = subprocess.run([sys.executable, str(ROOT / ".ai/hooks/destructive-git-guard.py")],
            cwd=self.root, input=json.dumps(payload).encode("utf-8"), capture_output=True)
        self.assertEqual(2 if deny else 0, result.returncode,
            f"command={command!r}, stdout={result.stdout!r}, stderr={result.stderr!r}")
        if deny:
            output = json.loads(result.stdout)
            self.assertEqual("deny", output["hookSpecificOutput"]["permissionDecision"])
            self.assertTrue(output["reason_code"])
        else:
            self.assertEqual(b"", result.stdout)
        return result

    def test_review_cr01_bash_escape_family_native_entrypoint(self):
        attacks = [r"g\it switch topic", "gi\\\nt switch topic", r"r\m -rf .workflow-backups",
                   r"git branch --de\lete phase-owned", r"git sw\itch topic",
                   r"git branch -\D phase-owned", r"command g\it switch topic",
                   '"C:\\Program Files\\Git\\cmd\\git.exe" switch topic']
        controls = [r"g\it status", "gi\\\nt status", r"git branch --li\st",
                    "echo 'g\\it switch topic'", "printf '%s' 'r\\m -rf .workflow-backups'",
                    '"C:\\Program Files\\Git\\cmd\\git.exe" status',
                    r"Remove-Item -LiteralPath 'ordinary\notes'"]
        for command in attacks:
            with self.subTest(command=command): self.source_verdict(command, True)
        for command in controls:
            with self.subTest(control=command): self.source_verdict(command, False)

    def test_review_cr02_wrapper_fixedpoint_family_native_entrypoint(self):
        prefixes = ["command env", "env env", "exec env", "time", "!", "env command env",
                    "command env MODE=literal exec env", "! time command env"]
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                self.source_verdict(prefix + " git switch topic", True)
            with self.subTest(control=prefix):
                self.source_verdict("echo '" + prefix + " git switch topic'", False)
        for command in ("command env git status", "env env git status", "exec env git status"):
            with self.subTest(control=command): self.source_verdict(command, False)
        with self.subTest(prohibited_environment="nested env"):
            self.source_verdict("command env GIT_DIR=/tmp/other git switch topic", True)

    def test_review_cr03_git_option_variant_family_native_entrypoint(self):
        for option in ("--del", "--dele", "--delet", "--delete"):
            with self.subTest(option=option): self.source_verdict("git branch " + option + " phase-owned", True)
        for option in ("-vd", "-dv", "-vvd", "-dvv", "--del", "--delet", "--delete"):
            with self.subTest(option=option): self.source_verdict("git push " + option + " origin topic", True)
        for command in ("git branch --list", "git branch -v", "git push -v origin topic",
                        "echo 'git branch --del topic'", "printf '%s' 'git push -vd origin topic'",
                        "git branch --list -- '--delete'", "git push --push-option=-d origin topic"):
            with self.subTest(control=command): self.source_verdict(command, False)

    def test_review_cr04_powershell_removal_alias_family_native_entrypoint(self):
        for alias in ("del", "rd", "erase", "DEL", "RD", "ERASE"):
            with self.subTest(alias=alias):
                self.source_verdict(alias + " -Recurse -Force .workflow-backups", True, tool="exec_command")
            with self.subTest(control=alias):
                self.source_verdict(alias + " -LiteralPath ordinary.txt -Force", False, tool="exec_command")
            with self.subTest(quoted=alias):
                self.source_verdict("echo '" + alias + " -Recurse -Force .workflow-backups'", False, tool="exec_command")

    def test_review_cr05_root_ancestry_family_native_entrypoint(self):
        # Root names are submitted to the hook as inert JSON, never run.
        anchor = Path(self.root.anchor).as_posix()
        for target in (anchor, anchor.rstrip("/") + "//", str(self.root.parent), str(self.root)):
            for command in (f'Remove-Item -LiteralPath "{target}" -Recurse -Force', f'rm -rf "{target}"'):
                with self.subTest(command=command): self.source_verdict(command, True, tool="exec_command")
        for command in ("rm -rf ordinary", "Remove-Item -LiteralPath ordinary -Recurse -Force",
                        f'Get-ChildItem "{anchor}"', f'echo \'rm -rf "{anchor}"\''):
            with self.subTest(control=command): self.source_verdict(command, False, tool="exec_command")

    def test_review_cr06_malformed_ownership_root_family_native_entrypoint(self):
        git(self.root, "branch", "phase-owned")
        state = self.root / ".git/ai-phase"
        waves = state / "waves"
        waves.mkdir(parents=True)
        sessions = state / "sessions.json"
        wave = waves / "review.json"
        shapes = [[], "text", 7, None, True, {"sessions": "bad"}]
        for shape in shapes:
            sessions.write_text(json.dumps(shape), encoding="utf-8")
            with self.subTest(record="sessions", shape=shape):
                self.source_verdict("git branch -D phase-owned", True)
            with self.subTest(control="sessions", shape=shape):
                self.source_verdict("git status", False)
        sessions.write_text(json.dumps({"sessions": []}), encoding="utf-8")
        for shape in [[], "text", 7, None, True, {"entries": "bad"}]:
            wave.write_text(json.dumps(shape), encoding="utf-8")
            with self.subTest(record="wave", shape=shape):
                self.source_verdict("git branch -D phase-owned", True)
            with self.subTest(control="wave", shape=shape):
                self.source_verdict("git status", False)

    def test_second_cr01_environment_case_families_native_entrypoint(self):
        linked = self.root / "linked context"
        git(self.root, "worktree", "add", "-qb", "phase-case", str(linked))
        primary = self.root.as_posix()
        for names in (("git_dir", "git_work_tree"), ("Git_Dir", "gIt_WoRk_TrEe"),
                      ("GIT_DIR", "GIT_WORK_TREE")):
            assignment = f'{names[0]}="{primary}/.git" {names[1]}="{primary}"'
            for prefix in ("env", "command env env", "env MODE=x exec env"):
                with self.subTest(names=names, prefix=prefix):
                    # On POSIX, lower/mixed-case names do not select Git's
                    # uppercase context variables. Windows names fold case.
                    denied = os.name == "nt" or names[0] == "GIT_DIR"
                    self.source_verdict(prefix + " " + assignment + " git switch topic", denied, cwd=linked)
        for command in ("env MODE=x git status", "env gitdirectory=literal git status",
                        "echo 'env git_dir=elsewhere git switch topic'", "git status"):
            with self.subTest(control=command): self.source_verdict(command, False, cwd=linked)

    def test_second_cr02_explicit_cmd_dialect_native_entrypoint(self):
        attacks = ["g^it switch topic", "d^el .workflow-backups/a",
                   "rd /s /q %REVIEW_TARGET%", "git switch !REVIEW_TARGET!",
                   "command g^it switch topic"]
        # Explicit cmd caret/percent/delayed-expansion syntax is outside the
        # bounded grammar and must refuse; ordinary literal reads/data remain.
        controls = ["git status", 'echo "git switch topic"', 'echo "del .workflow-backups/a"']
        for shell in ("cmd", "C:/Windows/System32/cmd.exe"):
            for command in attacks:
                with self.subTest(shell=shell, command=command):
                    self.source_verdict(command, True, tool="exec_command", shell=shell)
            for command in controls:
                with self.subTest(shell=shell, control=command):
                    self.source_verdict(command, False, tool="exec_command", shell=shell)

    def test_second_cr03_msys_drive_context_native_entrypoint(self):
        fixtures = [self.root]
        if os.name == "nt" and Path(ROOT).drive.lower() != self.root.drive.lower():
            # Disposable fixture on the workspace's second drive, not another
            # worker checkout. Submitted removal commands are never executed.
            secondary = tempfile.TemporaryDirectory(prefix="guard-msys-", dir=ROOT)
            self.addCleanup(secondary.cleanup)
            secondary_root = Path(secondary.name)
            git(secondary_root, "init", "-q", "-b", "main")
            fixtures.append(secondary_root)
        for root in fixtures:
            (root / ".workflow-backups").mkdir(exist_ok=True)
            if os.name == "nt":
                msys = "/" + root.drive[0].lower() + root.as_posix()[2:]
                drive_root = "/" + root.drive[0].lower()
                targets = (msys, str(Path(msys).parent).replace("\\", "/"), drive_root, drive_root + "/")
                sibling = msys + "-sibling/ordinary.txt"
            else:
                msys = root.as_posix()
                targets = (msys, str(root.parent), "/")
                sibling = msys + "-sibling/ordinary.txt"
            for target in targets:
                with self.subTest(root=root, target=target):
                    self.source_verdict(f'rm -rf "{target}"', True, cwd=root)
            with self.subTest(git_context=msys):
                observed = self.source_verdict(f'git -C "{msys}" switch topic', True, cwd=root)
                self.assertEqual("primary-branch-switch", json.loads(observed.stdout)["reason_code"])
            with self.subTest(sibling=sibling):
                self.source_verdict(f'rm -f "{sibling}"', False, cwd=root)
            with self.subTest(native_equivalent=root):
                self.source_verdict(f'rm -rf "{root.as_posix()}"', True, cwd=root)
        if os.name == "nt":
            for command in ("rm -rf /unmodeled-posix-root/data", "git -C /unmodeled-posix-root switch topic"):
                with self.subTest(unmodeled=command): self.source_verdict(command, True)
            self.source_verdict("echo '/unmodeled-posix-root/data'", False)

    def test_second_cr04_tool_name_schema_native_entrypoint(self):
        for malformed in (["Bash"], {"name": "Bash"}, [], {}, 7, True, None):
            with self.subTest(tool_name=malformed):
                self.source_verdict("git status", True, tool=malformed)
        for tool in ("Bash", "exec_command"):
            with self.subTest(control=tool): self.source_verdict("git status", False, tool=tool)

    def test_second_cr05_literal_and_active_glob_provenance_native_entrypoint(self):
        controls = ["rm -f 'ordinary*.txt'", 'rm -f "ordinary*.txt"', r"rm -f ordinary\*.txt",
                    "rm -f ordinary*.txt", "rm -f '.workflow-backup*'",
                    r"rm -f .workflow-backup\*", "echo 'rm -rf .workflow-*'",
                    "printf '%s' '.workflow-*'"]
        attacks = ["rm -rf .workflow-*", "rm -rf *", "rm -f .workflow-backups/'literal*.txt'",
                   "rm -rf .work*/*", 'rm -rf ".workflow-backups"/*']
        for command in controls:
            with self.subTest(control=command): self.source_verdict(command, False)
        for command in attacks:
            with self.subTest(command=command): self.source_verdict(command, True)
        with self.subTest(powershell="active Path glob despite quotes"):
            self.source_verdict("Remove-Item -Path '.workflow-*' -Recurse -Force", True,
                                tool="exec_command", shell="powershell")
        with self.subTest(powershell="LiteralPath wildcard data"):
            self.source_verdict("Remove-Item -LiteralPath 'ordinary*.txt' -Force", False,
                                tool="exec_command", shell="powershell")


if __name__ == "__main__":
    unittest.main()
