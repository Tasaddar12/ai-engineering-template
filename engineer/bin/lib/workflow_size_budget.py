"""Workflow size budget, progressive-disclosure and prompt-embed guards.

Ported from upstream gsd-core ``tests/workflow-size-budget.test.cjs`` and its
measurement helper ``scripts/workflow-size.cjs`` at commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).

Workflow definitions are loaded verbatim into an agent's context on every
invocation, so each top-level workflow is measured in LF-normalized bytes and
held under a tier hard cap. Per-mode bodies are extracted lazily
(``<workflow>/modes``, ``<workflow>/steps``, ``<workflow>/templates``) and must not be
eagerly ``@``-imported. Every check returns a list of violation strings; an empty
list means the rule holds.

Deviations:
- ``gsd-core/workflows`` -> ``engineer/workflows``; ``agents/gsd-<name>.md`` ->
  ``agents/<name>.md``; ``commands/gsd/`` -> ``commands/``.
- Tier membership keeps the upstream stems verbatim; stems with no file here
  (autonomous, transition, discuss-phase-assumptions, review) are inert.
- The ``execute-plan.md`` build-time embed path is ``engineer/workflows/execute-plan.md``
  (backticked, no ``@`` sigil) rather than ``~/.claude/gsd-core/workflows/execute-plan.md``.
- Shipped content here carries no issue-number citations, so the ``#3370`` and
  ``#3324`` citation assertions are dropped; the behavioral assertions remain.
- ``GITHUB_STEP_SUMMARY`` reporting and the fast-check properties are kept
  (the latter as seeded stdlib generators in the test module).
"""
import math
import os
from pathlib import Path
import re
import sys

SOURCE = Path(__file__).resolve().parents[3]
WORKFLOWS_DIR = SOURCE/"engineer/workflows"
AGENTS_DIR = SOURCE/"agents"

XL_CAP = 98304       # 96 KiB
LARGE_CAP = 61440    # 60 KiB
DEFAULT_CAP = 40960  # 40 KiB
DISCUSS_PHASE_TARGET = 32000
MARGIN_RATIO = 0.95

XL_WORKFLOWS = frozenset({"execute-phase", "plan-phase", "new-project"})
LARGE_WORKFLOWS = frozenset({
    "docs-update", "autonomous", "complete-milestone", "verify-work", "transition",
    "discuss-phase-assumptions", "progress", "new-milestone", "update", "quick", "code-review", "review",
})

DISCUSS_EXPECTED_MODES = ("power", "all", "auto", "chain", "text", "batch", "analyze", "default", "advisor")
DISCUSS_EXPECTED_TEMPLATES = ("context.md", "discussion-log.md", "checkpoint.json")
CONTEXT_SECTIONS = ("<domain>", "<decisions>", "<canonical_refs>", "<code_context>", "<specifics>", "<deferred>")
CHECKPOINT_KEYS = ("phase", "phase_name", "timestamp", "areas_completed", "areas_remaining", "decisions")

BARE_INCLUDE_LINE = re.compile(r"^\s*@(\$HOME|~)/")
ANTI_AUTO_APPROVAL = re.compile(r"never auto-approve|do not auto-approve|must not auto-approve|under any circumstance, including")


# --- measurement ------------------------------------------------------------

def lf_byte_count(path):
    """UTF-8 byte length of a file as counted on an LF checkout."""
    content = Path(path).read_bytes().decode("utf-8").replace("\r\n", "\n")
    return len(content.encode("utf-8"))


def list_workflow_stems(directory=WORKFLOWS_DIR):
    """Sorted stems of top-level ``*.md`` files; never recurses."""
    return sorted(p.name[:-3] for p in Path(directory).iterdir() if p.is_file() and p.name.endswith(".md"))


def measure_md_files(directory, predicate=lambda name: True):
    names = sorted(p.name for p in Path(directory).iterdir() if p.is_file() and p.name.endswith(".md") and predicate(p.name))
    return {name: lf_byte_count(Path(directory)/name) for name in names}


def measure_workflows(directory=WORKFLOWS_DIR):
    return measure_md_files(directory)


def cap_for(workflow):
    if workflow in XL_WORKFLOWS:
        return {"tier": "XL", "cap": XL_CAP}
    if workflow in LARGE_WORKFLOWS:
        return {"tier": "LARGE", "cap": LARGE_CAP}
    return {"tier": "DEFAULT", "cap": DEFAULT_CAP}


