"""Runtime launcher parity: port of upstream tests/runtime-launcher-parity.test.cjs."""
import importlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
LIB = SOURCE / "engineer" / "bin" / "lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package; `.ai/runtime/lib` also claims the name `lib`."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB / "__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib." + name)


parity = _load("runtime_launcher_parity")

SNIPPET = parity.read_text(parity.SNIPPET_FILE)
PREAMBLE = parity.expected_preamble(SNIPPET)
SNIPPET_RELATIVE = "engineer/workflows/_runtime-launcher.snippet.sh"
needs_shell = unittest.skipUnless(parity.shell_available(), "bash and sh are required for launcher fixtures")


def hard_error_position(snippet: str) -> int:
    return snippet.index("exit 1", snippet.index(parity.HARD_ERROR))


class FixtureCase(unittest.TestCase):
    """Temp-dir helpers; every fixture runs from a non-git working directory."""

    def temp(self, prefix="engineer 373 "):
        directory = tempfile.TemporaryDirectory(prefix=prefix)
        self.addCleanup(directory.cleanup)
        return Path(directory.name)

    def launch(self, body="", exports=None, home=None, path=None, work=None, env=None, snippet=SNIPPET, unset=("ENGINEER_RUN",)):
        work = work or self.temp("engineer work ")
        home = home or self.temp("engineer home ")
        overrides = {"HOME": parity.posix(home), "PATH": path if path is not None else parity.build_isolated_path(), **(env or {})}
        script = parity.snippet_script(snippet, body, exports, unset)
        return parity.run_script(script, work, parity.snippet_env(overrides))


class StructuralParity(unittest.TestCase):
    def test_bootstrap_only_preamble_placement_preserved(self):
        self.skipTest("scripts/sync-runtime-launcher.cjs (transformFile) absent in this repo")

    def test_a_no_retired_gsd_sdk_token_in_workflows(self):
        files = parity.collect_markdown(parity.WORKFLOWS_DIR)
        self.assertGreater(len(files), 0)
        self.assertEqual([], parity.token_offenders(files, parity.WORKFLOWS_DIR, "GSD_SDK"))

    def test_a2_every_default_arm_is_covered_by_the_scrub_lists(self):
        covered = {*parity.SNIPPET_SCRUB, *parity.CALLER_OR_SELF_ASSIGNED}
        extracted = parity.default_arm_vars(SNIPPET)
        # Upstream requires 15 arms (its registry spans many runtimes); this snippet reads five.
        self.assertGreaterEqual(len(extracted), 5, extracted)
        self.assertEqual([], parity.uncovered_default_vars(SNIPPET, covered))

    def test_b_workflows_hold_exactly_one_canonical_preamble_before_first_use(self):
        # Violation: 20 workflow files (add-backlog.md, audit-milestone.md, debug.md, ...) still carry the
        # legacy one-line `_ENGINEER_SHIM_NAME=` launcher instead of the canonical snippet.
        files = parity.collect_markdown(parity.WORKFLOWS_DIR)
        self.assertGreater(len(files), 0)
        self.assertEqual([], parity.preamble_violations(files, parity.WORKFLOWS_DIR, PREAMBLE))

    def test_b2_resolver_reference_matches_the_snippet(self):
        reference = parity.read_text(parity.RESOLVER_REFERENCE)
        self.assertEqual([], parity.resolver_reference_violations(reference, SNIPPET, SNIPPET_RELATIVE))

    def test_m_config_homes_precede_the_path_candidate_and_all_candidates_are_identity_gated(self):
        candidates = parity.select_candidates(SNIPPET)
        self.assertGreaterEqual(len(candidates), 7, candidates)
        home_claude = parity.candidate_index(candidates, "$HOME/.claude}")
        home_codex = parity.candidate_index(candidates, "$HOME/.codex}")
        path_arm = parity.candidate_index(candidates, "_engineer_path_candidate")
        self.assertNotEqual(-1, home_claude, "snippet must probe the Claude config home")
        self.assertNotEqual(-1, home_codex, "snippet must probe the Codex config home")
        self.assertNotEqual(-1, path_arm, "snippet must keep the PATH fallback arm")
        self.assertLess(max(home_claude, home_codex), path_arm, "local installs outrank PATH")
        self.assertEqual(len(candidates) - 1, path_arm, "PATH candidate is the last arm")
        select_body = SNIPPET[SNIPPET.index("_engineer_select() {"):SNIPPET.index("if [ -n \"${ENGINEER_RUN:-}\" ]")]
        self.assertIn('_engineer_identity_ok "$_engineer_candidate"', select_body)
        self.assertIn("command -v engineer_run", SNIPPET)
        self.assertGreater(SNIPPET.index('ENGINEER_RUN="$_engineer_candidate"'), SNIPPET.index("_engineer_identity_ok() {"))

    def test_n_delegation_roster_loads_the_resolver_by_include(self):
        roster = {name: parity.AGENTS_DIR / name for name in ("executor.md", "plan-checker.md", "verifier.md", "planner.md")}
        roster["execute-phase.md"] = parity.WORKFLOWS_DIR / "execute-phase.md"
        self.assertEqual([], parity.roster_violations(roster))

    def test_n_execute_plan_workflow_absent(self):
        self.skipTest("workflows/execute-plan.md absent in this repo")

    def test_g_claude_home_arm_precedes_the_hard_error_and_is_propagated(self):
        probe = ".claude/engineer/bin/"
        self.assertIn(probe, SNIPPET)
        self.assertLess(SNIPPET.index(probe), hard_error_position(SNIPPET))
        self.assertIn("${CLAUDE_CONFIG_DIR:-$HOME/.claude}", SNIPPET)
        files = parity.collect_markdown(parity.WORKFLOWS_DIR)
        self.assertEqual([], parity.files_missing_probe(files, parity.WORKFLOWS_DIR, probe))

    def test_h_codex_arm_is_present_and_propagated(self):
        probe = ".codex/engineer/bin/"
        self.assertIn(probe, SNIPPET)
        self.assertLess(SNIPPET.index(probe), hard_error_position(SNIPPET))
        files = parity.collect_markdown(parity.WORKFLOWS_DIR)
        self.assertEqual([], parity.files_missing_probe(files, parity.WORKFLOWS_DIR, probe))

    def test_f0_snippet_braces_are_balanced(self):
        depth, lowest = parity.brace_depth(SNIPPET)
        self.assertEqual(0, depth, "unbalanced braces in the snippet")
        self.assertEqual(0, lowest, "a closing brace precedes its opener")

    def test_f_snippet_has_no_engineer_tools_substring(self):
        self.assertNotIn("/engineer-tools", SNIPPET)

    def test_f2_do_workflow_dispatcher_scan(self):
        self.skipTest("workflows/do.md and the /gsd[:-] dispatcher-parity scanner absent in this repo")


