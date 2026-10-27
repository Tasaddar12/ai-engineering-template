"""Regenerate complete native role definitions and unfilled adoption seeds."""
from pathlib import Path
import re
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def main():
    spec = importlib.util.spec_from_file_location("asset_installer", ROOT / "bin/install.py")
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    assets = ROOT / "bin/install-assets"
    for name in ("PROJECT", "REQUIREMENTS", "ROADMAP", "STATE"):
        text = (ROOT / "engineer/templates" / (name.lower() + ".md")).read_text(encoding="utf-8")
        match = re.search(r"```markdown\r?\n(.*?)\r?\n```", text, re.S)
        if match is None:
            raise ValueError("complete artifact block missing: " + name)
        body = match[1]
        if name == "REQUIREMENTS":
            body = body.replace("### Authentication", "### [Category 1]")
            descriptions = ("User can sign up with email and password", "User receives email verification after signup",
                            "User can reset password via email link", "User session persists across browser refresh")
            for description in descriptions:
                body = body.replace(description, "[Requirement description]")
            body = re.sub(r"AUTH-(\d+)", r"[REQ-\1]", body)
            body = body.replace("| Phase 1 |", "| Phase [N] |")
        if name == "ROADMAP":
            body = body.replace("Critical Fix", "[Inserted phase name]")
        (assets / (name + ".txt")).write_text(body + "\n", encoding="utf-8")
    for path in sorted((ROOT / "agents").glob("*.md")):
        if path.stem in {"AGENT", "code-fixer"}:
            continue
        raw = path.read_bytes()
        description = re.search(r"^description: (.+)$", raw.decode("utf-8"), re.M)
        method = installer.render_asset("agents/" + path.name, raw, "codex").decode("utf-8")
        native = installer.agent_native(path.stem, description[1] if description else path.stem, method)
        (assets / "codex-agents" / (path.stem + ".toml")).write_bytes(native)


if __name__ == "__main__":
    main()
