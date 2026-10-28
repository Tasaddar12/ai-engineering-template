"""Spec-completeness edge probe: the first adapter of the probe-core resolution model.

Ported from upstream ``src/edge-probe.cts`` of gsd-core (MIT, Copyright (c) 2026
Open GSD) at pinned commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79.

The generic lifecycle, ``validate_resolution``, ``analyze_coverage`` and the CLI
scaffold live in ``probe_core``. This module keeps the edge-specific cluster: the
five data/behavior shapes, the closed eight-category edge taxonomy, shape
classification, edge proposal and the ``explicit | backstop`` verification
validators.

CLI: ``python -m lib.edge_probe <requirements.json> [resolutions.json]`` prints the
coverage report as JSON. Exit 0 on success; exit 2 with a usage line or an
``error:`` line on stderr for missing arguments, invalid JSON or any validation
failure.

Deviations:
  - ``SHAPE_CUES`` are compiled with ``re.ASCII`` so ``\\b`` keeps JavaScript's
    ASCII word-boundary semantics.
  - ``main`` takes the user arguments only (upstream indexes ``process.argv``).
  - Errors are ``ValueError`` with the upstream message text.
"""
from __future__ import annotations

import json
import re
import sys

from . import probe_core
from .probe_core import ExitError

_FLAGS = re.IGNORECASE | re.ASCII

SHAPE_CUES = {
    "numeric-range": re.compile(r"\b(round(ing|ed)?|threshold|max(imum)?|min(imum)?|limit|bound(ary)?|between|cap|percent|amount|price|count|number|score|rate|decimal)\b", _FLAGS),
    "collection": re.compile(r"\b(lists?|arrays?|sets?|items?|collections?|each|every|all|sort(ed|ing)?|merge|dedupe|group|ranges?|intervals?|overlap(ping)?)\b", _FLAGS),
    "text": re.compile(r"\b(string|text|names?|labels?|truncate|substring|char(acter)?s?|length|slug|message|unicode)\b", _FLAGS),
    "stateful": re.compile(r"\b(save|persist|store|update|toggle|create|delete|remove|submit|retry|apply|register|insert)\b", _FLAGS),
    "io": re.compile(r"\b(files?|requests?|fetch|upload|download|network|api|endpoints?|connections?|sockets?)\b", _FLAGS),
}

# The locked shape vocabulary: exactly the keys of SHAPE_CUES (single source of truth).
VALID_SHAPES = frozenset(SHAPE_CUES)

TAXONOMY = [
    {"id": "boundary", "name": "Boundary values", "shapes": ["numeric-range"], "probe": "What happens exactly at each min/max/threshold — and one step either side?"},
    {"id": "adjacency", "name": "Adjacency / touching", "shapes": ["collection"], "probe": "When two things are exactly equal or just touch, do they merge, collide, or separate?"},
    {"id": "empty", "name": "Empty / degenerate", "shapes": ["collection", "text"], "probe": "What is the result for empty, single-element, or null input?"},
    {"id": "encoding", "name": "Encoding / representation", "shapes": ["text"], "probe": "Whose definition of length/equality applies — bytes, code points, grapheme clusters, or normalized form?"},
    {"id": "ordering", "name": "Ordering / stability", "shapes": ["collection"], "probe": "When elements compare equal, is output order specified and stable?"},
    {"id": "precision", "name": "Precision / overflow", "shapes": ["numeric-range"], "probe": "Where can precision loss, overflow, or rounding/tie-breaking occur — and what is the exact contract (e.g. half-up vs half-to-even, ceil/floor/truncate)?"},
    {"id": "idempotency", "name": "Idempotency / repetition", "shapes": ["stateful"], "probe": "What happens if this runs twice on the same input?"},
    {"id": "concurrency", "name": "Concurrency / effect ordering", "shapes": ["stateful", "io"], "probe": "If interrupted or run in parallel, what is guaranteed?"},
]