@needs_shell
class BehavioralResolution(FixtureCase):
    def test_c_launcher_resolves_through_a_runtime_dir_with_spaces(self):
        base = self.temp("engineer 373 ")
        parity.write_runtime_stub(base, "STUB", kind="")
        result = self.launch('engineer_run query state.json', exports={"RUNTIME_DIR": parity.posix(base)})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("STUB:query state.json", result.stdout)

    def test_d_missing_launcher_is_a_loud_failure(self):
        base = self.temp("engineer 373 notools ")
        result = self.launch('engineer_run query state.json', exports={"RUNTIME_DIR": parity.posix(base)})
        self.assertNotEqual(0, result.returncode)
        self.assertIn(parity.HARD_ERROR, result.stderr)

    def test_e_path_fallback_uses_an_identity_proving_installed_launcher(self):
        base = self.temp("engineer 373 pathfb ")
        parity.write_launcher_stub(base / "bin", "installed")
        path = os.pathsep.join([parity.posix(base / "bin"), parity.build_isolated_path()])
        result = self.launch('printf "ENGINEER_RUN=%s\\n" "$ENGINEER_RUN"\nengineer_run query state.json',
                             exports={"RUNTIME_DIR": parity.posix(base)}, path=path)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertRegex(result.stdout.replace("\\", "/"), r"(?m)^ENGINEER_RUN=.+/bin/engineer_run$")
        self.assertIn("installed:query state.json", result.stdout)

    def test_k_foreign_path_launcher_cannot_hijack_a_config_home_install(self):
        home, foreign = self.temp("engineer-home-"), self.temp("engineer-foreign-")
        parity.write_runtime_stub(home, "LOCAL", kind=".claude")
        parity.write_launcher_stub(foreign, "FOREIGN", identity=False)
        path = os.pathsep.join([parity.posix(foreign), parity.build_isolated_path()])
        result = self.launch('printf "ENGINEER_RUN=%s\\n" "$ENGINEER_RUN"\nengineer_run query git.base-branch --is-protected master',
                             home=home, path=path, exports={"RUNTIME_DIR": parity.posix(self.temp("engineer-rt-"))})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(".claude/engineer/bin/", result.stdout.replace("\\", "/"))
        self.assertIn("LOCAL:query git.base-branch --is-protected master", result.stdout)
        self.assertNotIn("FOREIGN:", result.stdout)

    def test_k2_resolved_tool_honors_default_branch_override(self):
        self.skipTest("git.allow_default_branch_commits override absent in this repo's runtime")

    def test_d2_foreign_path_launcher_with_no_install_still_hard_errors(self):
        foreign = self.temp("engineer-foreign-")
        parity.write_launcher_stub(foreign, "FOREIGN", identity=False)
        path = os.pathsep.join([parity.posix(foreign), parity.build_isolated_path()])
        result = self.launch("engineer_run ping test", path=path, exports={"RUNTIME_DIR": parity.posix(self.temp("engineer-rt-"))})
        self.assertNotEqual(0, result.returncode)
        self.assertIn(parity.HARD_ERROR, result.stderr)
        self.assertNotIn("FOREIGN:", result.stdout)

    def test_l_config_home_install_outranks_an_identity_proving_path_launcher(self):
        home, path_bin = self.temp("engineer-home-"), self.temp("engineer-path-")
        parity.write_runtime_stub(home, "LOCAL", kind=".claude")
        parity.write_launcher_stub(path_bin, "PATHSTUB")
        path = os.pathsep.join([parity.posix(path_bin), parity.build_isolated_path()])
        result = self.launch('printf "ENGINEER_RUN=%s\\n" "$ENGINEER_RUN"\nengineer_run query state.json',
                             home=home, path=path, exports={"RUNTIME_DIR": parity.posix(self.temp("engineer-rt-"))})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(".claude/engineer/bin/", result.stdout.replace("\\", "/"))
        self.assertIn("LOCAL:query state.json", result.stdout)
        self.assertNotIn("PATHSTUB:", result.stdout)

    def test_h_codex_home_default_resolves_when_path_has_no_launcher(self):
        home = self.temp("engineer-codex-home-")
        parity.write_runtime_stub(home, "CODEX_HOME_STUB", kind=".codex")
        result = self.launch('printf "ENGINEER_RUN=%s\\n" "$ENGINEER_RUN"\nengineer_run query init.quick',
                             home=home, exports={"RUNTIME_DIR": parity.posix(self.temp("engineer-codex-rt-"))})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(".codex/engineer/bin/", result.stdout.replace("\\", "/"))
        self.assertIn("CODEX_HOME_STUB:query init.quick", result.stdout)


