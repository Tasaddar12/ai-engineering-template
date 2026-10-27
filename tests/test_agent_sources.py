"""Required local inputs for agent methods resolve in the checkout."""
from pathlib import Path
import re
import tomllib
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


def tool_names(value):
    """Shared upstream roles use both YAML lists and comma-separated strings."""
    return set(value if isinstance(value, list) else value.split(", ")) if value else set()


def region(text, opening, closing):
    match = re.search(re.escape(opening) + r"(.*?)" + re.escape(closing), text, re.S)
    return match.group(1) if match else ""


class AgentSourceTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / name).read_text(encoding="utf-8")

    def test_scout_role_uses_the_exported_scout_filenames_and_names(self):
        metadata = yaml.safe_load(self.read("agents/scout.md").split("---", 2)[1])
        native = tomllib.loads(self.read("bin/install-assets/codex-agents/scout.toml"))
        self.assertEqual("scout", metadata["name"])
        self.assertEqual("scout", native["name"])
        self.assertIn("agents/scout.md", native["developer_instructions"])
        self.assertNotIn("model", metadata)
        self.assertNotIn("effort", metadata)
        self.assertEqual("gpt-6-luna", native["model"])
        self.assertEqual("high", native["model_reasoning_effort"])
        self.assertEqual("read-only", native["sandbox_mode"])

    def test_coordinator_uses_explicit_scout_route_and_workers_remain_routed(self):
        dispatch = region(self.read("agents/coordinator.md"), "<dispatch>", "</dispatch>")
        for required in ("source locations are unknown", "one discovery scout", "Distinct additional scouts",
                         "../engineer/references/scout-dispatch.md", "Route by role", "executor", "planner"):
            self.assertIn(required, dispatch)
        self.assertIn("The coordinator dispatches normal workers", self.read("engineer/references/scout-dispatch.md"))

    def test_worker_local_adapters_allow_only_supported_scout_nesting(self):
        for role in (ROOT / "agents").glob("*.md"):
            if role.stem in {"AGENT", "scout", "coordinator", "targeted-fixer", "code-fixer"}:
                continue
            with self.subTest(role=role.name):
                text = role.read_text(encoding="utf-8")
                self.assertIn("../engineer/references/scout-dispatch.md", text)
                self.assertIn("coordinator", text)
                self.assertIn("only named read-only scout packets", text)
                self.assertIn("exact host registration and capacity", text)
                self.assertIn("never create generic/source-writing children", text)
                self.assertIn("The coordinator dispatches normal workers", self.read("engineer/references/scout-dispatch.md"))
                self.assertNotRegex(text, r"Only the (?:coordinator|orchestrator)\s+dispatches\s+agents")

    def test_scout_fallback_preserves_complete_assignments_and_resume_state(self):
        text = self.read("engineer/references/scout-dispatch.md")
        fallback = text.split("scout_request:", 1)[1].split("```", 1)[0]
        for field in ("parent_assignment_id:", "repository:", "revision:", "reason:",
                      "stage:", "assignments:", "requested_fields:", "search_scope:",
                      "constraints:", "resume_with:"):
            self.assertIn(field, fallback)
        for duty in ("queued dispatch", "Join ALL", "citations conflict", "domain owner",
                     "first remaining action", "do not restart the original task"):
            self.assertIn(duty, text)

    def test_precondition_checkpoint_and_failed_truth_precedence_are_preserved(self):
        executor = self.read("agents/executor.md")
        unmet = executor.split("**Unmet:**", 1)[1].split('1. **If', 1)[0]
        for duty in ("STOP", "partial task commit", "blocking-human", "exact precondition",
                     "human may satisfy", "fresh continuation", "plan-phase revision"):
            self.assertIn(duty, unmet)
        verifier = self.read("agents/verifier.md")
        tree = verifier.split("## Step 9: Determine Overall Status", 1)[1].split("## Step 9b", 1)[0]
        for condition in ("truth is FAILED", "artifact is missing or a stub", "PARTIAL or NOT_WIRED",
                          "blocker anti-pattern", "status: gaps_found", "status: human_needed"):
            self.assertIn(condition, tree)
        self.assertLess(tree.index("status: gaps_found"), tree.index("status: human_needed"))

    def test_scout_shared_adapter_is_host_agnostic_and_respects_permissions(self):
        text = self.read("agents/scout.md")
        metadata = yaml.safe_load(text.split("---", 2)[1])
        self.assertTrue({"Read", "Grep", "Glob"} <= tool_names(metadata["tools"]))
        self.assertTrue({"Agent", "Task", "Write", "Edit"} <= tool_names(metadata["disallowedTools"]))
        method = region(text, "<method>", "</method>")
        for instruction in ("native Read/Grep/Glob", "bounded read-only shell", "host actually grants",
                            "permissions", "Do not use shell to bypass a host restriction",
                            "Never silently expand", "exact searched scope"):
            self.assertIn(instruction, method)
        self.assertIn("never dispatch children, modify files, run tests or execute project code", text)
        body = text.split("---", 2)[2]
        for host_setting in ("Claude", "Codex", "Haiku", "Luna", "exec_command", "sandbox_mode"):
            self.assertNotIn(host_setting, body)

    def test_native_models_and_shared_roles_without_model_frontmatter(self):
        luna = {"codebase-mapper", "doc-writer", "doc-verifier", "integration-checker", "scout", "targeted-fixer"}
        definitions = sorted((ROOT / "bin/install-assets/codex-agents").glob("*.toml"))
        self.assertEqual(21, len(definitions))
        self.assertNotIn("code-fixer", {path.stem for path in definitions})
        for definition in definitions:
            with self.subTest(role=definition.stem):
                native = tomllib.loads(definition.read_text(encoding="utf-8"))
                frontmatter = yaml.safe_load(self.read("agents/" + definition.stem + ".md").split("---", 2)[1])
                self.assertEqual(definition.stem, native["name"])
                self.assertEqual(frontmatter["description"], native["description"])
                self.assertEqual("gpt-6-luna" if definition.stem in luna else "gpt-6.1-sol", native["model"])
                self.assertEqual("medium" if definition.stem in {"executor", "doc-verifier", "integration-checker"} else "high", native["model_reasoning_effort"])
                self.assertNotIn("effort", frontmatter)
                self.assertNotIn("model", frontmatter)
                allowed, denied = tool_names(frontmatter.get("tools")), tool_names(frontmatter.get("disallowedTools"))
                self.assertFalse(allowed & denied)
                if definition.stem == "scout":
                    self.assertEqual("read-only", native["sandbox_mode"])
                    self.assertTrue({"Read", "Grep", "Glob"} <= allowed)
                    self.assertTrue({"Agent", "Task", "Write", "Edit"} <= denied)
                elif definition.stem == "targeted-fixer":
                    self.assertEqual("workspace-write", native["sandbox_mode"])
                    self.assertTrue({"Write", "Edit", "Bash"} <= allowed)
                    self.assertTrue({"Agent", "Task"} <= denied)
                    self.assertNotIn("Agent", allowed)
                else:
                    # Read-only specialists may deliberately deny Agent; shared source owns that policy.
                    self.assertTrue({"Read", "Grep", "Glob"} <= allowed)

    def test_targeted_fixer_is_a_bounded_leaf_with_structured_inputs_and_evidence(self):
        text = self.read("agents/targeted-fixer.md")
        for field in ("origin:", "diagnosis_or_finding:", "symbols:", "required_behavior:", "constraints:", "result_destination:",
                      "`checkout`", "`branch`", "`revision`", "`owned_paths`", "`files_deleted`",
                      "`checks`", "`summary_path`", "Stable finding ID", "source evidence", "required property",
                      "Artifact digest", "forbidden paths/resources", "approval/implementation authority"):
            self.assertIn(field, text)
        for boundary in ("leaf role", "do not create children", "discovery beyond the bounded scope",
                         "return one named question to the coordinator", "Missing fields or identity mismatches",
                         "Never create worktrees", "independent", "git add --", "worker-handoff.md",
                         "Do not claim a deferred or unrun check passed"):
            self.assertIn(boundary.lower(), text.lower())

    def test_targeted_fixer_catalogs_link_the_authoritative_role(self):
        for name in ("bin/install-assets/agent-entry.txt", "agents/AGENT.md"):
            text = self.read(name)
            self.assertIn("targeted-fixer", text)
            self.assertIn("targeted-fixer.md)", text)
        roles = self.read("hooks/lib/agent-roles.sh")
        write_roles = re.search(r"^WRITE_ROLES='([^']*)'", roles, re.MULTILINE)[1].split()
        self.assertTrue({"executor", "doc-writer", "debugger", "targeted-fixer", "nyquist-auditor"} <= set(write_roles))
        self.assertFalse((ROOT / "bin/install-assets/codex-agents/code-fixer.toml").exists())

    def test_bounded_correction_dispatch_has_supported_routing_and_retained_gates(self):
        shared = self.read("engineer/references/bounded-correction-dispatch.md")
        dispatch = shared.split("## Host dispatch and isolation", 1)[1]
        for token in ("../../agents/targeted-fixer.md", "engineer_run query resolve-model targeted-fixer --raw",
                      "engineer_run query resolve-effort targeted-fixer --raw", 'subagent_type="targeted-fixer"',
                      "concrete values inline", "omit inherited", "dispatch-isolation", "worktree.create",
                      "worktree-branch-check.md", "worktree-path-safety.md", "harness-worktree",
                      'isolation="worktree"', "Do not emit harness isolation on an orchestrator-worktree call",
                      "originating debugger/reviewer", "fresh independent review and verification"):
            self.assertIn(token, dispatch)
        for name in ("execute-phase", "verify-work", "ship"):
            text = self.read("engineer/workflows/" + name + ".md")
            self.assertIn("targeted-fixer", text)
            self.assertIn("../references/bounded-correction-dispatch.md", text)
            self.assertNotRegex(text, r"(?:models|efforts)\[['\"]targeted-fixer['\"]\]")
        execute = self.read("engineer/workflows/execute-phase.md")
        critical = region(execute, '<step name="code_review_gate">', "</step>")
        for token in ("failures block completion", "bounded isolated correction", "new frozen batch"):
            self.assertIn(token, critical)
        verify = self.read("engineer/workflows/verify-work.md")
        gaps = region(verify, '<step name="plan_gap_closure">', "</step>")
        for token in ("targeted-fixer", "debugger", "planner", "model/effort inline", "workflows/execute-phase.md"):
            self.assertIn(token, gaps)
        self.assertIn("up to three", verify)
        ship = region(self.read("engineer/workflows/ship.md"), '<step name="judge_checks">', "</step>")
        for token in ("at most 2 rounds", "targeted-fixer", "debugger", "ship-repair/return-to-caller", "passed/current", "pr.checks"):
            self.assertIn(token, ship)

    def test_repair_origin_adapters_reference_the_shared_dispatch(self):
        for name in ("debugger", "code-reviewer", "coordinator"):
            with self.subTest(role=name):
                text = self.read("agents/" + name + ".md")
                self.assertIn("engineer/references/bounded-correction-dispatch.md", text)
                self.assertNotIn('subagent_type="targeted-fixer"', text)

    def test_every_role_reads_the_shared_scout_procedure(self):
        for role in (ROOT / "agents").glob("*.md"):
            if role.name in {"AGENT.md", "code-fixer.md"}:
                continue
            with self.subTest(role=role.name):
                self.assertIn("../engineer/references/scout-dispatch.md", role.read_text(encoding="utf-8"))

    def test_agent_required_local_reads_resolve(self):
        for path in (ROOT / "agents").glob("*.md"):
            body = path.read_text(encoding="utf-8")
            for required in re.findall(r"@((?:agents|commands|engineer|docs)/[\w./-]+\.md)", body):
                with self.subTest(agent=path.name, required=required):
                    self.assertTrue((ROOT / required).is_file())


