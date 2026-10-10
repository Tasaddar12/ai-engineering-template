"""Offline subprocess proofs for selected-TODO issue publication and retirement."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".ai/runtime/phase.py"

# A real child process models persistent GitHub state. Only the gh executable
# boundary is redirected; Git, CLI parsing, locks and TODO files are real.
FAKE_GH = r'''
import json, os, sys
from pathlib import Path
import yaml
path = Path(os.environ["FAKE_GH_STATE"])
data = json.loads(path.read_text(encoding="utf-8"))
args = sys.argv[1:]
data["calls"].append(args)
out, code = "", 0
mode = data.get("mode", "")
repo = "github.com/acme/project"
if args == ["--version"]:
    out = "gh fixture"
elif args[:2] == ["auth", "status"]:
    if mode == "auth":
        code = 1
elif args[:2] == ["repo", "view"]:
    assert args[2] == repo
    out = json.dumps({"nameWithOwner": "acme/project",
                      "url": "https://github.com/acme/project",
                      "hasIssuesEnabled": mode != "disabled"})
    if mode == "repo-mismatch":
        out = json.dumps({"nameWithOwner": "other/project",
                          "url": "https://github.com/other/project",
                          "hasIssuesEnabled": True})
elif args[0] == "api":
    assert "--hostname" in args and args[args.index("--hostname")+1] == "github.com"
    assert "--method" in args and args[args.index("--method")+1] == "GET"
    endpoint = args[1]
    assert endpoint.startswith("repos/acme/project/")
    if "?" in endpoint:
        assert "--paginate" in args and "--slurp" in args
        assert "state=all" in endpoint and "per_page=100" in endpoint
        records = data["issues"] if "/issues?" in endpoint else data["pulls"]
        if mode == "preview-mutate":
            todo = Path(data["todo"])
            todo.write_text(todo.read_text(encoding="utf-8") + "\nConcurrent context\n",
                            encoding="utf-8")
        pages = [records[i:i+100] for i in range(0, len(records), 100)] or [[]]
        out = json.dumps(pages)
        if mode == "lookup":
            code = 1
        elif mode == "json":
            out = "{bad json"
        elif mode == "pagination":
            out = json.dumps(records)
    else:
        number = int(endpoint.rsplit("/", 1)[1])
        records = data["pulls"] if "/pulls/" in endpoint else data["issues"]
        matches = [i for i in records if i["number"] == number]
        if not matches or mode == "view" or (mode == "readback" and data["creates"]):
            code = 1
        else:
            out = json.dumps(dict(matches[0], **data.get("direct_changes", {})))
elif args[:2] == ["issue", "create"]:
    assert args[args.index("--repo")+1] == repo
    todo = Path(data["todo"])
    metadata = yaml.safe_load(todo.read_text(encoding="utf-8").split("---", 2)[1])
    assert metadata["issuePublication"]["state"] == "attempted"
    assert metadata["issuePublication"]["publicTitle"] == args[args.index("--title")+1]
    data["creates"] += 1
    if mode != "create-before":
        number = max([i["number"] for i in data["issues"]] + [0]) + 1
        issue = {"number": number, "html_url": "https://github.com/acme/project/issues/" + str(number),
                 "title": args[args.index("--title")+1], "state": "open",
                 "body": Path(args[args.index("--body-file")+1]).read_text(encoding="utf-8")}
        if mode == "bad-title":
            issue["title"] = "unexpected title"
        if mode == "bad-body":
            issue["body"] = "unexpected body"
        data["issues"].append(issue)
        out = issue["html_url"]
        if mode == "mutate":
            todo.write_text(todo.read_text(encoding="utf-8") + "\nChanged after creation\n",
                            encoding="utf-8")
    if mode in ("lost", "create-before", "create-after"):
        code, out = 1, ""
else:
    raise AssertionError("unexpected provider call " + repr(args))
path.write_text(json.dumps(data), encoding="utf-8")
print(out)
if code:
    print("PRIVATE PROVIDER LOG MUST NOT LEAK", file=sys.stderr)
sys.exit(code)
'''

DRIVER = r'''
import os, runpy, subprocess, sys
sys.path.insert(0, os.environ["FAKE_RUNTIME_LIB"])
from lib import delivery, todos
# Inject filesystem failures at actual write/replace boundaries, scoped to one
# selected save state. The real serializer and persistence helper still run.
import builtins, json
from pathlib import Path
fault = os.environ.get("TODO_SAVE_FAULT")
active = False
if fault:
    saved_open, saved_fdopen, saved_replace = builtins.open, os.fdopen, os.replace
    saved_record = todos.save_record
    todo = Path(os.environ["TODO_FAULT_PATH"]).resolve()
    def record_fault():
        Path(os.environ["TODO_FAULT_FIRED"]).write_text(
            os.environ["TODO_FAULT_STATE"] + ":" + fault, encoding="utf-8")
    class FailingWrite:
        def __init__(self, handle):
            self.handle = handle
        def __enter__(self):
            self.handle.__enter__()
            return self
        def __exit__(self, *args):
            return self.handle.__exit__(*args)
        def __getattr__(self, name):
            return getattr(self.handle, name)
        def write(self, value):
            self.handle.write(value[:20])
            record_fault()
            raise OSError("PRIVATE FILESYSTEM DETAIL")
    def failing_open(path, mode="r", *args, **options):
        handle = saved_open(path, mode, *args, **options)
        if active and fault == "write" and Path(path).resolve() == todo and "w" in mode:
            return FailingWrite(handle)
        return handle
    def failing_fdopen(*args, **options):
        handle = saved_fdopen(*args, **options)
        return FailingWrite(handle) if active and fault == "write" else handle
    def failing_replace(source, target, *args, **options):
        if active and fault == "replace" and Path(target).resolve() == todo:
            record_fault()
            raise OSError("PRIVATE FILESYSTEM DETAIL")
        return saved_replace(source, target, *args, **options)
    def failing_record(path, metadata, body):
        global active
        state = (metadata.get("issuePublication") or {}).get("state", "identity")
        active = state == os.environ["TODO_FAULT_STATE"]
        if active:
            Path(os.environ["TODO_FAULT_BEFORE"]).write_bytes(todo.read_bytes())
        try:
            return saved_record(path, metadata, body)
        finally:
            active = False
    builtins.open, os.fdopen, os.replace = failing_open, failing_fdopen, failing_replace
    todos.save_record = failing_record
original = subprocess.run
def redirect(command, **options):
    if command and command[0] == "gh":
        command = [sys.executable, os.environ["FAKE_GH_SCRIPT"], *command[1:]]
    return original(command, **options)
delivery.subprocess.run = redirect
sys.argv = [os.environ["FAKE_RUNTIME"], *sys.argv[1:]]
runpy.run_path(os.environ["FAKE_RUNTIME"], run_name="__main__")
'''


class TodoIssues(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="todo-issues-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Todo Fixture")
        self.git("config", "user.email", "todo@example.test")
        (self.directory / "README.md").write_text("# Fixture\n", encoding="utf-8")
        self.git("add", "--", "README.md")
        self.git("commit", "-qm", "initial")
        self.git("remote", "add", "origin", "https://github.com/acme/project.git")
        (self.directory / ".planning/todos/pending").mkdir(parents=True)
        self.todo = self.directory / ".planning/todos/pending/legacy.md"
        self.body = "\n## Problem\n\nPrivate customer evidence\n\n## Solution\n\nSafe approach hints\n\n## Context\n\nFull local context.\n"
        self.todo.write_text("---\ntitle: Private customer title\narea: tooling\nseverity: major\nfiles: [src/app.py:12]\ncustom: retain me\n---\n" + self.body,
                             encoding="utf-8")
        self.public = self.directory / "reviewed public.md"
        self.public.write_text("## Problem\n\nSafe evidence\n\n## ExpectedBehavior\n\nResolve it\n\n## Acceptance\n\nRepro passes\n\n## Scope\n\nsrc/app.py\n", encoding="utf-8")
        self.fake = self.directory / "fake_gh.py"
        self.fake.write_text(FAKE_GH, encoding="utf-8")
        self.statefile = self.directory / "remote.json"
        self.save({"calls": [], "issues": [], "pulls": [], "creates": 0,
                   "todo": str(self.todo)})
        self.environment = dict(os.environ, PYTHONIOENCODING="utf-8",
                                GH_REPO="hostile/redirect",
                                FAKE_RUNTIME=str(RUNTIME),
                                FAKE_RUNTIME_LIB=str(RUNTIME.parent),
                                FAKE_GH_SCRIPT=str(self.fake),
                                FAKE_GH_STATE=str(self.statefile))

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.directory,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def save(self, data):
        self.statefile.write_text(json.dumps(data), encoding="utf-8")

    def remote(self, **changes):
        data = json.loads(self.statefile.read_text(encoding="utf-8"))
        data.update(changes)
        self.save(data)
        return data

    def run_verb(self, *args, ok=True):
        result = subprocess.run([sys.executable, "-c", DRIVER, "query", *args],
                                cwd=self.directory, env=self.environment,
                                capture_output=True, text=True, encoding="utf-8")
        self.assertNotIn("Traceback", result.stderr, result.stderr)
        if self.environment.get("TODO_SAVE_FAULT"):
            fired = Path(self.environment["TODO_FAULT_FIRED"])
            self.assertTrue(fired.is_file(), "selected save fault never fired")
            self.assertEqual(fired.read_text(encoding="utf-8"),
                             self.environment["TODO_FAULT_STATE"] + ":" +
                             self.environment["TODO_SAVE_FAULT"])
        payload = json.loads(result.stdout)
        self.assertEqual(bool(payload.get("ok")), ok, payload)
        self.assertEqual(result.returncode, 0 if ok else 1)
        self.assertNotIn("PRIVATE PROVIDER LOG", result.stdout + result.stderr)
        return payload

    def metadata(self):
        return yaml.safe_load(self.todo.read_text(encoding="utf-8").split("---", 2)[1])

    def patch_metadata(self, **fields):
        text = self.todo.read_text(encoding="utf-8")
        metadata = self.metadata()
        metadata.update(fields)
        self.todo.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n" +
                             text.split("---", 2)[2].lstrip("\n"), encoding="utf-8")

    def preview(self, *args, ok=True):
        return self.run_verb("todo.issue-preview", self.todo.name, *args, ok=ok)

    def publish(self, preview=None, *decision, ok=True, title="Public reviewed title"):
        preview = preview or self.preview()
        return self.run_verb("todo.issue-publish", self.todo.name,
                        "--preview-token", preview["previewToken"], "--title", title,
                        "--body-file", str(self.public), *(decision or ("--no-match",)), ok=ok)

    def issue(self, number=1, state="open", title="Existing semantic duplicate", body="Relevant evidence"):
        return {"number": number, "html_url": "https://github.com/acme/project/issues/" + str(number),
                "title": title, "body": body, "state": state}

    def inject_save_failure(self, state, fault):
        before = self.directory / "before-failed-save.md"
        fired = self.directory / "save-fault-fired.txt"
        fired.unlink(missing_ok=True)
        # A portable alias reproduces the lexical/canonical mismatch also seen
        # with Windows DOS 8.3 temporary roots, without filesystem privileges.
        alias = self.todo.parent / ".." / "pending" / self.todo.name
        self.assertNotEqual(alias, self.todo)
        self.assertEqual(alias.resolve(), self.todo.resolve())
        self.environment.update(TODO_SAVE_FAULT=fault, TODO_FAULT_STATE=state,
                                TODO_FAULT_PATH=str(alias),
                                TODO_FAULT_BEFORE=str(before),
                                TODO_FAULT_FIRED=str(fired))
        return before

    def clear_save_failure(self):
        for key in ("TODO_SAVE_FAULT", "TODO_FAULT_STATE", "TODO_FAULT_PATH",
                    "TODO_FAULT_BEFORE", "TODO_FAULT_FIRED"):
            self.environment.pop(key, None)

    def assert_pending_context(self):
        self.assertEqual(self.metadata()["custom"], "retain me")
        self.assertTrue(self.todo.read_text(encoding="utf-8").endswith(self.body))
        self.assertFalse(self.metadata().get("issueURL"))

    def test_failed_link_write_preserves_attempt_and_recovers_once(self):
        original = self.todo.read_bytes()
        for fault in ("write", "replace"):
            with self.subTest(fault=fault):
                self.clear_save_failure()
                self.todo.write_bytes(original)
                self.remote(issues=[], creates=0)
                self.patch_metadata(issuePublication={}, issueURL=None, issueNumber=None)
                preview = self.preview()
                before = self.inject_save_failure("linked", fault)
                failure = self.publish(preview, ok=False)
                self.assertEqual(failure["code"], "todo-write")
                self.assertNotIn("PRIVATE FILESYSTEM DETAIL", json.dumps(failure))
                self.assertEqual(self.todo.read_bytes(), before.read_bytes())
                self.assert_pending_context()
                metadata = self.metadata()
                self.assertEqual(metadata["todoId"], preview["todoId"])
                self.assertEqual(metadata["issuePublication"]["state"], "attempted")
                self.assertTrue(metadata["issuePublication"]["intentDigest"])
                self.assertEqual(self.remote()["creates"], 1)
                self.assertEqual(list(self.todo.parent.iterdir()), [self.todo])
                self.clear_save_failure()
                self.run_verb("todo.complete", self.todo.name, ok=False)
                recovered = self.publish()
                self.assertTrue(recovered["recovered"])
                self.assertEqual(recovered["todoId"], preview["todoId"])
                self.assertEqual(self.remote()["creates"], 1)
                self.assertEqual(len(self.remote()["issues"]), 1)

    def test_failed_prepared_or_attempted_save_prevents_create(self):
        original = self.todo.read_bytes()
        for state in ("prepared", "attempted"):
            for fault in ("write", "replace"):
                with self.subTest(state=state, fault=fault):
                    self.clear_save_failure()
                    self.todo.write_bytes(original)
                    self.patch_metadata(issuePublication={}, issueURL=None, issueNumber=None)
                    preview = self.preview() if state == "attempted" else None
                    before = self.inject_save_failure(state, fault)
                    failure = (self.publish(preview, ok=False) if preview
                               else self.preview(ok=False))
                    self.assertEqual(failure["code"], "todo-write")
                    self.assertEqual(self.todo.read_bytes(), before.read_bytes())
                    self.assertTrue(self.todo.read_text(encoding="utf-8").endswith(self.body))
                    self.assertEqual(self.remote()["creates"], 0)
                    self.assertEqual(list(self.todo.parent.iterdir()), [self.todo])
                    self.clear_save_failure()

    def test_direct_duplicate_changes_refuse_stale_review(self):
        original = self.todo.read_bytes()
        for selection in ("semantic", "marker"):
            for changes in ({"title": "Changed after lookup"},
                            {"body": "Different scope"}, {"state": "closed"}):
                with self.subTest(selection=selection, changes=changes):
                    self.todo.write_bytes(original)
                    self.remote(issues=[], direct_changes={})
                    preview = self.preview()
                    body = ("<!-- todo-id: " + preview["todoId"] + " -->"
                            if selection == "marker" else "Relevant evidence")
                    self.remote(issues=[self.issue(body=body)], direct_changes={})
                    preview = self.preview()
                    before = self.todo.read_bytes()
                    self.remote(direct_changes=changes)
                    decision = (("--existing-issue", self.issue()["html_url"])
                                if selection == "semantic" else ("--no-match",))
                    failure = self.publish(preview, *decision, ok=False)
                    self.assertEqual(failure["code"], "stale-preview")
                    self.assertEqual(self.todo.read_bytes(), before)
                    self.assert_pending_context()
                    self.assertEqual(self.remote()["creates"], 0)
                    self.remote(direct_changes={})

    def test_attempted_without_url_cannot_complete_or_lose_context(self):
        self.patch_metadata(issuePublication={"state": "attempted", "intentDigest": "unknown"})
        before = self.todo.read_bytes()
        failure = self.run_verb("todo.complete", self.todo.name, ok=False)
        self.assertEqual(failure["code"], "issue-unresolved")
        self.assertEqual(self.todo.read_bytes(), before)
        self.assertFalse((self.directory / ".planning/todos/completed").exists())

    def test_preview_stable_identity_and_private_complete_context(self):
        first = self.preview()
        second = self.preview()
        self.assertEqual(first["todoId"], second["todoId"])
        self.assertEqual(first["previewToken"], second["previewToken"])
        self.assertEqual(first["privateLocal"]["label"], "PRIVATE LOCAL REVIEW INPUT")
        self.assertEqual(first["privateLocal"]["title"], "Private customer title")
        self.assertIn("Full local context", first["privateLocal"]["body"])
        self.assertEqual(first["privateLocal"]["metadata"]["files"], ["src/app.py:12"])
        self.assertEqual(self.metadata()["custom"], "retain me")
        self.assertTrue(self.todo.read_text(encoding="utf-8").endswith(self.body))
        self.assertEqual(self.remote()["creates"], 0)

    def test_new_todo_identity_and_legacy_listing_remain_usable(self):
        added = self.run_verb("todo.add", "New capture", "--problem", "Full repro",
                         "--solution", "Approach", "--files", "src/app.py:12")
        self.assertTrue(added["todoId"])
        listed = self.run_verb("todo.list")
        self.assertEqual(listed["count"], 2)
        self.assertTrue(all(item.get("todoId") for item in listed["todos"] if item["title"] == "New capture"))
        new_preview = self.run_verb("todo.issue-preview", Path(added["file"]).name)
        self.assertEqual(new_preview["todoId"], added["todoId"])
        self.run_verb("todo.complete", Path(added["file"]).name)

    def test_create_only_reviewed_public_content_and_link_pending(self):
        result = self.publish()
        metadata = self.metadata()
        issue = self.remote()["issues"][0]
        self.assertTrue(result["created"])
        self.assertEqual(metadata["issueURL"], issue["html_url"])
        self.assertEqual(metadata["issueNumber"], issue["number"])
        self.assertEqual(metadata["issuePublication"]["state"], "linked")
        self.assertEqual(issue["title"], "Public reviewed title")
        self.assertNotIn("Private customer", issue["body"] + issue["title"])
        self.assertIn("<!-- todo-id: " + metadata["todoId"] + " -->", issue["body"])
        self.assertTrue(self.todo.read_text(encoding="utf-8").endswith(self.body))
        self.assertTrue(self.todo.exists())
        linked = self.run_verb("todo.list")["todos"][0]
        self.assertEqual(linked["issueURL"], metadata["issueURL"])

    def test_missing_or_empty_public_title_and_decision_refuse_before_create(self):
        preview = self.preview()
        options = ["--preview-token", preview["previewToken"], "--body-file", str(self.public)]
        for extra in (["--no-match"], ["--title", "", "--no-match"],
                      ["--title", "Public"], ["--title", "Public", "--no-match",
                                             "--existing-issue", self.issue()["html_url"]]):
            with self.subTest(extra=extra):
                self.run_verb("todo.issue-publish", self.todo.name, *options, *extra, ok=False)
        self.assertEqual(self.remote()["creates"], 0)

    def test_semantic_reuse_open_and_closed_does_not_edit_or_complete(self):
        for state in ("open", "closed"):
            with self.subTest(state=state):
                self.remote(issues=[self.issue(state=state)])
                result = self.publish(None, "--existing-issue", self.issue()["html_url"])
                self.assertFalse(result["created"])
                self.assertTrue(self.todo.exists())
                self.assertEqual(self.remote()["creates"], 0)
                self.assertEqual(self.remote()["issues"][0]["title"], "Existing semantic duplicate")
                self.assertFalse(any(c[:2] in (["issue", "edit"], ["issue", "close"])
                                     for c in self.remote()["calls"]))

    def test_preview_includes_closed_candidates_and_complete_pagination(self):
        records = [self.issue(number=n, state="closed") for n in range(1, 102)]
        self.remote(issues=records)
        result = self.preview()
        self.assertEqual(len(result["candidates"]), 101)
        self.assertEqual(result["candidates"][-1]["number"], 101)

    def test_pr_objects_excluded_and_related_context_selected(self):
        pr = {"number": 3, "html_url": "https://github.com/acme/project/pull/3",
              "title": "Related PR", "body": "PR context", "state": "open",
              "head": {"ref": self.git("branch", "--show-current")}}
        issue_pr = self.issue(number=3)
        issue_pr["pull_request"] = {"url": "u"}
        self.remote(issues=[issue_pr, self.issue()], pulls=[pr])
        result = self.preview("--related-pr", pr["html_url"])
        self.assertEqual([i["number"] for i in result["candidates"]], [1])
        self.assertEqual(result["relatedPRs"][0]["body"], "PR context")

    def test_bad_repository_auth_lookup_json_and_pagination_block(self):
        for mode in ("auth", "disabled", "repo-mismatch", "lookup", "json", "pagination"):
            with self.subTest(mode=mode):
                self.remote(mode=mode)
                self.preview(ok=False)
                self.assertNotIn("issueURL", self.metadata())
                self.assertEqual(self.remote()["creates"], 0)

    def test_wrong_origin_or_supplied_urls_cannot_redirect(self):
        self.git("remote", "set-url", "origin", "https://example.test/acme/project")
        self.preview(ok=False)
        self.git("remote", "set-url", "origin", "git@github.com:acme/project.git")
        self.preview("--related-pr", "https://github.com/other/repo/pull/3", ok=False)
        self.publish(None, "--existing-issue", "https://github.com/other/repo/issues/1", ok=False)
        self.assertEqual(self.remote()["creates"], 0)

    def test_stale_local_candidate_and_pr_context_invalidate_preview(self):
        for kind in ("local", "issue", "pr"):
            with self.subTest(kind=kind):
                preview = self.preview()
                if kind == "local":
                    self.todo.write_text(self.todo.read_text(encoding="utf-8") + "\nNew context\n",
                                         encoding="utf-8")
                elif kind == "issue":
                    self.remote(issues=[self.issue()])
                else:
                    self.remote(pulls=[{"number": 2, "html_url": "https://github.com/acme/project/pull/2",
                                        "title": "New PR", "body": "new", "state": "open",
                                        "head": {"ref": self.git("branch", "--show-current")}}])
                failure = self.publish(preview, ok=False)
                self.assertEqual(failure["code"], "stale-preview")
                self.assertEqual(self.remote()["creates"], 0)

    def test_create_loss_recovers_exact_marker_once_and_then_is_idempotent(self):
        self.remote(mode="lost")
        self.publish(ok=False)
        self.assertEqual(self.metadata()["issuePublication"]["state"], "attempted")
        self.assertNotIn("issueURL", self.metadata())
        self.remote(mode="")
        result = self.publish()
        self.assertTrue(result["recovered"])
        self.assertEqual(self.remote()["creates"], 1)
        again = self.publish()
        self.assertFalse(again["created"])
        self.assertEqual(self.remote()["creates"], 1)

    def test_uncertain_zero_and_multiple_marker_matches_never_create_again(self):
        self.remote(mode="create-before")
        self.publish(ok=False)
        self.remote(mode="")
        self.publish(ok=False)
        self.assertEqual(self.remote()["creates"], 1)
        self.assertNotIn("issueURL", self.metadata())
        marker = "<!-- todo-id: " + self.metadata()["todoId"] + " -->"
        self.remote(issues=[self.issue(1, body=marker), self.issue(2, body=marker)])
        self.publish(ok=False)
        self.assertEqual(self.remote()["creates"], 1)
        self.assertNotIn("issueURL", self.metadata())

    def test_create_failure_after_creation_and_unreadable_readback_recover(self):
        for mode in ("create-after", "readback"):
            with self.subTest(mode=mode):
                self.remote(mode=mode, issues=[], creates=0)
                self.patch_metadata(issuePublication={}, issueURL=None, issueNumber=None)
                self.publish(ok=False)
                self.assertEqual(self.metadata()["issuePublication"]["state"], "attempted")
                self.remote(mode="")
                self.assertTrue(self.publish()["recovered"])
                self.assertEqual(self.remote()["creates"], 1)

    def test_readback_title_body_and_snapshot_mismatch_leave_attempted(self):
        for mode in ("bad-title", "bad-body", "mutate"):
            with self.subTest(mode=mode):
                self.remote(mode=mode, issues=[], creates=0)
                self.patch_metadata(issuePublication={}, issueURL=None, issueNumber=None)
                self.publish(ok=False)
                self.assertEqual(self.metadata()["issuePublication"]["state"], "attempted")
                self.assertNotIn("issueURL", {k: v for k, v in self.metadata().items() if v})
                self.assertTrue(self.todo.exists())

    def test_recovery_does_not_accept_changed_reviewed_intent(self):
        self.remote(mode="lost")
        self.publish(ok=False)
        self.remote(mode="")
        self.public.write_text("Different reviewed publication", encoding="utf-8")
        self.publish(ok=False)
        self.assertEqual(self.remote()["creates"], 1)
        self.assertNotIn("issueURL", self.metadata())

    def test_exact_marker_dedup_reuses_verified_intent_or_blocks(self):
        preview = self.preview()
        marker = "<!-- todo-id: " + preview["todoId"] + " -->"
        self.remote(issues=[self.issue(body=marker)])
        result = self.publish()
        self.assertFalse(result["created"])
        self.assertEqual(self.remote()["creates"], 0)

    def test_linked_open_error_and_wrong_repo_status_cannot_complete(self):
        self.publish()
        before = self.todo.read_bytes()
        self.run_verb("todo.complete", self.todo.name, ok=False)
        self.assertEqual(self.todo.read_bytes(), before)
        self.remote(mode="view")
        self.run_verb("todo.complete", self.todo.name, ok=False)
        self.assertEqual(self.todo.read_bytes(), before)
        self.remote(mode="")
        self.patch_metadata(issueURL="https://github.com/other/repo/issues/1")
        before = self.todo.read_bytes()
        self.run_verb("todo.complete", self.todo.name, ok=False)
        self.assertEqual(self.todo.read_bytes(), before)

    def test_recovered_closed_issue_permits_explicit_completion_only(self):
        self.remote(mode="lost")
        self.publish(ok=False)
        self.remote(mode="")
        self.publish()
        data = self.remote()
        data["issues"][0]["state"] = "closed"
        self.save(data)
        result = self.run_verb("todo.complete", self.todo.name)
        self.assertFalse(self.todo.exists())
        self.assertTrue((self.directory / result["completed"]).exists())

    def test_legacy_completion_path_and_collision_safety(self):
        before = self.todo.read_bytes()
        for name in ("../pending/legacy.md", str(self.todo), "x/legacy.md"):
            self.run_verb("todo.complete", name, ok=False)
            self.assertEqual(self.todo.read_bytes(), before)
        completed = self.directory / ".planning/todos/completed"
        completed.mkdir()
        target = completed / self.todo.name
        target.write_text("Unrelated completed record", encoding="utf-8")
        self.run_verb("todo.complete", self.todo.name, ok=False)
        self.assertEqual(target.read_text(encoding="utf-8"), "Unrelated completed record")
        self.assertEqual(self.todo.read_bytes(), before)
        target.unlink()
        self.run_verb("todo.complete", "legacy")
        self.assertEqual(target.read_bytes(), before)

    def test_ambiguous_name_and_symlink_escape_are_refused(self):
        other = self.todo.with_name("legacy-other.md")
        other.write_bytes(self.todo.read_bytes())
        self.run_verb("todo.complete", "legacy", ok=False)
        self.preview()  # exact selection still works
        external = self.directory / "outside.md"
        external.write_text("keep", encoding="utf-8")
        link = self.todo.with_name("escape.md")
        try:
            link.symlink_to(external)
        except OSError:
            self.skipTest("symlink creation unavailable on this host")
        self.run_verb("todo.issue-preview", link.name, ok=False)
        self.run_verb("todo.complete", link.name, ok=False)
        self.assertEqual(external.read_text(encoding="utf-8"), "keep")

    def test_preview_cannot_overwrite_concurrent_local_context(self):
        self.remote(mode="preview-mutate")
        self.preview(ok=False)
        self.assertIn("Concurrent context", self.todo.read_text(encoding="utf-8"))
        self.assertNotIn("issueURL", self.metadata())

    def test_private_todo_is_not_a_separate_public_body_file(self):
        preview = self.preview()
        self.run_verb("todo.issue-publish", self.todo.name, "--preview-token",
                      preview["previewToken"], "--title", "Reviewed",
                      "--body-file", str(self.todo), "--no-match", ok=False)
        self.assertEqual(self.remote()["creates"], 0)

    def test_malformed_origin_and_unresolved_intent_are_handled(self):
        self.git("remote", "set-url", "origin", "https://github.com:bad/acme/project")
        self.preview(ok=False)
        self.patch_metadata(issuePublication={"intentDigest": "unknown"})
        before = self.todo.read_bytes()
        self.run_verb("todo.complete", self.todo.name, ok=False)
        self.assertEqual(self.todo.read_bytes(), before)

    @unittest.skipUnless(os.name == "nt", "Windows junction guard")
    def test_windows_pending_junction_cannot_redirect_local_mutation(self):
        pending = self.todo.parent
        preserved = pending.with_name("preserved")
        pending.rename(preserved)
        outside = self.directory / "outside"
        outside.mkdir()
        other = outside / self.todo.name
        other.write_text("Do not change", encoding="utf-8")
        made = subprocess.run(["cmd", "/c", "mklink", "/J", str(pending), str(outside)],
                              capture_output=True, text=True)
        if made.returncode:
            preserved.rename(pending)
            self.skipTest("junction creation unavailable")
        self.run_verb("todo.complete", self.todo.name, ok=False)
        self.run_verb("todo.issue-preview", self.todo.name, ok=False)
        self.assertEqual(other.read_text(encoding="utf-8"), "Do not change")
        self.assertTrue((preserved / self.todo.name).exists())

    def test_incomplete_selection_options_and_existing_linkage_cannot_create(self):
        self.run_verb("todo.issue-preview", self.todo.name, "another.md", ok=False)
        self.preview("--related-pr", ok=False)
        self.preview()
        self.patch_metadata(issueURL=self.issue()["html_url"])
        self.publish(ok=False)
        self.assertEqual(self.remote()["creates"], 0)

    def test_invalid_private_frontmatter_is_not_echoed_in_failure(self):
        self.todo.write_text("---\nsecret: [PRIVATE TOKEN\n---\nbody\n",
                             encoding="utf-8")
        result = self.preview(ok=False)
        self.assertNotIn("PRIVATE TOKEN", json.dumps(result))

    def test_repeated_concurrent_publish_serializes_and_creates_once(self):
        preview = self.preview()
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self.publish, preview) for _ in range(2)]
            results = [future.result() for future in futures]
        self.assertEqual(sum(result["created"] for result in results), 1)
        self.assertEqual(self.remote()["creates"], 1)


if __name__ == "__main__":
    unittest.main()
