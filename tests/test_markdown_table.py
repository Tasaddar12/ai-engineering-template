"""Tests for engineer/bin/lib/markdown_table.py (port of upstream gsd-core src/markdown-table.cts)."""
import importlib
import importlib.util
from pathlib import Path
import random
import re
import sys
import unittest

LIB = Path(__file__).resolve().parents[1]/"engineer"/"bin"/"lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package (`lib` collides with .ai/runtime/lib)."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = pkg
        spec.loader.exec_module(pkg)
    return importlib.import_module("engineer_bin_lib."+name)


_m = _load("markdown_table")
TABLE_SCHEMAS = _m.TABLE_SCHEMAS
QUICK_TASKS_SECTION_ABSENT = _m.QUICK_TASKS_SECTION_ABSENT
append_quick_task_row = _m.append_quick_task_row
delete_table_row = _m.delete_table_row
escape_cell = _m.escape_cell
find_table_by_schema = _m.find_table_by_schema
find_table_with_columns = _m.find_table_with_columns
insert_table_row = _m.insert_table_row
is_delimiter_row = _m.is_delimiter_row
match_table_schema = _m.match_table_schema
migrate_quick_tasks_table = _m.migrate_quick_tasks_table
parse_markdown_table = _m.parse_markdown_table
reset_quick_task_rows = _m.reset_quick_task_rows
split_table_row = _m.split_table_row
update_table_cell = _m.update_table_cell

BARE_LF = re.compile(r"(?<!\r)\n")


class ParseMarkdownTableTests(unittest.TestCase):
    def test_four_column_flat_table(self):
        src = "\n".join(["| Phase | Plans Complete | Status | Completed |", "| --- | --- | --- | --- |",
                         "| 1. Alpha | 2/2 | Complete | \u2705 |", "| 2. Beta | 1/2 | In Progress | |"])
        result = parse_markdown_table(src)
        self.assertTrue(result["ok"])
        self.assertEqual(["Phase", "Plans Complete", "Status", "Completed"], result["value"]["columns"])
        self.assertEqual(2, len(result["value"]["rows"]))
        self.assertEqual("1. Alpha", result["value"]["rows"][0]["Phase"])
        self.assertEqual("2/2", result["value"]["rows"][0]["Plans Complete"])
        self.assertEqual("In Progress", result["value"]["rows"][1]["Status"])
        self.assertEqual("", result["value"]["rows"][1]["Completed"])

    def test_five_column_milestone_grouped(self):
        src = "\n".join(["| Phase | Milestone | Plans Complete | Status | Completed |", "|---|---|---|---|---|",
                         "| 1. Alpha | v1.0 | 2/2 | Complete | \u2705 |", "| 2. Beta | v1.1 | 0/3 | Planned | |"])
        result = parse_markdown_table(src)
        self.assertEqual(["v1.0", "v1.1"], [r["Milestone"] for r in result["value"]["rows"]])

    def test_first_table_after_prose(self):
        src = "\n".join(["Some intro prose before the table.", "", "| Requirement | Phase | Status |", "| --- | --- | --- |", "| R1 | 1 | Done |"])
        result = parse_markdown_table(src)
        self.assertEqual(["Requirement", "Phase", "Status"], result["value"]["columns"])
        self.assertEqual("R1", result["value"]["rows"][0]["Requirement"])

    def test_table_stops_at_first_non_pipe_line(self):
        src = "| A | B |\n|---|---|\n| 1 | 2 |\nprose\n| 3 | 4 |\n"
        self.assertEqual(1, len(parse_markdown_table(src)["value"]["rows"]))

    def test_ragged_rows_boundary(self):
        header = "| Phase | Plans Complete | Status | Completed |"
        delimiter = "| --- | --- | --- | --- |"
        short = parse_markdown_table("\n".join([header, delimiter, "| 1. Alpha | 2/2 | Complete |"]))
        self.assertEqual({"ok": False, "reason": "row 1 has 3 cells, expected 4"}, short)
        exact = parse_markdown_table("\n".join([header, delimiter, "| 1. Alpha | 2/2 | Complete | \u2705 |"]))
        self.assertTrue(exact["ok"])
        self.assertEqual(1, len(exact["value"]["rows"]))
        long = parse_markdown_table("\n".join([header, delimiter, "| 1. Alpha | 2/2 | Complete | \u2705 | extra |"]))
        self.assertEqual({"ok": False, "reason": "row 1 has 5 cells, expected 4"}, long)

    def test_malformed_input(self):
        empty = {"ok": False, "reason": "empty or non-string input"}
        self.assertEqual(empty, parse_markdown_table(""))
        self.assertEqual(empty, parse_markdown_table("   \n  \n  "))
        self.assertEqual(empty, parse_markdown_table(42))
        self.assertEqual({"ok": False, "reason": "no table found"}, parse_markdown_table("# Heading\n\nJust some prose, no table here.\n"))
        self.assertEqual({"ok": False, "reason": "missing delimiter row"},
                         parse_markdown_table("| Phase | Status |\n| 1. Alpha | Complete |"))
        self.assertEqual({"ok": False, "reason": "missing delimiter row"}, parse_markdown_table("| Phase | Status |"))
        self.assertEqual({"ok": False, "reason": "delimiter/header column count mismatch"},
                         parse_markdown_table("| Phase | Plans Complete | Status |\n| --- | --- |\n| a | b | c |"))

    def test_crlf_input(self):
        result = parse_markdown_table("| A | B |\r\n|---|---|\r\n| 1 | 2 |\r\n")
        self.assertEqual({"A": "1", "B": "2"}, result["value"]["rows"][0])

    def test_round_trip_property(self):
        rng = random.Random(2143)
        alphabet = "abXY01 _-.:;/#"
        for _ in range(300):
            ncols = rng.randint(1, 4)
            columns = []
            while len(columns) < ncols:
                name = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 6))).strip()
                if name and name not in columns:
                    columns.append(name)
            rows = []
            for _ in range(rng.randint(0, 4)):
                rows.append(["".join(rng.choice(alphabet) for _ in range(rng.randint(1, 8))).strip() or "x" for _ in columns])
            lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
            lines += ["| " + " | ".join(r) + " |" for r in rows]
            result = parse_markdown_table("\n".join(lines))
            self.assertTrue(result["ok"], result)
            self.assertEqual(columns, result["value"]["columns"])
            for i, cells in enumerate(rows):
                for j, col in enumerate(columns):
                    self.assertEqual(cells[j], result["value"]["rows"][i][col])