class CommandSummaries(unittest.TestCase):
    """The command and skill summaries are short, structured and machine-edited.

    A repeated line or a numbered list that skips costs an agent context and
    misleads it without failing anything, so it survives until a human notices.
    Scoped to these files on purpose: agent and workflow bodies contain tree
    diagrams and examples where a repeated line is legitimate.
    """

    NUMBERED = re.compile(r"^(\d+)\. ")

    def sources(self):
        yield from sorted(ROOT.glob("commands/*.md"))
        yield from sorted(ROOT.glob("skills/*/SKILL.md"))

    def label(self, path):
        return path.parent.name + "/" + path.name

    def test_no_line_is_repeated_immediately(self):
        for path in self.sources():
            previous = None
            for number, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(), start=1):
                stripped = line.strip()
                if stripped and stripped == previous:
                    self.fail(self.label(path) + ":" + str(number)
                              + " repeats the line above: " + stripped[:70])
                previous = stripped

    def test_numbered_lists_count_up_by_one(self):
        for path in self.sources():
            run = []
            for line in path.read_text(encoding="utf-8").splitlines() + [""]:
                match = self.NUMBERED.match(line.strip())
                if match:
                    run.append(int(match.group(1)))
                    continue
                if len(run) > 1:
                    with self.subTest(file=self.label(path)):
                        self.assertEqual(
                            run, list(range(run[0], run[0] + len(run))),
                            self.label(path) + " has a numbered list that does "
                            "not count up by one: " + str(run))
                run = []

