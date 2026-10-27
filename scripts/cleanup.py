"""Explicit preview-bound cleanup bridge; never registered as a hook."""
import argparse
from pathlib import Path
import subprocess
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("preview")
    apply = commands.add_parser("apply")
    apply.add_argument("--approval-token", required=True)
    apply.add_argument("--confirm", action="store_true", required=True)
    args = parser.parse_args(argv)
    entry = Path(__file__).resolve().parents[1] / "engineer/bin/engineer.py"
    if not entry.is_file():
        print("cleanup runtime unavailable: " + str(entry), file=sys.stderr)
        return 2
    command = [sys.executable, str(entry), "query", "cleanup." + args.action]
    if args.action == "apply":
        command.extend(["--approval-token", args.approval_token, "--confirm"])
    # The runtime binds the token to the exact preview and revalidates ownership,
    # cleanliness, ancestry, branch and HEAD before each individual deletion.
    result = subprocess.run(command)
    return 0 if result.returncode == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
