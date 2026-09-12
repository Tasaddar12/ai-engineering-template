#!/usr/bin/env python3
"""Small phase coordinator. Markdown procedures remain the human entry points."""
import argparse
import subprocess
import sys

from phase_records import PhaseError, load_phase
from phase_runner import (assigned, check_phase_dependencies, clean, lock, new_phase,
                          publish_phase, repo, run_phase, status_text, sync_state,
                          uat_phase, verify_phase)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="Create a pending phase and roadmap link")
    new.add_argument("slug")
    new.add_argument("--title", required=True)
    for name in ("check", "run", "resume", "verify", "uat", "publish"):
        command = sub.add_parser(name)
        command.add_argument("phase")
        if name in ("run", "resume", "verify"):
            command.add_argument("--workers-stopped", action="store_true")
        if name == "run":
            command.add_argument("--replan", action="store_true")
        if name == "uat":
            command.add_argument("--case", type=int)
            command.add_argument("--result", choices=["pass", "fail", "blocked", "skipped"])
            command.add_argument("--note")
        if name == "publish":
            command.add_argument("--authorized", action="store_true")
            command.add_argument("--base", required=True)
            command.add_argument("--draft", action="store_true")
    status = sub.add_parser("status")
    status.add_argument("phase", nargs="?")
    status.add_argument("--remote", action="store_true", help="Read live PR observations without changing local records")
    sub.add_parser("sync")
    args = parser.parse_args(argv)
    try:
        root = repo()
        if args.command == "status":
            print(status_text(root, args.phase, args.remote), end="")
            return 0
        if args.command == "check":
            phase = load_phase(root, args.phase, ready=True)
            check_phase_dependencies(phase)
            print(f"{phase.directory.name}: ready; {len(phase.components)} component(s). Independent checker still assesses feasibility.")
            return 0
        assigned(root)
        clean(root)
        with lock(root):
            if args.command == "new":
                new_phase(root, args.slug, args.title)
            elif args.command == "sync":
                sync_state(root)
            else:
                phase = load_phase(root, args.phase, ready=True)
                if args.command in ("run", "resume"):
                    run_phase(phase, resume=args.command == "resume", workers_stopped=args.workers_stopped,
                              replan=getattr(args, "replan", False))
                elif args.command == "verify":
                    verify_phase(phase, workers_stopped=args.workers_stopped)
                elif args.command == "uat":
                    uat_phase(phase, args.case, args.result, args.note)
                elif args.command == "publish":
                    publish_phase(phase, authorized=args.authorized, base=args.base, draft=args.draft)
        return 0
    except (PhaseError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"Phase stopped: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Phase interrupted; inspect workers, then resume with --workers-stopped.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
