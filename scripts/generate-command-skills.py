"""Regenerate full command skills. Native roles use bin/generate-assets.py.

This writes assets from canonical sources; it is not a verification command.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    skills = ROOT / "skills"
    for command in sorted((ROOT / "commands").glob("*.md")):
        if command.name == "COMMAND.md":
            continue
        destination = skills / command.stem / "SKILL.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Preserve full native frontmatter, arguments and procedure. Host path
        # adaptation is owned by bin/install.py, not the canonical skill mirror.
        destination.write_bytes(command.read_bytes())
    placeholder = skills / "SKILL" / "SKILL.md"
    if placeholder.is_file():
        placeholder.unlink()
        if not any(placeholder.parent.iterdir()):
            placeholder.parent.rmdir()


if __name__ == "__main__":
    main()
