"""Explicit adopting-project initialization and narrowly scoped narrative updates."""
from __future__ import annotations
import json
import re
from . import config, records
from .core import Failure, now, planning_lock, read, write
from .planning import cell, replace_section, safe
from .text import join_frontmatter

PROJECT_FIELDS = {"name", "description", "core_value", "context", "constraints", "out_of_scope", "requirements", "decisions", "business_context"}
SECTIONS = {"What This Is", "Core Value", "Business Context", "Context", "Constraints", "Out of Scope"}


def _text(value, label, required=False):
    if not isinstance(value, str) or "\x00" in value or required and not value.strip():
        raise Failure("invalid-project-field", label+" must be "+("nonempty " if required else "")+"text", 2)
    return value.strip()


def _list(value, label):
    if not isinstance(value, list) or not all(isinstance(item, str) and "\x00" not in item for item in value):
        raise Failure("invalid-project-field", label+" must be a text array", 2)
    return value


def _spec(args):
    value = args.json("fields", args.json("data", {}))
    if not isinstance(value, dict):
        raise Failure("invalid-onboarding-input", "--fields must be an object", 2)
    allowed = {"project", "requirements", "phases", "config"}
    if set(value)-allowed:
        raise Failure("unknown-onboarding-field", ", ".join(sorted(set(value)-allowed)), 2)
    project = value.get("project", {})
    if not isinstance(project, dict) or set(project)-PROJECT_FIELDS:
        raise Failure("unknown-project-field", str(set(project)-PROJECT_FIELDS) if isinstance(project, dict) else "project must be an object", 2)
    project = dict(project)
    for field in ("name", "description", "core_value"):
        option = field.replace("_", "-")
        if args.has(option):
            project[field] = args.get(option)
        project[field] = _text(project.get(field, ""), field, True)
    if "\n" in project["name"] or "\r" in project["name"]:
        raise Failure("invalid-project-name", "Name must be one line", 2)
    for field in ("context", "business_context"):
        project[field] = _text(project.get(field, ""), field)
    for field in ("constraints", "out_of_scope"):
        project[field] = _list(project.get(field, []), field)
    requirements = value.get("requirements", project.get("requirements", []))
    phases = value.get("phases", [])
    if not isinstance(requirements, list) or not isinstance(phases, list):
        raise Failure("invalid-onboarding-input", "requirements and phases must be arrays", 2)
    ids = set()
    for requirement in requirements:
        if not isinstance(requirement, dict) or set(requirement)-{"id", "description", "category", "phase"}:
            raise Failure("invalid-requirement", "Use id, description, category and phase fields", 2)
        identifier = requirement.get("id", "")
        if not re.fullmatch(r"[A-Z][A-Z0-9]*-\d+", str(identifier)) or identifier in ids:
            raise Failure("invalid-requirement-id", str(identifier), 2)
        ids.add(identifier)
        _text(requirement.get("description", ""), "requirement.description", True)
    for index, phase in enumerate(phases, 1):
        if not isinstance(phase, dict) or set(phase)-{"name", "goal", "requirements", "depends_on", "success_criteria"}:
            raise Failure("invalid-phase-spec", "Use name, goal, requirements, depends_on and success_criteria", 2)
        _text(phase.get("name", ""), "phase.name", True)
        _text(phase.get("goal", ""), "phase.goal", True)
        needed = _list(phase.get("requirements", []), "phase.requirements")
        if set(needed)-ids:
            raise Failure("unknown-phase-requirement", ", ".join(sorted(set(needed)-ids)), 2)
        if not isinstance(phase.get("depends_on", []), list):
            raise Failure("invalid-phase-dependency", "depends_on must be an array", 2)
        if "\n" in phase["name"] or "\r" in phase["name"]:
            raise Failure("invalid-phase-name", "Name must be one line", 2)
        for dependency in phase.get("depends_on", []):
            if not re.fullmatch(r"\d+", str(dependency)) or not 0 < int(dependency) < index:
                raise Failure("invalid-phase-dependency", str(dependency), 2)
        _list(phase.get("success_criteria", []), "phase.success_criteria")
    for requirement in requirements:
        if "phase" in requirement and requirement["phase"] is not None:
            if not re.fullmatch(r"\d+", str(requirement["phase"])) or not 1 <= int(requirement["phase"]) <= len(phases):
                raise Failure("invalid-requirement-phase", str(requirement["phase"]), 2)
    settings = value.get("config", {})
    if not isinstance(settings, dict):
        raise Failure("invalid-config", "config must be an object", 2)
    config.validate(config.merge(config.DEFAULTS, settings))
    return project, requirements, phases, settings


