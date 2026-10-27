"""Frontmatter access and structural validation."""
from .core import Failure, pick, planning_lock, read, safe_path, write
from .text import join_frontmatter, scalar, split_frontmatter

SCHEMAS = {
    "plan": {"phase": (str, int), "plan": (str, int), "type": str, "wave": int,
             "depends_on": list, "files_modified": list, "autonomous": bool, "must_haves": dict},
    "summary": {"phase": (str, int), "plan": (str, int), "status": str},
    "verification": {"status": str},
}


def errors(metadata, schema):
    if schema not in SCHEMAS:
        raise Failure("unknown-schema", schema, 2)
    result = []
    if schema == "verification" and not any(isinstance(metadata.get(key), (str, int)) and not isinstance(metadata.get(key), bool) for key in ("phase", "quick")):
        result.append("Verification requires a phase or quick identifier")
    for key, kind in SCHEMAS[schema].items():
        if key not in metadata:
            result.append(f"Missing field: {key}")
        elif not isinstance(metadata[key], kind) or (kind is int and isinstance(metadata[key], bool)):
            result.append(f"Invalid type: {key}")
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
        findings = errors(metadata, args.get("schema", "plan"))
        return {"valid": not findings, "errors": findings}, int(bool(findings))
    with planning_lock():
        metadata, body = split_frontmatter(read(path))
        schema = next((name for name in SCHEMAS if path.name.endswith("-"+name.upper()+".md")), None)
        previous_errors = set(errors(metadata, schema)) if schema else set()
        field = args.get("field", args.arg(1))
        if not field or not args.has("value"):
            raise Failure("missing-argument", "frontmatter.set requires --field and --value", 2)
        from .config import assign
        assign(metadata, field, scalar(str(args.get("value"))))
        introduced = set(errors(metadata, schema))-previous_errors if schema else set()
        if introduced:
            raise Failure("invalid-frontmatter-update", "Field value violates the artifact schema", errors=sorted(introduced))
        write(path, join_frontmatter(metadata, body))
    return {"updated": True, "field": field, "path": str(path)}
