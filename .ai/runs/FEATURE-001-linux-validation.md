# FEATURE-001 Linux validation

Reviewed code head: 274ca00bb42e3ea96db7f60dc189633e0651f633, integrated locally. Ubuntu 24.04 under WSL, Python 3.12.3: `python -m pytest -q tests/test_core.py` passed all 14 tests, including symlink rejection. Windows Python 3.13.14 passed 13 with one symlink-creation privilege skip. Linux dependencies were installed in a dedicated ignored local environment; no legacy workflow was resumed. No source changes were needed.
