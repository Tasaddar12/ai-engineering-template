"""Preservation regressions. Execution is deferred until every overhaul PR is open."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"engineer/bin"))
from lib import bundles, cleanup, codebase, config, delivery, frontmatter, handoff, issues, misc, models, numbering, planning_review, records, security_tracking, uat, verification, worktrees
from lib.core import Args, Failure, read, write_json
from lib.text import join_frontmatter, split_frontmatter


class PreservationCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.environment = patch.dict(os.environ, {"ENGINEER_ROOT": str(self.root), "ENGINEER_HOST": "codex"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Preservation Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("remote", "add", "origin", "https://github.com/example/preservation.git")
        self.put("README.md", "fixture\n")
        self.commit("fixture")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=True).stdout.strip()

    def put(self, name, content):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def commit(self, message):
        self.git("add", "--all")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD")

    def phase(self, name):
        return Path(records.phase_change(Args([name]), "add")["directory"])

    def isolated_root(self):
        self.put(".gitignore", ".worktrees/\n")
        self.commit("ignore worktrees")


class IsolationContract(PreservationCase):
    def test_method_only_code_fixer_is_readable_but_never_dispatchable(self):
        namespace = self.root/"namespace"
        self.put("namespace/agents/code-fixer.md", "---\nname: code-fixer\n---\nFull retained method\n")
        self.put("namespace/agents/targeted-fixer.md", "---\nname: targeted-fixer\n---\nScoped role\n")
        with patch.object(models, "NAMESPACE", namespace):
            packet = models.list_agents(Args([]))
            self.assertEqual(["targeted-fixer"], [item["name"] for item in packet["agents"]])
            self.assertEqual("code-fixer", packet["method_sources"][0]["name"])
            with self.assertRaises(Failure) as caught:
                models.resolve_agent("code-fixer")
        self.assertEqual("agent-method-only", caught.exception.code)

    def test_negotiates_only_real_isolation_and_refuses_unignored_root(self):
        with self.assertRaises(Failure):
            worktrees.isolation(Args([]))
        self.isolated_root()
        packet = worktrees.isolation(Args(["--phase", "03", "--plan", "03-01"]))
        self.assertEqual("orchestrator-worktree", packet["mode"])
        self.assertEqual("03-01", packet["plan"])
        with patch.dict(os.environ, {"ENGINEER_HOST": "claude"}):
            native = worktrees.isolation(Args([]))
        self.assertEqual("harness-worktree", native["mode"])
        self.assertEqual('isolation="worktree"', native["harnessFlag"])
        for disabled in (None, False, "none", "sequential"):
            with self.subTest(disabled=disabled), patch.object(config, "load", return_value={"workflow": {"isolation": disabled}}):
                with self.assertRaises(Failure):
                    worktrees.isolation(Args([]))
        with self.assertRaises(Failure):
            worktrees.isolation(Args(["--force-isolation", "none"]))

    def test_cleanup_rejects_tampered_exact_approval_before_any_git_delete(self):
        self.isolated_root()
        packet = cleanup.command(Args([]), "preview")
        path = self.root/".planning/cleanup"/(packet["approval_token"]+".json")
        write_json(path, {"entries": [{"path": str(self.root), "branch": "main", "head": self.git("rev-parse", "HEAD")}], "created": "tampered"})
        with patch.object(cleanup, "run") as execution:
            with self.assertRaises(Failure) as caught:
                cleanup.command(Args(["--approval-token", packet["approval_token"], "--confirm"]), "apply")
        execution.assert_not_called()
        self.assertEqual("cleanup-preview-corrupt", caught.exception.code)


class RecordPreservation(PreservationCase):
    def test_no_renumber_and_normal_remove_rewrite_links_once(self):
        self.phase("First")
        self.phase("Second")
        third = self.phase("Third")
        self.put(str(third.relative_to(self.root)/"03-01-PLAN.md"), join_frontmatter({"phase": "03", "depends_on": ["03-02"]},
                 "See [context](03-CONTEXT.md) and .planning/phases/03-third/03-02-PLAN.md. Threat T-03-01 stays.\n"))
        self.put(".planning/PROJECT.md", "Narrative Phase 03 and [plan](phases/03-third/03-01-PLAN.md).\n")
        result = records.phase_change(Args(["01", "--no-renumber"]), "remove")
        self.assertEqual([], result["renumbered"])
        self.assertTrue(third.is_dir())
        records.phase_change(Args(["02"]), "remove")
        moved = self.root/".planning/phases/02-third/02-01-PLAN.md"
        metadata, body = split_frontmatter(read(moved))
        self.assertEqual("02", metadata["phase"])
        self.assertEqual(["02-02"], metadata["depends_on"])
        self.assertIn("02-CONTEXT.md", body)
        self.assertIn("phases/02-third/02-02-PLAN.md", body)
        self.assertIn("T-03-01", body)
        self.assertIn("Phase 02", read(self.root/".planning/PROJECT.md"))

    def test_decision_outcome_milestone_goal_and_derived_save_preserve_prose(self):
        misc.milestone(Args(["v1.0 Test", "--goal", "Observable goal"]), "create")
        self.assertIn("**Goal:** Observable goal", read(self.root/".planning/ROADMAP.md"))
        self.phase("Behavior")
        self.put(".planning/STATE.md", "# State\n\n## Current Position\n\nPhase: 01\nStatus: Planning\n\nAuthor supplied narrative.\n")
        records.state_action(Args(["Use stdlib", "--rationale", "Portable", "--outcome", "Accepted"]), "add-decision")
        self.assertIn("| Use stdlib | Portable | Accepted |", read(self.root/".planning/PROJECT.md"))
        packet = records.state_action(Args([]), "save")
        self.assertEqual(1, packet["progress"]["total_phases"])
        self.assertIn("Author supplied narrative.", read(self.root/".planning/STATE.md"))
        with self.assertRaises(Failure):
            records.state_action(Args(["replacement content"]), "save")

    def test_validate_reports_cross_record_drift_without_blocking_and_repair_is_bound(self):
        self.phase("Behavior")
        self.put(".planning/STATE.md", "# State\n\n## Current Position\nPhase: 99\n\nPreserve this decision.\n")
        packet, status = misc.integrity(Args([]))
        self.assertEqual(0, status)
        self.assertTrue(any("absent phase" in item["error"] for item in packet["warnings"]))
        self.assertEqual(1, misc.integrity(Args(["--strict"]))[1])
        preview = planning_review.repair(Args([]))
        self.put(".planning/PROJECT.md", "Changed author intent\n")
        with self.assertRaises(Failure):
            planning_review.repair(Args(["--apply", "--expect", preview["digest"]]))
        current = planning_review.repair(Args([]))
        planning_review.repair(Args(["--apply", "--expect", current["digest"]]))
        self.assertIn("Preserve this decision.", read(self.root/".planning/STATE.md"))
        self.assertIn("Phase: 99", read(self.root/".planning/STATE.md"))

    def test_init_reports_real_work_and_missing_expected_directory(self):
        self.phase("Behavior")
        self.put(".planning/STATE.md", "## Current Position\nPhase: 01\n")
        quick = records.quick(Args(["Repair"]), "create")
        todo = records.todo(Args(["Inspect"]), "add")
        with patch.object(models, "resolve", return_value="inherit"):
            packet = bundles.init(Args([]), "complete-milestone")
        self.assertEqual(1, len(packet["milestone_phases"]))
        self.assertEqual(quick["id"], packet["open_quick"][0]["id"])
        self.assertEqual(todo["title"], packet["pending_todos"][0]["title"])
        self.assertEqual(config.DEFAULTS["context_window"], packet["context_window"])
        self.assertEqual("01", packet["incomplete_phase"]["number"])


class HandoffAndFreshness(PreservationCase):
    def test_full_role_continuation_roundtrips_without_replacement(self):
        continuation = "Resume verifier role.\nKeep exactly this remaining scope.\n"
        digest = "Full supplied digest\nLine two with requested fields.\n"
        handoff.command(Args(["verifier-1", "--reason", "context", "--role", "verifier", "--continuation", continuation,
                              "--digest", digest, "--remaining", "Read only src/a.py"]), "write")
        packet = handoff.command(Args(["verifier-1"]), "read")
        self.assertEqual(continuation, packet["continuation"])
        self.assertEqual(digest, packet["digest"])
        self.assertEqual(["Read only src/a.py"], packet["remaining"])
        handoff.command(Args(["verifier-1"]), "consume")
        with self.assertRaises(Failure):
            handoff.command(Args(["verifier-1"]), "consume")

    def test_unreachable_map_revision_recovers_from_touched_map_history(self):
        self.put(".planning/codebase/ARCHITECTURE.md", "Actual source map\n")
        baseline = self.commit("map source")
        codebase.command(Args(["ARCHITECTURE", "--paths", "src"]), "record")
        path = self.root/".planning/codebase/.freshness.json"
        data = json.loads(read(path))
        data["maps"]["ARCHITECTURE"]["revision"] = "f"*40
        write_json(path, data)
        packet = codebase.command(Args([]), "status")["maps"][0]
        self.assertFalse(packet["stale"])
        self.assertTrue(packet["recovered_from_map_history"])
        self.assertEqual(baseline, packet["baseline_revision"])
        self.put("src/app.py", "changed\n")
        self.commit("source change")
        with patch.object(config, "load", return_value={"codebase": {"max_age_commits": 0}}):
            packet = codebase.command(Args([]), "status")["maps"][0]
        self.assertTrue(packet["stale"])
        self.assertEqual(["src/app.py"], packet["changed_files"])


class IssueProvider(PreservationCase):
    def test_uat_bullet_acceptance_fields_and_step_rows_follow_selected_variant(self):
        self.prepare_issue()
        template = self.namespace/"engineer/templates/issue.md"
        body = """## Steps and expected outcomes

