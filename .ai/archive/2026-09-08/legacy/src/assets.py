"""Deterministic catalog of framework assets and project-owned seeds.

The catalog describes the bytes shipped by this source tree.  It performs no
installation or upgrade writes; later workflow services consume the immutable
catalog after its manifest has passed the closed v1 contract registry.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from contracts import ContractRegistry, load_contract_registry
from domain_values import (
    DomainError,
    DomainException,
    ErrorCategory,
    FrozenJsonObject,
    ScopePath,
    ScopePathKind,
    Sha256Digest,
)


SCHEMA_VERSION = "1.0"
PRODUCT_TREES = ("agents", "templates", "workflows")
TEXT_SUFFIXES = frozenset({".json", ".md", ".py", ".txt"})
TOOL_ENTRYPOINTS = ("ai.py", "validate_foundation.py")
REQUIRED_TOOL_MODULES = ("ai.py", "contracts.py", "domain_values.py", "validate_foundation.py")
PROVIDER_TOKEN = "{{PROVIDER_NOTE}}"
_EXCLUDED_SOURCE_DIRECTORIES = frozenset(
    {".git", ".worktrees", ".venv", "generated", "__pycache__"}
)
_GENERATED_EMPTY_SOURCE = "generated/empty-file"


class ProviderRoot(StrEnum):
    """Supported portable record roots, including the source repository legacy root."""

    CODEX = ".codex"
    CLAUDE = ".claude"
    LEGACY_AI = ".ai"

    @property
    def entry_name(self) -> str:
        return "CLAUDE.md" if self is ProviderRoot.CLAUDE else "AGENTS.md"


class AssetOwnership(StrEnum):
    """Manifest ownership before and after a seed is instantiated."""

    FRAMEWORK = "framework"
    SEED_ONLY = "seed_only"


def _failure(
    category: ErrorCategory,
    message: str,
    *,
    details: Mapping[str, object] | None = None,
) -> DomainException:
    return DomainException(
        DomainError(
            category=category,
            message=message,
            retryable=False,
            details={} if details is None else details,
        )
    )


def _digest(content: bytes) -> Sha256Digest:
    return Sha256Digest(hashlib.sha256(content).hexdigest())


def _exact_path(value: ScopePath | str, label: str) -> ScopePath:
    try:
        path = value if isinstance(value, ScopePath) else ScopePath.exact_file(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {label}: {exc}") from exc
    if path.kind is not ScopePathKind.EXACT_FILE:
        raise ValueError(f"{label} must identify an exact file")
    return path


@dataclass(frozen=True, slots=True)
class OwnedAsset:
    """One immutable destination payload and its source provenance."""

    path: ScopePath
    source_ref: ScopePath
    ownership: AssetOwnership
    content: bytes = field(repr=False, compare=True)
    sha256: Sha256Digest = field(init=False)

    def __post_init__(self) -> None:
        path = _exact_path(self.path, "asset path")
        source_ref = _exact_path(self.source_ref, "asset source_ref")
        try:
            ownership = AssetOwnership(self.ownership)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid asset ownership: {self.ownership!r}") from exc
        if not isinstance(self.content, bytes):
            raise TypeError("asset content must be bytes")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "source_ref", source_ref)
        object.__setattr__(self, "ownership", ownership)
        object.__setattr__(self, "sha256", _digest(self.content))

    @property
    def is_framework_managed(self) -> bool:
        """Whether upgrade logic may treat the instantiated path as framework-owned."""

        return self.ownership is AssetOwnership.FRAMEWORK

    def manifest_entry(self) -> dict[str, str]:
        return {
            "path": self.path.as_wire(),
            "sha256": str(self.sha256),
            "ownership": self.ownership.value,
            "source_ref": self.source_ref.as_wire(),
        }


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and have no surrounding whitespace")
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value):
        raise ValueError(f"{label} contains a control or invisible formatting character")
    return unicodedata.normalize("NFC", value)


def _migration_ids(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError("migration_ids must be an iterable of strings")
    result = tuple(_text(value, "migration ID") for value in values)
    aliases: set[str] = set()
    for value in result:
        alias = unicodedata.normalize("NFKC", value).casefold()
        if alias in aliases:
            raise ValueError(f"duplicate or aliased migration ID: {value!r}")
        aliases.add(alias)
    return result


def _validate_asset_paths(assets: Sequence[OwnedAsset], provider_root: ProviderRoot) -> None:
    root = ScopePath.directory(provider_root.value)
    seen: set[tuple[str, ...]] = set()
    accepted: list[ScopePath] = []
    for asset in assets:
        if not root.contains(asset.path):
            raise ValueError(
                f"asset path escapes provider root {provider_root.value}: {asset.path}"
            )
        if asset.path.comparison_key in seen:
            raise ValueError(f"duplicate or aliased asset path: {asset.path}")
        for prior in accepted:
            if prior.overlaps(asset.path):
                raise ValueError(
                    f"asset paths have an ancestor collision: {prior} and {asset.path}"
                )
        seen.add(asset.path.comparison_key)
        accepted.append(asset.path)


@dataclass(frozen=True, slots=True)
class AssetCatalog:
    """A canonical provider-specific payload with no installation side effects."""

    framework_version: str
    provider_root: ProviderRoot
    assets: tuple[OwnedAsset, ...]
    installation_record: FrozenJsonObject
    migration_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        version = _text(self.framework_version, "framework version")
        try:
            provider_root = ProviderRoot(self.provider_root)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"unsupported provider root: {self.provider_root!r}") from exc
        if isinstance(self.assets, (str, bytes, bytearray)):
            raise TypeError("assets must be an iterable of OwnedAsset values")
        assets = tuple(self.assets)
        if not assets:
            raise ValueError("asset catalog cannot be empty")
        if not all(isinstance(asset, OwnedAsset) for asset in assets):
            raise TypeError("assets must contain only OwnedAsset values")
        assets = tuple(sorted(assets, key=lambda asset: asset.path.as_wire()))
        _validate_asset_paths(assets, provider_root)
        installation = (
            self.installation_record
            if isinstance(self.installation_record, FrozenJsonObject)
            else FrozenJsonObject(self.installation_record)
        )
        migrations = _migration_ids(self.migration_ids)
        object.__setattr__(self, "framework_version", version)
        object.__setattr__(self, "provider_root", provider_root)
        object.__setattr__(self, "assets", assets)
        object.__setattr__(self, "installation_record", installation)
        object.__setattr__(self, "migration_ids", migrations)

    @property
    def framework_assets(self) -> tuple[OwnedAsset, ...]:
        return tuple(asset for asset in self.assets if asset.is_framework_managed)

    @property
    def seed_assets(self) -> tuple[OwnedAsset, ...]:
        return tuple(asset for asset in self.assets if not asset.is_framework_managed)

    @property
    def manifest_path(self) -> ScopePath:
        return ScopePath.exact_file(f"{self.provider_root.value}/framework/manifest.json")

    @property
    def manifest_record(self) -> FrozenJsonObject:
        return FrozenJsonObject(
            {
                "schema_version": SCHEMA_VERSION,
                "kind": "asset-manifest",
                "framework_version": self.framework_version,
                "assets": [asset.manifest_entry() for asset in self.assets],
                "migration_ids": list(self.migration_ids),
            }
        )

    def asset(self, path: ScopePath | str) -> OwnedAsset:
        candidate = _exact_path(path, "catalog lookup path")
        for asset in self.assets:
            if asset.path.comparison_key == candidate.comparison_key:
                return asset
        raise KeyError(candidate.as_wire())


def _manifest_assets(manifest: Mapping[str, object], provider_root: ProviderRoot) -> None:
    raw_assets = manifest.get("assets")
    if not isinstance(raw_assets, Sequence) or isinstance(raw_assets, (str, bytes, bytearray)):
        raise _failure(ErrorCategory.INVALID_INPUT, "asset manifest assets must be an array")
    paths: list[ScopePath] = []
    seen: set[tuple[str, ...]] = set()
    root = ScopePath.directory(provider_root.value)
    for index, entry in enumerate(raw_assets):
        if not isinstance(entry, Mapping):
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"asset manifest entry {index} must be an object",
            )
        try:
            path = _exact_path(entry.get("path"), f"asset manifest path at index {index}")
            _exact_path(entry.get("source_ref"), f"asset manifest source_ref at index {index}")
            Sha256Digest(entry.get("sha256"))
            AssetOwnership(entry.get("ownership"))
        except (TypeError, ValueError) as exc:
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"invalid asset manifest entry at index {index}: {exc}",
                details={"entry_index": index},
            ) from exc
        if not root.contains(path):
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"asset manifest path escapes provider root {provider_root.value}: {path}",
                details={"entry_index": index, "path": path.as_wire()},
            )
        if path.comparison_key in seen:
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"asset manifest contains a duplicate or aliased path: {path}",
                details={"entry_index": index, "path": path.as_wire()},
            )
        for prior in paths:
            if prior.overlaps(path):
                raise _failure(
                    ErrorCategory.INVALID_INPUT,
                    f"asset manifest paths have an ancestor collision: {prior} and {path}",
                    details={"entry_index": index, "path": path.as_wire()},
                )
        seen.add(path.comparison_key)
        paths.append(path)


def _plain_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _plain_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json(item) for item in value]
    return value


def verify_asset_manifest(
    manifest: Mapping[str, object],
    catalog: AssetCatalog,
    registry: ContractRegistry,
) -> None:
    """Validate schema, safe paths, content hashes, and the exact catalog projection."""

    if not isinstance(catalog, AssetCatalog):
        raise TypeError("catalog must be an AssetCatalog")
    if not isinstance(registry, ContractRegistry):
        raise TypeError("registry must be a ContractRegistry")
    registry.validate(manifest, source=catalog.manifest_path.as_wire())
    _manifest_assets(manifest, catalog.provider_root)

    raw_assets = manifest["assets"]
    assert isinstance(raw_assets, Sequence)
    by_key = {
        asset.path.comparison_key: asset
        for asset in catalog.assets
    }
    for index, entry in enumerate(raw_assets):
        assert isinstance(entry, Mapping)
        path = ScopePath.exact_file(str(entry["path"]))
        asset = by_key.get(path.comparison_key)
        if asset is None:
            raise _failure(
                ErrorCategory.VALIDATION_FAILED,
                f"asset manifest contains an unrecognized path: {path}",
                details={"entry_index": index, "path": path.as_wire()},
            )
        actual = _digest(asset.content)
        if str(actual) != entry["sha256"]:
            raise _failure(
                ErrorCategory.VALIDATION_FAILED,
                f"asset manifest hash mismatch for {path}",
                details={
                    "entry_index": index,
                    "path": path.as_wire(),
                    "expected_sha256": entry["sha256"],
                    "actual_sha256": str(actual),
                },
            )

    expected = catalog.manifest_record.to_dict()
    if _plain_json(manifest) != expected:
        raise _failure(
            ErrorCategory.VALIDATION_FAILED,
            "asset manifest does not exactly match the deterministic catalog",
        )


def _is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def _source_path(source_root: Path, source_ref: ScopePath | str) -> Path:
    reference = _exact_path(source_ref, "source_ref")
    root = source_root.resolve(strict=False)
    path = source_root.joinpath(*reference.value.split("/"))
    try:
        resolved = path.resolve(strict=False)
    except OSError as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"cannot resolve catalog source {reference}: {exc}",
        ) from exc
    if not resolved.is_relative_to(root):
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"catalog source escapes source root: {reference}",
        )
    current = path
    while current != source_root and current != current.parent:
        if _is_link(current):
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"catalog source traverses a link or junction: {reference}",
            )
        current = current.parent
    if not path.is_file():
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"catalog source file is unavailable: {reference}",
        )
    return path


def _source_directory(source_root: Path, relative_directory: str) -> Path:
    try:
        reference = ScopePath.directory(relative_directory)
    except (TypeError, ValueError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"invalid catalog source directory {relative_directory!r}: {exc}",
        ) from exc
    root = source_root.resolve(strict=False)
    directory = source_root.joinpath(*reference.value.split("/"))
    try:
        resolved = directory.resolve(strict=False)
    except OSError as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"cannot resolve catalog source directory {reference}: {exc}",
        ) from exc
    if not resolved.is_relative_to(root):
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"catalog source directory escapes source root: {reference}",
        )
    current = directory
    while current != source_root and current != current.parent:
        if _is_link(current):
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"catalog source directory traverses a link or junction: {reference}",
            )
        current = current.parent
    if not directory.is_dir():
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"catalog source directory is unavailable: {reference}",
        )
    return directory


def _normalize_text(content: bytes) -> bytes:
    return content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _provider_note(provider_root: ProviderRoot) -> str:
    if provider_root is ProviderRoot.CLAUDE:
        return (
            "Claude Code loads project instructions from `.claude/CLAUDE.md`. The Markdown files "
            "under `.claude/agents/` are workflow documentation selected explicitly; they are not "
            "native subagent registrations. See the official project memory guide: "
            "https://code.claude.com/docs/en/memory"
        )
    root = provider_root.value
    return (
        f"For Codex or ChatGPT, explicitly ask the session to read `{root}/AGENTS.md` at "
        "startup. Codex discovers AGENTS.md files from the project root down to the current "
        "working directory, so a hidden child entry is not loaded from a project-root "
        "launch; ordinary ChatGPT chats also do not automatically read local folders. See "
        "the official Codex instruction guide: "
        "https://learn.chatgpt.com/docs/agent-configuration/agents-md"
    )


def _render(
    content: bytes,
    source_ref: ScopePath,
    provider_root: ProviderRoot,
    *,
    substitute_provider: bool = True,
) -> bytes:
    if source_ref.value == _GENERATED_EMPTY_SOURCE:
        return content
    suffix = Path(source_ref.value).suffix.lower()
    if suffix not in TEXT_SUFFIXES and Path(source_ref.value).name != "GITATTRIBUTES":
        return content
    if not substitute_provider:
        return _normalize_text(content)
    try:
        text = _normalize_text(content).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"catalog text source is not UTF-8: {source_ref}",
        ) from exc
    text = text.replace(PROVIDER_TOKEN, _provider_note(provider_root))
    if provider_root is not ProviderRoot.CODEX:
        text = text.replace(".codex", provider_root.value)
    if provider_root is ProviderRoot.CLAUDE:
        text = text.replace("AGENTS.md", provider_root.entry_name)
    return text.encode("utf-8")


def _walk_source_files(source_root: Path, relative_directory: str) -> tuple[ScopePath, ...]:
    directory = _source_directory(source_root, relative_directory)
    found: list[ScopePath] = []
    for base, names, files in os.walk(directory, followlinks=False):
        base_path = Path(base)
        linked_names = [name for name in names if _is_link(base_path / name)]
        if linked_names:
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"catalog source tree contains a linked directory: {base_path / linked_names[0]}",
            )
        names[:] = sorted(name for name in names if name not in _EXCLUDED_SOURCE_DIRECTORIES)
        for name in sorted(files):
            path = base_path / name
            if _is_link(path):
                raise _failure(
                    ErrorCategory.INVALID_INPUT,
                    f"catalog source tree contains a linked file: {path}",
                )
            relative = path.relative_to(source_root).as_posix()
            try:
                found.append(ScopePath.exact_file(relative))
            except (TypeError, ValueError) as exc:
                raise _failure(
                    ErrorCategory.INVALID_INPUT,
                    f"catalog source tree contains an unsafe path {relative!r}: {exc}",
                ) from exc
    if not found:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"catalog source tree is empty: {relative_directory}",
        )
    return tuple(sorted(found, key=ScopePath.as_wire))


def _tool_source_refs(source_root: Path) -> tuple[ScopePath, ...]:
    source_directory = source_root / "src"
    if not source_directory.is_dir() or _is_link(source_directory):
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            "catalog source is missing a safe src directory",
        )
    modules: dict[str, ScopePath] = {}
    for path in sorted(source_directory.glob("*.py"), key=lambda item: item.name):
        reference = ScopePath.exact_file(path.relative_to(source_root).as_posix())
        if path.stem in modules:
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"duplicate flat tool module name: {path.stem}",
            )
        modules[path.stem] = reference

    missing = [name for name in REQUIRED_TOOL_MODULES if Path(name).stem not in modules]
    if missing:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"catalog source is missing required tool modules: {', '.join(missing)}",
        )

    pending = [Path(name).stem for name in TOOL_ENTRYPOINTS]
    included: set[str] = set()
    while pending:
        module_name = pending.pop()
        if module_name in included:
            continue
        reference = modules.get(module_name)
        if reference is None:
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"catalog source is missing helper module: {module_name}.py",
            )
        path = _source_path(source_root, reference)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"cannot inspect tool imports in {reference}: {exc}",
            ) from exc
        included.add(module_name)
        for node in ast.walk(tree):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name.partition(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported = [node.module.partition(".")[0]]
            pending.extend(name for name in imported if name in modules and name not in included)

    required = {Path(name).stem for name in REQUIRED_TOOL_MODULES}
    unreachable = sorted(required - included)
    if unreachable:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            "required tool modules are outside the entry-point closure: "
            + ", ".join(f"{name}.py" for name in unreachable),
        )
    return tuple(modules[name] for name in sorted(included))


def _asset_from_source(
    source_root: Path,
    destination: str,
    source_ref: ScopePath | str,
    ownership: AssetOwnership,
    provider_root: ProviderRoot,
    *,
    substitute_provider: bool = True,
) -> OwnedAsset:
    reference = _exact_path(source_ref, "source_ref")
    content = _source_path(source_root, reference).read_bytes()
    return OwnedAsset(
        path=ScopePath.exact_file(destination),
        source_ref=reference,
        ownership=ownership,
        content=_render(
            content,
            reference,
            provider_root,
            substitute_provider=substitute_provider,
        ),
    )


def _empty_asset(destination: str, provider_root: ProviderRoot) -> OwnedAsset:
    return OwnedAsset(
        path=ScopePath.exact_file(destination),
        source_ref=ScopePath.exact_file(_GENERATED_EMPTY_SOURCE),
        ownership=AssetOwnership.SEED_ONLY,
        content=_render(b"", ScopePath.exact_file(_GENERATED_EMPTY_SOURCE), provider_root),
    )


def _validate_installation(catalog: AssetCatalog, registry: ContractRegistry) -> None:
    installation = catalog.installation_record.to_dict()
    registry.validate(
        installation,
        source=f"{catalog.provider_root.value}/framework.json",
    )
    if installation["framework_version"] != catalog.framework_version:
        raise _failure(
            ErrorCategory.VALIDATION_FAILED,
            "framework installation and asset manifest versions differ",
        )
    if installation["manifest_ref"] != catalog.manifest_path.as_wire():
        raise _failure(
            ErrorCategory.VALIDATION_FAILED,
            "framework installation manifest_ref does not identify the catalog manifest",
        )

    root = ScopePath.directory(catalog.provider_root.value)
    try:
        owned_roots = tuple(ScopePath(value) for value in installation["owned_roots"])
        project_roots = tuple(ScopePath(value) for value in installation["project_owned_roots"])
    except (TypeError, ValueError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"framework installation contains an unsafe ownership root: {exc}",
        ) from exc
    all_roots = owned_roots + project_roots
    if any(not root.contains(item) for item in all_roots):
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"framework installation ownership root escapes {catalog.provider_root.value}",
        )
    for index, left in enumerate(all_roots):
        for right in all_roots[index + 1 :]:
            if left.overlaps(right):
                raise _failure(
                    ErrorCategory.INVALID_INPUT,
                    f"framework installation ownership roots overlap: {left} and {right}",
                )
    for asset in catalog.assets:
        roots = owned_roots if asset.is_framework_managed else project_roots
        if not any(candidate.contains(asset.path) for candidate in roots):
            label = "framework" if asset.is_framework_managed else "project"
            raise _failure(
                ErrorCategory.VALIDATION_FAILED,
                f"{label}-owned asset is outside its declared roots: {asset.path}",
            )


def build_owned_asset_catalog(
    source_root: Path,
    provider_root: ProviderRoot | str = ProviderRoot.CODEX,
    *,
    registry: ContractRegistry | None = None,
) -> AssetCatalog:
    """Discover, hash, and validate the complete source payload for one provider root."""

    source = Path(source_root)
    if not source.is_dir() or _is_link(source):
        raise _failure(ErrorCategory.INVALID_INPUT, f"invalid catalog source root: {source}")
    try:
        selected_root = ProviderRoot(provider_root)
    except (TypeError, ValueError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"unsupported provider root: {provider_root!r}",
        ) from exc
    selected_registry = registry or load_contract_registry(source / "schemas" / "v1")
    if not isinstance(selected_registry, ContractRegistry):
        raise TypeError("registry must be a ContractRegistry")

    root = selected_root.value
    assets: list[OwnedAsset] = []
    _source_path(source, "docs/agents/README.md")
    for tree_name in PRODUCT_TREES:
        for reference in _walk_source_files(source, f"docs/{tree_name}"):
            relative = reference.value.removeprefix(f"docs/{tree_name}/")
            assets.append(
                _asset_from_source(
                    source,
                    f"{root}/{tree_name}/{relative}",
                    reference,
                    AssetOwnership.FRAMEWORK,
                    selected_root,
                )
            )

    default_framework = {
        f"{root}/requirements.txt": "docs/defaults/requirements.txt",
        f"{root}/.gitattributes": "docs/defaults/GITATTRIBUTES",
        f"{root}/framework.json": "docs/defaults/FRAMEWORK.json",
    }
    default_seeds = {
        f"{root}/README.md": "docs/defaults/README.md",
        f"{root}/{selected_root.entry_name}": "docs/defaults/INSTRUCTIONS.md",
        f"{root}/STATE.json": "docs/defaults/STATE.json",
        f"{root}/project/policy.json": "docs/defaults/POLICY.json",
        f"{root}/project/agent-models.json": "docs/defaults/AGENT_MODELS.json",
        f"{root}/decisions/index.json": "docs/defaults/DECISIONS.json",
    }
    for destination, reference in default_framework.items():
        assets.append(
            _asset_from_source(
                source,
                destination,
                reference,
                AssetOwnership.FRAMEWORK,
                selected_root,
            )
        )
    for destination, reference in default_seeds.items():
        assets.append(
            _asset_from_source(
                source,
                destination,
                reference,
                AssetOwnership.SEED_ONLY,
                selected_root,
            )
        )

    for reference in _tool_source_refs(source):
        assets.append(
            _asset_from_source(
                source,
                f"{root}/tools/{Path(reference.value).name}",
                reference,
                AssetOwnership.FRAMEWORK,
                selected_root,
                substitute_provider=False,
            )
        )
    schema_directory = source / "schemas" / "v1"
    schema_paths = sorted(schema_directory.glob("*.schema.json"), key=lambda path: path.name)
    if not schema_paths:
        raise _failure(ErrorCategory.INVALID_INPUT, "catalog source has no canonical v1 schemas")
    for path in schema_paths:
        reference = ScopePath.exact_file(path.relative_to(source).as_posix())
        assets.append(
            _asset_from_source(
                source,
                f"{root}/framework/schemas/v1/{path.name}",
                reference,
                AssetOwnership.FRAMEWORK,
                selected_root,
                substitute_provider=False,
            )
        )

    for directory in ("plans/current", "plans/completed", "plans/archived", "research"):
        assets.append(_empty_asset(f"{root}/{directory}/.gitkeep", selected_root))

    framework_asset = next(
        asset for asset in assets if asset.path.as_wire() == f"{root}/framework.json"
    )
    try:
        installation_data = json.loads(framework_asset.content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"cannot decode docs/defaults/FRAMEWORK.json: {exc}",
        ) from exc
    if not isinstance(installation_data, Mapping):
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            "docs/defaults/FRAMEWORK.json must contain an object",
        )
    version = installation_data.get("framework_version")
    if not isinstance(version, str):
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            "docs/defaults/FRAMEWORK.json has no framework_version",
        )

    catalog = AssetCatalog(
        framework_version=version,
        provider_root=selected_root,
        assets=tuple(assets),
        installation_record=FrozenJsonObject(installation_data),
        migration_ids=(),
    )
    _validate_installation(catalog, selected_registry)
    verify_asset_manifest(catalog.manifest_record, catalog, selected_registry)
    return catalog


__all__ = [
    "AssetCatalog",
    "AssetOwnership",
    "OwnedAsset",
    "ProviderRoot",
    "build_owned_asset_catalog",
    "verify_asset_manifest",
]
