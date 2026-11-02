"""Generic spec-phase probe resolution model shared by every probe adapter.

Ported from upstream ``src/probe-core.cts`` of gsd-core (MIT, Copyright (c) 2026
Open GSD) at pinned commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79.

Owns the resolution lifecycle, the status x verification re-cut,
``validate_resolution`` / ``validate_requirement``, the ``analyze_coverage``
merge / rollup / orphan-reject engine, the prohibition projection and
disposition helpers, the truth-axis honest-verifier helpers and the
``run_probe_cli`` I/O scaffold.

Two orthogonal axes:
  status: resolved | dismissed | unresolved   -- the shared resolution lifecycle
  verification: <probe-defined> | None         -- how a resolved item is verified

Data shapes are plain dicts with the upstream JSON field names (``requirement_id``,
``byVerification``, ``requiredFieldsByVerification`` ...), because every value
crosses a JSON boundary. Validation failures raise ``ValueError`` carrying the
upstream message text.

Deviations:
  - Upstream ``Error`` becomes ``ValueError``; ``ExitError`` is defined here as a
    minimal private equivalent of the upstream ``cli-exit`` module.
  - ``run_probe_cli`` takes ``argv`` as the user arguments only (no leading
    interpreter and script entries); upstream indexes ``process.argv[2]``/``[3]``,
    here they are ``argv[0]``/``argv[1]``. It is keyword-driven instead of an
    options object, and defaults to ``sys.argv[1:]``.
  - JSON parse error text comes from Python's ``json`` module, not V8.
  - Default output is always UTF-8 bytes, matching Node, regardless of the console code page.
  - The upstream tests that round-trip ``projectProhibitions`` / ``projectTruths``
    through ``frontmatter.parseMustHavesBlock`` are not ported: this repository has
    no ``must_haves`` block parser at the pinned base commit.
"""
from __future__ import annotations

import json
import re
import sys

VALID_STATUS = ["resolved", "dismissed", "unresolved"]

PROHIBITION_VALIDATORS = {
    "categories": [],
    "verification": ["test", "judgment"],
    # A resolved prohibition's checkable content is its statement, not a resolution
    # string, so neither tier requires one.
    "requiredFieldsByVerification": {"test": [], "judgment": []},
}

INSUFFICIENT_SPEC = "insufficient_spec"


class ExitError(Exception):
    """Raised by the default ``exit`` hook so entry points can translate it to a return code."""

    def __init__(self, code):
        super().__init__(f"exit {code}")
        self.code = code


def _js(value):
    """Render a value the way a JavaScript template literal would."""
    if value is None:
        return "undefined"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _nonblank(value):
    return value is not None and bool(str(value).strip())


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _key(entry):
    return f"{_js(entry.get('requirement_id'))}::{_js(entry.get('category'))}"


def _is_valid_item(item):
    """Structural guard for one item of the report ``items`` list."""
    if not isinstance(item, dict):
        return False
    requirement_id, category = item.get("requirement_id"), item.get("category")
    if not isinstance(requirement_id, str) or not requirement_id.strip():
        return False
    if not isinstance(category, str) or not category.strip():
        return False
    status = item.get("status")
    if not isinstance(status, str) or status not in VALID_STATUS:
        return False
    if not isinstance(item.get("probe"), str):
        return False
    for field in ("verification", "resolution", "reason"):
        if field not in item or (item[field] is not None and not isinstance(item[field], str)):
            return False
    return True


def _is_valid_report(report):
    """Structural guard for the report an adapter's ``analyze`` returns."""
    if not isinstance(report, dict):
        return False
    items = report.get("items")
    if not isinstance(items, list) or not all(_is_valid_item(item) for item in items):
        return False
    coverage = report.get("coverage")
    if not isinstance(coverage, dict):
        return False
    if not all(_is_number(coverage.get(field)) for field in ("applicable", "resolved", "unresolved")):
        return False
    return isinstance(coverage.get("byVerification"), dict)