class SplitRowAndDelimiterTests(unittest.TestCase):
    def test_split_table_row(self):
        self.assertEqual(["a", "b", "c"], split_table_row("| a | b | c |"))
        self.assertEqual(["a", "b"], split_table_row("a | b"))
        self.assertEqual(["a|b", "c"], split_table_row(r"| a\|b | c |"))
        self.assertEqual(["a\\b", "c"], split_table_row(r"| a\\b | c |"))
        self.assertEqual(["", ""], split_table_row("| | |"))
        self.assertEqual(["x"], split_table_row("  |  x  |  "))

    def test_is_delimiter_row(self):
        self.assertTrue(is_delimiter_row(["---", ":---", "---:", ":---:", " - - ", "-"]))
        self.assertFalse(is_delimiter_row(["---", "abc"]))
        self.assertFalse(is_delimiter_row(["::"]))
        self.assertFalse(is_delimiter_row([""]))
        self.assertTrue(is_delimiter_row([]))


class MatchTableSchemaTests(unittest.TestCase):
    def test_every_variant_resolves(self):
        for schema_id, variants in TABLE_SCHEMAS.items():
            for variant in variants:
                self.assertEqual({"id": schema_id, "label": variant["label"]}, match_table_schema(variant["columns"]))

    def test_unknown_header(self):
        self.assertIsNone(match_table_schema(["Foo", "Bar", "Baz"]))

    def test_order_and_count_must_match(self):
        self.assertIsNone(match_table_schema(["Status", "Phase", "Plans Complete", "Completed"]))
        self.assertIsNone(match_table_schema(["Phase", "Plans Complete", "Status"]))

    def test_registry_shape(self):
        self.assertEqual({"RoadmapProgress", "RequirementsTraceability", "QuickTasks", "Security"}, set(TABLE_SCHEMAS))
        self.assertEqual(["no-status", "with-status"], [v["label"] for v in TABLE_SCHEMAS["QuickTasks"]])
        self.assertEqual(["trust-boundaries", "threat-register", "accepted-risks", "audit-trail"],
                         [v["label"] for v in TABLE_SCHEMAS["Security"]])


NO_STATUS_STATE = "\n".join(["# STATE", "", "### Quick Tasks Completed", "", "| # | Description | Date | Commit | Directory |",
                             "|---|-------------|------|--------|-----------|", "| 1 | fix typo | 2026-01-01 | abc1234 | \u2014 |", "",
                             "### Blockers/Concerns", "None"])
WITH_STATUS_STATE = "\n".join(["# STATE", "", "### Quick Tasks Completed", "", "| # | Description | Date | Commit | Status | Directory |",
                               "|---|-------------|------|--------|--------|-----------|", "| 1 | fix typo | 2026-01-01 | abc1234 | Pass | \u2014 |", "",
                               "### Blockers/Concerns", "None"])


def fields(description, date="2026-07-13", commit="a574966", **extra):
    return {"description": description, "date": date, "commit": commit, **extra}


def head_section(content):
    return content.split("### Blockers/Concerns")[0]


