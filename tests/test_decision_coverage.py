from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class DecisionChecks(RuntimeCase):
    def test_decisions_require_plan_and_verification_citations(self):
        directory = Path(self.phase())
        (directory/"01-CONTEXT.md").write_text("D-01: Keep behavior\nD-02: Handle limits\n", encoding="utf-8")
        self.plan(directory, "D-01 implemented")
        self.assertEqual(["D-02"], self.cli("check.decision-coverage-plan", "1", status=1)["uncovered"])
        self.plan(directory, "D-01 implemented; D-02 implemented")
        self.assertTrue(self.cli("check.decision-coverage-plan", "1")["passed"])
        (directory/"01-VERIFICATION.md").write_text("D-01 evidence\nD-02 evidence\n", encoding="utf-8")
        self.assertTrue(self.cli("check.decision-coverage-verify", "1")["passed"])
