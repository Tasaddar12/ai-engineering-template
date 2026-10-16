"""Codex startup and synchronous guard contracts.

The retained installed tracer dispatches generated hooks locally. It is not a
native Codex receipt; actual native generated-handler proof belongs to Task6B.
"""
from pathlib import Path
from contextlib import ExitStack, chdir
import copy
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

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


class SafeLiteralLauncherTests(unittest.TestCase):
    """Isolated launcher regressions with every process boundary stubbed."""

    def setUp(self):
        self.runtime = importlib.import_module("lib.codex_worktree")
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path("C:/synthetic/repository")
        self.destination = self.root / ".worktrees/quick-unit"
        self.definitions = {event: "synthetic-guard-" + event
                            for event in self.runtime.EVENTS}
        self.caller = {"root": self.root, "common": self.root, "primary": self.root}
        self.destination_info = {"root": self.destination, "common": self.root,
                                 "primary": self.root}
        self.record = {"synthetic": "validated-session"}
        self.budget = type("StubBudget", (), {"git": lambda *_args, **_kwargs: "a" * 40})()
        self.open_session = self.stack.enter_context(patch.object(
            self.runtime.worktrees, "open_session", return_value={"worktree": self.destination}))
        self.preflight = self.stack.enter_context(patch.object(
            self.runtime, "NativePreflight", side_effect=AssertionError("preflight must not run")))
        self.process_call = self.stack.enter_context(patch.object(
            self.runtime.subprocess, "call", side_effect=AssertionError("final launch must not run")))
        self.stack.enter_context(patch.object(self.runtime.prewrite, "unit",
                                              side_effect=lambda kind, label: (kind, label)))
        self.stack.enter_context(patch.object(self.runtime.prewrite, "Budget",
                                              return_value=self.budget))
        self.stack.enter_context(patch.object(self.runtime.prewrite, "facts",
                                              side_effect=[self.caller, self.destination_info,
                                                           self.destination_info]))
        self.stack.enter_context(patch.object(self.runtime.prewrite, "existing_session",
                                              return_value=None))
        self.stack.enter_context(patch.object(self.runtime.prewrite, "target_path",
                                              return_value=self.destination))
        self.stack.enter_context(patch.object(self.runtime, "Workspace", return_value=object()))
        self.stack.enter_context(patch.object(self.runtime, "installed_snapshot",
                                              return_value=("stable-snapshot", self.definitions)))
        self.stack.enter_context(patch.object(self.runtime, "validate_root",
                                              return_value=self.record))
        self.stack.enter_context(patch.object(self.runtime, "check_launchability"))
        self.stack.enter_context(patch.object(self.runtime.shutil, "which",
                                              return_value="C:/synthetic/bin/codex.cmd"))

    def test_safe_literal_launcher_rejects_batch_before_session_or_native_entrypoints(self):
        from contextlib import redirect_stderr
        from io import StringIO

        stderr = StringIO()
        with redirect_stderr(stderr):
            result = self.runtime.launcher_main(["quick", "unit", "--prompt",
                                                 "literal 100% punctuation: !?,"])

        self.assertEqual(2, result)
        self.assertIn("unsupported Windows batch launcher", stderr.getvalue())
        self.open_session.assert_not_called()
        self.preflight.assert_not_called()
        self.process_call.assert_not_called()

    def test_safe_literal_launcher_forwards_prompt_to_direct_executable_as_one_argument(self):
        executable = "C:/synthetic/bin/codex.exe"
        prompt = "literal 100% punctuation: !?,"
        native = type("StubNative", (), {"request": lambda *_args, **_kwargs: {}})()
        self.runtime.shutil.which.return_value = executable
        self.preflight.side_effect = None
        self.preflight.return_value.__enter__.return_value = native
        self.process_call.side_effect = None
        self.process_call.return_value = 0
        self.stack.enter_context(patch.object(self.runtime, "check_hooks"))
        self.stack.enter_context(patch.object(self.runtime, "policy_snapshot", return_value={"safe": True}))

        result = self.runtime.launcher_main(["quick", "unit", "--prompt", prompt])

        self.assertEqual(0, result)
        self.preflight.assert_called_once_with(executable, self.destination)
        argv = self.process_call.call_args.args[0]
        self.assertEqual([executable, "--cd", str(self.destination), "--enable", "hooks",
                          "--", prompt], argv)
        self.assertNotIn("shell", self.process_call.call_args.kwargs)


