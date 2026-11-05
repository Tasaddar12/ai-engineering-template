"""Canonical producer instructions checked against offline runtime contracts."""
import importlib.util
import json
from pathlib import Path
import re
import shlex
import unittest

try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE


WORKFLOW = "engineer/workflows/execute-phase.md"


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

    def test_wave_progress_call_checks_the_completed_plan(self):
        self.check_producer(WORKFLOW)

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

    def test_merge_guidance_matches_fail_closed_scope_packet(self):
        section = text(WORKFLOW).split("5.5. **Integrate the isolated wave:**", 1)[1].split("5.6.", 1)[0]
        self.assertNotIn("It never blocks a merge", section)
        self.assertNotIn("**advisory**", section)
        for required in ("preserved", "worker-scope-violation", "exact", "coordinator",
                         "worktree-recovery-policy.md", "worktree.create"):
            self.assertIn(required, section)


class ExactScopeRuntime(RuntimeCase):
    def test_unexpected_file_is_preserved_and_never_integrated(self):
        self.put(".gitignore", ".worktrees/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "ignore isolated workers")
        self.git("switch", "-c", "codex/integration")
        summary = ".planning/phases/04-behavior/04-02-SUMMARY.md"
        worker = self.cli("worktree.create", "04-02", "--phase", "4", "--files", "src/owned.py",
                          "--summary-path", summary)
        target = Path(worker["path"])
        for path, content in (("src/owned.py", "owned = True\n"), ("src/unexpected.py", "preserve = True\n"),
                              (summary, '---\nphase: "04"\nplan: "02"\nstatus: complete\n---\n')):
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
        self.git("-C", str(target), "add", "src/owned.py", "src/unexpected.py", summary)
        self.git("-C", str(target), "commit", "-m", "worker exceeded exact scope")
        revision = self.git("-C", str(target), "rev-parse", "HEAD")
        receipt = self.put(".git/host-terminal.json", json.dumps({
            "host": "codex", "source": "native-host", "status": "completed", "agent_id": "scope-worker",
            "branch": worker["branch"], "head": revision, "worktree_path": worker["path"], "summary_path": summary,
        }))
        self.cli("worktree.record-agent", "04-02", "--phase", "4", "--path", target,
                 "--branch", worker["branch"], "--base", worker["base"], "--files", "src/owned.py",
                 "--summary-path", summary, "--agent-id", "scope-worker", "--terminal-receipt", receipt)
        before = self.git("rev-parse", "HEAD")
        packet = json.loads(self.cli("worktree.merge-wave", "--phase", "4", status=1, raw=True))
        self.assertFalse(packet["wave_clean"])
        self.assertEqual([], packet["merged"])
        self.assertEqual("preserved", packet["preserved"][0]["status"])
        self.assertEqual("worker-scope-violation", packet["preserved"][0]["error"])
        self.assertEqual(before, self.git("rev-parse", "HEAD"))
        self.assertFalse((self.root / "src/unexpected.py").exists())
        self.assertEqual("preserve = True\n", (target / "src/unexpected.py").read_text(encoding="utf-8"))
        self.assertEqual(revision, self.git("-C", str(target), "rev-parse", "HEAD"))


if __name__ == "__main__":
    unittest.main()
