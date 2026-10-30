"""Tests for engineer/bin/lib/artifacts.py (port of upstream gsd-core src/artifacts.cts)."""
import importlib
import importlib.util
from pathlib import Path
import re
import sys
import unittest

LIB = Path(__file__).resolve().parents[1]/"engineer"/"bin"/"lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package (`lib` collides with .ai/runtime/lib)."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = pkg
        spec.loader.exec_module(pkg)
    return importlib.import_module("engineer_bin_lib."+name)


_m = _load("artifacts")
CANONICAL_EXACT = _m.CANONICAL_EXACT
CANONICAL_PATTERNS = _m.CANONICAL_PATTERNS
is_canonical_planning_file = _m.is_canonical_planning_file

EXPECTED_EXACT = {
    "PROJECT.md", "ROADMAP.md", "STATE.md", "REQUIREMENTS.md", "MILESTONES.md", "BACKLOG.md", "LEARNINGS.md",
    "THREADS.md", "config.json", "CLAUDE.md", "RETROSPECTIVE.md", "STATE-ARCHIVE.md",
    "milestone.lock", "state.json", "skill-manifest.json", "PATTERNS.md",
}


class CanonicalExactTests(unittest.TestCase):
    def test_is_a_frozen_set_with_exact_membership(self):
        self.assertIsInstance(CANONICAL_EXACT, frozenset)
        self.assertEqual(EXPECTED_EXACT, set(CANONICAL_EXACT))

    def test_contains_expected_files(self):
        for name in ("PROJECT.md", "ROADMAP.md", "STATE.md", "REQUIREMENTS.md", "MILESTONES.md", "BACKLOG.md",
                     "LEARNINGS.md", "THREADS.md", "config.json", "CLAUDE.md", "RETROSPECTIVE.md", "state.json"):
            self.assertIn(name, CANONICAL_EXACT)


class CanonicalPatternsTests(unittest.TestCase):
    def test_is_a_sequence_of_compiled_patterns(self):
        self.assertEqual(2, len(CANONICAL_PATTERNS))
        for pattern in CANONICAL_PATTERNS:
            self.assertIsInstance(pattern, re.Pattern)

    def test_matches_milestone_audit_docs(self):
        for name in ("v1.2.3-MILESTONE-AUDIT.md", "v1.2-MILESTONE-AUDIT.md"):
            self.assertTrue(any(p.search(name) for p in CANONICAL_PATTERNS), name)
        self.assertTrue(CANONICAL_PATTERNS[0].search("v1.2-milestone-audit.MD"))
        self.assertFalse(CANONICAL_PATTERNS[0].search("v1.2-MILESTONE-AUDIT.md.bak"))

    def test_matches_version_stamped_docs(self):
        self.assertTrue(any(p.search("v2.0.0-release-plan.md") for p in CANONICAL_PATTERNS))


class IsCanonicalPlanningFileTests(unittest.TestCase):
    def test_every_exact_name(self):
        for name in CANONICAL_EXACT:
            self.assertIs(True, is_canonical_planning_file(name), name)

    def test_specific_registry_entries(self):
        for name in ("STATE.md", "config.json", "state.json", "PATTERNS.md", "RETROSPECTIVE.md"):
            self.assertIs(True, is_canonical_planning_file(name))

    def test_unrecognized_files(self):
        for name in ("random-file.md", "", "MY-NOTES.md", "scratch.md", "random-output.md", "state.md"):
            self.assertIs(False, is_canonical_planning_file(name), name)

    def test_phase_level_artifacts_at_root_are_not_canonical(self):
        for name in ("01-CONTEXT.md", "01-01-PLAN.md"):
            self.assertIs(False, is_canonical_planning_file(name))

    def test_version_stamped_documents(self):
        for name in ("v1.50.0-MILESTONE-AUDIT.md", "v1.0-MILESTONE-AUDIT.md", "v2.3.1-MILESTONE-AUDIT.md",
                     "v2.0.0-plan.md", "v1.0-notes.md", "V1.0-notes.MD"):
            self.assertIs(True, is_canonical_planning_file(name), name)

    def test_version_stamp_requires_dot_digits_dash_and_md_suffix(self):
        for name in ("v1-plan.md", "v1.0plan.md", "v1.0-plan.txt", "v1.0-plan.md.bak", "xv1.0-plan.md", "v1.a-plan.md", ".md"):
            self.assertIs(False, is_canonical_planning_file(name), name)

    def test_javascript_dot_semantics_for_the_version_pattern(self):
        self.assertIs(True, is_canonical_planning_file("v1.0-.md"))
        self.assertIs(False, is_canonical_planning_file("v1.0-a\nb.md"))
        self.assertIs(False, is_canonical_planning_file("v1.0-a\u2028b.md"))
        self.assertIs(False, is_canonical_planning_file("v1.0-plan.md\n"))
        self.assertIs(False, is_canonical_planning_file("v\u0661.0-plan.md"))  # JS \d is ASCII-only


if __name__ == "__main__":
    unittest.main()
