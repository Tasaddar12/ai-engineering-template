"""Independent, read-only R1 reproduction for the exact TASK-013 candidate."""
from __future__ import annotations

import copy
import dataclasses
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / ".worktrees/TASK-013-a1"
BASE = "24f7c768f996c4abf66ed37a5ea1e89b459dd74b"
HEAD = "51a94cd050ad6c7cb525c6d26c9c7e38e0943c13"
CANDIDATE = ROOT / ".ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-013-a1-51a94cd050ad.json"
sys.dont_write_bytecode = True
sys.path.insert(0, str(TREE / "src"))
import contracts
import domain_values
import plan_graph
from contracts import ContractRegistry, structural_task_digest
from domain_values import DomainException, ErrorCategory, RecordRef, TaskStatus, freeze_json
from plan_graph import AcceptedDependency, build_dependency_graph


def git(*args: str, cwd: Path = TREE) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True).stdout


def read(path: Path):
    return json.loads(path.read_bytes())


def verify_identity() -> None:
    c = read(CANDIDATE)
    assert git("rev-parse", "HEAD").decode().strip() == c["head_oid"] == HEAD
    assert git("rev-parse", "HEAD", cwd=ROOT).decode().strip() == c["base_oid"] == BASE
    assert not git("status", "--porcelain=v1", "--untracked-files=all")
    git("merge-base", "--is-ancestor", BASE, HEAD)
    digest = hashlib.sha256(git("diff", "--binary", BASE, HEAD)).hexdigest()
    assert digest == c["diff_sha256"]
    paths = git("diff", "--name-only", BASE, HEAD).decode().splitlines()
    assert paths == [
        ".ai/plans/current/PLAN-001/evidence/implementation/TASK-013.md",
        "src/plan_graph.py", "tests/unit/planning_dag/test_plan_graph.py",
    ]
    git("diff", "--check", BASE, HEAD)
    for ref in c["context_refs"]:
        data = git("show", f"{HEAD}:{ref['path']}")
        assert hashlib.sha256(data).hexdigest() == ref["sha256"], ref["path"]
        assert (TREE / ref["path"]).read_bytes().replace(b"\r\n", b"\n") == data.replace(b"\r\n", b"\n")
        print("context hash PASS", ref["path"], ref["sha256"])
    for ref in c["validation_refs"]:
        assert hashlib.sha256((ROOT / ref["path"]).read_bytes()).hexdigest() == ref["sha256"]
        print("validation hash PASS", ref["path"], ref["sha256"])
    policy_names = ["policy.json", "agent-models.json"]
    policy_bytes = b"".join((ROOT / ".ai/project" / name).read_bytes() for name in policy_names)
    assert hashlib.sha256(policy_bytes).hexdigest() == c["policy_model_digest"]
    for name in policy_names:
        rel = f".ai/project/{name}"
        assert git("show", f"{BASE}:{rel}") == git("show", f"{HEAD}:{rel}")
        assert read(ROOT / rel) == read(TREE / rel)
    material = {key: value for key, value in c.items() if key != "fingerprint"}
    actual = hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    assert actual == c["fingerprint"] == "9c7b3139798b22e6f1bb30a9d5e5bf9230db0c75a348cdedbc30f472201bd9ae"
    registry.validate(c)
    task = read(TREE / ".ai/plans/current/PLAN-001/tasks/current/TASK-013.json")
    assert task["depends_on"] == ["TASK-001", "TASK-004"]
    for task_id in task["depends_on"]:
        assert read(TREE / f".ai/plans/current/PLAN-001/tasks/current/{task_id}.json")["status"] == "accepted"
    for module in (contracts, domain_values, plan_graph):
        assert Path(module.__file__).resolve().parent == (TREE / "src").resolve()
        print("exact-source import", module.__name__, module.__file__)
    print("identity PASS", BASE, HEAD, "clean candidate; scope", paths)
    print("diff hash PASS", digest)
    print("policy/model hash PASS", c["policy_model_digest"])
    print("fingerprint PASS", actual)
    print("ROOT initial status (coordinator candidate/evidence files may be untracked):")
    print(git("status", "--porcelain=v1", cwd=ROOT).decode())


registry = ContractRegistry(TREE / "schemas/v1")
bundle = TREE / ".ai/plans/current/PLAN-001"
task_template = read(bundle / "tasks/current/TASK-013.json")
plan_template = read(bundle / "plan.json")


