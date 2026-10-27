"""Compare literal engineer query call sites with the Python runtime registry."""
import ast
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import files, main_guard, parser, read_text, safe_path

CALL = re.compile(r'\bengineer_run\s+query\s+([A-Za-z][A-Za-z0-9_]*(?:[.-][A-Za-z0-9_]+)*)(?![A-Za-z0-9_.-])')


def literal(node, environment):
    """Resolve only finite string expressions; never evaluate Python code."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id in environment:
        return environment[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return literal(node.left, environment) + literal(node.right, environment)
    raise ValueError("Registry names must be literal strings or bounded loop variables")


def constructed_registry(function):
    """Inspect the runtime's closed registration function without importing it.

    Handler expressions are deliberately not visited or executed. Only the name
    dictionary, exact key assignments and finite string loops are accepted.
    """
    if function.args.args or function.args.posonlyargs or function.args.kwonlyargs or function.args.vararg or function.args.kwarg or function.decorator_list:
        raise ValueError("Registry constructor must have no arguments or decorators")
    found, state = set(), {"name": None, "returned": False, "steps": 0}

    def statements(body, environment):
        for node in body:
            state["steps"] += 1
            if state["steps"] > 10000 or state["returned"]:
                raise ValueError("Unbounded or unreachable registry construction")
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                continue  # Optional function docstring.
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Dict) and state["name"] is None:
                    state["name"] = target.id
                    for key in node.value.keys:
                        found.add(literal(key, environment))
                elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == state["name"]:
                    found.add(literal(target.slice, environment))
                else:
                    raise ValueError("Unsupported registry assignment")
            elif isinstance(node, ast.For) and isinstance(node.target, ast.Name) and isinstance(node.iter, (ast.Tuple, ast.List)) and not node.orelse:
                if len(node.iter.elts) > 1000:
                    raise ValueError("Registry registration loop is too large")
                for item in node.iter.elts:
                    nested = {**environment, node.target.id: literal(item, environment)}
                    statements(node.body, nested)
            elif isinstance(node, ast.Return) and isinstance(node.value, ast.Name) and node.value.id == state["name"]:
                state["returned"] = True
            else:
                raise ValueError("Registry construction contains unsupported dynamic behavior")

    statements(function.body, {})
    if not state["returned"] or state["name"] is None:
        raise ValueError("Registry constructor must return its named dictionary")
    return found


def registered_verbs(source):
    """Read static registry keys without importing or executing the runtime."""
    tree = ast.parse(source)
    found = set()
    registry_seen = False
    functions = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = node
            continue
        value = None
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "VERBS" for target in node.targets):
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "VERBS":
            value = node.value
        if value is not None:
            if registry_seen:
                raise ValueError("Multiple VERBS assignments cannot be inspected unambiguously")
            registry_seen = True
            if isinstance(value, ast.Dict):
                if any(not isinstance(key, ast.Constant) or not isinstance(key.value, str) for key in value.keys):
                    raise ValueError("VERBS contains dynamic keys; expose a static registry for inspection")
                found.update(key.value for key in value.keys)
            elif isinstance(value, (ast.Set, ast.List, ast.Tuple)):
                if any(not isinstance(item, ast.Constant) or not isinstance(item.value, str) for item in value.elts):
                    raise ValueError("VERBS contains dynamic entries")
                found.update(item.value for item in value.elts)
            elif isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id in functions and not value.args and not value.keywords:
                found.update(constructed_registry(functions[value.func.id]))
            else:
                raise ValueError("VERBS must be a static dict, set, list or tuple")
    if not registry_seen:
        raise ValueError("No static VERBS registry found in engineer/bin/engineer.py")
    return found


def call_sites(root):
    result = []
    for path in files(root):
        text = read_text(path)
        if text is None:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for match in CALL.finditer(line):
                # Angle-bracket placeholders and shell expressions never match CALL.
                result.append((match[1], path.relative_to(root.resolve()).as_posix(), number))
    return result


def main():
    command = parser(__doc__)
    command.add_argument("--report", action="store_true")
    command.add_argument("--fail-on-unknown", action="store_true")
    args = command.parse_args()
    runtime = safe_path(args.root, "engineer/bin/engineer.py")
    known = registered_verbs(runtime.read_text(encoding="utf-8"))
    sites = call_sites(args.root)
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
