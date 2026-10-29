"""Reject executable Node examples and retired JS runtime helpers in tracked Markdown.

Scan the Git index's complete filename inventory (including hidden directories and
case-insensitive Markdown suffixes). Prose about Node, graph nodes, package-manager
commands and JavaScript application source remain valid documentation.
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


def node_commands(region):
    """Locate executable tokens, independent of argument extension or presence.

    Quote-aware words distinguish an executable from data passed to grep/printf
    or JavaScript string literals. Shell control operators establish fresh command
    positions; redirection operands do not. Launch wrappers keep that position.
    """
    command, redirect, shell, payload, wrapper = True, False, False, False, False
    for match in TOKEN.finditer(region):
        kind, token = match.lastgroup, match[0]
        if kind in ("space", "comment"):
            continue
        if kind == "newline":
            command, redirect, shell, payload, wrapper = True, False, False, False, False
            continue
        if kind == "operator":
            if token in ("<", ">"):
                redirect = True
            else:
                command, shell, payload, wrapper = token != ")", False, False, False
            continue
        if kind != "word":
            continue
        # Double-quoted shell words still execute command substitutions; quoted
        # grep/printf data without substitutions remains ordinary argument data.
        for quoted in re.finditer(r'"(?:\\.|[^"\\])*"', token):
            for substitution in re.finditer(r'(?<!\\)\$\((.*?)(?:\)|$)', quoted[0], re.S):
                for position, nested in node_commands(substitution[1]):
                    yield match.start()+quoted.start()+substitution.start(1)+position, nested
        if redirect:
            redirect = False
            continue
        try:
            words = shlex.split(token)
            value = words[0] if len(words) == 1 else token
        except ValueError:
            value = token.strip("\"'")
        basename = value.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if payload:
            for position, nested in node_commands(value):
                yield match.start()+position, nested
            payload = False
        if shell and re.fullmatch(r"-[a-z]*c", value):
            payload = True
        if not command:
            continue
        if basename in ("node", "node.exe", "nodejs", "nodejs.exe"):
            yield match.start(), token
            command = False
        elif basename in ("env", "command", "exec", "sudo", "nohup", "setsid", "timeout"):
            wrapper = True
        elif (re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", value)
              or value in ("if", "then", "elif", "else", "while", "until", "do", "!", "{", "}")
              or wrapper and (value.startswith("-") or value.isdecimal())):
            continue
        else:
            shell = basename in ("sh", "bash", "zsh", "dash", "ksh", "eval")
            payload = basename == "eval"
            command = False


def executable_regions(text):
    """Yield (offset, text) for fences and inline code, without broad path exemptions."""
    lines = text.splitlines(keepends=True)
    offset, fence, body, start = 0, None, [], 0
    for line in lines:
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            if fence is None:
                fence, start, body = marker[1], offset+len(line), []
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                yield start, "".join(body), False
                fence = None
            else:
                body.append(line)
        elif fence is not None:
            body.append(line)
        elif line.startswith(("    ", "\t")):
            yield offset, line, False
        else:
            for match in re.finditer(r"(`+)(.+?)\1", line):
                yield offset+match.start(2), match[2], True
        offset += len(line)
    if fence is not None:
        yield start, "".join(body), False


def findings(text):
    results = []
    for offset, region, inline in executable_regions(text):
        region = re.sub(r"[\\`]\r?\n", lambda m: " "*len(m[0]), region)
        for position, token in node_commands(region):
            # An isolated inline runtime name is a prose identifier, like `git`.
            # Bare commands remain prohibited in fences and in inline pipelines.
            if inline and token == region.strip():
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
    return [Path(name.decode("utf-8")) for name in output.split(b"\0") if name.lower().endswith((b".md", b".markdown"))]


def main(root=ROOT):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    files = tracked_markdown(root)
    errors = []
    for file in files:
        for line, reason, command in findings((root/file).read_text(encoding="utf-8-sig")):
            errors.append(f"{file.as_posix()}:{line}: {reason}: {command}")
    print("\n".join(errors)) if errors else None
    print(f"Scanned {len(files)} tracked Markdown files; {len(errors)} findings.")
    return int(bool(errors))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Git checkout to scan")
    sys.exit(main(parser.parse_args().root))
