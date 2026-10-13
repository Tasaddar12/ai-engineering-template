"""Real runtime/locks/TODO files with an offline GitLab CLI subprocess."""
import json
import os
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
import test_todo_issues as fixture

HOST = "gitlab.example.test:8443"
PROJECT = "team/sub/project"
URL = "https://" + HOST + "/" + PROJECT

FAKE_GLAB = r'''
import json, os, sys
from pathlib import Path
import yaml
path = Path(os.environ["FAKE_GH_STATE"])
data = json.loads(path.read_text(encoding="utf-8"))
args = sys.argv[1:]
data["calls"].append(args)
assert args[0] == "api"
assert args[args.index("--hostname")+1] == "gitlab.example.test:8443"
assert os.environ["GITLAB_API_HOST"] == "gitlab.example.test:8443"
assert os.environ["GLAB_API_PROTOCOL"] == "https"
assert os.environ["API_PROTOCOL"] == "https"
assert os.environ["GITLAB_SUBFOLDER"] == "/"
assert os.environ["GLAB_ENABLE_CI_AUTOLOGIN"] == "false"
assert "GITLAB_REPO" not in os.environ
endpoint, method = args[1], args[args.index("--method")+1]
assert endpoint.startswith("projects/team%2Fsub%2Fproject")
suffix = endpoint[len("projects/team%2Fsub%2Fproject"):].lstrip("/")
mode = data.get("mode", "")
base = "https://gitlab.example.test:8443/team/sub/project"
out, code = None, 0
if not suffix:
    assert method == "GET"
    out = dict(id=31, path_with_namespace="team/sub/project", web_url=base, issues_enabled=True)
    if mode == "disabled": out["issues_enabled"] = False
    if mode == "repo-mismatch": out["path_with_namespace"] = "other/project"
    if mode == "repo-url": out["web_url"] = "https://other.test/team/sub/project"
    if mode == "auth": code = 1
elif method == "POST":
    assert suffix == "issues"
    metadata = yaml.safe_load(Path(data["todo"]).read_text(encoding="utf-8").split("---", 2)[1])
    assert metadata["issuePublication"]["state"] == "attempted"
    payload = json.loads(Path(args[args.index("--input")+1]).read_text(encoding="utf-8"))
    assert metadata["issuePublication"]["publicTitle"] == payload["title"]
    data["creates"] += 1
    if mode != "create-before":
        number = max([i["iid"] for i in data["issues"]]+[0])+1
        out = dict(iid=number, project_id=31, web_url=base+"/-/issues/"+str(number),
                   title=payload["title"], description=payload["description"], state="opened")
        if mode == "bad-title": out["title"] = "unexpected title"
        if mode == "bad-body": out["description"] = "unexpected body"
        data["issues"].append(out)
        if mode == "mutate":
            todo = Path(data["todo"])
            todo.write_text(todo.read_text(encoding="utf-8")+"\nChanged after creation\n", encoding="utf-8")
    if mode in ("lost", "create-before", "create-after"): code = 1
elif "?" in suffix:
    assert method == "GET" and "state=all" in suffix and "per_page=100" in suffix
    page = int(suffix.rsplit("page=",1)[1])
    records = data["issues"] if suffix.startswith("issues?") else data["pulls"]
    out = records[(page-1)*100:page*100]
    if mode == "pagination-repeat": out = records[:100]
    if mode == "pagination": out = {"items": out}
    if mode == "lookup": code = 1
    if mode == "preview-mutate":
        todo = Path(data["todo"])
        todo.write_text(todo.read_text(encoding="utf-8")+"\nConcurrent context\n", encoding="utf-8")
else:
    assert method == "GET"
    number = int(suffix.rsplit("/",1)[1])
    records = data["issues"] if suffix.startswith("issues/") else data["pulls"]
    matches = [i for i in records if i["iid"] == number]
    if not matches or mode == "view" or (mode == "readback" and data["creates"]): code = 1
    else: out = dict(matches[0], **data.get("direct_changes", {}))
path.write_text(json.dumps(data), encoding="utf-8")
print("{bad json" if mode == "json" else json.dumps(out))
if code: print("PRIVATE PROVIDER LOG MUST NOT LEAK", file=sys.stderr)
sys.exit(code)
'''

DRIVER = fixture.DRIVER.replace('if command and command[0] == "gh":',
                               'if command and command[0] in ("gh", "glab"):')


