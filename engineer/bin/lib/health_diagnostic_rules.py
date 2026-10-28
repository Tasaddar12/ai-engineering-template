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

_W = SEVERITY["WARNING"]
_E = SEVERITY["ERROR"]
_INFO = SEVERITY["INFO"]
_NONE = REMEDY_RISK["NONE"]
_DESTRUCTIVE = REMEDY_RISK["DESTRUCTIVE"]


def _remedy(action, risk, args=None):
    return {"action": REMEDY_ACTION[action], "risk": risk, "args": args or {}}


# --- root-existence: E002, E003, E004, W001 ----------------------------------------------

def _check_e002(snapshot):
    if snapshot["projectSections"]["exists"]:
        return []
    return [_diag("E002", _E, "PROJECT.md not found", advise_remedy("/gsd-new-project"))]


def _check_e003(snapshot):
    # Known ambiguity (upstream): UNREADABLE covers both an absent and an unreadable ROADMAP.md.
    if snapshot["milestone"]["scope"] != SCOPE["UNREADABLE"]:
        return []
    return [_diag("E003", _E, "ROADMAP.md not found", advise_remedy("/gsd-new-milestone"))]


def _check_e004(snapshot):
    # Known gap (upstream): UNREADABLE covers both an absent and an unreadable STATE.md.
    if snapshot["currentPhaseLabel"]["scope"] != SCOPE["UNREADABLE"]:
        return []
    return [_diag("E004", _E, "STATE.md not found", _remedy("REGENERATE_STATE", _DESTRUCTIVE))]


REQUIRED_SECTIONS = ["## What This Is", "## Core Value", "## Requirements"]


def _check_w001(snapshot):
    value = snapshot["projectSections"]["value"]
    if value is None:
        return []
    diagnostics = []
    for required in REQUIRED_SECTIONS:
        heading = re.sub(r"^##\s+", "", required)
        if heading not in value:
            diagnostics.append(_diag("W001", _W, f"PROJECT.md missing section: {required}", advise_remedy("Add section manually")))
    return diagnostics


RULE_GROUPS["root-existence"] = [
    _rule("E002", _E, "PROJECT.md not found", False, _check_e002),
    _rule("E003", _E, "ROADMAP.md not found", False, _check_e003),
    _rule("E004", _E, "STATE.md not found", False, _check_e004),
    _rule("W001", _W, "PROJECT.md missing required section", False, _check_w001),
]


# --- config-validation: W003, E005, W004, W008, W016, W012, W013, W014, W015, W022, W029 -----

def _check_w003(snapshot):
    if snapshot["config"]["exists"]:
        return []
    return [_diag("W003", _W, "config.json not found", _remedy("CREATE_CONFIG", _NONE))]


def _check_e005(snapshot):
    config = snapshot["config"]
    if not config["exists"] or config["value"] is not None:
        return []
    return [_diag("E005", _E, "config.json: JSON parse error", _remedy("RESET_CONFIG", _DESTRUCTIVE))]


def _check_w004(snapshot):
    value = snapshot["config"]["value"]
    if not value:
        return []
    profile = _get(value, "model_profile")
    if _truthy(profile) and profile not in VALID_PROFILES:
        return [_diag("W004", _W, f'config.json: invalid model_profile "{_js_string(profile)}"',
                      advise_remedy(f"Valid values: {', '.join(VALID_PROFILES)}"))]
    return []


def _workflow_of(snapshot):
    value = snapshot["config"]["value"]
    return _get(value, "workflow") if value else _UNDEF


def _check_w008(snapshot):
    workflow = _workflow_of(snapshot)
    if _truthy(workflow) and _get(workflow, "nyquist_validation") is _UNDEF:
        return [_diag("W008", _W, "config.json: workflow.nyquist_validation absent (defaults to enabled but agents may skip)",
                      _remedy("ADD_NYQUIST_KEY", _NONE))]
    return []


