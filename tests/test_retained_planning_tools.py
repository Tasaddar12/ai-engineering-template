"""End-to-end regressions for retained planning evidence and compatibility helpers."""
import datetime as dt
import json
from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class RetainedPlanningTools(RuntimeCase):
    def research_input(self, questions=None):
        return self.put("research.json", json.dumps({"ecosystem": "python", "config": {"context7": True, "websearch": True, "firecrawl": True},
                        "questions": questions or [{"text": "Versioned API", "kind": "docs", "version": "1.0"}]}))

    def test_research_cache_citations_freshness_and_reuse(self):
        source = self.research_input()
        planned = self.cli("research-plan", "--input", source)["items"][0]
        self.assertEqual("context7", planned["fetch"]["provider"])
        key = planned["key"]
        self.cli("research-store.put", key, "--content", "Actual documentation", status=2, raw=True)
        self.cli("research-store", "put", key, "--content", "Actual documentation", "--url", "https://docs.python.org/3/", "--provider", "official")
        self.assertTrue(self.cli("research-store.get", key)["hit"])
        self.assertEqual(1, self.cli("research-store.query", "--query", "documentation")["count"])
        reused = self.cli("research-plan", "--input", source)["items"][0]
        self.assertFalse(reused["cache"]["stale"])
        self.assertNotIn("fetch", reused)
        cache = self.root / ".planning/research-cache" / (key + ".json")
        entry = json.loads(cache.read_text())
        entry["recorded"] = (dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=8)).isoformat()
        cache.write_text(json.dumps(entry), encoding="utf-8")
        stale = self.cli("research-plan", "--input", source)["items"][0]
        self.assertTrue(stale["cache"]["stale"])
        self.assertIn("fetch", stale)
        entry["recorded"] = dt.datetime.now(dt.timezone.utc).isoformat()
        entry["sources"] = []
        cache.write_text(json.dumps(entry), encoding="utf-8")
        self.assertTrue(self.cli("research-plan", "--input", source)["items"][0]["cache"]["stale"])

    def test_research_routes_sources_and_rejects_invalid_input(self):
        source = self.research_input([{"text": "News", "kind": "web"}, {"text": "Read page", "kind": "scrape"}])
        items = self.cli("research-plan", source)["items"]
        self.assertEqual(["websearch", "firecrawl"], [item["fetch"]["provider"] for item in items])
        for age in ("-1", "nan", "infinity", "bad"):
            self.cli("research-plan", source, "--max-age-hours", age, status=2, raw=True)
        key = "a" * 64
        self.cli("research-store.put", key, "--content", "Citation", "--url", "missing.md", status=2, raw=True)
        citation = self.put("evidence.md", "Observed source")
        self.assertTrue(self.cli("research-store.put", key, "--content", "Citation", "--sources", citation)["stored"])
        source.write_text('{"questions":[{"text":"Unavailable"}]}', encoding="utf-8")
        self.assertIn("blocked", self.cli("research-plan", source)["items"][0])

    def test_confidence_is_provider_authority_with_bare_verified(self):
        self.assertEqual("HIGH", self.cli("classify-confidence", "--verified", "--provider", "official"))
        self.assertEqual("MEDIUM", self.cli("classify-confidence", "--provider", "official"))
        self.assertEqual("MEDIUM", self.cli("classify-confidence", "--provider", "unknown", "--verified"))
        self.assertEqual("LOW", self.cli("classify-confidence", "--provider", "unknown", "--verified=false"))

    def context_fixture(self):
        directory = Path(self.phase())
        self.put("src/api.py", "version = 1")
        context = directory / "01-CONTEXT.md"
        context.write_text('---\nsource_paths: [src/api.py]\n---\n# Decisions\nKeep API.\n', encoding="utf-8")
        plan = self.plan(directory)
        return context, plan

    def test_context_drift_warn_block_and_regenerated_artifact(self):
        context, plan = self.context_fixture()
        self.assertTrue(self.cli("verify.context-drift", "1", "--record")["recorded"])
        self.assertEqual([], self.cli("verify.context-drift", "1")["stale_artifacts"])
        self.put("src/api.py", "version = 2")
        drift = self.cli("verify.context-drift", "1")
        self.assertTrue(drift["source_changed"])
        self.assertEqual([plan.name], drift["stale_artifacts"])
        self.assertFalse(drift["block"])
        self.cli("config-set", "workflow.context_drift_action", "block")
        self.assertTrue(self.cli("verify.context-drift", "1")["block"])
        plan.write_text(plan.read_text() + "Regenerated.\n", encoding="utf-8")
        self.assertFalse(self.cli("verify.context-drift", "1")["block"])
        context.write_text(context.read_text() + "Updated premise.\n", encoding="utf-8")
        self.assertTrue(self.cli("verify.context-drift", "1")["context_changed"])
        self.cli("config-set", "workflow.context_drift_action", "ignore", status=2, raw=True)
        for mode in ("warn", "auto", "off"):
            self.cli("config-set", "workflow.context_guard_mode", mode)

    def test_context_drift_confines_declared_paths(self):
        self.context_fixture()
        result = self.cli("verify.context-drift", "1", "--paths", "../outside", "--record", status=69)
        self.assertFalse(result["available"])
        self.assertFalse(list(self.root.glob(".planning/phases/*/.context-freshness.json")))

    def test_quick_append_escapes_and_deduplicates_without_completing_record(self):
        self.init_records()
        quick = self.cli("quick.create", "Actual authority")
        self.cli("quick-tasks-append", "--task", "pipes | and backslash \\ plus\nline", "--quick-id", quick["quick_id"], "--slug", "actual-authority")
        replay = self.cli("quick-tasks-append", "--task", "replay", "--quick-id", quick["quick_id"], "--slug", "actual-authority")
        self.assertTrue(replay["duplicate"])
        self.assertEqual("pending", self.cli("quick.get", quick["quick_id"])["status"])
        state = (self.root / ".planning/STATE.md").read_text(encoding="utf-8")
        self.assertIn("pipes \\|", state)
        self.assertNotIn("replay", state)

    def test_quick_migration_preserves_escaped_source_and_is_idempotent(self):
        self.init_records()
        state = self.root / ".planning/STATE.md"
        with state.open("a", encoding="utf-8") as stream:
            stream.write("\n### Quick Tasks Completed (legacy)\n\n| Date | Task | Owner |\n| --- | --- | --- |\n| 2026-01-01 | Repair \\| parser | Sam |\n")
        before = state.read_bytes()
        self.assertEqual(1, self.cli("quick-tasks-migrate")["count"])
        self.assertEqual(0, self.cli("quick-tasks-migrate")["count"])
        task = self.cli("quick.list")["tasks"][0]
        self.assertIn("Repair | parser", task["description"])
        self.assertIn("Owner: Sam", task["description"])
        self.assertEqual(before, state.read_bytes())

    def test_roadmap_dependencies_union_plans_and_existing_dependencies(self):
        first = self.phase("First")
        second = self.cli("phase.add", "Second")["directory"]
        self.cli("phase.add", "Third")
        path = self.plan(second)
        path.write_text(path.read_text().replace("depends_on: []", 'depends_on: ["01-01"]'), encoding="utf-8")
        path.rename(path.with_name("02-01-PLAN.md"))
        self.cli("phase.edit", "2", "--depends-on", "Phase 3")
        result = self.cli("roadmap.annotate-dependencies", "2")
        self.assertEqual(["01", "03"], result["dependencies"])
        self.assertIn("Phase 01", self.cli("roadmap.get-phase", "2")["depends_on"])
        self.assertFalse(self.cli("roadmap.annotate-dependencies", "1")["updated"])
