"""Code-review pipeline regression guards: port of upstream tests/code-review-pipeline-regression.test.cjs."""
import importlib
import re
import shutil
import importlib.util
import os
import json
import subprocess
import shlex
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
# The counts fence forks grep/sed/awk per run; on Windows Git Bash each run costs seconds, so the executed matrices
# are POSIX-only by default (upstream skips them on win32 too). Set ENGINEER_CRP_FORCE_BASH=1 to run them anyway.
needs_fast_bash = unittest.skipUnless(
    crp.shell_available() and (os.name != "nt" or os.environ.get("ENGINEER_CRP_FORCE_BASH")),
    "POSIX-only executed fence matrix (set ENGINEER_CRP_FORCE_BASH=1 to force on Windows)")


def runtime_query(directory, *arguments, input=None):
    """Exercise the registered CLI, isolated from ambient Python packages."""
    return subprocess.run([sys.executable, "-I", str(SOURCE / "engineer/bin/engineer.py"),
                           "query", *arguments], cwd=directory, input=input,
                          capture_output=True, text=True, encoding="utf-8", timeout=60,
                          env={**os.environ, "ENGINEER_ROOT": str(directory)})


def summary_files(text):
    with tempfile.TemporaryDirectory(prefix="engineer-summary-") as directory:
        Path(directory, "SUMMARY.md").write_text("---\n" + text + "\n---\n", encoding="utf-8")
        result = runtime_query(directory, "review.summary-files", "SUMMARY.md", "--raw")
        if result.returncode:
            raise AssertionError(result.stderr or result.stdout)
        return result.stdout.splitlines()


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
        self.assertEqual(["Dockerfile", "app/page.tsx", "tests/bar.test.ts"], summary_files(
            "key-files:\n  created:\n    - Dockerfile — multi-stage build\n"
            "    - app/page.tsx — filters for topic/mode/date\n"
            "    - tests/bar.test.ts (122 lines — 17 assertions)\n"
            "key-decisions:\n  - ignore/a/prose narrative"))

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

    def test_runtime_stops_at_hyphenated_section_boundaries(self):
        self.assertEqual(["src/index.ts"], summary_files(
            "key-files:\n  created:\n    - src/index.ts\nkey-decisions:\n  - topic/mode/date filters"))

    def test_runtime_strips_em_dash_and_parenthetical_narrative(self):
        self.assertEqual(["app/foo.tsx", "tests/bar.test.ts"], summary_files(
            "key-files:\n  created:\n    - app/foo.tsx — topic/mode/date filters\n"
            "    - tests/bar.test.ts (122 lines — 17 assertions)"))

    def test_runtime_accepts_nested_and_root_paths_without_the_slash_extension_bug(self):
        self.assertEqual(["package.json", "docker/Dockerfile"], summary_files(
            "key-files:\n  created:\n    - package.json\n    - docker/Dockerfile"))

    def test_runtime_accepts_known_extensionless_build_files(self):
        self.assertEqual(["Dockerfile", "Makefile", "Justfile", "Containerfile", "Procfile"], summary_files(
            "key-files:\n  modified:\n" + "".join("    - " + name + "\n" for name in
            ["Dockerfile", "Makefile", "Justfile", "Containerfile", "Procfile"])))

    def test_runtime_rejects_summary_paths_outside_project(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "SUMMARY.md").write_text(
                "---\nkey-files:\n  created:\n    - ../outside.py\n---\n", encoding="utf-8")
            result = runtime_query(directory, "review.summary-files", "SUMMARY.md", "--raw")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("path", (result.stdout + result.stderr).lower())

    def test_shipped_extractor_delegates_to_registered_summary_parser(self):
        self.assertIn('engineer_run query review.summary-files "$1"', WORKFLOW_LF)

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

    @needs_bash
    def test_present_results_accepts_both_labels(self):
        script = crp.fence_containing(WORKFLOW_LF, "CRITICAL=$(", WORKFLOW_LF.index('<step name="present_results">'))
        for label in ("critical", "blocker"):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                Path(directory, "REVIEW.md").write_text(
                    "---\nfindings:\n  " + label + ": 8\n---\n", encoding="utf-8")
                prefix = "engineer_run() { " + shlex.quote(crp.posix(sys.executable)) + " -I " + shlex.quote(crp.posix(SOURCE / "engineer/bin/engineer.py")) + ' "$@"; }\nREVIEW_PATH=REVIEW.md\n'
                result = crp.run_bash(prefix + script + '\nprintf "%s" "$CRITICAL"',
                                      cwd=directory, env={**os.environ, "ENGINEER_ROOT": directory})
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("8", result.stdout.strip())

    def test_present_results_includes_bl_headings_alongside_cr_and_wr(self):
        self.assertTrue("### BL-" in WORKFLOW and "### CR-" in WORKFLOW and "### WR-" in WORKFLOW
                        or "^### CR-\\|^### BL-\\|^### WR-" in WORKFLOW)


class CommitReviewStatusGate(TempCase):
    @needs_bash
    def test_valid_status_is_accepted_and_missing_status_is_rejected(self):
        script = crp.fence_containing(WORKFLOW_LF, "HAS_STATUS=$(", WORKFLOW_LF.index('<step name="commit_review">'))
        for status in ("clean", "issues_found", None):
            with self.subTest(status=status):
                directory = self.temp()
                report = directory / "REVIEW.md"
                report.write_text("---\n" + ("status: " + status if status else "phase: 01") + "\n---\n", encoding="utf-8")
                prefix = "engineer_run() { " + shlex.quote(crp.posix(sys.executable)) + " -I " + shlex.quote(crp.posix(SOURCE / "engineer/bin/engineer.py")) + ' "$@"; }\nREVIEW_PATH=REVIEW.md\nCOMMIT_DOCS=false\n'
                result = crp.run_bash(prefix + script, cwd=directory, env={**os.environ, "ENGINEER_ROOT": str(directory)})
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(status is not None, "REVIEW.md created at" in result.stdout, result.stdout)


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


class DiffBaseSingleOwner(TempCase):
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
        self.skipTest("upstream fallow pre-pass fixture absent in this repo")

    def test_t2_tier3_scope_is_the_union_of_recorded_task_commits(self):
        directory = self.temp()
        subprocess.run(["git", "init", "-q", str(directory)], check=True, capture_output=True)
        def commit(name, subject):
            (directory / name).write_text(name, encoding="utf-8")
            subprocess.run(["git", "add", name], cwd=directory, check=True, capture_output=True)
            subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                            "commit", "-qm", subject], cwd=directory, check=True, capture_output=True)
        commit("first.py", "feat(01-01): first task")
        commit("outside.py", "chore: interleaved change")
        commit("second.py", "feat(01-02): second task")
        result = runtime_query(directory, "review.scope", "--phase", "01")
        self.assertEqual(0, result.returncode, result.stderr)
        scope = json.loads(result.stdout)
        self.assertEqual(["first.py", "second.py"], scope["files"])
        self.assertEqual(["outside.py"], scope["outsideUnion"])

    def test_t3_no_committed_phase_directory_leaves_base_and_scope_empty(self):
        directory = self.temp()
        subprocess.run(["git", "init", "-q", str(directory)], check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "--allow-empty", "-qm", "initial"], cwd=directory, check=True, capture_output=True)
        result = runtime_query(directory, "review.scope", "--phase", "01")
        self.assertEqual(0, result.returncode, result.stderr)
        scope = json.loads(result.stdout)
        self.assertEqual([], scope["files"])
        self.assertEqual("unresolved", scope["status"])


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



# --- Increment B: gate counts, executed against the shipped bash fence ------------------

DISPOSITION = crp.read_text(crp.DISPOSITION_STEP_PATH)
REVIEW_WITH_FINDINGS = "\n".join([
    "---", "phase: 01", "findings:", "  critical: 1", "  warning: 2", "  info: 1", "  total: 4", "status: issues_found", "---", "",
    "## Critical Issues", "", "### CR-01: SQL injection in auth", "", "## Warnings", "", "### WR-01: missing null check", "",
    "### WR-02: unused import", "", "## Info", "", "### IN-01: stale TODO"])


class GateCountsMirror(unittest.TestCase):
    """Upstream #3829: the pure mirror of the gate's frontmatter reads."""

    def test_reads_the_counts_beside_the_status(self):
        self.assertEqual({"status": "issues_found", "critical": "1", "warning": "2", "info": "1", "total": "4"},
                         crp.parse_gate_counts(REVIEW_WITH_FINDINGS))

    def test_blocker_is_the_critical_tier_equivalent(self):
        self.assertEqual("1", crp.parse_gate_counts(REVIEW_WITH_FINDINGS.replace("  critical: 1", "  blocker: 1"))["critical"])

    def test_body_status_and_total_never_displace_the_frontmatter(self):
        parsed = crp.parse_gate_counts(REVIEW_WITH_FINDINGS + "\n\n---\n\nstatus: clean\ntotal: 999\n")
        self.assertEqual("issues_found", parsed["status"])
        self.assertEqual("4", parsed["total"])

    def test_review_with_no_findings_block_yields_no_counts(self):
        parsed = crp.parse_gate_counts("---\nphase: 02\nstatus: issues_found\n---\n\n# Phase 02")
        self.assertEqual(("issues_found", "", ""), (parsed["status"], parsed["total"], parsed["critical"]))

    def test_optional_count_absent_from_frontmatter_is_not_supplied_by_the_body(self):
        leaky = "---\nphase: 01\nstatus: issues_found\n---\n\n# Report\n\n---\n\ntotal: 7\ncritical: 9"
        parsed = crp.parse_gate_counts(leaky)
        self.assertEqual(("issues_found", "", ""), (parsed["status"], parsed["total"], parsed["critical"]))

    def test_crlf_review_parses_to_bare_values(self):
        crlf = "\r\n".join(["---", "phase: 01", "findings:", "  critical: 1", "  warning: 0", "  info: 2", "  total: 3",
                            "status: issues_found", "---", "", "### CR-01: a"])
        parsed = crp.parse_gate_counts(crlf)
        self.assertEqual({"status": "issues_found", "critical": "1", "warning": "0", "info": "2", "total": "3"}, parsed)
        self.assertFalse(any("\r" in value for value in parsed.values()))

    def test_unterminated_frontmatter_yields_no_values(self):
        unterminated = "---\nphase: 01\nstatus: issues_found\n\n# body\n\ntotal: 777\ncritical: 66"
        self.assertEqual({"status": "", "critical": "", "warning": "", "info": "", "total": ""}, crp.parse_gate_counts(unterminated))

    def test_docs_parity_gate_states_the_breakdown(self):
        self.assertIn("Code review: ${REVIEW_TOTAL} findings — ${REVIEW_CRITICAL} critical, ${REVIEW_WARNING} warning, ${REVIEW_INFO} info.", DISPOSITION)

    def test_docs_parity_first_match_guard_and_closing_delimiter(self):
        self.assertIn('grep -m1 "^status:"', DISPOSITION)
        self.assertIn("awk 'NR==1{if($0!=\"---\") exit; next} /^---$/{closed=1; exit}", DISPOSITION)
        self.assertIn("tr -d '\\r' < \"$REVIEW_FILE\"", DISPOSITION)
        self.assertIn('END{if (closed) printf "%s", buf}', DISPOSITION)

    def test_docs_parity_non_blocking_and_unchanged_run(self):
        self.assertIn("Code review disposition record skipped (non-blocking).", DISPOSITION)
        self.assertIn("engineer_run query review.reconcile", DISPOSITION)
        self.assertIn('|| echo "Code review disposition record skipped (non-blocking)."', DISPOSITION)
        self.assertNotIn("Code review disposition unchanged:", DISPOSITION)

    def test_docs_parity_gate_reaches_the_extracted_step(self):
        parent = crp.read_text(crp.SHARED_VERIFY_STEP_PATH)
        self.assertRegex(parent, r"Read and execute\s+`engineer/workflows/execute-phase/steps/code-review-disposition\.md`")
        self.assertLess(parent.index("code-review-disposition.md"), parent.index("**TDD review escalation"))