class ModuleUnits(FixtureCase):
    def test_extract_shell_blocks_handles_indent_and_languages(self):
        text = "intro\n```bash\na\nb\n```\n```python\nprint()\n```\n  ```sh\n  c\n  ```\n```\nd\n```\n"
        blocks = parity.extract_shell_blocks(text)
        self.assertEqual([["a", "b"], ["  c"], ["d"]], [block["lines"] for block in blocks])
        self.assertEqual([0, 1, 2], [block["index"] for block in blocks])

    def test_preamble_violations_count_order_and_delegation(self):
        base = self.temp("units-")
        pre = ["_engineer_identity_ok() {", "}"]
        fence = lambda *lines: "```bash\n" + "\n".join(lines) + "\n```\n"  # noqa: E731
        (base / "ok.md").write_text(fence(*pre, "engineer_run x"), encoding="utf-8")
        (base / "none.md").write_text(fence("engineer_run x"), encoding="utf-8")
        (base / "twice.md").write_text(fence(*pre) + fence(*pre, "engineer_run x"), encoding="utf-8")
        (base / "late.md").write_text(fence("engineer_run x") + fence(*pre), encoding="utf-8")
        (base / "delegates.md").write_text("@~/.claude/engineer/references/run-resolver.md\n" + fence("engineer_run x"), encoding="utf-8")
        (base / "unused.md").write_text(fence("echo hi"), encoding="utf-8")
        found = parity.preamble_violations(sorted(base.glob("*.md")), base, pre)
        self.assertEqual(["late.md", "none.md", "twice.md"], sorted(item.split(":")[0] for item in found))
        self.assertIn("found 2", next(item for item in found if item.startswith("twice")))
        self.assertIn("AFTER", next(item for item in found if item.startswith("late")))

    def test_files_missing_probe_and_token_offenders(self):
        base = self.temp("units-")
        (base / "a.md").write_text("```bash\nengineer_run x\n.claude/engineer/bin/\n```\n", encoding="utf-8")
        (base / "b.md").write_text("```bash\nengineer_run x\n```\nGSD_SDK\n", encoding="utf-8")
        files = sorted(base.glob("*.md"))
        self.assertEqual(["b.md"], parity.files_missing_probe(files, base, ".claude/engineer/bin/"))
        self.assertEqual(["b.md"], parity.token_offenders(files, base, "GSD_SDK"))

    def test_default_arm_vars_and_uncovered(self):
        text = 'a="${ONE:-x}" b="${TWO:-y}" c="${ONE:-z}" d=${THREE}'
        self.assertEqual(["ONE", "TWO"], parity.default_arm_vars(text))
        self.assertEqual(["TWO"], parity.uncovered_default_vars(text, {"ONE"}))

    def test_brace_depth(self):
        self.assertEqual((0, 0), parity.brace_depth("{ ${a} }"))
        self.assertEqual((1, 0), parity.brace_depth("{"))
        self.assertEqual((0, -1), parity.brace_depth("} {"))

    def test_select_candidates_reads_the_ordered_list(self):
        self.assertEqual(['"$a/x"', '"$b/y"'], parity.select_candidates('  _engineer_select \\\n    "$a/x" \\\n    "$b/y" || {\n'))
        self.assertEqual([], parity.select_candidates("no select here"))

    def test_resolver_reference_violations(self):
        fence = lambda body: "```bash\n" + body + "\n```\n"  # noqa: E731
        self.assertEqual([], parity.resolver_reference_violations(fence("a\nb"), "a\nb\n", "x.sh"))
        self.assertEqual([], parity.resolver_reference_violations(fence(". engineer/x.sh"), "a\n", "x.sh"))
        self.assertEqual(1, len(parity.resolver_reference_violations(fence(". other/y.sh"), "a\n", "x.sh")))
        self.assertEqual(1, len(parity.resolver_reference_violations(fence("drifted"), "a\n", "x.sh")))

    def test_roster_violations(self):
        base = self.temp("units-")
        (base / "good.md").write_text("@~/.claude/references/run-resolver.md\n", encoding="utf-8")
        (base / "inline.md").write_text("@~/.claude/references/run-resolver.md\n_engineer_identity_ok() {\n", encoding="utf-8")
        (base / "missing.md").write_text("nothing\n", encoding="utf-8")
        found = parity.roster_violations({name: base / name for name in ("good.md", "inline.md", "missing.md")})
        self.assertEqual(2, len(found))
        self.assertTrue(found[0].startswith("inline.md") and found[1].startswith("missing.md"))

    def test_snippet_env_scrubs_steering_variables_in_any_case(self):
        env = parity.snippet_env({"PATH": "p"}, base={"Path": "ambient", "CODEX_HOME": "x", "KEEP": "1"})
        self.assertEqual("", env["CODEX_HOME"])
        self.assertEqual("p", env["PATH"])
        self.assertNotIn("Path", env)
        self.assertEqual("1", env["KEEP"])

    def test_build_isolated_path_filters_launcher_dirs_and_relative_entries(self):
        has, empty = self.temp("units-has-"), self.temp("units-empty-")
        parity.write_launcher_stub(has, "X")
        joined = os.pathsep.join([str(has), "", ".", "sub/dir", str(empty)])
        self.assertEqual(str(empty), parity.build_isolated_path(joined))
        self.assertEqual("", parity.build_isolated_path(str(has)))

    def test_expected_preamble_rejects_empty(self):
        self.assertEqual(["a", "b"], parity.expected_preamble("a\nb\n"))
        with self.assertRaises(ValueError):
            parity.expected_preamble("")

    def test_quote_survives_single_quotes(self):
        self.assertEqual("'a'\"'\"'b'", parity.quote("a'b"))



