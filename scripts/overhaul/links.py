"""Check navigable Markdown and canonical source @includes, not code examples.

Literal reusable-source includes remain checked inside prompt examples. Scoped
npm package names and adopting-project output paths are not reusable inputs.
"""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import files, main_guard, parser, read_text

MARKDOWN = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+["\'][^\n]*?["\'])?\s*\)')
REFERENCE = re.compile(r'^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)', re.MULTILINE)
INCLUDE = re.compile(r'(?<![\w/])@((?:~?/|\.{1,2}/)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.*{}$<>:-]+)+)')
SOURCE_ROOTS = {"agents", "commands", "engineer", "skills", "docs", "hooks", "bin"}


def navigation_text(text):
    """Mask illustrative code while retaining offsets for actual navigation."""
    result, fence = [], None
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if fence is None and marker:
            fence = marker[1]
            result.append(re.sub(r'[^\r\n]', ' ', line))
        elif fence is not None:
            result.append(re.sub(r'[^\r\n]', ' ', line))
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not line[marker.end():].strip():
                fence = None
        else:
            result.append(line)
    return re.sub(r'(`+)([^`\n]*?)\1', lambda m: ' ' * len(m[0]), ''.join(result))


def targets(text):
    for pattern, include in ((MARKDOWN, False), (REFERENCE, False), (INCLUDE, True)):
        # Canonical @includes inside authored prompt blocks remain real inputs;
        # scoped npm names and illustrative project outputs are not includes.
        scan = text if include else navigation_text(text)
        for match in pattern.finditer(scan):
            target = match[1].strip("<>").rstrip(".,;:")
            if include and not target.startswith(("/", "~/", "./", "../")) and target.split("/", 1)[0] not in SOURCE_ROOTS:
                continue
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
    candidates = [root / name] if include and not name.startswith(("./", "../")) else [source.parent / name]
    if name.split("/", 1)[0] in SOURCE_ROOTS:
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
