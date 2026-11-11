"""Offline tests for the independent CC0 source audit. No network is used."""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import openfootball_history_audit as audit

NOW = datetime(2026, 11, 11, 14, tzinfo=timezone.utc)

GOOD = """= Test League 2025/26

# Matches  2
# Teams    2

Fri Aug 15 2025
  19:00   Alpha FC  2-1 (1-0)  Beta FC
Sat Aug 16
  20:00   Beta FC  0-0 (0-0)  Alpha FC
"""


class OpenFootballHistoryTests(unittest.TestCase):
    def test_small_complete_home_away_round_robin(self):
        data = audit.assess_text(GOOD, expected_matches=2, expected_teams=2)
        self.assertTrue(data["structurally_complete"])
        self.assertEqual(data["declared_matches"], 2)
        self.assertEqual(data["parsed_scores"], 2)
        self.assertEqual(data["teams"], 2)
        self.assertEqual(data["unique_home_away_pairs"], 2)
        self.assertTrue(data["balanced_home_away"])
        self.assertFalse(data["independently_result_verified"])
        self.assertFalse(data["fixture_dates_verified"])
        self.assertFalse(data["approved_for_forecasts"])

    def test_missing_duplicate_and_bad_scores_fail_closed(self):
        cases = (
            GOOD.replace("Beta FC  0-0 (0-0)  Alpha FC",
                         "Alpha FC  0-0 (0-0)  Beta FC"),
            GOOD.replace("Beta FC  0-0 (0-0)  Alpha FC", "Beta FC  –  Alpha FC"),
            GOOD.replace("2-1 (1-0)", "2-1 (3-0)"),
            GOOD.replace("20:00", "25:00"),
            GOOD.replace("# Matches  2", "# Matches  3"),
            GOOD.replace("# Matches  2", "# Games  2"),
        )
        for case in cases:
            with self.subTest(case=case[-105:]):
                self.assertFalse(audit.assess_text(
                    case, expected_matches=2, expected_teams=2)["structurally_complete"])

    def test_no_synthetic_results_or_unrelated_lines(self):
        sample = GOOD + "\n   (Goal scorer 2')\n   Fixtures tbd\n"
        self.assertEqual(audit.assess_text(
            sample, expected_matches=2, expected_teams=2)["parsed_scores"], 2)
        self.assertRaises(ValueError, audit.assess_text, {})

    def test_pinned_urls_and_source_boundaries(self):
        self.assertEqual(set(audit.SOURCES), {"Premier League", "LaLiga"})
        for league, meta in audit.SOURCES.items():
            self.assertRegex(meta["commit"], "^[0-9a-f]{40}$")
            self.assertIn(meta["commit"], audit.source_url(meta))
            self.assertTrue(audit.source_url(meta).startswith(
                "https://raw.githubusercontent.com/openfootball/"))
        script = (Path(__file__).resolve().parents[1] /
                  "openfootball_history_audit.py").read_text(encoding="utf-8")
        self.assertNotIn("forecast_engine", script)
        self.assertNotIn("predictions.json", script)
        self.assertNotIn("lab_forward/", script)

    def test_reports_are_structural_not_model_admission(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
                audit, "fetch_text", return_value=GOOD):
            result = audit.run(Path(tmp), NOW)
            self.assertFalse(result["automatic_promotion"])
            self.assertFalse(result["models_modified"])
            self.assertEqual(len(result["leagues"]), 2)
            self.assertTrue(all(x["structurally_complete"]
                                for x in result["leagues"].values()))
            text = (Path(tmp) / "OPENFOOTBALL_HISTORIA_2025.md").read_text()
            self.assertIn("Struktura", text)
            self.assertIn("Zgodna struktura nie dowodzi", text)
            data = json.loads((Path(tmp) / "openfootball_historia_2025.json").read_text())
            self.assertFalse(data["leagues"]["LaLiga"]["approved_for_forecasts"])

    def test_fetch_failure_not_misrepresented_as_absent_history(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
                audit, "fetch_text", side_effect=TimeoutError("source timeout")):
            result = audit.run(Path(tmp), NOW)
            self.assertFalse(result["leagues"]["LaLiga"]["read_ok"])
            self.assertIn("TimeoutError", result["leagues"]["LaLiga"]["error"])
            text = (Path(tmp) / "OPENFOOTBALL_HISTORIA_2025.md").read_text()
            self.assertIn("NIEPOTWIERDZONA", text)
            self.assertNotIn("| LaLiga | 0 | 0 |", text)


if __name__ == "__main__":
    unittest.main()
