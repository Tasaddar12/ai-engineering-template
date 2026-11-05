"""Bounded producer-policy contracts and actual installed-runtime composition.

These tests do NOT implement an LLM eligibility algorithm. Human/gap report
variants are explicitly authored synthetic observations, not inferred verdicts.
Policy assertions pin the guardrails the real verifier must apply; schema alone
cannot validate provenance, truthful prose, independent review or acceptance.
Only disposable generic projects are installed or executed. No scans, services,
provider calls or real project records are used.

For a reproducible old-policy RED, select a committed source with
ENGINEER_ADVISORY_TEST_REF and run AdvisoryPolicyContracts. Functional tests
install that selected Git pin through bin/install.py for BOTH hosts. Providers
are strict mocks; Git, projection, Node proof, fingerprint and check receipts
are real. Assertions use specified/derived contracts, never mere exit success.
"""
from contextlib import contextmanager
import copy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1]
SELECTED_REF = os.environ.get("ENGINEER_ADVISORY_TEST_REF", "HEAD")
HOSTS = ("claude", "codex")
P1 = "The dashboard MUST NOT execute real or test scans before the owner separately approves coordinated scan UAT."
P2 = "The dashboard MUST NOT present passive discovery candidates, absent scanner evidence, fixture passes or a disabled bridge as successful scanned or production-qualified results."
PLAN = ".planning/phases/01-fixture/01-01-PLAN.md"
REPORT = ".planning/phases/01-fixture/01-VERIFICATION.md"
SUMMARY = ".planning/phases/01-fixture/01-01-SUMMARY.md"
CONTEXT = ".planning/phases/01-fixture/01-CONTEXT.md"
AUTHORITY = "fixture-decisions.md#invocation: explicitly implement unattended and deliver source after required non-scan checks; future operations remain held"
ITEMS = [{"statement": literal, "status": "resolved", "verification": "judgment"}
         for literal in (P1, P2)]


def run(argv, cwd=SOURCE, env=None, timeout=60):
    return subprocess.run(list(map(str, argv)), cwd=cwd, env=env, text=True,
                          encoding="utf-8", capture_output=True, timeout=timeout)


def git(directory, *args):
    result = run(["git", "-C", directory, *args], timeout=30)
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def source_text(path):
    return git(SOURCE, "show", f"{SELECTED_REF}:{path}")


def normalized(text):
    return " ".join(text.split())