class LifecycleNoteAllowanceTests(unittest.TestCase):
    """Primary lifecycle/note decisions without process or Git boundaries."""

    def setUp(self):
        self.runtime = importlib.import_module("lib.codex_worktree")
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-lifecycle-stubs-")
        self.addCleanup(self.temporary.cleanup)
        self.primary = Path(self.temporary.name).resolve()
        self.info = {"root": self.primary, "primary": self.primary}

    def test_primary_prompt_note_then_source_write_denial(self):
        from lib.results import VerbError

        with patch.object(self.runtime.prewrite, "Budget", return_value=object()), \
                patch.object(self.runtime.prewrite, "facts", return_value=self.info), \
                patch.object(self.runtime.prewrite, "classification", side_effect=("note", "source")) as classify:
            with chdir(self.primary):
                for event in ("SessionStart", "UserPromptSubmit"):
                    self.runtime.hook_decision({
                        "hook_event_name": event,
                        "cwd": str(self.primary),
                        "prompt": "Please read the project and save a brief task note.",
                    })
                self.runtime.hook_decision({
                    "hook_event_name": "PreToolUse",
                    "cwd": str(self.primary),
                    "tool_name": "Write",
                    "tool_input": {"file_path": ".planning/scratchpads/task.md", "content": "note"},
                })
                with self.assertRaisesRegex(VerbError, "primary refused"):
                    self.runtime.hook_decision({
                        "hook_event_name": "PreToolUse",
                        "cwd": str(self.primary),
                        "tool_name": "Write",
                        "tool_input": {"file_path": "source.py", "content": "change"},
                    })

        self.assertEqual(2, classify.call_count)


