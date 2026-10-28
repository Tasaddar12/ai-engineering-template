"""Health diagnostic rule table: shared types, phase-id helpers and the rule groups.

Port of ``src/health-diagnostic-types.cts`` and ``src/health-diagnostic-rules/*.cts``
from gsd-core at pinned commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79
(MIT, Copyright (c) 2026 Open GSD).

``health_diagnostic.py`` imports this module and composes ``RULES``; this module
never imports ``health_diagnostic`` (the upstream split exists to avoid that cycle).

A rule is a dict ``{"code", "severity", "description", "repairable", "check"}``;
``check(snapshot)`` returns a list of Diagnostic dicts
``{"code", "severity", "message", "remedy": {"action", "risk", "args"}}``.

The ``snapshot`` is a dict with the upstream ``PlanningSnapshot`` field names
(``projectSections``, ``config``, ``phaseDirs``, ``roadmapDeclaredPhases``, ...), each
field a dict carrying ``value`` and (where upstream does) ``scope`` / ``exists`` /
``reason``. The snapshot builder (``planning-snapshot.cts``) is not ported; callers
supply the dict.

Deviations:
- ``PlanningSnapshot`` is a plain dict; there is no builder bound to the repo's
  ``planning.py`` / ``records.py`` readers (the repo stores config as ``config.yaml``
  and has no equivalent of the 30-field snapshot).
- Phase-id helpers (``phase-id.cts``, ``validate.cts``) are ported privately for the
  functions the rules call: extract/normalize/compare/match/sentinel/variants and the
  legacy plus ``bracket`` conventions. Custom phase naming
  (``phase_naming: custom``: ``customPhaseQuery`` / ``customDirectoryOwner`` /
  recorded-id indexes) is NOT ported; a snapshot whose ``directoryContext.phaseNaming``
  is ``custom`` is evaluated as the numeric convention.
- ``phaseStatusFromFacts`` / ``toDisplayLabel`` (``phase-status.cts``),
  ``normalizeStateStatus`` (``state-document.cts``), ``legacyStatusRepairTarget``
  (``verification.cts``), ``isCanonicalPlanningFile`` (``artifacts.cts``),
  ``toComparablePathKey`` (``shell-command-projection.cts``) and ``SCOPE``
  (``planning-scope.cts``) are inlined as private/public helpers here.
- ``VALID_PROFILES`` / ``VALID_PHASE_TYPES`` / ``VALID_TIERS`` are the literal values of
  upstream ``model-catalog.json``; ``PACKAGE_NAME`` is the upstream package identity.
  Rule messages keep upstream wording (``GSD``, ``gsd-*``, ``/gsd-...``) verbatim.
- W028 (install surface shadowing) needs ``install-shadow-report`` / ``runtime-slash``,
  which are not ported: its ``check`` returns ``[]`` until a renderer is registered with
  ``set_install_shadow_renderer(fn)`` where ``fn(cwd) -> (runtime, lines)``.
- A non-string value for ``phase_branch_template`` / ``milestone_branch_template`` yields
  no finding (upstream would throw a TypeError).
"""
from __future__ import annotations

import functools
import json
import math
import os
import re
import sys
from types import MappingProxyType

# --- Types leaf (health-diagnostic-types.cts) ------------------------------------

SEVERITY = MappingProxyType({"ERROR": "error", "WARNING": "warning", "INFO": "info"})

REMEDY_ACTION = MappingProxyType({
    "CREATE_CONFIG": "createConfig",
    "RESET_CONFIG": "resetConfig",
    "REGENERATE_STATE": "regenerateState",
    "ADD_NYQUIST_KEY": "addNyquistKey",
    "ADD_AI_INTEGRATION_PHASE_KEY": "addAiIntegrationPhaseKey",
    "BACKFILL_MILESTONES": "backfillMilestones",
    "REPAIR_VERIFICATION_STATUS": "repairVerificationStatus",
    "ADVISE": "advise",
})

REMEDY_RISK = MappingProxyType({"NONE": "none", "DESTRUCTIVE": "destructive"})

SCOPE = MappingProxyType({"COMPLETE": "complete", "TRUNCATED": "truncated", "UNSCOPED": "unscoped", "UNREADABLE": "unreadable"})

PACKAGE_NAME = "@opengsd/gsd-core"


def advise_remedy(command):
    """The shared ``{action: ADVISE, risk: NONE, args: {command}}`` remedy."""
    return {"action": REMEDY_ACTION["ADVISE"], "risk": REMEDY_RISK["NONE"], "args": {"command": command}}


