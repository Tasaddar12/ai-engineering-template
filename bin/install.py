#!/usr/bin/env python3
"""Install the complete pinned Claude or Codex workflow assets."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_support import cli

if __name__ == '__main__':
    raise SystemExit(cli('install'))