def tier_cap_violations(sizes, cap_lookup=cap_for):
    """Messages for every file whose byte count exceeds its tier hard cap."""
    findings = []
    for file, size in sizes.items():
        stem = file[:-3] if file.endswith(".md") else file
        tier = cap_lookup(stem)
        if size > tier["cap"]:
            findings.append("%s is %d bytes - exceeds the %s hard cap of %d. The cap is a red line, not a budget "
                            "to raise: extract per-mode bodies to workflows/%s/modes/, templates to "
                            "workflows/%s/templates/, or shared references to engineer/references/ and load "
                            "them lazily." % (file, size, tier["tier"], tier["cap"], stem, stem))
    return findings


# --- headroom census --------------------------------------------------------

def margin_for(cap):
    """Reserved-margin threshold in bytes: floor, so it never reaches the cap."""
    return math.floor(cap*MARGIN_RATIO)


def build_headroom_rows(sizes, cap_lookup):
    rows = []
    for file, size in sizes.items():
        name = file[:-3] if file.endswith(".md") else file
        tier = cap_lookup(name)
        margin = margin_for(tier["cap"])
        rows.append({"name": name, "tier": tier["tier"], "bytes": size, "cap": tier["cap"], "margin": margin,
                     "headroom": tier["cap"]-size, "usedPct": size/tier["cap"]*100, "overMargin": size > margin})
    return sorted(rows, key=lambda row: (row["headroom"], row["name"]))


def format_headroom_table(rows, limit=None):
    shown = rows if limit is None else rows[:limit]
    width = max([4]+[len(r["name"]) for r in shown])
    head = "  ".join(["file".ljust(width), "tier".ljust(7), "bytes".rjust(7), "cap".rjust(7), "margin".rjust(7),
                      "headroom".rjust(8), "used".rjust(6)])
    body = ["  ".join([r["name"].ljust(width), r["tier"].ljust(7), str(r["bytes"]).rjust(7), str(r["cap"]).rjust(7),
                       str(r["margin"]).rjust(7), str(r["headroom"]).rjust(8), ("%.1f" % r["usedPct"]).rjust(5)+"%"])
            for r in shown]
    return [head]+body


def build_headroom_summary_markdown(title, rows):
    pressured = [r for r in rows if r["overMargin"]]
    percent = round(MARGIN_RATIO*100)
    lines = ["### "+title, ""]
    if not pressured:
        lines.append("All %d files are under the %d%% reserved margin." % (len(rows), percent))
        return "\n".join(lines)+"\n"
    lines += ["**%d of %d** files are over the %d%% reserved margin." % (len(pressured), len(rows), percent), "",
              "| file | tier | bytes | cap | headroom | used |", "| --- | --- | ---: | ---: | ---: | ---: |"]
    for r in pressured:
        lines.append("| `%s` | %s | %d | %d | %d | %.1f%% |" % (r["name"], r["tier"], r["bytes"], r["cap"], r["headroom"], r["usedPct"]))
    return "\n".join(lines)+"\n"


def append_headroom_step_summary(title, rows, env=None):
    """Append the census to ``$GITHUB_STEP_SUMMARY`` when set; never raises."""
    env = os.environ if env is None else env
    target = env.get("GITHUB_STEP_SUMMARY")
    if not target:
        return False
    try:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(build_headroom_summary_markdown(title, rows)+"\n")
        return True
    except OSError as exc:
        sys.stderr.write("workflow-size: could not write GITHUB_STEP_SUMMARY: %s\n" % exc)
        return False


# --- discuss-phase progressive disclosure -----------------------------------

def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def required_reading_block(content):
    """Body of the first ``<required_reading>`` block, or None."""
    match = re.search(r"<required_reading>(.*?)</required_reading>", content, re.S)
    return match.group(1) if match else None


def discuss_phase_budget_violations(path, target=DISCUSS_PHASE_TARGET):
    size = lf_byte_count(path)
    if size < target:
        return []
    return ["%s is %d bytes - must be under %d. Per-mode logic belongs in workflows/discuss-phase/modes/<mode>.md, "
            "templates in workflows/discuss-phase/templates/." % (Path(path).name, size, target)]


def missing_files(directory, names):
    return [name for name in names if not (Path(directory)/name).exists()]


def stub_mode_files(modes_dir, minimum=100):
    """Mode files whose stripped content is not longer than ``minimum`` characters."""
    return [p.name for p in sorted(Path(modes_dir).iterdir())
            if p.is_file() and p.name.endswith(".md") and len(p.read_text(encoding="utf-8").strip()) <= minimum]


def referenced_mode_files(parent_content):
    """Mode names the parent workflow dispatches to via ``discuss-phase/modes/<name>.md``."""
    return list(dict.fromkeys(re.findall(r"discuss-phase/modes/([A-Za-z0-9_-]+)\.md", parent_content)))