class AppendQuickTaskRowTests(unittest.TestCase):
    def test_extra_table_is_untouched_and_appended_task_is_in_quick_table(self):
        for eol in ("\n", "\r\n"):
            suffix = eol.join(["", "", "| Note | Text |", "| --- | --- |", "| untouched | bytes |", ""])
            state = head_section(NO_STATUS_STATE).rstrip().replace("\n", eol) + suffix
            appended = append_quick_task_row(state, fields("new task"))
            self.assertTrue(appended["ok"])
            content = appended["value"]["content"]
            parsed = parse_markdown_table(content)
            self.assertTrue(parsed["ok"])
            self.assertEqual(["fix typo", "new task"], [row["Description"] for row in parsed["value"]["rows"]])
            self.assertTrue(content.endswith(suffix))
            reset = reset_quick_task_rows(content)
            self.assertTrue(reset["ok"])
            self.assertEqual(2, reset["value"]["cleared"])
            self.assertTrue(reset["value"]["content"].endswith(suffix))
            legacy = eol.join(["## Quick Tasks Completed", "", "| Task | Date |", "| --- | --- |", "| legacy | 2026-01-01 |"])+suffix
            migrated = migrate_quick_tasks_table(legacy)
            self.assertTrue(migrated["ok"])
            self.assertTrue(migrated["value"]["content"].endswith(suffix))

    def test_no_status_table(self):
        result = append_quick_task_row(NO_STATUS_STATE, fields("add missing import"))
        self.assertTrue(result["ok"])
        self.assertEqual("no-status", result["value"]["variant"])
        self.assertEqual("| 2 | add missing import | 2026-07-13 | a574966 | \u2014 |", result["value"]["row"])
        self.assertIn(result["value"]["row"], result["value"]["content"])
        self.assertEqual({"content", "row", "variant"}, set(result["value"]))

    def test_with_status_table(self):
        result = append_quick_task_row(WITH_STATUS_STATE, fields("bump version", commit="b6fc5f6", status="Needs Review"))
        self.assertEqual("with-status", result["value"]["variant"])
        self.assertEqual("| 2 | bump version | 2026-07-13 | b6fc5f6 | Needs Review | \u2014 |", result["value"]["row"])

    def test_status_defaults_to_dash(self):
        result = append_quick_task_row(WITH_STATUS_STATE, fields("x"))
        self.assertEqual("| 2 | x | 2026-07-13 | a574966 | \u2014 | \u2014 |", result["value"]["row"])

    def test_row_lands_after_last_table_line_and_keeps_surroundings(self):
        result = append_quick_task_row(NO_STATUS_STATE, fields("added"))
        expected = NO_STATUS_STATE.replace("| 1 | fix typo | 2026-01-01 | abc1234 | \u2014 |\n",
                                           "| 1 | fix typo | 2026-01-01 | abc1234 | \u2014 |\n| 2 | added | 2026-07-13 | a574966 | \u2014 |\n")
        self.assertEqual(expected, result["value"]["content"])

    def test_unknown_header_fails_loud(self):
        garbled = "\n".join(["# STATE", "", "### Quick Tasks Completed", "", "| Foo | Bar | Baz | Qux |", "|---|---|---|---|", "| 1 | 2 | 3 | 4 |"])
        result = append_quick_task_row(garbled, fields("x", commit="abc"))
        self.assertFalse(result["ok"])
        self.assertEqual("unrecognized Quick Tasks schema (columns: Foo | Bar | Baz | Qux)", result["reason"])

    def test_absent_section(self):
        result = append_quick_task_row("# STATE\n\n### Blockers/Concerns\nNone\n", fields("x"))
        self.assertEqual({"ok": False, "reason": QUICK_TASKS_SECTION_ABSENT}, result)
        self.assertEqual("no Quick Tasks Completed section", QUICK_TASKS_SECTION_ABSENT)

    def test_unparseable_section_reports_table_reason(self):
        result = append_quick_task_row("# STATE\n\n### Quick Tasks Completed\n\nnot a table\n", fields("x"))
        self.assertEqual({"ok": False, "reason": "quick-tasks table: no table found"}, result)

    def test_row_number_boundary(self):
        zero = "\n".join(["# STATE", "", "### Quick Tasks Completed", "", "| # | Description | Date | Commit | Directory |",
                          "|---|-------------|------|--------|-----------|"])
        self.assertTrue(append_quick_task_row(zero, fields("x"))["value"]["row"].startswith("| 1 |"))
        two = zero + "\n| 1 | first | 2026-01-01 | aaa1111 | \u2014 |\n| 2 | second | 2026-01-02 | bbb2222 | \u2014 |"
        self.assertTrue(append_quick_task_row(two, fields("x"))["value"]["row"].startswith("| 3 |"))

    def test_round_trips_through_parse(self):
        result = append_quick_task_row(NO_STATUS_STATE, fields("round trip check", commit="ccc3333"))
        reparsed = parse_markdown_table(head_section(result["value"]["content"]))
        self.assertTrue(reparsed["ok"])
        self.assertEqual(2, len(reparsed["value"]["rows"]))
        for row in reparsed["value"]["rows"]:
            self.assertEqual(len(reparsed["value"]["columns"]), len(row))

    def test_escaping_round_trips(self):
        for description, expected in (("fix a | b bug", "fix a | b bug"), ("fix C:\\path bug", "fix C:\\path bug"),
                                      ("a\\|b", "a\\|b"), ("line one\nline two", "line one line two")):
            result = append_quick_task_row(NO_STATUS_STATE, fields(description))
            self.assertTrue(result["ok"])
            self.assertNotIn("\n", result["value"]["row"])
            reparsed = parse_markdown_table(head_section(result["value"]["content"]))
            self.assertTrue(reparsed["ok"], description)
            self.assertEqual(expected, reparsed["value"]["rows"][1]["Description"])

    def test_crlf_is_preserved(self):
        crlf = NO_STATUS_STATE.replace("\n", "\r\n")
        result = append_quick_task_row(crlf, fields("crlf check"))
        section = head_section(result["value"]["content"])
        self.assertIsNone(BARE_LF.search(section))
        self.assertIn("\r\n", section)

    def test_quick_id_widening(self):
        empty = "\n".join(["# STATE", "", "### Quick Tasks Completed", "", "| # | Description | Date | Commit | Directory |",
                            "|---|-------------|------|--------|-----------|", "", "### Blockers/Concerns", "None"])
        directory = "[260811-gfl-arreglar-quick-tasks-append](./quick/260811-gfl-arreglar-quick-tasks-append/)"
        result = append_quick_task_row(empty, fields("Arreglar quick-tasks-append", "2026-08-11", "0d3c644",
                                                     quickId="260811-gfl", directory=directory))
        self.assertEqual(f"| 260811-gfl | Arreglar quick-tasks-append | 2026-08-11 | 0d3c644 | {directory} |", result["value"]["row"])
        plain = append_quick_task_row(empty, fields("no id supplied", "2026-08-11", "abc1234"))
        self.assertTrue(plain["value"]["row"].startswith("| 1 | no id supplied |"))
        self.assertTrue(plain["value"]["row"].endswith("| \u2014 |"))

    def test_none_optional_fields_fall_back(self):
        result = append_quick_task_row(WITH_STATUS_STATE, fields("x", status=None, directory=None, quickId=None))
        self.assertEqual("| 2 | x | 2026-07-13 | a574966 | \u2014 | \u2014 |", result["value"]["row"])


