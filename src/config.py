"""Immutable project configuration decoding and compatibility checks.

The module reads only the framework's tracked JSON records.  Provider-native
settings and the process environment are deliberately outside this boundary:
catalog entries are recommendations, while a policy profile is an automatic
binding only when its wire ``configured`` flag is true.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any

from contracts import ContractRegistry, SCHEMA_VERSION, load_contract_registry
from domain_values import (
    DomainError,
    DomainException,
    ErrorCategory,
    InstallationStatus,
)


SUPPORTED_SCHEMA_COMPATIBILITY = SCHEMA_VERSION
RECORD_NAMESPACES = (".codex", ".claude", ".ai")

SAFE_AUTONOMOUS_ACTIONS = frozenset(
    {
        "read",
        "research",
        "local_worktrees",
        "edit_scope",
        "tests",
        "commits",
        "reviews",
        "replan",
    }
)
SENSITIVE_ACTIONS = frozenset(
    {
        "remote_push",
        "remote_pr_write",
        "protected_merge",
        "deployment",
        "destructive_database",
        "credentials",
        "paid_services",
        "remote_delete",
        "major_product_scope",
    }
)
KNOWN_ACTIONS = SAFE_AUTONOMOUS_ACTIONS | SENSITIVE_ACTIONS

_INVALID_WINDOWS_CHARACTERS = frozenset('<>:"|?*')
_RESERVED_WINDOWS_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "CLOCK$",
        "CONIN$",
        "CONOUT$",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
)
_FRAMEWORK_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:[A-Za-z0-9.+-]*)\Z")


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


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and have no surrounding whitespace")
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value):
        raise ValueError(f"{label} contains a control or invisible formatting character")
    return unicodedata.normalize("NFC", value)


def _strings(values: object, label: str, *, sort: bool = False) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{label} must be an array")
    result = tuple(_text(value, label) for value in values)
    aliases: set[str] = set()
    for value in result:
        alias = unicodedata.normalize("NFKC", value).casefold()
        if alias in aliases:
            raise ValueError(f"{label} contains a duplicate or aliased value {value!r}")
        aliases.add(alias)
    return tuple(sorted(result)) if sort else result


def _require_distinct_names(values: tuple[str, ...], label: str) -> None:
    aliases = [unicodedata.normalize("NFKC", value).casefold() for value in values]
    if len(set(aliases)) != len(aliases):
        raise ValueError(f"{label} contains duplicate or aliased names")


def _integer(value: object, label: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    return value


def _portable_path(value: object, label: str, *, allow_directory: bool = True) -> str:
    text = _text(value, label).replace("\\", "/")
    directory = text.endswith("/")
    if directory and not allow_directory:
        raise ValueError(f"{label} must name a file")
    separated = text[:-1] if directory else text
    if separated.startswith("/") or re.match(r"[A-Za-z]:", separated):
        raise ValueError(f"{label} must be repository-relative")
    parts = separated.split("/")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"{label} contains an unsafe path component")
    normalized: list[str] = []
    for part in parts:
        if any(character in _INVALID_WINDOWS_CHARACTERS for character in part):
            raise ValueError(f"{label} contains a non-portable path component")
        if part.endswith((" ", ".")):
            raise ValueError(f"{label} contains a non-portable path component")
        if part.split(".", 1)[0].rstrip(" ").upper() in _RESERVED_WINDOWS_NAMES:
            raise ValueError(f"{label} contains a reserved Windows path component")
        normalized.append(unicodedata.normalize("NFC", part))
    return "/".join(normalized) + ("/" if directory else "")


def _path_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value.rstrip("/")).casefold()


def _claim_contains(claim: str, path: str) -> bool:
    claim_key = _path_key(claim)
    path_key = _path_key(path)
    return claim_key == path_key or (claim.endswith("/") and path_key.startswith(claim_key + "/"))


def _is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def _checked_root(root: Path) -> Path:
    candidate = Path(root)
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Cannot resolve project root {candidate}: {exc}",
            details={"root": str(candidate)},
        ) from exc
    if not resolved.is_dir():
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Project root is not a directory: {resolved}",
            details={"root": str(resolved)},
        )
    return resolved


def _checked_path(root: Path, relative: str, *, directory: bool) -> Path:
    normalized = _portable_path(relative, "configuration path", allow_directory=directory)
    candidate = root.joinpath(*normalized.rstrip("/").split("/"))
    current = root
    for component in candidate.relative_to(root).parts:
        current = current / component
        if _is_link(current):
            raise _failure(
                ErrorCategory.POLICY_DENIED,
                f"Refusing linked configuration path: {current}",
                details={"path": normalized},
            )
    if directory:
        if not candidate.is_dir():
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"Configuration directory is missing: {candidate}",
                details={"path": normalized},
            )
    elif not candidate.is_file():
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Configuration file is missing: {candidate}",
            details={"path": normalized},
        )
    return candidate


def _read_json(root: Path, relative: str) -> dict[str, object]:
    path = _checked_path(root, relative, directory=False)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Cannot read configuration JSON {relative}: {exc}",
            details={"path": relative},
        ) from exc
    if not isinstance(value, dict):
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Configuration JSON must be an object: {relative}",
            details={"path": relative},
        )
    return value


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


@dataclass(frozen=True, slots=True)
class InstallationRecord:
    """The exact typed fields of ``framework-installation.schema.json``."""

    schema_version: str
    framework_version: str
    schema_compatibility: str
    installation_status: InstallationStatus
    manifest_ref: str | None
    owned_roots: tuple[str, ...]
    project_owned_roots: tuple[str, ...]
    kind: str = field(default="framework-installation", init=False)

    def __post_init__(self) -> None:
        schema_version = _text(self.schema_version, "installation schema_version")
        framework_version = _text(self.framework_version, "framework_version")
        compatibility = _text(self.schema_compatibility, "schema_compatibility")
        if _FRAMEWORK_VERSION.fullmatch(framework_version) is None:
            raise ValueError("framework_version must be a semantic version")
        status = (
            self.installation_status
            if isinstance(self.installation_status, InstallationStatus)
            else InstallationStatus(self.installation_status)
        )
        manifest = (
            None
            if self.manifest_ref is None
            else _portable_path(self.manifest_ref, "manifest_ref", allow_directory=False)
        )
        owned = tuple(
            sorted(_portable_path(value, "owned_roots item") for value in self.owned_roots)
        )
        project_owned = tuple(
            sorted(
                _portable_path(value, "project_owned_roots item")
                for value in self.project_owned_roots
            )
        )
        if not project_owned:
            raise ValueError("project_owned_roots cannot be empty")
        all_roots = owned + project_owned
        if len({_path_key(value) for value in all_roots}) != len(all_roots):
            raise ValueError("installation ownership contains duplicate or aliased roots")
        if any(
            _claim_contains(left, right) or _claim_contains(right, left)
            for left in owned
            for right in project_owned
        ):
            raise ValueError("framework-owned and project-owned roots overlap")
        namespaces = {
            value.rstrip("/").split("/", 1)[0]
            for value in all_roots + (() if manifest is None else (manifest,))
            if value.rstrip("/").split("/", 1)[0] in RECORD_NAMESPACES
        }
        if len(namespaces) != 1:
            raise ValueError("installation must identify exactly one workflow namespace")
        namespace = next(iter(namespaces))
        if status is InstallationStatus.SOURCE_FOUNDATION and namespace != ".ai":
            raise ValueError("source_foundation must use the source .ai namespace")
        if status is not InstallationStatus.SOURCE_FOUNDATION and namespace in {
            ".codex",
            ".claude",
        }:
            foreign_roots = [
                value
                for value in all_roots + (() if manifest is None else (manifest,))
                if value.rstrip("/").split("/", 1)[0] != namespace
            ]
            if foreign_roots:
                raise ValueError(
                    "installed ownership and manifest paths must stay in the workflow namespace"
                )
        required_policy = f"{namespace}/project/policy.json"
        required_models = f"{namespace}/project/agent-models.json"
        if not any(_claim_contains(claim, required_policy) for claim in project_owned):
            raise ValueError("project-owned roots must contain project/policy.json")
        if not any(_claim_contains(claim, required_models) for claim in project_owned):
            raise ValueError("project-owned roots must contain project/agent-models.json")
        if status is InstallationStatus.INSTALLED:
            if manifest is None:
                raise ValueError("installed configuration requires manifest_ref")
            if not any(_claim_contains(claim, manifest) for claim in owned):
                raise ValueError("manifest_ref must be within framework-owned roots")
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "framework_version", framework_version)
        object.__setattr__(self, "schema_compatibility", compatibility)
        object.__setattr__(self, "installation_status", status)
        object.__setattr__(self, "manifest_ref", manifest)
        object.__setattr__(self, "owned_roots", owned)
        object.__setattr__(self, "project_owned_roots", project_owned)

    @property
    def namespace(self) -> str:
        for value in self.project_owned_roots:
            namespace = value.rstrip("/").split("/", 1)[0]
            if namespace in RECORD_NAMESPACES:
                return namespace
        raise RuntimeError("validated installation has no namespace")

    def to_wire(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "framework_version": self.framework_version,
            "schema_compatibility": self.schema_compatibility,
            "installation_status": self.installation_status.value,
            "manifest_ref": self.manifest_ref,
            "owned_roots": list(self.owned_roots),
            "project_owned_roots": list(self.project_owned_roots),
        }


@dataclass(frozen=True, slots=True, order=True)
class ExternalGrant:
    action: str
    resource: str
    authority_ref: str


@dataclass(frozen=True, slots=True, order=True)
class PolicyModelProfile:
    name: str
    provider: str | None
    model_id: str | None
    capability_rank: int
    configured: bool


@dataclass(frozen=True, slots=True)
class ProjectPolicy:
    schema_version: str
    id: str
    autonomous_actions: tuple[str, ...]
    approval_actions: tuple[str, ...]
    external_grants: tuple[ExternalGrant, ...]
    max_parallel: int
    max_review_cycles: int
    max_rewrites: int
    max_agent_invocations: int
    required_sandbox: bool
    allow_review_downgrade: bool
    model_profiles: tuple[PolicyModelProfile, ...]
    kind: str = field(default="policy", init=False)

    def model_profile(self, name: str) -> PolicyModelProfile:
        normalized = _text(name, "policy model profile name")
        for profile in self.model_profiles:
            if profile.name == normalized:
                return profile
        raise _failure(
            ErrorCategory.UNSUPPORTED_CAPABILITY,
            f"Unknown policy model profile {normalized!r}",
            details={"profile": normalized},
        )

    def action_requirement(self, action: str) -> ActionRequirement:
        normalized = _text(action, "action")
        if normalized in self.autonomous_actions:
            return ActionRequirement.AUTONOMOUS
        if normalized in self.approval_actions:
            return ActionRequirement.APPROVAL
        return ActionRequirement.DENIED

    def with_run_settings(self, settings: RunSettings) -> ProjectPolicy:
        """Return a detached effective policy without changing project policy."""
        if not isinstance(settings, RunSettings):
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                "effective policy requires RunSettings",
            )
        return replace(
            self,
            max_parallel=settings.max_parallel,
            max_review_cycles=settings.max_review_cycles,
            max_rewrites=settings.max_rewrites,
            max_agent_invocations=settings.max_agent_invocations,
            required_sandbox=settings.required_sandbox,
        )

    def to_wire(self) -> dict[str, object]:
        """Return a detached, schema-shaped policy snapshot."""
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "id": self.id,
            "autonomous_actions": list(self.autonomous_actions),
            "approval_actions": list(self.approval_actions),
            "external_grants": [
                {
                    "action": grant.action,
                    "resource": grant.resource,
                    "authority_ref": grant.authority_ref,
                }
                for grant in self.external_grants
            ],
            "max_parallel": self.max_parallel,
            "max_review_cycles": self.max_review_cycles,
            "max_rewrites": self.max_rewrites,
            "max_agent_invocations": self.max_agent_invocations,
            "required_sandbox": self.required_sandbox,
            "allow_review_downgrade": self.allow_review_downgrade,
            "model_profiles": [
                {
                    "name": profile.name,
                    "provider": profile.provider,
                    "model_id": profile.model_id,
                    "capability_rank": profile.capability_rank,
                    "configured": profile.configured,
                }
                for profile in self.model_profiles
            ],
        }


@dataclass(frozen=True, slots=True, order=True)
class ProviderModelProfile:
    provider: str
    name: str
    model_id: str
    capability_rank: int
    reasoning_effort: str | None
    effort: str | None


@dataclass(frozen=True, slots=True)
class ProviderModels:
    name: str
    profiles: tuple[ProviderModelProfile, ...]

    def profile(self, name: str) -> ProviderModelProfile:
        normalized = _text(name, "provider profile name")
        for profile in self.profiles:
            if profile.name == normalized:
                return profile
        raise _failure(
            ErrorCategory.UNSUPPORTED_CAPABILITY,
            f"Provider {self.name!r} has no profile {normalized!r}",
            details={"provider": self.name, "profile": normalized},
        )


@dataclass(frozen=True, slots=True, order=True)
class RoleModelDefaults:
    role: str
    openai: str
    anthropic: str


@dataclass(frozen=True, slots=True, order=True)
class PolicyProfileMapping:
    policy_profile: str
    provider_profile: str


@dataclass(frozen=True, slots=True)
class AgentModels:
    schema_version: str
    verified_on: date
    active_provider: str
    sources: tuple[str, ...]
    providers: tuple[ProviderModels, ...]
    roles: tuple[RoleModelDefaults, ...]
    policy_profile_map: tuple[PolicyProfileMapping, ...]
    kind: str = field(default="agent-models", init=False)

    def provider(self, name: str | None = None) -> ProviderModels:
        selected = self.active_provider if name is None else _text(name, "provider").casefold()
        for provider in self.providers:
            if provider.name == selected:
                return provider
        raise _failure(
            ErrorCategory.UNSUPPORTED_CAPABILITY,
            f"Unknown model provider {selected!r}",
            details={"provider": selected},
        )

    def model_profile(
        self, name: str, *, provider: str | None = None
    ) -> ProviderModelProfile:
        return self.provider(provider).profile(name)

    def model_for_role(self, role: str) -> ProviderModelProfile:
        normalized = _text(role, "role")
        for default in self.roles:
            if default.role == normalized:
                profile_name = (
                    default.openai
                    if self.active_provider == "openai"
                    else default.anthropic
                )
                return self.model_profile(profile_name)
        raise _failure(
            ErrorCategory.UNSUPPORTED_CAPABILITY,
            f"Unknown configured role {normalized!r}",
            details={"role": normalized},
        )

    def provider_profile_for_policy(self, policy_profile: str) -> ProviderModelProfile:
        normalized = _text(policy_profile, "policy profile")
        for mapping in self.policy_profile_map:
            if mapping.policy_profile == normalized:
                return self.model_profile(mapping.provider_profile)
        raise _failure(
            ErrorCategory.UNSUPPORTED_CAPABILITY,
            f"Unknown policy profile mapping {normalized!r}",
            details={"profile": normalized},
        )


@dataclass(frozen=True, slots=True)
class RunSettings:
    """A resolved, persistable snapshot; resume reuses this value unchanged."""

    max_parallel: int = 4
    max_review_cycles: int = 2
    max_rewrites: int = 3
    max_agent_invocations: int = 300
    required_sandbox: bool = False

    def __post_init__(self) -> None:
        _integer(self.max_parallel, "max_parallel", 1)
        _integer(self.max_review_cycles, "max_review_cycles", 1)
        _integer(self.max_rewrites, "max_rewrites", 0)
        _integer(self.max_agent_invocations, "max_agent_invocations", 0)
        if not isinstance(self.required_sandbox, bool):
            raise TypeError("required_sandbox must be a boolean")

    def to_payload(self) -> dict[str, int | bool]:
        """Return the closed portable payload persisted by a state owner."""
        return {
            "max_parallel": self.max_parallel,
            "max_review_cycles": self.max_review_cycles,
            "max_rewrites": self.max_rewrites,
            "max_agent_invocations": self.max_agent_invocations,
            "required_sandbox": self.required_sandbox,
        }


BUILT_IN_RUN_SETTINGS = RunSettings()


@dataclass(frozen=True, slots=True)
class RunOverrides:
    """Optional run-local restrictions; values may not broaden project policy."""

    max_parallel: int | None = None
    max_review_cycles: int | None = None
    max_rewrites: int | None = None
    max_agent_invocations: int | None = None
    required_sandbox: bool | None = None

    def __post_init__(self) -> None:
        for name, minimum in (
            ("max_parallel", 1),
            ("max_review_cycles", 1),
            ("max_rewrites", 0),
            ("max_agent_invocations", 0),
        ):
            value = getattr(self, name)
            if value is not None:
                _integer(value, name, minimum)
        if self.required_sandbox is not None and not isinstance(self.required_sandbox, bool):
            raise TypeError("required_sandbox override must be a boolean or None")


class ActionRequirement(StrEnum):
    AUTONOMOUS = "autonomous"
    APPROVAL = "approval"
    DENIED = "denied"


@dataclass(frozen=True, slots=True)
class ProjectSettings:
    project_root: Path
    namespace: str
    installation: InstallationRecord
    policy: ProjectPolicy
    models: AgentModels
    policy_ref: str
    agent_models_ref: str

    def configured_model(self, policy_profile: str) -> ProviderModelProfile | None:
        configured = self.policy.model_profile(policy_profile)
        if not configured.configured:
            return None
        return self.models.provider_profile_for_policy(configured.name)

    def model_for_role(self, role: str) -> ProviderModelProfile:
        return self.models.model_for_role(role)

    def resolve_run(
        self,
        overrides: RunOverrides | None = None,
        *,
        saved: RunSettings | None = None,
    ) -> RunSettings:
        """Apply defaults, project policy, then restrictive run overrides.

        Passing ``saved`` represents resume and returns that immutable snapshot;
        combining a saved snapshot with new overrides is rejected.
        """
        if saved is not None:
            if not isinstance(saved, RunSettings):
                raise _failure(
                    ErrorCategory.INVALID_INPUT,
                    "saved run configuration must be RunSettings",
                )
            if overrides is not None:
                raise _failure(
                    ErrorCategory.INVALID_INPUT,
                    "resume cannot combine saved settings with new run overrides",
                )
            return saved
        if overrides is not None and not isinstance(overrides, RunOverrides):
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                "run overrides must be RunOverrides",
            )
        project = replace(
            BUILT_IN_RUN_SETTINGS,
            max_parallel=self.policy.max_parallel,
            max_review_cycles=self.policy.max_review_cycles,
            max_rewrites=self.policy.max_rewrites,
            max_agent_invocations=self.policy.max_agent_invocations,
            required_sandbox=self.policy.required_sandbox,
        )
        if overrides is None:
            return project
        updates: dict[str, object] = {}
        for name in (
            "max_parallel",
            "max_review_cycles",
            "max_rewrites",
            "max_agent_invocations",
        ):
            value = getattr(overrides, name)
            if value is None:
                continue
            if value > getattr(project, name):
                raise _failure(
                    ErrorCategory.POLICY_DENIED,
                    f"Run override cannot increase {name} beyond project policy",
                    details={"setting": name},
                )
            updates[name] = value
        if overrides.required_sandbox is not None:
            if project.required_sandbox and not overrides.required_sandbox:
                raise _failure(
                    ErrorCategory.POLICY_DENIED,
                    "Run override cannot disable required sandboxing",
                    details={"setting": "required_sandbox"},
                )
            updates["required_sandbox"] = overrides.required_sandbox
        return replace(project, **updates)

    def effective_policy(
        self,
        overrides: RunOverrides | None = None,
    ) -> ProjectPolicy:
        """Build the schema-valid effective policy snapshot for a new run."""
        return self.policy.with_run_settings(self.resolve_run(overrides))


def _decode_installation(
    artifact: Mapping[str, object], registry: ContractRegistry, source: str
) -> InstallationRecord:
    registry.validate(artifact, source=source)
    try:
        return InstallationRecord(
            schema_version=artifact["schema_version"],
            framework_version=artifact["framework_version"],
            schema_compatibility=artifact["schema_compatibility"],
            installation_status=artifact["installation_status"],
            manifest_ref=artifact["manifest_ref"],
            owned_roots=tuple(artifact["owned_roots"]),
            project_owned_roots=tuple(artifact["project_owned_roots"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"{source}: invalid framework installation: {exc}",
            details={"source": source},
        ) from exc


def decode_installation_record(
    artifact: Mapping[str, object],
    registry: ContractRegistry,
    *,
    source: str = "framework installation",
) -> InstallationRecord:
    """Validate and detach one installation wire record."""
    if not isinstance(registry, ContractRegistry):
        raise _failure(ErrorCategory.INVALID_INPUT, "registry must be a ContractRegistry")
    if not isinstance(artifact, Mapping):
        raise _failure(ErrorCategory.INVALID_INPUT, f"{source}: artifact must be an object")
    installation = _decode_installation(artifact, registry, source)
    _validate_compatibility(installation)
    return installation


def decode_run_settings(payload: Mapping[str, object]) -> RunSettings:
    """Hydrate a saved run snapshot from an exact, non-record payload.

    The state owner may store these bytes behind the existing
    ``state-event.payload_ref``.  This is not a new v1 artifact kind.
    """
    if not isinstance(payload, Mapping):
        raise _failure(
            ErrorCategory.INVALID_INPUT, "saved run settings must be an object"
        )
    expected = {
        "max_parallel",
        "max_review_cycles",
        "max_rewrites",
        "max_agent_invocations",
        "required_sandbox",
    }
    actual = set(payload)
    if actual != expected:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            "saved run settings have missing or unknown fields",
            details={
                "missing": sorted(expected - actual),
                "unknown": sorted(actual - expected),
            },
        )
    try:
        return RunSettings(
            max_parallel=payload["max_parallel"],
            max_review_cycles=payload["max_review_cycles"],
            max_rewrites=payload["max_rewrites"],
            max_agent_invocations=payload["max_agent_invocations"],
            required_sandbox=payload["required_sandbox"],
        )
    except (TypeError, ValueError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Invalid saved run settings: {exc}",
        ) from exc


def _load_schema_registry(
    root: Path, namespace: str, status: InstallationStatus
) -> ContractRegistry:
    if (
        status is InstallationStatus.SOURCE_FOUNDATION
        and (root / "schemas" / "v1").is_dir()
    ):
        relative = "schemas/v1/"
    else:
        relative = f"{namespace}/framework/schemas/v1/"
    schema_root = _checked_path(root, relative, directory=True)
    for path in schema_root.glob("*.schema.json"):
        if _is_link(path):
            raise _failure(
                ErrorCategory.POLICY_DENIED,
                f"Refusing linked schema file: {path}",
                details={"path": path.relative_to(root).as_posix()},
            )
    return load_contract_registry(schema_root)


def _validate_compatibility(installation: InstallationRecord) -> None:
    if installation.schema_version != SCHEMA_VERSION:
        raise _failure(
            ErrorCategory.UNSUPPORTED_CAPABILITY,
            f"Unsupported installation schema version {installation.schema_version!r}",
            details={"schema_version": installation.schema_version},
        )
    if installation.schema_compatibility != SUPPORTED_SCHEMA_COMPATIBILITY:
        raise _failure(
            ErrorCategory.UNSUPPORTED_CAPABILITY,
            f"Unsupported schema compatibility {installation.schema_compatibility!r}",
            details={"schema_compatibility": installation.schema_compatibility},
        )
    if installation.installation_status is InstallationStatus.UPGRADE_PENDING:
        raise _failure(
            ErrorCategory.UNSUPPORTED_CAPABILITY,
            "Framework installation has an upgrade pending",
            details={"installation_status": installation.installation_status.value},
        )


def _discover_namespace(root: Path, requested: str | None = None) -> str:
    if requested is not None:
        selected = _text(requested, "namespace")
        if selected not in RECORD_NAMESPACES:
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"Unknown workflow namespace {selected!r}",
                details={"namespace": selected},
            )
    candidates = RECORD_NAMESPACES
    found = [
        namespace
        for namespace in candidates
        if (root / namespace / "framework.json").is_file()
        and not _is_link(root / namespace / "framework.json")
    ]
    if len(found) != 1:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            "Project must contain exactly one readable workflow installation",
            details={"namespaces": found},
        )
    if requested is not None and found[0] != selected:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Requested workflow namespace {selected!r} is not installed",
            details={"namespace": selected},
        )
    return found[0]


def load_installation_record(root: Path, *, namespace: str | None = None) -> InstallationRecord:
    """Discover and decode the project's single managed installation record."""
    project_root = _checked_root(root)
    selected = _discover_namespace(project_root, namespace)
    artifact = _read_json(project_root, f"{selected}/framework.json")
    provisional_status = artifact.get("installation_status")
    try:
        status = InstallationStatus(provisional_status)
    except (TypeError, ValueError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Invalid installation status {provisional_status!r}",
        ) from exc
    registry = _load_schema_registry(project_root, selected, status)
    installation = _decode_installation(
        artifact, registry, f"{selected}/framework.json"
    )
    if installation.namespace != selected:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            "Installation ownership does not match its workflow namespace",
            details={"expected_namespace": selected, "actual_namespace": installation.namespace},
        )
    _validate_compatibility(installation)
    return installation