def mode_dispatch_violations(parent, modes):
    findings = []
    for mode in modes:
        if not re.search(r"discuss-phase/modes/%s\.md" % re.escape(mode), parent):
            findings.append("Parent discuss-phase.md must reference workflows/discuss-phase/modes/%s.md" % mode)
    return findings


def context_template_lazy_violations(parent):
    findings = []
    block = required_reading_block(parent)
    if block is not None and re.search(r"discuss-phase/templates/context\.md", block):
        findings.append("CONTEXT.md template must NOT be in <required_reading> - that defeats lazy loading.")
    if not re.search(r"discuss-phase/templates/context\.md", parent):
        findings.append("Parent must reference workflows/discuss-phase/templates/context.md inside the write_context step.")
    return findings


def advisor_gate_violations(parent):
    findings = []
    if not re.search(r"USER-PROFILE\.md", parent):
        findings.append("Parent must reference USER-PROFILE.md to detect advisor mode.")
    guarded = (re.search(r"test\s+-[ef]\s+[\"'$].*USER-PROFILE", parent) or re.search(r"\[\[\s+-[ef]\s+[\"'$].*USER-PROFILE", parent)
               or re.search(r"\[\s+-[ef]\s+[\"'$].*USER-PROFILE", parent))
    if not guarded:
        findings.append("Advisor mode detection must use a file-existence guard (test -f / [ -f ]).")
    advisor_read = (re.search(r"ADVISOR_MODE.{0,200}?modes/advisor\.md", parent, re.S)
                    or re.search(r"modes/advisor\.md.{0,200}?ADVISOR_MODE", parent, re.S)
                    or re.search(r"if.{0,200}?ADVISOR_MODE.{0,400}?advisor\.md", parent, re.S))
    if not advisor_read:
        findings.append("Read of modes/advisor.md must be guarded by ADVISOR_MODE.")
    return findings


def mode_content_violations(mode, content):
    """Behavior-preservation regexes for each extracted discuss-phase mode body."""
    rules = {
        "auto-skip": (r"skip.{0,80}interactive|without\s+(?:using\s+)?AskUserQuestion|recommended\s+(?:option|default)", re.I | re.S),
        "auto-cap": (r"single\s+pass|max_discuss_passes|MAX_PASSES|pass\s+cap", re.I),
        "all": (r"auto-select(?:ed)?\s+ALL|select\s+ALL|all\s+gray\s+areas", re.I),
        "batch": (r"2[-\s–]5|2\s+to\s+5|--batch=N|--batch\s+N", 0),
        "analyze": (r"trade[-\s]off|tradeoff|pros.{0,30}cons", re.I | re.S),
    }
    flags = rules[mode][1]
    if re.search(rules[mode][0], content, flags):
        return []
    return ["%s mode body lost its documented behavior (%s)." % (mode, rules[mode][0])]


def chain_mode_violations(content):
    if re.search("plan-phase", content) and re.search(r"(auto-advance|auto\s+plan)", content, re.I):
        return []
    return ["chain.md must preserve the documented auto-advance to plan-phase behavior."]


def text_mode_violations(content):
    if re.search("AskUserQuestion", content) and re.search(r"(numbered\s+list|plain[-\s]text)", content, re.I):
        return []
    return ["text.md must preserve the rule: replace AskUserQuestion with plain-text numbered lists."]


def context_template_violations(content):
    findings = ["CONTEXT.md template missing required section %s" % s for s in CONTEXT_SECTIONS if s not in content]
    if not re.search("spec_lock", content, re.I):
        findings.append("CONTEXT.md template must document the conditional <spec_lock> section.")
    return findings


def checkpoint_template_violations(raw):
    import json
    try:
        parsed = json.loads(raw)
    except ValueError as exc:
        return ["checkpoint.json template must parse as valid JSON: %s" % exc]
    if not isinstance(parsed, dict):
        return ["checkpoint.json template must be a JSON object"]
    return ['checkpoint.json template missing required field "%s"' % k for k in CHECKPOINT_KEYS if k not in parsed]


def inline_discussion_log_occurrences(parent):
    return len(re.findall(r"\| Option \| Description \| Selected \|", parent))


def dispatch_flag_present(parent):
    return bool(re.search(r"ARGUMENTS|--auto|--chain|--all|--power", parent))


# --- lazy MVP bodies --------------------------------------------------------

def eager_import_violations(content, body_name, label):
    """An ``@``-sigil path ending in ``body_name`` expands into context on load."""
    if re.search(r"@[~./\w-]*"+re.escape(body_name), content, re.A):
        return ["%s contains an eager @-import of %s - this loads the body into context for every session. "
                "Replace with a conditional Read instruction or a plain backtick path." % (label, body_name)]
    return []


