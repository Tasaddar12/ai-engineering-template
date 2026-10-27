"""Preview phase check commands; use --apply to execute the selected batch."""
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import main_guard, parser, plan


def check_blocks(text):
    result = {}
    phase = None
    in_check = False
    for line in text.splitlines():
        heading = re.match(r'^### Phase (\d+[a-f]?):', line)
        if heading:
            phase = heading[1]
            result.setdefault(phase, [])
        if line.startswith("## "):
            phase = None
        if line == "```check" and phase is not None:
            in_check = True
        elif line.startswith("```"):
            in_check = False
        elif in_check and line.strip():
            result[phase].append(line)
    return result


def selected_checks(text, phases, all_phases=False):
    blocks = check_blocks(text)
    selected = list(blocks) if all_phases else phases
    result = []
    for phase in selected:
        key = "8" if re.fullmatch(r'8[a-f]', phase) else phase
        if key not in blocks:
            raise ValueError(f"Unknown phase: {phase}")
        for line in blocks[key]:
            if phase == "5" and "scripts/progress.py" in line and "--stage" not in line:
                line += " --stage core"
            result.append((phase, line))
    return result


def main():
    command = parser(__doc__)
    selection = command.add_mutually_exclusive_group(required=True)
    selection.add_argument("--phase", action="append")
    selection.add_argument("--all", action="store_true")
    command.add_argument("--apply", action="store_true", help="Execute checks; default only previews commands")
    args = command.parse_args()
    commands = selected_checks(plan(args.root), args.phase, args.all)
    failed = False
    for phase, line in commands:
        if not args.apply:
            print(f"WOULD RUN [{phase}] {line}")
            continue
        completed = subprocess.run(["bash", "-c", line], cwd=args.root)
        ok = completed.returncode == 0
        print(f"{'PASS' if ok else 'FAIL'} [{phase}] {line}", flush=True)
        failed |= not ok
    return int(failed)


if __name__ == "__main__":
    sys.exit(main_guard(main))