class QuickTasksHeadingToleranceTests(unittest.TestCase):
    SUFFIXED = NO_STATUS_STATE.replace("### Quick Tasks Completed", "### Quick Tasks Completed (v1.1+)")
    MULTI = "\n".join(["# STATE", "", "### Quick Tasks Completed (v1.1+)", "", "| # | Description | Date | Commit | Directory |",
                       "|---|-------------|------|--------|-----------|",
                       "| 250101-abc | first v1.1 task | 2025-01-01 | 0123abc | [dir](./quick/250101-abc/) |", "",
                       "### Quick Tasks Completed (v1.0)", "", "| # | Description | Date | Commit | Directory |",
                       "|---|-------------|------|--------|-----------|", "| 1 | legacy v1.0 task | 2024-06-01 | old1234 | \u2014 |"])
    LEGACY_FIRST = "\n".join(["# STATE", "", "### Quick Tasks Completed (v1.0)", "", "| Date | Slug | Scope | Artifacts |",
                              "|------|------|-------|-----------|", "| 2024-06-01 | old | full | \u2014 |", "",
                              "### Quick Tasks Completed (v1.1+)", "", "| # | Description | Date | Commit | Directory |",
                              "|---|-------------|------|--------|-----------|", "| 1 | fix typo | 2026-01-01 | abc1234 | \u2014 |"])

    def test_append_locates_suffixed_heading(self):
        result = append_quick_task_row(self.SUFFIXED, fields("probe", "2026-08-25", "deadbee"))
        self.assertTrue(result["ok"], result)
        self.assertIn("| 2 | probe | 2026-08-25 | deadbee | \u2014 |", result["value"]["content"])
        self.assertIn("### Quick Tasks Completed (v1.1+)", result["value"]["content"])

    def test_reset_locates_suffixed_heading(self):
        result = reset_quick_task_rows(self.SUFFIXED)
        self.assertTrue(result["ok"], result)
        self.assertEqual(1, result["value"]["cleared"])
        self.assertNotIn("fix typo", result["value"]["content"])
        self.assertIn("### Quick Tasks Completed (v1.1+)", result["value"]["content"])

    def test_word_boundary(self):
        not_quick = self.SUFFIXED.replace("### Quick Tasks Completed (v1.1+)", "### Quick Tasks Completedness (v1.1+)")
        self.assertEqual(QUICK_TASKS_SECTION_ABSENT, append_quick_task_row(not_quick, fields("x"))["reason"])
        accented = self.SUFFIXED.replace("Completed (v1.1+)", "Completed\u00e9 (v1.1+)")
        self.assertTrue(append_quick_task_row(accented, fields("x"))["ok"])  # JS \b is ASCII-only

    def test_heading_is_case_insensitive_and_any_level(self):
        state = NO_STATUS_STATE.replace("### Quick Tasks Completed", "## QUICK TASKS COMPLETED")
        self.assertTrue(append_quick_task_row(state, fields("x"))["ok"])

    def test_multiple_sections_append_to_canonical_one(self):
        result = append_quick_task_row(self.MULTI, fields("second v1.1 task", "2025-02-02", "0456def"))
        self.assertTrue(result["ok"], result)
        content = result["value"]["content"]
        v11 = content.index("### Quick Tasks Completed (v1.1+)")
        v10 = content.index("### Quick Tasks Completed (v1.0)")
        self.assertTrue(v11 < content.index("second v1.1 task") < v10)
        self.assertIn("| 1 | legacy v1.0 task | 2024-06-01 | old1234 | \u2014 |", content)

    def test_legacy_first_does_not_shadow_usable(self):
        result = append_quick_task_row(self.LEGACY_FIRST, fields("new task", "2026-08-25", "deadbee"))
        self.assertTrue(result["ok"], result)
        self.assertIn("| 2 | new task | 2026-08-25 | deadbee | \u2014 |", result["value"]["content"])

    def test_only_legacy_reports_the_real_problem(self):
        only_legacy = self.LEGACY_FIRST[:self.LEGACY_FIRST.index("### Quick Tasks Completed (v1.1+)")]
        result = append_quick_task_row(only_legacy, fields("x", "2026-08-25", "abc"))
        self.assertFalse(result["ok"])
        self.assertIn("unrecognized Quick Tasks schema", result["reason"])

    def test_later_deferred_items_table_is_not_the_splice_target(self):
        layout = "\n".join(["# STATE", "", "### Quick Tasks Completed (v1.1+)", "", "| # | Description | Date | Commit | Directory |",
                            "|---|-------------|------|--------|-----------|", "| 1 | fix typo | 2026-01-01 | abc1234 | \u2014 |", "",
                            "### Blockers/Concerns", "None", "", "## Deferred Items", "",
                            "| Category | Item | Status | Deferred At | Milestone |", "|----------|------|--------|-------------|-----------|",
                            "| scope | extra thing | deferred | 2026-01-02 | v1.1 |", ""])
        result = append_quick_task_row(layout, fields("probe", "2026-08-25", "deadbee"))
        content = result["value"]["content"]
        row = "| 2 | probe | 2026-08-25 | deadbee | \u2014 |"
        self.assertLess(content.index(row), content.index("## Deferred Items"))
        self.assertIn("| scope | extra thing | deferred | 2026-01-02 | v1.1 |\n", content)
        self.assertNotIn(row, content[content.index("## Deferred Items"):])

    def test_document_order_tie_break(self):
        both = self.MULTI.replace("| 1 | legacy v1.0 task", "| 99 | archived task")
        result = append_quick_task_row(both, fields("new task", "2026-08-25", "deadbee"))
        content = result["value"]["content"]
        v10 = content.index("### Quick Tasks Completed (v1.0)")
        # first section holds one row, so the new row is number 2 and lands before the v1.0 heading
        self.assertTrue(content.index("| 2 | new task | 2026-08-25 | deadbee | \u2014 |") < v10)


class ResetQuickTaskRowsTests(unittest.TestCase):
    TWO_ROWS = "\n".join(["# STATE", "", "### Quick Tasks Completed", "", "| # | Description | Date | Commit | Directory |",
                          "|---|-------------|------|--------|-----------|", "| 1 | fix typo | 2026-01-01 | abc1234 | \u2014 |",
                          "| 2 | bump version | 2026-01-02 | def5678 | \u2014 |", "", "### Blockers/Concerns", "None"])
    EMPTY = "\n".join(["# STATE", "", "### Quick Tasks Completed", "", "| # | Description | Date | Commit | Directory |",
                       "|---|-------------|------|--------|-----------|", "", "### Blockers/Concerns", "None"])

    def test_clears_rows_keeps_header_and_delimiter(self):
        result = reset_quick_task_rows(self.TWO_ROWS)
        self.assertTrue(result["ok"])
        self.assertEqual((2, "no-status"), (result["value"]["cleared"], result["value"]["variant"]))
        self.assertEqual(self.EMPTY, result["value"]["content"])
        self.assertEqual({"content", "cleared", "variant"}, set(result["value"]))

    def test_with_status_variant(self):
        result = reset_quick_task_rows(WITH_STATUS_STATE)
        self.assertEqual(("with-status", 1), (result["value"]["variant"], result["value"]["cleared"]))
        self.assertIn(WITH_STATUS_STATE.split("\n")[4], result["value"]["content"])

    def test_already_empty_is_byte_identical(self):
        result = reset_quick_task_rows(self.EMPTY)
        self.assertEqual(0, result["value"]["cleared"])
        self.assertEqual(self.EMPTY, result["value"]["content"])

    def test_unrecognized_schema_is_refused(self):
        garbled = "\n".join(["# STATE", "", "### Quick Tasks Completed", "", "| # | Thing | When |", "|---|-------|------|", "| 1 | fix typo | 2026-01-01 |"])
        result = reset_quick_task_rows(garbled)
        self.assertFalse(result["ok"])
        self.assertIn("unrecognized", result["reason"])

    def test_empty_and_non_string(self):
        self.assertEqual({"ok": False, "reason": "empty or non-string input"}, reset_quick_task_rows(""))
        self.assertEqual({"ok": False, "reason": "empty or non-string input"}, reset_quick_task_rows(42))

    def test_absent_section(self):
        self.assertEqual({"ok": False, "reason": QUICK_TASKS_SECTION_ABSENT},
                         reset_quick_task_rows("# STATE\n\n### Blockers/Concerns\nNone\n"))

    def test_crlf_is_preserved(self):
        result = reset_quick_task_rows(self.TWO_ROWS.replace("\n", "\r\n"))
        section = head_section(result["value"]["content"])
        self.assertIsNone(BARE_LF.search(section))
        self.assertIn("\r\n", section)

    def test_unrelated_preceding_table_untouched(self):
        doc = "\n".join(["# STATE", "", "## Roadmap Progress", "", "| Phase | Plans Complete | Status | Completed |", "| --- | --- | --- | --- |",
                          "| 1. Alpha | 2/2 | Complete | \u2705 |", "", "### Quick Tasks Completed", "",
                          "| # | Description | Date | Commit | Directory |", "|---|-------------|------|--------|-----------|",
                          "| 1 | fix typo | 2026-01-01 | abc1234 | \u2014 |", "", "### Blockers/Concerns", "None"])
        result = reset_quick_task_rows(doc)
        self.assertEqual(1, result["value"]["cleared"])
        self.assertIn("| 1. Alpha | 2/2 | Complete | \u2705 |", result["value"]["content"])
        self.assertNotIn("fix typo", result["value"]["content"])

    def test_row_count_property(self):
        for n in (0, 1, 2, 7, 50):
            rows = [f"| {i} | task {i} | 2026-01-01 | abc{i:04d} | \u2014 |" for i in range(1, n + 1)]
            state = "\n".join(["# STATE", "", "### Quick Tasks Completed", "", "| # | Description | Date | Commit | Directory |",
                               "|---|-------------|------|--------|-----------|", *rows, "", "### Blockers/Concerns", "None"])
            result = reset_quick_task_rows(state)
            self.assertTrue(result["ok"])
            self.assertEqual(n, result["value"]["cleared"])
            self.assertIn(state.split("\n")[4], result["value"]["content"])


