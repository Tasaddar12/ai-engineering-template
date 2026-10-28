"""Code-review pipeline regression guards: port of upstream tests/code-review-pipeline-regression.test.cjs."""
import importlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
LIB = SOURCE / "engineer" / "bin" / "lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package; `.ai/runtime/lib` also claims the name `lib`."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB / "__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib." + name)


crp = _load("code_review_pipeline_regression")
WORKFLOW = crp.read_text(crp.WORKFLOW_PATH)
WORKFLOW_LF = crp.read_normalized(crp.WORKFLOW_PATH)
FIXER = crp.read_text(crp.FIXER_PATH)
REVIEWER = crp.read_text(crp.REVIEWER_PATH)
needs_bash = unittest.skipUnless(crp.shell_available(), "bash is required for shell fence fixtures")


def scope_section(src=WORKFLOW):
    start = src.index("const files = [];")
    return src[start:src.index("if (files.length)", start)]


class TempCase(unittest.TestCase):
    def temp(self, prefix="engineer-crp-"):
        directory = tempfile.TemporaryDirectory(prefix=prefix)
        self.addCleanup(directory.cleanup)
        return Path(directory.name)


class ComputeFileScopeParser(unittest.TestCase):
    """Upstream Bug 1: the compute_file_scope SUMMARY parser."""

    def test_4461_shipped_fence_parses_verbatim(self):
        start = WORKFLOW_LF.index('<step name="compute_file_scope">')
        marker = WORKFLOW_LF.index("EXTRACTED=$(", start)
        self.assertNotEqual(-1, marker)
        script = crp.fence_containing(WORKFLOW_LF, "EXTRACTED=$(", start)
        if not crp.shell_available():
            self.skipTest("bash unavailable")
        self.assertEqual("", crp.bash_syntax_error(script), "bash rejected the shipped fence")

    def test_4461_shipped_extractor_helper_with_adversarial_input(self):
        self.skipTest("the shipped extract_summary_files helper runs `node -`; Node is never executed by this suite")

    def test_extracts_only_created_and_modified_entries(self):
        yaml = "\n".join([
            "key-files:", "  created:", "    - app/foo.tsx", "  modified:", "    - lib/bar.ts",
            "key-decisions:", "  - We chose RSC for performance reasons",
            "patterns-established:", "  - Always validate at the boundary",
            "requirements-completed:", "  - REQ-01 done"])
        self.assertEqual(["app/foo.tsx", "lib/bar.ts"], sorted(crp.parse_key_files(yaml)))

    def test_strips_em_dash_narrative(self):
        yaml = "key-files:\n  created:\n    - app/foo.tsx — RSC catalogue with topic/mode/date filters"
        self.assertEqual(["app/foo.tsx"], crp.parse_key_files(yaml))

    def test_strips_parenthetical(self):
        yaml = "key-files:\n  created:\n    - tests/bar.test.ts (122 lines — 17 assertions)"
        self.assertEqual(["tests/bar.test.ts"], crp.parse_key_files(yaml))

    def test_hyphenated_sections_in_any_order_are_identical(self):
        a = "key-decisions:\n  - Some decision\nkey-files:\n  created:\n    - src/index.ts\npatterns-established:\n  - Some pattern"
        b = "patterns-established:\n  - Some pattern\nkey-files:\n  created:\n    - src/index.ts\nkey-decisions:\n  - Some decision"
        self.assertEqual(crp.parse_key_files(a), crp.parse_key_files(b))
        self.assertEqual(["src/index.ts"], crp.parse_key_files(a))

    def test_prose_only_bullets_from_key_decisions_are_never_files(self):
        yaml = "key-decisions:\n  - We chose RSC for performance reasons\n  - Deferred auth to Phase 3\nkey-files:\n  created:\n    - app/page.tsx"
        self.assertEqual(["app/page.tsx"], crp.parse_key_files(yaml))

    def test_2666_root_level_files_with_extensions_are_accepted(self):
        yaml = "key-files:\n  modified:\n    - package.json\n    - renovate.json\n    - .gitlab-ci.yml\n    - AGENTS.md\n    - CLAUDE.md"
        self.assertEqual([".gitlab-ci.yml", "AGENTS.md", "CLAUDE.md", "package.json", "renovate.json"], sorted(crp.parse_key_files(yaml)))

    def test_2666_nested_extensionless_build_files_are_accepted(self):
        yaml = "key-files:\n  modified:\n    - docker/Dockerfile\n    - web/Makefile"
        self.assertEqual(["docker/Dockerfile", "web/Makefile"], sorted(crp.parse_key_files(yaml)))

    def test_2666_root_level_extensionless_build_files_are_accepted(self):
        yaml = "key-files:\n  created:\n    - Dockerfile\n    - Makefile\n    - Justfile\n    - Containerfile\n    - Procfile"
        self.assertEqual(["Containerfile", "Dockerfile", "Justfile", "Makefile", "Procfile"], sorted(crp.parse_key_files(yaml)))

    def test_2666_reporter_ten_file_phase_yields_all_ten(self):
        paths = ["Dockerfile", ".gitlab-ci.yml", "renovate.json", "AGENTS.md", "CLAUDE.md", "docs/DEVELOPMENT.md",
                 "scripts/version-consistency-gate.mjs", "web/package.json", "web/version_management.md", "web/update-version.cjs"]
        yaml = "key-files:\n  created:\n" + "\n".join(f"    - {path}" for path in paths)
        self.assertEqual(sorted(paths), sorted(crp.parse_key_files(yaml)))

    def test_2666_prose_bullet_with_no_extension_and_unknown_basename_is_rejected(self):
        yaml = "key-decisions:\n  - topic/mode/date filters\nkey-files:\n  created:\n    - app/page.tsx"
        self.assertEqual(["app/page.tsx"], crp.parse_key_files(yaml))

    def test_2666_em_dash_stripping_still_works_on_an_accepted_root_file(self):
        yaml = "key-files:\n  modified:\n    - Dockerfile — multi-stage build"
        self.assertEqual(["Dockerfile"], crp.parse_key_files(yaml))

    def test_workflow_contains_hyphen_aware_boundary_regex(self):
        self.assertTrue("[\\\\w-]" in scope_section() or "[\\w-]" in scope_section())

    def test_workflow_contains_em_dash_split_and_parenthetical_strip(self):
        section = scope_section()
        self.assertIn("replace(/\\s+\\([^)]*\\)\\s*$, '')".replace("$,", "$/,"), section)
        self.assertIn("split(/\\s+—\\s", section)

    def test_2666_workflow_does_not_carry_the_buggy_slash_and_extension_predicate(self):
        self.assertNotIn("/\\//.test(raw) && /\\.[A-Za-z0-9]+$/.test(raw)", scope_section())

    def test_2666_workflow_accepts_known_extensionless_build_files(self):
        self.assertRegex(scope_section(), r"(?i)dockerfile")

    def test_2666_tier3_cross_check_uses_exact_whole_line_matching(self):
        self.assertIn("grep -Fxq", WORKFLOW)
        self.assertNotIn('case "$IN_SCOPE"', WORKFLOW)