class GitLabTodoIssues(unittest.TestCase):
    # Reuse local record/runtime harness helpers, never a live provider fixture.
    git = fixture.TodoIssues.git
    save = fixture.TodoIssues.save
    remote = fixture.TodoIssues.remote
    metadata = fixture.TodoIssues.metadata
    patch_metadata = fixture.TodoIssues.patch_metadata
    preview = fixture.TodoIssues.preview
    publish = fixture.TodoIssues.publish
    inject_save_failure = fixture.TodoIssues.inject_save_failure
    clear_save_failure = fixture.TodoIssues.clear_save_failure

    def setUp(self):
        fixture.TodoIssues.setUp(self)
        self.git("remote", "set-url", "origin", "ssh://git@gitlab.example.test:2222/" + PROJECT + ".git")
        config = {"delivery": {"provider": "gitlab", "gitlab_hosts": {
            "gitlab.example.test": "https://" + HOST}}}
        (self.directory / ".planning/config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
        self.fake.write_text(FAKE_GLAB, encoding="utf-8")
        self.environment.update(GITLAB_REPO="hostile/redirect", GITLAB_HOST="hostile.test",
                                GITLAB_API_HOST="hostile.test", GLAB_API_PROTOCOL="http", API_PROTOCOL="http",
                                GITLAB_SUBFOLDER="/evil", GLAB_ENABLE_CI_AUTOLOGIN="true")

    def assert_pending_context(self):
        self.assertEqual(self.metadata()["custom"], "retain me")
        self.assertTrue(self.todo.read_text(encoding="utf-8").endswith(self.body))
        self.assertFalse((self.directory / ".planning/todos/completed").exists())

    def run_verb(self, *args, ok=True):
        result = subprocess.run([sys.executable, "-c", DRIVER, "query", *args], cwd=self.directory,
                                env=self.environment, capture_output=True, text=True, encoding="utf-8")
        self.assertNotIn("Traceback", result.stderr, result.stderr)
        self.assertNotIn("PRIVATE PROVIDER LOG", result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(bool(payload.get("ok")), ok, payload)
        self.assertEqual(result.returncode, 0 if ok else 1)
        if self.environment.get("TODO_SAVE_FAULT"):
            self.assertTrue(Path(self.environment["TODO_FAULT_FIRED"]).is_file())
        return payload

    def issue(self, number=1, state="opened", title="Existing duplicate", body="Relevant evidence"):
        return {"iid": number, "project_id": 31, "web_url": URL + "/-/issues/" + str(number),
                "title": title, "description": body, "state": state}

    def mr(self, number=1, state="opened", branch=None):
        item = self.issue(number, state)
        item.update(web_url=URL + "/-/merge_requests/" + str(number),
                    source_branch=branch or self.git("branch", "--show-current"))
        return item

    def test_preview_selected_private_context_candidates_and_mrs_paginated(self):
        unrelated = self.todo.parent / "other.md"
        unrelated.write_text("---\ntitle: Other\n---\nPrivate unrelated\n", encoding="utf-8")
        before = unrelated.read_bytes()
        self.remote(issues=[self.issue(i, "closed" if i % 2 else "opened") for i in range(1, 202)],
                    pulls=[self.mr(1), self.mr(2, "merged", "other"), self.mr(3, "closed", "elsewhere")])
        preview = self.preview("--related-pr", self.mr(2)["web_url"])
        self.assertEqual(preview["repository"], HOST + "/" + PROJECT)
        self.assertEqual(len(preview["candidates"]), 201)
        self.assertEqual(preview["candidates"][0]["state"], "CLOSED")
        self.assertEqual([x["number"] for x in preview["relatedPRs"]], [1, 2])
        self.assertTrue(preview["relatedPRs"][1]["merged"])
        self.assertIn("Full local context", preview["privateLocal"]["body"])
        self.assertEqual(unrelated.read_bytes(), before)
        self.assertEqual(self.preview("--related-pr", self.mr(2)["web_url"])["previewToken"], preview["previewToken"])

    def test_create_readback_stored_linkage_and_explicit_closed_completion(self):
        result = self.publish()
        self.assertTrue(result["created"])
        self.assertEqual(self.metadata()["issueURL"], URL + "/-/issues/1")
        data = self.remote()
        self.assertEqual(data["creates"], 1)
        self.assertNotIn("Private customer", data["issues"][0]["description"])
        self.assertIn("<!-- todo-id: " + result["todoId"] + " -->", data["issues"][0]["description"])
        self.assertEqual(self.metadata()["issuePublication"]["state"], "linked")
        self.assertEqual(self.run_verb("todo.complete", self.todo.name, ok=False)["code"], "issue-open")
        self.assert_pending_context()
        data["issues"][0]["state"] = "closed"
        self.save(data)
        self.assertFalse(self.publish()["created"])
        self.assertTrue(self.todo.exists())
        self.run_verb("todo.complete", self.todo.name)
        self.assertFalse(self.todo.exists())
        completed = self.directory / ".planning/todos/completed" / self.todo.name
        self.assertEqual(yaml.safe_load(completed.read_text(encoding="utf-8").split("---", 2)[1])["issueNumber"], 1)
        self.assertEqual(self.remote()["creates"], 1)

    def test_reuse_open_or_closed_without_mutating_issue(self):
        original = self.todo.read_bytes()
        for state in ("opened", "closed"):
            self.todo.write_bytes(original)
            item = self.issue(state=state)
            self.remote(issues=[item])
            result = self.publish(self.preview(), "--existing-issue", item["web_url"])
            self.assertFalse(result["created"])
            self.assertTrue(self.todo.exists())
            self.assertEqual(self.remote()["issues"], [item])
            self.assertEqual(self.remote()["creates"], 0)

    def test_uncertain_create_and_readback_recover_exact_intent_once(self):
        original = self.todo.read_bytes()
        for mode in ("lost", "create-after", "readback"):
            self.todo.write_bytes(original)
            self.remote(mode=mode, issues=[], creates=0)
            self.publish(ok=False)
            self.assertEqual(self.metadata()["issuePublication"]["state"], "attempted")
            self.assert_pending_context()
            self.remote(mode="")
            recovered = self.publish(self.preview())
            self.assertTrue(recovered["recovered"])
            self.assertFalse(recovered["created"])
            self.assertFalse(self.publish()["created"])
            self.assertEqual(self.remote()["creates"], 1)

    def test_uncertain_zero_multiple_or_changed_intent_never_retries(self):
        self.remote(mode="create-before")
        self.publish(ok=False)
        self.remote(mode="")
        self.assertEqual(self.publish(self.preview(), ok=False)["code"], "issue-unresolved")
        self.assertEqual(self.remote()["creates"], 1)
        marker = "<!-- todo-id: " + self.metadata()["todoId"] + " -->"
        self.remote(issues=[self.issue(1, body=marker), self.issue(2, body=marker)])
        self.publish(self.preview(), ok=False)
        self.remote(issues=[self.issue(body=marker)])
        self.publish(self.preview(), ok=False)
        self.assertEqual(self.remote()["creates"], 1)
        self.assertEqual(self.run_verb("todo.complete", self.todo.name, ok=False)["code"], "issue-unresolved")

    def test_recovery_rejects_changed_public_intent(self):
        self.remote(mode="lost")
        self.publish(ok=False)
        self.remote(mode="")
        self.publish(self.preview(), title="Different reviewed title", ok=False)
        self.assertEqual(self.remote()["creates"], 1)

    def test_invalid_issue_variant_or_body_precedes_remote_calls(self):
        preview = self.preview()
        calls, before = self.remote()["calls"], self.todo.read_bytes()
        self.public.write_text("Not an issue template", encoding="utf-8")
        self.assertEqual(self.publish(preview, ok=False)["code"], "issue-format")
        self.assertEqual(self.remote()["calls"], calls)
        self.assertEqual(self.todo.read_bytes(), before)
        self.assertEqual(self.remote()["creates"], 0)

    def test_local_candidate_or_mr_changes_invalidate_preview(self):
        original = self.todo.read_bytes()
        for change in ("local", "issue", "mr"):
            self.todo.write_bytes(original)
            self.remote(issues=[self.issue()], pulls=[self.mr()])
            preview = self.preview()
            if change == "local": self.todo.write_text(self.todo.read_text(encoding="utf-8")+"\nNew private context\n", encoding="utf-8")
            elif change == "issue": self.remote(issues=[self.issue(title="Changed")])
            else: self.remote(pulls=[self.mr(state="closed")])
            self.assertEqual(self.publish(preview, ok=False)["code"], "stale-preview")
            self.assertEqual(self.remote()["creates"], 0)

    def test_direct_readback_mismatch_cannot_link(self):
        original = self.todo.read_bytes()
        for changes in ({"title": "Changed"}, {"state": "closed"}, {"project_id": 32},
                        {"web_url": "https://other.test/g/p/-/issues/1"}, {"iid": 2}):
            self.todo.write_bytes(original)
            item = self.issue()
            self.remote(issues=[item], direct_changes={})
            preview = self.preview()
            self.remote(direct_changes=changes)
            before = self.todo.read_bytes()
            self.publish(preview, "--existing-issue", item["web_url"], ok=False)
            self.assertEqual(self.todo.read_bytes(), before)
            self.assertNotIn("issueURL", self.metadata())
            self.assertEqual(self.remote()["creates"], 0)

    def test_provider_project_json_collection_and_item_failures_preserve_pending(self):
        for mode in ("auth", "disabled", "repo-mismatch", "repo-url", "lookup", "json", "pagination"):
            self.remote(mode=mode)
            self.preview(ok=False)
            self.assert_pending_context()
            self.assertEqual(self.remote()["creates"], 0)
        for changes in ({"iid": True}, {"project_id": True}, {"state": "merged"}, {"title": []},
                        {"description": {}}, {"web_url": URL + "/-/merge_requests/1"}):
            self.remote(mode="", issues=[dict(self.issue(), **changes)])
            self.preview(ok=False)
            self.assert_pending_context()

    def test_repeated_or_oversized_pagination_is_refused(self):
        self.remote(mode="pagination-repeat", issues=[self.issue(i) for i in range(1, 102)])
        self.assertEqual(self.preview(ok=False)["code"], "issue-response")
        self.assertEqual(self.remote()["creates"], 0)

    def test_unsafe_related_url_and_origin_fail_without_create(self):
        self.preview("--related-pr", URL.replace(PROJECT, "other/project") + "/-/merge_requests/1", ok=False)
        before_calls = len(self.remote()["calls"])
        self.git("remote", "set-url", "origin", "https://unknown.test/team/project")
        before = self.todo.read_bytes()
        self.preview(ok=False)
        self.assertEqual(len(self.remote()["calls"]), before_calls)
        self.assertEqual(self.todo.read_bytes(), before)

    def test_create_public_readback_mismatch_remains_attempted(self):
        original = self.todo.read_bytes()
        for mode in ("bad-title", "bad-body", "mutate"):
            self.todo.write_bytes(original)
            self.remote(mode=mode, issues=[], creates=0)
            self.publish(ok=False)
            self.assertEqual(self.metadata()["issuePublication"]["state"], "attempted")
            self.assertNotIn("issueURL", self.metadata())
            self.assertEqual(self.remote()["creates"], 1)

    def test_failed_attempt_save_prevents_create_and_failed_link_recovers(self):
        preview = self.preview()
        before = self.inject_save_failure("attempted", "replace")
        self.publish(preview, ok=False)
        self.assertEqual(self.todo.read_bytes(), before.read_bytes())
        self.assertEqual(self.remote()["creates"], 0)
        self.clear_save_failure()
        preview = self.preview()
        self.inject_save_failure("linked", "replace")
        self.publish(preview, ok=False)
        self.assertEqual(self.metadata()["issuePublication"]["state"], "attempted")
        self.clear_save_failure()
        self.assertTrue(self.publish(self.preview())["recovered"])
        self.assertEqual(self.remote()["creates"], 1)

    def test_completion_rechecks_repository_number_state_and_url(self):
        self.publish()
        for changes in ({"state": "opened"}, {"iid": 2}, {"project_id": 32},
                        {"web_url": URL.replace(PROJECT, "other/project") + "/-/issues/1"}):
            self.remote(direct_changes=changes)
            self.run_verb("todo.complete", self.todo.name, ok=False)
            self.assert_pending_context()
        self.remote(direct_changes={}, mode="view")
        self.run_verb("todo.complete", self.todo.name, ok=False)
        self.assert_pending_context()
        self.remote(mode="")
        self.git("remote", "set-url", "origin", "https://github.com/acme/project")
        self.run_verb("todo.complete", self.todo.name, ok=False)
        self.assertTrue(self.todo.exists())
        self.assertEqual(self.remote()["creates"], 1)

    def test_preview_preserves_concurrent_local_context(self):
        self.remote(mode="preview-mutate")
        self.assertEqual(self.preview(ok=False)["code"], "stale-preview")
        self.assertIn("Concurrent context", self.todo.read_text(encoding="utf-8"))
        self.assertNotIn("issuePublication", self.metadata())

    def test_exact_marker_reuse_requires_reviewed_matching_candidate(self):
        preview = self.preview()
        marker = "<!-- todo-id: " + preview["todoId"] + " -->"
        self.remote(issues=[self.issue(body=marker)])
        self.assertFalse(self.publish(self.preview())["created"])
        self.assertEqual(self.remote()["creates"], 0)

    def test_concurrent_repeated_publish_creates_once(self):
        preview = self.preview()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.publish(preview), range(2)))
        self.assertEqual(sum(x["created"] for x in results), 1)
        self.assertEqual(self.remote()["creates"], 1)
        self.assert_pending_context()

    def test_unicode_reviewed_intent_survives_utf8_readback(self):
        self.public.write_text(self.public.read_text(encoding="utf-8") + "\nCafé 日本語\n", encoding="utf-8")
        result = self.publish(title="Café 日本語")
        self.assertTrue(result["created"])
        self.assertEqual(self.remote()["issues"][0]["title"], "Café 日本語")
        self.assertIn("Café 日本語", self.remote()["issues"][0]["description"])


if __name__ == "__main__":
    unittest.main()
