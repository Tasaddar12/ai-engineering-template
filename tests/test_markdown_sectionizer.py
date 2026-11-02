"""Tests for engineer/bin/lib/markdown_sectionizer.py (port of upstream gsd-core src/markdown-sectionizer.cts)."""
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


_m = _load("markdown_sectionizer")
XML_DECISION_TAG_NAMES = _m.XML_DECISION_TAG_NAMES
collect_section = _m.collect_section
collect_sections = _m.collect_sections
delete_section = _m.delete_section
edit_outside_fences = _m.edit_outside_fences
edit_outside_tagged_blocks = _m.edit_outside_tagged_blocks
extract_fenced_block = _m.extract_fenced_block
extract_tagged_blocks = _m.extract_tagged_blocks
extract_xml_tag_bodies = _m.extract_xml_tag_bodies
iterate_bullets = _m.iterate_bullets
mask_fences = _m.mask_fences
replace_section = _m.replace_section
scan_fenced_blocks = _m.scan_fenced_blocks
scan_inline_code_spans = _m.scan_inline_code_spans
strip_fenced_code = _m.strip_fenced_code
strip_inline_code = _m.strip_inline_code
strip_tagged_blocks = _m.strip_tagged_blocks
tokenize_headings = _m.tokenize_headings
update_bullet = _m.update_bullet
update_heading = _m.update_heading
with_section = _m.with_section


def head(text):
    return lambda h: h["text"] == text


class StripInlineCodeTests(unittest.TestCase):
    def test_single_backtick_span_removed(self):
        self.assertEqual("Verify the   helper", strip_inline_code("Verify the `api` helper"))

    def test_double_backtick_span(self):
        self.assertEqual("see   here", strip_inline_code("see ``a `nested` tick`` here"))

    def test_unmatched_run_is_literal(self):
        self.assertEqual("a ` stray backtick", strip_inline_code("a ` stray backtick"))

    def test_longer_closing_run_does_not_close(self):
        self.assertEqual("a `x`` b", strip_inline_code("a `x`` b"))

    def test_multiple_spans(self):
        self.assertEqual("  and   remain not", strip_inline_code("`a` and `b` remain not"))

    def test_spans_do_not_cross_lines(self):
        self.assertEqual("open `here\nstill` open", strip_inline_code("open `here\nstill` open"))

    def test_non_string_and_empty(self):
        for bad in (None, "", 5, []):
            self.assertEqual("", strip_inline_code(bad))

    def test_text_without_backticks_unchanged(self):
        s = "plain prose, no code spans at all"
        self.assertEqual(s, strip_inline_code(s))

    def test_many_unmatched_increasing_runs_is_linear(self):
        line = " ".join("`" * n for n in range(1, 400))
        self.assertEqual(line, strip_inline_code(line))


class ScanInlineCodeSpansTests(unittest.TestCase):
    def test_spans_cover_delimiters(self):
        self.assertEqual([{"start": 4, "end": 9, "content": "api"}, {"start": 14, "end": 19, "content": "x"}],
                         scan_inline_code_spans("use `api` and ``x``"))

    def test_offsets_into_full_string(self):
        self.assertEqual([{"start": 2, "end": 5, "content": "x"}], scan_inline_code_spans("a `x`\nno `span\nhere"))

    def test_non_string_and_empty(self):
        self.assertEqual([], scan_inline_code_spans(None))
        self.assertEqual([], scan_inline_code_spans(""))


class StripFencedCodeTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual({"text": "", "unterminatedFence": False}, strip_fenced_code(""))

    def test_non_string(self):
        for bad in (None, 42, [], {}):
            self.assertEqual({"text": "", "unterminatedFence": False}, strip_fenced_code(bad))

    def test_no_fences_unchanged(self):
        src = "## Heading\n\nSome text.\n\n- bullet"
        self.assertEqual({"text": src, "unterminatedFence": False}, strip_fenced_code(src))

    def test_backtick_fence(self):
        r = strip_fenced_code("\n".join(["before", "```js", "const x = 1;", "```", "after"]))
        self.assertEqual({"text": "before\nafter", "unterminatedFence": False}, r)

    def test_tilde_fence(self):
        r = strip_fenced_code("before\n~~~\nsome code\n~~~\nafter")
        self.assertEqual({"text": "before\nafter", "unterminatedFence": False}, r)

    def test_crlf(self):
        r = strip_fenced_code("before\r\n```\r\ncode\r\n```\r\nafter")
        self.assertNotIn("code", r["text"])
        self.assertFalse(r["unterminatedFence"])
        self.assertEqual("before\r\nafter", r["text"])

    def test_unterminated(self):
        r = strip_fenced_code("before\n```\nsome code without closing fence")
        self.assertTrue(r["unterminatedFence"])
        self.assertNotIn("some code", r["text"])

    def test_tilde_inside_backtick_fence_is_content(self):
        r = strip_fenced_code("```\n~~~\nstill inside\n```\noutside")
        self.assertEqual({"text": "outside", "unterminatedFence": False}, r)

    def test_backtick_inside_tilde_fence_is_content(self):
        r = strip_fenced_code("~~~\n```\nstill inside\n~~~\noutside")
        self.assertEqual({"text": "outside", "unterminatedFence": False}, r)

    def test_longer_same_char_closer(self):
        r = strip_fenced_code("text\n```\nbody\n`````\nafter")
        self.assertEqual({"text": "text\nafter", "unterminatedFence": False}, r)

    def test_closer_with_trailing_text_is_content(self):
        r = strip_fenced_code("```\n``` still inside (has trailing text)\n```\nafter")
        self.assertEqual({"text": "after", "unterminatedFence": False}, r)

    def test_multiple_blocks(self):
        r = strip_fenced_code("a\n```\ncode1\n```\nb\n```\ncode2\n```\nc")
        self.assertEqual({"text": "a\nb\nc", "unterminatedFence": False}, r)

    def test_backtick_in_info_string_is_not_an_opener(self):
        r = strip_fenced_code("``` ` not-a-fence\n## Heading\n")
        self.assertIn("## Heading", r["text"])
        self.assertIn("``` ` not-a-fence", r["text"])
        self.assertFalse(r["unterminatedFence"])

    def test_four_space_indent_is_not_a_fence(self):
        self.assertEqual("    ```\nkept", strip_fenced_code("    ```\nkept")["text"])

    def test_js_dot_semantics_embedded_carriage_return_is_not_a_delimiter(self):
        # JS `.` excludes \r, so "```a\rb" is not a fence opener and the line is kept
        r = strip_fenced_code("```a\rb\ncode")
        self.assertEqual({"text": "```a\rb\ncode", "unterminatedFence": False}, r)


class StripFencedCodePropertyTests(unittest.TestCase):
    ALPHABET = ["```", "~~~", "````", "```js", "  ```", "# H", "- [ ] x", "", "text", "``` `", "\r", "a\r"]

    def docs(self, count=400, seed=1):
        rng = random.Random(seed)
        for _ in range(count):
            lines = [rng.choice(self.ALPHABET) for _ in range(rng.randint(0, 12))]
            yield rng.choice(["\n", "\r\n"]).join(lines)

    def test_never_throws_and_shape(self):
        for doc in self.docs():
            r = strip_fenced_code(doc)
            self.assertIsInstance(r["text"], str)
            self.assertIsInstance(r["unterminatedFence"], bool)

    def test_idempotent(self):
        for doc in self.docs(seed=2):
            once = strip_fenced_code(doc)
            twice = strip_fenced_code(once["text"])
            self.assertEqual(once["text"], twice["text"], repr(doc))
            self.assertTrue(not twice["unterminatedFence"] or once["unterminatedFence"], repr(doc))

    def test_never_longer_than_input(self):
        for doc in self.docs(seed=3):
            self.assertLessEqual(len(strip_fenced_code(doc)["text"]), len(doc))

    def test_arbitrary_unicode_strings_do_not_throw(self):
        rng = random.Random(4)
        for _ in range(200):
            doc = "".join(chr(rng.choice([rng.randint(0, 0x2FF), rng.randint(0x2000, 0x2100), 0x60, 0x7E, 0x0A, 0x0D]))
                          for _ in range(rng.randint(0, 80)))
            strip_fenced_code(doc)
            tokenize_headings(doc)
            iterate_bullets(doc)


