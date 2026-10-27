"""Declared phase findings, public issues and TODO retirement via current APIs."""
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch
import test_todo_issues as fixtures
from lib import core, delivery, issues, phase_issues, sessions, misc, verification
from lib.core import Args, Failure
from lib.text import join_frontmatter
PROVIDER_GH = delivery.gh


class PhaseIssues(fixtures.IssueFixture):
    def phase(self, entries=None, declaration=True, status="complete"):
        directory = self.directory/".planning/phases/01-fixture"
        directory.mkdir(parents=True, exist_ok=True)
        self.source = directory/"01-01-SUMMARY.md"
        self.family = "phase"
        (self.directory/".planning/ROADMAP.md").write_text("# Roadmap\n\n## Phases\n\n## Phase 1: Fixture\n\n**Goal:** Test\n**Plans:** 1 plan\n\nPlans:\n- [ ] 01-01: Test\n\n## Progress\n", encoding="utf-8")
        self.write_record(entries, declaration, status)
        return directory

    def entry(self, **changes):
        return dict({"id": "P1", "summary": "Private problem", "variant": "Bug", "state": "unresolved", "relationship": "followup"}, **changes)

    def write_record(self, entries=None, declaration=True, status="complete"):
        metadata = {"status": status}
        if declaration: metadata["issue_refs"] = [] if entries is None else entries
        self.source.write_text(join_frontmatter(metadata, "Private phase evidence\n"), encoding="utf-8")

    def handoff(self):
        return phase_issues.handoff(Args(["1"]))

    def session(self, **changes):
        self.branch = self.git("branch", "--show-current")
        self.sessions = sessions.store()
        self.sessions.parent.mkdir(parents=True, exist_ok=True)
        entry = dict({"kind": "phase", "label": "1", "branch": self.branch, "worktree": str(self.directory), "status": "open"}, **changes)
        self.sessions.write_text(json.dumps({"sessions": [entry]}))
        self.pull = {"number": 5, "url": "https://github.com/acme/project/pull/5", "state": "OPEN", "headRefName": self.branch, "headRefOid": self.git("rev-parse", "HEAD"), "body": self.pr_body(), "title": "Fixture", "isDraft": True, "baseRefName": "main"}
        self.pr_edits = 0
        self.git("branch", "main")

    def gh(self, args, check=True):
        if args[:2] in (["pr", "edit"], ["pr", "create"]):
            self.calls.append(list(args))
            self.pr_edits += 1
            if args[1] == "create":
                self.pull = {"number": 5, "url": "https://github.com/acme/project/pull/5", "state": "OPEN", "headRefName": self.branch, "headRefOid": self.git("rev-parse", "HEAD"), "isDraft": "--draft" in args}
            for option, field in (("--base", "baseRefName"), ("--title", "title")):
                if option in args: self.pull[field] = args[args.index(option)+1]
            if "--body-file" in args: self.pull["body"] = Path(args[args.index("--body-file")+1]).read_text(encoding="utf-8")
            return subprocess.CompletedProcess(args, 0, "", "")
        if args[:2] == ["pr", "view"] and not getattr(self, "pull", None):
            return subprocess.CompletedProcess(args, 1, "", "no pull requests found")
        if self.mode == "bodyfile-mutate" and args[:2] == ["issue", "view"]:
            self.pr_body_file.write_text("Closes #1", encoding="utf-8")
        return super().gh(args, check=check)

    def pr_body(self, extra=""):
        return "## Goal\nOffline fixture relationship audit.\n## Changes\nPreserve declared finding relationships.\n## Verification\nNot run; pending final batch.\n## Known gaps\nSynthetic provider data is not live assurance.\n## Risks or rollback\nDiscard this temporary repository.\n"+extra+"\n"

    def open(self, extra=None, body_file=None, phase=None, base=None):
        # Commit the exact candidate before publication, as real callers must.
        self.git("add", ".")
        if self.git("status", "--porcelain"):
            self.git("commit", "-qm", "reviewed fixture candidate")
        if self.pull: self.pull["headRefOid"] = self.git("rev-parse", "HEAD")
        values = [self.branch]
        if extra is not None: values += ["--body", self.pr_body(extra)]
        if body_file: values += ["--body-file", str(body_file)]
        if phase: values += ["--phase", phase]
        if base: values += ["--base", base]
        def local(argv, cwd=None, **options):
            if argv[:2] == ["git", "push"]: return subprocess.CompletedProcess(argv, 0, "", "")
            return core.run(argv, cwd, **options)
        with patch.object(delivery, "run", side_effect=local):
            return delivery.command(Args(values), "open")

    def folded(self, state="OPEN", body=None):
        self.phase()
        self.session()
        (self.source.parent/"01-CONTEXT.md").write_text("## Decisions\n\n### Folded Todos\n\n- `legacy.md`: implemented here.\n\n### Reviewed Todos\n\n- `unselected.md`: not folded.\n", encoding="utf-8")
        self.todo.write_text(join_frontmatter({"issue_url": "https://github.com/acme/project/issues/1"}, "Private TODO evidence\n"), encoding="utf-8")
        self.rows = [self.issue(state=state, body=body)]
        self.pull["state"] = "MERGED"

    def reconcile(self, name="legacy.md", url="https://github.com/acme/project/pull/5"):
        return phase_issues.reconcile_todos(Args(["1", "--pr", url, "--todos", name]))

    def uat_body(self, accepted=False):
        # This is explicitly synthetic test evidence, never a real acceptance
        # claim. Production authenticity remains an independent review duty.
        body = issues.variant_template(fixtures.ROOT/"engineer/templates/issue.md", "UAT")
        body = re.sub(r"\[[^\]\n]+\]", "Synthetic offline fixture", body)
        if accepted:
            body = body.replace("Status: PENDING HUMAN acceptance", "Status: ACCEPTED")
            body = re.sub(r"(?m)^- Reviewer:.*$", "- Reviewer: Synthetic fixture reviewer", body)
            body = re.sub(r"(?m)^- Date:.*$", "- Date: 2026-10-13", body)
            body = re.sub(r"(?m)^- Decision:.*$", "- Decision: Synthetic fixture records an accepted decision.", body)
            body = re.sub(r"(?m)^- Evidence:.*$", "- Evidence: fixture://human-response/accepted", body)
            body = re.sub(r"(?m)^(\|\s*\d+\s*\|[^\n]*\|) pending \|", r"\1 PASS fixture evidence |", body)
        return body

    def test_publish_shared_engine_and_handoff_keeps_private_content(self):
        self.phase([self.entry()])
        result = self.publish()
        self.assertFalse(result["reused"])
        self.assertEqual("Bug", self.metadata()["issue_refs"][0]["variant"])
        self.assertNotIn("Private", self.rows[0]["body"])
        self.assertTrue(self.handoff()["ready"])
        self.assertIn("Private phase evidence", self.source.read_text())

    def test_reuse_open_and_closed_preserves_variant(self):
        for state in ("OPEN", "CLOSED"):
            self.phase([self.entry()])
            self.rows = [self.issue(state=state)]
            self.assertTrue(self.publish(decision=["--existing-issue", "1"])["reused"])
            self.assertEqual("Bug", self.metadata()["issue_refs"][0]["variant"])
        self.assertEqual((0, 0), (self.creates, self.edits))

    def test_malformed_reused_kind_cannot_link(self):
        self.phase([self.entry()])
        self.rows = [self.issue(body="## Human acceptance\nStatus: PENDING")]
        self.fails(lambda: self.preview(["--existing-issue", "1"]), "issue-format")
        self.assertNotIn("issue_url", self.metadata()["issue_refs"][0])

    def test_uncertain_create_records_blocked_then_recovers_without_duplicate(self):
        self.phase([self.entry()])
        preview = self.preview()
        self.mode = "lost"
        self.fails(lambda: self.publish(preview))
        self.assertFalse(self.handoff()["ready"])
        self.mode = ""
        self.assertTrue(self.publish(preview)["reused"])
        self.assertEqual(1, self.creates)

    def test_uncertain_zero_matches_never_retry_creation(self):
        self.phase([self.entry()])
        preview = self.preview()
        self.mode = "create-before"
        self.fails(lambda: self.publish(preview))
        self.mode = ""
        self.fails(lambda: self.publish(preview), "issue-publication-uncertain")
        self.assertEqual(1, self.creates)

    def test_private_source_and_invalid_shape_precede_remote_mutation(self):
        self.phase([self.entry()])
        self.fails(lambda: self.preview(body_file=self.source), "private-source-body-refused")
        self.public.write_text("Private invalid body")
        self.fails(self.preview, "issue-format")
        self.assertEqual(0, self.creates)

    def test_wrong_variant_cannot_reclassify_problem(self):
        self.phase([self.entry()])
        self.fails(lambda: self.preview(variant="UAT"), "issue-variant-conflict")
        self.assertEqual(0, self.creates)

    def test_stale_record_refuses_create(self):
        self.phase([self.entry()])
        preview = self.preview()
        self.source.write_text(self.source.read_text()+"Changed evidence\n")
        self.fails(lambda: self.publish(preview), "stale-issue-preview")
        self.assertEqual(0, self.creates)

    def test_changed_record_during_preview_preserves_concurrent_evidence(self):
        self.phase([self.entry()])
        self.mode = "preview-mutate"
        self.fails(self.preview, "issue-source-drift")
        self.assertIn("Concurrent context", self.source.read_text())
        self.assertEqual([], self.attempts())

    def test_traversal_wrong_phase_and_symlink_are_denied(self):
        self.phase([self.entry()])
        for name in ("../outside.md", "../../phases/02-other/02-01-SUMMARY.md"):
            args = Args(["1", name, "P1", "--title", self.title, "--body-file", str(self.public), "--variant", "Bug", "--no-match"])
            self.fails(lambda: issues.publication(args, "preview", "phase"))
        external = self.directory/"outside"
        external.mkdir()
        (external/"finding.md").write_bytes(self.source.read_bytes())
        alias = self.source.parent/"alias"
        self.make_alias(alias, external)
        try:
            args = Args(["1", "alias/finding.md", "P1", "--title", self.title, "--body-file", str(self.public), "--variant", "Bug", "--no-match"])
            self.fails(lambda: issues.publication(args, "preview", "phase"), "aliased-issue-source")
            self.assertTrue((external/"finding.md").exists())
        finally: self.remove_alias(alias)
        self.assertEqual(0, self.creates)

    def test_malformed_duplicate_and_untruthful_dispositions_fail(self):
        for entries in ("wrong", [self.entry(), self.entry()], [self.entry(state="resolved")], [self.entry(state="pending-human", relationship="resolving")], [self.entry(state="blocked-publication")]):
            self.phase(entries)
            self.assertFalse(self.handoff()["ready"])

    def test_canonical_identity_rejects_pr_wrong_origin_and_number(self):
        for changes in ({"url": "https://github.com/acme/project/pull/1"}, {"url": "https://github.com/other/project/issues/1"}, {"issueNumber": 2}, {"issueRepo": "github.com/other/project"}):
            self.phase([self.entry(**dict({"url": "https://github.com/acme/project/issues/1", "issueNumber": 1}, **changes))])
            self.assertFalse(self.handoff()["ready"])

    def test_type_preserving_update_requires_fresh_review_and_readback(self):
        self.phase([self.entry()])
        self.publish()
        decision = ["--existing-issue", "1"]
        preview = self.preview(decision)
        self.public.write_text(fixtures.PUBLIC+"\nReviewed added observation.\n")
        self.fails(lambda: self.publish(preview, decision, action="update"), "stale-issue-preview")
        preview = self.preview(decision)
        result = self.publish(preview, decision, action="update")
        self.assertTrue(result["published"])
        self.assertEqual(1, self.edits)
        self.assertEqual("Bug", self.metadata()["issue_refs"][0]["variant"])

    def test_attempted_multiple_markers_and_changed_intent_are_rejected(self):
        self.phase([self.entry()])
        preview = self.preview()
        self.mode = "lost"
        self.fails(lambda: self.publish(preview))
        self.mode = ""
        self.rows.append(dict(self.rows[0], number=2, url="https://github.com/acme/project/issues/2"))
        self.fails(lambda: self.publish(preview), "issue-identity-ambiguous")
        self.assertEqual(1, self.creates)

    def test_update_cannot_change_kind_or_use_stale_body_readback(self):
        self.phase([self.entry()])
        self.publish()
        decision = ["--existing-issue", "1"]
        preview = self.preview(decision)
        self.fails(lambda: self.publish(preview, decision, action="update", variant="UAT"), "issue-variant-conflict")
        self.direct_changes = {"body": fixtures.PUBLIC+"Changed"}
        self.fails(lambda: self.publish(preview, decision, action="update"), "stale-issue-preview")
        self.assertEqual(0, self.edits)

    def test_context_declarations_are_included_but_legacy_context_needs_none(self):
        directory = self.phase()
        context = directory/"01-CONTEXT.md"
        context.write_text("Legacy planning narrative\n")
        self.assertTrue(self.handoff()["ready"])
        context.write_text(join_frontmatter({"issue_refs": [self.entry()]}, "Context"))
        self.assertFalse(self.handoff()["ready"])

    def test_private_malformed_yaml_diagnostics_are_sanitized(self):
        self.phase()
        self.source.write_text("---\nissue_refs: [PRIVATE INVALID RECORD\n---\n")
        failure = self.fails(self.handoff, "invalid-issue-source")
        self.assertNotIn("PRIVATE INVALID RECORD", str(failure))

    def test_phase_session_cannot_bypass_handoff_by_omitting_phase(self):
        self.phase(declaration=False)
        self.session()
        self.fails(lambda: self.open("No declarations"), "phase-issues")
        self.assertEqual(0, self.pr_edits)

    def test_followup_closing_keyword_and_body_omitted_retarget_are_blocked(self):
        self.phase([self.entry()])
        self.publish()
        self.session()
        url = self.rows[0]["url"]
        for extra in ("Fixes #1. Related: "+url, "Closes acme/project#1. Related: "+url, "Resolves "+url, "Closes [problem]("+url+")"):
            self.fails(lambda: self.open(extra), "phase-issue-links")
        self.pull["body"] = self.pr_body("Fixes #1. Related: "+url)
        self.fails(lambda: self.open(base="main"), "phase-issue-links")
        self.assertEqual(0, self.pr_edits)

    def test_canonical_followup_link_delivers_and_explicit_phase_conflict_denies(self):
        self.phase([self.entry()])
        self.publish()
        self.session()
        self.assertTrue(self.open("Follow-up: "+self.rows[0]["url"])["updated"])
        self.fails(lambda: self.open("Follow-up: "+self.rows[0]["url"], phase="2"), "delivery-scope-conflict")
        self.assertEqual(1, self.pr_edits)

    def test_reconciliation_waits_for_closed_issue_then_retries_idempotently(self):
        self.folded()
        self.assertEqual("pending", self.reconcile()["items"][0]["state"])
        self.assertTrue(self.todo.exists())
        self.rows[0]["state"] = "CLOSED"
        self.assertEqual("completed", self.reconcile()["items"][0]["state"])
        self.assertFalse(self.todo.exists())
        self.assertEqual("already-completed", self.reconcile()["items"][0]["state"])
        self.assertEqual(0, self.creates)

    def test_open_wrong_head_and_missing_merge_readback_preserve_todo(self):
        self.folded(state="CLOSED")
        original = dict(self.pull)
        for pull in (dict(original, state="OPEN"), dict(original, headRefName="another"), None):
            self.pull = pull
            self.assertEqual("pending", self.reconcile()["items"][0]["state"])
            self.assertTrue(self.todo.exists())

    def test_pending_human_uat_cannot_be_forged_as_resolving_even_when_closed(self):
        self.phase([self.entry(variant="UAT", state="resolved", relationship="resolving", evidence="fixture evidence", url="https://github.com/acme/project/issues/1")])
        self.rows = [self.issue(state="CLOSED", body=self.uat_body())]
        self.fails(lambda: phase_issues.audit_pr("1", "Closes "+self.rows[0]["url"]), "phase-issue-links")
        self.assertFalse(phase_issues.accepted_human(self.uat_body()))

    def test_closed_uat_without_human_acceptance_keeps_folded_todo_pending(self):
        self.folded(state="CLOSED", body=self.uat_body())
        self.assertEqual("pending", self.reconcile()["items"][0]["state"])
        self.assertTrue(self.todo.exists())

    def test_uat_final_readback_must_preserve_accepted_human_evidence(self):
        self.folded(state="CLOSED", body=self.uat_body(True))
        accepted = dict(self.rows[0])
        for final in (dict(accepted, body=self.uat_body()), dict(accepted, body=fixtures.PUBLIC), None, dict(accepted, state="OPEN")):
            self.views = [accepted, final]
            self.assertEqual("pending", self.reconcile()["items"][0]["state"])
            self.assertTrue(self.todo.exists())
        bug = self.issue(state="CLOSED")
        self.views = [bug, dict(bug, body=self.uat_body())]
        self.assertEqual("pending", self.reconcile()["items"][0]["state"])

    def test_accepted_uat_todo_can_be_retired_after_final_closed_readback(self):
        self.folded(state="CLOSED", body=self.uat_body(True))
        self.assertTrue(phase_issues.accepted_human(self.rows[0]["body"]))
        self.assertEqual("completed", self.reconcile()["items"][0]["state"])
        self.assertFalse(self.todo.exists())

    def test_resolved_bug_issue_can_be_referenced_as_resolving_by_pr(self):
        self.phase([self.entry(state="resolved", relationship="resolving", evidence="fixture checked outcome", url="https://github.com/acme/project/issues/1")])
        self.rows = [self.issue()]
        self.session()
        result = self.open("Closes "+self.rows[0]["url"])
        self.assertTrue(result["updated"])
        self.assertIn("Closes "+self.rows[0]["url"], self.pull["body"])

    def test_accepted_uat_issue_can_be_referenced_as_resolving_by_pr(self):
        self.phase([self.entry(variant="UAT", state="resolved", relationship="resolving", evidence="synthetic accepted response fixture", url="https://github.com/acme/project/issues/1")])
        self.rows = [self.issue(state="CLOSED", body=self.uat_body(True))]
        self.session()
        self.assertTrue(self.open("Closes "+self.rows[0]["url"])["updated"])
        self.assertEqual(1, self.pr_edits)

    def test_phase_session_ambiguity_and_wrong_origin_pr_cannot_mutate(self):
        self.phase()
        self.session()
        data = json.loads(self.sessions.read_text())
        data["sessions"].append(dict(data["sessions"][0]))
        self.sessions.write_text(json.dumps(data))
        self.fails(lambda: self.open("Reviewed empty findings"), "ambiguous-delivery-session")
        data["sessions"].pop()
        self.sessions.write_text(json.dumps(data))
        self.pull["url"] = "https://github.com/other/project/pull/5"
        self.fails(lambda: self.open("Reviewed empty findings"), "provider-repository-mismatch")
        self.assertEqual(0, self.pr_edits)

    def test_reconciliation_rejects_unfolded_and_traversal_without_moving(self):
        self.folded(state="CLOSED")
        for name in ("unselected.md", "../legacy.md"):
            self.fails(lambda: self.reconcile(name), "todo-not-folded")
            self.assertTrue(self.todo.exists())

    def test_failed_issue_readback_and_local_change_preserve_folded_todo(self):
        self.folded(state="CLOSED")
        self.mode = "view"
        self.assertEqual("pending", self.reconcile()["items"][0]["state"])
        self.assertTrue(self.todo.exists())

    def test_phase_create_and_body_file_precedence_use_origin_pinned_target(self):
        self.phase([self.entry()])
        self.publish()
        self.session()
        self.pull = None
        body = self.directory/"pr body.md"
        body.write_text(self.pr_body("Follow-up: "+self.rows[0]["url"]))
        result = self.open("Closes #1", body_file=body, base="main")
        self.assertTrue(result["created"])
        self.assertEqual(body.read_text(), result["body"])
        self.assertTrue(result["isDraft"])
        with patch.object(delivery, "run", return_value=subprocess.CompletedProcess([], 0, "", "")) as boundary:
            PROVIDER_GH(["issue", "view", "1"])
        self.assertEqual("github.com/acme/project", boundary.call_args.args[0][-1])

    def test_declaration_setter_uses_snapshot_and_preserves_publication_identity(self):
        self.phase(declaration=False)
        draft = self.directory/"declarations.json"
        draft.write_text(json.dumps([self.entry()]))
        preview = phase_issues.declare(Args(["1", self.source.name]))
        phase_issues.declare(Args(["1", self.source.name, "--entries-file", str(draft), "--expect-digest", preview["snapshotDigest"]]))
        self.publish()
        preview = phase_issues.declare(Args(["1", self.source.name]))
        draft.write_text(json.dumps([self.entry(state="resolved", evidence="fixture outcome")]))
        phase_issues.declare(Args(["1", self.source.name, "--entries-file", str(draft), "--expect-digest", preview["snapshotDigest"]]))
        self.assertEqual(self.rows[0]["url"], self.metadata()["issue_refs"][0]["issue_url"])
        self.fails(lambda: phase_issues.declare(Args(["1", self.source.name, "--entries-file", str(draft), "--expect-digest", "stale"])), "phase-artifact-drift")

    def test_changed_todo_during_issue_readback_is_not_retired(self):
        self.folded(state="CLOSED")
        self.source = self.todo
        self.mode = "mutate"
        self.assertEqual("pending", self.reconcile()["items"][0]["state"])
        self.assertTrue(self.todo.exists())
        self.assertIn("Changed during readback", self.todo.read_text())

    def test_effective_body_cannot_change_between_validation_and_publish(self):
        self.phase([self.entry()])
        self.publish()
        self.session()
        self.pr_body_file = self.directory/"phase pr body.md"
        self.pr_body_file.write_text(self.pr_body("Follow-up: "+self.rows[0]["url"]))
        self.mode = "bodyfile-mutate"
        self.fails(lambda: self.open(body_file=self.pr_body_file), "pr-publication-drift")
        self.assertEqual(0, self.pr_edits)
        self.assertEqual("Closes #1", self.pr_body_file.read_text())

    def test_reviewed_empty_handoff_and_complete(self):
        self.phase()
        self.assertTrue(self.handoff()["ready"])
        # Completion retains its independent verification gate; a structured
        # passed record is provided by an explicit offline verification seam.
        with patch.object(verification, "status", return_value={"status": "passed"}):
            self.assertTrue(misc.complete_phase(Args(["1"]))["updated"])

    def test_missing_declaration_blocks_before_roadmap_write(self):
        self.phase(declaration=False)
        roadmap = self.directory/".planning/ROADMAP.md"
        before = roadmap.read_bytes()
        self.fails(lambda: misc.complete_phase(Args(["1"])), "phase-issues")
        self.assertEqual(before, roadmap.read_bytes())

    def test_unlinked_halted_problem_cannot_handoff(self):
        self.phase([self.entry()], status="halted")
        self.assertFalse(self.handoff()["ready"])
        self.assertTrue(self.handoff()["errors"])


if __name__ == "__main__":
    unittest.main()
