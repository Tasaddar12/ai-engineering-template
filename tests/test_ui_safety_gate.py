"""Port of upstream tests/ui-safety-gate.test.cjs plus CLI exit-code coverage."""
import importlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT/"engineer/bin"
LIB = ROOT/"engineer/bin/lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package (another ``lib`` package exists under .ai/runtime)."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib."+name)


gate = _load("ui_safety_gate")
NOTHING = {"hasUI": False, "tokens": [], "matchedToken": None, "matchedLine": None}


class UiTokensTests(unittest.TestCase):
    def test_expected_tokens(self):
        self.assertIsInstance(gate.UI_TOKENS, tuple)
        for token in ("UI", "frontend", "component"):
            self.assertIn(token, gate.UI_TOKENS)
        self.assertEqual(11, len(gate.UI_TOKENS))


class CheckUiPresenceTests(unittest.TestCase):
    def test_non_string_input(self):
        self.assertEqual(NOTHING, gate.check_ui_presence(42))
        self.assertEqual(NOTHING, gate.check_ui_presence(None))
        self.assertEqual(NOTHING, gate.check_ui_presence(b"UI"))

    def test_empty_string(self):
        self.assertEqual(NOTHING, gate.check_ui_presence(""))

    def test_standalone_ui_token_is_case_insensitive(self):
        result = gate.check_ui_presence("This task involves UI work")
        self.assertTrue(result["hasUI"])
        self.assertIn("ui", result["tokens"])
        self.assertIn("ui", gate.check_ui_presence("the ui layer")["tokens"])

    def test_frontend_token(self):
        result = gate.check_ui_presence("Build a frontend component")
        self.assertTrue(result["hasUI"])
        self.assertIn("frontend", result["tokens"])

    def test_interior_of_an_alphanumeric_word_does_not_match(self):
        self.assertFalse(gate.check_ui_presence("Requirements analysis")["hasUI"])
        self.assertFalse(gate.check_ui_presence("microfrontend architecture")["hasUI"])
        self.assertFalse(gate.check_ui_presence("pagelayout and viewer")["hasUI"])
        self.assertFalse(gate.check_ui_presence("form1 and 2form")["hasUI"])

    def test_hyphen_is_a_word_boundary(self):
        result = gate.check_ui_presence("micro-frontend design")
        self.assertTrue(result["hasUI"])
        self.assertIn("frontend", result["tokens"])

    def test_hyphenated_proper_noun_matches_and_is_introspectable(self):
        result = gate.check_ui_presence("Fix broken references in dashboard-financeiro and .env.tpl.")
        self.assertEqual((True, ["dashboard"], "dashboard"), (result["hasUI"], result["tokens"], result["matchedToken"]))
        self.assertIn("dashboard-financeiro", result["matchedLine"])

    def test_matched_line_is_the_first_matching_line(self):
        result = gate.check_ui_presence("Intro line with no tokens.\nBuild the login form.\nAlso a dashboard.")
        self.assertEqual(("form", "Build the login form."), (result["matchedToken"], result["matchedLine"]))

    def test_hint_yes_without_tokens_has_null_match_fields(self):
        result = gate.check_ui_presence("**UI hint**: yes\n\nBackend API refactor.\n")
        self.assertEqual((True, [], None, None), (result["hasUI"], result["tokens"], result["matchedToken"], result["matchedLine"]))

    def test_crlf_is_normalised(self):
        result = gate.check_ui_presence("Phase 1\r\nBuild a form\r\nDone")
        self.assertTrue(result["hasUI"])
        self.assertIn("form", result["tokens"])
        self.assertEqual("Build a form", result["matchedLine"])

    def test_repeated_tokens_are_deduplicated(self):
        result = gate.check_ui_presence("UI component and another UI widget")
        self.assertEqual(1, result["tokens"].count("ui"))
        self.assertEqual(["ui"], result["tokens"], "the consumed boundary hides the adjacent tokens, as in JavaScript")
        self.assertEqual(["ui", "component", "widget"], gate.check_ui_presence("UI, component, UI, widget")["tokens"], "first-seen order")

    def test_multiple_distinct_tokens(self):
        result = gate.check_ui_presence("Build a dashboard with a form")
        self.assertTrue(result["hasUI"])
        self.assertIn("dashboard", result["tokens"])
        self.assertIn("form", result["tokens"])

    def test_tokens_sharing_one_boundary_character_are_not_both_matched(self):
        # The trailing boundary of one match is consumed, so an immediately adjacent token
        # separated by a single character loses its leading boundary (JavaScript matchAll behaves the same).
        self.assertEqual(["form"], gate.check_ui_presence("form view")["tokens"])
        self.assertEqual(["form", "view"], gate.check_ui_presence("form  view")["tokens"])

    def test_token_at_the_end_of_a_line_matches(self):
        self.assertEqual(["page"], gate.check_ui_presence("go to the next page")["tokens"])
        self.assertEqual(["screen"], gate.check_ui_presence("screen")["tokens"])

    def test_lone_carriage_return_is_not_a_line_break(self):
        self.assertEqual(["form"], gate.check_ui_presence("a form\rb")["tokens"])

    def test_non_ascii_neighbours_are_boundaries(self):
        self.assertTrue(gate.check_ui_presence("caféform")["hasUI"])
        self.assertTrue(gate.check_ui_presence("éformé")["hasUI"])

    def test_kelvin_sign_is_not_an_ascii_k(self):
        self.assertFalse(gate.check_ui_presence("K")["hasUI"])
        self.assertEqual(["ui"], gate.check_ui_presence("UI")["tokens"])


