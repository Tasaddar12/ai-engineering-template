"""Public find-phase fields remain usable through the runtime CLI."""
from pathlib import Path

try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class PhaseLookupContract(RuntimeCase):
    def test_documented_fields_and_phase_name_selection(self):
        directory = self.phase("Runtime phase lookup")
        self.plan(directory)
        self.put(Path(directory)/"01-01-SUMMARY.md", "# Completed plan\n")

        result = self.cli("find-phase", "1")

        self.assertEqual({
            "found": True,
            "directory": directory,
            "phase_number": "01",
            "phase_name": "runtime-phase-lookup",
            "plans": ["01-01-PLAN.md"],
            "summaries": ["01-01-SUMMARY.md"],
        }, {field: result[field] for field in (
            "found", "directory", "phase_number", "phase_name", "plans", "summaries")})
        self.assertEqual("runtime-phase-lookup", result["name"])
        self.assertEqual("runtime-phase-lookup",
                         self.cli("find-phase", "1", "--pick", "phase_name", raw=True))
