"""Offline structural contracts; provider truth requires independent readback."""
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "engineer/references/git-workflow.md"
PRODUCERS = (
    "engineer/templates/phase-prompt.md", "engineer/templates/summary.md",
    "engineer/templates/issue.md", "engineer/templates/pull-request.md",
    "agents/planner.md", "agents/executor.md",
    "agents/plan-checker.md", "agents/verifier.md",
    "agents/code-reviewer.md", "engineer/workflows/plan-phase.md",
    "engineer/workflows/execute-phase.md", "engineer/workflows/verify-work.md",
    "engineer/workflows/quick.md", "engineer/workflows/ship.md",
    "engineer/references/template-contract.md",
)
PATHS = (CANONICAL,) + PRODUCERS
PLAN_FIELDS = ("Threat ID", "Category", "Component", "Severity", "Disposition", "Mitigation Plan")
FLAG_FIELDS = ("Flag", "File", "Description")
OUTCOME_FIELDS = ("PLAN / Threat ID", "Canonical issue", "Outcome", "Git state", "Evidence")
CHECKLIST_FIELDS = ("Entry identity", "Canonical risk key", "Aliases / occurrences", "PLAN / Threat ID",
                    "Owner", "Scope / acceptance", "Assessment / uncertainty", "Lifecycle / outcome",
                    "Next action", "Revision / check evidence", "Canonical reference")
AUDIT_LINK = "../references/git-workflow.md#issue-link-audit"
TRACK_LINK = "git-workflow.md#canonical-threat-tracking"
TRACK_STEPS = (
    ("engineer/workflows/plan-phase.md", "handle_preparer_return"),
    ("engineer/workflows/execute-phase.md", "aggregate_results"),
    ("engineer/workflows/quick.md", "reconcile_plan_threats"),
    ("engineer/workflows/quick.md", "reconcile_summary_threats"),
    ("engineer/workflows/ship.md", "preflight_checks"),
    ("engineer/workflows/ship.md", "generate_pr_body"),
    ("engineer/workflows/ship.md", "merge_and_close"),
)
AUDIT_STEPS = (
    ("engineer/workflows/verify-work.md", "spawn_verifier"),
    ("engineer/workflows/execute-phase.md", "code_review_gate"),
    ("engineer/workflows/execute-phase.md", "review_phase_issues"),
    ("engineer/workflows/ship.md", "preflight_checks"),
    ("engineer/workflows/ship.md", "generate_pr_body"),
    ("engineer/workflows/ship.md", "create_pr"),
    ("engineer/workflows/ship.md", "refresh_issue_link_audit"),
    ("engineer/workflows/ship.md", "merge_and_close"),
)
# Short cues within real sections replace embedded original paragraphs.
ROUTING_DUTIES = {
    "lookup": ("Checklist lookup", "chore(security): phase {phase-id} security checklist",
               "phase-security-checklist", "title AND label", "before any", "open and closed"),
    "lookup recovery": ("Multiple matches", "Pending", "uncertain creation", "before retrying"),
    "existing identity": ("remain canonical", "reopening-authority blocker", "bypass"),
    "planned default": ("NEW planned risks", "accepted/deferred", "mandatory default", "without an existing", "both searches"),
    "heading identity": ("stable `###` heading", "issue BODY", "provider heading anchors",
                         "never fabricate anchor slugs", "Reuse the matching heading", "Pending"),
    "heading stability": ("renaming a heading breaks", "all affected references", "without a", '"(comment)"'),
    "assessment links": ("owning PLAN assessment", "PLAN/ID", "SUMMARY/PR linked outcomes separate"),
    "register separation": ("never a combined PLAN register", "six-column register", "owning PLAN"),
    "standalone unplanned": ("distinct unplanned threat", "standalone Security risk", "checklist-only", "cannot replace"),
    "safe reconciliation": ("safe separate review", "serialized writes", "template validation",
                            "uncertain-create recovery", "Never route threats", "exemption never waives"),
    "checked is not closed": ("individual outcome evidence", "does not mean", "scope-complete evidence",
                              "existing explicit closure authority"),
}
AUDIT_DUTIES = {
    "independent scope": ("fresh independent", "must not be the author", "CONTEXT acceptance",
                          "PLAN threat/checklist", "SUMMARY outcomes", "Ordinary linked follow-ups", "issue.validate"),
    "coverage": ("omitted", "duplicate tracking", "planned-checklist", "standalone", "safe destination"),
    "closure": ("Neutral versus closing", "GitLab", "scope-complete", "explicit closure authority", "Never infer closure"),
    "packet": ("source revision", "head SHA", "body/link snapshot", "verified URLs", "provider readback",
               "when it was read", "unresolved findings/dependencies", "never a pass"),
    "currentness": ("invalidate", "fresh applicable", "coordinator-currentness-check",
                    "Before merge", "last provider readback", "no new merge"),
    "verifier ownership": ("verifier owns", "optional supplementary", "fresh non-author verifier",
                           "Join the result", "After publication", "Pending"),
}
PUBLICATION_DUTIES = {
    "### Identity and publication": {
        "risk identity": ("stable canonical risk key", "aliases/occurrences", "across reruns"),
        "closed-match evidence": ("semantic scope", "matching resolution evidence", "reopening authority"),
        "uncertain recovery": ("uncertain creation", "exact reviewed intent", "before retrying"),
        "provider fallback": ("GitHub-only", "verified authorized host tool", "Pending/publication blocker"),
    },
    "### Safe reporting": {
        "safe disclosure": ("sanitized", "without private-channel approval", "restricted channel",
                            "blocks only", "destination visibility"),
    },
    "### Assessment, status and closure": {
        "assessment ownership": ("owning PLAN assessment", "rather than copying", "six-column register"),
        "evidenced closure": ("neutral issue links", "scope-complete", "explicit closure authority",
                              "Never label accepted/deferred", "readback"),
    },
}


