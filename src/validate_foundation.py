"""Validate installed AI workload records and this repository's foundation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

_SCRIPT_PATH = Path(__file__).resolve()
_INSTALLED_NAMESPACE = (
    _SCRIPT_PATH.parent.parent.name
    if _SCRIPT_PATH.parent.name == "tools"
    and _SCRIPT_PATH.parent.parent.name in {".codex", ".claude", ".ai"}
    else None
)

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    dependency_command = (
        f"python -m pip install -r {_INSTALLED_NAMESPACE}/requirements.txt"
        if _INSTALLED_NAMESPACE is not None
        else 'python -m pip install -e ".[dev]"'
    )
    raise SystemExit(
        f"Install the validation dependency with: {dependency_command}"
    ) from exc

from ai import structural_task_digest

PLAN_BUCKETS = ("current", "completed", "archived")
TASK_BUCKETS = ("current", "completed", "archived")
RECORD_NAMESPACES = (".codex", ".claude", ".ai")
SKIP_DIRECTORIES = {
    ".git",
    ".worktrees",
    ".venv",
    "generated",
    "__pycache__",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "local",
}
LEGACY_AI_DIRECTORIES = ("tasks", "specs", "graphs", "reviews", "archive")


class ValidationFailure(RuntimeError):
    """One or more foundation invariants failed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationFailure(message)


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"Cannot read JSON {path}: {exc}") from exc
    _require(isinstance(value, dict), f"Expected object in {path}")
    return value


def _default_root() -> Path:
    script = Path(__file__).resolve()
    if script.parent.name == "tools" and script.parent.parent.name in RECORD_NAMESPACES:
        return script.parents[2]
    return script.parents[1]


def _records_root(root: Path) -> Path:
    matches = [
        root / name
        for name in RECORD_NAMESPACES
        if (root / name / "STATE.json").is_file()
        and (root / name / "framework.json").is_file()
    ]
    _require(
        bool(matches),
        f"{root}: no installed .codex, .claude, or legacy .ai workflow records",
    )
    _require(len(matches) == 1, f"{root}: multiple workflow namespaces are not supported")
    return matches[0]


def _walk_files(root: Path, suffix: str, *, skip_history: bool = False) -> Iterator[Path]:
    """Walk children with name-based pruning; ancestors of root never affect discovery."""
    for directory, names, files in os.walk(root):
        base = Path(directory)
        relative_parts = base.relative_to(root).parts
        names[:] = [
            name
            for name in names
            if name not in SKIP_DIRECTORIES
            and not (skip_history and (name == "history" or "history" in relative_parts))
        ]
        for name in files:
            if name.endswith(suffix):
                yield base / name


def _schema_root(root: Path, records: Path, source_foundation: bool) -> Path:
    source = root / "schemas" / "v1"
    installed = records / "framework" / "schemas" / "v1"
    if source_foundation and source.is_dir():
        return source
    if installed.is_dir():
        return installed
    raise ValidationFailure("Cannot locate schemas/v1 or installed workflow schemas")


def _schemas(root: Path, records: Path, source_foundation: bool) -> dict[str, dict[str, Any]]:
    result = {
        path.stem.removesuffix(".schema"): _read(path)
        for path in sorted(_schema_root(root, records, source_foundation).glob("*.schema.json"))
    }
    _require(bool(result), "No JSON schemas found")
    for name, schema in result.items():
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            raise ValidationFailure(f"Invalid JSON Schema {name}: {exc}") from exc
    return result


