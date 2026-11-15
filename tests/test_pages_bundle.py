"""Offline regression tests for Pages preview (no deployment)."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "pages_preview", ROOT / "tools/prepare_pages_bundle.py")
pages = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pages)


class PagesPreviewTests(unittest.TestCase):
    def test_site_references_are_all_in_allowlist(self):
        manifest = pages.validate()
        self.assertEqual(set(manifest), set(pages.PUBLIC_FILES))
        self.assertEqual(
            pages.references((ROOT / "index.html").read_text(encoding="utf-8")),
            {
                "lab_forward/RAPORT.md", "lab_forward/experiment.json",
                "lab_forward/ledger.json", "lab_forward/run_status.json",
                "predictions.json", "tips.json",
            },
        )

    def test_bundle_is_byte_identical_and_excludes_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "pages-bundle"
            checksums = pages.stage(dest)
            actual = {
                p.relative_to(dest).as_posix()
                for p in dest.rglob("*") if p.is_file()
            }
            self.assertEqual(actual, set(pages.PUBLIC_FILES))
            for rel in checksums:
                self.assertEqual((dest / rel).read_bytes(), (ROOT / rel).read_bytes())
                self.assertFalse(rel.startswith((".github/", "docs/", "tests/", "tools/", "data/")))
            with self.assertRaises(ValueError):
                pages.stage(dest)

    def test_missing_and_conflicting_sources_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for rel in pages.PUBLIC_FILES:
                file = base / rel
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes((ROOT / rel).read_bytes())
            (base / "CNAME").write_text("wrong.example\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "CNAME"):
                pages.validate(base)
            (base / "CNAME").write_text("rzotkiewka.pl\n", encoding="utf-8")
            (base / "tips.json").unlink()
            with self.assertRaisesRegex(ValueError, "Missing"):
                pages.validate(base)

    def test_unlisted_local_asset_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for rel in pages.PUBLIC_FILES:
                file = base / rel
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes((ROOT / rel).read_bytes())
            page = base / "index.html"
            page.write_text(
                page.read_text(encoding="utf-8")
                + "\n<script>fetch('./secret.json')</script>",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unstaged"):
                pages.validate(base)


    def test_ci_retains_both_readonly_quality_gates(self):
        """PR #42 must not erase LAB checks already merged by PR #40."""
        workflow = (ROOT / ".github/workflows/quality_site.yml").read_text(encoding="utf-8")
        checks = (
            "test_lab_readonly_status.py",
            "test_pages_bundle.py",
        )
        for filename in checks:
            with self.subTest(filename=filename):
                self.assertEqual(workflow.count(f"      - 'tests/{filename}'"), 2)
                self.assertEqual(
                    workflow.count(f"run: python -m unittest discover -s tests -p '{filename}' -v"),
                    1,
                )
        self.assertIn("lab_forward/status_readonly.py", workflow)
        self.assertIn("tools/prepare_pages_bundle.py", workflow)
        self.assertIn("      - name: Testy niezmiennosci harmonogramu i modeli LAB", workflow)


    def test_preview_preserves_published_lab_observation_notices(self):
        """Pages preview must retain the truthful LAB freshness UI from PR #43."""
        original = (ROOT / "index.html").read_text(encoding="utf-8")
        for text in (
            "Czas obserwacji nie jest czasem publikacji strony",
            "function labSnapshotAge(status,now=Date.now())",
            "Nowsze skany mogły zajść bez nowej publikacji",
            "Ostatnia obserwacja w opublikowanym raporcie:",
        ):
            with self.subTest(text=text):
                self.assertIn(text, original)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "pages-preview"
            pages.stage(output)
            self.assertEqual((output / "index.html").read_bytes(),
                             (ROOT / "index.html").read_bytes())


    def test_pages_change_classifier_real_commit_examples(self):
        """Compare known repo edits without assuming any current deployment filter."""
        from tools.pages_change_impact import classify
        # Confirmed status-only commits ac78286, b22cdc6:
        changed = ["lab_forward/RAPORT.md", "lab_forward/run_status.json"]
        strict = classify(changed)
        self.assertEqual(strict["decision"], "PUBLISH_CANDIDATE")
        opt_in = classify(changed, allow_stale_lab=True)
        self.assertEqual(opt_in["decision"], "SKIP_CANDIDATE_STALE_LAB")
        self.assertEqual(opt_in["mode"], "DRY_RUN_ONLY")
        self.assertEqual(opt_in["lab_observations"], sorted(changed))
        # #39 changed actual public HTML, so even opt-in must publish.
        self.assertEqual(classify(
            ["index.html", "tests/test_demo_cards.mjs"],
            allow_stale_lab=True)["decision"], "PUBLISH_CANDIDATE")
        # A new observation and new ledger must publish even in opt-in mode.
        self.assertEqual(classify(
            ["lab_forward/ledger.json", "lab_forward/run_status.json"],
            allow_stale_lab=True)["decision"], "PUBLISH_CANDIDATE")
        # #42 changed only build/research files (not public data), but a
        # workflow change requires human review rather than a blind skip.
        self.assertEqual(classify(
            [".github/workflows/quality_site.yml",
             "docs/PAGES_PLAN_DRY_RUN.md",
             "tools/prepare_pages_bundle.py"])["decision"], "REVIEW_UNKNOWN")

    def test_pages_change_classifier_fails_closed(self):
        from tools.pages_change_impact import classify
        for path in ("new/unknown.css", ".github/workflows/deploy.yml", "logo.png",
                     "lab_forward/new_data.json"):
            with self.subTest(path=path):
                result = classify([path], allow_stale_lab=True)
                self.assertEqual(result["decision"], "REVIEW_UNKNOWN")
                self.assertEqual(result["unknown"], [path])
        for path in ("../secret", "/tmp/foo", "a/./x", "a//b", "a\\b",
                     "", " file ", "./index.html"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    classify([path])
        with self.assertRaises(ValueError):
            classify([])
        self.assertEqual(classify(
            ["CNAME"], allow_stale_lab=True)["decision"], "PUBLISH_CANDIDATE")
        self.assertEqual(classify(
            ["tools/prepare_pages_bundle.py"])["decision"], "PUBLISH_CANDIDATE")
        self.assertEqual(classify(
            ["tools/prepare_pages_bundle.py"])["build_inputs"], ["tools/prepare_pages_bundle.py"])
        self.assertEqual(classify(
            ["tests/test_pages_bundle.py", "docs/PAGES_IMPACT_DRY_RUN.md"]
        )["decision"], "SKIP_CANDIDATE_TECHNICAL")
        self.assertEqual(classify(
            ["index.html", "unlisted/new_file.json"],
            allow_stale_lab=True)["decision"], "REVIEW_UNKNOWN")


if __name__ == "__main__":
    unittest.main()
