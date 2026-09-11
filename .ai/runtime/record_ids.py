import argparse
import json
from pathlib import Path
import re
import sys

from orchestrate import Blocked, ID_KINDS, git, json_section, require


KINDS = (*ID_KINDS, 'PLAN', 'ORCH', 'RES')
RECORD_DIRECTORIES = ('plans', 'fixes', 'specs', 'decisions', 'research', 'state/orchestration')


def highest_issued(roots, common):
    highest = dict.fromkeys(KINDS, 0)

    def include(kind, bounds):
        require(kind in KINDS and isinstance(bounds, list) and len(bounds) == 2 and
                all(type(n) is int for n in bounds) and 0 < bounds[0] <= bounds[1], 'Invalid reserved ID range')
        highest[kind] = max(highest[kind], bounds[1])

    for root in roots:
        for directory in RECORD_DIRECTORIES:
            for path in (root / '.ai' / directory).rglob('*.md'):
                record = re.match(r'(' + '|'.join(KINDS) + r')-(\d+)(?:-|\.md$)', path.name)
                if record:
                    highest[record[1]] = max(highest[record[1]], int(record[2]))
        for manifest in (root / '.ai/state/orchestration').glob('ORCH-*.md'):
            text = manifest.read_text(encoding='utf-8')
            if re.search(r'^## Execution schedule[ \t]*$', text, re.M):
                schedule = json_section(text, 'Execution schedule')
                for track in schedule['tracks']:
                    for kind, bounds in track['ids'].items():
                        include(kind, bounds)
            section = re.search(r'^## Reserved id blocks[ \t]*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
            columns = None
            if section:
                for line in section[1].splitlines():
                    if not line.strip().startswith('|'):
                        continue
                    cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
                    if 'Track' in cells and any(kind in cells for kind in ID_KINDS):
                        columns = cells
                    elif columns and any(re.search(r'\d', cell) for cell in cells):
                        require(len(cells) == len(columns), f'Malformed ID table in {manifest}')
                        for kind, cell in zip(columns, cells):
                            if kind in ID_KINDS:
                                match = re.fullmatch(r'`?(\d+)\s*[-–]\s*(\d+)`?', cell)
                                require(match is not None, f'Invalid {kind} reservation in {manifest}')
                                include(kind, [int(match[1]), int(match[2])])
    for receipt in (common / 'orchestration').glob('*/state.json'):
        run = re.fullmatch(r'ORCH-(\d+)', receipt.parent.name)
        if run:
            highest['ORCH'] = max(highest['ORCH'], int(run[1]))
        data = json.loads(receipt.read_text(encoding='utf-8'))
        for track in data['tracks'].values():
            for kind, bounds in track.get('ids', {}).items():
                include(kind, bounds)
    return highest


def next_range(repository, kind, count=1):
    require(kind in KINDS and type(count) is int and count > 0, 'Select an ID kind and a positive count')
    root = Path(repository).resolve()
    roots = [Path(line.removeprefix('worktree ')) for line in git(root, 'worktree', 'list', '--porcelain').splitlines()
             if line.startswith('worktree ')]
    require(all(path.is_dir() for path in roots), 'Inspect missing worktrees before allocating IDs')
    common = Path(git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    highest = highest_issued(roots, common)[kind]
    return {'kind': kind, 'first': highest + 1, 'last': highest + count, 'reserved': False}


def main():
    parser = argparse.ArgumentParser(description='Propose IDs above existing records, issued manifests and runtime receipts; does not reserve them.')
    parser.add_argument('kind', choices=KINDS)
    parser.add_argument('--count', type=int, default=1)
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        print(json.dumps(next_range(args.repository, args.kind, args.count), indent=2))
        return 0
    except (Blocked, KeyError, TypeError, ValueError, OSError) as exc:
        print(f'Blocked: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
