"""Compare literal engineer query call sites with the Python runtime registry."""
import ast
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import files, main_guard, parser, read_text, safe_path

CALL = re.compile(r'\bengineer_run\s+query\s+([A-Za-z][A-Za-z0-9_.-]*)(?:[ \t]+([A-Za-z][A-Za-z0-9_.-]*))?')


def registered_verbs(source):
    """Read literal registry construction without importing or running the CLI."""
    tree = ast.parse(source)
    found = set()
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}

    def literal(node, environment):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name) and node.id in environment:
            return environment[node.id]
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            return [literal(item, environment) for item in node.elts]
        if isinstance(node, ast.Dict):
            return {literal(key, environment): literal(value, environment) for key, value in zip(node.keys, node.values)}
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return literal(node.left, environment)+literal(node.right, environment)
        if isinstance(node, ast.Subscript):
            return literal(node.value, environment)[literal(node.slice, environment)]
        if isinstance(node, ast.IfExp):
            return literal(node.body if literal(node.test, environment) else node.orelse, environment)
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
            return literal(node.left, environment) == literal(node.comparators[0], environment)
        raise ValueError("Registry names must be built from literal values")

    def add(value):
        if not isinstance(value, str):
            raise ValueError("A registry key is not a string")
        found.add(value)

    def dictionary(node, environment):
        if not isinstance(node, ast.Dict):
            raise ValueError("Registry updates require a literal dictionary")
        for key in node.keys:
            add(literal(key, environment))

    def walk(nodes, environment, registries):
        for node in nodes:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        if target.id.lower() == "verbs" and isinstance(node.value, ast.Dict):
                            registries.add(target.id)
                            dictionary(node.value, environment)
                        else:
                            try:
                                environment[target.id] = literal(node.value, environment)
                            except ValueError:
                                environment.pop(target.id, None)
                    elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id in registries:
                        add(literal(target.slice, environment))
            elif isinstance(node, ast.For) and isinstance(node.target, ast.Name):
                for value in literal(node.iter, environment):
                    walk(node.body, {**environment, node.target.id: value}, set(registries))
            elif isinstance(node, ast.If):
                walk(node.body, dict(environment), set(registries))
                walk(node.orelse, dict(environment), set(registries))
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id in registries and call.func.attr == "update":
                    if len(call.args) != 1:
                        raise ValueError("Registry update has an unsupported signature")
                    dictionary(call.args[0], environment)

    declarations = []
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(target, ast.Name) and target.id == "VERBS" for target in targets):
            declarations.append(node.value)
    if len(declarations) != 1:
        raise ValueError("Expected one VERBS declaration")
    value = declarations[0]
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id in functions and not value.args and not value.keywords:
        walk(functions[value.func.id].body, {}, set())
    elif isinstance(value, ast.Dict):
        dictionary(value, {})
    elif isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        for name in literal(value, {}):
            add(name)
    else:
        raise ValueError("Unsupported registry declaration; no runtime code was executed")
    return found


def call_sites(root, known=()):
    result = []
    namespaces = {name.partition('.')[0] for name in known if '.' in name}
    for path in files(root):
        text = read_text(path)
        if text is None:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for match in CALL.finditer(line):
                name = match[1]
                if name == "VERB":
                    continue  # Literal syntax placeholder in CLI usage examples.
                if name.endswith('.') or (match.end(1) < len(line) and line[match.end(1)] in '<{$'):
                    continue
                if name not in known and name in namespaces and match[2]:
                    name += '.'+match[2]
                result.append((name, path.relative_to(root.resolve()).as_posix(), number))
    return result


def main():
    command = parser(__doc__)
    command.add_argument("--report", action="store_true")
    command.add_argument("--fail-on-unknown", action="store_true")
    args = command.parse_args()
    runtime = safe_path(args.root, "engineer/bin/engineer.py")
    known = registered_verbs(runtime.read_text(encoding="utf-8")) | {"help", "verbs"}
    sites = call_sites(args.root, known)
    unknown = [(verb, path, number) for verb, path, number in sites if verb not in known]
    for verb, path, number in sorted(unknown):
        print(f"UNKNOWN {path}:{number}: {verb}")
    if args.report:
        for verb in sorted({site[0] for site in sites} & known):
            print(f"KNOWN {verb}")
    print(f"{len(known)} registered; {len(sites)} call sites; {len(unknown)} unknown call sites")
    return int(args.fail_on_unknown and bool(unknown))


if __name__ == "__main__":
    sys.exit(main_guard(main))