@needs_shell
class StandaloneExecutable(FixtureCase):
    def test_launcher_needs_no_dirname_with_only_python_on_path(self):
        self.check_restricted_launcher("has space")

    def test_launcher_handles_apostrophe_with_only_python_on_path(self):
        self.check_restricted_launcher("O'Connor project")

    @unittest.skipIf(os.name == "nt", "backslashes are separators in Windows filenames")
    def test_launcher_preserves_literal_posix_backslashes(self):
        self.check_restricted_launcher("has\\backslash space")

    def check_restricted_launcher(self, directory_name):
        base = self.temp("engineer-restricted-path-") / directory_name
        wrappers = parity.python_wrapper_dir(self.temp("engineer-only-python-"), sys.executable)
        for runtime_layout in (Path("engineer") / "bin", Path(".codex") / "engineer" / "bin"):
            with self.subTest(runtime_layout=str(runtime_layout)):
                bin_dir = base / runtime_layout
                bin_dir.mkdir(parents=True)
                launcher = bin_dir / parity.LAUNCHER
                launcher.write_bytes((SOURCE / "engineer/bin" / parity.LAUNCHER).read_bytes())
                (bin_dir / "engineer.py").write_text("import sys\nprint('RESTRICTED_OK:' + ' '.join(sys.argv[1:]))\n", encoding="utf-8")
                # str(Path) supplies native backslashes on Windows; as_posix also covers
                # snippet callers. Both must work with no dirname/tr/cygpath on PATH.
                relative = launcher.relative_to(base)
                for script_path in dict.fromkeys((str(launcher), launcher.as_posix(), str(relative), relative.as_posix())):
                    with self.subTest(script_path=script_path):
                        result = subprocess.run([parity.sh_path(), script_path, "query", "restricted"],
                                                env={**os.environ, "PATH": parity.posix(wrappers)},
                                                cwd=base, capture_output=True, text=True)
                        self.assertEqual(0, result.returncode, result.stderr)
                        self.assertIn("RESTRICTED_OK:query restricted", result.stdout)

    """Upstream (#381): the shipped launcher delegates beside itself; the preamble persists its bin dir."""

    def test_i_launcher_executable_delegates_to_engineer_py_beside_it(self):
        base = self.temp("engineer-381-I-")
        bin_dir = base / "engineer" / "bin"
        bin_dir.mkdir(parents=True)
        launcher = bin_dir / parity.LAUNCHER
        launcher.write_bytes((SOURCE / "engineer" / "bin" / parity.LAUNCHER).read_bytes())
        launcher.chmod(0o755)
        (bin_dir / "engineer.py").write_text("import sys\nprint('ENGINEER_STUB:' + ' '.join(sys.argv[1:]))\n", encoding="utf-8")
        wrappers = parity.python_wrapper_dir(self.temp("engineer-py-"), sys.executable)
        env = {**os.environ, "PATH": os.pathsep.join([parity.posix(wrappers), os.environ.get("PATH", "")])}
        result = parity.run_launcher_executable(launcher, ["query", "x"], env)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("ENGINEER_STUB:query x", result.stdout)

    def persisted(self, directory_name):
        base = self.temp("engineer-381-J-") / directory_name
        stub = parity.write_runtime_stub(base, "ENGINEER_RUN_STUB", kind="")
        env_file = base.parent / "envfile"
        result = self.launch("", exports={"RUNTIME_DIR": parity.posix(base)}, env={"CLAUDE_ENV_FILE": parity.posix(env_file)})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(env_file.exists(), "CLAUDE_ENV_FILE must be created after the preamble runs")
        return stub, env_file

    def test_j_preamble_persists_the_bin_dir_to_claude_env_file(self):
        _, env_file = self.persisted("has space")
        line = parity.env_file_path_line(parity.read_text(env_file))
        self.assertTrue(line.startswith('export PATH="'), line)
        self.assertIn("has space/engineer/bin", line.replace("\\", "/"))
        self.assertTrue(line.endswith(':$PATH"'), line)
        if os.name == "nt":
            return  # Git Bash keeps `C:/` drive paths colon-joined in PATH; upstream skips this half on win32 too.
        # A later fresh shell gets the launcher by sourcing the file; it never had the bin dir on PATH before.
        result = parity.run_shell_text('. "$CLAUDE_ENV_FILE"; engineer_run hello',
                                       parity.snippet_env({"CLAUDE_ENV_FILE": parity.posix(env_file), "PATH": os.environ.get("PATH", "")}))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("ENGINEER_RUN_STUB:hello", result.stdout)

    def test_j_persisted_line_escapes_shell_metacharacters(self):
        _, env_file = self.persisted("a$b`c")
        line = parity.env_file_path_line(parity.read_text(env_file))
        self.assertIn("a\\$b\\`c", line, "$ and backtick must be escaped inside the double-quoted export")
        result = parity.run_shell_text('. "$CLAUDE_ENV_FILE"; printf %s "$PATH"',
                                       parity.snippet_env({"CLAUDE_ENV_FILE": parity.posix(env_file), "PATH": os.environ.get("PATH", "")}))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("a$b`c/engineer/bin", result.stdout.replace("\\", "/"))


