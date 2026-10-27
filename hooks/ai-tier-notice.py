"""Advisory notice for primary-checkout writes and workflow authority boundaries."""
import sys
from pathlib import Path
from hook_common import read_event, root_for


def main():
    try:
        event = read_event()
        root = root_for(event)
        if (root / ".git").is_dir():
            namespace = Path(__file__).resolve().parent.parent
            rules = namespace / "engineer/RULES.md"
            print("NOTICE: primary checkout. Follow " + str(rules).replace("\\", "/") + "#phase-authority and use a coordinator-assigned isolated checkout for worker source changes. Planning and discussion do not grant implementation permission.", file=sys.stderr)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
