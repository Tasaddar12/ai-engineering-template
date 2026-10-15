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
CHECKLIST_FIELDS = ("Entry identity", "Canonical risk key", "Aliases / occurrences", "PLAN / Threat ID",
                    "Owner", "Scope / acceptance", "Assessment / uncertainty", "Lifecycle / outcome",
                    "Next action", "Revision / check evidence", "Canonical reference")

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


def checklist_errors(root):
    canonical = (root / CANONICAL).read_text(encoding="utf-8")
    routing = section(canonical, "### Planned checklist and unplanned routing")
    normalized = " ".join(routing.split())
    errors = []
    if CHECKLIST_FIELDS not in table_headers(routing):
        errors.append("checklist entry fields")
    duties = {
        "existing tracker reuse": ("Existing actionable matching trackers remain canonical",
                                  "without duplicating or replacing their identities",
                                  "Closed unresolved matches retain the reopening-authority blocker"),
        "planned canonical identity": ("stable canonical risk keys and aliases across reruns",
                                       "distinct entries in one phase security checklist issue",
                                       "Verify that each entry URL actually addresses that risk"),
        "register separation": ("never a combined PLAN register", "full six-column register in its owning PLAN",
                                "SUMMARY/PR linked outcomes separate"),
        "standalone unplanned": ("distinct unplanned threat discovered during execution or review",
                                 "actionable standalone Security risk issue, or an existing full-scope matching issue",
                                 "checklist-only entry cannot replace standalone tracking",
                                 "owning PLAN and the phase checklist"),
        "mandatory safe reconciliation": ("safe separate review, serialized writes, template validation, readback and uncertain-create recovery",
                                           "Never route threats through TODO publication",
                                           "resolved-problem exemption never waives this reconciliation"),
        "checked is not closed": ("checked checklist item requires individual outcome evidence",
                                  "does not mean issue closure", "scope-complete evidence for every included risk",
                                  "existing explicit closure authority"),
    }
    for label, phrases in duties.items():
        if not all(phrase in normalized for phrase in phrases):
            errors.append(label)
    template = (root / ".ai/templates/issue.md").read_text(encoding="utf-8").split(
        "### Security risk\n", 1)[1].split("### UAT\n", 1)[0]
    if not all(phrase in " ".join(template.split()) for phrase in (
            "same Security risk variant", "keep every required heading", "individually addressable entry",
            "Existing actionable matching issues remain canonical", "Distinct unplanned threats require standalone",
            "do not authorize issue closure")):
        errors.append("Security risk template routing")
    for name, step, phrases in (
        (".ai/workflows/plan-phase.md", "handle_preparer_return",
         ("existing matching tracker", "planned phase security checklist entry", "stable key, aliases", "six-column register")),
        (".ai/workflows/execute-phase.md", "aggregate_results",
         ("existing actionable matching trackers", "distinct canonical entries", "standalone actionable Security risk issues")),
        (".ai/workflows/execute-phase.md", "review_phase_issues",
         ("canonical-threat-tracking", "standalone distinct unplanned risks", "closure authority")),
    ):
        body = " ".join(steps((root / name).read_text(encoding="utf-8")).get(step, "").split())
        if not all(phrase in body for phrase in phrases):
            errors.append(step + ": routing hook")
    return errors


