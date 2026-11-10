"""Protect the frozen forward experiment from accidental schedule/bundle drift.

This is a static, offline safety guard. Passing it does NOT prove that the
GitHub Actions schedule event was delivered.
"""
import base64
import hashlib
import io
import json
import re
import unittest
import zipfile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "test_przedmeczowy.yml"
FROZEN_SHA256 = "b527e7ebf9f77245fa15a977f1bd79d28d2f6a7fa7ed01bbef54f8bec8ef2689"
EXPECTED_CRON = "37 * * * *"


class ForwardLabSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_hourly_schedule_and_manual_fallback(self):
        text = self.workflow
        self.assertRegex(text, r"(?m)^on:\s*\n  workflow_dispatch:\s*\n  schedule:\s*\n")
        self.assertRegex(text, r"(?m)^\s+- cron: '37 \* \* \* \*'\s*$")
        self.assertNotRegex(text, r"(?m)^  (push|pull_request|pull_request_target):")
        for line in (
            '  workflow_run:',
            'workflows: ["RZOTKIEWKA - prognozy i wyniki 1.6"]',
            'types: [completed]',
            'branches: [main]',
            "github.event.workflow_run.conclusion == 'success'",
            "github.event.workflow_run.event == 'schedule'",
            "github.event.workflow_run.head_branch == github.event.repository.default_branch",
            "github.event.workflow_run.repository.full_name == github.repository",
        ):
            self.assertIn(line, text)
        self.assertIn("group: rzotkiewka-forward-lab", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn("contents: write", text)

    def test_frozen_bundle_is_unchanged_and_has_six_hour_window(self):
        text = self.workflow
        payloads = re.findall(r'payload\s*=\s*"""(.*?)"""', text, re.S)
        self.assertEqual(len(payloads), 1, "Expected one immutable zip payload")
        expected = re.findall(
            r"hashlib\.sha256\(blob\)\.hexdigest\(\) != '([0-9a-f]{64})'",
            text)
        self.assertEqual(expected, [FROZEN_SHA256])
        blob = base64.b64decode(payloads[0])
        self.assertEqual(hashlib.sha256(blob).hexdigest(), FROZEN_SHA256)
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            names = archive.namelist()
            self.assertTrue(all(
                not name.startswith("/") and ".." not in Path(name).parts
                for name in names))
            for file in ("config.json", "forward.py", "archived_v21.py"):
                self.assertIn(file, names)
            config = json.loads(archive.read("config.json"))
            self.assertEqual(config.get("min_lead_hours"), 162)
            self.assertEqual(config.get("max_lead_hours"), 168)

    def test_quality_ci_runs_on_lab_safety_changes_in_pull_requests(self):
        quality = (ROOT / ".github" / "workflows" / "quality_site.yml").read_text(encoding="utf-8")
        self.assertIn("  pull_request:\n    branches: [main]\n    paths:\n", quality)
        pr_paths = quality.split("  pull_request:", 1)[1].split("  push:", 1)[0]
        for path in (
            "tests/test_site_integrity.py",
            "tests/test_mobile_nav.cjs",
            "tests/test_archive_fail_closed.mjs",
            "tests/test_lab_schedule.py",
            "tests/test_lab_diagnostics.py",
            ".github/workflows/diagnostyka_terminarza_lab.yml",
            ".github/workflows/test_przedmeczowy.yml",
            ".github/workflows/quality_site.yml",
        ):
            self.assertIn(f"      - '{path}'", pr_paths)

    def test_status_output_tracks_trigger_and_attempt(self):
        text = self.workflow
        for term in (
            "'event': os.environ['GITHUB_EVENT_NAME']",
            "'upstream_event': os.environ.get('UPSTREAM_EVENT') or None",
            "'upstream_run_id': os.environ.get('UPSTREAM_RUN_ID') or None",
            "'observed_at': datetime.now(timezone.utc).isoformat",
            "'observation_outcome': os.environ['OBSERVATION_OUTCOME']",
            "'planned_cron_utc': '37 * * * *'",
            "git add -- lab_forward/",
            "git push origin \"HEAD:$TARGET_BRANCH\"",
        ):
            self.assertIn(term, text)
        status = json.loads((ROOT / "lab_forward" / "run_status.json")
                            .read_text(encoding="utf-8"))
        self.assertIn(status["event"], ("workflow_dispatch", "schedule", "workflow_run"))
        if status["event"] == "workflow_run":
            self.assertEqual(status.get("upstream_event"), "schedule")
        self.assertEqual(status["planned_cron_utc"], EXPECTED_CRON)
        observed = datetime.fromisoformat(
            status["observed_at"].replace("Z", "+00:00"))
        self.assertIsNotNone(observed.tzinfo)
        self.assertLess(observed, datetime.now(timezone.utc))
        self.assertRegex(status["run_id"], r"^\d+$")


if __name__ == "__main__":
    unittest.main()
