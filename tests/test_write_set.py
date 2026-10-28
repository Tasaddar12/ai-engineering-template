"""Tests for engineer/bin/lib/write_set.py (port of upstream gsd-core src/write-set.cts)."""
from pathlib import Path
import random
import sys
import unittest

import importlib
import importlib.util

LIB = Path(__file__).resolve().parents[1]/"engineer"/"bin"/"lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package (`lib` collides with .ai/runtime/lib)."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = pkg
        spec.loader.exec_module(pkg)
    return importlib.import_module("engineer_bin_lib."+name)

write_set_complete = _load("write_set").write_set_complete


class WriteSetCompleteTests(unittest.TestCase):
    def test_every_surface_applied_is_true(self):
        self.assertIs(True, write_set_complete([
            {"surface": "checkbox", "applied": True},
            {"surface": "traceability", "applied": True},
        ]))

    def test_one_surface_not_applied_is_false(self):
        self.assertIs(False, write_set_complete([
            {"surface": "checkbox", "applied": True},
            {"surface": "traceability", "applied": False},
        ]))

    def test_no_surfaces_applied_is_false(self):
        self.assertIs(False, write_set_complete([
            {"surface": "checkbox", "applied": False},
            {"surface": "traceability", "applied": False},
        ]))

    def test_boundary_empty_write_set_is_never_complete(self):
        self.assertIs(False, write_set_complete([]))

    def test_boundary_single_outcome(self):
        self.assertIs(True, write_set_complete([{"surface": "checkbox", "applied": True}]))
        self.assertIs(False, write_set_complete([{"surface": "checkbox", "applied": False}]))

    def test_boundary_two_outcomes_both_true(self):
        self.assertIs(True, write_set_complete([
            {"surface": "checkbox", "applied": True},
            {"surface": "traceability", "applied": True},
        ]))

    def test_requirement_field_does_not_affect_the_verdict(self):
        self.assertIs(True, write_set_complete([
            {"surface": "checkbox", "applied": True, "requirement": "R-1"},
            {"surface": "checkbox", "applied": True, "requirement": "R-2"},
        ]))
        self.assertIs(False, write_set_complete([
            {"surface": "checkbox", "applied": True, "requirement": "R-1"},
            {"surface": "checkbox", "applied": False, "requirement": "R-2"},
        ]))

    def test_does_not_mutate_input(self):
        ws = [{"surface": "a", "applied": True}]
        write_set_complete(ws)
        self.assertEqual([{"surface": "a", "applied": True}], ws)

    def test_property_matches_nonempty_and_all_applied(self):
        rng = random.Random(2143)
        for _ in range(500):
            ws = [{"surface": "s" * rng.randint(1, 12), "applied": rng.random() < 0.7}
                  for _ in range(rng.randint(0, 8))]
            expected = len(ws) > 0 and all(o["applied"] for o in ws)
            self.assertEqual(expected, write_set_complete(ws), ws)


if __name__ == "__main__":
    unittest.main()