class AgentParity(unittest.TestCase):
    def test_b_agents_hold_exactly_one_canonical_preamble_before_first_use(self):
        # Violation: agents/code-fixer.md, code-reviewer.md, debug-session-manager.md, debugger.md,
        # phase-researcher.md and ui-researcher.md use engineer_run without the canonical preamble
        # (code-fixer.md carries the legacy one-line `_ENGINEER_SHIM_NAME=` launcher; the rest carry none).
        files = parity.collect_markdown(parity.AGENTS_DIR)
        self.assertGreater(len(files), 0)
        self.assertEqual([], parity.preamble_violations(files, parity.AGENTS_DIR, PREAMBLE))


class ClaudeHomeFallback(FixtureCase):
    """Upstream bug-211: the Claude config home is probed before the hard error."""

    def test_a_snippet_contains_the_claude_home_arm(self):
        self.assertIn(".claude/engineer/bin/", SNIPPET)

    def test_b_representative_propagated_file_contains_the_arm(self):
        self.assertIn(".claude/engineer/bin/", parity.read_text(parity.WORKFLOWS_DIR / "add-phase.md"))

    @needs_shell
    def test_c_resolves_the_claude_home_stub_when_nothing_else_matches(self):
        home = self.temp("engineer-211-home-")
        parity.write_runtime_stub(home, "CLAUDE_HOME_STUB", kind=".claude")
        result = self.launch('printf "ENGINEER_RUN=%s\\n" "$ENGINEER_RUN"\nengineer_run ping test',
                             home=home, exports={"RUNTIME_DIR": parity.posix(self.temp("engineer-211-rt-"))})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(".claude/engineer/bin/", result.stdout.replace("\\", "/"))
        self.assertIn("CLAUDE_HOME_STUB:ping test", result.stdout)

    @needs_shell
    def test_c2_claude_config_dir_outranks_the_default_home(self):
        home, config = self.temp("engineer-211-home-"), self.temp("engineer-211-cfg-")
        parity.write_runtime_stub(home, "DEFAULT_HOME", kind=".claude")
        parity.write_runtime_stub(config, "CONFIG_DIR", kind="")
        result = self.launch("engineer_run ping test", home=home, env={"CLAUDE_CONFIG_DIR": parity.posix(config)},
                             exports={"RUNTIME_DIR": parity.posix(self.temp("engineer-211-rt-"))})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("CONFIG_DIR:ping test", result.stdout)
        self.assertNotIn("DEFAULT_HOME", result.stdout)

    @needs_shell
    def test_d_hard_error_when_local_path_and_claude_home_all_miss(self):
        result = self.launch("engineer_run ping test", exports={"RUNTIME_DIR": parity.posix(self.temp("engineer-211-nort-"))})
        self.assertNotEqual(0, result.returncode)
        self.assertIn(parity.HARD_ERROR, result.stderr)