FIXTURES = {
    "the documented review": REVIEW_WITH_FINDINGS,
    "blocker: as the critical tier-equivalent": REVIEW_WITH_FINDINGS.replace("  critical: 1", "  blocker: 1"),
    "a body ---, status: and total: after the frontmatter": REVIEW_WITH_FINDINGS + "\n\n---\n\nstatus: clean\ntotal: 999\n",
    "a legacy review with no findings: block": "---\nphase: 02\nstatus: issues_found\n---\n\n# Phase 02",
    "CRLF line endings": REVIEW_WITH_FINDINGS.replace("\n", "\r\n"),
    "unterminated frontmatter": "---\nstatus: issues_found\ntotal: 4\n\n## Body",
    "no frontmatter at all": "# Phase 01\n\nnothing here\n",
    "a zero-finding review": "\n".join(["---", "phase: 01", "findings:", "  critical: 0", "  warning: 0", "  info: 0", "  total: 0",
                                        "status: issues_found", "---"]),
    "a count with an internal space": REVIEW_WITH_FINDINGS.replace("  critical: 1", "  critical: 1 0"),
    "a self-consistent repaired breakdown": "\n".join(["---", "phase: 01", "status: issues_found", "findings:", "  critical: 1 0",
                                                       "  warning: 0", "  info: 0", "  total: 1 0", "---", "", "### CR-01: a"]),
    "tab-separated counts": "\n".join(["---", "phase: 01", "status: issues_found", "findings:", "  critical:\t1", "  warning:\t1",
                                       "  info:\t1", "  total:\t3", "---", "", "### CR-01: a"]),
    "a status whose truncation would flip the arm": REVIEW_WITH_FINDINGS.replace("status: issues_found", "status: clean:junk"),
    "a status with a trailing unicode space": REVIEW_WITH_FINDINGS.replace("status: issues_found", "status: clean "),
    "a count with a trailing unicode space": REVIEW_WITH_FINDINGS.replace("  critical: 1", "  critical: 1 "),
    "a findings: opener with a trailing unicode space": REVIEW_WITH_FINDINGS.replace("findings:", "findings: "),
    "a value containing a second colon": REVIEW_WITH_FINDINGS.replace("status: issues_found", "status: issues:found"),
    "a key indented with a form feed": REVIEW_WITH_FINDINGS.replace("  critical: 1", "\fcritical: 1"),
    "a top-level total: ahead of the nested one": "\n".join(["---", "phase: 02", "total: 999", "status: issues_found", "findings:",
                                                           "  critical: 1", "  warning: 0", "  info: 0", "  total: 1", "---"]),
    "a top-level info: and critical: ahead of the nested ones": "\n".join(["---", "critical: 42", "info: 7", "status: issues_found",
                                                                         "findings:", "  critical: 1", "  warning: 0", "  info: 0",
                                                                         "  total: 1", "---"]),
}
LOCALE_FIXTURES = {
    "a status with a trailing unicode space": FIXTURES["a status with a trailing unicode space"],
    "a count with a trailing unicode space": FIXTURES["a count with a trailing unicode space"],
    "a unicode-space indented count key": REVIEW_WITH_FINDINGS.replace("  critical: 1", " critical: 1"),
    "a findings: opener with a trailing unicode space": FIXTURES["a findings: opener with a trailing unicode space"],
    "the documented review": REVIEW_WITH_FINDINGS,
}
UNTERMINATED = "\n".join(["---", "phase: 01", "status: issues_found", "findings:", "  critical: 3", "  warning: 0", "  info: 0",
                          "  total: 3", "", "## Critical Issues", "", "### CR-01: a", "### CR-02: b", "### CR-03: c"])


def mirror_message(text, phase=1):
    return crp.render_gate_message(crp.parse_gate_counts(text), phase)


def fm_review(rows, status="issues_found"):
    return "\n".join(["---", "findings:", *rows, f"status: {status}", "---"])


NO_STATUS = "\n".join(["---", "phase: 01", "findings:", "  critical: 3", "  warning: 0", "  info: 0", "  total: 3", "---", "", "### CR-01: a"])
REPAIRED = "\n".join(["---", "phase: 01", "status: issues_found", "findings:", "  critical: 1 0", "  warning: 0", "  info: 0",
                      "  total: 1 0", "---", "", "### CR-01: a", "### WR-01: b", "### WR-02: c"])

# Named single cases beyond the mirror fixtures; all run in one bash process per environment (see run_gate_batch).
SINGLE_CASES = {
    "partial": {"text": "---\nfindings:\n  total: 4\nstatus: issues_found\n---"},
    "missing": {"text": "", "write_review": False},
    "total_only": {"text": fm_review(["  total: 4"])},
    "all_four": {"text": fm_review(["  critical: 1", "  warning: 2", "  info: 1", "  total: 4"])},
    "directory": {"text": REVIEW_WITH_FINDINGS, "plant_dir": True},
    "empty": {"text": ""},
    "unterminated": {"text": UNTERMINATED},
    "unterminated_directory": {"text": UNTERMINATED, "plant_dir": True},
    "no_status": {"text": NO_STATUS},
    "no_frontmatter": {"text": "# Phase 01\n\n### CR-01: a finding\n"},
    "repaired": {"text": REPAIRED},
}


@needs_fast_bash
class GateCountsShippedShell(unittest.TestCase):
    """Upstream #3861 round 1/2/11: the counts mirror is asserted against the shipped shell."""

    @classmethod
    def setUpClass(cls):
        names = [*(("fixture", name) for name in FIXTURES), *(("single", name) for name in SINGLE_CASES)]
        cases = [{"text": FIXTURES[name]} if kind == "fixture" else SINGLE_CASES[name] for kind, name in names]
        cls.default = dict(zip(names, crp.run_gate_batch(cases)))
        locale_cases = [{"text": text} for text in LOCALE_FIXTURES.values()]
        cls.c_locale = dict(zip(LOCALE_FIXTURES, crp.run_gate_batch(locale_cases, {"LC_ALL": "C", "LANG": "C"})))
        cls.utf8_locale = dict(zip(LOCALE_FIXTURES, crp.run_gate_batch(locale_cases, {"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"})))

    def single(self, name):
        return self.default[("single", name)]

    def test_shipped_shell_and_mirror_agree_on_every_fixture(self):
        for name, text in FIXTURES.items():
            with self.subTest(name):
                self.assertEqual(mirror_message(text), self.default[("fixture", name)]["stdout"],
                                 "the mirror has drifted from the shipped awk/grep block")

    def test_shipped_reads_are_locale_invariant(self):
        for name, text in LOCALE_FIXTURES.items():
            with self.subTest(name):
                self.assertEqual(0, self.c_locale[name]["exitCode"])
                self.assertEqual(0, self.utf8_locale[name]["exitCode"])
                self.assertEqual(self.c_locale[name]["stdout"], self.utf8_locale[name]["stdout"], "drop LC_ALL=C and this reds")
                self.assertEqual(mirror_message(text), self.c_locale[name]["stdout"])

    def test_zero_finding_review_reports_a_real_breakdown(self):
        self.assertEqual("Code review: 0 findings — 0 critical, 0 warning, 0 info.\nConsider running: /code-review 1 --fix\n",
                         self.default[("fixture", "a zero-finding review")]["stdout"])

    def test_partial_findings_block_makes_the_breakdown_unavailable(self):
        out = self.single("partial")
        self.assertEqual("0", crp.read_gate_message(out["stdout"])["countsOk"])
        self.assertRegex(out["stdout"], r"(?m)^Code review found issues\.$")

    def test_missing_review_leaves_the_counts_empty_and_does_not_abort(self):
        out = self.single("missing")
        self.assertEqual(0, out["exitCode"])
        self.assertEqual("", out["stdout"])
        self.assertFalse(crp.read_gate_message(out["stdout"])["reported"])

    def test_countless_fallback_requires_all_four_counts(self):
        total_only = self.single("total_only")
        self.assertRegex(total_only["stdout"], r"(?m)^Code review found issues\.$")
        self.assertNotIn("findings —", total_only["stdout"])
        self.assertRegex(self.single("all_four")["stdout"], r"(?m)^Code review: 4 findings — 1 critical, 2 warning, 1 info\.$")

    @unittest.skipIf(os.name == "nt" or (hasattr(os, "getuid") and os.getuid() == 0), "POSIX mode bits are not honored (Windows) or bypassed (root)")
    def test_unreadable_review_leaves_the_counts_empty(self):
        with tempfile.TemporaryDirectory(prefix="engineer-crp-") as directory:
            path = Path(directory) / "01-REVIEW.md"
            path.write_text(REVIEW_WITH_FINDINGS, encoding="utf-8")
            path.chmod(0)
            script = "set -euo pipefail\n" + crp.bash_fences(DISPOSITION)[0] + "\n"
            result = crp.run_bash(script, env={**os.environ, "PHASE_DIR": crp.posix(directory), "PHASE_NUMBER": "1"})
        self.assertEqual((0, ""), (result.returncode, result.stdout))

    def test_directory_standing_in_for_review_leaves_the_counts_empty(self):
        out = self.single("directory")
        self.assertEqual((0, ""), (out["exitCode"], out["stdout"]))
        self.assertFalse(crp.read_gate_message(out["stdout"])["reported"])

    def test_empty_review_reports_the_unparseable_status(self):
        out = self.single("empty")
        self.assertEqual(0, out["exitCode"])
        self.assertRegex(out["stdout"], r"(?m)^Code review status unparsed: ")
        self.assertNotRegex(out["stdout"], r"(?m)^Code review: \d+ findings")
        self.assertTrue(crp.read_gate_message(out["stdout"])["unparsed"])

    def test_round11_unterminated_frontmatter_is_unparsed_not_silent(self):
        out = self.single("unterminated")
        self.assertEqual(0, out["exitCode"])
        self.assertIn(crp.GATE_UNPARSED.rstrip("\n"), out["stdout"])
        self.assertNotRegex(out["stdout"], r"(?m)^Code review: \d+ findings")
        self.assertNotIn("Consider running", out["stdout"])

    def test_round11_closed_frontmatter_without_status_is_the_same_arm(self):
        self.assertRegex(self.single("no_status")["stdout"], r"(?m)^Code review status unparsed: ")

    def test_round11_review_with_no_frontmatter_is_the_same_arm(self):
        self.assertRegex(self.single("no_frontmatter")["stdout"], r"(?m)^Code review status unparsed: ")

    def test_round11_absent_and_directory_stay_silent(self):
        self.assertEqual("", self.single("missing")["stdout"])
        self.assertEqual("", self.single("unterminated_directory")["stdout"])

    def test_block1_withholds_a_breakdown_built_from_repaired_counts(self):
        out = self.single("repaired")
        self.assertEqual(0, out["exitCode"])
        self.assertNotIn("10 findings", out["stdout"])
        self.assertNotIn("10 critical", out["stdout"])
        self.assertRegex(out["stdout"], r"(?m)^Code review found issues\.")


