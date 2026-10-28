"""Responsive-separator guard for shipped markdown content.

Ported from upstream gsd-core ``tests/responsive-separators.test.cjs`` at
commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).
Convention owner: ``engineer/references/ui-brand.md`` "Separators and Banners".

A rule line is a line whose trimmed content is composed entirely of U+2500,
U+2501 or U+2550, three or more of them. A panel character is one of the
double-line box glyphs anywhere on a line. Tree glyphs, boxed-table rows,
progress bars and inline art never match.

Deviations:
- ``gsd-core/`` -> ``engineer/``; ``agents/`` -> ``agents/``;
  ``commands/gsd/`` -> ``commands/``.
- The upstream fast-check property tests are replaced by a deterministic seeded
  generator in the test module (stdlib only).
"""
import re
from pathlib import Path

SHIPPED_ROOTS = ("engineer", "agents", "commands")
MIN_RULE_RUN = 3
RULE_LINE_RE = re.compile("^[─━═]{%d,}$" % MIN_RULE_RUN)
PANEL_CHAR_RE = re.compile("[╔╗╚╝║╠╣╦╩╬]")
HEAVY, LIGHT, DOUBLE = "━", "─", "═"

REMEDY = (
    '\n\nPer engineer/references/ui-brand.md "Separators and Banners":\n'
    "  - a stage banner is an ATX heading with no rule lines;\n"
    "  - a panel becomes a heading followed by its rows as plain lines;\n"
    "  - a divider between sections is --- with a blank line above and below.\n"
    "A fixed-width run wraps in a narrow pane and comes apart from its heading."
)


def is_fixed_width_rule_line(line):
    """True when the stripped line is only 3+ rule glyphs."""
    return bool(RULE_LINE_RE.match(line.strip()))


def has_panel_character(line):
    return bool(PANEL_CHAR_RE.search(line))


def find_markdown_files(directory):
    directory = Path(directory)
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.rglob("*.md") if path.is_file())


def shipped_markdown_files(repo_root, roots=SHIPPED_ROOTS):
    files = []
    for root in roots:
        files.extend(find_markdown_files(Path(repo_root)/root))
    return files


def scan(files, predicate, repo_root=None):
    """Return ``path:line: excerpt`` for each line matching ``predicate``."""
    violations = []
    for file_path in files:
        file_path = Path(file_path)
        content = file_path.read_text(encoding="utf-8")
        shown = file_path
        if repo_root is not None:
            try:
                shown = file_path.relative_to(repo_root)
            except ValueError:
                pass
        for number, line in enumerate(re.split(r"\r?\n", content), 1):
            if predicate(line):
                violations.append("%s:%d: %s" % (Path(shown).as_posix(), number, line.strip()[:40]))
    return violations
