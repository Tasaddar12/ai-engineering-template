"""Read-only reproduction of PLAN-001 graph r4 isolation identities/checks."""
from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "src"))
from ai import structural_task_digest

BUNDLE = ROOT / ".ai/plans/current/PLAN-001"
graph_path = BUNDLE / "graph.json"
graph = json.loads(graph_path.read_text(encoding="utf-8"))
tasks = {
    path.stem: json.loads(path.read_text(encoding="utf-8"))
    for path in sorted((BUNDLE / "tasks/current").glob("TASK-*.json"))
}
ancestors: dict[str, set[str]] = {}


def visit(task_id: str, trail: frozenset[str] = frozenset()) -> set[str]:
    assert task_id not in trail, f"cycle: {task_id}"
    if task_id not in ancestors:
        result: set[str] = set()
        for dependency in tasks[task_id]["depends_on"]:
            result.add(dependency)
            result.update(visit(dependency, trail | {task_id}))
        ancestors[task_id] = result
    return ancestors[task_id]


def normalize(path: str) -> str:
    return unicodedata.normalize("NFC", path.replace("\\", "/")).casefold()


def overlaps(left: str, right: str) -> bool:
    left, right = normalize(left), normalize(right)
    return left == right or (left.endswith("/") and right.startswith(left)) or (
        right.endswith("/") and left.startswith(right)
    )


for task_id in tasks:
    visit(task_id)
assert {node["task_id"]: node["depends_on"] for node in graph["nodes"]} == {
    task_id: task["depends_on"] for task_id, task in tasks.items()
}
conflicts = []
unordered = 0
ids = sorted(tasks)
for index, left in enumerate(ids):
    for right in ids[index + 1:]:
        if left in ancestors[right] or right in ancestors[left]:
            continue
        unordered += 1
        ls, rs = tasks[left]["scope"], tasks[right]["scope"]
        for owner, paths, peer, peer_paths in (
            (left, ls["write_paths"], right, rs["write_paths"] + rs["read_paths"]),
            (right, rs["write_paths"], left, ls["read_paths"]),
        ):
            for path in paths:
                for peer_path in peer_paths:
                    if overlaps(path, peer_path):
                        conflicts.append([owner, path, peer, peer_path])
        if set(ls["resources"]) & set(rs["resources"]):
            conflicts.append([left, right, "resource"])
assert not conflicts, conflicts
plan = json.loads((BUNDLE / "plan.json").read_text(encoding="utf-8"))
coverage = {
    criterion["id"]: [task_id for task_id, task in tasks.items()
                      if criterion["id"] in task["plan_acceptance_ids"]]
    for criterion in plan["acceptance_criteria"]
}
assert all(coverage.values())
command_checks = {}
for task_id, task in tasks.items():
    command = json.loads((BUNDLE / "commands" / f"test.{task_id}.json").read_text())
    command_checks[task_id] = (
        command["success_rule"] == "unittest_nonzero_count"
        and command["shell"] is False
        and any(command["argv"][5].startswith(path) for path in task["scope"]["write_paths"])
    )
assert all(command_checks.values())
files = [graph_path, BUNDLE / "plan.json", BUNDLE / "spec.json"]
files += sorted((BUNDLE / "tasks/current").glob("TASK-*.json"))
files += sorted((BUNDLE / "commands").glob("*.json"))
files += [ROOT / ".ai/shared/architecture/service-contracts.md", ROOT / "src/ai.py",
          ROOT / "src/install.py", ROOT / "src/validate_foundation.py"]
print(json.dumps({
    "graph_id": graph["id"],
    "graph_raw_sha256": hashlib.sha256(graph_path.read_bytes()).hexdigest(),
    "graph_canonical_sha256": hashlib.sha256(json.dumps(graph, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest(),
    "task_structural_sha256": structural_task_digest(list(tasks.values())),
    "declared_task_structural_sha256": graph["task_set_sha256"],
    "task_count": len(tasks), "unordered_pairs_checked": unordered,
    "conflicts": conflicts, "command_checks": command_checks,
    "acceptance_coverage": coverage,
    "raw_file_hashes": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in files},
}, indent=2))
