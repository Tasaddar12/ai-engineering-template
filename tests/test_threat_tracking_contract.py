"""Offline artifact/step checks; provider semantics still require review."""
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
PLAN_FIELDS = ("Threat ID", "Category", "Component", "Severity", "Disposition", "Mitigation Plan")
FLAG_FIELDS = ("Flag", "File", "Description")
OUTCOME_FIELDS = ("PLAN / Threat ID", "Canonical issue", "Outcome", "Git state", "Evidence")

# Exact base blocks embedded for shallow/offline CI; no Git subprocess in tests.
RESTORED_BLOCKS = (
    ('coder task reference', '.ai/agents/coder.md', "**Threat model reference:** Before starting each task, check if the plan's `<threat_model>` assigns `mitigate` dispositions to this task's files. Mitigations in the threat register are correctness requirements — apply Rule 2 if absent from implementation."),
    ('coder conditional discovery', '.ai/agents/coder.md', "**Threat surface scan:** Before writing the SUMMARY, check if any files created/modified introduce security-relevant surface NOT in the plan's `<threat_model>` — new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries. If found, add:\n\n```markdown\n## Threat Flags\n\n| Flag | File | Description |\n|------|------|-------------|\n| threat_flag: {type} | {file} | {new surface description} |\n```\n\nOmit section if nothing found.\n"),
    ('preparer original threat model', '.ai/agents/phase-preparer.md', '<threat_model>\n## Trust Boundaries\n\n| Boundary | Description |\n|----------|-------------|\n| {e.g., client→API} | {untrusted input crosses here} |\n\n## STRIDE Threat Register\n\n| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |\n|-----------|----------|-----------|----------|-------------|-----------------|\n| T-{phase}-01 | {S/T/R/I/D/E} | {function/endpoint/file} | {critical\\|high\\|medium\\|low} | mitigate | {specific mitigation action} |\n| T-{phase}-02 | {category} | {component} | low | accept | {rationale for acceptance} |\n| T-{phase}-SC | Tampering | dependency installation | high | mitigate | verify exact package identity/version and project-approved source |\n</threat_model>'),
    ('preparer non-applicability', '.ai/agents/phase-preparer.md', 'When none of those triggers applies, state `Security review: not applicable`\nwith the exact unchanged boundary or documentation/configuration-only scope in\nthe PLAN verification section. The independent checker must reject a triggered\nPLAN with a missing register or disposition. These are mandatory preparation\nchecks, not a claim that the Python runtime performs threat analysis.\n\n'),
    ('preparer Severity checklist', '.ai/agents/phase-preparer.md', '- [ ] Every threat has a Severity (critical|high|medium|low)'),
    ('checker complete Dimension 7d', '.ai/agents/phase-checker.md', "## Dimension 7d: Security Planning Gate\n\nBefore accepting task verification, apply the preparer's\n[Security planning gate](phase-preparer.md#security-planning-gate) to each PLAN.\nA changed authentication, authorization, secret-handling, isolation or untrusted\ninput boundary requires the named threat register, dispositions and mitigation\nverification commands. Missing required entries are BLOCKER findings. A PLAN\nwith no trigger must state its concrete non-applicability reason. Do not infer\nan unavailable `security_enforcement` setting or treat an absent setting as an\nexemption.\n\n"),
)


def file_template(text):
    """Read the real artifact, excluding other examples and guidance."""
    region = text.split("## File Template\n", 1)[1]
    fence = chr(96) * 3
    return re.search("^" + fence + "markdown\n(.*?)^" + fence, region, re.M | re.S).group(1)


def section(text, title):
    depth = len(title.split(" ", 1)[0])
    return re.search(r"^" + re.escape(title) + r"\n(.*?)(?=^#{1," + str(depth) +
                     r"}\s|\Z)", text, re.M | re.S).group(1)


def steps(text):
    return dict(re.findall(r'^<step name="([^"]+)">\n(.*?)^</step>', text, re.M | re.S))


def table_headers(text):
    return [tuple(cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip("|")))
            for line in text.splitlines() if line.startswith("| ")]


def reaches_canonical(root, source):
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
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", path.read_text(encoding="utf-8")):
            target = unquote(target.split("#", 1)[0].strip("<>"))
            if not target or re.match(r"[a-zA-Z][\w+.-]*:", target):
                continue
            next_path = (path.parent / target).resolve()
            if next_path.is_relative_to(root.resolve()):
                queue.append(next_path.relative_to(root.resolve()).as_posix())
    return False


def restoration_errors(content):
    return [label + ": original block changed" for label, name, original in RESTORED_BLOCKS
            if original not in content[name]]