def phase_review(phase, critical, warning, info):
    total = critical + warning + info
    return "\n".join(["---", f"phase: {phase}", "status: issues_found", "findings:", f"  critical: {critical}", f"  warning: {warning}",
                      f"  info: {info}", f"  total: {total}", "---", "", "### CR-01: a finding"])


def pad_integer_part(phase):
    return re.sub(r"^[0-9]+", lambda m: m.group(0).rjust(2, "0"), phase)


CALLER_RE = re.compile(r"^[0-9]+[A-Z]?(\.[0-9]+)*$")
SHAPE_PROBES = ["../../etc/passwd", "abc", "", "-1", "3.", ".1", "+1", "3 1", "1..2", "1.2.", "23a", "A23", "2A3", "23AB", "23.1A"]
AGREEMENT_PROBES = ["1", "03", "03.1", "23.1.2", "1.2.3.4", "12345678", "1.12345678", "1.1234567.1", "12345678.12345678",
                    "1.1.1.1.1.1.1.1.1.1", "12A", "3A", "23A.1.2", "12345678A", "23a", "A23", "2A3", "23AB", "23.1A", "1..2",
                    "1.2.", ".1", "3.", "abc", "-1", "+1", "3 1", "../../etc/passwd"]
OVER_BOUND = ["123456789", "1.999999999", "123456789A"]
COMPONENT_BOUND = {"1.12345678.1": False, "1.123456789.1": True, "1.1234567.1": False, "12345678.12345678": False}
N_SEGMENT = ["23.1.2", "1.2.3.4"]
LETTER_VARIANTS = [("12A", "12A"), ("3A", "03A"), ("23A.1.2", "23A.1.2"), ("12345678A", "12345678A")]


@needs_fast_bash
class DottedPhaseNumbers(unittest.TestCase):
    """Upstream #3861 round 2/11/12: a dotted or letter-variant phase number does not break the step."""

    @classmethod
    def setUpClass(cls):
        refusal_values = list(dict.fromkeys([*SHAPE_PROBES, *AGREEMENT_PROBES, *OVER_BOUND, *COMPONENT_BOUND]))
        cases = [{"write_review": False, "phase_number": value} for value in refusal_values]
        cases += [{"text": phase_review("03.1", 1, 0, 0), "padded": "03.1"}]
        cases += [{"text": phase_review(phase, 1, 2, 0), "padded": pad_integer_part(phase), "phase_number": phase} for phase in N_SEGMENT]
        cases += [{"text": phase_review(phase, 1, 0, 0), "padded": padded, "phase_number": phase} for phase, padded in LETTER_VARIANTS]
        cases += [{"text": phase_review("01", 1, 0, 0)}]
        results = crp.run_gate_batch(cases)
        cls.refusal = dict(zip(refusal_values, results[:len(refusal_values)]))
        rest = results[len(refusal_values):]
        cls.dotted, cls.n_segment, cls.letters, cls.integer = rest[0], dict(zip(N_SEGMENT, rest[1:3])), rest[3:7], rest[7]

    def refused(self, value):
        result = self.refusal[value]
        self.assertEqual(0, result["exitCode"], f"{value!r}: advisory -- must not abort")
        self.assertNotIn("Code review: ", result["stdout"], f"{value!r}: no counts without a review")
        return "skipped (unusable phase number" in result["stdout"]

    def test_the_two_fences_derive_padded_identically(self):
        fences = crp.bash_fences(DISPOSITION)
        self.assertEqual(2, len(fences), "the step must still carry exactly two bash fences")

        def derivation(fence, which):
            start = fence.find('_pd="${PHASE_DIR:-}"')
            end = fence.find('DISPOSITION_FILE="${_pd}/${PADDED}-REVIEW-DISPOSITION.md"')
            self.assertGreater(start, -1, f"block {which} must still open the derivation with _pd")
            self.assertGreater(end, start, f"block {which} must still close it by building the ledger path")
            return fence[start:end].split("\n")
        a, b = derivation(fences[0], 1), derivation(fences[1], 2)
        self.assertGreater(len(a), 20)
        self.assertEqual(len(a), len(b))
        differing = [(x, y) for x, y in zip(a, b) if x != y]
        self.assertEqual(1, len(differing), differing)
        self.assertIn("Code review reporting skipped", differing[0][0])
        self.assertIn("Code review disposition skipped", differing[0][1])

    def test_block1_reports_a_dotted_phase_instead_of_aborting(self):
        out = self.dotted
        self.assertEqual(0, out["exitCode"])
        self.assertNotIn("invalid number", out["stderr"])
        self.assertRegex(out["stdout"], "(?m)^Code review: 1 findings — 1 critical, 0 warning, 0 info\\.$")

    def test_phase_number_outside_the_documented_shape_builds_no_path(self):
        for value in SHAPE_PROBES:
            with self.subTest(value):
                self.assertTrue(self.refused(value), f"{value!r} must be refused by name, not silently coerced")

    def test_n_segment_phase_number_reports_counts(self):
        for phase, out in self.n_segment.items():
            with self.subTest(phase):
                self.assertEqual(0, out["exitCode"])
                self.assertNotIn("skipped (unusable phase number", out["stdout"])
                self.assertRegex(out["stdout"], "(?m)^Code review: 3 findings — 1 critical, 2 warning, 0 info\\.$")
                self.assertNotIn("invalid number", out["stderr"])

    def test_letter_variant_phase_number_reports_counts(self):
        for (phase, _), out in zip(LETTER_VARIANTS, self.letters):
            with self.subTest(phase):
                self.assertEqual(0, out["exitCode"])
                self.assertNotIn("skipped (unusable phase number", out["stdout"])
                self.assertRegex(out["stdout"], "(?m)^Code review: 1 findings — 1 critical, 0 warning, 0 info\\.$")

    def test_fence_agrees_with_its_callers_within_the_length_bound(self):
        for value in AGREEMENT_PROBES:
            with self.subTest(value):
                self.assertEqual(not CALLER_RE.match(value), self.refused(value))

    def test_fence_keeps_refusing_a_component_over_eight_characters(self):
        for value in OVER_BOUND:
            with self.subTest(value):
                self.assertTrue(CALLER_RE.match(value))
                self.assertTrue(self.refused(value), "the per-component 8-char bound changed")

    def test_length_bound_is_per_component(self):
        for phase, expected in COMPONENT_BOUND.items():
            with self.subTest(phase):
                self.assertEqual(expected, self.refused(phase))

    def test_integer_phase_is_still_zero_padded(self):
        self.assertEqual(0, self.integer["exitCode"])
        self.assertRegex(self.integer["stdout"], r"(?m)^Code review: 1 findings")


class LocalePinCensus(unittest.TestCase):
    def test_every_locale_sensitive_tool_in_the_step_is_pinned_to_lc_all_c(self):
        # The inline launcher preamble pins its locale-sensitive path escaping to the C locale.
        offenders = []
        for number, line in enumerate(DISPOSITION.replace("\r\n", "\n").split("\n"), 1):
            if re.match(r"^\s*#", line):
                continue
            rest = re.sub(r"LC_ALL=C\s+(?:grep|sed|awk)\b", "", line)
            for hit in re.findall(r"(?:^|[^A-Za-z0-9_-])(?:grep|sed|awk)\b", rest):
                offenders.append(f"{number}: {hit.strip()} (unpinned)")
        self.assertEqual([], offenders)
        self.assertRegex(DISPOSITION, r"\|\s*cut -d: -f2-")


