#!/usr/bin/env python3
"""Preview legacy relocation and selected copies; never delete legacy sources."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_support import cli, migration_plan

if __name__ == '__main__':
    raise SystemExit(cli('migrate'))
