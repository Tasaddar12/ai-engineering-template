"""Frontmatter access and structural validation."""
import re
from .core import Failure, pick, planning_lock, read, root, safe_path, write
from .text import join_frontmatter, scalar, split_frontmatter

SCHEMAS = {
    "plan": {"plan": (str, int), "type": str, "wave": int,
             "depends_on": list, "files_modified": list, "files_deleted": list, "resources": list,
             "autonomous": bool, "must_haves": dict,
             "requirements": list, "acceptance": list, "documentation": list, "checks": list, "issue_refs": list},
    "summary": {"plan": (str, int), "status": str, "requirements-completed": list,
                "acceptance": list, "documentation": list, "issue_refs": list},
    "context": {"discussion": str, "issue_refs": list},
    "verification": {"status": str, "covered_digest": str, "covered_files": list},
}


def errors(metadata, schema):
    if schema not in SCHEMAS:
        raise Failure("unknown-schema", schema, 2)
    result = []
    if sum(isinstance(metadata.get(key), (str, int)) and not isinstance(metadata.get(key), bool) for key in ("phase", "quick")) != 1:
        result.append(schema.title()+" requires exactly one phase or quick identifier")
    for key in ("phase", "quick"):
        if key in metadata:
            pattern = r"\d+(?:\.\d+)?(?:-[^\n]+)?" if key == "phase" else r"\d+(?:-[^\n]+)?"
            if isinstance(metadata[key], bool) or not re.fullmatch(pattern, str(metadata[key])):
                result.append("Invalid "+key+" identity")
    for key, kind in SCHEMAS[schema].items():
        if key not in metadata:
            result.append(f"Missing field: {key}")
        elif not isinstance(metadata[key], kind) or (kind is int and isinstance(metadata[key], bool)):
            result.append(f"Invalid type: {key}")
    # A field belonging to another artifact kind is still typed when present;
    # stray metadata cannot hide declarations from a later consumer.
    list_fields = {key for fields in SCHEMAS.values() for key, kind in fields.items() if kind is list}
    for key in list_fields - set(SCHEMAS[schema]):
        if key in metadata and not isinstance(metadata[key], list):
            result.append(f"Invalid type: {key}")
    if "plan" in metadata and isinstance(metadata["plan"], bool):
        result.append("Invalid type: plan")
    if schema == "plan" and isinstance(metadata.get("wave"), int) and metadata["wave"] < 1:
        result.append("wave must be a positive integer")
    if isinstance(metadata.get("issue_refs"), list):
        for index, entry in enumerate(metadata["issue_refs"]):
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not entry["id"].strip():
                result.append(f"issue_refs[{index}] requires an identified finding mapping")
            elif entry.get("state") == "pending-human" and entry.get("relationship", "followup") != "followup":
                result.append(f"issue_refs[{index}] pending human acceptance requires followup")
    if schema == "context" and metadata.get("discussion") not in ("pending", "complete"):
        result.append("Discussion must be pending or complete; only actual captured answers establish completion")
    if schema == "plan" and isinstance(metadata.get("checks"), list):
        for index, check in enumerate(metadata["checks"]):
            argv = check
            if not isinstance(argv, list) or not argv or any(not isinstance(value, str) or not value.strip() for value in argv):
                result.append(f"Check {index+1} requires a nonempty argv array of strings")
    if schema == "plan" and "phase" in metadata and isinstance(metadata.get("requirements"), list) and not metadata["requirements"]:
        result.append("Executable phase PLAN requires owning requirement IDs")
    if schema == "plan" and isinstance(metadata.get("must_haves"), dict):
        for key in ("truths", "artifacts", "key_links"):
            if not isinstance(metadata["must_haves"].get(key), list):
                result.append("must_haves."+key+" requires a list")
    if schema == "verification" and "covered_digest" in metadata and not re.fullmatch(r"v4:sha256:[a-f0-9]{64}", str(metadata["covered_digest"])):
        result.append("covered_digest must use v4:sha256:<64 lowercase hex>")
    return result


def path_errors(path, metadata, schema):
    path = path.resolve()
    planning = root()/".planning"
    if not path.is_relative_to(planning):
        return []
    parts = path.relative_to(planning).parts
    if len(parts) < 3 or parts[0] not in ("phases", "quick"):
        return []
    kind = "quick" if parts[0] == "quick" else "phase"
    expected = parts[1].split("-")[0]
    identifier = str(metadata.get(kind, "")).split("-", 1)[0]
    try:
        matching = tuple(map(int, identifier.split("."))) == tuple(map(int, expected.split(".")))
    except ValueError:
        matching = False
    if kind == "quick":
        # A date prefix is shared by many tasks. Bind the complete owner ID.
        quick_meta, _ = split_frontmatter(read(path.parent/"QUICK.md"))
        actual = str(quick_meta.get("id", parts[1] if re.match(r"^[0-9]{6}-[0-9]{3}-", parts[1]) else expected))
        declared = str(metadata.get("quick", ""))
        matching = declared == actual if not actual.isdigit() else declared.zfill(3) == actual.zfill(3)
    result = [] if matching and ("phase" if kind == "quick" else "quick") not in metadata else ["Record identity disagrees with its actual "+kind+" directory"]
    if kind == "phase" and schema in ("plan", "summary"):
        basename = path.name.removesuffix("-"+schema.upper()+".md")
        plan = str(metadata.get("plan", ""))
        suffix = basename.removeprefix(expected+"-")
        if not plan.isdigit() or not suffix.isdigit() or int(plan) != int(suffix):
            result.append("Plan identity disagrees with artifact basename")
    return result


def command(args, action):
    path = safe_path(args.need())
    if not path.is_file():
        raise Failure("file-not-found", str(path))
    metadata, body = split_frontmatter(read(path))
    if action == "get":
        field = args.get("field", args.arg(1))
        return pick(metadata, field) if field else metadata
    if action == "validate":
        schema = args.get("schema", "plan")
        findings = errors(metadata, schema)+path_errors(path, metadata, schema)
        return {"valid": not findings, "errors": findings}, int(bool(findings))
    with planning_lock():
        metadata, body = split_frontmatter(read(path))
        schema = next((name for name in SCHEMAS if path.name.endswith("-"+name.upper()+".md")), None)
        previous_errors = set(errors(metadata, schema)+path_errors(path, metadata, schema)) if schema else set()
        field = args.get("field", args.arg(1))
        if not field or not args.has("value"):
            raise Failure("missing-argument", "frontmatter.set requires --field and --value", 2)
        from .config import assign
        assign(metadata, field, scalar(str(args.get("value"))))
        introduced = set(errors(metadata, schema)+path_errors(path, metadata, schema))-previous_errors if schema else set()
        if introduced:
            raise Failure("invalid-frontmatter-update", "Field value violates the artifact schema", errors=sorted(introduced))
        write(path, join_frontmatter(metadata, body))
    return {"updated": True, "field": field, "path": str(path)}