class DispositionLedgerRuntime(TempCase):
    """Previously Node-only ledger cases exercise the shipped Python verb."""

    def test_ledger_rows_preserve_pipe_reasons_and_crlf(self):
        for reason in (r"wait \| vendor", "wait | vendor", r"one\|\|two", r"back\\|slash"):
            with self.subTest(reason=reason):
                fixture = crp.ReconcileFixture(self.temp())
                prior = "| CR-01 | critical | deferred | " + reason + " |\r\n"
                first = fixture.run(review_doc("### CR-01: a"), prior=prior)
                self.assertEqual(0, first["returncode"], first["stderr"])
                again = fixture.run(review_doc("### CR-01: a"))
                self.assertEqual(first["rows"], again["rows"])
                self.assertEqual("deferred", again["rows"][0]["disposition"])

    def test_shortfall_and_invalid_count_cases(self):
        for count in (0, 1, 2):
            with self.subTest(count=count):
                out = crp.ReconcileFixture(self.temp()).run(review_doc("### CR-01: a"), review_total=count)
                self.assertEqual(0, out["returncode"], out["stderr"])
                self.assertEqual(max(0, count - 1), out["result"]["unparsed"])

    def test_ledger_write_refuses_non_regular_files(self):
        fixture = crp.ReconcileFixture(self.temp())
        fixture.ledger_path.mkdir()
        result = runtime_query(fixture.directory, "review.reconcile", "--phase", "01",
                               "--review-file", "01-REVIEW.md", "--disposition-file", fixture.ledger_path.name)
        self.assertNotEqual(0, result.returncode)
        self.assertTrue(fixture.ledger_path.is_dir())
        self.assertIn("review-source-not-regular", result.stdout + result.stderr)

    def test_ledger_write_refuses_symlinks_without_touching_target(self):
        fixture = crp.ReconcileFixture(self.temp())
        target = fixture.directory / "target.txt"
        target.write_text("preserve target", encoding="utf-8")
        try:
            fixture.ledger_path.symlink_to(target)
        except OSError as error:
            self.skipTest("host cannot create symlinks: " + str(error))
        result = runtime_query(fixture.directory, "review.reconcile", "--phase", "01",
                               "--review-file", "01-REVIEW.md", "--disposition-file", fixture.ledger_path.name)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("preserve target", target.read_text(encoding="utf-8"))
        self.assertTrue(fixture.ledger_path.is_symlink())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "host has no FIFO support")
    def test_ledger_write_refuses_fifo_without_blocking(self):
        fixture = crp.ReconcileFixture(self.temp())
        os.mkfifo(fixture.ledger_path)
        result = runtime_query(fixture.directory, "review.reconcile", "--phase", "01",
                               "--review-file", "01-REVIEW.md", "--disposition-file", fixture.ledger_path.name)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("review-source-not-regular", result.stdout + result.stderr)

    def test_runtime_has_no_embedded_command_line_script(self):
        command = [sys.executable, "-I", str(SOURCE / "engineer/bin/engineer.py"),
                   "query", "review.reconcile", "--phase", "01", "--review-file", "01-REVIEW.md",
                   "--disposition-file", "01-REVIEW-DISPOSITION.md"]
        self.assertLess(len(subprocess.list2cmdline(command)), 24576)


# --- Increment C: workflow structure, id census, lookup, fixer, resolver ------------------

class CheckEmptyScopeRecovery(unittest.TestCase):
    """Upstream #4665: check_empty_scope recovers --fix onto an existing REVIEW.md."""

    def block(self):
        start = WORKFLOW.index('<step name="check_empty_scope">')
        end = WORKFLOW.index('<step name="structural_pre_pass">')
        self.assertGreater(end, start, "structural_pre_pass must follow check_empty_scope")
        return WORKFLOW[start:end]

    def test_recovers_fix_onto_an_existing_review(self):
        block = self.block()
        self.assertIn('REVIEW_PATH="${PHASE_DIR}/${PADDED_PHASE}-REVIEW.md"', block)
        self.assertTrue("FIX_FLAG" in block and '-f "${REVIEW_PATH}"' in block)
        self.assertIn('"${#REVIEW_FILES[@]}" -ne 0', block)

    def test_fix_recovery_routes_to_dispatch_fix_past_the_fresh_review_steps(self):
        block = self.block()
        self.assertRegex(block, "dispatch-fix")
        self.assertRegex(block, r"structural_pre_pass[\s\S]*dispatch_reviewer_lanes[\s\S]*spawn_reviewer[\s\S]*commit_review")
        self.assertNotRegex(block, r"spawn the (reviewer|agent)|code-reviewer")

    def test_plain_empty_scope_skip_survives_for_the_non_fix_path(self):
        block = self.block()
        self.assertIn("No source files changed in phase ${PHASE_ARG}. Skipping review.", block)
        self.assertRegex(block, r"(?i)Exit workflow")


class DispositionStepStructure(unittest.TestCase):
    """Upstream #3861 round 1: the step-file structural contract."""

    def test_step_never_instructs_the_agent_to_read_and_execute_itself(self):
        self.assertNotIn("execute-phase/steps/" + crp.DISPOSITION_STEP_PATH.name, DISPOSITION)

    def test_disposition_instruction_appears_exactly_once(self):
        count = sum(1 for line in DISPOSITION.splitlines() if line.startswith("**Record a per-finding disposition.**"))
        self.assertEqual(1, count)

    def test_every_shell_block_derives_the_variables_it_reads(self):
        derived = ["PADDED", "REVIEW_FILE", "DISPOSITION_FILE"]
        fences = crp.bash_fences(DISPOSITION)
        self.assertGreaterEqual(len(fences), 2)
        for number, fence in enumerate(fences, 1):
            for name in derived:
                without_passthrough = re.sub(r"(?:^|[\s;])" + name + r'="\$\{' + name + r'\}"', " ", fence, flags=re.M)
                assigned = re.search(r"(?:^|[\s;])" + name + r"=(?![\s;#]|$)", without_passthrough, re.M)
                reads = re.search(r"\$\{?" + name + r"\b", re.sub(r"(?:^|[\s;])" + name + "=", "", fence, flags=re.M))
                if not reads:
                    continue
                with self.subTest(block=number, variable=name):
                    self.assertTrue(assigned, f"block {number} reads {name} without deriving it")


class EmbeddedScriptBudget(unittest.TestCase):
    """Runtime calls stay below the Windows command-line budget."""

    def test_disposition_invocation_stays_under_windows_command_line_budget(self):
        # Check the shipped call site once docs are integrated; no embedded script extraction.
        calls = [fence for fence in crp.bash_fences(DISPOSITION) if "review.reconcile" in fence]
        self.assertTrue(calls, "the disposition step must call the installed Python adapter")
        for fence in calls:
            invocation = fence[fence.index("engineer_run query review.reconcile"):]
            self.assertLess(len(invocation), 24576)


class FindingIdCensus(TempCase):
    """Every emitted reviewer prefix must survive the registered ledger parser."""

    def test_all_canonical_prefixes_have_the_correct_tier(self):
        review = review_doc("### CR-01: critical", "### BL-01: blocker", "### WR-01: warning", "### IN-01: info")
        out = crp.ReconcileFixture(self.temp()).run(review)
        self.assertEqual(0, out["returncode"], out["stderr"])
        self.assertEqual([("CR-01", "critical"), ("BL-01", "critical"), ("WR-01", "warning"), ("IN-01", "info")],
                         [(row["id"], row["severity"]) for row in out["rows"]])

    def test_prefix_set_covers_every_id_shape_the_reviewer_agent_emits(self):
        emitted = crp.emitted_id_prefixes(REVIEWER)
        self.assertTrue(emitted, "reviewer must declare its finding-id shapes")
        for prefix in sorted(emitted):
            with self.subTest(prefix=prefix):
                out = crp.ReconcileFixture(self.temp()).run(review_doc("### " + prefix + "-01: finding"))
                self.assertEqual([prefix + "-01"], [row["id"] for row in out["rows"]])

    def test_one_letter_finding_prefix_in_agent_template_is_not_invisible(self):
        self.assertGreater(len(re.findall(r"^###\s+([A-Z]+)-\d+:", REVIEWER, re.M)), 0)
        self.assertEqual({"C"}, crp.emitted_id_prefixes("### C-01: x"))


class FixWorkflowReachability(TempCase):
    """Upstream #3861 round 2: the disposition ledger is reachable in a shipped path."""

    FIX = crp.read_text(crp.FIX_WORKFLOW_PATH)

    def test_fix_workflow_reads_and_executes_the_disposition_step_after_committing_the_report(self):
        self.assertIn('<step name="record_disposition">', self.FIX)
        self.assertIn("engineer/workflows/execute-phase/steps/code-review-disposition.md", self.FIX)
        commit, record, present = (self.FIX.find(f'<step name="{name}">') for name in ("commit_fix_report", "record_disposition", "present_results"))
        self.assertTrue(commit > -1 and record > -1 and present > -1, "all three steps must exist")
        self.assertLess(commit, record, "the ledger is reconciled AFTER the fix report is written")
        self.assertLess(record, present, "and before results are presented")

    def test_iteration_backups_are_removed_after_the_ledger_has_read_them(self):
        record = self.FIX.find('<step name="record_disposition">')
        cleanup = self.FIX.find('<step name="cleanup_iteration_backups">')
        self.assertGreater(cleanup, -1, "the backups must be removed by a named step, not inline in the loop")
        self.assertLess(record, cleanup, "the ledger reads the backups BEFORE they are removed")
        loop = self.FIX[self.FIX.index('<step name="auto_iteration_loop">'):self.FIX.index('<step name="commit_fix_report">')]
        self.assertIsNone(re.search(r'rm -f "\$\{REVIEW_PATH%\.md\}\.iter"', loop), "the loop must no longer delete the backups it just wrote")

    def test_gate_writes_all_open_and_the_fix_path_resolves_it(self):
        fixture = crp.ReconcileFixture(self.temp())
        review = review_doc("### CR-01: a")
        first = fixture.run(review)
        self.assertEqual("open", first["rows"][0]["disposition"])
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "--allow-empty", "-qm", "fix: repair CR-01"],
                       cwd=fixture.directory, check=True, capture_output=True)
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=fixture.directory,
                                  check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()
        fixed = fixture.run(review, fix="## Fixed Issues\n### CR-01: a\n**Commit:** " + revision)
        self.assertEqual(0, fixed["returncode"], fixed["stderr"])
        self.assertEqual("fixed", fixed["rows"][0]["disposition"])
        self.assertEqual(0, fixed["result"]["open"])


STEP_LINES = DISPOSITION.replace("\r\n", "\n").split("\n")
STEP_LOOKUPS = crp.anchored_line_indexes(STEP_LINES, 'REVIEW_FILE="${_pd}/${PADDED}-REVIEW.md"', 2)
STEP_STARTS = crp.anchored_line_indexes(STEP_LINES, '_pd="${PHASE_DIR:-}"', 2)
STEP_DERIVATIONS = ["\n".join(STEP_LINES[start:STEP_LOOKUPS[n] + 1]) for n, start in enumerate(STEP_STARTS)]


