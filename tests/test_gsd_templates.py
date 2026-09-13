"""Completeness, losslessness, and reference closure of the pinned GSD import."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("import_gsd_templates", ROOT / "tools/import_gsd_templates.py")
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)

EXPECTED_TEMPLATES = {
    "AI-SPEC.md", "DEBUG.md", "README.md", "SECURITY.md", "UAT.md", "UI-SPEC.md", "VALIDATION.md",
    "codebase/architecture.md", "codebase/stack.md", "config.json", "context.md", "continue-here.md",
    "copilot-instructions.md", "dev-preferences.md", "discussion-log.md", "milestone-archive.md",
    "milestone.md", "phase-prompt.md", "planner-subagent-prompt.md", "project.md", "requirements.md",
    "research-project/ARCHITECTURE.md", "research-project/FEATURES.md", "research-project/PITFALLS.md",
    "research-project/STACK.md", "research-project/SUMMARY.md", "research.md", "retrospective.md",
    "roadmap.md", "spec.md", "state.md", "summary-complex.md", "summary-minimal.md",
    "summary-standard.md", "summary.compact.md", "summary.md", "user-profile.md",
    "user-setup.compact.md", "user-setup.md", "verification-report.md",
}


def canonical_bytes(path: Path) -> bytes:
    # Git may materialize CRLF on Windows; provenance identifies Git blob bytes.
    return path.read_bytes().replace(b"\r\n", b"\n")


def restore_original(entry, imported: bytes) -> bytes:
    if not entry["local_note_appended"]:
        return imported
    text = imported.decode()
    if not text.endswith(IMPORTER.NOTE):
        raise AssertionError("Missing or changed additive local note")
    text = text[:-len(IMPORTER.NOTE)]
    edits = sorted(
        (offset, edit["original"], edit["replacement"])
        for edit in entry["reference_substitutions"]
        for offset in edit["offsets"]
    )
    chunks = []
    delta = 0
    cursor = 0
    for offset, original, replacement in edits:
        start = offset + delta
        if text[start:start + len(replacement)] != replacement:
            raise AssertionError(f"Reference edit no longer matches at {offset}: {original}")
        chunks.extend((text[cursor:start], original))
        cursor = start + len(replacement)
        delta += len(replacement) - len(original)
    chunks.append(text[cursor:])
    restored = "".join(chunks)
    for edit in reversed(entry["conflict_adaptations"]):
        if restored.count(edit["replacement"]) != edit["count"]:
            raise AssertionError("Conflict correction no longer uniquely reversible")
        restored = restored.replace(edit["replacement"], edit["original"])
    return restored.encode()


class GsdTemplateImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / ".ai/gsd/PROVENANCE.json").read_text(encoding="utf-8"))
        cls.references = json.loads((ROOT / ".ai/gsd/REFERENCES.json").read_text(encoding="utf-8"))

    def test_all_templates_and_support_trees_present(self):
        self.assertEqual(self.manifest["revision"], "c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977")
        counts = {"gsd-core/templates": 40, "agents": 64, "commands": 72,
                  "gsd-core/references": 131, "gsd-core/workflows": 177, "gsd-core/contexts": 3}
        self.assertEqual(self.manifest["source_tree_counts"], counts)
        sources = [entry["source"] for entry in self.manifest["files"]]
        destinations = [entry["destination"] for entry in self.manifest["files"]]
        self.assertEqual(len(sources), 487)
        self.assertEqual(len(set(sources)), 487)
        self.assertEqual(len(set(destinations)), 487)
        for prefix, count in counts.items():
            self.assertEqual(sum(source.startswith(prefix + "/") for source in sources), count)
        actual = {source.removeprefix("gsd-core/templates/") for source in sources if source.startswith("gsd-core/templates/")}
        self.assertEqual(actual, EXPECTED_TEMPLATES)
        on_disk = {path.relative_to(ROOT / ".ai/templates").as_posix() for path in (ROOT / ".ai/templates").rglob("*") if path.is_file()}
        self.assertTrue(EXPECTED_TEMPLATES <= on_disk)
        self.assertFalse(on_disk - EXPECTED_TEMPLATES - {"ADR.md", "CURRENT-SPEC.md"}, "Stale or unaudited template")

    def test_every_imported_body_reconstructs_exact_upstream_blob(self):
        for entry in self.manifest["files"]:
            with self.subTest(path=entry["destination"]):
                content = canonical_bytes(ROOT / entry["destination"])
                self.assertEqual(hashlib.sha256(content).hexdigest(), entry["destination_sha256"])
                original = restore_original(entry, content)
                self.assertEqual(len(original), entry["source_bytes"])
                self.assertEqual(hashlib.sha256(original).hexdigest(), entry["source_sha256"])

    def test_license_preserved(self):
        content = canonical_bytes(ROOT / ".ai/gsd/LICENSE")
        self.assertEqual(hashlib.sha256(content).hexdigest(), self.manifest["license"]["source_sha256"])
        self.assertIn(b"MIT", content)
        self.assertIn(b"Open GSD", content)

    def test_reference_substitutions_resolve_actual_local_methods_or_pinned_sources(self):
        for entry in self.manifest["files"]:
            for edit in entry["reference_substitutions"]:
                target = edit["replacement"]
                with self.subTest(source=entry["source"], reference=edit["original"]):
                    self.assertEqual(edit["count"], len(edit["offsets"]))
                    if target.startswith(".ai/"):
                        self.assertTrue((ROOT / target).is_dir() if target.endswith("/") else (ROOT / target).is_file(), target)
                    else:
                        self.assertTrue(target.startswith(IMPORTER.SOURCE_URL), target)
        for reference in self.references["references"]:
            with self.subTest(reference=reference):
                self.assertTrue(reference["source_url"].startswith(IMPORTER.SOURCE_URL))
                if reference["kind"] == "local-guidance":
                    self.assertTrue((ROOT / reference["destination"]).is_file())
                else:
                    self.assertEqual(reference["kind"], "upstream-source-only")
                    self.assertIn("not installed", reference["boundary"])

    def test_no_unresolved_real_core_method_references(self):
        for reference in self.references["unresolved_or_examples"]:
            path = reference["reference"]
            if re.match(r"(?:gsd-core/)?(?:templates|references|workflows|contexts|agents|commands)/", path):
                # This is explicitly an illustrative input/output in a few-shot
                # example. It is not a required backing workflow in that source.
                self.assertIn(path, {"gsd-core/workflows/context-bridge.md", "commands/gsd/misc.md"})
                self.assertEqual(reference["in"], ".ai/gsd/references/few-shot-examples/verifier.md")
        for symbol, destination in self.references["command_definitions"].items():
            self.assertTrue(symbol.startswith("/gsd:"))
            self.assertTrue((ROOT / destination).is_file())
        self.assertEqual(len(self.references["command_definitions"]), 72)

    def test_import_does_not_install_upstream_runtime_or_reinterpret_json_config(self):
        config = next(entry for entry in self.manifest["files"] if entry["source"] == "gsd-core/templates/config.json")
        self.assertEqual(config["source_sha256"], config["destination_sha256"])
        self.assertFalse(config["local_note_appended"])
        self.assertFalse((ROOT / ".ai/gsd/bin").exists())
        self.assertFalse((ROOT / ".ai/gsd/hooks").exists())

    def test_truncated_content_cannot_pass_losslessness_check(self):
        entry = next(entry for entry in self.manifest["files"] if entry["source"] == "gsd-core/templates/project.md")
        content = canonical_bytes(ROOT / entry["destination"])
        truncated = content.replace(b"# PROJECT.md Template", b"# Project", 1)
        self.assertNotEqual(truncated, content)
        try:
            restored = restore_original(entry, truncated)
        except AssertionError:
            return
        self.assertNotEqual(hashlib.sha256(restored).hexdigest(), entry["source_sha256"])


if __name__ == "__main__":
    unittest.main()