def _validate_agent_models(
    models: dict[str, Any], guide_stems: set[str], namespace: str
) -> None:
    providers = models["providers"]
    roles = models["roles"]
    _require(
        set(roles) == guide_stems,
        f"agent-models role guide mapping mismatch: {set(roles) ^ guide_stems}",
    )
    for provider_name, provider in providers.items():
        profiles = provider["profiles"]
        model_ranks: dict[str, int] = {}
        for profile_name, profile in profiles.items():
            model_id = profile["model_id"]
            capability_rank = profile["capability_rank"]
            previous_rank = model_ranks.setdefault(model_id, capability_rank)
            _require(
                previous_rank == capability_rank,
                f"agent-models {provider_name} assigns different ranks to {model_id}",
            )
            if provider_name == "openai":
                _require(
                    profile["effort"] is None,
                    f"agent-models openai profile {profile_name} must leave effort null",
                )
            if provider_name == "anthropic":
                _require(
                    profile["reasoning_effort"] is None,
                    f"agent-models anthropic profile {profile_name} must leave reasoning_effort null",
                )
        for role_name, role in roles.items():
            _require(
                role[provider_name] in profiles,
                f"agent-models role {role_name} references unknown {provider_name} profile",
            )
        for policy_name, profile_name in models["policy_profile_map"].items():
            _require(
                profile_name in profiles,
                f"agent-models policy profile {policy_name} references unknown "
                f"{provider_name} profile",
            )
        implementation_name = models["policy_profile_map"]["implementation"]
        review_name = models["policy_profile_map"]["review_high"]
        _require(
            profiles[review_name]["capability_rank"]
            > profiles[implementation_name]["capability_rank"],
            f"agent-models {provider_name} review_high must outrank implementation",
        )
    expected_provider = {".codex": "openai", ".claude": "anthropic"}.get(namespace)
    if expected_provider is not None:
        _require(
            models["active_provider"] == expected_provider,
            f"agent-models active_provider must be {expected_provider} in {namespace}",
        )


def _validate_artifact(
    path: Path, schemas: dict[str, dict[str, Any]], counts: dict[str, int]
) -> dict[str, Any]:
    artifact = _read(path)
    kind = artifact.get("kind")
    _require(isinstance(kind, str) and kind in schemas, f"Unknown artifact kind in {path}: {kind!r}")
    try:
        Draft202012Validator(schemas[kind], format_checker=FormatChecker()).validate(artifact)
    except Exception as exc:
        raise ValidationFailure(f"Schema validation failed for {path}: {exc}") from exc
    counts["validated_artifacts"] += 1
    return artifact


def _reference(root: Path, value: str, *, owner: str, within: Path | None = None) -> Path:
    candidate = (root / value).resolve(strict=False)
    root_resolved = root.resolve(strict=False)
    _require(candidate.is_relative_to(root_resolved), f"{owner}: reference escapes project: {value}")
    _require(candidate.is_file(), f"{owner}: missing reference {value}")
    if within is not None:
        _require(
            candidate.is_relative_to(within.resolve(strict=False)),
            f"{owner}: plan-owned reference leaves its bundle: {value}",
        )
    return candidate


def _overlaps(left: str, right: str) -> bool:
    a, b = left.replace("\\", "/").casefold(), right.replace("\\", "/").casefold()
    return a == b or (a.endswith("/") and b.startswith(a)) or (b.endswith("/") and a.startswith(b))


def _validate_task_locations(tasks: dict[str, tuple[str, dict[str, Any]]], plan_id: str) -> None:
    for task_id, (bucket, task) in tasks.items():
        _require(task["id"] == task_id, f"{plan_id}: task filename/ID mismatch for {task_id}")
        _require(task["plan_id"] == plan_id, f"{plan_id}/{task_id}: wrong plan_id")
        if bucket == "current":
            _require(task["status"] != "completed" and not task["archived"], f"{plan_id}/{task_id}: current status mismatch")
        elif bucket == "completed":
            _require(task["status"] == "completed" and not task["archived"], f"{plan_id}/{task_id}: completed status mismatch")
        else:
            _require(bool(task["archived"]), f"{plan_id}/{task_id}: archived flag must be true")


