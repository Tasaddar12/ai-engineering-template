"""Preview deterministic mechanical substitutions in canonical source files."""
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import files, main_guard, manifest, parser, read_text, safe_path


def substitutions(text, role_renames, launcher=None):
    counts = {}
    # Replace complete upstream one-line launchers before token substitutions.
    launcher_pattern = r'^_GSD_SHIM_NAME=[^\n]*(?:\n|$)'
    if re.search(launcher_pattern, text, re.MULTILINE):
        if not launcher or not launcher.strip() or any(token in launcher for token in ("gsd-tools", "gsd_run", "_GSD_SHIM")):
            raise ValueError("Port engineer/workflows/_runtime-launcher.snippet.sh to engineer_run before replacing upstream launchers")
        text, count = re.subn(launcher_pattern, lambda _: launcher.rstrip() + "\n", text, flags=re.MULTILINE)
        counts["launcher"] = count
    replacements = [
        ("runtime", r'\bgsd_run\b', "engineer_run"),
        ("tools-query", r'(?<![A-Za-z0-9_./-])gsd-tools\s+query\b', "engineer_run query"),
        ("references", re.escape("~/.claude/gsd-core/references/"), "engineer/references/"),
        ("templates", re.escape("~/.claude/gsd-core/templates/"), "engineer/templates/"),
        ("workflows", r'(?:~\/\.claude\/)?gsd-core/workflows/', "engineer/workflows/"),
        ("commands", r'/gsd:([A-Za-z][A-Za-z0-9_-]*)', r'/\1'),
        ("command-name", r'(?m)^(name:\s*)gsd:', r'\1'),
        ("local-methods", re.escape(".ai/references/methods/"), "engineer/references/"),
        ("local-paths", r'\.ai/(references|templates|workflows)/', r'engineer/\1/'),
        ("local-runtime", r'\bphase_run(?=\s+query\b)', "engineer_run"),
        ("instruction-file", r'\bCLAUDE\.md\b', "AGENTS.md"),
    ]
    roles = sorted({Path(source).stem for source in role_renames} | {"gsd-executor"}, key=len, reverse=True)
    replacements.append(("roles", r'(?<![A-Za-z0-9_-])(?:' + "|".join(map(re.escape, roles)) + r')(?![A-Za-z0-9_-])', None))
    for label, pattern, replacement in replacements:
        text, count = re.subn(pattern, (lambda match: match[0][4:]) if replacement is None else replacement, text)
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
