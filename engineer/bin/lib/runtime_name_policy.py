"""Runtime name policy: alias resolution and canonicalization for runtime identifiers.

Ported from open-gsd/gsd-core src/runtime-name-policy.cts
(commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79, MIT, Copyright (c) 2026 Open GSD).
Public functions keep the upstream behavior with snake_case names:
canonicalizeRuntimeName -> canonicalize_runtime_name,
resolveRuntimeNameFromCandidates -> resolve_runtime_name_from_candidates,
getProjectInstructionFile -> get_project_instruction_file, getDirName -> get_dir_name,
getRuntimeLabel -> get_runtime_label, getGlobalConfigHomeFragment ->
get_global_config_home_fragment, runtimeFlags -> runtime_flags,
hostBehaviorsFor -> host_behaviors_for, assertKnownRuntime -> assert_known_runtime,
assertNotRetiredRuntime -> assert_not_retired_runtime, isKnownRuntimeId ->
is_known_runtime_id, isRetiredRuntimeId -> is_retired_runtime_id. Constants and error
classes (RETIRED_RUNTIME_IDS, LEGACY_NON_REGISTRY_RUNTIME_HOMES,
LEGACY_NON_REGISTRY_RUNTIME_IDS, FALLBACK_HOST_BEHAVIORS, NO_LOCAL_CONFIG_DIR_SENTINEL,
UnknownRuntimeError, RetiredRuntimeError) keep their upstream names.

Deviations:
    - The capability registry is bound to the sibling port ``capability_registry``
      (upstream lazily requires ./capability-registry.cjs). If it cannot be imported
      the registry counts as failed to load, exactly as upstream treats a failed require.
    - The alias manifest is looked up at ../shared/runtime-aliases.manifest.json
      relative to this file's directory (upstream's gsd-core/bin/shared path) and at
      ../../../sdk/shared/...; neither exists in this repository, so the built-in
      FALLBACK_ALIASES table (identical to upstream's manifest) is what applies.
    - Registry rows, aliases, labels and instruction files are upstream GSD data: they
      name the GSD runtime set, not this repository's own. The existing runtime verb
      ``project-instruction-file`` (engineer/bin/lib/models.py ``instruction``) differs
      from get_project_instruction_file; see the port report for the discrepancies.
    - JS "string" type checks map to ``isinstance(value, str)``; the JS "frozen" objects
      map to read-only mappings.
"""
import json
from pathlib import Path
import re
import unicodedata
from types import MappingProxyType

__all__ = [
    "RETIRED_RUNTIME_IDS", "UnknownRuntimeError", "RetiredRuntimeError", "is_retired_runtime_id",
    "assert_not_retired_runtime", "LEGACY_NON_REGISTRY_RUNTIME_HOMES", "LEGACY_NON_REGISTRY_RUNTIME_IDS",
    "is_known_runtime_id", "assert_known_runtime", "FALLBACK_HOST_BEHAVIORS", "host_behaviors_for",
    "canonicalize_runtime_name", "resolve_runtime_name_from_candidates", "get_project_instruction_file",
    "NO_LOCAL_CONFIG_DIR_SENTINEL", "get_dir_name", "get_runtime_label", "get_global_config_home_fragment",
    "runtime_flags",
]

_UNSET = object()


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


# Runtime ids that were deliberately RETIRED, as opposed to ids never heard of.
# 'gem' + 'ini' keeps the literal out of prose lints, as upstream does.
_RETIRED_RUNTIME_DETAILS = {
    "gem" + "ini": {"successor": "Antigravity", "retiredBy": "#1928", "sunset": "2026-06-18"},
}


def _normalize_for_retirement_match(value):
    """NFKC-fold, lowercase, drop every non-alphanumeric character (membership matching only)."""
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", value).lower())


def _build_retired_spellings():
    spellings = {}
    for retired_id in _RETIRED_RUNTIME_DETAILS:
        spellings[_normalize_for_retirement_match(retired_id)] = retired_id
        spellings[_normalize_for_retirement_match(retired_id + "-cli")] = retired_id
    return spellings


_RETIRED_RUNTIME_SPELLINGS = _build_retired_spellings()

# The canonical retired runtime ids, lowercase (canonical ids only, not alias spellings).
RETIRED_RUNTIME_IDS = frozenset(_RETIRED_RUNTIME_DETAILS)