def _validate_archive_manifests(
    root: Path,
    bundle: Path,
    schemas: dict[str, dict[str, Any]],
    counts: dict[str, int],
) -> None:
    history = bundle / "history"
    if not history.is_dir():
        return
    for revision in sorted(path for path in history.iterdir() if path.is_dir()):
        files = list(_walk_files(revision, ""))
        if not files:
            continue
        manifest_path = revision / "manifest.json"
        _require(manifest_path.is_file(), f"{revision.relative_to(root)}: missing archive manifest")
        manifest = _validate_artifact(manifest_path, schemas, counts)
        _require(manifest["plan_id"] == bundle.name, f"{manifest_path}: wrong plan_id")
        listed = set()
        for entry in manifest["artifacts"]:
            artifact_path = (revision / entry["path"]).resolve(strict=False)
            _require(
                artifact_path.is_relative_to(revision.resolve(strict=False)),
                f"{manifest_path}: archive entry escapes its snapshot root: {entry['path']}",
            )
            _require(
                artifact_path.is_file(),
                f"{manifest_path}: missing snapshot artifact {entry['path']}",
            )
            _require(artifact_path != manifest_path, f"{manifest_path}: manifest cannot hash itself")
            digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            _require(digest == entry["sha256"], f"{manifest_path}: stale hash for {entry['path']}")
            listed.add(artifact_path)
        actual = {path.resolve() for path in files if path != manifest_path}
        _require(actual == listed, f"{manifest_path}: archive membership mismatch")
        counts["archive_manifests"] += 1