class ReviewLookupPadding(unittest.TestCase):
    """Upstream #3829: the step's REVIEW.md lookup resolves a letter-suffixed phase without a shell re-pad."""

    LINES, LOOKUPS, DERIVATIONS = STEP_LINES, STEP_LOOKUPS, STEP_DERIVATIONS

    def test_no_fence_re_pads_the_phase_number_with_printf(self):
        offenders = [(number, line) for number, line in enumerate(self.LINES, 1)
                     if not re.match(r"^\s*#", line) and re.search(r'printf\s+"%0\d*d"\s+"?\$\{?PHASE_NUMBER', line)]
        self.assertEqual([], offenders)
        for derivation in self.DERIVATIONS:
            bound = next((line for line in derivation.split("\n") if "PADDED=" in line and 'PADDED=""' not in line), None)
            self.assertIsNotNone(bound, "the derivation must bind PADDED")
            self.assertIsNone(re.search(r"printf|\$\(\(", bound), f"the pad must not be arithmetic: {bound.strip()}")

    def test_both_lookup_lines_are_unchanged(self):
        for index in self.LOOKUPS:
            self.assertEqual('REVIEW_FILE="${_pd}/${PADDED}-REVIEW.md"', self.LINES[index].strip())

    def test_nothing_rebinds_review_file_after_the_lookup(self):
        bind = re.compile(r"^\s*(?:export\s+)?REVIEW_FILE\+?=")
        binds = [re.sub(r"^\s*(?:export\s+)?", "", line) for line in self.LINES if bind.match(line)]
        canonical = 'REVIEW_FILE="${_pd}/${PADDED}-REVIEW.md"'
        self.assertEqual(2, sum(1 for line in binds if line.startswith(canonical)), "each fence must bind the canonical lookup exactly once")
        for line in binds:
            self.assertTrue(line.startswith(canonical) or line.startswith('REVIEW_FILE="${REVIEW_FILE}"'),
                            f"REVIEW_FILE is rebound to something other than the canonical lookup: {line}")

    @needs_bash
    def test_padding_agrees_with_the_reference_normalizer_across_the_letter_matrix(self):
        ids = ["3A", "8", "9", "08", "09", "12A", "4B", "23.1.2", "03A.1.2", "1", "06", "36.14", "08.5"]
        with tempfile.TemporaryDirectory(prefix="engineer-crp-") as directory:
            for phase, cells in zip(ids, crp.run_derivations(self.DERIVATIONS, ids, directory)):
                for cell in cells:
                    with self.subTest(phase=phase):
                        self.assertEqual(crp.normalize_phase_name(phase), cell, f"padding drifted from the normalizer on {phase}")

    @needs_bash
    def test_padding_agrees_with_the_reference_normalizer_on_any_accepted_id(self):
        import random
        rng = random.Random(5213)
        digits = lambda: "".join(rng.choice("0123456789") for _ in range(rng.randint(1, 8)))  # noqa: E731
        ids = [digits() + rng.choice(["", "", *"ABCDEFGHIJKLMNOPQRSTUVWXYZ"]) + "".join("." + digits() for _ in range(rng.randint(0, 4)))
               for _ in range(25)]
        with tempfile.TemporaryDirectory(prefix="engineer-crp-") as directory:
            for phase, cells in zip(ids, crp.run_derivations(self.DERIVATIONS, ids, directory)):
                for cell in cells:
                    with self.subTest(phase=phase):
                        self.assertEqual(crp.normalize_phase_name(phase), cell)

    @needs_bash
    def test_composition_derivation_and_lookup_resolve_the_letter_phase_review(self):
        with tempfile.TemporaryDirectory(prefix="engineer-crp-") as directory:
            for phase, status in [("3A", "clean"), ("8", "issues"), ("9", "skipped")]:
                padded = crp.normalize_phase_name(phase)
                Path(directory, f"{padded}-REVIEW.md").write_bytes(f"---\nstatus: {status}\n---\n# review\n".encode("utf-8"))
                for derivation in self.DERIVATIONS:
                    script = "\n".join(["set -e", derivation, 'test -f "$REVIEW_FILE" || { echo "MISSING $REVIEW_FILE"; exit 3; }',
                                        'printf \'%s %s\' "$PADDED" "$(grep -m1 "^status:" "$REVIEW_FILE" | cut -d: -f2 | tr -d " ")"'])
                    result = crp.run_bash(script, env={**os.environ, "PHASE_DIR": crp.posix(directory), "PHASE_NUMBER": phase})
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                    self.assertEqual(f"{padded} {status}", result.stdout.strip())


class FixerTypeScriptCheck(unittest.TestCase):
    """Upstream #5213: the fixer's Tier-2 TypeScript check is project-aware."""

    def typescript_row(self, text):
        return next((line for line in text.splitlines() if line.startswith("| TypeScript |")), "")

    def test_edited_file_is_never_passed_to_tsc_positionally(self):
        self.assertIsNone(re.search(r"tsc\s+--noEmit\s+\{file\}", FIXER), 'a positional "tsc --noEmit {file}" check remains')
        self.assertIsNone(re.search(r"tsc\s+--noEmit\s+\S*\.tsx?\b", FIXER), "a positional tsc file argument remains")

    def test_typescript_row_prefers_the_project_typecheck_and_a_config_that_includes_the_file(self):
        row = self.typescript_row(FIXER)
        self.assertNotEqual("", row, "no TypeScript row in the Tier-2 table")
        self.assertRegex(row, r"(?i)typecheck")
        self.assertIn("--listFilesOnly", row)
        self.assertRegex(row, r"(?i)Tier 1")

    def test_solution_style_root_config_is_not_treated_as_passing(self):
        self.assertRegex(FIXER, r"(?i)solution-style")
        self.assertRegex(FIXER, r'"files": \[\]|files: \[\]')

    def test_other_tier_2_rows_are_unchanged(self):
        self.assertIn("| JavaScript | `node -c {file}` (syntax check) |", FIXER)
        self.assertIn("| Python | `python -c \"import ast; ast.parse(open('{file}').read())\"` |", FIXER)
        self.assertIn("| Other | Skip to Tier 1 only |", FIXER)

    def test_procedure_says_how_to_find_the_config_filter_the_output_and_avoid_build_artifacts(self):
        self.assertRegex(FIXER, r"(?i)walk up")
        self.assertIn("-p <config>", FIXER)
        self.assertIn("never `-b`", FIXER)
        self.assertRegex(FIXER, r"(?i)only (?:output )?lines (?:that start with|for) `\{file\}`")

    def test_compact_variant(self):
        self.skipTest("agents/code-fixer.compact.md absent in this repo")

    def test_scoping_rule_and_fallback_list_use_the_project_aware_form(self):
        self.assertIsNone(re.search(r"If `npx tsc --noEmit \{file\}`", FIXER), "the scoping rule still names the positional form")
        self.assertIsNone(re.search(r"syntax check \(node -c, tsc --noEmit,", FIXER), "the fallback list still names bare tsc --noEmit")


class HelperModuleResolver(unittest.TestCase):
    """Review operations share the identity-checked Python runtime launcher."""

    def test_every_helper_loading_step_uses_the_runtime_dispatcher(self):
        for verb in ("review.flags", "review.depth", "review.normalize-fallow"):
            with self.subTest(verb=verb):
                self.assertIn("engineer_run query " + verb, WORKFLOW_LF)
        self.assertNotRegex(WORKFLOW_LF, r"require\(['\"]\./engineer/bin/lib")

    def test_other_resolver_sites(self):
        self.skipTest("upstream review.md and structural-pre-pass.md fixtures absent in this repo")

    def test_one_identity_checked_resolver_initializes_all_operations(self):
        self.assertEqual(1, WORKFLOW_LF.count("_engineer_identity_ok()"))
        self.assertIn('query runtime-identity --pick packageName --raw', WORKFLOW_LF)


@needs_bash
class HelperModuleResolverExecuted(TempCase):
    """Run the actual resolver preamble against copied Python installations."""

    def setUp(self):
        self.sandbox = self.temp("engineer-launcher-")
        self.project = self.sandbox / "project"
        self.home = self.sandbox / "home"
        self.project.mkdir()
        self.home.mkdir()
        start = WORKFLOW_LF.index("_engineer_identity_ok()")
        self.script = WORKFLOW_LF[start:WORKFLOW_LF.index('if [ -n "${CLAUDE_ENV_FILE:-}"', start)]

    def install(self, root):
        target = root / "engineer" / "bin"
        shutil.copytree(SOURCE / "engineer" / "bin", target)
        return target / "engineer_run"

    def run_block(self, env=None, prefix=""):
        clean = {key: value for key, value in os.environ.items() if key not in
                 {"ENGINEER_RUN", "RUNTIME_DIR", "CLAUDE_CONFIG_DIR", "CODEX_HOME", "ENGINEER_ROOT"}}
        clean.update({"HOME": crp.posix(self.home), "CODEX_HOME": crp.posix(self.home / ".codex"),
                      "CLAUDE_CONFIG_DIR": crp.posix(self.home / ".claude"), **(env or {})})
        return crp.run_bash(prefix + self.script + '\nprintf "%s\n" "$ENGINEER_RUN"\n'
                            + 'engineer_run query review.flags -- --fix --depth deep', cwd=self.project, env=clean)

    def assert_selected(self, result, path):
        self.assertEqual(0, result.returncode, result.stderr)
        lines = result.stdout.splitlines()
        # Git Bash may alias the host temporary root as /tmp.
        expected_suffix = "/" + path.relative_to(self.sandbox.parent).as_posix()
        self.assertTrue(lines[0].replace("\\", "/").endswith(expected_suffix), lines[0])
        flags = json.loads("\n".join(lines[1:]))
        self.assertTrue(flags["fix"])
        self.assertEqual("deep", flags["depth"])

    def test_global_install_resolves_from_the_default_home(self):
        launcher = self.install(self.home / ".claude")
        self.assert_selected(self.run_block(), launcher)

    def test_launcher_on_path_locates_the_install(self):
        launcher = self.install(self.sandbox / "path-install")
        self.assert_selected(self.run_block({"PATH": crp.posix(launcher.parent) + ":" + os.environ.get("PATH", "").replace("\\", "/")}) , launcher)

    def test_local_install_resolves_from_runtime_dir(self):
        root = self.sandbox / "explicit-root"
        launcher = self.install(root)
        self.assert_selected(self.run_block({"RUNTIME_DIR": crp.posix(root)}), launcher)

    def test_engineer_run_environment_is_the_first_candidate(self):
        launcher = self.install(self.sandbox / "explicit")
        self.install(self.home / ".claude")
        self.assert_selected(self.run_block({"ENGINEER_RUN": crp.posix(launcher)}), launcher)

    def test_missing_runtime_stops_with_actionable_error(self):
        result = self.run_block()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("No engineer-runtime launcher was found", result.stderr)
        self.assertEqual("", result.stdout)

    def test_malformed_explicit_runtime_does_not_fall_back(self):
        bad = self.sandbox / "wrong-runtime"
        bad.write_text('#!/bin/sh\nprintf wrong-package', encoding="utf-8")
        self.install(self.home / ".claude")
        result = self.run_block({"ENGINEER_RUN": crp.posix(bad)})
        self.assertNotEqual(0, result.returncode)
        self.assertIn("does not identify engineer-runtime", result.stderr)

    def test_local_install_under_claude_or_codex_resolves_from_project_root(self):
        for name in (".claude", ".codex"):
            with self.subTest(name):
                launcher = self.install(self.project / name)
                self.assert_selected(self.run_block(), launcher)
                shutil.rmtree(self.project / name)

    def test_launcher_shell_function_is_not_read_as_a_path(self):
        result = self.run_block(prefix="engineer_run() { :; }\n")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)

    def test_symlinked_launcher_preserves_runtime_and_flag_parsing(self):
        launcher = self.install(self.sandbox / "real")
        link = self.sandbox / "linked-launcher"
        try:
            link.symlink_to(launcher)
        except OSError as error:
            self.skipTest("host cannot create symlinks: " + str(error))
        self.assert_selected(self.run_block({"ENGINEER_RUN": crp.posix(link)}), link)


