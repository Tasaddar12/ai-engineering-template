"""Omit-when-inherit guard for workflow model dispatch.

Ported from upstream gsd-core ``tests/model-omit-when-inherit-guard.test.cjs``
at commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).
Rule owner: ``engineer/references/model-profile-resolution.md``.

Workflow orchestrators must omit the ``model=`` parameter from ``Agent()`` calls
when the bound ``*_model`` value is ``inherit`` or empty, every ``model="{X}"``
placeholder must name a field its own workflow binds, and every spawned agent
must have a model resolution behind it. Each check returns a list of findings;
an empty list means the rule holds.

Deviations:
- ``gsd-core/workflows`` -> ``engineer/workflows``;
  ``gsd-core/references/model-profile-resolution.md`` ->
  ``engineer/references/model-profile-resolution.md``;
  ``gsd_run`` -> ``engineer_run``; ``gsd-<agent>`` -> ``<agent>`` (names come
  from ``agents/*.md``).
- Agent names carry no ``gsd-`` prefix here, so the spawn collector matches only
  names that exist in ``agents/``: the dispatch shape ``subagent_type="<name>"``
  and the prose shape ``spawn `<name>``` (backticks required, since an unprefixed
  name such as ``planner`` is ordinary prose otherwise).
- ``readWorkflowCombined`` -> :func:`read_workflow_combined` (host plus
  ``<workflow>/steps/*.md``); Python text mode already normalizes CRLF.
- ``runGsdTools query <surface>`` -> ``engineer.py query <surface>`` run inside a
  throwaway git project; a non-zero exit or non-JSON payload is inconclusive.
- ``pattern.cjs`` ``escapeRegex`` -> :func:`re.escape`.
- The omit-rule marker is ``<!-- model-omit-on-inherit -->`` (shipped content here carries
  no issue-number prefix).
- The ``resolve-model <unknown-agent>`` -> empty string check is not ported: this
  runtime has no ``MODEL_PROFILES`` table or ``unknown_agent`` flag and raises
  ``agent-not-found`` instead (see the test module's skip).
- The fast-check property tests use a seeded stdlib generator in the test module.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

SOURCE = Path(__file__).resolve().parents[3]
WORKFLOWS = SOURCE/"engineer/workflows"
AGENTS = SOURCE/"agents"
RUNTIME = SOURCE/"engineer/bin/engineer.py"
MODEL_REFERENCE = SOURCE/"engineer/references/model-profile-resolution.md"

OMIT_RULE_MARKER = "<!-- model-omit-on-inherit -->"
MODEL_PLACEHOLDER_RE = re.compile(r'model="\{([A-Za-z0-9_]+)\}"')
MODEL_SITE_RE = re.compile(r'model="\{')


def read_workflow_combined(workflow_path):
    """Host workflow text plus its ``<wf>/steps/*.md`` fragments, in sorted order."""
    workflow_path = Path(workflow_path)
    combined = workflow_path.read_text(encoding="utf-8")
    steps = workflow_path.parent/workflow_path.stem/"steps"
    if steps.is_dir():
        for entry in sorted(steps.iterdir(), key=lambda p: p.name):
            if entry.name.endswith(".md"):
                combined += "\n"+entry.read_text(encoding="utf-8")
    return combined


def workflow_files(workflows_dir=WORKFLOWS):
    return sorted(p.name for p in Path(workflows_dir).iterdir() if p.is_file() and p.name.endswith(".md"))


def states_omit_rule(content):
    """True when the body states the omit-on-inherit rule (marker or inline wording)."""
    if OMIT_RULE_MARKER in content:
        return True
    near = re.search(r"omit.{0,200}model=|model=.{0,200}omit", content, re.I | re.S)
    return bool(near) and bool(re.search("inherit", content, re.I))


def workflows_that_dispatch_with_a_model(workflows_dir=WORKFLOWS):
    """(file, combined content) for every workflow that emits a ``model="{...}"`` site."""
    pairs = ((name, read_workflow_combined(Path(workflows_dir)/name)) for name in workflow_files(workflows_dir))
    return [(name, content) for name, content in pairs if MODEL_SITE_RE.search(content)]


def workflows_missing_omit_rule(workflows_dir=WORKFLOWS):
    return [name for name, content in workflows_that_dispatch_with_a_model(workflows_dir) if not states_omit_rule(content)]


# --- placeholder binding ----------------------------------------------------

def extract_model_placeholders(content):
    return MODEL_PLACEHOLDER_RE.findall(content)


def shell_assigned_names(content):
    return set(re.findall(r"^[ \t]*([A-Za-z0-9_]+)=\$\(", content, re.M))


def queried_init_surfaces(content):
    dotted = re.findall(r"query\s+(init\.[a-z0-9-]+)", content)
    suffixed = re.findall(r"query\s+([a-z0-9-]+-init)\b", content)
    return list(dict.fromkeys(dotted+suffixed))


_PARSE_HEAD = r"(?:Parse JSON for|Parse from init JSON|Extract from init JSON)"


def declared_parse_names(content):
    names = set()
    for line in re.findall(r"^.*"+_PARSE_HEAD+r".*$", content, re.I | re.M):
        names.update(re.findall(r"`([A-Za-z0-9_]+)`", line))
    for match in re.finditer(_PARSE_HEAD+r"[^\n]*\n((?:[ \t]*[-*][^\n]*\n)+)", content, re.I):
        names.update(re.findall(r"`([A-Za-z0-9_]+)`", match.group(1)))
    return names


def make_init_resolver(runtime=RUNTIME):
    """Return ``resolve(surface)`` -> set of payload keys or None, with caching.

    Surfaces run inside a throwaway git project so the real checkout is never
    touched. None means the surface needs arguments we cannot supply or printed
    a non-JSON payload: inconclusive, not proof of absence.
    """
    cache = {}
    holder = {}

    def project():
        if "dir" not in holder:
            holder["tmp"] = tempfile.TemporaryDirectory()
            root = Path(holder["tmp"].name)
            for args in (["init", "-q", "-b", "main"], ["config", "user.name", "Guard"],
                         ["config", "user.email", "guard@example.invalid"]):
                subprocess.run(["git", *args], cwd=root, capture_output=True, check=True)
            holder["dir"] = root
        return holder["dir"]

    def resolve(surface):
        if surface in cache:
            return cache[surface]
        keys = None
        root = project()
        env = {**os.environ, "ENGINEER_ROOT": str(root), "ENGINEER_HOST": "claude"}
        try:
            process = subprocess.run([sys.executable, "-I", str(runtime), "query", surface], cwd=root, env=env,
                                     text=True, capture_output=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            process = None
        if process is not None and process.returncode == 0:
            try:
                payload = json.loads(process.stdout)
                if isinstance(payload, dict):
                    keys = set(payload)
            except ValueError:
                keys = None
        cache[surface] = keys
        return keys

    resolve.close = lambda: holder["tmp"].cleanup() if "tmp" in holder else None
    return resolve


def bound_model_names(content, resolve_init):
    bound = shell_assigned_names(content) | declared_parse_names(content)
    for surface in queried_init_surfaces(content):
        keys = resolve_init(surface)
        if keys:
            bound.update(keys)
    return bound


def unbound_model_placeholders(content, resolve_init):
    placeholders = list(dict.fromkeys(extract_model_placeholders(content)))
    if not placeholders:
        return []
    bound = bound_model_names(content, resolve_init)
    return [name for name in placeholders if name not in bound]


def unbound_placeholder_findings(workflows_dir, resolve_init):
    """(findings, scanned file count, placeholder count) over bare host files."""
    findings, scanned, placeholders = [], 0, 0
    for name in workflow_files(workflows_dir):
        content = (Path(workflows_dir)/name).read_text(encoding="utf-8")
        found = extract_model_placeholders(content)
        if not found:
            continue
        scanned += 1
        placeholders += len(found)
        for unbound in unbound_model_placeholders(content, resolve_init):
            findings.append('%s: model="{%s}" - no init payload key, shell assignment, or declared parse '
                            "field of that name. The substitution has no source, so the orchestrator "
                            "invents a value." % (name, unbound))
    return findings, scanned, placeholders


# --- spawn coverage ---------------------------------------------------------

def agent_names(agents_dir=AGENTS):
    """Agent role names from ``agents/*.md`` (the ``AGENT.md`` template excluded)."""
    return tuple(sorted((p.stem for p in Path(agents_dir).glob("*.md") if p.stem != "AGENT"), key=lambda n: (-len(n), n)))


_AGENT_CACHE = {}


def _default_agents():
    if "names" not in _AGENT_CACHE:
        _AGENT_CACHE["names"] = agent_names()
    return _AGENT_CACHE["names"]


def spawned_agent_types(content, agents=None):
    """Agent types this workflow spawns, by dispatch shape or backticked prose shape."""
    names = tuple(sorted(agents if agents is not None else _default_agents(), key=lambda n: (-len(n), n)))
    if not names:
        return []
    alternation = "|".join(re.escape(n) for n in names)
    dispatch = re.findall(r'subagent_type[=:]\s*"?('+alternation+r')(?![A-Za-z0-9_-])"?', content)
    prose = re.findall(r"(?<![a-z] )\bspawn(?:s|ing)?\s+`("+alternation+r")(?![A-Za-z0-9_-])", content, re.I)
    return list(dict.fromkeys(dispatch+prose))


def model_ref_names(content):
    braced = MODEL_PLACEHOLDER_RE.findall(content)
    bare = re.findall(r"model=([A-Za-z_][A-Za-z0-9_]*)", content)
    return list(dict.fromkeys(braced+bare))


def uncovered_spawned_agents(content, resolve_init, agents=None):
    spawned = spawned_agent_types(content, agents)
    if not spawned:
        return []
    bound = bound_model_names(content, resolve_init)
    carries_resolution = any(n in bound for n in model_ref_names(content)) or any(re.search(r"_model$", n, re.I) for n in bound)
    uncovered = []
    for agent in spawned:
        direct = re.search(r"resolve-model\s+[\"'`]?"+re.escape(agent)+r"[\"'`]?", content)
        if not (direct or carries_resolution):
            uncovered.append(agent)
    return uncovered


def spawn_coverage_findings(workflows_dir, resolve_init, agents=None):
    """(findings, spawning file count, covered spawn count) over combined workflow text."""
    findings, spawning, covered = [], 0, 0
    for name in workflow_files(workflows_dir):
        content = read_workflow_combined(Path(workflows_dir)/name)
        spawned = spawned_agent_types(content, agents)
        if not spawned:
            continue
        spawning += 1
        uncovered = uncovered_spawned_agents(content, resolve_init, agents)
        covered += len(spawned)-len(uncovered)
        for agent in uncovered:
            findings.append("%s: spawns %s with no model resolution - neither a `resolve-model %s` binding "
                            "nor a bound model= reference. The spawn silently inherits the caller's model, "
                            "ignoring the configured model profile." % (name, agent, agent))
    return findings, spawning, covered


# --- reference document and ship hook gate ----------------------------------

def reference_violations(content, label="model-profile-resolution.md"):
    findings = []
    if re.search(r'model="inherit"', content):
        findings.append('%s: must not instruct passing model="inherit"; an inherit/empty model 404s on '
                        "non-Claude runtimes and must be OMITTED instead." % label)
    if re.search(r'model="\{resolved_model\}"', content):
        findings.append('%s: must not ship a copy-pasteable model="{resolved_model}"; no init payload emits '
                        "that field." % label)
    if not re.search("omit", content, re.I):
        findings.append("%s: must state the omit-on-inherit/empty rule." % label)
    return findings
