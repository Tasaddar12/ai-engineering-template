"""Offline regressions for declaration, register ownership and canonical targets."""
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import unittest
from unittest.mock import patch

try:
    from .test_engineer_runtime import RuntimeCase
    from .test_artifacts import _load
except ImportError:
    from test_engineer_runtime import RuntimeCase
    from test_artifacts import _load

security = _load("security_tracking")
phase_issues = _load("phase_issues")
text_format = _load("text")


def register(*identifiers):
    return ("<threat_model>\n"
            "| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |\n"
            "|---|---|---|---|---|---|\n" +
            "".join(f"| {identifier} | T | dependency | high | mitigate | Verify lock |\n"
                    for identifier in identifiers) + "</threat_model>\n")


class DeclarationContracts(RuntimeCase):
    def test_populated_declaration_handoff_preserves_existing_relationship_and_history(self):
        directory = Path(self.phase())
        self.plan(directory)
        self.git('remote', 'add', 'origin', 'https://github.com/acme/project.git')
        summary = directory / '01-01-SUMMARY.md'
        summary.write_text('---\nphase: "01"\nplan: "01"\nstatus: complete\n---\nDelivered\n')
        entry = {'id': 'BUG-1', 'state': 'unresolved', 'relationship': 'followup',
                 'url': 'https://github.com/acme/project/issues/2'}
        source = self.put('entries.json', json.dumps([entry]))
        snapshot = self.cli('phase.issue-declare', '1', summary.name)['snapshotDigest']
        self.cli('phase.issue-declare', '1', summary.name, '--entries-file', source, '--expect-digest', snapshot)
        self.git('add', str(summary.relative_to(self.root)))
        self.git('commit', '-m', 'actual declared summary')
        with patch.dict(os.environ, self.env), patch.object(phase_issues.issues, 'issue_get',
                return_value={'url': entry['url'], 'state': 'OPEN'}):
            packet = phase_issues.handoff(security.Args(['1']))
            self.assertTrue(packet['ready'], packet['errors'])
            self.assertEqual(entry['url'], packet['findings'][0]['url'])
        original = summary.read_bytes()
        for replacement in ([], [{**entry, 'url': entry['url'] + '0'}]):
            source.write_text(json.dumps(replacement))
            snapshot = self.cli('phase.issue-declare', '1', summary.name)['snapshotDigest']
            self.cli('phase.issue-declare', '1', summary.name, '--entries-file', source,
                     '--expect-digest', snapshot, status=1, raw=True)
            self.assertEqual(original, summary.read_bytes())
        with self.assertRaises(phase_issues.Failure) as error:
            phase_issues._refs([{'id': 'BUG-2', 'state': 'resolved', 'reason': 'Narration only'}])
        self.assertEqual('finding-resolution-unproved', error.exception.code)

    def test_windows_summary_path_uses_git_object_separators_without_weakening_equality(self):
        directory = Path(self.phase())
        self.plan(directory)
        summary = directory / "01-01-SUMMARY.md"
        summary.write_text('---\nphase: "01"\nplan: "01"\nstatus: complete\nissue_refs: []\n---\nDelivered\n')
        self.git("add", str(summary.relative_to(self.root)))
        self.git("commit", "-m", "complete summary")
        original = Path.relative_to
        def windows_relative(path, *args):
            relative = original(path, *args)
            return PureWindowsPath(relative) if path == summary else relative
        with patch.dict(os.environ, self.env), patch.object(Path, "relative_to", windows_relative):
            result = phase_issues.handoff(security.Args(["1"]))
            self.assertTrue(result["ready"], result["errors"])
            summary.write_text(summary.read_text() + "Uncommitted changes\n")
            result = phase_issues.handoff(security.Args(["1"]))
            self.assertFalse(result["ready"])
            self.assertTrue(any("must match committed" in e["reason"] for e in result["errors"]))
            summary.write_text(summary.read_text().replace("status: complete", "status: partial"))
            self.assertFalse(phase_issues.handoff(security.Args(["1"]))["ready"])

    def test_declare_round_trips_all_six_evidence_schemas(self):
        directory = Path(self.phase())
        self.git("remote", "add", "origin", "https://github.com/acme/project.git")
        for schema, fields in {
            "summary": 'plan: "01"\nstatus: complete\n', "review": "status: clean\n",
            "verification": "status: human_needed\n", "security": "status: pending\n",
            "validation": "", "uat": "status: testing\n",
        }.items():
            for entries in ([], [{"id": "BUG-1", "state": "unresolved", "relationship": "followup",
                                  "url": "https://github.com/acme/project/issues/2"}]):
                with self.subTest(schema=schema, entries=entries):
                    path = directory / ("01-01-" + schema.upper() + ".md")
                    path.write_text('---\nphase: "01"\n' + fields + "---\nActual evidence\n")
                    source = self.put("entries.json", json.dumps(entries))
                    before = self.cli("phase.issue-declare", "1", path.name)
                    result = self.cli("phase.issue-declare", "1", path.name, "--entries-file", source,
                                      "--expect-digest", before["snapshotDigest"])
                    self.assertEqual(entries, result["entries"])
                    self.assertTrue(self.cli("frontmatter.validate", path, "--schema", schema)["valid"])
                    self.assertTrue(self.cli("planning.integrity")["valid"])
                    self.assertEqual(entries, self.cli("phase.issue-declare", "1", path.name)["entries"])
                    self.assertTrue(path.read_text().endswith("Actual evidence\n"))

    def test_declaration_failures_leave_original_bytes_and_history_intact(self):
        directory = Path(self.phase())
        path = directory / "01-API-REVIEW.md"
        path.write_text('---\nphase: "01"\nstatus: clean\n---\nReview evidence\n')
        source = self.put("entries.json", "[]")
        original = path.read_bytes()
        self.cli("phase.issue-declare", "1", path.name, "--entries-file", source,
                 "--expect-digest", "stale", status=1, raw=True)
        self.assertEqual(original, path.read_bytes())
        for entries in ({}, ["BUG-1"], [{"id": ""}], [{"id": "BUG-1"}, {"id": "BUG-1"}]):
            source.write_text(json.dumps(entries))
            snapshot = self.cli("phase.issue-declare", "1", path.name)["snapshotDigest"]
            self.cli("phase.issue-declare", "1", path.name, "--entries-file", source,
                     "--expect-digest", snapshot, status=1, raw=True)
            self.assertEqual(original, path.read_bytes())

    def test_declarations_do_not_weaken_schema_or_handoff(self):
        directory = Path(self.phase())
        self.plan(directory)
        summary = directory / "01-01-SUMMARY.md"
        summary.write_text('---\nphase: "01"\nplan: "01"\nstatus: complete\n---\nDelivered\n')
        self.git("add", str(summary.relative_to(self.root)))
        self.git("commit", "-m", "complete summary")
        packet = self.cli("phase.handoff", "1")
        self.assertTrue(any(e.get("error") == "invalid-finding-declarations" for e in packet["errors"]))
        source = self.put("entries.json", "[]")
        snapshot = self.cli("phase.issue-declare", "1", summary.name)["snapshotDigest"]
        self.cli("phase.issue-declare", "1", summary.name, "--entries-file", source,
                 "--expect-digest", snapshot)
        self.git("add", str(summary.relative_to(self.root)))
        self.git("commit", "-m", "declare findings")
        self.assertTrue(self.cli("phase.handoff", "1")["ready"])
        for value in ("{}", '"invalid"', "null"):
            summary.write_text('---\nphase: "01"\nplan: "01"\nstatus: complete\nissue_refs: ' + value + '\n---\nEvidence\n')
            errors = self.cli("frontmatter.validate", summary, "--schema", "summary", status=1)["errors"]
            self.assertIn("Invalid type: issue_refs", errors)
        summary.write_text('---\nphase: "01"\nplan: "01"\nstatus: complete\nunrecognized: []\n---\nEvidence\n')
        self.assertIn("Unknown field: unrecognized", self.cli("frontmatter.validate", summary,
                      "--schema", "summary", status=1)["errors"])