class ExtractFencedBlockTests(unittest.TestCase):
    def test_empty_and_non_string(self):
        self.assertIsNone(extract_fenced_block("", "coverage"))
        self.assertIsNone(extract_fenced_block(None, "coverage"))

    def test_non_string_info_string(self):
        self.assertIsNone(extract_fenced_block("```coverage\nbody\n```", None))

    def test_extracts_inner_body(self):
        src = "prose before\n```coverage\n[{\"capability\":\"search\",\"decision\":\"INTEGRATE\",\"reason\":\"\"}]\n```\nprose after"
        self.assertEqual('[{"capability":"search","decision":"INTEGRATE","reason":""}]', extract_fenced_block(src, "coverage"))

    def test_case_insensitive(self):
        src = "```Coverage\ninner text\n```"
        self.assertEqual("inner text", extract_fenced_block(src, "coverage"))
        self.assertEqual("inner text", extract_fenced_block(src, "COVERAGE"))

    def test_other_info_string_ignored(self):
        self.assertIsNone(extract_fenced_block('```json\n{"a":1}\n```', "coverage"))

    def test_no_fence(self):
        self.assertIsNone(extract_fenced_block("just prose\n## Heading\n- bullet", "coverage"))

    def test_unterminated(self):
        self.assertIsNone(extract_fenced_block("```coverage\nunterminated body, no closing fence", "coverage"))

    def test_tilde(self):
        self.assertEqual("tilde-fenced body", extract_fenced_block("~~~coverage\ntilde-fenced body\n~~~", "coverage"))

    def test_exact_equality_not_prefix(self):
        self.assertIsNone(extract_fenced_block("```coverage extra-stuff\nbody\n```", "coverage"))

    def test_trailing_whitespace_trimmed(self):
        self.assertEqual("body", extract_fenced_block("```coverage   \nbody\n```", "coverage"))

    def test_nested_inside_longer_fence(self):
        src = "````outer\n```coverage\nnested body\n```\n````"
        self.assertIsNone(extract_fenced_block(src, "coverage"))
        self.assertEqual("```coverage\nnested body\n```", extract_fenced_block(src, "outer"))

    def test_first_matching_block(self):
        src = "```coverage\nfirst\n```\nprose\n```coverage\nsecond\n```"
        self.assertEqual("first", extract_fenced_block(src, "coverage"))

    def test_empty_body_is_empty_string(self):
        self.assertEqual("", extract_fenced_block("```coverage\n\n```", "coverage"))


class ScanFencedBlocksTests(unittest.TestCase):
    def test_record_shape(self):
        blocks = scan_fenced_blocks(["before", "```js", "const x = 1;", "```", "after"])
        self.assertEqual([{"char": "`", "len": 3, "infoString": "js", "openLineIdx": 1, "closeLineIdx": 3}], blocks)

    def test_unterminated(self):
        blocks = scan_fenced_blocks(["before", "```", "body, never closed"])
        self.assertEqual((1, -1), (blocks[0]["openLineIdx"], blocks[0]["closeLineIdx"]))

    def test_requires_three_chars(self):
        self.assertEqual([], scan_fenced_blocks(["``", "not a fence"]))
        self.assertEqual([], scan_fenced_blocks(["~~", "not a fence"]))
        self.assertEqual("`", scan_fenced_blocks(["```", "x", "```"])[0]["char"])
        self.assertEqual("~", scan_fenced_blocks(["~~~", "x", "~~~"])[0]["char"])

    def test_indent_tolerance(self):
        blocks = scan_fenced_blocks(["   ```", "body", "```"])
        self.assertEqual((0, 2), (blocks[0]["openLineIdx"], blocks[0]["closeLineIdx"]))
        self.assertEqual([], scan_fenced_blocks(["    ```", "still not a fence"]))

    def test_closer_rules(self):
        self.assertEqual(2, scan_fenced_blocks(["```", "body", "`````"])[0]["closeLineIdx"])
        self.assertEqual(-1, scan_fenced_blocks(["````", "body", "```"])[0]["closeLineIdx"])

    def test_nested_shorter_run_is_content(self):
        blocks = scan_fenced_blocks(["````outer", "```coverage", "nested body", "```", "````"])
        self.assertEqual(1, len(blocks))
        self.assertEqual((4, 0, 4), (blocks[0]["len"], blocks[0]["openLineIdx"], blocks[0]["closeLineIdx"]))

    def test_shorter_run_while_open(self):
        blocks = scan_fenced_blocks(["````", "```", "still inside", "````"])
        self.assertEqual((0, 3), (blocks[0]["openLineIdx"], blocks[0]["closeLineIdx"]))

    def test_trailing_text_closer_is_content(self):
        blocks = scan_fenced_blocks(["```", "``` still inside (has trailing text)", "```", "after"])
        self.assertEqual((0, 2), (blocks[0]["openLineIdx"], blocks[0]["closeLineIdx"]))

    def test_backtick_in_info_string_not_an_opener(self):
        self.assertEqual([], scan_fenced_blocks(["``` has ` a backtick", "more text"]))

    def test_info_string_trimmed(self):
        self.assertEqual("js and stuff", scan_fenced_blocks(["```   js and stuff   ", "body", "```"])[0]["infoString"])

    def test_multiple_blocks_in_order(self):
        blocks = scan_fenced_blocks(["a", "```", "code1", "```", "b", "~~~py", "code2", "~~~", "c"])
        self.assertEqual(2, len(blocks))
        self.assertEqual(("`", 1, 3), (blocks[0]["char"], blocks[0]["openLineIdx"], blocks[0]["closeLineIdx"]))
        self.assertEqual(("~", "py", 5, 7), (blocks[1]["char"], blocks[1]["infoString"], blocks[1]["openLineIdx"], blocks[1]["closeLineIdx"]))

    def test_crlf_delimiters(self):
        blocks = scan_fenced_blocks(["```\r", "x", "```\r"])
        self.assertEqual((0, 2), (blocks[0]["openLineIdx"], blocks[0]["closeLineIdx"]))


