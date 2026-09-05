"""Foundation CLI."""
import argparse
from collections.abc import Sequence
from ai_engineering import __version__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m ai_engineering",
        description="Phase-one foundation. Plan execution is not implemented yet.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(argv)
    parser.print_help()
    return 0