class MigrateQuickTasksTableTests(unittest.TestCase):
    def legacy(self, eol="\n"):
        return eol.join(["# State", "", "## Quick Tasks Completed", "", "| Date | Slug | Scope | Artifacts |",
                         "|------|------|-------|-----------|", "| 2026-04-17 | 260417-abc | bootstrap | roles/x |",
                         "| 2026-05-02 | 260502-def | cli | quick/y |"]) + eol

    def test_migrates_legacy_schema(self):
        r = migrate_quick_tasks_table(self.legacy())
        self.assertTrue(r["ok"], r)
        self.assertTrue(r["value"]["migrated"])
        self.assertEqual(["Date", "Slug", "Scope", "Artifacts"], r["value"]["from"])
        self.assertEqual(2, r["value"]["rows"])
        content = r["value"]["content"]
        self.assertIn("| # | Description | Date | Commit | Status | Directory |", content)
        self.assertIn("| --- | ------------- | ------ | -------- | -------- | ----------- |", content)
        self.assertIn("| 1 | 260417-abc \u00b7 bootstrap | 2026-04-17 | \u2014 | \u2014 | roles/x |", content)
        self.assertIn("| 2 | 260502-def \u00b7 cli | 2026-05-02 | \u2014 | \u2014 | quick/y |", content)
        self.assertNotIn("| Date | Slug |", content)

    def test_unknown_columns_kept_in_description(self):
        state = "\n".join(["# State", "", "## Quick Tasks Completed", "", "| Date | Owner |", "|------|-------|", "| 2026-04-17 | sim |"])
        r = migrate_quick_tasks_table(state)
        self.assertIn("Owner: sim", r["value"]["content"])

    def test_alias_collision_is_lossless(self):
        state = "\n".join(["# State", "", "## Quick Tasks Completed", "", "| Date | When |", "|------|------|", "| 2026-04-17 | morning |"])
        r = migrate_quick_tasks_table(state)
        self.assertIn("| 1 | When: morning | 2026-04-17 | \u2014 | \u2014 | \u2014 |", r["value"]["content"])

    def test_canonical_table_is_noop(self):
        canonical = "\n".join(["# State", "", "## Quick Tasks Completed", "", "| # | Description | Date | Commit | Directory |",
                               "|---|-------------|------|--------|-----------|", "| 1 | existing | 2026-04-17 | deadbee | ./quick/a/ |"])
        r = migrate_quick_tasks_table(canonical)
        self.assertEqual({"content": canonical, "migrated": False}, r["value"])

    def test_absent_section_is_noop(self):
        r = migrate_quick_tasks_table("# State\n\n## Other\n")
        self.assertTrue(r["ok"])
        self.assertFalse(r["value"]["migrated"])

    def test_unparseable_table_fails_loud(self):
        r = migrate_quick_tasks_table("# State\n\n## Quick Tasks Completed\n\nnot a table\n")
        self.assertFalse(r["ok"])
        self.assertTrue(r["reason"])

    def test_crlf_preserved(self):
        r = migrate_quick_tasks_table(self.legacy("\r\n"))
        self.assertIn("\r\n", r["value"]["content"])
        self.assertIsNone(BARE_LF.search(r["value"]["content"].split("## Quick Tasks Completed")[1]))

    def test_second_table_in_section_is_preserved(self):
        state = "\n".join(["# State", "", "## Quick Tasks Completed", "", "| Date | Slug |", "|---|---|", "| 2026-01-01 | a |", "",
                           "| Note | Text |", "|---|---|", "| n | t |", ""])
        r = migrate_quick_tasks_table(state)
        self.assertIn("| Note | Text |", r["value"]["content"])
        self.assertIn("| n | t |", r["value"]["content"])

    def test_migrated_table_is_appendable(self):
        migrated = migrate_quick_tasks_table(self.legacy())
        appended = append_quick_task_row(migrated["value"]["content"], fields("probe", "2026-08-20", "deadbee", directory="./quick/probe/"))
        self.assertTrue(appended["ok"], appended)
        self.assertIn("probe", appended["value"]["row"])
        self.assertEqual("with-status", appended["value"]["variant"])


FOUR_COL = "\n".join(["| Phase | Plans Complete | Status | Completed |", "|-------|-----------------|--------|-----------|",
                      "| 1. Alpha | 2/2 | Complete    | 2026-01-01 |", "| 2. Beta  | 1/2 | In Progress |            |"])
