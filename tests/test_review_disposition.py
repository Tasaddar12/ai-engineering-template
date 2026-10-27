"""Ledger regressions authored for the Python port; execution deferred by user."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
# Isolate the new runtime package from any legacy lib already imported by a suite.
SPEC = importlib.util.spec_from_file_location("ledger_runtime", ROOT / "engineer/bin/lib/__init__.py",
                                            submodule_search_locations=[str(ROOT / "engineer/bin/lib")])
PACKAGE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PACKAGE
SPEC.loader.exec_module(PACKAGE)
from ledger_runtime import review_disposition as ledger
from ledger_runtime.core import Args


def review(body, total=1):
    return f"---\nstatus: findings\nfindings:\n  critical: {total}\n  warning: 0\n  info: 0\n  total: {total}\n---\n{body}\n"


class LedgerJoin(unittest.TestCase):
    def test_title_identity_and_empty_are_not_unknown(self):
        old = ledger.render(ledger.reconcile(review("### CR-01:"), "", [("fix.md", "## Fixed Issues\n### CR-01:")]), "01", "old")
        result = ledger.reconcile(review("### CR-01: New"), old, [])
        self.assertEqual(result["rows"][0]["disposition"], "open")
        self.assertEqual(result["dropped"], ["CR-01=fixed"])
        self.assertIn('title: ""', old)

    def test_json_titles_and_spacing_and_stale_report(self):
        title = 'Parser: "quoted" # heading'
        old = ledger.render(ledger.reconcile(review("### CR-01: " + title), "", []), "01", "old")
        self.assertEqual(ledger.prior_rows(old)[1]["CR-01"], title)
        result = ledger.reconcile(review("### CR-01: Parser   fails"), old,
                                  [("new.md", "## Fixed Issues\n### CR-01: Parser fails")])
        self.assertEqual(result["rows"][0]["disposition"], "fixed")
        stale = ledger.reconcile(review("### CR-01: New"), old, [("old.md", "## Fixed Issues\n### CR-01: Old")])
        self.assertEqual(stale["stale_fix"], ["CR-01"])
        self.assertEqual(stale["open"], 1)

    def test_every_pass_first_outcome_and_applied_beats_deferred(self):
        initial = ledger.render(ledger.reconcile(review("### CR-01: One"), "", []), "01", "old")
        initial = initial.replace("| open | - |", "| deferred | waiting on A | B || C |")
        result = ledger.reconcile(review("### CR-01: One"), initial,
                                 [("final.md", "## Skipped Issues\n### CR-01: One"),
                                  ("iter2.md", "## Fixed Issues\n### CR-01: One\n### WR-02: Two"),
                                  ("iter1.md", "## Fixed Issues\n### IN-03: Three")])
        self.assertEqual([r["disposition"] for r in result["rows"]], ["skipped", "fixed", "fixed"])
        self.assertTrue(result["rows"][1]["carried"])
        preserved = ledger.render(ledger.reconcile("", initial, []), "01", "new")
        self.assertIn(r"waiting on A \| B \|\| C", preserved)
        again = ledger.render(ledger.reconcile("", preserved, []), "01", "new")
        self.assertEqual(preserved, again)

    def test_section_severity_carries_then_reused_id_resets(self):
        old = ledger.render(ledger.reconcile(review("## Critical Issues\n### WR-04: Old"), "", []), "01", "old")
        carried = ledger.reconcile("", old, [])
        self.assertEqual(carried["rows"][0]["severity"], "critical")
        self.assertEqual(carried["rows"][0]["disposition"], "open")
        self.assertEqual(ledger.reconcile(review("### WR-04: New"), old, [])["rows"][0]["severity"], "warning")

    def test_foreign_fences_and_whole_sections(self):
        body = "```md\n~~~\n### CR-99: Example\n```\n## Warnings\n### WR-01: Real"
        result = ledger.reconcile(review(body), "", [("fix.md", "## Fixed Issues Verification\n### WR-01: Real")])
        self.assertEqual([r["id"] for r in result["rows"]], ["WR-01"])
        self.assertEqual(result["open"], 1)

    def test_partial_and_total_unparsed_findings(self):
        self.assertEqual(ledger.reconcile(review("### CR-01: One", 3), "", [])["unparsed"], 2)
        self.assertEqual(ledger.reconcile(review("#### X-01: Unknown", 3), "", [])["unparsed"], 3)

    def test_frontmatter_closed_mapping_scoped_ascii_and_consistent(self):
        text = "---\nstatus: clean:junk\ntotal: 100\nfindings:\n  blocker: 08\n  warning: 00\n  info: 00\n  total: 08\n---\ntotal: 99"
        status, counts, valid = ledger.review_metadata(text)
        self.assertEqual(status, "clean:junk")
        self.assertEqual(counts["total"], 8)
        self.assertTrue(valid)
        self.assertFalse(ledger.review_metadata(text.replace("total: 08", "total: 1 0"))[2])
        self.assertEqual(ledger.review_metadata(text.replace("---\ntotal: 99", "total: 99"))[1], {})
        self.assertEqual(ledger.review_metadata("---\nstatus: clean\u2003\n---")[0], "clean\u2003")

    def test_invalid_prior_enum_cannot_hide_open(self):
        old = "| CR-01 | critical | opne | typo |"
        self.assertEqual(ledger.reconcile(review("### CR-01: One"), old, [])["open"], 1)

    def test_legacy_unknown_title_inherits_but_known_empty_does_not(self):
        old = "| CR-01 | critical | deferred | documented reason |"
        result = ledger.reconcile(review("### CR-01: New"), old, [])
        self.assertEqual(result["rows"][0]["disposition"], "deferred")
        self.assertEqual(result["rows"][0]["source"], "documented reason")

    def test_carried_marker_removed_when_finding_reappears(self):
        old = ledger.render(ledger.reconcile(review("### CR-01: One"), "", []), "01", "old")
        carried = ledger.render(ledger.reconcile("", old, []), "01", "old")
        self.assertIn(ledger.MARK, carried)
        current = ledger.render(ledger.reconcile(review("### CR-01: One"), carried, []), "01", "old")
        self.assertNotIn(ledger.MARK, current)

    def test_pipe_escape_parity(self):
        self.assertEqual(ledger.escape_pipes(r"A||B\\|C\|D"), r"A\|\|B\\\|C\|D")

    def test_phase_string_axes_and_rejections(self):
        self.assertEqual(ledger.phase_name("0008A.1.2.3"), "0008A.1.2.3")
        self.assertEqual(ledger.phase_name("3A.1.2"), "03A.1.2")
        for value in ("", "../1", "1..2", "23.1A", "23AB", "123456789", "1." + ".".join(["12345678"] * 30)):
            with self.assertRaises(ValueError):
                ledger.phase_name(value)


class LedgerFiles(unittest.TestCase):
    def test_zero_parsed_declared_total_still_writes_ledger(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            (base / "03A.1-REVIEW.md").write_text(review("#### XX-01: Unknown", 2), encoding="utf-8")
            with patch.object(ledger, "root", return_value=base):
                result = ledger.record(Args(["--phase", "3A.1", "--phase-dir", str(base)]))
            self.assertEqual(result["status"], "recorded")
            self.assertEqual(result["total"], 0)
            self.assertIn("unparsed: 2", Path(result["path"]).read_text(encoding="utf-8"))

    def test_all_passes_consumed_timestamp_stable_and_no_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            directory = base / "phase"
            directory.mkdir()
            (directory / "01-REVIEW.md").write_text(review("", 0), encoding="utf-8")
            for name, ident in (("01-REVIEW-FIX.iter2.md", "CR-02"), ("01-REVIEW-FIX.iter10.md", "CR-10"), ("01-REVIEW-FIX.md", "CR-11")):
                (directory / name).write_text("## Fixed Issues\n### " + ident + ": Fixed", encoding="utf-8")
            args = Args(["--phase", "1", "--phase-dir", str(directory)])
            with patch.object(ledger, "root", return_value=base), patch.object(ledger, "now", return_value="first"):
                result = ledger.record(args)
                self.assertEqual(result["status"], "recorded")
                self.assertEqual([r["id"] for r in result["rows"]], ["CR-11", "CR-10", "CR-02"])
                self.assertEqual(len(result["consumed_passes"]), 3)
                path = Path(result["path"])
                before = path.read_bytes()
                with patch.object(ledger, "now", return_value="second"):
                    self.assertEqual(ledger.record(args)["status"], "unchanged")
                self.assertEqual(path.read_bytes(), before)
                self.assertEqual(len(list(directory.glob("*-FIX*.md"))), 3)
                mismatch = ledger.record(Args(["--phase", "1", "--phase-dir", str(directory), "--review-digest", "wrong"]))
                self.assertTrue(mismatch["retain_fix_passes"])

    def test_symlink_ledger_is_advisory_and_target_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            outside = base / "outside.md"
            outside.write_text("untouched", encoding="utf-8")
            target = base / "01-REVIEW-DISPOSITION.md"
            try:
                target.symlink_to(outside)
            except OSError:
                self.skipTest("host does not permit fixture symlinks")
            with patch.object(ledger, "root", return_value=base):
                result = ledger.record(Args(["--phase", "1", "--phase-dir", str(base)]))
            self.assertEqual(result["status"], "skipped")
            self.assertFalse(result["waiver"])
            self.assertEqual(outside.read_text(encoding="utf-8"), "untouched")


if __name__ == "__main__":
    unittest.main()