def _check_w016(snapshot):
    workflow = _workflow_of(snapshot)
    if _truthy(workflow) and _get(workflow, "ai_integration_phase") is _UNDEF:
        return [_diag("W016", _W,
                      "config.json: workflow.ai_integration_phase absent (defaults to enabled — run /gsd-ai-integration-phase before planning AI system phases)",
                      _remedy("ADD_AI_INTEGRATION_PHASE_KEY", _NONE))]
    return []


def _check_w012(snapshot):
    value = snapshot["config"]["value"]
    if not value:
        return []
    strategy = _get(value, "branching_strategy")
    if _truthy(strategy) and strategy not in VALID_BRANCHING_STRATEGIES:
        return [_diag("W012", _W, f'config.json: invalid branching_strategy "{_js_string(strategy)}"',
                      advise_remedy(f"Valid values: {', '.join(VALID_BRANCHING_STRATEGIES)}"))]
    return []


def _check_w013(snapshot):
    value = snapshot["config"]["value"]
    if not value:
        return []
    cw = _get(value, "context_window")
    if cw is _UNDEF:
        return []
    is_number = isinstance(cw, (int, float)) and not isinstance(cw, bool)
    if not is_number or cw <= 0 or (isinstance(cw, float) and not cw.is_integer()):
        return [_diag("W013", _W, f'config.json: context_window should be a positive integer, got "{_js_string(cw)}"',
                      advise_remedy("Set to 200000 (default) or 1000000 (for 1M models)"))]
    return []


def _template_check(snapshot, key, placeholder, code, message, fix):
    value = snapshot["config"]["value"]
    if not value:
        return []
    template = _get(value, key)
    if _truthy(template) and isinstance(template, str) and placeholder not in template:
        return [_diag(code, _W, message, advise_remedy(fix))]
    return []


def _check_w014(snapshot):
    return _template_check(snapshot, "phase_branch_template", "{phase}", "W014",
                           "config.json: phase_branch_template missing {phase} placeholder",
                           "Template must include {phase} for phase number substitution")


def _check_w015(snapshot):
    return _template_check(snapshot, "milestone_branch_template", "{milestone}", "W015",
                           "config.json: milestone_branch_template missing {milestone} placeholder",
                           "Template must include {milestone} for version substitution")


def _check_w022(snapshot):
    value = snapshot["config"]["value"]
    if not value:
        return []
    diagnostics = []
    models = _get(value, "models")
    if isinstance(models, dict):
        for phase_type, tier in models.items():
            if phase_type not in VALID_PHASE_TYPES:
                diagnostics.append(_diag("W022", _W, f'config.json: models has an unknown phase type "{phase_type}" which will be ignored',
                                         advise_remedy(f"Valid phase types: {', '.join(VALID_PHASE_TYPES)}")))
            elif not isinstance(tier, str) or tier not in VALID_TIERS:
                diagnostics.append(_diag("W022", _W,
                                         f"config.json: models.{phase_type} has an invalid tier value {_json(tier)} which will be ignored",
                                         advise_remedy(f"Valid tiers: {', '.join(VALID_TIERS)}")))
    elif models is not _UNDEF and models is not None:
        diagnostics.append(_diag("W022", _W,
                                 f"config.json: models is set to {_json(models)}, but must be an object mapping phase types to tiers — this value will be ignored",
                                 advise_remedy('Set models to an object like {"planning": "sonnet"}, or remove the key to use profile defaults')))
    return diagnostics


def _check_w029(snapshot):
    field = snapshot.get("planningTracked")
    if not field or field.get("scope") != SCOPE["COMPLETE"]:
        return []
    if not field["value"].get("ignored") or not field["value"].get("tracked"):
        return []
    return [_diag("W029", _W,
                  ".planning/ matches a gitignore rule but is still tracked by git — .gitignore has no effect on already-tracked files, so staging keeps picking them up",
                  advise_remedy("Run `git rm -r --cached .planning/` to untrack it (the ignore rule then takes effect); this does not delete the files on disk"))]


