from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class UiGate(RuntimeCase):
    def test_ui_phase_requires_approved_spec(self):
        directory = Path(self.phase("Frontend interface"))
        self.assertTrue(self.cli("check.ui-plan-gate", "1", status=1)["blocked"])
        spec = directory/"01-UI-SPEC.md"
        spec.write_text("---\nstatus: draft\n---\nLayout\n", encoding="utf-8")
        self.assertTrue(self.cli("check.ui-plan-gate", "1", status=1)["blocked"])
        self.cli("frontmatter.set", spec, "--field", "status", "--value", "approved")
        self.assertFalse(self.cli("check.ui-plan-gate", "1")["blocked"])

    def test_backend_phase_has_no_ui_gate(self):
        self.phase("Background queue")
        self.assertFalse(self.cli("check.ui-plan-gate", "1")["blocked"])