| Step | Action | Expected outcome | Actual outcome / evidence |
|------|--------|------------------|---------------------------|
| 1 | Open delivered page | Title visible | pending |

## Human acceptance

- Status: PENDING HUMAN acceptance
- Reviewer: pending
- Date: pending
- Decision: pending
- Evidence: pending
"""
        import re
        content = re.sub(r"(?ms)(^### UAT\n\n```markdown\n).*?^```", lambda match: match[1]+body+"```", read(template))
        template.write_text(content, encoding="utf-8")
        issues.validate("Delivered acceptance", body, "UAT")
        with self.assertRaises(Failure):
            issues.validate("Delivered acceptance", body.replace("PENDING HUMAN acceptance", "ACCEPTED"), "UAT")

    def test_pr_validation_uses_fenced_body_and_keeps_optional_sections_optional(self):
        self.prepare_issue()
        template = self.namespace/"engineer/templates/pull-request.md"
        body = "## Goal\nObserved outcome\n## Changes\nConcrete change\n## Verification\nPending ordered final batch\n## Known gaps\nFinal checks\n## Risks or rollback\nRevert the owned commit\n"
        template.write_text("# PR\n## File Template\n```markdown\n"+body+"## Requirements or Issues\nOptional\n## Stack\nConditional\n```\n## Authoring and consumer contract\nGuidance\n", encoding="utf-8")
        delivery.validate_body(body)

    def test_variant_catalog_parser_ignores_other_fences_and_catalog_prose(self):
        template = self.put("catalog.md", """## Introduction