class TokenizeHeadingsTests(unittest.TestCase):
    def test_empty_and_non_string(self):
        for bad in ("", None):
            self.assertEqual([], tokenize_headings(bad))

    def test_document_order(self):
        tokens = tokenize_headings("# H1\n## H2\n### H3\n")
        self.assertEqual([(1, "H1"), (2, "H2"), (3, "H3")], [(t["level"], t["text"]) for t in tokens])

    def test_fenced_headings_ignored(self):
        tokens = tokenize_headings("# Real heading\n```\n## Fake heading inside fence\n```\n## Another real heading")
        self.assertEqual(["Real heading", "Another real heading"], [t["text"] for t in tokens])

    def test_unicode(self):
        tokens = tokenize_headings("## Résumé — Überblick\n### 日本語見出し\n")
        self.assertEqual(["Résumé — Überblick", "日本語見出し"], [t["text"] for t in tokens])

    def test_line_and_offset(self):
        src = "prose\n## Heading\n"
        t = tokenize_headings(src)[0]
        self.assertEqual((2, 6), (t["line"], t["offset"]))
        self.assertTrue(src[t["offset"]:].startswith("## Heading"))

    def test_token_shape(self):
        self.assertEqual({"level", "text", "line", "offset"}, set(tokenize_headings("# A")[0]))

    def test_crlf(self):
        self.assertEqual(["H1", "H2"], [t["text"] for t in tokenize_headings("# H1\r\n## H2\r\n")])

    def test_setext_ignored(self):
        self.assertEqual([], tokenize_headings("Title\n=====\n\nSubtitle\n--------\n"))

    def test_up_to_three_space_indent(self):
        for indent, level in ((" ", 1), ("  ", 2), ("   ", 3)):
            tokens = tokenize_headings(f"{indent}{'#' * level} Heading text\n")
            self.assertEqual([(level, "Heading text")], [(t["level"], t["text"]) for t in tokens])

    def test_four_space_indent_is_not_a_heading(self):
        tokens = tokenize_headings("    ## Four space — not a heading\n## Real heading\n")
        self.assertEqual(["Real heading"], [t["text"] for t in tokens])

    def test_empty_headings(self):
        for src in ("##\n", "##   \n"):
            tokens = tokenize_headings(src)
            self.assertEqual([(2, "")], [(t["level"], t["text"]) for t in tokens])

    def test_closing_hash_sequence_stripped(self):
        self.assertEqual("Title", tokenize_headings("## Title ##\n")[0]["text"])
        self.assertEqual("C#", tokenize_headings("## C#\n")[0]["text"])
        self.assertEqual("", tokenize_headings("## ##\n")[0]["text"])

    def test_seven_hashes_and_missing_space_are_not_headings(self):
        self.assertEqual([], tokenize_headings("####### seven\n#hashtag\n"))

    def test_backtick_info_line_is_not_a_fence_opener(self):
        tokens = tokenize_headings("``` ` not-a-fence\n## Heading\nprose\n```\n")
        self.assertTrue(any(t["text"] == "Heading" for t in tokens))

    def test_tilde_fence_with_backtick_info_is_valid(self):
        tokens = tokenize_headings("~~~ ` this-is-fine\n## Inside tilde fence\n~~~\n## Outside\n")
        self.assertFalse(any(t["text"] == "Inside tilde fence" for t in tokens))
        self.assertTrue(any(t["text"] == "Outside" for t in tokens))

    def test_crlf_fenced_headings_ignored(self):
        texts = [t["text"] for t in tokenize_headings("# Outer\r\n```\r\n# Inner\r\n```\r\n## After\r\n")]
        self.assertEqual(["Outer", "After"], texts)

    def test_mismatched_delimiter_inside_fence_skips_heading_check(self):
        tokens = tokenize_headings("````\n```\n# inside\n````\n# out\n")
        self.assertEqual(["out"], [t["text"] for t in tokens])


class CollectSectionsTests(unittest.TestCase):
    def test_empty_and_non_string(self):
        self.assertEqual([], collect_sections("", lambda h: True))
        self.assertEqual([], collect_sections(None, lambda h: True))
        self.assertEqual([], collect_sections("no headings here", lambda h: True))

    def test_always_true_predicate(self):
        sections = collect_sections("## A\nBody A\n## B\nBody B\n", lambda h: True)
        self.assertEqual(["A", "B"], [s["heading"]["text"] for s in sections])
        self.assertEqual(["Body A", "Body B"], [s["body"] for s in sections])

    def test_non_matching_headings_become_body(self):
        src = "## Section A\nContent A\n## Section B\nContent B\n"
        sections = collect_sections(src, lambda h: "A" in h["text"])
        self.assertEqual(1, len(sections))
        self.assertIn("Section B", sections[0]["body"])
        self.assertIn("Content B", sections[0]["body"])

    def test_last_section_runs_to_eof(self):
        sections = collect_sections("## Only\nBody line 1\nBody line 2", lambda h: True)
        self.assertEqual("Body line 1\nBody line 2", sections[0]["body"])

    def test_adjacent_headings_have_empty_bodies(self):
        sections = collect_sections("## A\n## B\n## C\nContent C\n", lambda h: True)
        self.assertEqual(["", "", "Content C"], [s["body"] for s in sections])

    def test_section_shape_and_invariant(self):
        content = "## Alpha\nAlpha body.\n## Beta\nBeta body.\n## Gamma\nGamma body\n"
        sections = collect_sections(content, lambda h: True)
        self.assertEqual({"heading", "body", "bodyStart", "bodyEnd"}, set(sections[0]))
        for s in sections:
            self.assertEqual(s["body"], content[s["bodyStart"]:s["bodyEnd"]])
            self.assertEqual(content, replace_section(content, s, s["body"]))


class CollectSectionTests(unittest.TestCase):
    def test_no_match_and_non_string(self):
        self.assertIsNone(collect_section("## Foo\ntext\n", head("Bar")))
        self.assertIsNone(collect_section("", lambda h: True))
        self.assertIsNone(collect_section(None, lambda h: True))

    def test_level_bounded_default(self):
        r = collect_section("## Section A\nContent A\n## Section B\nContent B", head("Section A"))
        self.assertEqual("Content A", r["body"])

    def test_subheadings_included_when_level_bounded(self):
        src = "## Parent\nParent intro\n### Child\nChild body\n## Sibling\nSibling body"
        r = collect_section(src, head("Parent"), {"levelBounded": True})
        self.assertEqual("Parent intro\n### Child\nChild body", r["body"])

    def test_level_bounded_false_stops_at_any_heading(self):
        src = "## Parent\nParent intro\n### Child\nChild body\n## Sibling"
        r = collect_section(src, head("Parent"), {"levelBounded": False})
        self.assertEqual("Parent intro", r["body"])

    def test_strip_fences(self):
        src = "## Section\n```\ncode here\n```\nprose here"
        r = collect_section(src, head("Section"), {"stripFences": True})
        self.assertEqual("prose here", r["body"])
        self.assertIn("code here", collect_section(src, head("Section"))["body"])

    def test_heading_token_in_result(self):
        r = collect_section("## My Section\nContent\n", head("My Section"))
        self.assertEqual("My Section", r["heading"]["text"])
        self.assertEqual(2, r["heading"]["level"])

    def test_h3_section_with_h4_child(self):
        src = "### Alpha\nAlpha body\n#### Sub-Alpha\nSub-Alpha body\n### Beta\nBeta body"
        r = collect_section(src, head("Alpha"), {"levelBounded": True})
        self.assertIn("Sub-Alpha", r["body"])
        self.assertNotIn("Beta body", r["body"])

    def test_section_at_eof(self):
        self.assertEqual("Last line", collect_section("## Only\nLast line", head("Only"))["body"])

    def test_none_option_values_fall_back_to_defaults(self):
        src = "## P\nbody\n### C\nchild\n## S\n"
        r = collect_section(src, head("P"), {"levelBounded": None, "stopAtLevel": None, "stripFences": None})
        self.assertEqual("body\n### C\nchild", r["body"])

    def test_stop_at_level(self):
        src = "## Parent\nParent body\n### Child\nChild body\n## Sibling\nSibling body"
        r = collect_section(src, head("Parent"), {"stopAtLevel": 3})
        self.assertEqual("Parent body", r["body"])
        r = collect_section(src, head("Parent"), {"levelBounded": True})
        self.assertIn("Child body", r["body"])
        self.assertNotIn("Sibling body", r["body"])
        r = collect_section("## A\nA body\n## B\nB body\n", head("A"), {"stopAtLevel": 2})
        self.assertEqual("A body", r["body"])

    def test_stop_at_level_takes_precedence_over_level_bounded(self):
        src = "## Parent\nParent body\n### Child\nChild body\n## Sibling"
        r = collect_section(src, head("Parent"), {"stopAtLevel": 3, "levelBounded": False})
        self.assertEqual("Parent body", r["body"])

    def test_stop_at_level_invariant(self):
        src = "## Parent\nParent body\n### Child\nChild body\n## Sibling\nSibling body\n"
        s = collect_section(src, head("Parent"), {"stopAtLevel": 3})
        self.assertEqual(s["body"], src[s["bodyStart"]:s["bodyEnd"]])
        self.assertEqual(src, replace_section(src, s, s["body"]))

    def test_fenced_heading_does_not_end_section(self):
        src = "## Real\nReal body\n```\n## Fake inside fence\n```\nMore real body"
        r = collect_section(src, head("Real"))
        self.assertIn("More real body", r["body"])
        self.assertIn("## Fake inside fence", r["body"])