def section(text, heading):
    depth = len(heading.split(" ", 1)[0])
    if heading + "\n" not in text:
        return ""
    lines, fenced = [], False
    for line in text.split(heading + "\n", 1)[1].splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and re.match(r"^#{1," + str(depth) + r"}\s", line):
            break
        lines.append(line)
    return "\n".join(lines)


def steps(text):
    return dict(re.findall(r'^<step name="([^"]+)">\n(.*?)^</step>', text, re.M | re.S))


def file_template(text):
    region = text.split("## File Template\n", 1)[1]
    return re.search(r"^```markdown\n(.*?)^```", region, re.M | re.S).group(1)


def table_headers(text):
    return [tuple(c.strip() for c in re.split(r"(?<!\\)\|", line.strip("|")))
            for line in text.splitlines() if line.startswith("| ")]


def duty_errors(text, groups):
    text = " ".join(text.split())
    return [label for label, tokens in groups.items() if not all(t in text for t in tokens)]


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


def artifact_errors(root):
    content = {name: (root / name).read_text(encoding="utf-8") for name in PATHS}
    errors = []
    plan = file_template(content["engineer/templates/phase-prompt.md"])
    if "<threat_model>" not in plan or PLAN_FIELDS not in table_headers(plan):
        errors.append("PLAN register")
    if not all(t in plan for t in ("[Threat ID]", "canonical issue URL", "Pending: dependency")):
        errors.append("PLAN identity")
    summary = file_template(content["engineer/templates/summary.md"])
    flags = section(summary, "## Threat Flags")
    if FLAG_FIELDS not in table_headers(flags) or "omit this section" not in flags:
        errors.append("conditional discovery")
    for name, artifact in (("SUMMARY", summary),
                            ("PR", file_template(content["engineer/templates/pull-request.md"]))):
        if OUTCOME_FIELDS not in table_headers(artifact) or PLAN_FIELDS in table_headers(artifact):
            errors.append(name + " outcomes")
    coder = content["agents/executor.md"]
    if not all(t in coder for t in ("**Threat model reference:**", "<threat_model>", "`mitigate`", "Rule 2")):
        errors.append("coder mitigation")
    discovery = coder.split("**Threat surface scan:**", 1)[-1].split("**Remaining work:**", 1)[0]
    if FLAG_FIELDS not in table_headers(discovery) or "Omit section if nothing found" not in discovery:
        errors.append("coder discovery")
    preparer = content["agents/planner.md"]
    threat = preparer.split("<threat_model>", 1)[-1].split("</threat_model>", 1)[0]
    if PLAN_FIELDS not in table_headers(threat) or "## Trust Boundaries" not in threat:
        errors.append("preparer register")
    if not all(t in preparer for t in ("Security review: not applicable", "Every threat has a Severity")):
        errors.append("preparer assessment")
    gate = section(content["agents/plan-checker.md"], "## Dimension 7d: Security Planning Gate")
    errors += duty_errors(gate, {"checker security gate": ("planner.md#security-planning-gate",
                             "dispositions", "BLOCKER", "non-applicability", "absent setting")})
    for name in PRODUCERS:
        if not reaches_canonical(root, name):
            errors.append(name + ": unreachable")
    for name, step in TRACK_STEPS:
        body = steps(content[name]).get(step, "")
        if TRACK_LINK not in body or re.search(r"^\*\*Only when", body, re.M):
            errors.append(step + ": mandatory tracking")
    order = list(steps(content["engineer/workflows/quick.md"]))
    for before, after in (("plan", "reconcile_plan_threats"), ("reconcile_plan_threats", "check_plan"),
                          ("execute", "reconcile_summary_threats"), ("reconcile_summary_threats", "verify")):
        if before not in order or after not in order or order.index(before) >= order.index(after):
            errors.append("quick ordering")
    return errors


