"""Offline contracts for real host observations; no timers or worker probes."""
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ".ai/references/parallel-status.md"
WORKFLOW = ".ai/workflows/execute-phase.md"
COORDINATOR = ".ai/agents/coordinator.md"
RULES = ".ai/RULES.md"
ENTRY = "AGENTS.md"
PATHS = (REFERENCE, WORKFLOW, COORDINATOR, RULES, ENTRY)
COLUMNS = ("Assignment / PLAN", "Worker id", "Role", "Resolved model", "Plan state",
           "Execute state", "Verify state", "Last observed progress", "Stall flag",
           "Blocker", "PR/MR")
HOOKS = ("discover_and_group_plans", "execute_waves", "integrate_wave", "run_checks")
LINK = "../references/parallel-status.md"

# Short semantic cues are scoped to the real heading/step, never pinned paragraphs.
DUTIES = {
    "Assignment table": {
        "states": ("queued", "running", "blocked", "complete", "pending", "passed", "failed", "unavailable"),
        "evidence": ("timestamp", "cited evidence", "start/end", "check evidence", "acceptance"),
    },
    "Lifecycle refreshes": {
        "refresh": ("grouping/dispatch", "changed rows", "join/handoff/final", "integration/check"),
        "actual intervals": ("one actual bounded", "wait call", "its return", "Never split"),
        "blocking host": ("blocking dispatch/join", "only the full dispatch", "intermediate observations unavailable"),
    },
    "Bounded stall decision": {
        "stall decision": ("second consecutive", "neither progress", "host state change",
                           "requires `stalled`", "coordinator", "decision", "both observation intervals"),
        "bounded choices": ("continue one", "status/handoff", "access/decision blocker", "external blocker"),
        "stop safety": ("never proves", "never grants", "wait timeout", "host confirmation",
                        "Do not automatically", "confirmed stopped/interrupted", "dirty work",
                        "continuation limits", "fresh independent verification"),
    },
}


def steps(text):
    return dict(re.findall(r'^<step name="([^"]+)">\n(.*?)^</step>', text, re.M | re.S))


def section(text, title):
    match = re.search(r"^## " + re.escape(title) + r"\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return " ".join(match.group(1).split()) if match else ""


def contract_errors(root):
    content = {name: (root / name).read_text(encoding="utf-8") for name in PATHS}
    reference = content[REFERENCE]
    errors = []
    headers = [tuple(c.strip() for c in line.strip("|").split("|"))
               for line in reference.splitlines() if line.startswith("| ")]
    if COLUMNS not in headers:
        errors.append("assignment columns")
    for heading, groups in DUTIES.items():
        body = section(reference, heading)
        for label, tokens in groups.items():
            if not all(token in body for token in tokens):
                errors.append(label)
    intro = " ".join(reference.split("## Assignment table", 1)[0].split())
    for label, tokens in {
        "waves": ("separate table", "actual dependency/file-overlap"),
        "join": ("every active write-capable worker", "before integration"),
    }.items():
        if not all(t in intro for t in tokens):
            errors.append(label)
    for name in HOOKS:
        if LINK not in steps(content[WORKFLOW]).get(name, ""):
            errors.append(name + ": hook")
    execution = re.search(r"<execution>(.*?)</execution>", content[COORDINATOR], re.S)
    if not execution or LINK not in execution.group(1):
        errors.append("coordinator hook")
    rules = section(content[RULES], "Orchestration and handoffs")
    if not all(t in rules for t in ("timeout", "host confirms", "stop before reassigning",
                                    "dirty work", "continuation", "Never automatically")):
        errors.append("canonical stop rule")
    recovery = section(content[RULES], "Interruption and recovery")
    if not all(t in recovery for t in ("host wait timeout", "does not establish exit",
                                       "Before inspecting dirty files", "reassigning",
                                       "host confirmation", "stopped", "continuation",
                                       "#orchestration-and-handoffs", "worker-handoff.md")):
        errors.append("recovery stop gate")
    if ".ai/RULES.md#orchestration-and-handoffs" not in content[ENTRY]:
        errors.append("entry stop link")
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

    def replace(self, root, name, old, new="Removed"):
        path = root / name
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def test_real_contract(self):
        self.assertEqual([], contract_errors(ROOT))

    def test_each_column(self):
        for field in COLUMNS:
            with self.subTest(field=field):
                root = self.fixture()
                self.replace(root, REFERENCE, "| " + field + " |")
                self.assertIn("assignment columns", contract_errors(root))

    def test_scoped_observation_and_safety_mutations(self):
        for heading, groups in DUTIES.items():
            for label, tokens in groups.items():
                for token in tokens:
                    with self.subTest(heading=heading, token=token):
                        root = self.fixture()
                        path = root / REFERENCE
                        text = path.read_text(encoding="utf-8")
                        start = text.index("## " + heading)
                        end = text.find("\n## ", start + 1)
                        body = text[start:end if end != -1 else len(text)]
                        # Match across line wrapping without pinning sentence wording.
                        pattern = r"\s+".join(re.escape(w) for w in token.split())
                        changed, count = re.subn(pattern, "Removed", body)
                        self.assertGreater(count, 0)
                        path.write_text(text.replace(body, changed, 1), encoding="utf-8")
                        self.assertIn(label, contract_errors(root))

    def test_each_lifecycle_hook(self):
        for name in HOOKS:
            with self.subTest(step=name):
                root = self.fixture()
                path = root / WORKFLOW
                text = path.read_text(encoding="utf-8")
                body = steps(text)[name]
                path.write_text(text.replace(body, body.replace(LINK, "missing.md"), 1), encoding="utf-8")
                self.assertIn(name + ": hook", contract_errors(root))
        root = self.fixture()
        self.replace(root, COORDINATOR, LINK)
        self.assertIn("coordinator hook", contract_errors(root))

    def test_stop_rule_and_entry_link(self):
        for name, token, expected in (
            (RULES, "stop before reassigning", "canonical stop rule"),
            (RULES, "Never automatically", "canonical stop rule"),
            (ENTRY, ".ai/RULES.md#orchestration-and-handoffs", "entry stop link"),
        ):
            with self.subTest(token=token):
                root = self.fixture()
                self.replace(root, name, token)
                self.assertIn(expected, contract_errors(root))

    def test_recovery_seam_requires_confirmation_before_inspection(self):
        for token in ("does not establish exit", "Before inspecting dirty files",
                      "host confirmation", "#orchestration-and-handoffs", "worker-handoff.md"):
            with self.subTest(token=token):
                root = self.fixture()
                path = root / RULES
                text = path.read_text(encoding="utf-8")
                start = text.index("## Interruption and recovery")
                end = text.index("\n## ", start + 1)
                body = text[start:end]
                pattern = r"\s+".join(re.escape(w) for w in token.split())
                changed, count = re.subn(pattern, "Removed", body)
                self.assertGreater(count, 0)
                path.write_text(text.replace(body, changed, 1), encoding="utf-8")
                self.assertIn("recovery stop gate", contract_errors(root))


if __name__ == "__main__":
    unittest.main()
