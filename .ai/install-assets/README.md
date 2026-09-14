# Installer inputs

These files are packaging inputs for [install.py](../install.py). The installer
does not copy this directory into adopting projects.

- `agent-entry.txt` is installed as a delimited block in root AGENTS.md. It is
  project guidance; the source repository's root AGENTS.md remains maintainer guidance.
- PROJECT, REQUIREMENTS, ROADMAP and STATE text files become pending onboarding
  records only when destination records are missing. Complete authoring methods
  and illustrative examples remain in the separately installed `.ai/templates/`.
- `legacy-context.json` identifies the original faulty installer payload at its
  recorded revision. SHA-256 hashes use LF-normalized bytes. The original agent
  entry supports exact block replacement; retained rule/history content supplies
  regression fixtures. Preserve this historical baseline when changing the installer.

Changes to these inputs require testing the rendered destination, including
project context, preservation, links, runtime startup and the repair boundary.