class RuntimeTests(unittest.TestCase):
    """Real Git units; deterministic native RPC fixtures and SIMULATED launch spy."""
    def setUp(self):
        self.runtime = importlib.import_module("lib.codex_worktree")
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-runtime-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "repo"
        self.root.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Runtime Fixture")
        self.git("config", "user.email", "runtime@example.invalid")
        self.git("config", "core.autocrlf", "false")
        (self.root / ".planning/phases/01-test").mkdir(parents=True)
        (self.root / ".planning/config.yaml").write_text("worktree:\n  root: .worktrees\n", encoding="utf-8")
        (self.root / ".gitignore").write_text(".worktrees/\nignored.bin\n.planning/scratchpads/\n", encoding="utf-8")
        (self.root / ".gitattributes").write_text("* -text\n", encoding="utf-8")
        (self.root / "source.txt").write_bytes(b"committed\n")
        (self.root / ".planning/phases/01-test/01-CONTEXT.md").write_text("fixture phase", encoding="utf-8")
        (self.root / ".planning/ROADMAP.md").write_text("# Roadmap\n\n### Phase 1: Test\n\n**Goal:** Fixture\n", encoding="utf-8")
        shutil.copytree(ROOT / ".ai/runtime", self.root / ".codex/runtime",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (self.root / ".codex/hooks").mkdir()
        shutil.copy2(ROOT / ".ai/hooks/codex-worktree.py", self.root / ".codex/hooks/codex-worktree.py")
        (self.root / ".codex/codex-worktree.py").write_text("# simulated B entry-point dependency\n", encoding="utf-8")
        posix, windows = self.runtime.guard_commands()
        groups = []
        for event in self.runtime.EVENTS:
            groups += ["[[hooks." + event + "]]"]
            if event == "PreToolUse":
                groups += ['matcher = "*"']
            groups += ["[[hooks." + event + ".hooks]]", 'type = "command"',
                       "command = " + json.dumps(posix), "commandWindows = " + json.dumps(windows), "timeout = 30"]
        self.config = self.root / ".codex/config.toml"
        self.config.write_text('model = "personal-model"\nmodel_reasoning_effort = "high"\n'
                               '[features]\nhooks = false\n' + "\n".join(groups) + "\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "installed deterministic fixture")
        self.revision = self.git("rev-parse", "HEAD")
        self.policy = {"sandbox_mode": "workspace-write", "approval_policy": {
            "granular": {"mcp_elicitations": False, "rules": True, "sandbox_approval": True,
                         "request_permissions": False, "skill_approval": False}},
            "sandbox_workspace_write": {"network_access": False, "exclude_slash_tmp": True,
                                        "exclude_tmpdir_env_var": True, "writable_roots": [str(self.base / "notes")]},
            "approvals_reviewer": "auto_review"}
        self.requests = []
        self.launched = []
        self.destination = None
        self.change_rpc = None

    def git(self, *argv, cwd=None):
        result = command("git", *argv, cwd=cwd or self.root)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.strip()

    def fake_native(self, executable, destination):
        case = self
        self.destination = destination
        class RPC:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def request(self, method, params):
                case.requests.append((method, copy.deepcopy(params)))
                if method == "config/read":
                    response = {"config": copy.deepcopy(case.policy), "origins": {}}
                else:
                    command_text = case.runtime.guard_commands()[os.name == "nt"]
                    response = {"data": [{"cwd": str(destination), "warnings": [], "errors": [], "hooks": [
                        {"eventName": native, "handlerType": "command", "command": command_text,
                         "enabled": True, "isManaged": False, "key": event, "source": "project",
                         "sourcePath": str(destination / ".codex/config.toml"), "timeoutSec": 30,
                         "trustStatus": "trusted", "currentHash": "native-opaque-hash", "displayOrder": index,
                         "matcher": "*" if event == "PreToolUse" else None}
                        for index, (event, native) in enumerate(case.runtime.EVENTS.items())]}]}
                return case.change_rpc(method, params, response) if case.change_rpc else response
        return RPC()

    def launch(self, *args):
        def simulated_native(argv, cwd):
            self.launched.append((list(argv), Path(cwd)))
            return 0
        with chdir(self.root), patch.object(self.runtime.shutil, "which", return_value="SIMULATED-native-codex"), \
                patch.object(self.runtime, "NativePreflight", side_effect=self.fake_native), \
                patch.object(self.runtime, "check_launchability"), \
                patch.object(self.runtime.subprocess, "call", side_effect=simulated_native):
            return self.runtime.launcher_main(list(args or ("quick", "unit")))

    def event(self, cwd, tool="Bash", data=None, event="PreToolUse"):
        return {"hook_event_name": event, "cwd": str(cwd), "tool_name": tool,
                "tool_input": data if data is not None else {"command": "python -m unittest"}}

    def assert_refused(self, event, cwd=None):
        from lib.results import VerbError
        with chdir(cwd or event["cwd"]), self.assertRaises(VerbError):
            self.runtime.hook_decision(event)

    def assert_allowed(self, event, message):
        from lib.results import VerbError
        refusal = None
        with chdir(event["cwd"]):
            try:
                self.runtime.hook_decision(event)
            except VerbError as exc:
                refusal = str(exc)
        self.assertIsNone(refusal, message + ": " + str(refusal))

    def primary_snapshot(self):
        paths = ("source.txt", "staged.txt", "untracked.txt", "ignored.bin", ".codex/config.toml")
        return ({name: (self.root / name).read_bytes() for name in paths if (self.root / name).exists()},
                (self.root / ".git/index").read_bytes())

    def test_runtime_selection_native_spy_guard_and_reuse_preserve_primary(self):
        (self.root / "staged.txt").write_bytes(b"staged primary")
        self.git("add", "staged.txt")
        (self.root / "source.txt").write_bytes(b"unstaged primary")
        (self.root / "untracked.txt").write_bytes(b"untracked primary")
        (self.root / "ignored.bin").write_bytes(b"ignored primary")
        before = self.primary_snapshot()
        prompt = '--cd primary; $(echo data) "literal prompt"'
        self.assertEqual(0, self.launch("quick", "unit", "--exec", "--prompt", prompt))
        destination = self.destination
        self.assertNotEqual(self.root, destination)
        self.assertEqual(["SIMULATED-native-codex", "--cd", str(destination), "--enable", "hooks", "exec", "--", prompt],
                         self.launched[0][0])
        self.assertEqual(destination, self.launched[0][1])
        self.assertEqual(0, self.launch("quick", "unit", "--prompt=--dangerously-bypass-hook-trust"))
        self.assertEqual(["--", "--dangerously-bypass-hook-trust"], self.launched[-1][0][-2:])
        self.assertEqual(1, self.launched[-1][0].count("--dangerously-bypass-hook-trust"))
        self.assert_refused(self.event(self.root))
        self.assert_refused(self.event(destination, "Write", {"file_path": str(self.root / "source.txt"), "content": "no"}))
        with chdir(destination):
            self.runtime.hook_decision(self.event(destination))
        # Actual ordinary isolated test/commit stays usable after guard approval.
        self.assertEqual(0, command(sys.executable, "-c", "assert 2 + 2 == 4", cwd=destination).returncode)
        (destination / "source.txt").write_bytes(b"isolated committed change")
        self.git("add", "source.txt", cwd=destination)
        self.git("commit", "-qm", "isolated ordinary commit", cwd=destination)
        self.assertEqual(0, self.launch())
        self.assertEqual(destination, self.destination)
        self.assertEqual(2, self.git("worktree", "list", "--porcelain").count("worktree "))
        self.assertEqual(before, self.primary_snapshot())
        self.assertEqual(3, len(self.launched))

    def test_runtime_phase_selection_and_missing_phase(self):
        self.assertEqual(0, self.launch("phase", "1"))
        self.assertTrue(self.destination.name.startswith("phase-01-"))
        self.assertEqual(2, self.launch("phase", "99"))
        self.assertEqual(1, len(self.launched))

    def test_runtime_unknown_options_refuse_before_creation(self):
        listing = self.git("worktree", "list", "--porcelain")
        for option in ("--cd", "--sandbox", "--ask-for-approval", "--approve-for-me", "--enable", "--disable",
                       "--config", "--profile", "--add-dir", "--resume", "--fork", "--worktree",
                       "--dangerously-bypass-approvals-and-sandbox", "--dangerously-bypass-hook-trust", "--pro"):
            with self.subTest(option=option), self.assertRaises(SystemExit):
                self.launch("quick", "unit", option, "unsafe")
        self.assertEqual(listing, self.git("worktree", "list", "--porcelain"))
        self.assertEqual([], self.launched)

    def test_runtime_policy_refusals_and_zero_model_calls_preserve_configuration(self):
        before = self.config.read_bytes()
        variants = [("sandbox_mode", value) for value in ("read-only", "danger-full-access", None, "unknown")]
        variants += [("approval_policy", value) for value in (None, "on-failure", {}, {"granular": {"rules": True}},
                                                              {"granular": {"rules": 1, "sandbox_approval": True, "mcp_elicitations": True}})]
        variants += [("sandbox_workspace_write", {"network_access": "true"}), ("approvals_reviewer", "unknown")]
        for root_side in (0, 1):
            for key, value in variants + [("approval_policy", "MISSING")]:
                def change(method, params, response):
                    if method == "config/read" and (Path(params["cwd"]) == self.root) == (root_side == 0):
                        if value == "MISSING":
                            response["config"].pop(key)
                        else:
                            response["config"][key] = value
                    return response
                with self.subTest(side=root_side, key=key, value=value):
                    self.change_rpc = change
                    self.assertEqual(2, self.launch())
                    self.assertEqual([], self.launched)
                    self.assertEqual(before, self.config.read_bytes())

    def test_runtime_policy_project_layers_granular_roots_and_snapshot_drift(self):
        before = self.config.read_bytes()
        for changed_key, changed_value in (("sandbox_workspace_write", None), ("approvals_reviewer", "user"),
                                          ("approval_policy", "never"), ("approval_policy", {"granular": {
                                              "rules": False, "sandbox_approval": True, "mcp_elicitations": False}})):
            def change(method, params, response):
                if method == "config/read" and Path(params["cwd"]) != self.root:
                    response["config"][changed_key] = changed_value
                return response
            self.change_rpc = change
            self.assertEqual(2, self.launch())
        def drift(method, params, response):
            if method == "config/read" and sum(item[0] == "config/read" for item in self.requests) > 2:
                response["config"]["approval_policy"] = "never"
            return response
        self.requests.clear()
        self.change_rpc = drift
        self.assertEqual(2, self.launch())
        self.assertEqual([], self.launched)
        self.assertEqual(before, self.config.read_bytes())

    def test_runtime_hook_trust_schema_disable_warnings_and_load_errors_refuse(self):
        for key, value in (("enabled", False), ("trustStatus", "untrusted"), ("trustStatus", "modified"),
                           ("trustStatus", "invented"), ("async", True), ("timeoutSec", 120), ("source", "user"),
                           ("matcher", ".*"), ("command", "replaced"), ("handlerType", "prompt"),
                           ("currentHash", None), ("isManaged", "yes")):
            def change(method, params, response):
                if method == "hooks/list":
                    response["data"][0]["hooks"][0][key] = value
                return response
            self.change_rpc = change
            with self.subTest(key=key, value=value):
                self.assertEqual(2, self.launch())
        for field in ("warnings", "errors"):
            def change(method, params, response):
                if method == "hooks/list":
                    response["data"][0][field] = [{"path": "config", "message": "load failure"}]
                return response
            self.change_rpc = change
            self.assertEqual(2, self.launch())
        self.assertEqual([], self.launched)

    def test_runtime_missing_modified_and_changed_installed_inputs_refuse(self):
        path = self.root / ".codex/hooks/codex-worktree.py"
        original = path.read_bytes()
        path.unlink()
        self.assertEqual(2, self.launch())
        path.write_bytes(original + b"\n# uncommitted\n")
        self.assertEqual(2, self.launch())
        path.write_bytes(original)
        def change(method, params, response):
            if method == "hooks/list":
                (self.destination / ".codex/hooks/codex-worktree.py").write_bytes(b"changed before launch")
            return response
        self.change_rpc = change
        self.assertEqual(2, self.launch())
        self.assertEqual([], self.launched)

    def test_runtime_missing_destination_dependency_does_not_copy_primary(self):
        older = self.revision
        self.git("rm", ".codex/codex-worktree.py")
        self.git("commit", "-qm", "old base missing installed launcher")
        missing = self.git("rev-parse", "HEAD")
        self.git("checkout", older, "--", ".codex/codex-worktree.py")
        self.git("commit", "-qm", "current caller has launcher")
        self.assertEqual(2, self.launch("quick", "missing", "--base", missing))
        from lib import worktrees
        from lib.paths import Workspace
        session = worktrees.session_for(Workspace(self.root), "quick", "missing")
        self.assertIsNotNone(session)
        self.assertFalse((Path(session["worktree"]) / ".codex/codex-worktree.py").exists())
        self.assertEqual([], self.launched)

    def test_runtime_base_branch_common_registration_and_unit_refusals(self):
        self.assertEqual(0, self.launch())
        destination = self.destination
        self.launched.clear()
        manifest = self.root / ".git/ai-phase/sessions.json"
        original = manifest.read_bytes()
        data = json.loads(original)
        for update in ({"branch": "quick-wrong"}, {"base": "0" * 40}, {"kind": "milestone"},
                       {"label": "bad label"}, {"worktree": str(self.root)}):
            changed = copy.deepcopy(data)
            changed["sessions"][0].update(update)
            manifest.write_text(json.dumps(changed), encoding="utf-8")
            with self.subTest(update=update):
                self.assert_refused(self.event(destination))
        duplicate = copy.deepcopy(data)
        duplicate["sessions"].append(copy.deepcopy(duplicate["sessions"][0]))
        manifest.write_text(json.dumps(duplicate), encoding="utf-8")
        self.assertEqual(2, self.launch())
        manifest.write_bytes(original)
        self.git("checkout", "--detach", cwd=destination)
        self.assertEqual(2, self.launch())
        self.assert_refused(self.event(destination))
        self.assertEqual([], self.launched)

    def test_runtime_unregistered_foreign_and_mismatched_base_are_refused(self):
        self.assertEqual(0, self.launch())
        self.launched.clear()
        destination = self.destination
        self.git("commit", "--allow-empty", "-qm", "caller advances")
        self.assertEqual(2, self.launch("quick", "unit", "--base", "HEAD"))
        foreign = self.base / "foreign"
        self.git("init", "-q", str(foreign))
        (foreign / "source.txt").write_bytes(b"foreign")
        self.git("add", ".", cwd=foreign)
        self.git("commit", "-qm", "foreign", cwd=foreign)
        self.assert_refused(self.event(foreign))
        unowned = self.base / "unowned"
        self.git("worktree", "add", "-b", "quick-unowned", str(unowned), self.revision)
        self.assert_refused(self.event(unowned))
        with chdir(destination):
            self.runtime.hook_decision(self.event(destination))
        self.assertEqual([], self.launched)

    def test_runtime_note_allowance_source_and_payload_refusal_matrix(self):
        for target in (".planning/scratchpads/task.md", ".planning/handoffs/run/scratch/task.md", str(self.base / "note.md")):
            with chdir(self.root):
                self.runtime.hook_decision(self.event(self.root, "Write", {"file_path": target, "content": "note"}))
        for tool, data in (("Write", {"file_path": "source.txt", "content": "no"}),
                           ("Edit", {"file_path": "source.txt", "old_string": "x", "new_string": "y"}),
                           ("apply_patch", {"patch": "*** Begin Patch\n*** Delete File: .planning/scratchpads/note.md\n*** End Patch"}),
                           ("unknown", {"command": "opaque writer"}),
                           ("apply_patch", {"patch": "*** Begin Patch\n*** Update File: source.txt\n@@\n-x\n+y\n*** Add File: .planning/scratchpads/note.md\n+note\n*** End Patch"})):
            self.assert_refused(self.event(self.root, tool, data))
        self.assert_refused(self.event(self.base), cwd=self.root)
        for event in ("SessionStart", "UserPromptSubmit"):
            self.assert_allowed(self.event(self.root, event=event),
                                "primary lifecycle diagnostics must not block ordinary prompts")
        with chdir(self.root):
            self.runtime.hook_decision(self.event(self.root, data={"command": "git status --short"}))
        self.assertEqual(0, self.launch())
        destination = self.destination
        for data in ({"command": "opaque", "workdir": str(self.root)},
                     {"command": "opaque", "path": str(self.root / "source.txt")},
                     {"command": "opaque", "cwd": "../.."}):
            self.assert_refused(self.event(destination, data=data))
        with chdir(destination):
            for event in ("SessionStart", "UserPromptSubmit"):
                self.runtime.hook_decision(self.event(destination, event=event))
            self.runtime.hook_decision(self.event(destination, "unknown", {"opaque": True}))

    def test_runtime_adapter_normalizes_malformed_and_unexpected_errors_to_exit2(self):
        adapter = ROOT / ".ai/hooks/codex-worktree.py"
        for payload in ("{", "[]", json.dumps(self.event(self.root))):
            result = command(sys.executable, str(adapter), cwd=self.root, input=payload)
            self.assertEqual(2, result.returncode)
            self.assertIn("Codex worktree guard refused", result.stderr)
        with chdir(self.root):
            self.runtime.check_launchability(self.root, {"PreToolUse": self.runtime.guard_commands()[os.name == "nt"]},
                                             self.runtime.prewrite.Budget())

    def test_runtime_structured_hardlink_nested_patch_move_and_tracked_note_controls(self):
        self.assertEqual(0, self.launch())
        destination = self.destination
        nested = destination / "nested"
        self.git("init", "-q", str(nested))
        os.link(destination / "source.txt", destination / "hardlink.txt")
        for path in ("nested/target.txt", "hardlink.txt", "../escape.txt", ".git/config"):
            self.assert_refused(self.event(destination, "Write", {"file_path": path, "content": "no"}))
        self.assert_refused(self.event(destination, "Write", {"file_path": "source.txt", "content": "no", "workdir": str(self.root)}))
        self.assert_refused(self.event(self.root, data={"command": "git status", "cmd": "writer"}))
        patch_text = ("*** Begin Patch\n*** Update File: source.txt\n*** Move to: " + str(self.root / "moved.txt") +
                      "\n@@\n-committed\n+changed\n*** End Patch")
        self.assert_refused(self.event(destination, "apply_patch", {"patch": patch_text}))
        tracked = self.root / ".planning/scratchpads/tracked.md"
        tracked.parent.mkdir(parents=True)
        tracked.write_text("delivered", encoding="utf-8")
        self.git("add", "-f", ".planning/scratchpads/tracked.md")
        self.assert_refused(self.event(self.root, "Write", {"file_path": str(tracked), "content": "no"}))
        self.assertEqual(b"committed\n", (self.root / "source.txt").read_bytes())

    def test_runtime_setup_and_rpc_failures_never_launch_model(self):
        from lib.results import VerbError
        before = self.config.read_bytes()
        with chdir(self.root), patch.object(self.runtime.shutil, "which", return_value=None):
            self.assertEqual(2, self.runtime.launcher_main(["quick", "unit"]))
        with chdir(self.root), patch.object(self.runtime.shutil, "which", return_value="SIMULATED-native"), \
                patch.object(self.runtime, "NativePreflight", side_effect=OSError("cannot start helper")), \
                patch.object(self.runtime, "check_launchability"), patch.object(self.runtime.subprocess, "call") as model:
            self.assertEqual(2, self.runtime.launcher_main(["quick", "unit"]))
            model.assert_not_called()
        with chdir(self.root), patch.object(self.runtime.shutil, "which", return_value="SIMULATED-native"), \
                patch.object(self.runtime, "NativePreflight", side_effect=self.fake_native), \
                patch.object(self.runtime, "check_launchability", side_effect=VerbError("missing Python")), \
                patch.object(self.runtime.subprocess, "call") as model:
            self.assertEqual(2, self.runtime.launcher_main(["quick", "unit"]))
            model.assert_not_called()
        self.assertEqual(before, self.config.read_bytes())

    def test_runtime_native_preflight_wire_protocol_and_rpc_error_are_bounded(self):
        # A real child process speaking deterministic RPC, explicitly SIMULATED native.
        script = self.base / "simulated_native_rpc.py"
        script.write_text('''import json, sys
for line in sys.stdin:
    value = json.loads(line)
    method = value['method']
    if method == 'initialized':
        continue
    if method == 'initialize':
        result = {'userAgent': 'SIMULATED-native'}
    elif method == 'config/read':
        result = {'observed': value['params']}
    else:
        print(json.dumps({'id': value['id'], 'error': {'code': -1, 'message': 'simulated read failure'}}), flush=True)
        continue
    print(json.dumps({'id': value['id'], 'result': result}), flush=True)
''', encoding="utf-8")
        real_popen = subprocess.Popen
        captured = []
        def fixture_process(argv, **kwargs):
            captured.append(argv)
            return real_popen([sys.executable, str(script)], **kwargs)
        from lib.results import VerbError
        with patch.object(self.runtime.subprocess, "Popen", side_effect=fixture_process):
            with self.runtime.NativePreflight("SIMULATED-native", self.root) as native:
                observed = native.request("config/read", {"cwd": str(self.root), "includeLayers": True})
                self.assertEqual({"cwd": str(self.root), "includeLayers": True}, observed["observed"])
                with self.assertRaises(VerbError):
                    native.request("unsupported/read", {})
            self.assertIsNotNone(native.process.poll())
        self.assertEqual([["SIMULATED-native", "--cd", str(self.root), "--enable", "hooks", "app-server"]], captured)

    def test_runtime_native_timeout_and_malformed_response_refuse(self):
        from lib.results import VerbError
        import queue
        import time
        native = self.runtime.NativePreflight("SIMULATED-native", self.root)
        native.sequence = 0
        native.end = time.monotonic() - 1
        native.messages = queue.Queue()
        with patch.object(native, "send"), self.assertRaises(VerbError):
            native.request("config/read", {})
        native.end = time.monotonic() + 1
        native.messages.put(None)
        with patch.object(native, "send"), self.assertRaises(VerbError):
            native.request("hooks/list", {})

    def test_runtime_active_wave_workers_remain_usable_with_accumulated_commits(self):
        from lib import worktrees
        from lib.paths import Workspace
        workers = [worktrees.create(Workspace(self.root), plan, phase="01", base=self.revision)
                   for plan in ("01-01", "01-02")]
        self.assertFalse((self.root / ".git/ai-phase/sessions.json").exists())
        for entry in workers:
            destination = Path(entry["worktree"])
            self.assertNotEqual(destination.name, entry["branch"])
            self.assert_allowed(self.event(destination), "valid runtime-owned active wave worker must remain usable")
            self.assert_allowed(self.event(destination, "Write", {"file_path": "source.txt", "content": "worker"}),
                                "active worker structured source must remain usable")
            (destination / "source.txt").write_bytes(b"accumulated worker commit")
            self.git("add", "source.txt", cwd=destination)
            self.git("commit", "-qm", "ordinary worker commit", cwd=destination)
            self.assert_allowed(self.event(destination), "accumulated active worker HEAD remains valid")
        self.assertEqual(b"committed\n", (self.root / "source.txt").read_bytes())

    def test_runtime_adopted_named_phase_at_non_generated_path_remains_usable(self):
        from lib import worktrees
        from lib.paths import Workspace
        destination = self.base / "existing linked phase"
        self.git("worktree", "add", "-b", "phase-existing-named", str(destination), self.revision)
        worktrees.adopt_session(Workspace(destination), "phase", "01")
        self.assert_allowed(self.event(destination), "valid adopted named phase receipt must remain usable")
        self.assert_allowed(self.event(destination, "Write", {"file_path": "source.txt", "content": "adopted"}),
                            "adopted phase structured source remains usable")
        (destination / "source.txt").write_bytes(b"accumulated adopted commit")
        self.git("add", "source.txt", cwd=destination)
        self.git("commit", "-qm", "ordinary adopted phase commit", cwd=destination)
        self.assert_allowed(self.event(destination), "accumulated adopted HEAD remains valid")
        self.assertEqual(0, self.launch("phase", "01"))
        self.assertEqual(destination, self.destination)
        manifest = self.root / ".git/ai-phase/sessions.json"
        original = manifest.read_bytes()
        for update in ({"label": "99"}, {"kind": "quick"}, {"branch": "phase-wrong"},
                       {"worktree": str(self.root)}, {"status": "closed"}):
            changed = json.loads(original)
            changed["sessions"][0].update(update)
            manifest.write_text(json.dumps(changed), encoding="utf-8")
            self.assert_refused(self.event(destination))
        manifest.write_bytes(original)

    def test_runtime_wave_identity_status_malformed_duplicates_foreign_and_detached_refuse(self):
        from lib import worktrees
        from lib.paths import Workspace
        entry = worktrees.create(Workspace(self.root), "01-01", phase="01", base=self.revision)
        destination = Path(entry["worktree"])
        manifest = worktrees.manifest_path(Workspace(self.root), "01")
        original = manifest.read_bytes()
        self.git("commit", "--allow-empty", "-qm", "caller advances outside worker")
        non_ancestor = self.git("rev-parse", "HEAD")
        foreign = self.base / "foreign worker"
        self.git("init", "-q", str(foreign))
        for update in ({"plan": ""}, {"phase": "99"}, {"branch": "phase-wrong"},
                       {"base": non_ancestor}, {"base": "0" * 40}, {"worktree": str(self.root)},
                       {"worktree": str(foreign)}, {"isolation": "harness-worktree"},
                       {"files": None}, *({"status": status} for status in ("merged", "closed", "blocked", "cleaned", "missing"))):
            changed = json.loads(original)
            changed["entries"][0].update(update)
            manifest.write_text(json.dumps(changed), encoding="utf-8")
            with self.subTest(update=update):
                self.assert_refused(self.event(destination))
        for value in ("{", "[]", json.dumps({"phase": "01", "entries": [None]}),
                      json.dumps({"phase": "99", "entries": []})):
            manifest.write_text(value, encoding="utf-8")
            self.assert_refused(self.event(destination))
        duplicate = json.loads(original)
        duplicate["entries"].append(copy.deepcopy(duplicate["entries"][0]))
        manifest.write_text(json.dumps(duplicate), encoding="utf-8")
        self.assert_refused(self.event(destination))
        duplicate["entries"][1].update(worktree=str(self.base / "other"), branch="phase-other")
        manifest.write_text(json.dumps(duplicate), encoding="utf-8")
        self.assert_refused(self.event(destination))
        manifest.write_bytes(original)
        stray = manifest.with_name("foreign-envelope.json")
        stray.write_bytes(original)
        self.assert_refused(self.event(destination))
        stray.unlink()
        # A session and active wave must never claim the same physical checkout.
        sessions = self.root / ".git/ai-phase/sessions.json"
        sessions.write_text(json.dumps({"sessions": [{"kind": "quick", "label": "conflict", "status": "open",
                             "worktree": str(destination), "branch": entry["branch"], "base": entry["base"]}]}), encoding="utf-8")
        self.assert_refused(self.event(destination))
        sessions.unlink()
        self.git("checkout", "--detach", cwd=destination)
        self.assert_refused(self.event(destination))
        self.assertEqual(b"committed\n", (self.root / "source.txt").read_bytes())


if __name__ == "__main__":
    unittest.main()