def _validate_plan(
    root: Path,
    bucket: str,
    bundle: Path,
    schemas: dict[str, dict[str, Any]],
    counts: dict[str, int],
) -> str:
    plan = _validate_artifact(bundle / "plan.json", schemas, counts)
    plan_id = str(plan["id"])
    _require(bundle.name == plan_id, f"{bundle}: directory/plan ID mismatch")
    if bucket == "current":
        _require(plan["status"] != "completed" and not plan["archived"], f"{plan_id}: current status mismatch")
    elif bucket == "completed":
        _require(plan["status"] == "completed" and not plan["archived"], f"{plan_id}: completed status mismatch")
    else:
        _require(bool(plan["archived"]), f"{plan_id}: archived flag must be true")

    for value in plan["spec_refs"]:
        _reference(root, value, owner=plan_id, within=bundle)
    _reference(root, plan["document_ref"], owner=plan_id, within=bundle)
    graph_path = _reference(root, plan["graph_ref"], owner=plan_id, within=bundle)
    for value in plan["adr_refs"] + plan["research_refs"]:
        _reference(root, value, owner=plan_id)
    if plan["isolation_review_ref"] is not None:
        _reference(root, plan["isolation_review_ref"], owner=plan_id, within=bundle)

    spec_paths = sorted({root / value for value in plan["spec_refs"]})
    for path in spec_paths:
        spec = _validate_artifact(path, schemas, counts)
        _reference(root, spec["document_ref"], owner=f"{plan_id}/{spec['id']}", within=bundle)

    tasks: dict[str, tuple[str, dict[str, Any]]] = {}
    for task_bucket in TASK_BUCKETS:
        directory = bundle / "tasks" / task_bucket
        _require(directory.is_dir(), f"{plan_id}: missing tasks/{task_bucket}")
        for path in sorted(directory.glob("TASK-*.json")):
            task = _validate_artifact(path, schemas, counts)
            task_id = str(task["id"])
            _require(path.stem == task_id, f"{plan_id}: task filename/ID mismatch {path.name} != {task_id}")
            _require(task_id not in tasks, f"{plan_id}: duplicate local task ID {task_id}")
            tasks[task_id] = (task_bucket, task)
    _validate_task_locations(tasks, plan_id)
    live_tasks = {task_id: task for task_id, (location, task) in tasks.items() if location != "archived"}
    _require(set(plan["task_ids"]) == set(live_tasks), f"{plan_id}: plan/task membership mismatch")

    commands: dict[str, dict[str, Any]] = {}
    command_dir = bundle / "commands"
    _require(command_dir.is_dir(), f"{plan_id}: missing commands directory")
    for path in sorted(command_dir.glob("*.json")):
        command = _validate_artifact(path, schemas, counts)
        command_id = str(command["id"])
        _require(command_id not in commands, f"{plan_id}: duplicate command ID {command_id}")
        _require(path.name == f"{command_id}.json", f"{plan_id}: command filename mismatch {path.name}")
        commands[command_id] = command

    for task_id, task in live_tasks.items():
        for value in task["spec_refs"]:
            _reference(root, value, owner=f"{plan_id}/{task_id}", within=bundle)
        for value in task["adr_refs"] + task["research_refs"]:
            _reference(root, value, owner=f"{plan_id}/{task_id}")
        for command_id in task["validation_commands"]:
            _require(command_id in commands, f"{plan_id}/{task_id}: missing local command {command_id}")

    graph = _validate_artifact(graph_path, schemas, counts)
    _require(graph["plan_id"] == plan_id, f"{plan_id}: graph belongs to another plan")
    nodes = {node["task_id"]: node["depends_on"] for node in graph["nodes"]}
    _require(len(nodes) == len(graph["nodes"]), f"{plan_id}: duplicate graph node")
    _require(set(nodes) == set(live_tasks), f"{plan_id}: graph/task membership mismatch")
    ancestors: dict[str, set[str]] = {}

    def visit(task_id: str, trail: set[str]) -> set[str]:
        _require(task_id not in trail, f"{plan_id}: cycle involving {task_id}")
        if task_id in ancestors:
            return ancestors[task_id]
        _require(task_id in live_tasks, f"{plan_id}: missing dependency {task_id}")
        result: set[str] = set()
        for dependency in live_tasks[task_id]["depends_on"]:
            _require(dependency in live_tasks, f"{plan_id}/{task_id}: unknown dependency {dependency}")
            result.add(dependency)
            result.update(visit(dependency, trail | {task_id}))
        ancestors[task_id] = result
        return result

    for task_id, task in live_tasks.items():
        _require(task["depends_on"] == nodes[task_id], f"{plan_id}/{task_id}: graph dependency mismatch")
        _require(len(task["depends_on"]) == len(set(task["depends_on"])), f"{plan_id}/{task_id}: duplicate dependency")
        _require(len(task["acceptance_criteria"]) <= 3, f"{plan_id}/{task_id}: needs size review")
        visit(task_id, set())

    ids = sorted(live_tasks)
    for index, left in enumerate(ids):
        for right in ids[index + 1 :]:
            if left in ancestors[right] or right in ancestors[left]:
                continue
            counts["unordered_pairs_checked"] += 1
            left_scope, right_scope = live_tasks[left]["scope"], live_tasks[right]["scope"]
            for left_path in left_scope["write_paths"]:
                for right_path in right_scope["write_paths"] + right_scope["read_paths"]:
                    _require(not _overlaps(left_path, right_path), f"{plan_id}: unordered overlap {left}:{left_path} {right}:{right_path}")
            for right_path in right_scope["write_paths"]:
                for left_path in left_scope["read_paths"]:
                    _require(not _overlaps(right_path, left_path), f"{plan_id}: unordered overlap {right}:{right_path} {left}:{left_path}")
            _require(
                not set(left_scope["resources"]) & set(right_scope["resources"]),
                f"{plan_id}: unordered resource overlap {left}/{right}",
            )

    expected = {criterion["id"] for criterion in plan["acceptance_criteria"]}
    covered = {value for task in live_tasks.values() for value in task["plan_acceptance_ids"]}
    _require(expected == covered, f"{plan_id}: acceptance coverage mismatch {expected ^ covered}")
    digest = structural_task_digest(list(live_tasks.values()))
    _require(graph["task_set_sha256"] == digest, f"{plan_id}: stale structural task digest")
    if graph["status"] == "approved":
        _require(bool(graph["review_ref"]), f"{plan_id}: approved graph has no review")
        review_path = _reference(root, graph["review_ref"], owner=plan_id, within=bundle)
        report = _validate_artifact(review_path, schemas, counts)
        _require(report["verdict"] == "pass", f"{plan_id}: graph review did not pass")
        _require(report["task_set_sha256"] == digest, f"{plan_id}: review digest mismatch")
        _require(report["graph_revision"] == graph["revision"], f"{plan_id}: review revision mismatch")
        _require(plan["isolation_review_ref"] == graph["review_ref"], f"{plan_id}: review reference mismatch")
    else:
        _require(graph["review_ref"] is None, f"{plan_id}: unapproved graph cannot reuse a review")
        _require(plan["isolation_review_ref"] is None, f"{plan_id}: plan cannot reuse an isolation review")

    for evidence in sorted((bundle / "evidence").glob("*.json")):
        _validate_artifact(evidence, schemas, counts)
    _validate_archive_manifests(root, bundle, schemas, counts)
    counts["tasks"] += len(tasks)
    counts["plans"] += 1
    return plan_id