class AdvisoryPolicyContracts(unittest.TestCase):
    """Specified prose contracts; these do not simulate an agent's judgment."""

    def test_shared_authority_is_explicit_scoped_and_does_not_mutate_defaults(self):
        reference = normalized(source_text("engineer/references/prohibition-probe.md"))
        for obligation in (
            "## Invocation authority and judgment reporting",
            "A specific, trusted user instruction",
            "without changing those settings",
            "Missing or ambiguous authority uses interactive handling",
            "Being AFK, silence, or “no questions” alone does not establish permission",
            "Neither Git author identity nor an agent's claim of human authorship proves acceptance",
            "Inspect the actual goal, requirements, locked decisions, trusted user decisions and PLAN checkpoints/evidence obligations",
            "Absence of an explicit manual-test sentence alone is insufficient",
            "current, source-scoped independent assessment",
            "An old review, SUMMARY claim or finite fixture pass alone does not establish this",
            "No actual outstanding present human acceptance/action/authentication/blocking-human checkpoint",
            "Unknown provenance or ambiguity about required human acceptance cannot take this route",
        ):
            with self.subTest(obligation=obligation):
                self.assertIn(obligation, reference)
        for path in ("agents/verifier.md", "engineer/templates/verification-report.md"):
            text = source_text(path)
            self.assertIn("prohibition-probe.md", text)
            self.assertIn("Invocation authority", text)

    def test_routing_preserves_real_human_and_evidence_blockers(self):
        reference = normalized(source_text("engineer/references/prohibition-probe.md"))
        verifier = normalized(source_text("agents/verifier.md"))
        for boundary in (
            "Only a `resolved` / `judgment` prohibition qualifies",
            "Interactive/default-only judgment, unresolved/unknown items, unclear provenance/intent",
            "Explicit present human acceptance and human-action/auth/blocking-human checkpoints still require their actual resolution",
            "Behavior-unverified truths and unconfirmed backstop/`insufficient_spec` truths stay human items, including infrastructure phases",
            "Failed truths/artifacts/links, security/test-quality blockers and unresolved evidence gaps stay gaps",
            "A test-tier prohibition with absent, partial, unsupported, failing or unprovable enforcement is `gaps_found` in **both modes**",
            "Existing Step 7 convergence advisories retain their separate re-verification-only scope/evidence rules",
        ):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, reference)
        for boundary in (
            "mixed advisory plus any genuine human item is `human_needed`",
            "**passed is ONLY valid when the human verification section is empty.**",
            "blocker anti-pattern/security/test-quality finding",
            "Behavior-unverified", "check.prohibition-enforcement",
            "Never fabricate a check path, Python-as-node descriptor or evidence",
        ):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, verifier)
        self.assertNotIn("enforcement is deferred", verifier)
        self.assertNotIn("If ANY prohibition remains flagged", verifier)

    def test_exact_accounting_report_fields_and_delivery_disclosure(self):
        reference = source_text("engineer/references/prohibition-probe.md")
        for literal in (P1, P2, "2 original = 2 projected + 0 dropped"):
            self.assertIn(literal, reference)
        for boundary in (
            "zero-based array position", "flagged/unverified/NON-AUTHORITATIVE",
            "never-auto-dismiss", "no-silent-drop", "Preserve prior reports/history",
            "Fingerprint, revision, configured-check receipts, independent review, CI and merge-authority gates still apply",
        ):
            self.assertIn(boundary, normalized(reference))
        for path in ("agents/verifier.md", "engineer/templates/verification-report.md"):
            text = source_text(path)
            self.assertIn("## Unverified Prohibitions", text)
            self.assertIn("complete with N flagged prohibitions", text)
            self.assertRegex(normalized(text), r"SUMMARY.*delivery")
            self.assertIn("NON-AUTHORITATIVE", text)
        template = source_text("engineer/templates/verification-report.md")
        advisory = template.split("advisory:", 1)[1].split("behavior_unverified_items:", 1)[0]
        self.assertEqual({"finding", "category", "reason", "evidence_status"},
                         set(re.findall(r"(?m)^\s*(?:- )?(\w+):", advisory)))
        self.assertIn("do not invent a digest", normalized(template))
        self.assertIn("Source-passed does not qualify production, complete pending UAT or approve future scans", normalized(template))


def installed_modules(namespace, host):
    """Import the actual exported modules with a private package name per host."""
    name = "_advisory_installed_" + host
    lib = namespace / "engineer/bin/lib"
    spec = importlib.util.spec_from_file_location(name, lib / "__init__.py",
                                                submodule_search_locations=[str(lib)])
    package = importlib.util.module_from_spec(spec)
    sys.modules[name] = package
    spec.loader.exec_module(package)
    return {key: importlib.import_module(name + "." + key) for key in
            ("core", "text", "probe_core", "prohibition_probe", "frontmatter", "verification", "delivery")}


class InstalledAdvisoryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="engineer-advisory-installs-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.base = Path(cls.temporary.name)
        cls.pin = git(SOURCE, "rev-parse", SELECTED_REF + "^{commit}")
        cls.seeds, cls.modules = {}, {}
        for host in HOSTS:
            target = cls.base / (host + " supported fixture")
            result = run([sys.executable, "-I", SOURCE / "bin/install.py", "--source", SOURCE,
                          "--ref", cls.pin, "--target", target, "--host", host, "--local", "--no-hooks"], timeout=120)
            if result.returncode:
                raise AssertionError(result.stderr)
            packet = json.loads(result.stdout)
            if not packet.get("applied") or not packet.get("complete"):
                raise AssertionError(packet)
            namespace = target / ("." + host)
            cls.seeds[host] = target
            cls.modules[host] = installed_modules(namespace, host)

    @contextmanager
    def project(self, host):
        with tempfile.TemporaryDirectory(prefix="engineer-advisory-project-") as temporary:
            target = Path(temporary) / "generic fixture"
            # Supported local exports are relocatable; each test owns its copy.
            shutil.copytree(self.seeds[host], target)
            git(target, "init", "-b", "fixture")
            git(target, "config", "user.name", "Synthetic Fixture Agent")
            git(target, "config", "user.email", "agent@example.invalid")
            git(target, "config", "core.autocrlf", "false")
            (target / ".gitignore").write_text(".claude/\n.codex/\n.agents/\n.planning/verification-receipts/\n", encoding="utf-8")
            prior = Path.cwd()
            with patch.dict(os.environ, {"ENGINEER_ROOT": str(target), "ENGINEER_HOST": host}):
                os.chdir(target)
                try:
                    yield target, self.modules[host]
                finally:
                    os.chdir(prior)

    def cli(self, target, host, *args, expected=0):
        result = run([sys.executable, "-I", target / ("." + host) / "engineer/bin/engineer.py", "query", *args], cwd=target)
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return json.loads(result.stdout) if result.stdout.strip() else json.loads(result.stderr)

    def initialize(self, target, host, modules):
        """Real project.init, real check body and tracked synthetic evidence inputs."""
        fields = {
            "project": {"name": "Generic advisory contract fixture", "description": "Disposable offline policy/runtime exercise.",
                        "core_value": "A bounded literal fixture observation; no production or UAT acceptance."},
            "requirements": [{"id": "FIX-01", "description": "Read the actual clean marker.", "phase": 1}],
            "phases": [{"name": "Fixture", "goal": "Read a clean marker from a file.", "requirements": ["FIX-01"],
                        "success_criteria": ["The configured check reads the file and rejects any other marker."]}],
            "config": {"mode": "interactive", "workflow": {"auto_advance": False, "human_verify_mode": "end-of-phase"},
                       "verification": {"commands": [{"id": "fixture-marker", "argv": [sys.executable, "-I", "fixture_check.py"],
                           "sources": ["subject.txt", "fixture_check.py"], "environment": [], "timeout": 15}]}}
        }
        self.cli(target, host, "project.init", "--fields", json.dumps(fields))
        (target / "subject.txt").write_text("clean\n", encoding="utf-8")
        (target / "fixture_check.py").write_text(
            "from pathlib import Path\nassert Path('subject.txt').read_text(encoding='utf-8') == 'clean\\n'\nprint('actual clean marker checked')\n", encoding="utf-8")
        (target / "fixture-decisions.md").write_text(AUTHORITY + "\nNo present human acceptance is stipulated in this synthetic contract.\n", encoding="utf-8")
        phase = target / Path(PLAN).parent
        phase.mkdir(parents=True, exist_ok=True)
        metadata = {"phase": "01-fixture", "plan": "01", "type": "execute", "wave": 1,
                    "depends_on": [], "files_modified": ["fixture_check.py", "subject.txt"], "autonomous": True,
                    "must_haves": {"truths": ["The fixture check reads the clean marker."],
                                   "artifacts": [{"path": "fixture_check.py", "contains": "Path"}],
                                   "key_links": [{"from": "fixture_check.py", "to": "subject.txt", "via": "subject.txt"}],
                                   "prohibitions": modules["probe_core"].project_prohibitions(ITEMS)}}
        (target / PLAN).write_text(modules["text"].join_frontmatter(metadata, "# Synthetic contract\n"), encoding="utf-8")
        (target / SUMMARY).write_text(modules["text"].join_frontmatter(
            {"phase": "01-fixture", "plan": "01", "status": "complete"},
            "# Fixture source: complete with 2 flagged prohibitions\n\n" + self.disclosure() + "\n"), encoding="utf-8")
        (target / CONTEXT).write_text("---\nphase: 01-fixture\n---\n# Decisions\n\nD-01: Read the file; future operations remain held.\n", encoding="utf-8")
        git(target, "add", ".")
        git(target, "commit", "-m", "Initialize disposable fixture evidence")
        return metadata

    def disclosure(self):
        return "\n".join(f"{PLAN}#must_haves.prohibitions[{index}]: {item['statement']} — resolved/judgment; flagged/unverified/NON-AUTHORITATIVE"
                         for index, item in enumerate(ITEMS)) + "\n2 original = 2 projected + 0 dropped"

    def report(self, target, host, modules, *, status="passed", human=None, gaps=None, behavior=0):
        """Materialize the actual installed template with observed fixture evidence.

        Routing is supplied by the test author; this is NOT an eligibility engine.
        All illustrative sample rows are replaced, never asserted as observations.
        """
        template = (target / ("." + host) / "engineer/templates/verification-report.md").read_text(encoding="utf-8")
        example = re.search(r"## File Template\s+```markdown\n(.*?)\n```", template, re.S)
        self.assertIsNotNone(example)
        _, skeleton = modules["text"].split_frontmatter(example[1])
        head = git(target, "rev-parse", "HEAD")
        advisory = [{"finding": "unverified-prohibition — human review recommended", "category": "other",
                     "reason": f"{PLAN}#must_haves.prohibitions[{index}]; exact literal: {item['statement']}; lifecycle: resolved; tier: judgment; disposition: flagged/unverified/NON-AUTHORITATIVE; intent: fixture-decisions.md; invocation authority: {AUTHORITY}; recommended human review: universal judgment remains unverified",
                     "evidence_status": f"Synthetic assessment of fixture_check.py/subject.txt at {head}; actual configured check reads clean marker; independent review is a test premise, not a real dashboard review; no human acceptance, production or scan evidence claimed"}
                    for index, item in enumerate(ITEMS)]
        metadata = {"phase": "01-fixture", "verified": "2026-11-05T00:00:00Z", "status": status,
                    "score": "1/1 must-haves verified", "covered_files": ["subject.txt", "fixture_check.py", "fixture-decisions.md"],
                    "revision": head, "behavior_unverified": behavior, "advisory": advisory}
        if human:
            metadata["human_verification"] = human
        if gaps:
            metadata["gaps"] = gaps
        if behavior:
            metadata["behavior_unverified_items"] = human
        disclosure = "complete with 2 flagged prohibitions" if status == "passed" else status + "; 2 flagged prohibitions"
        blocks = {
            "Unverified Prohibitions": "**Flagged prohibitions:** 2.\n\n" + self.disclosure() + "\n\n" + AUTHORITY + "\nHuman review recommended; both universal judgments remain unverified.",
            "Goal Achievement": "Actual configured check, artifact and link checks establish only this synthetic source goal.",
            "Observable Truths": "| Truth | Status | Evidence |\n|---|---|---|\n| Clean marker read from file | ✓ VERIFIED | fixture_check.py executed by verification.run-checks |",
            "Required Artifacts": "fixture_check.py exists, imports Path and reads the actual subject.txt; verify.artifacts checks it.",
            "Key Link Verification": "fixture_check.py -> subject.txt via Path read; verify.key-links checks the literal connection.",
            "Requirements Coverage": "FIX-01: actual configured check; no broad prohibition counted as a truth.",
            "Anti-Patterns Found": "No claimed production behavior; fixture only.",
            "Human Verification Required": json.dumps(human) if human else "No required human observation in this synthetic fixture; advisory review recommended.",
            "Gaps Summary": json.dumps(gaps) if gaps else "No observed fixture implementation gap.",
            "Verification Metadata": "D-01: the clean marker check supports the file-reading decision only.\nNo production/UAT acceptance or future operation is authorized.",
        }
        headings = list(re.finditer(r"(?m)^(#{2,3}) (.+)$", skeleton))
        self.assertIn("Unverified Prohibitions", [match[2] for match in headings])
        body = f"# Fixture Verification\n\n**Status:** {status}\n**Completion disclosure:** {disclosure}\n\n"
        for match in headings:
            title = match[2]
            if title in blocks:
                body += match[0] + "\n\n" + blocks[title] + "\n\n"
        (target / REPORT).write_text(modules["text"].join_frontmatter(metadata, body), encoding="utf-8")
        return metadata

    def freeze(self, target, host):
        checks = self.cli(target, host, "verification.run-checks", "--force")
        self.assertTrue(checks["passed"])
        self.assertEqual(1, checks["count"])
        self.assertEqual("passed", checks["checks"][0]["status"])
        self.assertEqual(0, checks["checks"][0]["process_terminal"]["exit_code"])
        fingerprint = self.cli(target, host, "verification.fingerprint", "01", "--files", "subject.txt",
                               "--files", "fixture_check.py", "--files", "fixture-decisions.md")
        self.assertRegex(fingerprint["fingerprint"], r"^[a-f0-9]{64}$")
        git(target, "add", REPORT)
        git(target, "commit", "-m", "Record generated fixture verification")
        self.assertEqual("", git(target, "status", "--porcelain"))
        self.assertTrue(self.cli(target, host, "verification.check-status")["passed"])
        self.assertTrue(self.cli(target, host, "verification.current", "01")["current"])
        return checks

    def test_both_supported_installed_identities_pins_and_functional_cli(self):
        for host in HOSTS:
            with self.subTest(host=host), self.project(host) as (target, modules):
                namespace = target / ("." + host)
                manifest = json.loads((namespace / "engineer-install/manifest.json").read_text(encoding="utf-8"))
                identity = json.loads((namespace / "engineer-install/identity.json").read_text(encoding="utf-8"))
                self.assertEqual(host, manifest["host"])
                self.assertEqual("local", manifest["scope"])
                self.assertEqual(self.pin, manifest["revision"])
                self.assertEqual(manifest["installation_id"], identity["id"])
                packet = self.cli(target, host, "runtime-identity")
                self.assertEqual("engineer-runtime", packet["packageName"])
                self.assertEqual(host, packet["host"])
                self.assertEqual(namespace, Path(packet["namespace"]))
                launcher = run(["sh", namespace / "engineer/bin/engineer_run", "query", "runtime-identity"], cwd=target)
                self.assertEqual(0, launcher.returncode, launcher.stderr)
                self.assertEqual(host, json.loads(launcher.stdout)["host"])
                context = self.cli(target, host, "update-context", "--config-dir", "." + host, "--runtime", host)
                self.assertIn(self.pin, json.dumps(context))
                self.initialize(target, host, modules)
                self.assertTrue(self.cli(target, host, "frontmatter.validate", PLAN, "--schema", "plan")["valid"])
                for verb in ("verify.artifacts", "verify.key-links"):
                    self.assertTrue(self.cli(target, host, verb, PLAN)["valid"])
                self.report(target, host, modules)
                self.assertTrue(self.cli(target, host, "frontmatter.validate", REPORT, "--schema", "verification")["valid"])
                self.assertTrue(self.cli(target, host, "check.decision-coverage-verify", "01")["passed"])
                self.freeze(target, host)
                self.assertEqual("ship", self.cli(target, host, "verification.status", "01")["route"])
                metadata = self.cli(target, host, "frontmatter.get", REPORT)
                self.assertEqual(2, len(metadata["advisory"]))
                self.assertEqual({"finding", "category", "reason", "evidence_status"}, set(metadata["advisory"][0]))
                for index, literal in enumerate((P1, P2)):
                    self.assertIn(f"{PLAN}#must_haves.prohibitions[{index}]", metadata["advisory"][index]["reason"])
                    self.assertIn(literal, metadata["advisory"][index]["reason"])
                    self.assertIn("flagged/unverified/NON-AUTHORITATIVE", metadata["advisory"][index]["reason"])
                    self.assertIn(AUTHORITY, metadata["advisory"][index]["reason"])
                for path in (REPORT, SUMMARY):
                    disclosure = (target / path).read_text(encoding="utf-8")
                    self.assertIn("complete with 2 flagged prohibitions", disclosure)
                    self.assertIn("2 original = 2 projected + 0 dropped", disclosure)
                    self.assertIn(self.disclosure(), disclosure)
                self.assertNotIn("human_verification", metadata)
                self.assertEqual("interactive", self.cli(target, host, "config-get", "mode"))
                self.assertIs(False, self.cli(target, host, "config-get", "workflow.auto_advance"))

    def test_projection_never_loses_literals_or_greens_judgment(self):
        for host in HOSTS:
            modules = self.modules[host]
            core = modules["probe_core"]
            projected = core.project_prohibitions(copy.deepcopy(ITEMS))
            self.assertEqual(ITEMS, projected)
            self.assertEqual(2, len(projected))
            for index, item in enumerate(projected):
                self.assertEqual((P1, P2)[index], item["statement"])
                for context in ({}, {"enforcementEvidence": [{"passed": True, "failFirst": True}]}):
                    verdict = core.disposition_for_prohibition(item, context)
                    self.assertEqual(("unverified", True, "judgment"), (verdict["status"], verdict["flagged"], verdict["tier"]))
                for changed in ({**item, "status": "unknown"}, {**item, "status": "dismissed"},
                                {**item, "status": "unresolved", "verification": "judgment"}):
                    with self.assertRaises(ValueError):
                        core.validate_prohibition_resolution(changed)
            backstop = core.disposition_for_unverifiable_truth({"statement": "Unknown fixture invariant", "verification": "backstop"})
            self.assertEqual(("unverified", True, "insufficient_spec"), (backstop["status"], backstop["flagged"], backstop["reason"]))

    def test_native_human_gap_schema_status_currentness_and_both_delivery_refusals(self):
        # Author-assigned dispositions: policy tests above enforce who may route;
        # this test proves consumers do not waive real human/evidence observations.
        human_cases = ("interactive/default-only", "mixed advisory plus present human acceptance/checkpoint",
                       "human-action/authentication/blocking-human", "behavior-unverified", "backstop insufficient_spec")
        gap_cases = ("failed truth/artifact/link", "security/test-quality blocker", "evidence gap")
        for host in HOSTS:
            with self.subTest(host=host), self.project(host) as (target, modules):
                self.initialize(target, host, modules)
                delivery, verification = modules["delivery"], modules["verification"]
                for status, cases in (("human_needed", human_cases), ("gaps_found", gap_cases)):
                    for label in cases:
                        with self.subTest(host=host, observation=label):
                            human = [{"test": label, "expected": "Actual required resolution", "why_human": "Synthetic unresolved obligation"}] if status == "human_needed" else None
                            gaps = [{"truth": label, "status": "failed", "reason": "Actual evidence obligation remains"}] if status == "gaps_found" else None
                            self.report(target, host, modules, status=status, human=human, gaps=gaps,
                                        behavior=int(label == "behavior-unverified"))
                            self.assertTrue(self.cli(target, host, "frontmatter.validate", REPORT, "--schema", "verification")["valid"])
                            self.assertEqual("human" if status == "human_needed" else "fix", self.cli(target, host, "verification.status", "01")["route"])
                            current = self.cli(target, host, "verification.current", "01")
                            self.assertFalse(current["current"])
                            self.assertIn("verification has not passed", current["reasons"])
                            with patch.object(delivery, "gh", side_effect=AssertionError("provider forbidden")) as provider, patch.object(delivery, "view", side_effect=AssertionError("provider view forbidden")) as view, patch.object(verification, "current_evidence", side_effect=AssertionError("status must refuse first")) as currentness:
                                for action in ("ready", "merge"):
                                    with self.assertRaises(delivery.Failure) as error:
                                        delivery.command(modules["core"].Args(["fixture", "--phase", "01", "--confirm"]), action)
                                    self.assertEqual("phase-unverified", error.exception.code)
                                provider.assert_not_called()
                                view.assert_not_called()
                                currentness.assert_not_called()
                            bad, body = modules["text"].split_frontmatter((target / REPORT).read_text(encoding="utf-8"))
                            bad["status"] = "passed"
                            self.assertIn("Passed verification cannot contain unresolved gaps or human observations", modules["frontmatter"].errors(bad, "verification"))

    def test_real_node_producer_fail_first_and_fail_closed_in_both_modes(self):
        self.assertIsNotNone(shutil.which("node"), "Node is required: this test cannot relabel Python as node-test")
        for host in HOSTS:
            with self.subTest(host=host), self.project(host) as (target, modules):
                (target / "clean.txt").write_text("clean\n", encoding="utf-8")
                (target / "bad.txt").write_text("violation\n", encoding="utf-8")
                (target / "negative.test.cjs").write_text(
                    "const test=require('node:test'); const assert=require('node:assert/strict'); const fs=require('node:fs');\n"
                    "test('subject excludes violation',()=>assert.equal(fs.readFileSync(process.env.ENGINEER_PROHIB_SUBJECT || 'clean.txt','utf8'),'clean\\n'));\n", encoding="utf-8")
                (target / "vacuous.test.cjs").write_text("// Deliberately no tests.\n", encoding="utf-8")
                (target / "always-green.test.cjs").write_text("require('node:test')('does not inspect subject',()=>{});\n", encoding="utf-8")
                (target / "always-red.test.cjs").write_text("require('node:test')('always fails',()=>{throw Error('bad check')});\n", encoding="utf-8")
                (target / "load-error.test.cjs").write_text("throw Error('load error is not meaningful RED');\n", encoding="utf-8")
                prohibition = {"statement": "The generic fixture MUST NOT contain violation.", "status": "resolved", "verification": "test"}
                descriptor = {"kind": "node-test", "target": "negative.test.cjs", "violationFixture": "bad.txt", "cleanFixture": "clean.txt"}
                for mode in ("interactive", "autonomous"):
                    positive = self.cli(target, host, "check.prohibition-enforcement", "--payload", json.dumps({"prohibition": prohibition, "check": descriptor, "mode": mode}))
                    self.assertEqual("advisory", positive["outcome"])
                    self.assertFalse(positive["block"])
                    payload = positive["payload"]
                    self.assertEqual(("green", False, mode), (payload["status"], payload["flagged"], payload["mode"]))
                    self.assertEqual([{"kind": "node-test", "target": "negative.test.cjs", "failFirst": True, "passed": True, "failFirstProof": "violation-fixture"}], payload["evidence"])
                    judgment = self.cli(target, host, "check.prohibition-enforcement", "--payload", json.dumps({"prohibition": {**prohibition, "verification": "judgment"}, "check": descriptor, "mode": mode}))["payload"]
                    self.assertEqual(payload["evidence"], judgment["evidence"])
                    self.assertEqual(("unverified", True), (judgment["status"], judgment["flagged"]))
                    negatives = {"absent": None, "partial": {"kind": "lint-rule", "target": "clean.txt"},
                                 "unsupported": {**descriptor, "kind": "python-unittest"},
                                 "nonexistent-target": {**descriptor, "target": "missing.test.cjs"},
                                 "missing-bad": {**descriptor, "violationFixture": "missing.txt"},
                                 "bad-fixture-is-clean": {**descriptor, "violationFixture": "clean.txt"},
                                 "missing-clean": {k: v for k, v in descriptor.items() if k != "cleanFixture"},
                                 "nonexistent-clean": {**descriptor, "cleanFixture": "missing.txt"},
                                 "clean-is-bad": {**descriptor, "cleanFixture": "bad.txt"},
                                 "vacuous": {**descriptor, "target": "vacuous.test.cjs"},
                                 "unproven-red": {**descriptor, "target": "always-green.test.cjs", "failFirst": True},
                                 "failed-check": {**descriptor, "target": "always-red.test.cjs"},
                                 "load-crash": {**descriptor, "target": "load-error.test.cjs"}}
                    for label, check in negatives.items():
                        with self.subTest(host=host, mode=mode, case=label):
                            result = self.cli(target, host, "check.prohibition-enforcement", "--payload", json.dumps({"prohibition": prohibition, "check": check, "mode": mode}))
                            self.assertEqual("advisory", result["outcome"], "outer success is not enforcement success")
                            self.assertEqual(("unverified", True, []), (result["payload"]["status"], result["payload"]["flagged"], result["payload"]["evidence"]))

    def test_current_real_receipts_and_delivery_guard_composition(self):
        for host in HOSTS:
            with self.subTest(host=host), self.project(host) as (target, modules):
                self.initialize(target, host, modules)
                self.report(target, host, modules)
                checks = self.freeze(target, host)
                delivery = modules["delivery"]
                args = modules["core"].Args(["fixture", "--phase", "01", "--confirm"])
                # Same real fingerprint and passing receipts, but a real human
                # item: current_evidence independently refuses status alone.
                original_report = (target / REPORT).read_bytes()
                metadata, body = modules["text"].split_frontmatter(original_report.decode())
                metadata.update(status="human_needed", human_verification=[{"test": "Required fixture checkpoint", "expected": "Actual resolution", "why_human": "Unresolved synthetic human obligation"}])
                (target / REPORT).write_text(modules["text"].join_frontmatter(metadata, body), encoding="utf-8")
                git(target, "add", REPORT)
                git(target, "commit", "-m", "Synthetic unresolved human report observation")
                self.assertEqual(["verification has not passed"], self.cli(target, host, "verification.current", "01")["reasons"])
                for action in ("ready", "merge"):
                    refusal = self.cli(target, host, "pr." + action, "fixture", "--phase", "01", "--confirm", expected=1)
                    self.assertEqual("phase-unverified", refusal["error"])
                (target / REPORT).write_bytes(original_report)
                git(target, "add", REPORT)
                git(target, "commit", "-m", "Restore original generated synthetic evidence")
                self.assertTrue(self.cli(target, host, "verification.current", "01")["current"])
                # Only the provider boundary is mocked. Real status/currentness
                # evaluates generated fingerprint, real Git and real receipts.
                with patch.object(delivery, "gh", return_value=subprocess.CompletedProcess([], 0, "", "")) as provider:
                    self.assertTrue(delivery.command(args, "ready")["ready"])
                    provider.assert_called_once_with(["pr", "ready", "fixture"])
                pr = {"number": 1, "url": "https://github.com/example/fixture/pull/1", "state": "OPEN", "isDraft": False,
                      "headRefName": "fixture", "statusCheckRollup": [{"name": "fixture-ci", "conclusion": "SUCCESS"}], "mergeable": "MERGEABLE"}
                with patch.object(delivery, "view", side_effect=[pr, {**pr, "state": "MERGED"}]), patch.object(delivery, "gh", return_value=subprocess.CompletedProcess([], 0, "", "")) as provider:
                    result, code = delivery.command(args, "merge")
                    self.assertEqual((True, 0), (result["merged"], code))
                    provider.assert_called_once_with(["pr", "merge", "1", "--squash"])
                with patch.object(delivery, "gh", side_effect=AssertionError("writes forbidden")) as provider:
                    with self.assertRaises(delivery.Failure) as error:
                        delivery.command(modules["core"].Args(["fixture", "--phase", "01"]), "merge")
                    self.assertEqual("merge-not-authorized", error.exception.code)
                    for change in ({"statusCheckRollup": [{"name": "ci", "conclusion": "FAILURE"}]},
                                   {"statusCheckRollup": [{"name": "ci", "status": "IN_PROGRESS"}]}, {"mergeable": "CONFLICTING"}):
                        with self.subTest(host=host, provider_state=change), patch.object(delivery, "view", return_value={**pr, **change}):
                            with self.assertRaises(delivery.Failure) as blocked:
                                delivery.command(args, "merge")
                            self.assertEqual("merge-blocked", blocked.exception.code)
                    provider.assert_not_called()
                # Every mutation below is disposable synthetic negative evidence,
                # never a fabricated positive receipt or report fingerprint.
                report_path = target / REPORT
                original = report_path.read_bytes()
                for field, value, reason in (("fingerprint", None, "verification fingerprint is absent or stale"),
                                            ("fingerprint", "0" * 64, "verification fingerprint is absent or stale"),
                                            ("revision", "0" * 40, "verified revision is absent or outside current history")):
                    metadata, body = modules["text"].split_frontmatter(original.decode())
                    if value is None:
                        metadata.pop(field)
                    else:
                        metadata[field] = value
                    report_path.write_text(modules["text"].join_frontmatter(metadata, body), encoding="utf-8")
                    self.assert_stale(target, host, modules, reason)
                    report_path.write_bytes(original)
                (target / "untracked.txt").write_text("dirty\n", encoding="utf-8")
                self.assert_stale(target, host, modules, "working tree is dirty")
                (target / "untracked.txt").unlink()
                receipts = target / ".planning/verification-receipts"
                index_path = receipts / "current.json"
                index_bytes = index_path.read_bytes()
                index_path.unlink()
                self.assert_stale(target, host, modules, "configured checks lack passing receipts at current HEAD")
                index_path.write_bytes(index_bytes)
                receipt_path = receipts / (checks["checks"][0]["receipt_id"] + ".json")
                receipt_bytes = receipt_path.read_bytes()
                receipt_path.write_text("{}", encoding="utf-8")
                self.assert_stale(target, host, modules, "configured checks lack passing receipts at current HEAD")
                receipt_path.write_bytes(receipt_bytes)
                self.assertTrue(self.cli(target, host, "verification.current", "01")["current"])
                (target / "subject.txt").write_text("changed\n", encoding="utf-8")
                git(target, "add", "subject.txt")
                git(target, "commit", "-m", "Synthetic source drift")
                self.assert_stale(target, host, modules, "source changed since the frozen verification revision")

    def assert_stale(self, target, host, modules, reason):
        current = self.cli(target, host, "verification.current", "01")
        self.assertFalse(current["current"])
        self.assertIn(reason, current["reasons"])
        delivery = modules["delivery"]
        with patch.object(delivery, "gh", side_effect=AssertionError("provider writes forbidden")) as provider, patch.object(delivery, "view", side_effect=AssertionError("provider view forbidden")) as view:
            for action in ("ready", "merge"):
                with self.assertRaises(delivery.Failure) as error:
                    delivery.command(modules["core"].Args(["fixture", "--phase", "01", "--confirm"]), action)
                self.assertEqual("verification-stale", error.exception.code)
            provider.assert_not_called()
            view.assert_not_called()


if __name__ == "__main__":
    unittest.main()