def contract_errors(root):
    content = {name: (root / name).read_text(encoding="utf-8") for name in PATHS}
    errors = restoration_errors(content)
    plan = file_template(content[".ai/templates/phase-prompt.md"])
    if "<threat_model>" not in plan or PLAN_FIELDS not in table_headers(plan):
        errors.append("PLAN: missing six-column register")
    if "[Threat ID](verified canonical issue URL), or ID + Pending: dependency" not in plan:
        errors.append("PLAN: missing local ID issue link/Pending")
    summary = file_template(content[".ai/templates/summary.md"])
    flags = section(summary, "## Threat Flags")
    if FLAG_FIELDS not in table_headers(flags) or "omit this section if nothing found" not in flags:
        errors.append("SUMMARY: missing conditional discovery schema")
    for label, artifact in (("SUMMARY", summary), ("PR", file_template(content[".ai/templates/pull-request.md"]))):
        if OUTCOME_FIELDS not in table_headers(artifact):
            errors.append(label + ": missing linked outcome table")
        if PLAN_FIELDS in table_headers(artifact):
            errors.append(label + ": duplicated PLAN register")
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
    order = list(steps(content[".ai/workflows/quick.md"]))
    for before, after in (("plan", "reconcile_plan_threats"), ("reconcile_plan_threats", "check_plan"),
                          ("execute", "reconcile_summary_threats"), ("reconcile_summary_threats", "verify")):
        if before not in order or after not in order or order.index(before) >= order.index(after):
            errors.append("quick: mandatory reconciliation order")
    return errors


