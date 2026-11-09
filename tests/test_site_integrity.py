"""Offline tests for the RZOTKIEWKA public free-forecast page."""
import json
import shutil
import subprocess
import tempfile
import unittest
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.ids = []
        self.js = []
        self.json_data = {}
        self.script = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "script":
            self.script = {"type": attrs.get("type") or "text/javascript",
                           "id": attrs.get("id"), "chunks": []}

    def handle_data(self, data):
        if self.script is not None:
            self.script["chunks"].append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            kind = self.script["type"].lower()
            content = "".join(self.script["chunks"])
            if kind in ("text/javascript", "application/javascript", "module"):
                self.js.append(content)
            if kind == "application/json":
                self.json_data[self.script["id"]] = json.loads(content)
            self.script = None


class SiteIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.page = Page()
        cls.page.feed(cls.html)
        cls.page.close()

    def test_unique_ids(self):
        duplicates = [i for i, n in Counter(self.page.ids).items() if n > 1]
        self.assertFalse(duplicates, f"Duplicate HTML IDs: {duplicates}")
        for ident in ("ranking", "rank-list", "rank-state", "rank-order",
                      "rank-minprob", "rank-hit", "rank-brier", "premium", "lab"):
            self.assertIn(ident, self.page.ids)

    def test_version_two_showcase_has_real_archive_bindings(self):
        self.assertIn("RZOTKIEWKA 2.0", self.html)
        for ident in ("hero-archive-total", "hero-archive-graded",
                      "hero-archive-hits", "hero-archive-misses",
                      "hero-archive-ratio", "hero-bar-hits",
                      "hero-bar-misses", "hero-archive-note"):
            self.assertIn(ident, self.page.ids)
        js = "\n".join(self.page.js)
        self.assertIn("const ready=state.archiveReady&&!state.archiveFailed;", js)
        self.assertIn("const hitPercent=ready&&stats.graded", js)
        self.assertNotIn("RZOTKIEWKA 1.14", self.html)

    def test_no_default_cherry_picking(self):
        self.assertRegex(self.html, r'<select id="rank-state">\s*<option value="all" selected>')
        self.assertRegex(self.html, r'<select id="rank-minprob">\s*<option value="0" selected>')
        self.assertRegex(self.html, r'<select id="rank-order">\s*<option value="newest" selected>')
        js = "\n".join(self.page.js)
        for check in ("if(status==='all')return true;", "if(order==='newest')return -dt",
                      "const data=state.archive,stats=rankGroup(data);", "NIETRAFIONY"):
            self.assertIn(check, js)

    def test_demonstration_is_clearly_separate(self):
        self.assertIn("BEZ OPŁAT · PUBLICZNE WYNIKI", self.html)
        self.assertIn("fikcyjne dane demonstracyjne", self.html)
        self.assertIn("Płatności i dostęp Premium jeszcze nie są aktywne.", self.html)
        tips = json.loads((ROOT / "tips.json").read_text(encoding="utf-8"))
        self.assertEqual(tips.get("mode"), "demo")

    def test_published_archive_is_valid(self):
        from forecast_engine import valid_doc
        doc = json.loads((ROOT / "predictions.json").read_text(encoding="utf-8"))
        valid_doc(doc)
        for entry in doc["forecasts"]:
            snap = entry["snapshot"]
            created = datetime.fromisoformat(snap["created_at"].replace("Z", "+00:00"))
            kickoff = datetime.fromisoformat(snap["kickoff"].replace("Z", "+00:00"))
            self.assertLess(created, kickoff, entry["id"])

    def test_embedded_json(self):
        self.assertIsInstance(self.page.json_data.get("research-original-json"), dict)

    def test_inline_javascript_syntax(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js not installed locally; CI requires Node.js")
        self.assertGreater(len(self.page.js), 0)
        with tempfile.TemporaryDirectory() as tmp:
            for n, source in enumerate(self.page.js, 1):
                file = Path(tmp) / f"page_{n}.js"
                file.write_text(source, encoding="utf-8")
                result = subprocess.run([node, "--check", str(file)],
                                        capture_output=True, text=True, timeout=25)
                self.assertEqual(result.returncode, 0,
                                 f"JavaScript #{n} invalid: {result.stderr}")


if __name__ == "__main__":
    unittest.main()
