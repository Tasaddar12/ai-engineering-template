"""Generate the ``<error_codes>`` and ``<repair_actions>`` tables of ``engineer/workflows/health.md``.

Port of ``scripts/gen-health-docs.cjs`` from gsd-core at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).

The tables are projected from ``health_diagnostic.RULES`` (each rule carries a static
``description`` / ``repairable``), the three pre-check codes that stay outside the rule table
(``E001``, ``E010``, ``I010``) and the per-action Effect/Risk prose in ``REMEDY_ACTION_METADATA``.

Usage (from ``engineer/bin``)::

    python -m lib.gen_health_docs                       # print both tables to stdout
    python -m lib.gen_health_docs --write               # rewrite the tagged regions in health.md
    python -m lib.gen_health_docs --check               # exit 1 if either region is stale
    python -m lib.gen_health_docs --write --target <p>  # test-only: target a fixture file

Deviations:
- ``loadCompiledModule`` (``npm run build:lib`` artifact check) is replaced by importing
  ``health_diagnostic.RULES``; ``COMPILED_MODULE_*`` constants are not ported.
- The default target is ``engineer/workflows/health.md``.
- The ``--check`` remedy text names ``python -m lib.gen_health_docs --write``; the generated
  footnote paragraph is kept verbatim from upstream (it still names ``node scripts/gen-health-docs.cjs``,
  ``src/health-diagnostic.cts`` and ``#3309``), so a hand-edited footnote in ``health.md`` reads as drift.
- ``ExitError`` / ``runMain`` are inlined as a private ``_ExitError`` handled by ``main``.
- Rule descriptions come from the Python rule table verbatim, so wording the repo's ``health.md``
  localised (``Engineer`` for upstream ``GSD`` in W010, W019 and W028) reads as drift.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from .health_diagnostic import RULES

REPO_ROOT = Path(__file__).resolve().parents[3]
HEALTH_MD_REL = "engineer/workflows/health.md"
HEALTH_MD_PATH = REPO_ROOT / HEALTH_MD_REL

ERROR_CODES_START = "<error_codes>"
ERROR_CODES_END = "</error_codes>"
REPAIR_ACTIONS_START = "<repair_actions>"
REPAIR_ACTIONS_END = "</repair_actions>"

PRECHECK_CODES = (
    {"code": "E001", "severity": "error", "description": ".planning/ directory not found", "repairable": False},
    {"code": "E010", "severity": "error",
     "description": "CWD resolves to the user's home directory — health check would target the wrong .planning/", "repairable": False},
    {"code": "I010", "severity": "info", "description": "Resolved CWD reported alongside the E010 home-directory guard", "repairable": False},
)

REMEDY_ACTION_METADATA = {
    "createConfig": {"effect": "Create config.json with defaults", "risk": "None"},
    "resetConfig": {"effect": "Delete + recreate config.json", "risk": "Loses custom settings"},
    "regenerateState": {"effect": "Create STATE.md from ROADMAP structure when it is missing", "risk": "Loses session history"},
    "addNyquistKey": {"effect": "Add workflow.nyquist_validation: true to config.json", "risk": "None — matches existing default"},
    "addAiIntegrationPhaseKey": {"effect": "Add workflow.ai_integration_phase: true to config.json", "risk": "None — matches existing default"},
    "backfillMilestones": {
        "effect": "Synthesize missing MILESTONES.md entries from `.planning/milestones/vX.Y-ROADMAP.md` snapshots",
        "risk": "None — additive only; triggered by `--backfill` flag"},
    "repairVerificationStatus": {
        "effect": "Rewrite a known legacy verification `status` (`pass_with_caveats`) to `passed`, keeping the original as `legacy_status`",
        "risk": "None — only the `status` line changes; unknown statuses are never touched"},
}

REMEDY_ACTION_ORDER = ("createConfig", "resetConfig", "regenerateState", "addNyquistKey", "addAiIntegrationPhaseKey",
                       "backfillMilestones", "repairVerificationStatus")

REPAIRABLE_DISPLAY_OVERRIDE = {
    "W018": "Yes (`--backfill`)",
    "W030": "Yes (known legacy statuses only)",
}

STATIC_NOT_REPAIRABLE_BULLETS = ("PROJECT.md, ROADMAP.md content", "Phase directory renaming", "Orphaned plan cleanup")

FOOTNOTE_PARAGRAPH = (
    "Note: this table is **generated** — do not hand-edit it. It is produced by "
    "`node scripts/gen-health-docs.cjs --write` from `src/health-diagnostic.cts`'s `RULES` table "
    "(31 rules as of #3309, each carrying a static `description`/`repairable` on its `Rule` entry — "
    "see `src/health-diagnostic-types.cts`) plus the 3 pre-checks that stay outside the rule table by "
    "design (`E001`, `E010`, `I010` — safety rails in `cmdValidateHealth`, `src/verify.cts`, never "
    "`.planning/` findings). `scripts/lint-health-diagnostic-rule-table.cjs` already enforces the 1:1 "
    "code invariant this table depends on (no duplicate codes; severity is always a `Rule` property, "
    "never set per emit call) — before assigning a new code, add a `Rule` entry under "
    "`src/health-diagnostic-rules/` (its `code` is simply the next free number the lint guard has not "
    "yet seen) and run `node scripts/gen-health-docs.cjs --write` to regenerate this table; "
    "`npm run lint:generated-sync` fails if it drifts. `W025` (the `workflow.use_worktrees`/"
    "`dispatch.isolation` check, #2486) is a workflow-layer diagnostic emitted directly by this file's "
    "own `run_health_check` step, not by `cmdValidateHealth` — it stays documented in that step, not in "
    "this generated table.")

_PREFIX_RANK = {"E": 0, "W": 1, "I": 2}


class _ExitError(Exception):
    def __init__(self, code=1, message=None):
        super().__init__(message if message is not None else f"process exit {code}")
        self.code = code
        self.has_user_message = message is not None


def parse_code(code):
    match = re.match(r"^([A-Z]+)(\d+)\Z", code, re.ASCII)
    if not match:
        raise ValueError(f'gen-health-docs: unparseable diagnostic code "{code}"')
    return {"prefix": match.group(1), "number": int(match.group(2))}


def compare_codes(a, b):
    pa, pb = parse_code(a["code"]), parse_code(b["code"])
    rank_a, rank_b = _PREFIX_RANK.get(pa["prefix"], 99), _PREFIX_RANK.get(pb["prefix"], 99)
    if rank_a != rank_b:
        return rank_a - rank_b
    return pa["number"] - pb["number"]


def build_error_code_rows(rules):
    """Real rules plus the pre-check codes, sorted E-codes, W-codes numerically, then I-codes."""
    seen, rows = set(), []
    for entry in [*rules, *PRECHECK_CODES]:
        if entry["code"] in seen:
            raise ValueError(f'gen-health-docs: duplicate diagnostic code "{entry["code"]}" across RULES + PRECHECK_CODES')
        seen.add(entry["code"])
        rows.append(entry)
    rows.sort(key=lambda row: (_PREFIX_RANK.get(parse_code(row["code"])["prefix"], 99), parse_code(row["code"])["number"]))
    return rows


def cell_text(text):
    return (str(text).replace("\\", "\\\\").replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")
            .replace("\r\n", " ").replace("\n", " ").strip())


def repairable_cell(row):
    if row["code"] in REPAIRABLE_DISPLAY_OVERRIDE:
        return REPAIRABLE_DISPLAY_OVERRIDE[row["code"]]
    return "Yes" if row["repairable"] else "No"


def render_error_codes_region(rules):
    lines = ["", "| Code | Severity | Description | Repairable |", "|------|----------|-------------|------------|"]
    for row in build_error_code_rows(rules):
        lines.append(f"| {row['code']} | {row['severity']} | {cell_text(row['description'])} | {repairable_cell(row)} |")
    lines += ["", FOOTNOTE_PARAGRAPH, ""]
    return "\n".join(lines)


def render_repair_actions_region():
    lines = ["", "| Action | Effect | Risk |", "|--------|--------|------|"]
    for action in REMEDY_ACTION_ORDER:
        meta = REMEDY_ACTION_METADATA.get(action)
        if not meta:
            raise ValueError(f'gen-health-docs: no Effect/Risk metadata registered for repair action "{action}" '
                             "— add an entry to REMEDY_ACTION_METADATA.")
        lines.append(f"| {action} | {meta['effect']} | {meta['risk']} |")
    lines += ["", "**Not repairable (too risky):**"]
    lines += [f"- {bullet}" for bullet in STATIC_NOT_REPAIRABLE_BULLETS]
    lines.append("")
    return "\n".join(lines)


def splice_region(text, start_tag, end_tag, new_inner):
    """Replace the content between the first ``start_tag`` / ``end_tag`` pair; each tag must be unique."""
    start_idx, end_idx = text.find(start_tag), text.find(end_tag)
    if start_idx == -1 or end_idx == -1:
        raise _ExitError(1, f"gen-health-docs: {HEALTH_MD_REL} is missing the {start_tag}/{end_tag} tags.")
    if text.find(start_tag, start_idx + 1) != -1 or text.find(end_tag, end_idx + 1) != -1:
        raise _ExitError(1, f"gen-health-docs: {HEALTH_MD_REL} has more than one {start_tag}/{end_tag} pair.")
    return f"{text[:start_idx + len(start_tag)]}{new_inner}\n{text[end_idx:]}"


def regenerate_health_md(rules, current_text):
    out = splice_region(current_text, ERROR_CODES_START, ERROR_CODES_END, render_error_codes_region(rules))
    return splice_region(out, REPAIR_ACTIONS_START, REPAIR_ACTIONS_END, render_repair_actions_region())


def parse_args(argv):
    opts = {"write": False, "check": False, "targetPath": None}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--write":
            opts["write"] = True
        elif arg == "--check":
            opts["check"] = True
        elif arg == "--target":
            if i + 1 >= len(argv):
                raise _ExitError(1, "--target requires a path argument.")
            opts["targetPath"] = argv[i + 1]
            i += 1
        else:
            raise _ExitError(1, f"unknown flag: {arg}\nRecognized flags: --write, --check, --target <path>.")
        i += 1
    return opts


def _run(argv, rules):
    opts = parse_args(argv)
    resolved = Path(opts["targetPath"]).resolve() if opts["targetPath"] else HEALTH_MD_PATH
    display = opts["targetPath"] if opts["targetPath"] else HEALTH_MD_REL
    if not resolved.exists():
        raise _ExitError(1, f"gen-health-docs: {display} not found.")
    with open(resolved, "r", encoding="utf-8", newline="") as handle:
        current = handle.read()
    expected = regenerate_health_md(rules, current)
    count = len(rules) + len(PRECHECK_CODES)

    if opts["write"]:
        with open(resolved, "w", encoding="utf-8", newline="") as handle:
            handle.write(expected)
        sys.stdout.write(f"Wrote {display} — {count} error/warning/info code(s), {len(REMEDY_ACTION_ORDER)} repair action(s).\n")
        return 0

    if opts["check"]:
        if expected != current:
            sys.stderr.write(f"{display} is stale — its <error_codes>/<repair_actions> tables do not match "
                             "health_diagnostic.RULES.\nRun:\n  python -m lib.gen_health_docs --write\n\n")
            raise _ExitError(1)
        sys.stdout.write(f"{display} is up to date ({count} codes, {len(REMEDY_ACTION_ORDER)} repair actions).\n")
        return 0

    sys.stdout.write(render_error_codes_region(rules) + "\n\n" + render_repair_actions_region() + "\n")
    return 0


def main(argv=None, rules=None):
    """CLI entry point; ``rules`` defaults to ``health_diagnostic.RULES``. Returns the exit code."""
    try:
        return _run(list(sys.argv[1:] if argv is None else argv), RULES if rules is None else rules)
    except _ExitError as exc:
        if exc.has_user_message and exc.code != 0:
            sys.stderr.write(f"{exc}\n")
        return exc.code


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main())