```markdown
## File Template
### UAT
fake
```
## File Template
### Bug
```markdown
## Problem
## Solution
```
### Security risk
```markdown
## Security concern
## Impact
```
## Guidance
""")
        selected = issues.variant_template(template, "Bug")
        self.assertEqual(["## Problem", "## Solution"], selected.strip().splitlines())
        with self.assertRaises(Failure):
            issues.variant_template(template, "defect")

    def prepare_issue(self):
        self.namespace = self.root/"namespace"
        template = self.namespace/"engineer/templates/issue.md"
        template.parent.mkdir(parents=True)
        template.write_text(read(Path(__file__).resolve().parents[1]/"engineer/templates/issue.md"), encoding="utf-8")
        namespace_patch = patch.object(models, "NAMESPACE", self.namespace)
        namespace_patch.start()
        self.addCleanup(namespace_patch.stop)
        self.todo = records.todo(Args(["Fix boundary", "--problem", "The boundary fails"]), "add")
        body = issues.file_template(template, "Bug").replace("[What is failing and why it matters.]", "The boundary fails.")
        self.body = self.put("body.md", body)
        return [self.todo["path"], "--title", "Fix boundary", "--variant", "Bug", "--body-file", str(self.body)]

    def provider(self, args, check=True):
        if args[:2] == ["issue", "list"]:
            return subprocess.CompletedProcess(args, 0, json.dumps(self.remote), "")
        if args[:2] == ["issue", "view"]:
            return subprocess.CompletedProcess(args, 0, json.dumps(self.remote[0]), "")
        if args[:2] == ["issue", "create"]:
            self.creates += 1
            body = Path(args[args.index("--body-file")+1]).read_text(encoding="utf-8")
            self.remote = [{"url": "https://github.com/example/preservation/issues/7", "number": 7, "title": "Fix boundary", "body": body, "state": "OPEN", "labels": []}]
            if self.timeout:
                raise Failure("provider-timeout", "uncertain create")
            return subprocess.CompletedProcess(args, 0, self.remote[0]["url"], "")
        raise AssertionError(args)

    def test_uncertain_create_recovers_once_and_preview_cannot_reset_consumption(self):
        argv = self.prepare_issue()+["--no-match"]
        self.remote, self.creates, self.timeout = [], 0, True
        with patch.object(delivery, "gh", side_effect=self.provider):
            preview = issues.publication(Args(argv), "preview")
            result = issues.publication(Args(argv+["--preview-token", preview["previewToken"]]), "publish")
        self.assertEqual(1, self.creates)
        self.assertTrue(result["reused"])
        self.assertEqual("https://github.com/example/preservation/issues/7", split_frontmatter(read(Path(self.todo["path"])))[0]["issue_url"])

    def test_reviewed_closed_match_stays_pending_and_no_match_conflict_blocks(self):
        argv = self.prepare_issue()
        self.remote = [{"url": "https://github.com/example/preservation/issues/7", "number": 7, "title": "Fix boundary", "body": read(self.body), "state": "CLOSED", "labels": []}]
        self.creates, self.timeout = 0, False
        with patch.object(delivery, "gh", side_effect=self.provider):
            with self.assertRaises(Failure):
                issues.publication(Args(argv+["--no-match"]), "preview")
            selected = argv+["--existing-issue", "7"]
            preview = issues.publication(Args(selected), "preview")
            result = issues.publication(Args(selected+["--preview-token", preview["previewToken"]]), "publish")
        self.assertTrue(result["requires_reconciliation"])
        self.assertTrue(Path(self.todo["path"]).exists())
        self.assertEqual(0, self.creates)


class QuickVerification(PreservationCase):
    def test_v4_coverage_binding_is_required_and_source_drift_invalidates_it(self):
        directory = self.phase("Covered source")
        self.put("src/app.py", "original\n")
        self.commit("source")
        args = Args(["01", "--covered-files", "src/app.py"])
        packet = verification.fingerprint(args)
        self.assertRegex(packet["covered_digest"], r"^v4:sha256:[a-f0-9]{64}$")
        report = Path(packet["path"])
        metadata, body = split_frontmatter(read(report))
        metadata["status"] = "passed"
        report.write_text(join_frontmatter(metadata, body), encoding="utf-8")
        self.commit("verification")
        self.assertTrue(verification.current_evidence("01")["current"])
        metadata["covered_digest"] = "v3:sha256:"+packet["fingerprint"]
        report.write_text(join_frontmatter(metadata, body), encoding="utf-8")
        self.commit("stale digest scheme")
        self.assertTrue(any("v4" in reason for reason in verification.current_evidence("01")["reasons"]))
        self.assertTrue(any("v4" in error for error in frontmatter.errors(metadata, "verification")))

    def test_unknown_check_selection_cannot_produce_vacuous_passing_receipt(self):
        self.put(".planning/config.yaml", "verification:\n  commands:\n    - id: real\n      argv: [python, -c, pass]\n")
        with self.assertRaises(Failure) as caught:
            verification.run_checks(Args(["--checks", "typo"]))
        self.assertEqual("unknown-check", caught.exception.code)

    def test_structured_quick_verification_rejects_source_and_pr_revision_drift(self):
        quick = records.quick(Args(["Fix quick boundary"]), "create")
        self.put("src/app.py", "correct\n")
        self.git("switch", "-c", "codex/quick")
        self.commit("quick implementation")
        args = Args(["--quick", quick["id"], "--covered-files", "src/app.py"])
        report = Path(verification.fingerprint(args)["path"])
        metadata, body = split_frontmatter(read(report))
        metadata["status"] = "passed"
        report.write_text(join_frontmatter(metadata, body), encoding="utf-8")
        self.commit("quick verification")
        self.assertEqual("passed", verification.status(Args(["--quick", quick["id"]]))["status"])
        self.assertTrue(verification.current_evidence(quick=quick["id"])["current"])
        pr = {"number": 1, "url": "https://github.com/example/preservation/pull/1", "headRefOid": "0"*40, "body": ""}
        with patch.object(delivery, "view", return_value=pr):
            with self.assertRaises(Failure) as caught:
                delivery.verified_delivery(Args(["--quick", quick["id"]]), "codex/quick")
        self.assertEqual("pr-revision-mismatch", caught.exception.code)
        self.put("src/app.py", "regression\n")
        self.commit("source drift")
        self.assertFalse(verification.current_evidence(quick=quick["id"])["current"])


class RecordSchemas(PreservationCase):
    def plan_metadata(self):
        return {"phase": "01", "plan": "01", "type": "execute", "wave": 1, "depends_on": [],
                "files_modified": [], "files_deleted": [], "resources": [], "autonomous": True,
                "requirements": ["REQ-01"], "acceptance": [], "documentation": [], "checks": [], "issue_refs": [],
                "must_haves": {"truths": [], "artifacts": [], "key_links": []}}

    def test_complete_metadata_and_actual_argv_are_required_without_inventing_approval(self):
        metadata = self.plan_metadata()
        self.assertEqual([], frontmatter.errors(metadata, "plan"))
        for field in ("acceptance", "documentation", "checks", "issue_refs"):
            incomplete = {key: value for key, value in metadata.items() if key != field}
            self.assertTrue(any(field in error for error in frontmatter.errors(incomplete, "plan")))
        for checks in (["python -m unittest"], [["python", ""]], [{"argv": ["python", "-m", "unittest"]}]):
            self.assertTrue(any("argv" in error for error in frontmatter.errors({**metadata, "checks": checks}, "plan")))
        self.assertEqual([], frontmatter.errors({**metadata, "checks": [["python", "-m", "unittest"]]}, "plan"))
        self.assertTrue(frontmatter.errors({"phase": "01", "discussion": "approved", "issue_refs": []}, "context"))
        self.assertEqual([], frontmatter.errors({"phase": "01", "discussion": "pending", "issue_refs": []}, "context"))
        self.assertTrue(frontmatter.errors({"phase": "01", "plan": "01", "status": "complete"}, "summary"))
        quick = {key: value for key, value in metadata.items() if key != "phase"}
        quick.update({"quick": "001", "requirements": []})
        self.assertEqual([], frontmatter.errors(quick, "plan"))
        self.assertTrue(frontmatter.errors({**quick, "quick": "invented-phase"}, "plan"))


class LocalHumanUAT(PreservationCase):
    def plan_metadata(self):
        return RecordSchemas.plan_metadata(self)

    def prepare_session(self, result="pass", accepted=True, gaps="", checklist="A-1 delivered outcome"):
        directory = self.phase("Human acceptance")
        plan = self.plan_metadata()
        self.put(str(directory.relative_to(self.root)/"01-01-PLAN.md"), join_frontmatter(plan, "Delivered fixture behavior\n"))
        summary = {"phase": "01", "plan": "01", "status": "complete", "requirements-completed": [], "acceptance": [], "documentation": [], "issue_refs": []}
        self.put(str(directory.relative_to(self.root)/"01-01-SUMMARY.md"), join_frontmatter(summary, "Committed fixture source\n"))
        self.commit("delivered fixture")
        path = directory/"01-UAT.md"
        body = ("## Acceptance checklist\n\n- [x] "+checklist+"\n\n## Tests\n\n### 1. Owner boundary\nacceptance: A-1\nexpected: Owner-only update succeeds\nresult: "+result+"\n\n"
                "## Human acceptance\n\nstatus: "+("ACCEPTED" if accepted else "PENDING HUMAN acceptance")+"\naccepted_by: "+("Human fixture" if accepted else '""')+"\naccepted_at: "+("2026-10-27" if accepted else '""')+"\ndecision: "+("Accepted the covered fixture build" if accepted else '""')+"\n\n## Gaps\n\n"+gaps)
        path.write_text(join_frontmatter({"phase": "01", "status": "partial", "source": ["01-01-SUMMARY.md"]}, body), encoding="utf-8")
        return path

    def test_all_pass_actions_still_need_actual_final_human_fields(self):
        path = self.prepare_session(accepted=False)
        self.assertFalse(uat.session_status(path)["passed"])
        with self.assertRaises(Failure):
            uat.complete(Args([str(path)]))
        metadata, body = split_frontmatter(read(path))
        self.assertEqual("partial", metadata["status"])
        self.assertIn('accepted_by: ""', body)

    def test_skipped_blocked_unresolved_and_not_testable_actions_never_complete(self):
        path = self.prepare_session()
        original = read(path)
        for status in ("skipped", "not-testable", "blocked", "issue", "pending"):
            with self.subTest(status=status):
                path.write_text(original.replace("result: pass", "result: "+status), encoding="utf-8")
                self.assertFalse(uat.session_status(path)["passed"])
                with self.assertRaises(Failure):
                    uat.complete(Args([str(path)]))

    def test_historical_gap_requires_executed_matching_resolution_and_human_retest_when_requested(self):
        gap = "- gap_id: G-1\n  status: resolved\n  test: 1\n  resolved_by: 01-02-PLAN.md\n  resolved_at: 2026-10-27\n"
        path = self.prepare_session(result="issue", gaps=gap)
        self.assertFalse(uat.session_status(path)["passed"])
        plan = {**self.plan_metadata(), "plan": "02"}
        self.put(str(path.parent.relative_to(self.root)/"01-02-PLAN.md"), join_frontmatter(plan, "Resolve stable gap G-1\n"))
        summary = {"phase": "01", "plan": "02", "status": "complete", "requirements-completed": [], "acceptance": ["G-1: owner-check fixture passed"], "documentation": [], "issue_refs": []}
        summary_path = self.put(str(path.parent.relative_to(self.root)/"01-02-SUMMARY.md"), join_frontmatter(summary, "## Resolution evidence\n\nG-1 fixture regression outcome recorded.\n"))
        self.commit("executed gap closure fixture")
        self.assertTrue(uat.session_status(path)["passed"])
        self.assertEqual(["1"], uat.session_status(path)["resolved_tests"])
        self.assertIn("result: issue", read(path))
        original = read(path)
        path.write_text(original.replace("A-1 delivered outcome", "A-1 human retest action 1"), encoding="utf-8")
        self.assertFalse(uat.session_status(path)["passed"])
        path.write_text(original, encoding="utf-8")
        summary_path.write_text(read(summary_path)+"uncommitted drift\n", encoding="utf-8")
        self.assertFalse(uat.session_status(path)["passed"])


class CanonicalSecurityTracking(PreservationCase):
    def prepare_risk(self):
        directory = self.phase("Security boundary")
        self.plan = self.put(str(directory.relative_to(self.root)/"01-01-PLAN.md"), """<threat_model>
| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| T-01-01 + Pending: canonical review | Authorization | handler | high | mitigate | Require owner checks |
</threat_model>
""")
        self.entry = {"key": "github.com/example/preservation|handler owner check|cross-owner write", "id": "handler-owner",
                      "heading": "Handler owner boundary", "plan": "01-01-PLAN.md", "threat_id": "T-01-01", "planned": True,
                      "owner": "Implementation owner", "scope_acceptance": "PLAN owns scope and acceptance",
                      "assessment_uncertainty": "PLAN assessment; deployment unknown", "lifecycle_outcome": "unresolved",
                      "next_action": "Implement PLAN mitigation", "revision_check_evidence": "Pending: final checks deferred",
                      "aliases_occurrences": "01-01/T-01-01", "match_review": {"disposition": "no-match", "evidence": "Reviewed full-scope search candidates", "reviewed_issue_urls": [], "reviewed_pr_urls": []}}
        self.entries = self.put("risks.json", json.dumps([self.entry]))
        namespace = self.root/"namespace"
        template = namespace/"engineer/templates/issue.md"
        template.parent.mkdir(parents=True)
        template.write_text(read(Path(__file__).resolve().parents[1]/"engineer/templates/issue.md"), encoding="utf-8")
        namespace_patch = patch.object(models, "NAMESPACE", namespace)
        namespace_patch.start()
        self.addCleanup(namespace_patch.stop)
        return Args(["01", "--entries-file", str(self.entries), "--variant", "Security risk"])

    def test_quick_tracking_uses_actual_quick_identity_and_dedicated_container(self):
        self.prepare_risk()
        quick = records.quick(Args(["Secure quick boundary"]), "create")
        plan = Path(quick["directory"])/"001-PLAN.md"
        plan.write_text(read(self.plan), encoding="utf-8")
        self.entry["plan"] = plan.name
        self.entries.write_text(json.dumps([self.entry]), encoding="utf-8")
        searches = []
        def search(query, label=None):
            searches.append((query, label))
            return []
        with patch.object(security_tracking, "issue_search", side_effect=search), patch.object(security_tracking, "query", return_value=[]):
            packet = security_tracking.command(Args([quick["id"], "--entries-file", str(self.entries)]), "review", "quick")
        self.assertTrue(packet["ready"])
        self.assertEqual("001", packet["quick"])
        self.assertEqual("quick:001", packet["scope"]["key"])
        self.assertNotIn("phase", packet)
        self.assertEqual(('"chore(security): quick 001 security checklist"', "quick-security-checklist"), searches[0])

    def test_unavailable_or_duplicate_container_lookup_never_creates(self):
        args = self.prepare_risk()
        with patch.object(security_tracking, "issue_search", side_effect=Failure("offline", "lookup unavailable")), patch.object(security_tracking, "query", return_value=[]):
            packet = security_tracking.review(args)
        self.assertFalse(packet["ready"])
        self.assertTrue(any("lookup unavailable" in item for item in packet["pending"]))
        title = "chore(security): phase 01 security checklist"
        containers = [{"title": title, "url": "https://github.com/example/preservation/issues/"+str(n), "body": "", "state": "OPEN"} for n in (1, 2)]
        def search(query, label=None):
            return containers if label else []
        with patch.object(security_tracking, "issue_search", side_effect=search), patch.object(security_tracking, "query", return_value=[]), patch.object(delivery, "gh") as provider:
            with self.assertRaises(Failure):
                security_tracking.command(args, "preview")
        provider.assert_not_called()

    def test_actual_provider_anchor_is_used_and_guessed_fragment_is_rejected(self):
        self.prepare_risk()
        body = security_tracking.entry_body(self.entry, None)
        url = "https://github.com/example/preservation/issues/9"
        provider = {"html_url": url, "number": 9, "state": "open", "body": body,
                    "body_html": '<h3><a id="provider-anchor-42" href="#actual-heading-42"></a>Handler owner boundary</h3>'}
        with patch.object(security_tracking, "query", return_value=provider):
            result = security_tracking.render_readback(url, body, [self.entry])
            self.assertIn(result[0]["url"], (url+"#provider-anchor-42", url+"#actual-heading-42"))
            wrong = {**self.entry, "heading_url": url+"#handler-owner-boundary"}
            with self.assertRaises(Failure):
                security_tracking.render_readback(url, body, [wrong])
        missing = {**provider, "body_html": "<h3>Handler owner boundary</h3>"}
        with patch.object(security_tracking, "query", return_value=missing):
            with self.assertRaises(Failure):
                security_tracking.render_readback(url, body, [self.entry])

    def test_unplanned_risk_requires_standalone_body_and_closed_unresolved_match_is_pending(self):
        args = self.prepare_risk()
        self.entry["planned"] = False
        self.entries.write_text(json.dumps([self.entry]), encoding="utf-8")
        with self.assertRaises(Failure):
            security_tracking.load_entries(args)
        self.entry["planned"] = True
        self.entry["match_review"] = {"disposition": "existing", "evidence": "Reviewed full remediation scope", "url": "https://github.com/example/preservation/issues/3", "reviewed_issue_urls": [], "reviewed_pr_urls": []}
        self.entries.write_text(json.dumps([self.entry]), encoding="utf-8")
        closed = {"url": "https://github.com/example/preservation/issues/3", "state": "CLOSED", "title": "Existing risk", "body": "Unresolved risk"}
        def provider(argv):
            return closed if argv[:2] == ["issue", "view"] else []
        with patch.object(security_tracking, "issue_search", return_value=[]), patch.object(security_tracking, "query", side_effect=provider):
            packet = security_tracking.review(args)
        self.assertFalse(packet["ready"])
        self.assertTrue(any("reopening authority" in item for item in packet["pending"]))


if __name__ == "__main__":
    unittest.main()
