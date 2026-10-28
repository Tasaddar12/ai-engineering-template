"""Reviewer lane descriptor: the cross-AI reviewer lane contract declared as data.

Ported from upstream gsd-core ``src/review-lane-descriptor.cts`` at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).
The ``splitLines`` helper from upstream ``src/text-lines.cts`` is inlined as the
private ``_split_lines``.

This module DECLARES; it does not execute. It exposes:

* ``ARGV_PLACEHOLDER`` - the closed five-member argv template vocabulary.
* ``REVIEWER_LANES`` - the eleven declared first-party lanes, in ``write_reviews``
  order (frozen; each lane is a read-only dict with camelCase upstream field names).
* ``LANE_SLUG_RE`` - the slug grammar every lane slug must satisfy.
* ``merge_reviewer_lanes(first_party, registry)`` - first-party union installed
  overlay ``reviewer`` bodies, first-party winning on slug collision.
* ``PARITY_VIOLATION`` / ``check_reviewer_lane_parity(input)`` - bidirectional
  descriptor / roster / registry parity plus the workflow anti-parity checks.
* ``DOCS_PARITY_VIOLATION`` / ``check_reviewer_docs_parity(input)`` - documentation
  parity of the declared roster against documents supplied by the caller.

Lane and violation dicts keep upstream's camelCase keys (``timeoutFloorMs``,
``workflowText``, ...) so manifests and JSON output are interchangeable with
upstream. Both checkers are pure and total: they never read the filesystem and
never raise on malformed input.

Deviations:

* Upstream has no CLI in this module (``routeReviewLane`` in ``gsd-tools.cjs``
  consumes it), so there is no ``main``. The repo's ``review-lane`` verb is
  implemented separately by ``workflow_ops.review_lane`` and does not use this
  module.
* Upstream lane data and regexes name GSD-specific surfaces and are kept
  verbatim: the availability probe anchors on ``gsd_run review-lane availability``
  (this repo's runtime command is ``engineer_run``), the documentation arm keys on
  ``/gsd-review`` / ``/gsd:review`` (this repo's command is ``/code-review``), the
  workflow step is ``<step name="invoke_reviewers">``, and config keys keep the
  upstream ``review.*`` names. The module takes no workflow or document
  identity of its own, so a caller may adapt the equivalents by passing text
  that uses the upstream markers.
* The upstream TypeScript interfaces and type aliases (``LaneTransport``,
  ``PromptChannel``, ``OutputChannel``, ``EffortChannel``, ``EvidenceClass``,
  ``LaneHandler``, ``EmptyOutputPolicy``, ``LaneProbe``, ``SpawnInvoke``,
  ``HttpInvoke``, ``SpawnLane``, ``HttpLane``, ``ReviewerLane``,
  ``ParityInput``, ``ParityResult``, ``DocsParityInput``, ``DocsParityResult``)
  are type-only and have no runtime counterpart; their shapes are the dict
  shapes documented here.
* ``Object.freeze`` is mirrored by read-only ``dict``/``list`` subclasses that
  raise ``TypeError`` on mutation and copy/pickle as plain containers. Like
  upstream the freeze is shallow: a lane is frozen, its nested ``invoke`` is not.
* JavaScript string coercion (``String(x)``) and ``typeof`` used for violation
  subjects are reproduced by private helpers.
"""
from __future__ import annotations

import math
import re

_UNDEFINED = object()


class _FrozenDict(dict):
    """Read-only dict mirroring ``Object.freeze`` on an object."""

    def _locked(self, *args, **kwargs):
        raise TypeError("frozen mapping is read-only")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _locked

    def __copy__(self):
        return dict(self)

    def __deepcopy__(self, memo):
        import copy
        return {key: copy.deepcopy(value, memo) for key, value in self.items()}

    def __reduce__(self):
        return (dict, (dict(self),))


class _FrozenList(list):
    """Read-only list mirroring ``Object.freeze`` on an array."""

    def _locked(self, *args, **kwargs):
        raise TypeError("frozen list is read-only")

    __setitem__ = __delitem__ = __iadd__ = __imul__ = _locked
    append = extend = insert = pop = remove = clear = sort = reverse = _locked

    def __copy__(self):
        return list(self)

    def __deepcopy__(self, memo):
        import copy
        return [copy.deepcopy(value, memo) for value in self]

    def __reduce__(self):
        return (list, (list(self),))