def make(edges, *, statuses=None, coverage=None, plan_id="PLAN-700", criteria=("AC-01",), graph_status="proposed"):
    tasks = []
    for key, dependencies in edges.items():
        item = copy.deepcopy(task_template)
        item.update(id=key, plan_id=plan_id, depends_on=list(dependencies), status=(statuses or {}).get(key, "backlog"), archived=False, plan_acceptance_ids=list((coverage or {}).get(key, criteria)), superseded_by=[])
        tasks.append(item)
    plan = copy.deepcopy(plan_template)
    plan.update(id=plan_id, status="replanning" if graph_status == "proposed" else "running", task_ids=list(edges), isolation_review_ref=None)
    plan["acceptance_criteria"] = [{"id": key, "description": "Independent criterion", "verification": "Independent behavior"} for key in criteria]
    graph = {"schema_version": "1.0", "kind": "task-graph", "id": f"{plan_id}-r2", "plan_id": plan_id, "revision": 2, "status": graph_status, "nodes": [{"task_id": key, "depends_on": list(value)} for key, value in edges.items()], "task_set_sha256": structural_task_digest(tasks), "review_ref": None}
    return plan, graph, tasks


def build(records):
    return build_dependency_graph(*records, registry=registry)


def ref(task_id, plan_id="PLAN-700"):
    return RecordRef(kind="task", plan_id=plan_id, local_id=task_id)