class NonClaudeRuntimeHomes(FixtureCase):
    """Upstream bug-891, narrowed to the runtime homes this repo has: Claude and Codex."""

    EXPECTED_PROBES = {"codex": "${CODEX_HOME:-$HOME/.codex}/engineer/bin/"}

    def test_a_snippet_contains_every_non_claude_runtime_home_probe(self):
        missing = [name for name, probe in self.EXPECTED_PROBES.items() if probe not in SNIPPET]
        self.assertEqual([], missing)

    def test_a_other_runtime_home_probes(self):
        self.skipTest("hermes, cursor, copilot, windsurf, augment, trae, qwen, codebuddy, cline, grok, antigravity, "
                      "opencode, kilo, zcode, pi, kimi and kimi-code runtime homes absent in this repo")

    def test_a2_codex_probe_follows_the_claude_arm_and_precedes_the_hard_error(self):
        claude, error = SNIPPET.index(".claude/engineer/bin/"), hard_error_position(SNIPPET)
        self.assertLess(claude, SNIPPET.index(self.EXPECTED_PROBES["codex"]))
        self.assertLess(SNIPPET.index(self.EXPECTED_PROBES["codex"]), error)

    def test_b0_isolated_path_invariants(self):
        # Upstream also asserts node survives on the isolated PATH; the launcher here is a shell script.
        has, empty = self.temp("engineer-891-colocated-"), self.temp("engineer-891-empty-")
        parity.write_launcher_stub(has, "X")
        self.assertFalse(parity.has_launcher(empty))
        self.assertTrue(parity.has_launcher(has))
        sep = os.pathsep
        cases = {
            "emptyElement": (f"{empty}{sep}{sep}{empty}", [str(empty), str(empty)]),
            "dotElement": (f"{empty}{sep}.{sep}{empty}", [str(empty), str(empty)]),
            "relativeElement": (f"{empty}{sep}sub/dir", [str(empty)]),
            "fullyFiltered": (str(has), []),
            "launcherDirDropped": (f"{has}{sep}{empty}", [str(empty)]),
        }
        for label, (base_path, expected) in cases.items():
            with self.subTest(label):
                result = parity.build_isolated_path(base_path)
                self.assertEqual(expected, result.split(sep) if result else [], f"{label}: {result}")

    @needs_shell
    def test_b_isolated_path_strips_a_leaked_launcher_and_codex_home_wins(self):
        sentinel = self.temp("engineer-4205-sentinel-")
        parity.write_launcher_stub(sentinel, "SENTINEL_INVOKED", identity=False)
        isolated = parity.build_isolated_path(os.pathsep.join([str(sentinel), os.environ.get("PATH", "")]))
        self.assertNotIn(str(sentinel), isolated.split(os.pathsep))
        codex_home, home = self.temp("engineer-891-codex-"), self.temp("engineer-891-home-")
        parity.write_runtime_stub(codex_home, "CODEX_HOME_STUB", kind="")
        result = self.launch('printf "ENGINEER_RUN=%s\\n" "$ENGINEER_RUN"\nengineer_run ping test', home=home, path=isolated,
                             env={"CODEX_HOME": parity.posix(codex_home)}, exports={"RUNTIME_DIR": parity.posix(self.temp("engineer-891-rt-"))})
        normalized = result.stdout.replace("\\", "/")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("SENTINEL_INVOKED", normalized)
        self.assertNotIn(sentinel.name, normalized)
        self.assertIn(parity.posix(codex_home), normalized)
        self.assertIn("CODEX_HOME_STUB:ping test", normalized)

    @needs_shell
    def test_c_default_codex_home_is_used_when_codex_home_is_unset(self):
        home = self.temp("engineer-891-home-")
        parity.write_runtime_stub(home, "CODEX_DEFAULT_STUB", kind=".codex")
        result = self.launch("engineer_run status", home=home, exports={"RUNTIME_DIR": parity.posix(self.temp("engineer-891-rt2-"))},
                             unset=("ENGINEER_RUN", "CODEX_HOME"))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("CODEX_DEFAULT_STUB:status", result.stdout)

    def test_d_resolution_order_claude_then_codex_then_error(self):
        candidates = parity.select_candidates(SNIPPET)
        self.assertLess(parity.candidate_index(candidates, "$HOME/.claude}"), parity.candidate_index(candidates, "$HOME/.codex}"))
        self.assertLess(SNIPPET.index("_engineer_select \\"), hard_error_position(SNIPPET))

    def test_e_every_inline_workflow_carries_the_codex_probe(self):
        files = parity.collect_markdown(parity.WORKFLOWS_DIR)
        self.assertGreater(len(files), 0)
        self.assertEqual([], parity.files_missing_probe(files, parity.WORKFLOWS_DIR, "$HOME/.codex}"))


