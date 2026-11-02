"""Preview deterministic mechanical substitutions in canonical source files."""
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import files, main_guard, manifest, parser, read_text, safe_path


def substitutions(text, role_renames, launcher=None):
    counts = {}
    current_launcher = r'(?ms)^_engineer_identity_ok\(\) \{.*?^if \[ -n "\$\{CLAUDE_ENV_FILE:-\}" \]; then\n.*?^fi(?:\n|$)'
    if launcher:
        refreshed = 0
        def refresh(match):
            nonlocal refreshed
            replacement = launcher.rstrip() + "\n"
            if match[0] != replacement:
                refreshed += 1
            return replacement
        text = re.sub(current_launcher, refresh, text)
        if refreshed:
            counts["launcher-refresh"] = refreshed
    replacements = [
        ("local-methods", re.escape(".ai/references/methods/"), "engineer/references/"),
        ("local-paths", r'\.ai/(references|templates|workflows)/', r'engineer/\1/'),
        ("local-runtime", r'\bphase_run(?=\s+query\b)', "engineer_run"),
        # These standalone verbs retain their CLI shape in section 14. Family
        # dispatch, DROP verbs and argument rewrites remain reconciliation work.
        ("query-prefix", r'\bengineer_run\s+(?=(?:run-with-timeout|audit-open)\b)', "engineer_run query "),
        ("runtime-invocation", r'\bnode\s+(?=[^\s`]*engineer\.py\b)', "python -I "),
        ("removed-host-alias", re.escape(', `--agy`'), ""),
    ]
    for label, pattern, replacement in replacements:
        text, count = re.subn(pattern, replacement, text)
        if count:
            counts[label] = count
    return text, counts


def main():
    command = parser(__doc__)
    command.add_argument("--apply", action="store_true")
    command.add_argument("--path", action="append", default=[], help="Exact file or directory, relative to root")
    args = command.parse_args()
    filters = [safe_path(args.root, name) for name in args.path]
    allowed = list(files(args.root))
    if filters:
        for target in filters:
            if not any(target == path or path.is_relative_to(target) for path in allowed):
                raise ValueError(f"Path does not select a canonical source file: {target}")
        allowed = [path for path in allowed if any(path == item or path.is_relative_to(item) for item in filters)]
    launcher_path = safe_path(args.root, "engineer/workflows/_runtime-launcher.snippet.sh")
    launcher = read_text(launcher_path) if launcher_path.exists() else None
    changes = []
    for path in allowed:
        if path == launcher_path:
            continue
        text = read_text(path)
        if text is None:
            continue
        replacement, counts = substitutions(text, manifest()["renames"], launcher)
        if counts:
            changes.append((path, replacement, counts))
    # Finish discovery before mutation so a missing launcher cannot partially apply.
    for path, replacement, counts in changes:
        print(f"{'WRITE' if args.apply else 'WOULD WRITE'} {path.relative_to(args.root.resolve()).as_posix()}: " + ", ".join(f"{name}={count}" for name, count in sorted(counts.items())))
        if args.apply:
            path.write_bytes(replacement.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))
    print(f"{len(changes)} files; {sum(sum(counts.values()) for _, _, counts in changes)} substitutions")
    return 0


if __name__ == "__main__":
    sys.exit(main_guard(main))
