"""Offline authoring contracts, not runtime enforcement or provider/evidence truth."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".ai/runtime"))
from lib import issue_format
from test_threat_tracking_contract import CHECKLIST_FIELDS, CHECKLIST_LINK, section, steps

TEMPLATE = ".ai/templates/issue.md"
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


def consolidated():
    text = (ROOT / TEMPLATE).read_text(encoding="utf-8")
    guidance = section(text, "#### Consolidated security checklist")
    return guidance, re.search(r"^```markdown\n(.*?)^```", guidance, re.M | re.S).group(1)


def shape_errors(body):
    """Check the copyable example's row/heading/task contract, not risk facts."""
    lines = issue_format.visible_lines(body)
    rows = [issue_format.cells(line) for line in lines if issue_format.cells(line)]
    errors = []
    if len(rows) < 3 or tuple(rows[0]) != CHECKLIST_FIELDS or not issue_format.separator(rows[1]):
        return ["table"]
    if any(len(row) != len(CHECKLIST_FIELDS) or not all(row) for row in rows[2:]):
        return ["columns"]
    ids = [row[0] for row in rows[2:]]
    if len(ids) != len(set(ids)):
        errors.append("duplicate risk")
    headings = re.findall(r"^### (.+)$", "\n".join(lines), re.M)
    if ids != headings:
        errors.append("identity")
    pairs = re.findall(r"^### (.+)\n\n- \[[ x]\] Remediation verified(?=\n|$)", body, re.M)
    if pairs != ids:
        errors.append("task pairs")
    tasks = re.findall(r"^- \[[ x]\] (.*)$", "\n".join(lines), re.M)
    if tasks != ["Remediation verified"] * len(ids):
        errors.append("task labels")
    if any(re.search(r"\[[ x]\]", cell) for row in rows for cell in row):
        errors.append("table task")
    return errors


class ConsolidatedSecurityFormat(unittest.TestCase):
    def test_copyable_schema_and_row_task_identity(self):
        _, body = consolidated()
        self.assertEqual([], shape_errors(body))
        self.assertEqual(1, len(re.findall(r"^\|---", body, re.M)))
        self.assertTrue(issue_format.validate(body, "Security risk")["valid"])

    def test_prose_table_drift_and_task_mutations_are_detected(self):
        _, body = consolidated()
        table = re.search(r"^\| Risk ID .*?(?=\n\n)", body, re.M | re.S).group()
        row = table.splitlines()[-1]
        cases = (
            (body.replace(table, "- Risk: action"), "table"),
            (body.replace("| Owner | Status |", "| Status | Owner |"), "table"),
            (body.replace("| [Responsible party] |", "|"), "columns"),
            (body.replace(row, row + "\n" + row), "duplicate risk"),
            (body.replace("### [stable entry ID]", "### Renamed"), "identity"),
            (body.replace("- [ ] Remediation verified", ""), "task pairs"),
            (body.replace("Remediation verified", "#123"), "task labels"),
            (body.replace("| [Responsible party] |", "| - [ ] Owner |"), "table task"),
        )
        for changed, expected in cases:
            with self.subTest(expected=expected):
                self.assertIn(expected, shape_errors(changed))

    def test_multiple_distinct_rows_have_one_matching_task_each(self):
        _, body = consolidated()
        row = next(line for line in body.splitlines() if line.startswith("| [stable entry ID]"))
        pair = "### [stable entry ID]\n\n- [ ] Remediation verified"
        body = body.replace(row, row + "\n" + row.replace("[stable entry ID]", "R-002"))
        body = body.replace(pair, pair + "\n\n" + pair.replace("[stable entry ID]", "R-002"))
        self.assertEqual([], shape_errors(body))
        self.assertEqual([], shape_errors(body.replace("- [ ]", "- [x]", 1)))

    def test_runtime_heading_gate_does_not_claim_layout_or_evidence_enforcement(self):
        _, body = consolidated()
        table = re.search(r"^\| Risk ID .*?(?=\n\n)", body, re.M | re.S).group()
        malformed = body.replace(table, "- This list violates the authoring contract.")
        # Deliberately passes the unchanged runtime. Author/provider review is required.
        for draft in (malformed, body.replace("- [ ]", "- [x]")):
            result = issue_format.validate(draft, "Security risk")
            self.assertTrue(result["valid"])
            self.assertTrue(result["structuralOnly"])

    def test_writers_load_single_canonical_block_at_required_reconciliation(self):
        for name, step in WRITERS:
            with self.subTest(name=name, step=step):
                text = steps((ROOT / name).read_text(encoding="utf-8"))[step]
                self.assertIn(CHECKLIST_LINK, text)
                self.assertIn("ID/task pairs", text)
                self.assertNotIn("| Risk ID |", text)  # No independently drifting schema.
        for name in READERS:
            with self.subTest(name=name):
                self.assertIn(CHECKLIST_LINK, (ROOT / name).read_text(encoding="utf-8"))

    def test_completion_and_provider_limitations_are_explicit(self):
        guidance, _ = consolidated()
        completion = guidance.split("**Completion:**", 1)[1].split("**Identity and reuse:**", 1)[0]
        for required in ("implemented remediation", "bounded acceptance", "matching revision",
                         "actual secure check/result", "accessible evidence", "unchecked",
                         "Planning", "deferral", "transfer", "PR merge", "issue closure",
                         "stale", "uncheck"):
            with self.subTest(required=required):
                self.assertIn(required, completion)
        for required in ("table cells render", "as text", "automatically tick", "disabled boxes",
                         "only", "Remediation verified", "headings/order only",
                         "historical", "never mint a second canonical"):
            with self.subTest(required=required):
                self.assertIn(required, guidance)


if __name__ == "__main__":
    unittest.main()