def _decode_provider_models(
    provider: str, artifact: Mapping[str, object]
) -> ProviderModels:
    profiles_artifact = _mapping(artifact["profiles"], f"{provider} profiles")
    profiles: list[ProviderModelProfile] = []
    model_ranks: dict[str, int] = {}
    for raw_name, raw_profile in profiles_artifact.items():
        name = _text(raw_name, f"{provider} profile name")
        value = _mapping(raw_profile, f"{provider} profile {name}")
        model_id = _text(value["model_id"], f"{provider} {name} model_id")
        rank = _integer(value["capability_rank"], f"{provider} {name} rank", 1)
        reasoning = value["reasoning_effort"]
        effort = value["effort"]
        if reasoning is not None:
            reasoning = _text(reasoning, f"{provider} {name} reasoning_effort")
        if effort is not None:
            effort = _text(effort, f"{provider} {name} effort")
        if provider == "openai" and effort is not None:
            raise ValueError(f"OpenAI profile {name!r} cannot set Anthropic effort")
        if provider == "anthropic" and reasoning is not None:
            raise ValueError(f"Anthropic profile {name!r} cannot set OpenAI reasoning_effort")
        previous = model_ranks.setdefault(model_id, rank)
        if previous != rank:
            raise ValueError(f"model {model_id!r} has inconsistent capability ranks")
        profiles.append(
            ProviderModelProfile(provider, name, model_id, rank, reasoning, effort)
        )
    _require_distinct_names(tuple(profile.name for profile in profiles), f"{provider} profiles")
    return ProviderModels(provider, tuple(sorted(profiles, key=lambda item: item.name)))


