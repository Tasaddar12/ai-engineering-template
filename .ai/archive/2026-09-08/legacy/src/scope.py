"""Deterministic ownership conflicts and task change-scope checks.

The module is deliberately graph- and Git-independent.  Callers supply whether
two owners are already sequenced and translate observed Git changes into the
immutable values below.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from domain_values import (
    DomainError,
    DomainException,
    ErrorCategory,
    ScopeClaim,
    ScopePath,
    ScopePathKind,
)


class AccessMode(StrEnum):
    """The access made by one side of a path conflict."""

    READ = "read"
    WRITE = "write"


class ScopeConflictKind(StrEnum):
    """Exclusive ownership relationships understood by the v1 workflow."""

    WRITE_WRITE = "write_write"
    WRITE_READ = "write_read"
    SEMANTIC_RESOURCE = "semantic_resource"


@dataclass(frozen=True, slots=True)
class ScopeConflict:
    """One path or semantic-resource collision between two scope claims."""

    kind: ScopeConflictKind
    left_path: ScopePath | None = None
    right_path: ScopePath | None = None
    left_access: AccessMode | None = None
    right_access: AccessMode | None = None
    left_resource: str | None = None
    right_resource: str | None = None

    def __post_init__(self) -> None:
        kind = self.kind if isinstance(self.kind, ScopeConflictKind) else ScopeConflictKind(self.kind)
        object.__setattr__(self, "kind", kind)
        if kind is ScopeConflictKind.SEMANTIC_RESOURCE:
            if any(
                value is not None
                for value in (self.left_path, self.right_path, self.left_access, self.right_access)
            ):
                raise ValueError("semantic resource conflicts cannot carry path fields")
            if self.left_resource is None or self.right_resource is None:
                raise ValueError("semantic resource conflicts require both resource claims")
            # Delegate resource validation and NFC display normalization to the
            # accepted ScopeClaim boundary.
            left_claim = ScopeClaim(resources=(self.left_resource,))
            right_claim = ScopeClaim(resources=(self.right_resource,))
            if not left_claim.conflicts_with(right_claim):
                raise ValueError("semantic resource claims do not conflict")
            object.__setattr__(self, "left_resource", left_claim.resources[0])
            object.__setattr__(self, "right_resource", right_claim.resources[0])
            return

        if self.left_resource is not None or self.right_resource is not None:
            raise ValueError("path conflicts cannot carry semantic resource fields")
        if not isinstance(self.left_path, ScopePath) or not isinstance(self.right_path, ScopePath):
            raise TypeError("path conflicts require two ScopePath values")
        if not self.left_path.overlaps(self.right_path):
            raise ValueError("path claims do not overlap")
        left_access = (
            self.left_access
            if isinstance(self.left_access, AccessMode)
            else AccessMode(self.left_access)
        )
        right_access = (
            self.right_access
            if isinstance(self.right_access, AccessMode)
            else AccessMode(self.right_access)
        )
        if left_access is AccessMode.READ and right_access is AccessMode.READ:
            raise ValueError("read/read paths are not an ownership conflict")
        expected_kind = (
            ScopeConflictKind.WRITE_WRITE
            if left_access is AccessMode.WRITE and right_access is AccessMode.WRITE
            else ScopeConflictKind.WRITE_READ
        )
        if kind is not expected_kind:
            raise ValueError("path access modes do not match the conflict kind")
        object.__setattr__(self, "left_access", left_access)
        object.__setattr__(self, "right_access", right_access)


@dataclass(frozen=True, slots=True)
class ScopeConflictReport:
    """All collisions plus the caller-supplied sequencing relationship."""

    sequenced: bool
    conflicts: tuple[ScopeConflict, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if isinstance(self.conflicts, (str, bytes, bytearray)):
            raise TypeError("conflicts must be an iterable of ScopeConflict values")
        conflicts = tuple(self.conflicts)
        if not all(isinstance(conflict, ScopeConflict) for conflict in conflicts):
            raise TypeError("conflicts must contain ScopeConflict values")
        if not isinstance(self.sequenced, bool):
            raise TypeError("sequenced must be a boolean")
        object.__setattr__(self, "conflicts", conflicts)

    @property
    def requires_sequencing(self) -> bool:
        return bool(self.conflicts)

    @property
    def blocks_concurrency(self) -> bool:
        return self.requires_sequencing

    @property
    def has_unsequenced_conflict(self) -> bool:
        return self.requires_sequencing and not self.sequenced

    @property
    def sequencing_satisfied(self) -> bool:
        return not self.requires_sequencing or self.sequenced

    @property
    def can_run_concurrently(self) -> bool:
        return not self.blocks_concurrency


def _path_conflict_key(conflict: ScopeConflict) -> tuple[Any, ...]:
    assert conflict.left_path is not None
    assert conflict.right_path is not None
    assert conflict.left_access is not None
    assert conflict.right_access is not None
    return (
        0,
        conflict.kind.value,
        conflict.left_path.comparison_key,
        conflict.left_path.kind.value,
        conflict.left_path.as_wire(),
        conflict.left_access.value,
        conflict.right_path.comparison_key,
        conflict.right_path.kind.value,
        conflict.right_path.as_wire(),
        conflict.right_access.value,
    )


def _conflict_key(conflict: ScopeConflict) -> tuple[Any, ...]:
    if conflict.kind is not ScopeConflictKind.SEMANTIC_RESOURCE:
        return _path_conflict_key(conflict)
    assert conflict.left_resource is not None
    assert conflict.right_resource is not None
    # Equivalence is decided by ScopeClaim.conflicts_with; these strings only
    # provide a stable presentation order for already-detected conflicts.
    return (1, conflict.left_resource.casefold(), conflict.right_resource.casefold())


def detect_scope_conflicts(
    left: ScopeClaim,
    right: ScopeClaim,
    *,
    sequenced: bool,
) -> ScopeConflictReport:
    """Report exclusive ownership between two claims.

    ``sequenced`` is an observed dependency/ordering fact supplied by the caller.
    This module does not infer graph reachability.  Conflicts always preclude
    concurrency; ``sequencing_satisfied`` records whether the caller's supplied
    ordering fact resolves the ownership requirement.
    """
    if not isinstance(left, ScopeClaim) or not isinstance(right, ScopeClaim):
        raise TypeError("scope conflict detection requires two ScopeClaim values")
    if not isinstance(sequenced, bool):
        raise TypeError("sequenced must be a boolean")

    conflicts: list[ScopeConflict] = []
    path_pairs = (
        (left.write_paths, AccessMode.WRITE, right.write_paths, AccessMode.WRITE),
        (left.write_paths, AccessMode.WRITE, right.read_paths, AccessMode.READ),
        (left.read_paths, AccessMode.READ, right.write_paths, AccessMode.WRITE),
    )
    for left_paths, left_access, right_paths, right_access in path_pairs:
        kind = (
            ScopeConflictKind.WRITE_WRITE
            if left_access is AccessMode.WRITE and right_access is AccessMode.WRITE
            else ScopeConflictKind.WRITE_READ
        )
        for left_path in left_paths:
            for right_path in right_paths:
                # ScopePath.overlaps is the accepted conservative normalization
                # and ancestor-collision rule from TASK-001.
                if left_path.overlaps(right_path):
                    conflicts.append(
                        ScopeConflict(
                            kind=kind,
                            left_path=left_path,
                            right_path=right_path,
                            left_access=left_access,
                            right_access=right_access,
                        )
                    )

    for left_resource in left.resources:
        for right_resource in right.resources:
            # Singleton claims reuse TASK-001's exact Unicode/case resource
            # equivalence without creating a second normalization contract.
            if ScopeClaim(resources=(left_resource,)).conflicts_with(
                ScopeClaim(resources=(right_resource,))
            ):
                conflicts.append(
                    ScopeConflict(
                        kind=ScopeConflictKind.SEMANTIC_RESOURCE,
                        left_resource=left_resource,
                        right_resource=right_resource,
                    )
                )

    return ScopeConflictReport(
        sequenced=sequenced,
        conflicts=tuple(sorted(conflicts, key=_conflict_key)),
    )


class PathChangeKind(StrEnum):
    """The v1 handoff change vocabulary."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass(frozen=True, slots=True, init=False)