class SeverityLabelParser(unittest.TestCase):
    """Upstream Bug 2: present_results accepts both critical: and blocker:."""

    def test_blocker_is_parsed_as_critical(self):
        fm = "phase: 03-courses\nfindings:\n  blocker: 8\n  warning: 2\n  info: 0\n  total: 10\nstatus: issues_found"
        self.assertEqual(8, crp.parse_frontmatter_critical(fm))

    def test_critical_is_parsed(self):
        fm = "phase: 03-courses\nfindings:\n  critical: 5\n  warning: 1\n  info: 0\n  total: 6\nstatus: issues_found"
        self.assertEqual(5, crp.parse_frontmatter_critical(fm))

    def test_neither_label_returns_zero(self):
        self.assertEqual(0, crp.parse_frontmatter_critical("findings:\n  warning: 3\n  info: 1\n  total: 4"))

    def test_present_results_grep_accepts_both_labels(self):
        self.assertIn('grep -E "^[[:space:]]*(critical|blocker):"', WORKFLOW)

    def test_present_results_includes_bl_headings_alongside_cr_and_wr(self):
        self.assertTrue("### BL-" in WORKFLOW and "### CR-" in WORKFLOW and "### WR-" in WORKFLOW
                        or "^### CR-\\|^### BL-\\|^### WR-" in WORKFLOW)


class FixerBlockerTier(unittest.TestCase):
    """Upstream Bug 3: the fixer treats BL-* as Critical-tier alongside CR-*."""

    def test_finding_parser_documents_bl_as_critical_tier_equivalent(self):
        section = crp.tag_section(FIXER, "finding_parser")
        self.assertIsNotNone(section, "code-fixer.md must have a <finding_parser> block")
        self.assertIn("BL-", section)

    def test_parse_findings_documents_severity_as_cr_or_bl(self):
        section = crp.step_section(FIXER, "parse_findings")
        self.assertIsNotNone(section, "code-fixer.md must have a parse_findings step")
        self.assertTrue("CR-* or BL-*" in section or "CR-* and BL-*" in section)

    def test_critical_warning_filter_set_includes_bl(self):
        section = crp.step_section(FIXER, "parse_findings")
        index = section.index("critical_warning")
        line = section[section.rfind("\n", 0, index):section.find("\n", index)]
        self.assertIn("BL-", line)

    def test_sort_order_mentions_bl(self):
        self.assertIn("BL-", crp.step_section(FIXER, "parse_findings"))


