# Installer inputs

These files are packaging inputs for [install.py](../install.py). The installer
does not copy this directory into adopting projects.

- `agent-entry.txt` is installed as a delimited block in root AGENTS.md. It is
  project guidance; the source repository's root AGENTS.md remains maintainer guidance.
- PROJECT, REQUIREMENTS, ROADMAP and STATE text files become pending onboarding
  records only when destination records are missing. Complete authoring methods
  and illustrative examples remain in the separately installed `.ai/templates/`.

Explicit repair reads the original release directly from Git at the installer's
pinned revision. No duplicate history or JSON manifest is kept or installed.

Changes to these inputs require testing the rendered destination, including
project context, preservation, links, runtime startup and the repair boundary.
