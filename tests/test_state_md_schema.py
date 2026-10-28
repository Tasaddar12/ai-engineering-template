import importlib
import importlib.util
import sys
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "engineer/bin/lib"


def _load(name):
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB / "__init__.py", submodule_search_locations=[str(LIB)])
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = pkg
        spec.loader.exec_module(pkg)
    return importlib.import_module("engineer_bin_lib." + name)


schema = _load("state_md_schema")


class StateMdSchema(unittest.TestCase):
    def test_key_order_matches_upstream_literal_order(self):
        self.assertEqual(
            ["gsd_state_version", "milestone", "milestone_name", "current_phase", "current_phase_name",
             "current_plan", "status", "stopped_at", "paused_at", "last_updated", "last_activity",
             "last_activity_desc", "state_head", "progress", "progress.total_phases",
             "progress.completed_phases", "progress.total_plans", "progress.completed_plans",
             "progress.percent"],
            list(schema.STATE_FIELD_SCHEMA))

    def test_status_lifecycle_enum(self):
        self.assertEqual(
            ("unknown", "paused", "executing", "planning", "discussing", "verifying", "completed"),
            schema.STATUS_LIFECYCLE_ENUM)
        self.assertEqual(schema.STATUS_LIFECYCLE_ENUM, schema.STATE_FIELD_SCHEMA["status"]["enum"])

    def test_schema_is_frozen_at_every_level(self):
        with self.assertRaises(TypeError):
            schema.STATE_FIELD_SCHEMA["x"] = {}
        with self.assertRaises(TypeError):
            schema.STATE_FIELD_SCHEMA["status"]["type"] = "number"
        self.assertIsInstance(schema.STATE_FIELD_SCHEMA["status"]["bodySource"], tuple)

    def test_every_row_uses_closed_vocabularies(self):
        self.assertEqual([], schema.validate_state_field_schema())

    def test_validate_reports_bad_rows(self):
        bad = {"k": {"type": "string", "cardinality": "many", "source": "psychic", "preservation": "derive"}}
        problems = schema.validate_state_field_schema(bad)
        self.assertIn("k.source: 'psychic' is not one of ['body', 'disk', 'external', 'curated', 'free']", problems)
        self.assertIn("k: missing required field 'emitted'", problems)

    def test_status_row(self):
        row = schema.STATE_FIELD_SCHEMA["status"]
        self.assertEqual("non-sentinel-unknown", row["guard"])
        self.assertEqual("preserve-when-unchanged", row["preservation"])
        self.assertEqual("always", row["emitted"])
        self.assertEqual(("Status",), row["bodySource"])

    def test_last_activity_has_body_source_but_no_label(self):
        row = schema.STATE_FIELD_SCHEMA["last_activity"]
        self.assertEqual(("Last Activity", "Last activity"), row["bodySource"])
        self.assertNotIn("bodyLabel", row)
        self.assertEqual("derive", row["preservation"])

    def test_stopped_at_fallback_order(self):
        self.assertEqual(("Stopped At", "Stopped at"), schema.STATE_FIELD_SCHEMA["stopped_at"]["bodySource"])

    def test_current_plan_accepted_shapes_declared_not_predicate(self):
        self.assertEqual(("N", "N of M"), schema.STATE_FIELD_SCHEMA["current_plan"]["acceptedShapes"])
        self.assertNotIn("N/M", schema.STATE_FIELD_SCHEMA["current_plan"]["acceptedShapes"])

    def test_progress_ratchet_and_leaf_rows(self):
        self.assertEqual("progress-ratchet", schema.STATE_FIELD_SCHEMA["progress"]["mergeStrategy"])
        self.assertEqual("preserve-always", schema.STATE_FIELD_SCHEMA["progress"]["preservation"])
        for leaf in ("total_phases", "completed_phases", "total_plans", "completed_plans", "percent"):
            row = schema.STATE_FIELD_SCHEMA[f"progress.{leaf}"]
            self.assertEqual(("number", "disk", "derive"), (row["type"], row["source"], row["preservation"]))

    def test_external_milestone_rows(self):
        for key in ("milestone", "milestone_name"):
            row = schema.STATE_FIELD_SCHEMA[key]
            self.assertEqual(("external", "preserve-if-placeholder", "when-present"),
                             (row["source"], row["preservation"], row["emitted"]))

    def test_body_label_only_on_preserve_when_unchanged_rows(self):
        for key, row in schema.STATE_FIELD_SCHEMA.items():
            if "bodyLabel" in row:
                self.assertEqual("preserve-when-unchanged", row["preservation"], key)

    def test_vocabularies(self):
        self.assertEqual(("body", "disk", "external", "curated", "free"), schema.FIELD_SOURCES)
        self.assertEqual(("derive", "preserve-when-unchanged", "preserve-always", "preserve-if-placeholder"),
                         schema.FIELD_PRESERVATIONS)
        self.assertEqual(("non-sentinel-unknown",), schema.FIELD_GUARDS)
        self.assertEqual(("progress-ratchet",), schema.FIELD_MERGE_STRATEGIES)


if __name__ == "__main__":
    unittest.main()
