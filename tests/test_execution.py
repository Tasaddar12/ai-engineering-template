"""Behavioral command-policy, process and managed-worktree regression tests."""

from __future__ import annotations

import copy
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from ai_engineering.constraints import ConstraintPolicy
from ai_engineering.errors import FrameworkError, PolicyError
from ai_engineering.git import Git
from ai_engineering.io import read_yaml, write_yaml
from ai_engineering.runner import CommandRunner
from ai_engineering.state import StateStore, reconcile


@pytest.fixture
def config() -> dict[str, Any]:
    root = Path(__file__).parents[1]
    value = read_yaml(root / "src/ai_engineering/templates/project/constraints.yaml")
    value = copy.deepcopy(value)
    value["commands"]["rules"] += [
        {"argv_prefix": ["python", "-c"], "effect": "allow"},
        {"argv_prefix": ["git", "init"], "effect": "allow"},
        {"argv_prefix": ["git", "config"], "effect": "allow"},
        {"argv_prefix": ["git", "update-index"], "effect": "allow"},
        {"argv_prefix": ["git", "merge"], "effect": "allow", "action": "merge"},
        {"argv_prefix": ["not-a-real-tool-994403"], "effect": "allow"},
    ]
    return value


@pytest.mark.parametrize(
    "argv",
    [
        ["git", "push", "origin", "main", "--force"],
        ["git", "push", "--force-with-lease", "origin", "main"],
        ["git", "push", "origin", "+HEAD:main"],
        ["git", "push", "origin", ":main"],
        ["git", "push", "origin", "-vf", "main"],
        ["git", "push", "--mirror"],
        ["git", "push", "--forc", "origin", "HEAD"],
        ["git", "-C", "../elsewhere", "push"],
        ["git", "-c", "alias.safe=!bad", "safe"],
        ["git", "reset", "HEAD", "--hard"],
        ["git", "diff", "--output=../stolen"],
        ["git", "diff", "--out=../stolen"],
        ["git", "diff", "--ext-diff"],
        ["git", "branch", "-D", "main"],
        ["git", "branch", "-vD", "main"],
        ["git", "worktree", "remove", "--force", "tree"],
        ["git", "worktree", "remove", "-ff", "tree"],
        ["cmd", "/c", "echo bad"],
        ["pwsh", "-Command", "Write-Output bad"],
        ["helper.cmd"],
        ["/tmp/git", "status"],
    ],
)
def test_forbidden_cannot_be_overridden(config: dict[str, Any], argv: list[str]) -> None:
    policy = ConstraintPolicy(config, grants=["push", "destructive", "commit"])
    with pytest.raises(PolicyError):
        policy.check_command(argv, "implementation")


def test_approval_role_default_and_explicit_action(config: dict[str, Any]) -> None:
    policy = ConstraintPolicy(config)
    policy.check_command(["git", "status"], "critical_review")
    policy.check_command([sys.executable, "-m", "pytest"], "implementation")
    for argv, role, action in [
        (["git", "push", "origin", "HEAD"], "orchestrator", None),
        (["python", "-c", "pass"], "critical_review", None),
        (["git", "status"], "orchestrator", "deployment"),
        (["unlisted"], "orchestrator", None),
        (["git", "worktree", "remove", "tree"], "implementation", None),
    ]:
        with pytest.raises(PolicyError):
            policy.check_command(argv, role, action)
    ConstraintPolicy(config, ["push"]).check_command(
        ["git", "push", "origin", "HEAD"], "orchestrator"
    )
    config["commands"]["rules"].append({"argv_prefix": ["git", "status"], "effect": "forbid"})
    with pytest.raises(PolicyError):
        ConstraintPolicy(config, ["push"]).check_command(["git", "status"], "orchestrator")
    config["roles"] = {"research": {"run_commands": False}}
    with pytest.raises(PolicyError):
        ConstraintPolicy(config).check_command(["git", "status"], "research")


def test_scope_protected_and_secret_paths(tmp_path: Path, config: dict[str, Any]) -> None:
    policy = ConstraintPolicy(config)
    policy.root = tmp_path
    policy.check_paths(["src/auth/service.py", "tests/test_auth.py"], ["src/auth", "tests"])
    for value in [
        "src/authentication/service.py",
        "../src/auth.py",
        str(tmp_path / "abs.py"),
        "src/auth/.env",
        "src/auth/private.key",
        "src/auth/key.pem",
        "src/auth/.git/config",
    ]:
        with pytest.raises(PolicyError):
            policy.check_paths([value], ["src/auth"])
    for value in [".git/config", ".ai/STATE.yaml", ".ai/agents/review.yaml"]:
        with pytest.raises(PolicyError):
            policy.check_paths([value], ["."])


