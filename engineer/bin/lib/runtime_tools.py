"""Deterministic JSON and command adapters used by complete workflow exports."""
import json
from pathlib import Path
import re
import shlex
import sys
from .core import Failure, input_json, now, pick, read, root, safe_path, write_json
from .text import split_frontmatter


def payload(args):
    if args.has("payload"):
        return args.json("payload")
    if args.has("input") or args.has("file"):
        return input_json(args.get("input", args.get("file")))
    return input_json()


def json_command(args, action):
    if action == "encode-lines":
        return [line for line in sys.stdin.read().splitlines() if line]
    if action == "depth-input":
        return {"flagDepth": args.get("flag-depth"), "configDepth": args.get("config-depth", "standard"),
                "overrides": args.json("overrides", []), "files": sys.stdin.read().splitlines(), "repoRoot": str(root())}
    data = payload(args)
    field = args.get("field", args.arg(0))
    if field:
        try:
            data = pick(data, str(field))
        except Failure:
            if not args.has("default"):
                raise
            try:
                data = json.loads(str(args.get("default")))
            except ValueError:
                data = str(args.get("default"))
    if action in ("get", "read"):
        return data
    if action == "length":
        if not isinstance(data, (list, dict, str)):
            raise Failure("json-type", "Length requires an array, mapping or string", 2)
        return len(data)
    if action == "lines":
        if args.has("pluck"):
            if not isinstance(data, list):
                raise Failure("json-type", "Pluck requires an array", 2)
            data = [pick(item, str(args.get("pluck"))) for item in data]
        if not isinstance(data, list) or any(isinstance(item, (dict, list)) for item in data):
            raise Failure("json-type", "Lines requires scalar array values", 2)
        if args.has("require-nonempty") and not data:
            raise Failure("json-empty", "Expected a nonempty array")
        if any("\n" in str(item) or "\0" in str(item) for item in data):
            raise Failure("json-line-boundary", "Array values contain a line boundary")
        return str(args.get("separator", "\n")).join(str(item) for item in data)
    if action == "commits":
        commits = data.get("commits", []) if isinstance(data, dict) else data
        if not isinstance(commits, list):
            raise Failure("json-type", "Commit evidence must be an array", 2)
        if args.has("first"):
            commits = commits[:1]
        return "\n".join(str(item.get("sha", item.get("hash", "")))[:10]+" "+str(item.get("subject", ""))
                         for item in commits if isinstance(item, dict))
    if action == "status-reason":
        if not isinstance(data, dict):
            raise Failure("json-type", "Status requires a mapping", 2)
        return str(data.get("status", ""))+((": "+str(data["reason"])) if data.get("reason") else "")
    if action == "depth-fields":
        if not isinstance(data, dict):
            raise Failure("json-type", "Review depth requires a mapping", 2)
        matched = data.get("matchedRule") or {}
        fields = [data.get("depth", ""), data.get("source", ""), matched.get("index", ""), matched.get("path", ""),
                  data.get("invalidFlagDepth", False), data.get("invalidConfigDepth", False), data.get("downgraded", False)]
        return "\x1f".join(str(value).lower() if isinstance(value, bool) else str(value) for value in fields)
    if action == "exec-ready":
        return bool(isinstance(data, dict) and data.get("isolation") == "orchestrator-worktree"
                    and isinstance(data.get("exec"), dict) and data["exec"].get("command"))
    if action == "has-section":
        section = str(args.get("section", args.arg(0, "")))
        if not section:
            raise Failure("json-section", "Supply --section", 2)
        manifest = data.get("section_manifest") if isinstance(data, dict) and "section_manifest" in data else data
        if manifest is None:
            return True
        if not isinstance(manifest, dict) or not isinstance(manifest.get("included"), list):
            raise Failure("json-type", "Section manifest must be null or include an array", 2)
        return section in manifest["included"]
    if action == "predicate":
        if args.has("equals"):
            return data == args.json("equals")
        if args.has("includes"):
            if not isinstance(data, (str, list, dict)):
                raise Failure("json-type", "Includes requires a collection", 2)
            return args.get("includes") in data
        if args.has("all-fields"):
            return all(bool(pick(data, name)) for name in args.all("all-fields"))
        return data is not None and data is not False
    if action == "validate":
        schema = args.get("schema")
        if schema == "requirements":
            valid = isinstance(data, list) and bool(data) and all(isinstance(item, dict) and isinstance(item.get("id"), str)
                and item["id"].strip() and isinstance(item.get("text"), str) and item["text"].strip()
                and "<replace:" not in item["text"].lower() for item in data)
        elif schema == "elements":
            valid = isinstance(data, list) and bool(data) and all(isinstance(item, dict) and isinstance(item.get("id"), str)
                and item["id"].strip() and isinstance(item.get("text"), str) and item["text"].strip()
                and "<replace:" not in item["text"].lower() for item in data)
        elif schema == "coverage":
            valid = isinstance(data, dict) and isinstance(data.get("items"), list) and isinstance(data.get("coverage"), dict)
        else:
            raise Failure("unknown-json-schema", str(schema), 2)
        if not valid:
            raise Failure("json-schema", "Input does not satisfy "+schema, 2)
        return {"valid": True, "schema": schema}
    raise Failure("unknown-json-action", action, 2)


