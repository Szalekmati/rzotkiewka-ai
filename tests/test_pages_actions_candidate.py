"""Offline static tests for an INACTIVE GitHub Pages workflow proposal.

Never executes candidate YAML or changes GitHub Pages settings.
"""
from pathlib import Path
import re
import unittest

from tools.prepare_pages_bundle import PUBLIC_FILES
from tools.pages_change_impact import classify, ESSENTIAL_PUBLIC, BUILD_INPUTS

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "docs/PAGES_ACTIONS_CANDIDATE.yml"


class PagesActionsCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CANDIDATE.read_text(encoding="utf-8")

    def test_candidate_is_inactive_and_has_no_schedules(self):
        self.assertTrue(CANDIDATE.is_file())
        self.assertFalse((ROOT / ".github/workflows/pages_deploy.yml").exists())
        self.assertIn("# CANDIDATE ONLY", self.source)
        self.assertIn("on:\n  push:\n    branches: [main]", self.source)
        self.assertIn("  workflow_dispatch:", self.source)
        for trigger in ("\n  schedule:", "\n  pull_request:", "\n  workflow_run:"):
            self.assertNotIn(trigger, self.source)
        guard = "github.repository == 'Szalekmati/rzotkiewka-ai' && github.ref == 'refs/heads/main'"
        self.assertEqual(self.source.count(guard), 2)

    def test_every_public_file_and_builder_is_a_publish_trigger(self):
        paths = re.findall(r"(?m)^      - '([^']+)'$", self.source)
        expected = set(PUBLIC_FILES) | {
            "tools/prepare_pages_bundle.py", ".github/workflows/pages_deploy.yml",
        }
        self.assertEqual(len(paths), len(set(paths)), "Duplicate Pages paths")
        self.assertEqual(set(paths), expected)
        for path in PUBLIC_FILES:
            with self.subTest(file=path):
                self.assertEqual(classify([path])["decision"], "PUBLISH_CANDIDATE")
        self.assertIn("tools/prepare_pages_bundle.py", BUILD_INPUTS)
        self.assertEqual(classify(["tools/prepare_pages_bundle.py"])["decision"],
                         "PUBLISH_CANDIDATE")
        self.assertNotIn("lab_forward/RAPORT.md", ESSENTIAL_PUBLIC)

    def test_no_stale_lab_opt_in_or_pull_request_deployment(self):
        self.assertNotIn("--allow-stale-lab", self.source)
        self.assertNotIn("SKIP_CANDIDATE_STALE_LAB", self.source)
        self.assertNotIn("actions/cache@", self.source)
        self.assertNotIn("secrets.", self.source)
        self.assertIn("cancel-in-progress: false", self.source)
        self.assertIn("needs: build", self.source)
        self.assertIn("name: github-pages", self.source)
        self.assertIn("id-token: write", self.source)
        self.assertIn("pages: write", self.source)
        self.assertIn("actions/upload-pages-artifact@v4", self.source)
        self.assertIn("actions/deploy-pages@v4", self.source)

    def test_build_uses_reviewed_public_bundle(self):
        command = 'python tools/prepare_pages_bundle.py "$RUNNER_TEMP/rzotkiewka-pages"'
        self.assertIn(command, self.source)
        self.assertIn("path: " + "$" + "{{ runner.temp }}/rzotkiewka-pages", self.source)
        for testname in ("test_site_integrity.py", "test_lab_readonly_status.py",
                         "test_pages_bundle.py"):
            self.assertIn(testname, self.source)
        self.assertNotIn("git push", self.source)

    def test_migration_requires_owner_approval(self):
        instructions = (ROOT / "docs/PAGES_ACTIONS_MIGRATION.md").read_text(
            encoding="utf-8")
        for phrase in ("NIEAKTYWNY", "osobnym, jednoznacznym zatwierdzeniu",
                       "Settings > Pages", "rollback", "DNS", "LAB"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), instructions.lower())


if __name__ == "__main__":
    unittest.main()
