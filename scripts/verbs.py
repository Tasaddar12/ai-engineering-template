"""Compare literal engineer query call sites with the Python runtime registry."""
import ast
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import files, main_guard, parser, read_text, safe_path

CALL = re.compile(r'\bengineer_run\s+query\s+([A-Za-z][A-Za-z0-9_.-]*)')


def registered_verbs(source):
    """Read static registry keys without importing or executing the runtime."""
    tree = ast.parse(source)
    found = set()
    registry_seen = False
    for node in ast.walk(tree):
        value = None
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "VERBS" for target in node.targets):
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "VERBS":
            value = node.value
        if value is not None:
            registry_seen = True
            if isinstance(value, ast.Dict):
                if any(not isinstance(key, ast.Constant) or not isinstance(key.value, str) for key in value.keys):
                    raise ValueError("VERBS contains dynamic keys; expose a static registry for inspection")
                found.update(key.value for key in value.keys)
            elif isinstance(value, (ast.Set, ast.List, ast.Tuple)):
                if any(not isinstance(item, ast.Constant) or not isinstance(item.value, str) for item in value.elts):
                    raise ValueError("VERBS contains dynamic entries")
                found.update(item.value for item in value.elts)
            else:
                raise ValueError("VERBS must be a static dict, set, list or tuple")
    if not registry_seen:
        raise ValueError("No static VERBS registry found in engineer/bin/engineer.py")
    return found


def call_sites(root):
    result = []
    for path in files(root):
        text = read_text(path)
        if text is None:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for match in CALL.finditer(line):
                # Angle-bracket placeholders and shell expressions never match CALL.
                result.append((match[1], path.relative_to(root.resolve()).as_posix(), number))
    return result


def main():
    command = parser(__doc__)
    command.add_argument("--report", action="store_true")
    command.add_argument("--fail-on-unknown", action="store_true")
    args = command.parse_args()
    runtime = safe_path(args.root, "engineer/bin/engineer.py")
    known = registered_verbs(runtime.read_text(encoding="utf-8"))
    sites = call_sites(args.root)
    unknown = [(verb, path, number) for verb, path, number in sites if verb not in known]
    for verb, path, number in sorted(unknown):
        print(f"UNKNOWN {path}:{number}: {verb}")
    if args.report:
        for verb in sorted({site[0] for site in sites} & known):
            print(f"KNOWN {verb}")
    print(f"{len(known)} registered; {len(sites)} call sites; {len(unknown)} unknown call sites")
    return int(args.fail_on_unknown and bool(unknown))


if __name__ == "__main__":
    sys.exit(main_guard(main))
