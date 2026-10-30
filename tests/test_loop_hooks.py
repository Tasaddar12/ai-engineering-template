"""Closed retained hook rendering is data only, with current query names."""
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class LoopHooks(RuntimeCase):
    def test_ship_post_is_known_empty_without_synthesized_agents(self):
        before = self.git("status", "--porcelain")
        dotted = self.cli("loop.render-hooks", "ship:post")
        nested = self.cli("loop", "render-hooks", "ship:post", "--raw", raw=True)
        import json
        self.assertEqual(dotted, json.loads(nested))
        self.assertEqual([], dotted["activeHooks"])
        self.assertEqual([], dotted["activeCaps"])
        self.assertFalse(dotted["executes"])
        self.assertEqual(before, self.git("status", "--porcelain"))

    def test_config_conditions_metadata_and_supported_queries(self):
        plan = self.cli("loop.render-hooks", "plan:pre")
        research = next(item for item in plan["activeHooks"] if item["capId"] == "research")
        self.assertEqual({"agent": "phase-researcher"}, research["ref"])
        self.assertEqual("step", research["kind"])
        self.assertIn("RESEARCH", research["fragment"]["inline"])
        ui = next(item for item in plan["activeHooks"] if item["capId"] == "ui" and item["kind"] == "gate")
        self.assertEqual("check.ui-plan-gate", ui["check"]["query"])
        self.assertTrue(ui["blocking"])
        self.assertEqual("halt", ui["onError"])
        self.assertIn("approval", ui["condition"])
        self.cli("config-set", "workflow.research", "false")
        disabled = self.cli("loop.render-hooks", "plan:pre")
        self.assertNotIn("research", [item["capId"] for item in disabled["activeHooks"]])
        self.assertIn("research", [item["capId"] for item in disabled["inactiveHooks"]])
        self.assertFalse(self.cli("loop.render-hooks", "plan:pre", "--active-cap", "research"))
        verbs = set(self.cli("verbs")["verbs"])
        for event in self.cli("loop.events")["events"]:
            packet = self.cli("loop.render-hooks", event, "--after-fingerprint", "captured-sha")
            for item in packet["activeHooks"]:
                self.assertEqual("captured-sha", item["requiresCurrentVerification"])
                self.assertNotIn(item["capId"], ("broken-windows", "windows"))
                if "check" in item:
                    self.assertIn(item["check"]["query"], verbs)
                    self.assertEqual(["{phase}"], item["check"]["args"])
        catalog = self.cli("loop.list")
        self.assertTrue(catalog["closedRegistry"])
        self.assertNotIn("broken-windows", catalog["capabilities"])
        self.cli("loop.render-hooks", "invented:event", status=2, raw=True)
        self.cli("loop.execute", "ship:post", status=2, raw=True)
