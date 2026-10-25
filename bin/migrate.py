#!/usr/bin/env python3
"""Migrate an existing deployment to the new AI Engineer workflow layout.

Entry-point scaffold. Deployment behavior will be planned and implemented later.
"""

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    parser.exit(2, "Migration scaffold only; deployment migration is not implemented.\n")


if __name__ == "__main__":
    raise SystemExit(main())