class ThreatOwnershipContracts(RuntimeCase):
    def test_preflight_counts_owned_register_rows_not_aliases_or_cross_references(self):
        directory = Path(self.phase())
        first = self.plan(directory, register("T-01-01", "T-01-27") + "Historical T-01-SC; references T-01-02.\n")
        second = directory / "01-02-PLAN.md"
        second.write_text(first.read_text().replace('plan: "01"', 'plan: "02"').replace(
            register("T-01-01", "T-01-27"), register("T-01-02", "T-01-28")) +
            "Historical T-01-SC; references T-01-01.\n" +
            "```md\n" + register("T-01-01") + "```\n")
        for verb in ("init.phase-op", "init.plan-phase", "init.execute-phase"):
            with self.subTest(verb=verb):
                packet = self.cli(verb, "1")
                self.assertEqual([], packet["threat_id_duplicates"])
                self.assertEqual(0, packet["threat_id_duplicate_count"])

    def test_only_exact_phase_reserved_id_can_repeat_across_plans(self):
        directory = Path(self.phase())
        first = self.plan(directory, register("T-01-01", "T-01-SC", "T-02-SC"))
        second = directory / "01-02-PLAN.md"
        second.write_text(first.read_text().replace('plan: "01"', 'plan: "02"'))
        packet = self.cli("init.execute-phase", "1")
        self.assertEqual({"T-01-01", "T-02-SC"}, {e["id"] for e in packet["threat_id_duplicates"]})
        self.assertTrue(all(e["plans"] == ["01-01", "01-02"] for e in packet["threat_id_duplicates"]))

    def test_duplicate_owned_rows_in_one_plan_still_block_preflight(self):
        directory = Path(self.phase())
        self.plan(directory, register("T-01-SC", "T-01-SC"))
        packet = self.cli("init.execute-phase", "1")
        self.assertEqual([{"id": "T-01-SC", "plans": ["01-01", "01-01"]}], packet["threat_id_duplicates"])


