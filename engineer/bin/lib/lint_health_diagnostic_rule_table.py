"""Lint gate for the health-diagnostic rule table: the 1:1 code invariant and the fixture-proof invariant.

Port of ``scripts/lint-health-diagnostic-rule-table.cjs`` from gsd-core at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).

Checks (run from ``engineer/bin`` as ``python -m lib.lint_health_diagnostic_rule_table``):

1. 1:1 code invariant: every ``rule["code"]`` in ``health_diagnostic.RULES`` is unique and every
   rule's ``severity`` is a ``SEVERITY`` value (also applied to the ``C0NN`` rules of
   ``CONSISTENCY_RULES``).
2. Fixture-proof invariant: every rule code is named by a titled test block in the health-diagnostic
   test files (``tests/test_health_diagnostic*.py``); a comment or string mention does not count. Codes in
   ``PERMANENTLY_INERT_CODES`` (``W024``) are exempted and reported separately.
3. ``S0NN`` namespace: the code set is discovered from ``stateDiagnostic(...)`` call sites in the state
   validation source and checked against its test file. Fails closed when the source exists but yields no
   call sites.

Exit codes: 0 pass, 1 violation. Output matches upstream's ``PASS`` lines.

Deviations:
- The compiled-artifact load (``npm run build:lib``) is replaced by importing ``health_diagnostic``.
- A "titled block" is a Python ``class`` / ``def test*`` name, or (as upstream) a ``describe(`` / ``test(`` /
  ``it(`` call with a string title. Titles are matched case-insensitively with ``_`` as a token boundary, so
  ``test_w001_fires`` names ``W001``.
- Test files scanned are ``tests/test_health_diagnostic*.py``; the ``C0NN`` rules are proven against the same
  file (upstream used ``tests/health-diagnostic-rules/consistency.test.cjs``).
- ``S0NN`` discovery targets ``engineer/bin/lib/state_validate.py`` and ``tests/test_state_validate.py``
  (upstream ``src/state.cts`` / ``tests/state.test.cjs``). Neither exists in this repo, so the pass is
  reported as skipped instead of failing; ``STATE_VALIDATE_CODES`` is computed lazily by
  ``load_state_validate_codes`` rather than at import time.
- ``ExitError`` / ``runMain`` are inlined as a private ``_ExitError`` handled by ``main``.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_DIR = REPO_ROOT / "tests"
CONSISTENCY_TEST_FILE = TEST_DIR / "test_health_diagnostic.py"
CONSISTENCY_CODE_PREFIX_RE = re.compile(r"^C\d{3}\Z")
STATE_VALIDATE_TEST_FILE = TEST_DIR / "test_state_validate.py"
STATE_VALIDATE_SOURCE_FILE = REPO_ROOT / "engineer" / "bin" / "lib" / "state_validate.py"

STATE_DIAGNOSTIC_CALL_RE = re.compile(r"""\bstateDiagnostic\s*\(\s*(['"`])(S\d{3})\1""")
_JS_TITLED_BLOCK_RE = re.compile(r"""\b(describe|test|it)\(\s*(['"`])((?:\\.|(?!\2)[^\\])*)\2""")
_PY_TITLED_BLOCK_RE = re.compile(r"^[ \t]*(?:class[ \t]+(\w+)|(?:async[ \t]+)?def[ \t]+(test\w*))", re.M)

PERMANENTLY_INERT_CODES = {
    "W024": ("readStateHeadFreshness requires a git-log shell-out, forbidden ambient I/O for Rule.check "
             "(§8.1 rule 1) — the real check runs in cmdValidateHealth itself, outside the rule table "
             "(src/verify.cts). This rule-table entry is a permanent no-op by design, not a fixture gap."),
}


class _ExitError(Exception):
    def __init__(self, code=1, message=None):
        super().__init__(message if message is not None else f"process exit {code}")
        self.code = code
        self.has_user_message = message is not None


def format_repo_relative(path):
    try:
        return Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def discover_state_validate_codes(source_text, source_label=None):
    """Every ``S0NN`` code on a ``stateDiagnostic(...)`` call site; fails closed on an empty result."""
    codes = [match.group(2) for match in STATE_DIAGNOSTIC_CALL_RE.finditer(source_text)]
    unique = sorted(set(codes))
    if not unique:
        label = source_label if source_label is not None else format_repo_relative(STATE_VALIDATE_SOURCE_FILE)
        raise _ExitError(
            1,
            f"lint-health-diagnostic-rule-table: found no stateDiagnostic() call sites in {label}.\n"
            "  This pass discovers the S0NN code set from those call sites (#3696), so an empty\n"
            "  result means the helper was renamed or its call shape changed — not that there are\n"
            "  no codes. Update STATE_DIAGNOSTIC_CALL_RE to match the new shape.\n")
    return unique


def load_state_validate_codes(source_file=None):
    """Discovered ``S0NN`` codes, or ``None`` when the state validation source does not exist."""
    source = Path(source_file) if source_file is not None else STATE_VALIDATE_SOURCE_FILE
    if not source.is_file():
        return None
    return discover_state_validate_codes(source.read_text(encoding="utf-8"), format_repo_relative(source))


def check_one_to_one_invariant(rules, severity):
    """Return ``{"duplicates": [{code, count}], "badSeverities": [{code, severity}]}``."""
    severity_values = set(severity.values())
    counts, bad = {}, []
    for rule in rules:
        counts[rule["code"]] = counts.get(rule["code"], 0) + 1
        if rule["severity"] not in severity_values:
            bad.append({"code": rule["code"], "severity": rule["severity"]})
    return {"duplicates": [{"code": code, "count": count} for code, count in counts.items() if count > 1], "badSeverities": bad}


def extract_titled_blocks(text):
    """Titles of every ``describe(`` / ``test(`` / ``it(`` call and every Python ``class`` / ``def test*``."""
    titles = [match.group(3) for match in _JS_TITLED_BLOCK_RE.finditer(text)]
    titles += [match.group(1) or match.group(2) for match in _PY_TITLED_BLOCK_RE.finditer(text)]
    return titles


def code_appears_in_title(code, titles):
    """True when ``code`` is a whole token (case-insensitive) inside at least one title."""
    pattern = re.compile(r"(?:^|[^A-Za-z0-9])" + re.escape(code) + r"(?:$|[^A-Za-z0-9])", re.I)
    return any(pattern.search(f"|{title}|") for title in titles)


def find_health_diagnostic_test_files(repo_root=None):
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    tests = root / "tests"
    return sorted(tests.glob("test_health_diagnostic*.py")) if tests.is_dir() else []


def check_fixture_proof_invariant(rules, test_files, inert_codes=None):
    """Return ``{"uncovered": [...], "exempted": [...], "testFilesScanned": [...]}``."""
    inert = PERMANENTLY_INERT_CODES if inert_codes is None else inert_codes
    titles = []
    for file in test_files:
        titles.extend(extract_titled_blocks(Path(file).read_text(encoding="utf-8")))
    uncovered, exempted = [], []
    for rule in rules:
        if rule["code"] in inert:
            exempted.append(rule["code"])
        elif not code_appears_in_title(rule["code"], titles):
            uncovered.append(rule["code"])
    return {"uncovered": uncovered, "exempted": exempted, "testFilesScanned": list(test_files)}


def _problems(rules, consistency_rules, severity, test_files, state_codes, state_test_files):
    one = check_one_to_one_invariant(rules, severity)
    proof = check_fixture_proof_invariant(rules, test_files)
    consistency_new = [r for r in consistency_rules if CONSISTENCY_CODE_PREFIX_RE.match(r["code"])]
    c_one = check_one_to_one_invariant(consistency_new, severity)
    c_files = [CONSISTENCY_TEST_FILE] if CONSISTENCY_TEST_FILE.exists() else []
    c_proof = check_fixture_proof_invariant(consistency_new, c_files, {})
    s_uncovered = []
    if state_codes is not None:
        s_uncovered = check_fixture_proof_invariant([{"code": c} for c in state_codes], state_test_files, {})["uncovered"]

    problems = []
    if one["duplicates"]:
        listing = "\n".join(f"  {d['code']} ({d['count']} occurrences)" for d in one["duplicates"])
        problems.append(f"§8.2 rule 1 violated: {len(one['duplicates'])} duplicated rule code(s) in RULES "
                        f"(health_diagnostic.RULES):\n{listing}\n"
                        "  remedy: codes are append-only and 1:1 with a single Rule — rename or remove the duplicate.")
    if one["badSeverities"]:
        listing = "\n".join(f"  {b['code']}: severity={_js_json(b['severity'])}" for b in one["badSeverities"])
        problems.append(f"§8.2 rule 3 violated: {len(one['badSeverities'])} rule(s) with a severity not in SEVERITY's values:\n{listing}\n"
                        "  remedy: severity is a property of the RULE — set it to SEVERITY.ERROR/WARNING/INFO.")
    if proof["uncovered"]:
        scanned = "\n  ".join(format_repo_relative(f) for f in test_files)
        problems.append(f"§8.5 violated: {len(proof['uncovered'])} rule code(s) with no test block naming them "
                        f"(a comment or bare string mention does not count):\n  {', '.join(proof['uncovered'])}\n\n"
                        f"  Searched these test files:\n  {scanned}\n\n"
                        "  remedy: add or extend a test class / test method name in tests/test_health_diagnostic.py so the "
                        f"title names the code (e.g. def test_{proof['uncovered'][0].lower()}_fires), "
                        "and drive the rule to fire against a hand-built snapshot dict.")
    if c_one["duplicates"]:
        listing = "\n".join(f"  {d['code']} ({d['count']} occurrences)" for d in c_one["duplicates"])
        problems.append(f"§8.2 rule 1 violated (C0NN namespace): {len(c_one['duplicates'])} duplicated rule code(s) in "
                        f"CONSISTENCY_RULES (health_diagnostic.CONSISTENCY_RULES):\n{listing}\n"
                        "  remedy: codes are append-only and 1:1 with a single Rule — rename or remove the duplicate.")
    if c_one["badSeverities"]:
        listing = "\n".join(f"  {b['code']}: severity={_js_json(b['severity'])}" for b in c_one["badSeverities"])
        problems.append(f"§8.2 rule 3 violated (C0NN namespace): {len(c_one['badSeverities'])} rule(s) with a severity not "
                        f"in SEVERITY's values:\n{listing}\n"
                        "  remedy: severity is a property of the RULE — set it to SEVERITY.ERROR/WARNING/INFO.")
    if c_proof["uncovered"]:
        problems.append(f"§8.5 violated (C0NN namespace): {len(c_proof['uncovered'])} rule code(s) with no test block naming them "
                        f"(a comment or bare string mention does not count):\n  {', '.join(c_proof['uncovered'])}\n\n"
                        f"  Searched: {format_repo_relative(CONSISTENCY_TEST_FILE)}" + (" (file not found)" if not c_files else "") +
                        "\n\n  remedy: add or extend a test class / test method name in tests/test_health_diagnostic.py "
                        f"so the title names the code (e.g. def test_{c_proof['uncovered'][0].lower()}_fires).")
    if s_uncovered:
        problems.append(f"§8.5 violated (S0NN namespace): {len(s_uncovered)} code(s) with no test block naming them "
                        f"(a comment or bare string mention does not count):\n  {', '.join(s_uncovered)}\n\n"
                        f"  Searched: {format_repo_relative(STATE_VALIDATE_TEST_FILE)}" + (" (file not found)" if not state_test_files else "") +
                        f"\n\n  remedy: add or extend a test name in tests/test_state_validate.py so the title names the code "
                        f"(e.g. def test_{s_uncovered[0].lower()}_fires).")
    return problems, proof, consistency_new


def _js_json(value):
    return json.dumps(value)


_DISCOVER = object()


def run(rules=None, consistency_rules=None, severity=None, test_files=None, state_codes=_DISCOVER):
    """Evaluate the gate. Returns the list of stdout lines; raises ``_ExitError`` on a violation.

    ``state_codes`` defaults to discovery from the state validation source; ``None`` skips the S0NN pass.
    """
    from . import health_diagnostic as hd
    rules = hd.RULES if rules is None else rules
    consistency_rules = hd.CONSISTENCY_RULES if consistency_rules is None else consistency_rules
    severity = hd.SEVERITY if severity is None else severity
    files = find_health_diagnostic_test_files() if test_files is None else list(test_files)
    state_codes = load_state_validate_codes() if state_codes is _DISCOVER else state_codes
    state_files = [STATE_VALIDATE_TEST_FILE] if STATE_VALIDATE_TEST_FILE.exists() else []

    problems, proof, consistency_new = _problems(rules, consistency_rules, severity, files, state_codes, state_files)
    if problems:
        raise _ExitError(1, "\n\n".join(problems) + "\n")

    exempted = proof["exempted"]
    covered = len(rules) - len(exempted)
    lines = [f"lint-health-diagnostic-rule-table: PASS — {len(rules)} rule code(s): {covered} covered by a "
             f"titled test, {len(exempted)} exempted across {len(files)} test file(s)." +
             (f"\n  Exempted: {'; '.join(f'{c} ({PERMANENTLY_INERT_CODES.get(c)})' for c in exempted)}" if exempted else ""),
             f"lint-health-diagnostic-rule-table: PASS (C0NN namespace) — {len(consistency_new)} new rule code(s) "
             f"({', '.join(r['code'] for r in consistency_new)}), all covered in {format_repo_relative(CONSISTENCY_TEST_FILE)}."]
    if state_codes is None:
        lines.append("lint-health-diagnostic-rule-table: SKIP (S0NN namespace) — "
                     f"{format_repo_relative(STATE_VALIDATE_SOURCE_FILE)} not found; no stateDiagnostic() call sites to check.")
    else:
        lines.append(f"lint-health-diagnostic-rule-table: PASS (S0NN namespace) — {len(state_codes)} code(s) "
                     f"({', '.join(state_codes)}), all covered in {format_repo_relative(STATE_VALIDATE_TEST_FILE)}.")
    return lines


def main(argv=None):
    """CLI entry point (no flags). Returns the process exit code."""
    try:
        for line in run():
            sys.stdout.write(line + "\n")
        return 0
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