class IterateBulletsTests(unittest.TestCase):
    def test_empty_and_non_string(self):
        for bad in ("", None, "   "):
            self.assertEqual([], iterate_bullets(bad))

    def test_dash(self):
        items = iterate_bullets("- First\n- Second\n")
        self.assertEqual([{"marker": "dash", "text": "First", "indent": "", "checked": None},
                          {"marker": "dash", "text": "Second", "indent": "", "checked": None}], items)

    def test_star_and_plus(self):
        items = iterate_bullets("* Asterisk\n+ Plus\n")
        self.assertEqual([("dash", "Asterisk"), ("dash", "Plus")], [(i["marker"], i["text"]) for i in items])

    def test_checkboxes(self):
        un = iterate_bullets("- [ ] Todo item\n")[0]
        self.assertEqual(("checkbox-unchecked", False, "Todo item"), (un["marker"], un["checked"], un["text"]))
        for box in ("x", "X"):
            ch = iterate_bullets(f"- [{box}] Done item\n")[0]
            self.assertEqual(("checkbox-checked", True), (ch["marker"], ch["checked"]))

    def test_numbered(self):
        items = iterate_bullets("1. First\n2. Second\n42. Forty-two\n")
        self.assertEqual(["numbered"] * 3, [i["marker"] for i in items])
        self.assertEqual("Forty-two", items[2]["text"])
        self.assertIsNone(items[0]["checked"])

    def test_continuation_lines(self):
        items = iterate_bullets("- Main bullet\n  continuation line\n  another continuation\n- Next bullet")
        self.assertEqual("Main bullet continuation line another continuation", items[0]["text"])
        self.assertEqual("Next bullet", items[1]["text"])

    def test_blank_line_terminates(self):
        self.assertEqual(["First", "Second"], [i["text"] for i in iterate_bullets("- First\n\n- Second\n")])
        self.assertEqual(["First"], [i["text"] for i in iterate_bullets("- First\n\n  not continuation\n")])

    def test_mixed_markers(self):
        items = iterate_bullets("1. Numbered\n- [x] Checked\n- [ ] Unchecked\n- Plain dash")
        self.assertEqual(["numbered", "checkbox-checked", "checkbox-unchecked", "dash"], [i["marker"] for i in items])

    def test_crlf(self):
        self.assertEqual(["First", "Second"], [i["text"] for i in iterate_bullets("- First\r\n- Second\r\n")])

    def test_indent(self):
        self.assertEqual("  ", iterate_bullets("  - Indented bullet\n")[0]["indent"])

    def test_non_bullet_lines_ignored_or_terminate(self):
        self.assertEqual(["Bullet"], [i["text"] for i in iterate_bullets("Some prose\n\n- Bullet\n")])
        items = iterate_bullets("- A\nprose line not indented\n  indented after prose\n- B")
        self.assertEqual(["A", "B"], [i["text"] for i in items])


class UpdateBulletTests(unittest.TestCase):
    def test_non_string_and_empty_returned_unchanged(self):
        self.assertIsNone(update_bullet(None, lambda *a: True, lambda l: l))
        self.assertEqual("", update_bullet("", lambda *a: True, lambda l: l))

    def test_no_match_is_noop(self):
        content = "- [ ] Phase 1: Foo\n- [ ] Phase 2: Bar\n"
        self.assertEqual(content, update_bullet(content, lambda t, r, i: "Phase 9" in t, lambda l: l + " EDITED"))

    def test_flips_only_matched_bullet(self):
        content = "\n".join(["# Roadmap", "", "- [ ] Phase 1: Foundation", "- [ ] Phase 2: API", "- [ ] Phase 3: Polish", ""])
        result = update_bullet(content, lambda t, r, i: "Phase 2" in t,
                               lambda raw: raw.replace("[ ]", "[x]", 1) + " (completed 2026-01-01)")
        self.assertEqual("\n".join(["# Roadmap", "", "- [ ] Phase 1: Foundation",
                                    "- [x] Phase 2: API (completed 2026-01-01)", "- [ ] Phase 3: Polish", ""]), result)

    def test_match_arguments(self):
        seen = []
        update_bullet("- [ ] Phase 1: Foo\n", lambda t, r, i: seen.append((t, r, i)) or True, lambda r: r)
        self.assertEqual([("Phase 1: Foo", "- [ ] Phase 1: Foo", 0)], seen)

    def test_dash_and_numbered(self):
        self.assertEqual("- Alpha\n- Beta!\n", update_bullet("- Alpha\n- Beta\n", lambda t, r, i: t == "Beta", lambda l: l + "!"))
        self.assertEqual("1. Alpha\n2. Beta!\n", update_bullet("1. Alpha\n2. Beta\n", lambda t, r, i: t == "Beta", lambda l: l + "!"))

    def test_fenced_bullet_ignored(self):
        content = "\n".join(["- [ ] Phase 1: Foo", "```md", "- [ ] Phase 1: Foo (inside fence, must not match)", "```", "- [ ] Phase 2: Bar", ""])
        result = update_bullet(content, lambda t, r, i: "Phase 1" in t, lambda r: r.replace("[ ]", "[x]", 1))
        self.assertEqual(content.replace("- [ ] Phase 1: Foo\n", "- [x] Phase 1: Foo\n", 1), result)

    def test_bullet_only_inside_fence_is_noop(self):
        content = "```md\n- [ ] Phase 9: OnlyInFence\n```\n- [ ] Phase 1: Foo\n"
        self.assertEqual(content, update_bullet(content, lambda t, r, i: "Phase 9" in t, lambda r: r.replace("[ ]", "[x]")))

    def test_crlf_preserved(self):
        content = "- [ ] Phase 1: Foo\r\n- [ ] Phase 2: Bar\r\n"
        result = update_bullet(content, lambda t, r, i: "Phase 2" in t, lambda r: r.replace("[ ]", "[x]"))
        self.assertEqual("- [ ] Phase 1: Foo\r\n- [x] Phase 2: Bar\r\n", result)

    def test_non_string_transform_is_noop(self):
        content = "- [ ] Phase 1: Foo\n"
        self.assertEqual(content, update_bullet(content, lambda *a: True, lambda r: None))

    def test_only_first_match_replaced(self):
        content = "- [ ] Phase 1: Foo\n- [ ] Phase 1: Foo (duplicate)\n"
        result = update_bullet(content, lambda t, r, i: t.startswith("Phase 1"), lambda r: r.replace("[ ]", "[x]"))
        self.assertEqual("- [x] Phase 1: Foo\n- [ ] Phase 1: Foo (duplicate)\n", result)

    def test_indentation_preserved(self):
        self.assertEqual("  - [x] Nested: Item\n",
                         update_bullet("  - [ ] Nested: Item\n", lambda t, r, i: "Nested" in t, lambda l: l.replace("[ ]", "[x]")))

    def test_multi_space_checkbox_marker_is_stripped_cleanly(self):
        seen = []
        result = update_bullet("-  [ ] Phase 1: Foo\n", lambda t, r, i: seen.append(t) or "Phase 1" in t,
                               lambda r: r.replace("[ ]", "[x]") + " (completed 2026-01-01)")
        self.assertEqual(["Phase 1: Foo"], seen)
        self.assertEqual("-  [x] Phase 1: Foo (completed 2026-01-01)\n", result)

    def test_multi_space_dash_and_numbered(self):
        self.assertEqual("-   Alpha\n-   Beta!\n", update_bullet("-   Alpha\n-   Beta\n", lambda t, r, i: t == "Beta", lambda l: l + "!"))
        self.assertEqual("1.   Alpha\n2.   Beta!\n", update_bullet("1.   Alpha\n2.   Beta\n", lambda t, r, i: t == "Beta", lambda l: l + "!"))

    def test_tab_separated_marker(self):
        self.assertEqual("-\t[x] Phase 1: Foo\n",
                         update_bullet("-\t[ ] Phase 1: Foo\n", lambda t, r, i: "Phase 1" in t, lambda r: r.replace("[ ]", "[x]")))
        self.assertEqual("-\tAlpha\n-\tBeta!\n", update_bullet("-\tAlpha\n-\tBeta\n", lambda t, r, i: t == "Beta", lambda l: l + "!"))
        self.assertEqual("1.\tAlpha\n2.\tBeta!\n", update_bullet("1.\tAlpha\n2.\tBeta\n", lambda t, r, i: t == "Beta", lambda l: l + "!"))

    def test_line_index_is_physical_split_index(self):
        content = "intro\n- [ ] a\n\n- [ ] a\n"
        out = update_bullet(content, lambda t, r, i: i == 3, lambda r: r.replace("[ ]", "[x]"))
        self.assertEqual("intro\n- [ ] a\n\n- [x] a\n", out)

    def test_indented_nested_bullet_is_offered_too(self):
        seen = []
        update_bullet("- A\n  - nested\n", lambda t, r, i: seen.append(i) or False, lambda r: r)
        self.assertEqual([0, 1], seen)

    def test_flip_unflip_round_trip_property(self):
        rng = random.Random(7)
        for _ in range(200):
            n = rng.randint(1, 8)
            labels = ["".join(rng.choice("abc xyz-:.") for _ in range(rng.randint(1, 20))).strip() or "x" for _ in range(n)]
            target = rng.randrange(n)
            lines = [f"- [ ] Item {k}: {labels[k]}" for k in range(n)]
            content = "\n".join(lines) + "\n"
            flipped = update_bullet(content, lambda t, r, i: f"Item {target}:" in t, lambda r: r.replace("[ ]", "[x]", 1) + " EDITED")
            parts = flipped.split("\n")
            for k in range(n):
                if k != target:
                    self.assertEqual(lines[k], parts[k])
            self.assertEqual(f"- [x] Item {target}: {labels[target]} EDITED", parts[target])
            restored = update_bullet(flipped, lambda t, r, i: f"Item {target}:" in t,
                                     lambda r: r.replace("[x]", "[ ]", 1).replace(" EDITED", ""))
            self.assertEqual(content, restored)


