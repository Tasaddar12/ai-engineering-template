"""Report reconciliation completion from exact Rows Git trailers."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import completed_rows, deferred_workflow_rows, git, main_guard, parser, plan, rows


def main():
    command = parser(__doc__)
    command.add_argument("--prefix", action="append", default=[])
    command.add_argument("--require-done", action="store_true")
    command.add_argument("--list", action="store_true")
    command.add_argument("--stage", choices=("all", "core", "features"), default="all", help="Scope Phase 5 core workflows separately from Phase 8 feature workflows")
    args = command.parse_args()
    text = plan(args.root)
    catalog = rows(text)
    selected = {row for row in catalog if not args.prefix or any(row.startswith(prefix + "-") or row == prefix for prefix in args.prefix)}
    deferred = deferred_workflow_rows(text)
    if args.stage == "core":
        selected -= deferred
    elif args.stage == "features":
        selected &= deferred
    if not selected:
        raise ValueError("No reconciliation rows match the requested prefixes")
    done = completed_rows(git(args.root, "log", "--format=%B%x1e"))
    unknown = done - catalog.keys()
    for row in sorted(unknown):
        print(f"UNKNOWN TRAILER ROW {row}")
    remaining = selected - done
    print(f"{len(selected - remaining)} done / {len(selected)} total; {len(remaining)} remaining")
    if args.list:
        for row in sorted(selected):
            print(f"{'OPEN' if row in remaining else 'DONE'} {row}")
    return int(args.require_done and bool(remaining))


if __name__ == "__main__":
    sys.exit(main_guard(main))
