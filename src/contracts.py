"""Offline v1 JSON contracts, logical references, and structural identities.

The registry deliberately has no retrieval callback.  Every schema resource used
to validate a record must be present in the supplied local ``schemas/v1``
directory, so validation cannot depend on network availability.
"""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any
from urllib.parse import urldefrag, urljoin

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

from domain_values import (
    DomainError,
    DomainException,
    EntityId,
    ErrorCategory,
    PlanId,
    RecordRef,
)


SCHEMA_VERSION = "1.0"
SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID_PREFIX = "https://ai-engineering.invalid/schemas/v1/"
STRUCTURAL_TASK_FIELDS = (
    "id",
    "plan_id",
    "title",
    "objective",
    "depends_on",
    "scope",
    "acceptance_criteria",
    "plan_acceptance_ids",
    "spec_refs",
    "adr_refs",
    "research_refs",
    "input_contracts",
    "output_contracts",
    "validation_commands",
    "estimated_production_files",
    "size_rationale",
    "out_of_scope",
    "handoff_requirements",
)

_PLAN_LOCATION = re.compile(
    r"(?P<prefix>^(?:\.ai|\.codex|\.claude)[\\/]plans[\\/])"
    r"(?:completed|archived)(?=[\\/]PLAN-[0-9]{3,}(?:[\\/]|$))"
)
_TASK_LOCATION = re.compile(
    r"(?P<prefix>^(?:\.ai|\.codex|\.claude)[\\/]plans[\\/]"
    r"(?:current|completed|archived)[\\/]PLAN-[0-9]{3,}[\\/]tasks[\\/])"
    r"(?:completed|archived)(?=[\\/]TASK-[0-9]{3,}(?:\.json)?(?:$|[^A-Za-z0-9_.-]))"
)


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


def _read_schema(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Cannot read JSON Schema {path}: {exc}",
            details={"path": str(path)},
        ) from exc
    if not isinstance(value, dict):
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Expected a JSON object in schema {path}",
            details={"path": str(path)},
        )
    return value


def _references(value: object) -> tuple[str, ...]:
    found: list[str] = []
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, Mapping):
            for keyword in ("$ref", "$dynamicRef"):
                reference = item.get(keyword)
                if isinstance(reference, str):
                    found.append(reference)
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return tuple(found)


def _plain_json(value: object) -> object:
    """Detach immutable Mapping/tuple values into jsonschema's native containers."""
    if isinstance(value, Mapping):
        return {str(key): _plain_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json(item) for item in value]
    return value


class ContractRegistry:
    """A closed collection of locally loaded v1 validators."""

    __slots__ = ("_schemas", "_schema_ids", "_registry", "_validators")

    def __init__(self, schema_root: Path) -> None:
        root = Path(schema_root)
        paths = sorted(root.glob("*.schema.json")) if root.is_dir() else []
        if not paths:
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"No v1 JSON schemas found in {root}",
                details={"schema_root": str(root)},
            )

        schemas: dict[str, dict[str, Any]] = {}
        schema_ids: dict[str, str] = {}
        for path in paths:
            schema = _read_schema(path)
            properties = schema.get("properties")
            kind_schema = properties.get("kind") if isinstance(properties, Mapping) else None
            version_schema = (
                properties.get("schema_version") if isinstance(properties, Mapping) else None
            )
            kind = kind_schema.get("const") if isinstance(kind_schema, Mapping) else None
            version = version_schema.get("const") if isinstance(version_schema, Mapping) else None
            schema_id = schema.get("$id")
            expected_kind = path.name.removesuffix(".schema.json")
            expected_id = SCHEMA_ID_PREFIX + path.name
            if schema.get("$schema") != SCHEMA_DIALECT:
                raise _failure(
                    ErrorCategory.UNSUPPORTED_CAPABILITY,
                    f"Unsupported JSON Schema dialect in {path}",
                    details={"path": str(path), "dialect": schema.get("$schema")},
                )
            if version != SCHEMA_VERSION:
                raise _failure(
                    ErrorCategory.UNSUPPORTED_CAPABILITY,
                    f"Unsupported schema version in {path}: {version!r}",
                    details={"path": str(path), "schema_version": version},
                )
            if kind != expected_kind or schema_id != expected_id:
                raise _failure(
                    ErrorCategory.INVALID_INPUT,
                    f"Schema identity does not match its filename: {path}",
                    details={"path": str(path), "kind": kind, "schema_id": schema_id},
                )
            if schema.get("additionalProperties") is not False:
                raise _failure(
                    ErrorCategory.INVALID_INPUT,
                    f"Artifact schema must reject unknown top-level fields: {path}",
                    details={"path": str(path)},
                )
            if kind in schemas or schema_id in schema_ids:
                raise _failure(
                    ErrorCategory.INVALID_INPUT,
                    f"Duplicate schema identity in {root}: {kind!r}",
                    details={"path": str(path), "kind": kind},
                )
            try:
                Draft202012Validator.check_schema(schema)
            except SchemaError as exc:
                raise _failure(
                    ErrorCategory.INVALID_INPUT,
                    f"Invalid JSON Schema {path}: {exc.message}",
                    details={"path": str(path)},
                ) from exc
            schemas[kind] = schema
            schema_ids[schema_id] = kind

        for kind, schema in schemas.items():
            schema_id = str(schema["$id"])
            for reference in _references(schema):
                target, _ = urldefrag(urljoin(schema_id, reference))
                if target != schema_id and target not in schema_ids:
                    raise _failure(
                        ErrorCategory.UNSUPPORTED_CAPABILITY,
                        f"Schema {kind!r} references unavailable offline resource {reference!r}",
                        details={"kind": kind, "reference": reference},
                    )

        registry = Registry().with_resources(
            (schema_id, Resource.from_contents(schemas[kind]))
            for schema_id, kind in schema_ids.items()
        )
        validators = {
            kind: Draft202012Validator(
                schema,
                registry=registry,
                format_checker=FormatChecker(),
            )
            for kind, schema in schemas.items()
        }
        self._schemas = MappingProxyType(schemas)
        self._schema_ids = MappingProxyType(schema_ids)
        self._registry = registry
        self._validators = MappingProxyType(validators)

    @property
    def kinds(self) -> tuple[str, ...]:
        return tuple(sorted(self._schemas))

    @property
    def schema_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._schema_ids))

    def schema(self, kind: str) -> Mapping[str, Any]:
        try:
            return deepcopy(self._schemas[kind])
        except (KeyError, TypeError) as exc:
            raise _failure(
                ErrorCategory.UNSUPPORTED_CAPABILITY,
                f"Unknown artifact kind: {kind!r}",
                details={"kind": kind},
            ) from exc

    def validate(self, artifact: Mapping[str, object], *, source: str = "artifact") -> None:
        if not isinstance(artifact, Mapping):
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"{source}: artifact must be a JSON object",
            )
        kind = artifact.get("kind")
        version = artifact.get("schema_version")
        if isinstance(version, str) and version != SCHEMA_VERSION:
            raise _failure(
                ErrorCategory.UNSUPPORTED_CAPABILITY,
                f"{source}: unsupported schema_version {version!r}",
                details={"schema_version": version},
            )
        if not isinstance(kind, str):
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"{source}: artifact kind must be a string",
            )
        validator = self._validators.get(kind)
        if validator is None:
            raise _failure(
                ErrorCategory.UNSUPPORTED_CAPABILITY,
                f"{source}: unknown artifact kind {kind!r}",
                details={"kind": kind},
            )
        try:
            error = next(validator.iter_errors(_plain_json(artifact)), None)
        except Unresolvable as exc:
            raise _failure(
                ErrorCategory.VALIDATION_FAILED,
                f"{source}: {kind} contract contains an unresolvable offline reference: {exc}",
                details={"kind": kind},
            ) from exc
        if error is None:
            return
        assert isinstance(error, ValidationError)
        location = "/" + "/".join(str(component) for component in error.absolute_path)
        raise _failure(
            ErrorCategory.VALIDATION_FAILED,
            f"{source}: {kind} contract violation at {location}: {error.message}",
            details={"kind": kind, "path": location},
        )


