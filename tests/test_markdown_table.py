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
delete_table_row = _m.delete_table_row
escape_cell = _m.escape_cell
find_table_by_schema = _m.find_table_by_schema
find_table_with_columns = _m.find_table_with_columns
insert_table_row = _m.insert_table_row
is_delimiter_row = _m.is_delimiter_row
match_table_schema = _m.match_table_schema
parse_markdown_table = _m.parse_markdown_table
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
        self.assertEqual({"RoadmapProgress", "RequirementsTraceability", "Security"}, set(TABLE_SCHEMAS))
        self.assertEqual(["trust-boundaries", "threat-register", "accepted-risks", "audit-trail"],
                         [v["label"] for v in TABLE_SCHEMAS["Security"]])


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
