"""Consolidated issue format and writer links."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".ai/runtime"))
from lib import issue_format
from test_threat_tracking_contract import CHECKLIST_FIELDS, CHECKLIST_LINK, section, steps

WRITERS = (
    (".ai/workflows/plan-phase.md", "handle_preparer_return"),
    (".ai/workflows/execute-phase.md", "aggregate_results"),
    (".ai/workflows/quick.md", "reconcile_plan_threats"),
    (".ai/workflows/quick.md", "reconcile_summary_threats"),
    (".ai/workflows/ship.md", "preflight_checks"),
)
READERS = (
    ".ai/agents/phase-preparer.md", ".ai/agents/phase-checker.md",
    ".ai/agents/verifier.md", ".ai/runtime/TEMPLATE-CONTRACT.md",
)


class ConsolidatedSecurityFormat(unittest.TestCase):
    def test_template_and_filled_example_use_canonical_columns_and_tasks(self):
        text = (ROOT / ".ai/templates/issue.md").read_text(encoding="utf-8")
        template = section(text, "#### Consolidated security checklist")
        blocks = re.findall(r"^```markdown\n(.*?)^```", template, re.M | re.S)
        self.assertEqual(2, len(blocks))
        for block in blocks:
            with self.subTest(block=block[:45]):
                rows = [issue_format.cells(line) for line in block.splitlines()
                        if issue_format.cells(line)]
                self.assertEqual(CHECKLIST_FIELDS, tuple(rows[0]))
                self.assertTrue(issue_format.separator(rows[1]))
                self.assertEqual(3, len(rows))
                self.assertEqual(7, len(rows[2]))
                self.assertTrue(all(rows[2]))
                self.assertIn("### " + rows[2][0] + "\n\n- [ ] Remediation verified", block)

    def test_writers_and_reviewers_link_to_canonical_template(self):
        for name, step in WRITERS:
            with self.subTest(name=name, step=step):
                text = steps((ROOT / name).read_text(encoding="utf-8"))[step]
                self.assertIn(CHECKLIST_LINK, text)
        for name in READERS:
            with self.subTest(name=name):
                self.assertIn(CHECKLIST_LINK, (ROOT / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
