#!/usr/bin/env python3
"""Fresh installation of the AI Engineer workflow for Codex or Claude.

Entry-point scaffold. Deployment behavior will be planned and implemented later.
"""

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    parser.exit(2, "Installer scaffold only; installation behavior is not implemented.\n")


if __name__ == "__main__":
    raise SystemExit(main())