def _diag(code, severity, message, remedy):
    return {"code": code, "severity": severity, "message": message, "remedy": remedy}


def _rule(code, severity, description, repairable, check):
    return {"code": code, "severity": severity, "description": description, "repairable": repairable, "check": check}


# --- JavaScript-semantics helpers --------------------------------------------------

_UNDEF = object()


def _truthy(value):
    """JavaScript truthiness: empty objects/arrays are truthy, NaN/0/''/null are not."""
    if value is _UNDEF or value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0 and not (isinstance(value, float) and math.isnan(value))
    if isinstance(value, str):
        return len(value) > 0
    return True


def _get(obj, key):
    """``obj[key]`` with JavaScript semantics: missing and non-object receivers give undefined."""
    return obj.get(key, _UNDEF) if isinstance(obj, dict) else _UNDEF


def _js_string(value):
    """Template-literal string conversion of a parsed-JSON value."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, list):
        return ",".join("" if v is None else _js_string(v) for v in value)
    if isinstance(value, dict):
        return "[object Object]"
    return str(value)


def _json(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _parse_int(text):
    """``parseInt(text, 10)``: leading integer or None for NaN."""
    match = re.match(r"\s*([+-]?\d+)", text, re.ASCII)
    return int(match.group(1)) if match else None


def _locale_key(text):
    """Approximation of ``localeCompare(b, undefined, {numeric: true})`` as a sort key."""
    parts = re.split(r"(\d+)", text)
    return [(0, int(p)) if p.isdigit() else (1, p.casefold(), p.swapcase()) for p in parts if p != ""]


def _locale_compare(a, b):
    """Approximation of ``String.prototype.localeCompare``."""
    ka, kb = (a.casefold(), a.swapcase()), (b.casefold(), b.swapcase())
    return (ka > kb) - (ka < kb)


# --- Model catalog (model-catalog.json) -------------------------------------------

VALID_PROFILES = ["quality", "balanced", "budget", "adaptive", "inherit"]
VALID_PHASE_TYPES = ("planning", "discuss", "research", "execution", "verification", "completion")
VALID_TIERS = ("opus", "sonnet", "haiku", "inherit")
VALID_BRANCHING_STRATEGIES = ["none", "phase", "milestone"]

# --- Phase identity helpers (phase-id.cts / validate.cts subset) ------------------

PHASE_NUMBER_TOKEN_SOURCE = r"\d+[A-Z]?(?:\.\d+)*"
_PHASE_CONTINUATION_SEGMENT_SOURCE = r"\d{2}(?!\d)"
_OPTIONAL_PROJECT_CODE_PREFIX_SOURCE = r"(?:[A-Z][A-Z0-9_]*-)?"
_BRACKET_PROJECT_CODE_SRC = r"[A-Z][A-Z0-9_]*"
_BRACKET_NUMERIC_SRC = r"(?:[1-9]\d{2,}|\d{2})"
_BRACKET_ID_SRC = _BRACKET_PROJECT_CODE_SRC + r"\." + _BRACKET_NUMERIC_SRC
_BRACKET_DIR_PREFIX_SRC = _BRACKET_ID_SRC + "-"
SENTINEL_RANGES = (0, 999)

_I = re.IGNORECASE | re.ASCII
_A = re.ASCII
_PROJECT_CODE_PREFIX_STRIP_RE = re.compile(r"^[A-Z][A-Z0-9_]*-(?=\d)", _A)
_PROJECT_CODE_PREFIX_STRIP_RE_I = re.compile(r"^[A-Z][A-Z0-9_]*-(?=\d)", _I)
_PROJECT_CODE_PREFIX_CAPTURE_RE_I = re.compile(r"^([A-Z][A-Z0-9_]*)-(\d.*)", _I)
_BRACKET_ID_PREFIX_RE = re.compile(r"^" + _BRACKET_PROJECT_CODE_SRC + r"\.(" + _BRACKET_NUMERIC_SRC + r")(?=-|$)", _A)
_BRACKET_DIR_TOKEN_RE = re.compile(r"^" + _BRACKET_DIR_PREFIX_SRC + r"(\d+(?:\.\d+)?)(?=-|$)", _I)
_BRACKET_QUALIFIED_KEY_RE = re.compile(
    r"^(" + _BRACKET_PROJECT_CODE_SRC + r")\.(" + _BRACKET_NUMERIC_SRC + r")-(\d+(?:\.\d+)?)(?=-|$)", _I)
_LEADING_DIGIT_RUN_RE = re.compile(r"^(\d+)(?:-|$)", _A)
_BARE_INTEGER_RE = re.compile(r"^\d+\Z", _A)
_PHASE_DIR_NAME_RE = re.compile(
    r"^" + _OPTIONAL_PROJECT_CODE_PREFIX_SOURCE + r"\d{2,}(?:-\d+)*(?:\.\d+)*-[\w-]+\Z", _I)
_BRACKET_PHASE_DIR_RE = re.compile(r"^(?:" + _BRACKET_DIR_PREFIX_SRC + r")\d+(?:\.\d+)?(?:-[\w-]+)?\Z", _I)


def fold_bracket_id(bracket_id):
    return str(bracket_id).upper()


def strip_project_code_prefix(value, case_insensitive=True):
    pattern = _PROJECT_CODE_PREFIX_STRIP_RE_I if case_insensitive else _PROJECT_CODE_PREFIX_STRIP_RE
    return pattern.sub("", str(value), count=1)


def normalize_phase_name(phase):
    text = str(phase)
    stripped = strip_project_code_prefix(text, False)
    milestone = re.match(r"^(\d+)((?:-\d+)+)([A-Z]?(?:\.\d+)*)\Z", stripped, _I)
    if milestone:
        major = milestone.group(1).rjust(2, "0")
        subs = [s.rjust(2, "0") for s in milestone.group(2)[1:].split("-")]
        return f"{major}-{'-'.join(subs)}{milestone.group(3) or ''}"
    match = re.match(r"^(\d+)([A-Z])?((?:\.\d+)*)", stripped, _I)
    if match:
        return match.group(1).rjust(2, "0") + (match.group(2) or "") + (match.group(3) or "")
    return text


def get_milestone_from_phase_id(phase_id, convention=None):
    if convention == "bracket":
        match = _BRACKET_ID_PREFIX_RE.match(fold_bracket_id(phase_id))
        if not match:
            return None
        mm = int(match.group(1))
        return None if mm in SENTINEL_RANGES else f"v{mm}.0"
    stripped = strip_project_code_prefix(phase_id)
    match = re.match(r"^0*(\d+)-\d", stripped, _A)
    if not match:
        return None
    major = int(match.group(1))
    return None if major in (0, 999) else f"v{major}.0"


def is_sentinel_phase_id(phase_id, convention=None):
    text = str(phase_id)
    if convention == "bracket":
        bracket = _BRACKET_ID_PREFIX_RE.match(fold_bracket_id(text))
        if bracket:
            return int(bracket.group(1)) in SENTINEL_RANGES
        bare = re.match(r"^0*(\d+)", strip_project_code_prefix(text), _A)
        return bare is not None and int(bare.group(1)) == 999
    legacy = re.match(r"^0*(\d+)", strip_project_code_prefix(text), _A)
    if not legacy:
        return False
    return int(legacy.group(1)) in SENTINEL_RANGES


def is_sentinel_phase_dir(dir_name):
    bracket_dir = re.match(r"^[A-Z][A-Z0-9_]*\.(\d+)-\d", dir_name, _A)
    if bracket_dir:
        return int(bracket_dir.group(1)) in SENTINEL_RANGES
    return is_sentinel_phase_id(dir_name)


def compare_phase_num(a, b, context=None):
    """Numeric-convention ``comparePhaseNum`` (custom-naming ordering is not ported)."""
    sa, sb = strip_project_code_prefix(a), strip_project_code_prefix(b)
    ms_re = r"^(\d+)((?:-\d+)+)([A-Z]?(?:\.\d+)*)\Z"
    milestone_a, milestone_b = re.match(ms_re, sa, _I), re.match(ms_re, sb, _I)
    if milestone_a and milestone_b:
        segs_a = [int(milestone_a.group(1))] + [int(s) for s in milestone_a.group(2)[1:].split("-")]
        segs_b = [int(milestone_b.group(1))] + [int(s) for s in milestone_b.group(2)[1:].split("-")]
        for i in range(max(len(segs_a), len(segs_b))):
            av = segs_a[i] if i < len(segs_a) else 0
            bv = segs_b[i] if i < len(segs_b) else 0
            if av != bv:
                return av - bv
        suf_a, suf_b = milestone_a.group(3) or "", milestone_b.group(3) or ""
        if suf_a != suf_b:
            return -1 if suf_a < suf_b else 1
        return 0
    if milestone_a or milestone_b:
        return _locale_compare(str(a), str(b))
    num_re = r"^(\d+)([A-Z])?((?:\.\d+)*)"
    pa, pb = re.match(num_re, sa, _I), re.match(num_re, sb, _I)
    if not pa or not pb:
        return _locale_compare(str(a), str(b))
    diff = int(pa.group(1)) - int(pb.group(1))
    if diff != 0:
        return diff
    la, lb = (pa.group(2) or "").upper(), (pb.group(2) or "").upper()
    if la != lb:
        if not la:
            return -1
        if not lb:
            return 1
        return -1 if la < lb else 1
    a_dec = [int(p) for p in pa.group(3)[1:].split(".")] if pa.group(3) else []
    b_dec = [int(p) for p in pb.group(3)[1:].split(".")] if pb.group(3) else []
    if not a_dec and b_dec:
        return -1
    if not b_dec and a_dec:
        return 1
    for i in range(max(len(a_dec), len(b_dec))):
        av = a_dec[i] if i < len(a_dec) else 0
        bv = b_dec[i] if i < len(b_dec) else 0
        if av != bv:
            return av - bv
    return 0


def _derive_phase_token_segments(dir_name):
    code_match = _PROJECT_CODE_PREFIX_CAPTURE_RE_I.match(dir_name)
    prefix, rest = "", dir_name
    if code_match:
        prefix, rest = code_match.group(1) + "-", code_match.group(2)
    token_segments, first_letter_prefixed = [], False
    for i, seg in enumerate(rest.split("-")):
        if i == 0:
            if re.match(r"^\d", seg, _A):
                token_segments.append(seg)
            elif re.match(r"^[A-Za-z]{1,3}\d", seg, _A):
                token_segments.append(seg)
                first_letter_prefixed = True
            else:
                break
        elif (first_letter_prefixed and re.match(r"^\d", seg, _A)) or \
                (not first_letter_prefixed and re.match(r"^" + _PHASE_CONTINUATION_SEGMENT_SOURCE, seg, _A)):
            token_segments.append(seg)
        else:
            break
    return prefix, token_segments, first_letter_prefixed


def extract_phase_token(dir_name, convention=None):
    if convention == "bracket":
        bracket_dir = _BRACKET_DIR_TOKEN_RE.match(dir_name)
        if bracket_dir:
            return bracket_dir.group(1)
    prefix, token_segments, first_letter_prefixed = _derive_phase_token_segments(dir_name)
    if not token_segments:
        return dir_name
    if not first_letter_prefixed and len(token_segments) > 1 and re.fullmatch(r"\d{2}[a-z][a-z0-9]*", token_segments[-1], _A):
        token_segments.pop()
    return prefix + "-".join(token_segments)


def bracket_qualified_key(text, convention=None):
    if convention != "bracket":
        return None
    match = _BRACKET_QUALIFIED_KEY_RE.match(str(text))
    if not match:
        return None
    milestone = int(match.group(2))
    phase = [int(n) for n in match.group(3).split(".")]
    return f"{fold_bracket_id(match.group(1))}.{milestone}-{'.'.join(str(n) for n in phase)}"


def phase_token_matches(dir_name, normalized, convention=None):
    if convention == "bracket":
        q_key = bracket_qualified_key(normalized, convention)
        if q_key:
            return bracket_qualified_key(dir_name, convention) == q_key
        if extract_phase_token(dir_name, convention).upper() == normalized.upper():
            return True
    if extract_phase_token(dir_name).upper() == normalized.upper():
        return True
    stripped = strip_project_code_prefix(dir_name)
    if stripped != dir_name and extract_phase_token(stripped).upper() == normalized.upper():
        return True
    return False


def phase_directory_context(config, roadmap="", known_ids=None):
    naming = config.get("phase_naming")
    return {"phaseNaming": naming.lower() if isinstance(naming, str) else naming,
            "projectCode": config.get("project_code"), "roadmap": roadmap, "knownIds": list(known_ids or [])}


def phase_lookup_query(query, context):
    """Custom naming (literal ids) is not ported; every query is normalized."""
    return normalize_phase_name(query)


def _unpad(digits):
    return re.sub(r"^0+(?=\d)", "", digits)


def match_phase_dirs(dirs, query, convention=None, bracket_context=None, context=None):
    """``matchPhaseDirs`` for the numeric and bracket conventions."""
    normalized = query if convention == "bracket" else normalize_phase_name(query)
    candidates = dirs
    if convention == "bracket" and bracket_context and not bracket_qualified_key(normalized, convention):
        qualified = f"{bracket_context['project']}.{bracket_context['milestone']}-{normalized}"
        exact = [d for d in dirs if phase_token_matches(d, qualified, convention)]
        if exact:
            return {"matches": exact, "usedBareFallback": False}
        candidates = [d for d in dirs if bracket_qualified_key(d, convention) is None]
    primary = [d for d in candidates if phase_token_matches(d, normalized, convention)]
    if primary:
        return {"matches": primary, "usedBareFallback": False}
    if query != normalized and "-" in query:
        literal = [d for d in dirs if phase_token_matches(d, query, convention)]
        if literal:
            return {"matches": literal, "usedBareFallback": False}
    bare = str(normalized)
    if not _BARE_INTEGER_RE.match(bare):
        return {"matches": primary, "usedBareFallback": False}
    want = _unpad(bare)
    fallback = []
    for d in candidates:
        match = _LEADING_DIGIT_RUN_RE.match(strip_project_code_prefix(d))
        if match and _unpad(match.group(1)) == want:
            fallback.append(d)
    return {"matches": fallback, "usedBareFallback": bool(fallback)}


def phase_key_from_token(token, context=None):
    stripped = "-".join(re.sub(r"^0+(?=\d)", "", segment) for segment in str(token).split("-"))
    return normalize_phase_name(stripped).upper()


def phase_key_from_dir(dir_name, convention=None, context=None):
    return phase_key_from_token(extract_phase_token(dir_name, convention), context)


def is_phase_dir_name(dir_name, convention=None):
    if not isinstance(dir_name, str):
        raise TypeError(f"isPhaseDirName: directory name must be a string, received {type(dir_name).__name__}")
    if convention == "bracket" and _BRACKET_PHASE_DIR_RE.match(dir_name):
        return True
    return bool(_PHASE_DIR_NAME_RE.match(dir_name))


def phase_variants(phase):
    variants = {phase}
    dot = phase.find(".")
    head = phase if dot == -1 else phase[:dot]
    tail = "" if dot == -1 else phase[dot:]
    milestone_head = re.match(r"^(\d+)((?:-\d+)+)([A-Z]?)\Z", head, _I)
    if milestone_head:
        major, subs, letter = milestone_head.group(1), milestone_head.group(2), milestone_head.group(3) or ""
        padded_major = major.rjust(2, "0")
        unpadded_major = str(int(major))
        parts = subs[1:].split("-")
        padded_subs = "-".join(s.rjust(2, "0") for s in parts)
        unpadded_subs = "-".join(str(int(s)) for s in parts)
        variants.add(f"{padded_major}-{padded_subs}{letter}{tail}")
        variants.add(f"{unpadded_major}-{unpadded_subs}{letter}{tail}")
        variants.add(f"{unpadded_major}-{padded_subs}{letter}{tail}")
        variants.add(f"{padded_major}-{unpadded_subs}{letter}{tail}")
        return variants
    head_match = re.match(r"^(\d+)([A-Z]?)\Z", head, _I)
    if not head_match:
        return variants
    numeric_head, letter = head_match.group(1), head_match.group(2) or ""
    variants.add(f"{int(numeric_head)}{letter}{tail}")
    variants.add(f"{numeric_head.rjust(2, '0')}{letter}{tail}")
    return variants


# --- Phase status ladder (phase-status.cts subset) ---------------------------------

_VERIFICATION_STATUS_VALUES = ("passed", "gaps_found", "human_needed", "stale", "missing", "unparseable", "phase_dir_not_found")
_DISPLAY_LABEL = {"not_started": "Not Started", "planned": "Planned", "in_progress": "In Progress",
                  "executed": "Executed", "needs_review": "Needs Review", "complete": "Complete"}


def phase_status_from_facts(facts):
    if not isinstance(facts, dict):
        raise TypeError("phaseStatusFromFacts: facts object required")
    for name in ("planCount", "summaryCount"):
        value = facts.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise TypeError(f"phaseStatusFromFacts: {name} must be a non-negative integer, got {_json(value)}")
    if not isinstance(facts.get("complete"), bool):
        raise TypeError(f"phaseStatusFromFacts: complete must be a boolean, got {_json(facts.get('complete'))}")
    verification = facts.get("verificationStatus")
    if verification is not None and verification not in _VERIFICATION_STATUS_VALUES:
        raise TypeError(f"phaseStatusFromFacts: verificationStatus: {_json(verification)} is not a VerificationStatus "
                        f"(expected one of {', '.join(_VERIFICATION_STATUS_VALUES)})")
    if facts["complete"]:
        return "complete"
    if facts["planCount"] == 0:
        return "not_started"
    if facts["summaryCount"] == 0:
        return "planned"
    if facts["summaryCount"] < facts["planCount"]:
        return "in_progress"
    if verification == "human_needed":
        return "needs_review"
    return "executed"


def to_display_label(status, pending_word="Not Started"):
    if status not in _DISPLAY_LABEL:
        raise TypeError(f"toDisplayLabel: {_json(status)} is not a PHASE_STATUS value")
    if pending_word not in ("Pending", "Not Started"):
        raise TypeError(f"toDisplayLabel: pendingWord must be 'Pending' or 'Not Started', got {_json(pending_word)}")
    return pending_word if status == "not_started" else _DISPLAY_LABEL[status]


# --- State status vocabulary (state-document.cts subset) ---------------------------

STATUS_EXACT_TOKENS = MappingProxyType({
    "paused": "paused", "stopped": "paused", "executing": "executing", "in progress": "executing",
    "ready to execute": "executing", "planning": "planning", "ready to plan": "planning",
    "planning complete": "planning", "discussing": "discussing", "verifying": "verifying",
    "completed": "completed", "done": "completed", "complete": "completed", "phase complete": "completed",
    "phase complete — ready for verification": "verifying", "all phases complete": "completed",
    "milestone complete": "completed", "unknown": "unknown",
})
STATUS_ANCHORED_PATTERNS = (
    (re.compile(r"^executing phase\s+\S+\Z"), "executing"),
    (re.compile(r"^planning phase\s+\S+\Z"), "planning"),
    (re.compile(r"^verifying phase\s+\S+\Z"), "verifying"),
    (re.compile(r"^phase\s+\S+\s+complete\Z"), "completed"),
    (re.compile(r"^\S+\s+milestone complete\Z"), "completed"),
    (re.compile(r"^complete\s*[✓✔✅☑]?\Z"), "completed"),
)


def normalize_state_status(status, paused_at=None):
    if _truthy(paused_at):
        return "paused"
    if not status:
        return "unknown"
    key = re.sub(r"\s+", " ", status.strip().lower())
    exact = STATUS_EXACT_TOKENS.get(key)
    if exact:
        return exact
    for pattern, token in STATUS_ANCHORED_PATTERNS:
        if pattern.search(key):
            return token
    return status


# --- Canonical planning files (artifacts.cts) --------------------------------------

CANONICAL_EXACT = frozenset([
    "PROJECT.md", "ROADMAP.md", "STATE.md", "REQUIREMENTS.md", "MILESTONES.md", "BACKLOG.md", "LEARNINGS.md",
    "THREADS.md", "config.json", "CLAUDE.md", "RETROSPECTIVE.md", "WINDOWS.md", "STATE-ARCHIVE.md",
    "milestone.lock", "state.json", "skill-manifest.json", "PATTERNS.md",
])
CANONICAL_PATTERNS = (
    re.compile(r"^v\d+\.\d+(?:\.\d+)?-MILESTONE-AUDIT\.md\Z", _I),
    re.compile(r"^v\d+\.\d+(?:\.\d+)?-.*\.md\Z", _I),
)


def is_canonical_planning_file(filename):
    return filename in CANONICAL_EXACT or any(p.match(filename) for p in CANONICAL_PATTERNS)


# --- Legacy verification status repairs (verification.cts) -------------------------

LEGACY_STATUS_REPAIRS = MappingProxyType({"pass_with_caveats": "passed"})


def legacy_status_repair_target(raw):
    return LEGACY_STATUS_REPAIRS.get(raw) if isinstance(raw, str) else None


# --- Path comparison (shell-command-projection.cts) --------------------------------

def to_comparable_path_key(path, platform=None):
    platform = platform or sys.platform
    normalized = os.path.abspath(path).replace("\\", "/")
    normalized = re.sub(r"/+$", "", normalized)
    return normalized.lower() if platform == "win32" else normalized


# --- Rule groups ---------------------------------------------------------------------
# Each group is the upstream ``RULES`` array of one ``health-diagnostic-rules/*.cts`` file;
# ``health_diagnostic.py`` concatenates them in upstream order.

RULE_GROUPS = {}
