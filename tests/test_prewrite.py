"""Boundary/failure fixtures over public prewrite operations and real Git.

No host entry is simulated here. Native creation events and selected timeout
outcomes are test inputs, not evidence that a live agent moved. The composed
installed host-adapter layer lives in test_same_agent_worktree.py.
"""
from contextlib import chdir, contextmanager
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".ai/runtime/phase.py"
sys.path.insert(0, str(RUNTIME.parent))
from lib import prewrite  # noqa: E402
from lib.results import VerbError  # noqa: E402


class PrewriteTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="prewrite-boundary-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "repo"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Boundary Fixture")
        self.git("config", "user.email", "boundary@example.invalid")
        (self.root / ".planning").mkdir()
        (self.root / ".planning/config.yaml").write_text('worktree:\n  root: "custom root"\n', encoding="utf-8")
        (self.root / ".gitignore").write_text("custom root/\nignored.bin\n", encoding="utf-8")
        (self.root / ".gitattributes").write_text("* -text\n", encoding="utf-8")
        (self.root / "source.md").write_bytes(b"committed source\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        self.state = self.root / ".git/ai-phase/prewrite"

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.root, check=True,
                              capture_output=True, encoding="utf-8").stdout.strip()

    @contextmanager
    def context(self, cwd=None, session="session"):
        environment = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.root))
        if session is None:
            environment.pop("CLAUDE_CODE_SESSION_ID", None)
        else:
            environment["CLAUDE_CODE_SESSION_ID"] = session
        with chdir(cwd or self.root), patch.dict(os.environ, environment, clear=True):
            yield

    def event(self, path="source.md", *, tool="Write", request="edit", cwd=None, actor="actor"):
        data = {"file_path": str(path), "content": "pending edit"}
        if tool == "Edit":
            data = {"file_path": str(path), "old_string": "source", "new_string": "changed"}
        elif tool == "MultiEdit":
            data = {"file_path": str(path), "edits": [{"old_string": "source", "new_string": "changed"}]}
        elif tool == "NotebookEdit":
            data = {"notebook_path": str(path), "new_source": "print(1)"}
        return {"hook_event_name": "PreToolUse", "cwd": str(cwd or self.root),
                "session_id": "session", "agent_id": actor, "tool_use_id": request,
                "tool_name": tool, "tool_input": data}

    def inventory(self):
        return (self.git("worktree", "list", "--porcelain"),
                {p.name: p.read_bytes() for p in self.state.glob("*.json")} if self.state.exists() else {})

    def reserve(self, label="unit"):
        record = prewrite.workflow_request(None, "quick", label, "new", "session", "actor")
        return prewrite.begin(None, record["request_id"], "quick", label, "new", "session", "actor")

    def native_event(self, record):
        return {"hook_event_name": "WorktreeCreate", "cwd": str(self.root),
                "session_id": "session", "agent_id": "actor", "name": record["creation_name"]}

    def test_notes_and_reads_do_not_need_identity_or_tickets(self):
        for host in ("claude", "codex"):
            for target in (".planning/scratchpads/nested/task.md", str(self.base / "plain PR body.md"),
                           ".planning/handoffs/opaque/scratch/task.md"):
                with self.subTest(host=host, path=target), self.context(session=None):
                    for existing in (False, True):
                        path = Path(target) if Path(target).is_absolute() else self.root / target
                        if existing:
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(b"existing note")
                        event = self.event(target)
                        event.pop("session_id")
                        event.pop("agent_id")
                        self.assertIsNone(prewrite.source_decision(event, host))
                    self.assertFalse(self.state.exists())
            with self.context(session=None):
                event = self.event(tool="Read")
                self.assertIsNone(prewrite.source_decision(event, host))
                self.assertFalse(self.state.exists())

    def test_native_mutation_tools_collect_source_targets(self):
        with self.context():
            for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"):
                with self.subTest(tool=tool):
                    event = self.event(tool=tool, request=tool)
                    event["agent_id"] = "actor-" + tool
                    if tool == "apply_patch":
                        event["tool_input"] = {"command": "*** Begin Patch\r\n*** Update File: source.md\r\n@@\r\n-committed source\r\n+changed\r\n*** End Patch\r\n"}
                    decision = prewrite.source_decision(event, "claude")["hookSpecificOutput"]
                    self.assertEqual("deny", decision["permissionDecision"])
                    self.assertIn("prewrite.begin", decision["permissionDecisionReason"])
            self.assertEqual(1, self.inventory()[0].count("worktree "))
            self.assertEqual(b"committed source\n", (self.root / "source.md").read_bytes())

    def test_tracked_mixed_delete_move_and_delivered_markdown_are_source(self):
        tracked = self.root / ".planning/scratchpads/tracked.md"
        tracked.parent.mkdir(parents=True)
        tracked.write_text("tracked", encoding="utf-8")
        self.git("add", ".planning/scratchpads/tracked.md")
        self.git("commit", "-qm", "tracked note is source")
        operations = [self.event(".planning/scratchpads/tracked.md"), self.event("source.md")]
        for body in ("*** Add File: .planning/scratchpads/note.md\n+note\n*** Update File: source.md\n@@\n-committed source\n+changed",
                     "*** Delete File: .planning/scratchpads/untracked.md",
                     "*** Update File: .planning/scratchpads/tracked.md\n*** Move to: moved.md\n@@\n-tracked\n+tracked"):
            event = self.event(tool="apply_patch")
            event["tool_input"] = {"command": "*** Begin Patch\n" + body + "\n*** End Patch"}
            operations.append(event)
        with self.context():
            for index, event in enumerate(operations):
                event["tool_use_id"] = "source-" + str(index)
                event["agent_id"] = "actor-" + str(index)
                self.assertIn("prewrite.begin", prewrite.source_decision(event, "claude")["hookSpecificOutput"]["permissionDecisionReason"])

    def test_unsafe_path_forms_refuse_without_creating_records(self):
        invalid = ("../escape.md", "", "C:relative.md", "//server/share/file", "source.md:stream",
                   "source.md\x00bad", ".git/config", str(self.root / "alias/../source.md"))
        with self.context():
            for path in invalid:
                with self.subTest(path=path), self.assertRaises(VerbError):
                    prewrite.source_decision(self.event(path), "claude")
            self.assertFalse(self.state.exists())
            # Canonical absolute and Windows separator spellings remain valid.
            for index, path in enumerate((str(self.root / "source.md"), "./source.md", "nested\\new.md")):
                self.assertIsNotNone(prewrite.source_decision(self.event(path, request=str(index), actor="actor-" + str(index)), "claude"))

    def test_existing_hardlink_never_gets_a_note_exemption(self):
        target = self.root / ".planning/scratchpads/hardlinked.md"
        target.parent.mkdir(parents=True)
        os.link(self.root / "source.md", target)
        with self.context(), self.assertRaises(VerbError):
            prewrite.source_decision(self.event(str(target)), "claude")

    def test_symlink_ancestor_never_gets_a_note_exemption(self):
        link = self.root / ".planning/scratchpads"
        try:
            link.symlink_to(self.base, target_is_directory=True)
        except OSError as exc:
            self.skipTest("symlink creation unavailable: " + str(exc))
        with self.context(), self.assertRaises(VerbError):
            prewrite.source_decision(self.event(".planning/scratchpads/linked.md"), "claude")

    @unittest.skipUnless(os.name == "nt", "Windows junction control")
    def test_windows_junction_ancestor_is_refused(self):
        junction = self.root / ".planning/scratchpads"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(self.base)], capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        with self.context(), self.assertRaises(VerbError):
            prewrite.source_decision(self.event(".planning/scratchpads/junction.md"), "claude")

    @unittest.skipUnless(os.name == "nt", "Windows short-path alias control")
    def test_windows_short_alias_is_kept_raw_and_refused(self):
        import ctypes
        buffer = ctypes.create_unicode_buffer(32768)
        size = ctypes.windll.kernel32.GetShortPathNameW(str(self.root), buffer, len(buffer))
        self.assertGreater(size, 0)
        if os.path.normcase(buffer.value) == os.path.normcase(str(self.root)):
            self.skipTest("filesystem has no alternate 8.3 spelling for this fixture")
        alias = buffer.value + "\\source.md"  # Deliberately do not resolve it.
        with self.context(), self.assertRaises(VerbError):
            prewrite.source_decision(self.event(alias), "claude")

    def test_nested_repository_and_non_temp_external_targets_are_not_notes(self):
        nested = self.root / ".planning/scratchpads/nested"
        nested.mkdir(parents=True)
        self.git("init", "-q", str(nested))
        with self.context(), self.assertRaises(VerbError):
            prewrite.source_decision(self.event(str(nested / "task.md")), "claude")
        with self.context(), patch.object(prewrite.tempfile, "gettempdir", return_value=str(self.base / "other-temp")), self.assertRaises(VerbError):
            prewrite.source_decision(self.event(str(self.base / "outside.md")), "claude")
        mixed = self.event(tool="apply_patch")
        mixed["tool_input"] = {"command": "*** Begin Patch\n*** Add File: " + (self.base / "note.md").as_posix() + "\n+note\n*** Delete File: source.md\n*** End Patch"}
        with self.context(), self.assertRaises(VerbError):
            prewrite.source_decision(mixed, "claude")

    def test_session_correlation_and_actor_claim_conflicts_refuse(self):
        with self.context(session=None), self.assertRaises(VerbError):
            prewrite.workflow_request(None, "quick", "unit", "new", "claimed-only", None)
        with self.context():
            missing = self.event()
            missing.pop("session_id")
            with self.assertRaises(VerbError):
                prewrite.source_decision(missing, "claude")
            record = self.reserve()
            before = self.inventory()
            for session, actor in (("different", "actor"), ("session", "different")):
                with self.assertRaises(VerbError):
                    prewrite.begin(None, record["request_id"], "quick", "unit", "new", session, actor)
            payload = self.native_event(record)
            payload["agent_id"] = "wrong-native-actor"
            with self.assertRaises(VerbError):
                prewrite.native_create(payload)
            self.assertEqual(before, self.inventory())
        # No optional agent-ID environment is invented, and absence alone does
        # not attest main-agent eligibility or host binding.
        with self.context():
            provisional = prewrite.workflow_request(None, "quick", "provisional", "new")
            self.assertIsNone(provisional["agent_id"])
            self.assertNotIn("host_binding_verified", provisional)

    def test_repeat_changed_targets_and_stale_tickets_do_not_recreate(self):
        with self.context():
            event = self.event()
            first = prewrite.source_decision(event, "claude")
            before = self.inventory()
            self.assertEqual(first, prewrite.source_decision(event, "claude"))
            self.assertEqual(before, self.inventory())
            event["tool_input"]["file_path"] = "changed-target.md"
            with self.assertRaises(VerbError):
                prewrite.source_decision(event, "claude")
            self.assertEqual(before, self.inventory())
            request = re.search(r"prewrite.begin ([0-9a-f]+)", str(first))[1]
            path = self.state / (request + ".json")
            record = json.loads(path.read_text(encoding="utf-8"))
            record["created"] = 1
            path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaises(VerbError):
                prewrite.begin(None, request, "quick", "unit", "new", "session", "actor")
            self.assertEqual(1, self.inventory()[0].count("worktree "))

    def test_retried_source_with_new_tool_id_reuses_pending_request(self):
        with self.context():
            first = prewrite.source_decision(self.event(request="original"), "claude")
            before = self.inventory()
            retried = prewrite.source_decision(self.event(request="host-retry-new-id"), "claude")
            self.assertEqual(first, retried, "host-generated retry IDs must not reserve another native unit")
            self.assertEqual(before, self.inventory())
            with self.assertRaises(VerbError):
                prewrite.source_decision(self.event("different.md", request="changed-intent"), "claude")
            self.assertEqual(before, self.inventory())

    def test_confirmed_native_session_survives_ticket_expiry_and_requires_observed_actor(self):
        with self.context():
            record = self.reserve()
            prewrite.native_create(self.native_event(record))
        with self.context(record["worktree"]):
            prewrite.confirm(None, record["request_id"], "session", "actor")
            missing = self.event(cwd=record["worktree"])
            missing.pop("agent_id")
            with self.assertRaises(VerbError):
                prewrite.source_decision(missing, "claude")
            path = self.state / (record["request_id"] + ".json")
            confirmed = json.loads(path.read_text(encoding="utf-8"))
            confirmed["created"] = 1
            path.write_text(json.dumps(confirmed), encoding="utf-8")
            self.assertIsNone(prewrite.source_decision(self.event(cwd=record["worktree"]), "claude"))

    def test_incomplete_bound_journal_returns_structured_cli_refusal(self):
        with self.context():
            record = self.reserve()
        record.update(mode="existing", worktree=str(self.root))
        record.pop("existing_session", None)
        (self.state / (record["request_id"] + ".json")).write_text(json.dumps(record), encoding="utf-8")
        environment = dict(os.environ, CLAUDE_CODE_SESSION_ID="session", PYTHONIOENCODING="utf-8")
        result = subprocess.run([sys.executable, str(RUNTIME), "query", "prewrite.confirm", record["request_id"],
                                 "--session-id", "session", "--agent-id", "actor"],
                                cwd=self.root, env=environment, capture_output=True, encoding="utf-8")
        self.assertEqual(1, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(json.loads(result.stdout)["ok"])

    def test_new_native_checkout_cannot_advance_before_first_confirmation(self):
        with self.context():
            record = self.reserve()
            prewrite.native_create(self.native_event(record))
        root = Path(record["worktree"])
        (root / "source.md").write_bytes(b"unexpected committed native work\n")
        self.git("add", "source.md", cwd=root)
        self.git("commit", "-qm", "unexpected pre-confirm work", cwd=root)
        with self.context(root), self.assertRaises(VerbError):
            prewrite.confirm(None, record["request_id"], "session", "actor")
        self.assertEqual(b"unexpected committed native work\n", (root / "source.md").read_bytes())

    def test_explicit_units_modes_and_repeated_begin_never_alias(self):
        with self.context():
            first = self.reserve("first")
            self.assertEqual(first, prewrite.begin(None, first["request_id"], "quick", "first", "new", "session", "actor"))
            second = self.reserve("second")
            self.assertNotEqual(first["worktree"], second["worktree"])
            self.assertNotEqual(first["branch"], second["branch"])
            with self.assertRaises(VerbError):
                prewrite.begin(None, first["request_id"], "quick", "first", "existing", "session", "actor")
            duplicate = prewrite.workflow_request(None, "quick", "first", "new", "session", "actor")
            with self.assertRaises(VerbError):
                prewrite.begin(None, duplicate["request_id"], "quick", "first", "new", "session", "actor")
            self.assertEqual(1, self.inventory()[0].count("worktree "))

    def test_precreated_registered_tree_is_not_a_native_receipt(self):
        with self.context():
            record = self.reserve()
            self.git("worktree", "add", "-b", record["branch"], record["worktree"], record["base"])
        with self.context(record["worktree"]), self.assertRaises(VerbError):
            prewrite.confirm(None, record["request_id"], "session", "actor")
        with self.context(), self.assertRaises(VerbError):
            prewrite.native_create(self.native_event(record))
        self.assertFalse((self.root / ".git/ai-phase/sessions.json").exists())

    def test_native_path_and_branch_collisions_preserve_existing_data(self):
        with self.context():
            for collision in ("path", "branch"):
                record = self.reserve(collision)
                if collision == "path":
                    path = Path(record["worktree"])
                    path.mkdir(parents=True)
                    (path / "owned.bin").write_bytes(b"pre-existing\x00data")
                else:
                    self.git("branch", record["branch"])
                before = self.inventory()
                with self.assertRaises(VerbError):
                    prewrite.native_create(self.native_event(record))
                self.assertEqual(before, self.inventory())
            self.assertEqual(b"pre-existing\x00data", (self.root / "custom root" / ("wf-entry-" + next(
                path.stem for path in self.state.glob("*.json") if json.loads(path.read_text())["label"] == "path")) / "owned.bin").read_bytes())

    def test_uncertain_failures_before_and_after_creation_preserve_dirty_primary(self):
        (self.root / "source.md").write_bytes(b"staged primary\n")
        self.git("add", "source.md")
        (self.root / "source.md").write_bytes(b"unstaged over staged\n")
        (self.root / "untracked.bin").write_bytes(b"untracked\x00\xff")
        (self.root / "ignored.bin").write_bytes(b"ignored\x00\xff")
        before = (self.git("ls-files", "--stage"), self.git("status", "--porcelain"),
                  {name: (self.root / name).read_bytes() for name in ("source.md", "untracked.bin", "ignored.bin")})
        original = prewrite.Budget.git
        for after in (False, True):
            with self.subTest(after_creation=after), self.context():
                record = self.reserve("failure-" + str(after))

                def timed_out(budget, cwd, *args, **options):
                    if args[:2] == ("worktree", "add"):
                        if after:
                            original(budget, cwd, *args, **options)
                        raise VerbError("SIMULATED lost Git creation result", "prewrite-timeout")
                    return original(budget, cwd, *args, **options)

                with patch.object(prewrite.Budget, "git", timed_out), self.assertRaises(VerbError):
                    prewrite.native_create(self.native_event(record))
                self.assertEqual("uncertain", json.loads((self.state / (record["request_id"] + ".json")).read_text())["state"])
                snapshot = self.inventory()
                with self.assertRaises(VerbError):
                    prewrite.native_create(self.native_event(record))
                self.assertEqual(snapshot, self.inventory())
                self.assertEqual(after, Path(record["worktree"]).exists())
                if after:
                    with self.context(record["worktree"]):
                        verified = prewrite.confirm(None, record["request_id"], "session", "actor")
                        self.assertFalse(verified["host_binding_verified"])
                        self.assertEqual(b"committed source\n", (Path.cwd() / "source.md").read_bytes())
                current = (self.git("ls-files", "--stage"), self.git("status", "--porcelain"),
                           {name: (self.root / name).read_bytes() for name in before[2]})
                self.assertEqual(before, current)

    def test_correct_ordinary_isolated_control_allows_both_hosts(self):
        worktree = self.root / "custom root/ordinary"
        self.git("worktree", "add", "-b", "quick-ordinary", str(worktree))
        for host in ("claude", "codex"):
            with self.context(worktree):
                self.assertIsNone(prewrite.source_decision(self.event(cwd=worktree), host))
        self.assertFalse(self.state.exists())

    def test_source_root_head_and_config_drift_refuse_creation(self):
        with self.context():
            record = self.reserve()
            (self.root / "source.md").write_text("new committed head", encoding="utf-8")
            self.git("add", "source.md")
            self.git("commit", "-qm", "advance primary")
            with self.assertRaises(VerbError):
                prewrite.native_create(self.native_event(record))
            self.assertFalse(Path(record["worktree"]).exists())
            record = self.reserve("branch-drift")
            self.git("branch", "-m", "renamed-fixture-primary")
            with self.assertRaises(VerbError):
                prewrite.native_create(self.native_event(record))
            record = self.reserve("config-drift")
            (self.root / ".planning/config.yaml").write_text("worktree:\n  root: different-root\n", encoding="utf-8")
            with self.assertRaises(VerbError):
                prewrite.native_create(self.native_event(record))
            self.assertFalse(Path(record["worktree"]).exists())

    def test_malformed_captured_inputs_refuse_and_cli_json_failure_is_exit_two(self):
        with self.context():
            for data in (None, {}, {"file_path": []}):
                event = self.event()
                event["tool_input"] = data
                with self.assertRaises(VerbError):
                    prewrite.source_decision(event, "claude")
            empty = self.event(tool="apply_patch")
            empty["tool_input"] = {"command": "*** Begin Patch\n*** End Patch"}
            with self.assertRaises(VerbError):
                prewrite.source_decision(empty, "claude")
            for tool, data in (([], {}), ("MultiEdit", {"file_path": "source.md", "edits": [{"file_path": "other.md"}]}),
                               ("apply_patch", {"command": "*** Begin Patch\n*** Update File: source.md\n*** End Patch"}),
                               ("apply_patch", {"command": "one", "patch": "another"})):
                event = self.event()
                event.update(tool_name=tool, tool_input=data)
                with self.assertRaises(VerbError):
                    prewrite.source_decision(event, "claude")
        for raw in (b"{", b"[]", b'{"tool_name":"Write","tool_name":"Edit"}'):
            result = subprocess.run([sys.executable, str(RUNTIME.parent / "lib/prewrite.py"), "hook", "--host", "claude"],
                                    cwd=self.root, input=raw, capture_output=True)
            self.assertEqual(2, result.returncode)
            self.assertFalse(result.stdout)
            self.assertIn(b"source-prewrite:", result.stderr)
            self.assertNotIn(b"Traceback", result.stderr)
        with self.assertRaises(VerbError):
            prewrite.Budget(seconds=0).git(self.root, "status")

    def test_os_released_lock_has_bounded_contention_and_recovers(self):
        script = ("from lib import prewrite; import sys; "
                  "b=prewrite.Budget(); i=prewrite.facts(b); "
                  "\nwith prewrite.locked(i,b):\n print('locked',flush=True); sys.stdin.read(1)\n")
        environment = dict(os.environ, PYTHONPATH=str(RUNTIME.parent), PYTHONIOENCODING="utf-8")
        child = subprocess.Popen([sys.executable, "-c", script], cwd=self.root, env=environment,
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual("locked", child.stdout.readline().strip())
            with self.context():
                started = time.monotonic()
                with self.assertRaises(VerbError) as refusal:
                    self.reserve()
                self.assertEqual("prewrite-busy", refusal.exception.code)
                self.assertLess(time.monotonic() - started, 5, "lock must not outlive source hook budget")
            child.terminate()
            child.communicate(timeout=5)
            with self.context():
                self.assertEqual("ready", self.reserve()["state"])
        finally:
            if child.poll() is None:
                child.terminate()
            child.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
