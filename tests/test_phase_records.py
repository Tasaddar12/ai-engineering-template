"""Record navigation and preparation behavior, including fresh-worktree handoffs."""
from pathlib import Path
import hashlib
import os
import re
import sys
import unittest
from urllib.parse import unquote, urlsplit

import yaml

import test_phase_runtime as fixtures


SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / ".ai/runtime"))
from phase_runner import validate_summary  # noqa: E402
from phase_records import acceptance_outcomes, PhaseError, git as record_git, overlaps, owns, read_yaml, record, file_template, load_phase  # noqa: E402


class AcceptanceParsingTests(unittest.TestCase):
    def test_plain_and_bold_ids_preserve_order_and_outcome_text(self):
        body = ("## Acceptance\n\n"
                "- A1: Plain outcome.\n"
                "- [ ] **AUTH-02**: Outcome with **bold text**.\n"
                "- [x] **A3:** Checked outcome.\n"
                "- [X] A4: Another checked outcome.\n"
                "\n## Other\n- A5: Outside acceptance.\n")
        self.assertEqual(acceptance_outcomes(body), [
            ("A1", "Plain outcome."), ("AUTH-02", "Outcome with **bold text**."),
            ("A3", "Checked outcome."), ("A4", "Another checked outcome.")])

    def test_duplicate_ids_rejected_across_formats(self):
        for duplicate in ("A1:", "**A1**:", "**A1:**"):
            with self.subTest(duplicate=duplicate):
                with self.assertRaisesRegex(PhaseError, "Duplicate acceptance identifiers"):
                    acceptance_outcomes(f"## Acceptance\n- A1: First.\n- {duplicate} Second.\n")

    def test_unbalanced_bold_is_not_an_identifier(self):
        for malformed in ("**A1:", "A1**:", "**A1*:"):
            with self.subTest(malformed=malformed):
                self.assertEqual(acceptance_outcomes(f"## Acceptance\n- {malformed} Outcome.\n"), [])

    def test_empty_outcome_does_not_consume_next_bullet(self):
        self.assertEqual(acceptance_outcomes("## Acceptance\n- **A1:**\n- A2: Second.\n"),
                         [("A1", ""), ("A2", "Second.")])


class PhaseRecordTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PhaseRuntimeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_phase_loading_accepts_bold_ids_and_rejects_styled_duplicates(self):
        f = self.fixture
        context_path = f.checkout / fixtures.PHASE_PATH / "01-CONTEXT.md"
        metadata, body = record(context_path)
        for styled in ("**A1**:", "**A1:**"):
            with self.subTest(styled=styled):
                styled_body = body.replace("A1:", styled)
                f.record(context_path.relative_to(f.checkout), metadata, styled_body)
                self.assertEqual(load_phase(f.checkout, "01", ready=True).acceptance, ["A1"])
                duplicate_body = styled_body.replace(styled, "A1: Duplicate.\n- " + styled, 1)
                f.record(context_path.relative_to(f.checkout), metadata, duplicate_body)
                with self.assertRaisesRegex(PhaseError, "Duplicate acceptance identifiers"):
                    load_phase(f.checkout, "01", ready=True)

    def test_new_phase_stays_pending_and_allocates_across_worktrees(self):
        f = self.fixture
        f.cli("new", "second", "--title", "Second change")
        context = f.checkout / ".planning/phases/02-second/02-CONTEXT.md"
        self.assertEqual(record(context)[0]["approval"], "pending")
        self.assertIn("02-CONTEXT.md", (f.checkout / ".planning/ROADMAP.md").read_text(encoding='utf-8'))
        self.assertEqual(f.git(f.checkout, "status", "--porcelain"), "")
        sibling = f.primary / ".worktrees/another"
        f.git(f.primary, "worktree", "add", "-b", "codex/another", str(sibling), "codex/phase-test")
        f.cli("new", "third", "--title", "Third change", root=sibling)
        self.assertTrue((sibling / ".planning/phases/03-third/03-CONTEXT.md").is_file())
        f.cli("run", "02", succeeds=False)
        self.assertEqual(f.events(), [])
        f.assert_primary_untouched()

    def test_sync_commits_only_derived_state(self):
        f = self.fixture
        before = f.git(f.checkout, "rev-parse", "HEAD")
        f.cli("sync")
        paths = f.git(f.checkout, "diff", "--name-only", before, "HEAD").splitlines()
        self.assertEqual(paths, [".planning/STATE.md"])
        self.assertIn("01-example", (f.checkout / ".planning/STATE.md").read_text(encoding='utf-8'))
        f.assert_primary_untouched()

    def test_full_upstream_outputs_execute_verify_uat_and_preserve_authored_state(self):
        f = self.fixture
        f.prepare_remote()
        f.configure(PHASE_FIXTURE_MODE="full-templates")
        context_path = f.checkout / fixtures.PHASE_PATH / "01-CONTEXT.md"
        context_data, local_context = record(context_path)
        context_data["uat"] = True
        context_body = file_template(f.checkout, "context.md")
        context_body = context_body.replace("[X]", "01").replace("[Name]", "Example")
        context_body = context_body.replace("[Clear statement of what this phase delivers — the scope anchor. This comes from ROADMAP.md and is fixed. Discussion clarifies implementation within this boundary.]", "Deliver integrated fixture output.")
        f.record(fixtures.PHASE_PATH / "01-CONTEXT.md", context_data,
                 context_body + "\n## Acceptance\n\n- [ ] **A1:** Assigned output works.\n\n## Authorization\n\nUser requested fixture execution and testing.\n")
        plan_path = f.checkout / fixtures.PHASE_PATH / "01-01-PLAN.md"
        plan_data, _ = record(plan_path)
        plan = file_template(f.checkout, "phase-prompt.md")
        original_metadata = read_yaml(plan.split("---", 2)[1])
        original_metadata.update(plan_data, wave=1, user_setup=[], must_haves={
            "truths": ["Assigned output exists after execution"],
            "artifacts": [{"path": "src/01-01.txt", "provides": "Fixture output"}], "key_links": []})
        plan_body = plan.split("---", 2)[2]
        # Checkpoints are conditional examples. This fixture has no human decision
        # inside execution; actual UAT is exercised separately below.
        plan_body = re.sub(r'<task type="checkpoint:.*?</task>', "", plan_body, flags=re.S)
        f.record(fixtures.PHASE_PATH / "01-01-PLAN.md", original_metadata,
                 plan_body + "\n## Documentation\n\nNo external guide obligation for the fixture.\n")
        state_path = f.checkout / ".planning/STATE.md"
        state_path.write_text(file_template(f.checkout, "state.md") + "\nCoordinator note: preserve this decision.\n", encoding="utf-8")
        f.commit("Prepare full upstream artifact outputs")
        f.cli("check", "01")
        f.cli("run", "01")
        self.assertIn("01-01 implemented", (f.checkout / "src/01-01.txt").read_text(encoding='utf-8'))
        summary_data, summary_body = record(f.summary("01-01"))
        self.assertEqual(summary_data["requirements-completed"], ["R1"])
        self.assertIn("## Performance", summary_body)
        f.cli("verify", "01")
        report = f.checkout / fixtures.PHASE_PATH / "01-VERIFICATION.md"
        self.assertIn("### Key Link Verification", record(report)[1])
        f.cli("uat", "01")
        uat = f.checkout / fixtures.PHASE_PATH / "01-UAT.md"
        data, body = record(uat)
        self.assertEqual(data["source"], [str(fixtures.PHASE_PATH / "01-01-SUMMARY.md").replace("\\", "/")])
        self.assertIn("## Current Test", body)
        self.assertIn("expected: Assigned output works.", body)
        uat.write_text(uat.read_text(encoding='utf-8') + "\n## Interview Notes\n\nPreserve the user's additional context.\n", encoding="utf-8")
        f.commit("Record authored UAT context")
        f.cli("uat", "01", "--case", "1", "--result", "fail", "--note", "Observed issue")
        f.cli("uat", "01", "--case", "1", "--result", "pass", "--note", "Retest observed output")
        data, body = record(uat)
        self.assertEqual(data["status"], "complete")
        self.assertEqual(len(data["cases"][0]["observations"]), 2)
        self.assertIn("Preserve the user's additional context.", body)
        f.cli("sync")
        self.assertIn("## Accumulated Context", state_path.read_text(encoding='utf-8'))
        self.assertIn("Coordinator note: preserve this decision.", state_path.read_text(encoding='utf-8'))
        f.publish()
        f.assert_primary_untouched()

    def test_legacy_records_and_old_checkpoint_do_not_disappear_from_status(self):
        f = self.fixture
        f.write(f.checkout, ".ai/PROJECT.md", "Legacy identity must be reconciled.\n")
        result = f.cli("status", succeeds=False)
        self.assertIn("Legacy project records remain", result.stderr)
        (f.checkout / ".ai/PROJECT.md").unlink()
        legacy_relative = str(fixtures.PHASE_PATH).replace("\\", "/").replace(".planning/", ".ai/")
        key = hashlib.sha256((str(f.checkout) + "\n" + legacy_relative).encode()).hexdigest()[:20]
        path = f.primary / ".git/ai/phases" / f"01-example-{key}" / "state.yaml"
        path.parent.mkdir(parents=True)
        path.write_text("components: {}\n", encoding="utf-8")
        result = f.cli("status", "01", succeeds=False)
        self.assertIn("Legacy checkpoint exists", result.stderr)
        self.assertTrue(path.exists())

    def test_explicit_files_deleted_allows_removal_with_coverage(self):
        self.deletion_case(declared=True)

    def test_files_modified_does_not_authorize_unannounced_removal(self):
        self.deletion_case(declared=False)

    def deletion_case(self, declared):
        f = self.fixture
        f.write(f.checkout, "src/obsolete.txt", "Obsolete fixture output.\n")
        f.component("01-01", files=["src/obsolete.txt"], checks=[[
            sys.executable, "-c", "from pathlib import Path; assert not Path('src/obsolete.txt').exists()"]])
        path = f.checkout / fixtures.PHASE_PATH / "01-01-PLAN.md"
        data, body = record(path)
        if declared:
            data.update(files_modified=[], files_deleted=["src/obsolete.txt"])
        f.record(path.relative_to(f.checkout), data, body)
        f.configure(PHASE_FIXTURE_MODE="delete")
        f.commit("Prepare declared deletion" if declared else "Prepare undeclared deletion regression")
        result = f.cli("run", "01", succeeds=declared)
        self.assertEqual((f.checkout / "src/obsolete.txt").exists(), not declared)
        if not declared:
            self.assertIn("undeclared deletion", result.stdout + result.stderr)
            self.assertTrue(Path(f.events()[0]["worktree"]).exists())

    def test_optional_summary_variant_retains_original_sections_and_adds_required_evidence(self):
        f = self.fixture
        # An explicitly supplied variant remains supported; no compact variant
        # is shipped by the template. Exercise that input without a deleted file.
        metadata = {"phase": "01-example", "plan": "01"}
        body = ("# Component summary\n\n## Accomplishments\n\nImplemented the assigned output.\n\n"
                "## Task Commits\n\nRecorded implementation commit.\n\n"
                "## Files Created/Modified\n\nsrc/01-01.txt contains the result.\n\n"
                "## Decisions & Deviations\n\nUse assigned output interface.\n\n"
                "## Next Phase Readiness\n\nReady for independent verification.\n")
        metadata.update(status="complete", acceptance=["A1"], documentation=[], **{"requirements-completed": ["R1"]})
        summary = f.summary("01-01")
        f.record(summary.relative_to(f.checkout), metadata, body)
        phase = load_phase(f.checkout, "01", ready=True)
        with self.assertRaisesRegex(PhaseError, "Decisions Made"):
            validate_summary(phase, phase.components["01-01"], f.checkout)
        for title, evidence in (("Decisions Made", "Use assigned output interface."),
                                ("Deviations from Plan", "None."),
                                ("Issues Encountered", "None."),
                                ("User Setup Required", "None."),
                                ("Checks", "Named fixture check asserted expected output; exit 0.")):
            body += f"\n## {title}\n\n{evidence}\n"
        f.record(summary.relative_to(f.checkout), metadata, body)
        validate_summary(phase, phase.components["01-01"], f.checkout)
        self.assertIn("## Decisions & Deviations", record(summary)[1])

    def test_native_tdd_feature_plan_runs_named_red_and_green_assertions(self):
        f = self.fixture
        f.write(f.checkout, "src/total.py", "def total(values):\n    return 0\n")
        f.component("01-01", files=["src/total.py", "tests/test_total.py"], checks=[[
            sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_total.py", "-v"]])
        path = f.checkout / fixtures.PHASE_PATH / "01-01-PLAN.md"
        metadata, _ = record(path)
        metadata["type"] = "tdd"
        source = Path(os.environ.get("TDD_REFERENCE_TEST_SOURCE", str(SOURCE / ".ai/runtime/TEMPLATE-CONTRACT.md")))
        reference = source.read_text(encoding="utf-8")
        feature = re.search(r"(?ms)^```xml\n(<feature>.*?</feature>)\n```", reference)[1]
        feature = (feature.replace("[One observable behavior]", "Sum nonempty inputs")
                    .replace("[Exact implementation and test paths]", "src/total.py, tests/test_total.py")
                    .replace("[Inputs, expected outputs, boundary cases and the assertion that fails before repair]", "total([1, 2, 3]) returns 6; name the assertion test_total_nonempty")
                    .replace("[Implementation approach after the failing behavioral check is established]", "Return sum(values) after observing the named assertion fail"))
        body = ("<objective>Sum nonempty inputs correctly.</objective>\n"
                "<context>Inspect src/total.py and the assigned acceptance.</context>\n" + feature +
                "\n<verification>Run the named assertion through unittest.</verification>\n"
                "<success_criteria>The named assertion fails before and passes after repair.</success_criteria>\n"
                "<output>Write the assigned SUMMARY with RED/GREEN evidence.</output>\n")
        f.record(path.relative_to(f.checkout), metadata, body + "\n## Documentation\n\nNo external guide change required.\n")
        prepared = path.read_text(encoding="utf-8")
        path.write_text(re.sub(r"<behavior>.*?</behavior>", "", prepared, flags=re.S), encoding="utf-8")
        self.assertIn("TDD feature missing <behavior>", f.cli("check", "01", succeeds=False).stderr)
        self.assertEqual(f.events(), [])
        path.write_text(prepared, encoding="utf-8")
        f.configure(PHASE_FIXTURE_MODE="native-tdd")
        f.commit("Prepare native feature-shaped TDD plan")
        f.cli("check", "01")
        f.cli("run", "01")
        summary = f.summary("01-01").read_text(encoding="utf-8")
        self.assertIn("AssertionError: 0 != 6", summary)
        self.assertIn("exit 0; one named test passed", summary)
        self.assertIn("## Performance", summary)
        self.assertIn("<feature>", path.read_text(encoding='utf-8'))
        self.assertNotIn("<tasks>", path.read_text(encoding='utf-8'))
        history = f.git(f.checkout, "log", "--format=%s")
        self.assertIn("test: specify total", history)
        self.assertIn("feat: implement total", history)
        f.assert_primary_untouched()

    def test_new_phase_refuses_concrete_legacy_sibling_without_losing_it(self):
        f = self.fixture
        sibling = f.primary / ".worktrees/legacy-sibling"
        f.git(f.primary, "worktree", "add", "-b", "codex/legacy-sibling", str(sibling), "codex/phase-test")
        old = f.write(sibling, ".ai/phases/02-preserved/02-CONTEXT.md", "Preserve old pending work.\n")
        f.git(sibling, "add", "--all")
        f.git(sibling, "commit", "-m", "Preserve legacy phase input")
        # A primary's empty historical README alone must not be the reason to block.
        f.write(f.primary, ".ai/phases/README.md", "Old directory guide.\n")
        result = f.cli("new", "next", "--title", "Next phase", succeeds=False)
        self.assertIn("Legacy phases remain in registered worktree", result.stderr)
        self.assertIn("legacy-sibling", result.stderr)
        self.assertEqual(old.read_text(encoding='utf-8'), "Preserve old pending work.\n")
        self.assertFalse((f.checkout / ".planning/phases/02-next").exists())

    def test_native_plan_rejects_missing_task_action_and_unresolved_checkpoint(self):
        f = self.fixture
        path = f.checkout / fixtures.PHASE_PATH / "01-01-PLAN.md"
        original = path.read_text(encoding='utf-8')
        path.write_text(re.sub(r"<action>.*?</action>", "", original), encoding='utf-8')
        self.assertIn("task missing <action>", f.cli("check", "01", succeeds=False).stderr)
        path.write_text(original.replace("autonomous: true", "autonomous: false"), encoding='utf-8')
        self.assertIn("checkpoint/non-autonomous", f.cli("check", "01", succeeds=False).stderr)
        self.assertEqual(f.events(), [])

    def test_git_text_normalizes_line_endings_while_raw_preserves_them(self):
        f = self.fixture
        content = b"first\r\nsecond\rthird\n"
        (f.checkout / "line-endings.txt").write_bytes(content)
        f.commit("Record a blob with mixed line endings")
        self.assertEqual(record_git(f.checkout, "show", "HEAD:line-endings.txt"), "first\nsecond\nthird")
        self.assertEqual(record_git(f.checkout, "show", "HEAD:line-endings.txt", raw=True), content.decode())

    def test_readiness_rejects_coordinator_ownership_and_bad_configuration(self):
        f = self.fixture
        for path in (".ai/", ".PLANNING/PHASES/", ".planning/state.md", ".planning/config.yaml"):
            with self.subTest(path=path):
                f.component("01-01", files=[path])
                f.commit("Declare invalid coordinator ownership")
                f.cli("check", "01", succeeds=False)
        f.component("01-01")
        f.config["execution"]["max_parallel"] = True
        f.configure()
        f.commit("Reject boolean concurrency")
        f.cli("check", "01", succeeds=False)
        self.assertEqual(f.events(), [])

    def test_approved_flag_does_not_accept_placeholder_authorization(self):
        f = self.fixture
        context = f.checkout / fixtures.PHASE_PATH / "01-CONTEXT.md"
        context.write_text(context.read_text(encoding='utf-8').replace(
            "The user approved implementing and verifying this phase in worktrees.", "CHANGEME"
        ), encoding="utf-8")
        f.commit("Leave authorization unresolved")
        f.cli("check", "01", succeeds=False)
        self.assertEqual(f.events(), [])

    def test_explicit_replan_after_check_mutation_preserves_prior_implementation(self):
        f = self.fixture
        original = f.config["verification"]["commands"]
        f.config["verification"]["commands"] = [[sys.executable, "-c",
            "from pathlib import Path; import subprocess; "
            "p=Path('check-created.txt'); apply=Path.cwd().name=='phase'; "
            "p.write_text('Unintended change', encoding='utf-8') if apply else None; "
            "subprocess.run(['git','add','check-created.txt'],check=True) if apply else None; "
            "subprocess.run(['git','commit','-m','Unintended check commit'],check=True) if apply else None"]]
        f.configure()
        f.commit("Prepare a check that unexpectedly changes source")
        f.cli("run", "01", succeeds=False)
        self.assertTrue((f.checkout / "check-created.txt").is_file())
        (f.checkout / "check-created.txt").unlink()
        f.config["verification"]["commands"] = original
        f.configure()
        f.commit("Resolve inspected check mutation and restore read-only check")
        f.cli("run", "01", "--replan", "--workers-stopped")
        self.assertEqual(len(f.events()), 1)
        self.assertTrue(f.summary("01-01").is_file())
        self.assertFalse((f.checkout / "check-created.txt").exists())

    def test_committed_verification_remains_visible_without_local_checkpoint(self):
        f = self.fixture
        f.cli("run", "01")
        f.cli("verify", "01")
        sibling = f.primary / ".worktrees/inspection"
        f.git(f.primary, "worktree", "add", "-b", "codex/inspection", str(sibling), "codex/phase-test")
        before = f.git(sibling, "rev-parse", "HEAD")
        result = f.cli("status", "01", root=sibling)
        self.assertIn("recorded verification: passed", result.stdout)
        self.assertIn("checkpoint unavailable", result.stdout)
        self.assertEqual(f.git(sibling, "rev-parse", "HEAD"), before)


class OwnershipBoundaryTests(unittest.TestCase):
    def test_exact_ownership_and_conservative_overlap_have_separate_case_rules(self):
        self.assertTrue(owns("README.md", "README.md"))
        self.assertFalse(owns("README.md", "readme.md"))
        self.assertFalse(owns("src/", "Src/component.py"))
        self.assertTrue(overlaps(["README.md"], ["readme.md"]))
        self.assertTrue(overlaps(["src/"], ["Src/component.py"]))


class DocumentNavigationTests(unittest.TestCase):
    def test_active_markdown_links_resolve_to_files_and_headings(self):
        documents = [SOURCE / "AGENTS.md", SOURCE / "README.md"]
        for directory in (".ai", ".agents", ".planning", "docs"):
            for path in (SOURCE / directory).rglob("*.md"):
                relative = path.relative_to(SOURCE).as_posix()
                # Preserved upstream teaching examples are checked by the dedicated
                # provenance/reference suite, not as active checkout-relative links.
                if relative.startswith(".ai/templates/") and path.name not in ("ADR.md", "CURRENT-SPEC.md"):
                    continue
                documents.append(path)
        checked = 0
        for path in documents:
            body = re.sub(r"(?ms)^```.*?^```[^\n]*$", "", path.read_text(encoding="utf-8-sig"))
            body = re.sub(r"`+[^`\n]*`+", "", body)
            for match in re.finditer(r"\[[^\]\n]+\]\((<[^>]+>|[^)\s]+)\)", body):
                target = match[1].strip("<>")
                parts = urlsplit(target)
                if parts.scheme or parts.netloc:
                    continue
                destination = (path.parent / unquote(parts.path)).resolve() if parts.path else path
                with self.subTest(file=path.relative_to(SOURCE), link=target):
                    self.assertTrue(destination.exists(), f"Missing linked file: {destination}")
                    if parts.fragment and destination.suffix == ".md":
                        headings = re.findall(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", destination.read_text(encoding="utf-8-sig"))
                        anchors = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
                        self.assertIn(unquote(parts.fragment), anchors)
                checked += 1
        self.assertGreater(checked, 100, "Link inspection unexpectedly skipped the active documentation")

    def test_repository_skills_have_discoverable_metadata(self):
        skills_root = SOURCE / ".agents/skills"
        skill_dirs = [path for path in skills_root.iterdir() if path.is_dir()]
        self.assertTrue(skill_dirs, "Repository skills are missing")
        names = set()
        for directory in skill_dirs:
            with self.subTest(skill=directory.name):
                metadata, body = record(directory / "SKILL.md")
                name = metadata.get("name")
                description = metadata.get("description")
                self.assertIsInstance(name, str)
                self.assertEqual(name, directory.name)
                self.assertRegex(name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
                self.assertLessEqual(len(name), 64)
                self.assertNotIn(name, names)
                names.add(name)
                self.assertIsInstance(description, str)
                self.assertTrue(description.strip())
                self.assertLessEqual(len(description), 1024)
                self.assertTrue(body.strip())

    def test_templates_and_config_use_readable_unambiguous_yaml(self):
        for path in (SOURCE / ".ai/templates").glob("*.md"):
            if path.read_text(encoding="utf-8").startswith("---\n"):
                with self.subTest(template=path.name):
                    metadata, body = record(path)
                    self.assertTrue(metadata)
                    self.assertTrue(body.strip())
        config = read_yaml((SOURCE / ".planning/config.yaml").read_text(encoding="utf-8"))
        self.assertEqual(config["verification"]["commands"], [])
        with self.assertRaisesRegex(PhaseError, "Duplicate YAML key"):
            read_yaml("approval: pending\napproval: approved\n")


if __name__ == "__main__":
    unittest.main()
