"""CLI acceptance contracts for reconciled UAT gaps and their local evidence."""
import json
from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class UatProvenance(RuntimeCase):
    def setUp(self):
        super().setUp()
        self.directory = Path(self.phase())
        self.path = self.directory/"01-UAT.md"
        self.plan_path = self.directory/"01-02-PLAN.md"
        self.summary_path = self.directory/"01-02-SUMMARY.md"
        self.plan_path.write_text('---\ngap_ids: [G1]\n---\nFix the reported gap.\n', encoding="utf-8")
        self.summary_path.write_text('---\nstatus: complete\n---\nImplemented gap closure.\n', encoding="utf-8")
        self.session()

    def session(self, result="issue", **changes):
        gap = {"gap_id": "G1", "truth": "Login succeeds", "status": "resolved", "test": 1,
               "resolved_by": self.plan_path.name, "resolved_at": "2026-10-28"}
        gap.update(changes)
        self.path.write_text('---\nstatus: complete\n---\n## Tests\n\n### 1. Login\nresult: '+result+
                             '\n\n## Summary\n\ntotal: 1\n\n## Gaps\n\n'+
                             '\n'.join(('- ' if index == 0 else '  ')+key+': '+json.dumps(value)
                                       for index, (key, value) in enumerate(gap.items()))+'\n', encoding="utf-8")

    def assert_blocked(self):
        packet = self.cli("phase.uat-passed", "1", "--uat-only", status=1)
        self.assertFalse(packet["passed"])
        self.assertTrue(packet["blocking_items"])
        self.assertGreater(self.cli("audit-uat")["count"], 0)

    def test_valid_resolution_and_iso_timestamp_pass(self):
        self.assertTrue(self.cli("phase.uat-passed", "1", "--uat-only")["passed"])
        self.assertEqual(0, self.cli("audit-uat")["count"])
        self.session(resolved_at="2026-10-28T12:30:00Z")
        self.assertTrue(self.cli("phase.uat-passed", "1")["passed"])
        self.assertEqual(0, self.cli("audit-open")["counts"]["uat"])

    def test_plan_absent_blocks(self):
        self.plan_path.unlink()
        self.assert_blocked()

    def test_matching_summary_absent_blocks(self):
        self.summary_path.rename(self.directory/"01-03-SUMMARY.md")
        self.assert_blocked()

    def test_plan_gap_id_mismatch_or_absence_blocks(self):
        for frontmatter in ('gap_ids: [G2]', 'gap_ids: G1', 'gap_ids: []', 'other: value'):
            with self.subTest(frontmatter=frontmatter):
                self.plan_path.write_text('---\n'+frontmatter+'\n---\n', encoding="utf-8")
                self.assert_blocked()

    def test_invalid_resolution_fields_block(self):
        for field, value in (("status", "failed"), ("status", "pass"), ("status", "resolved-ish"),
                             ("resolved_by", ""), ("resolved_by", None), ("resolved_at", ""),
                             ("resolved_at", "yesterday"), ("resolved_at", "2026-02-30"),
                             ("resolved_at", None), ("gap_id", ""), ("gap_id", None)):
            with self.subTest(field=field, value=value):
                self.session(**{field: value})
                self.assert_blocked()

    def test_traversal_and_absolute_plan_paths_block(self):
        for name in ("../01-02-PLAN.md", "..\\01-02-PLAN.md", "child/01-02-PLAN.md",
                     str(self.plan_path.resolve()), "C:\\other\\01-02-PLAN.md", "01-02-PLAN.md:stream"):
            with self.subTest(name=name):
                self.session(resolved_by=name)
                self.assert_blocked()

    def test_nonregular_plan_and_summary_block(self):
        for path in (self.plan_path, self.summary_path):
            with self.subTest(path=path.name):
                original = path.read_text(encoding="utf-8")
                path.unlink()
                path.mkdir()
                self.assert_blocked()
                path.rmdir()
                path.write_text(original, encoding="utf-8")

    def test_symlink_evidence_blocks(self):
        target = self.put("outside-PLAN.md", self.plan_path.read_text(encoding="utf-8"))
        self.plan_path.unlink()
        try:
            self.plan_path.symlink_to(target)
        except OSError as error:
            self.skipTest("Host cannot create symlinks: "+str(error))
        self.assert_blocked()
        self.plan_path.unlink()
        self.plan_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
        original = self.summary_path.read_text(encoding="utf-8")
        self.summary_path.unlink()
        target.write_text(original, encoding="utf-8")
        self.summary_path.symlink_to(target)
        self.assert_blocked()

    def test_pending_blocked_and_unproven_resolved_test_remain_blockers(self):
        for result in ("pending", "blocked", "resolved"):
            with self.subTest(result=result):
                self.session(result=result)
                self.assert_blocked()

    def test_unresolved_second_gap_and_regression_block(self):
        self.path.write_text(self.path.read_text(encoding="utf-8")+
                             '\n- gap_id: G2\n  test: 1\n  truth: Login regressed\n  status: failed\n', encoding="utf-8")
        self.assert_blocked()

    def test_orphan_failed_gap_blocks_even_when_test_passed(self):
        self.session(result="pass", status="failed", test=99)
        self.assert_blocked()

    def test_malformed_gap_yaml_blocks(self):
        self.path.write_text('## Tests\n### 1. Login\nresult: pass\n## Gaps\n- truth: [broken\n', encoding="utf-8")
        self.assert_blocked()

    def test_ordinary_passed_pending_and_manual_verification(self):
        self.path.write_text('## Tests\n### 1. Login\nresult: pass\n', encoding="utf-8")
        self.assertTrue(self.cli("phase.uat-passed", "1", "--uat-only")["passed"])
        self.path.write_text('## Tests\n### 1. Login\nresult: pending\n', encoding="utf-8")
        self.assert_blocked()
        self.session()
        self.put(self.directory/"01-VERIFICATION.md", '---\nstatus: human_needed\nhuman_verification: [Review appearance]\n---\n')
        self.assertFalse(self.cli("phase.uat-passed", "1", "--require-verification", status=1)["passed"])
        self.assertEqual(1, self.cli("audit-uat")["count"])
