"""Typed artifact frontmatter contracts and bounded field mutations."""
import re
from .core import Failure, pick, planning_lock, read, safe_path, write
from .text import join_frontmatter, scalar, split_frontmatter

SCHEMAS = {
    "plan": {"phase": (str, int), "plan": (str, int), "type": str, "wave": int,
             "depends_on": list, "files_modified": list, "autonomous": bool, "must_haves": dict},
    "summary": {"phase": (str, int), "plan": (str, int), "status": str},
    "verification": {"phase": (str, int), "status": str},
    "context": {"phase": (str, int)}, "research": {"phase": (str, int)},
    "validation": {"phase": (str, int)}, "uat": {"phase": (str, int), "status": str},
    "security": {"phase": (str, int), "status": str}, "review": {"phase": (str, int), "status": str},
    "quick": {"id": (str, int), "description": str, "status": str},
}
OPTIONAL = {
    "plan": {"requirements": list, "acceptance": list, "documentation": list, "resources": list, "checks": list,
             "files_deleted": list, "estimate": dict, "gap_closure": bool, "user_setup": list, "tags": list,
             "threat_model": (dict, list), "task_count": int, "mvp": bool, "reversible": (str, bool)},
    "summary": {"subsystem": (str, list), "tags": list, "requires": list, "provides": list, "affects": list,
                "actuals": dict, "estimate": dict, "tech-stack": dict, "key-files": dict, "key-decisions": list,
                "patterns-established": list, "requirements-completed": list, "coverage": list, "duration": (str, int, float),
                "completed": str, "decisions": list, "metrics": dict, "one_liner": str, "acceptance": list,
                "documentation": list, "plan_head_before": str, "plan_head_after": str, "base_revision": str},
    "verification": {"verified": str, "score": str, "covered_files": list, "covered_digest": str, "revision": str,
                     "behavior_unverified": int, "behavior_unverified_items": list, "coincidental_reliance_items": list,
                     "human_verification": list, "gaps": list, "deferred": list, "advisory": list, "overrides": list,
                     "overrides_applied": (list, int), "re_verification": dict},
    "review": {"reviewed": str, "revision": str, "depth": str, "files_reviewed": int, "files_reviewed_list": list, "findings": dict},
    "context": {"created": str, "updated": str, "status": str, "source": (str, list), "decisions": list},
    "research": {"created": str, "researched": str, "status": str, "domain": str, "confidence": str, "coverage": str},
    "validation": {"slug": str, "status": str, "nyquist_compliant": bool, "wave_0_complete": bool, "created": str, "updated": str},
    "uat": {"source": list, "started": str, "updated": str},
    "security": {"audited": str, "threats_total": int, "threats_open": int, "threats_closed": int, "revision": str},
    "quick": {"created": str, "updated": str, "commit": str, "verification": str, "issue": str, "pr": str,
              "migration_source": str, "source": str, "legacy_row": str},
}
ENUMS = {"plan": {"type": {"execute", "tdd", "quick"}},
         "summary": {"status": {"complete", "blocked", "partial"}},
         "verification": {"status": {"passed", "gaps_found", "human_needed"}},
         "review": {"status": {"clean", "issues_found", "skipped"}},
         "quick": {"status": {"pending", "planned", "in_progress", "blocked", "complete", "passed", "closed"}}}


def _schema(name):
    return "plan" if name == "plan-gap-closure" else name