class UnknownRuntimeError(Exception):
    """A non-empty runtime id that is neither registered nor a known non-registry host."""

    code = "GSD_UNKNOWN_RUNTIME"
    name = "UnknownRuntimeError"

    def __init__(self, runtime_id):
        super().__init__(
            f'Runtime "{runtime_id}" is not registered in the capability registry. '
            "Refusing to resolve it, because the previous behaviour silently returned Claude Code's values.")
        self.runtime_id = runtime_id


class RetiredRuntimeError(Exception):
    """A retired runtime id reached a resolution accessor."""

    code = "GSD_RETIRED_RUNTIME"
    name = "RetiredRuntimeError"

    def __init__(self, runtime_id, detail):
        super().__init__(
            f'Runtime "{runtime_id}" was retired by {detail["retiredBy"]} (sunset {detail["sunset"]}); '
            f'use "{detail["successor"]}" instead. Refusing to resolve it, because the previous '
            "behaviour silently returned Claude Code's values.")
        self.runtime_id = runtime_id


def is_retired_runtime_id(runtime):
    """True when ``runtime`` names a retired runtime under any of its spellings."""
    if not isinstance(runtime, str):
        return False
    return _normalize_for_retirement_match(runtime) in _RETIRED_RUNTIME_SPELLINGS


def assert_not_retired_runtime(runtime):
    """Raise RetiredRuntimeError when ``runtime`` names a retired runtime. No-op otherwise."""
    if not isinstance(runtime, str):
        return
    retired_id = _RETIRED_RUNTIME_SPELLINGS.get(_normalize_for_retirement_match(runtime))
    if retired_id is None:
        return
    detail = _RETIRED_RUNTIME_DETAILS.get(retired_id)
    if detail is None:
        return
    raise RetiredRuntimeError(retired_id, detail)


# Legacy runtime ids with a dedicated resolution branch but no registry descriptor.
LEGACY_NON_REGISTRY_RUNTIME_HOMES = _freeze({
    "grok": {"env": "GROK_AGENTS_HOME", "dir": [".agents"]},
})
LEGACY_NON_REGISTRY_RUNTIME_IDS = frozenset(LEGACY_NON_REGISTRY_RUNTIME_HOMES)


def _load_registry_runtimes():
    """The capability registry's ``runtimes`` map, or None when it fails to load."""
    try:
        from . import capability_registry
        runtimes = getattr(capability_registry, "RUNTIMES", None)
        return runtimes if isinstance(runtimes, dict) else None
    except Exception:
        return None


def is_known_runtime_id(runtime):
    """True for a registered runtime id or a LEGACY_NON_REGISTRY_RUNTIME_IDS member (raw-id match)."""
    if not isinstance(runtime, str) or not runtime:
        return False
    runtimes = _load_registry_runtimes()
    if runtimes is not None and runtime in runtimes:
        return True
    return runtime in LEGACY_NON_REGISTRY_RUNTIME_IDS


def assert_known_runtime(runtime):
    """The one refusal every descriptor accessor shares.

    No-op for an absent id ('' or non-string). A retired id raises RetiredRuntimeError; any
    other non-empty unknown id raises UnknownRuntimeError. When the registry failed to load,
    unknown-ness cannot be proven, so the check degrades to a no-op.
    """
    if not isinstance(runtime, str) or not runtime:
        return
    assert_not_retired_runtime(runtime)
    if _load_registry_runtimes() is None:
        return
    if not is_known_runtime_id(runtime):
        raise UnknownRuntimeError(runtime)


# Fail-safe floor for the two hosts whose generic fallthrough would be wrong if the registry
# failed to load.
FALLBACK_HOST_BEHAVIORS = _freeze({
    "claude": {
        "settingsFileByScope": {"local": "settings.local.json", "global": "settings.json"},
        "permissionsSchema": "claude",
        "sourceMarkerFile": ".gsd-source",
        "hyphenNameAgentBody": True,
        "legacyCommandsGsdInstallMigration": True,
        "legacyCommandsGsdUninstall": "global",
    },
    "antigravity": {"globalDirResolver": "antigravity"},
})


