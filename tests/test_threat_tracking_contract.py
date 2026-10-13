"""Offline artifact/step checks; no claim of provider side effects."""
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ".ai/references/git-workflow.md"
PRODUCERS = (
    ".ai/templates/phase-prompt.md", ".ai/templates/summary.md",
    ".ai/templates/issue.md", ".ai/templates/pull-request.md",
    ".ai/agents/phase-preparer.md", ".ai/agents/coder.md",
    ".ai/agents/phase-checker.md", ".ai/agents/verifier.md",
    ".ai/workflows/plan-phase.md", ".ai/workflows/execute-phase.md",
    ".ai/workflows/quick.md", ".ai/workflows/ship.md",
    ".ai/runtime/TEMPLATE-CONTRACT.md",
)
PATHS = (CANONICAL,) + PRODUCERS
REGISTER_FIELDS = (
    "Threat ID / risk key and source aliases", "Category", "Component/scope",
    "Severity and assessment", "Disposition", "Mitigation/task/check",
    "Owner", "Status", "Canonical issue", "Resolution evidence",
)
PR_FIELDS = ("Threat ID / risk key", "Severity", "Status", "Canonical issue",
             "Safe mitigation / resolution evidence")


def file_template(text):
    """Select the actual artifact block, excluding guidance/examples."""
    region = text.split("## File Template\n", 1)[1]
    fence = chr(96) * 3
    return re.search("^" + fence + "markdown\n(.*?)^" + fence,
                     region, re.M | re.S).group(1)


def section(text, title):
    return re.search(r"^" + re.escape(title) + r"\n(.*?)(?=^## |\Z)",
                     text, re.M | re.S).group(1)


def steps(text):
    return dict(re.findall(r'^<step name="([^"]+)">\n(.*?)^</step>',
                           text, re.M | re.S))


def table_headers(text):
    return [tuple(cell.strip() for cell in line.strip("|").split("|"))
            for line in text.splitlines() if line.startswith("| Threat ID")]


def reaches_canonical(root, source):
    """Follow actual local Markdown links with bounded traversal."""
    queue, seen = [source], set()
    while queue:
        name = queue.pop()
        if name == CANONICAL:
            return True
        if name in seen:
            continue
        seen.add(name)
        path = root / name
        if not path.is_file():
            continue
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)",
                                 path.read_text(encoding="utf-8")):
            target = unquote(target.split("#", 1)[0].strip("<>"))
            if not target or re.match(r"[a-zA-Z][\w+.-]*:", target):
                continue
            next_path = (path.parent / target).resolve()
            if next_path.is_relative_to(root.resolve()):
                queue.append(next_path.relative_to(root.resolve()).as_posix())
    return False


def contract_errors(root):
    errors = []
    content = {name: (root / name).read_text(encoding="utf-8") for name in PATHS}
    for name, marker in ((".ai/templates/phase-prompt.md", "<threat_model>"),
                         (".ai/templates/summary.md", "## Threat Flags")):
        block = file_template(content[name])
        if marker not in block or REGISTER_FIELDS not in table_headers(block):
            errors.append(name + ": missing artifact threat fields")
    pr = section(file_template(content[".ai/templates/pull-request.md"]), "## Risks or rollback")
    if PR_FIELDS not in table_headers(pr):
        errors.append("PR: missing lifecycle table")
    for name in PRODUCERS:
        if not reaches_canonical(root, name):
            errors.append(name + ": canonical procedure unreachable")
    required = (
        (".ai/workflows/plan-phase.md", "handle_preparer_return"),
        (".ai/workflows/execute-phase.md", "aggregate_results"),
        (".ai/workflows/quick.md", "reconcile_plan_threats"),
        (".ai/workflows/quick.md", "reconcile_summary_threats"),
        (".ai/workflows/ship.md", "preflight_checks"),
        (".ai/workflows/ship.md", "generate_pr_body"),
        (".ai/workflows/ship.md", "merge_and_close"),
    )
    for name, step in required:
        body = steps(content[name]).get(step, "")
        if "git-workflow.md#canonical-threat-tracking" not in body:
            errors.append(name + ":" + step + ": mandatory tracking missing")
        if re.search(r"^\*\*Only when", body, re.M):
            errors.append(name + ":" + step + ": tracking made optional")
    quick_order = list(steps(content[".ai/workflows/quick.md"]))
    for before, after in (("plan", "reconcile_plan_threats"),
                          ("reconcile_plan_threats", "check_plan"),
                          ("execute", "reconcile_summary_threats"),
                          ("reconcile_summary_threats", "verify")):
        if before not in quick_order or after not in quick_order or (
                quick_order.index(before) >= quick_order.index(after)):
            errors.append("quick: mandatory reconciliation order")
    return errors


