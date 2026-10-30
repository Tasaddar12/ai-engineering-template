"""UI-consideration probe: the third adapter of the probe-core resolution model.

Ported from upstream ``src/ui-consideration-probe.cts`` of gsd-core (MIT, Copyright
(c) 2026 Open GSD) at pinned commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79.

Keeps only the UI-specific cluster: the six element kinds, the closed eight-category
shape-rooted UI state taxonomy, element classification, consideration proposal, the
propose-then-confirm view, the deterministic ``--auto`` floor and the
``explicit | backstop`` verification validators. The generic lifecycle, merge and CLI
scaffold live in ``probe_core``. Open, domain-specific UX considerations are prose-owned
in ``references/domain-probes.md``, not here.

CLI: ``python -m lib.ui_consideration_probe <elements.json> [resolutions.json]`` prints
the coverage report as JSON. Exit 0 on success; exit 2 with a usage line or an
``error:`` line on stderr for missing arguments, invalid JSON or any validation failure.

Deviations:
  - ``UI_CUES`` are compiled with ``re.ASCII`` so ``\\b`` keeps JavaScript's ASCII
    word-boundary semantics.
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

UI_CUES = {
    "form": re.compile(r"\b(forms?|inputs?|fields?|submit|validation|validate|password|email|checkbox|radio|textarea)\b", _FLAGS),
    "list-collection": re.compile(r"\b(lists?|listing|tables?|grids?|collections?|rows?|items?|cards?|feed|results?)\b", _FLAGS),
    "nav": re.compile(r"\b(nav|navigation|menus?|tabs?|breadcrumbs?|pagination|sidebars?)\b", _FLAGS),
    "media": re.compile(r"\b(images?|img|videos?|avatars?|thumbnails?|photos?|gallery|icons?)\b", _FLAGS),
    "interactive-control": re.compile(r"\b(buttons?|toggles?|switch|switches|dropdowns?|sliders?|controls?|pickers?)\b", _FLAGS),
    "static-content": re.compile(r"\b(labels?|headings?|titles?|paragraphs?|copy|descriptions?|text)\b", _FLAGS),
}

# The locked element vocabulary: exactly the keys of UI_CUES (single source of truth).
VALID_ELEMENT_KINDS = frozenset(UI_CUES)

UI_TAXONOMY = [
    {"id": "empty", "name": "Empty / no data", "elements": ["form", "list-collection", "media"], "consideration": "What is shown when there is no data — zero items, an unfilled form, or absent media?"},
    {"id": "loading", "name": "Loading / in-flight", "elements": ["form", "list-collection", "media", "nav", "interactive-control"], "consideration": "What is shown while data or content is still loading (skeleton, spinner, progressive reveal)?"},
    {"id": "error", "name": "Error / failure", "elements": ["form", "list-collection", "media", "nav", "interactive-control"], "consideration": "What is shown when the load or submit fails (message, retry affordance, partial fallback)?"},
    {"id": "populated", "name": "Populated / happy path", "elements": ["list-collection", "media"], "consideration": "What does the normal populated (happy-path) state look like at a typical volume of content?"},
    {"id": "partial", "name": "Partial / incomplete", "elements": ["form", "list-collection"], "consideration": "What is shown for partial or incomplete data — some fields or rows present, others missing?"},
    {"id": "overflow", "name": "Overflow / truncation", "elements": ["list-collection", "nav", "static-content"], "consideration": "What happens when content exceeds its container — scroll, clip, wrap, or truncate?"},
    {"id": "zero-one-many", "name": "Zero / one / many", "elements": ["list-collection"], "consideration": "How does the layout read at zero, one, and many items (singular vs plural copy, spacing)?"},
    {"id": "long-text", "name": "Long text", "elements": ["form", "static-content", "interactive-control", "nav"], "consideration": "What happens with unusually long text — truncation, wrapping, ellipsis, or reflow?"},
]

# Soft "review manually" signal for an element whose prose matched no cue; not a ninth
# taxonomy category, it only joins UI_VALIDATORS["categories"].
UNCLASSIFIED_CATEGORY = "unclassified"
_UNCLASSIFIED_PROBE = "unclassified — review manually"

UI_VALIDATORS = {
    "categories": [entry["id"] for entry in UI_TAXONOMY] + [UNCLASSIFIED_CATEGORY],
    "verification": ["explicit", "backstop"],
    "requiredFieldsByVerification": {"explicit": ["resolution"], "backstop": ["resolution"]},
}


def classify_element(text):
    """Detect which element kinds a description's prose matches (heuristic, English cues)."""
    subject = "" if text is None else str(text)
    return [kind for kind, cue in UI_CUES.items() if cue.search(subject)]