if __name__ == "__main__":
    unittest.main()


class SkillMirror(unittest.TestCase):
    """AGENTS.md promises `skills/` mirrors `commands/` one-for-one.

    Nothing enforced that, so a command could be updated and its skill left
    behind - a host that discovers skills and a host that registers slash
    commands would then behave differently for the same workflow.
    """

    SKIPPED = {"README.md", "COMMAND.md", "install.md"}

    def commands(self):
        return sorted(path for path in (ROOT / "commands").glob("*.md")
                      if path.name not in self.SKIPPED)

    def test_every_command_has_a_skill(self):
        for command in self.commands():
            skill = ROOT / "skills" / command.stem / "SKILL.md"
            self.assertTrue(skill.is_file(),
                            command.name + " has no matching skill at "
                            + skill.as_posix())

    def test_every_skill_has_a_command(self):
        for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
            command = ROOT / "commands" / (skill.parent.name + ".md")
            self.assertTrue(command.is_file(),
                            skill.parent.name + " is a skill with no command")

    def test_each_pair_is_identical(self):
        for command in self.commands():
            skill = ROOT / "skills" / command.stem / "SKILL.md"
            if not skill.is_file():
                continue
            with self.subTest(command=command.name):
                self.assertEqual(
                    skill.read_text(encoding="utf-8"),
                    command.read_text(encoding="utf-8"),
                    command.name + " and its skill have drifted apart; copy the "
                    "command over the skill")