RULE_GROUPS["config-validation"] = [
    _rule("W003", _W, "config.json not found", True, _check_w003),
    _rule("E005", _E, "config.json parse error", False, _check_e005),
    _rule("W004", _W, "config.json invalid field value", False, _check_w004),
    _rule("W008", _W, "config.json: workflow.nyquist_validation absent (defaults to enabled but agents may skip)", True, _check_w008),
    _rule("W016", _W, "config.json: workflow.ai_integration_phase absent (defaults to enabled but agents may skip AI-integration-phase planning)", True, _check_w016),
    _rule("W012", _W, "config.json invalid branching_strategy value", False, _check_w012),
    _rule("W013", _W, "config.json context_window not a positive integer", False, _check_w013),
    _rule("W014", _W, "config.json phase_branch_template missing {phase} placeholder", False, _check_w014),
    _rule("W015", _W, "config.json milestone_branch_template missing {milestone} placeholder", False, _check_w015),
    _rule("W022", _W, "config.json models entry malformed (unknown phase type, invalid tier, or non-object value)", False, _check_w022),
    _rule("W029", _W, ".planning/ matches a gitignore rule but is still tracked by git (gitignore has no effect on already-tracked files)", False, _check_w029),
]


# --- agent-install: W010 --------------------------------------------------------------------

def _check_agent_install(snapshot):
    field = snapshot["agentInstall"]
    status, scope = field["value"], field["scope"]
    if scope == SCOPE["UNREADABLE"]:
        return []
    if status["agents_installed"]:
        return []
    missing, incomplete = status["missing_agents"], status["incomplete_agents"]
    if len(status["installed_agents"]) == 0:
        return [_diag("W010", _W, f'No GSD agents found in {status["agents_dir"]} — Task(subagent_type="gsd-*") will fall back to general-purpose',
                      advise_remedy(f"Run the GSD installer: npx {PACKAGE_NAME}@latest"))]
    if len(incomplete) > 0 and len(missing) == 0:
        return [_diag("W010", _W,
                      f"Incomplete agent installs (missing generated file): {', '.join(incomplete)} — affected workflows may fall back to general-purpose",
                      advise_remedy(f"Re-run the GSD installer to complete the install: npx {PACKAGE_NAME}@latest"))]
    if len(incomplete) > 0:
        return [_diag("W010", _W,
                      f"Missing {len(missing)} GSD agents: {', '.join(missing)}; incomplete agent installs (missing generated file): {', '.join(incomplete)} — affected workflows will fall back to general-purpose",
                      advise_remedy(f"Run the GSD installer: npx {PACKAGE_NAME}@latest"))]
    return [_diag("W010", _W, f"Missing {len(missing)} GSD agents: {', '.join(missing)} — affected workflows will fall back to general-purpose",
                  advise_remedy(f"Run the GSD installer: npx {PACKAGE_NAME}@latest"))]


RULE_GROUPS["agent-install"] = [
    _rule("W010", _W, "GSD agent installation missing or incomplete", False, _check_agent_install),
]


# --- milestone-archive-hygiene: W018, W019 ----------------------------------------------------

def _check_w018(snapshot):
    status = snapshot["milestoneArchiveStatus"]["value"]
    archived, documented = status["archivedVersions"], set(status["documentedVersions"])
    if len(archived) == 0:
        return []
    missing = [version for version in archived if version not in documented]
    if len(missing) == 0:
        return []
    return [_diag("W018", _W, f"MILESTONES.md missing {len(missing)} archived milestone(s): {', '.join(missing)}",
                  _remedy("BACKFILL_MILESTONES", _NONE))]


def _check_w019(snapshot):
    diagnostics = []
    for filename in snapshot["planningRootFiles"]["value"]:
        if not filename.endswith(".md") or is_canonical_planning_file(filename):
            continue
        diagnostics.append(_diag("W019", _W, f"Unrecognized .planning/ file: {filename} — not a canonical GSD artifact",
                                 advise_remedy("Move to .planning/milestones/ archive subdir or delete if stale. See templates/README.md for the canonical artifact list.")))
    return diagnostics


RULE_GROUPS["milestone-archive-hygiene"] = [
    _rule("W018", _W, "MILESTONES.md missing entry for archived milestone snapshot", True, _check_w018),
    _rule("W019", _W, "Unrecognized .planning/ root file — not a canonical GSD artifact", False, _check_w019),
]