def _render(project, requirements, phases):
    bullets = lambda values: "\n".join("- "+item for item in values) or "None recorded."
    project_text = ("# "+project["name"]+"\n\n## What This Is\n\n"+project["description"]+
                    "\n\n## Core Value\n\n"+project["core_value"]+"\n\n## Business Context\n\n"+project["business_context"]+
                    "\n\n## Requirements\n\n### Validated\n\nNone yet.\n\n### Active\n\n"+
                    ("\n".join("- [ ] **"+item["id"]+"**: "+item["description"] for item in requirements) or "No requirements scoped yet.")+
                    "\n\n### Out of Scope\n\n"+bullets(project["out_of_scope"])+"\n\n## Context\n\n"+project["context"]+
                    "\n\n## Constraints\n\n"+bullets(project["constraints"])+"\n\n## Key Decisions\n\n| Decision | Rationale | Outcome |\n|---|---|---|\n")
    decisions = project.get("decisions", [])
    if not isinstance(decisions, list):
        raise Failure("invalid-project-decisions", "decisions must be an array", 2)
    for decision in decisions:
        if not isinstance(decision, dict) or set(decision)-{"decision", "rationale", "outcome"}:
            raise Failure("invalid-project-decision", "Use decision, rationale and outcome", 2)
        project_text += "| "+cell(_text(decision.get("decision", ""), "decision", True))+" | "+cell(decision.get("rationale", ""))+" | "+cell(decision.get("outcome", "Pending"))+" |\n"
    req_text = "# Requirements: "+project["name"]+"\n\n**Defined:** "+now()[:10]+"\n**Core Value:** "+project["core_value"]+"\n\n## v1 Requirements\n\n"
    for category in dict.fromkeys(item.get("category", "General") for item in requirements):
        req_text += "### "+str(category)+"\n\n"+"\n".join("- [ ] **"+item["id"]+"**: "+item["description"] for item in requirements if item.get("category", "General") == category)+"\n\n"
    req_text += "## v2 Requirements\n\nNone scoped.\n\n## Out of Scope\n\n"+bullets(project["out_of_scope"])+"\n\n## Traceability\n\n| Requirement | Phase | Status |\n|---|---|---|\n"
    for item in requirements:
        mapped = item.get("phase")
        if mapped is None:
            mapped = next((index for index, phase in enumerate(phases, 1) if item["id"] in phase.get("requirements", [])), None)
        req_text += "| "+item["id"]+" | "+("Phase "+str(mapped) if mapped else "Unassigned")+" | Pending |\n"
    roadmap = "# Roadmap: "+project["name"]+"\n\n## Overview\n\n"+project["description"]+"\n\n## Phases\n\n"
    roadmap += "\n".join("- [ ] **Phase "+str(index)+": "+phase["name"]+"** - "+phase["goal"] for index, phase in enumerate(phases, 1))+"\n\n## Phase Details\n\n"
    for index, phase in enumerate(phases, 1):
        dependencies = ", ".join("Phase "+str(dep) for dep in phase.get("depends_on", [])) or "Nothing"
        phase_requirements = list(dict.fromkeys(phase.get("requirements", [])+[item["id"] for item in requirements if str(item.get("phase", "")) == str(index)]))
        roadmap += ("### Phase "+str(index)+": "+phase["name"]+"\n**Goal:** "+phase["goal"]+"\n**Depends on:** "+dependencies+
                    "\n**Requirements:** "+", ".join(phase_requirements)+"\n**Success Criteria:**\n"+
                    "\n".join("  "+str(i)+". "+criterion for i, criterion in enumerate(phase.get("success_criteria", []), 1))+"\n**Plans:** 0 plans\n\n")
    roadmap += "## Progress\n\n| Phase | Plans Complete | Status | Completed |\n|---|---|---|---|\n"
    for index, phase in enumerate(phases, 1):
        roadmap += "| "+str(index)+". "+cell(phase["name"])+" | 0/0 | Not started | - |\n"
    state = join_frontmatter({"engineer_state_version": "1.0", "status": "planning", "progress": {"total_phases": len(phases), "completed_phases": 0, "total_plans": 0, "completed_plans": 0, "percent": 0}},
            "# Project State\n\n## Project Reference\n\nSee: .planning/PROJECT.md\n\n**Core value:** "+project["core_value"]+
            "\n\n## Current Position\n\nPhase: "+("1 of "+str(len(phases))+" ("+phases[0]["name"]+")" if phases else "None")+
            "\nPlan: None\nStatus: Ready to discuss\nLast activity: "+now()[:10]+" — Onboarding initialized\nProgress: 0%\n\n## Performance Metrics\n\nNo execution metrics yet.\n\n## Accumulated Context\n\n### Decisions\n\nNone recorded.\n\n### Pending Todos\n\nNone.\n\n### Blockers/Concerns\n\nNone.\n\n## Session Continuity\n\nLast session: "+now()+"\nStopped at: Onboarding initialized\nResume file: None\n")
    return {"PROJECT.md": project_text, "REQUIREMENTS.md": req_text, "ROADMAP.md": roadmap, "STATE.md": state}


