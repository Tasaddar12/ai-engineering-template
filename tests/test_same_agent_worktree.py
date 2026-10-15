"""SIMULATED native host contract composed with installed hooks and real Git.

SimulatedClaude represents one existing actor, its advertised schema, and the
host's persistent default context. It is not Claude, a model-following test, or
live movement evidence. The installer, hook launchers, runtime and Git below
are real. No production helper is mocked or imported from a proposed module.
"""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

import yaml

import test_install as installed


class SimulatedRefusal(Exception):
    """The explicitly simulated host cannot perform this native operation."""


class SimulatedClaude:
    """Test-only native adapter; tools always use this actor's default cwd.

    The schema is a fixture, not a claim about a particular Claude release.
    Native entry calls the actual registered creation provider. Updating cwd,
    permissions and loaded context here simulates host behavior, never runtime
    behavior. The original project-directory variable deliberately stays old.
    """

    def __init__(self, case):
        self.case = case
        self.actor = ("SIMULATED-session", "SIMULATED-coder")
        self.cwd = case.directory / "nested cwd"
        self.project_dir = case.directory
        self.schema = {"properties": {"name": {"type": "string"},
                                      "path": {"type": "string"}}}
        self.available = True
        self.eligible = True
        self.policy = True
        self.trusted = True
        self.events = []
        self.completed = False
        self.loaded_root = None
        self.writable_root = None
        self.reads = {}
        self.edits = 0
        self.entry_head = None

    def gate(self, mode):
        if not self.available:
            raise SimulatedRefusal("native tool is not in the actual advertised pool")
        tools = self.case.role_tools("coder")
        if "EnterWorktree" not in tools:
            raise SimulatedRefusal("role does not permit EnterWorktree")
        field = "name" if mode == "new" else "path"
        if (self.schema is None or self.schema.get("properties", {}).get(field, {}).get("type") != "string"):
            raise SimulatedRefusal("advertised native schema cannot carry " + field)
        if mode == "new" and not self.eligible:
            raise SimulatedRefusal("pinned/already-worktree role cannot create")
        if not self.policy:
            raise SimulatedRefusal("native policy refused entry")
        if not self.trusted or "WorktreeCreate" not in self.case.settings["hooks"]:
            raise SimulatedRefusal("creation hook is not trusted and registered")
        # This checks the installed instruction artifact in addition to exports;
        # it cannot demonstrate that a live model follows those instructions.
        protocol = (self.case.directory / ".claude/references/same-agent-worktree.md").read_text(encoding="utf-8")
        for operation in ("EnterWorktree", "prewrite.begin", "prewrite.confirm"):
            self.case.assertIn(operation, protocol)

    def enter(self, target, *, bind=True, complete=True, approved=True):
        mode = target["mode"]
        self.gate(mode)
        if mode == "existing" and not self.eligible:
            permitted = self.project_dir / ".claude/worktrees"
            if not Path(target["worktree"]).resolve().is_relative_to(permitted):
                raise SimulatedRefusal("pinned/already-worktree native path is outside its permitted root")
        if mode == "existing" and not approved:
            raise SimulatedRefusal("existing outside path requires native approval")
        # Existing sessions accumulate commits beyond their immutable fork
        # base. Observe HEAD before path entry separately from that base.
        self.entry_head = (self.case.git("rev-parse", "HEAD", cwd=target["worktree"]).strip()
                           if mode == "existing" else target["base"])
        arguments = ({"name": target["creation_name"]} if mode == "new"
                     else {"path": target["worktree"]})
        self.events.append((self.actor, "EnterWorktree", arguments))
        if mode == "new":
            result = self.case.creation_callback(target["creation_name"], self)
            self.case.assertEqual(0, result.returncode, result.stderr.decode("utf-8", "replace"))
            lines = result.stdout.decode("utf-8").strip().splitlines()
            self.case.assertEqual(1, len(lines), "creation provider must return only its root")
            destination = Path(lines[0]).resolve()
        else:
            destination = Path(target["worktree"]).resolve()
        self.case.assertEqual(Path(target["worktree"]).resolve(), destination)
        self.completed = complete
        if bind:
            self.cwd = destination
            self.writable_root = destination
            # A native host reloads project instructions/configuration; this is
            # simulated host state, not something prewrite.confirm can certify.
            self.case.assertTrue((self.cwd / "CLAUDE.md").read_text(encoding="utf-8"))
            self.case.assertTrue((self.cwd / ".planning/config.yaml").read_text(encoding="utf-8"))
            self.loaded_root = destination

    def prove_defaults(self, target, *, actor=None):
        expected = Path(target["worktree"]).resolve()
        if (not self.completed or (actor is not None and actor != self.actor)
                or self.cwd != expected or self.loaded_root != expected
                or self.writable_root != expected):
            raise SimulatedRefusal("same-actor native completion/default context is unproven")
        # No cwd parameter is offered to these simulated tools. In particular,
        # CLAUDE_PROJECT_DIR cannot substitute for the destination default cwd.
        self.case.assertEqual(expected, Path(self.git("rev-parse", "--show-toplevel").strip()).resolve())
        self.case.assertEqual(target["branch"], self.git("branch", "--show-current").strip())
        self.case.assertEqual(self.entry_head, self.git("rev-parse", "HEAD").strip())
        self.case.assertEqual(target["base"], self.git("merge-base", target["base"], "HEAD").strip())
        self.case.assertNotEqual(self.project_dir, self.cwd)

    def git(self, *args):
        return self.case.git(*args, cwd=self.cwd)

    def runtime(self, *args, ok=True):
        return self.case.runtime(*args, cwd=self.cwd, actor=self.actor, ok=ok)

    def read(self, relative):
        self.case.assertFalse(Path(relative).is_absolute())
        value = (self.cwd / relative).read_bytes()
        self.reads[relative] = value
        return value

    def rebuilt_edit(self, target):
        self.prove_defaults(target)
        self.case.assertIn("source.txt", self.reads, "fresh destination read must precede rebuilding")
        fresh = self.reads["source.txt"]
        replacement = fresh + b"rebuilt after native entry\n"
        payload = self.case.event(self, "rebuilt-edit", "Edit", {
            "file_path": "source.txt", "old_string": fresh.decode("utf-8"),
            "new_string": replacement.decode("utf-8")})

        def mutate():
            self.case.assertEqual(0, self.edits, "never replay a completed rebuilt edit")
            self.case.assertEqual(fresh, (self.cwd / "source.txt").read_bytes())
            (self.cwd / "source.txt").write_bytes(replacement)
            self.edits += 1

        denied, _ = self.case.pipeline(self, payload, self.cwd / "source.txt", mutation=mutate)
        self.case.assertFalse(denied, "validated destination-local rebuilt edit must continue")
        return replacement