class ReviewOptionsViaCLI(TempCase):
    def test_flags_preserve_literal_values_and_implied_fix(self):
        for flag in ("--fix", "--all", "--auto"):
            with self.subTest(flag=flag):
                result = runtime_query(self.temp(), "review.flags", "--", "02", flag,
                                       "--files", "src/a file.py", "--files", "Dockerfile", "--depth=deep")
                self.assertEqual(0, result.returncode, result.stderr)
                value = json.loads(result.stdout)
                self.assertTrue(value["fix"])
                self.assertEqual("02", value["phase"])
                self.assertEqual("src/a file.py,Dockerfile", value["files"])
                self.assertEqual("deep", value["depth"])

    def test_malformed_flags_fail_instead_of_becoming_success(self):
        for arguments in (("--depth",), ("--unknown",), ("--files", "--fix")):
            with self.subTest(arguments=arguments):
                result = runtime_query(self.temp(), "review.flags", "--", *arguments)
                self.assertNotEqual(0, result.returncode)

    @needs_bash
    def test_shipped_depth_fence_dispatches_effective_depth_after_large_scope_downgrade(self):
        script = crp.fence_containing(WORKFLOW_LF, "DEPTH_FIELDS=$(", WORKFLOW_LF.index('<step name="resolve_depth">'))
        for count, expected in ((50, "deep"), (51, "standard")):
            with self.subTest(count=count):
                directory = self.temp()
                result = runtime_query(directory, "review.depth", "--stdin", input=json.dumps({
                    "flagDepth": "deep", "files": ["src/file" + str(number) + ".py" for number in range(count)]}))
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(expected, json.loads(result.stdout)["depth"])
                executed = crp.run_bash(script + '\nprintf "EFFECTIVE_DEPTH=%s\n" "$REVIEW_DEPTH"', cwd=directory,
                                        env={**os.environ, "DEPTH_OK": "true", "DEPTH_JSON": result.stdout})
                self.assertEqual(0, executed.returncode, executed.stderr)
                self.assertIn("EFFECTIVE_DEPTH=" + expected, executed.stdout)

    def test_depth_rejects_outside_project_paths(self):
        result = runtime_query(self.temp(), "review.depth", "--stdin", input=json.dumps({"files": ["../outside.py"]}))
        self.assertNotEqual(0, result.returncode)


class LegacyLedgerGroups(TempCase):
    """Exercise the Python equivalents of the former embedded-script cases."""

    def test_fence_tracking_status_and_count_consistency(self):
        for fence in ("```", "~~~"):
            with self.subTest(fence=fence):
                text = review_doc(fence + "text", "### CR-01: example", fence + "extra", fence,
                                  "### WR-01: real", status="clean")
                out = crp.ReconcileFixture(self.temp()).run(text)
                self.assertEqual(["WR-01"], [row["id"] for row in out["rows"]])

    def test_iteration_fix_reports_prefer_the_latest_decision(self):
        out = crp.ReconcileFixture(self.temp()).run(review_doc("### CR-01: a"), iterations={
            1: "## Skipped Issues\n### CR-01: a\nreason one",
            2: "## Skipped Issues\n### CR-01: a\nreason two"})
        self.assertEqual("01-REVIEW-FIX.iter2.md", out["rows"][0]["source"])
        self.assertEqual("skipped", out["rows"][0]["disposition"])

    def test_cli_keeps_shell_metacharacters_literal(self):
        title = 'literal $(touch injected) `whoami` "$HOME" — review'
        fixture = crp.ReconcileFixture(self.temp())
        out = fixture.run(review_doc("### CR-01: " + title))
        self.assertEqual(title, out["result"]["findings"][0]["title"])
        self.assertFalse((fixture.directory / "injected").exists())

    def test_absent_review_still_reconciles(self):
        out = crp.ReconcileFixture(self.temp()).run(prior="| CR-01 | critical | deferred | wait |")
        self.assertEqual(0, out["returncode"], out["stderr"])
        self.assertEqual(("CR-01", "deferred", True),
                         (out["rows"][0]["id"], out["rows"][0]["disposition"], out["rows"][0]["carried"]))

    def test_invalid_count_values_are_rejected(self):
        for value in ("-1", "garbage", "1.5"):
            with self.subTest(value=value):
                out = crp.ReconcileFixture(self.temp()).run(review_doc("### CR-01: a"), review_total=value)
                self.assertNotEqual(0, out["returncode"])


class ModuleUnitsC(TempCase):
    def test_disposition_script_extraction_unescapes_shell_quoting(self):
        body = r'const a = `\${b}` + \"q\" + \\n;'
        src = 'x\nFOO=1 node -e "\n' + body + '\n" || echo skipped\ny'
        script = crp.disposition_script(src)
        self.assertEqual('\nconst a = `${b}` + "q" + \\n;', script)
        with self.assertRaises(ValueError):
            crp.disposition_script("no script")
        with self.assertRaises(ValueError):
            crp.disposition_script('node -e "unterminated')

    def test_id_alternations_and_severity_map(self):
        script = r"a=/^(?:CR|BL|WR|IN)-/; b=/(?:IN|WR|BL|CR)-\d/; const s = ({CR:'critical', BL:'critical', WR:'warning'}[id.split('-')[0]])"
        self.assertEqual(["BL|CR|IN|WR", "BL|CR|IN|WR"], crp.id_alternations(script))
        self.assertEqual(["CR", "BL", "WR"], crp.severity_map_keys(script))
        with self.assertRaises(ValueError):
            crp.severity_map_keys("nothing")

    def test_emitted_id_prefixes_reads_headings_and_prose(self):
        text = "### CR-01: a\nBL- IDs are tier-equivalent\nIDs beginning with `SEC-` are extra\nX- prefix too"
        self.assertEqual({"CR", "BL", "SEC", "X"}, crp.emitted_id_prefixes(text))

    def test_anchored_line_indexes_enforces_the_count(self):
        lines = ["a", "xx", "b", "xx"]
        self.assertEqual([1, 3], crp.anchored_line_indexes(lines, "xx", 2))
        with self.assertRaises(ValueError):
            crp.anchored_line_indexes(lines, "xx", 1)

    def test_normalize_phase_name(self):
        self.assertEqual("03", crp.normalize_phase_name("3"))
        self.assertEqual("03A", crp.normalize_phase_name("3A"))
        self.assertEqual("008", crp.normalize_phase_name("008"))
        self.assertEqual("23.1.2", crp.normalize_phase_name("23.1.2"))
        self.assertEqual("../x", crp.normalize_phase_name("../x"))

    def test_resolver_blocks_and_shape(self):
        src = ("pre\n# engineer-resolve-lib begin a.cjs: why\n_engineer_lib_probe=\"a.cjs\"\n"
               "_engineer_gr=\"$(command -v x)\"\n_engineer_pick \"$d\" \"$_engineer_gr\" || true\n"
               "if [ -z \"$ENGINEER_LIB_DIR\" ]; then echo a.cjs; fi\n# engineer-resolve-lib end\nmid\n"
               "  # engineer-resolve-lib begin b.cjs: why\n  _engineer_lib_probe=\"b.cjs\"\n"
               "  _engineer_pick \"$d\" || true\n  # engineer-resolve-lib end\n")
        blocks = crp.resolver_blocks(src)
        self.assertEqual(["a.cjs", "b.cjs"], [block["module"] for block in blocks])
        self.assertEqual(crp.resolver_shape(blocks[0]["text"], "a.cjs").split("\n")[1:],
                         crp.resolver_shape(blocks[1]["text"], "b.cjs").split("\n")[1:])

    @needs_bash
    def test_run_derivations_and_resolver_block_run_under_bash(self):
        directory = self.temp()
        cells = crp.run_derivations(['PADDED="${PHASE_NUMBER}x"'], ["1", "2"], directory)
        self.assertEqual([["1x"], ["2x"]], cells)
        result = crp.run_resolver_block('# engineer-resolve-lib begin m: x\nENGINEER_LIB_DIR=/lib\n# engineer-resolve-lib end', dict(os.environ), directory)
        self.assertEqual("/lib", result.stdout)

    def test_parse_gate_counts_ignores_unicode_spaces_like_the_c_locale(self):
        parsed = crp.parse_gate_counts("---\nstatus: clean\u2003\n---")
        self.assertEqual("clean\u2003", parsed["status"])
        self.assertEqual("", crp.render_gate_message(crp.parse_gate_counts("---\nstatus: clean\n---"), 1))
        self.assertEqual(crp.GATE_UNPARSED, crp.render_gate_message(crp.parse_gate_counts(""), 1))
        inconsistent = "---\nstatus: issues_found\nfindings:\n  critical: 1\n  warning: 1\n  info: 1\n  total: 2\n---"
        self.assertTrue(crp.render_gate_message(crp.parse_gate_counts(inconsistent), 7).startswith("Code review found issues."))
        self.assertTrue(crp.render_gate_message(crp.parse_gate_counts(inconsistent), 7).endswith("/code-review 7 --fix\n"))
        self.assertEqual({"reported": False}, crp.read_gate_message(""))


class LedgerLegendText(TempCase):
    """The rendered Python ledger explains retained history and decision behavior."""

    def test_ledger_does_not_promise_unconditional_preservation(self):
        out = crp.ReconcileFixture(self.temp()).run(review_doc("### CR-01: a"))
        self.assertNotIn("preserves every row and every disposition", out["ledger"])
        self.assertIn("Reused labels retain the displaced finding in history", out["ledger"])

    def test_reused_id_keeps_displaced_open_record_in_history(self):
        fixture = crp.ReconcileFixture(self.temp())
        fixture.run(review_doc("### CR-01: old"))
        out = fixture.run(review_doc("### CR-01: new"))
        self.assertEqual("open", out["rows"][0]["disposition"])
        self.assertTrue(any(event.get("action") == "finding-id-reused" and
                            event["finding"]["title"] == "old" for event in json.loads(runtime_query(fixture.directory, "frontmatter.get", fixture.ledger_path.name, "--field", "history").stdout)))

    def test_displaced_decision_remains_in_history_with_id_and_disposition(self):
        fixture = crp.ReconcileFixture(self.temp())
        fixture.run(review_doc("### CR-01: old"), prior="| CR-01 | critical | deferred | waiting |")
        out = fixture.run(review_doc("### CR-01: new"))
        displaced = [event["finding"] for event in json.loads(runtime_query(fixture.directory, "frontmatter.get", fixture.ledger_path.name, "--field", "history").stdout) if event.get("action") == "finding-id-reused"]
        self.assertTrue(any(row["id"] == "CR-01" and row["disposition"] == "deferred" for row in displaced))

    def test_block_2_gates_on_review_status_in_shell(self):
        fences = crp.bash_fences(DISPOSITION)
        self.assertGreaterEqual(len(fences), 2)
        self.assertRegex(fences[1], "REVIEW_STATUS")
        self.assertRegex(fences[1], r"clean\|skipped")