# --- worktree-health: W020, W017, W027 --------------------------------------------------------

def _check_w020(snapshot):
    diagnostics = []
    health = snapshot["worktreeHealth"]
    degraded = health.get("scope") == SCOPE["UNREADABLE"]
    reason = health.get("reason")
    if degraded and reason == "git_timed_out":
        diagnostics.append(_diag("W020", _W,
                                 "Worktree health check degraded: git worktree list timed out after 10s — orphan/stale worktrees could not be inspected",
                                 advise_remedy("Run: git worktree list --porcelain to diagnose; check for .git/index.lock or a hung git process")))
    if degraded and reason == "git_list_failed":
        diagnostics.append(_diag("W020", _W,
                                 "Worktree health check degraded: git worktree list failed — orphan/stale worktrees could not be inspected",
                                 advise_remedy("Run: git worktree list --porcelain to diagnose; check git repository state and permissions")))
    for finding in health["value"]:
        if finding.get("kind") != "unverified":
            continue
        diagnostics.append(_diag("W020", _W,
                                 f"Worktree health check degraded: could not stat {finding['path']} — presence/staleness could not be verified",
                                 advise_remedy("Check filesystem permissions on the worktree path, or investigate why statSync failed for it")))
    return diagnostics


def _check_w017(snapshot):
    return [_diag("W017", _W, f"Orphan git worktree: {finding['path']} (path no longer exists on disk)", advise_remedy("git worktree prune"))
            for finding in snapshot["worktreeHealth"]["value"] if finding.get("kind") == "orphan"]


def is_active_worktree_path(active_cwd, worktree_path, platform=None):
    """True when ``active_cwd`` equals or is nested under ``worktree_path`` (case-folded on win32 only)."""
    active = to_comparable_path_key(active_cwd, platform)
    worktree = to_comparable_path_key(worktree_path, platform)
    return active == worktree or active.startswith(worktree + "/")


def _check_w027(snapshot):
    diagnostics = []
    active_cwd = snapshot["cwd"]
    for finding in snapshot["worktreeHealth"]["value"]:
        if finding.get("kind") != "stale" or is_active_worktree_path(active_cwd, finding["path"]):
            continue
        path = finding["path"]
        diagnostics.append(_diag(
            "W027", _W,
            f"Stale git worktree: {path} (last modified {_js_string(finding['ageMinutes'])} minutes ago). Inspect uncommitted work first: "
            f"git -C {path} status --porcelain; if clean run: git worktree remove {path}; only add --force to discard changes",
            advise_remedy("git -C <path> status --porcelain; if clean: git worktree remove <path>; add --force only to discard changes")))
    return diagnostics


RULE_GROUPS["worktree-health"] = [
    _rule("W020", _W, "Worktree health scan degraded — git worktree list timed out, failed, or a finding could not be verified", False, _check_w020),
    _rule("W017", _W, "Orphan git worktree (path no longer exists on disk)", False, _check_w017),
    _rule("W027", _W, "Stale git worktree (not modified in a long time)", False, _check_w027),
]


# --- consistency (validate.consistency only): C001-C004 -----------------------------------------

def _check_c001(snapshot):
    config = snapshot["config"]["value"]
    if _get(config, "phase_naming") == "custom":
        return []
    numbers = []
    for name in snapshot["allPhaseDirNames"]["value"]:
        if "." in name or is_sentinel_phase_dir(name):
            continue
        number = _parse_int(name)
        if number is not None:
            numbers.append(number)
    numbers.sort()
    return [_diag("C001", _W, f"Gap in phase numbering: {numbers[i - 1]} → {numbers[i]}",
                  advise_remedy("Create the missing phase directory or renumber to close the gap"))
            for i in range(1, len(numbers)) if numbers[i] != numbers[i - 1] + 1]


