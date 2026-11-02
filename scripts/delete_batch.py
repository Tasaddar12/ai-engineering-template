"""Preview, remove, or verify one explicit manifest deletion batch."""
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import main_guard, manifest, parser, safe_path


def delete_paths(root, paths, *, apply=False, verify=False):
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("Batch must contain unique, explicit paths")
    # Preflight the entire batch before any deletion. Only exact files qualify.
    targets = [(name, safe_path(root, name)) for name in paths]
    for name, path in targets:
        if path.exists() and not path.is_file():
            raise ValueError(f"Manifest entry must be an exact file: {name}")
    existing = [name for name, path in targets if path.exists()]
    if verify:
        for name in existing:
            print(f"PRESENT {name}")
        print(f"{len(existing)} of {len(paths)} batch paths remain")
        return int(bool(existing))
    for name, path in targets:
        print(f"{'DELETE' if apply else 'WOULD DELETE'} {name}" if path.exists() else f"ABSENT {name}")
    if apply and existing:
        # git rm fails on untracked or modified files. Never force or bypass it.
        subprocess.run(["git", "-C", str(root.resolve()), "rm", "-r", "--", *existing], check=True)
    return 0


def main():
    command = parser(__doc__)
    command.add_argument("--batch", required=True, choices=("A", "B"))
    mode = command.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = command.parse_args()
    return delete_paths(args.root, manifest()[f"batch_{args.batch.lower()}"], apply=args.apply, verify=args.verify)


if __name__ == "__main__":
    sys.exit(main_guard(main))