# --- Increment D: the disposition ledger, through `review.reconcile` -------------------------

def review_doc(*body, status="issues_found", counts=None):
    head = ["---", "phase: 01", "status: " + status]
    if counts:
        head[2:2] = ["findings:", *[f"  {key}: {value}" for key, value in counts.items()]]
    return "\n".join([*head, "---", "", *body])


def triple(rows):
    return [(row["id"], row["severity"], row["disposition"]) for row in rows]


class DispositionLedgerViaVerb(TempCase):
    """Upstream #3829/#3861 behavior through the registered Python review.reconcile command."""

    def fixture(self, phase="01"):
        return crp.ReconcileFixture(self.temp("engineer-3829-"), phase)

    def by_id(self, out):
        return {row["id"]: row for row in out["rows"]}

    def test_every_finding_is_recorded_defaulting_to_open_at_the_right_severity(self):
        out = self.fixture().run(REVIEW_WITH_FINDINGS)
        self.assertEqual(0, out["returncode"], out["stderr"])
        self.assertEqual([("CR-01", "critical", "open"), ("WR-01", "warning", "open"), ("WR-02", "warning", "open"), ("IN-01", "info", "open")],
                         triple(out["rows"]))
        self.assertEqual((3 + 1, 4), (out["result"]["open"], out["result"]["total"]))

    def test_bl_findings_are_recorded_at_the_critical_tier(self):
        out = self.fixture().run(REVIEW_WITH_FINDINGS.replace("### CR-01:", "### BL-01:"))
        self.assertEqual(("BL-01", "critical"), (out["rows"][0]["id"], out["rows"][0]["severity"]))

    def test_the_ledger_is_a_sibling_and_the_review_is_never_written(self):
        fixture = self.fixture("02")
        review = "---\nstatus: issues_found\n---\n\n### CR-01: a finding"
        fixture.run(review)
        self.assertTrue(fixture.ledger_path.exists())
        self.assertEqual(review, (fixture.directory / "02-REVIEW.md").read_text(encoding="utf-8"))

    def test_finding_ids_are_enumerated_in_order_once_each(self):
        review = review_doc("### CR-01: a", "### WR-01: b", "### IN-01: c", "### CR-01: a")
        self.assertEqual(["CR-01", "WR-01", "IN-01"], [row["id"] for row in self.fixture().run(review)["rows"]])

    def test_conflicting_duplicate_id_fails_closed_without_writing_a_ledger(self):
        review = review_doc("### CR-01: a", "### WR-01: b", "### IN-01: c", "### CR-01: a duplicate id, which must not produce a second row")
        fixture = self.fixture()
        out = fixture.run(review)
        self.assertNotEqual(0, out["returncode"])
        self.assertIn("ambiguous-review-finding", out["stderr"])
        self.assertFalse(fixture.ledger_path.exists(), "ambiguous IDs must not create a partial ledger")

    def test_a_recorded_decision_survives_a_rerun_and_keeps_its_reason(self):
        prior = "| CR-01 | critical | deferred | ships next phase |\n| WR-01 | warning | open | - |\n"
        out = self.fixture().run(REVIEW_WITH_FINDINGS, prior=prior)
        row = self.by_id(out)["CR-01"]
        self.assertEqual(("deferred", "ships next phase"), (row["disposition"], row["source"]))
        self.assertEqual(3, out["result"]["open"])

    def test_a_deferral_reason_with_punctuation_survives_verbatim(self):
        prior = "| CR-01 | critical | deferred | ships next phase, see ADR-99 |"
        self.assertEqual("ships next phase, see ADR-99", self.by_id(self.fixture().run(REVIEW_WITH_FINDINGS, prior=prior))["CR-01"]["source"])

    def test_a_hand_edited_row_missing_its_trailing_pipe_still_preserves_the_decision(self):
        review = review_doc("### CR-01: a")
        row = self.by_id(self.fixture().run(review, prior="| CR-01 | critical | deferred | see issue 42"))["CR-01"]
        self.assertEqual(("deferred", "see issue 42"), (row["disposition"], row["source"]))

    def test_a_review_with_no_finding_headings_produces_no_record(self):
        fixture = self.fixture("02")
        out = fixture.run("---\nphase: 02\nstatus: issues_found\n---\n\nprose only")
        self.assertFalse(out["written"])
        self.assertFalse(fixture.ledger_path.exists())

    def test_a_decided_finding_the_review_no_longer_reports_is_carried_not_dropped(self):
        prior = "| CR-01 | critical | deferred | ships next phase |\n| IN-01 | info | open | - |\n"
        out = self.fixture().run(review_doc("### WR-01: still here"), prior=prior)
        rows = self.by_id(out)
        self.assertEqual(("deferred", True, "ships next phase"), (rows["CR-01"]["disposition"], rows["CR-01"]["carried"], rows["CR-01"]["source"]))
        self.assertEqual(("open", True), (rows["IN-01"]["disposition"], rows["IN-01"]["carried"]))

    def test_the_carried_marker_is_rendered_never_stored_so_it_cannot_accumulate(self):
        fixture = self.fixture()
        shrunk = review_doc("### WR-01: b")
        out = fixture.run(shrunk, prior="| CR-01 | critical | deferred | ships next phase |")
        for _ in range(3):
            out = fixture.run(shrunk)
        self.assertEqual("ships next phase", self.by_id(out)["CR-01"]["source"])
        self.assertLessEqual(fixture.ledger_path.read_text(encoding="utf-8").count("(not in the current review)"), 1)

    def test_a_review_reporting_nothing_still_reconciles_an_existing_ledger(self):
        prior = "| CR-01 | critical | deferred | ships next phase |\n| WR-01 | warning | open | - |\n"
        out = self.fixture().run(review_doc("no findings"), prior=prior)
        self.assertEqual(["CR-01", "WR-01"], [row["id"] for row in out["rows"]])
        self.assertEqual([("deferred", True), ("open", True)], [(row["disposition"], row["carried"]) for row in out["rows"]])
        self.assertEqual(1, out["result"]["open"])

    def test_a_review_with_no_findings_and_no_prior_ledger_produces_nothing(self):
        self.assertFalse(self.fixture().run(review_doc("no findings"))["written"])

    def test_a_deferral_on_a_finding_still_in_the_review_is_not_reset_to_open(self):
        out = self.fixture().run(REVIEW_WITH_FINDINGS, prior="| WR-01 | warning | deferred | later |")
        self.assertEqual("deferred", self.by_id(out)["WR-01"]["disposition"])

    def test_unchanged_run_rewrites_nothing(self):
        fixture = self.fixture()
        fixture.run(REVIEW_WITH_FINDINGS)
        before = fixture.ledger_path.read_bytes()
        out = fixture.run(REVIEW_WITH_FINDINGS)
        self.assertEqual(before, fixture.ledger_path.read_bytes())
        self.assertTrue(out["result"].get("unchanged"))

    def test_a_skipped_outcome_is_reconciled_from_the_fix_report_with_provenance(self):
        fix = "\n".join(["# Phase 01: Code Review Fix Report", "", "## Fixed Issues", "", "### WR-01: missing null check", "",
                         "## Skipped Issues", "", "### WR-02: unused import"])
        rows = self.by_id(self.fixture().run(REVIEW_WITH_FINDINGS, fix=fix))
        self.assertEqual(("skipped", "01-REVIEW-FIX.md"), (rows["WR-02"]["disposition"], rows["WR-02"]["source"]))
        self.assertEqual("open", rows["CR-01"]["disposition"])

    def test_a_fixed_heading_without_a_commit_receipt_leaves_the_finding_open(self):
        fix = "## Fixed Issues\n\n### WR-01: missing null check"
        out = self.fixture().run(REVIEW_WITH_FINDINGS, fix=fix)
        rows = self.by_id(out)
        self.assertEqual("open", rows["WR-01"]["disposition"])
        self.assertEqual(4, out["result"]["open"])
        self.assertIn("fixed-report-missing-commit", [item["kind"] for item in out["result"]["diagnostics"]])

    def test_a_fixed_heading_without_receipt_preserves_an_earlier_deferral(self):
        out = self.fixture().run(REVIEW_WITH_FINDINGS, prior="| CR-01 | critical | deferred | later |",
                                 fix="## Fixed Issues\n\n### CR-01: SQL injection in auth")
        self.assertEqual("deferred", out["rows"][0]["disposition"])
        self.assertEqual(3, out["result"]["open"])
        self.assertIn("fixed-report-missing-commit", [item["kind"] for item in out["result"]["diagnostics"]])

    def test_the_gate_requires_a_commit_receipt_before_a_fixed_outcome_resolves(self):
        fixture = self.fixture()
        review = "\n".join(["---", "phase: 01", "status: issues_found", "findings:", "  critical: 1", "  warning: 1", "  info: 0",
                            "  total: 2", "---", "", "## Critical Issues", "", "### CR-01: the critical one", "", "## Warnings", "",
                            "### WR-01: the warning one"])
        fix = "\n".join(["---", "status: complete", "---", "", "## Fixed Issues", "", "### CR-01: the critical one", "",
                         "## Skipped Issues", "", "### WR-01: the warning one"])
        gate = fixture.run(review, review_total=2)
        self.assertEqual(["open", "open"], [row["disposition"] for row in gate["rows"]])
        after = fixture.run(review, fix=fix, review_total=2)
        self.assertEqual([("CR-01", "open"), ("WR-01", "skipped")], [(row["id"], row["disposition"]) for row in after["rows"]])
        self.assertEqual(1, after["result"]["open"])
        self.assertIn("fixed-report-missing-commit", [item["kind"] for item in after["result"]["diagnostics"]])

    def test_a_section_heading_that_merely_starts_with_fixed_issues_does_not_classify_findings(self):
        fix = "# Fix report\n\n## Fixed Issues Verification\n\n### IN-01: named while verifying"
        self.assertEqual("open", self.by_id(self.fixture().run(REVIEW_WITH_FINDINGS, fix=fix))["IN-01"]["disposition"])

    def test_a_finding_heading_outside_the_fixed_or_skipped_sections_is_not_a_disposition(self):
        fix = "## Skipped Issues\n\n### WR-01: missing null check\n\n## Verification\n\n### IN-01: mentioned while describing how the fix was verified"
        rows = self.by_id(self.fixture().run(REVIEW_WITH_FINDINGS, fix=fix))
        self.assertEqual(("skipped", "open"), (rows["WR-01"]["disposition"], rows["IN-01"]["disposition"]))

    def test_a_stale_fix_report_does_not_mark_a_new_finding_of_the_same_id_as_decided(self):
        review = review_doc("### CR-01: a new finding")
        stale = "## Skipped Issues\n\n### CR-01: what this id used to mean"
        self.assertEqual("open", self.by_id(self.fixture().run(review, fix=stale))["CR-01"]["disposition"])

    def test_a_skipped_outcome_naming_the_same_finding_still_applies(self):
        review = review_doc("### CR-01: the same finding")
        fix = "## Skipped Issues\n\n### CR-01: the same finding"
        self.assertEqual("skipped", self.by_id(self.fixture().run(review, fix=fix))["CR-01"]["disposition"])

    def test_a_finding_heading_inside_a_fenced_block_is_an_example_not_a_finding(self):
        review = review_doc("```", "### CR-77: an example inside a fence", "```", "", "### CR-01: a real finding")
        self.assertEqual(["CR-01"], [row["id"] for row in self.fixture().run(review)["rows"]])

    def test_a_foreign_fence_marker_inside_a_fence_does_not_swap_example_for_finding(self):
        review = review_doc("```", "~~~", "### CR-77: an example inside a fence", "```", "", "### CR-01: a real finding")
        self.assertEqual(["CR-01"], [row["id"] for row in self.fixture().run(review)["rows"]])

    def test_a_line_with_an_info_string_is_an_opener_never_a_closer(self):
        review = review_doc("```", "```js", "### CR-77: still inside the fence", "```", "", "### CR-01: real")
        self.assertEqual(["CR-01"], [row["id"] for row in self.fixture().run(review)["rows"]])

    def test_a_finding_id_whose_prefix_is_a_js_object_property_name_produces_no_row(self):
        review = review_doc("### CONSTRUCTOR-01: a", "### TOSTRING-02: b", "### CR-01: real")
        self.assertEqual(["CR-01"], [row["id"] for row in self.fixture().run(review)["rows"]])

    def test_an_unterminated_frontmatter_block_yields_no_counts_to_reconcile_against(self):
        review = "\n".join(["---", "phase: 01", "status: issues_found", "", "# body", "", "total: 777", "### CR-01: a"])
        out = self.fixture().run(review, review_total=1)
        self.assertEqual(0, out["result"].get("unparsed", 0))