class WorkflowResolution(FixtureCase):
    """Upstream bug-3668: the resolver extracted from a shipped workflow supports installed user projects."""

    def resolver(self):
        return parity.extract_resolver_snippet(parity.read_text(parity.WORKFLOWS_DIR / "next.md"))

    def run_resolver(self, runtime_dir, path_dir, home=None):
        self.assertTrue(runtime_dir, "an empty RUNTIME_DIR silently resolves the real repo root")
        body = 'printf "ENGINEER_RUN=%s\\n" "$ENGINEER_RUN"\nengineer_run query state.json'
        path = os.pathsep.join([parity.posix(path_dir), parity.build_isolated_path()])
        script = "set -e\n" + parity.snippet_script(self.resolver(), body, {"RUNTIME_DIR": parity.posix(runtime_dir)})
        work, fake_home = self.temp("engineer work "), home or self.temp("engineer home ")
        env = parity.snippet_env({"HOME": parity.posix(fake_home), "PATH": path})
        return parity.run_script(script, work, env)

    def test_resolver_is_extractable_from_a_shipped_workflow(self):
        self.assertIn("engineer_run() {", self.resolver())

    @needs_shell
    def test_falls_back_to_installed_launcher_when_project_local_copy_is_absent(self):
        tmp = self.temp("engineer-3668-")
        parity.write_launcher_stub(tmp / "bin", "installed")
        (tmp / "runtime-no-local").mkdir()
        result = self.run_resolver(tmp / "runtime-no-local", tmp / "bin")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertRegex(result.stdout.replace("\\", "/"), r"(?m)^ENGINEER_RUN=.+/bin/engineer_run$")
        self.assertIn("installed:query state.json", result.stdout)

    @needs_shell
    def test_preserves_runtime_dir_local_launcher_preference_over_path(self):
        tmp = self.temp("engineer-3668-")
        parity.write_launcher_stub(tmp / "bin", "path-installed")
        parity.write_runtime_stub(tmp / "runtime", "runtime", kind="")
        result = self.run_resolver(tmp / "runtime", tmp / "bin")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertRegex(result.stdout.replace("\\", "/"), r"(?m)^ENGINEER_RUN=.+/runtime/engineer/bin/engineer_run$")
        self.assertIn("runtime:query state.json", result.stdout)
        self.assertNotIn("path-installed:query state.json", result.stdout)