def command(args, action="init"):
    if action in ("init", "create", "onboard", "new-project"):
        project, requirements, phases, settings = _spec(args)
        artifacts = _render(project, requirements, phases)
        base = safe(records.planning())
        if (base/"config.yaml").exists():
            config.load()
        with planning_lock():
            existing = [name for name in artifacts if (base/name).exists()]
            if existing and not args.has("resume"):
                raise Failure("project-already-initialized", "Existing records are preserved; use --resume to create only missing artifacts", existing=existing)
            if (base/"PROJECT.md").exists() and read(base/"PROJECT.md").splitlines()[0] != "# "+project["name"]:
                raise Failure("project-identity-conflict", "Resume input names a different project")
            created = []
            for name, content in artifacts.items():
                path = safe(base/name)
                if not path.exists():
                    write(path, content)
                    created.append(str(path))
            for index, phase in enumerate(phases, 1):
                safe(base/"phases"/(str(index).zfill(2)+"-"+records.slug(phase["name"]))).mkdir(parents=True, exist_ok=True)
        configured = config.new_project(type(args)([json.dumps(settings)]))
        return {"initialized": True, "created": created, "preserved": existing, "config": configured,
                "phase_count": len(phases), "implementation_authorized": False, "project_name": project["name"]}
    if action == "update":
        heading = args.get("section")
        if heading not in SECTIONS or not args.has("content"):
            raise Failure("invalid-project-update", "Choose a narrative --section and --content; structural tables use their runtime verbs", 2)
        path = safe(records.planning()/"PROJECT.md")
        with planning_lock():
            if not path.exists():
                raise Failure("project-not-found", str(path))
            before = read(path)
            write(path, replace_section(before, "## "+heading, _text(args.get("content"), "content")))
        return {"updated": True, "section": heading, "path": str(path)}
    if action in ("get", "status"):
        artifacts = {name: {"path": str(records.planning()/name), "exists": (records.planning()/name).is_file()} for name in ("PROJECT.md", "REQUIREMENTS.md", "ROADMAP.md", "STATE.md")}
        return {"initialized": all(item["exists"] for item in artifacts.values()), "artifacts": artifacts}
    raise Failure("unsupported-onboarding-action", action, 2)