def _check_c002(snapshot):
    diagnostics = []
    for entry in snapshot["perPhasePlanNumbering"]["value"]:
        nums = entry["planNums"]
        for i in range(1, len(nums)):
            if nums[i] != nums[i - 1] + 1:
                diagnostics.append(_diag("C002", _W, f"Gap in plan numbering in {entry['phaseDir']}: plan {nums[i - 1]} → {nums[i]}",
                                         advise_remedy("Create the missing plan or renumber to close the gap")))
    return diagnostics


def _check_c003(snapshot):
    return [_diag("C003", _W, f"Summary {entry['orphanSummary']} in {entry['phaseDir']} has no matching PLAN.md",
                  advise_remedy("Create the matching PLAN.md or remove the orphan summary"))
            for entry in snapshot["perPhaseOrphanSummaries"]["value"]]


def _check_c004(snapshot):
    return [_diag("C004", _W, f"{entry['phaseDir']}/{entry['plan']}: missing 'wave' in frontmatter",
                  advise_remedy("Add a 'wave' key to the plan's frontmatter"))
            for entry in snapshot["perPhaseWaveMissingPlans"]["value"]]


RULE_GROUPS["consistency"] = [
    _rule("C001", _W, "Gap in disk phase numbering (integer sequence)", False, _check_c001),
    _rule("C002", _W, "Gap in plan numbering within a phase", False, _check_c002),
    _rule("C003", _W, "Orphan SUMMARY with no matching live PLAN", False, _check_c003),
    _rule("C004", _W, "PLAN missing 'wave' in frontmatter", False, _check_c004),
]


# --- install-surface-shadowing: W028 ------------------------------------------------------------

_INSTALL_SHADOW_RENDERER = None


def set_install_shadow_renderer(renderer):
    """Register ``renderer(cwd) -> (runtime, lines)`` (``None`` unregisters); W028 is inert without one."""
    global _INSTALL_SHADOW_RENDERER
    _INSTALL_SHADOW_RENDERER = renderer


def _check_install_surface_shadowing(snapshot):
    if _INSTALL_SHADOW_RENDERER is None:
        return []
    try:
        runtime, lines = _INSTALL_SHADOW_RENDERER(snapshot["cwd"])
    except Exception:  # noqa: BLE001 - advisory rule: never break the health run
        return []
    if len(lines) == 0:
        return []
    return [_diag("W028", _W, " ".join(lines), advise_remedy(f"Review install scopes for {runtime}: npx {PACKAGE_NAME}@latest"))]


RULE_GROUPS["install-surface-shadowing"] = [
    _rule("W028", _W, "A GSD-owned install scope shadows another on this machine", False, _check_install_surface_shadowing),
]


def _directory_context(snapshot, known_ids):
    context = snapshot.get("directoryContext")
    if context is not None:
        return context
    return phase_directory_context(snapshot["config"]["value"] or {}, "", known_ids)


# --- state-consistency: W024, W002, W011, W021, W026 ----------------------------------------------

def _check_w024(snapshot):
    # Deliberately inert upstream: no snapshot field backs the git-log freshness probe.
    return []


def _build_valid_phase_set(snapshot):
    valid = set()
    for name in snapshot["phaseDirs"]["value"]:
        token = extract_phase_token(name, snapshot.get("phaseIdConvention"))
        if token:
            valid.add(token)
    for entry in snapshot["roadmapDeclaredPhases"]["value"]:
        valid.add(entry["phaseId"])
    for token in snapshot["archivedPhaseTokens"]["value"]:
        valid.add(token)
    return valid


def _split_phase_token(token):
    dot = token.find(".")
    return (token, "") if dot == -1 else (token[:dot], token[dot:])


def _pad_phase_head(head, tail):
    return head.rjust(2, "0") + tail if re.fullmatch(r"\d+", head, _A) else None


def _normalize_phase_token_set(valid):
    normalized = set()
    for token in valid:
        normalized.add(token)
        head, tail = _split_phase_token(token)
        padded = _pad_phase_head(head, tail)
        if padded is not None:
            normalized.add(padded)
    return normalized