def _decode_agent_models(
    artifact: Mapping[str, object], registry: ContractRegistry, namespace: str, source: str
) -> AgentModels:
    registry.validate(artifact, source=source)
    try:
        active_provider = _text(artifact["active_provider"], "active_provider").casefold()
        if namespace == ".codex" and active_provider != "openai":
            raise ValueError(".codex installations require active_provider 'openai'")
        if namespace == ".claude" and active_provider != "anthropic":
            raise ValueError(".claude installations require active_provider 'anthropic'")
        providers_artifact = _mapping(artifact["providers"], "providers")
        providers = tuple(
            _decode_provider_models(name, _mapping(providers_artifact[name], name))
            for name in ("anthropic", "openai")
        )
        provider_by_name = {provider.name: provider for provider in providers}
        roles_artifact = _mapping(artifact["roles"], "roles")
        roles: list[RoleModelDefaults] = []
        for raw_role, raw_defaults in roles_artifact.items():
            role = _text(raw_role, "role name")
            defaults = _mapping(raw_defaults, f"role {role}")
            openai = _text(defaults["openai"], f"role {role} openai profile")
            anthropic = _text(defaults["anthropic"], f"role {role} anthropic profile")
            provider_by_name["openai"].profile(openai)
            provider_by_name["anthropic"].profile(anthropic)
            roles.append(RoleModelDefaults(role, openai, anthropic))
        _require_distinct_names(tuple(item.role for item in roles), "roles")
        map_artifact = _mapping(artifact["policy_profile_map"], "policy_profile_map")
        mappings: list[PolicyProfileMapping] = []
        for raw_policy, raw_provider_profile in map_artifact.items():
            policy_name = _text(raw_policy, "policy profile name")
            profile_name = _text(raw_provider_profile, f"policy profile {policy_name}")
            for provider in providers:
                provider.profile(profile_name)
            mappings.append(PolicyProfileMapping(policy_name, profile_name))
        _require_distinct_names(
            tuple(item.policy_profile for item in mappings), "policy_profile_map"
        )
        for provider in providers:
            policy_lookup = {item.policy_profile: item.provider_profile for item in mappings}
            implementation = provider.profile(policy_lookup["implementation"])
            review = provider.profile(policy_lookup["review_high"])
            if review.capability_rank <= implementation.capability_rank:
                raise ValueError(
                    f"{provider.name} review_high must outrank implementation"
                )
        verified = date.fromisoformat(_text(artifact["verified_on"], "verified_on"))
        sources = _strings(artifact["sources"], "model source")
        return AgentModels(
            schema_version=_text(artifact["schema_version"], "model schema_version"),
            verified_on=verified,
            active_provider=active_provider,
            sources=sources,
            providers=providers,
            roles=tuple(sorted(roles, key=lambda item: item.role)),
            policy_profile_map=tuple(
                sorted(mappings, key=lambda item: item.policy_profile)
            ),
        )
    except DomainException:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise _failure(
            ErrorCategory.UNSUPPORTED_CAPABILITY,
            f"{source}: incompatible agent model configuration: {exc}",
            details={"source": source},
        ) from exc


