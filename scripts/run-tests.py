"""Run every unittest module in isolated processes and retain complete results."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.workers <= 16:
        parser.error("workers must be between 1 and 16")
    output = args.output_dir.resolve()
    if output.is_relative_to(ROOT):
        parser.error("results must be outside the source checkout")
    if output.exists() and any(output.iterdir()):
        parser.error("choose an empty results directory to preserve prior evidence")
    output.mkdir(parents=True, exist_ok=True)
    modules = sorted(path.name for path in (ROOT / "tests").glob("test_*.py"))
    if not modules:
        parser.error("no test modules found")
    revision = git("rev-parse", "HEAD")
    status = git("status", "--porcelain", "--untracked-files=all")
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "NO_COLOR": "1", "PYTHON_COLORS": "0"}

    def run(module):
        command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", module, "-v"]
        started = time.monotonic()
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                encoding="utf-8", errors="replace", stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        log = output / (module + ".log")
        log.write_text(result.stdout, encoding="utf-8")
        return {"module": module, "argv": command, "exit_code": result.returncode,
                "elapsed_seconds": round(time.monotonic() - started, 3), "log": str(log)}

    print(f"Revision {revision}; {len(modules)} modules; {args.workers} processes", flush=True)
    results = []
    # Every module is joined, including after another module fails.
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(run, module) for module in modules]):
            result = future.result()
            results.append(result)
            print(f"{'PASS' if result['exit_code'] == 0 else 'FAIL'} {result['module']} ({result['elapsed_seconds']}s)", flush=True)
    unchanged = revision == git("rev-parse", "HEAD") and status == git("status", "--porcelain", "--untracked-files=all")
    record = {"revision": revision, "source_unchanged": unchanged,
              "modules": sorted(results, key=lambda item: item["module"])}
    (output / "results.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    failed = [item for item in record["modules"] if item["exit_code"] != 0]
    for item in failed:
        print(f"\n--- {item['module']} complete output ---", flush=True)
        print(Path(item["log"]).read_text(encoding="utf-8"), flush=True)
    print(f"{len(results) - len(failed)}/{len(modules)} modules passed; source unchanged: {unchanged}; results: {output}", flush=True)
    return int(bool(failed) or not unchanged)


if __name__ == "__main__":
    raise SystemExit(main())
