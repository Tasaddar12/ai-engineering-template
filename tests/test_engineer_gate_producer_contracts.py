"""Canonical producer instructions checked against offline runtime contracts."""
import importlib.util
from pathlib import Path
import re
import shlex
import unittest

try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE


def text(path):
    return (SOURCE / path).read_text(encoding="utf-8")


class PlanProgressProducers(RuntimeCase):
    def prepare_roadmap(self):
        for number in range(1, 5):
            self.phase("Behavior " + str(number))
        self.cli("roadmap.set-plans", "4", "--plans", "04-01: First", "04-02: Second")

    def check_producer(self, path):
        self.prepare_roadmap()
        call = next(line.strip() for line in text(path).splitlines()
                    if line.strip().startswith("engineer_run query roadmap.update-plan-progress "))
        values = {"PHASE_NUMBER": "4", "PHASE": "04", "PLAN": "02", "plan_id": "04-02"}
        call = re.sub(r"\$\{(\w+)\}", lambda match: values[match[1]], call)
        arguments = shlex.split(call)[2:]
        result = self.cli(*arguments)
        self.assertEqual("04-02", result["plan"])
        self.assertEqual(["roadmap.update-plan-progress", "04-02"], arguments,
                         "The runtime consumes one stable NN-MM identifier")
        roadmap = (self.root / ".planning/ROADMAP.md").read_text(encoding="utf-8")
        self.assertRegex(roadmap, r"(?m)^- \[x\] 04-02\b")
        self.assertRegex(roadmap, r"(?m)^- \[ \] 04-01\b")


    def test_executor_progress_call_checks_its_plan(self):
        self.check_producer("agents/executor.md")




class ExecutionReferences(unittest.TestCase):
    def test_planner_and_template_execution_contexts_resolve_for_both_hosts(self):
        spec = importlib.util.spec_from_file_location("_gate_contract_installer", SOURCE / "bin/install_support.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        for path in ("agents/planner.md", "engineer/templates/phase-prompt.md"):
            contexts = re.findall(r"<execution_context>\n(.*?)</execution_context>", text(path), re.S)
            self.assertTrue(contexts, path)
            for context in contexts:
                with self.subTest(path=path, context=context):
                    references = re.findall(r"^@~/.claude/(\S+)", context, re.M)
                    self.assertTrue(references)
                    for reference in references:
                        self.assertTrue((SOURCE / reference).is_file(), reference)
                    self.assertIn("agents/executor.md", references)
                    for host in ("claude", "codex"):
                        namespace = Path("." + host)
                        adapted = installer.adapt(context.encode(), host, namespace, path, []).decode()
                        self.assertIn("@" + namespace.as_posix() + "/agents/executor.md", adapted)







if __name__ == "__main__":
    unittest.main()
