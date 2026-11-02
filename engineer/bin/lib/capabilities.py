"""Closed retained capability dispatch. Rendering never executes a workflow."""
from . import config
from .core import Failure

EVENTS = ("discuss:pre", "discuss:post", "plan:pre", "plan:post", "execute:wave:pre",
          "execute:wave:post", "execute:post", "verify:pre", "verify:post", "ship:pre", "ship:post")
# Only these retained methods can contribute dispatch. User configuration cannot
# inject shell commands, new roles, provider lanes or removed workflow features.
HOOKS = (
    ("research", "plan:pre", "step", "workflow.research", "agent", "phase-researcher", "researcher"),
    ("pattern-mapper", "plan:pre", "step", "workflow.pattern_mapping", "agent", "pattern-mapper", "planner"),
    ("ui", "plan:pre", "step", "workflow.ui_phase", "skill", "ui-phase", "orchestrator"),
    ("ui", "plan:pre", "gate", "workflow.ui_safety_gate", "query", "check.ui-plan-gate", "orchestrator"),
    ("security", "plan:pre", "contribution", "workflow.security_enforcement", "agent", "planner", "planner"),
    ("tdd", "plan:pre", "contribution", "workflow.tdd_mode", "agent", "planner", "planner"),
    ("tdd", "execute:post", "gate", "workflow.tdd_mode", "query", "tdd.review-checkpoint", "orchestrator"),
    ("code-review", "execute:post", "step", "workflow.code_review", "skill", "code-review", "orchestrator"),
    ("security", "verify:post", "step", "workflow.security_enforcement", "skill", "secure-phase", "orchestrator"),
    ("validation", "verify:post", "step", "workflow.nyquist_validation", "skill", "validate-phase", "orchestrator"),
    ("decisions", "plan:post", "gate", "workflow.context_coverage_gate", "query", "check.decision-coverage-plan", "orchestrator"),
    ("ui", "execute:wave:post", "gate", "workflow.ui_safety_gate", "query", "check.ui-safety-gate", "orchestrator"),
    ("security", "ship:pre", "gate", "workflow.security_enforcement", "query", "security.status", "orchestrator"),
    ("validation", "ship:pre", "gate", "workflow.nyquist_validation", "query", "validation.coverage", "orchestrator"),
)
INSTRUCTIONS = {
    "research": "Research the assigned phase only. Read its CONTEXT, SPEC and requirements. Cite primary versioned sources and actual observations; distinguish missing evidence. Return the assigned RESEARCH artifact and unresolved decisions. Follow the complete phase-researcher role method.",
    "pattern-mapper": "Inspect only the assigned source scope and CONTEXT/RESEARCH file references. Return cited existing patterns, representative paths, consuming interfaces and conflicting examples in the assigned PATTERNS artifact. Source inspection is read-only. Do not infer an approved design or change source. Follow the complete pattern-mapper role method.",
    "ui": "Use the approved phase scope and actual human UI decisions. Generate/check the complete UI-SPEC; unknown approval remains pending. Do not fabricate approval, visual observations or human acceptance.",
    "security": "Preserve phase-unique threat IDs, explicit boundaries, severity, mitigation/acceptance authority and cited evidence. Security review is a specialist judgment, never a source-text pass. Do not resolve or close a threat without its evidence and authority.",
    "tdd": "For behavior-adding tasks record actual RED evidence before implementation and later GREEN evidence. Missing or invalid RED is not passing. Do not reclassify a behavior change solely to bypass TDD. Follow the retained TDD method.",
    "code-review": "Dispatch an independent code-reviewer on a captured revision and explicit base. Findings require stable IDs, exact source citations and required properties. Route bounded repairs through targeted-fixer; preserve the full independent review and remaining scope.",
    "validation": "Assess acceptance-to-test coverage using actual checks and artifacts. Missing execution remains unverified. Dispatch nyquist-auditor only with exact owned test paths and implementation authority; never fabricate a passing test result.",
    "decisions": "Every explicit decision identifier must be traced through the assigned plans and verification artifacts. A reference proves structural coverage only, never delivered behavior or human acceptance.",
}


def command(args, action):
    if action == "events":
        return {"events": list(EVENTS)}
    if action == "list":
        return {"capabilities": sorted(INSTRUCTIONS), "events": list(EVENTS), "closedRegistry": True}
    if action != "render-hooks":
        raise Failure("unknown-capability-action", action, 2)
    point = args.need()
    if point not in EVENTS:
        raise Failure("unknown-loop-event", point, 2)
    settings = config.load()
    active, inactive = [], []
    for identifier, event, kind, key, refkind, target, into in HOOKS:
        if event != point:
            continue
        value = config.lookup(settings, key, identifier == "pattern-mapper")
        enabled = value is True or (identifier == "ui" and value == "auto")
        if not enabled:
            inactive.append({"capId": identifier, "kind": kind, "reason": key+" is disabled"})
            continue
        entry = {"id": identifier+"."+point+"."+kind, "capId": identifier, "point": point,
                 "kind": kind, "into": into, "ref": {refkind: target},
                 "fragment": {"inline": INSTRUCTIONS[identifier]}, "configValues": {}}
        if refkind == "query":
            entry["check"] = {"query": target, "args": ["{phase}"]}
            entry["blocking"] = True
            entry["onError"] = "halt"
        if identifier == "security":
            entry["configValues"] = {"security_asvs_level": config.lookup(settings, "workflow.security_asvs_level", 1),
                                     "security_block_on": config.lookup(settings, "workflow.security_block_on", "high")}
        if identifier == "ui":
            entry["condition"] = "UI applicability and actual approval are evaluated by check.ui-plan-gate"
        if args.has("after-fingerprint"):
            entry["requiresCurrentVerification"] = str(args.get("after-fingerprint"))
        active.append(entry)
    if args.has("active-cap"):
        return any(item["capId"] == args.get("active-cap") for item in active)
    caps = [{"id": name, "capId": name} for name in dict.fromkeys(item["capId"] for item in active)]
    return {"point": point, "activeHooks": active, "activeCaps": caps, "inactiveHooks": inactive, "executes": False}