def _check_w002(snapshot):
    valid = _build_valid_phase_set(snapshot)
    if len(valid) == 0:
        return []
    normalized_valid = _normalize_phase_token_set(valid)
    sorted_valid = sorted(valid, key=_locale_key)
    scope_clause = f" in workstream {snapshot['workstream']}" if snapshot.get("workstream") else ""
    diagnostics = []
    for ref in snapshot["statePhaseTokens"]["value"]:
        head, tail = _split_phase_token(ref)
        padded = _pad_phase_head(head, tail)
        padded = ref if padded is None else padded
        if ref in normalized_valid or padded in normalized_valid:
            continue
        diagnostics.append(_diag(
            "W002", _W,
            f"STATE.md references phase {ref}, but only phases {', '.join(sorted_valid)} are declared{scope_clause}",
            advise_remedy("Review STATE.md manually before changing it; /gsd-health --repair will not overwrite an existing STATE.md for phase mismatches")))
    return diagnostics


def _current_phase_id_from_label(label):
    if not label:
        return None
    match = re.match(r"^0*(" + PHASE_NUMBER_TOKEN_SOURCE + r")", label, _A)
    return match.group(1) if match else None


def _check_w011(snapshot):
    phase_id = _current_phase_id_from_label(snapshot["currentPhaseLabel"]["value"])
    if phase_id is None:
        return []
    if snapshot["roadmapPhaseCheckboxes"]["value"].get(phase_id) is not True:
        return []
    status = (snapshot["stateStatus"]["value"] or "").strip()
    if normalize_state_status(status, None) == "completed":
        return []
    return [_diag("W011", _W,
                  f"STATE.md says current phase is {phase_id} (status: {status.lower() or 'unknown'}) but ROADMAP.md shows it as [x] complete — state files may be out of sync",
                  advise_remedy("Run /gsd-progress to re-derive current position, or manually update STATE.md"))]


def _check_milestone_prefix_w021(snapshot):
    diagnostics = []
    for entry in snapshot["roadmapDeclaredPhases"]["value"]:
        if entry.get("milestone") is None:
            continue
        expected = get_milestone_from_phase_id(entry["phaseId"])
        if expected is None or expected == entry["milestone"]:
            continue
        diagnostics.append(_diag("W021", _W,
                                 f"Phase {entry['phaseId']}: integer prefix implies {expected} but listed under {entry['milestone']}",
                                 advise_remedy("gsd-tools roadmap upgrade --convention milestone-prefixed")))
    return diagnostics


def _check_w021(snapshot):
    diagnostics = []
    root_convention = _get(snapshot["config"]["value"], "phase_id_convention")
    if root_convention == "milestone-prefixed":
        diagnostics.extend(_check_milestone_prefix_w021(snapshot))
    if snapshot.get("phaseIdConvention") == "bracket":
        for mm in snapshot["roadmapBracketIncoherences"]["value"]:
            if mm["kind"] == "missing-bracket":
                message = (f"Phase {mm['phaseId']}: heading is not in bracket form under the 'bracket' convention "
                           f"(expected `[CODE.{mm['sectionMilestone']}] {mm['phaseId']}:`)")
            else:
                message = f"Phase {mm['phaseId']}: bracket milestone {mm['phaseMilestone']} does not match its section milestone {mm['sectionMilestone']}"
            diagnostics.append(_diag("W021", _W, message, advise_remedy(
                "Bracket migration lands with the #612 migrator (PR-3); until then, manually align the bracket milestone in this heading to match the enclosing section.")))
    return diagnostics


def _check_w026(snapshot):
    status = (snapshot["stateStatus"]["value"] or "").strip().lower()
    if not re.search(r"milestone complete|archived", status):
        return []
    phase_ids = snapshot["currentMilestoneRoadmapPhaseIds"]["value"]
    context = _directory_context(snapshot, phase_ids)
    unstarted = []
    for phase_id in phase_ids:
        found = match_phase_dirs(snapshot["allPhaseDirNames"]["value"], phase_lookup_query(phase_id, context),
                                 snapshot.get("phaseIdConvention"), None, context)
        if len(found["matches"]) == 0:
            unstarted.append(phase_id)
    if len(unstarted) == 0:
        return []
    return [_diag("W026", _W,
                  f"STATE says milestone complete but ROADMAP lists {len(unstarted)} unstarted phase(s) (e.g. Phase {unstarted[0]})",
                  advise_remedy("Run validate consistency or re-run complete-milestone after verifying all phases are done"))]


