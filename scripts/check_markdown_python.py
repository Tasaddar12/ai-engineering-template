"""Reject retired JavaScript runtime helper calls in active Markdown.

Scan tracked Markdown outside archived workflow, planning and maintenance records.
Generic Node commands for adopting projects and JavaScript examples remain valid.
"""
from pathlib import Path
import argparse
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'''(?P<space>[ \t\r]+)|(?P<newline>\n)|(?P<comment>\#[^\n]*)|(?P<operator>\$\(|&&|\|\||[|;&()<>])|(?P<word>(?:\\.|"(?:\\.|[^"\\])*"|'[^']*'|[^\s|;&()<>"'\\])+)|(?P<other>.)''')
RETIRED = re.compile(r'''(?:\brequire\s*\([^\n]*(?:code-review-(?:flags|depth)|fallow-runner)|(?:\b(?:python3?|node(?:js)?)\b|\$\([^\n]*)[^\n]*\b(?:edge-probe|spec-section|ui-consideration-probe)\.cjs)''')


def substitutions(text):
    """Yield balanced executable substitutions, excluding escaped/single-quoted data."""
    index, quote = 0, None
    while index < len(text):
        character = text[index]
        if quote == "'":
            if character == "'":
                quote = None
            index += 1
            continue
        if character == "\\":
            index += 2
            continue
        if character == "#" and quote is None and (index == 0 or text[index-1].isspace()):
            end = text.find("\n", index)
            index = len(text) if end == -1 else end
            continue
        if character == "'" and quote is None:
            quote = "'"
        elif character == '"':
            quote = None if quote == '"' else '"'
        elif character == "`":
            end = index+1
            while end < len(text):
                if text[end] == "\\":
                    end += 2
                elif text[end] == "`":
                    break
                else:
                    end += 1
            yield index, min(end+1, len(text)), index+1, text[index+1:end]
            index = end+1
            continue
        elif text.startswith("$(", index):
            end, depth, inner_quote = index+2, 1, None
            while end < len(text) and depth:
                current = text[end]
                if current == "\\" and inner_quote != "'":
                    end += 2
                    continue
                if inner_quote:
                    if current == inner_quote:
                        inner_quote = None
                elif current in ("'", '"', "`"):
                    inner_quote = current
                elif current == "(":
                    depth += 1
                elif current == ")":
                    depth -= 1
                end += 1
            body_end = end-1 if depth == 0 else end
            yield index, end, index+2, text[index+2:body_end]
            index = end
            continue
        index += 1


WRAPPER_OPERANDS = {
    "env": {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"},
    "sudo": {"-u", "--user", "-g", "--group", "-h", "--host", "-p", "--prompt", "-C", "--close-from", "-R", "--chroot", "-D", "--chdir", "-r", "--role", "-t", "--type"},
    "exec": {"-a"}, "command": set(),
    "timeout": {"-k", "--kill-after", "-s", "--signal"},
    "nohup": set(), "setsid": set(),
}


def node_commands(region, scan_substitutions=True):
    """Parse ordinary static command positions and launcher option/operand grammar."""
    masked = list(region)
    for start, end, body_start, body in substitutions(region) if scan_substitutions else ():
        for position, token in node_commands(body):
            yield body_start+position, token
        masked[start:end] = ["\n" if c == "\n" else " " for c in region[start:end]]
    command, redirect, shell, payload = True, False, False, False
    wrapper, operand, options, duration = None, None, True, False
    for match in TOKEN.finditer("".join(masked)):
        kind, token = match.lastgroup, match[0]
        if kind in ("space", "comment"):
            continue
        if kind == "newline" or kind == "operator" and token not in ("<", ">"):
            command, redirect, shell, payload = token != ")", False, False, False
            wrapper, operand, options, duration = None, None, True, False
            continue
        if kind == "operator":
            redirect = True
            continue
        if kind != "word":
            continue
        if redirect:
            redirect = False
            continue
        try:
            words = shlex.split(token)
            value = words[0] if len(words) == 1 else token
        except ValueError:
            value = token.strip("\"'")
        basename = value.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if payload or operand in ("-S", "--split-string"):
            for position, nested in node_commands(value):
                yield match.start()+position, nested
            payload, operand, command = False, None, False
            continue
        if operand:
            operand = None
            continue
        if shell and re.fullmatch(r"-[a-z]*c", value):
            payload = True
        if not command:
            continue
        if wrapper and options and value == "--":
            options = False
            continue
        if wrapper and options and value.startswith("-"):
            option, equal, argument = value.partition("=")
            if wrapper == "command" and option in ("-v", "-V"):
                command = False  # lookup only; its operands are not executed
            elif wrapper == "env" and option in ("-S", "--split-string") and equal:
                for position, nested in node_commands(argument):
                    yield match.start()+len(option)+1+position, nested
                command = False
            elif option in WRAPPER_OPERANDS[wrapper] and not equal:
                operand = option
            continue
        if wrapper == "timeout" and not duration:
            if re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[smhd])?", value):
                duration = True
                continue
        if re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", value):
            continue
        if basename in ("node", "node.exe", "nodejs", "nodejs.exe"):
            yield match.start(), token
            command = False
        elif basename in WRAPPER_OPERANDS:
            wrapper, operand, options, duration = basename, None, True, False
        elif value in ("if", "then", "elif", "else", "while", "until", "do", "!", "{", "}"):
            continue
        else:
            shell = basename in ("sh", "bash", "zsh", "dash", "ksh", "eval")
            payload = basename == "eval"
            command = False


