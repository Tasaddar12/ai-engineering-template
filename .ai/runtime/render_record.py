import argparse
from pathlib import Path
import sys

from orchestrate import Blocked, git, rebase_record_links, relative_path, require


def main():
    parser = argparse.ArgumentParser(description='Print a record template with links rebased for its destination.')
    parser.add_argument('template')
    parser.add_argument('destination')
    args = parser.parse_args()
    try:
        root = Path(git(Path.cwd(), 'rev-parse', '--show-toplevel')).resolve()
        for name in (args.template, args.destination):
            relative_path(name)
            require((root / name).resolve().is_relative_to(root), 'Record path escapes the checkout')
        text = (root / args.template).read_text(encoding='utf-8')
        sys.stdout.write(rebase_record_links(text, args.template, args.destination))
        return 0
    except (Blocked, OSError, ValueError) as exc:
        print(f'Blocked: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
