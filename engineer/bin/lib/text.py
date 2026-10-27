"""Safe YAML subset used by configuration and Markdown frontmatter.

Supports indented mappings/sequences, flow collections, quoted/plain scalars,
comments, and literal/folded blocks. Tags, anchors, aliases, merge keys and
duplicate mapping keys are rejected; no executable constructors are involved.
"""
from __future__ import annotations
import json
import re
from .core import Failure


def _split(text, delimiter=","):
    parts, start, depth, quote, escape = [], 0, 0, None, False
    for i, char in enumerate(text):
        if escape:
            escape = False
        elif quote:
            if char == "\\" and quote == '"':
                escape = True
            elif char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        elif char == delimiter and depth == 0:
            parts.append(text[start:i].strip())
            start = i + 1
    if quote or depth:
        raise Failure("invalid-yaml", "Unclosed quote or flow collection", 2)
    parts.append(text[start:].strip())
    return parts


def _comment(text):
    quote, escaped = None, False
    for i, char in enumerate(text):
        if escaped:
            escaped = False
        elif quote:
            if char == "\\" and quote == '"':
                escaped = True
            elif char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "#" and (i == 0 or text[i-1].isspace()):
            return text[:i].rstrip()
    return text.rstrip()


def scalar(text):
    text = _comment(text.strip())
    if not text or text in ("null", "Null", "NULL", "~"):
        return None
    if text.startswith(("!", "&", "*")):
        raise Failure("unsafe-yaml", "YAML tags, anchors and aliases are unsupported", 2)
    if text.startswith(("[", "{")):
        try:
            return json.loads(text)
        except ValueError:
            pass
    if text.startswith('"'):
        try:
            return json.loads(text)
        except ValueError as exc:
            raise Failure("invalid-yaml", str(exc), 2) from exc
    if text.startswith("'"):
        if not text.endswith("'"):
            raise Failure("invalid-yaml", "Unclosed single quoted scalar", 2)
        return text[1:-1].replace("''", "'")
    if text.startswith("["):
        if not text.endswith("]"):
            raise Failure("invalid-yaml", "Unclosed flow sequence", 2)
        return [scalar(item) for item in _split(text[1:-1])] if text[1:-1].strip() else []
    if text.startswith("{"):
        if not text.endswith("}"):
            raise Failure("invalid-yaml", "Unclosed flow mapping", 2)
        result = {}
        for item in _split(text[1:-1]) if text[1:-1].strip() else []:
            key, value = pair(item)
            if key in result:
                raise Failure("invalid-yaml", f"Duplicate key: {key}", 2)
            result[key] = scalar(value)
        return result
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    # Leading-zero identifiers such as phase and plan numbers remain strings.
    if re.fullmatch(r"[-+]?(0|[1-9][0-9]*)", text):
        return int(text)
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d+)?", text):
        return float(text)
    return text


def pair(text):
    quote, depth = None, 0
    for i, char in enumerate(text):
        if quote:
            if char == quote and (i == 0 or text[i-1] != "\\"):
                quote = None
        elif char in "\"'":
            quote = char
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        elif char == ":" and depth == 0 and (i + 1 == len(text) or text[i+1].isspace()):
            key = scalar(text[:i])
            if not isinstance(key, (str, int)) or str(key) == "<<":
                raise Failure("invalid-yaml", "Invalid mapping key", 2)
            return str(key), text[i+1:].strip()
    raise Failure("invalid-yaml", f"Expected mapping entry: {text}", 2)