FIVE_COL = "\n".join(["| Phase | Milestone | Plans Complete | Status | Completed |", "|-------|-----------|-----------------|--------|-----------|",
                      "| 1. Alpha | v1.0 | 2/2 | Complete    | 2026-01-01 |", "| 2. Beta  | v1.0 | 1/2 | In Progress |            |"])


def by_phase(name):
    return lambda row, index=0: row["Phase"].strip() == name


class FindTableTests(unittest.TestCase):
    def test_by_schema_anywhere_in_document(self):
        doc = "\n".join(["# Roadmap", "", "## Overview", "", "Some prose.", "", "## Milestone v1.0: Test", "",
                         "| Phase | Plans Complete | Status | Completed |", "| --- | --- | --- | --- |",
                         "| 1. Alpha | 2/2 | Complete | \u2705 |", "| 2. Beta | 1/2 | In Progress | |"])
        table = find_table_by_schema(doc, "RoadmapProgress")
        self.assertEqual(["Phase", "Plans Complete", "Status", "Completed"], table["columns"])
        self.assertEqual("1. Alpha", table["rows"][0]["Phase"])
        self.assertEqual(2, len(table["rows"]))

    def test_by_schema_not_first_table(self):
        doc = "\n".join(["# Roadmap", "", "| Symbol | Meaning |", "| --- | --- |", "| \u2705 | Done |", "",
                         "## Progress", "", "| Phase | Plans Complete | Status | Completed |", "| --- | --- | --- | --- |",
                         "| 1. Alpha | 2/2 | Complete | \u2705 |"])
        self.assertEqual(1, len(find_table_by_schema(doc, "RoadmapProgress")["rows"]))

    def test_by_schema_no_match_and_non_string(self):
        self.assertIsNone(find_table_by_schema("| Symbol | Meaning |\n| --- | --- |\n| a | b |", "RoadmapProgress"))
        self.assertIsNone(find_table_by_schema(None, "RoadmapProgress"))

    def test_by_schema_skips_unparseable_match_and_continues(self):
        doc = "\n".join(["| Phase | Plans Complete | Status | Completed |", "| a |", "", "| Phase | Plans Complete | Status | Completed |",
                         "| --- | --- | --- | --- |", "| 1 | 2 | 3 | 4 |"])
        self.assertEqual(1, len(find_table_by_schema(doc, "RoadmapProgress")["rows"]))

    def test_with_columns_order_independent_and_extras(self):
        doc = "\n".join(["## Progress", "", "| Status | Foo | Phase | Plans Complete | Completed |", "| --- | --- | --- | --- | --- |",
                         "| Complete | x | 1. Alpha | 2/2 | \u2705 |", "| In Progress | x | 2. Beta | 1/2 | |"])
        table = find_table_with_columns(doc, ["Phase", "Plans Complete", "Status", "Completed"])
        self.assertEqual(["Status", "Foo", "Phase", "Plans Complete", "Completed"], table["columns"])
        self.assertEqual("1. Alpha", table["rows"][0]["Phase"])
        self.assertEqual("1/2", table["rows"][1]["Plans Complete"])

    def test_with_columns_missing_and_non_string(self):
        doc = "| Phase | Owner | Completed |\n| --- | --- | --- |\n| 1. Alpha | jo | \u2705 |"
        self.assertIsNone(find_table_with_columns(doc, ["Phase", "Plans Complete", "Status", "Completed"]))
        self.assertIsNone(find_table_with_columns(None, ["Phase"]))


