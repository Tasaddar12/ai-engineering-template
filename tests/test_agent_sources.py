"""Required local inputs for agent methods resolve in the checkout."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentSourceTests(unittest.TestCase):
    def test_agent_required_local_reads_resolve(self):
        for path in (ROOT / ".ai/agents").glob("*.md"):
            body = path.read_text(encoding="utf-8")
            for required in re.findall(r"@((?:\.ai|docs)/[\w./-]+\.md)", body):
                with self.subTest(agent=path.name, required=required):
                    self.assertTrue((ROOT / required).is_file())


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