class DispositionSeverityViaVerb(TempCase):
    """Upstream #3861 round 2/11 (M3): severity comes from the section, not just the id prefix."""

    def severity(self, review, prior=None):
        out = crp.ReconcileFixture(self.temp("engineer-3861-")).run(review, prior=prior)
        return {row["id"]: row["severity"] for row in out["rows"]}

    def test_critical_misnumbered_as_wr_is_critical_under_the_critical_section(self):
        review = review_doc("## Critical Issues", "", "### CR-01: properly numbered", "", "### WR-04: a critical the reviewer mis-numbered", "",
                            "## Info", "", "### IN-01: an info item")
        self.assertEqual({"CR-01": "critical", "WR-04": "critical", "IN-01": "info"}, self.severity(review))

    def test_an_in_finding_under_warnings_is_recorded_warning(self):
        self.assertEqual({"IN-02": "warning"}, self.severity(review_doc("## Warnings", "", "### IN-02: mis-numbered the other way")))

    def test_the_id_prefix_governs_when_no_recognized_section_encloses_the_finding(self):
        review = review_doc("### CR-01: a", "### BL-02: b", "### WR-03: c", "### IN-04: d")
        self.assertEqual({"CR-01": "critical", "BL-02": "critical", "WR-03": "warning", "IN-04": "info"}, self.severity(review))

    def test_a_lookalike_section_heading_does_not_retier_the_findings_under_it(self):
        self.assertEqual({"IN-05": "info"}, self.severity(review_doc("## Critical Issues Verification", "", "### IN-05: not actually critical")))

    def test_a_section_heading_inside_a_fenced_example_does_not_govern(self):
        review = review_doc("```markdown", "## Critical Issues", "```", "", "### IN-06: outside the fence")
        self.assertEqual({"IN-06": "info"}, self.severity(review))

    def test_a_carried_row_keeps_the_severity_the_ledger_recorded(self):
        fixture = crp.ReconcileFixture(self.temp("engineer-3861-"))
        first = review_doc("## Critical Issues", "", "### CR-01: properly numbered", "", "### WR-04: a critical the reviewer mis-numbered", "")
        run1 = fixture.run(first)
        self.assertEqual("critical", {row["id"]: row["severity"] for row in run1["rows"]}["WR-04"])
        edited = run1["ledger"].replace("| WR-04 | critical | open | - |", "| WR-04 | critical | deferred | waiting on team A |")
        self.assertNotEqual(run1["ledger"], edited, "the hand edit must have landed")
        run2 = fixture.run(review_doc("## Critical Issues", "", "### CR-01: properly numbered", ""), prior=edited)
        row = {r["id"]: r for r in run2["rows"]}["WR-04"]
        self.assertEqual(("critical", "deferred", True), (row["severity"], row["disposition"], row["carried"]))
        self.assertTrue(row["source"].startswith("waiting on team A"))


class DispositionShortfallViaVerb(TempCase):
    """Upstream #3861 round 2 (B4) / round 12: a finding the heading parser cannot match is surfaced, not dropped."""

    REVIEW_5 = "\n".join(["---", "phase: 01", "status: issues_found", "findings:", "  critical: 1", "  warning: 2", "  info: 2", "  total: 5",
                          "---", "", "### CR-01: a conforming finding", "### WR-01: another conforming one", "### WR-02: a third",
                          "### SEC-01: a prefix the alternation does not carry", "#### IN-09: a heading one level too deep"])

    def run_one(self, review, **kwargs):
        return crp.ReconcileFixture(self.temp("engineer-3861-")).run(review, **kwargs)

    def test_the_shortfall_is_stated_in_the_ledger_and_the_result(self):
        out = self.run_one(self.REVIEW_5, review_total=5)
        self.assertEqual((2, 3), (out["result"]["unparsed"], out["result"]["total"]))
        self.assertRegex(out["ledger"], r"(?m)^unparsed: 2$")

    def test_a_review_whose_findings_all_parse_reports_no_shortfall(self):
        clean = review_doc("### CR-01: the only finding", counts={"critical": 1, "warning": 0, "info": 0, "total": 1})
        self.assertEqual(0, self.run_one(clean, review_total=1)["result"]["unparsed"])

    def test_an_absent_total_reconciles_nothing(self):
        legacy = review_doc("### CR-01: a", "### WR-01: b")
        out = self.run_one(legacy)
        self.assertEqual((0, 2), (out["result"]["unparsed"], out["result"]["total"]))

    def test_a_total_smaller_than_the_rows_is_not_a_negative_shortfall(self):
        review = "\n".join(["---", "phase: 01", "status: issues_found", "findings:", "  total: 1", "---", "", "### CR-01: a", "### WR-01: b"])
        out = self.run_one(review, review_total=1)
        self.assertEqual(0, out["result"]["unparsed"])
        self.assertNotRegex(out["ledger"], r"unparsed: -")

    def test_a_review_none_of_whose_findings_parse_still_records_the_shortfall(self):
        review = "\n".join(["---", "phase: 01", "status: issues_found", "findings:", "  critical: 2", "  warning: 0", "  info: 0", "  total: 2",
                            "---", "", "## Critical Issues", "", "### SEC-01: a prefix the alternation does not carry", "### SEC-02: and a second one"])
        out = self.run_one(review, review_total=2)
        self.assertTrue(out["written"], "silence here is the exact silent drop this reconciliation exists to close")
        self.assertEqual((2, 0), (out["result"]["unparsed"], out["result"]["total"]))

    def test_a_genuinely_clean_review_still_writes_nothing(self):
        clean = review_doc("No issues.", status="clean", counts={"critical": 0, "warning": 0, "info": 0, "total": 0})
        self.assertFalse(self.run_one(clean, review_total=0)["written"])

    def test_a_clean_review_with_an_unparseable_fix_report_still_writes_nothing(self):
        clean = review_doc("No issues.", status="clean", counts={"critical": 0, "warning": 0, "info": 0, "total": 0})
        fix = "## Fixed Issues\n\n### SEC-03: an unmatched id in the fix report"
        self.assertFalse(self.run_one(clean, fix=fix, review_total=0)["written"])

    def test_a_contradicting_findings_block_yields_no_shortfall(self):
        review = review_doc("", "### CR-01: a conforming finding", "### WR-01: another", "### WR-02: a third",
                            counts={"critical": 1, "warning": 1, "info": 1, "total": 10})
        out = self.run_one(review, review_total=10)
        self.assertEqual((0, 3), (out["result"]["unparsed"], out["result"]["total"]))

    def test_a_consistent_total_still_reconciles(self):
        review = review_doc("", "### CR-01: a conforming finding", "### WR-01: another", "### WR-02: a third",
                            counts={"critical": 2, "warning": 2, "info": 1, "total": 5})
        self.assertEqual(2, self.run_one(review, review_total=5)["result"]["unparsed"])

    def test_a_status_the_ledger_cannot_read_does_not_suppress_the_record(self):
        review = review_doc("### CR-01: a", status="clean:junk", counts={"critical": 1, "warning": 0, "info": 0, "total": 1})
        self.assertTrue(self.run_one(review, review_total=1)["written"])


class DispositionIdentityViaVerb(TempCase):
    """Upstream #3829/#3861 round 5: a reused id does not inherit the old finding's decision."""

    def test_a_decision_is_not_inherited_when_the_id_now_names_a_different_finding(self):
        fixture = crp.ReconcileFixture(self.temp("engineer-3861-"))
        seed = fixture.run(review_doc("### CR-01: the original finding"), prior="| CR-01 | critical | deferred | waiting on the vendor |\n")
        out = fixture.run(review_doc("### CR-01: a brand new finding"), prior=seed["ledger"])
        self.assertEqual("open", out["rows"][0]["disposition"], "a reused id must not inherit the old decision")

if __name__ == "__main__":
    unittest.main()