def host_behaviors_for(runtime, registry=_UNSET):
    """A runtime's ``hostBehaviors`` bag (the single accessor).

    Absent id -> {}; registered id -> the descriptor's hostBehaviors (or the fallback floor
    when it declares none); known non-registry id -> {}; registry failed to load -> the floor
    for the ids it covers, else {}; any other id -> {}. ``registry`` is injectable: a mapping
    with a ``runtimes`` key, or None to simulate a registry that failed to load.
    """
    if not isinstance(runtime, str) or not runtime:
        return {}

    def floor():
        return FALLBACK_HOST_BEHAVIORS[runtime] if runtime in FALLBACK_HOST_BEHAVIORS else {}

    if registry is _UNSET:
        runtimes = _load_registry_runtimes()
    else:
        runtimes = registry.get("runtimes") if registry else None
    if runtimes is None:
        return floor()
    if runtime in runtimes:
        entry = runtimes[runtime]
        declared = ((entry or {}).get("runtime") or {}).get("hostBehaviors")
        return declared if declared is not None else floor()
    return {}


_FALLBACK_ALIASES = {
    "claude": ["claude", "claude-code", "claude-cli"],
    "opencode": ["opencode", "open-code", "opencode-cli"],
    "kilo": ["kilo", "kilo-cli"],
    "codex": ["codex", "codex-app", "codex-cli", "codex_desktop", "codex-desktop"],
    "copilot": ["copilot", "copilot-cli", "github-copilot"],
    "antigravity": ["antigravity", "antigravity-cli", "antigravity-agent"],
    "cursor": ["cursor", "cursor-cli", "cursor-nightly"],
    "windsurf": ["windsurf", "windsurf-cli", "windsurf-next", "devin-desktop"],
    "augment": ["augment", "augment-code", "augment-cli"],
    "trae": ["trae", "trae-cli"],
    "qwen": ["qwen", "qwen-code", "qwen-cli"],
    "hermes": ["hermes", "hermes-agent", "hermes-cli"],
    "kimi": ["kimi"],
    "kimi-code": ["kimi-code", "kimicode", "kimi_code"],
    "codebuddy": ["codebuddy", "codebuddy-cli"],
    "cline": ["cline", "cline-cli"],
}


def _normalize_runtime_token(value):
    return re.sub(r"[_\s]+", "-", str(value).strip().lower())


def _load_alias_manifest():
    here = Path(__file__).resolve().parent
    candidates = [here.parent/"shared"/"runtime-aliases.manifest.json",
                  here.parents[2]/"sdk"/"shared"/"runtime-aliases.manifest.json"]
    for manifest_path in candidates:
        try:
            parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                return parsed
        except (OSError, ValueError, IndexError):
            continue  # try next candidate
    return {key: list(value) for key, value in _FALLBACK_ALIASES.items()}


def _build_alias_index(manifest):
    index = {}
    for canonical, aliases in manifest.items():
        if not isinstance(canonical, str) or not isinstance(aliases, list):
            continue
        index[_normalize_runtime_token(canonical)] = _normalize_runtime_token(canonical)
        for alias in aliases:
            if isinstance(alias, str):
                index[_normalize_runtime_token(alias)] = _normalize_runtime_token(canonical)
    return index


_ALIAS_TO_CANONICAL = _build_alias_index(_load_alias_manifest())


def canonicalize_runtime_name(value):
    """Canonical runtime id for a known alias, or None (also None for non-strings)."""
    if not isinstance(value, str):
        return None
    return _ALIAS_TO_CANONICAL.get(_normalize_runtime_token(value)) or None


def resolve_runtime_name_from_candidates(*candidates):
    """First non-empty string candidate wins; known aliases canonicalize, unknown ones normalize."""
    for candidate in candidates:
        if not isinstance(candidate, str):
            continue
        normalized = _normalize_runtime_token(candidate)
        if not normalized:
            continue
        return canonicalize_runtime_name(normalized) or normalized
    return None


def get_project_instruction_file(runtime):
    """Project instruction file path (relative to the project root) for a runtime id.

    claude -> .claude/CLAUDE.md; copilot -> .github/copilot-instructions.md; a registered
    runtime's ``hostBehaviors.projectInstructionFile`` (antigravity -> GEMINI.md); every
    other runtime, unknown or future ids included -> AGENTS.md. Retired ids raise.
    """
    assert_not_retired_runtime(runtime)
    canonical = canonicalize_runtime_name(runtime)
    if canonical == "claude":
        return ".claude/CLAUDE.md"
    if canonical == "copilot":
        return ".github/copilot-instructions.md"
    from . import capability_registry
    declared = None
    if canonical:
        entry = capability_registry.RUNTIMES.get(canonical)
        declared = (((entry or {}).get("runtime") or {}).get("hostBehaviors") or {}).get("projectInstructionFile")
    if isinstance(declared, str) and declared:
        return declared
    return "AGENTS.md"


