"""Report broken local Markdown links and literal @path includes."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import files, main_guard, parser, read_text

MARKDOWN = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+["\'][^\n]*?["\'])?\s*\)')
REFERENCE = re.compile(r'^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)', re.MULTILINE)
INCLUDE = re.compile(r'(?<![\w/])@((?:~/\.(?:claude|codex)/|(?:\.{1,2}/)?(?:agents|commands|engineer|skills|docs|hooks|bin)/)[A-Za-z0-9_.*{}$<>:/-]+)')


def navigation(text):
    """Exclude fenced and inline examples without changing diagnostic line numbers."""
    fence = None
    lines = []
    for line in text.splitlines(keepends=True):
        opening = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)', line)
        if fence:
            if opening and opening[1][0] == fence[0] and len(opening[1]) >= len(fence) and not opening[2].strip():
                fence = None
            lines.append('\n' if line.endswith('\n') else '')
        elif opening:
            fence = opening[1]
            lines.append('\n' if line.endswith('\n') else '')
        else:
            lines.append(re.sub(r'(`+)(.*?)\1', lambda m: ' ' * len(m[0]), line))
    return ''.join(lines)


def targets(text):
    for pattern, include in ((MARKDOWN, False), (REFERENCE, False), (INCLUDE, True)):
        for match in pattern.finditer(text):
            target = match[1].strip("<>").rstrip(".,;:")
            yield target, text.count("\n", 0, match.start()) + 1, include


def resolve_target(root, source, target, include=False):
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not parts.path:
        return None
    name = unquote(parts.path)
    if any(token in name for token in ("$", "{", "}", "*", "<", ">")):
        return None  # Dynamic include/output patterns are not literal file paths.
    for prefix in ("~/.claude/", "~/.codex/"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            if name.startswith(("references/", "templates/", "workflows/")):
                name = "engineer/" + name
            return (root / name).is_file()  # Canonical source backing an installed import.
    if name.startswith("~"):
        return False
    if name.startswith("/"):
        return False
    root = root.resolve()
    candidates = [root / name] if include else [source.parent / name]
    if name.split("/", 1)[0] in {"agents", "commands", "engineer", "skills", "docs", "hooks", "bin"}:
        candidates.append(root / name)
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_relative_to(root) and candidate.exists():
            return True
    return False


def broken_links(root):
    sources = list(files(root, ("agents", "commands", "engineer", "skills", "docs")))
    sources += [root / name for name in ("AGENTS.md", "README.md", "CONTRIBUTING.md") if (root / name).is_file()]
    for source in sources:
        if source.suffix != ".md":
            continue
        text = read_text(source)
        if text is None:
            continue
        for target, line, include in targets(navigation(text)):
            if resolve_target(root, source, target, include) is False:
                yield source.relative_to(root.resolve()).as_posix(), line, target


def main():
    args = parser(__doc__).parse_args()
    broken = list(broken_links(args.root))
    for source, line, target in broken:
        print(f"BROKEN {source}:{line}: {target}")
    print(f"{len(broken)} broken targets")
    return int(bool(broken))


if __name__ == "__main__":
    sys.exit(main_guard(main))