def routing_errors(root):
    text = (root / CANONICAL).read_text(encoding="utf-8")
    routing = section(text, "### Planned checklist and unplanned routing")
    errors = duty_errors(routing, ROUTING_DUTIES)
    for heading, duties in PUBLICATION_DUTIES.items():
        errors += duty_errors(section(text, heading), duties)
    if CHECKLIST_FIELDS not in table_headers(routing):
        errors.append("entry fields")
    if routing.find("Checklist lookup") >= routing.find("Then perform"):
        errors.append("lookup ordering")
    template = section((root / "engineer/templates/issue.md").read_text(encoding="utf-8"), "### Security risk")
    errors += duty_errors(template, {
        "template routing": ("mandatory default", "stable `###` heading", "heading-anchor URLs",
                             "Existing actionable", "Distinct unplanned", "owning PLANs"),
    })
    risk_block = re.search(r"^```markdown\n(.*?)^```", template, re.M | re.S).group(1)
    guidance = template.split("```", 2)[-1]
    errors += duty_errors(risk_block, {
        "standalone assessment": ("- Severity:", "impact/likelihood", "uncertainty",
                                  "- Mitigation or safe next action:", "Safe remediation outcome", "Observable secure check"),
    })
    errors += duty_errors(guidance, {
        "template assessment": ("Only checklist", "PLAN assessment:", "PLAN mitigation:", "rather than repeating"),
        "no PLAN required": ("Standalone issues require no PLAN",),
    })
    execution = steps((root / "engineer/workflows/execute-phase.md").read_text(encoding="utf-8"))["aggregate_results"]
    errors += duty_errors(execution, {
        "execution default": ("canonical default", "new planned risk", "accepted/deferred",
                              "canonical trackers", "standalone tracking", "distinct unplanned"),
    })
    if "may use" in execution:
        errors.append("execution default")
    runtime = section((root / "engineer/references/template-contract.md").read_text(encoding="utf-8"),
                      "### Risk-routing destinations")
    errors += duty_errors(runtime, {"runtime planned scope": ("new planned risks", "accepted/deferred", "mandatory")})
    return errors


