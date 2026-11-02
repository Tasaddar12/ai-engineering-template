"""UI safety gate: does a roadmap phase section describe a frontend (UI) surface?

Ported from upstream ``src/ui-safety-gate.cts`` of gsd-core (MIT, Copyright (c) 2026
Open GSD) at pinned commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79.

Shell-free token sniffer with ASCII word-boundary anchoring
``(^|[^a-zA-Z0-9])(TOKEN)([^a-zA-Z0-9]|$)``: a token matches only when it is not an
interior substring of an alphanumeric word ("microfrontend" does not match,
"micro-frontend" does). An explicit ``**UI hint**: yes|no`` metadata line is the
author's authoritative declaration and overrides token sniffing; every ``**UI hint**:``
line is stripped before sniffing so the bare ``UI`` in it never counts.

Public API: ``UI_TOKENS`` and ``check_ui_presence(text)`` returning
``{"hasUI", "tokens", "matchedToken", "matchedLine"}``.

CLI: ``python -m lib.ui_safety_gate`` reads the phase-section text from stdin and
exits 0 when UI tokens are found, 1 when real input was examined and none were
found, 66 (NO_INPUT) when stdin was empty or whitespace-only, and 69 (UNAVAILABLE)
when stdin could not be read. It writes nothing to stdout; a read failure writes one
``ERROR:`` line to stderr.

Deviations:
  - Upstream resolves the exit codes through its registry (``PASS``/``FAIL``/
    ``NO_INPUT``/``UNAVAILABLE``) and ``terminateNow``; here the registered values
    (0, 1, 66, 69) are constants and ``main`` returns the code.
  - The stdin read-failure message names ``ui-safety-gate.py`` instead of
    ``ui-safety-gate.cjs``.
  - Regexes use ``re.ASCII`` and an explicit JavaScript ``\\s`` class so word boundaries,
    case folding and whitespace match JavaScript semantics; ``trim`` uses the same
    whitespace set.
  - The sibling gate ``src/gate-ui-safety.cts`` (``check ui-safety-gate <phase>``)
    depends on gate modules that do not exist at the base commit and is not ported.
"""
from __future__ import annotations

import re
import sys

UI_TOKENS = ("UI", "interface", "frontend", "component", "layout", "page", "screen", "view", "form", "dashboard", "widget")

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_NO_INPUT = 66
EXIT_UNAVAILABLE = 69

# JavaScript's `\s` / `String.prototype.trim` whitespace set.
_WS_CHARS = "\t\n\u000b\u000c\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
_S = "[" + _WS_CHARS.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + "]"

# ASCII word boundaries: JS [a-zA-Z0-9] is ASCII-only, unlike POSIX [[:alnum:]].
_UI_GATE_PATTERN = re.compile("(^|[^a-zA-Z0-9])(" + "|".join(UI_TOKENS) + ")([^a-zA-Z0-9]|\\Z)", re.IGNORECASE | re.ASCII)
_HINT_VALUE = re.compile("^" + _S + r"*\*\*UI hint\*\*" + _S + "*:" + _S + r"*(yes|no)\b", re.IGNORECASE | re.MULTILINE | re.ASCII)
_HINT_LINE = re.compile("^" + _S + r"*\*\*UI hint\*\*" + _S + "*:", re.IGNORECASE | re.ASCII)


def check_ui_presence(text):
    """Check a roadmap phase section for frontend UI indicators.

    ``hasUI`` is true when a UI token matched as a standalone word (or the section
    declares ``**UI hint**: yes``); ``tokens`` are the lowercased distinct matches in
    first-seen order; ``matchedToken``/``matchedLine`` record the first match so
    consumers can show what tripped the sniffer. ``**UI hint**: no`` returns no UI and
    no tokens whatever the prose says. Non-string input is "no UI".
    """
    if not isinstance(text, str):
        return {"hasUI": False, "tokens": [], "matchedToken": None, "matchedLine": None}
    normalised = text.replace("\r\n", "\n")
    hint_match = _HINT_VALUE.search(normalised)
    hint = hint_match.group(1).lower() if hint_match else None
    sniffable = "\n".join(line for line in normalised.split("\n") if not _HINT_LINE.match(line))
    found, matched_token, matched_line = [], None, None
    for line in sniffable.split("\n"):
        for match in _UI_GATE_PATTERN.finditer(line):
            token = match.group(2).lower()
            if matched_token is None:
                matched_token, matched_line = token, line
            if token not in found:
                found.append(token)
    if hint == "no":
        return {"hasUI": False, "tokens": [], "matchedToken": None, "matchedLine": None}
    if hint == "yes":
        return {"hasUI": True, "tokens": found, "matchedToken": matched_token, "matchedLine": matched_line}
    return {"hasUI": len(found) > 0, "tokens": found, "matchedToken": matched_token, "matchedLine": matched_line}


def main(argv=None, stdin=None, stderr=None):
    """CLI entry point: read stdin, return the exit code (see the module docstring)."""
    stdin = stdin if stdin is not None else getattr(sys.stdin, "buffer", sys.stdin)
    stderr = stderr if stderr is not None else sys.stderr
    try:
        data = stdin.read()
        text = data.decode("utf-8", "replace") if isinstance(data, (bytes, bytearray)) else str(data)
    except (OSError, ValueError) as error:
        stderr.write(f"ERROR: ui-safety-gate.py stdin read failed: {error}\n")
        return EXIT_UNAVAILABLE
    # Whitespace-only counts as empty; real input (even a lone NUL byte) reaches the detector.
    if text.strip(_WS_CHARS) == "":
        return EXIT_NO_INPUT
    return EXIT_PASS if check_ui_presence(text)["hasUI"] else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
