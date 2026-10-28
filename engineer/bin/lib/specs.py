"""Specification projections and explicit probe resolutions, never AI judgment."""
import json
import re
from .core import Failure, input_json, read, safe_path

UI_KINDS = {
    "form": r"\bform|input|submit|field\b", "list-collection": r"\blist|collection|table|rows|grid|feed\b",
    "nav": r"\bnav|menu|breadcrumb|tabs?\b", "media": r"\bimage|video|audio|media|photo\b",
    "interactive-control": r"\bbutton|toggle|slider|switch|control\b", "static-content": r"\btext|paragraph|article|heading|content\b",
}
UI_CATEGORIES = {
    "empty": ("form list-collection media", "What appears when no data or media exists?"),
    "loading": ("form list-collection media nav interactive-control", "What appears while data or content is in flight?"),
    "error": ("form list-collection media nav interactive-control", "How is failure communicated and retried?"),
    "populated": ("list-collection media", "What is the typical populated state?"),
    "partial": ("form list-collection", "What appears for incomplete fields or rows?"),
    "overflow": ("list-collection nav static-content", "How does content exceeding its container behave?"),
    "zero-one-many": ("list-collection", "What changes across zero, one and many items?"),
    "long-text": ("form static-content interactive-control nav", "What happens with unusually long text?"),
}


def _load(args):
    return input_json(None if args.has("stdin") else args.get("input", args.arg(0)))


def _resolution(item, tiers):
    state = item.get("status", "unresolved")
    if state not in ("resolved", "dismissed", "unresolved"):
        raise Failure("invalid-probe-state", str(state), 2)
    if state == "dismissed" and not str(item.get("reason", "")).strip():
        raise Failure("invalid-probe-resolution", "Dismissal needs an actual reason", 2)
    if state == "resolved" and (item.get("verification") not in tiers or not str(item.get("resolution", "")).strip()):
        raise Failure("invalid-probe-resolution", "Resolution needs a supported verification tier and concrete obligation", 2)
    return {"status": state, **{key: item.get(key) for key in ("verification", "resolution", "reason")}}


def _coverage(items):
    return {"applicable": len(items), "resolved": sum(item["status"] == "resolved" for item in items),
            "dismissed": sum(item["status"] == "dismissed" for item in items),
            "unresolved": sum(item["status"] == "unresolved" for item in items),
            "unclassified": sum(item.get("category") == "unclassified" for item in items)}


def command(args, action):
    value = _load(args)
    if action == "ui":
        elements = value.get("elements") if isinstance(value, dict) else value
        if not isinstance(elements, list) or not elements:
            raise Failure("invalid-ui-elements", "Supply a nonempty array of actual UI element descriptions", 2)
        resolutions = value.get("resolutions", []) if isinstance(value, dict) else []
        indexed = {}
        for item in resolutions:
            if not isinstance(item, dict) or not item.get("element_id") or item.get("category") not in (*UI_CATEGORIES, "unclassified"):
                raise Failure("invalid-ui-resolution", "Resolution needs element_id and a recognized category", 2)
            key = (item["element_id"], item["category"])
            if key in indexed:
                raise Failure("duplicate-ui-resolution", str(key), 2)
            indexed[key] = _resolution(item, ("explicit", "backstop"))
        items, classified, ids = [], [], set()
        for element in elements:
            if not isinstance(element, dict) or not isinstance(element.get("id"), str) or not isinstance(element.get("text"), str) or not element["text"].strip() or "<replace:" in element["text"]:
                raise Failure("invalid-ui-element", "Every element needs an id and concrete text", 2)
            if element["id"] in ids:
                raise Failure("duplicate-ui-element", element["id"], 2)
            ids.add(element["id"])
            kinds = element.get("elements")
            if kinds is None:
                kinds = [kind for kind, pattern in UI_KINDS.items() if re.search(pattern, element.get("text_en", element["text"]), re.I)]
            if not isinstance(kinds, list) or any(kind not in UI_KINDS for kind in kinds):
                raise Failure("invalid-ui-kind", "Override must contain recognized UI kinds", 2)
            classified.append({"id": element["id"], "elements": kinds, "requiresConfirmation": "elements" not in element})
            categories = [category for category, (applies, _) in UI_CATEGORIES.items() if set(kinds) & set(applies.split())]
            for category in categories or ["unclassified"]:
                resolution = indexed.get((element["id"], category), {"status": "unresolved", "verification": None, "resolution": None, "reason": None})
                if category == "unclassified" and resolution["status"] == "resolved":
                    raise Failure("unclassified-ui-resolution", "Classify the surface before inventing state obligations", 2)
                items.append({"element_id": element["id"], "category": category, **resolution,
                              "probe": UI_CATEGORIES[category][1] if category in UI_CATEGORIES else "Review this surface manually; no finite kind was recognized"})
        unknown = [key for key in indexed if key[0] not in ids or not any(row["element_id"] == key[0] and row["category"] == key[1] for row in items)]
        if unknown:
            raise Failure("orphan-ui-resolution", "Resolution does not correspond to a raised consideration", entries=unknown)
        return {"items": items, "elements": classified, "coverage": _coverage(items), "behaviorVerified": False}
    if action in ("prohibitions", "project", "coverage"):
        entries = value.get("items", value.get("prohibitions", [])) if isinstance(value, dict) else value
        if not isinstance(entries, list):
            raise Failure("invalid-prohibitions", "Supply an authored array; prohibition recall is not a deterministic classifier", 2)
        items, ids = [], set()
        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("id") or not entry.get("requirement_id") or not str(entry.get("text", "")).strip():
                raise Failure("invalid-prohibition", "Each prohibition requires id, requirement_id and actual must-NOT text", 2)
            if entry["id"] in ids:
                raise Failure("duplicate-prohibition", entry["id"], 2)
            ids.add(entry["id"])
            item = {**entry, **_resolution(entry, ("test", "judgment"))}
            if item.get("status") == "resolved" and item.get("verification") == "test":
                if not item.get("check_target") or not item.get("check_kind"):
                    item["missing_check_descriptor"] = True
                elif item["check_kind"] not in ("node-test", "lint-rule", "command", "python-test"):
                    raise Failure("invalid-prohibition-check", str(item["check_kind"]), 2)
            items.append(item)
        return {"items": items, "prohibitions": items, "coverage": _coverage(items),
                "judgmentRequired": [item["id"] for item in items if item.get("verification") == "judgment"], "behaviorVerified": False}
    raise Failure("unknown-spec-operation", action, 2)
