"""STATE.md field schema: the single row-per-key declaration of STATE.md frontmatter keys.

Port of ``src/state-md-schema.cts`` from gsd-core at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).

The module is a leaf: it imports nothing from the package. Every exported
mapping is read-only (``MappingProxyType``) and keeps upstream's key order,
which is observable by consumers that iterate the table.

Deviations:
- ``FieldSource`` / ``FieldPreservation`` / ``FieldGuard`` / ``FieldMergeStrategy``
  (TypeScript string-literal unions) become tuples of the allowed members:
  ``FIELD_SOURCES``, ``FIELD_PRESERVATIONS``, ``FIELD_GUARDS``,
  ``FIELD_MERGE_STRATEGIES``. ``validate_state_field_schema`` checks rows
  against them, which the TypeScript compiler does upstream.
- Row field names stay camelCase (``bodySource``, ``bodyLabel``,
  ``acceptedShapes``, ``mergeStrategy``) so JSON projections match upstream.
- ``state-transition.cts`` / ``state.cts`` projections (``FIELD_CLASSIFICATION``
  and friends) are not part of this module upstream and are not ported here.
- The key ``gsd_state_version`` is kept verbatim from upstream. The repo
  template and ``onboarding.py`` write ``engineer_state_version``.
"""
from __future__ import annotations

from types import MappingProxyType

FIELD_SOURCES = ("body", "disk", "external", "curated", "free")
FIELD_PRESERVATIONS = ("derive", "preserve-when-unchanged", "preserve-always", "preserve-if-placeholder")
FIELD_GUARDS = ("non-sentinel-unknown",)
FIELD_MERGE_STRATEGIES = ("progress-ratchet",)
FIELD_TYPES = ("string", "number", "boolean", "object")
FIELD_CARDINALITIES = ("one", "optional", "many")
FIELD_EMISSIONS = ("always", "when-present")

STATUS_LIFECYCLE_ENUM = ("unknown", "paused", "executing", "planning", "discussing", "verifying", "completed")


def _row(type, cardinality, source, preservation, emitted, **extra):
    row = {"type": type, "cardinality": cardinality, "source": source, "preservation": preservation, "emitted": emitted}
    row.update(extra)
    return MappingProxyType(row)


def _build():
    return {
        # Schema
        "gsd_state_version": _row("string", "one", "free", "derive", "always"),
        # Milestone (external - from ROADMAP.md)
        "milestone": _row("string", "optional", "external", "preserve-if-placeholder", "when-present"),
        "milestone_name": _row("string", "optional", "external", "preserve-if-placeholder", "when-present"),
        # Phase / plan position (body-derived)
        "current_phase": _row("string", "optional", "body", "preserve-when-unchanged", "when-present",
                              bodySource=("Current Phase",), bodyLabel="Current Phase"),
        "current_phase_name": _row("string", "optional", "curated", "preserve-when-unchanged", "when-present",
                                   bodySource=("Current Phase Name",), bodyLabel="Current Phase Name"),
        # `Current Plan` parses as a bare number `N` or the anchored hybrid `N of M`
        # (`^(\d+)\s+of\s+(\d+)\s*$`); `N/M` stays undeclared and must keep failing.
        "current_plan": _row("string", "optional", "body", "preserve-when-unchanged", "when-present",
                             bodySource=("Current Plan",), bodyLabel="Current Plan",
                             acceptedShapes=("N", "N of M")),
        # Status / lifecycle (body-derived; #1230 delta heuristic applies). The
        # 'unknown' sentinel is the only executor-side guard in this table.
        "status": _row("string", "one", "body", "preserve-when-unchanged", "always",
                       enum=STATUS_LIFECYCLE_ENUM, guard="non-sentinel-unknown",
                       bodySource=("Status",), bodyLabel="Status"),
        "stopped_at": _row("string", "optional", "body", "preserve-when-unchanged", "when-present",
                           bodySource=("Stopped At", "Stopped at"), bodyLabel="Stopped At"),
        "paused_at": _row("string", "optional", "body", "preserve-when-unchanged", "when-present",
                          bodySource=("Paused At",), bodyLabel="Paused At"),
        # Activity log
        "last_updated": _row("string", "one", "free", "derive", "always"),
        # `last_activity` carries bodySource but deliberately NO bodyLabel: its
        # preservation is 'derive', so it never reaches a label lookup.
        "last_activity": _row("string", "optional", "body", "derive", "when-present",
                              bodySource=("Last Activity", "Last activity")),
        "last_activity_desc": _row("string", "optional", "body", "preserve-when-unchanged", "when-present",
                                   bodySource=("Last Activity Description",), bodyLabel="Last Activity Description"),
        # Commit provenance (#2573): recomputed on every write, never preserved.
        "state_head": _row("string", "optional", "free", "derive", "when-present"),
        # Progress block (disk-derived, except the curated progress ratchet).
        "progress": _row("object", "optional", "curated", "preserve-always", "when-present",
                         mergeStrategy="progress-ratchet"),
        "progress.total_phases": _row("number", "optional", "disk", "derive", "when-present"),
        "progress.completed_phases": _row("number", "optional", "disk", "derive", "when-present"),
        "progress.total_plans": _row("number", "optional", "disk", "derive", "when-present"),
        "progress.completed_plans": _row("number", "optional", "disk", "derive", "when-present"),
        "progress.percent": _row("number", "optional", "disk", "derive", "when-present"),
    }


STATE_FIELD_SCHEMA = MappingProxyType(_build())

_ALLOWED = {
    "type": FIELD_TYPES,
    "cardinality": FIELD_CARDINALITIES,
    "source": FIELD_SOURCES,
    "preservation": FIELD_PRESERVATIONS,
    "emitted": FIELD_EMISSIONS,
    "guard": FIELD_GUARDS,
    "mergeStrategy": FIELD_MERGE_STRATEGIES,
}


def validate_state_field_schema(schema=None):
    """Return a list of human-readable problems with ``schema`` (default: the shipped one).

    Python replacement for the compile-time checks TypeScript performs upstream.
    """
    problems = []
    for key, row in (STATE_FIELD_SCHEMA if schema is None else schema).items():
        for field, allowed in _ALLOWED.items():
            if field in row and row[field] not in allowed:
                problems.append(f"{key}.{field}: {row[field]!r} is not one of {list(allowed)}")
        for required in ("type", "cardinality", "source", "preservation", "emitted"):
            if required not in row:
                problems.append(f"{key}: missing required field {required!r}")
    return problems
