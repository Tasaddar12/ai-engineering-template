"""Preview the complete workflow file inventory; --apply writes it."""
import hashlib
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASELINE, TREE_ROOTS, files, git, main_guard, manifest, parser, read_text, safe_path

INVENTORY_ROOTS = TREE_ROOTS + ("scripts", "docs")
UPSTREAM_COPY = "1eb6c97"


def blob_id(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def render_inventory(root):
    root = root.resolve()
    baseline = {}
    for record in git(root, "ls-tree", "-r", UPSTREAM_COPY, "--", *INVENTORY_ROOTS).splitlines():
        metadata, path = record.split("\t", 1)
        baseline[path] = metadata.split()[2]
    source_names = {destination: source for source, destination in manifest()["renames"].items()}
    source_names["engineer/templates/TEMPLATE.md"] = "engineer/templates/README.md"
    lines = ["# Workflow file inventory", "", f"Anchor baseline: `{BASELINE}`. Origins compare Git blob content with the downloaded upstream copy at `{UPSTREAM_COPY}` after structural path mapping.", "", "Regenerate with `python -I scripts/inventory.py --apply`; compare with `--check`.", "", "| File | Origin | Lines | Remaining gsd references |", "|---|---|---:|---:|"]
    paths = sorted(files(root, INVENTORY_ROOTS), key=lambda path: path.relative_to(root).as_posix())
    entries = []
    for path in paths:
        name = path.relative_to(root).as_posix()
        if name == "docs/INVENTORY.md" or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        data = path.read_bytes()
        text = read_text(path)
        original = baseline.get(source_names.get(name, name))
        normalized = data.replace(b"\r\n", b"\n")
        origin = "local-only" if original is None else "upstream" if original in {blob_id(data), blob_id(normalized)} else "reconciled"
        count = len(text.splitlines()) if text is not None else "binary"
        refs = len(re.findall("gsd", text, re.IGNORECASE)) if text is not None else 0
        entries.append((name, f"| `{name}` | {origin} | {count} | {refs} |"))
    entries.append(("docs/INVENTORY.md", "| `docs/INVENTORY.md` | local-only | INVENTORY_LINES | INVENTORY_REFS |"))
    lines.extend(entry for _, entry in sorted(entries))
    body = "\n".join(lines)
    refs = len(re.findall("gsd", body, re.IGNORECASE))
    lines = [line.replace("INVENTORY_LINES", str(len(lines))).replace("INVENTORY_REFS", str(refs)) for line in lines]
    return "\n".join(lines) + "\n"


def main():
    command = parser(__doc__)
    mode = command.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = command.parse_args()
    rendered = render_inventory(args.root)
    destination = safe_path(args.root, "docs/INVENTORY.md")
    if args.check:
        stale = not destination.exists() or destination.read_bytes() != rendered.encode("utf-8")
        print("STALE docs/INVENTORY.md" if stale else "CURRENT docs/INVENTORY.md")
        return int(stale)
    if args.apply:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(rendered.encode("utf-8"))
        print("WROTE docs/INVENTORY.md")
    else:
        print(rendered, end="")
        print("DRY RUN: use --apply to write docs/INVENTORY.md")
    return 0


if __name__ == "__main__":
    sys.exit(main_guard(main))
