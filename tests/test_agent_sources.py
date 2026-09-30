"""Required local inputs for agent methods resolve in the checkout."""
from pathlib import Path
import re
import tomllib
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class AgentSourceTests(unittest.TestCase):
    def test_native_models_and_scout_only_frontmatter_exception(self):
        luna = {"codebase-mapper", "doc-writer", "doc-verifier", "integration-checker", "luna_scout"}
        for definition in (ROOT / ".ai/install-assets/codex-agents").glob("*.toml"):
            native = tomllib.loads(definition.read_text(encoding="utf-8"))
            role = ROOT / ".ai/agents" / (definition.stem + ".md")
            frontmatter = yaml.safe_load(role.read_text(encoding="utf-8").split("---", 2)[1])
            self.assertEqual(definition.stem, native["name"])
            self.assertEqual(frontmatter["description"], native["description"])
            self.assertEqual("gpt-6-luna" if definition.stem in luna else "gpt-6.1-sol", native["model"])
            self.assertEqual("medium" if definition.stem in {"doc-verifier", "integration-checker"} else "high",
                             native["model_reasoning_effort"])
            self.assertNotIn("effort", frontmatter)
            if definition.stem == "luna_scout":
                self.assertEqual("haiku", frontmatter["model"])
                self.assertEqual("read-only", native["sandbox_mode"])
                self.assertEqual({"Read", "Grep", "Glob"}, set(frontmatter["tools"].split(", ")))
                self.assertTrue({"Agent", "Task", "Write", "Edit", "Bash"} <= set(frontmatter["disallowedTools"].split(", ")))
            else:
                self.assertNotIn("model", frontmatter)
                self.assertIn("Agent", frontmatter["tools"].split(", "))
                self.assertNotIn("Agent", frontmatter.get("disallowedTools", "").split(", "))
                self.assertNotIn("Task", frontmatter.get("disallowedTools", "").split(", "))

    def test_every_role_reads_the_shared_scout_procedure(self):
        for role in (ROOT / ".ai/agents").glob("*.md"):
            if role.name == "README.md":
                continue
            with self.subTest(role=role.name):
                self.assertIn("../references/scout-dispatch.md", role.read_text(encoding="utf-8"))

    def test_agent_required_local_reads_resolve(self):
        for path in (ROOT / ".ai/agents").glob("*.md"):
            body = path.read_text(encoding="utf-8")
            for required in re.findall(r"@((?:\.ai|docs)/[\w./-]+\.md)", body):
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
        yield from sorted(ROOT.glob(".ai/commands/*.md"))
        yield from sorted(ROOT.glob(".agents/skills/*/SKILL.md"))

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
    """AGENTS.md promises `.agents/skills/` mirrors `.ai/commands/` one-for-one.

    Nothing enforced that, so a command could be updated and its skill left
    behind - a host that discovers skills and a host that registers slash
    commands would then behave differently for the same workflow.
    """

    SKIPPED = {"README.md", "install.md"}

    def commands(self):
        return sorted(path for path in (ROOT / ".ai" / "commands").glob("*.md")
                      if path.name not in self.SKIPPED)

    def test_every_command_has_a_skill(self):
        for command in self.commands():
            skill = ROOT / ".agents" / "skills" / command.stem / "SKILL.md"
            self.assertTrue(skill.is_file(),
                            command.name + " has no matching skill at "
                            + skill.as_posix())

    def test_every_skill_has_a_command(self):
        for skill in sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md")):
            command = ROOT / ".ai" / "commands" / (skill.parent.name + ".md")
            self.assertTrue(command.is_file(),
                            skill.parent.name + " is a skill with no command")

    def test_each_pair_is_identical(self):
        for command in self.commands():
            skill = ROOT / ".agents" / "skills" / command.stem / "SKILL.md"
            if not skill.is_file():
                continue
            with self.subTest(command=command.name):
                self.assertEqual(
                    skill.read_text(encoding="utf-8"),
                    command.read_text(encoding="utf-8"),
                    command.name + " and its skill have drifted apart; copy the "
                    "command over the skill")
