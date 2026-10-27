"""Reject Node helper dependencies in the reusable workflow source."""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import files, main_guard, parser, read_text


INLINE = re.compile(r'\bnode[ \t]+(?:-[epc]\b|--(?:eval|print)\b)')


def findings(root):
    for path in files(root):
        relative = path.relative_to(root.resolve()).as_posix()
        if path.suffix.lower() == ".cjs":
            yield relative, 1, "CommonJS helper file"
        text = read_text(path)
        if text is None:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if INLINE.search(line):
                yield relative, number, "inline Node helper"


def main():
    args = parser(__doc__).parse_args()
    problems = list(findings(args.root))
    for path, line, reason in problems:
        print(f"FORBIDDEN {path}:{line}: {reason}")
    print(f"{len(problems)} Node helper dependencies")
    return int(bool(problems))


if __name__ == "__main__":
    sys.exit(main_guard(main))
