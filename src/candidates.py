"""Deterministic, IO-free construction of immutable review candidates.

Git inspection, context discovery, validation execution, and persistence belong to
their respective adapters.  This module accepts the exact bytes those services
observed and binds them to the v1 candidate record.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, TypeAlias

from contracts import ContractRegistry
from domain_values import (
    DomainError,
    DomainException,
    ErrorCategory,
    PlanId,
    Revision,
    ScopePath,
    Sha256Digest,
)


SCHEMA_VERSION = "1.0"
KIND = "candidate"

_TASK_ID = re.compile(r"TASK-[0-9]{3,}\Z")
_GIT_OID = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})\Z")

BytesInput: TypeAlias = bytes | bytearray | memoryview


def _bytes(value: BytesInput, label: str) -> bytes:
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError(f"{label} must be bytes-like")
    return bytes(value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if not value:
        raise ValueError(f"{label} cannot be empty")
    return value


def _canonical_path(value: object, label: str) -> tuple[str, tuple[str, ...]]:
    path = _text(value, label)
    scope_path = ScopePath.exact_file(path)
    if scope_path.as_wire() != path:
        raise ValueError(f"{label} must use canonical repository path syntax")
    return path, scope_path.comparison_key


def _git_oid(value: object, label: str) -> str:
    oid = _text(value, label)
    if _GIT_OID.fullmatch(oid) is None:
        raise ValueError(f"{label} must be a full 40- or 64-character lowercase Git object ID")
    return oid


def _task_id(value: object) -> str | None:
    if value is None:
        return None
    task_id = _text(value, "task ID")
    if _TASK_ID.fullmatch(task_id) is None:
        raise ValueError("task ID must match TASK-[0-9]{3,}")
    return task_id


def _iterable(values: Iterable[Any], label: str) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes, bytearray, memoryview)):
        raise TypeError(f"{label} must be an iterable of values")
    try:
        return tuple(values)
    except TypeError as exc:
        raise TypeError(f"{label} must be iterable") from exc


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _plain_json(value: object) -> object:
    """Detach immutable Mapping/tuple JSON into encoder-native containers."""

    if isinstance(value, Mapping):
        return {key: _plain_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json(item) for item in value]
    return value


def _canonical_json(value: Mapping[str, object]) -> bytes:
    try:
        text = json.dumps(
            _plain_json(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return text.encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError(f"candidate is not canonical UTF-8 JSON: {exc}") from exc


@dataclass(frozen=True, slots=True)
class MaterialInput:
    """A canonical repository path and a defensive copy of its exact bytes."""

    path: str
    content: bytes

    def __post_init__(self) -> None:
        path, _ = _canonical_path(self.path, "material path")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "content", _bytes(self.content, "material content"))

    @property
    def alias_key(self) -> tuple[str, ...]:
        return _canonical_path(self.path, "material path")[1]


def _materials(
    values: Iterable[MaterialInput],
    label: str,
    *,
    required: bool,
) -> tuple[MaterialInput, ...]:
    material = _iterable(values, label)
    if required and not material:
        raise ValueError(f"{label} must contain at least one material input")
    if not all(isinstance(item, MaterialInput) for item in material):
        raise TypeError(f"{label} must contain MaterialInput values")
    return tuple(sorted(material, key=lambda item: (item.alias_key, item.path)))


def _required_paths(values: Iterable[str], label: str) -> tuple[str, ...]:
    paths = _iterable(values, label)
    normalized: list[tuple[str, tuple[str, ...]]] = []
    for value in paths:
        normalized.append(_canonical_path(value, f"{label} path"))
    aliases: dict[tuple[str, ...], str] = {}
    for path, alias_key in normalized:
        prior = aliases.get(alias_key)
        if prior is not None:
            raise ValueError(
                f"{label} contains duplicate or aliased paths {prior!r} and {path!r}"
            )
        aliases[alias_key] = path
    return tuple(
        path for path, _ in sorted(normalized, key=lambda item: (item[1], item[0]))
    )


def _reject_aliases(values: Iterable[MaterialInput], label: str) -> None:
    seen: dict[tuple[str, ...], str] = {}
    for item in values:
        prior = seen.get(item.alias_key)
        if prior is not None:
            raise ValueError(
                f"{label} contains duplicate or aliased paths {prior!r} and {item.path!r}"
            )
        seen[item.alias_key] = item.path


def _require_materials(
    materials: tuple[MaterialInput, ...],
    required_paths: tuple[str, ...],
    label: str,
) -> None:
    supplied = {material.alias_key: material.path for material in materials}
    missing: list[str] = []
    for required_path in required_paths:
        _, alias_key = _canonical_path(required_path, f"required {label} path")
        supplied_path = supplied.get(alias_key)
        if supplied_path is None:
            missing.append(required_path)
        elif supplied_path != required_path:
            raise ValueError(
                f"{label} required path {required_path!r} aliases supplied path "
                f"{supplied_path!r}"
            )
    if missing:
        raise ValueError(f"{label} is missing required material inputs: {missing!r}")


@dataclass(frozen=True, slots=True, init=False)
class CandidateContext:
    """Applicable context roles, frozen and ordered independently of caller order.

    Context discovery owns applicability.  The caller must pass every applicable ADR
    and dependency-handoff path in the corresponding ``required_*_paths`` argument.
    An empty required-path collection explicitly means that role does not apply.
    """

    plan: MaterialInput
    graph: MaterialInput
    specs: tuple[MaterialInput, ...]
    adrs: tuple[MaterialInput, ...]
    contracts: tuple[MaterialInput, ...]
    handoffs: tuple[MaterialInput, ...]
    supplemental: tuple[MaterialInput, ...]
    required_adr_paths: tuple[str, ...]
    required_handoff_paths: tuple[str, ...]

    def __init__(
        self,
        *,
        plan: MaterialInput,
        graph: MaterialInput,
        specs: Iterable[MaterialInput],
        adrs: Iterable[MaterialInput],
        contracts: Iterable[MaterialInput],
        handoffs: Iterable[MaterialInput],
        required_adr_paths: Iterable[str],
        required_handoff_paths: Iterable[str],
        supplemental: Iterable[MaterialInput] = (),
    ) -> None:
        if not isinstance(plan, MaterialInput):
            raise TypeError("plan context must be a MaterialInput")
        if not isinstance(graph, MaterialInput):
            raise TypeError("graph context must be a MaterialInput")
        specs_tuple = _materials(specs, "spec context", required=True)
        adrs_tuple = _materials(adrs, "ADR context", required=False)
        contracts_tuple = _materials(contracts, "contract context", required=True)
        handoffs_tuple = _materials(handoffs, "handoff context", required=False)
        supplemental_tuple = _materials(supplemental, "supplemental context", required=False)
        required_adrs = _required_paths(required_adr_paths, "required ADR context")
        required_handoffs = _required_paths(
            required_handoff_paths,
            "required handoff context",
        )
        _require_materials(adrs_tuple, required_adrs, "ADR context")
        _require_materials(handoffs_tuple, required_handoffs, "handoff context")
        ordered = (
            (plan,)
            + (graph,)
            + specs_tuple
            + adrs_tuple
            + contracts_tuple
            + handoffs_tuple
            + supplemental_tuple
        )
        _reject_aliases(ordered, "candidate context")
        object.__setattr__(self, "plan", plan)
        object.__setattr__(self, "graph", graph)
        object.__setattr__(self, "specs", specs_tuple)
        object.__setattr__(self, "adrs", adrs_tuple)
        object.__setattr__(self, "contracts", contracts_tuple)
        object.__setattr__(self, "handoffs", handoffs_tuple)
        object.__setattr__(self, "supplemental", supplemental_tuple)
        object.__setattr__(self, "required_adr_paths", required_adrs)
        object.__setattr__(self, "required_handoff_paths", required_handoffs)

    @property
    def ordered(self) -> tuple[MaterialInput, ...]:
        return (
            (self.plan, self.graph)
            + self.specs
            + self.adrs
            + self.contracts
            + self.handoffs
            + self.supplemental
        )


@dataclass(frozen=True, slots=True, init=False)
class CandidateRequest:
    """All material inputs needed to construct or recheck one candidate."""

    candidate_id: str
    task_id: str | None
    plan_id: PlanId
    graph_revision: Revision
    base_oid: str
    head_oid: str
    diff: bytes
    context: CandidateContext
    validation: tuple[MaterialInput, ...]
    checklist_version: str
    policy: bytes
    model_profile: bytes

    def __init__(
        self,
        *,
        candidate_id: str,
        task_id: str | None,
        plan_id: PlanId | str,
        graph_revision: Revision | int,
        base_oid: str,
        head_oid: str,
        diff: BytesInput,
        context: CandidateContext,
        validation: Iterable[MaterialInput],
        checklist_version: str,
        policy: BytesInput,
        model_profile: BytesInput,
    ) -> None:
        if not isinstance(context, CandidateContext):
            raise TypeError("context must be a CandidateContext")
        plan = plan_id if isinstance(plan_id, PlanId) else PlanId(plan_id)
        revision = (
            graph_revision
            if isinstance(graph_revision, Revision)
            else Revision(graph_revision)
        )
        validation_tuple = _materials(validation, "validation evidence", required=True)
        _reject_aliases(
            context.ordered + validation_tuple,
            "candidate context and validation evidence",
        )
        object.__setattr__(self, "candidate_id", _text(candidate_id, "candidate ID"))
        object.__setattr__(self, "task_id", _task_id(task_id))
        object.__setattr__(self, "plan_id", plan)
        object.__setattr__(self, "graph_revision", revision)
        object.__setattr__(self, "base_oid", _git_oid(base_oid, "base OID"))
        object.__setattr__(self, "head_oid", _git_oid(head_oid, "head OID"))
        object.__setattr__(self, "diff", _bytes(diff, "diff"))
        object.__setattr__(self, "context", context)
        object.__setattr__(self, "validation", validation_tuple)
        object.__setattr__(self, "checklist_version", _text(checklist_version, "checklist version"))
        object.__setattr__(self, "policy", _bytes(policy, "policy"))
        object.__setattr__(self, "model_profile", _bytes(model_profile, "model profile"))


@dataclass(frozen=True, slots=True)
class ContentRef:
    """An immutable v1 path/digest pair."""

    path: str
    sha256: Sha256Digest

    def __post_init__(self) -> None:
        path, _ = _canonical_path(self.path, "content reference path")
        digest = self.sha256 if isinstance(self.sha256, Sha256Digest) else Sha256Digest(self.sha256)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "sha256", digest)

    @property
    def alias_key(self) -> tuple[str, ...]:
        return _canonical_path(self.path, "content reference path")[1]

    def to_wire(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256.value}


def _refs_from_wire(value: object, label: str) -> tuple[ContentRef, ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{label} must be an array")
    refs: list[ContentRef] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise TypeError(f"{label} entries must be objects")
        refs.append(ContentRef(path=item["path"], sha256=item["sha256"]))
    if not refs:
        raise ValueError(f"{label} cannot be empty")
    aliases: dict[tuple[str, ...], str] = {}
    for ref in refs:
        prior = aliases.get(ref.alias_key)
        if prior is not None:
            raise ValueError(f"{label} contains duplicate or aliased paths {prior!r} and {ref.path!r}")
        aliases[ref.alias_key] = ref.path
    return tuple(refs)


@dataclass(frozen=True, slots=True)
class Candidate:
    """An immutable, schema-shaped candidate whose fingerprint excludes itself."""

    candidate_id: str
    task_id: str | None
    plan_id: PlanId
    graph_revision: Revision
    base_oid: str
    head_oid: str
    diff_sha256: Sha256Digest
    context_refs: tuple[ContentRef, ...]
    validation_refs: tuple[ContentRef, ...]
    checklist_version: str
    policy_model_digest: Sha256Digest
    fingerprint: Sha256Digest

    def __post_init__(self) -> None:
        candidate_id = _text(self.candidate_id, "candidate ID")
        task_id = _task_id(self.task_id)
        plan_id = self.plan_id if isinstance(self.plan_id, PlanId) else PlanId(self.plan_id)
        revision = (
            self.graph_revision
            if isinstance(self.graph_revision, Revision)
            else Revision(self.graph_revision)
        )
        diff_digest = (
            self.diff_sha256
            if isinstance(self.diff_sha256, Sha256Digest)
            else Sha256Digest(self.diff_sha256)
        )
        context_refs = _iterable(self.context_refs, "context_refs")
        validation_refs = _iterable(self.validation_refs, "validation_refs")
        if not context_refs or not validation_refs:
            raise ValueError("candidate context and validation references cannot be empty")
        if not all(isinstance(reference, ContentRef) for reference in context_refs + validation_refs):
            raise TypeError("candidate references must contain ContentRef values")
        aliases: dict[tuple[str, ...], str] = {}
        for reference in context_refs + validation_refs:
            prior = aliases.get(reference.alias_key)
            if prior is not None:
                raise ValueError(
                    "candidate references contain duplicate or aliased paths "
                    f"{prior!r} and {reference.path!r}"
                )
            aliases[reference.alias_key] = reference.path
        policy_digest = (
            self.policy_model_digest
            if isinstance(self.policy_model_digest, Sha256Digest)
            else Sha256Digest(self.policy_model_digest)
        )
        fingerprint = (
            self.fingerprint
            if isinstance(self.fingerprint, Sha256Digest)
            else Sha256Digest(self.fingerprint)
        )
        object.__setattr__(self, "candidate_id", candidate_id)
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "graph_revision", revision)
        object.__setattr__(self, "base_oid", _git_oid(self.base_oid, "base OID"))
        object.__setattr__(self, "head_oid", _git_oid(self.head_oid, "head OID"))
        object.__setattr__(self, "diff_sha256", diff_digest)
        object.__setattr__(self, "context_refs", context_refs)
        object.__setattr__(self, "validation_refs", validation_refs)
        object.__setattr__(
            self,
            "checklist_version",
            _text(self.checklist_version, "checklist version"),
        )
        object.__setattr__(self, "policy_model_digest", policy_digest)
        object.__setattr__(self, "fingerprint", fingerprint)
        expected = _sha256(_canonical_json(self.unsigned_wire()))
        if fingerprint.value != expected:
            raise ValueError("candidate fingerprint does not match its unsigned v1 record")

    def unsigned_wire(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": KIND,
            "id": self.candidate_id,
            "task_id": self.task_id,
            "plan_id": self.plan_id.value,
            "graph_revision": self.graph_revision.value,
            "base_oid": self.base_oid,
            "head_oid": self.head_oid,
            "diff_sha256": self.diff_sha256.value,
            "context_refs": [reference.to_wire() for reference in self.context_refs],
            "validation_refs": [reference.to_wire() for reference in self.validation_refs],
            "checklist_version": self.checklist_version,
            "policy_model_digest": self.policy_model_digest.value,
        }

    def to_wire(self) -> dict[str, object]:
        artifact = self.unsigned_wire()
        artifact["fingerprint"] = self.fingerprint.value
        return artifact


def _refs(materials: Iterable[MaterialInput]) -> tuple[ContentRef, ...]:
    return tuple(
        ContentRef(path=material.path, sha256=Sha256Digest(_sha256(material.content)))
        for material in materials
    )


def _candidate_from_unsigned(
    unsigned: Mapping[str, object],
    *,
    fingerprint: str | None = None,
) -> Candidate:
    calculated = _sha256(_canonical_json(unsigned))
    if fingerprint is not None and fingerprint != calculated:
        raise ValueError("candidate fingerprint does not match its unsigned v1 record")
    return Candidate(
        candidate_id=unsigned["id"],
        task_id=_task_id(unsigned["task_id"]),
        plan_id=PlanId(unsigned["plan_id"]),
        graph_revision=Revision(unsigned["graph_revision"]),
        base_oid=_git_oid(unsigned["base_oid"], "base OID"),
        head_oid=_git_oid(unsigned["head_oid"], "head OID"),
        diff_sha256=Sha256Digest(unsigned["diff_sha256"]),
        context_refs=_refs_from_wire(unsigned["context_refs"], "context_refs"),
        validation_refs=_refs_from_wire(unsigned["validation_refs"], "validation_refs"),
        checklist_version=_text(unsigned["checklist_version"], "checklist version"),
        policy_model_digest=Sha256Digest(unsigned["policy_model_digest"]),
        fingerprint=Sha256Digest(calculated),
    )


def build_candidate(request: CandidateRequest, registry: ContractRegistry) -> Candidate:
    """Hash one immutable input snapshot and validate the emitted v1 record."""

    if not isinstance(request, CandidateRequest):
        raise TypeError("request must be a CandidateRequest")
    context_refs = _refs(request.context.ordered)
    validation_refs = _refs(request.validation)
    unsigned: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "id": request.candidate_id,
        "task_id": request.task_id,
        "plan_id": request.plan_id.value,
        "graph_revision": request.graph_revision.value,
        "base_oid": request.base_oid,
        "head_oid": request.head_oid,
        "diff_sha256": _sha256(request.diff),
        "context_refs": [reference.to_wire() for reference in context_refs],
        "validation_refs": [reference.to_wire() for reference in validation_refs],
        "checklist_version": request.checklist_version,
        # This ordering preserves the repository's existing v1 candidate convention.
        "policy_model_digest": _sha256(request.policy + request.model_profile),
    }
    candidate = _candidate_from_unsigned(unsigned)
    registry.validate(candidate.to_wire(), source=f"candidate {request.candidate_id}")
    return candidate


def candidate_from_wire(
    artifact: Mapping[str, object],
    registry: ContractRegistry,
) -> Candidate:
    """Validate and freeze a serialized candidate, including its fingerprint."""

    registry.validate(artifact, source="candidate record")
    unsigned = {key: value for key, value in artifact.items() if key != "fingerprint"}
    return _candidate_from_unsigned(unsigned, fingerprint=artifact["fingerprint"])


def verify_candidate(
    candidate: Candidate | Mapping[str, object],
    current: CandidateRequest,
    registry: ContractRegistry,
) -> Candidate:
    """Return the candidate only when every current material input still matches."""

    observed = (
        candidate
        if isinstance(candidate, Candidate)
        else candidate_from_wire(candidate, registry)
    )
    registry.validate(observed.to_wire(), source=f"candidate {observed.candidate_id}")
    expected = build_candidate(current, registry)
    observed_wire = observed.to_wire()
    expected_wire = expected.to_wire()
    changed = tuple(
        key for key in expected_wire if observed_wire.get(key) != expected_wire[key]
    )
    if changed:
        raise DomainException(
            DomainError(
                category=ErrorCategory.STATE_CONFLICT,
                message="candidate is stale for the supplied material inputs",
                details={"changed_fields": changed},
            )
        )
    return observed


__all__ = [
    "Candidate",
    "CandidateContext",
    "CandidateRequest",
    "ContentRef",
    "MaterialInput",
    "build_candidate",
    "candidate_from_wire",
    "verify_candidate",
]