class UpdateHeadingTests(unittest.TestCase):
    def swap(self, to):
        return lambda raw: to

    def test_rewrites_first_accepted_heading(self):
        content = "# Roadmap\n\n### Phase 1: Setup\nbody\n### Phase 2: Next\n"
        out = update_heading(content, lambda h, raw, idx: h["text"].startswith("Phase 1"), self.swap("### Phase 1-01: Setup"))
        self.assertEqual("# Roadmap\n\n### Phase 1-01: Setup\nbody\n### Phase 2: Next\n", out)

    def test_fenced_heading_never_offered(self):
        seen = []
        out = update_heading("```\n### Phase 1: Fenced\n```\n### Phase 1: Real\n",
                             lambda h, raw, idx: seen.append(idx) or True, self.swap("### CHANGED"))
        self.assertEqual([3], seen)
        self.assertEqual("```\n### Phase 1: Fenced\n```\n### CHANGED\n", out)

    def test_crlf_raw_line_carries_cr(self):
        raws = []
        out = update_heading("### A\r\n### B\r\ntext\n### C",
                             lambda h, raw, idx: raws.append(raw) or h["text"] == "B", lambda raw: raw.replace("B", "Bee"))
        self.assertEqual(["### A\r", "### B\r"], raws)
        self.assertEqual("### A\r\n### Bee\r\ntext\n### C", out)

    def test_line_index_disambiguates(self):
        content = "## v1\n### Phase 1: Same\n## v2\n### Phase 1: Same\n"
        out = update_heading(content, lambda h, raw, idx: idx == 3, self.swap("### Phase 2-01: Same"))
        self.assertEqual("## v1\n### Phase 1: Same\n## v2\n### Phase 2-01: Same\n", out)

    def test_last_line_without_newline(self):
        self.assertEqual("# A\n### C", update_heading("# A\n### B", lambda h, r, i: h["text"] == "B", self.swap("### C")))

    def test_bounded_noops(self):
        content = "### A\n"
        self.assertEqual(content, update_heading(content, lambda *a: False, self.swap("x")))
        self.assertEqual(content, update_heading(content, lambda *a: True, lambda r: 42))
        self.assertEqual("", update_heading("", lambda *a: True, self.swap("x")))
        self.assertIsNone(update_heading(None, lambda *a: True, self.swap("x")))

    def test_identity_rewrite_is_byte_identical_property(self):
        rng = random.Random(9)
        pool = ["# H", "### Phase 1: x", "text", "", "```", "- [ ] item"]
        for _ in range(200):
            content = "\n".join(rng.choice(pool) for _ in range(rng.randint(0, 12)))
            self.assertEqual(content, update_heading(content, lambda *a: True, lambda raw: raw))


