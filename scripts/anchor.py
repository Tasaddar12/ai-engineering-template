"""Print a row's cited baseline ranges side by side, without changing files."""
from itertools import zip_longest
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASELINE, git, historical_path, main_guard, parser, plan, rows

CITATION = re.compile(r'(?P<path>(?:\.?[A-Za-z0-9_-]+/)*\.?[A-Za-z0-9_.-]+\.(?:md|py|sh|json|yaml|yml|txt|cjs)):(?P<ranges>\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*)')


def citations(cell):
    for match in CITATION.finditer(cell):
        for span in match["ranges"].split(","):
            bounds = span.strip().split("-")
            start, end = int(bounds[0]), int(bounds[-1])
            if start < 1 or end < start:
                raise ValueError(f"Invalid cited range: {match[0]}")
            yield match["path"], start, end


def anchor_lines(root, cell):
    result = []
    cache = {}
    tree = git(root, "ls-tree", "-r", "--name-only", BASELINE).splitlines()
    for path, start, end in citations(cell):
        if path not in cache:
            source = historical_path(tree, path)
            cache[path] = git(root, "show", f"{BASELINE}:{source}").splitlines()
        content = cache[path]
        if end > len(content):
            raise ValueError(f"Range exceeds baseline file: {path}:{start}-{end}")
        result.append(f"{path}:{start}-{end}")
        result.extend(f"{number:5}: {content[number - 1]}" for number in range(start, end + 1))
    return result or [f"No explicit line citation: {cell.strip()}"]


def row_cells(text, row_id):
    catalog = rows(text)
    if row_id not in catalog:
        raise ValueError(f"Unknown row: {row_id}")
    # Escaped pipes occur inside instruction code samples.
    return [cell.strip() for cell in re.split(r'(?<!\\)\|', catalog[row_id])[1:-1]]


def main():
    command = parser(__doc__)
    command.add_argument("row_id")
    args = command.parse_args()
    cells = row_cells(plan(args.root), args.row_id)
    # Reconciliation table layouts differ in sections 13/14. Extract citation
    # cells rather than assuming every row shares the agent table layout.
    local_cells = [cell for cell in cells[1:] if re.search(r'\.ai/[^ |;`]+:\d', cell)]
    upstream_cells = [cell for cell in cells[1:] if cell not in local_cells and list(citations(cell))]
    left = anchor_lines(args.root, " ; ".join(upstream_cells))
    right = anchor_lines(args.root, " ; ".join(local_cells))
    width = max(40, max(map(len, left)))
    print(f"{args.row_id} — baseline {BASELINE}")
    print(" | ".join(cells))
    print(f"{'Upstream target':<{width}} | Local source")
    for original, local in zip_longest(left, right, fillvalue=""):
        print(f"{original:<{width}} | {local}")
    return 0


if __name__ == "__main__":
    sys.exit(main_guard(main))
