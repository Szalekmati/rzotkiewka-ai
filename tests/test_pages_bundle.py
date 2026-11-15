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


if __name__ == "__main__":
    unittest.main()