def validate_requirement(requirement):
    """Validate a requirement's generic id/text fields; fail closed instead of coercing."""
    if not isinstance(requirement, dict):
        raise ValueError("requirement id must be a non-empty string (got undefined)")
    requirement_id = requirement.get("id")
    if not isinstance(requirement_id, str) or not requirement_id.strip():
        raise ValueError(f"requirement id must be a non-empty string (got {json.dumps(requirement_id)})")
    text = requirement.get("text")
    if text is not None and not isinstance(text, str):
        raise ValueError(f"requirement {requirement_id} text must be a string when present")


def validate_resolution(resolution, validators):
    """Validate a resolution against a probe's injected validators; return True on success."""
    if not isinstance(resolution, dict):
        raise ValueError("invalid status \"undefined\" for undefined::undefined")
    key = _key(resolution)
    status = resolution.get("status")
    if not isinstance(status, str) or status not in VALID_STATUS:
        raise ValueError(f"invalid status \"{_js(status)}\" for {key}")
    verification = resolution.get("verification")
    # verification is None unless the status is "resolved", for every status.
    if status != "resolved" and verification is not None:
        raise ValueError(f"verification must be null unless status is \"resolved\" (got \"{_js(verification)}\") for {key}")
    if status == "unresolved":
        if _nonblank(resolution.get("resolution")):
            raise ValueError(f"unresolved must not carry a resolution ({key})")
        if _nonblank(resolution.get("reason")):
            raise ValueError(f"unresolved must not carry a reason ({key})")
    if status == "dismissed" and not _nonblank(resolution.get("reason")):
        raise ValueError(f"dismissed requires a reason ({key})")
    if status == "resolved":
        tiers = ", ".join(validators["verification"])
        if verification is None:
            raise ValueError(f"resolved requires a verification tier (one of: {tiers}) for {key}")
        if not isinstance(verification, str) or verification not in validators["verification"]:
            raise ValueError(f"invalid verification \"{_js(verification)}\" for {key} — must be one of: {tiers}")
        for field in validators["requiredFieldsByVerification"].get(verification, []):
            if not _nonblank(resolution.get(field)):
                raise ValueError(f"{verification} requires a {field} ({key})")
    return True


def analyze_coverage(items, resolutions=None, validators=None):
    """Merge author resolutions onto already-proposed items and roll up coverage counts.

    ``coverage.resolved`` counts the closed items (``resolved`` plus ``dismissed``),
    which equals ``applicable - unresolved``. ``byVerification`` breaks the
    ``resolved``-status items down by tier, each tier initialised to 0. Raises on any
    invalid resolution, a duplicate, an orphan, or an item whose category is outside
    ``validators["categories"]``.
    """
    if not isinstance(items, list):
        raise ValueError("items must be an array")
    if validators is None:
        raise ValueError("validators are required")
    resolutions = [] if resolutions is None else resolutions
    if not isinstance(resolutions, list):
        raise ValueError("resolutions must be an array")
    resolution_map = {}
    for resolution in resolutions:
        validate_resolution(resolution, validators)
        if _key(resolution) in resolution_map:
            raise ValueError(f"duplicate resolution for {_key(resolution)}")
        resolution_map[_key(resolution)] = resolution
    valid_categories = set(validators["categories"])
    merged, item_keys = [], set()
    for item in items:
        if item.get("category") not in valid_categories:
            raise ValueError(
                f"item {_key(item)} has unknown category \"{_js(item.get('category'))}\" — not one of: {', '.join(validators['categories'])}")
        item_keys.add(_key(item))
        override = resolution_map.get(_key(item))
        if override is not None:
            merged.append({**item, "status": override["status"], "verification": override.get("verification"),
                           "resolution": override.get("resolution"), "reason": override.get("reason")})
        else:
            # Rolled up verbatim, so the item's own status/fields must be valid too.
            validate_resolution(item, validators)
            merged.append(item)
    for key in resolution_map:
        if key not in item_keys:
            raise ValueError(f"unknown resolution for {key} — no matching proposed item (typo'd category or non-applicable shape?)")
    unresolved = sum(1 for item in merged if item["status"] == "unresolved")
    applicable = len(merged)
    by_verification = {tier: 0 for tier in validators["verification"]}
    for item in merged:
        if item["status"] == "resolved" and item.get("verification") is not None:
            by_verification[item["verification"]] = by_verification.get(item["verification"], 0) + 1
    return {"items": merged, "coverage": {
        "applicable": applicable, "resolved": applicable - unresolved, "unresolved": unresolved,
        "unclassified": sum(1 for item in merged if item["category"] == "unclassified"),
        "byVerification": by_verification}}