class ThreatTrackingContract(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for name in PATHS:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((ROOT / name).read_text(encoding="utf-8"), encoding="utf-8")
        return root

    def mutate(self, root, name, old, new):
        path = root / name
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def test_real_file_templates_and_mandatory_workflow_seams(self):
        self.assertEqual([], contract_errors(ROOT))

    def test_guidance_example_cannot_replace_artifact_carry_forward_fields(self):
        root = self.fixture()
        self.mutate(root, ".ai/templates/summary.md",
                    "| Canonical issue |", "| External reference |")
        path = root / ".ai/templates/summary.md"
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n" + " | ".join(REGISTER_FIELDS) + "\n")
        self.assertIn(".ai/templates/summary.md: missing artifact threat fields",
                      contract_errors(root))

    def test_missing_alias_or_evidence_in_plan_is_detected(self):
        for field in ("Threat ID / risk key and source aliases", "Resolution evidence"):
            with self.subTest(field=field):
                root = self.fixture()
                self.mutate(root, ".ai/templates/phase-prompt.md", field, "Removed field")
                self.assertIn(".ai/templates/phase-prompt.md: missing artifact threat fields",
                              contract_errors(root))

    def test_missing_pr_status_is_detected(self):
        root = self.fixture()
        self.mutate(root, ".ai/templates/pull-request.md", "| Status |", "| State note |")
        self.assertIn("PR: missing lifecycle table", contract_errors(root))

    def test_optional_only_quick_tracking_is_detected(self):
        for required, optional in (("reconcile_plan_threats", "check_plan"),
                                   ("reconcile_summary_threats", "verify")):
            with self.subTest(required=required):
                root = self.fixture()
                path = root / ".ai/workflows/quick.md"
                text = path.read_text(encoding="utf-8")
                match = re.search(r'^<step name="' + required + r'">\n(.*?)^</step>\n',
                                  text, re.M | re.S)
                hook = match.group(1)
                text = text.replace(match.group(0), "", 1)
                text = text.replace('<step name="' + optional + '">\n',
                                    '<step name="' + optional + '">\n' + hook, 1)
                path.write_text(text, encoding="utf-8")
                self.assertTrue(any(required + ": mandatory tracking missing" in error
                                    for error in contract_errors(root)))

    def test_existing_hook_made_conditional_is_detected(self):
        root = self.fixture()
        self.mutate(root, ".ai/workflows/quick.md",
                    '<step name="reconcile_summary_threats">\n',
                    '<step name="reconcile_summary_threats">\n'
                    '**Only when VALIDATE_MODE is true.**\n')
        self.assertTrue(any("tracking made optional" in error for error in contract_errors(root)))

    def test_removed_coordinator_phase_hook_is_detected(self):
        root = self.fixture()
        self.mutate(root, ".ai/workflows/execute-phase.md",
                    "git-workflow.md#canonical-threat-tracking", "missing-procedure.md")
        self.assertTrue(any("aggregate_results: mandatory tracking missing" in error
                            for error in contract_errors(root)))

    def test_producer_link_loss_is_detected(self):
        root = self.fixture()
        name = ".ai/templates/phase-prompt.md"
        self.mutate(root, name, "git-workflow.md#canonical-threat-tracking", "missing.md")
        self.assertIn(name + ": canonical procedure unreachable", contract_errors(root))


if __name__ == "__main__":
    unittest.main()
