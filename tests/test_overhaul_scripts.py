"""Aggregate the overhaul tooling suites for the Phase 0 check command."""
import importlib.util
from pathlib import Path
import sys
import unittest

TOOL_DIR = Path(__file__).resolve().parents[1] / "scripts"


def load_tool(name):
    sys.path.insert(0, str(TOOL_DIR))
    try:
        spec = importlib.util.spec_from_file_location(f"overhaul_{name}", TOOL_DIR / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(TOOL_DIR))


def load_tests(loader, standard_tests, pattern):
    suite = unittest.TestSuite()
    for path in sorted(Path(__file__).parent.glob("test_overhaul_*.py")):
        if path.stem == "test_overhaul_scripts":
            continue
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))
    return suite