class TaggedBlockTests(unittest.TestCase):
    def test_extract_empty_and_non_string(self):
        self.assertEqual([], extract_tagged_blocks("", "decisions"))
        self.assertEqual([], extract_tagged_blocks(None, "decisions"))
        self.assertEqual([], extract_tagged_blocks("<decisions>body</decisions>", ""))
        self.assertEqual([], extract_tagged_blocks("<decisions>body</decisions>", None))
        self.assertEqual([], extract_tagged_blocks("prose\n## Heading\n- bullet", "decisions"))

    def test_extract_single_and_multiple(self):
        self.assertEqual(["\nD-01: Foo\n"], extract_tagged_blocks("before\n<decisions>\nD-01: Foo\n</decisions>\nafter", "decisions"))
        self.assertEqual(["alpha", "beta", "gamma"],
                         extract_tagged_blocks("<tag>alpha</tag> middle <tag>beta</tag> end <tag>gamma</tag>", "tag"))

    def test_extract_crlf(self):
        self.assertEqual(["\r\nD-01: CRLF test\r\n"], extract_tagged_blocks("<decisions>\r\nD-01: CRLF test\r\n</decisions>", "decisions"))

    def test_tag_name_is_escaped(self):
        self.assertEqual(["inner"], extract_tagged_blocks("<my.tag>inner</my.tag>", "my.tag"))
        self.assertEqual([], extract_tagged_blocks("<myXtag>other</myXtag>", "my.tag"))
        self.assertEqual(["inner"], extract_tagged_blocks("<my+tag>inner</my+tag>", "my+tag"))

    def test_unclosed_tag_has_no_match(self):
        self.assertEqual([], extract_tagged_blocks("Text with <decisions> but tag is unclosed.", "decisions"))

    def test_nested_same_name_extracts_inner(self):
        self.assertEqual(["inner"], extract_tagged_blocks("<x><x>inner</x></x>", "x"))

    def test_back_to_back(self):
        self.assertEqual(["first", "second"], extract_tagged_blocks("<x>first</x><x>second</x>", "x"))

    def test_many_unclosed_openings_yield_nothing(self):
        self.assertEqual([], extract_tagged_blocks("<x>a\n" * 50 + "no closing tag", "x"))

    def test_attributes_opt_in(self):
        self.assertEqual("XY<details open>active</details>Z",
                         strip_tagged_blocks("X<details>shipped</details>Y<details open>active</details>Z", "details"))
        self.assertEqual(["body"], extract_tagged_blocks('<task type="auto">body</task>', "task", True))
        self.assertEqual([], extract_tagged_blocks('<task type="auto">body</task>', "task"))

    def test_extract_is_case_sensitive_and_strip_is_case_insensitive_by_default(self):
        self.assertEqual([], extract_tagged_blocks("<TAG>x</TAG>", "tag"))
        self.assertEqual("", strip_tagged_blocks("<TAG>x</TAG>", "tag"))
        self.assertEqual("<TAG>x</TAG>", strip_tagged_blocks("<TAG>x</TAG>", "tag", False, True))

    def test_strip_guards(self):
        self.assertEqual("", strip_tagged_blocks("", "a"))
        self.assertEqual("", strip_tagged_blocks(None, "a"))
        self.assertEqual("<a>x</a>", strip_tagged_blocks("<a>x</a>", ""))

    def test_attributed_boundary_with_allow_attributes(self):
        self.assertEqual(["in"], extract_tagged_blocks('<t a="1"><t b="2">in</t>', "t", True))


class EditOutsideTaggedBlocksTests(unittest.TestCase):
    def wrap(self, s):
        return f"[{s}]"

    def seeing(self, doc, tag, *flags):
        seen = []
        edit_outside_tagged_blocks(doc, tag, lambda s: seen.append(s) or s, *flags)
        return seen[0] if seen else None

    def test_edits_only_outside_and_restores_blocks(self):
        block1 = "<details>\nkeep $1 $& one\n</details>"
        block2 = "<details>\nkeep two\n</details>"
        out = edit_outside_tagged_blocks(f"a\n{block1}\nb\n{block2}\nc", "details", self.wrap)
        self.assertEqual(f"[a\n{block1}\nb\n{block2}\nc]", out)

    def test_edit_sees_placeholders_in_order(self):
        self.assertRegex(self.seeing("x<details>1</details>y<details>2</details>z", "details"),
                         r"^x<!-- gsd-masked-details-\d+-0 -->y<!-- gsd-masked-details-\d+-1 -->z$")

    def test_no_block_present(self):
        self.assertEqual("plain", self.seeing("plain", "details"))
        self.assertEqual("[plain]", edit_outside_tagged_blocks("plain", "details", self.wrap))

    def test_unclosed_opener_stays_visible(self):
        self.assertEqual("<details>open forever", self.seeing("<details>open forever", "details"))

    def test_attributed_opener_hidden_only_with_allow_attributes(self):
        doc = "<details open>x</details>"
        self.assertEqual(doc, self.seeing(doc, "details"))
        self.assertRegex(self.seeing(doc, "details", True), r"^<!-- gsd-masked-details-\d+-0 -->$")
        self.assertEqual(f"[{doc}]", edit_outside_tagged_blocks(doc, "details", self.wrap, True))

    def test_case_sensitivity(self):
        doc = "<details>x</details>"
        self.assertRegex(self.seeing(doc, "DETAILS"), r"^<!-- gsd-masked-DETAILS-\d+-0 -->$")
        self.assertEqual(doc, self.seeing(doc, "DETAILS", False, True))

    def test_placeholder_lookalike_is_not_a_block(self):
        doc = "<!-- gsd-masked-details-0-0 -->\n<details>b</details>\ntail"
        self.assertEqual(f"[{doc}]", edit_outside_tagged_blocks(doc, "details", self.wrap))
        # the nonce skips the lookalike's number, so the real placeholder is distinct
        self.assertRegex(self.seeing(doc, "details"), r"\n<!-- gsd-masked-details-1-0 -->\ntail$")

    def test_dropped_or_duplicated_placeholder_returns_original(self):
        doc = "a<details>b</details>c"
        self.assertEqual(doc, edit_outside_tagged_blocks(doc, "details", lambda s: "gone"))
        self.assertEqual(doc, edit_outside_tagged_blocks(doc, "details", lambda s: s + s))

    def test_non_string_edit_result(self):
        self.assertEqual("a<details>b</details>", edit_outside_tagged_blocks("a<details>b</details>", "details", lambda s: None))

    def test_empty_and_non_string_input(self):
        self.assertEqual("", edit_outside_tagged_blocks("", "details", self.wrap))
        self.assertIsNone(edit_outside_tagged_blocks(None, "details", self.wrap))
        self.assertEqual("[abc]", edit_outside_tagged_blocks("abc", "", self.wrap))


class MaskFencesTests(unittest.TestCase):
    F = "```"

    def upper(self, text):
        return re.sub(r"^field:.*$", "field: EDITED", text, flags=re.M)

    def test_edit_reaches_only_live_lines(self):
        F = self.F
        content = "\n".join(["field: a", F, "field: in-fence", F, "field: b"])
        self.assertEqual("\n".join(["field: EDITED", F, "field: in-fence", F, "field: EDITED"]), edit_outside_fences(content, self.upper))

    def test_no_fence_edited_as_given(self):
        self.assertEqual("field: EDITED\nfield: EDITED", edit_outside_fences("field: a\nfield: b", self.upper))

    def test_unterminated_fence_masks_to_end(self):
        F = self.F
        content = "\n".join(["field: a", F, "field: in-fence", "field: also"])
        self.assertEqual("\n".join(["field: EDITED", F, "field: in-fence", "field: also"]), edit_outside_fences(content, self.upper))

    def test_tilde_and_multiple_blocks(self):
        F = self.F
        content = "\n".join(["~~~", "field: t", "~~~", "field: live", F, "field: c", F])
        self.assertEqual("\n".join(["~~~", "field: t", "~~~", "field: EDITED", F, "field: c", F]), edit_outside_fences(content, self.upper))

    def test_crlf_keeps_terminators(self):
        F = self.F
        content = "\r\n".join(["field: a", F, "field: in-fence", F, "field: b"])
        out = edit_outside_fences(content, lambda t: re.sub(r"^field: a", "field: A", t, count=1, flags=re.M))
        self.assertEqual("\r\n".join(["field: A", F, "field: in-fence", F, "field: b"]), out)

    def test_destroyed_placeholder_fails_closed(self):
        content = "\n".join(["field: a", self.F, "x", self.F])
        self.assertEqual(content, edit_outside_fences(content, lambda t: "nothing left"))

    def test_non_string_results_and_inputs(self):
        content = "\n".join(["a", self.F, "b", self.F])
        self.assertEqual(content, edit_outside_fences(content, lambda t: None))
        self.assertIsNone(edit_outside_fences(None, self.upper))
        self.assertEqual("", edit_outside_fences("", self.upper))

    def test_mask_exposes_masked_and_restore(self):
        content = "\n".join(["field: a", self.F, "field: in-fence", self.F, "field: b"])
        mask = mask_fences(content)
        self.assertNotIn("in-fence", mask.masked)
        self.assertEqual(content, mask.restore(mask.masked))
        self.assertIsNone(mask.restore("lost"))
        self.assertIsNone(mask.restore(None))

    def test_no_fence_mask_is_identity(self):
        mask = mask_fences("plain\ntext")
        self.assertEqual("plain\ntext", mask.masked)
        self.assertEqual("edited", mask.restore("edited"))
        self.assertEqual("", mask_fences("").masked)
        self.assertIsNone(mask_fences(None).masked)

    def test_placeholder_lookalike_does_not_confuse_restore(self):
        decoy = "<!-- gsd-masked-fence-0-0 -->"
        F = self.F
        content = "\n".join([decoy, F, "field: in-fence", F, "field: b"])
        self.assertEqual("\n".join([decoy, F, "field: in-fence", F, "field: EDITED"]), edit_outside_fences(content, self.upper))

    def test_restore_round_trip_property(self):
        rng = random.Random(11)
        pool = ["```", "~~~", "````", "```js", "  ```", "field: x", "# Heading", "", "<!-- gsd-masked-fence-0-0 -->", "ab", "x y"]
        for _ in range(300):
            lines = [rng.choice(pool) for _ in range(rng.randint(0, 14))]
            content = rng.choice(["\n", "\r\n"]).join(lines)
            mask = mask_fences(content)
            self.assertEqual(content, mask.restore(mask.masked), repr(content))


