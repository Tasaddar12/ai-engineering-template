"""Rerun only the two minimum-version errors without changing candidate tests."""
import json
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[5]
tree = root / '.worktrees/TASK-006-a1'
suite = unittest.defaultTestLoader.discover(str(tree / 'tests/unit/commands'), pattern='test_*.py')
def flatten(value):
    for item in value:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item
all_tests = list(flatten(suite))
selected = [t for t in all_tests if any(name in t.id() for name in (
    'test_inherited_pipe_descendant_cannot_block_timeout_or_cancellation_return',
    'test_detached_descendant_timeout_and_cancellation_never_overclaim_cleanup'))]
assert len(all_tests) == 22 and len(selected) == 2
print(json.dumps({'python': sys.version, 'candidate_tests': str(tree / 'tests/unit/commands'),
                  'discovered': len(all_tests), 'selected_ids': [t.id() for t in selected]}), flush=True)
result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(selected))
print(json.dumps({'tests_run': result.testsRun, 'errors': len(result.errors),
                  'failures': len(result.failures), 'skips': len(result.skipped),
                  'successful': result.wasSuccessful()}), flush=True)
raise SystemExit(0 if result.wasSuccessful() else 1)
