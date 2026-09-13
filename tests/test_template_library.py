"""Completeness, losslessness, and reference closure of the pinned GSD import."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("import_templates", ROOT / "tools/import_templates.py")
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
    text = imported.decode()
    if entry["local_note_appended"]:
        if not text.endswith(IMPORTER.NOTE):
            raise AssertionError("Missing or changed additive local note")
        text = text[:-len(IMPORTER.NOTE)]
    for stage in reversed(entry["namespace_stages"]):
        text = undo_edits(text, stage)
    text = undo_edits(text, entry["reference_substitutions"])
    restored = undo_edits(text, entry["markdown_substitutions"])
    for edit in reversed(entry["conflict_adaptations"]):
        if restored.count(edit["replacement"]) != edit["count"]:
            raise AssertionError("Conflict correction no longer uniquely reversible")
        restored = restored.replace(edit["replacement"], edit["original"])
    return restored.encode()


def undo_edits(text, substitutions):
    edits = sorted(
        (offset, edit["original"], edit["replacement"])
        for edit in substitutions
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
    return "".join(chunks)


class TemplateLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / ".ai/library/PROVENANCE.json").read_text(encoding="utf-8"))
        cls.references = json.loads((ROOT / ".ai/library/REFERENCES.json").read_text(encoding="utf-8"))

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
        content = canonical_bytes(ROOT / ".ai/library/LICENSE")
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
                self.assertEqual(reference["in"], ".ai/library/references/few-shot-examples/verifier.md")
        for symbol, destination in self.references["command_definitions"].items():
            self.assertTrue(symbol.startswith("/workflow:"))
            self.assertTrue((ROOT / destination).is_file())
        self.assertEqual(len(self.references["command_definitions"]), 72)

    def test_import_does_not_install_upstream_runtime_or_reinterpret_json_config(self):
        config = next(entry for entry in self.manifest["files"] if entry["source"] == "gsd-core/templates/config.json")
        self.assertEqual(config["source_sha256"], config["destination_sha256"])
        self.assertFalse(config["local_note_appended"])
        self.assertFalse((ROOT / ".ai/library/bin").exists())
        self.assertFalse((ROOT / ".ai/library/hooks").exists())

    def test_active_bodies_have_only_the_local_namespace(self):
        for directory in ("agents", "commands", "references", "workflows", "contexts"):
            actual = {path.relative_to(ROOT).as_posix() for path in (ROOT / ".ai/library" / directory).rglob("*") if path.is_file()}
            expected = {entry["destination"] for entry in self.manifest["files"] if entry["destination"].startswith(f".ai/library/{directory}/")}
            self.assertEqual(actual, expected, "Stale or unaudited library file")
        for entry in self.manifest["files"]:
            with self.subTest(path=entry["destination"]):
                content = canonical_bytes(ROOT / entry["destination"]).decode()
                self.assertIsNone(re.search("gsd", content, re.IGNORECASE))
                self.assertNotIn(".ai/library/commands/workflow/", content)
                self.assertNotIn(".ai/library/agents/workflow-", content)
        self.assertIsNone(re.search("gsd", (ROOT / ".ai/library/README.md").read_text(encoding="utf-8"), re.IGNORECASE))

    def test_real_markdown_links_resolve_including_source_catalog_fragments(self):
        examples = {
            (".ai/templates/state.md", "path"),
            (".ai/library/agents/doc-writer.md", "CODE_OF_CONDUCT.md"),
            (".ai/templates/summary.md", "./{phase}-USER-SETUP.md"),
            (".ai/templates/summary.compact.md", "./{phase}-USER-SETUP.md"),
            (".ai/library/workflows/quick.md", "./quick/${quick_id}-${slug}/"),
        }
        for entry in self.manifest["files"]:
            if not entry["destination"].endswith(".md"):
                continue
            path = ROOT / entry["destination"]
            for target in re.findall(r"\]\(([^\s)]+)\)", path.read_text(encoding="utf-8")):
                if target.startswith(("http:", "https:", "mailto:", "#")) or (entry["destination"], target) in examples:
                    continue
                file_name, _, fragment = target.partition("#")
                resolved = (ROOT if file_name.startswith(".ai/") else path.parent) / unquote(file_name)
                with self.subTest(path=entry["destination"], target=target):
                    self.assertTrue(resolved.exists(), str(resolved))
                    if resolved.name == "SOURCES.md":
                        self.assertIn(f'id="{fragment}"', resolved.read_text(encoding="utf-8"))

    def test_workflow_step_manifest_references_actual_local_files(self):
        sections = json.loads((ROOT / ".ai/library/workflows/section-manifest.json").read_text(encoding="utf-8"))
        for workflow, steps in sections["workflows"].items():
            for step in steps:
                with self.subTest(workflow=workflow, step=step["id"]):
                    self.assertTrue((ROOT / step["read"]).is_file(), step["read"])

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