def validate_prohibition_resolution(resolution):
    """Validate a prohibition resolution against the ``test | judgment`` vocabulary."""
    return validate_resolution(resolution, PROHIBITION_VALIDATORS)


def _truthy_text(value):
    return isinstance(value, str) and value.strip() != ""


def project_prohibitions(items):
    """Project prohibition items into the ``must_haves.prohibitions`` list shape.

    Emits ``statement`` and ``status`` always, ``verification`` and ``reason`` when
    present, and the flat ``check_*`` scalars only for a well-formed descriptor (a
    valid ``check_kind`` and a non-empty ``check_target``). A non-list input projects
    to an empty list.
    """
    if not isinstance(items, list):
        return []
    out = []
    for item in items:
        if isinstance(item, list):
            item = {}
        if not isinstance(item, dict):
            continue
        statement = item.get("statement")
        status = item.get("status")
        entry = {"statement": statement if isinstance(statement, str) else "",
                 "status": status if isinstance(status, str) else "unresolved"}
        if item.get("verification") is not None:
            entry["verification"] = _js(item["verification"])
        if item.get("reason") is not None and _nonblank(item["reason"]):
            entry["reason"] = _js(item["reason"])
        kind = item.get("check_kind")
        if kind in ("node-test", "lint-rule") and _truthy_text(item.get("check_target")):
            entry["check_kind"] = kind
            entry["check_target"] = item["check_target"]
            if kind == "lint-rule" and _truthy_text(item.get("check_rule")):
                entry["check_rule"] = item["check_rule"]
            if _truthy_text(item.get("check_violation_fixture")):
                entry["check_violation_fixture"] = item["check_violation_fixture"]
            if _truthy_text(item.get("check_clean_fixture")):
                entry["check_clean_fixture"] = item["check_clean_fixture"]
        out.append(entry)
    return out


def disposition_for_prohibition(prohibition, context=None):
    """Fail-closed verify-time disposition for a single prohibition.

    Without enforcement evidence the result is always ``unverified`` and flagged;
    only a test-tier item with evidence is ``green``.
    """
    prohibition = prohibition if isinstance(prohibition, dict) else {}
    verification = prohibition.get("verification")
    tier = verification if verification in ("test", "judgment") else None
    evidence = (context or {}).get("enforcementEvidence")
    has_enforcement = isinstance(evidence, list) and len(evidence) > 0
    if not has_enforcement:
        reason = ("test-tier prohibition has no passing wired enforcement check — flagged unverified (fail-closed; never a silent pass, ADR-550 D5d)"
                  if tier == "test" else
                  "prohibition has no enforcement evidence — flagged unverified (fail-closed; never a silent pass, ADR-550 D5d)")
        return {"status": "unverified", "flagged": True, "tier": tier, "reason": reason}
    if tier == "test":
        return {"status": "green", "flagged": False, "tier": tier,
                "reason": "test-tier prohibition has wired enforcement evidence"}
    return {"status": "unverified", "flagged": True, "tier": tier,
            "reason": "judgment-tier prohibition routes to judgment review — never a silent green (ADR-550 D4)"}


def truth_statement(truth):
    """Extract a truth's statement from its string or object form."""
    if isinstance(truth, str):
        return truth
    if isinstance(truth, dict) and isinstance(truth.get("statement"), str):
        return truth["statement"]
    return ""


