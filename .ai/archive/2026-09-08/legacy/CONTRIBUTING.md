# Contributing

Use Python 3.11 or newer. Keep executable modules directly under `src/`, use full type annotations for public functions, pass subprocess arguments as lists with `shell=False`, and return explicit errors for invalid or conflicting input.

Install development dependencies with `python -m pip install -e ".[dev]"`. Run `python -m unittest discover -s tests -v` and `python src/validate_foundation.py` before submitting a change. Tests should cover observable behavior and failure recovery, especially non-destructive installation into populated folders and cross-platform path handling.

Do not commit secrets, credentials, local worktrees, virtual environments, generated build output, or temporary validation data.
