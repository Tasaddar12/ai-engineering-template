from __future__ import annotations

import copy
import hashlib
import sys
import unittest
import unicodedata
from dataclasses import FrozenInstanceError, replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import install
from assets import (
    AssetCatalog,
    AssetOwnership,
    OwnedAsset,
    ProviderRoot,
    build_owned_asset_catalog,
    verify_asset_manifest,
)
from contracts import load_contract_registry
from domain_values import DomainException, ErrorCategory


class OwnedAssetCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_contract_registry(ROOT / "schemas" / "v1")
        cls.codex = build_owned_asset_catalog(
            ROOT,
            ProviderRoot.CODEX,
            registry=cls.registry,
        )

    def test_catalog_is_deterministic_complete_and_schema_valid(self) -> None:
        repeated = build_owned_asset_catalog(ROOT, ".codex", registry=self.registry)
        self.assertEqual(repeated, self.codex)
        self.assertEqual(
            [asset.path.as_wire() for asset in self.codex.assets],
            sorted(asset.path.as_wire() for asset in self.codex.assets),
        )
        self.registry.validate(self.codex.manifest_record, source="test manifest")
        self.registry.validate(self.codex.installation_record, source="test installation")
        verify_asset_manifest(self.codex.manifest_record, self.codex, self.registry)

        expected_documents = {
            path.relative_to(ROOT).as_posix()
            for tree in ("agents", "templates", "workflows")
            for path in (ROOT / "docs" / tree).rglob("*")
            if path.is_file()
        }
        catalog_documents = {
            asset.source_ref.as_wire()
            for asset in self.codex.framework_assets
            if asset.source_ref.as_wire().startswith(
                ("docs/agents/", "docs/templates/", "docs/workflows/")
            )
        }
        self.assertEqual(catalog_documents, expected_documents)
        self.assertIn("docs/agents/README.md", catalog_documents)
        self.assertEqual(
            {
                asset.source_ref.as_wire()
                for asset in self.codex.framework_assets
                if asset.source_ref.as_wire().startswith("schemas/v1/")
            },
            {
                path.relative_to(ROOT).as_posix()
                for path in (ROOT / "schemas" / "v1").glob("*.schema.json")
            },
        )

    def test_every_manifest_hash_is_recomputed_from_exact_payload_bytes(self) -> None:
        entries = {
            entry["path"]: entry
            for entry in self.codex.manifest_record["assets"]
        }
        self.assertEqual(set(entries), {asset.path.as_wire() for asset in self.codex.assets})
        for asset in self.codex.assets:
            with self.subTest(path=asset.path.as_wire()):
                actual = hashlib.sha256(asset.content).hexdigest()
                self.assertEqual(str(asset.sha256), actual)
                self.assertEqual(entries[asset.path.as_wire()]["sha256"], actual)
                self.assertEqual(
                    entries[asset.path.as_wire()]["source_ref"],
                    asset.source_ref.as_wire(),
                )

    def test_catalog_matches_current_framework_payload_and_reachable_tool_closure(self) -> None:
        for assistant, root in (
            ("codex", ProviderRoot.CODEX),
            ("claude", ProviderRoot.CLAUDE),
        ):
            with self.subTest(assistant=assistant):
                catalog = (
                    self.codex
                    if root is ProviderRoot.CODEX
                    else build_owned_asset_catalog(ROOT, root, registry=self.registry)
                )
                managed, seed, namespace, _ = install._planned_payload(
                    ROOT, ROOT / "synthetic", assistant
                )
                manifest_path = f"{namespace}/framework/manifest.json"
                expected_managed = {
                    path: content
                    for path, content in managed.items()
                    if path != manifest_path
                }
                actual_managed = {
                    asset.path.as_wire(): asset.content
                    for asset in catalog.framework_assets
                }
                self.assertEqual(actual_managed, expected_managed)
                self.assertEqual(
                    {asset.path.as_wire() for asset in catalog.seed_assets},
                    set(seed),
                )
        self.assertFalse(
            any(asset.source_ref.as_wire().startswith(".ai/") for asset in self.codex.assets)
        )
        self.assertFalse(
            any(
                asset.source_ref.as_wire().startswith("schemas/examples/")
                for asset in self.codex.assets
            )
        )

        tool_names = {
            Path(asset.path.as_wire()).name
            for asset in self.codex.framework_assets
            if asset.path.as_wire().startswith(".codex/tools/")
        }
        self.assertEqual(
            tool_names,
            {"ai.py", "contracts.py", "domain_values.py", "validate_foundation.py"},
        )
        self.assertNotIn("assets.py", tool_names)
        self.assertNotIn("workflow_ports.py", tool_names)
        self.assertNotIn("install.py", tool_names)

    def test_provider_roots_render_self_contained_records_and_preserve_legacy_ai(self) -> None:
        for root in ProviderRoot:
            with self.subTest(provider_root=root.value):
                catalog = build_owned_asset_catalog(ROOT, root, registry=self.registry)
                prefix = root.value + "/"
                self.assertTrue(
                    all(asset.path.as_wire().startswith(prefix) for asset in catalog.assets)
                )
                installation = catalog.installation_record.to_dict()
                self.assertEqual(
                    installation["manifest_ref"],
                    f"{root.value}/framework/manifest.json",
                )
                ownership_roots = (
                    installation["owned_roots"] + installation["project_owned_roots"]
                )
                self.assertTrue(all(path.startswith(prefix) for path in ownership_roots))
                entry_name = "CLAUDE.md" if root is ProviderRoot.CLAUDE else "AGENTS.md"
                entry = catalog.asset(f"{root.value}/{entry_name}")
                self.assertEqual(entry.ownership, AssetOwnership.SEED_ONLY)
                self.assertIn(f"{root.value}/{entry_name}", entry.content.decode("utf-8"))
                verify_asset_manifest(catalog.manifest_record, catalog, self.registry)

    def test_seed_only_assets_become_project_owned_after_instantiation(self) -> None:
        expected_seeds = {
            ".codex/README.md",
            ".codex/AGENTS.md",
            ".codex/STATE.json",
            ".codex/project/policy.json",
            ".codex/project/agent-models.json",
            ".codex/decisions/index.json",
            ".codex/plans/current/.gitkeep",
            ".codex/plans/completed/.gitkeep",
            ".codex/plans/archived/.gitkeep",
            ".codex/research/.gitkeep",
        }
        self.assertEqual(
            {asset.path.as_wire() for asset in self.codex.seed_assets},
            expected_seeds,
        )
        entries = {
            entry["path"]: entry for entry in self.codex.manifest_record["assets"]
        }
        for asset in self.codex.seed_assets:
            with self.subTest(path=asset.path.as_wire()):
                self.assertFalse(asset.is_framework_managed)
                self.assertEqual(entries[asset.path.as_wire()]["ownership"], "seed_only")
        self.assertTrue(
            self.codex.asset(".codex/framework.json").is_framework_managed
        )
        self.assertIn(
            ".codex/framework.json",
            self.codex.installation_record["owned_roots"],
        )

    def test_catalog_and_records_detach_mutable_inputs(self) -> None:
        source = self.codex.assets[0]
        mutable_installation = self.codex.installation_record.to_dict()
        mutable_installation["owned_roots"].append(".codex/mutated/")
        catalog = AssetCatalog(
            framework_version=self.codex.framework_version,
            provider_root=self.codex.provider_root,
            assets=[source],
            installation_record=mutable_installation,
        )
        mutable_installation["owned_roots"].append(".codex/later/")
        self.assertNotIn(".codex/later/", catalog.installation_record["owned_roots"])
        with self.assertRaises(FrozenInstanceError):
            source.content = b"changed"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            catalog.manifest_record["new"] = "value"  # type: ignore[index]

    def test_tampered_hash_or_payload_is_rejected(self) -> None:
        manifest = self.codex.manifest_record.to_dict()
        original_hash = manifest["assets"][0]["sha256"]
        manifest["assets"][0]["sha256"] = (
            "0" * 64 if original_hash != "0" * 64 else "1" * 64
        )
        with self.assertRaises(DomainException) as caught:
            verify_asset_manifest(manifest, self.codex, self.registry)
        self.assertEqual(caught.exception.category, ErrorCategory.VALIDATION_FAILED)
        self.assertIn("hash mismatch", str(caught.exception))

        first = self.codex.assets[0]
        tampered_asset = OwnedAsset(
            path=first.path,
            source_ref=first.source_ref,
            ownership=first.ownership,
            content=first.content + b"tampered",
        )
        tampered_catalog = replace(
            self.codex,
            assets=(tampered_asset,) + self.codex.assets[1:],
        )
        with self.assertRaisesRegex(DomainException, "hash mismatch"):
            verify_asset_manifest(
                self.codex.manifest_record,
                tampered_catalog,
                self.registry,
            )

    def test_duplicate_case_unicode_and_ancestor_aliases_are_rejected(self) -> None:
        original = self.codex.manifest_record.to_dict()
        first = copy.deepcopy(original["assets"][0])
        duplicate_cases = {
            "exact": first["path"],
            "case": first["path"].upper(),
            "unicode-composed": ".codex/templates/caf\N{LATIN SMALL LETTER E WITH ACUTE}.md",
        }
        for label, path in duplicate_cases.items():
            with self.subTest(label=label):
                manifest = copy.deepcopy(original)
                entry = copy.deepcopy(first)
                entry["path"] = path
                manifest["assets"].append(entry)
                if label == "unicode-composed":
                    alias = copy.deepcopy(first)
                    alias["path"] = unicodedata.normalize("NFD", path)
                    manifest["assets"].append(alias)
                with self.assertRaises(DomainException) as caught:
                    verify_asset_manifest(manifest, self.codex, self.registry)
                self.assertEqual(caught.exception.category, ErrorCategory.INVALID_INPUT)
                self.assertIn("duplicate or aliased", str(caught.exception))

        ancestor = copy.deepcopy(original)
        entry = copy.deepcopy(first)
        entry["path"] = ".codex/tools"
        ancestor["assets"].append(entry)
        with self.assertRaisesRegex(DomainException, "ancestor collision"):
            verify_asset_manifest(ancestor, self.codex, self.registry)

    def test_escaping_and_nonportable_manifest_paths_are_rejected(self) -> None:
        invalid_paths = (
            "../outside.txt",
            "/absolute.txt",
            "C:/outside.txt",
            ".codex/../outside.txt",
            ".claude/tools/ai.py",
            ".codex/tools/CON",
            ".codex/tools/bad\N{FULLWIDTH COLON}stream.py",
        )
        original = self.codex.manifest_record.to_dict()
        for invalid in invalid_paths:
            with self.subTest(path=invalid):
                manifest = copy.deepcopy(original)
                manifest["assets"][0]["path"] = invalid
                with self.assertRaises(DomainException) as caught:
                    verify_asset_manifest(manifest, self.codex, self.registry)
                self.assertEqual(caught.exception.category, ErrorCategory.INVALID_INPUT)

    def test_unknown_root_and_nonexistent_source_fail_closed(self) -> None:
        with self.assertRaises(DomainException) as caught:
            build_owned_asset_catalog(ROOT, ".unknown", registry=self.registry)
        self.assertEqual(caught.exception.category, ErrorCategory.INVALID_INPUT)
        with self.assertRaises(DomainException):
            build_owned_asset_catalog(ROOT / "missing", registry=self.registry)


if __name__ == "__main__":
    unittest.main()