def applicable_categories(kinds):
    """Return the taxonomy category ids whose element kinds intersect ``kinds``."""
    wanted = set(kinds)
    return [entry["id"] for entry in UI_TAXONOMY if any(kind in wanted for kind in entry["elements"])]


def validate_requirement(element):
    """Validate an element: the generic id/text checks plus the UI-specific ones."""
    probe_core.validate_requirement(element)
    elements, text, text_en = element.get("elements"), element.get("text"), element.get("text_en")
    if elements is not None and not isinstance(elements, list):
        raise ValueError(f"element {element['id']} elements must be an array when present")
    if elements is None and not (isinstance(text, str) and text.strip()):
        raise ValueError(f"element {element['id']} text must be a non-empty string when no elements override is provided")
    if text_en is not None and not (isinstance(text_en, str) and text_en.strip()):
        raise ValueError(f"element {element['id']} text_en must be a non-empty string when present")


def validate_resolution(resolution):
    """Validate a UI-consideration resolution against the UI verification vocabulary."""
    return probe_core.validate_resolution(resolution, UI_VALIDATORS)


def propose_considerations(element):
    """Propose candidate considerations for an element; every item starts unresolved."""
    validate_requirement(element)
    if isinstance(element.get("elements"), list):
        for kind in element["elements"]:
            if not isinstance(kind, str) or kind not in VALID_ELEMENT_KINDS:
                raise ValueError(f"invalid element kind {json.dumps(kind)} for element {element['id']} — must be one of: {', '.join(UI_CUES)}")
        kinds = element["elements"]
    else:
        text_en = element.get("text_en")
        kinds = classify_element(element["text"] if text_en is None else text_en)
        if not kinds:
            return [{"requirement_id": element["id"], "category": UNCLASSIFIED_CATEGORY, "status": "unresolved",
                     "verification": None, "resolution": None, "reason": None, "probe": _UNCLASSIFIED_PROBE}]
    considerations = []
    for category_id in applicable_categories(kinds):
        entry = next((candidate for candidate in UI_TAXONOMY if candidate["id"] == category_id), None)
        considerations.append({"requirement_id": element["id"], "category": category_id, "status": "unresolved",
                               "verification": None, "resolution": None, "reason": None,
                               "probe": entry["consideration"] if entry else ""})
    return considerations


def analyze_coverage(elements, resolutions=None):
    """Propose considerations for every element, then merge resolutions and roll up coverage."""
    if not isinstance(elements, list):
        raise ValueError("elements must be an array")
    items, seen = [], set()
    for element in elements:
        validate_requirement(element)
        if element["id"] in seen:
            raise ValueError(f"duplicate element id {json.dumps(element['id'])}")
        seen.add(element["id"])
        items.extend(propose_considerations(element))
    return probe_core.analyze_coverage(items, [] if resolutions is None else resolutions, UI_VALIDATORS)


def propose_elements(elements):
    """Per-element propose-then-confirm view: detected kinds, categories, considerations.

    ``unclassified`` is true only when prose classified to zero cues; an explicit
    ``elements: []`` opt-out stays silent. Deterministic for an unchanged input.
    """
    proposals = []
    for element in elements:
        validate_requirement(element)
        considerations = propose_considerations(element)
        if isinstance(element.get("elements"), list):
            kinds = element["elements"]
        else:
            text_en = element.get("text_en")
            kinds = classify_element(element["text"] if text_en is None else text_en)
        unclassified = not isinstance(element.get("elements"), list) and len(kinds) == 0
        proposals.append({"id": element["id"], "kinds": kinds,
                          "categories": [] if unclassified else applicable_categories(kinds),
                          "considerations": considerations, "unclassified": unclassified})
    return proposals


def auto_resolve(items):
    """Deterministic ``--auto`` floor: backstop every applicable item, never dismiss.

    An ``unclassified`` item stays ``unresolved``; every other item resolves to a
    conservative ``backstop`` whose ``resolution`` is the taxonomy question.
    """
    resolutions = []
    for item in items:
        if item["category"] == UNCLASSIFIED_CATEGORY:
            resolutions.append({"requirement_id": item["requirement_id"], "category": item["category"], "status": "unresolved",
                                "verification": None, "resolution": None, "reason": None})
        else:
            resolutions.append({"requirement_id": item["requirement_id"], "category": item["category"], "status": "resolved",
                                "verification": "backstop", "resolution": item["probe"], "reason": None})
    return resolutions


def main(argv=None):
    """CLI entry point; returns the process exit code."""
    argv = sys.argv[1:] if argv is None else argv
    try:
        probe_core.run_probe_cli(analyze_coverage, "ui_consideration_probe.py <elements.json> [resolutions.json]", argv=argv)
    except ExitError as error:
        return error.code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
