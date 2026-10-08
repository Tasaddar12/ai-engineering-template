"""Guard the cross-file contracts for readiness-routed committed chunks."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ParallelContractTests(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def assertContains(self, text, expected):
        self.assertTrue(expected in text, f"missing contract text: {expected!r}")

    def test_commands_and_skill_mirrors_stay_identical(self):
        for name in ("execute-phase", "verify-work", "quick"):
            self.assertEqual(
                self.read(f".ai/commands/{name}.md"),
                self.read(f".agents/skills/{name}/SKILL.md"),
                f"{name} command and installed skill drifted",
            )

    def test_chunk_contract_keeps_separate_gate_receipts_and_final_checks(self):
        reference = self.read(".ai/references/parallel-pipeline.md")
        workflow = self.read(".ai/workflows/execute-phase.md")
        reviewer = self.read(".ai/agents/code-reviewer.md")
        for verb in ("pipeline.route --spec", "pipeline.register --spec", "pipeline.prepare",
                     "pipeline.run-checks", "pipeline.record-review", "pipeline.integrate",
                     "pipeline.status"):
            self.assertContains(reference + workflow, verb)
        for field in ('"owned_paths"', '"depends_on"', '"resources"', '"acceptance"',
                      '"argv"', '"timeout"', '"base_sha"', '"provenance"'):
            self.assertContains(reference, field)
        self.assertContains(reference, "separate detached reviewer and test snapshots")
        self.assertContains(reference, "--no-reuse")
        self.assertContains(reference, "verification.run-checks")
        self.assertContains(reference, "Before phase verification")
        self.assertContains(reference, "not a model tester or new agent")
        self.assertContains(reviewer, "schema-1 JSON report")
        self.assertContains(reviewer, '"base_sha"')
        self.assertContains(reviewer, '"status": "passed"')
        self.assertContains(reviewer, '"provenance"')

    def test_dependency_and_completion_rules_prevent_whole_wave_barriers(self):
        reference = self.read(".ai/references/parallel-pipeline.md")
        workflow = self.read(".ai/workflows/execute-phase.md")
        self.assertContains(reference, "returns `wait`")
        self.assertContains(reference, "dependency cycle is `blocked`")
        self.assertContains(reference, "ancestor of this chunk's base")
        self.assertContains(reference, "pipeline.integrate` records a revision the coordinator has already merged")
        self.assertContains(reference, "git merge --no-ff <registered-head-SHA>")
        self.assertContains(reference, "whole-plan")
        self.assertContains(reference, "`.planning/config.yaml`")
        self.assertContains(reference, "mode/content inventory")
        self.assertContains(reference, "fails closed")
        self.assertContains(workflow, "Do not wait for all phase tasks or an entire proposed wave")
        self.assertContains(workflow, "Wait only for a prerequisite")
        self.assertContains(workflow, "applicable chunk gates pass")

    def test_scout_packet_and_luna_authority_are_limited(self):
        dispatch = self.read(".ai/references/scout-dispatch.md")
        packet = self.read(".ai/templates/scout-packet.md")
        rules = self.read(".ai/RULES.md")
        for token in ("source-evidence/v1", "task_class", "source_revision", "inputs",
                      "scope", "acceptance", "provenance", "config", "outputs", "citation"):
            self.assertContains(packet, token)
        self.assertContains(packet, "reuse.cross_revision")
        self.assertContains(packet, "reuse.complete_scope")
        self.assertContains(dispatch, "satisfy a fixed count")
        self.assertContains(dispatch, "They do not implement")
        self.assertContains(dispatch, "correctness, security")
        self.assertContains(rules, "coordinator")


if __name__ == "__main__":
    unittest.main()
