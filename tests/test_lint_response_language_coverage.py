"""Behavior contract for lib.lint_response_language_coverage (port of scripts/lint-response-language-coverage.cjs)."""
import contextlib
import importlib
import importlib.util
import io
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "engineer" / "bin"
LIB = BIN / "lib"


def _load(name):
    """Import engineer/bin/lib/<name> as an isolated package (another `lib` package exists under .ai/runtime)."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB / "__init__.py",
                                                      submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib." + name)


lint = _load("lint_response_language_coverage")

IMPORT_LINE = "@~/.claude/engineer/references/response-language-directive.md"
COVERED_INLINE = "Apply response_language to all user-facing prose, narration included.\n"
STRONG_REFERENCE = ("ALL user-facing output of this workflow MUST be in `response_language` — "
                    "narration between tool calls, findings, and report prose.\n")
WEAK_REFERENCE = ("**If `response_language` is set:** All user-facing questions, prompts, and "
                  "explanations in this workflow MUST be presented in `{response_language}`.\n")


class Recorder:
    def __init__(self):
        self.errors, self.logs = [], []

    def error(self, message):
        self.errors.append(message)

    def log(self, message):
        self.logs.append(message)


class Case(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.n = 0

    def tree(self):
        self.n += 1
        root = self.base / f"t{self.n}"
        root.mkdir()
        return root

    def write(self, root, relative, content):
        target = Path(root) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="")
        return target

    def rel(self, files, root):
        return [str(Path(f).relative_to(root)).replace(os.sep, "/") for f in files]

    def fixture(self):
        root = self.tree()
        self.write(root, "covered-by-reference.md", IMPORT_LINE + "\n")
        self.write(root, "nested/covered-inline.md", "Use config.response_language for all prose, narration included.\n")
        self.write(root, "nested/mere-field-mention.md", "Parse JSON for: phase_number, response_language.\n")
        self.write(root, "nested/modes/uncovered.md", "# English-only mode\n")
        self.write(root, "nested/ignored.txt", "not a workflow")
        return root

    def reference_fixture(self, reference_text):
        root = self.tree()
        (root / "references").mkdir()
        (root / "workflows").mkdir()
        self.write(root / "workflows", "takes-the-reference.md", IMPORT_LINE + "\n")
        if reference_text is not None:
            self.write(root, "references/response-language-directive.md", reference_text)
        return root, root / "workflows"

    def fragment_fixture(self, parent_covered=True, parent_names_fragment=True, kind="steps", name="converge-banner.md"):
        root = self.tree()
        stub = f"read and execute `engineer/workflows/autonomous/{kind}/{name if parent_names_fragment else 'something-else.md'}`"
        self.write(root, "autonomous.md", "\n".join([IMPORT_LINE if parent_covered else "# No directive here", stub]) + "\n")
        self.write(root, f"autonomous/{kind}/{name}", "Display: `Planning: convergence enabled`\n")
        return root

    def reference_root_for(self, root):
        # The default reference root must hold the strong shared reference for @-import coverage.
        ref_root = self.tree()
        self.write(ref_root, "references/response-language-directive.md", STRONG_REFERENCE)
        return ref_root


class Discovery(Case):
    def test_walks_nested_directories_and_ignores_non_markdown(self):
        root = self.fixture()
        self.assertEqual(["covered-by-reference.md", "nested/covered-inline.md", "nested/mere-field-mention.md",
                          "nested/modes/uncovered.md"], self.rel(lint.find_markdown_files_recursive(str(root)), root))

    def test_uppercase_extension_is_discovered_and_is_a_violation_not_an_exemption(self):
        root = self.tree()
        self.write(root, "SHOUTING.MD", "# no directive\n")
        self.write(root, "mixed.Md", "# no directive\n")
        self.write(root, "not-a-workflow.mdx", "# a format the catalog does not emit\n")
        self.assertEqual(["SHOUTING.MD", "mixed.Md"], self.rel(lint.find_markdown_files_recursive(str(root)), root))
        self.assertEqual(["SHOUTING.MD", "mixed.Md"], self.rel(lint.find_violations(str(root)), root))

    def test_every_admitted_extension_is_reachable_by_the_case_insensitive_match(self):
        for extension in lint.WORKFLOW_EXTENSIONS:
            self.assertEqual(extension.lower(), extension, f"{extension} can never match")
            self.assertTrue(extension.startswith("."), f"{extension} is not an extension splitext returns")

    def test_is_workflow_file(self):
        self.assertTrue(lint.is_workflow_file("a.md"))
        self.assertTrue(lint.is_workflow_file("A.MD"))
        self.assertFalse(lint.is_workflow_file("a.mdx"))
        self.assertFalse(lint.is_workflow_file(".md"))
        self.assertFalse(lint.is_workflow_file("md"))

    def link_directory(self, target, link):
        try:
            os.symlink(target, link, target_is_directory=True)
            return
        except (OSError, NotImplementedError):
            pass
        if os.name == "nt":
            made = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
            if made.returncode == 0:
                return
        self.skipTest("directory links unavailable on this host")

    def test_walk_follows_a_linked_subtree_instead_of_skipping_it(self):
        root = self.tree()
        workflows, outside = root / "workflows", root / "outside"
        workflows.mkdir()
        outside.mkdir()
        self.write(workflows, "covered.md", COVERED_INLINE)
        self.write(outside, "uncovered.md", "# English-only mode\n")
        self.link_directory(outside, workflows / "linked")
        self.assertEqual(["covered.md", "linked/uncovered.md"],
                         sorted(self.rel(lint.find_markdown_files_recursive(str(workflows)), workflows)))
        self.assertEqual(["uncovered.md"], [Path(f).name for f in lint.find_violations(str(workflows))])

    def test_a_link_cycle_is_entered_once(self):
        root = self.tree()
        self.write(root, "a.md", COVERED_INLINE)
        self.link_directory(root, root / "loop")
        found = lint.find_markdown_files_recursive(str(root))
        self.assertEqual(1, len([f for f in found if f.endswith("a.md")]))

    def test_unlistable_directory_raises(self):
        with self.assertRaises(OSError):
            lint.find_markdown_files_recursive(str(self.base / "absent"))


class InlineDirective(Case):
    def test_rejects_a_bare_field_mention_and_accepts_an_actionable_directive(self):
        self.assertFalse(lint.has_response_language_coverage("response_language\n"))
        self.assertTrue(lint.has_response_language_coverage("Apply response_language to all user-facing prose, narration included.\n"))

    def test_pre_weak_wording_is_no_longer_coverage_and_naming_narration_is(self):
        weak = ("**If `response_language` is set:** All user-facing questions, prompts, and "
                "explanations in this workflow MUST be presented in `{response_language}`. "
                "Technical terms, code, file paths, and subagent prompts stay in English — "
                "only user-facing output is translated.\n")
        self.assertFalse(lint.has_response_language_coverage(weak))
        for token in ("narration between tool calls", "narration", "output between tool calls"):
            with self.subTest(token=token):
                self.assertTrue(lint.has_response_language_coverage(
                    f"Apply response_language to all user-facing output — {token} included.\n"))
        for weak_token in ("status updates", "progress notes", "findings"):
            with self.subTest(weak_token=weak_token):
                self.assertFalse(lint.has_response_language_coverage(
                    f"Apply response_language to all user-facing output — {weak_token} included.\n"))
        self.assertFalse(lint.has_response_language_coverage("Narration between tool calls is emitted here.\n"))
        self.assertFalse(lint.has_response_language_coverage(
            "Apply response_language to all user-facing prose.\nNarration is emitted between tool calls.\n"))

    def test_crlf_lines_are_split(self):
        self.assertTrue(lint.carries_inline_directive("intro\r\nApply response_language to prose, narration included.\r\n"))

    def test_ascii_word_boundaries(self):
        self.assertFalse(lint.carries_inline_directive("Apply response_languages to prose, narration included."))
        self.assertFalse(lint.carries_inline_directive("Apply response_language to prose, narrationx included."))
        self.assertTrue(lint.carries_inline_directive("APPLY RESPONSE_LANGUAGE TO PROSE, NARRATION INCLUDED."))

    def test_narration_class_regex_accepts_exactly_the_two_forms(self):
        self.assertTrue(lint.NARRATION_CLASS_RE.search("the Narration"))
        self.assertTrue(lint.NARRATION_CLASS_RE.search("Between Tool Calls"))
        self.assertIsNone(lint.NARRATION_CLASS_RE.search("status updates, progress notes, findings"))


class DirectiveImport(Case):
    def test_imported_directive_reference(self):
        for line in (IMPORT_LINE, "@$HOME/.claude/engineer/references/response-language-directive.md",
                     "  " + IMPORT_LINE + "  "):
            with self.subTest(line=line):
                self.assertEqual("references/response-language-directive.md", lint.imported_directive_reference(line + "\n"))
                self.assertTrue(lint.imports_directive_reference(line + "\n"))
        self.assertEqual("references/execute-phase-response-language.md", lint.imported_directive_reference(
            "@~/.claude/engineer/references/execute-phase-response-language.md\n"))

    def test_import_is_found_on_any_line_including_crlf(self):
        self.assertIsNotNone(lint.imported_directive_reference("# Title\r\n" + IMPORT_LINE + "\r\nbody\r\n"))

    def test_a_mention_of_the_path_is_not_an_import(self):
        for line in ("- #2529: added the shared references/response-language-directive.md reference.",
                     "The directive lives in `engineer/references/response-language-directive.md`.",
                     "references/response-language-directive.md is deprecated; do not import it.",
                     "Add `" + IMPORT_LINE + "` to new workflows."):
            with self.subTest(line=line):
                self.assertIsNone(lint.imported_directive_reference(line + "\n"))
                self.assertFalse(lint.has_response_language_coverage(line + "\n"))

    def test_import_coverage_needs_the_reference_to_carry_a_directive(self):
        root, workflows = self.reference_fixture(STRONG_REFERENCE)
        self.assertTrue(lint.has_response_language_coverage(IMPORT_LINE + "\n", str(root)))
        weak_root, _ = self.reference_fixture(WEAK_REFERENCE)
        self.assertFalse(lint.has_response_language_coverage(IMPORT_LINE + "\n", str(weak_root)))
        missing_root, _ = self.reference_fixture(None)
        self.assertFalse(lint.has_response_language_coverage(IMPORT_LINE + "\n", str(missing_root)))


class ViolationsAndPins(Case):
    def test_reports_an_uncovered_nested_workflow_while_accepting_both_coverage_forms(self):
        root = self.fixture()
        ref_root = self.reference_root_for(root)
        self.assertEqual(["nested/mere-field-mention.md", "nested/modes/uncovered.md"],
                         self.rel(lint.find_violations(str(root), str(ref_root)), root))

    def test_every_shared_inline_pin_is_one_exact_canonical_line(self):
        root = self.tree()
        for relative in lint.EXACT_INLINE_DIRECTIVE_WORKFLOWS:
            self.write(root, relative, lint.INLINE_RESPONSE_LANGUAGE_DIRECTIVE + "\n")
        # A set that is empty would make every assertion below vacuous.
        self.assertGreater(len(lint.EXACT_INLINE_DIRECTIVE_WORKFLOWS), 0)
        self.assertEqual([], lint.find_violations(str(root)))
        drifted = root / "discuss-phase" / "modes" / "all.md"
        drifted.write_text("Apply response_language to all user-facing prose; preserve code and paths.\n", encoding="utf-8")
        self.assertEqual([str(drifted)], lint.find_violations(str(root)))

    def test_the_canonical_line_itself_satisfies_the_inline_predicate(self):
        self.assertTrue(lint.carries_inline_directive(lint.INLINE_RESPONSE_LANGUAGE_DIRECTIVE))

    def test_a_pinned_workflow_that_converts_to_the_shared_reference_is_not_a_violation(self):
        pinned = sorted(p for p in lint.EXACT_INLINE_DIRECTIVE_WORKFLOWS if "/" in p)[0]
        converted, workflows = self.reference_fixture(STRONG_REFERENCE)
        self.write(workflows, pinned, IMPORT_LINE + "\n")
        self.assertEqual([], lint.find_violations(str(workflows), str(converted)))

        reworded, workflows = self.reference_fixture(STRONG_REFERENCE)
        self.write(workflows, pinned, "Apply response_language to user-facing prose, narration included.\n")
        self.assertEqual([pinned], self.rel(lint.find_violations(str(workflows), str(reworded)), workflows))

        weakened, workflows = self.reference_fixture(WEAK_REFERENCE)
        self.write(workflows, pinned, IMPORT_LINE + "\n")
        self.assertEqual(sorted([pinned, "takes-the-reference.md"]),
                         sorted(self.rel(lint.find_violations(str(workflows), str(weakened)), workflows)))

    def test_an_imported_reference_that_no_longer_carries_a_directive_uncovers_its_importers(self):
        strong, workflows = self.reference_fixture(STRONG_REFERENCE)
        self.assertEqual([], lint.find_violations(str(workflows), str(strong)))
        self.assertEqual([], lint.find_broken_directive_references(lint.find_markdown_files_recursive(str(workflows)), str(strong)))
        weak, workflows = self.reference_fixture(WEAK_REFERENCE)
        self.assertEqual(["takes-the-reference.md"], [Path(f).name for f in lint.find_violations(str(workflows), str(weak))])
        self.assertEqual(["references/response-language-directive.md"],
                         lint.find_broken_directive_references(lint.find_markdown_files_recursive(str(workflows)), str(weak)))
        missing, workflows = self.reference_fixture(None)
        self.assertEqual(["takes-the-reference.md"], [Path(f).name for f in lint.find_violations(str(workflows), str(missing))])

    def test_a_reference_nobody_imports_is_never_reported_broken(self):
        root = self.tree()
        self.write(root, "a.md", COVERED_INLINE)
        self.assertEqual([], lint.find_broken_directive_references(lint.find_markdown_files_recursive(str(root)), str(self.tree())))

    def test_reference_verdict_is_not_stale_after_a_rewrite(self):
        ref_root = self.tree()
        target = self.write(ref_root, "references/response-language-directive.md", WEAK_REFERENCE)
        self.assertFalse(lint.reference_carries_directive("references/response-language-directive.md", str(ref_root)))
        target.write_text(STRONG_REFERENCE + "padding so size differs\n", encoding="utf-8")
        self.assertTrue(lint.reference_carries_directive("references/response-language-directive.md", str(ref_root)))
        target.unlink()
        self.assertFalse(lint.reference_carries_directive("references/response-language-directive.md", str(ref_root)))


class Fragments(Case):
    def test_a_fragment_inherits_coverage_from_the_parent_that_names_it(self):
        for kind in ("steps", "modes", "templates", "detail"):
            with self.subTest(kind=kind):
                root = self.fragment_fixture(kind=kind)
                ref_root = self.reference_root_for(root)
                self.assertTrue(lint.inherits_parent_coverage(str(root), f"autonomous/{kind}/converge-banner.md", str(ref_root)))
                self.assertEqual([], lint.find_violations(str(root), str(ref_root)))

    def test_inheritance_is_refused_when_the_parent_is_uncovered_or_does_not_name_the_fragment(self):
        ref_root = self.reference_root_for(None)
        for kind in ("steps", "detail"):
            with self.subTest(kind=kind):
                uncovered = self.fragment_fixture(parent_covered=False, kind=kind)
                self.assertEqual(["autonomous.md", f"autonomous/{kind}/converge-banner.md"],
                                 self.rel(lint.find_violations(str(uncovered), str(ref_root)), uncovered))
                unreferenced = self.fragment_fixture(parent_names_fragment=False, kind=kind)
                self.assertEqual([f"autonomous/{kind}/converge-banner.md"],
                                 self.rel(lint.find_violations(str(unreferenced), str(ref_root)), unreferenced))

    def test_a_detail_file_with_its_own_directive_is_accepted_independently_of_the_parent(self):
        root = self.fragment_fixture(parent_covered=False, kind="detail", name="converge-detail.md")
        self.write(root, "autonomous/detail/converge-detail.md",
                   "Apply response_language to all user-facing prose, narration between tool calls included.\n")
        self.assertEqual(["autonomous.md"], self.rel(lint.find_violations(str(root), str(self.reference_root_for(root))), root))

    def test_inheritance_reaches_fragment_directories_only(self):
        root = self.fragment_fixture()
        ref_root = str(self.reference_root_for(root))
        self.assertFalse(lint.inherits_parent_coverage(str(root), "autonomous.md", ref_root))
        self.assertFalse(lint.inherits_parent_coverage(str(root), "autonomous/steps/nested/converge-banner.md", ref_root))
        self.assertFalse(lint.inherits_parent_coverage(str(root), "autonomous/references/converge-banner.md", ref_root))

    def test_a_fragment_without_a_parent_file_does_not_inherit(self):
        root = self.tree()
        self.write(root, "orphan/steps/x.md", "text\n")
        self.assertFalse(lint.inherits_parent_coverage(str(root), "orphan/steps/x.md"))

    def test_a_fragment_mentioned_but_never_dispatched_does_not_inherit(self):
        root = self.tree()
        self.write(root, "autonomous.md", IMPORT_LINE + "\n- #1671: the banner prose moved to `engineer/workflows/autonomous/steps/converge-banner.md`.\n")
        self.write(root, "autonomous/steps/converge-banner.md", "Display: `Planning: convergence enabled`\n")
        ref_root = str(self.reference_root_for(root))
        self.assertFalse(lint.inherits_parent_coverage(str(root), "autonomous/steps/converge-banner.md", ref_root))
        self.assertEqual(["autonomous/steps/converge-banner.md"], self.rel(lint.find_violations(str(root), ref_root), root))

    def test_dispatch_requires_a_read_execute_context_not_a_bare_mention(self):
        dispatches = [
            "If `section_manifest` is `null`: read and execute `engineer/workflows/a/steps/b.md`. Otherwise skip.",
            "Read and execute `engineer/workflows/a/steps/b.md`.",
            "Read+execute `engineer/workflows/a/steps/b.md` (defines the helpers).",
            "Read `engineer/workflows/a/steps/b.md` if planning freezes on Windows.",
            "**Executor routing.** Per plan, run `engineer/workflows/a/steps/b.md` to set `EXECUTOR_TYPE`.",
            '**"none":** Read and execute `a/steps/b.md`.',
        ]
        for line in dispatches:
            with self.subTest(line=line):
                self.assertTrue(lint.names_fragment_as_entry_point(line + "\n", "a/steps/b.md"))
        mentions = [
            "- #1234: extracted the wave logic into `engineer/workflows/a/steps/b.md`.",
            "The prose below used to live in `engineer/workflows/a/steps/b.md`.",
            "`engineer/workflows/a/steps/b.md` is deprecated and no longer dispatched.",
            "Read and execute the step below.\nSee `engineer/workflows/a/steps/b.md`.",
            "Read the roadmap first, then decide whether any of this still applies to `engineer/workflows/a/steps/b.md`.",
            "Read and execute `vendor/a/steps/b.md`.",
        ]
        for line in mentions:
            with self.subTest(line=line):
                self.assertFalse(lint.names_fragment_as_entry_point(line + "\n", "a/steps/b.md"))

    def test_verb_window_is_forty_characters(self):
        near = "read " + "x" * 30 + " `a/steps/b.md`"
        far = "read " + "x" * 60 + " `a/steps/b.md`"
        self.assertTrue(lint.names_fragment_as_entry_point(near, "a/steps/b.md"))
        self.assertFalse(lint.names_fragment_as_entry_point(far, "a/steps/b.md"))


class Run(Case):
    def test_reports_a_failure_code_and_each_violation(self):
        root = self.fixture()
        io = Recorder()
        code = lint.run(str(root), io, str(self.reference_root_for(root)))
        self.assertEqual(1, code)
        self.assertEqual([], io.logs)
        self.assertRegex(io.errors[0], r"2 workflow\(s\) have no response-language coverage")
        self.assertIn("nested/mere-field-mention.md", io.errors[0])
        self.assertIn("nested/modes/uncovered.md", io.errors[0])
        self.assertNotIn("covered-inline.md", io.errors[0])

    def test_returns_success_and_emits_the_covered_workflow_count(self):
        root = self.tree()
        self.write(root, "covered.md", COVERED_INLINE)
        io = Recorder()
        self.assertEqual(0, lint.run(str(root), io))
        self.assertEqual([], io.errors)
        self.assertEqual(["lint-response-language-coverage: OK (1 workflows covered)"], io.logs)

    def test_fails_instead_of_passing_vacuously_when_discovery_finds_no_workflow(self):
        root = self.tree()
        self.write(root, "not-a-workflow/notes.txt", "not Markdown")
        io = Recorder()
        self.assertEqual(1, lint.run(str(root), io))
        self.assertEqual([], io.logs)
        self.assertRegex(io.errors[0], r"no workflow files found")

    def test_fails_closed_on_an_unreadable_workflow_directory(self):
        root = self.tree()
        self.write(root, "file-not-dir.md", "Apply response_language to all prose.\n")
        io = Recorder()
        self.assertEqual(1, lint.run(str(root / "does-not-exist"), io))
        self.assertRegex(io.errors[0], r"cannot read the workflow directory")
        self.assertIn("ENOENT", io.errors[0])
        self.assertEqual(1, lint.run(str(root / "file-not-dir.md"), io))
        self.assertRegex(io.errors[1], r"cannot read the workflow directory")
        self.assertRegex(io.errors[1], r"ENOTDIR|ENOENT")
        self.assertEqual([], io.logs)

    def test_a_weakened_reference_is_one_systemic_failure_not_one_per_importer(self):
        weak, workflows = self.reference_fixture(WEAK_REFERENCE)
        io = Recorder()
        self.assertEqual(1, lint.run(str(workflows), io, str(weak)))
        self.assertEqual([], io.logs)
        self.assertRegex(io.errors[0], r"shared directive reference\(s\) no longer carry an actionable directive")
        self.assertIn("references/response-language-directive.md", io.errors[0])
        self.assertNotIn("workflow(s) have no response-language coverage", io.errors[0])

    def test_default_console_writes_log_to_stdout_and_errors_to_stderr(self):
        root = self.tree()
        self.write(root, "covered.md", COVERED_INLINE)
        completed = subprocess.run(
            [sys.executable, "-c",
             "import importlib.util,sys;"
             f"s=importlib.util.spec_from_file_location('l',r'{LIB / 'lint_response_language_coverage.py'}');"
             "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
             f"sys.exit(m.run(r'{root}'))"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("lint-response-language-coverage: OK (1 workflows covered)\n", completed.stdout.replace("\r\n", "\n"))
        self.assertEqual("", completed.stderr)


class MatcherProperties(unittest.TestCase):
    """The four-predicate matcher, with vocabulary written out independently of the module's regexes."""
    FIELD = "response_language"
    NARRATION = "between tool calls"
    ACTIONS = ["apply", "present", "render", "respond", "translate", "use", "write", "must", "should"]
    OUTPUTS = ["explanation", "explanations", "language", "output", "outputs", "prompt", "prompts", "prose",
               "question", "questions", "template", "templates", "user-facing"]
    FILLER = ["the", "and", "of", "in", "for", "each", "step", "file", "then", "this"]

    @staticmethod
    def cased(word, mode):
        if mode == "upper":
            return word.upper()
        if mode == "title":
            return " ".join(w[:1].upper() + w[1:] for w in word.split(" "))
        return word

    def parts(self, rng):
        return {"action": rng.choice(self.ACTIONS), "output": rng.choice(self.OUTPUTS),
                "order": rng.sample([0, 1, 2, 3], 4), "mode": rng.choice(["lower", "upper", "title"]),
                "gaps": [[rng.choice(self.FILLER) for _ in range(rng.randint(0, 4))] for _ in range(5)]}

    def signals(self, parts):
        return [self.FIELD, parts["action"], parts["output"], self.NARRATION]

    def build_line(self, parts, omit=-1):
        tokens, words = self.signals(parts), []
        for position, index in enumerate([i for i in parts["order"] if i != omit]):
            words.extend(parts["gaps"][position])
            words.append(self.cased(tokens[index], parts["mode"]))
        words.extend(parts["gaps"][4])
        return " ".join(words).strip()

    def test_one_line_with_all_four_signals_is_coverage_wherever_it_sits(self):
        rng = random.Random(2529)
        for run in range(200):
            parts = self.parts(rng)
            before = [rng.choice(self.FILLER) for _ in range(rng.randint(0, 4))]
            after = [rng.choice(self.FILLER) for _ in range(rng.randint(0, 4))]
            line = self.build_line(parts)
            with self.subTest(run=run, line=line):
                self.assertTrue(lint.carries_inline_directive("\n".join([*before, line, *after])))

    def test_dropping_any_one_signal_is_not_coverage(self):
        rng = random.Random(2530)
        for run in range(200):
            parts, omit = self.parts(rng), rng.randint(0, 3)
            line = self.build_line(parts, omit)
            with self.subTest(run=run, line=line):
                self.assertFalse(lint.carries_inline_directive(line))

    def test_the_four_signals_spread_across_lines_are_not_coverage(self):
        rng = random.Random(2531)
        runs = 0
        while runs < 200:
            parts = self.parts(rng)
            breaks = [rng.random() < 0.5 for _ in range(3)]
            if not any(breaks):
                continue
            runs += 1
            tokens = self.signals(parts)
            document = self.cased(tokens[parts["order"][0]], parts["mode"])
            for position, index in enumerate(parts["order"][1:]):
                document += ("\n" if breaks[position] else " ") + self.cased(tokens[index], parts["mode"])
            with self.subTest(document=document):
                self.assertFalse(lint.carries_inline_directive(document))


