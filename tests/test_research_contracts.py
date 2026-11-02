"""Original research and measured estimate contracts through the real CLI."""
import json
import datetime as dt
from pathlib import Path
import tempfile
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class ResearchContracts(RuntimeCase):
    def test_documented_input_routes_natively_and_refreshes_stale_cache(self):
        questions = [
            {"text": "How does X work?", "kind": "docs", "library": "x", "version": "1.2.3"},
            {"text": "Best practices for Y?", "kind": "web"},
            {"text": "Read the API page", "kind": "scrape", "url": "https://example.com/api"},
        ]
        source = self.put("research-plan-input.json", json.dumps({"ecosystem": "npm", "questions": questions}))
        plan = self.cli("research-plan", "--input", source)
        self.assertFalse(plan["executesFetch"])
        self.assertEqual(["websearch", "websearch", "webfetch"], [item["fetch"]["provider"] for item in plan["items"]])
        self.assertTrue(all("blocked" not in item for item in plan["items"]))
        self.assertEqual("https://example.com/api", plan["items"][2]["fetch"]["url"])
        key = plan["items"][0]["key"]
        self.cli("research-store.put", key, "--content", "Digest", "--source", "curated",
                 "--provider", "official", "--confidence", "MEDIUM", "--kind", "docs")
        cache_path = self.root/".planning/research-cache"/(key+".json")
        entry = json.loads(cache_path.read_text())
        entry["recorded"] = (dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=8)).isoformat()
        cache_path.write_text(json.dumps(entry), encoding="utf-8")
        stale = self.cli("research-plan", source)["items"][0]
        self.assertTrue(stale["cache"]["stale"])
        self.assertEqual("websearch", stale["fetch"]["provider"])
        self.assertEqual([], stale["cache"]["entry"]["sources"])
        legacy = {"context7": True, "ref": True, "exa_search": True, "tavily_search": True, "firecrawl": True}
        source.write_text(json.dumps({"ecosystem": "npm", "config": legacy, "questions": questions}), encoding="utf-8")
        routed = self.cli("research-plan", source)["items"]
        self.assertEqual(["websearch", "websearch", "webfetch"], [item["fetch"]["provider"] for item in routed])

    def test_external_temp_input_and_full_original_cache_arguments(self):
        with tempfile.TemporaryDirectory() as external:
            path = Path(external)/"research-plan-input.json"
            content = json.dumps({"ecosystem": "npm", "config": {"brave_search": True},
                                  "questions": [{"text": "Library API", "kind": "web"}]})
            path.write_text(content, encoding="utf-8")
            item = self.cli("research-plan", "--input", path)["items"][0]
            key = item["key"]
            self.assertEqual("websearch", item["fetch"]["provider"])
            self.cli("research-store", "put", key, "--content", "Source digest", "--source", "curated",
                     "--provider", "official", "--confidence", "HIGH", "--kind", "docs")
            cached = self.cli("research-plan", "--input", path)["items"][0]
            self.assertNotIn("fetch", cached)
            self.assertEqual([], cached["cache"]["entry"]["sources"])
            self.assertEqual("not-provided", cached["cache"]["entry"]["citationStatus"])
            self.assertFalse(cached["cache"]["entry"]["claimJudgment"])
            self.assertEqual(content, path.read_text(encoding="utf-8"))
            self.assertTrue((self.root/".planning/research-cache"/(key+".json")).is_file())
            self.cli("research-store.put", key, "--content", "Bare", status=2, raw=True)
            self.cli("research-store.put", key, "--content", "Bad", "--source", "curated",
                     "--provider", "official", "--confidence", "HIGH", "--kind", "docs",
                     "--url", "https://", status=2, raw=True)
            path.write_text('{"questions": [false]}', encoding="utf-8")
            self.cli("research-plan", "--input", path, status=2, raw=True)

    def test_calibration_pairs_raw_plan_estimates_and_summary_actuals(self):
        directory = Path(self.phase())
        empty = self.cli("estimate-calibration")
        self.assertEqual((1, "low", 0), (empty["factor"], empty["confidence"], empty["sample_count"]))
        for index in range(1, 7):
            prefix = "01-"+str(index).zfill(2)
            self.put(str(directory.relative_to(self.root)/ (prefix+"-PLAN.md")),
                     '---\nestimate:\n  tokens: 900\n  raw_tokens: 100\n---\n')
            self.put(str(directory.relative_to(self.root)/ (prefix+"-SUMMARY.md")),
                     '---\nactuals:\n  tokens: 200\n---\n# Completed\n')
            data = self.cli("estimate-calibrate")
            self.assertEqual("low" if index < 3 else "med" if index < 6 else "high", data["confidence"])
            self.assertEqual(1 if index < 3 else 2, data["factor"])
        self.assertEqual(6, data["sample_count"])
        self.assertEqual(100, data["samples"][0]["predicted"])
        self.assertEqual(data, json.loads((self.root/".planning/estimation-calibration.json").read_text()))
        checked = self.cli("estimate-check", "--tokens", "70000", "--calibrated")
        self.assertEqual(140000, checked["projected_tokens"])
        self.assertFalse(checked["within_budget"])
        self.assertTrue(checked["advisory"])
        self.assertEqual(70000, self.cli("estimate-check", "--tokens", "70000")["projected_tokens"])
        for bad in ("nan", "inf", "-1"):
            self.cli("estimate-check", "--tokens", bad, status=2, raw=True)