def issue_audit_errors(root):
    canonical = (root / CANONICAL).read_text(encoding="utf-8")
    if "## Issue-link audit\n" not in canonical:
        return ["canonical audit heading"]
    audit = " ".join(section(canonical, "## Issue-link audit").split())
    errors = []
    duties = {
        "independent semantic scope": ("fresh independent reviewer/verifier", "must not be the author",
                                       "CONTEXT acceptance", "every PLAN threat/checklist identity", "SUMMARY outcomes",
                                       "Ordinary linked follow-ups", "structural `issue.validate` success does not prove it"),
        "audit tracking scope": ("Actionable link destination and full scope/acceptance", "omitted or duplicate tracking",
                                 "planned-checklist coverage", "separate standalone tracking for distinct unplanned risks",
                                 "safe destination visibility"),
        "audit closure authority": ("Neutral versus closing references", "GitLab neutral-link policy",
                                    "scope-complete resolution evidence", "existing explicit closure authority",
                                    "Never infer closure from merge, checked checklist items or accepted/deferred status"),
        "audit evidence packet": ("reviewed source revision", "PR/MR body/link snapshot", "verified URLs",
                                  "provider readback evidence", "observed state and when it was read",
                                  "unresolved findings/dependencies", "unverifiable link is a gap with a dependency, never a pass"),
        "audit currentness": ("Material changes to links, body, risk outcomes or source invalidate the affected audit",
                              "fresh applicable independent evidence before claiming ready", "verification-evidence.md#coordinator-currentness-check",
                              "Before merge, require the current independent audit and last provider readback",
                              "no new merge or issue closure authority"),
    }
    for label, phrases in duties.items():
        if not all(phrase in audit for phrase in phrases):
            errors.append(label)
    anchor = "../references/git-workflow.md#issue-link-audit"
    for name, step in (
        (".ai/workflows/execute-phase.md", "code_review_gate"),
        (".ai/workflows/execute-phase.md", "review_phase_issues"),
        (".ai/workflows/ship.md", "preflight_checks"),
        (".ai/workflows/ship.md", "generate_pr_body"),
        (".ai/workflows/ship.md", "create_pr"),
        (".ai/workflows/ship.md", "merge_and_close"),
    ):
        if anchor not in steps((root / name).read_text(encoding="utf-8")).get(step, ""):
            errors.append(step + ": audit hook")
    verifier = (root / ".ai/agents/verifier.md").read_text(encoding="utf-8")
    context = verifier.split("## Step 1: Load Context", 1)[1].split("## Step 2:", 1)[0]
    if anchor not in context:
        errors.append("verifier: independent audit hook")
    review = steps((root / ".ai/workflows/execute-phase.md").read_text(encoding="utf-8"))["code_review_gate"]
    prompt = re.search(r'Agent\(\s+prompt="(.*?)",\s+subagent_type="code-reviewer"', review, re.S).group(1)
    if anchor not in prompt or "body/link snapshot" not in prompt or "actual provider" not in prompt:
        errors.append("reviewer assignment: audit packet")
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

    def test_planned_checklist_real_structure_and_each_field_mutation(self):
        self.assertEqual([], checklist_errors(ROOT))
        for field in CHECKLIST_FIELDS:
            with self.subTest(field=field):
                root = self.fixture()
                path = root / CANONICAL
                text = path.read_text(encoding="utf-8")
                routing = section(text, "### Planned checklist and unplanned routing")
                path.write_text(text.replace(routing, routing.replace("| " + field + " |", "| Removed |", 1), 1), encoding="utf-8")
                self.assertIn("checklist entry fields", checklist_errors(root))

    def test_planned_unplanned_routing_duties_and_mutations(self):
        cases = (
            ("Existing actionable matching trackers remain canonical", "existing tracker reuse"),
            ("Closed unresolved matches retain the reopening-authority blocker", "existing tracker reuse"),
            ("stable canonical risk keys and aliases across reruns", "planned canonical identity"),
            ("Verify that each entry URL actually addresses that risk", "planned canonical identity"),
            ("never a combined PLAN register", "register separation"),
            ("checklist-only entry cannot replace standalone tracking", "standalone unplanned"),
            ("resolved-problem exemption never waives this reconciliation", "mandatory safe reconciliation"),
            ("checked checklist item requires individual outcome evidence", "checked is not closed"),
            ("scope-complete evidence for every included risk", "checked is not closed"),
        )
        for phrase, error in cases:
            with self.subTest(duty=error):
                root = self.fixture()
                path = root / CANONICAL
                text = path.read_text(encoding="utf-8")
                pattern = r"\s+".join(re.escape(word) for word in phrase.split())
                self.assertRegex(text, pattern)
                path.write_text(re.sub(pattern, "Removed", text, count=1), encoding="utf-8")
                self.assertIn(error, checklist_errors(root))

    def test_routing_stays_in_mandatory_real_steps(self):
        for name, step, phrase in (
            (".ai/workflows/plan-phase.md", "handle_preparer_return", "planned phase security checklist entry"),
            (".ai/workflows/execute-phase.md", "aggregate_results", "standalone actionable Security risk issues"),
            (".ai/workflows/execute-phase.md", "review_phase_issues", "standalone distinct unplanned risks"),
        ):
            with self.subTest(step=step):
                root = self.fixture()
                self.mutate(root, name, phrase, "Removed")
                self.assertIn(step + ": routing hook", checklist_errors(root))

    def test_security_risk_template_preserves_canonical_routing(self):
        root = self.fixture()
        self.mutate(root, ".ai/templates/issue.md", "Existing actionable matching issues remain canonical", "Removed")
        self.assertIn("Security risk template routing", checklist_errors(root))

    def test_independent_audit_real_scope_packet_and_currentness(self):
        self.assertEqual([], issue_audit_errors(ROOT))

    def test_independent_audit_duty_mutations(self):
        cases = (
            ("fresh independent reviewer/verifier", "independent semantic scope"),
            ("Ordinary linked follow-ups", "independent semantic scope"),
            ("structural `issue.validate` success does not prove it", "independent semantic scope"),
            ("planned-checklist coverage", "audit tracking scope"),
            ("separate standalone tracking for distinct unplanned risks", "audit tracking scope"),
            ("Neutral versus closing references", "audit closure authority"),
            ("existing explicit closure authority", "audit closure authority"),
            ("unverifiable link is a gap with a dependency, never a pass", "audit evidence packet"),
            ("PR/MR body/link snapshot", "audit evidence packet"),
            ("Material changes to links, body, risk outcomes or source invalidate the affected audit", "audit currentness"),
            ("Before merge, require the current independent audit and last provider readback", "audit currentness"),
        )
        for phrase, error in cases:
            with self.subTest(duty=error):
                root = self.fixture()
                path = root / CANONICAL
                text = path.read_text(encoding="utf-8")
                audit = section(text, "## Issue-link audit")
                pattern = r"\s+".join(re.escape(word) for word in phrase.split())
                self.assertRegex(audit, pattern)
                path.write_text(text.replace(audit, re.sub(pattern, "Removed", audit, count=1), 1), encoding="utf-8")
                self.assertIn(error, issue_audit_errors(root))

    def test_each_actual_audit_step_and_verifier_hook_is_required(self):
        anchor = "../references/git-workflow.md#issue-link-audit"
        for name, step in (
            (".ai/workflows/execute-phase.md", "code_review_gate"),
            (".ai/workflows/execute-phase.md", "review_phase_issues"),
            (".ai/workflows/ship.md", "preflight_checks"),
            (".ai/workflows/ship.md", "generate_pr_body"),
            (".ai/workflows/ship.md", "create_pr"),
            (".ai/workflows/ship.md", "merge_and_close"),
        ):
            with self.subTest(step=step):
                root = self.fixture()
                path = root / name
                text = path.read_text(encoding="utf-8")
                body = steps(text)[step]
                path.write_text(text.replace(body, body.replace(anchor, "missing.md"), 1), encoding="utf-8")
                self.assertIn(step + ": audit hook", issue_audit_errors(root))
        root = self.fixture()
        self.mutate(root, ".ai/agents/verifier.md", anchor, "missing.md")
        self.assertIn("verifier: independent audit hook", issue_audit_errors(root))

    def test_audit_heading_and_reviewer_prompt_cannot_be_replaced_by_guidance(self):
        root = self.fixture()
        self.mutate(root, CANONICAL, "## Issue-link audit", "## Removed audit")
        self.assertIn("canonical audit heading", issue_audit_errors(root))
        root = self.fixture()
        name = ".ai/workflows/execute-phase.md"
        path = root / name
        text = path.read_text(encoding="utf-8")
        old = "[Issue-link audit](../references/git-workflow.md#issue-link-audit)"
        self.assertIn(old, text)
        path.write_text(text.replace(old, "Removed reviewer audit", 1), encoding="utf-8")
        self.assertIn("reviewer assignment: audit packet", issue_audit_errors(root))

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