class UpdateTableCellTests(unittest.TestCase):
    def test_single_cell_update_leaves_other_bytes_identical(self):
        result = update_table_cell(FOUR_COL, by_phase("2. Beta"), "Status", " Complete    ")
        self.assertTrue(result["ok"])
        before = FOUR_COL.split("\n")
        after = result["value"].split("\n")
        self.assertEqual(before[:3], after[:3])
        self.assertEqual("| 2. Beta  | 1/2 | Complete    |            |", after[3])
        reparsed = parse_markdown_table(result["value"])
        self.assertEqual("Complete", reparsed["value"]["rows"][1]["Status"])

    def test_function_receives_current_trimmed_value(self):
        seen = []

        def transform(current):
            seen.append(current)
            return " NEW-DATE " if re.fullmatch(r"\d{4}-\d{2}-\d{2}", current) else current

        result = update_table_cell(FOUR_COL, by_phase("1. Alpha"), "Completed", transform)
        self.assertEqual(["2026-01-01"], seen)
        self.assertIn("NEW-DATE", result["value"])
        self.assertIn("| 2. Beta  | 1/2 | In Progress |            |", result["value"])

    def test_unknown_column_and_no_match_and_no_table(self):
        r = update_table_cell(FOUR_COL, lambda row, i: True, "Nonexistent", "x")
        self.assertEqual({"ok": False, "reason": "unknown column: Nonexistent"}, r)
        self.assertEqual({"ok": False, "reason": "no matching row"},
                         update_table_cell(FOUR_COL, lambda row, i: row["Phase"] == "does not exist", "Status", "x"))
        self.assertEqual({"ok": False, "reason": "no table found"},
                         update_table_cell("just some prose, no table here", lambda r, i: True, "Status", "x"))

    def test_malformed_table_keeps_its_specific_reason(self):
        self.assertEqual({"ok": False, "reason": "missing delimiter row"},
                         update_table_cell("| A | B |\n| 1 | 2 |", lambda r, i: True, "A", "x"))
        self.assertEqual({"ok": False, "reason": "missing delimiter row"},
                         update_table_cell("| A | B |", lambda r, i: True, "A", "x"))
        self.assertEqual({"ok": False, "reason": "delimiter/header column count mismatch"},
                         update_table_cell("| A | B |\n|---|\n| 1 | 2 |", lambda r, i: True, "A", "x"))

    def test_reaches_later_table_when_first_lacks_column(self):
        multi = "\n".join(["| Phase | Name | Requirements |", "|-------|------|--------------|", "| 1 | Portal Spec | 4 (PORTAL-01..04) |", "",
                           "| Requirement | Phase | Status |", "|-------------|-------|--------|", "| AUTHZ-02 | Phase 02.2 | Pending |"])
        by_req = lambda row, i: next(iter(row.values()), "").strip().lower() == "authz-02"  # noqa: E731
        result = update_table_cell(multi, by_req, "Status", " Complete ")
        self.assertTrue(result["ok"], result)
        self.assertIn("| Phase | Name | Requirements |", result["value"])
        self.assertIn("| 1 | Portal Spec | 4 (PORTAL-01..04) |", result["value"])
        self.assertRegex(result["value"], r"AUTHZ-02 \| Phase 02\.2 \| Complete")

    def test_five_column_table(self):
        result = update_table_cell(FIVE_COL, by_phase("1. Alpha"), "Plans Complete", " 2/2 ")
        lines = result["value"].split("\n")
        self.assertEqual(FIVE_COL.split("\n")[0], lines[0])
        self.assertEqual(FIVE_COL.split("\n")[3], lines[3])
        self.assertIn("v1.0", lines[2])
        self.assertIn("Complete    ", lines[2])

    def test_crlf_preserved(self):
        crlf = FOUR_COL.replace("\n", "\r\n")
        result = update_table_cell(crlf, by_phase("2. Beta"), "Status", " Complete    ")
        self.assertIsNone(BARE_LF.search(result["value"]))
        self.assertEqual("Complete", parse_markdown_table(result["value"])["value"]["rows"][1]["Status"])

    def test_match_receives_data_row_index(self):
        seen = []
        update_table_cell(FOUR_COL, lambda row, i: seen.append(i) or i == 1, "Status", " Complete    ")
        self.assertEqual([0, 1], seen)

    def test_ragged_siblings_do_not_block(self):
        extra = "\n".join(["| Phase | Plans Complete | Status | Completed |", "|-------|-----------------|--------|-----------|",
                            "| 1. Alpha | 2/2 | Complete    | 2026-01-01 |", "| 2. Beta  | 1/2 | In Progress |            | extra |"])
        result = update_table_cell(extra, by_phase("1. Alpha"), "Status", " Complete    ")
        self.assertTrue(result["ok"])
        self.assertIn("| 2. Beta  | 1/2 | In Progress |            | extra |", result["value"])
        missing = "\n".join(["| Phase | Plans Complete | Status | Completed |", "|-------|-----------------|--------|-----------|",
                             "| 2. Beta  | 1/2 | In Progress |", "| 1. Alpha | 2/2 | Complete    | 2026-01-01 |"])
        result = update_table_cell(missing, by_phase("1. Alpha"), "Status", " Complete    ")
        self.assertTrue(result["ok"])
        self.assertIn("| 2. Beta  | 1/2 | In Progress |", result["value"])

    def test_short_row_without_target_cell_is_skipped(self):
        short = "\n".join(["| Phase | Plans Complete | Status | Completed |", "|-------|-----------------|--------|-----------|",
                           "| 2. Beta  | 1/2 | In Progress |"])
        self.assertEqual({"ok": False, "reason": "no matching row"},
                         update_table_cell(short, by_phase("2. Beta"), "Completed", " 2026-01-01 "))

    def test_cell_count_boundary(self):
        header = ["| Phase | Plans Complete | Status | Completed |", "|-------|-----------------|--------|-----------|"]
        r = update_table_cell("\n".join(header + ["| 1. Alpha | 2/2 | Complete |"]), by_phase("1. Alpha"), "Status", " In Progress ")
        self.assertIn("| 1. Alpha | 2/2 | In Progress |", r["value"])
        r = update_table_cell("\n".join(header + ["| 1. Alpha | 2/2 | Complete | 2026-01-01 |"]), by_phase("1. Alpha"), "Completed", " 2026-02-02 ")
        self.assertIn("| 1. Alpha | 2/2 | Complete | 2026-02-02 |", r["value"])
        r = update_table_cell("\n".join(header + ["| 1. Alpha | 2/2 | Complete | 2026-01-01 | extra |"]), by_phase("1. Alpha"), "Plans Complete", " 3/3 ")
        self.assertIn("| 1. Alpha | 3/3 | Complete | 2026-01-01 | extra |", r["value"])

    def test_noop_probe_function(self):
        seen = []
        result = update_table_cell(FOUR_COL, by_phase("2. Beta"), "Status", lambda cur: seen.append(cur) or cur)
        self.assertEqual(["In Progress"], seen)
        self.assertEqual(FOUR_COL, result["value"])  # padding preserved: a true no-op

    def test_value_spliced_verbatim_and_escaped_cells_unescaped_for_match(self):
        table = "| Name | Note |\n|---|---|\n| a\\|b | x |"
        seen = []
        update_table_cell(table, lambda row, i: seen.append(row["Name"]) or True, "Note", " y ")
        self.assertEqual(["a|b"], seen)
        self.assertEqual("| Name | Note |\n|---|---|\n| a\\|b | y |", update_table_cell(table, lambda r, i: True, "Note", " y ")["value"])