def audit_errors(root):
    canonical = (root / CANONICAL).read_text(encoding="utf-8")
    errors = duty_errors(section(canonical, "## Issue-link audit"), AUDIT_DUTIES)
    for name, step in AUDIT_STEPS:
        if AUDIT_LINK not in steps((root / name).read_text(encoding="utf-8")).get(step, ""):
            errors.append(step + ": audit hook")
    verifier = (root / "agents/verifier.md").read_text(encoding="utf-8")
    context = section(verifier, "## Step 1: Load Context")
    if AUDIT_LINK not in context or "owning non-author verifier" not in context:
        errors.append("verifier audit")
    workflow = steps((root / "engineer/workflows/verify-work.md").read_text(encoding="utf-8"))
    prompt = workflow["spawn_verifier"].split('prompt="', 1)[1]
    if not all(t in prompt for t in (AUDIT_LINK, "Own the independent", "source/body/link snapshot", "provider readback")):
        errors.append("verify assignment")
    ship = steps((root / "engineer/workflows/ship.md").read_text(encoding="utf-8"))
    dispatch = ship.get("refresh_issue_link_audit", "")
    if not all(t in dispatch for t in ('subagent_type="verifier"', "fresh non-author", "{current_source_revision}",
                                       "{provider_head_sha}", "{current_body_and_links}",
                                       "{timestamped_provider_readback_or_Pending_dependency}", "Join the result")):
        errors.append("ship dispatch")
    for step in ("preflight_checks", "create_pr", "merge_and_close"):
        if "refresh_issue_link_audit" not in ship[step]:
            errors.append(step + ": refresh")
    if not all(t in " ".join(ship["create_pr"].split()) for t in ("Recheck", "after publication", "linked issue states")):
        errors.append("publication recheck")
    reviewer = (root / "agents/code-reviewer.md").read_text(encoding="utf-8")
    local = reviewer.split("<local_workflow>", 1)[1].split("</local_workflow>", 1)[0]
    if AUDIT_LINK not in local or "supplement" not in local or "verifier" not in local:
        errors.append("reviewer supplement")
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

    def mutate(self, root, name, token, new="Removed", heading=None, step=None):
        path = root / name
        text = path.read_text(encoding="utf-8")
        body = steps(text)[step] if step else section(text, heading) if heading else text
        pattern = r"\s+".join(re.escape(w) for w in token.split())
        changed, count = re.subn(pattern, lambda _: new, body)
        self.assertGreater(count, 0, token)
        path.write_text(text.replace(body, changed, 1), encoding="utf-8")

    def test_real_artifacts(self):
        self.assertEqual([], artifact_errors(ROOT))

    def test_real_routing(self):
        self.assertEqual([], routing_errors(ROOT))

    def test_real_audit(self):
        self.assertEqual([], audit_errors(ROOT))

    def test_register_and_discovery_mutations(self):
        for name, token, expected in (
            ("engineer/templates/phase-prompt.md", "| Mitigation Plan |", "PLAN register"),
            ("engineer/templates/phase-prompt.md", "Pending: dependency", "PLAN identity"),
            ("engineer/templates/summary.md", "| Flag | File | Description |", "conditional discovery"),
            ("engineer/templates/summary.md", "omit this section", "conditional discovery"),
            ("agents/executor.md", "**Threat model reference:**", "coder mitigation"),
            ("agents/executor.md", "Omit section if nothing found", "coder discovery"),
            ("agents/planner.md", "| Mitigation Plan |", "preparer register"),
            ("agents/planner.md", "Every threat has a Severity", "preparer assessment"),
            ("agents/plan-checker.md", "BLOCKER", "checker security gate"),
        ):
            with self.subTest(expected=expected, token=token):
                root = self.fixture()
                self.mutate(root, name, token)
                self.assertIn(expected, artifact_errors(root))

    def test_outcomes_are_separate_from_register(self):
        for name, label in (("engineer/templates/summary.md", "SUMMARY"), ("engineer/templates/pull-request.md", "PR")):
            for field in OUTCOME_FIELDS:
                with self.subTest(name=name, field=field):
                    root = self.fixture()
                    self.mutate(root, name, "| " + field + " |")
                    with (root / name).open("a", encoding="utf-8") as stream:
                        stream.write("\n| " + " | ".join(OUTCOME_FIELDS) + " |\n")
                    self.assertIn(label + " outcomes", artifact_errors(root))

    def test_mandatory_tracking_steps(self):
        for name, step in TRACK_STEPS:
            with self.subTest(step=step):
                root = self.fixture()
                path = root / name
                text = path.read_text(encoding="utf-8")
                body = steps(text)[step]
                path.write_text(text.replace(body, body.replace(TRACK_LINK, "missing.md"), 1), encoding="utf-8")
                self.assertIn(step + ": mandatory tracking", artifact_errors(root))
        root = self.fixture()
        self.mutate(root, "engineer/workflows/quick.md", '<step name="reconcile_summary_threats">',
                    '<step name="reconcile_summary_threats">\n**Only when OPTIONAL.**')
        self.assertIn("reconcile_summary_threats: mandatory tracking", artifact_errors(root))

    def test_quick_reconciliation_cannot_move_into_optional_steps(self):
        for required, optional in (("reconcile_plan_threats", "check_plan"),
                                   ("reconcile_summary_threats", "verify")):
            with self.subTest(step=required):
                root = self.fixture()
                path = root / "engineer/workflows/quick.md"
                text = path.read_text(encoding="utf-8")
                block = re.search(r'^<step name="' + required + r'">.*?^</step>\n',
                                  text, re.M | re.S).group(0)
                text = text.replace(block, "", 1).replace('<step name="' + optional + '">',
                       '<step name="' + optional + '">\n' + block, 1)
                path.write_text(text, encoding="utf-8")
                self.assertIn("quick ordering", artifact_errors(root))

    def test_register_cannot_be_duplicated_into_outcomes(self):
        for name, label in (("engineer/templates/summary.md", "SUMMARY"),
                            ("engineer/templates/pull-request.md", "PR")):
            with self.subTest(artifact=label):
                root = self.fixture()
                path = root / name
                text = path.read_text(encoding="utf-8")
                artifact = file_template(text)
                path.write_text(text.replace(artifact, artifact + "\n| " + " | ".join(PLAN_FIELDS) + " |\n", 1),
                                encoding="utf-8")
                self.assertIn(label + " outcomes", artifact_errors(root))

    def test_canonical_link_loss(self):
        root = self.fixture()
        name = "engineer/templates/phase-prompt.md"
        self.mutate(root, name, TRACK_LINK, "missing.md")
        # The integrity-contract link is a legitimate alternate route. Removing
        # only the direct canonical link must preserve that reachability.
        self.assertTrue(reaches_canonical(root, name))
        self.assertNotIn(name + ": unreachable", artifact_errors(root))
        path = root / name
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"\[([^\]\n]+)\]\([^)\n]+\)", r"\1", text)
        path.write_text(text, encoding="utf-8")
        self.assertFalse(reaches_canonical(root, name))
        self.assertIn(name + ": unreachable", artifact_errors(root))

    def test_routing_duty_mutations(self):
        for label, tokens in ROUTING_DUTIES.items():
            for token in tokens:
                with self.subTest(label=label, token=token):
                    root = self.fixture()
                    self.mutate(root, CANONICAL, token, heading="### Planned checklist and unplanned routing")
                    self.assertIn(label, routing_errors(root))

    def test_each_entry_field(self):
        for field in CHECKLIST_FIELDS:
            with self.subTest(field=field):
                root = self.fixture()
                self.mutate(root, CANONICAL, "| " + field + " |",
                            heading="### Planned checklist and unplanned routing")
                self.assertIn("entry fields", routing_errors(root))

    def test_publication_safety_mutations(self):
        for heading, duties in PUBLICATION_DUTIES.items():
            for label, tokens in duties.items():
                for token in tokens:
                    with self.subTest(label=label, token=token):
                        root = self.fixture()
                        self.mutate(root, CANONICAL, token, heading=heading)
                        self.assertIn(label, routing_errors(root))

    def test_template_assessment_links(self):
        for token in ("PLAN assessment:", "PLAN mitigation:"):
            with self.subTest(token=token):
                root = self.fixture()
                self.mutate(root, "engineer/templates/issue.md", token)
                self.assertIn("template assessment", routing_errors(root))

    def test_standalone_assessment_and_no_plan_support(self):
        for token, expected in (("- Severity:", "standalone assessment"),
                                ("- Mitigation or safe next action:", "standalone assessment"),
                                ("Observable secure check", "standalone assessment"),
                                ("Standalone issues require no PLAN", "no PLAN required"),
                                ("Only checklist", "template assessment")):
            with self.subTest(token=token):
                root = self.fixture()
                self.mutate(root, "engineer/templates/issue.md", token, heading="### Security risk")
                self.assertIn(expected, routing_errors(root))

    def test_execution_and_runtime_default_seams(self):
        for name, token, expected in (
            ("engineer/workflows/execute-phase.md", "canonical default", "execution default"),
            ("engineer/workflows/execute-phase.md", "accepted/deferred", "execution default"),
            ("engineer/workflows/execute-phase.md", "standalone tracking", "execution default"),
            ("engineer/references/template-contract.md", "new planned risks", "runtime planned scope"),
            ("engineer/references/template-contract.md", "accepted/deferred", "runtime planned scope"),
        ):
            with self.subTest(token=token, name=name):
                root = self.fixture()
                self.mutate(root, name, token,
                            step="aggregate_results" if "execute-phase" in name else None,
                            heading="### Risk-routing destinations" if "TEMPLATE-CONTRACT" in name else None)
                self.assertIn(expected, routing_errors(root))
        root = self.fixture()
        self.mutate(root, "engineer/workflows/execute-phase.md", "canonical default", "optional path; may use",
                    step="aggregate_results")
        self.assertIn("execution default", routing_errors(root))

    def test_audit_duty_mutations(self):
        for label, tokens in AUDIT_DUTIES.items():
            for token in tokens:
                with self.subTest(label=label, token=token):
                    root = self.fixture()
                    self.mutate(root, CANONICAL, token, heading="## Issue-link audit")
                    self.assertIn(label, audit_errors(root))

    def test_each_actual_audit_hook(self):
        for name, step in AUDIT_STEPS:
            with self.subTest(step=step):
                root = self.fixture()
                path = root / name
                text = path.read_text(encoding="utf-8")
                body = steps(text)[step]
                path.write_text(text.replace(body, body.replace(AUDIT_LINK, "missing.md"), 1), encoding="utf-8")
                self.assertIn(step + ": audit hook", audit_errors(root))

    def test_verifier_and_ship_dispatch_packets(self):
        for name, token, expected in (
            ("agents/verifier.md", "owning non-author verifier", "verifier audit"),
            ("engineer/workflows/verify-work.md", "Own the independent", "verify assignment"),
            ("engineer/workflows/ship.md", 'subagent_type="verifier"', "ship dispatch"),
            ("engineer/workflows/ship.md", "{current_source_revision}", "ship dispatch"),
            ("engineer/workflows/ship.md", "{current_body_and_links}", "ship dispatch"),
            ("engineer/workflows/ship.md", "{timestamped_provider_readback_or_Pending_dependency}", "ship dispatch"),
            ("engineer/workflows/ship.md", "after publication", "publication recheck"),
        ):
            with self.subTest(token=token):
                root = self.fixture()
                self.mutate(root, name, token)
                self.assertIn(expected, audit_errors(root))


if __name__ == "__main__":
    unittest.main()