def executable_regions(text):
    """Yield (offset, text) for fences and inline code, without broad path exemptions."""
    lines = text.splitlines(keepends=True)
    offset, fence, body, start, source = 0, None, [], 0, False
    for line in lines:
        # Replace container markers by equal-width spaces so original offsets and
        # line diagnostics survive blockquotes, nested lists and their fences.
        prefix = 0
        containers = r"[ \t]{0,3}>[ \t]?" if fence else r"[ \t]{0,3}>[ \t]?|[ \t]{0,3}(?:[-+*]|\d+[.)])[ \t]+"
        while container := re.match(containers, line[prefix:]):
            prefix += container.end()
        visible = " "*prefix+line[prefix:]
        marker = re.match(r"^\s*(`{3,}|~{3,})(.*)$", visible)
        if marker:
            if fence is None:
                fence, start, body = marker[1], offset+len(line), []
                source = marker[2].strip().lower() in ("js", "javascript", "ts", "typescript", "jsx", "tsx", "mermaid")
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                yield start, "".join(body), "source" if source else False
                fence = None
            else:
                body.append(visible)
        elif fence is not None:
            body.append(visible)
        elif visible.startswith(("    ", "\t")) and not prefix:
            yield offset, visible, False
        else:
            for match in re.finditer(r"(`+)(.+?)\1", visible):
                yield offset+match.start(2), match[2], True
            prose = re.search(r"\b(?:Run|Execute|Invoke|Launch|Start)\s+((?:node(?:js)?)(?:\.exe)?(?:\s+[^\n]+|$))", visible, re.I)
            if prose:
                yield offset+prose.start(1), prose[1], False
        offset += len(line)
    if fence is not None:
        yield start, "".join(body), "source" if source else False


def findings(text, runtime_only=False):
    results = []
    for offset, region, inline in executable_regions(text):
        region = re.sub(r"[\\`]\r?\n", lambda m: " "*len(m[0]), region)
        for position, token in (() if runtime_only else node_commands(region, scan_substitutions=inline != "source")):
            # An isolated inline runtime name is a prose identifier, like `git`.
            # Bare commands remain prohibited in fences and in inline pipelines.
            if inline is True and token == region.strip():
                prefix = text[text.rfind("\n", 0, offset)+1:offset].rstrip("` ")
                if not re.search(r"\b(?:run|execute|invoke|launch|start)\s*$", prefix, re.I):
                    continue
            absolute = offset+position
            results.append((text.count("\n", 0, absolute)+1, "executable Node command", token))
        for pattern, reason in ((RETIRED, "retired JavaScript helper"),):
            for match in pattern.finditer(region):
                line_start = region.rfind("\n", 0, match.start())+1
                # Shell comments document semantics, rather than execute commands.
                if region[line_start:match.start()].lstrip().startswith("#"):
                    continue
                absolute = offset+match.start()
                results.append((text.count("\n", 0, absolute)+1, reason, match[0].strip()))
    return sorted(set(results))


def tracked_markdown(root=ROOT):
    output = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"])
    files = [Path(name.decode("utf-8")) for name in output.split(b"\0")
             if name.lower().endswith((b".md", b".markdown"))]
    return [file for file in files
            if file.parts[0] not in (".ai", ".planning")
            and file.as_posix() != "PLANNED-UPDATES.md"
            and file.parts[:2] != ("docs", "maintenance")]


def main(root=ROOT):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    files = tracked_markdown(root)
    errors = []
    for file in files:
        for line, reason, command in findings((root/file).read_text(encoding="utf-8-sig"), runtime_only=True):
            errors.append(f"{file.as_posix()}:{line}: {reason}: {command}")
    print("\n".join(errors)) if errors else None
    print(f"Scanned {len(files)} tracked Markdown files; {len(errors)} findings.")
    return int(bool(errors))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Git checkout to scan")
    sys.exit(main(parser.parse_args().root))
