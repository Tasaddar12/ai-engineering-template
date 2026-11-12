"""Standards routing: index rows resolve to exact sections; plans pin IDs per task."""
import sys
import unittest
try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE

sys.path.insert(0, str(SOURCE/"engineer/bin"))
from lib import standards  # noqa: E402

TASK = """<tasks>
<task type="auto"><name>Add behavior</name><files>src/app.py</files>
<read_first>README.md</read_first><standards>{ids}</standards><action>Implement behavior</action>
<verify>python -m unittest discover</verify><done>Behavior is observable</done></task>
</tasks>
"""


class CatalogContract(unittest.TestCase):
    def test_every_index_row_resolves_to_existing_sections(self):
        self.assertEqual([], standards.validate_catalog())

    def test_catalog_covers_every_domain(self):
        domains = {rid.split(".", 1)[0] for rid in standards.catalog()}
        self.assertEqual({"python", "api", "architecture", "sql"}, domains)


class StandardsRead(RuntimeCase):
    def test_section_carries_preamble_and_enclosing_intro_only(self):
        result = self.cli("standards-read", "python.errors.chaining")
        text = result["text"]
        self.assertIn("### 3.1 ", text)
        self.assertIn("## 3. ", text)
        self.assertIn("**Applies to:**", text)
        self.assertNotIn("\n## 4. ", text)
        self.assertNotIn("\n## 1. ", text)
        self.assertEqual(len(text), result["chars"])

    def test_whole_rule_returns_the_complete_document(self):
        document = (SOURCE/"engineer/standards/python/async-gather.md").read_text(encoding="utf-8").rstrip()
        self.assertIn(document, self.cli("standards-read", "python.async.gather", "--raw", raw=True))

    def test_required_companions_are_included(self):
        self.assertIn("PRIME DIRECTIVE", self.cli("standards-read", "python.style.layout", "--raw", raw=True))
        boundaries = self.cli("standards-read", "python.structure.boundaries", "--raw", raw=True)
        self.assertIn("## 1.", boundaries)
        self.assertIn("## 9.", boundaries)

    def test_alternative_selector_stays_within_the_row_document(self):
        text = self.cli("standards-read", "python.style.layout@§6", "--raw", raw=True)
        self.assertIn("## 6.", text)
        self.assertNotIn("\n## 2. ", text)
        # Heading text may contain spaces and omit the section number.
        named = self.cli("standards-read", "python.errors.hierarchy@Exception chaining", "--raw", raw=True)
        self.assertIn("### 3.1 ", named)
        self.assertNotIn("\n## 1. ", named)

    def test_overlapping_ids_share_one_document_block(self):
        result = self.cli("standards-read", "python.errors.hierarchy", "python.errors.hierarchy,python.errors.chaining")
        self.assertEqual(1, len(result["documents"]))
        self.assertEqual(1, result["text"].count("**Applies to:**"))

    def test_unknown_id_and_missing_input_fail_closed(self):
        self.cli("standards-read", "python.nope", status=2, raw=True)
        self.cli("standards-read", "python.style.layout@§99", status=2, raw=True)
        self.cli("standards-read", status=2, raw=True)
        self.cli("standards-read", "python.errors.chaining", "--task", "1", status=2, raw=True)
        self.cli("standards-read", "--plan", "missing-PLAN.md", status=2, raw=True)
        # Selectors address sections, never the document title.
        self.cli("standards-read", "python.errors.hierarchy@Error Handling", status=2, raw=True)

    def test_heading_selector_may_contain_commas(self):
        text = self.cli("standards-read", "api.rest.collections@Filtering, Sorting", "--raw", raw=True)
        self.assertIn("Filtering", text)

    def test_list_filters_by_domain(self):
        everything = self.cli("standards-list")["count"]
        sql = self.cli("standards-list", "sql")
        self.assertEqual(len(standards.catalog()), everything)
        self.assertTrue(sql["standards"] and all(row["id"].startswith("sql.") for row in sql["standards"]))
        self.cli("standards-list", "cobol", status=2, raw=True)
        domains = [row["id"].split(".", 1)[0] for row in self.cli("standards-list")["standards"]]
        self.assertEqual(sorted(set(domains)), list(dict.fromkeys(domains)))


class PinnedStandards(RuntimeCase):
    def test_plan_tasks_pin_ids_that_downstream_agents_read(self):
        path = self.plan(self.phase(), TASK.format(ids="python.errors.chaining, python.async.gather"))
        self.assertTrue(self.cli("verify.plan-structure", path)["valid"])
        result = self.cli("standards-read", "--plan", path, "--task", "1")
        self.assertEqual(["python.errors.chaining", "python.async.gather"], result["ids"])

    def test_unknown_pinned_id_invalidates_the_plan(self):
        path = self.plan(self.phase(), TASK.format(ids="python.nope"))
        result = self.cli("verify.plan-structure", path, status=1)
        self.assertTrue(any("python.nope" in error for error in result["errors"]))

    def test_plan_without_pins_reports_a_distinct_failure(self):
        path = self.plan(self.phase())
        self.cli("standards-read", "--plan", path, status=3, raw=True)


if __name__ == "__main__":
    unittest.main()