def lazy_reference_violations(content, body_name, label):
    if re.search(re.escape(body_name), content):
        return []
    return ["%s must still reference %s (as a lazy path or Read instruction)." % (label, body_name)]


def required_reading_leak_violations(content, body_names, label):
    block = required_reading_block(content)
    if block is None:
        return []
    return ["%s must NOT appear in %s <required_reading> - that block is always loaded." % (name, label)
            for name in body_names if re.search(re.escape(name), block)]


def reference_body_exists(name, roots=(SOURCE/"engineer", SOURCE/"agents")):
    """True when a file with this name exists under any of the roots."""
    return any(next(Path(root).rglob(name), None) is not None for root in roots if Path(root).is_dir())


# --- Agent() prompt @-include scan ------------------------------------------

def list_workflow_files_recursive(directory=WORKFLOWS_DIR):
    return sorted(p for p in Path(directory).rglob("*.md") if p.is_file())


def bare_include_lines_in_prompt_regions(content):
    """Lines of ``@$HOME/`` / ``@~/`` includes inside ``prompt="`` ... ``"`` regions."""
    hits, in_prompt = [], False
    for number, line in enumerate(content.split("\n"), 1):
        if not in_prompt and re.search(r'prompt="\s*$', line):
            in_prompt = True
            continue
        if in_prompt and re.search(r'^\s*"\s*$', line):
            in_prompt = False
            continue
        if in_prompt and BARE_INCLUDE_LINE.search(line):
            hits.append({"line": number, "text": line.strip()})
    return hits


def bare_include_offenders(directory=WORKFLOWS_DIR, repo_root=SOURCE):
    offenders = []
    for path in list_workflow_files_recursive(directory):
        try:
            shown = path.relative_to(repo_root).as_posix()
        except ValueError:
            shown = path.as_posix()
        for hit in bare_include_lines_in_prompt_regions(path.read_text(encoding="utf-8")):
            offenders.append("%s:%d %s" % (shown, hit["line"], hit["text"]))
    return offenders


def execution_context_block(content):
    match = re.search(r"<execution_context>(.{0,4000}?)</execution_context>", content, re.S)
    return match.group(1) if match else None


def execution_context_violations(content, embed_path):
    block = execution_context_block(content)
    if block is None:
        return ["execute-phase.md must keep an <execution_context> block in the executor dispatch prompt"]
    findings = []
    if not re.search("ORCHESTRATOR build-time embed", block):
        findings.append("<execution_context> must carry the ORCHESTRATOR build-time embed instruction")
    if "`%s`" % embed_path not in block:
        findings.append("<execution_context> must list %s (backticked, no @ sigil) for build-time embed" % embed_path)
    return findings


def dispatch_region(content, from_anchor, to_anchor):
    """Text from ``from_anchor`` up to the next ``to_anchor``; ValueError when an anchor is missing."""
    start = content.find(from_anchor)
    if start == -1:
        raise ValueError('anchor "%s" not found' % from_anchor)
    end = content.find(to_anchor, start)
    if end == -1:
        raise ValueError('anchor "%s" not found after "%s"' % (to_anchor, from_anchor))
    return content[start:end]


def gate_routing_fragment_violations(fragment):
    findings = []
    if not re.search(r'gate="blocking"', fragment):
        findings.append('the gate rule must name gate="blocking"')
    if not re.search(r"auto-approv", fragment, re.I):
        findings.append("the gate rule must state blocking is auto-approvable in auto-mode")
    if not re.search("blocking-human", fragment):
        findings.append('the gate rule must name gate="blocking-human" as the always-surface carve-out')
    if not re.search(r"do NOT add text refusing or overriding\s+auto-approval", fragment):
        findings.append("the gate rule must forbid composing dispatch text that refuses or overrides auto-approval")
    findings += anti_auto_approval_violations(fragment, "the gate rule")
    return findings


def anti_auto_approval_violations(text, label):
    if ANTI_AUTO_APPROVAL.search(text):
        return ["%s must not contain anti-auto-approval instructions" % label]
    return []


def pattern_a_violations(region):
    findings = []
    if not re.search(r'gate="blocking"', region):
        findings.append('Pattern A must name gate="blocking"')
    if not re.search("blocking-human", region):
        findings.append('Pattern A must name gate="blocking-human"')
    if not re.search(r"auto-approv", region, re.I):
        findings.append("Pattern A must state blocking is auto-approvable in auto-mode")
    if not re.search(r"no instruction (?:that )?overrid", region, re.I):
        findings.append("Pattern A must forbid adding instructions that override the executor checkpoint protocol")
    findings += anti_auto_approval_violations(region, "Pattern A")
    return findings


def missing_markers(content, markers):
    return [marker for marker in markers if marker not in content]