class RepoLocalClaudeInstall(FixtureCase):
    """Upstream bug-444: a project-local `.claude` install outranks the config home."""

    def test_a_repo_local_claude_arm_precedes_the_config_home_arm(self):
        candidates = parity.select_candidates(SNIPPET)
        local = parity.candidate_index(candidates, "$_engineer_root/.claude/engineer/bin/")
        home = parity.candidate_index(candidates, "${CLAUDE_CONFIG_DIR:-$HOME/.claude}")
        self.assertNotEqual(-1, local, "snippet must contain the repo-local .claude check")
        self.assertNotEqual(-1, home, "Claude arm must honor CLAUDE_CONFIG_DIR with $HOME/.claude as the fallback")
        self.assertLess(local, home, "local overrides global")

    def fixture(self, with_home):
        root, home = self.temp("engineer-444-root-"), self.temp("engineer-444-home-")
        parity.write_runtime_stub(root, "LOCAL_WINS" if with_home else "LOCAL_CLAUDE_STUB", kind=".claude")
        if with_home:
            parity.write_runtime_stub(home, "HOME_WINS", kind=".claude")
        return root, home

    @needs_shell
    def test_b_resolves_the_repo_local_claude_stub_when_it_is_the_only_location(self):
        root, home = self.fixture(with_home=False)
        result = self.launch('printf "ENGINEER_RUN=%s\\n" "$ENGINEER_RUN"\nengineer_run ping test', home=home, work=root,
                             exports={"RUNTIME_DIR": parity.posix(root)})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(".claude/engineer/bin/engineer_run", result.stdout.replace("\\", "/"))
        self.assertIn("LOCAL_CLAUDE_STUB:ping test", result.stdout)

    @needs_shell
    def test_c_repo_local_claude_install_wins_over_the_home_install(self):
        root, home = self.fixture(with_home=True)
        result = self.launch("engineer_run check", home=home, work=root, exports={"RUNTIME_DIR": parity.posix(root)})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("LOCAL_WINS:check", result.stdout)
        self.assertNotIn("HOME_WINS", result.stdout)

class ModuleUnitsExtra(FixtureCase):
    def test_extract_resolver_snippet_returns_the_preamble_span(self):
        text = "```bash\nx=1\n" + "\n".join(PREAMBLE) + "\nengineer_run query\n```\n"
        self.assertEqual("\n".join(PREAMBLE), parity.extract_resolver_snippet(text))
        with self.assertRaises(ValueError):
            parity.extract_resolver_snippet("```bash\necho hi\n```\n")
        with self.assertRaises(ValueError):
            parity.extract_resolver_snippet("```bash\n_engineer_identity_ok() {\n}\n```\n")

    def test_env_file_path_line(self):
        self.assertEqual('export PATH="a:$PATH"', parity.env_file_path_line('x\nexport PATH="a:$PATH"\n'))
        self.assertEqual("", parity.env_file_path_line("nothing"))

    @needs_shell
    def test_write_launcher_stub_identity_modes(self):
        base = self.temp("units-")
        stub = parity.write_launcher_stub(base, "M")
        proved = parity.run_launcher_executable(stub, ["query", "runtime-identity", "--pick", "packageName", "--raw"], dict(os.environ))
        self.assertEqual(parity.EXPECTED_IDENTITY, proved.stdout.strip())
        foreign = parity.write_launcher_stub(base / "f", "F", identity=False)
        refused = parity.run_launcher_executable(foreign, ["query", "runtime-identity"], dict(os.environ))
        self.assertEqual("F:query runtime-identity", refused.stdout.strip())


if __name__ == "__main__":
    unittest.main()