def errors(metadata, schema):
    gap = schema == "plan-gap-closure"
    schema = _schema(schema)
    if schema not in SCHEMAS:
        raise Failure("unknown-schema", str(schema), 2)
    if not isinstance(metadata, dict):
        return ["Frontmatter must be a mapping"]
    result = []
    fields = {**SCHEMAS[schema], **OPTIONAL.get(schema, {})}
    for key, kind in fields.items():
        if key not in metadata:
            if key in SCHEMAS[schema]:
                result.append("Missing field: "+key)
        elif not isinstance(metadata[key], kind) or isinstance(metadata[key], bool) and kind is not bool and (kind is int or isinstance(kind, tuple) and int in kind):
            result.append("Invalid type: "+key)
    for key in metadata:
        if key not in fields and not key.startswith("x-"):
            # Preserve existing extension data; report unsupported fields rather than discard it.
            result.append("Unknown field: "+key)
    for key, allowed in ENUMS.get(schema, {}).items():
        if key in metadata and (not isinstance(metadata[key], str) or metadata[key] not in allowed):
            result.append("Invalid value: "+key)
    if gap and metadata.get("gap_closure") is not True:
        result.append("gap_closure must be true")
    if "phase" in metadata and not re.fullmatch(r"\d+(?:\.\d+)?(?:-.+)?", str(metadata["phase"])):
        result.append("Invalid phase identifier")
    if "plan" in metadata and not re.fullmatch(r"\d+", str(metadata["plan"])):
        result.append("Invalid plan identifier")
    if schema == "plan":
        wave = metadata.get("wave")
        if isinstance(wave, int) and wave < 1:
            result.append("wave must be positive")
        for field in ("depends_on", "files_modified", "files_deleted", "requirements", "acceptance", "documentation", "resources"):
            value = metadata.get(field, [])
            if isinstance(value, list) and not all(isinstance(item, str) for item in value):
                result.append(field+" must contain text values")
        must = metadata.get("must_haves")
        if isinstance(must, dict):
            if set(must)-{"truths", "artifacts", "key_links"}:
                result.append("Unknown must_haves field")
            for key in ("truths", "artifacts", "key_links"):
                if key not in must or not isinstance(must[key], list):
                    result.append("must_haves."+key+" must be an array")
    if schema == "summary" and isinstance(metadata.get("coverage"), list):
        seen = set()
        for index, item in enumerate(metadata["coverage"]):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item.get("description") or not isinstance(item.get("human_judgment"), bool):
                result.append("Invalid coverage entry: "+str(index))
                continue
            if item["id"] in seen:
                result.append("Duplicate coverage id: "+item["id"])
            seen.add(item["id"])
            if item["human_judgment"] and not item.get("rationale"):
                result.append("Human coverage requires rationale: "+item["id"])
            checks = item.get("verification", [])
            if not isinstance(checks, list) or any(not isinstance(check, dict) or check.get("status") not in ("pass", "fail", "unknown") or not check.get("ref") for check in checks):
                result.append("Invalid coverage verification: "+item["id"])
    if schema == "verification" and metadata.get("status") == "passed":
        if not metadata.get("covered_files") or not (metadata.get("covered_digest") or metadata.get("revision")):
            result.append("Passed verification requires covered_files and revision or covered_digest")
        if metadata.get("human_verification") or metadata.get("gaps") or metadata.get("behavior_unverified", 0):
            result.append("Passed verification cannot contain unresolved gaps or human observations")
    return result


def schema_for(path):
    if path.name == "QUICK.md":
        return "quick"
    return next((name for name in SCHEMAS if path.name.endswith("-"+name.upper()+".md")), None)


def command(args, action):
    if action not in ("get", "set", "validate"):
        raise Failure("unsupported-frontmatter-action", str(action), 2)
    from .planning import safe
    path = safe(safe_path(args.need()))
    if not path.is_file():
        raise Failure("file-not-found", str(path))
    metadata, body = split_frontmatter(read(path))
    if action == "get":
        field = args.get("field", args.arg(1))
        return pick(metadata, field) if field else metadata
    schema = args.get("schema", schema_for(path))
    if action == "validate":
        schema = schema or "plan"
        findings = errors(metadata, schema)
        expected = SCHEMAS[_schema(schema)]
        return {"valid": not findings, "errors": findings, "missing": [key for key in expected if key not in metadata],
                "present": sorted(metadata), "schema": schema}, int(bool(findings))
    with planning_lock():
        metadata, body = split_frontmatter(read(path))
        previous_errors = set(errors(metadata, schema)) if schema else set()
        field = args.get("field", args.arg(1))
        if not field or not args.has("value"):
            raise Failure("missing-argument", "frontmatter.set requires --field and --value", 2)
        root_field = field.split(".")[0]
        allowed = {**SCHEMAS[_schema(schema)], **OPTIONAL.get(_schema(schema), {})} if schema else metadata
        if root_field not in allowed and not root_field.startswith("x-"):
            raise Failure("unknown-frontmatter-field", root_field, 2)
        from .config import assign
        assign(metadata, field, scalar(str(args.get("value"))))
        introduced = set(errors(metadata, schema))-previous_errors if schema else set()
        if introduced:
            raise Failure("invalid-frontmatter-update", "Field value violates the artifact schema", errors=sorted(introduced))
        write(path, join_frontmatter(metadata, body))
    return {"updated": True, "field": field, "path": str(path)}