class ReplaceAndWithSectionTests(unittest.TestCase):
    def test_replace_section_preserves_surroundings(self):
        content = "## Intro\nIntro body.\n## Name\nOld name body.\n## Footer\nFooter body.\n"
        section = collect_section(content, head("Name"))
        new = replace_section(content, section, "New name body.\n")
        self.assertEqual("## Intro\nIntro body.\n## Name\nNew name body.\n\n## Footer\nFooter body.\n", new)

    def test_round_trip_identity(self):
        content = "## Section A\nLine one.\nLine two.\n## Section B\nB body.\n"
        s = collect_section(content, head("Section A"))
        self.assertEqual(s["body"], content[s["bodyStart"]:s["bodyEnd"]])
        self.assertEqual(content, replace_section(content, s, s["body"]))

    def test_crlf(self):
        content = "## Title\r\nOld body.\r\n## Next\r\nNext body.\r\n"
        s = collect_section(content, head("Title"))
        updated = replace_section(content, s, "New body.\r\n")
        self.assertIn("## Title\r\n", updated)
        self.assertIn("New body.", updated)
        self.assertNotIn("Old body.", updated)
        self.assertIn("## Next\r\nNext body.", updated)

    def test_non_string_arguments(self):
        content = "## Sec\nbody\n"
        s = collect_section(content, head("Sec"))
        self.assertIsNone(replace_section(None, s, "x"))
        self.assertEqual(content, replace_section(content, s, None))

    def test_offset_invariant_variants(self):
        for content, name in (("## A\nBody A\n## B\nBody B\n", "A"), ("## Only\nLast line", "Only"),
                              ("## Title\r\nBody line.\r\n## Next\r\nNext body.\r\n", "Title"), ("## A\n## B\nB body\n", "A")):
            s = collect_section(content, head(name))
            self.assertEqual(s["body"], content[s["bodyStart"]:s["bodyEnd"]], content)
            self.assertEqual(content, replace_section(content, s, s["body"]), content)

    def test_with_section_edits_only_target(self):
        content = "## Intro\nIntro body.\n## Name\nOld name body.\n## Footer\nFooter body.\n"
        result = with_section(content, "Name", lambda b: b.replace("Old name body.", "New name body."))
        self.assertEqual("## Intro\nIntro body.\n## Name\nNew name body.\n## Footer\nFooter body.\n", result)

    def test_with_section_miss_and_noop_cases(self):
        content = "## A\nBody A\n## B\nBody B\n"
        self.assertEqual(content, with_section(content, "Nonexistent", lambda b: b + " MUTATED"))
        self.assertEqual(content, with_section(content, "A", lambda b: b))
        self.assertEqual(content, with_section(content, "A", lambda b: 42))
        self.assertIsNone(with_section(None, "A", lambda b: b + "x"))

    def test_with_section_predicate_form_and_trimmed_target(self):
        content = "## Alpha\nAlpha body\n## Beta\nBeta body\n"
        result = with_section(content, lambda h: h["level"] == 2 and h["text"] == "Beta", lambda b: b.upper())
        self.assertIn("## Beta\nBETA BODY", result)
        self.assertIn("## Alpha\nAlpha body", result)
        self.assertIn("## Alpha\nALPHA BODY", with_section(content, "  Alpha ", lambda b: b.upper()))

    def test_greedy_regex_cannot_cross_a_section_boundary(self):
        content = "\n".join(["## Section One", "alpha content line 1", "alpha content line 2", "## Section Two",
                             "beta content to be replaced", "## Section Three", "gamma content line 1", "gamma content line 2"]) + "\n"
        one = collect_section(content, head("Section One"))
        three = collect_section(content, head("Section Three"))
        result = with_section(content, "Section Two", lambda body: re.sub(r"[\s\S]*", "REPLACED ENTIRELY", body, count=1))
        self.assertEqual(one["body"], collect_section(result, head("Section One"))["body"])
        self.assertEqual(three["body"], collect_section(result, head("Section Three"))["body"])
        self.assertIn("## Section Two\nREPLACED ENTIRELY", result)

    def test_opts_forwarded_to_collect_section(self):
        content = "## P\nP body\n### C\nC body\n"
        result = with_section(content, "P", lambda b: b + " EDITED", {"levelBounded": False})
        self.assertEqual("## P\nP body EDITED\n### C\nC body\n", result)

    def anchored(self, k):
        pattern = re.compile(rf"^Phase\s+{k}(?=[\s:(]|$)", re.I)
        return lambda h: pattern.search(h["text"]) is not None

    def test_sibling_isolation_property(self):
        rng = random.Random(2143)
        for _ in range(150):
            n = rng.randint(2, 6)
            bodies = ["".join(rng.choice("abc XYZ019") for _ in range(rng.randint(1, 30))).strip() or "x" for _ in range(n)]
            decoys = [rng.choice([None, rng.randint(1, 6)]) for _ in range(n)]
            lines = []
            for k in range(1, n + 1):
                decoy = decoys[k - 1]
                heading = f"Phase {k}: legacy Phase {decoy} notes" if decoy is not None and decoy != k else f"Phase {k}"
                lines += [f"## {heading}", f"body-{k}: {bodies[k - 1]}"]
            doc = "\n".join(lines) + "\n"
            target = rng.randint(1, n)
            before = [collect_section(doc, self.anchored(k))["body"] for k in range(1, n + 1)]
            result = with_section(doc, self.anchored(target), lambda b: b + " EDITED")
            for k in range(1, n + 1):
                body = collect_section(result, self.anchored(k))["body"]
                self.assertEqual(before[k - 1] + " EDITED" if k == target else before[k - 1], body)

    def test_mixed_heading_levels_and_title_collision(self):
        content = "\n".join(["### Phase 3: Migrate off Phase 1 pipeline", "gamma body line", "### Phase 1: Foundation",
                             "alpha body line", "#### Phase 2: API (deeper level, nested syntactically under Phase 1)",
                             "**Plans:** 1 plans"]) + "\n"
        before2 = collect_section(content, self.anchored(2))
        result = with_section(content, self.anchored(1), lambda b: b + " EDITED", {"levelBounded": False})
        self.assertIn("### Phase 3: Migrate off Phase 1 pipeline\ngamma body line", result)
        self.assertNotIn("gamma body line EDITED", result)
        self.assertEqual(before2["body"], collect_section(result, self.anchored(2))["body"])
        self.assertIn("alpha body line EDITED", result)


