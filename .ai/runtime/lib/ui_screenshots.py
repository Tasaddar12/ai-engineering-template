"""Deterministic screenshot matrix coverage; no browser or visual verdicts."""
import hashlib
import itertools
import json
from pathlib import Path
import re
import uuid

from .results import VerbError, require


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _unique_strings(value):
    return (isinstance(value, list) and bool(value) and all(_text(x) for x in value)
            and len(set(value)) == len(value))


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        raise VerbError("cannot read screenshot input: " + str(exc), "bad-screenshot-input") from None


def requirements(scope, expected_revision):
    """Expand a separately planned scope; shared edits require every inventoried route."""
    def check(condition, message):
        require(condition, message, "bad-screenshot-scope")

    check(isinstance(scope, dict), "screenshot scope must be an object")
    check(isinstance(expected_revision, str) and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", expected_revision),
          "expected revision must be a full lowercase commit ID")
    check(type(scope.get("schema")) is int and scope.get("schema") == 1 and scope.get("revision") == expected_revision,
          "scope schema/revision does not match the requested revision")
    routes = scope.get("routes")
    check(isinstance(routes, list) and bool(routes), "scope needs the dependent route inventory")
    ids = [r.get("route") if isinstance(r, dict) else None for r in routes]
    check(all(_text(x) for x in ids) and len(set(ids)) == len(ids), "route IDs must be unique strings")
    kind = scope.get("change_kind")
    check(kind in ("local", "shared"), "change_kind must be local or shared")
    affected = scope.get("affected_routes")
    check(_unique_strings(affected) and set(affected) <= set(ids), "affected_routes must name inventory routes")
    selected = set(ids) if kind == "shared" else set(affected)
    rows = []
    for route in routes:
        check(_text(route.get("url")) and route["url"].startswith(("http://", "https://")), "route needs an HTTP URL")
        check(_unique_strings(route.get("criteria")), "route needs unique acceptance criterion IDs")
        states, viewports = route.get("states"), route.get("viewports")
        check(isinstance(states, dict) and bool(states) and all(_text(k) and _text(v) for k, v in states.items()),
              "states must map state IDs to exact capture procedures")
        check(isinstance(viewports, dict) and bool(viewports), "route needs viewport definitions")
        for name, size in viewports.items():
            check(_text(name) and isinstance(size, dict) and set(size) == {"width", "height"}
                  and all(type(v) is int and v > 0 for v in size.values()), "viewport needs positive integer width/height")
        if route["route"] not in selected:
            continue
        for criterion, state, viewport in itertools.product(route["criteria"], states, viewports):
            rows.append({"criterion": criterion, "route": route["route"], "state": state,
                         "viewport": viewport, "width": viewports[viewport]["width"],
                         "height": viewports[viewport]["height"], "url": route["url"],
                         "procedure": states[state], "revision": expected_revision})
    return rows


def _key(row):
    return tuple(row.get(k) for k in ("criterion", "route", "state", "viewport"))


def validate(scope, manifest, expected_revision, artifact_root):
    """Return every missing cell; malformed or mismatched evidence never covers it."""
    expected = requirements(scope, expected_revision)
    required = {_key(row): row for row in expected}
    errors, covered, indexed = [], [], {}
    if (not isinstance(manifest, dict) or type(manifest.get("schema")) is not int
            or manifest.get("schema") != 1):
        manifest = {}
        errors.append("manifest must be a schema 1 object")
    if manifest.get("revision") != expected_revision:
        errors.append("manifest revision mismatch")
    captures = manifest.get("captures", [])
    if not isinstance(captures, list):
        captures = []
        errors.append("captures must be a list")
    for index, row in enumerate(captures):
        if not isinstance(row, dict) or any(not _text(row.get(k)) for k in ("criterion", "route", "state", "viewport")):
            errors.append("capture %d has invalid matrix identity" % index)
            continue
        key = _key(row)
        indexed.setdefault(key, []).append(row)
        if key not in required:
            errors.append("unexpected capture: " + "/".join(key))
    missing = []
    root = Path(artifact_root)
    for key, wanted in required.items():
        rows = indexed.get(key, [])
        reason = None
        row = rows[0] if rows else {}
        if not rows:
            reason = "missing capture"
        elif len(rows) != 1:
            reason = "duplicate capture"
        elif errors and manifest.get("revision") != expected_revision:
            reason = "manifest revision mismatch"
        elif any(row.get(k) != value or type(row.get(k)) is not type(value) for k, value in wanted.items()):
            reason = "capture binding mismatch"
        elif row.get("result") != "captured":
            reason = "capture result: " + str(row.get("result", "missing"))
        elif row.get("error"):
            reason = "captured result contradicts capture error"
        elif not _text(row.get("artifact")) or not isinstance(row.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
            reason = "missing artifact reference/digest"
        else:
            try:
                artifact = Path(row["artifact"])
                data = (artifact if artifact.is_absolute() else root / artifact).read_bytes()
                if not data or hashlib.sha256(data).hexdigest() != row["sha256"]:
                    reason = "artifact digest mismatch or empty artifact"
            except (OSError, ValueError) as exc:
                reason = "artifact unavailable: " + str(exc)
        if reason:
            missing.append(dict(wanted, reason=reason))
        else:
            covered.append(dict(wanted, artifact=row["artifact"], sha256=row["sha256"]))
    return {"status": "complete" if not missing and not errors else "gaps_found",
            "revision": expected_revision, "required_count": len(expected),
            "covered_count": len(covered), "covered": covered, "missing": missing, "errors": errors}


def produce(scope, expected_revision, capture, artifact_root):
    """One consumer adapter: capture(requirement, target_path), once per matrix cell.

    The adapter drives the existing browser harness and writes image bytes to the
    target. An exception records a failed attempt without discarding other cells.
    This interface never claims that a browser visited anything by itself.
    """
    rows = requirements(scope, expected_revision)
    root = Path(artifact_root)
    root.mkdir(parents=True, exist_ok=True)
    captures = []
    for index, wanted in enumerate(rows):
        # Use a fresh name so a failed/no-op adapter cannot reuse a stale image.
        target = root / ("capture-%d-%s.png" % (index, uuid.uuid4().hex))
        row = dict(wanted, result="failed", artifact=str(target.resolve()), sha256=None)
        try:
            capture(dict(wanted), target)
            data = target.read_bytes()
            if not data:
                raise ValueError("capture artifact is empty")
            row.update(result="captured", sha256=hashlib.sha256(data).hexdigest())
        except Exception as exc:
            row["error"] = str(exc)
        captures.append(row)
    return {"schema": 1, "revision": expected_revision, "captures": captures}


def validate_files(scope_file, manifest_file, expected_revision):
    return validate(read_json(scope_file), read_json(manifest_file), expected_revision,
                    Path(manifest_file).resolve().parent)
