"""Bounded assessment proof; mutates only a verified disposable source copy."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
EXPECTED_HEAD = "43c8004c7313105f63d3b8d21726f8a056b96842"
LOG: list[str] = []


def note(value: str) -> None:
    print(value, flush=True)
    LOG.append(value)


def command(argv: list[str], cwd: Path, expected: int) -> str:
    result = subprocess.run(
        argv, cwd=cwd, shell=False, capture_output=True, text=True, timeout=180
    )
    output = result.stdout + result.stderr
    note(json.dumps({"argv": argv, "cwd": str(cwd), "exit_code": result.returncode}))
    note(output.rstrip())
    assert result.returncode == expected, (argv, result.returncode, expected)
    return output


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    head = command(["git", "rev-parse", "HEAD"], ROOT, 0).strip()
    assert head == EXPECTED_HEAD, head
    command(["git", "diff", "--exit-code", "HEAD", "--"], ROOT, 0)
    review_root = ROOT / ".ai/plans/current/PLAN-001/reviews"
    preserved = {
        path: digest(path)
        for path in review_root.rglob("*")
        if path.is_file()
    }
    for relative in (
        "src/ai.py", "src/assets.py", "src/install.py", "src/workflow_ports.py",
        "tests/unit/templates/test_assets.py",
        ".ai/plans/current/PLAN-001/evidence/implementation/TASK-005.md",
        ".ai/plans/current/PLAN-001/graph.json",
        ".ai/plans/current/PLAN-001/tasks/current/TASK-005.json",
        ".ai/plans/current/PLAN-001/tasks/current/TASK-034.json",
        ".ai/plans/current/PLAN-001/tasks/current/TASK-037.json",
        ".ai/STATE.json", ".ai/project/policy.json",
    ):
        path = ROOT / relative
        preserved[path] = digest(path)
    note("Preserved-file snapshot count: " + str(len(preserved)))
    note("Input SHA-256: " + json.dumps({
        path.relative_to(ROOT).as_posix(): value
        for path, value in preserved.items()
        if path.parent != review_root and review_root not in path.parents
    }, sort_keys=True))

    local = (ROOT / ".ai/local").resolve(strict=True)
    scratch = Path(tempfile.mkdtemp(prefix="task005-future-closure-", dir=local)).resolve()
    marker = scratch / ".assessment-owner"
    marker.write_text("/root/assess_005_closure", encoding="utf-8")
    try:
        source = scratch / "source"
        for relative in ("src", "docs", "schemas/v1", "tests/unit/templates"):
            shutil.copytree(
                ROOT / relative,
                source / relative,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        copied_test = source / "tests/unit/templates/test_assets.py"
        assert digest(copied_test) == preserved[ROOT / "tests/unit/templates/test_assets.py"]
        suite = [sys.executable, "-B", "-m", "unittest", "discover", "-s",
                 "tests/unit/templates/", "-p", "test_*.py"]
        note("CASE 1: unmodified copied source and unchanged owned suite")
        baseline = command(suite, source, 0)
        assert "Ran 10 tests" in baseline and "OK" in baseline

        ai = source / "src/ai.py"
        original_ai = ai.read_bytes()
        anchor = b"from __future__ import annotations\n"
        normalized_ai = original_ai.replace(b"\r\n", b"\n")
        assert normalized_ai.count(anchor) == 1
        ai.write_bytes(normalized_ai.replace(
            anchor, anchor + b"\nimport closure_assessment_helper\n", 1
        ))
        (source / "src/closure_assessment_helper.py").write_bytes(
            b"from closure_assessment_leaf import VALUE\n"
        )
        (source / "src/closure_assessment_leaf.py").write_bytes(b"VALUE = 37\n")
        (source / "src/closure_assessment_unused.py").write_bytes(
            b'raise RuntimeError("unreachable sentinel must not ship")\n'
        )
        note("CASE 2: copied ai.py imports helper; helper imports leaf; unused module remains unreachable")
        growth = command(suite, source, 1)
        assert "Ran 10 tests" in growth and "FAILED (failures=1)" in growth
        assert "Items in the first set but not the second" in growth
        assert "closure_assessment_helper.py" in growth and "closure_assessment_leaf.py" in growth

        probe = r'''
import hashlib, json, sys
from pathlib import Path
source = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(source / "src"))
import assets, install
from contracts import load_contract_registry
registry = load_contract_registry(source / "schemas/v1")
expected = set(json.loads(sys.argv[2]))
for assistant, root in (("codex", assets.ProviderRoot.CODEX), ("claude", assets.ProviderRoot.CLAUDE)):
    catalog = assets.build_owned_asset_catalog(source, root, registry=registry)
    managed, seeds, namespace, _ = install._planned_payload(source, source / "synthetic", assistant)
    managed.pop(namespace + "/framework/manifest.json")
    actual = {item.path.as_wire(): item.content for item in catalog.framework_assets}
    assert actual == managed
    assert {item.path.as_wire() for item in catalog.seed_assets} == set(seeds)
    names = {Path(item.path.as_wire()).name for item in catalog.framework_assets if item.path.as_wire().startswith(namespace + "/tools/")}
    assert names == expected, (names, expected)
    assert "closure_assessment_unused.py" not in names
    assert {"ai.py", "contracts.py", "domain_values.py", "validate_foundation.py"} <= names
    assets.verify_asset_manifest(catalog.manifest_record, catalog, registry)
    for item in catalog.framework_assets:
        if item.path.as_wire().startswith(namespace + "/tools/"):
            path = source.parent / "emitted" / item.path.as_wire()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(item.content)
            assert hashlib.sha256(item.content).hexdigest() == str(item.sha256)
    print(json.dumps({"assistant": assistant, "tool_names": sorted(names), "managed_parity": True, "seed_destinations_equal": True, "manifest_verified": True, "fixed_exclusion_would_fail_for": sorted(names & {"assets.py", "workflow_ports.py", "install.py"})}))
print("Imported implementation origins: " + json.dumps({"assets": assets.__file__, "install": install.__file__}))
'''
        base_names = {"ai.py", "contracts.py", "domain_values.py", "validate_foundation.py"}
        grown_names = base_names | {"closure_assessment_helper.py", "closure_assessment_leaf.py"}
        command([sys.executable, "-B", "-c", probe, str(source), json.dumps(sorted(grown_names))], source, 0)
        command([sys.executable, "-I", "-B", "-c", "import runpy, sys; from pathlib import Path; tools = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(tools)); sys.argv = [str(tools / 'ai.py'), '--help']; runpy.run_path(sys.argv[0], run_name='__main__')", str(scratch / "emitted/.codex/tools")], scratch, 0)

        note("CASE 3: additionally make existing assets and workflow_ports modules reachable")
        ai.write_bytes(ai.read_bytes().replace(
            anchor, anchor + b"\nimport assets\nimport workflow_ports\n", 1
        ))
        named_growth = command(suite, source, 1)
        assert "Ran 10 tests" in named_growth and "FAILED (failures=1)" in named_growth
        named_names = grown_names | {"assets.py", "workflow_ports.py"}
        command([sys.executable, "-B", "-c", probe, str(source), json.dumps(sorted(named_names))], source, 0)
        command([sys.executable, "-I", "-B", "-c", "import runpy, sys; from pathlib import Path; tools = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(tools)); sys.argv = [str(tools / 'ai.py'), '--help']; runpy.run_path(sys.argv[0], run_name='__main__')", str(scratch / "emitted/.codex/tools")], scratch, 0)
        assert digest(copied_test) == preserved[ROOT / "tests/unit/templates/test_assets.py"]
        note("Owned test bytes were unchanged throughout all copied-source cases.")
    finally:
        resolved = scratch.resolve(strict=True)
        assert resolved.parent == local and resolved.name.startswith("task005-future-closure-")
        assert marker.read_text(encoding="utf-8") == "/root/assess_005_closure"
        assert not resolved.is_symlink()
        shutil.rmtree(resolved)
        assert not scratch.exists()
        note("Removed only the verified owned temporary directory: " + str(resolved))

    changed = [str(path.relative_to(ROOT)) for path, before in preserved.items() if not path.is_file() or digest(path) != before]
    assert not changed, changed
    note("All snapshotted existing review/source/control/handoff bytes remain unchanged.")
    assert command(["git", "rev-parse", "HEAD"], ROOT, 0).strip() == EXPECTED_HEAD
    command(["git", "diff", "--exit-code", "HEAD", "--"], ROOT, 0)
    note("Assessment proof completed; no task candidate, R1/R2 verdict, or graph transition produced.")


if __name__ == "__main__":
    try:
        main()
    finally:
        output = Path(__file__).with_suffix(".txt")
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(LOG) + "\n")

