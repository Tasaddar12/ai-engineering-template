"""Standalone issue publication tests with real files and fully offline providers.

Preview state lives in the current runtime's content-bound JSON receipts rather
than private TODO frontmatter. Every inherited scenario retains its behavioral
assertions against that public API and real atomic persistence boundaries.
"""
import copy
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"engineer/bin"))
from lib import core, issues, records, delivery, phase_issues, repository
from lib.core import Args, Failure
from lib.text import split_frontmatter, join_frontmatter

PUBLIC = """## Problem
Blank search fails for signed-in users.
## Expected behavior
An empty result appears.
## Actual behavior
Unknown; this is an offline regression fixture.
## Reproduction
Build: fixture. Environment: disposable test repository.
Entry point: https://example.invalid/search/ . Setup: offline fixture only.
1. Submit an empty query and inspect the displayed result.
## Safe evidence
The regression fixture provides the observation; no production evidence exists.
## Impact
Fixture users cannot clear a search.
## Acceptance
Blank searches show an empty result, verified in the final authorized batch.
## Scope
In: blank searches. Out: ranking.
## Related links
https://example.invalid/requirements/search
"""


class PartialWriter:
    def __init__(self, handle): self.handle = handle
    def __enter__(self): return self
    def __exit__(self, *args): return self.handle.__exit__(*args)
    def __getattr__(self, name): return getattr(self.handle, name)
    def write(self, value):
        self.handle.write(value[:20])
        self.handle.flush()
        raise OSError("injected partial atomic write")


class IssueFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="engineer-issues-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.git("init", "-q", "-b", "topic")
        self.git("config", "user.name", "Issue Fixture")
        self.git("config", "user.email", "issue@example.invalid")
        (self.directory/"source").write_text("fixture")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        self.git("remote", "add", "origin", "https://github.com/acme/project.git")
        self.todo = self.directory/".planning/todos/pending/legacy.md"
        self.todo.parent.mkdir(parents=True)
        self.private_body = "Private customer evidence\n\n## Context\nFull local context.\n"
        self.todo.write_text(join_frontmatter({"title": "Private customer title", "severity": "major", "custom": "retain me"}, self.private_body), encoding="utf-8")
        self.public = self.directory/"reviewed public.md"
        self.public.write_text(PUBLIC, encoding="utf-8")
        self.source = self.todo
        self.title = "Public reviewed title"
        self.variant = "Bug"
        self.family = "todo"
        self.rows, self.pulls, self.calls = [], [], []
        self.creates, self.edits, self.mode = 0, 0, ""
        self.direct_changes = {}
        self.views = []
        environment = patch.dict(os.environ, {"ENGINEER_ROOT": str(self.directory)})
        environment.start()
        self.addCleanup(environment.stop)
        discovery = patch.object(issues, "run", side_effect=self.api)
        discovery.start()
        self.addCleanup(discovery.stop)
        provider = patch.object(delivery, "gh", side_effect=self.gh)
        provider.start()
        self.addCleanup(provider.stop)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.directory, check=True, capture_output=True, text=True).stdout.strip()

    def metadata(self, path=None):
        return split_frontmatter((path or self.source).read_text(encoding="utf-8"))[0]

    def patch_metadata(self, **changes):
        metadata, body = split_frontmatter(self.source.read_text(encoding="utf-8"))
        metadata.update(changes)
        self.source.write_text(join_frontmatter(metadata, body), encoding="utf-8")

    def issue(self, number=1, state="OPEN", title=None, body=None, **changes):
        return dict({"number": number, "url": f"https://github.com/acme/project/issues/{number}", "title": title or self.title, "state": state, "body": PUBLIC if body is None else body, "labels": []}, **changes)

    def api(self, argv, cwd=None, check=True):
        self.calls.append(list(argv))
        self.assertEqual(["gh", "api", "--hostname", "github.com", "--method", "GET"], argv[:6])
        if self.mode == "preview-mutate":
            self.source.write_text(self.source.read_text()+"Concurrent context\n", encoding="utf-8")
        if self.mode in ("lookup", "auth", "disabled", "repo-mismatch") or self.mode == "lost" and self.creates:
            return subprocess.CompletedProcess(argv, 1, "", "PRIVATE PROVIDER LOG")
        if self.mode == "json": return subprocess.CompletedProcess(argv, 0, "{bad", "")
        if self.mode == "pagination": return subprocess.CompletedProcess(argv, 0, json.dumps({"partial": True}), "")
        endpoint = argv[-1]
        self.assertTrue(endpoint.startswith("repos/acme/project/"))
        self.assertIn("state=all", endpoint)
        self.assertIn("per_page=100", endpoint)
        page = int(parse_qs(urlparse(endpoint).query)["page"][0])
        rows = self.pulls if "/pulls?" in endpoint else self.rows
        return subprocess.CompletedProcess(argv, 0, json.dumps(rows[(page-1)*100:page*100]), "")

    def gh(self, args, check=True):
        self.calls.append(list(args))
        if args[:2] == ["issue", "view"]:
            if self.mode == "view" or self.mode == "readback" and self.creates:
                raise Failure("provider-query-failed", "Offline readback unavailable")
            if self.mode == "mutate":
                self.source.write_text(self.source.read_text()+"Changed during readback\n", encoding="utf-8")
            if self.views:
                value = self.views.pop(0)
                if value is None: raise Failure("provider-query-failed", "Offline readback unavailable")
                return subprocess.CompletedProcess(args, 0, json.dumps(value), "")
            row = next(row for row in self.rows if row["url"] == args[2])
            return subprocess.CompletedProcess(args, 0, json.dumps(dict(row, **self.direct_changes)), "")
        if args[:2] == ["issue", "create"]:
            self.assertTrue(any(item.get("used") == "publishing" for item in self.attempts()))
            self.creates += 1
            if self.mode == "create-before": raise Failure("provider-query-failed", "Uncertain offline outcome")
            row = self.issue(number=max([item["number"] for item in self.rows]+[0])+1, title=args[args.index("--title")+1], body=Path(args[args.index("--body-file")+1]).read_text(encoding="utf-8"))
            if self.mode == "bad-title": row["title"] = "unexpected"
            if self.mode == "bad-body": row["body"] = "unexpected"
            self.rows.append(row)
            if self.mode in ("lost", "create-after"): raise Failure("provider-query-failed", "Uncertain offline outcome")
            return subprocess.CompletedProcess(args, 0, row["url"], "")
        if args[:2] == ["issue", "edit"]:
            self.edits += 1
            row = next(row for row in self.rows if row["url"] == args[2])
            row.update(title=args[args.index("--title")+1], body=Path(args[args.index("--body-file")+1]).read_text(encoding="utf-8"))
            return subprocess.CompletedProcess(args, 0, "", "")
        if args[:2] == ["pr", "view"]:
            if not getattr(self, "pull", None): raise Failure("pr-not-found", "Offline fixture has no PR")
            return subprocess.CompletedProcess(args, 0, json.dumps(self.pull), "")
        self.fail("Unexpected offline provider call: "+repr(args))

    def arguments(self, decision=None, token=None, title=None, body_file=None, variant=None):
        pos = [self.todo.name] if self.family == "todo" else ["1", self.source.name, "P1"]
        options = ["--title", self.title if title is None else title, "--body-file", str(body_file or self.public), "--variant", self.variant if variant is None else variant]
        options += list(decision if decision is not None else ["--no-match"])
        if token: options += ["--preview-token", token]
        return Args(pos+options)

    def preview(self, decision=None, **options):
        return issues.publication(self.arguments(decision, **options), "preview", self.family)

    def publish(self, preview=None, decision=None, action="publish", **options):
        preview = preview or self.preview(decision, **options)
        return issues.publication(self.arguments(decision, token=preview["preview_token"], **options), action, self.family)

    def attempts(self):
        return [json.loads(path.read_text()) for path in (self.directory/".planning/issue-previews").glob("*.json")]

    def fails(self, call, code=None):
        with self.assertRaises((Failure, OSError)) as caught: call()
        if code: self.assertEqual(code, caught.exception.code)
        self.assertNotIn("PRIVATE PROVIDER LOG", str(caught.exception))
        return caught.exception

    def complete(self, name=None):
        return records.todo(Args([name or self.todo.name]), "complete")

    def make_alias(self, alias, physical):
        if os.name == "nt":
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(physical)], capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
        else: alias.symlink_to(physical, target_is_directory=True)

    def remove_alias(self, alias):
        if os.name == "nt": alias.rmdir()
        else: alias.unlink()


