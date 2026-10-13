"""Offline phase declaration and publication boundary tests."""
import json
import unittest
from pathlib import Path
import yaml
import test_todo_issues as fixtures

class PhaseIssues(unittest.TestCase):
    setUp = fixtures.TodoIssues.setUp
    git = fixtures.TodoIssues.git
    save = fixtures.TodoIssues.save
    remote = fixtures.TodoIssues.remote
    run_verb = fixtures.TodoIssues.run_verb
    issue = fixtures.TodoIssues.issue

    def phase(self, entries=None, declaration=True, status="complete"):
        directory = self.directory / ".planning/phases/01-fixture"
        directory.mkdir(parents=True, exist_ok=True)
        self.record = directory / "01-01-SUMMARY.md"
        self.name = self.record.relative_to(self.directory).as_posix()
        (self.directory / ".planning/ROADMAP.md").write_text("# Roadmap\n\n## Phases\n\n- [ ] **Phase 1: Fixture** - Test\n\n## Phase Details\n\n### Phase 1: Fixture\n**Goal**: Test\n**Plans**: 1 plan\n\nPlans:\n- [ ] 01-01: Test\n", encoding="utf-8")
        fake = fixtures.FAKE_GH.replace('metadata = yaml.safe_load(todo.read_text(encoding="utf-8").split("---", 2)[1])', 'metadata = yaml.safe_load(todo.read_text(encoding="utf-8").split("---", 2)[1])["issue_refs"][0]')
        fake = fake.replace('else:\n    raise AssertionError("unexpected provider call " + repr(args))', """elif args[:2] == ["pr", "view"]:
    if data.get("pr"):
        out = json.dumps(data["pr"])
    else:
        code = 1
elif args[:2] in (["pr", "edit"], ["pr", "create"]):
    if args[1] == "create":
        data["pr"] = {"number": 5, "url": "https://github.com/acme/project/pull/5", "state": "OPEN", "headRefName": args[args.index("--head")+1], "isDraft": "--draft" in args}
    for option, field in (("--base", "baseRefName"), ("--title", "title"), ("--body", "body")):
        if option in args:
            data["pr"][field] = args[args.index(option)+1]
    if "--body-file" in args:
        data["pr"]["body"] = Path(args[args.index("--body-file")+1]).read_text(encoding="utf-8")
    data["pr_edits"] = data.get("pr_edits", 0) + 1
elif args[:2] == ["issue", "edit"]:
    issue = next(i for i in data["issues"] if i["html_url"] == args[2])
    issue.update(title=args[args.index("--title")+1], body=Path(args[args.index("--body-file")+1]).read_text(encoding="utf-8"))
    data["edits"] = data.get("edits", 0) + 1
else:
    raise AssertionError("unexpected provider call " + repr(args))""")
        self.fake.write_text(fake, encoding="utf-8")
        self.remote(todo=str(self.record))
        self.write_record(entries, declaration, status)

    def write_record(self, entries=None, declaration=True, status="complete"):
        metadata = {"status": status}
        if declaration:
            metadata["issue_refs"] = entries if entries is not None else []
        self.record.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\nPrivate phase evidence\n", encoding="utf-8")

    def entry(self, **changes):
        return dict({"id": "P1", "summary": "Private problem", "variant": "Bug", "state": "unresolved", "relationship": "followup"}, **changes)

    def metadata(self):
        return yaml.safe_load(self.record.read_text(encoding="utf-8").split("---", 2)[1])

    def preview(self, ok=True, name=None):
        return self.run_verb("phase.issue-preview", "1", name or self.name, "P1", ok=ok)

    def publish(self, preview=None, decision=None, variant="Bug", ok=True, body_file=None):
        preview = preview or self.preview()
        return self.run_verb("phase.issue-publish", "1", self.name, "P1",
            "--preview-token", preview["previewToken"], "--title", "Public reviewed title",
            "--body-file", str(body_file or self.public), "--variant", variant,
            *(decision or ["--no-match"]), ok=ok)

    def test_publish_shared_engine_and_handoff_keeps_private_content(self):
        self.phase([self.entry()])
        result = self.publish()
        self.assertTrue(result["created"])
        self.assertEqual(self.metadata()["issue_refs"][0]["variant"], "Bug")
        self.assertNotIn("Private", self.remote()["issues"][0]["body"])
        self.assertTrue(self.run_verb("phase.handoff", "1")["ready"])

    def test_reuse_open_and_closed_preserves_variant(self):
        for state in ("open", "closed"):
            with self.subTest(state=state):
                self.phase([self.entry()])
                self.remote(issues=[self.issue(state=state, body=self.public.read_text(encoding="utf-8"))], creates=0)
                result = self.publish(decision=["--existing-issue", "https://github.com/acme/project/issues/1"])
                self.assertFalse(result["created"])
                self.assertEqual(self.remote()["creates"], 0)

    def test_malformed_reused_kind_cannot_link(self):
        self.phase([self.entry()])
        self.remote(issues=[self.issue(body="## Human acceptance\nStatus: PENDING HUMAN acceptance")])
        result = self.publish(decision=["--existing-issue", "https://github.com/acme/project/issues/1"], ok=False)
        self.assertEqual(result["code"], "issue-format")
        self.assertNotIn("issueURL", self.metadata()["issue_refs"][0])

    def test_uncertain_create_records_blocked_then_recovers_without_duplicate(self):
        self.phase([self.entry()])
        self.remote(mode="lost")
        result = self.publish()
        self.assertEqual(result["state"], "blocked-publication")
        self.assertFalse(self.run_verb("phase.handoff", "1")["ready"])
        self.assertEqual(self.metadata()["issue_refs"][0]["issuePublication"]["state"], "attempted")
        self.remote(mode="")
        recovered = self.publish()
        self.assertTrue(recovered["recovered"])
        self.assertEqual(self.remote()["creates"], 1)

    def test_uncertain_zero_matches_never_retry_creation(self):
        self.phase([self.entry()])
        self.remote(mode="create-before")
        self.publish()
        self.remote(mode="")
        self.assertEqual(self.publish(ok=False)["code"], "issue-unresolved")
        self.assertEqual(self.remote()["creates"], 1)

    def test_private_source_and_invalid_shape_precede_remote_mutation(self):
        self.phase([self.entry()])
        preview = self.preview()
        self.assertEqual(self.publish(preview, body_file=self.record, ok=False)["code"], "issue-review")
        self.public.write_text("Private invalid body", encoding="utf-8")
        self.assertEqual(self.publish(preview, ok=False)["code"], "issue-format")
        self.assertEqual(self.remote()["creates"], 0)

    def test_wrong_variant_cannot_reclassify_problem(self):
        self.phase([self.entry()])
        self.assertEqual(self.publish(variant="UAT", ok=False)["code"], "issue-variant")
        self.assertEqual(self.remote()["creates"], 0)

    def test_stale_record_refuses_create(self):
        self.phase([self.entry()])
        preview = self.preview()
        self.record.write_text(self.record.read_text(encoding="utf-8") + "Changed private evidence\n", encoding="utf-8")
        self.assertEqual(self.publish(preview, ok=False)["code"], "stale-preview")
        self.assertEqual(self.remote()["creates"], 0)

    def test_changed_record_during_preview_preserves_concurrent_evidence(self):
        self.phase([self.entry()])
        self.remote(mode="preview-mutate")
        self.assertEqual(self.preview(ok=False)["code"], "stale-preview")
        self.assertIn("Concurrent context", self.record.read_text(encoding="utf-8"))

    def test_traversal_wrong_phase_and_symlink_are_denied(self):
        self.phase([self.entry()])
        for name in ("../outside.md", ".planning/phases/02-other/02-01-SUMMARY.md"):
            self.assertEqual(self.preview(name=name, ok=False)["code"], "path-escape")
        alias = self.record.parent / "01-02-SUMMARY.md"
        try:
            alias.symlink_to(self.record)
        except OSError:
            return
        self.assertEqual(self.preview(name=alias.name, ok=False)["code"], "path-escape")
        self.assertEqual(self.remote()["creates"], 0)

    def test_malformed_duplicate_and_untruthful_dispositions_fail(self):
        for refs in ("wrong", [self.entry(), self.entry()], [self.entry(state="resolved")],
                     [self.entry(state="pending-human", relationship="resolving")], [self.entry(state="blocked-publication")]):
            with self.subTest(refs=refs):
                self.phase(refs)
                self.run_verb("phase.handoff", "1", ok=False)

    def test_canonical_identity_rejects_pr_wrong_origin_and_number(self):
        for changes in ({"issueURL": "https://github.com/acme/project/pull/1"},
                        {"issueURL": "https://github.com/other/project/issues/1"},
                        {"issueNumber": 2}, {"issueRepo": "github.com/other/project"}):
            self.phase([self.entry(**dict({"issueRepo": "github.com/acme/project",
                "issueURL": "https://github.com/acme/project/issues/1", "issueNumber": 1}, **changes))])
            self.run_verb("phase.handoff", "1", ok=False)

    def test_type_preserving_update_requires_fresh_review_and_readback(self):
        self.phase([self.entry()])
        self.publish()
        preview = self.preview()
        self.public.write_text(self.public.read_text(encoding="utf-8").replace("An empty result appears.", "A reviewed empty result appears."), encoding="utf-8")
        result = self.run_verb("phase.issue-update", "1", self.name, "P1", "--preview-token", preview["previewToken"],
            "--title", "Updated public title", "--body-file", str(self.public), "--variant", "Bug")
        self.assertTrue(result["updated"])
        self.assertEqual(self.remote()["edits"], 1)
        self.assertEqual(self.metadata()["issue_refs"][0]["variant"], "Bug")

    def test_attempted_multiple_markers_and_changed_intent_are_rejected(self):
        self.phase([self.entry()])
        self.remote(mode="lost")
        self.publish()
        self.remote(mode="")
        issue = self.remote()["issues"][0]
        duplicate = dict(issue, number=2, html_url="https://github.com/acme/project/issues/2")
        self.remote(issues=[issue, duplicate])
        self.assertEqual(self.publish(ok=False)["code"], "issue-unresolved")
        self.assertEqual(self.remote()["creates"], 1)

    def test_update_cannot_change_kind_or_use_stale_body_readback(self):
        self.phase([self.entry()])
        self.publish()
        preview = self.preview()
        result = self.run_verb("phase.issue-update", "1", self.name, "P1", "--preview-token", preview["previewToken"],
            "--title", "Changed", "--body-file", str(self.public), "--variant", "UAT", ok=False)
        self.assertEqual(result["code"], "issue-variant")
        self.remote(direct_changes={"body": "Unexpected changed body"})
        result = self.run_verb("phase.issue-update", "1", self.name, "P1", "--preview-token", preview["previewToken"],
            "--title", "Changed", "--body-file", str(self.public), "--variant", "Bug", ok=False)
        self.assertEqual(result["code"], "stale-preview")
        self.assertEqual(self.remote().get("edits", 0), 0)

    def test_context_declarations_are_included_but_legacy_context_needs_none(self):
        self.phase()
        context = self.record.parent / "01-CONTEXT.md"
        context.write_text("Legacy planning narrative\n", encoding="utf-8")
        self.assertTrue(self.run_verb("phase.handoff", "1")["ready"])
        context.write_text("---\n" + yaml.safe_dump({"issue_refs": [self.entry()]}) + "---\n", encoding="utf-8")
        self.run_verb("phase.handoff", "1", ok=False)

    def test_private_malformed_yaml_diagnostics_are_sanitized(self):
        self.phase()
        self.record.write_text("---\nissue_refs: [PRIVATE INVALID RECORD\n---\n", encoding="utf-8")
        result = self.run_verb("phase.handoff", "1", ok=False)
        self.assertNotIn("PRIVATE INVALID RECORD", json.dumps(result))

    def session(self, **changes):
        self.branch = self.git("branch", "--show-current")
        entry = dict({"kind": "phase", "label": "1", "branch": self.branch, "worktree": str(self.directory),
            "status": "open", "pr": {"url": "https://github.com/acme/project/pull/5", "number": 5}}, **changes)
        self.sessions = self.directory / ".git/ai-phase/sessions.json"
        self.sessions.parent.mkdir(parents=True, exist_ok=True)
        self.sessions.write_text(json.dumps({"sessions": [entry]}), encoding="utf-8")
        self.remote(pr={"number": 5, "url": "https://github.com/acme/project/pull/5", "state": "OPEN",
            "headRefName": self.branch, "body": "", "isDraft": True, "baseRefName": "main"})

    def test_phase_session_cannot_bypass_handoff_by_omitting_phase(self):
        self.phase(declaration=False)
        self.session()
        self.run_verb("pr.open", self.branch, "--body", "No declarations", ok=False)
        self.assertEqual(self.remote().get("pr_edits", 0), 0)

    def test_followup_closing_keyword_and_body_omitted_retarget_are_blocked(self):
        self.phase([self.entry()])
        self.publish()
        self.session()
        for body in ("Fixes #1", "Closes acme/project#1", "Resolves https://github.com/acme/project/issues/1"):
            self.run_verb("pr.open", self.branch, "--body", body, ok=False)
        data = self.remote(); data["pr"]["body"] = "Fixes #1"; self.save(data)
        self.run_verb("pr.open", self.branch, "--base", "other", ok=False)
        self.assertEqual(self.remote().get("pr_edits", 0), 0)

    def test_canonical_followup_link_delivers_and_explicit_phase_conflict_denies(self):
        self.phase([self.entry()])
        self.publish()
        self.session()
        self.run_verb("pr.open", self.branch, "--body", "Follow-up: https://github.com/acme/project/issues/1")
        self.run_verb("pr.open", self.branch, "--phase", "2", "--body", "Follow-up: https://github.com/acme/project/issues/1", ok=False)
        self.assertEqual(self.remote()["pr_edits"], 1)

    def folded(self, state="open"):
        self.phase()
        self.session()
        context = self.record.parent / "01-CONTEXT.md"
        context.write_text("## Decisions\n\n### Folded Todos\n\n- `legacy.md`: implemented here.\n\n### Reviewed Todos\n\n- `unselected.md`: not folded.\n", encoding="utf-8")
        self.todo.write_text("---\n" + yaml.safe_dump({"issueRepo": "github.com/acme/project", "issueURL": "https://github.com/acme/project/issues/1", "issueNumber": 1, "issuePublication": {"state": "linked"}}) + "---\nPrivate TODO evidence\n", encoding="utf-8")
        data = self.remote(issues=[self.issue(state=state)])
        data["pr"]["state"] = "MERGED"; self.save(data)

    def reconcile(self):
        return self.run_verb("phase.reconcile-todos", "1", "--pr", "https://github.com/acme/project/pull/5", "--todos", "legacy.md")

    def test_reconciliation_waits_for_closed_issue_then_retries_idempotently(self):
        self.folded()
        result = self.reconcile()
        self.assertEqual(result["items"][0]["state"], "pending")
        self.assertTrue(self.todo.exists())
        self.remote(issues=[self.issue(state="closed")])
        self.assertEqual(self.reconcile()["items"][0]["state"], "completed")
        self.assertFalse(self.todo.exists())
        self.assertEqual(self.reconcile()["items"][0]["state"], "already-completed")
        self.assertEqual(self.remote()["creates"], 0)

    def test_open_wrong_head_and_missing_merge_readback_preserve_todo(self):
        self.folded(state="closed")
        original = self.remote()["pr"]
        for pull in (dict(original, state="OPEN"), dict(original, headRefName="another"), None):
            self.remote(pr=pull)
            result = self.reconcile()
            self.assertEqual(result["items"][0]["state"], "pending")
            self.assertTrue(self.todo.exists())

    def test_reviewed_empty_handoff_and_complete(self):
        self.phase()
        self.assertTrue(self.run_verb("phase.handoff", "1")["ready"])
        self.run_verb("phase.complete", "1")

    def test_missing_declaration_blocks_before_roadmap_write(self):
        self.phase(declaration=False)
        roadmap = self.directory / ".planning/ROADMAP.md"
        before = roadmap.read_bytes()
        self.assertEqual(self.run_verb("phase.complete", "1", ok=False)["code"], "phase-issues")
        self.assertEqual(roadmap.read_bytes(), before)

    def test_unlinked_halted_problem_cannot_handoff(self):
        self.phase([self.entry()], status="halted")
        self.assertEqual(self.run_verb("phase.handoff", "1", ok=False)["code"], "phase-issues")

if __name__ == "__main__":
    unittest.main()