RULE_GROUPS["state-consistency"] = [
    _rule("W024", _W, "STATE.md was written many commits ago — treat its contents as approximate", False, _check_w024),
    _rule("W002", _W, "STATE.md references invalid phase", False, _check_w002),
    _rule("W011", _W, "STATE.md current-phase status disagrees with ROADMAP.md checkbox", False, _check_w011),
    _rule("W021", _W, "Phase's integer prefix implies a different milestone than its ROADMAP section (phase_id_convention: milestone-prefixed)",
          False, _check_w021),
    _rule("W026", _W, "STATE says milestone complete but ROADMAP lists an unstarted phase for that milestone", False, _check_w026),
]


# --- phase-structure: W005, W023, I001, W009, W030 --------------------------------------------------

def _check_w005(snapshot):
    diagnostics = []
    convention = snapshot.get("phaseIdConvention")
    for name in snapshot["phaseDirs"]["value"]:
        if not is_phase_dir_name(name, convention):
            diagnostics.append(_diag("W005", _W, f'Phase directory "{name}" doesn\'t follow NN-name format',
                                     advise_remedy("Rename to match pattern (e.g., 01-setup)")))
    return diagnostics


def _check_w023(snapshot):
    groups = {}
    for name in snapshot["phaseDirs"]["value"]:
        groups.setdefault(normalize_phase_name(extract_phase_token(name)), []).append(name)
    phase_by_dir = {p["dir"]: p for p in snapshot["phases"]["value"]}
    context = snapshot.get("directoryContext")

    def order(a, b):
        return compare_phase_num(a, b, context) or _locale_compare(str(a), str(b))

    diagnostics = []
    for key, dirs in groups.items():
        if len(dirs) < 2:
            continue
        described = []
        for name in sorted(dirs, key=functools.cmp_to_key(order)):
            phase = phase_by_dir.get(name)
            status = to_display_label(phase_status_from_facts({
                "planCount": phase["planCount"] if phase else 0,
                "summaryCount": phase["summaryCount"] if phase else 0,
                "complete": phase["complete"] if phase else False,
                "verificationStatus": phase["verificationStatus"] if phase else None,
            }), "Not Started")
            described.append(f"{name} ({status})")
        diagnostics.append(_diag("W023", _W, f'Phase directories collide on normalized key "{key}": {", ".join(described)}',
                                 advise_remedy("Inspect each directory; rename or remove the duplicate so only one directory maps to this phase key")))
    return diagnostics


def _check_i001(snapshot):
    diagnostics = []
    for phase in snapshot["phases"]["value"]:
        deficit = phase["planCount"] - phase["summaryCount"]
        if deficit > 0:
            diagnostics.append(_diag("I001", _INFO, f"Phase {phase['dir']} has {deficit} plan(s) without a matching summary",
                                     advise_remedy("May be in progress")))
    return diagnostics


def _check_w009(snapshot):
    diagnostics = []
    for entry in snapshot["researchValidationStatus"]["value"]:
        if entry["hasValidationArchitecture"] and not entry["hasValidationMd"]:
            diagnostics.append(_diag("W009", _W, f"Phase {entry['dir']}: has Validation Architecture in RESEARCH.md but no VALIDATION.md",
                                     advise_remedy("Re-run /gsd-plan-phase with --research to regenerate")))
    return diagnostics


