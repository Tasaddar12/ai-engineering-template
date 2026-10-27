"""Report broken local Markdown links and literal @path includes."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import files, main_guard, parser, read_text

MARKDOWN = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+["\'][^\n]*?["\'])?\s*\)')
REFERENCE = re.compile(r'^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)', re.MULTILINE)
INCLUDE = re.compile(r'(?<![\w/])@((?:~?/|\.{1,2}/)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.*{}$<>:-]+)+)')


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
    if name.startswith("~"):
        return False  # Upstream installed-home links must be repointed.
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
    for source in files(root, ("agents", "commands", "engineer", "skills")):
        if source.suffix != ".md":
            continue
        text = read_text(source)
        if text is None:
            continue
        for target, line, include in targets(text):
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