class DeleteSectionTests(unittest.TestCase):
    def test_noop_cases(self):
        content = "## A\nBody A\n## B\nBody B\n"
        self.assertEqual(content, delete_section(content, head("Nonexistent")))
        self.assertIsNone(delete_section(None, lambda h: True))

    def test_middle_section_leaves_siblings(self):
        content = "\n".join(["### Phase 1: Foundation", "**Goal:** Setup", "", "### Phase 2: Auth", "**Goal:** Authentication",
                             "", "### Phase 3: Features", "**Goal:** Core features", ""])
        result = delete_section(content, lambda h: h["text"].startswith("Phase 2"))
        self.assertEqual("### Phase 1: Foundation\n**Goal:** Setup\n\n### Phase 3: Features\n**Goal:** Core features\n", result)
        self.assertNotIn("\n\n\n", result)

    def test_last_phase_does_not_touch_following_progress(self):
        content = "\n".join(["# Roadmap", "", "### Phase 1: Foundation", "**Goal:** Setup", "", "### Phase 2: Auth",
                             "**Goal:** Authentication", "", "## Progress", "", "| Phase | Plans | Status | Completed |",
                             "|---|---|---|---|", "| 1 | 0/1 | Planned | - |", "| 2 | 0/1 | Planned | - |", ""])
        result = delete_section(content, lambda h: h["text"].startswith("Phase 2"))
        self.assertNotIn("Phase 2:", result)
        self.assertNotIn("Authentication", result)
        for kept in ("## Progress", "| Phase | Plans | Status | Completed |", "| 1 | 0/1 | Planned | - |", "| 2 | 0/1 | Planned | - |"):
            self.assertIn(kept, result)

    def test_nested_subsection_removed_with_parent(self):
        content = "\n".join(["### Phase 2: Auth", "**Goal:** Authentication", "", "#### Phase 2.1: Follow-up",
                             "**Goal:** Nested cleanup", "", "### Phase 3: Features", "**Goal:** Core features", ""])
        result = delete_section(content, lambda h: h["text"].startswith("Phase 2:"))
        self.assertEqual("### Phase 3: Features\n**Goal:** Core features\n", result)

    def test_stop_at_level(self):
        content = "\n".join(["## Parent", "Parent intro", "### Child", "Child body", "## Sibling", "Sibling body"])
        result = delete_section(content, head("Parent"), {"stopAtLevel": 3})
        self.assertEqual("### Child\nChild body\n## Sibling\nSibling body", result)

    def test_level_bounded_false(self):
        content = "\n".join(["## Parent", "Parent intro", "### Child", "Child body", "## Sibling", "Sibling body"])
        result = delete_section(content, head("Parent"), {"levelBounded": False})
        self.assertEqual("### Child\nChild body\n## Sibling\nSibling body", result)

    def test_double_blank_seam_collapsed(self):
        content = "\n".join(["Intro paragraph.", "", "", "### Phase 2: Auth", "**Goal:** Authentication", "",
                             "### Phase 3: Features", "**Goal:** Core features"])
        result = delete_section(content, lambda h: h["text"].startswith("Phase 2"))
        self.assertEqual("Intro paragraph.\n\n### Phase 3: Features\n**Goal:** Core features", result)

    def test_crlf_seam_collapsed_with_crlf(self):
        content = "Intro\r\n\r\n\r\n### A\r\nx\r\n### B\r\ny"
        self.assertEqual("Intro\r\n\r\n### B\r\ny", delete_section(content, head("A")))

    def test_section_at_eof(self):
        self.assertEqual("### Phase 1\nBody 1\n", delete_section("### Phase 1\nBody 1\n### Phase 2\nBody 2", head("Phase 2")))

    def test_explicit_end_offset_bounds_deletion(self):
        content = "\n".join(["### Phase 2", "Body 2", "<details>", "<summary>History</summary>", "#### Archived phase",
                             "Historical body", "</details>", ""])
        boundary = content.index("<details>")
        self.assertEqual(content[boundary:], delete_section(content, head("Phase 2"), {"endOffset": boundary}))

    def test_end_offset_is_clamped_and_never_widens(self):
        content = "### A\nx\n### B\ny\n"
        self.assertEqual("### B\ny\n", delete_section(content, head("A"), {"endOffset": 10_000}))
        self.assertEqual(content, delete_section(content, head("A"), {"endOffset": 0}))
        self.assertEqual(content, delete_section(content, head("A"), {"endOffset": -5}))
        self.assertEqual("### B\ny\n", delete_section(content, head("A"), {"endOffset": float("nan")}))
        self.assertEqual("### B\ny\n", delete_section(content, head("A"), {"endOffset": "5"}))
        self.assertEqual("### B\ny\n", delete_section(content, head("A"), {"endOffset": True}))


class ExtractXmlTagBodiesTests(unittest.TestCase):
    def render(self, tag, body, attrs="", upper=False):
        name = tag.upper() if upper else tag
        return f"<{name}{attrs}>{body}</{name}>"

    def test_tag_name_set(self):
        self.assertEqual(("objective", "tasks", "task", "action", "read_first", "behavior", "verify",
                          "acceptance_criteria", "done"), XML_DECISION_TAG_NAMES)

    def test_flat_run_grouped_by_tag_order(self):
        rng = random.Random(5139)
        alphabet = "abcXYZ019 D-05.:,\n_"
        for _ in range(200):
            pieces = [{"tag": rng.choice(XML_DECISION_TAG_NAMES),
                       "body": "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 12))),
                       "attrs": rng.choice(["", ' id="1"', ' type="auto" n="2"', "\tx=y"]), "upper": rng.random() < 0.5}
                      for _ in range(rng.randint(0, 8))]
            sep = rng.choice(["", " ", "\n", " prose D-01 "])
            text = sep.join(self.render(p["tag"], p["body"], p["attrs"], p["upper"]) for p in pieces)
            expected = "\n".join(p["body"] for name in XML_DECISION_TAG_NAMES for p in pieces if p["tag"] == name)
            self.assertEqual(expected, extract_xml_tag_bodies(text))

    def test_inner_tag_absorbed_and_extracted_on_its_own_pass(self):
        for outer in XML_DECISION_TAG_NAMES:
            for inner in XML_DECISION_TAG_NAMES:
                if outer == inner:
                    continue
                outer_body = f"prefix D-05 <{inner}>innerbody</{inner}>"
                text = f"<{outer}>{outer_body}</{outer}>"
                ordered = sorted([(XML_DECISION_TAG_NAMES.index(outer), outer_body), (XML_DECISION_TAG_NAMES.index(inner), "innerbody")])
                self.assertEqual("\n".join(b for _, b in ordered), extract_xml_tag_bodies(text), (outer, inner))

    def test_text_without_scanned_element_is_empty(self):
        self.assertEqual("", extract_xml_tag_bodies("abc<other>def</other>"))
        self.assertEqual("", extract_xml_tag_bodies(""))

    def test_empty_bodies_are_dropped(self):
        self.assertEqual("x", extract_xml_tag_bodies("<task></task><done>x</done>"))

    def test_outer_prefix_prose_is_kept(self):
        text = "<action>per D-05 <verify>npm test</verify></action>"
        self.assertEqual("per D-05 <verify>npm test</verify>\nnpm test", extract_xml_tag_bodies(text))


if __name__ == "__main__":
    unittest.main()
