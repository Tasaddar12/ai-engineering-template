"""Claude orchestration guards: port of upstream tests/claude-orchestration.test.cjs."""
import importlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
LIB = SOURCE / "engineer" / "bin" / "lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package; `.ai/runtime/lib` also claims the name `lib`."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB / "__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib." + name)


orchestration = _load("claude_orchestration")
DOC = orchestration.read_text(orchestration.WORKFLOW_PATH)


class WaveHookSourceContract(unittest.TestCase):
    """Upstream section E: execute-phase.md renders execute:wave:pre before dispatch."""

    def test_invokes_loop_render_hooks_for_wave_pre(self):
        self.assertIn(orchestration.WAVE_PRE_HOOK, DOC)

    def test_wave_pre_hook_precedes_the_wave_agent_dispatch(self):
        hook, dispatch = orchestration.hook_precedes_dispatch(DOC)
        self.assertNotEqual(-1, hook, "execute:wave:pre render-hooks call site must exist")
        self.assertNotEqual(-1, dispatch, "the executor Agent() dispatch call site (step 3) must exist")
        self.assertLess(hook, dispatch, "it is a pre-wave hook")

    def test_frontmatter_declares_all_four_execute_points(self):
        self.assertIsNotNone(orchestration.frontmatter_points(DOC), "a points: line is required")
        self.assertEqual([], orchestration.missing_points(DOC))

    def test_wave_post_hook_is_still_rendered(self):
        self.assertIn(orchestration.WAVE_POST_HOOK, DOC)


class WorkflowSize(unittest.TestCase):
    """Upstream section H: execute-phase.md stays minimal and under the frozen byte ceiling."""

    def test_step_2_75_stays_minimal(self):
        body = orchestration.step_body(DOC)
        self.assertIsNotNone(body, "step 2.75 must exist and precede step 3")
        self.assertEqual([], orchestration.step_violations(body))

    def test_below_the_frozen_pre_phase_6_byte_ceiling(self):
        size = orchestration.lf_byte_count(orchestration.WORKFLOW_PATH)
        self.assertLess(size, orchestration.BYTE_CEILING, f"execute-phase.md must stay below {orchestration.BYTE_CEILING}; got {size}")

    def test_manifest_construction_doc_in_the_capability_fragment(self):
        self.skipTest("capabilities/claude-orchestration/docs/workflow-backend-dispatch.md absent in this repo")


class AbsentUpstreamSubjects(unittest.TestCase):
    """Each upstream describe block whose subject has no counterpart here is one skipped test."""

    def test_detect_workflow_backend_and_semver(self):
        self.skipTest("gsd-core/bin/lib/claude-orchestration.cjs detectWorkflowBackend/compareSemver absent in this repo")

    def test_emit_workflow_script(self):
        self.skipTest("emitWorkflowScript absent in this repo (single/multi-wave emission, overlap staging, injection hardening, "
                      "per-plan use_worktree, #3674 golden pins, #2686 model threading)")

    def test_capability_declaration_and_registry(self):
        self.skipTest("capabilities/claude-orchestration/capability.json, scripts/gen-capability-registry.cjs and the committed "
                      "capability registry absent in this repo (capability declaration, registry integration, section D)")

    def test_inline_fallback_parity(self):
        self.skipTest("Workflow-backend inline-fallback parity absent in this repo (no detectWorkflowBackend/emitWorkflowScript)")

    def test_resolve_wave_dispatch_seam_and_cli(self):
        self.skipTest("resolveWaveDispatch and the `claude-orchestration resolve-wave-dispatch` / emit-workflow CLI absent in "
                      "this repo (sections A, B, C, F, G)")

    def test_capability_doc_reflects_the_4740_removal(self):
        self.skipTest("docs/explanation/claude-orchestration-capability.md absent in this repo (section I)")

    def test_emitted_script_contract_2590_and_outcomes_3302(self):
        self.skipTest("emitted Workflow script contract (#2590), reachable backend flags and per-agent outcomes (#3302) "
                      "absent in this repo")

    def test_workflow_backend_dispatch_doc_bridge_3302(self):
        self.skipTest("workflow-backend-dispatch doc (C1-C6) absent in this repo")


class ModuleUnits(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)

    def test_lf_byte_count_counts_crlf_as_one_byte(self):
        path = self.dir / "a.md"
        path.write_bytes(b"a\r\nb\r\n")
        self.assertEqual(4, orchestration.lf_byte_count(path))

    def test_frontmatter_points_and_missing_points(self):
        text = "<!-- x\npoints: execute:pre, execute:wave:pre\n-->"
        self.assertEqual("execute:pre, execute:wave:pre", orchestration.frontmatter_points(text))
        self.assertEqual(["execute:wave:post", "execute:post"], orchestration.missing_points(text))
        self.assertEqual(list(orchestration.EXECUTE_POINTS), orchestration.missing_points("no header"))

    def test_hook_precedes_dispatch_reports_indexes(self):
        text = f"x {orchestration.WAVE_PRE_HOOK} y {orchestration.DISPATCH_ANCHOR}"
        hook, dispatch = orchestration.hook_precedes_dispatch(text)
        self.assertTrue(0 <= hook < dispatch)
        self.assertEqual((-1, -1), orchestration.hook_precedes_dispatch("nothing"))
        hook, dispatch = orchestration.hook_precedes_dispatch(f"{orchestration.DISPATCH_ANCHOR} {orchestration.WAVE_PRE_HOOK}")
        self.assertGreater(hook, dispatch)

    def test_step_body_slicing(self):
        text = f"head\n{orchestration.STEP_START}\nbody{orchestration.STEP_END}\ntail"
        self.assertEqual(f"{orchestration.STEP_START}\nbody", orchestration.step_body(text))
        self.assertIsNone(orchestration.step_body("head " + orchestration.STEP_START))
        self.assertIsNone(orchestration.step_body("nothing"))

    def test_step_violations_flag_missing_hook_and_worktree_detail(self):
        self.assertEqual([], orchestration.step_violations(orchestration.WAVE_PRE_HOOK))
        self.assertEqual(3, len(orchestration.step_violations("use_worktree USE_WORKTREES_FOR_PLAN")))


if __name__ == "__main__":
    unittest.main()