class UiHintTests(unittest.TestCase):
    def test_hint_no_is_authoritative_non_frontend(self):
        result = gate.check_ui_presence("**UI hint**: no\n\nBackend-only spike for RBAC/Entra.\n")
        self.assertEqual((False, []), (result["hasUI"], result["tokens"]))

    def test_hint_yes_is_authoritative_frontend(self):
        self.assertTrue(gate.check_ui_presence("**UI hint**: yes\n\nRefactor the login screen layout.\n")["hasUI"])

    def test_hint_yes_over_a_pure_backend_body(self):
        result = gate.check_ui_presence("**UI hint**: yes\n\nBackend API refactor.\n")
        self.assertEqual((True, []), (result["hasUI"], result["tokens"]))

    def test_hint_value_is_whole_word_matched(self):
        self.assertTrue(gate.check_ui_presence("**UI hint**: nope\n\nBuild a dashboard component.\n")["hasUI"])

    def test_hint_without_yes_or_no_is_stripped(self):
        self.assertFalse(gate.check_ui_presence("**UI hint**: maybe\n\nBackend REST API only.\n")["hasUI"])

    def test_hint_no_overrides_ui_language_elsewhere(self):
        self.assertFalse(gate.check_ui_presence("**UI hint**: no\n\nBuild a dashboard component.\n")["hasUI"])

    def test_hint_is_case_and_spacing_tolerant_but_line_anchored(self):
        self.assertFalse(gate.check_ui_presence("  **ui HINT**  :  NO\nBuild a dashboard")["hasUI"])
        self.assertTrue(gate.check_ui_presence("Note: **UI hint**: no\nBuild a dashboard")["hasUI"], "a mid-line mention is not the metadata line")
        self.assertTrue(gate.check_ui_presence("Intro\n**UI hint**: yes")["hasUI"])
        self.assertFalse(gate.check_ui_presence("**UI hint**: no\r\nBuild a form\r\n")["hasUI"])

    def test_first_hint_line_wins(self):
        self.assertFalse(gate.check_ui_presence("**UI hint**: no\n**UI hint**: yes\nform")["hasUI"])
        self.assertTrue(gate.check_ui_presence("**UI hint**: yes\n**UI hint**: no\nform")["hasUI"])

    def test_hint_lines_never_contribute_tokens(self):
        result = gate.check_ui_presence("**UI hint**: yes\nbuild the widget")
        self.assertEqual(["widget"], result["tokens"])
        self.assertEqual("build the widget", result["matchedLine"])


class UiSafetyGateCliTests(unittest.TestCase):
    def run_main(self, data):
        stderr = io.StringIO()
        code = gate.main(stdin=io.BytesIO(data), stderr=stderr)
        return code, stderr.getvalue()

    def test_exit_constants_are_the_registered_values(self):
        self.assertEqual((0, 1, 66, 69), (gate.EXIT_PASS, gate.EXIT_FAIL, gate.EXIT_NO_INPUT, gate.EXIT_UNAVAILABLE))

    def test_ui_found_exits_0(self):
        self.assertEqual((0, ""), self.run_main(b"Build the login form"))

    def test_no_ui_in_real_input_exits_1(self):
        self.assertEqual((1, ""), self.run_main(b"Backend REST API only"))
        self.assertEqual((1, ""), self.run_main(b"**UI hint**: no\nBuild a form"), "an explicit hint on real input is still exit 1")

    def test_empty_or_whitespace_input_exits_66(self):
        for data in (b"", b"   \n\t\r\n", " ﻿".encode("utf-8"), " 　".encode("utf-8")):
            self.assertEqual((66, ""), self.run_main(data), data)

    def test_a_lone_nul_byte_is_real_input(self):
        self.assertEqual((1, ""), self.run_main(b"\x00"))

    def test_invalid_utf8_is_replaced_not_fatal(self):
        self.assertEqual((0, ""), self.run_main(b"\xff\xfe bad bytes but a form here"))

    def test_hint_yes_with_no_tokens_exits_0(self):
        self.assertEqual((0, ""), self.run_main(b"**UI hint**: yes\nBackend only"))

    def test_stdin_read_failure_exits_69_with_one_stderr_line(self):
        class Broken:
            def read(self):
                raise OSError("boom")
        stderr = io.StringIO()
        self.assertEqual(69, gate.main(stdin=Broken(), stderr=stderr))
        self.assertEqual("ERROR: ui-safety-gate.py stdin read failed: boom\n", stderr.getvalue())

    def test_text_stdin_is_accepted(self):
        self.assertEqual(0, gate.main(stdin=io.StringIO("a dashboard"), stderr=io.StringIO()))

    def run_module(self, data):
        return subprocess.run([sys.executable, "-m", "lib.ui_safety_gate"], cwd=BIN, input=data, capture_output=True)

    def test_subprocess_exit_codes_and_silent_stdout(self):
        for data, code in ((b"Build the login form\n", 0), (b"Backend only\n", 1), (b"", 66), (b"  \n", 66)):
            process = self.run_module(data)
            self.assertEqual((code, b""), (process.returncode, process.stdout), data)

    def test_subprocess_reads_utf8_regardless_of_console_code_page(self):
        process = self.run_module("café — page".encode("utf-8"))
        self.assertEqual((0, b""), (process.returncode, process.stdout))


if __name__ == "__main__":
    unittest.main()
