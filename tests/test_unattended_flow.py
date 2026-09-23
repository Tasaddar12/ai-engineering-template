"""The phase flow runs unattended from /execute-phase through /ship.

Each of these once stopped a real run and left the user to type the next
command: the orchestrator told to "dispatch nothing new" at the handoff limit,
a "/clear then /verify-work" hand-off, a question about resuming a partial
execution, and "re-run /ship when the checks settle". The procedures are prose
a model follows, so the guard is on the prose itself.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".ai" / "workflows"


def read(path):
    return path.read_text(encoding="utf-8")


def step(text, name):
    match = re.search(r'<step name="%s">(.*?)</step>' % re.escape(name), text, re.DOTALL)
    assert match, "missing step " + name
    return match.group(1)


class UnattendedFlow(unittest.TestCase):

    def test_no_phase_workflow_hands_the_user_a_command_to_continue(self):
        for name in ("execute-phase", "verify-work", "ship"):
            with self.subTest(workflow=name):
                text = read(WORKFLOWS / (name + ".md"))
                self.assertNotIn("`/clear` then", text)
                # The instruction form, not the rule forbidding it.
                self.assertNotRegex(text, r"(?i)re-run `/ship {")
                self.assertNotRegex(text, r"`/ship \{phase_number\}` again")

    def test_execute_phase_continues_into_verification(self):
        text = read(WORKFLOWS / "execute-phase.md")
        completion = step(text, "completion")
        self.assertIn("workflows/verify-work.md", completion)
        self.assertIn("immediately", completion)
        self.assertNotIn("Next Up", completion)

    def test_a_partial_execution_continues_without_asking(self):
        gate = step(read(WORKFLOWS / "execute-phase.md"), "safe_resume_gate")
        self.assertNotIn("AskUserQuestion", gate)
        self.assertIn("do not ask", gate)

    def test_verification_continues_into_shipping(self):
        ready = step(read(WORKFLOWS / "verify-work.md"), "present_ready")
        self.assertIn("workflows/ship.md", ready)
        self.assertNotIn("Next Up", ready)

    def test_shipping_waits_for_checks_itself(self):
        checks = step(read(WORKFLOWS / "ship.md"), "judge_checks")
        self.assertIn('pr.checks "${SESSION_BRANCH}" --wait', checks)
        self.assertIn("debugger", checks)

    def test_the_orchestrator_is_never_told_to_stop_at_the_limit(self):
        hook = read(ROOT / ".ai" / "hooks" / "context-handoff.sh")
        # The advisory an agent without identity receives -- the one the
        # orchestrator used to obey -- not the comments explaining its history.
        advisory = re.search(r'^unknown_stop="(.*?)"$', hook, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(advisory, "unknown_stop advisory not found")
        self.assertNotIn("dispatch nothing new", advisory.group(1))
        self.assertNotIn("recommend continuing", advisory.group(1))
        self.assertIn("does not apply to you", advisory.group(1))
        for name in ("execute-phase", "verify-work"):
            with self.subTest(workflow=name):
                self.assertIn("never stop because", read(WORKFLOWS / (name + ".md")))


if __name__ == "__main__":
    unittest.main()