def _check_w030(snapshot):
    diagnostics = []
    for phase in snapshot["phases"]["value"]:
        invalid = phase.get("verificationStatusError")
        if not invalid:
            continue
        target = legacy_status_repair_target(invalid.get("rawStatus"))
        if target is None:
            remedy = advise_remedy("Set the report frontmatter `status` to one of passed | gaps_found | human_needed, "
                                   "or delete the report and re-run the phase verification")
        else:
            remedy = _remedy("REPAIR_VERIFICATION_STATUS", _NONE, {"file": invalid["file"], "from": invalid["rawStatus"], "to": target})
        diagnostics.append(_diag("W030", _W, f"Phase {phase['dir']}: {invalid['message']}", remedy))
    return diagnostics


RULE_GROUPS["phase-structure"] = [
    _rule("W005", _W, "Phase directory naming mismatch", False, _check_w005),
    _rule("W023", _W, "Phase directories collide on normalized key", False, _check_w023),
    _rule("I001", _INFO, "Plan without SUMMARY (may be in progress)", False, _check_i001),
    _rule("W009", _W, "Phase has Validation Architecture in RESEARCH.md but no VALIDATION.md", False, _check_w009),
    _rule("W030", _W, "Phase verification report status is outside the closed set", True, _check_w030),
]


# --- roadmap-disk-consistency: W006, W007 -------------------------------------------------------------

def _dirs_for_phase(dirs, phase_id, convention, context):
    canonical = match_phase_dirs(dirs, phase_lookup_query(phase_id, context), convention, None, context)["matches"]
    if canonical:
        return canonical
    variants = phase_variants(phase_id)
    matched = []
    for name in dirs:
        token = extract_phase_token(name, convention).upper()
        if any(token == variant.upper() for variant in variants):
            matched.append(name)
    return matched


def _is_phase_not_started(phase_id, checkboxes):
    return any(variant in checkboxes and checkboxes[variant] is False for variant in phase_variants(phase_id))


def _check_w006(snapshot):
    if snapshot["roadmapDeclaredPhases"]["scope"] != SCOPE["COMPLETE"]:
        return []
    dirs = snapshot["allPhaseDirNames"]["value"]
    convention = snapshot.get("phaseIdConvention")
    declared = snapshot["roadmapDeclaredPhases"]["value"]
    context = _directory_context(snapshot, [entry["phaseId"] for entry in declared])
    archived = set(snapshot["archivedPhaseTokens"]["value"])
    sentinel_tokens = set(snapshot["roadmapSentinelPhaseTokens"]["value"])
    checkboxes = snapshot["roadmapPhaseCheckboxes"]["value"]
    diagnostics = []
    for entry in declared:
        phase_id = entry["phaseId"]
        if phase_id in sentinel_tokens or is_sentinel_phase_id(phase_id):
            continue
        if _dirs_for_phase(dirs, phase_id, convention, context):
            continue
        if any(variant in archived for variant in phase_variants(phase_id)):
            continue
        if _is_phase_not_started(phase_id, checkboxes):
            continue
        diagnostics.append(_diag("W006", _W, f"Phase {phase_id} in ROADMAP.md but no directory on disk",
                                 advise_remedy("Create phase directory or remove from roadmap")))
    return diagnostics


def _check_w007(snapshot):
    if snapshot["roadmapDeclaredPhases"]["scope"] != SCOPE["COMPLETE"]:
        return []
    dirs = snapshot["allPhaseDirNames"]["value"]
    convention = snapshot.get("phaseIdConvention")
    declared = snapshot["roadmapDeclaredPhases"]["value"]
    context = _directory_context(snapshot, [entry["phaseId"] for entry in declared])
    claimed = set()
    for entry in declared:
        claimed.update(_dirs_for_phase(dirs, entry["phaseId"], convention, context))
    diagnostics = []
    for name in dirs:
        token = extract_phase_token(name, convention)
        if is_sentinel_phase_dir(name) or name in claimed:
            continue
        diagnostics.append(_diag("W007", _W, f"Phase {token} exists on disk but not in ROADMAP.md", advise_remedy("Add to roadmap or remove directory")))
    return diagnostics


RULE_GROUPS["roadmap-disk-consistency"] = [
    _rule("W006", _W, "Phase in ROADMAP but no directory", False, _check_w006),
    _rule("W007", _W, "Phase on disk but not in ROADMAP", False, _check_w007),
]
