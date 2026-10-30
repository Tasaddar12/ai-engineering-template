"""Canonical artifact registry: the file names workflows officially produce at the
``.planning/`` root, used by health (W019) to flag unrecognized files.

Ported from upstream gsd-core ``src/artifacts.cts`` at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).
Add entries to ``CANONICAL_EXACT`` whenever a new workflow produces a ``.planning/``
root file.

Deviations:
- ``CANONICAL_EXACT`` is a ``frozenset`` (upstream ``ReadonlySet``); ``CANONICAL_PATTERNS`` is a tuple of
  compiled ``re`` patterns (upstream ``ReadonlyArray<RegExp>``). Match with ``pattern.search``, which is
  the equivalent of ``RegExp.test`` for these anchored patterns.
- The anchors use ``\\Z`` and ``[0-9]`` and ``.`` is narrowed to exclude the ECMAScript line terminators
  so the patterns accept exactly what the JavaScript ones accept.
- Upstream's registry content is carried verbatim, including entries for upstream-only producers
  (``milestone.lock``, ``state.json``, ``skill-manifest.json``, ``PATTERNS.md``); this
  repo's ``engineer/templates/README.md`` index may list a different set, which is not reconciled here.
"""
from __future__ import annotations

import re

__all__ = ["CANONICAL_EXACT", "CANONICAL_PATTERNS", "is_canonical_planning_file"]

# Exact-match canonical file names at .planning/ root
CANONICAL_EXACT = frozenset([
    "PROJECT.md",
    "ROADMAP.md",
    "STATE.md",
    "REQUIREMENTS.md",
    "MILESTONES.md",
    "BACKLOG.md",
    "LEARNINGS.md",
    "THREADS.md",
    "config.json",
    "CLAUDE.md",
    "RETROSPECTIVE.md",
    "STATE-ARCHIVE.md",  # state prune writes this at the .planning/ root
    "milestone.lock",  # milestone (phase + session) claim; persistent, unlike the transient STATE.md.lock/WAITING.json
    "state.json",  # machine-readable state contract published at step boundaries
    "skill-manifest.json",  # skill manifest write (project-scoped planning root)
    "PATTERNS.md",  # graduated cross-phase patterns; distinct from the per-phase NN-PATTERNS.md
])

_DOT = "[^\n\r\u2028\u2029]"

# Pattern-match canonical file names (regex tests on the basename)
CANONICAL_PATTERNS = (
    re.compile(r"^v[0-9]+\.[0-9]+(?:\.[0-9]+)?-MILESTONE-AUDIT\.md\Z", re.IGNORECASE),  # complete-milestone (pre-archive)
    re.compile(r"^v[0-9]+\.[0-9]+(?:\.[0-9]+)?-" + _DOT + r"*\.md\Z", re.IGNORECASE),  # other version-stamped planning docs
)


def is_canonical_planning_file(filename):
    """True if ``filename`` (basename only, no path) is a canonical ``.planning/`` root artifact."""
    if filename in CANONICAL_EXACT:
        return True
    for pattern in CANONICAL_PATTERNS:
        if pattern.search(filename):
            return True
    return False
