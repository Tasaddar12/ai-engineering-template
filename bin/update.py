#!/usr/bin/env python3
"""Preview a pinned workflow update; apply only exact reviewed snapshots."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_support import cli, inventory, plan_update

if __name__ == '__main__':
    raise SystemExit(cli('update'))