class PathChange:
    """One observed exact-file change from a candidate diff."""

    path: ScopePath
    change: PathChangeKind
    previous_path: ScopePath | None = None

    def __init__(
        self,
        path: ScopePath | str,
        change: PathChangeKind | str,
        previous_path: ScopePath | str | None = None,
    ) -> None:
        path = path if isinstance(path, ScopePath) else ScopePath.exact_file(path)
        change = change if isinstance(change, PathChangeKind) else PathChangeKind(change)
        if previous_path is not None and not isinstance(previous_path, ScopePath):
            previous_path = ScopePath.exact_file(previous_path)
        if path.kind is not ScopePathKind.EXACT_FILE:
            raise ValueError("changed path must be an exact file")
        if previous_path is not None and previous_path.kind is not ScopePathKind.EXACT_FILE:
            raise ValueError("previous changed path must be an exact file")
        if change is PathChangeKind.RENAMED and previous_path is None:
            raise ValueError("renamed changes require previous_path")
        if change is not PathChangeKind.RENAMED and previous_path is not None:
            raise ValueError("only renamed changes may carry previous_path")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "change", change)
        object.__setattr__(self, "previous_path", previous_path)

    def to_wire(self) -> dict[str, str | None]:
        return {
            "path": self.path.as_wire(),
            "change": self.change.value,
            "previous_path": (
                None if self.previous_path is None else self.previous_path.as_wire()
            ),
        }