# Sentinel for a runtime whose descriptor declares configHome.kind == "none" (no local config dir).
NO_LOCAL_CONFIG_DIR_SENTINEL = "(no-local-config-dir)"


def get_dir_name(runtime):
    """On-disk local config directory name for a runtime id (unknown/empty -> '.claude')."""
    assert_known_runtime(runtime)
    if not runtime:
        return ".claude"
    from . import capability_registry
    entry = ((capability_registry.RUNTIMES.get(runtime) or {}).get("runtime")) or {}
    directory = entry.get("localConfigDir")
    if isinstance(directory, str) and directory:
        return directory
    if (entry.get("configHome") or {}).get("kind") == "none":
        return NO_LOCAL_CONFIG_DIR_SENTINEL
    return ".claude"


_RUNTIME_LABELS = {
    "claude": "Claude Code",
    "opencode": "OpenCode",
    "kilo": "Kilo",
    "codex": "Codex",
    "copilot": "Copilot",
    "antigravity": "Antigravity",
    "cursor": "Cursor",
    "windsurf": "Windsurf",
    "augment": "Augment",
    "trae": "Trae",
    "qwen": "Qwen Code",
    "hermes": "Hermes Agent",
    "kimi": "Kimi CLI",
    "kimi-code": "Kimi Code",
    "codebuddy": "CodeBuddy",
    "cline": "Cline",
    "zcode": "ZCode",
    "pi": "pi",
    "vscode": "VS Code",
}


def get_runtime_label(runtime):
    """Short display label for a runtime id (unknown/empty -> 'Claude Code')."""
    assert_known_runtime(runtime)
    if not runtime:
        return "Claude Code"
    label = _RUNTIME_LABELS.get(runtime)
    return label if isinstance(label, str) and label else "Claude Code"


_DEFAULT_CONFIG_HOME_FRAGMENT = "'.claude'"
_GLOBAL_CONFIG_HOME_FRAGMENTS = {
    "copilot": "'.copilot'",
    "opencode": "'.config', 'opencode'",
    "kilo": "'.config', 'kilo'",
    "codex": "'.codex'",
    "cursor": "'.cursor'",
    "windsurf": "'.windsurf'",
    "augment": "'.augment'",
    "trae": "'.trae'",
    "qwen": "'.qwen'",
    "hermes": "'.hermes'",
    "codebuddy": "'.codebuddy'",
    "cline": "'.cline'",
    "kimi": "'.config', 'agents'",
    "kimi-code": "'.kimi-code'",
    "zcode": "'.zcode'",
    "pi": "'.pi', 'agent'",
}


def get_global_config_home_fragment(runtime):
    """Global config-home path-fragment source snippet (hook path.join codegen).

    claude/unknown/empty -> the default ``'.claude'`` fragment; antigravity is resolved by the
    caller, not here.
    """
    assert_known_runtime(runtime)
    if not runtime:
        return _DEFAULT_CONFIG_HOME_FRAGMENT
    fragment = _GLOBAL_CONFIG_HOME_FRAGMENTS.get(runtime)
    return fragment if isinstance(fragment, str) and fragment else _DEFAULT_CONFIG_HOME_FRAGMENT


_RUNTIME_FLAG_IDS = (
    "opencode", "kilo", "codex", "copilot", "antigravity", "cursor",
    "windsurf", "augment", "trae", "qwen", "hermes", "codebuddy", "cline", "kimi", "kimi-code", "zcode", "pi",
)


def _runtime_id_to_flag_name(runtime_id):
    return "is" + runtime_id[:1].upper() + re.sub(r"-([a-z])", lambda match: match.group(1).upper(), runtime_id[1:])


def runtime_flags(runtime):
    """Read-only map of ``is<Runtime>`` booleans for a runtime id (e.g. ``flags['isOpencode']``)."""
    return MappingProxyType({_runtime_id_to_flag_name(runtime_id): runtime == runtime_id for runtime_id in _RUNTIME_FLAG_IDS})
