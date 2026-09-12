"""Read the small Markdown/YAML phase interface; no generated input schemas."""
from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import yaml


class PhaseError(Exception):
    """An actionable workflow failure, rather than successful completion."""


def require(condition, message):
    if not condition:
        raise PhaseError(message)


def git(root, *args, check=True):
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if check:
        require(result.returncode == 0, result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        require(isinstance(key, str), "YAML keys must be strings")
        require(key not in result, f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read_yaml(text):
    try:
        value = yaml.load(text, Loader=UniqueLoader)
    except yaml.YAMLError as exc:
        raise PhaseError(f"Invalid YAML: {exc}") from exc
    require(isinstance(value, dict), "Expected a YAML mapping")
    return value


def record(path):
    require(path.is_file(), f"Missing record: {path}")
    text = path.read_text(encoding="utf-8-sig")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)(.*)", text, re.S)
    require(match is not None, f"Missing YAML frontmatter: {path}")
    return read_yaml(match[1]), match[2]


def section(body, name):
    match = re.search(rf"(?im)^##\s+{re.escape(name)}\s*$\n?(.*?)(?=^##\s|\Z)", body, re.S | re.M)
    return match[1].strip() if match else ""


def string_list(value, label):
    require(isinstance(value, list) and all(isinstance(v, str) and v.strip() for v in value),
            f"{label} must be a list of nonempty strings")
    require(len(value) == len(set(value)), f"Duplicate entries in {label}")
    return value


def commands(value, label, required=False):
    require(isinstance(value, list), f"{label} must be a list of argv lists")
    if required:
        require(bool(value), f"{label} must include at least one real check")
    for argv in value:
        require(isinstance(argv, list) and argv and all(isinstance(v, str) and v for v in argv),
                f"{label} entries must be nonempty argv lists, not shell strings")
    return value


def safe_path(root, value):
    require(isinstance(value, str) and bool(value), "Ownership paths must be nonempty strings")
    p = PurePosixPath(value)
    require(not p.is_absolute() and not any(c in value for c in "\\:*?[]\x00\r\n\t")
            and all(part.casefold() not in (".", "..", ".git", ".worktrees") for part in value.rstrip("/").split("/")),
            f"Use an exact relative file or directory/ prefix: {value}")
    resolved = (root / p).resolve()
    require(resolved.is_relative_to(root.resolve()), f"Path escapes assigned worktree: {value}")
    cursor = root / p
    while cursor != root and cursor.is_relative_to(root):
        require(not cursor.is_symlink() and not (hasattr(cursor, "is_junction") and cursor.is_junction()),
                f"Ownership cannot traverse a link: {value}")
        cursor = cursor.parent
    return value


def owns(prefix, path):
    # Conservative across platforms: instructions should also be safe on Windows/macOS.
    prefix, path = prefix.casefold(), path.casefold()
    return path == prefix or (prefix.endswith("/") and path.startswith(prefix))


def overlaps(left, right):
    return any(owns(a, b) or owns(b, a) for a in left for b in right)


@dataclass
class Component:
    id: str
    path: Path
    data: dict
    body: str

    @property
    def summary(self):
        return self.path.with_name(self.id + "-SUMMARY.md")


@dataclass
class Phase:
    root: Path
    directory: Path
    number: str
    context: dict
    body: str
    components: dict[str, Component]
    config: dict
    acceptance: list[str]

    @property
    def relative(self):
        return self.directory.relative_to(self.root).as_posix()

    def artifact(self, suffix):
        return self.directory / f"{self.number}-{suffix}.md"

    def fingerprint(self):
        paths = [self.root / ".ai/config.yaml", self.root / ".ai/RULES.md",
                 self.root / ".ai/PROJECT.md", self.root / ".ai/REQUIREMENTS.md"]
        paths += [p for p in self.directory.glob("*.md") if not
                  re.search(r"-(SUMMARY|VERIFICATION|UAT)\.md$", p.name)]
        digest = hashlib.sha256()
        for path in sorted(set(paths)):
            if path.name == ".continue-here.md":
                continue
            digest.update(path.relative_to(self.root).as_posix().encode())
            digest.update(path.read_bytes() if path.exists() else b"<missing>")
        return digest.hexdigest()


def load_phase(root, name, ready=False):
    base = root / ".ai/phases"
    require(isinstance(name, str) and re.fullmatch(r"\d{2,}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?", name),
            "Select a phase number or its directory name, for example 01-authentication")
    candidates = [p for p in base.glob(name if "-" in name else name + "-*") if p.is_dir()]
    require(len(candidates) == 1, f"Expected one phase matching {name}; found {len(candidates)}")
    directory = candidates[0]
    safe_path(root, directory.relative_to(root).as_posix())
    number = directory.name.split("-", 1)[0]
    context, body = record(directory / f"{number}-CONTEXT.md")
    require(str(context.get("phase")) == number, "CONTEXT phase must match its folder number (quote it in YAML)")
    require(context.get("approval") in ("pending", "approved"), "CONTEXT approval must be pending or approved")
    require(isinstance(context.get("uat", False), bool), "CONTEXT uat must be true or false")
    deps = string_list(context.get("depends_on", []), "phase depends_on")
    for dep in deps:
        require(re.fullmatch(r"\d{2,}-[a-z0-9]+(?:-[a-z0-9]+)*", dep) and dep != directory.name,
                f"Invalid phase dependency: {dep}")
    acceptance = re.findall(r"(?m)^\s*-\s+(?:\[[ xX]\]\s+)?([A-Z][A-Z0-9_-]*\d+)\s*:", section(body, "Acceptance"))
    require(len(acceptance) == len(set(acceptance)), "Duplicate acceptance identifiers in CONTEXT")
    config = read_yaml((root / ".ai/config.yaml").read_text(encoding="utf-8-sig"))
    execution = config.get("execution", {})
    require(isinstance(execution, dict), "execution must be a mapping")
    parallel = execution.get("max_parallel", 2)
    require(type(parallel) is int and 1 <= parallel <= 8, "execution.max_parallel must be 1..8")
    for key, default in (("worker_timeout_seconds", 3600), ("check_timeout_seconds", 300)):
        value = execution.get(key, default)
        require(type(value) is int and 1 <= value <= 86400, f"execution.{key} must be an integer from 1 to 86400")
    require(isinstance(config.get("verification", {}), dict), "verification must be a mapping")
    require(isinstance(config.get("publication", {}), dict), "publication must be a mapping")
    string_list(config.get("publication", {}).get("required_checks", []), "publication.required_checks")
    env = execution.get("environment", {})
    require(isinstance(env, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()),
            "execution.environment must map string names to string values")
    components = {}
    for path in sorted(directory.glob("*-IMPLEMENT.md")):
        require(re.fullmatch(rf"{number}-\d{{2,}}-IMPLEMENT\.md", path.name), f"Invalid component filename: {path.name}")
        data, content = record(path)
        cid = path.name.removesuffix("-IMPLEMENT.md")
        require(data.get("kind") in ("code", "documentation"), f"{cid}: kind must be code or documentation")
        for key in ("depends_on", "files", "resources", "acceptance", "documentation"):
            data[key] = string_list(data.get(key, []), f"{cid}.{key}")
        require(bool(data["files"]), f"{cid}: declare files or directory/ prefixes")
        for value in data["files"] + data["documentation"]:
            safe_path(root, value)
            reserved = [".ai/phases/", ".ai/STATE.md", ".ai/PROJECT.md", ".ai/REQUIREMENTS.md",
                        ".ai/RULES.md", ".ai/config.yaml"]
            require(not overlaps([value], reserved),
                    f"{cid}: phase records, STATE and immutable inputs are coordinator-owned; summary ownership is automatic")
        for value in data["documentation"]:
            require(not value.endswith("/"), f"{cid}: documentation obligations must name exact files")
        commands(data.get("checks", []), f"{cid}.checks", required=ready)
        require(set(data["acceptance"]) <= set(acceptance), f"{cid}: unknown acceptance identifier")
        if ready:
            require(bool(data["acceptance"]), f"{cid}: declare acceptance coverage")
            for title in ("Objective", "Read first", "Implementation", "Verification", "Documentation"):
                require(bool(section(content, title)), f"{cid}: missing {title} instructions")
        components[cid] = Component(cid, path, data, content)
    visiting, visited = set(), set()

    def visit(cid):
        require(cid in components, f"Unknown component dependency: {cid}")
        require(cid not in visiting, "Component dependencies contain a cycle")
        if cid in visited:
            return
        visiting.add(cid)
        for dep in components[cid].data["depends_on"]:
            visit(dep)
        visiting.remove(cid)
        visited.add(cid)

    for cid in components:
        visit(cid)
    if ready:
        require(context["approval"] == "approved", "Phase needs recorded human approval before execution")
        require(bool(section(body, "Authorization")) and "CHANGEME" not in section(body, "Authorization"),
                "Record the actual human authorization in CONTEXT")
        require(bool(section(body, "Goal")) and bool(acceptance), "CONTEXT needs a goal and identified acceptance outcomes")
        require(bool(components), "Prepare at least one IMPLEMENT component before running")
        covered = {a for c in components.values() for a in c.data["acceptance"]}
        require(set(acceptance) <= covered, "Every acceptance outcome needs component coverage")
        commands(config.get("verification", {}).get("commands", []), "verification.commands", required=True)
        for key in ("worker_command", "documentor_command", "verifier_command"):
            if key in execution:
                commands([execution[key]], f"execution.{key}", required=True)
        for kind in {c.data["kind"] for c in components.values()}:
            key = "documentor_command" if kind == "documentation" and execution.get("documentor_command") else "worker_command"
            commands([execution.get(key)], f"execution.{key}", required=True)
        commands([execution.get("verifier_command")], "execution.verifier_command", required=True)
    return Phase(root, directory, number, context, body, components, config, acceptance)