def truth_verification(truth):
    """Extract a truth's verification tier, or None. Tolerates stray whitespace and quotes."""
    if not isinstance(truth, dict):
        return None
    raw = truth.get("verification")
    value = re.sub(r"^[\"']|[\"']\Z", "", raw.strip()).strip() if isinstance(raw, str) else raw
    return value if value in ("explicit", "backstop") and isinstance(value, str) else None


def project_truths(items):
    """Project truths into a ``must_haves.truths`` block; only ``backstop`` keeps a marker."""
    if not isinstance(items, list):
        return []
    out = []
    for item in items:
        statement = truth_statement(item)
        if not statement:
            continue
        if truth_verification(item) == "backstop":
            out.append({"statement": statement, "verification": "backstop"})
        else:
            out.append(statement)
    return out


def disposition_for_unverifiable_truth(truth, context=None):
    """Verify-time disposition for a truth: a ``backstop`` truth without evidence abstains."""
    tier = truth_verification(truth)
    if tier != "backstop":
        return {"status": "green", "flagged": False, "tier": tier,
                "reason": "inferable truth — verified normally (no abstention; ADR-550 D4 over-abstention guard)"}
    evidence = (context or {}).get("evidence")
    if not isinstance(evidence, list) or len(evidence) == 0:
        return {"status": "unverified", "flagged": True, "tier": tier, "reason": INSUFFICIENT_SPEC}
    return {"status": "green", "flagged": False, "tier": tier,
            "reason": "backstop truth confirmed by explicit evidence (a passing wired held-out/property test or directly-observed behavior)"}


def _stream_writer(stream):
    """Write UTF-8 to a real text stream's byte layer; fall back to ``stream.write``."""
    def emit(text):
        buffer = getattr(stream, "buffer", None)
        if buffer is None:
            stream.write(text)
            return
        stream.flush()
        buffer.write(text.encode("utf-8"))
        buffer.flush()
    return emit


def run_probe_cli(analyze, usage, argv=None, read_file=None, write=None, write_err=None, exit=None):
    """Read the requirements (and optional resolutions) file, run ``analyze``, print the report.

    With no requirements path the usage line goes to stderr and the exit hook gets 2.
    A JSON parse failure, an ``analyze`` exception or a structurally invalid report is
    a handled error (stderr plus exit code 2), never a traceback. ``exit`` defaults to
    raising ``ExitError``; when an injected ``exit`` returns, processing stops.
    """
    argv = sys.argv[1:] if argv is None else argv

    def default_read(path):
        with open(path, encoding="utf-8-sig") as stream:
            return stream.read()

    read_file = read_file or default_read
    write = write or _stream_writer(sys.stdout)
    write_err = write_err or _stream_writer(sys.stderr)

    def default_exit(code):
        raise ExitError(code)

    exit = exit or default_exit
    requirements_path = argv[0] if len(argv) > 0 else None
    resolutions_path = argv[1] if len(argv) > 1 else None
    if not requirements_path:
        write_err(f"usage: {usage}\n")
        exit(2)
        return
    try:
        requirements = json.loads(read_file(requirements_path))
    except (ValueError, OSError) as error:
        write_err(f"error: cannot parse JSON from {requirements_path}: {error}\n")
        exit(2)
        return
    resolutions = []
    if resolutions_path:
        try:
            resolutions = json.loads(read_file(resolutions_path))
        except (ValueError, OSError) as error:
            write_err(f"error: cannot parse JSON from {resolutions_path}: {error}\n")
            exit(2)
            return
    try:
        report = analyze(requirements, resolutions)
        if not _is_valid_report(report):
            raise ValueError("adapter returned a structurally-invalid coverage report (expected { items[], coverage{ applicable, resolved, unresolved, byVerification } })")
        write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    except ExitError:
        raise
    except Exception as error:  # fail closed: surface every adapter failure as exit 2
        write_err(f"error: {error}\n")
        exit(2)