class CanonicalTargetContracts(RuntimeCase):
    def rendered(self, html, heading="T-32-03", key="acme/project|shared-results|incompatible-reuse", canonical_url=None):
        origin = {"owner": "acme", "repository": "project", "hostname": "github.com"}
        with patch.dict(os.environ, self.env), patch.object(security.repository, "require_url", return_value=497), \
                patch.object(security.issues, "provider", return_value=subprocess.CompletedProcess([], 0, json.dumps({"body_html": html}), "")):
            return security.rendered_targets("https://github.com/acme/project/issues/497",
                                             [{"id": "T-03-09", "key": key, "heading": heading,
                                               "canonical_url": canonical_url}], origin)

    def test_existing_verified_native_anchor_is_preserved_with_named_alias(self):
        key = "acme/project|shared-results|incompatible-reuse"
        html = ('<a name="user-content-risk"></a><h3><a class="anchor" aria-hidden="true" href="#t-32-03">T-32-03</a></h3>'
                '<p>Canonical risk key: ' + key + '</p>')
        established = "https://github.com/acme/project/issues/497#t-32-03"
        targets, pending = self.rendered(html, canonical_url=established)
        self.assertEqual([], pending)
        self.assertEqual({key: established}, targets)
        targets, pending = self.rendered(html, canonical_url=established + "-missing")
        self.assertEqual({}, targets)
        self.assertEqual(1, len(pending))

    def test_provider_named_anchor_binds_to_following_heading_and_key(self):
        key = "acme/project|shared-results|incompatible-reuse"
        html = ('<a name="user-content-t-32-03"></a>\n<h3>T-32-03</h3>\n'
                '<p><strong>Canonical risk key:</strong> ' + key + '</p>')
        targets, pending = self.rendered(html)
        self.assertEqual([], pending)
        self.assertEqual({key: "https://github.com/acme/project/issues/497#user-content-t-32-03"}, targets)

    def test_heading_anchor_and_named_anchor_keep_existing_verified_target(self):
        key = "acme/project|shared-results|incompatible-reuse"
        html = ('<a id="user-content-risk-t02-sc" name="risk-t02-sc"></a>\n'
                '<h3><a href="#t02-sc">T02-SC</a></h3>\n'
                '<p><strong>Canonical risk key:</strong> ' + key + '</p>')
        targets, pending = self.rendered(html, heading="T02-SC", canonical_url="https://github.com/acme/project/issues/497#user-content-risk-t02-sc")
        self.assertEqual([], pending)
        self.assertEqual("https://github.com/acme/project/issues/497#user-content-risk-t02-sc", targets[key])

    def test_anchor_missing_duplicate_heading_wrong_key_and_unrelated_names_fail_closed(self):
        key = "acme/project|shared-results|incompatible-reuse"
        section = '<h3><a class="anchor" aria-hidden="true" href="#t-32-03">T-32-03</a></h3><p>Canonical risk key: ' + key + '</p>'
        cases = ["<h3>T-32-03</h3>", section + section,
                 section.replace(key, "acme/project|different|risk"),
                 '<a name="user-content-t-32-03"></a><p>Unrelated text</p><h3>T-32-03</h3>',
                 '<a name="same-address"></a><h3>Other risk</h3><p>Canonical risk key: other-risk</p>'
                 '<a name="same-address"></a>' + section,
                 '<a name="one"></a><a name="two"></a><h3>T-32-03</h3><p>Canonical risk key: ' + key + '</p>']
        for html in cases:
            with self.subTest(html=html):
                targets, pending = self.rendered(html)
                self.assertEqual({}, targets)
                self.assertEqual(1, len(pending))

    def test_native_heading_anchor_remains_supported(self):
        key = "acme/project|shared-results|incompatible-reuse"
        targets, pending = self.rendered('<h3 id="t-32-03">T-32-03</h3><p>Canonical risk key: ' + key + '</p>')
        self.assertEqual([], pending)
        self.assertEqual("https://github.com/acme/project/issues/497#t-32-03", targets[key])

    def audit_fixture(self, identifiers=("T-01-SC", "T-01-SC")):
        directory = Path(self.phase())
        risks = {}
        target = "https://github.com/acme/project/issues/5#supply-chain"
        occurrences = []
        for index, identifier in enumerate(identifiers, 1):
            name = f"01-{index:02}-PLAN.md"
            (directory / name).write_text(register(identifier) + target + "\n")
            occurrences.append({"scope": "phase-key", "plan": name, "threat_id": identifier, "target": target})
        risks["shared-risk"] = {"entry_id": "SC", "heading": "Supply chain", "canonical_url": target,
                                "occurrences": occurrences}
        ctx = {"directory": directory, "key": "phase-key", "id": "01", "kind": "phase", "origin": {}}
        return ctx, {"risks": risks}, target

    def audit(self, ctx, state, target):
        with patch.object(security, "_state", return_value=(None, state)), \
                patch.object(security.issues, "issue_get", return_value={"url": target.split("#")[0]}), \
                patch.object(security, "rendered_targets", return_value=({"shared-risk": target}, [])):
            return security.threat_audit(ctx)

    def test_reserved_sc_audit_keeps_every_owned_occurrence_and_shared_identity(self):
        ctx, state, target = self.audit_fixture()
        packet = self.audit(ctx, state, target)
        self.assertTrue(packet["ready"], packet["errors"])
        self.assertEqual(2, len(packet["findings"]))

    def test_reserved_sc_missing_occurrence_or_inconsistent_target_stays_pending(self):
        ctx, state, target = self.audit_fixture()
        missing = json.loads(json.dumps(state))
        missing["risks"]["shared-risk"]["occurrences"].pop()
        self.assertFalse(self.audit(ctx, missing, target)["ready"])
        mismatched = json.loads(json.dumps(state))
        mismatched["risks"]["shared-risk"]["occurrences"][1]["target"] = target.replace("supply-chain", "another-risk")
        self.assertFalse(self.audit(ctx, mismatched, target)["ready"])
        different = json.loads(json.dumps(state))
        occurrence = different["risks"]["shared-risk"]["occurrences"].pop()
        different["risks"]["different-risk"] = {**different["risks"]["shared-risk"], "occurrences": [occurrence]}
        self.assertFalse(self.audit(ctx, different, target)["ready"])

    def test_ordinary_duplicate_and_same_plan_sc_duplicate_fail_audit(self):
        ctx, state, target = self.audit_fixture(("T-01-01", "T-01-01"))
        self.assertFalse(self.audit(ctx, state, target)["ready"])
        ctx, state, target = self.audit_fixture()
        first = ctx["directory"] / "01-01-PLAN.md"
        first.write_text(first.read_text() + register("T-01-SC"))
        self.assertFalse(self.audit(ctx, state, target)["ready"])