def review_obligation_errors(text):
    """Check a small set of declared duties, without simulating a provider."""
    canonical = section(text, "## Canonical threat tracking")
    normalized = " ".join(canonical.split())
    duties = {
        "per-PLAN ownership": ("respective PLAN's existing six-column register", "Do not relocate or collapse PLAN content"),
        "identity/aliases": ("stable canonical risk key", "source aliases/occurrences"),
        "closed-match review": ("open and closed issues", "semantic scope", "matching resolution evidence", "reopening authority"),
        "uncertain-create recovery": ("uncertain creation", "exact reviewed intent and key before retrying"),
        "safe reporting": ("without private-channel approval", "Missing private access blocks only", "destination visibility"),
        "evidence-based closure": ("neutral issue links", "existing explicit closure authority", "Never label accepted/deferred as resolved or infer closure from merge"),
        "provider fallback": ("GitHub-only", "verified authorized host tool", "otherwise retain Pending/publication blocker"),
    }
    return [label for label, phrases in duties.items() if not all(p in normalized for p in phrases)]


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

    def test_real_artifacts_and_mandatory_workflow_seams(self):
        self.assertEqual([], contract_errors(ROOT))

    def test_original_blocks_and_each_mutation(self):
        content = {name: (ROOT / name).read_text(encoding="utf-8") for name in PATHS}
        self.assertEqual([], restoration_errors(content))
        for label, name, original in RESTORED_BLOCKS:
            with self.subTest(block=label):
                changed = dict(content)
                changed[name] = changed[name].replace(original, "Removed original block", 1)
                self.assertIn(label + ": original block changed", restoration_errors(changed))

    def test_plan_six_columns_and_local_id_links_are_required(self):
        for old, error in (("| Mitigation Plan |", "PLAN: missing six-column register"),
                           ("[Threat ID](verified canonical issue URL), or ID + Pending: dependency",
                            "PLAN: missing local ID issue link/Pending")):
            with self.subTest(field=old):
                root = self.fixture()
                self.mutate(root, ".ai/templates/phase-prompt.md", old, "Removed")
                self.assertIn(error, contract_errors(root))

    def test_discovery_schema_and_conditional_emit_are_required(self):
        for old in ("| Flag | File | Description |", "omit this section if nothing found"):
            with self.subTest(field=old):
                root = self.fixture()
                self.mutate(root, ".ai/templates/summary.md", old, "Removed")
                self.assertIn("SUMMARY: missing conditional discovery schema", contract_errors(root))

    def test_guidance_cannot_replace_real_artifact_outcomes(self):
        for name, label in ((".ai/templates/summary.md", "SUMMARY"), (".ai/templates/pull-request.md", "PR")):
            with self.subTest(artifact=label):
                root = self.fixture()
                self.mutate(root, name, "| Canonical issue |", "| Removed |")
                with (root / name).open("a", encoding="utf-8") as stream:
                    stream.write("\n| " + " | ".join(OUTCOME_FIELDS) + " |\n")
                self.assertIn(label + ": missing linked outcome table", contract_errors(root))

    def test_each_outcome_column_is_required(self):
        for field in OUTCOME_FIELDS:
            with self.subTest(field=field):
                root = self.fixture()
                self.mutate(root, ".ai/templates/summary.md", "| " + field + " |", "| Removed |")
                self.assertIn("SUMMARY: missing linked outcome table", contract_errors(root))

    def test_optional_only_quick_tracking_is_detected(self):
        for required, optional in (("reconcile_plan_threats", "check_plan"), ("reconcile_summary_threats", "verify")):
            with self.subTest(required=required):
                root = self.fixture()
                path = root / ".ai/workflows/quick.md"
                text = path.read_text(encoding="utf-8")
                match = re.search(r'^<step name="' + required + r'">\n(.*?)^</step>\n', text, re.M | re.S)
                text = text.replace(match.group(0), "", 1).replace('<step name="' + optional + '">\n',
                       '<step name="' + optional + '">\n' + match.group(1), 1)
                path.write_text(text, encoding="utf-8")
                self.assertTrue(any(required + ": mandatory tracking missing" in e for e in contract_errors(root)))

    def test_tracking_made_conditional_is_detected(self):
        root = self.fixture()
        self.mutate(root, ".ai/workflows/quick.md", '<step name="reconcile_summary_threats">\n',
                    '<step name="reconcile_summary_threats">\n**Only when VALIDATE_MODE is true.**\n')
        self.assertTrue(any("tracking made optional" in e for e in contract_errors(root)))

    def test_generic_aggregate_results_hook_is_preserved(self):
        root = self.fixture()
        self.mutate(root, ".ai/workflows/execute-phase.md", "git-workflow.md#canonical-threat-tracking", "missing.md")
        self.assertTrue(any("aggregate_results: mandatory tracking missing" in e for e in contract_errors(root)))

    def test_producer_link_loss_is_detected(self):
        root = self.fixture()
        name = ".ai/templates/phase-prompt.md"
        self.mutate(root, name, "git-workflow.md#canonical-threat-tracking", "missing.md")
        self.assertIn(name + ": canonical procedure unreachable", contract_errors(root))

    def test_review_duties_and_mutations(self):
        text = (ROOT / CANONICAL).read_text(encoding="utf-8")
        self.assertEqual([], review_obligation_errors(text))
        for old, expected in (("Do not relocate or collapse PLAN content", "per-PLAN ownership"),
                              ("source aliases/occurrences", "identity/aliases"),
                              ("matching resolution evidence", "closed-match review"),
                              ("exact reviewed intent and key before retrying", "uncertain-create recovery"),
                              ("without private-channel approval", "safe reporting"),
                              ("existing explicit closure authority", "evidence-based closure"),
                              ("otherwise retain Pending/publication blocker", "provider fallback")):
            with self.subTest(duty=expected):
                pattern = r"\s+".join(re.escape(word) for word in old.split())
                self.assertRegex(text, pattern)
                self.assertIn(expected, review_obligation_errors(re.sub(pattern, "Removed", text)))

    def test_summary_outcome_and_git_state_are_independent(self):
        block = file_template((ROOT / ".ai/templates/summary.md").read_text(encoding="utf-8"))
        self.assertIn("never\n  label accepted/deferred resolved or infer closure from merge", block)
        header = "| " + " | ".join(OUTCOME_FIELDS) + " |"
        placeholder = block.split(header + "\n", 1)[1].splitlines()[1]
        records = []
        for outcome, state, evidence in (("unresolved", "open", "Pending secure check"),
                                          ("accepted", "open", "Owner decision, residual risk"),
                                          ("deferred", "open", "Owner, reason, next action"),
                                          ("mitigated", "open", "Revision/check passed; closure Pending"),
                                          ("resolved", "closed", "Revision/check passed; issue readback closed")):
            values = ("[T-P-01](01-01-PLAN.md#stride-threat-register)", "https://example.test/issues/1",
                      outcome, state, evidence)
            filled = block.replace(placeholder, "| " + " | ".join(values) + " |", 1)
            row = filled.split(header + "\n", 1)[1].splitlines()[1]
            records.append(dict(zip(OUTCOME_FIELDS, [c.strip() for c in row.strip("|").split("|")])))
        self.assertTrue(all(r["Git state"] == "open" for r in records[:4]))
        self.assertIn("readback closed", records[4]["Evidence"])
        self.assertTrue(all("PLAN.md#" in r["PLAN / Threat ID"] for r in records))
        self.assertFalse(any("Category" in r or "Mitigation Plan" in r for r in records))


if __name__ == "__main__":
    unittest.main()