class TodoIssues(IssueFixture):
    def test_failed_link_write_preserves_attempt_and_recovers_once(self):
        original = self.todo.read_bytes()
        preview = self.preview()
        original_replace = os.replace
        def fail_replace(source, target):
            if Path(target).resolve() == self.todo: raise OSError("injected atomic source save")
            return original_replace(source, target)
        with patch.object(core.os, "replace", side_effect=fail_replace): self.fails(lambda: self.publish(preview))
        self.assertEqual(original, self.todo.read_bytes())
        self.assertTrue(issues.unresolved_attempt(self.todo))
        self.assertEqual(1, self.creates)
        self.assertTrue(self.publish(preview)["reused"])
        self.assertEqual(1, self.creates)
        self.assertEqual("retain me", self.metadata()["custom"])

    def test_failed_prepared_or_attempted_save_prevents_create(self):
        for stage in ("prepared", "attempted"):
            preview = self.preview() if stage == "attempted" else None
            original_replace = os.replace
            def fail_replace(source, target):
                if Path(target).parent.name == "issue-previews": raise OSError("injected atomic preview save")
                return original_replace(source, target)
            if not preview:
                for path in (self.directory/".planning/issue-previews").glob("*.json"): path.unlink()
            before = self.todo.read_bytes()
            with patch.object(core.os, "replace", side_effect=fail_replace):
                self.fails(lambda: self.publish(preview) if preview else self.preview())
            self.assertEqual(0, self.creates)
            self.assertEqual(before, self.todo.read_bytes())

    def test_partial_writes_preserve_prepared_attempted_and_linked_evidence(self):
        for stage in ("prepared", "attempted", "linked"):
            case = TodoIssues()
            case.setUp()
            try:
                preview = None if stage == "prepared" else case.preview()
                before = case.todo.read_bytes()
                fdopen, json_write, source_write = os.fdopen, issues.write_json, issues.write
                def partial(*args, **kwargs): return PartialWriter(fdopen(*args, **kwargs))
                def failing_json(path, value):
                    target_stage = "attempted" if value.get("used") else "prepared"
                    if stage == target_stage:
                        with patch.object(core.os, "fdopen", side_effect=partial): return json_write(path, value)
                    return json_write(path, value)
                def failing_source(path, content):
                    with patch.object(core.os, "fdopen", side_effect=partial): return source_write(path, content)
                with patch.object(issues, "write_json", side_effect=failing_json), patch.object(issues, "write", side_effect=failing_source if stage == "linked" else source_write):
                    case.fails(lambda: case.publish(preview) if preview else case.preview())
                self.assertEqual(before, case.todo.read_bytes())
                self.assertEqual(1 if stage == "linked" else 0, case.creates)
                self.assertEqual([case.todo], list(case.todo.parent.iterdir()))
                if stage == "linked":
                    self.assertTrue(issues.unresolved_attempt(case.todo))
                    self.assertTrue(case.publish(preview)["reused"])
                    self.assertEqual(1, case.creates)
            finally: case.doCleanups()

    def test_direct_duplicate_changes_refuse_stale_review(self):
        for changes in ({"title": "Changed"}, {"body": PUBLIC+"Changed"}, {"state": "CLOSED"}):
            self.rows = [self.issue()]
            self.direct_changes = {}
            decision = ["--existing-issue", "1"]
            preview = self.preview(decision)
            self.direct_changes = changes
            self.fails(lambda: self.publish(preview, decision), "stale-issue-preview")
            self.assertNotIn("issue_url", self.metadata())
        self.assertEqual(0, self.creates)

    def test_attempted_without_url_cannot_complete_or_lose_context(self):
        preview = self.preview()
        self.mode = "create-before"
        self.fails(lambda: self.publish(preview))
        before = self.todo.read_bytes()
        self.assertTrue(issues.unresolved_attempt(self.todo))
        self.fails(self.complete)
        self.assertEqual(before, self.todo.read_bytes())

    def test_preview_stable_identity_and_private_complete_context(self):
        before = self.todo.read_bytes()
        first, second = self.preview(), self.preview()
        self.assertEqual(first["preview_token"], second["preview_token"])
        self.assertEqual(before, self.todo.read_bytes())
        self.assertNotIn("Private", first["body"])
        self.assertIn("engineer-issue:", first["body"])
        self.assertEqual("retain me", self.metadata()["custom"])

    def test_new_todo_identity_and_legacy_listing_remain_usable(self):
        created = records.todo(Args(["Another fixture", "--problem", "Observed fixture limitation"]), "add")
        listed = records.todo(Args([]), "list")
        self.assertEqual(2, listed["count"])
        self.assertTrue(Path(created["path"]).is_file())
        preview = self.preview()
        self.assertEqual(str(self.todo), preview["source"])
        self.assertIn("engineer-issue:", preview["body"])

    def test_create_only_reviewed_public_content_and_link_pending(self):
        result = self.publish()
        self.assertFalse(result["reused"])
        self.assertEqual(1, self.creates)
        self.assertNotIn("Private", self.rows[0]["title"]+self.rows[0]["body"])
        self.assertTrue(self.todo.is_file())
        self.assertEqual(result["url"], self.metadata()["issue_url"])
        self.assertTrue(self.todo.read_text().endswith(self.private_body))

    def test_structural_failure_precedes_create_and_attempt_persistence(self):
        self.public.write_text(PUBLIC.replace("## Actual behavior", "## Unexpected heading"))
        self.fails(self.preview, "issue-format")
        self.assertEqual([], self.attempts())
        self.assertEqual(0, self.creates)

    def test_missing_or_empty_public_title_and_decision_refuse_before_create(self):
        self.fails(lambda: self.preview(title=""), "reviewed-public-content-required")
        args = Args([self.todo.name, "--body-file", str(self.public), "--variant", "Bug", "--no-match"])
        self.fails(lambda: issues.publication(args, "preview"), "reviewed-public-content-required")
        preview = self.preview(decision=[])
        self.fails(lambda: self.publish(preview, decision=[]), "issue-disposition-required")
        self.assertEqual(0, self.creates)

    def test_html_literal_and_mixed_indent_precede_provider_and_attempt(self):
        for body in ("<div>\n"+PUBLIC+"\n</div>", "```markdown\n"+PUBLIC+"```", "\n".join("    "+line for line in PUBLIC.splitlines())):
            self.public.write_text(body)
            self.fails(self.preview, "issue-format")
        self.assertEqual([], self.calls)
        self.assertEqual([], self.attempts())

    def test_missing_or_malformed_schema_precedes_remote_mutation(self):
        template = self.directory/"empty namespace"
        (template/"engineer/templates").mkdir(parents=True)
        with patch.object(issues.models, "NAMESPACE", template): self.fails(self.preview, "issue-schema")
        (template/"engineer/templates/issue.md").write_text("## File Template\n### Bug\n```markdown\n## Problem\n```\n")
        with patch.object(issues.models, "NAMESPACE", template): self.fails(self.preview, "issue-schema")
        self.assertEqual([], self.calls)

    def test_semantic_reuse_open_and_closed_does_not_edit_or_complete(self):
        for state in ("OPEN", "CLOSED"):
            self.todo.write_text(join_frontmatter({"title": "Private", "custom": "retain me"}, self.private_body))
            self.rows = [self.issue(state=state)]
            decision = ["--existing-issue", "1"]
            result = self.publish(decision=decision)
            self.assertTrue(result["reused"])
            self.assertEqual(state == "CLOSED", result["requires_reconciliation"])
            self.assertTrue(self.todo.exists())
        self.assertEqual((0, 0), (self.creates, self.edits))

    def test_preview_includes_closed_candidates_and_complete_pagination(self):
        self.rows = [self.issue(number=n, title=f"Unrelated {n}") for n in range(1, 101)]+[self.issue(number=101, state="CLOSED")]
        preview = self.preview(["--existing-issue", "101"])
        self.assertEqual(101, preview["candidates"][0]["number"])
        self.assertTrue(any("page=2" in call[-1] for call in self.calls if call[:2] == ["gh", "api"]))
        self.assertEqual(0, self.creates)

    def test_pr_objects_excluded_and_related_context_selected(self):
        self.rows = [dict(self.issue(), pull_request={"url": "https://api.github.com/repos/acme/project/pulls/1"})]
        self.pulls = [dict(self.issue(), url="https://github.com/acme/project/pull/1")]
        preview = self.preview()
        self.assertEqual([], preview["candidates"])
        self.assertEqual("create", preview["disposition"])
        self.assertTrue(any("/pulls?" in call[-1] for call in self.calls if call[:2] == ["gh", "api"]))

    def test_bad_repository_auth_lookup_json_and_pagination_block(self):
        for mode in ("repo-mismatch", "auth", "disabled", "lookup", "json", "pagination"):
            self.mode = mode
            self.fails(self.preview)
            self.assertEqual(0, self.creates)
            self.assertEqual([], self.attempts())

    def test_wrong_origin_or_supplied_urls_cannot_redirect(self):
        for url in ("https://github.com/other/project/issues/1", "https://github.com/acme/project/pull/1", "https://github.com/acme/project/issues/1?redirect=elsewhere"):
            self.fails(lambda: self.preview(["--existing-issue", url]), "provider-repository-mismatch")
        self.assertEqual(0, self.creates)

    def test_stale_local_candidate_and_pr_context_invalidate_preview(self):
        preview = self.preview()
        self.pulls = [dict(self.issue(), url="https://github.com/acme/project/pull/1")]
        self.fails(lambda: self.publish(preview), "stale-issue-preview")
        preview = self.preview()
        self.todo.write_text(self.todo.read_text()+"Changed context\n")
        self.fails(lambda: self.publish(preview), "stale-issue-preview")
        self.assertEqual(0, self.creates)

    def test_create_loss_recovers_exact_marker_once_and_then_is_idempotent(self):
        preview = self.preview()
        self.mode = "lost"
        self.fails(lambda: self.publish(preview))
        self.assertTrue(issues.unresolved_attempt(self.todo))
        self.mode = ""
        self.assertTrue(self.publish(preview)["reused"])
        self.fails(lambda: self.publish(preview))
        self.assertEqual(1, self.creates)

    def test_uncertain_zero_and_multiple_marker_matches_never_create_again(self):
        preview = self.preview()
        self.mode = "create-before"
        self.fails(lambda: self.publish(preview))
        self.mode = ""
        self.fails(lambda: self.publish(preview), "issue-publication-uncertain")
        marker_body = preview["body"]
        self.rows = [self.issue(body=marker_body), self.issue(number=2, body=marker_body)]
        self.fails(lambda: self.publish(preview), "issue-identity-ambiguous")
        self.assertEqual(1, self.creates)

    def test_create_failure_after_creation_and_unreadable_readback_recover(self):
        preview = self.preview()
        self.mode = "readback"
        self.fails(lambda: self.publish(preview))
        self.mode = ""
        self.assertTrue(self.publish(preview)["reused"])
        self.assertEqual(1, self.creates)
        self.assertFalse(issues.unresolved_attempt(self.todo))
        case = TodoIssues()
        case.setUp()
        try:
            preview = case.preview()
            case.mode = "create-after"
            self.assertTrue(case.publish(preview)["reused"])
            self.assertEqual(1, case.creates)
            self.assertEqual(1, len(case.rows))
        finally: case.doCleanups()

    def test_readback_title_body_and_snapshot_mismatch_leave_attempted(self):
        for mode in ("bad-title", "bad-body", "mutate"):
            case = TodoIssues()
            case.setUp()
            try:
                preview = case.preview()
                case.mode = mode
                case.fails(lambda: case.publish(preview))
                self.assertTrue(case.todo.exists())
                self.assertNotIn("issue_url", case.metadata())
                self.assertTrue(issues.unresolved_attempt(case.todo))
                self.assertEqual(1, case.creates)
            finally: case.doCleanups()

    def test_recovery_does_not_accept_changed_reviewed_intent(self):
        preview = self.preview()
        self.mode = "lost"
        self.fails(lambda: self.publish(preview))
        self.mode = ""
        self.public.write_text(PUBLIC.replace("Blank search fails", "Different problem"))
        self.fails(lambda: self.publish(preview), "stale-issue-preview")
        self.assertEqual(1, self.creates)
        self.assertNotIn("issue_url", self.metadata())

    def test_exact_marker_dedup_reuses_verified_intent_or_blocks(self):
        preview = self.preview()
        self.rows = [self.issue(body=preview["body"])]
        result = self.publish(decision=["--existing-issue", "1"])
        self.assertTrue(result["reused"])
        self.assertEqual(0, self.creates)
        self.assertEqual(0, self.edits)

    def test_linked_open_error_and_wrong_repo_status_cannot_complete(self):
        self.publish()
        before = self.todo.read_bytes()
        self.fails(self.complete)
        self.mode = "view"
        self.fails(self.complete)
        self.mode = ""
        self.patch_metadata(issue_url="https://github.com/other/repo/issues/1")
        before = self.todo.read_bytes()
        self.fails(self.complete)
        self.assertEqual(before, self.todo.read_bytes())

    def test_recovered_closed_issue_permits_explicit_completion_only(self):
        preview = self.preview()
        self.mode = "readback"
        self.fails(lambda: self.publish(preview))
        self.mode = ""
        self.publish(preview)
        self.rows[0]["state"] = "CLOSED"
        self.assertTrue(self.todo.exists())
        result = self.complete()
        self.assertFalse(self.todo.exists())
        self.assertTrue(Path(result["path"]).is_file())

    def test_legacy_completion_path_and_collision_safety(self):
        before = self.todo.read_bytes()
        for name in ("../pending/legacy.md", "x/legacy.md"):
            self.fails(lambda: self.complete(name))
            self.assertEqual(before, self.todo.read_bytes())
        target = self.directory/".planning/todos/completed/legacy.md"
        target.parent.mkdir(parents=True)
        target.write_text("Unrelated record")
        self.fails(self.complete)
        self.assertEqual("Unrelated record", target.read_text())
        self.assertEqual(before, self.todo.read_bytes())
        target.unlink()
        self.complete()
        self.assertEqual(before, target.read_bytes())

    def test_ambiguous_name_and_symlink_escape_are_refused(self):
        self.todo.with_name("legacy-other.md").write_bytes(self.todo.read_bytes())
        self.fails(lambda: self.complete("legacy"))
        self.preview()
        alias = self.todo.parent/"alias"
        external = self.directory/"outside"
        external.mkdir()
        (external/"valuable.md").write_text("keep")
        self.make_alias(alias, external)
        try:
            self.fails(lambda: issues.todo_path(alias/"valuable.md"), "aliased-issue-source")
            self.fails(lambda: self.complete(str(alias/"valuable.md")))
            self.assertEqual("keep", (external/"valuable.md").read_text())
        finally: self.remove_alias(alias)

    def test_preview_cannot_overwrite_concurrent_local_context(self):
        self.mode = "preview-mutate"
        self.fails(self.preview, "issue-source-drift")
        self.assertIn("Concurrent context", self.todo.read_text())
        self.assertNotIn("issue_url", self.metadata())
        self.assertEqual([], self.attempts())

    def test_private_todo_is_not_a_separate_public_body_file(self):
        self.fails(lambda: self.preview(body_file=self.todo), "private-source-body-refused")
        self.assertEqual([], self.calls)
        self.assertEqual(0, self.creates)

    def test_malformed_origin_and_unresolved_intent_are_handled(self):
        self.git("remote", "set-url", "origin", "https://github.com:bad/acme/project")
        self.fails(self.preview, "unsupported-origin")
        self.patch_metadata(issuePublication={"intentDigest": "unknown"})
        before = self.todo.read_bytes()
        self.fails(self.complete)
        self.assertEqual(before, self.todo.read_bytes())

    def test_windows_pending_junction_cannot_redirect_local_mutation(self):
        pending = self.todo.parent
        preserved = pending.with_name("preserved")
        pending.rename(preserved)
        outside = self.directory/"outside"
        outside.mkdir()
        other = outside/self.todo.name
        other.write_text("Do not change")
        self.make_alias(pending, outside)
        try:
            self.fails(self.preview, "aliased-issue-source")
            self.fails(self.complete)
            self.assertEqual("Do not change", other.read_text())
        finally:
            self.remove_alias(pending)
            preserved.rename(pending)

    def test_incomplete_selection_options_and_existing_linkage_cannot_create(self):
        self.fails(lambda: self.preview(["--no-match", "--existing-issue", "1"]), "issue-disposition-conflict")
        self.publish()
        self.fails(lambda: self.publish(decision=["--existing-issue", "1"]), "issue-already-linked")
        self.assertEqual(1, self.creates)

    def test_invalid_private_frontmatter_is_not_echoed_in_failure(self):
        self.todo.write_text("---\nprivate: [PRIVATE CUSTOMER DETAIL\n---\ncontext")
        failure = self.fails(self.preview)
        self.assertNotIn("PRIVATE CUSTOMER DETAIL", str(failure))
        self.assertEqual(0, self.creates)

    def test_repeated_concurrent_publish_serializes_and_creates_once(self):
        preview = self.preview()
        def publish():
            try: return self.publish(preview)
            except Failure as exc: return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(lambda _: publish(), range(2)))
        self.assertEqual(1, self.creates)
        self.assertEqual(1, len(self.rows))
        self.assertTrue(any(isinstance(result, dict) and result["published"] for result in results))
        self.assertEqual(self.rows[0]["url"], self.metadata()["issue_url"])


if __name__ == "__main__":
    unittest.main()