def _installed_manifest(
    root: Path,
    framework: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
    counts: dict[str, int],
) -> tuple[dict[str, Any], list[Path]]:
    manifest_ref = framework.get("manifest_ref")
    _require(isinstance(manifest_ref, str), "Installed framework has no manifest_ref")
    manifest_path = _reference(root, manifest_ref, owner="framework installation")
    manifest = _validate_artifact(manifest_path, schemas, counts)
    managed_paths: list[Path] = []
    for asset in manifest["assets"]:
        path = _reference(root, asset["path"], owner="framework manifest")
        _require(
            hashlib.sha256(path.read_bytes()).hexdigest() == asset["sha256"],
            f"framework manifest: stale hash for {asset['path']}",
        )
        managed_paths.append(path)
    return manifest, managed_paths


def _validate_links(
    root: Path,
    records: Path,
    counts: dict[str, int],
    source_foundation: bool,
    managed_paths: Sequence[Path],
) -> None:
    if source_foundation:
        markdown = _walk_files(root, ".md", skip_history=True)
    else:
        entry_name = "CLAUDE.md" if records.name == ".claude" else "AGENTS.md"
        entry_paths = [records / "README.md", records / entry_name]
        markdown = iter(
            sorted(
                {
                    path
                    for path in [*managed_paths, *entry_paths]
                    if path.suffix.lower() == ".md" and path.is_file()
                }
            )
        )
    for path in markdown:
        _validate_markdown_links(root, path, counts)


def _validate_markdown_links(root: Path, path: Path, counts: dict[str, int]) -> None:
    content = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
    for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", content):
        if "://" in target or target.startswith("#"):
            continue
        destination = target.split("#", 1)[0]
        if destination:
            link_base = root / "docs" if path.parent == root / "docs" / "defaults" else path.parent
            _require((link_base / destination).exists(), f"{path.relative_to(root)}: broken link {target}")
            counts["local_links"] += 1