class NativeRouteTests(unittest.TestCase):
    """One actual install per suite; separate offline real-Git repo per test."""

    @classmethod
    def setUpClass(cls):
        installed.InstallerTests.setUpClass()
        cls.addClassCleanup(installed.InstallerTests.tearDownClass)
        cls.seed = installed.InstallerTests()
        cls.seed.setUp()
        cls.addClassCleanup(cls.seed.doCleanups)
        cls.seed.prewrite_fixture("claude")
        config = cls.seed.target / ".planning/config.yaml"
        data = yaml.safe_load(config.read_text(encoding="utf-8"))
        data["worktree"]["root"] = ".native-trees"
        config.write_text(yaml.safe_dump(data), encoding="utf-8", newline="\n")
        with (cls.seed.target / ".gitignore").open("a", encoding="utf-8") as stream:
            stream.write("\n.native-trees/\nignored.bin\n")
        (cls.seed.target / "staged.bin").write_bytes(b"committed\x00binary")
        (cls.seed.target / "unstaged.txt").write_bytes(b"committed\n")
        (cls.seed.target / ".gitattributes").write_text("source.txt -text\n", encoding="utf-8")
        installed.command("git", "add", ".planning/config.yaml", ".gitignore", "staged.bin",
                          "unstaged.txt", ".gitattributes", "source.txt", cwd=cls.seed.target)
        installed.command("git", "commit", "-qm", "native fixture custom ignored root", cwd=cls.seed.target)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="same-agent-SIMULATED-")
        self.addCleanup(temporary.cleanup)
        # Canonical ordinary fixture roots matter on Windows with 8.3 TEMP.
        self.directory = Path(temporary.name).resolve() / "project caf\u00e9 with spaces"
        installed.command("git", "clone", "--quiet", "--no-hardlinks", str(self.seed.target),
                          str(self.directory))
        self.git("remote", "remove", "origin")  # no network or provider is needed
        self.git("config", "user.name", "Native Fixture")
        self.git("config", "user.email", "native@example.invalid")
        (self.directory / "nested cwd").mkdir()
        self.settings = installed.read_settings(self.directory / ".claude/settings.json")
        editing = [group for group in self.settings["hooks"]["PreToolUse"]
                   if "NotebookEdit" in group.get("matcher", "")]
        self.assertEqual(1, len(editing))
        self.group = editing[0]
        self.host = SimulatedClaude(self)

    def git(self, *args, cwd=None):
        return installed.command("git", *args, cwd=cwd or self.directory)

    def role_tools(self, role):
        text = (self.directory / ".claude/agents" / (role + ".md")).read_text(encoding="utf-8")
        metadata = yaml.safe_load(text.split("---", 2)[1])
        return {value.strip() for value in metadata["tools"].split(",")}

    def runtime(self, *args, cwd=None, actor=None, ok=True):
        identity = actor or self.host.actor
        extra = (["--session-id", identity[0], "--agent-id", identity[1]]
                 if args[0].startswith("prewrite.") else [])
        environment = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1",
                           CLAUDE_PROJECT_DIR=str(self.directory), CLAUDE_CODE_SESSION_ID=identity[0])
        actual_cwd = cwd or self.directory
        root = Path(self.git("rev-parse", "--show-toplevel", cwd=actual_cwd).strip())
        runtime = root / ".claude/runtime/phase.py"
        result = subprocess.run([sys.executable, str(runtime), "query", *args, *extra],
                                cwd=cwd or self.directory, env=environment,
                                capture_output=True, encoding="utf-8", timeout=30)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        value = json.loads(result.stdout)
        self.assertNotEqual("unknown-verb", value.get("code"),
                            "missing public adapter is a setup gap, never native-route RED")
        self.assertEqual(ok, value.get("ok"), value)
        self.assertEqual(0 if ok else 1, result.returncode, value)
        return value

    @staticmethod
    def event(host, request, tool, tool_input):
        return {"hook_event_name": "PreToolUse", "cwd": str(host.cwd),
                "session_id": host.actor[0], "agent_id": host.actor[1],
                "tool_use_id": request, "tool_name": tool, "tool_input": tool_input}

    def pipeline(self, host, payload, destination, mutation=None):
        # Reuse the aggregate's real Windows/POSIX launcher and native decision
        # interpretation, including the original mutation's failure-open path.
        return self.seed.prewrite_pipeline("claude", self.group, host.cwd, payload,
                                          destination, mutation=mutation,
                                          environment_overrides={"CLAUDE_PROJECT_DIR": str(self.directory),
                                                                 "CLAUDE_CODE_SESSION_ID": host.actor[0]})

    def creation_callback(self, name, host=None):
        return self.location_callback("WorktreeCreate", "name", name, host)

    def location_callback(self, event, field, value, host=None, environment_overrides=None):
        actor = host or self.host
        groups = self.settings["hooks"][event]
        self.assertEqual(1, len(groups))
        self.assertEqual(1, len(groups[0]["hooks"]))
        handler = groups[0]["hooks"][0]
        payload = {"hook_event_name": event, "cwd": str(actor.cwd),
                   "session_id": actor.actor[0], "agent_id": actor.actor[1], field: value}
        environment = dict(os.environ, PYTHONIOENCODING="utf-8",
                           CLAUDE_PROJECT_DIR=str(self.directory),
                           CLAUDE_CODE_SESSION_ID=actor.actor[0],
                           PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"])
        environment.update(environment_overrides or {})
        return subprocess.run(self.seed.launcher_argv("claude", handler), cwd=actor.cwd,
                              env=environment, input=json.dumps(payload).encode("utf-8"),
                              capture_output=True, timeout=40)

    def inventory(self):
        state = self.directory / ".git/ai-phase/prewrite"
        return (self.git("worktree", "list", "--porcelain"),
                {path.relative_to(state).as_posix(): path.read_bytes()
                 for path in state.rglob("*") if path.is_file()} if state.exists() else {})

    def primary_snapshot(self):
        names = ("source.txt", "staged.bin", "unstaged.txt", "untracked.txt", "ignored.bin")
        return {"files": {name: (self.directory / name).read_bytes() for name in names},
                "index": self.git("ls-files", "--stage", "-z"),
                "status": self.git("status", "--porcelain", "-z"),
                "branch": self.git("branch", "--show-current"),
                "head": self.git("rev-parse", "HEAD")}

    def source_request(self):
        source = self.directory / "source.txt"
        original = source.read_bytes()
        before = self.git("worktree", "list", "--porcelain")
        payload = self.event(self.host, "original-pending", "Edit", {
            "file_path": str(source), "old_string": original.decode("utf-8"),
            "new_string": "STALE PENDING EDIT MUST NEVER BE REPLAYED\n"})
        denied, results = self.pipeline(self.host, payload, source)
        reasons = [json.loads(result.stdout).get("hookSpecificOutput", {}).get(
                   "permissionDecisionReason", "") for result in results if result.stdout.strip()]
        reason = "\n".join(reasons)
        # This is the named fresh behavioral RED. It observes actual installed
        # aggregate output, before touching any new module, verb or protocol file.
        self.assertIn("EnterWorktree", reason,
                      "A1/A2: installed Claude source decision did not deliver a same-agent "
                      "native EnterWorktree continuation; actual decision reasons=" + repr(reasons))
        self.assertTrue(denied, "source edit must be synchronously cancelled")
        self.assertEqual(original, source.read_bytes(), "original pending call executed")
        self.assertEqual(before, self.git("worktree", "list", "--porcelain"),
                         "denial must not precreate the native checkout")
        self.assertIn(".claude/references/same-agent-worktree.md", reason)
        match = re.search(r"prewrite\.begin\s+([A-Za-z0-9_-]+)", reason)
        self.assertIsNotNone(match, "denial must supply an actionable ticket, not just a notice")
        return match[1]

    def begin(self, request, kind="quick", label="native-edit", mode="new", ok=True):
        # Explicit unit/actor claims bind a ticket; they never attest live host
        # eligibility or authenticate the simulated tool inventory.
        return self.runtime("prewrite.begin", request, kind, label, "--mode", mode, ok=ok)

    def assert_confirm(self, request, target, *, reused=False):
        self.host.prove_defaults(target)
        result = self.host.runtime("prewrite.confirm", request)
        self.assertEqual(reused, result["reused"])
        self.assertFalse(result["host_binding_verified"], "runtime Git checks cannot certify native binding")
        self.assertEqual(self.host.cwd, Path(result["worktree"]).resolve())
        return result

    def test_simulated_installed_denial_native_entry_defaults_and_fresh_rebuilt_edit(self):
        """A1/A4/A6: actual pipeline -> native provider -> same simulated caller."""
        (self.directory / "source.txt").write_bytes(b"dirty PRIMARY ONLY\n")
        (self.directory / "staged.bin").write_bytes(b"staged\x00\xffbinary")
        self.git("add", "staged.bin")
        (self.directory / "staged.bin").write_bytes(b"unstaged over index\x00\xff")
        (self.directory / "unstaged.txt").write_bytes(b"unstaged data\n")
        (self.directory / "untracked.txt").write_bytes(b"untracked data\n")
        (self.directory / "ignored.bin").write_bytes(b"ignored\x00\xffdata")
        primary = self.primary_snapshot()
        request = self.source_request()
        target = self.begin(request)
        self.assertEqual("new", target["mode"])
        self.assertRegex(target["creation_name"], r"^wf-entry-[A-Za-z0-9_-]+$")
        self.assertRegex(target["branch"], r"^worktree-wf_[A-Za-z0-9_-]+$")
        self.assertEqual(primary["head"].strip(), target["base"])
        self.assertEqual(self.directory / ".native-trees", Path(target["worktree"]).parent)
        self.assertFalse(Path(target["worktree"]).exists(), "begin is a reservation, not native creation")
        self.host.enter(target)
        self.assertEqual([(self.host.actor, "EnterWorktree", {"name": target["creation_name"]})], self.host.events)
        with self.assertRaises(SimulatedRefusal):
            self.host.prove_defaults(target, actor=("SIMULATED-session", "replacement-child"))
        for field in ("loaded_root", "writable_root"):
            actual = getattr(self.host, field)
            setattr(self.host, field, self.directory)
            with self.assertRaises(SimulatedRefusal):
                self.host.prove_defaults(target)
            setattr(self.host, field, actual)
        self.assert_confirm(request, target)
        self.assertEqual(b"committed source\n", self.host.read("source.txt"))
        self.assertFalse((self.host.cwd / "untracked.txt").exists())
        self.assertFalse((self.host.cwd / "ignored.bin").exists())
        expected = self.host.rebuilt_edit(target)
        self.assertEqual(expected, (self.host.cwd / "source.txt").read_bytes())
        self.assertEqual(1, self.host.edits)
        self.assertEqual(primary, self.primary_snapshot())
        # Later simulated turn: the same object/actor retains destination defaults.
        self.host.reads.clear()
        self.assertEqual(expected, self.host.read("source.txt"))
        self.assertEqual(target["branch"], self.host.git("branch", "--show-current").strip())
        self.assertEqual(1, len(self.host.events))

    def test_simulated_gate_refusals_leave_ticket_and_git_untouched(self):
        """A2: positive actual-export/schema/policy/trust checks, no fallback."""
        request = self.source_request()
        target = self.begin(request)
        before = self.inventory()
        for attribute, value in (("available", False), ("schema", None),
                                 ("schema", {"properties": {"path": {"type": "string"}}}),
                                 ("schema", {"properties": {"name": {"type": "integer"}}}),
                                 ("eligible", False), ("policy", False), ("trusted", False)):
            with self.subTest(attribute=attribute, value=value):
                original = getattr(self.host, attribute)
                setattr(self.host, attribute, value)
                with self.assertRaises(SimulatedRefusal):
                    self.host.enter(target)
                setattr(self.host, attribute, original)
                self.assertEqual([], self.host.events)
                self.assertEqual(before, self.inventory())

    def test_simulated_old_defaults_never_authorize_rebuilt_edit(self):
        """A4: a created checkout/runtime result is distinct from host binding."""
        request = self.source_request()
        target = self.begin(request)
        self.host.enter(target, bind=False)
        with self.assertRaises(SimulatedRefusal):
            self.host.prove_defaults(target)
        # Git confirmation from the old default root must fail too. Supplying
        # an explicit destination cwd would not repair the simulated host.
        self.host.runtime("prewrite.confirm", request, ok=False)
        self.assertEqual(0, self.host.edits)
        self.assertEqual(b"committed source\n", (Path(target["worktree"]) / "source.txt").read_bytes())

    def test_native_creation_reuse_and_uncertain_result_preserve_one_checkout(self):
        """A3/A5: reserved creation names cannot impersonate approved path entry."""
        request = self.source_request()
        target = self.begin(request)
        self.host.enter(target, complete=False)
        with self.assertRaises(SimulatedRefusal):
            self.host.prove_defaults(target)
        before = self.inventory()
        repeated = self.creation_callback(target["creation_name"])
        self.assertNotEqual(0, repeated.returncode, "native creation must refuse existing-name reuse")
        self.assertFalse(repeated.stdout.strip(), "uncertain/reused creation cannot return a successful root")
        self.assertEqual(before, self.inventory())
        self.assertEqual(0, self.host.edits)
        self.assertEqual(2, before[0].count("worktree "))

    def test_registered_native_removal_preserves_clean_dirty_ignored_and_corrupt_receipt(self):
        request = self.source_request()
        target = self.begin(request)
        self.host.enter(target)
        self.assert_confirm(request, target)
        root = Path(target["worktree"])
        journal = self.directory / ".git/ai-phase/prewrite" / (request + ".json")
        for state in ("clean", "ignored-only", "dirty", "corrupt-receipt"):
            with self.subTest(state=state):
                if state == "ignored-only":
                    (root / "ignored.bin").write_bytes(b"native ignored\x00data")
                    self.assertFalse(self.host.git("status", "--porcelain").strip())
                elif state == "dirty":
                    (root / "source.txt").write_bytes(b"native unfinished source\n")
                elif state == "corrupt-receipt":
                    journal.write_bytes(b"{corrupt")
                before = self.inventory()
                observed = self.location_callback("WorktreeRemove", "worktree_path", str(root))
                self.assertEqual(0, observed.returncode, observed.stderr)
                self.assertFalse(observed.stdout.strip())
                self.assertIn(b"preserved", observed.stderr)
                self.assertEqual(before, self.inventory())
                self.assertTrue((root / ".git").is_file())
                if state != "clean":
                    self.assertEqual(b"native ignored\x00data", (root / "ignored.bin").read_bytes())

    def test_concurrent_registered_creation_calls_do_not_duplicate_tree(self):
        request = self.source_request()
        target = self.begin(request)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.creation_callback(target["creation_name"]), range(2)))
        self.assertEqual([0, 2], sorted(result.returncode for result in results))
        self.assertEqual(1, sum(bool(result.stdout.strip()) for result in results))
        self.assertEqual(2, self.inventory()[0].count("worktree "))
        self.assertEqual(0, self.host.edits)

    def test_old_source_and_wrong_actor_stay_denied_after_native_confirmation(self):
        request = self.source_request()
        target = self.begin(request)
        self.host.enter(target)
        self.assert_confirm(request, target)
        before = self.inventory()
        old = SimulatedClaude(self)
        primary = self.directory / "source.txt"
        original = primary.read_bytes()
        event = self.event(old, "original-pending", "Edit", {
            "file_path": str(primary), "old_string": original.decode(),
            "new_string": "STALE PENDING EDIT MUST NEVER BE REPLAYED\n"})
        denied, _ = self.pipeline(old, event, primary)
        self.assertTrue(denied)
        self.assertEqual(original, primary.read_bytes())
        self.assertEqual(before, self.inventory())
        self.host.actor = ("SIMULATED-session", "wrong-agent")
        fresh = self.host.cwd / "source.txt"
        denied, _ = self.pipeline(self.host, self.event(self.host, "wrong-actor", "Write", {
            "file_path": "source.txt", "content": "wrong actor"}), fresh)
        self.assertTrue(denied)
        self.assertEqual(b"committed source\n", fresh.read_bytes())
        self.assertEqual(before, self.inventory())

    def test_installed_exports_and_six_workflow_consumers_preserve_restrictions(self):
        """A2/A6 structural layer; the behavioral test above is the RED target."""
        for role in ("coordinator", "coder"):
            with self.subTest(role=role):
                original = (installed.ROOT / ".ai/agents" / (role + ".md")).read_text(encoding="utf-8")
                source_tools = set(yaml.safe_load(original.split("---", 2)[1])["tools"].split(", "))
                self.assertEqual(source_tools | {"EnterWorktree"}, self.role_tools(role))
        entry = (self.directory / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn(".claude/references/same-agent-worktree.md", entry)
        self.assertEqual(2, len(self.group["hooks"]))
        self.assertIn("worktree-guard.sh", self.group["hooks"][0]["command"])
        self.assertIn("source-prewrite.sh", self.group["hooks"][1]["command"])
        self.assertEqual(30, self.group["hooks"][1]["timeout"])
        for name in ("quick", "discuss-phase", "plan-phase", "execute-phase", "verify-work", "ship"):
            with self.subTest(workflow=name):
                text = (self.directory / ".claude/workflows" / (name + ".md")).read_text(encoding="utf-8")
                self.assertIn("same-agent-worktree.md", text)
                self.assertIn("prewrite.request", text)
                self.assertNotIn("context: fork", text)

    def test_review_native_provider_writes_one_utf8_path_under_legacy_stdout_codec(self):
        """CR-01: actual installed provider, binary UTF-8 input, legacy stdout."""
        config = self.directory / ".planning/config.yaml"
        data = yaml.safe_load(config.read_text(encoding="utf-8"))
        data["worktree"]["root"] = ".native-trees-\u6f22\u5b57"
        config.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
        with (self.directory / ".gitignore").open("a", encoding="utf-8") as stream:
            stream.write("\n.native-trees-\u6f22\u5b57/\n")
        self.git("add", ".planning/config.yaml", ".gitignore")
        self.git("commit", "-qm", "nonrepresentable native root fixture")
        requested = self.runtime("prewrite.request", "quick", "legacy-native-output", "--mode", "new")
        target = self.begin(requested["request_id"], label="legacy-native-output")
        self.host.gate("new")
        result = self.location_callback("WorktreeCreate", "name", target["creation_name"],
                                        environment_overrides={"PYTHONUTF8": "0", "PYTHONIOENCODING": "cp1252"})
        # The creation journal/Git facts are observed before checking status:
        # encoding failure after creation is an actual protocol failure, not
        # a launcher/import/setup failure. No fixture forces UTF-8 stdout.
        record = json.loads((self.directory / ".git/ai-phase/prewrite" /
                             (requested["request_id"] + ".json")).read_text(encoding="utf-8"))
        self.assertEqual("created", record["state"])
        self.assertTrue(Path(target["worktree"]).is_dir())
        self.assertEqual(target["base"], self.git("rev-parse", "HEAD", cwd=target["worktree"]).strip())
        self.assertEqual(0, result.returncode,
                         "native provider created its checkout but failed its UTF-8 path protocol: "
                         + result.stderr.decode("utf-8", "replace"))
        self.assertEqual((target["worktree"] + "\n").encode("utf-8"), result.stdout)
        # Preservation diagnostics also cross this standalone protocol boundary.
        removed = self.location_callback("WorktreeRemove", "worktree_path", target["worktree"],
                                         environment_overrides={"PYTHONUTF8": "0", "PYTHONIOENCODING": "cp1252"})
        self.assertEqual(0, removed.returncode, removed.stderr.decode("utf-8", "replace"))
        self.assertFalse(removed.stdout)
        self.assertIn(target["worktree"].encode("utf-8"), removed.stderr)
        self.assertTrue(Path(target["worktree"]).is_dir())

    def test_review_four_phase_initializers_follow_native_entry_before_locator_cd_and_init(self):
        """CR-02: interpret installed instruction order with real runtime/Git.

        This bounded instruction adapter is SIMULATED, not a live model. It
        executes the locator, primary-only bootstrap and destination init in
        the order prescribed by each installed initializer/open-session pair.
        A prescribed shell cd changes only cwd, never native completion.
        """
        roadmap = self.directory / ".planning/ROADMAP.md"
        roadmap.write_text("# Roadmap\n\n## Phases\n\n## Progress\n", encoding="utf-8")
        cases = [(name, mode) for name in ("discuss-phase", "plan-phase", "execute-phase", "verify-work")
                 for mode in ("new", "existing")]
        labels = []
        for index, (name, mode) in enumerate(cases, 1):
            self.runtime("phase.add", name + " " + mode)
            labels.append(str(index).zfill(2))
        self.git("add", ".planning")
        self.git("commit", "-qm", "phase initializer fixture inputs")
        for (name, mode), label in zip(cases, labels):
            with self.subTest(workflow=name, mode=mode):
                expected = b"committed source\n"
                metadata_before = None
                opened = None
                if mode == "existing":
                    opened = self.runtime("session.open", "phase", label, "--no-sync")
                    expected = (name + " accumulated committed work\n").encode("utf-8")
                    destination = Path(opened["worktree"])
                    (destination / "source.txt").write_bytes(expected)
                    self.git("add", "source.txt", cwd=destination)
                    self.git("commit", "-qm", "advance ordinary phase session", cwd=destination)
                    metadata_before = (self.directory / ".git/ai-phase/sessions.json").read_bytes()
                self.host = SimulatedClaude(self)
                text = (self.directory / ".claude/workflows" / (name + ".md")).read_text(encoding="utf-8")
                initialize = re.search(r'<step name="initialize"[^>]*>(.*?)</step>', text, re.S)[1]
                open_session = re.search(r'<step name="open_session"[^>]*>(.*?)</step>', text, re.S)[1]
                instructions = initialize + "\n" + open_session.split("`phase.locate` has already", 1)[0]
                actions = list(re.finditer(
                    r'phase_run query phase\.locate|prewrite\.request phase <label>|'
                    r'if \[ -n "\$\{worktree:-\}" \]; then cd|'
                    r'INIT=\$\(phase_run query (?P<init>init\.[\w.-]+)', instructions))
                self.assertTrue(actions, "installed workflow must provide executable routing steps")
                located, target, init_roots = None, None, []
                native_requests = 0
                for action in actions:
                    if action[0] == "phase_run query phase.locate":
                        located = self.host.runtime("phase.locate", label)
                        self.assertTrue(located["phase_found"])
                    elif action[0].startswith("if "):
                        if not self.host.completed and located.get("worktree"):
                            self.host.cwd = Path(located["worktree"])
                    elif action[0].startswith("prewrite.request"):
                        self.assertIsNotNone(located, "native bootstrap requires the read-only locator facts")
                        requested = self.host.runtime("prewrite.request", "phase", label, "--mode", mode)
                        native_requests += 1
                        target = self.host.runtime("prewrite.begin", requested["request_id"], "phase", label,
                                                   "--mode", mode)
                        self.host.enter(target)
                        self.assert_confirm(requested["request_id"], target, reused=mode == "existing")
                        located = self.host.runtime("phase.locate", label)
                        self.assertEqual(expected, self.host.read("source.txt"))
                    else:
                        bundle = self.host.runtime(action["init"], label)
                        self.assertTrue(bundle["phase_found"])
                        init_roots.append(self.host.cwd)
                self.assertEqual(1, native_requests, "workflow must not enter twice at open_session")
                self.assertEqual(1, len(self.host.events))
                self.assertTrue(init_roots)
                self.assertEqual([Path(target["worktree"])] * len(init_roots), init_roots,
                                 "destination initialization ran before native entry completed")
                if opened:
                    self.assertEqual(opened["base"], target["base"])
                    self.assertNotEqual(target["base"], self.host.git("rev-parse", "HEAD").strip())
                    self.assertEqual(metadata_before, (self.directory / ".git/ai-phase/sessions.json").read_bytes())

    def test_workflow_new_bootstrap_and_existing_ordinary_phase_quick_path_entry(self):
        """Workflow fixture has no intercepted edit and no fabricated denial.

        These public-interface cases are planned GREEN coverage. The role export
        assertion is structural and is not counted as the behavioral RED target.
        """
        self.assertIn("EnterWorktree", self.role_tools("coder"), "workflow caller must actually permit native entry")
        before = self.git("worktree", "list", "--porcelain")
        requested = self.runtime("prewrite.request", "quick", "workflow-new", "--mode", "new")
        self.assertEqual("workflow", requested["origin"])
        self.assertEqual(before, self.git("worktree", "list", "--porcelain"))
        request = requested["request_id"]
        self.begin(request, label="workflow-new", mode="existing", ok=False)
        target = self.begin(request, label="workflow-new")
        self.host.enter(target)
        self.assert_confirm(request, target)
        self.assertEqual(b"committed source\n", self.host.read("source.txt"))

        # Ordinary session.open creates these sessions, not a native hook. They
        # must work without a native-creation journal or metadata rewrite.
        for kind, label in (("phase", "01"), ("quick", "ordinary-existing")):
            with self.subTest(kind=kind):
                opened = self.runtime("session.open", kind, label, "--no-sync")
                session_root = Path(opened["worktree"])
                committed = ("committed " + kind + " session work\n").encode("utf-8")
                (session_root / "source.txt").write_bytes(committed)
                self.git("add", "source.txt", cwd=session_root)
                self.git("commit", "-qm", "advance ordinary " + kind + " session", cwd=session_root)
                advanced_head = self.git("rev-parse", "HEAD", cwd=session_root).strip()
                self.assertNotEqual(opened["base"], advanced_head)
                metadata = self.directory / ".git/ai-phase/sessions.json"
                sessions = metadata.read_bytes()
                self.host = SimulatedClaude(self)
                snapshot = self.inventory()
                bootstrap = self.runtime("prewrite.request", kind, label, "--mode", "existing")
                self.assertEqual("workflow", bootstrap["origin"])
                self.begin(bootstrap["request_id"], kind, label, "new", ok=False)
                existing = self.begin(bootstrap["request_id"], kind, label, "existing")
                self.assertEqual("existing", existing["mode"])
                self.assertEqual(Path(opened["worktree"]), Path(existing["worktree"]))
                self.assertEqual(opened["base"], existing["base"], "existing request rewrote the historical base")
                self.assertEqual(advanced_head, self.git("rev-parse", "HEAD", cwd=session_root).strip())
                self.assertFalse(existing.get("creation_name"), "ordinary sessions need no creation identity")
                self.assertEqual(snapshot[0], self.inventory()[0])
                self.host.eligible = False
                with self.assertRaisesRegex(SimulatedRefusal, "permitted root"):
                    self.host.enter(existing)
                self.host.eligible = True
                with self.assertRaisesRegex(SimulatedRefusal, "approval"):
                    self.host.enter(existing, approved=False)
                self.assertEqual([], self.host.events)
                self.host.enter(existing, approved=True)
                self.assert_confirm(bootstrap["request_id"], existing, reused=True)
                self.assertEqual(advanced_head, self.host.git("rev-parse", "HEAD").strip())
                self.assertEqual(committed, self.host.read("source.txt"), "fresh reads lost committed session work")
                self.assertEqual(sessions, metadata.read_bytes(), "existing confirmation rewrote ownership")
                self.assertEqual(snapshot[0], self.inventory()[0], "existing native entry created another checkout")
                self.assertEqual("path", next(iter(self.host.events[0][2])))

        self.runtime("prewrite.request", "quick", "missing-existing", "--mode", "existing", ok=False)
        self.runtime("session.open", "quick", "second-ordinary", "--no-sync")
        metadata = self.directory / ".git/ai-phase/sessions.json"
        entries = json.loads(metadata.read_text(encoding="utf-8"))
        for entry in entries["sessions"]:
            if entry["label"] == "second-ordinary":
                entry["label"] = "ordinary-existing"
        metadata.write_text(json.dumps(entries), encoding="utf-8")
        unchanged = metadata.read_bytes()
        self.runtime("prewrite.request", "quick", "ordinary-existing", "--mode", "existing", ok=False)
        self.assertEqual(unchanged, metadata.read_bytes(), "ambiguous bootstrap must not repair/rewrite ownership")


if __name__ == "__main__":
    unittest.main()