def package_manager(args):
    directory = safe_path(args.get("cwd", "."))
    package = directory/"package.json"
    try:
        metadata = json.loads(read(package, "{}"))
    except ValueError as exc:
        raise Failure("invalid-package-json", str(package), 2) from exc
    explicit = str(metadata.get("packageManager", "")).partition("@")[0]
    locks = (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lock", "bun"),
             ("bun.lockb", "bun"), ("package-lock.json", "npm"), ("npm-shrinkwrap.json", "npm"))
    manager = explicit if explicit in ("npm", "pnpm", "yarn", "bun") else next((name for lock, name in locks if (directory/lock).is_file()), "npm")
    script = args.arg(0, "test")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9:_-]*", str(script)):
        raise Failure("invalid-script", str(script), 2)
    scripts = metadata.get("scripts", {})
    if not isinstance(scripts, dict) or script not in scripts:
        raise Failure("package-script-missing", "No project script named "+str(script))
    argv = [manager, "run", script] if manager in ("npm", "bun") else [manager, script]
    if args.has("json"):
        return {"manager": manager, "argv": argv, "command": shlex.join(argv), "cwd": str(directory), "script": scripts[script]}
    return shlex.join(argv)


def normalize_test_command(args):
    command = str(args.need())
    # Shell pipelines are left intact; only a recognized single runner is changed.
    if re.search(r"[;&|`\n]|\$\(", command):
        return command
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise Failure("invalid-test-command", str(exc), 2) from exc
    if not argv:
        raise Failure("empty-test-command", "Supply a command", 2)
    names = {Path(word).name for word in argv}
    if "vitest" in names:
        argv = [word for word in argv if word not in ("--watch", "-w", "--watch=true")]
        position = next(i for i, word in enumerate(argv) if Path(word).name == "vitest")
        if "run" not in argv[position+1:] and "--run" not in argv[position+1:]:
            argv.insert(position+1, "run")
    elif "jest" in names:
        argv = [word for word in argv if word not in ("--watch", "--watchAll", "--watch=true", "--watchAll=true")]
        if "--watch=false" not in argv:
            argv.append("--watch=false")
    elif argv[0] in ("npm", "pnpm", "yarn", "bun"):
        directory = safe_path(args.get("cwd", "."))
        try:
            scripts = json.loads(read(directory/"package.json", "{}" )).get("scripts", {})
        except ValueError as exc:
            raise Failure("invalid-package-json", str(exc), 2) from exc
        script = next((word for word in argv[1:] if word != "run" and not word.startswith("-")), None)
        definition = str(scripts.get(script, ""))
        if "vitest" in definition and "--run" not in argv:
            argv.extend((["--"] if argv[0] == "npm" and "--" not in argv else [])+["--run"])
        elif "jest" in definition and not any(word.startswith("--watch") for word in argv):
            argv.extend((["--"] if argv[0] == "npm" and "--" not in argv else [])+["--watch=false"])
    return shlex.join(argv)