class ChangeEndpoint(StrEnum):
    """The endpoint of a change that was outside the write scope."""

    PATH = "path"
    PREVIOUS_PATH = "previous_path"


@dataclass(frozen=True, slots=True)
class ChangeScopeViolation:
    """One exact path that the task's claim does not permit it to change."""

    change: PathChange
    endpoint: ChangeEndpoint
    path: ScopePath

    def __post_init__(self) -> None:
        if not isinstance(self.change, PathChange):
            raise TypeError("scope violation change must be a PathChange")
        endpoint = (
            self.endpoint
            if isinstance(self.endpoint, ChangeEndpoint)
            else ChangeEndpoint(self.endpoint)
        )
        if not isinstance(self.path, ScopePath) or self.path.kind is not ScopePathKind.EXACT_FILE:
            raise TypeError("scope violation path must be an exact-file ScopePath")
        expected = (
            self.change.path
            if endpoint is ChangeEndpoint.PATH
            else self.change.previous_path
        )
        if expected is None or self.path.comparison_key != expected.comparison_key:
            raise ValueError("scope violation endpoint does not match its change")
        object.__setattr__(self, "endpoint", endpoint)


@dataclass(frozen=True, slots=True)
class ChangeScopeReport:
    """Immutable result of checking observed candidate changes against a claim."""

    changes: tuple[PathChange, ...] = field(default_factory=tuple)
    violations: tuple[ChangeScopeViolation, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if isinstance(self.changes, (str, bytes, bytearray)):
            raise TypeError("changes must be an iterable of PathChange values")
        if isinstance(self.violations, (str, bytes, bytearray)):
            raise TypeError("violations must be an iterable of ChangeScopeViolation values")
        changes = tuple(self.changes)
        violations = tuple(self.violations)
        if not all(isinstance(change, PathChange) for change in changes):
            raise TypeError("changes must contain PathChange values")
        if not all(isinstance(violation, ChangeScopeViolation) for violation in violations):
            raise TypeError("violations must contain ChangeScopeViolation values")
        if any(violation.change not in changes for violation in violations):
            raise ValueError("every scope violation must refer to a reported change")
        object.__setattr__(self, "changes", changes)
        object.__setattr__(self, "violations", violations)

    @property
    def permitted(self) -> bool:
        return not self.violations


def _freeze_changes(changes: Iterable[PathChange]) -> tuple[PathChange, ...]:
    if isinstance(changes, (str, bytes, bytearray)):
        raise TypeError("changes must be an iterable of PathChange values")
    try:
        frozen = tuple(changes)
    except TypeError as exc:
        raise TypeError("changes must be iterable") from exc
    if not all(isinstance(change, PathChange) for change in frozen):
        raise TypeError("changes must contain PathChange values")
    return frozen


def check_change_scope(
    scope: ScopeClaim,
    changes: Iterable[PathChange],
) -> ChangeScopeReport:
    """Check every changed endpoint against a task's declared write scope."""
    if not isinstance(scope, ScopeClaim):
        raise TypeError("change-scope checks require a ScopeClaim")
    frozen_changes = _freeze_changes(changes)
    violations: list[ChangeScopeViolation] = []
    for change in frozen_changes:
        if not scope.permits_write(change.path):
            violations.append(
                ChangeScopeViolation(change, ChangeEndpoint.PATH, change.path)
            )
        if (
            change.change is PathChangeKind.RENAMED
            and change.previous_path is not None
            and not scope.permits_write(change.previous_path)
        ):
            violations.append(
                ChangeScopeViolation(
                    change,
                    ChangeEndpoint.PREVIOUS_PATH,
                    change.previous_path,
                )
            )
    return ChangeScopeReport(frozen_changes, tuple(violations))


def enforce_change_scope(
    scope: ScopeClaim,
    changes: Iterable[PathChange],
) -> ChangeScopeReport:
    """Return a permitted report or raise a structured non-retryable scope error."""
    report = check_change_scope(scope, changes)
    if report.permitted:
        return report
    details = {
        "violations": [
            {
                "change": violation.change.change.value,
                "endpoint": violation.endpoint.value,
                "path": violation.path.as_wire(),
            }
            for violation in report.violations
        ]
    }
    raise DomainException(
        DomainError(
            category=ErrorCategory.SCOPE_CONFLICT,
            message="candidate changes are outside the declared task write scope",
            retryable=False,
            details=details,
        )
    )


__all__ = [
    "AccessMode",
    "ChangeEndpoint",
    "ChangeScopeReport",
    "ChangeScopeViolation",
    "PathChange",
    "PathChangeKind",
    "ScopeConflict",
    "ScopeConflictKind",
    "ScopeConflictReport",
    "check_change_scope",
    "detect_scope_conflicts",
    "enforce_change_scope",
]