def _normalize_policy_provider(value: object) -> str | None:
    if value is None:
        return None
    normalized = _text(value, "policy model provider").casefold()
    if normalized not in {"openai", "anthropic"}:
        raise ValueError(f"unknown policy model provider {value!r}")
    return normalized


def _decode_policy(
    artifact: Mapping[str, object],
    registry: ContractRegistry,
    models: AgentModels,
    source: str,
) -> ProjectPolicy:
    registry.validate(artifact, source=source)
    try:
        autonomous = _strings(
            artifact["autonomous_actions"], "autonomous_actions", sort=True
        )
        approval = _strings(artifact["approval_actions"], "approval_actions", sort=True)
        unknown = (set(autonomous) | set(approval)) - KNOWN_ACTIONS
        if unknown:
            raise ValueError(f"unknown policy actions: {', '.join(sorted(unknown))}")
        unsafe = set(autonomous) - SAFE_AUTONOMOUS_ACTIONS
        if unsafe:
            raise _failure(
                ErrorCategory.POLICY_DENIED,
                f"Sensitive actions cannot be autonomous: {', '.join(sorted(unsafe))}",
                details={"actions": sorted(unsafe)},
            )
        overlap = set(autonomous) & set(approval)
        if overlap:
            raise ValueError(
                f"actions cannot have two policy classes: {', '.join(sorted(overlap))}"
            )
        grants: list[ExternalGrant] = []
        for raw_grant in artifact["external_grants"]:
            grant = _mapping(raw_grant, "external grant")
            action = _text(grant["action"], "external grant action")
            if action not in approval:
                raise ValueError(
                    f"external grant action {action!r} is not approval-controlled"
                )
            grants.append(
                ExternalGrant(
                    action=action,
                    resource=_text(grant["resource"], "external grant resource"),
                    authority_ref=_text(
                        grant["authority_ref"], "external grant authority_ref"
                    ),
                )
            )
        if len(set(grants)) != len(grants):
            raise ValueError("external_grants contains duplicate entries")
        profiles: list[PolicyModelProfile] = []
        for raw_profile in artifact["model_profiles"]:
            profile = _mapping(raw_profile, "policy model profile")
            configured = profile["configured"]
            if not isinstance(configured, bool):
                raise TypeError("policy model configured must be a boolean")
            provider = _normalize_policy_provider(profile["provider"])
            model_id = (
                None
                if profile["model_id"] is None
                else _text(profile["model_id"], "policy model_id")
            )
            profiles.append(
                PolicyModelProfile(
                    name=_text(profile["name"], "policy model profile name"),
                    provider=provider,
                    model_id=model_id,
                    capability_rank=_integer(
                        profile["capability_rank"], "policy model capability_rank", 0
                    ),
                    configured=configured,
                )
            )
        profiles.sort(key=lambda item: item.name)
        _require_distinct_names(
            tuple(item.name for item in profiles), "policy model_profiles"
        )
        expected_profiles = {
            item.policy_profile for item in models.policy_profile_map
        }
        actual_profiles = {item.name for item in profiles}
        if actual_profiles != expected_profiles:
            missing = sorted(expected_profiles - actual_profiles)
            extra = sorted(actual_profiles - expected_profiles)
            raise ValueError(
                f"policy/model profile mismatch (missing={missing}, extra={extra})"
            )
        profile_by_name = {profile.name: profile for profile in profiles}
        if (
            profile_by_name["review_high"].capability_rank
            <= profile_by_name["implementation"].capability_rank
        ):
            raise ValueError("policy review_high must outrank implementation")
        for profile in profiles:
            if not profile.configured:
                continue
            if profile.provider is None or profile.model_id is None:
                raise ValueError(
                    f"configured policy profile {profile.name!r} requires provider and model_id"
                )
            if profile.provider != models.active_provider:
                raise ValueError(
                    f"configured policy profile {profile.name!r} does not use active_provider"
                )
            expected = models.provider_profile_for_policy(profile.name)
            if (
                profile.model_id != expected.model_id
                or profile.capability_rank != expected.capability_rank
            ):
                raise ValueError(
                    f"configured policy profile {profile.name!r} does not match "
                    "its model catalog profile"
                )
        required_sandbox = artifact["required_sandbox"]
        downgrade = artifact["allow_review_downgrade"]
        if not isinstance(required_sandbox, bool) or not isinstance(downgrade, bool):
            raise TypeError("policy boolean fields must be booleans")
        if downgrade:
            raise ValueError("review downgrade is unsupported")
        return ProjectPolicy(
            schema_version=_text(artifact["schema_version"], "policy schema_version"),
            id=_text(artifact["id"], "policy id"),
            autonomous_actions=autonomous,
            approval_actions=approval,
            external_grants=tuple(sorted(grants)),
            max_parallel=_integer(artifact["max_parallel"], "max_parallel", 1),
            max_review_cycles=_integer(
                artifact["max_review_cycles"], "max_review_cycles", 1
            ),
            max_rewrites=_integer(artifact["max_rewrites"], "max_rewrites", 0),
            max_agent_invocations=_integer(
                artifact["max_agent_invocations"], "max_agent_invocations", 1
            ),
            required_sandbox=required_sandbox,
            allow_review_downgrade=downgrade,
            model_profiles=tuple(profiles),
        )
    except DomainException:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"{source}: invalid or unsafe project policy: {exc}",
            details={"source": source},
        ) from exc


