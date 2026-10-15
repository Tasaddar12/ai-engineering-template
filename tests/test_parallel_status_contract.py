"""Offline instruction contracts for actual wave observations and bounded stalls."""
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ".ai/references/parallel-status.md"
WORKFLOW = ".ai/workflows/execute-phase.md"
COORDINATOR = ".ai/agents/coordinator.md"
PATHS = (REFERENCE, WORKFLOW, COORDINATOR)
COLUMNS = ("Assignment / PLAN", "Worker id", "Role", "Resolved model", "Plan state",
           "Execute state", "Verify state", "Last observed progress", "Stall flag",
           "Blocker", "PR/MR")


def steps(text):
    return dict(re.findall(r'^<step name="([^"]+)">\n(.*?)^</step>', text, re.M | re.S))


def section(text, title):
    match = re.search(r"^## " + re.escape(title) + r"\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return " ".join(match.group(1).split()) if match else ""


def contract_errors(root):
    reference, workflow, coordinator = ((root / name).read_text(encoding="utf-8") for name in PATHS)
    errors = []
    table = section(reference, "Assignment table")
    if "| " + " | ".join(COLUMNS) + " |" not in table:
        errors.append("assignment columns")
    duties = {
        "assignment states": (table, ("`queued`", "`running`", "`blocked`", "`complete`",
                                      "`pending`", "`passed`", "`failed`", "`inherit`", "`unavailable`")),
        "progress evidence": (table, ("timestamp and cited evidence", "bounded host wait's start/end or duration",
                                      "integration revision and check evidence", "does not establish acceptance")),
        "refresh events": (section(reference, "Lifecycle refreshes"),
                           ("grouping/dispatch", "observed worker update", "bounded host wait return",
                            "join", "integration/check result", "handoff/final report", "observation interval")),
        "stalled decision": (section(reference, "Bounded stall decision"),
                             ("second consecutive bounded wait interval", "neither progress nor a meaningful host state change",
                              "requires `stalled` and a recorded coordinator decision", "both observation intervals",
                              "continue one observed wait", "request a concise status/handoff",
                              "concrete access/decision blocker", "declared external blocker")),
        "lifecycle safeguards": (section(reference, "Bounded stall decision"),
                                 ("Elapsed time alone never proves a hang, completion or failure",
                                  "never grants permission to terminate", "Do not automatically kill, restart, reassign active paths",
                                  "Only a confirmed stopped/interrupted worker", "completed commits and dirty work",
                                  "existing continuation limits", "fresh independent verification")),
    }
    for label, (body, required) in duties.items():
        if not all(phrase in body for phrase in required):
            errors.append(label)
    normalized = " ".join(reference.split())
    if "separate table for each actual dependency/file-overlap wave" not in normalized:
        errors.append("actual wave separation")
    if "wait for every active write-capable worker before integration or integrated checks" not in normalized:
        errors.append("join before integration")
    for name in ("discover_and_group_plans", "execute_waves", "integrate_wave", "run_checks"):
        if "../references/parallel-status.md" not in steps(workflow).get(name, ""):
            errors.append(name + ": lifecycle hook")
    execution = re.search(r"<execution>\n(.*?)</execution>", coordinator, re.S).group(1)
    if "../references/parallel-status.md" not in execution:
        errors.append("coordinator: lifecycle hook")
    return errors


class ParallelStatusContract(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for name in PATHS:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((ROOT / name).read_text(encoding="utf-8"), encoding="utf-8")
        return root

    def mutate(self, root, name, old):
        path = root / name
        text = path.read_text(encoding="utf-8")
        pattern = r"\s+".join(re.escape(word) for word in old.split())
        self.assertRegex(text, pattern)
        path.write_text(re.sub(pattern, "Removed", text, count=1), encoding="utf-8")

    def test_real_wave_contract(self):
        self.assertEqual([], contract_errors(ROOT))

    def test_each_assignment_column_is_required(self):
        for field in COLUMNS:
            with self.subTest(field=field):
                root = self.fixture()
                self.mutate(root, REFERENCE, "| " + field + " |")
                self.assertIn("assignment columns", contract_errors(root))

    def test_each_actual_step_requires_its_own_hook(self):
        for name in ("discover_and_group_plans", "execute_waves", "integrate_wave", "run_checks"):
            with self.subTest(step=name):
                root = self.fixture()
                path = root / WORKFLOW
                text = path.read_text(encoding="utf-8")
                body = steps(text)[name]
                path.write_text(text.replace(body, body.replace("../references/parallel-status.md", "missing.md"), 1), encoding="utf-8")
                self.assertIn(name + ": lifecycle hook", contract_errors(root))

    def test_coordinator_execution_hook_is_required(self):
        root = self.fixture()
        self.mutate(root, COORDINATOR, "../references/parallel-status.md")
        self.assertIn("coordinator: lifecycle hook", contract_errors(root))

    def test_evidence_refresh_and_safeguard_mutations(self):
        cases = (
            ("separate table for each actual dependency/file-overlap wave", "actual wave separation"),
            ("timestamp and cited evidence", "progress evidence"),
            ("integration revision and check evidence", "progress evidence"),
            ("handoff/final report", "refresh events"),
            ("requires `stalled` and a recorded coordinator decision", "stalled decision"),
            ("neither progress nor a meaningful host state change", "stalled decision"),
            ("request a concise status/handoff", "stalled decision"),
            ("Elapsed time alone never proves a hang, completion or failure", "lifecycle safeguards"),
            ("never grants permission to terminate", "lifecycle safeguards"),
            ("Do not automatically kill, restart, reassign active paths", "lifecycle safeguards"),
            ("Only a confirmed stopped/interrupted worker", "lifecycle safeguards"),
            ("wait for every active write-capable worker before integration or integrated checks", "join before integration"),
        )
        for phrase, error in cases:
            with self.subTest(phrase=phrase):
                root = self.fixture()
                self.mutate(root, REFERENCE, phrase)
                self.assertIn(error, contract_errors(root))


if __name__ == "__main__":
    unittest.main()
