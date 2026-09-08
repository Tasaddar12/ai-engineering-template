"""Configured agent dispatch checks and a deterministic fake adapter.

The fake provider is an offline simulation.  It never reads provider-native
configuration, credentials, or the network.  ``FakeAgentProviderState`` is
deliberately separate from canonical workflow state: retaining that object lets
a newly constructed adapter reconnect to an already-started fake effect through
the normal idempotent ``start`` and ``poll`` methods.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import NoReturn

from config import ProjectSettings, ProviderModelProfile
from domain_values import (
    AgentOutputStatus,
    AgentRunStatus,
    DomainError,
    DomainException,
    EntityId,
    ErrorCategory,
    EvidenceRef,
    FrozenJsonObject,
    PlanId,
    Revision,
    ScopeClaim,
    ScopePath,
    Sha256Digest,
)
from workflow_ports import (
    AcceptanceCriterion,
    AgentAdapter,
    AgentHandle,
    AgentObservation,
    AgentOutputRecord,
    AgentRequest,
    AgentRunRecord,
    CancelObservation,
    CancelStatus,
    ModelIdentity,
)


SIMULATION_SOURCE = "deterministic_fake_agent"
_FAKE_STATE_FORMAT = "deterministic-fake-agent-state-v1"
_DEFAULT_REVIEW_ROLES = (
    "consistency-reviewer",
    "evidence-reviewer",
    "implementation-reviewer",
    "plan-integration-reviewer",
    "security-reviewer",
    "task-isolation-reviewer",
)
_TERMINAL_AGENT_STATUSES = {
    AgentRunStatus.SUCCEEDED,
    AgentRunStatus.FAILED,
    AgentRunStatus.CANCELLED,
}
_QUIESCED_CANCEL_STATUSES = {
    CancelStatus.CANCELLED,
    CancelStatus.ALREADY_TERMINAL,
}


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and have no surrounding whitespace")
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value):
        raise ValueError(f"{label} contains a control or invisible formatting character")
    return unicodedata.normalize("NFC", value)


def _texts(values: Iterable[str], label: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{label} must be an iterable, not a scalar string")
    try:
        result = tuple(_text(value, f"{label} item") for value in values)
    except TypeError as exc:
        raise TypeError(f"{label} must be iterable") from exc
    aliases = [unicodedata.normalize("NFKC", value).casefold() for value in result]
    if len(set(aliases)) != len(aliases):
        raise ValueError(f"{label} must not contain duplicate or aliased values")
    return result


def _failure(
    category: ErrorCategory,
    message: str,
    *,
    details: Mapping[str, object] | None = None,
) -> NoReturn:
    raise DomainException(
        DomainError(
            category=category,
            message=message,
            retryable=False,
            details={} if details is None else details,
        )
    )


def _effect_token(project_id: str, adapter_id: str, idempotency_key: str) -> str:
    content = "\n".join((project_id, adapter_id, idempotency_key)).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _require_keys(
    value: Mapping[str, object], expected: set[str], label: str
) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} has unknown or missing fields")


def _array(value: object, label: str) -> tuple[object, ...]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be an array")
    return tuple(value)


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    return value


def _boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} must be a boolean")
    return value


def _optional_text(value: object, label: str) -> str | None:
    return None if value is None else _text(value, label)


def _datetime(value: object, label: str) -> datetime | None:
    if value is None:
        return None
    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO 8601 datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return parsed


def _wire(value: object) -> object:
    """Project trusted DTOs into the fake provider's private JSON format."""

    if isinstance(value, ScopePath):
        return value.as_wire()
    if isinstance(value, ScopeClaim):
        return value.to_wire()
    if isinstance(value, (EntityId, PlanId, Revision, Sha256Digest)):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, FrozenJsonObject):
        return value.to_dict()
    if is_dataclass(value):
        return {item.name: _wire(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, tuple):
        return [_wire(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"cannot serialize fake provider value {type(value).__name__}")


def _decode_evidence(value: object) -> EvidenceRef:
    item = _mapping(value, "evidence reference")
    _require_keys(item, {"path", "sha256", "metadata"}, "evidence reference")
    return EvidenceRef(
        path=_text(item.get("path"), "evidence path"),
        sha256=_text(item.get("sha256"), "evidence sha256"),
        metadata=_mapping(item.get("metadata", {}), "evidence metadata"),
    )


def _decode_error(value: object) -> DomainError | None:
    if value is None:
        return None
    item = _mapping(value, "domain error")
    _require_keys(
        item,
        {"category", "message", "retryable", "evidence_refs", "details"},
        "domain error",
    )
    return DomainError(
        category=_text(item.get("category"), "error category"),
        message=_text(item.get("message"), "error message"),
        retryable=_boolean(item.get("retryable"), "error retryable"),
        evidence_refs=tuple(
            _decode_evidence(reference)
            for reference in _array(item.get("evidence_refs"), "error evidence_refs")
        ),
        details=_mapping(item.get("details"), "error details"),
    )


def _decode_model(value: object) -> ModelIdentity:
    item = _mapping(value, "model identity")
    _require_keys(
        item,
        {"profile", "provider", "model_id", "capability_rank", "invocation_id"},
        "model identity",
    )
    return ModelIdentity(
        profile=_text(item.get("profile"), "model profile"),
        provider=_text(item.get("provider"), "model provider"),
        model_id=_text(item.get("model_id"), "model ID"),
        capability_rank=_integer(item.get("capability_rank"), "model capability rank"),
        invocation_id=_text(item.get("invocation_id"), "model invocation ID"),
    )


def _decode_provider_model(value: object) -> ProviderModelProfile:
    item = _mapping(value, "configured provider model")
    _require_keys(
        item,
        {
            "provider",
            "name",
            "model_id",
            "capability_rank",
            "reasoning_effort",
            "effort",
        },
        "configured provider model",
    )
    return ProviderModelProfile(
        provider=_text(item.get("provider"), "configured model provider"),
        name=_text(item.get("name"), "configured model profile"),
        model_id=_text(item.get("model_id"), "configured model ID"),
        capability_rank=_integer(
            item.get("capability_rank"), "configured model capability rank"
        ),
        reasoning_effort=_optional_text(
            item.get("reasoning_effort"), "configured reasoning effort"
        ),
        effort=_optional_text(item.get("effort"), "configured effort"),
    )


def _decode_handle(value: object) -> AgentHandle:
    item = _mapping(value, "agent handle")
    _require_keys(
        item,
        {
            "project_id",
            "plan_id",
            "run_id",
            "request_id",
            "attempt_id",
            "lease_generation",
            "adapter_id",
            "idempotency_key",
            "external_handle",
        },
        "agent handle",
    )
    return AgentHandle(
        project_id=_text(item.get("project_id"), "handle project_id"),
        plan_id=_text(item.get("plan_id"), "handle plan_id"),
        run_id=_text(item.get("run_id"), "handle run_id"),
        request_id=_text(item.get("request_id"), "handle request_id"),
        attempt_id=_text(item.get("attempt_id"), "handle attempt_id"),
        lease_generation=_integer(
            item.get("lease_generation"), "handle lease_generation"
        ),
        adapter_id=_text(item.get("adapter_id"), "handle adapter_id"),
        idempotency_key=_text(
            item.get("idempotency_key"), "handle idempotency_key"
        ),
        external_handle=_optional_text(
            item.get("external_handle"), "handle external_handle"
        ),
    )


def _decode_request(value: object) -> AgentRequest:
    item = _mapping(value, "agent request")
    _require_keys(item, {item.name for item in fields(AgentRequest)}, "agent request")
    if item.get("schema_version") != "1.0" or item.get("kind") != "agent-request":
        raise ValueError("fake provider request has unsupported schema identity")
    scope = _mapping(item.get("scope"), "agent request scope")
    _require_keys(
        scope,
        {"write_paths", "read_paths", "prohibited_paths", "resources"},
        "agent request scope",
    )
    criteria_items = []
    for raw in _array(item.get("acceptance_criteria"), "acceptance criteria"):
        criterion = _mapping(raw, "acceptance criterion")
        _require_keys(
            criterion,
            {"id", "description", "verification"},
            "acceptance criterion",
        )
        criteria_items.append(
            AcceptanceCriterion(
                id=_text(criterion.get("id"), "criterion ID"),
                description=_text(
                    criterion.get("description"), "criterion description"
                ),
                verification=_text(
                    criterion.get("verification"), "criterion verification"
                ),
            )
        )
    criteria = tuple(criteria_items)
    task_id = item.get("task_id")
    return AgentRequest(
        id=_text(item.get("id"), "request id"),
        workflow_id=_text(item.get("workflow_id"), "workflow id"),
        run_id=_text(item.get("run_id"), "run id"),
        attempt_id=_text(item.get("attempt_id"), "attempt id"),
        task_id=None if task_id is None else _text(task_id, "task id"),
        plan_id=_text(item.get("plan_id"), "plan id"),
        spec_refs=tuple(
            _text(raw, "spec ref") for raw in _array(item.get("spec_refs"), "spec refs")
        ),
        role=_text(item.get("role"), "role"),
        graph_revision=_integer(item.get("graph_revision"), "graph revision"),
        base_oid=_text(item.get("base_oid"), "base oid"),
        current_oid=_text(item.get("current_oid"), "current oid"),
        worktree_id=_text(item.get("worktree_id"), "worktree id"),
        scope=ScopeClaim(
            write_paths=tuple(
                _text(raw, "write path")
                for raw in _array(scope.get("write_paths"), "write paths")
            ),
            read_paths=tuple(
                _text(raw, "read path")
                for raw in _array(scope.get("read_paths"), "read paths")
            ),
            prohibited_paths=tuple(
                _text(raw, "prohibited path")
                for raw in _array(scope.get("prohibited_paths"), "prohibited paths")
            ),
            resources=tuple(
                _text(raw, "resource")
                for raw in _array(scope.get("resources"), "resources")
            ),
        ),
        context_ref=_text(item.get("context_ref"), "context ref"),
        allowed_command_ids=tuple(
            _text(raw, "command id")
            for raw in _array(item.get("allowed_command_ids"), "allowed command ids")
        ),
        acceptance_criteria=criteria,
        dependency_handoffs=tuple(
            _text(raw, "dependency handoff")
            for raw in _array(item.get("dependency_handoffs"), "dependency handoffs")
        ),
        checklist_ids=tuple(
            _text(raw, "checklist id")
            for raw in _array(item.get("checklist_ids"), "checklist ids")
        ),
        model_profile=_text(item.get("model_profile"), "model profile"),
        policy_ref=_text(item.get("policy_ref"), "policy ref"),
        permission_subset=tuple(
            _text(raw, "permission")
            for raw in _array(item.get("permission_subset"), "permission subset")
        ),
        lease_generation=_integer(item.get("lease_generation"), "lease generation"),
        idempotency_key=_text(item.get("idempotency_key"), "idempotency key"),
    )


def _decode_output(value: object) -> AgentOutputRecord:
    item = _mapping(value, "agent output")
    _require_keys(item, {item.name for item in fields(AgentOutputRecord)}, "agent output")
    if item.get("schema_version") != "1.0" or item.get("kind") != "agent-output":
        raise ValueError("fake provider output has unsupported schema identity")
    return AgentOutputRecord(
        id=_text(item.get("id"), "output id"),
        request_id=_text(item.get("request_id"), "output request id"),
        attempt_id=_text(item.get("attempt_id"), "output attempt id"),
        status=AgentOutputStatus(_text(item.get("status"), "output status")),
        actual_model=_decode_model(item.get("actual_model")),
        artifact_refs=tuple(
            _text(raw, "artifact ref")
            for raw in _array(item.get("artifact_refs"), "artifact refs")
        ),
        command_evidence_refs=tuple(
            _text(raw, "command evidence ref")
            for raw in _array(
                item.get("command_evidence_refs"), "command evidence refs"
            )
        ),
        discoveries=tuple(
            _text(raw, "discovery")
            for raw in _array(item.get("discoveries"), "discoveries")
        ),
        scope_change_requests=tuple(
            _text(raw, "scope change request")
            for raw in _array(
                item.get("scope_change_requests"), "scope change requests"
            )
        ),
        error_category=_optional_text(item.get("error_category"), "output error category"),
        summary=_text(item.get("summary"), "output summary"),
    )


def _decode_run(value: object) -> AgentRunRecord:
    item = _mapping(value, "agent run")
    _require_keys(item, {item.name for item in fields(AgentRunRecord)}, "agent run")
    if item.get("schema_version") != "1.0" or item.get("kind") != "agent-run":
        raise ValueError("fake provider run has unsupported schema identity")
    model = item.get("actual_model")
    return AgentRunRecord(
        id=_text(item.get("id"), "agent run id"),
        request_ref=_text(item.get("request_ref"), "agent run request ref"),
        attempt_id=_text(item.get("attempt_id"), "agent run attempt id"),
        status=AgentRunStatus(_text(item.get("status"), "agent run status")),
        adapter_id=_text(item.get("adapter_id"), "agent run adapter id"),
        external_handle=_optional_text(
            item.get("external_handle"), "agent run external handle"
        ),
        actual_model=None if model is None else _decode_model(model),
        started_at=_datetime(item.get("started_at"), "agent run started_at"),
        finished_at=_datetime(item.get("finished_at"), "agent run finished_at"),
        output_ref=_optional_text(item.get("output_ref"), "agent run output ref"),
        error_category=_optional_text(
            item.get("error_category"), "agent run error category"
        ),
        lease_generation=_integer(
            item.get("lease_generation"), "agent run lease generation"
        ),
    )


def _decode_observation(value: object) -> AgentObservation:
    item = _mapping(value, "agent observation")
    _require_keys(
        item,
        {"status", "handle", "run", "output", "evidence_refs", "error"},
        "agent observation",
    )
    output_value = item.get("output")
    return AgentObservation(
        status=AgentRunStatus(_text(item.get("status"), "observation status")),
        handle=_decode_handle(item.get("handle")),
        run=_decode_run(item.get("run")),
        output=None if output_value is None else _decode_output(output_value),
        evidence_refs=tuple(
            _decode_evidence(reference)
            for reference in _array(
                item.get("evidence_refs"), "observation evidence refs"
            )
        ),
        error=_decode_error(item.get("error")),
    )


def _decode_cancellation(value: object) -> CancelObservation:
    item = _mapping(value, "cancel observation")
    _require_keys(
        item,
        {"status", "handle", "quiesced", "evidence_refs", "error"},
        "cancel observation",
    )
    return CancelObservation(
        status=CancelStatus(_text(item.get("status"), "cancel status")),
        handle=_decode_handle(item.get("handle")),
        quiesced=_boolean(item.get("quiesced"), "cancel quiesced"),
        evidence_refs=tuple(
            _decode_evidence(reference)
            for reference in _array(
                item.get("evidence_refs"), "cancel evidence refs"
            )
        ),
        error=_decode_error(item.get("error")),
    )


@dataclass(frozen=True, slots=True)
class AgentAdapterCapabilities:
    """Explicit capabilities of one injected adapter implementation."""

    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    command_ids: tuple[str, ...]
    model_profiles: tuple[ProviderModelProfile, ...]
    review_roles: tuple[str, ...] = _DEFAULT_REVIEW_ROLES
    queryable: bool = True
    cancellable: bool = True
    reports_model_provenance: bool = True

    def __post_init__(self) -> None:
        roles = _texts(self.roles, "capability roles")
        if not roles:
            raise ValueError("capability roles must not be empty")
        object.__setattr__(self, "roles", roles)
        object.__setattr__(self, "permissions", _texts(self.permissions, "capability permissions"))
        object.__setattr__(self, "command_ids", _texts(self.command_ids, "capability command_ids"))
        object.__setattr__(self, "review_roles", _texts(self.review_roles, "review roles"))
        try:
            profiles = tuple(self.model_profiles)
        except TypeError as exc:
            raise TypeError("model_profiles must be iterable") from exc
        if not profiles or not all(isinstance(item, ProviderModelProfile) for item in profiles):
            raise TypeError("model_profiles must contain ProviderModelProfile values")
        keys = [
            (
                _text(item.provider, "capability model provider").casefold(),
                _text(item.name, "capability model profile"),
            )
            for item in profiles
        ]
        if len(set(keys)) != len(keys):
            raise ValueError("model_profiles must not contain duplicate provider/profile pairs")
        for profile in profiles:
            _text(profile.model_id, "capability model ID")
            if isinstance(profile.capability_rank, bool) or not isinstance(
                profile.capability_rank, int
            ):
                raise TypeError("capability model rank must be an integer")
            if profile.capability_rank < 0:
                raise ValueError("capability model rank cannot be negative")
        object.__setattr__(self, "model_profiles", profiles)
        for name in ("queryable", "cancellable", "reports_model_provenance"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean")

    def model_profile(self, expected: ProviderModelProfile) -> ProviderModelProfile | None:
        for profile in self.model_profiles:
            if (
                profile.provider.casefold() == expected.provider.casefold()
                and profile.name == expected.name
            ):
                return profile
        return None

    def is_review_role(self, role: str) -> bool:
        return role in self.review_roles or role.endswith("-reviewer")


@dataclass(slots=True)
class _FakeEffect:
    request: AgentRequest
    handle: AgentHandle
    configured_model: ProviderModelProfile
    expected_model: ModelIdentity
    poll_script: tuple[AgentObservation, ...] = ()
    cancel_script: tuple[CancelObservation, ...] = ()
    poll_position: int = 0
    cancel_position: int = 0
    script_committed: bool = False
    last_observation: AgentObservation | None = None
    quiesced: bool = False


def _simulation_evidence_for_effect(
    effect: _FakeEffect, event: str, index: int
) -> EvidenceRef:
    external = effect.handle.external_handle
    assert external is not None
    path = f".ai/evidence/fake-agent/{external}/{event}-{index}.json"
    content = "\n".join(
        (
            SIMULATION_SOURCE,
            effect.handle.project_id.value,
            effect.handle.adapter_id,
            effect.request.id.value,
            external,
            event,
            str(index),
        )
    ).encode("utf-8")
    return EvidenceRef(
        path=path,
        sha256=Sha256Digest(hashlib.sha256(content).hexdigest()),
        metadata=FrozenJsonObject(
            {
                "observation_source": SIMULATION_SOURCE,
                "adapter_id": effect.handle.adapter_id,
                "effect_id": external,
                "simulated": True,
                "configured_profile": effect.configured_model.name,
                "submitted_reasoning_effort": (
                    effect.configured_model.reasoning_effort or "omitted"
                ),
                "submitted_effort": effect.configured_model.effort or "omitted",
                "observed_effort": "not_provider_observed",
            }
        ),
    )


def _queued_observation_for_effect(effect: _FakeEffect) -> AgentObservation:
    token = _effect_token(
        effect.handle.project_id.value,
        effect.handle.adapter_id,
        effect.handle.idempotency_key,
    )
    run = AgentRunRecord(
        id=EntityId(f"fake-run-{token[:32]}"),
        request_ref=(
            f"agent-request:{effect.request.plan_id.value}:{effect.request.id.value}"
        ),
        attempt_id=effect.request.attempt_id,
        status=AgentRunStatus.QUEUED,
        adapter_id=effect.handle.adapter_id,
        external_handle=effect.handle.external_handle,
        actual_model=None,
        started_at=None,
        finished_at=None,
        output_ref=None,
        error_category=None,
        lease_generation=effect.request.lease_generation,
    )
    return AgentObservation(
        status=AgentRunStatus.QUEUED,
        handle=effect.handle,
        run=run,
        output=None,
        evidence_refs=(_simulation_evidence_for_effect(effect, "poll-queued", 0),),
    )


class FakeAgentProviderState:
    """State owned by the deterministic fake provider, never by the workflow.

    Keep this object alive independently of a coordinator or adapter.  A new
    adapter with the same project and adapter identity can call ``start`` with
    the original request/key to recover the same handle, then ``poll`` it.  For
    a fresh Python process, pass a provider-owned ``backing_path``: every effect,
    immutable script, observation cursor, and quiescence fact is atomically
    stored there and restored when this class is reconstructed.  That private
    simulation file is not a canonical workflow journal or acceptance record.
    One live provider-state instance owns a backing path at a time; reopening is
    for sequential recovery after the prior provider process has stopped.
    """

    def __init__(self, backing_path: Path | None = None) -> None:
        self._lock = RLock()
        self._by_key: dict[tuple[str, str, str], _FakeEffect] = {}
        self._by_external_handle: dict[str, _FakeEffect] = {}
        if backing_path is None:
            self._backing_path = None
        else:
            candidate = Path(backing_path).resolve(strict=False)
            if not candidate.parent.is_dir():
                raise ValueError("fake provider backing parent must already exist")
            if candidate.exists() and not candidate.is_file():
                raise ValueError("fake provider backing path must be a file")
            self._backing_path = candidate
            if candidate.exists():
                self._load()

    @property
    def backing_path(self) -> Path | None:
        return self._backing_path

    @property
    def effect_count(self) -> int:
        with self._lock:
            return len(self._by_external_handle)

    def script(
        self,
        handle: AgentHandle,
        *,
        polls: Iterable[AgentObservation] = (),
        cancellations: Iterable[CancelObservation] = (),
    ) -> None:
        """Commit one immutable typed script for an already-started effect."""

        if not isinstance(handle, AgentHandle):
            raise TypeError("handle must be an AgentHandle")
        try:
            poll_script = tuple(polls)
            cancel_script = tuple(cancellations)
        except TypeError as exc:
            raise TypeError("fake scripts must be iterable") from exc
        if not all(isinstance(item, AgentObservation) for item in poll_script):
            raise TypeError("polls must contain AgentObservation values")
        if not all(isinstance(item, CancelObservation) for item in cancel_script):
            raise TypeError("cancellations must contain CancelObservation values")
        with self._lock:
            effect = self._effect_for_external_handle(handle)
            self._require_exact_handle(effect, handle)
            if (
                effect.script_committed
                or effect.poll_position
                or effect.cancel_position
            ):
                _failure(
                    ErrorCategory.STATE_CONFLICT,
                    "fake provider script is already committed or observed",
                    details={"external_handle": handle.external_handle or "unknown"},
                )
            previous = (
                effect.poll_script,
                effect.cancel_script,
                effect.script_committed,
            )
            effect.poll_script = poll_script
            effect.cancel_script = cancel_script
            effect.script_committed = True
            try:
                self._persist_locked()
            except Exception:
                (
                    effect.poll_script,
                    effect.cancel_script,
                    effect.script_committed,
                ) = previous
                raise

    def expected_model(self, handle: AgentHandle) -> ModelIdentity:
        """Return the model identity this simulation assigned to the effect."""

        if not isinstance(handle, AgentHandle):
            raise TypeError("handle must be an AgentHandle")
        with self._lock:
            effect = self._effect_for_external_handle(handle)
            self._require_exact_handle(effect, handle)
            return effect.expected_model

    def _effect_for_external_handle(self, handle: AgentHandle) -> _FakeEffect:
        external_handle = handle.external_handle
        if external_handle is None or external_handle not in self._by_external_handle:
            _failure(
                ErrorCategory.STATE_CONFLICT,
                "fake provider handle is unknown",
                details={"external_handle": external_handle or "unknown"},
            )
        return self._by_external_handle[external_handle]

    @staticmethod
    def _require_exact_handle(effect: _FakeEffect, handle: AgentHandle) -> None:
        if effect.handle != handle:
            _failure(
                ErrorCategory.STATE_CONFLICT,
                "fake provider handle identity does not match the started effect",
                details={"external_handle": handle.external_handle or "unknown"},
            )

    def _load(self) -> None:
        assert self._backing_path is not None
        try:
            raw = json.loads(self._backing_path.read_text(encoding="utf-8"))
            payload = _mapping(raw, "fake provider state")
            if set(payload) != {"format", "simulation_source", "effects"}:
                raise ValueError("fake provider state has unknown or missing fields")
            if payload.get("format") != _FAKE_STATE_FORMAT:
                raise ValueError("unsupported fake provider state format")
            if payload.get("simulation_source") != SIMULATION_SOURCE:
                raise ValueError("fake provider state is not marked as simulation")
            effects = tuple(
                self._decode_effect(value)
                for value in _array(payload.get("effects"), "fake provider effects")
            )
            for effect in effects:
                external = effect.handle.external_handle
                assert external is not None
                key = (
                    effect.handle.project_id.value,
                    effect.handle.adapter_id,
                    effect.handle.idempotency_key,
                )
                if key in self._by_key or external in self._by_external_handle:
                    raise ValueError("fake provider state contains duplicate effects")
                self._by_key[key] = effect
                self._by_external_handle[external] = effect
        except DomainException:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            self._by_key.clear()
            self._by_external_handle.clear()
            _failure(
                ErrorCategory.VALIDATION_FAILED,
                f"cannot restore deterministic fake provider state: {exc}",
                details={"backing_path": str(self._backing_path)},
            )

    def _decode_effect(self, value: object) -> _FakeEffect:
        item = _mapping(value, "fake provider effect")
        expected_keys = {
            "request",
            "handle",
            "configured_model",
            "expected_model",
            "poll_script",
            "cancel_script",
            "poll_position",
            "cancel_position",
            "script_committed",
            "last_observation",
            "quiesced",
        }
        if set(item) != expected_keys:
            raise ValueError("fake provider effect has unknown or missing fields")
        request = _decode_request(item["request"])
        handle = _decode_handle(item["handle"])
        configured_model = _decode_provider_model(item["configured_model"])
        expected_model = _decode_model(item["expected_model"])
        poll_script = tuple(
            _decode_observation(observation)
            for observation in _array(item["poll_script"], "poll script")
        )
        cancel_script = tuple(
            _decode_cancellation(observation)
            for observation in _array(item["cancel_script"], "cancel script")
        )
        poll_position = _integer(item["poll_position"], "poll position")
        cancel_position = _integer(item["cancel_position"], "cancel position")
        script_committed = _boolean(item["script_committed"], "script committed")
        quiesced = _boolean(item["quiesced"], "effect quiesced")
        last_value = item["last_observation"]
        last_observation = (
            None if last_value is None else _decode_observation(last_value)
        )
        if poll_position < 0 or poll_position > len(poll_script):
            raise ValueError("poll position is outside the saved script")
        if cancel_position < 0 or cancel_position > len(cancel_script):
            raise ValueError("cancel position is outside the saved script")
        if not script_committed and (poll_script or cancel_script):
            raise ValueError("uncommitted fake provider state cannot contain scripts")
        effect = _FakeEffect(
            request=request,
            handle=handle,
            configured_model=configured_model,
            expected_model=expected_model,
            poll_script=poll_script,
            cancel_script=cancel_script,
            poll_position=poll_position,
            cancel_position=cancel_position,
            script_committed=script_committed,
            last_observation=last_observation,
            quiesced=quiesced,
        )
        self._validate_restored_effect(effect)
        return effect

    @staticmethod
    def _validate_restored_effect(effect: _FakeEffect) -> None:
        request = effect.request
        handle = effect.handle
        configured_model = effect.configured_model
        expected_model = effect.expected_model
        if (
            handle.plan_id != request.plan_id
            or handle.run_id != request.run_id
            or handle.request_id != request.id
            or handle.attempt_id != request.attempt_id
            or handle.lease_generation != request.lease_generation
            or handle.idempotency_key != request.idempotency_key
        ):
            raise ValueError("restored fake handle does not match its immutable request")
        token = _effect_token(
            handle.project_id.value,
            handle.adapter_id,
            handle.idempotency_key,
        )
        if handle.external_handle != f"fake-agent-{token[:32]}":
            raise ValueError("restored fake handle is not deterministic")
        if (
            expected_model.profile != request.model_profile
            or configured_model.name != request.model_profile
            or expected_model.provider != configured_model.provider
            or expected_model.model_id != configured_model.model_id
            or expected_model.capability_rank != configured_model.capability_rank
            or expected_model.invocation_id != f"fake-invocation-{token[:32]}"
        ):
            raise ValueError("restored fake model identity does not match its effect")

        if not effect.script_committed and (
            effect.poll_script
            or effect.cancel_script
            or effect.poll_position
            or effect.cancel_position
        ):
            raise ValueError("uncommitted fake provider state contains observed scripts")

        terminal_poll = False
        if effect.poll_position:
            consumed_polls = effect.poll_script[: effect.poll_position]
            for observation in consumed_polls:
                FakeAgentProviderState._validate_restored_observation(
                    effect, observation
                )
            if any(
                observation.status in _TERMINAL_AGENT_STATUSES
                for observation in consumed_polls[:-1]
            ):
                raise ValueError("restored poll cursor advanced past a terminal result")
            last_index = effect.poll_position - 1
            expected_last = replace(
                consumed_polls[-1],
                evidence_refs=consumed_polls[-1].evidence_refs
                + (_simulation_evidence_for_effect(effect, "poll", last_index),),
            )
            if effect.last_observation != expected_last:
                raise ValueError(
                    "restored last observation does not match the consumed poll prefix"
                )
            terminal_poll = expected_last.status in _TERMINAL_AGENT_STATUSES
        elif effect.last_observation is not None:
            if effect.last_observation != _queued_observation_for_effect(effect):
                raise ValueError(
                    "restored unconsumed poll state has an unsupported last observation"
                )

        terminal_cancel = False
        if effect.cancel_position:
            consumed_cancellations = effect.cancel_script[: effect.cancel_position]
            if any(
                observation.handle != handle for observation in consumed_cancellations
            ):
                raise ValueError(
                    "restored consumed cancellation does not match its effect"
                )
            if any(
                observation.status in _QUIESCED_CANCEL_STATUSES
                for observation in consumed_cancellations[:-1]
            ):
                raise ValueError(
                    "restored cancellation cursor advanced past a terminal result"
                )
            terminal_cancel = (
                consumed_cancellations[-1].status in _QUIESCED_CANCEL_STATUSES
            )
        if terminal_poll and terminal_cancel:
            raise ValueError("restored effect contains conflicting terminal histories")
        if effect.quiesced is not (terminal_poll or terminal_cancel):
            raise ValueError("restored effect quiescence is not supported by its history")

    @staticmethod
    def _validate_restored_observation(
        effect: _FakeEffect, observation: AgentObservation
    ) -> None:
        if observation.handle != effect.handle:
            raise ValueError("restored observation handle does not match its effect")
        expected_request_ref = (
            f"agent-request:{effect.request.plan_id.value}:{effect.request.id.value}"
        )
        if observation.run.request_ref != expected_request_ref:
            raise ValueError("restored observation request_ref does not match its effect")
        observed_models = tuple(
            value
            for value in (
                observation.run.actual_model,
                None if observation.output is None else observation.output.actual_model,
            )
            if value is not None
        )
        if any(value != effect.expected_model for value in observed_models):
            raise ValueError("restored observation model provenance is inconsistent")
        if observation.status is AgentRunStatus.SUCCEEDED:
            assert observation.output is not None
            expected_output_ref = (
                f"agent-output:{effect.request.plan_id.value}:{observation.output.id.value}"
            )
            if observation.run.output_ref != expected_output_ref:
                raise ValueError("restored observation output_ref is inconsistent")

    def _persist_locked(self) -> None:
        if self._backing_path is None:
            return
        payload = {
            "format": _FAKE_STATE_FORMAT,
            "simulation_source": SIMULATION_SOURCE,
            "effects": [
                self._encode_effect(effect)
                for _, effect in sorted(self._by_key.items(), key=lambda item: item[0])
            ],
        }
        data = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        assert self._backing_path is not None
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=self._backing_path.parent,
                prefix=f".{self._backing_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self._backing_path)
        except OSError as exc:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            _failure(
                ErrorCategory.INTERNAL_ERROR,
                f"cannot persist deterministic fake provider state: {exc}",
                details={"backing_path": str(self._backing_path)},
            )

    @staticmethod
    def _encode_effect(effect: _FakeEffect) -> dict[str, object]:
        return {
            "request": _wire(effect.request),
            "handle": _wire(effect.handle),
            "configured_model": _wire(effect.configured_model),
            "expected_model": _wire(effect.expected_model),
            "poll_script": _wire(effect.poll_script),
            "cancel_script": _wire(effect.cancel_script),
            "poll_position": effect.poll_position,
            "cancel_position": effect.cancel_position,
            "script_committed": effect.script_committed,
            "last_observation": _wire(effect.last_observation),
            "quiesced": effect.quiesced,
        }


class DeterministicFakeAgentAdapter(AgentAdapter):
    """Offline, deterministic implementation of the frozen ``AgentAdapter``."""

    def __init__(
        self,
        *,
        project_id: EntityId | str,
        settings: ProjectSettings,
        capabilities: AgentAdapterCapabilities,
        provider_state: FakeAgentProviderState,
        adapter_id: str = "deterministic-fake-agent",
    ) -> None:
        self._project_id = project_id if isinstance(project_id, EntityId) else EntityId(project_id)
        if not isinstance(settings, ProjectSettings):
            raise TypeError("settings must be ProjectSettings")
        if not isinstance(capabilities, AgentAdapterCapabilities):
            raise TypeError("capabilities must be AgentAdapterCapabilities")
        if not isinstance(provider_state, FakeAgentProviderState):
            raise TypeError("provider_state must be FakeAgentProviderState")
        self._settings = settings
        self._capabilities = capabilities
        self._provider = provider_state
        self._adapter_id = _text(adapter_id, "adapter ID")

    def start(self, request: AgentRequest, idempotency_key: str) -> AgentHandle:
        if not isinstance(request, AgentRequest):
            raise TypeError("request must be an AgentRequest")
        key = _text(idempotency_key, "idempotency key")
        if request.idempotency_key != key:
            _failure(
                ErrorCategory.INVALID_INPUT,
                "start idempotency key does not match the immutable agent request",
                details={"request_id": request.id.value},
            )
        lookup_key = (self._project_id.value, self._adapter_id, key)
        with self._provider._lock:
            prior = self._provider._by_key.get(lookup_key)
            if prior is not None:
                if prior.request != request:
                    _failure(
                        ErrorCategory.STATE_CONFLICT,
                        "idempotency key is already bound to a materially different request",
                        details={"idempotency_key": key},
                    )
                configured = self._validate_new_dispatch(request)
                if (
                    prior.configured_model != configured
                    or prior.expected_model
                    != self._expected_model(request, configured, key)
                ):
                    _failure(
                        ErrorCategory.VALIDATION_FAILED,
                        "restored fake provider provenance does not match dispatch configuration",
                        details={"idempotency_key": key},
                    )
                return prior.handle

            configured = self._validate_new_dispatch(request)
            token = self._effect_token(key)
            external_handle = f"fake-agent-{token[:32]}"
            if external_handle in self._provider._by_external_handle:
                _failure(
                    ErrorCategory.STATE_CONFLICT,
                    "deterministic fake external handle collided with another effect",
                    details={"external_handle": external_handle},
                )
            handle = AgentHandle(
                project_id=self._project_id,
                plan_id=request.plan_id,
                run_id=request.run_id,
                request_id=request.id,
                attempt_id=request.attempt_id,
                lease_generation=request.lease_generation,
                adapter_id=self._adapter_id,
                idempotency_key=key,
                external_handle=external_handle,
            )
            expected_model = self._expected_model(request, configured, key)
            effect = _FakeEffect(
                request=request,
                handle=handle,
                configured_model=configured,
                expected_model=expected_model,
            )
            self._provider._by_key[lookup_key] = effect
            self._provider._by_external_handle[external_handle] = effect
            try:
                self._provider._persist_locked()
            except Exception:
                del self._provider._by_key[lookup_key]
                del self._provider._by_external_handle[external_handle]
                raise
            return handle

    def poll(self, handle: AgentHandle) -> AgentObservation:
        self._validate_adapter_handle(handle)
        with self._provider._lock:
            effect = self._provider._effect_for_external_handle(handle)
            self._provider._require_exact_handle(effect, handle)
            if (
                effect.last_observation is not None
                and effect.last_observation.status in _TERMINAL_AGENT_STATUSES
            ):
                return effect.last_observation
            if effect.quiesced:
                _failure(
                    ErrorCategory.STATE_CONFLICT,
                    "cannot poll an effect after confirmed cancellation",
                    details={"request_id": effect.request.id.value},
                )
            previous = (
                effect.poll_position,
                effect.last_observation,
                effect.quiesced,
            )
            if effect.poll_script:
                index = min(effect.poll_position, len(effect.poll_script) - 1)
                scripted = effect.poll_script[index]
                observation = self._mark_observation(effect, scripted, "poll", index)
                self._validate_observation(effect, observation)
                if effect.poll_position < len(effect.poll_script):
                    effect.poll_position += 1
            else:
                observation = self._queued_observation(effect)
                self._validate_observation(effect, observation)
            effect.last_observation = observation
            if observation.status in {
                AgentRunStatus.SUCCEEDED,
                AgentRunStatus.FAILED,
                AgentRunStatus.CANCELLED,
            }:
                effect.quiesced = True
            try:
                self._provider._persist_locked()
            except Exception:
                (
                    effect.poll_position,
                    effect.last_observation,
                    effect.quiesced,
                ) = previous
                raise
            return observation

    def cancel(self, handle: AgentHandle) -> CancelObservation:
        self._validate_adapter_handle(handle)
        with self._provider._lock:
            effect = self._provider._effect_for_external_handle(handle)
            self._provider._require_exact_handle(effect, handle)
            if (
                effect.last_observation is not None
                and effect.last_observation.status in _TERMINAL_AGENT_STATUSES
            ):
                return CancelObservation(
                    status=CancelStatus.ALREADY_TERMINAL,
                    handle=effect.handle,
                    quiesced=True,
                    evidence_refs=(
                        self._simulation_evidence(
                            effect, "cancel-already-terminal", 0
                        ),
                    ),
                )
            if effect.quiesced:
                if effect.cancel_position:
                    prior_index = effect.cancel_position - 1
                    prior = effect.cancel_script[prior_index]
                    if prior.status in _QUIESCED_CANCEL_STATUSES:
                        return self._mark_cancellation(effect, prior, prior_index)
                _failure(
                    ErrorCategory.STATE_CONFLICT,
                    "confirmed quiescence has no consistent terminal observation",
                    details={"request_id": effect.request.id.value},
                )
            if effect.cancel_script:
                previous = (effect.cancel_position, effect.quiesced)
                index = min(effect.cancel_position, len(effect.cancel_script) - 1)
                scripted = effect.cancel_script[index]
                observation = self._mark_cancellation(effect, scripted, index)
                self._validate_cancellation(effect, observation)
                if effect.cancel_position < len(effect.cancel_script):
                    effect.cancel_position += 1
                if observation.quiesced:
                    effect.quiesced = True
                try:
                    self._provider._persist_locked()
                except Exception:
                    effect.cancel_position, effect.quiesced = previous
                    raise
                return observation
            if effect.quiesced:
                return CancelObservation(
                    status=CancelStatus.ALREADY_TERMINAL,
                    handle=effect.handle,
                    quiesced=True,
                    evidence_refs=(
                        self._simulation_evidence(
                            effect, "cancel-already-terminal", 0
                        ),
                    ),
                )
            # Sending a cancellation request is not an observation that the
            # worker stopped.  The default fake therefore remains unresolved.
            return CancelObservation(
                status=CancelStatus.PENDING,
                handle=effect.handle,
                quiesced=False,
                evidence_refs=(self._simulation_evidence(effect, "cancel-pending", 0),),
            )

    def expected_model(self, handle: AgentHandle) -> ModelIdentity:
        """Expose deterministic simulation provenance for constructing scripts."""

        self._validate_adapter_handle(handle)
        return self._provider.expected_model(handle)

    def _validate_new_dispatch(self, request: AgentRequest) -> ProviderModelProfile:
        if request.policy_ref != self._settings.policy_ref:
            _failure(
                ErrorCategory.STATE_CONFLICT,
                "agent request policy_ref does not match the injected project settings",
                details={"request_policy_ref": request.policy_ref},
            )
        missing_runtime = [
            name
            for name, available in (
                ("query", self._capabilities.queryable),
                ("cancel", self._capabilities.cancellable),
                ("model_provenance", self._capabilities.reports_model_provenance),
            )
            if not available
        ]
        missing: list[str] = []
        if request.role not in self._capabilities.roles:
            missing.append(f"role:{request.role}")
        missing.extend(
            f"permission:{value}"
            for value in request.permission_subset
            if value not in self._capabilities.permissions
        )
        missing.extend(
            f"command:{value}"
            for value in request.allowed_command_ids
            if value not in self._capabilities.command_ids
        )
        missing.extend(f"runtime:{value}" for value in missing_runtime)
        if missing:
            _failure(
                ErrorCategory.UNSUPPORTED_CAPABILITY,
                "agent adapter does not support every requested capability",
                details={"missing": missing},
            )

        policy_profile = self._settings.policy.model_profile(request.model_profile)
        configured = self._settings.configured_model(request.model_profile)
        if configured is None:
            _failure(
                ErrorCategory.UNSUPPORTED_CAPABILITY,
                "agent model profile is a recommendation without a verified configured binding",
                details={"profile": request.model_profile},
            )
        assert configured is not None
        if (
            policy_profile.provider is None
            or policy_profile.model_id is None
            or policy_profile.provider.casefold() != configured.provider.casefold()
            or policy_profile.model_id != configured.model_id
            or policy_profile.capability_rank != configured.capability_rank
        ):
            _failure(
                ErrorCategory.UNSUPPORTED_CAPABILITY,
                "configured policy provider, model, or rank is inconsistent",
                details={"profile": request.model_profile},
            )
        available = self._capabilities.model_profile(configured)
        if available is None or available != configured:
            _failure(
                ErrorCategory.UNSUPPORTED_CAPABILITY,
                "adapter provider, model, rank, or effort capability does not match configuration",
                details={
                    "profile": request.model_profile,
                    "provider": configured.provider,
                    "model_id": configured.model_id,
                    "capability_rank": configured.capability_rank,
                },
            )
        if self._capabilities.is_review_role(
            request.role
        ) or request.model_profile.startswith("review"):
            implementation = self._settings.configured_model("implementation")
            if (
                implementation is None
                or configured.capability_rank <= implementation.capability_rank
            ):
                _failure(
                    ErrorCategory.UNSUPPORTED_CAPABILITY,
                    "review dispatch requires a verified model rank above implementation",
                    details={
                        "review_rank": configured.capability_rank,
                        "implementation_rank": (
                            "unverified"
                            if implementation is None
                            else implementation.capability_rank
                        ),
                    },
                )
        return configured

    def _validate_adapter_handle(self, handle: AgentHandle) -> None:
        if not isinstance(handle, AgentHandle):
            raise TypeError("handle must be an AgentHandle")
        if handle.project_id != self._project_id or handle.adapter_id != self._adapter_id:
            _failure(
                ErrorCategory.STATE_CONFLICT,
                "agent handle belongs to a different project or adapter",
                details={"adapter_id": handle.adapter_id, "project_id": handle.project_id.value},
            )

    def _expected_model(
        self,
        request: AgentRequest,
        configured: ProviderModelProfile,
        idempotency_key: str,
    ) -> ModelIdentity:
        token = self._effect_token(idempotency_key)
        return ModelIdentity(
            profile=request.model_profile,
            provider=configured.provider,
            model_id=configured.model_id,
            capability_rank=configured.capability_rank,
            invocation_id=f"fake-invocation-{token[:32]}",
        )

    def _validate_observation(
        self, effect: _FakeEffect, observation: AgentObservation
    ) -> None:
        if observation.handle != effect.handle:
            _failure(
                ErrorCategory.STATE_CONFLICT,
                "provider observation handle identity does not match the requested effect",
                details={"request_id": effect.request.id.value},
            )
        expected_request_ref = (
            f"agent-request:{effect.request.plan_id.value}:{effect.request.id.value}"
        )
        if observation.run.request_ref != expected_request_ref:
            _failure(
                ErrorCategory.STATE_CONFLICT,
                "provider observation request_ref does not match the started request",
                details={"request_id": effect.request.id.value},
            )
        observed_models = [
            value
            for value in (
                observation.run.actual_model,
                None if observation.output is None else observation.output.actual_model,
            )
            if value is not None
        ]
        if any(value != effect.expected_model for value in observed_models):
            _failure(
                ErrorCategory.VALIDATION_FAILED,
                "provider model provenance does not match the configured dispatch binding",
                details={"request_id": effect.request.id.value},
            )
        if observation.status is AgentRunStatus.SUCCEEDED:
            assert observation.output is not None
            expected_output_ref = (
                f"agent-output:{effect.request.plan_id.value}:{observation.output.id.value}"
            )
            if observation.run.output_ref != expected_output_ref:
                _failure(
                    ErrorCategory.STATE_CONFLICT,
                    "provider output_ref does not identify the structured agent output",
                    details={"request_id": effect.request.id.value},
                )
        if not any(
            reference.metadata.get("observation_source") == SIMULATION_SOURCE
            for reference in observation.evidence_refs
        ):
            _failure(
                ErrorCategory.VALIDATION_FAILED,
                "fake provider observation lacks deterministic simulation provenance",
                details={"request_id": effect.request.id.value},
            )

    @staticmethod
    def _validate_cancellation(
        effect: _FakeEffect, observation: CancelObservation
    ) -> None:
        if observation.handle != effect.handle:
            _failure(
                ErrorCategory.STATE_CONFLICT,
                "provider cancellation handle identity does not match the requested effect",
                details={"request_id": effect.request.id.value},
            )
        if not any(
            reference.metadata.get("observation_source") == SIMULATION_SOURCE
            for reference in observation.evidence_refs
        ):
            _failure(
                ErrorCategory.VALIDATION_FAILED,
                "fake cancellation observation lacks deterministic simulation provenance",
                details={"request_id": effect.request.id.value},
            )

    def _queued_observation(self, effect: _FakeEffect) -> AgentObservation:
        return _queued_observation_for_effect(effect)

    def _mark_observation(
        self,
        effect: _FakeEffect,
        observation: AgentObservation,
        event: str,
        index: int,
    ) -> AgentObservation:
        return replace(
            observation,
            evidence_refs=observation.evidence_refs
            + (self._simulation_evidence(effect, event, index),),
        )

    def _mark_cancellation(
        self, effect: _FakeEffect, observation: CancelObservation, index: int
    ) -> CancelObservation:
        return replace(
            observation,
            evidence_refs=observation.evidence_refs
            + (self._simulation_evidence(effect, "cancel", index),),
        )

    def _simulation_evidence(
        self, effect: _FakeEffect, event: str, index: int
    ) -> EvidenceRef:
        assert effect.handle.project_id == self._project_id
        assert effect.handle.adapter_id == self._adapter_id
        return _simulation_evidence_for_effect(effect, event, index)

    def _effect_token(self, idempotency_key: str) -> str:
        return _effect_token(self._project_id.value, self._adapter_id, idempotency_key)


__all__ = [
    "AgentAdapterCapabilities",
    "DeterministicFakeAgentAdapter",
    "FakeAgentProviderState",
    "SIMULATION_SOURCE",
]