def load_contract_registry(schema_root: Path) -> ContractRegistry:
    """Load all v1 schemas from *schema_root* into a closed local registry."""
    return ContractRegistry(schema_root)


def parse_record_ref(
    value: str,
    *,
    expected_plan_id: PlanId | str | None = None,
    expected_kind: str | None = None,
) -> RecordRef:
    """Parse ``kind:id`` or ``kind:plan-id:id`` through shared domain values."""
    if not isinstance(value, str):
        raise _failure(ErrorCategory.INVALID_INPUT, "record reference must be a string")
    parts = value.split(":")
    try:
        if len(parts) == 2:
            kind, local_id = parts
            reference = RecordRef(kind=kind, local_id=EntityId(local_id))
        elif len(parts) == 3:
            kind, plan_id, local_id = parts
            reference = RecordRef(
                kind=kind,
                plan_id=PlanId(plan_id),
                local_id=EntityId(local_id),
            )
        else:
            raise ValueError("record reference must contain two or three colon-separated parts")
    except (TypeError, ValueError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Invalid logical record reference {value!r}: {exc}",
            details={"reference": value},
        ) from exc

    if expected_kind is not None and reference.kind != expected_kind:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Logical record reference {value!r} has kind {reference.kind!r}, "
            f"expected {expected_kind!r}",
            details={"reference": value, "expected_kind": expected_kind},
        )
    if expected_plan_id is not None:
        try:
            expected_plan = (
                expected_plan_id
                if isinstance(expected_plan_id, PlanId)
                else PlanId(expected_plan_id)
            )
        except (TypeError, ValueError) as exc:
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"Invalid expected plan ID: {exc}",
            ) from exc
        if reference.plan_id != expected_plan:
            raise _failure(
                ErrorCategory.INVALID_INPUT,
                f"Logical record reference {value!r} is not qualified by {expected_plan}",
                details={"reference": value, "expected_plan_id": expected_plan.value},
            )
    return reference


def _canonicalize_location(value: str) -> str:
    task_canonical = _TASK_LOCATION.sub(lambda match: match.group("prefix") + "current", value)
    return _PLAN_LOCATION.sub(lambda match: match.group("prefix") + "current", task_canonical)


def _canonicalize_structural_value(value: object) -> object:
    if isinstance(value, str):
        return _canonicalize_location(value)
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize_structural_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_canonicalize_structural_value(item) for item in value]
    return value


def structural_task_digest(tasks: Sequence[Mapping[str, object]]) -> str:
    """Hash lifecycle-neutral task structure using the bootstrap wire encoding."""
    try:
        ordered = sorted(tasks, key=lambda item: str(item["id"]))
        projected = [
            {
                field: _canonicalize_structural_value(task[field])
                for field in STRUCTURAL_TASK_FIELDS
            }
            for task in ordered
        ]
        payload = json.dumps(
            projected,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise _failure(
            ErrorCategory.INVALID_INPUT,
            f"Cannot compute structural task digest: {exc}",
        ) from exc
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = [
    "ContractRegistry",
    "SCHEMA_DIALECT",
    "SCHEMA_ID_PREFIX",
    "SCHEMA_VERSION",
    "STRUCTURAL_TASK_FIELDS",
    "load_contract_registry",
    "parse_record_ref",
    "structural_task_digest",
]