class SecurityOccurrenceContracts(RuntimeCase):
    def test_invalid_security_apply_is_rejected_before_writing(self):
        directory = Path(self.phase())
        report = directory / '01-SECURITY.md'
        original = '---\nphase: "01"\nstatus: draft\n---\nAudit pending\n'
        for proposed in ({'audit_completed': 'true'}, {'covered_files': {}}):
            with self.subTest(proposed=proposed):
                report.write_text(original)
                source = self.put('resolution.json', json.dumps(proposed))
                preview = self.cli('security.resolve', '1', '--entries-file', source)
                self.cli('security.resolve', '1', '--entries-file', source, '--apply',
                         '--expect-digest', preview['snapshotDigest'], status=1, raw=True)
                self.assertEqual(original.encode(), report.read_bytes())

    def test_filled_canonical_security_template_is_schema_valid_without_verified_claim(self):
        template = Path(__file__).resolve().parents[1] / 'engineer/templates/SECURITY.md'
        report = self.put('.planning/phases/04-fixture/04-SECURITY.md', template.read_text().replace(
            '{N}', '04').replace('{phase-slug}', 'fixture').replace('{date}', '2026-11-05'))
        packet = self.cli('frontmatter.validate', report, '--schema', 'security')
        self.assertTrue(packet['valid'])
        self.assertEqual('draft', self.cli('frontmatter.get', report, '--field', 'status'))

    def test_supported_pending_security_report_apply_round_trips_typed_fields(self):
        directory = Path(self.phase())
        report = directory / '01-SECURITY.md'
        report.write_text('---\nphase: "01"\nstatus: draft\n---\nAudit pending\n')
        proposed = {'status': 'pending', 'revision': self.git('rev-parse', 'HEAD'),
                    'audit_revision': self.git('rev-parse', 'HEAD'), 'audit_completed': False,
                    'auditor': 'fixture auditor', 'asvs_level': 1, 'threat_evidence': [],
                    'fingerprint': 'pending', 'covered_files': ['README.md'], 'threats_open': 0,
                    'issue_refs': [], 'no_applicable_threats': False, 'coverage_rationale': 'Audit pending'}
        source = self.put('resolution.json', json.dumps(proposed))
        preview = self.cli('security.resolve', '1', '--entries-file', source)
        packet = self.cli('security.resolve', '1', '--entries-file', source, '--apply',
                          '--expect-digest', preview['snapshotDigest'])
        self.assertTrue(packet['applied'])
        self.assertFalse(packet['ready'])
        self.assertTrue(self.cli('frontmatter.validate', report, '--schema', 'security')['valid'])
        metadata = self.cli('frontmatter.get', report)
        for field, value in proposed.items():
            self.assertEqual(value, metadata[field])

    def test_security_schema_rejects_wrong_types_and_unknown_fields(self):
        frontmatter = _load('frontmatter')
        valid = {'phase': '01', 'status': 'draft'}
        invalid = {'slug': [], 'created': 1, 'asvs_level': True, 'audit_revision': [],
                   'audit_completed': 'true', 'auditor': [], 'threat_evidence': {}, 'fingerprint': [],
                   'covered_files': {}, 'no_applicable_threats': 'false', 'coverage_rationale': []}
        for field, value in invalid.items():
            with self.subTest(field=field):
                self.assertIn('Invalid type: ' + field, frontmatter.errors({**valid, field: value}, 'security'))
        self.assertIn('Unknown field: unrecognized', frontmatter.errors({**valid, 'unrecognized': []}, 'security'))

    def report_fixture(self, identifiers=("T-01-SC", "T-01-SC")):
        directory = Path(self.phase())
        for index, identifier in enumerate(identifiers, 1):
            path = directory / f"01-{index:02}-PLAN.md"
            path.write_text(register(identifier))
        self.git("add", ".planning")
        self.git("commit", "-m", "frozen source records")
        frozen = self.git("rev-parse", "HEAD")
        report = directory / "01-SECURITY.md"
        evidence = [{"id": identifier, "plan": f"01-{index:02}-PLAN.md",
                     "citations": [{"commit": frozen, "path": "README.md", "quote": "Fixture"}]}
                    for index, identifier in enumerate(identifiers, 1)]
        metadata = {"phase": "01", "status": "verified", "revision": frozen,
                    "audit_completed": True, "auditor": "independent fixture auditor", "asvs_level": 1,
                    "covered_files": ["README.md"], "threats_open": 0, "threat_evidence": evidence}
        ctx = {"directory": directory, "id": "01", "kind": "phase"}
        with patch.dict(os.environ, self.env):
            metadata["fingerprint"] = security.security_fingerprint(ctx, ["README.md"])
        rows = [{"id": identifier, "plan": f"01-{index:02}-PLAN.md", "status": "closed"}
                for index, identifier in enumerate(identifiers, 1)]
        self.save_report(report, metadata, rows)
        return report, metadata, rows

    def save_report(self, report, metadata, rows, include_plan=True):
        header = "| Threat ID |" + (" PLAN |" if include_plan else "") + " Severity | Disposition | Status |\n"
        body = header + "|---|" + ("---|" if include_plan else "") + "---|---|---|\n"
        for row in rows:
            body += "| " + row["id"] + " |" + (" " + row["plan"] + " |" if include_plan else "") + " high | mitigate | " + row["status"] + " |\n"
        report.write_text(text_format.join_frontmatter(metadata, body))
        self.git("add", str(report.relative_to(self.root)))
        self.git("commit", "--allow-empty", "-m", "actual security evidence")

    def status(self):
        with patch.dict(os.environ, self.env):
            return security.security_status(security.Args(["1"]))

    def test_reserved_sc_status_validates_each_plan_occurrence(self):
        self.report_fixture()
        packet = self.status()
        self.assertTrue(packet["ready"], packet["reasons"])
        self.assertEqual(0, packet["threats_open"])

    def test_unique_id_report_keeps_existing_no_plan_shape(self):
        report, metadata, rows = self.report_fixture(("T-01-01",))
        metadata["threat_evidence"][0].pop("plan")
        self.save_report(report, metadata, rows, include_plan=False)
        self.assertTrue(self.status()["ready"], self.status()["reasons"])

    def test_reserved_sc_status_omission_duplicate_wrong_plan_and_missing_citation_reject(self):
        report, metadata, rows = self.report_fixture()
        scenarios = []
        scenarios.append((metadata, rows[:1], True))
        scenarios.append((metadata, rows + rows[:1], True))
        scenarios.append((metadata, [{**rows[0], "plan": "01-99-PLAN.md"}, rows[1]], True))
        scenarios.append((metadata, rows, False))
        for replacement in ([], [{"id": "T-01-SC", "citations": metadata["threat_evidence"][0]["citations"]}],
                            [{**metadata["threat_evidence"][0], "citations": []}, metadata["threat_evidence"][1]],
                            [{**metadata["threat_evidence"][0], "plan": "01-99-PLAN.md"}, metadata["threat_evidence"][1]]):
            scenarios.append(({**metadata, "threat_evidence": replacement}, rows, True))
        for index, (meta, values, include_plan) in enumerate(scenarios):
            with self.subTest(scenario=index):
                self.save_report(report, meta, values, include_plan)
                self.assertFalse(self.status()["ready"])

    def test_windows_security_report_lookup_keeps_exact_committed_evidence(self):
        report, metadata, rows = self.report_fixture(("T-01-01",))
        original = Path.relative_to
        def windows_relative(path, *args):
            relative = original(path, *args)
            return PureWindowsPath(relative) if path == report else relative
        with patch.object(Path, "relative_to", windows_relative):
            packet = self.status()
            self.assertTrue(packet["ready"], packet["reasons"])


if __name__ == "__main__":
    unittest.main()