# Argv placeholders: a closed five-member vocabulary with no expressions, nesting
# or conditionals. A placeholder expands to zero or more argv elements and vanishes
# when it has nothing to contribute.
ARGV_PLACEHOLDER = _FrozenDict({
    # `modelArg` + the resolved model, or nothing.
    "MODEL": "{{model}}",
    # The host's effort argv, or nothing unless `effortChannel` is `argv`.
    "EFFORT": "{{effort}}",
    # `outputArg` + the review path, or nothing unless `outputChannel` is `file-arg`.
    "OUTPUT": "{{output}}",
    # The argv-borne prompt, or nothing unless `promptChannel` is `argv`/`argv-file-ref`.
    "PROMPT": "{{prompt}}",
    # A lane's own CLI-native inner timeout, derived from the resolved outer `timeoutMs`.
    "NATIVE_TIMEOUT": "{{nativeTimeout}}",
})

_SPAWN_STDIN_STDOUT = {"promptChannel": "stdin", "outputChannel": "stdout"}

# The eleven declared lanes, in `write_reviews` order. The `gemini` lane was retired
# upstream (Gemini CLI sunset); `kimi-code` joined with the invocation iteration.
REVIEWER_LANES = _FrozenList(_FrozenDict(lane) for lane in [
    {
        # 1_200_000 rather than the 900_000 floor: headless Claude measured ~525 s on a
        # large plan set.
        "slug": "claude",
        "flags": ["--claude"],
        "transport": "spawn",
        "probe": {"kind": "command-exists", "binary": "claude"},
        "invoke": {
            "binary": "claude",
            "args": ["{{model}}", "{{effort}}", "-p", "-"],
            **_SPAWN_STDIN_STDOUT,
            "modelArg": "--model",
            "effortChannel": "argv",
            # Suppress the invoking user's global/project CLAUDE.md and auto-memory so
            # the claude lane sees only the assembled prompt (independent-review premise).
            "env": {"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        },
        "timeoutFloorMs": 1_200_000,
        "timeoutConfigKey": "review.timeouts.claude",
        "emptyOutput": "stub-with-stderr",
        "reviewsSection": "Claude",
        "evidenceClass": "source-grounded",
        "requiresBinaries": [],
        "promptBudgetKey": "review.max_prompt_tokens_per_reviewer.claude",
        "modelConfigKey": "review.models.claude",
        "effortConfigKey": "review.effort.claude",
        "defaultEffort": "high",
        "handler": None,
    },
    {
        # Codex captures the review through its own `-o/--output-last-message` and discards
        # stdout, because on Windows it writes process-teardown noise to stdout AFTER the
        # final message, which would slip past the empty-output guard.
        "slug": "codex",
        "flags": ["--codex"],
        "transport": "spawn",
        "probe": {"kind": "command-exists", "binary": "codex"},
        "invoke": {
            "binary": "codex",
            # Leg order exactly: codex exec --ephemeral --model M $EFFORT --skip-git-repo-check -o F -
            "args": ["exec", "--ephemeral", "{{model}}", "{{effort}}", "--skip-git-repo-check", "{{output}}", "-"],
            "promptChannel": "stdin",
            "outputChannel": "file-arg",
            "outputArg": "-o",
            "modelArg": "--model",
            "effortChannel": "argv",
        },
        "timeoutFloorMs": 1_200_000,
        "timeoutConfigKey": "review.timeouts.codex",
        "emptyOutput": "stub-with-stderr",
        "reviewsSection": "Codex",
        "evidenceClass": "source-grounded",
        "requiresBinaries": [],
        "promptBudgetKey": "review.max_prompt_tokens_per_reviewer.codex",
        "modelConfigKey": "review.models.codex",
        "effortConfigKey": "review.effort.codex",
        "defaultEffort": "high",
        "handler": None,
    },
    {
        # Fed no prompt: CodeRabbit reviews the working-tree diff and accepts neither a
        # prompt nor a model flag. Its findings are down-weighted in the consensus step.
        "slug": "coderabbit",
        "flags": ["--coderabbit"],
        "transport": "spawn",
        "probe": {"kind": "command-exists", "binary": "coderabbit"},
        "invoke": {
            "binary": "coderabbit",
            "args": ["review", "--prompt-only"],
            "promptChannel": "none",
            "outputChannel": "stdout",
            "modelArg": None,
            "effortChannel": "none",
        },
        "timeoutFloorMs": 360_000,
        "timeoutConfigKey": None,
        "emptyOutput": "stub-with-stderr",
        "reviewsSection": "CodeRabbit",
        "evidenceClass": "diff-only",
        "requiresBinaries": [],
        "promptBudgetKey": "review.max_prompt_tokens_per_reviewer.coderabbit",
        # Accepts no model flag at all - not merely "none configured".
        "modelConfigKey": None,
        "effortConfigKey": None,
        "defaultEffort": None,
        "handler": None,
    },
    {
        # `--format json` is the primary invocation, not a fallback: the review text lives
        # in assistant `text` parts, which the default formatter drops when the agent stops
        # with no final message.
        "slug": "opencode",
        "flags": ["--opencode"],
        "transport": "spawn",
        "probe": {"kind": "command-exists", "binary": "opencode"},
        "invoke": {
            "binary": "opencode",
            "args": ["run", "{{model}}", "{{effort}}", "--format", "json", "-"],
            **_SPAWN_STDIN_STDOUT,
            "modelArg": "--model",
            "effortChannel": "argv",
        },
        "timeoutFloorMs": 660_000,
        "timeoutConfigKey": "review.timeouts.opencode",
        "emptyOutput": "stub-with-stderr",
        "reviewsSection": "OpenCode",
        "evidenceClass": "source-grounded",
        # The handler reconstructs from the JSON stream directly, so `jq` is not a prerequisite.
        "requiresBinaries": [],
        "promptBudgetKey": "review.max_prompt_tokens_per_reviewer.opencode",
        "modelConfigKey": "review.models.opencode",
        "effortConfigKey": "review.effort.opencode",
        "defaultEffort": "high",
        # The review is REBUILT from assistant `text` parts; a plain stdout copy would write
        # the raw JSON envelope as the review.
        "handler": "opencode",
    },
    {
        "slug": "qwen",
        "flags": ["--qwen"],
        "transport": "spawn",
        "probe": {"kind": "command-exists", "binary": "qwen"},
        "invoke": {
            "binary": "qwen",
            "args": ["-"],
            **_SPAWN_STDIN_STDOUT,
            "modelArg": None,
            "effortChannel": "none",
        },
        "timeoutFloorMs": 900_000,
        "timeoutConfigKey": None,
        "emptyOutput": "stub-with-stderr",
        "reviewsSection": "Qwen",
        "evidenceClass": "source-grounded",
        "requiresBinaries": [],
        "promptBudgetKey": "review.max_prompt_tokens_per_reviewer.qwen",
        "modelConfigKey": None,
        "effortConfigKey": None,
        "defaultEffort": None,
        "handler": None,
    },
    {
        # `cursor-agent` is a SEPARATE binary from the `cursor` IDE launcher. Print mode takes
        # the prompt as an ARGUMENT, so a full plan set is passed by file reference to stay
        # clear of the 32,767-char Windows process-argument ceiling.
        "slug": "cursor",
        "flags": ["--cursor"],
        "transport": "spawn",
        "probe": {"kind": "command-exists", "binary": "cursor-agent"},
        "invoke": {
            "binary": "cursor-agent",
            "args": ["-p", "{{model}}", "--mode", "ask", "--trust", "--output-format", "text", "{{prompt}}"],
            "promptChannel": "argv-file-ref",
            "outputChannel": "stdout",
            "modelArg": "--model",
            "effortChannel": "none",
        },
        "timeoutFloorMs": 900_000,
        "timeoutConfigKey": None,
        "emptyOutput": "stub-with-stderr",
        "reviewsSection": "Cursor",
        "evidenceClass": "source-grounded",
        "requiresBinaries": [],
        "promptBudgetKey": "review.max_prompt_tokens_per_reviewer.cursor",
        # cursor-agent exposes --model; wired the same as codex.
        "modelConfigKey": "review.models.cursor",
        "effortConfigKey": None,
        "defaultEffort": None,
        "handler": None,
    },
    {
        # Handler-owned: a three-layer fallback for an upstream stdout bug, a two-level timeout
        # (600 s external cap over a 540 s native --print-timeout), and a stale-response
        # watermark guard. `timeoutFloorMs` carries the OUTER bound only.
        "slug": "antigravity",
        "flags": ["--antigravity", "--agy"],
        "transport": "spawn",
        "probe": {"kind": "command-exists", "binary": "agy"},
        "invoke": {
            "binary": "agy",
            # `{{nativeTimeout}}` is the fifth ARGV_PLACEHOLDER member: it expands to a value
            # DERIVED from this lane's resolved outer `timeoutMs`, so the native
            # `--print-timeout` and the outer wall-clock cap can never drift apart.
            "args": ["--print-timeout", "{{nativeTimeout}}", "{{model}}", "-p", "{{prompt}}"],
            "promptChannel": "argv-file-ref",
            "outputChannel": "stdout",
            "modelArg": "--model",
            "effortChannel": "none",
        },
        "timeoutFloorMs": 600_000,
        "timeoutConfigKey": "review.timeouts.antigravity",
        "emptyOutput": "handler-owned",
        "reviewsSection": "Antigravity",
        "evidenceClass": "source-grounded",
        # The handler reads the transcript with a JSON parse per line, not `jq`.
        "requiresBinaries": [],
        "promptBudgetKey": "review.max_prompt_tokens_per_reviewer.antigravity",
        # NOT `review.models.antigravity` - the shipped key is `review.models.agy`. This lane is
        # why the key is declared, not derived.
        "modelConfigKey": "review.models.agy",
        "effortConfigKey": None,
        "defaultEffort": None,
        "handler": "antigravity",
    },
    {
        "slug": "ollama",
        "flags": ["--ollama"],
        "transport": "openai-http",
        "probe": {
            "kind": "http-reachable",
            "hostConfigKey": "review.ollama_host",
            "path": "/v1/models",
            "timeoutMs": 2_000,
        },
        "invoke": {
            "hostConfigKey": "review.ollama_host",
            "defaultHost": "http://localhost:11434",
            "path": "/v1/chat/completions",
            "modelDiscovery": "first-from-models-endpoint",
            "fallbackModel": "llama3",
            "effortChannel": "none",
        },
        "timeoutFloorMs": 120_000,
        "timeoutConfigKey": "review.timeouts.ollama",
        "emptyOutput": "stub-with-stderr",
        "reviewsSection": "Ollama",
        "evidenceClass": "source-grounded",
        # The openai-compatible handler speaks HTTP directly, so neither `jq` nor `curl` is required.
        "requiresBinaries": [],
        "promptBudgetKey": "review.max_prompt_tokens_per_reviewer.ollama",
        "modelConfigKey": "review.models.ollama",
        "effortConfigKey": None,
        "defaultEffort": None,
        "handler": "openai-compatible",
    },
    {
        "slug": "lm_studio",
        "flags": ["--lm-studio"],
        "transport": "openai-http",
        "probe": {
            "kind": "http-reachable",
            "hostConfigKey": "review.lm_studio_host",
            "path": "/v1/models",
            "timeoutMs": 2_000,
        },
        "invoke": {
            "hostConfigKey": "review.lm_studio_host",
            "defaultHost": "http://localhost:1234",
            "path": "/v1/chat/completions",
            "modelDiscovery": "first-from-models-endpoint",
            "fallbackModel": "local-model",
            "effortChannel": "none",
        },
        "timeoutFloorMs": 120_000,
        "timeoutConfigKey": "review.timeouts.lm_studio",
        "emptyOutput": "stub-with-stderr",
        "reviewsSection": "LM Studio",
        "evidenceClass": "source-grounded",
        "requiresBinaries": [],
        "promptBudgetKey": "review.max_prompt_tokens_per_reviewer.lm_studio",
        "modelConfigKey": "review.models.lm_studio",
        "effortConfigKey": None,
        "defaultEffort": None,
        "handler": "openai-compatible",
    },
    {
        "slug": "llama_cpp",
        "flags": ["--llama-cpp"],
        "transport": "openai-http",
        "probe": {
            "kind": "http-reachable",
            "hostConfigKey": "review.llama_cpp_host",
            "path": "/v1/models",
            "timeoutMs": 2_000,
        },
        "invoke": {
            "hostConfigKey": "review.llama_cpp_host",
            "defaultHost": "http://localhost:8080",
            "path": "/v1/chat/completions",
            "modelDiscovery": "first-from-models-endpoint",
            "fallbackModel": "local-model",
            "effortChannel": "none",
        },
        "timeoutFloorMs": 120_000,
        "timeoutConfigKey": "review.timeouts.llama_cpp",
        "emptyOutput": "stub-with-stderr",
        "reviewsSection": "llama.cpp",
        "evidenceClass": "source-grounded",
        "requiresBinaries": [],
        "promptBudgetKey": "review.max_prompt_tokens_per_reviewer.llama_cpp",
        "modelConfigKey": "review.models.llama_cpp",
        "effortConfigKey": None,
        "defaultEffort": None,
        "handler": "openai-compatible",
    },
    {
        # The probe is `command-capability`, not `command-exists`: `kimi` is claimed by BOTH the
        # Kimi Code CLI (Node) and the legacy Python kimi-cli, so an existence-only probe could
        # register the wrong tool. The needle `--output-format` appears in Kimi Code's `--help`
        # and is absent from the legacy CLI. The probe is bounded (`timeoutMs`) and runs only
        # for a SELECTED lane.
        "slug": "kimi-code",
        "flags": ["--kimi-code"],
        "transport": "spawn",
        "probe": {
            "kind": "command-capability",
            "binary": "kimi",
            "needle": "--output-format",
            "timeoutMs": 5_000,
        },
        "invoke": {
            # Print mode takes the prompt as an ARGUMENT, so the full plan set goes by file
            # reference - same shape as cursor.
            "binary": "kimi",
            "args": ["{{model}}", "-p", "{{prompt}}"],
            "promptChannel": "argv-file-ref",
            "outputChannel": "stdout",
            "modelArg": "-m",
            "effortChannel": "none",
        },
        "timeoutFloorMs": 900_000,
        "timeoutConfigKey": "review.timeouts.kimi-code",
        "emptyOutput": "stub-with-stderr",
        "reviewsSection": "Kimi Code",
        "evidenceClass": "source-grounded",
        "requiresBinaries": [],
        "promptBudgetKey": "review.max_prompt_tokens_per_reviewer.kimi-code",
        "modelConfigKey": "review.models.kimi-code",
        "effortConfigKey": None,
        "defaultEffort": None,
        "handler": None,
    },
])

# The slug grammar. A lane whose slug falls outside this class is unmatchable in the
# workflow markers, so it is reported as INVALID_SLUG rather than silently missed.
# `\Z` (not `$`) so a trailing newline does not slip through, matching JS `$` without /m.
LANE_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*\Z")


# --------------------------------------------------------------------------- #
# Private JS-semantics helpers
# --------------------------------------------------------------------------- #

def _split_lines(content):
    """Split on ``\\r\\n`` or ``\\n`` (inlined ``splitLines`` from text-lines.cts)."""
    if not isinstance(content, str):
        raise TypeError("splitLines: expected a string, got " + _js_typeof(content))
    return re.split(r"\r?\n", content)


def _js_typeof(value):
    if value is _UNDEFINED:
        return "undefined"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if callable(value):
        return "function"
    return "object"


def _js_number(value):
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        if value == int(value) and abs(value) < 1e21:
            return str(int(value))
    return str(value)


def _js_string(value):
    """Approximate JavaScript ``String(value)`` for violation subjects."""
    if value is _UNDEFINED:
        return "undefined"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return _js_number(value)
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return ",".join("" if item is None or item is _UNDEFINED else _js_string(item) for item in value)
    return "[object Object]"


def _is_array(value):
    return isinstance(value, (list, tuple))


def _is_object(value):
    """JS ``typeof x === 'object' && x !== null`` (arrays included)."""
    return isinstance(value, (dict, list, tuple))


def _get(obj, key):
    return obj.get(key, _UNDEFINED) if isinstance(obj, dict) else _UNDEFINED


def _trim(value):
    return value.strip().strip("﻿").strip()


# --------------------------------------------------------------------------- #
# Lane merge
# --------------------------------------------------------------------------- #

def merge_reviewer_lanes(first_party, registry):
    """Merge first-party lanes with installed overlay ``reviewer`` bodies.

    First-party union overlay, first-party wins on slug collision (returned by
    reference). Pure and total: a capability whose ``reviewer`` body is absent,
    non-object, or carries an empty or grammar-invalid slug is skipped. Returns a
    NEW list: first-party lanes in order, then accepted overlay lanes in registry
    iteration order.
    """
    by_slug = {}
    ordered = []
    for lane in first_party if _is_array(first_party) else []:
        raw = _get(lane, "slug")
        slug = _trim(raw) if isinstance(raw, str) else ""
        if not slug:
            continue
        if slug not in by_slug:
            by_slug[slug] = lane
            ordered.append(lane)

    capabilities = registry.get("capabilities") if isinstance(registry, dict) else None
    if isinstance(capabilities, dict):
        caps = list(capabilities.values())
    elif _is_array(capabilities):
        caps = list(capabilities)
    else:
        caps = []
    for cap in caps:
        if not isinstance(cap, dict):
            continue
        body = cap.get("reviewer")
        if not isinstance(body, dict):
            continue
        raw_slug = body.get("slug")
        slug = _trim(raw_slug) if isinstance(raw_slug, str) else ""
        if not slug or not LANE_SLUG_RE.match(slug):
            continue
        if slug in by_slug:
            continue
        lane = {**body, "slug": slug}
        by_slug[slug] = lane
        ordered.append(lane)
    return ordered


# --------------------------------------------------------------------------- #
# Lane parity
# --------------------------------------------------------------------------- #

PARITY_VIOLATION = _FrozenDict({
    "MALFORMED_LANE": "malformed_lane",
    "INVALID_SLUG": "invalid_slug",
    "ROSTER_SLUG_UNDECLARED": "roster_slug_undeclared",
    "DESCRIPTOR_LANE_NOT_IN_ROSTER": "descriptor_lane_not_in_roster",
    "REGISTRY_LANE_UNDECLARED": "registry_lane_undeclared",
    "DESCRIPTOR_LANE_NOT_IN_REGISTRY": "descriptor_lane_not_in_registry",
    "BESPOKE_LEG_PRESENT": "bespoke_leg_present",
    "AVAILABILITY_FALLBACK_MISMATCH": "availability_fallback_mismatch",
    "DUPLICATE_SLUG": "duplicate_slug",
    "DUPLICATE_FLAG": "duplicate_flag",
    "DUPLICATE_SECTION": "duplicate_section",
})

# A hand-authored `invoke_reviewers` leg marker; matching one is now the violation.
_LEG_MARKER_RE = re.compile(r"<!--\s*reviewer-lane:\s*([a-z0-9_-]+)\s*-->")

# The workflow's availability call at command position (upstream spelling).
_AVAILABILITY_CALL_RE = re.compile(r"^\s*gsd_run review-lane availability(?:\s|\Z)")
# One `<slug>:missing` row in the printf fallback; slug grammar capped at 32 chars.
_AVAILABILITY_FALLBACK_ROW_RE = re.compile(r"(?:'|\\n)([a-z0-9][a-z0-9_-]{0,31}):missing")

# Bounds of the step a bespoke leg marker could appear inside.
_INVOKE_STEP_RE = re.compile(r'<step name="invoke_reviewers">([\s\S]*?)</step>')


def _slice_step(workflow_text, pattern):
    match = pattern.search(workflow_text)
    return match.group(1) if match else ""


def _count_occurrences(haystack, pattern):
    counts = {}
    for match in pattern.finditer(haystack):
        key = match.group(1).strip()
        counts[key] = counts.get(key, 0) + 1
    return counts


def _string_set(values):
    """Ordered set of the string members of an array; non-arrays are empty."""
    return dict.fromkeys(x for x in values if isinstance(x, str)) if _is_array(values) else {}


def check_reviewer_lane_parity(input):
    """Bidirectional parity across descriptor, roster and generated registry.

    ``input`` is a mapping with keys ``descriptor`` (lanes), ``roster`` (slugs),
    ``registry`` (slugs declared by registry ``reviewer`` bodies) and
    ``workflowText`` (full text of the review workflow). Returns
    ``{"ok": bool, "violations": [{"reason", "subject"}, ...]}``.

    Pure and total: never reads the filesystem, never raises. Malformed
    ``registry`` / ``workflowText`` degrade to violations or coercion. CRLF
    insensitive.
    """
    data = input if isinstance(input, dict) else {}
    descriptor = data.get("descriptor")
    roster = data.get("roster")
    workflow_raw = data.get("workflowText")
    workflow_text = _js_string("" if workflow_raw is None else workflow_raw).replace("\r\n", "\n")
    violations = []

    def add(reason, subject):
        violations.append({"reason": reason, "subject": subject})

    seen_slug = {}
    seen_flag = {}
    seen_section = {}
    http_slugs = {}

    raw_lanes = list(descriptor) if _is_array(descriptor) else []
    for raw in raw_lanes:
        if not _is_object(raw):
            add(PARITY_VIOLATION["MALFORMED_LANE"], _js_string(raw))
            continue
        slug = _get(raw, "slug")
        if not isinstance(slug, str) or not LANE_SLUG_RE.match(slug):
            add(PARITY_VIOLATION["INVALID_SLUG"], _js_string(slug))
            continue
        section_raw = _get(raw, "reviewsSection")
        section = section_raw if isinstance(section_raw, str) else None

        if slug in seen_slug:
            add(PARITY_VIOLATION["DUPLICATE_SLUG"], slug)
        seen_slug[slug] = True
        if _get(raw, "transport") == "openai-http":
            http_slugs[slug] = True

        flags_raw = _get(raw, "flags")
        for flag in flags_raw if _is_array(flags_raw) else []:
            if not isinstance(flag, str):
                continue
            if flag in seen_flag:
                add(PARITY_VIOLATION["DUPLICATE_FLAG"], flag)
            seen_flag[flag] = True

        # Two lanes sharing a heading would silently MERGE their output in REVIEWS.md.
        if section is not None:
            if section in seen_section:
                add(PARITY_VIOLATION["DUPLICATE_SECTION"], section)
            seen_section[section] = True

    roster_set = _string_set(roster)
    for slug in roster_set:
        if slug not in seen_slug:
            add(PARITY_VIOLATION["ROSTER_SLUG_UNDECLARED"], slug)
    for slug in seen_slug:
        if slug not in roster_set:
            add(PARITY_VIOLATION["DESCRIPTOR_LANE_NOT_IN_ROSTER"], slug)

    # A non-array registry degrades to an empty set: every descriptor lane reports missing.
    registry_set = _string_set(data.get("registry"))
    for slug in registry_set:
        if slug not in seen_slug:
            add(PARITY_VIOLATION["REGISTRY_LANE_UNDECLARED"], slug)
    for slug in seen_slug:
        if slug not in registry_set:
            add(PARITY_VIOLATION["DESCRIPTOR_LANE_NOT_IN_REGISTRY"], slug)

    # Anti-parity: no bespoke per-CLI leg may return inside invoke_reviewers.
    for slug in _count_occurrences(_slice_step(workflow_text, _INVOKE_STEP_RE), _LEG_MARKER_RE):
        add(PARITY_VIOLATION["BESPOKE_LEG_PRESENT"], slug)

    # The availability call's `||` fallback must name exactly the openai-http lanes.
    availability_line = next((line for line in _split_lines(workflow_text) if _AVAILABILITY_CALL_RE.match(line)), None)
    if availability_line is None:
        add(PARITY_VIOLATION["AVAILABILITY_FALLBACK_MISMATCH"], "no-call")
    else:
        if "review-lane availability ||" not in availability_line:
            add(PARITY_VIOLATION["AVAILABILITY_FALLBACK_MISMATCH"], "no-fallback")
        fallback = dict.fromkeys(m.group(1) for m in _AVAILABILITY_FALLBACK_ROW_RE.finditer(availability_line))
        for slug in fallback:
            if slug not in http_slugs:
                add(PARITY_VIOLATION["AVAILABILITY_FALLBACK_MISMATCH"], slug)
        for slug in http_slugs:
            if slug not in fallback:
                add(PARITY_VIOLATION["AVAILABILITY_FALLBACK_MISMATCH"], slug)

    return {"ok": len(violations) == 0, "violations": violations}


# --------------------------------------------------------------------------- #
# Documentation parity
# --------------------------------------------------------------------------- #

DOCS_PARITY_VIOLATION = _FrozenDict({
    "MALFORMED_LANE": "malformed_lane",
    "DOC_FLAG_MISSING": "doc_flag_missing",
    "DOC_FLAG_UNDECLARED": "doc_flag_undeclared",
    "DOC_TITLE_MISSING": "doc_title_missing",
    "SIGNATURE_FLAG_MISSING": "signature_flag_missing",
    "DOC_UNREADABLE": "doc_unreadable",
    "TABLE_ROW_MISSING": "table_row_missing",
})

# Non-lane tokens that legitimately share the `/gsd-review` signature line.
_NON_LANE_SIGNATURE_FLAGS = frozenset(["--all"])

# Every bracketed `--token` on a signature line.
_BRACKETED_FLAG_RE = re.compile(r"\[(--[a-z0-9][a-z0-9-]*)\]")
_FENCE_RE = re.compile(r"^(`{3,}|~{3,})")
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_REVIEW_COMMAND_RE = re.compile(r"/gsd[-:]review\b", re.ASCII)


def _flag_is_documented(text, flag):
    """True when `flag` appears backticked or bracketed. Literal matching, not a regex."""
    return ("`" + flag + "`") in text or ("[" + flag + "]") in text


def _strip_non_prose(text):
    """Blank fenced code blocks and HTML comments, preserving line indexes."""
    out = []
    in_fence = False
    in_comment = False
    for line in text.split("\n"):
        trimmed = line.strip()
        if not in_comment and _FENCE_RE.match(trimmed):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
            continue
        working = line
        if not in_comment and "<!--" in working and "-->" not in working:
            in_comment = True
            out.append(working[:working.index("<!--")])
            continue
        if in_comment:
            if "-->" in working:
                in_comment = False
                out.append(working[working.index("-->") + 3:])
            else:
                out.append("")
            continue
        # Strip single-line comments to a FIXED POINT, then honor any unterminated opener.
        while True:
            previous = working
            working = _COMMENT_RE.sub("", working)
            if working == previous:
                break
        dangling = working.find("<!--")
        if dangling != -1:
            in_comment = True
            working = working[:dangling]
        out.append(working)
    return "\n".join(out)


def _flags_in_first_table_cell(lines, declared):
    """Declared flags appearing in the FIRST cell of a markdown table row."""
    found = {}
    for line in lines:
        trimmed = line.strip()
        if not trimmed.startswith("|"):
            continue
        cells = trimmed.split("|")
        if len(cells) < 2:
            continue
        first_cell = cells[1]
        for flag in declared:
            if _flag_is_documented(first_cell, flag):
                found[flag] = True
    return found


def _find_signature_line(lines):
    """Index of the `/gsd-review ... [--flag]` signature line, or -1."""
    for index, line in enumerate(lines):
        if _REVIEW_COMMAND_RE.search(line) and "[--" in line:
            return index
    return -1


def check_reviewer_docs_parity(input):
    """Documentation parity for the declared reviewer roster.

    ``input`` is a mapping with ``descriptor`` (lanes) and ``docs`` (mapping of
    document label to full text). Four independent arms: every declared flag is
    documented (``doc_flag_missing``); a per-lane table carries a first-cell row
    for every lane (``table_row_missing``); a signature line carries the full
    roster and nothing undeclared (``signature_flag_missing`` /
    ``doc_flag_undeclared``); the Purpose paragraph names every section title
    (``doc_title_missing``). A document with no ``/gsd-review`` surface is skipped,
    a non-string document is ``doc_unreadable``. Returns
    ``{"ok", "violations": [{"reason", "doc", "subject"}, ...], "skipped": [...]}``.

    Pure and total; CRLF insensitive.
    """
    data = input if isinstance(input, dict) else {}
    violations = []
    skipped = []

    def add(reason, doc, subject):
        violations.append({"reason": reason, "doc": doc, "subject": subject})

    declared_flags = []
    declared_titles = []
    descriptor = data.get("descriptor")
    for raw in list(descriptor) if _is_array(descriptor) else []:
        if not _is_object(raw):
            add(DOCS_PARITY_VIOLATION["MALFORMED_LANE"], "(descriptor)", _js_string(raw))
            continue
        flags = _get(raw, "flags")
        for flag in flags if _is_array(flags) else []:
            if isinstance(flag, str) and flag:
                declared_flags.append(flag)
        section = _get(raw, "reviewsSection")
        if isinstance(section, str) and section:
            declared_titles.append(section)
    declared_flag_set = dict.fromkeys(declared_flags)

    raw_docs = data.get("docs")
    if isinstance(raw_docs, dict):
        docs = raw_docs
    elif _is_array(raw_docs):
        docs = {str(index): value for index, value in enumerate(raw_docs)}
    else:
        docs = {}
    if not docs:
        for flag in declared_flag_set:
            add(DOCS_PARITY_VIOLATION["DOC_FLAG_MISSING"], "(no documents supplied)", flag)
        return {"ok": len(violations) == 0, "violations": violations, "skipped": skipped}

    for label, raw_value in docs.items():
        if not isinstance(raw_value, str):
            add(DOCS_PARITY_VIOLATION["DOC_UNREADABLE"], label, _js_typeof(raw_value))
            continue
        text = raw_value.replace("\r\n", "\n")
        prose = _strip_non_prose(text)

        # A mirror that does not document /gsd-review is a partial translation, not drift.
        if not _REVIEW_COMMAND_RE.search(prose):
            skipped.append(label)
            continue

        lines = prose.split("\n")

        # Arm 1: every declared flag is documented somewhere in the doc.
        for flag in declared_flag_set:
            if not _flag_is_documented(prose, flag):
                add(DOCS_PARITY_VIOLATION["DOC_FLAG_MISSING"], label, flag)

        # Arm 4: a doc carrying a per-lane table must carry a row for EVERY lane.
        row_flags = _flags_in_first_table_cell(lines, declared_flag_set)
        if row_flags:
            for flag in declared_flag_set:
                if flag not in row_flags:
                    add(DOCS_PARITY_VIOLATION["TABLE_ROW_MISSING"], label, flag)

        sig_index = _find_signature_line(lines)
        if sig_index == -1:
            continue

        # Arm 2: the signature line carries the FULL roster and nothing undeclared.
        sig_line = lines[sig_index]
        for flag in declared_flag_set:
            if not _flag_is_documented(sig_line, flag):
                add(DOCS_PARITY_VIOLATION["SIGNATURE_FLAG_MISSING"], label, flag)
        seen_undeclared = set()
        for match in _BRACKETED_FLAG_RE.finditer(sig_line):
            token = match.group(1)
            if token in declared_flag_set or token in _NON_LANE_SIGNATURE_FLAGS:
                continue
            if token in seen_undeclared:
                continue
            seen_undeclared.add(token)
            add(DOCS_PARITY_VIOLATION["DOC_FLAG_UNDECLARED"], label, token)

        # Arm 3: the Purpose paragraph (next non-blank line) names every section title.
        cursor = sig_index + 1
        while cursor < len(lines) and lines[cursor].strip() == "":
            cursor += 1
        if cursor >= len(lines):
            continue
        purpose = lines[cursor]
        for title in declared_titles:
            if title not in purpose:
                add(DOCS_PARITY_VIOLATION["DOC_TITLE_MISSING"], label, title)

    return {"ok": len(violations) == 0, "violations": violations, "skipped": skipped}