class ReviewerLabelEquivalence(unittest.TestCase):
    """Upstream reviewer contract: blocker:/BL- are tier-equivalent to critical:/CR-."""

    def test_write_review_documents_blocker_as_accepted_alternative(self):
        section = crp.step_section(REVIEWER, "write_review")
        self.assertIsNotNone(section, "code-reviewer.md must have a write_review step")
        self.assertIn("blocker", section)

    def test_write_review_acknowledges_bl_prefix(self):
        self.assertIn("BL-", crp.step_section(REVIEWER, "write_review"))


class TildePathExpansion(TempCase):
    """Upstream Bug 4 (#2352): compute_file_scope tilde-expands ~/ paths before the deleted-file filter."""

    def test_tilde_expansion_block_precedes_the_deleted_file_filter(self):
        post = WORKFLOW.index("**Post-processing (all tiers):**")
        expand = WORKFLOW.index("EXPANDED_FILES=()", post)
        case = WORKFLOW.index('case "$file" in', post)
        self.assertLess(case, expand + 400)
        window = WORKFLOW[case:case + 200]
        self.assertIn('"~/"*)', window)
        self.assertIn("${HOME}${file#\\~}", window)
        self.assertLess(expand, WORKFLOW.index("DELETED_COUNT=0", post))

    def run_post(self, home, files):
        script = crp.post_processing_script(WORKFLOW_LF)
        return crp.run_bash(script, files, env={**os.environ, "HOME": crp.posix(home)})

    def planted_home(self):
        home = self.temp("engineer-2352-home-")
        target = home / ".claude" / "engineer" / "workflows" / "verify-phase.md"
        target.parent.mkdir(parents=True)
        target.write_text("# real file\n", encoding="utf-8")
        return home, "~/.claude/engineer/workflows/verify-phase.md"

    @needs_bash
    def test_ac1_tilde_path_to_a_real_file_survives(self):
        home, tilde = self.planted_home()
        result = self.run_post(home, [tilde])
        self.assertEqual(0, result.returncode, result.stderr)
        normalized = result.stdout.replace("\\", "/")
        self.assertIn(home.name + "/.claude/engineer/workflows/verify-phase.md", normalized)  # msys prints /tmp/... for the temp dir
        self.assertIn("DELETED_COUNT=0", result.stdout)
        self.assertIn("REVIEW_FILES_COUNT=1", result.stdout)

    @needs_bash
    def test_ac2_tilde_path_to_a_missing_file_is_excluded_as_deleted(self):
        home, _ = self.planted_home()
        result = self.run_post(home, ["~/.claude/engineer/workflows/does-not-exist.md"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("DELETED_COUNT=1", result.stdout)
        self.assertIn("REVIEW_FILES_COUNT=0", result.stdout)

    @needs_bash
    def test_ac3_all_real_tilde_scope_is_not_emptied(self):
        home, tilde = self.planted_home()
        result = self.run_post(home, [tilde])
        count = int(result.stdout.split("REVIEW_FILES_COUNT=")[1].split()[0])
        self.assertGreater(count, 0)

    @needs_bash
    def test_ac4_mixed_tilde_and_missing_relative_resolve_independently(self):
        home, tilde = self.planted_home()
        result = self.run_post(home, [tilde, "this/relative/path/does-not-exist.md"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("DELETED_COUNT=1", result.stdout)
        self.assertIn("REVIEW_FILES_COUNT=1", result.stdout)
        survivors = [line for line in result.stdout.split("\n")
                     if not line.startswith("Filtered ") or "deleted files" not in line]
        survivors = [line for line in survivors if not line.startswith("  - ")]
        self.assertNotIn("this/relative/path/does-not-exist.md", "\n".join(survivors))
        self.assertIn("\n  - this/relative/path/does-not-exist.md\n", "\n" + result.stdout.replace("\r", "") + "\n")


class DiffBaseSingleOwner(unittest.TestCase):
    """Upstream Bug 5/6 -> #5164: every diff-base site asks the one evaluation-scope owner."""

    def test_no_workflow_fence_hand_rolls_an_anchor_grep_or_range(self):
        import re
        self.assertIn("engineer_run check evaluation-scope", WORKFLOW_LF)
        self.assertNotIn("--diff-filter=A", WORKFLOW_LF)
        self.assertEqual([], crp.find_grep_sites(WORKFLOW_LF))
        self.assertIsNone(re.search(r"git diff --name-only[^\n]*(?:DIFF_BASE|HEAD)", WORKFLOW_LF))

    def test_structural_pre_pass_asks_the_resolver_too(self):
        self.skipTest("engineer/workflows/code-review/steps/structural-pre-pass.md (fallow pre-pass) absent in this repo")

    def test_2666_tier3_cross_checks_the_summary_scope_against_the_resolver(self):
        self.assertIn("SUMMARY scope was missing", WORKFLOW_LF)
        self.assertIn("engineer_run check evaluation-scope", WORKFLOW_LF)

    def test_t1_tier3_and_fallow_bases_are_the_same_anchor(self):
        self.skipTest("fallow pre-pass step absent in this repo, and the Tier-3 fence reads resolver JSON through `node -e`")

    def test_t2_tier3_scope_is_the_union_of_recorded_task_commits(self):
        self.skipTest("the Tier-3 fence reads resolver JSON through `node -e`; Node is never executed by this suite")

    def test_t3_no_committed_phase_directory_leaves_base_and_scope_empty(self):
        self.skipTest("the Tier-3 fence reads resolver JSON through `node -e`; Node is never executed by this suite")


class ModuleUnitsA(TempCase):
    def test_is_acceptable_path(self):
        self.assertTrue(crp.is_acceptable_path("a/b.ts"))
        self.assertTrue(crp.is_acceptable_path("Dockerfile"))
        self.assertTrue(crp.is_acceptable_path("x/MAKEFILE"))
        self.assertFalse(crp.is_acceptable_path("topic/mode/date filters"))

    def test_step_and_tag_sections(self):
        src = '<step name="a">one</step><step name="b">two</step><x>tag</x>'
        self.assertEqual('<step name="b">two', crp.step_section(src, "b"))
        self.assertIsNone(crp.step_section(src, "missing"))
        self.assertEqual("<x>tag", crp.tag_section(src, "x"))
        self.assertIsNone(crp.tag_section(src, "y"))
        self.assertEqual("bc", crp.between("abcde", "b", "d"))
        self.assertIsNone(crp.between("abc", "z", "c"))

    def test_bash_fences_and_fence_containing(self):
        src = "x\n```bash\na=1\n```\ntext\n```bash\nMARK=2\nb\n```\n```py\nz\n```\n"
        self.assertEqual(["a=1", "MARK=2\nb"], crp.bash_fences(src))
        self.assertEqual("MARK=2\nb", crp.fence_containing(src, "MARK"))
        with self.assertRaises(ValueError):
            crp.fence_containing(src, "absent")
        with self.assertRaises(ValueError):
            crp.fence_containing("```bash\nMARK\n", "MARK")

    def test_fold_continuations_and_grep_site_scan(self):
        self.assertEqual("a  b", crp.fold_shell_continuations("a \\\n b"))
        wrapped = "```bash\nBASE=$(git log --format=%H \\\n  --grep='x' | tail -1)\n```\n"
        self.assertEqual(1, len(crp.find_grep_sites(wrapped)))
        self.assertEqual([], crp.find_grep_sites("```python\nBASE=$(git log --grep=x)\n```\n"))
        self.assertEqual([], crp.find_grep_sites("```bash\nBASE=$(git log --grep=x)\n"))

    def test_parse_frontmatter_critical_takes_first_label_only(self):
        self.assertEqual(2, crp.parse_frontmatter_critical("  blocker: 2\n  critical: 9"))
        self.assertEqual(0, crp.parse_frontmatter_critical("  critical: abc"))

    @needs_bash
    def test_post_processing_script_requires_the_section_and_runs(self):
        with self.assertRaises(ValueError):
            crp.post_processing_script("no section")
        src = "**Post-processing (all tiers):**\n```bash\nEXPANDED_FILES=()\nREVIEW_FILES=(\"${REVIEW_FILES[@]}\")\n```\n```bash\nDELETED_COUNT=0\n```\n"
        result = crp.run_bash(crp.post_processing_script(src), ["x"])
        self.assertIn("REVIEW_FILES_COUNT=1", result.stdout)
        self.assertEqual("", crp.bash_syntax_error("echo ok"))
        self.assertNotEqual("", crp.bash_syntax_error("if then"))


if __name__ == "__main__":
    unittest.main()