class DeleteTableRowTests(unittest.TestCase):
    FOUR = FOUR_COL + "\n| 3. Gamma | 0/2 | Planned     |            |"

    def test_deletes_only_matched_row(self):
        result = delete_table_row(self.FOUR, by_phase("2. Beta"))
        before = self.FOUR.split("\n")
        after = result["value"].split("\n")
        self.assertEqual(len(before) - 1, len(after))
        self.assertEqual(before[:3] + [before[4]], after)
        self.assertEqual(2, len(parse_markdown_table(result["value"])["value"]["rows"]))

    def test_surrounding_prose_preserved(self):
        doc = "\n".join(["Some intro prose.", "", self.FOUR, "", "Some trailing prose."])
        result = delete_table_row(doc, by_phase("1. Alpha"))
        self.assertTrue(result["value"].startswith("Some intro prose.\n\n"))
        self.assertTrue(result["value"].endswith("\nSome trailing prose."))
        self.assertNotIn("1. Alpha", result["value"])

    def test_ragged_siblings_tolerated(self):
        extra = "\n".join(["| Phase | Plans Complete | Status | Completed |", "|-------|-----------------|--------|-----------|",
                            "| 1. Alpha | 2/2 | Complete    | 2026-01-01 |", "| 2. Beta  | 1/2 | In Progress |            | extra |"])
        result = delete_table_row(extra, by_phase("1. Alpha"))
        self.assertTrue(result["ok"])
        self.assertIn("| 2. Beta  | 1/2 | In Progress |            | extra |", result["value"])
        missing = "\n".join(["| Phase | Plans Complete | Status | Completed |", "|-------|-----------------|--------|-----------|",
                             "| 2. Beta  | 1/2 | In Progress |", "| 1. Alpha | 2/2 | Complete    | 2026-01-01 |"])
        result = delete_table_row(missing, by_phase("1. Alpha"))
        self.assertIn("| 2. Beta  | 1/2 | In Progress |", result["value"])
        self.assertNotIn("1. Alpha", result["value"])

    def test_failures(self):
        self.assertEqual({"ok": False, "reason": "no matching row"}, delete_table_row(self.FOUR, lambda r, i: False))
        self.assertEqual({"ok": False, "reason": "no table found"}, delete_table_row("just prose", lambda r, i: True))
        self.assertEqual({"ok": False, "reason": "missing delimiter row"}, delete_table_row("| A | B |\n| 1 | 2 |", lambda r, i: True))
        self.assertEqual({"ok": False, "reason": "missing delimiter row"}, delete_table_row("| A | B |", lambda r, i: True))
        self.assertEqual({"ok": False, "reason": "delimiter/header column count mismatch"},
                         delete_table_row("| A | B |\n|---|\n| 1 | 2 |", lambda r, i: True))

    def test_index_is_data_row_position(self):
        seen = []
        delete_table_row(self.FOUR, lambda row, i: seen.append(i) or i == 1)
        self.assertEqual([0, 1], seen)

    def test_crlf_preserved(self):
        result = delete_table_row(self.FOUR.replace("\n", "\r\n"), by_phase("2. Beta"))
        self.assertIsNone(BARE_LF.search(result["value"]))
        rows = parse_markdown_table(result["value"])["value"]["rows"]
        self.assertEqual(["1. Alpha", "3. Gamma"], [r["Phase"] for r in rows])

    def test_last_row_leaves_no_dangling_newline(self):
        result = delete_table_row(self.FOUR, by_phase("3. Gamma"))
        self.assertTrue(result["value"].endswith("In Progress |            |"))
        crlf = delete_table_row(self.FOUR.replace("\n", "\r\n"), by_phase("3. Gamma"))
        self.assertTrue(crlf["value"].endswith("In Progress |            |"))

    def test_compact_rows(self):
        compact = "\n".join(["|Phase|Plans Complete|Status|Completed|", "|---|---|---|---|", "|1|Foo|0/2|Planned|",
                             "|3|Foo|0/2|Planned|", "|4|Foo|0/2|Planned|"])
        result = delete_table_row(compact, lambda row, i: next(iter(row.values()), "").strip() == "3")
        self.assertTrue(result["ok"])
        self.assertNotIn("|3|Foo|0/2|Planned|", result["value"])
        self.assertIn("|1|Foo|0/2|Planned|", result["value"])
        self.assertIn("|4|Foo|0/2|Planned|", result["value"])


class EscapeCellAndInsertRowTests(unittest.TestCase):
    def test_escape_cell(self):
        self.assertEqual("a\\|b", escape_cell("a|b"))
        self.assertEqual("C:\\\\path", escape_cell("C:\\path"))
        self.assertEqual("a\\\\\\|b", escape_cell("a\\|b"))
        self.assertEqual("line one line two", escape_cell("line one\r\n\nline two"))
        self.assertEqual("x", escape_cell("  x \n"))
        self.assertEqual("5", escape_cell(5))
        for value in ("plain", "a|b", "C:\\x", "a\\|b", "back\\"):
            self.assertEqual(value, split_table_row("| " + escape_cell(value) + " |")[0])

    def test_insert_after_last_row_in_header_order(self):
        table = "| B | A |\n|---|---|\n| 1 | 2 |\n\nprose"
        result = insert_table_row(table, lambda col: {"A": "a-val"}.get(col))
        self.assertEqual("| B | A |\n|---|---|\n| 1 | 2 |\n| - | a-val |\n\nprose", result["value"])

    def test_insert_with_zero_data_rows_and_custom_fallback(self):
        result = insert_table_row("| A | B |\n|---|---|\n\nafter", lambda col: None, "n/a")
        self.assertEqual("| A | B |\n|---|---|\n| n/a | n/a |\n\nafter", result["value"])

    def test_insert_reuses_crlf(self):
        result = insert_table_row("| A |\r\n|---|\r\n| 1 |\r\nend", lambda col: "x")
        self.assertEqual("| A |\r\n|---|\r\n| 1 |\r\n| x |\r\nend", result["value"])
        self.assertIsNone(BARE_LF.search(result["value"]))

    def test_insert_at_end_without_trailing_eol(self):
        result = insert_table_row("| A |\n|---|\n| 1 |", lambda col: "x")
        self.assertEqual("| A |\n|---|\n| 1 |\n| x |", result["value"])
        result = insert_table_row("| A |\r\n|---|\r\n| 1 |", lambda col: "x")
        self.assertEqual("| A |\r\n|---|\r\n| 1 |\r\n| x |", result["value"])
        result = insert_table_row("| A |\n|---|", lambda col: "x")
        self.assertEqual("| A |\n|---|\n| x |", result["value"])

    def test_insert_escapes_values(self):
        result = insert_table_row("| A | B |\n|---|---|", lambda col: "a|b" if col == "A" else "c\\d")
        self.assertEqual("| a\\|b | c\\\\d |", result["value"].split("\n")[2])
        reparsed = parse_markdown_table(result["value"])
        self.assertEqual({"A": "a|b", "B": "c\\d"}, reparsed["value"]["rows"][0])

    def test_insert_tolerates_ragged_rows(self):
        result = insert_table_row("| A | B |\n|---|---|\n| 1 |\n| 2 | 3 | 4 |\n", lambda col: "x")
        self.assertEqual("| A | B |\n|---|---|\n| 1 |\n| 2 | 3 | 4 |\n| x | x |\n", result["value"])

    def test_insert_failures(self):
        self.assertEqual({"ok": False, "reason": "no table found"}, insert_table_row("prose", lambda c: "x"))
        self.assertEqual({"ok": False, "reason": "missing delimiter row"}, insert_table_row("| A |\n| 1 |", lambda c: "x"))
        self.assertEqual({"ok": False, "reason": "missing delimiter row"}, insert_table_row("| A |", lambda c: "x"))
        self.assertEqual({"ok": False, "reason": "missing delimiter row"}, insert_table_row("| A |\n| b |\n", lambda c: "x"))


if __name__ == "__main__":
    unittest.main()