def validate(root: Path) -> dict[str, int]:
    root = root.resolve()
    records = _records_root(root)
    framework_preview = _read(records / "framework.json")
    source_foundation = framework_preview.get("installation_status") == "source_foundation"
    schemas = _schemas(root, records, source_foundation)
    counts = {
        "schemas": len(schemas),
        "validated_artifacts": 0,
        "plans": 0,
        "tasks": 0,
        "unordered_pairs_checked": 0,
        "archive_manifests": 0,
        "local_links": 0,
    }
    examples = root / "schemas" / "examples"
    if source_foundation and examples.is_dir():
        for path in sorted(examples.glob("*.json")):
            _validate_artifact(path, schemas, counts)

    shared = {
        "state": records / "STATE.json",
        "framework": records / "framework.json",
        "policy": records / "project" / "policy.json",
        "decisions": records / "decisions" / "index.json",
    }
    shared_records: dict[str, dict[str, Any]] = {}
    for name, path in shared.items():
        _require(path.is_file(), f"Missing shared record {path.relative_to(root)}")
        shared_records[name] = _validate_artifact(path, schemas, counts)
    state_record = shared_records["state"]
    expected_state_refs = {
        "framework_ref": shared["framework"],
        "policy_ref": shared["policy"],
        "decision_index_ref": shared["decisions"],
    }
    for field, expected_path in expected_state_refs.items():
        expected_ref = expected_path.relative_to(root).as_posix()
        _require(
            state_record[field] == expected_ref,
            f"STATE {field} must reference {expected_ref}",
        )
        _reference(root, state_record[field], owner=f"STATE.{field}")
    decision_ids: set[str] = set()
    for decision in shared_records["decisions"]["decisions"]:
        decision_id = str(decision["id"])
        _require(decision_id not in decision_ids, f"duplicate decision ID {decision_id}")
        decision_ids.add(decision_id)
        _reference(root, decision["document_ref"], owner=decision_id, within=records / "decisions")
    managed_paths: list[Path] = []
    agent_model_records: list[dict[str, Any]] = []
    guide_stems: set[str] = set()
    if source_foundation:
        for name in ("STATE.json", "FRAMEWORK.json", "POLICY.json", "DECISIONS.json"):
            _validate_artifact(root / "docs" / "defaults" / name, schemas, counts)
        models_path = root / "docs" / "defaults" / "AGENT_MODELS.json"
        _require(models_path.is_file(), "Missing docs/defaults/AGENT_MODELS.json")
        agent_model_records.append(_validate_artifact(models_path, schemas, counts))
        source_models_path = records / "project" / "agent-models.json"
        if source_models_path.exists():
            _reference(
                root,
                source_models_path.relative_to(root).as_posix(),
                owner="source agent-models configuration",
            )
            agent_model_records.append(
                _validate_artifact(source_models_path, schemas, counts)
            )
        guide_stems = {
            path.stem
            for path in (root / "docs" / "agents").glob("*.md")
            if path.name != "README.md"
        }
    else:
        _, managed_paths = _installed_manifest(root, framework_preview, schemas, counts)
        models_path = records / "project" / "agent-models.json"
        requires_agent_models = records.name == ".codex" or any(
            path.name == "agent-models.schema.json"
            and path.parent.name == "v1"
            and path.parent.parent.name == "schemas"
            for path in managed_paths
        )
        _require(
            not requires_agent_models or models_path.is_file(),
            f"Missing required agent-models configuration {models_path.relative_to(root)}",
        )
        if models_path.exists():
            _reference(
                root,
                models_path.relative_to(root).as_posix(),
                owner="agent-models configuration",
            )
            agent_model_records.append(_validate_artifact(models_path, schemas, counts))
            guide_stems = {
                path.stem
                for path in managed_paths
                if path.parent == records / "agents"
                and path.suffix.lower() == ".md"
                and path.name != "README.md"
            }
    for agent_models in agent_model_records:
        _validate_agent_models(agent_models, guide_stems, records.name)
    for path in sorted((records / "research").glob("*.json")):
        _validate_artifact(path, schemas, counts)

    for name in LEGACY_AI_DIRECTORIES:
        _require(not (records / name).exists(), f"Legacy plan data directory remains: {records.name}/{name}")

    registries: dict[str, set[str]] = {bucket: set() for bucket in PLAN_BUCKETS}
    for bucket in PLAN_BUCKETS:
        directory = records / "plans" / bucket
        _require(directory.is_dir(), f"Missing plan lifecycle directory {records.name}/plans/{bucket}")
        for bundle in sorted(path for path in directory.iterdir() if path.is_dir()):
            plan_id = _validate_plan(root, bucket, bundle, schemas, counts)
            _require(plan_id not in registries[bucket], f"Duplicate {bucket} plan {plan_id}")
            registries[bucket].add(plan_id)
    all_plan_ids = [plan_id for values in registries.values() for plan_id in values]
    _require(len(all_plan_ids) == len(set(all_plan_ids)), "A plan appears in multiple lifecycle directories")

    state = state_record
    _require(set(state["active_plans"]) == registries["current"], "STATE active_plans registry mismatch")
    _require(set(state["completed_plans"]) == registries["completed"], "STATE completed_plans registry mismatch")
    _require(set(state["archived_plans"]) == registries["archived"], "STATE archived_plans registry mismatch")

    if source_foundation:
        _require(not (root / "src" / "ai_engineering").exists(), "src/ai_engineering package layer must not exist")
        _require((root / "src" / "ai.py").is_file(), "Missing flat src/ai.py")
        _require((root / "src" / "install.py").is_file(), "Missing flat src/install.py")
        _require((root / "src" / "validate_foundation.py").is_file(), "Missing flat validator")
    _validate_links(root, records, counts, source_foundation, managed_paths)
    return counts


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate AI workload records and foundation links")
    parser.add_argument("--project", default=str(_default_root()), help="project root")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = validate(Path(args.project))
    except ValidationFailure as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