def yaml_load(content):
    stripped = content.strip()
    if not stripped:
        return {}
    if stripped.startswith(("{", "[")):
        try:
            return json.loads(stripped)
        except ValueError:
            return scalar(stripped)
    lines = content.splitlines()
    entries = []
    for index, line in enumerate(lines):
        if "\t" in line[:len(line)-len(line.lstrip())]:
            raise Failure("invalid-yaml", "Tabs are not valid indentation", 2)
        clean = _comment(line.lstrip())
        if clean and clean not in ("---", "..."):
            entries.append((len(line)-len(line.lstrip()), clean, index))

    def block(cursor, indent):
        sequence = entries[cursor][1] == "-" or entries[cursor][1].startswith("- ")
        result = [] if sequence else {}
        while cursor < len(entries) and entries[cursor][0] == indent:
            _, line, original = entries[cursor]
            is_item = line == "-" or line.startswith("- ")
            if is_item != sequence:
                raise Failure("invalid-yaml", "Mixed mapping and sequence", 2)
            if sequence:
                value = line[1:].strip()
                try:
                    key, tail = pair(value)
                    mapping = True
                except Failure:
                    mapping = False
                if mapping:
                    obj = {key: scalar(tail)}
                    cursor += 1
                    if cursor < len(entries) and entries[cursor][0] > indent:
                        nested_indent = entries[cursor][0]
                        child, cursor = block(cursor, nested_indent)
                        if not tail and (nested_indent > indent + 2 or isinstance(child, list)):
                            obj[key] = child
                        elif isinstance(child, dict):
                            for k, v in child.items():
                                if k in obj and tail:
                                    raise Failure("invalid-yaml", f"Duplicate key: {k}", 2)
                                obj[k] = v
                        else:
                            raise Failure("invalid-yaml", "Invalid sequence mapping", 2)
                    result.append(obj)
                else:
                    cursor += 1
                    if not value and cursor < len(entries) and entries[cursor][0] > indent:
                        obj, cursor = block(cursor, entries[cursor][0])
                    else:
                        obj = scalar(value)
                    result.append(obj)
            else:
                key, value = pair(line)
                if key in result:
                    raise Failure("invalid-yaml", f"Duplicate key: {key}", 2)
                cursor += 1
                if value in ("|", "|-", "|+", ">", ">-", ">+"):
                    end_line = entries[cursor][2] if cursor < len(entries) else len(lines)
                    end_cursor = cursor
                    while end_cursor < len(entries) and entries[end_cursor][0] > indent:
                        end_cursor += 1
                    end_line = entries[end_cursor][2] if end_cursor < len(entries) else len(lines)
                    section = lines[original + 1:end_line]
                    margin = min((len(s)-len(s.lstrip()) for s in section if s.strip()), default=indent+2)
                    body = [s[margin:] for s in section]
                    obj = (" ".join(body) if value.startswith(">") else "\n".join(body))
                    obj = obj.rstrip("\n") + ("" if value.endswith("-") else "\n")
                    cursor = end_cursor
                elif not value and cursor < len(entries) and entries[cursor][0] > indent:
                    obj, cursor = block(cursor, entries[cursor][0])
                else:
                    obj = scalar(value)
                result[key] = obj
            if cursor < len(entries) and entries[cursor][0] > indent:
                raise Failure("invalid-yaml", "Unexpected indentation", 2)
        return result, cursor

    if not entries:
        return {}
    result, cursor = block(0, entries[0][0])
    if cursor != len(entries):
        raise Failure("invalid-yaml", "Unexpected indentation", 2)
    return result


def yaml_dump(value, indent=0):
    # JSON scalars/flow arrays are valid YAML and remove implicit type ambiguity.
    prefix = " " * indent
    if isinstance(value, dict):
        lines = []
        for key, child in value.items():
            name = key if re.fullmatch(r"[A-Za-z_][\w.-]*", str(key)) else json.dumps(str(key))
            if isinstance(child, dict) and child:
                lines.extend([f"{prefix}{name}:", yaml_dump(child, indent+2)])
            elif isinstance(child, list) and child and any(isinstance(x, dict) for x in child):
                lines.extend([f"{prefix}{name}:", yaml_dump(child, indent+2)])
            else:
                lines.append(f"{prefix}{name}: {json.dumps(child, ensure_ascii=False)}")
        return "\n".join(lines)
    if isinstance(value, list):
        return "\n".join(prefix + "- " + json.dumps(child, ensure_ascii=False) for child in value)
    return prefix + json.dumps(value, ensure_ascii=False)


def split_frontmatter(content):
    match = re.match(r"\A\ufeff?---\r?\n(.*?)\r?\n---(?:\r?\n|$)", content, re.S)
    if not match:
        return {}, content
    metadata = yaml_load(match.group(1))
    if not isinstance(metadata, dict):
        raise Failure("invalid-frontmatter", "Frontmatter must be a mapping", 2)
    return metadata, content[match.end():]


def join_frontmatter(metadata, body):
    return "---\n" + yaml_dump(metadata) + "\n---\n" + body
