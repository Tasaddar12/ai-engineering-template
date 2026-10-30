"""Declared per-plan dispatch persistence through the real CLI."""
import json
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class DispatchContracts(RuntimeCase):
    def test_normal_plan_dispatch_refreshes_record_and_inspection_is_read_only(self):
        path = self.root/".planning/dispatch-isolation.json"
        for plan in ("01-01", "01-02"):
            self.assertEqual("orchestrator-worktree", self.cli("dispatch-isolation", "--raw", "--phase", "1", "--plan", plan, raw=True))
            data = json.loads(path.read_text())
            self.assertEqual(plan, data["plan_id"])
            self.assertEqual(plan, data["plan"])
            self.assertEqual("1", data["phase"])
            self.assertEqual(self.git("rev-parse", "HEAD"), data["revision"])
            self.assertEqual("orchestrator-worktree", data["mode"])
        before = path.read_bytes()
        self.cli("inspect-dispatch-isolation", "--phase", "1", "--plan", "01-03", "--force-isolation", "orchestrator-worktree")
        self.assertEqual(before, path.read_bytes())
        self.cli("dispatch-isolation")
        self.assertEqual(before, path.read_bytes())
        self.cli("dispatch-isolation", "--phase", "2", "--plan", "01-03", status=2, raw=True)
        self.assertEqual(before, path.read_bytes())

    def test_inspection_never_creates_the_record(self):
        self.cli("inspect-dispatch-isolation", "--phase", "1", "--plan", "01-01")
        self.assertFalse((self.root/".planning/dispatch-isolation.json").exists())