def test_runner_statuses_evidence_and_python_resolution(
    tmp_path: Path, config: dict[str, Any]
) -> None:
    runner = CommandRunner(tmp_path, config)
    result = runner.run(
        ["python", "-c", "import sys; print(sys.executable); print('oops', file=sys.stderr)"]
    )
    assert result.ok and result.status == "success" and result.returncode == 0
    assert Path(result.stdout.strip()) == Path(sys.executable)
    assert result.stderr.strip() == "oops"
    assert result.started_at <= result.finished_at
    expected = runner.run(["python", "-c", "raise SystemExit(3)"], expected_exit_codes=(0, 3))
    assert expected.status == "expected_failure" and expected.ok
    failed = runner.run(["python", "-c", "raise SystemExit(3)"])
    assert failed.status == "failed" and not failed.ok
    error = runner.run(["not-a-real-tool-994403"])
    assert error.status == "error" and error.returncode is None
    evidence = list((tmp_path / ".ai/local/commands").glob("*.yaml"))
    assert len(evidence) == 4
    assert {read_yaml(path)["status"] for path in evidence} == {
        "success",
        "expected_failure",
        "failed",
        "error",
    }


def test_runner_redacts_and_bounds_all_evidence(
    tmp_path: Path, config: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "unit-secret-" * 30
    monkeypatch.setenv("GH_TOKEN", secret)
    config["execution"]["max_output_chars"] = 256
    runner = CommandRunner(tmp_path, config)
    result = runner.run(
        ["python", "-c", "import os; print(os.environ['GH_TOKEN']); print('x'*1000000)"]
    )
    assert result.ok and len(result.stdout) <= 256 and secret not in result.stdout
    assert "[REDACTED]" in result.stdout
    runner.run(["python", "-c", f"print({secret!r})"])
    assert secret not in "".join(path.read_text() for path in (tmp_path / ".ai").rglob("*.yaml"))


def test_dry_run_no_side_effects_and_denied_evidence(
    tmp_path: Path, config: dict[str, Any]
) -> None:
    runner = CommandRunner(tmp_path, config, dry_run=True)
    result = runner.run(["python", "-c", "from pathlib import Path; Path('bad').write_text('bad')"])
    assert result.status == "dry_run" and not result.ok and not list(tmp_path.iterdir())
    with pytest.raises(PolicyError):
        runner.run(["git", "push", "origin", "HEAD"])
    assert not list(tmp_path.iterdir())
    runner = CommandRunner(tmp_path, config)
    with pytest.raises(PolicyError):
        runner.run(["git", "push", "origin", "HEAD"])
    evidence = next((tmp_path / ".ai/local/commands").glob("*.yaml"))
    assert read_yaml(evidence)["status"] == "denied"
    with pytest.raises(PolicyError):
        runner.run("git status")  # type: ignore[arg-type]
    with pytest.raises(PolicyError):
        runner.run(["git", "status"], cwd=tmp_path.parent)


def test_linked_cwd_is_refused(tmp_path: Path, config: dict[str, Any]) -> None:
    target = tmp_path / "target"
    target.mkdir()
    linked = tmp_path / "linked"
    try:
        linked.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Host cannot create symbolic links")
    with pytest.raises(PolicyError):
        CommandRunner(tmp_path, config).run(["git", "status"], cwd=linked)


def test_timeout_kills_ordinary_child_tree(tmp_path: Path, config: dict[str, Any]) -> None:
    runner = CommandRunner(tmp_path, config)
    child = (
        "import time; from pathlib import Path; time.sleep(2); Path('escaped').write_text('bad')"
    )
    parent = f"import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',{child!r}]); print('started', flush=True); time.sleep(30)"
    started = time.monotonic()
    result = runner.run(["python", "-c", parent], timeout=0.3)
    assert result.status == "timeout" and not result.ok
    assert time.monotonic() - started < 8
    time.sleep(2.1)
    assert not (tmp_path / "escaped").exists()


def test_input_does_not_deadlock(tmp_path: Path, config: dict[str, Any]) -> None:
    runner = CommandRunner(tmp_path, config)
    assert (
        runner.run(
            ["python", "-c", "import sys; print(sys.stdin.read())"], input_text="hello"
        ).stdout.strip()
        == "hello"
    )
    result = runner.run(
        ["python", "-c", "import time; time.sleep(30)"], input_text="x" * 1_000_000, timeout=0.2
    )
    assert result.status == "timeout"


def test_timeout_after_parent_exits_still_stops_children(
    tmp_path: Path, config: dict[str, Any]
) -> None:
    child = "import time; from pathlib import Path; time.sleep(2); Path('orphan').write_text('bad')"
    parent = f"import subprocess,sys; subprocess.Popen([sys.executable,'-c',{child!r}])"
    result = CommandRunner(tmp_path, config).run(["python", "-c", parent], timeout=0.3)
    assert result.status == "timeout"
    time.sleep(2.1)
    assert not (tmp_path / "orphan").exists()


@pytest.fixture
def repo(tmp_path: Path, config: dict[str, Any]) -> tuple[Path, CommandRunner, Git]:
    root = tmp_path / "repo"
    root.mkdir()
    runner = CommandRunner(root, config, grants=["merge"])
    for argv in (
        ["git", "init", "--initial-branch=main"],
        ["git", "config", "user.name", "Test"],
        ["git", "config", "user.email", "test@example.invalid"],
    ):
        result = runner.run(argv)
        assert result.ok, result.stderr
    (root / ".gitignore").write_text(".worktrees/\n.ai/local/\nignored.bin\n", encoding="utf-8")
    (root / "base.txt").write_text("base\n", encoding="utf-8")
    assert runner.run(["git", "add", "--all"]).ok
    assert runner.run(["git", "commit", "-m", "Initial"], action="commit").ok
    return root, runner, Git(root, runner)


def test_worktree_create_commit_diff_merge_cleanup(repo: tuple[Path, CommandRunner, Git]) -> None:
    root, runner, git = repo
    initial = git.head()
    tree = git.create_worktree("feature-a", "codex/feature-a")
    assert tree == root / ".worktrees/feature-a"
    assert git.head(tree) == initial and git.branch(tree) == "codex/feature-a"
    (tree / "new file.py").write_text("value = 1\n", encoding="utf-8")
    assert git.changed_files(tree, initial) == ["new file.py"]
    head = git.commit(tree, "Implement A")
    assert head != initial and "value = 1" in git.diff(tree, initial)
    assert not git.status(tree) and not git.is_ancestor(head)
    assert not git.cleanup(tree)
    assert runner.run(["git", "merge", "--ff-only", "codex/feature-a"], action="merge").ok
    assert git.is_ancestor(head)
    assert not git.cleanup(tree, active=True)
    assert Git(root, runner).cleanup(tree)
    assert not tree.exists() and (root / "new file.py").exists()
    assert len(git.list_worktrees()) == 1
    assert runner.run(["git", "show-ref", "--verify", "refs/heads/codex/feature-a"]).ok
    receipt = read_yaml(root / ".ai/local/worktrees/feature-a.yaml")
    assert receipt["status"] == "removed" and receipt["merge_confirmed"]


def test_cleanup_retains_dirty_ignored_locked_active_and_unknown(
    repo: tuple[Path, CommandRunner, Git],
) -> None:
    root, runner, git = repo
    tree = git.create_worktree("feature-b", "codex/feature-b")
    (tree / "ignored.bin").write_bytes(b"valuable ignored data")
    assert not git.cleanup(tree, disposition="abandoned")
    (tree / "ignored.bin").unlink()
    (tree / "base.txt").write_text("changed")
    assert not git.cleanup(tree, disposition="abandoned")
    (tree / "base.txt").write_text("base\n")
    assert runner.run(["git", "worktree", "lock", str(tree)]).ok
    assert not git.cleanup(tree)
    assert runner.run(["git", "worktree", "unlock", str(tree)]).ok
    write_yaml(
        root / ".ai/STATE.yaml",
        {"worktrees": [{"path": ".worktrees/feature-b", "status": "in-progress"}]},
    )
    assert not git.cleanup(tree)
    write_yaml(root / ".ai/STATE.yaml", {"worktrees": []})
    receipt = root / ".ai/local/worktrees/feature-b.yaml"
    saved = receipt.read_text()
    receipt.unlink()
    assert not git.cleanup(tree)
    receipt.write_text(saved)
    assert git.cleanup(tree)
    with pytest.raises(PolicyError):
        git.cleanup(root)


def test_unmerged_explicit_supersession_keeps_branch(repo: tuple[Path, CommandRunner, Git]) -> None:
    root, runner, git = repo
    tree = git.create_worktree("feature-c", "codex/feature-c")
    (tree / "base.txt").write_text("unmerged work")
    head = git.commit(tree, "Retained historical implementation")
    assert not git.cleanup(tree, disposition="old")
    assert git.cleanup(tree, disposition="superseded")
    result = runner.run(["git", "rev-parse", "refs/heads/codex/feature-c"])
    assert result.stdout.strip() == head
    receipt = read_yaml(root / ".ai/local/worktrees/feature-c.yaml")
    assert not receipt["merge_confirmed"] and receipt["disposition"] == "superseded"


def test_git_rejects_name_ref_reuse_and_protected_commit(
    repo: tuple[Path, CommandRunner, Git],
) -> None:
    _root, runner, git = repo
    for name, branch in [
        ("../escape", "codex/escape"),
        ("valid", "main"),
        ("valid", "codex/a..b"),
        ("valid", "--evil"),
    ]:
        with pytest.raises(PolicyError):
            git.create_worktree(name, branch)
    tree = git.create_worktree("feature-d", "codex/feature-d")
    with pytest.raises(FrameworkError):
        git.create_worktree("feature-d", "codex/feature-e")
    (tree / "private.pem").write_text("secret")
    before = git.head(tree)
    with pytest.raises(PolicyError):
        git.commit(tree, "Accidental secret")
    assert git.head(tree) == before
    assert runner.run(["git", "diff", "--cached", "--name-only"], cwd=tree).stdout == ""


def test_git_disables_repo_hooks_and_inherited_git_context(
    repo: tuple[Path, CommandRunner, Git], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _runner, git = repo
    monkeypatch.setenv("GIT_DIR", str(root / "wrong"))
    assert git.head()
    # A failing commit hook must not execute through this internal Git primitive.
    hook = root / ".git/hooks/pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    tree = git.create_worktree("feature-e", "codex/feature-e")
    (tree / "base.txt").write_text("updated\n")
    assert git.commit(tree, "Internal commit skips untrusted hooks")


def test_cleanup_refuses_hidden_index_changes_and_active_subject(
    repo: tuple[Path, CommandRunner, Git],
) -> None:
    root, runner, git = repo
    tree = git.create_worktree("feature-f", "codex/feature-f")
    assert runner.run(["git", "update-index", "--assume-unchanged", "base.txt"], cwd=tree).ok
    (tree / "base.txt").write_text("hidden valuable change")
    assert git.status(tree) == ""
    assert not git.cleanup(tree)
    assert (tree / "base.txt").read_text() == "hidden valuable change"
    assert runner.run(["git", "update-index", "--no-assume-unchanged", "base.txt"], cwd=tree).ok
    (tree / "base.txt").write_text("base\n")
    write_yaml(
        root / ".ai/STATE.yaml",
        {
            "active_features": ["FEATURE-123"],
            "worktrees": [{"path": str(tree), "status": "completed", "subject": "FEATURE-123"}],
        },
    )
    assert not git.cleanup(tree)


def test_real_git_reconciliation_preserves_intent(repo: tuple[Path, CommandRunner, Git]) -> None:
    root, _runner, git = repo
    tree = git.create_worktree("feature-g", "codex/feature-g")
    state = StateStore(root)
    state.save(
        {
            "project": {"name": "test"},
            "current_focus": {},
            "worktrees": [
                {
                    "path": str(tree),
                    "branch": "codex/wrong",
                    "head": "0" * 40,
                    "subject": "FEATURE-123",
                }
            ],
        }
    )
    before = state.path.read_bytes()
    result = reconcile(root, git)
    assert any("branch differs" in issue for issue in result["issues"])
    assert any("head differs" in issue for issue in result["issues"])
    assert "FEATURE-123" in result["merged"]
    assert state.path.read_bytes() == before
    reconcile(root, git, apply=True)
    assert state.load()["worktrees"][0]["branch"] == "codex/wrong"


def test_migration_preservation_allows_edits_but_blocks_deletion(
    repo: tuple[Path, CommandRunner, Git],
) -> None:
    _root, runner, git = repo
    tree = git.create_worktree("feature-h", "codex/feature-h")
    migrations = tree / "migrations"
    migrations.mkdir()
    migration = migrations / "001_initial.py"
    migration.write_text("original = True\n")
    git.commit(tree, "Add migration")
    migration.write_text("original = False\n")
    before = git.commit(tree, "Edit migration")
    migration.unlink()
    with pytest.raises(PolicyError, match="preserved"):
        git.commit(tree, "Accidentally delete migration")
    assert git.head(tree) == before
    assert runner.run(["git", "diff", "--cached", "--name-only"], cwd=tree).stdout == ""


def test_cleanup_resumes_only_after_fresh_observations(
    repo: tuple[Path, CommandRunner, Git],
) -> None:
    root, runner, git = repo
    tree = git.create_worktree("feature-i", "codex/feature-i")
    receipt = root / ".ai/local/worktrees/feature-i.yaml"
    # An interrupted attempt has an intent but the registered tree still exists.
    write_yaml(receipt, {**read_yaml(receipt), "status": "removing"})
    (tree / "base.txt").write_text("work since the interrupted attempt")
    assert not Git(root, runner).cleanup(tree)
    (tree / "base.txt").write_text("base\n")
    assert Git(root, runner).cleanup(tree)
    tree = git.create_worktree("feature-j", "codex/feature-j")
    receipt = root / ".ai/local/worktrees/feature-j.yaml"
    write_yaml(receipt, {**read_yaml(receipt), "status": "removing"})
    assert runner.run(["git", "worktree", "remove", str(tree)]).ok
    assert Git(root, runner).cleanup(tree)
    assert read_yaml(receipt)["reconciled_absence"]