# Soft "review manually" signal for a requirement whose prose matched no shape cue. It is
# not a ninth taxonomy category; it only joins EDGE_VALIDATORS["categories"].
UNCLASSIFIED_CATEGORY = "unclassified"
_UNCLASSIFIED_PROBE = "unclassified — review manually"

EDGE_VALIDATORS = {
    "categories": [entry["id"] for entry in TAXONOMY] + [UNCLASSIFIED_CATEGORY],
    "verification": ["explicit", "backstop"],
    "requiredFieldsByVerification": {"explicit": ["resolution"], "backstop": ["resolution"]},
}


def classify_shape(text):
    """Detect which shapes a requirement's prose matches (heuristic, English cues)."""
    subject = "" if text is None else str(text)
    return [shape for shape, cue in SHAPE_CUES.items() if cue.search(subject)]


def applicable_categories(shapes):
    """Return the taxonomy category ids whose shapes intersect ``shapes``."""
    wanted = set(shapes)
    return [entry["id"] for entry in TAXONOMY if any(shape in wanted for shape in entry["shapes"])]


def validate_requirement(requirement):
    """Validate a requirement: the generic id/text checks plus the edge-specific ones."""
    probe_core.validate_requirement(requirement)
    shapes, text, text_en = requirement.get("shapes"), requirement.get("text"), requirement.get("text_en")
    if shapes is not None and not isinstance(shapes, list):
        raise ValueError(f"requirement {requirement['id']} shapes must be an array when present")
    if shapes is None and not (isinstance(text, str) and text.strip()):
        raise ValueError(f"requirement {requirement['id']} text must be a non-empty string when no shapes override is provided")
    if text_en is not None and not (isinstance(text_en, str) and text_en.strip()):
        raise ValueError(f"requirement {requirement['id']} text_en must be a non-empty string when present")


def validate_resolution(resolution):
    """Validate an edge resolution against the edge verification vocabulary."""
    return probe_core.validate_resolution(resolution, EDGE_VALIDATORS)


def propose_edges(requirement):
    """Propose candidate edges for a requirement; every edge starts unresolved."""
    validate_requirement(requirement)
    if isinstance(requirement.get("shapes"), list):
        for shape in requirement["shapes"]:
            if not isinstance(shape, str) or shape not in VALID_SHAPES:
                raise ValueError(f"invalid shape {json.dumps(shape)} for requirement {requirement['id']} — must be one of: {', '.join(SHAPE_CUES)}")
        shapes = requirement["shapes"]
    else:
        text_en = requirement.get("text_en")
        shapes = classify_shape(requirement["text"] if text_en is None else text_en)
        if not shapes:
            return [{"requirement_id": requirement["id"], "category": UNCLASSIFIED_CATEGORY, "status": "unresolved",
                     "verification": None, "resolution": None, "reason": None, "probe": _UNCLASSIFIED_PROBE}]
    edges = []
    for category_id in applicable_categories(shapes):
        entry = next((candidate for candidate in TAXONOMY if candidate["id"] == category_id), None)
        edges.append({"requirement_id": requirement["id"], "category": category_id, "status": "unresolved",
                      "verification": None, "resolution": None, "reason": None,
                      "probe": entry["probe"] if entry else ""})
    return edges


def analyze_coverage(requirements, resolutions=None):
    """Propose edges for every requirement, then merge resolutions and roll up coverage."""
    if not isinstance(requirements, list):
        raise ValueError("requirements must be an array")
    items, seen = [], set()
    for requirement in requirements:
        validate_requirement(requirement)
        if requirement["id"] in seen:
            raise ValueError(f"duplicate requirement id {json.dumps(requirement['id'])}")
        seen.add(requirement["id"])
        items.extend(propose_edges(requirement))
    return probe_core.analyze_coverage(items, [] if resolutions is None else resolutions, EDGE_VALIDATORS)


def main(argv=None):
    """CLI entry point; returns the process exit code."""
    argv = sys.argv[1:] if argv is None else argv
    try:
        probe_core.run_probe_cli(analyze_coverage, "edge_probe.py <requirements.json> [resolutions.json]", argv=argv)
    except ExitError as error:
        return error.code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