def review_adapter(args, action):
    if action == "normalize-fallow":
        from .fallow_runner import normalize_fallow_report
        data = input_json(None if args.has("stdin") else args.get("input", args.arg(0)))
        if not isinstance(data, dict) or not any(key in data for key in ("dead_code", "duplication")):
            raise Failure("fallow-schema-unrecognized", "Expected a native Fallow report with dead_code or duplication", 2)
        for section, collections in (("dead_code", ("unused_exports", "unused_files", "circular_dependencies")),
                                     ("duplication", ("clone_groups",))):
            content = data.get(section)
            if content is None:
                continue
            if not isinstance(content, dict):
                raise Failure("fallow-schema-unrecognized", section + " must be an object", 2)
            for key in collections:
                collection = content.get(key)
                if collection is not None and (not isinstance(collection, list) or any(not isinstance(item, dict) for item in collection)):
                    raise Failure("fallow-schema-unrecognized", section + "." + key + " must be an array of objects", 2)
                for item in collection or []:
                    for nested in ("files", "instances"):
                        if nested in item and (not isinstance(item[nested], list) or any(not isinstance(value, str if nested == "files" else dict) for value in item[nested])):
                            raise Failure("fallow-schema-unrecognized", key + "." + nested + " has an invalid shape", 2)
        normalized = normalize_fallow_report(data)
        if args.has("output"):
            output = Path(str(args.get("output"))).expanduser()
            if output.is_symlink():
                raise Failure("structural-output-linked", str(output))
            if output.exists() and input_json(output) != normalized:
                raise Failure("structural-output-exists", "Refusing to overwrite a different explicit structural report")
            write_json(output, normalized)
        return normalized
    if action == "normalize-structural":
        data = input_json(args.get("input"))
        if not isinstance(data, dict) or not isinstance(data.get("findings"), list) or not isinstance(data.get("summary"), (str, dict)):
            raise Failure("structural-schema-unrecognized", "Expected a structural report with summary and findings; no findings were discarded", 2)
        findings = data["findings"]
        if any(not isinstance(item, dict) or not any(isinstance(item.get(key), str) and item[key].strip() for key in ("message", "description", "title")) for item in findings):
            raise Failure("structural-finding-unrecognized", "Every finding needs its actual title, description or message", 2)
        normalized = {"summary": data["summary"], "findings": findings}
        if args.has("output"):
            output = Path(str(args.get("output"))).expanduser()
            if output.is_symlink():
                raise Failure("structural-output-linked", str(output))
            if output.exists() and input_json(output) != normalized:
                raise Failure("structural-output-exists", "Refusing to overwrite a different explicit structural report")
            write_json(output, normalized)
        return normalized
    if action in ("frontmatter", "summary-files"):
        path = safe_path(args.get("report", args.arg(0, "")))
        if not path.is_file():
            raise Failure("review-file-missing", str(path))
        text = read(path)
        header = re.match(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text, re.S)
        if not header:
            raise Failure("review-frontmatter-missing", str(path))
        if action == "frontmatter":
            return header[1]
        metadata, _ = split_frontmatter(text)
        values = metadata.get("key-files", metadata.get("key_files", {}))
        if not isinstance(values, dict):
            raise Failure("review-files-schema", "key-files must be a mapping")
        paths = []
        from .code_review_pipeline_regression import parse_key_files
        for item in [*values.get("created", []), *values.get("modified", [])]:
            name = item.get("path") if isinstance(item, dict) else item
            if not isinstance(name, str) or "\n" in name:
                raise Failure("review-files-schema", "Expected scalar file paths")
            # Reuse the established SUMMARY scalar grammar: annotations are
            # descriptive text, and prose without a filename is not file scope.
            for filename in parse_key_files("  created:\n    - " + name):
                paths.append(str(safe_path(filename).relative_to(root())).replace("\\", "/"))
        return "\n".join(dict.fromkeys(paths))
    data = payload(args)
    if action == "contributions":
        hooks = data.get("activeHooks", []) if isinstance(data, dict) else []
        fragments = []
        for hook in hooks:
            if hook.get("kind") == "contribution" and hook.get("into") in ("reviewer", "code-reviewer"):
                fragment = hook.get("fragment", {}).get("inline")
                if not isinstance(fragment, str):
                    raise Failure("review-contribution-schema", "Expected inline contribution text")
                fragments.append(fragment)
        return "\n".join(fragments)
    if action == "evidence":
        results = data.get("results", []) if isinstance(data, dict) else data
        if not isinstance(results, list):
            raise Failure("review-evidence-schema", "Expected results array")
        paths, failures = [], []
        for result in results:
            if not isinstance(result, dict):
                raise Failure("review-evidence-schema", "Each result must be a mapping")
            path = result.get("reviewPath")
            if result.get("status") in ("success", "passed", "complete", "completed") and isinstance(path, str):
                try:
                    selected = Path(path).expanduser()
                    actual = (root()/selected).resolve() if not selected.is_absolute() else selected.resolve()
                    if not actual.is_relative_to(root().resolve()):
                        from .review_execution import verify_result
                        actual = verify_result(result)
                    else:
                        actual = safe_path(path)
                    if not actual.is_file():
                        raise Failure("review-file-missing", "Referenced review file is missing")
                    paths.append(str(actual))
                except (Failure, OSError, ValueError, TypeError, KeyError) as exc:
                    failures.append({**result, "reason": str(exc), "error": getattr(exc, "code", "review-evidence-invalid")})
            else:
                failures.append(result)
        return {"review_paths": paths, "failures": failures, "results": results}
    raise Failure("unknown-review-adapter", action, 2)