class IndependentGraphChecks(unittest.TestCase):
    def rejects(self, records, fragment=None):
        with self.assertRaises(DomainException) as caught:
            build(records)
        self.assertEqual(caught.exception.category, ErrorCategory.VALIDATION_FAILED)
        if fragment:
            self.assertIn(fragment, str(caught.exception))
        return caught.exception

    def test_01_live_approved_snapshot_and_isolation_digest(self):
        plan, graph = read(bundle / "plan.json"), read(bundle / "graph.json")
        tasks = [read(path) for bucket in ("current", "completed") for path in (bundle / "tasks" / bucket).glob("*.json")]
        actual = build((plan, graph, tasks))
        isolation = read(bundle / "reviews/r4-isolation-review.json")
        self.assertEqual(isolation["verdict"], "pass")
        self.assertEqual(graph["revision"], isolation["graph_revision"])
        self.assertEqual(structural_task_digest(tasks), isolation["task_set_sha256"])
        self.assertEqual(len(actual.nodes), 39)
        self.assertEqual(len(actual.topological_order), 39)
        self.assertEqual(len(actual.acceptance_coverage), 9)
        print("current r4 PASS: 39 nodes/order, 9 covered criteria, digest", graph["task_set_sha256"])

    def test_02_namespace_and_qualified_lookup(self):
        a = build(make({"TASK-001": []}))
        b = build(make({"TASK-001": []}, plan_id="PLAN-701"))
        self.assertNotEqual(a.nodes[0].task, b.nodes[0].task)
        self.assertEqual(a.node(ref("TASK-001")), a.nodes[0])
        for value in ("TASK-001", ref("TASK-999"), ref("TASK-001", "PLAN-701"), RecordRef(kind="review", plan_id="PLAN-700", local_id="TASK-001")):
            with self.subTest(value=value), self.assertRaises(DomainException):
                a.node(value)
        for field in ("graph", "task"):
            p, g, ts = make({"TASK-001": []})
            (g if field == "graph" else ts[0])["plan_id"] = "PLAN-701"
            self.rejects((p, g, ts))

    def test_03_all_small_graphs_against_permutation_oracle(self):
        ids = tuple(f"TASK-{i:03}" for i in range(1, 4))
        possible = [(a, b) for a in ids for b in ids if a != b]
        cyclic = acyclic = 0
        for mask in range(1 << len(possible)):
            edges = {key: [] for key in ids}
            for index, (node, dep) in enumerate(possible):
                if mask & (1 << index):
                    edges[node].append(dep)
            valid = [order for order in itertools.permutations(ids) if all(order.index(dep) < order.index(node) for node, ds in edges.items() for dep in ds)]
            if valid:
                self.assertEqual(tuple(str(item.local_id) for item in build(make(edges)).topological_order), min(valid))
                acyclic += 1
            else:
                self.rejects(make(edges), "cycle")
                cyclic += 1
        print("all 64 directed 3-node graphs PASS:", acyclic, "DAGs and", cyclic, "cyclic graphs; exhaustive permutation oracle")

    def test_04_shuffles_and_frontier_powersets(self):
        rng = random.Random(713)
        ids = tuple(f"TASK-{i:03}" for i in range(1, 6))
        for iteration in range(32):
            hidden = list(ids)
            rng.shuffle(hidden)
            edges = {key: [dep for dep in hidden[:i] if rng.randrange(2)] for i, key in enumerate(hidden)}
            original = make(edges)
            expected = build(original)
            shuffled = copy.deepcopy(original)
            rng.shuffle(shuffled[0]["task_ids"])
            rng.shuffle(shuffled[1]["nodes"])
            rng.shuffle(shuffled[2])
            for node in shuffled[1]["nodes"]:
                rng.shuffle(node["depends_on"])
            self.assertEqual(expected, build(shuffled))
            for task in shuffled[2]:
                rng.shuffle(task["depends_on"])
            # The accepted structural digest retains authored list order; rebuild
            # that attestation while checking semantic graph/order independence.
            shuffled[1]["task_set_sha256"] = structural_task_digest(shuffled[2])
            reordered = build(shuffled)
            self.assertEqual(expected.nodes, reordered.nodes)
            self.assertEqual(expected.topological_order, reordered.topological_order)
            self.assertEqual(expected.acceptance_coverage, reordered.acceptance_coverage)
            for mask in range(32):
                accepted = {key for i, key in enumerate(ids) if mask & (1 << i)}
                facts = [AcceptedDependency(ref(key), f"{i + 1:040x}") for i, key in enumerate(ids) if key in accepted]
                rng.shuffle(facts)
                ready = expected.ready_frontier(iter(facts))
                want = sorted(key for key, deps in edges.items() if key not in accepted and set(deps) <= accepted)
                self.assertEqual([str(item.task.local_id) for item in ready], want)
                for item in ready:
                    self.assertEqual(tuple(str(fact.task.local_id) for fact in item.dependency_facts), tuple(sorted(edges[str(item.task.local_id)])))
                    self.assertTrue(all(fact in facts for fact in item.dependency_facts))
        print("32 randomized 5-node DAG shuffles + 1,024 accepted-fact subsets PASS")

    def test_05_membership_edge_schema_and_digest_rejections(self):
        base = make({"TASK-001": [], "TASK-002": ["TASK-001"]})
        changes = [
            ("missing task", lambda p, g, ts: ts.pop()),
            ("duplicate task", lambda p, g, ts: ts.append(copy.deepcopy(ts[0]))),
            ("duplicate plan ID", lambda p, g, ts: p["task_ids"].append("TASK-001")),
            ("unknown node", lambda p, g, ts: g["nodes"].append({"task_id": "TASK-999", "depends_on": []})),
            ("duplicate node", lambda p, g, ts: g["nodes"].append(copy.deepcopy(g["nodes"][0]))),
            ("missing node", lambda p, g, ts: g["nodes"].pop()),
            ("self edge", lambda p, g, ts: g["nodes"][0]["depends_on"].append("TASK-001")),
            ("unknown edge", lambda p, g, ts: ts[0]["depends_on"].append("TASK-999")),
            ("inconsistent edge", lambda p, g, ts: g["nodes"][1]["depends_on"].clear()),
            ("duplicate task edge", lambda p, g, ts: ts[1]["depends_on"].append("TASK-001")),
            ("duplicate graph edge", lambda p, g, ts: g["nodes"][1]["depends_on"].append("TASK-001")),
            ("cross-plan edge", lambda p, g, ts: ts[1]["depends_on"].append("task:PLAN-701:TASK-001")),
            ("stale digest", lambda p, g, ts: ts[0].update(objective="Changed owned behavior")),
            ("unknown field", lambda p, g, ts: ts[0].update(extra=True)),
        ]
        for label, mutate in changes:
            with self.subTest(label=label):
                records = copy.deepcopy(base)
                mutate(*records)
                error = self.rejects(records)
                with self.assertRaises(TypeError):
                    error.error.details["tamper"] = True
        print("14 schema/membership/edge/digest negative cases PASS with immutable structured errors")

    def test_06_exact_acceptance_coverage(self):
        records = make({"TASK-001": [], "TASK-002": [], "TASK-003": []}, criteria=("AC-01", "AC-02"), coverage={"TASK-001": ["AC-01"], "TASK-002": ["AC-02"], "TASK-003": ["AC-02", "AC-01"]})
        graph = build(records)
        self.assertEqual({str(item.acceptance_id): [str(task.local_id) for task in item.tasks] for item in graph.acceptance_coverage}, {"AC-01": ["TASK-001", "TASK-003"], "AC-02": ["TASK-002", "TASK-003"]})
        for mode in ("missing", "unknown", "duplicate mapping", "duplicate criterion"):
            p, g, ts = copy.deepcopy(records)
            if mode == "missing":
                for task in ts:
                    task["plan_acceptance_ids"] = ["AC-01"]
            elif mode == "unknown":
                ts[0]["plan_acceptance_ids"].append("AC-99")
            elif mode == "duplicate mapping":
                ts[0]["plan_acceptance_ids"].append("AC-01")
            else:
                p["acceptance_criteria"].append(copy.deepcopy(p["acceptance_criteria"][0]))
            self.rejects((p, g, ts))

    def test_07_status_is_not_integration_evidence(self):
        checked = 0
        for status in TaskStatus:
            if status == TaskStatus.SUPERSEDED:
                continue
            records = make({"TASK-001": [], "TASK-002": ["TASK-001"]}, statuses={"TASK-001": str(status)})
            graph = build(records)
            self.assertNotIn(ref("TASK-002"), [item.task for item in graph.ready_frontier()])
            self.assertEqual([item.task for item in graph.ready_frontier()], [ref("TASK-001")] if status in (TaskStatus.BACKLOG, TaskStatus.READY) else [])
            fact = AcceptedDependency(ref("TASK-001"), "a" * 64)
            self.assertEqual(graph.ready_frontier([fact])[0].dependency_facts, (fact,))
            checked += 1
        print("all", checked, "non-superseded task statuses PASS; accepted/completed alone never unlock dependents")

    def test_08_integration_fact_boundary(self):
        graph = build(make({"TASK-001": []}))
        known = AcceptedDependency(ref("TASK-001"), "1" * 40)
        for values in ([known, known], [AcceptedDependency(ref("TASK-999"), "a" * 40)], [AcceptedDependency(ref("TASK-001", "PLAN-701"), "a" * 40)], [None], "TASK-001", {}, None):
            with self.subTest(values=values), self.assertRaises(DomainException):
                graph.ready_frontier(values)
        for oid in ("a" * 39, "a" * 41, "A" * 40, "a" * 63, "z" * 64, "a" * 40 + "\n", None):
            with self.subTest(oid=oid), self.assertRaises(ValueError):
                AcceptedDependency(ref("TASK-001"), oid)

    def test_09_immutable_input_output_and_no_runtime_io(self):
        records = make({"TASK-001": [], "TASK-002": ["TASK-001"]})
        original = copy.deepcopy(records)
        frozen = [freeze_json(records[0]), freeze_json(records[1]), [freeze_json(task) for task in records[2]]]
        graph = build(frozen)
        self.assertEqual(graph, build(records))
        self.assertEqual(records, original)
        records[2][0]["plan_acceptance_ids"].clear()
        records[1]["nodes"].clear()
        self.assertEqual(len(graph.nodes), 2)
        self.assertEqual(len(graph.acceptance_coverage[0].tasks), 2)
        for value, field in ((graph, "nodes"), (graph.nodes[0], "status"), (graph.acceptance_coverage[0], "tasks"), (AcceptedDependency(ref("TASK-001"), "a" * 40), "integration_commit"), (graph.ready_frontier()[0], "task")):
            with self.assertRaises((dataclasses.FrozenInstanceError, AttributeError)):
                setattr(value, field, None)
        from unittest.mock import patch
        with patch("builtins.open", side_effect=AssertionError("unexpected runtime IO")), patch("subprocess.run", side_effect=AssertionError("unexpected process")):
            self.assertEqual(graph, build(frozen))

    def test_10_proposed_replacement_graph_excludes_retained_history(self):
        # Whole live replacement graph: completed prerequisite remains, failed node is
        # superseded in retained history, and its successor owns remapped descendants.
        records = make({"TASK-001": [], "TASK-003": ["TASK-004"], "TASK-004": ["TASK-001"]}, statuses={"TASK-001": "completed"})
        graph = build(records)
        self.assertEqual([str(item.local_id) for item in graph.topological_order], ["TASK-001", "TASK-004", "TASK-003"])
        self.assertEqual(str(graph.status), "proposed")
        self.assertEqual([str(item.task.local_id) for item in graph.ready_frontier([AcceptedDependency(ref("TASK-001"), "a" * 40)])], ["TASK-004"])
        for mode in ("superseded", "archived"):
            p, g, ts = make({"TASK-001": [], "TASK-002": ["TASK-001"]})
            if mode == "archived":
                ts[1].update(status="completed", archived=True)
            else:
                ts[1].update(status="superseded", superseded_by=["TASK-004"])
            self.rejects((p, g, ts), "excluded task")
        print("proposed whole live replacement PASS; retained superseded/archived records are excluded from build input under live-graph contract")


if __name__ == "__main__":
    verify_identity()
    command = read(bundle / "commands/test.TASK-013.json")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    argv = [sys.executable, *command["argv"][1:]]
    result = subprocess.run(argv, cwd=TREE, env=env, capture_output=True, text=True, timeout=command["timeout_seconds"])
    print("Declared suite", argv, "cwd", TREE, "exit", result.returncode)
    print(result.stdout, result.stderr)
    assert result.returncode == 0 and "Ran 13 tests" in result.stderr
    run = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentGraphChecks))
    assert not git("status", "--porcelain=v1", "--untracked-files=all")
    assert git("rev-parse", "HEAD").decode().strip() == HEAD
    assert git("rev-parse", "HEAD", cwd=ROOT).decode().strip() == BASE
    print("Final exact head/root base/candidate cleanliness PASS")
    sys.exit(0 if run.wasSuccessful() and run.testsRun > 0 else 1)