class RealRepository(unittest.TestCase):
    """The shipped catalog under engineer/workflows and engineer/references."""

    def test_pinned_paths_are_live_in_the_real_catalog(self):
        discovered = {str(Path(f).relative_to(lint.WORKFLOWS_DIR)).replace(os.sep, "/")
                      for f in lint.find_markdown_files_recursive(lint.WORKFLOWS_DIR)}
        self.assertGreater(len(discovered), 0)
        self.assertEqual([], sorted(p for p in lint.EXACT_INLINE_DIRECTIVE_WORKFLOWS if p not in discovered))

    def test_a_pinned_workflow_is_one_that_could_not_have_inherited_instead(self):
        redundant = sorted(p for p in lint.EXACT_INLINE_DIRECTIVE_WORKFLOWS if lint.inherits_parent_coverage(lint.WORKFLOWS_DIR, p))
        self.assertEqual([], redundant)

    def test_no_shipped_workflow_or_reference_carries_the_weak_directive_sentence(self):
        weak = "All user-facing questions, prompts, and explanations in this workflow MUST be presented in"
        workflows = lint.find_markdown_files_recursive(lint.WORKFLOWS_DIR)
        references = lint.find_markdown_files_recursive(os.path.join(lint.REFERENCE_ROOT, "references"))
        offenders = [f for f in [*workflows, *references] if weak in Path(f).read_bytes().decode("utf-8", errors="replace")]
        self.assertEqual([], offenders)
        self.assertGreater(len(workflows), 0, "the workflow catalog scan produced no files")
        self.assertGreater(len(references), 0, "the reference directory scan produced no files")

    def test_the_shared_directive_reference_carries_an_actionable_directive(self):
        shared = Path(lint.REFERENCE_ROOT) / "references" / "response-language-directive.md"
        self.assertTrue(shared.exists())
        self.assertTrue(lint.carries_inline_directive(shared.read_text(encoding="utf-8")))

    def test_the_verifier_dispatch_prompt_carries_the_directive_after_its_anchor(self):
        # Upstream also pins execute-phase-response-language.md; that reference does not exist in this repo.
        anchor = "Create VERIFICATION.md."
        directive = ("Use response_language {response_language} for all user-facing prose — narration between tool calls, "
                     "status updates, progress notes, and findings included; preserve code and paths.")
        prompt = Path(lint.WORKFLOWS_DIR) / "execute-phase" / "steps" / "verify-phase-goal.md"
        lines = prompt.read_text(encoding="utf-8").splitlines()
        at = lines.index(anchor)
        self.assertEqual(directive, lines[at + 1])

    @unittest.expectedFailure
    def test_every_real_workflow_is_covered(self):
        """The real catalog is not fully covered; this stays expected-failing until the content is repaired.

        Violations at the pinned base: engineer/workflows/execute-phase.md @-imports
        references/execute-phase-response-language.md, which does not exist in engineer/references/, so run()
        reports one systemic broken-reference failure; with that reference uncovered, find_violations lists
        WORKFLOW.md (no directive), execute-phase.md, and the execute-phase fragments completion-reconciliation,
        executor-isolation-dispatch, partial-wave, per-plan-executor-routing, per-plan-worktree-gate,
        post-merge-gate, protected-branch, ready-wave-gate and tdd-applicability-resolution (each inherits from
        the uncovered parent).
        """
        io = Recorder()
        self.assertEqual(0, lint.run(io=io), "\n".join(io.errors)[:600])

    def test_real_run_inspects_a_non_empty_catalog(self):
        self.assertGreater(len(lint.find_markdown_files_recursive(lint.WORKFLOWS_DIR)), 0)


class CommandLine(unittest.TestCase):
    def test_module_runs_from_engineer_bin_and_reports_the_real_failure(self):
        completed = subprocess.run([sys.executable, "-m", "lib.lint_response_language_coverage"], cwd=BIN,
                                   env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                                   capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(1, completed.returncode)
        self.assertIn("lint-response-language-coverage:", completed.stderr)
        self.assertEqual("", completed.stdout)

    def test_main_ignores_arguments_like_upstream(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(lint.main([]), lint.main(["--unknown"]))


if __name__ == "__main__":
    unittest.main()