def load_project_settings(root: Path, installation: InstallationRecord) -> ProjectSettings:
    """Load validated project policy/model settings for one installation.

    Precedence is represented by :meth:`ProjectSettings.resolve_run`: built-in
    conservative defaults, the complete project policy, then a restrictive run
    override.  A saved run snapshot takes precedence during resume.
    """
    project_root = _checked_root(root)
    if not isinstance(installation, InstallationRecord):
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            "installation must be an InstallationRecord",
        )
    _validate_compatibility(installation)
    namespace = installation.namespace
    selected = _discover_namespace(project_root)
    if selected != namespace:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            "Installation argument does not match the project's workflow namespace",
            details={"expected_namespace": selected, "actual_namespace": namespace},
        )
    registry = _load_schema_registry(
        project_root, namespace, installation.installation_status
    )
    disk_installation_artifact = _read_json(
        project_root, f"{namespace}/framework.json"
    )
    disk_installation = _decode_installation(
        disk_installation_artifact, registry, f"{namespace}/framework.json"
    )
    if disk_installation != installation:
        raise _failure(
            ErrorCategory.STATE_CONFLICT,
            "Installation argument does not match the tracked installation record",
            details={"path": f"{namespace}/framework.json"},
        )
    policy_ref = f"{namespace}/project/policy.json"
    models_ref = f"{namespace}/project/agent-models.json"
    models_artifact = _read_json(project_root, models_ref)
    policy_artifact = _read_json(project_root, policy_ref)
    models = _decode_agent_models(models_artifact, registry, namespace, models_ref)
    policy = _decode_policy(policy_artifact, registry, models, policy_ref)
    return ProjectSettings(
        project_root=project_root,
        namespace=namespace,
        installation=installation,
        policy=policy,
        models=models,
        policy_ref=policy_ref,
        agent_models_ref=models_ref,
    )


__all__ = [
    "ActionRequirement",
    "AgentModels",
    "BUILT_IN_RUN_SETTINGS",
    "ExternalGrant",
    "InstallationRecord",
    "KNOWN_ACTIONS",
    "PolicyModelProfile",
    "PolicyProfileMapping",
    "ProjectPolicy",
    "ProjectSettings",
    "ProviderModelProfile",
    "ProviderModels",
    "RECORD_NAMESPACES",
    "RoleModelDefaults",
    "RunOverrides",
    "RunSettings",
    "SAFE_AUTONOMOUS_ACTIONS",
    "SENSITIVE_ACTIONS",
    "SUPPORTED_SCHEMA_COMPATIBILITY",
    "decode_installation_record",
    "decode_run_settings",
    "load_installation_record",
    "load_project_settings",
]
