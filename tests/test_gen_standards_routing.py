"""Generated standards routing tables: routing.json is the source; index regions are derived."""
import copy
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"engineer/bin"))
from lib import gen_standards_routing as gen, standards  # noqa: E402


def entries(data):
    return [entry for domain in data["domains"] for group in domain["groups"] for entry in group["entries"]]


class CommittedTables(unittest.TestCase):
    def test_committed_index_regions_are_current(self):
        self.assertEqual(0, gen.main(["--check", "--root", str(ROOT)]))

    def test_every_index_table_row_is_a_catalog_entry(self):
        # A row outside a generated region, or a dropped entry, would make these differ.
        rows = sum(len(re.findall(r"^\| `", path.read_text(encoding="utf-8"), re.M))
                   for path in (ROOT/"engineer/standards").glob("*/index.md"))
        self.assertEqual(len(standards.catalog()), rows)

    def test_routing_json_is_valid(self):
        self.assertEqual([], standards.validate_routing(standards.load_routing(ROOT), ROOT))


class GeneratorBehavior(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT/"engineer/standards", self.root/"engineer/standards")
        self.routing = self.root/standards.ROUTING
        self.data = json.loads(self.routing.read_text(encoding="utf-8"))

    def save(self, data):
        self.routing.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def test_write_regenerates_only_marked_regions(self):
        index = self.root/"engineer/standards/sql/index.md"
        before = index.read_text(encoding="utf-8")
        data = copy.deepcopy(self.data)
        sql = next(d for d in data["domains"] if d["domain"] == "sql")
        sql["groups"][0]["entries"][0]["concern"] = "ORM model foundations"
        self.save(data)
        self.assertEqual(1, gen.main(["--check", "--root", str(self.root)]))
        self.assertEqual(0, gen.main(["--write", "--root", str(self.root)]))
        self.assertEqual(0, gen.main(["--check", "--root", str(self.root)]))
        after = index.read_text(encoding="utf-8")
        self.assertIn("ORM model foundations", after)
        outside = lambda text: re.sub(r"<!-- STANDARDS-ROUTING:START.*?END:[\w-]+ -->", "", text, flags=re.S)
        self.assertEqual(outside(before), outside(after))

    def test_missing_markers_fail(self):
        index = self.root/"engineer/standards/api/index.md"
        index.write_text(re.sub(r"<!-- STANDARDS-ROUTING:END:routes -->\n", "", index.read_text(encoding="utf-8")), encoding="utf-8")
        self.assertEqual(1, gen.main(["--check", "--root", str(self.root)]))

    def test_validation_rejects_inconsistent_entries(self):
        cases = {
            "duplicate ID": None,
            "menu must start": lambda d: entries(d)[0].update(section="99"),
            "includes must match": lambda d: entries(d)[0].update(includes=["1"]),
            "does not exist": lambda d: entries(d)[0].update(path="engineer/standards/python/missing.md"),
            "exactly one of section or whole": lambda d: entries(d)[0].update(whole=True),
            "targets unknown ID": lambda d: d["aliases"].update({"python.old": "python.nope"}),
            "must not contain '|'": lambda d: entries(d)[0].update(concern="a | b"),
            "duplicate region": lambda d: d["domains"][2]["groups"][1].update(region=d["domains"][2]["groups"][0]["region"]),
            "exactly prefix, path and section": lambda d: d["domains"][2]["prefix_includes"][0].pop("section"),
            "matches no entry": lambda d: d["domains"][2]["prefix_includes"][0].update(prefix="nomatch"),
            "sorted by name": lambda d: d["domains"].reverse(),
            "each group needs": lambda d: d["domains"][0]["groups"][0].pop("entries"),
        }
        for expected, mutate in cases.items():
            with self.subTest(expected):
                data = copy.deepcopy(self.data)
                if expected == "duplicate ID":
                    group = data["domains"][0]["groups"][0]
                    group["entries"].append(dict(group["entries"][0]))
                else:
                    mutate(data)
                findings = standards.validate_routing(data, self.root)
                self.assertTrue(any(expected in finding for finding in findings), findings)


class GeneratorCommandLine(unittest.TestCase):
    def test_invalid_arguments_exit_2(self):
        for argv in (["--root"], ["--root", "--check"], ["--write", "--check"], ["--bogus"]):
            with self.subTest(argv=argv):
                self.assertEqual(2, gen.main(argv))

    def test_unknown_region_marker_fails_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT/"engineer/standards", root/"engineer/standards")
            index = root/"engineer/standards/sql/index.md"
            index.write_text(index.read_text(encoding="utf-8") + f"\n{gen.start_marker('orphan')}\n{gen.end_marker('orphan')}\n", encoding="utf-8")
            self.assertEqual(1, gen.main(["--check", "--root", str(root)]))


class Aliases(unittest.TestCase):
    def test_renamed_id_still_resolves(self):
        original = standards.load_routing
        def with_alias(root=None):
            data = original(root)
            data["aliases"] = {"python.errors.preserve-context": "python.errors.chaining"}
            return data
        standards.load_routing = with_alias
        self.addCleanup(setattr, standards, "load_routing", original)
        blocks = standards.resolve(["python.errors.preserve-context"])
        self.assertIn("### 3.1 ", blocks[0]["text"])


if __name__ == "__main__":
    unittest.main()
