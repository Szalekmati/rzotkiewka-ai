"""Offline tests for season-2025 OpenLigaDB list. No network, bets, or forecast changes."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import league_shortcuts_2025 as audit

NOW = datetime(2026, 11, 11, 14, tzinfo=timezone.utc)


class LeagueShortcutTests(unittest.TestCase):
    def test_inventory_identifies_old_shortcuts_and_manual_name_candidates(self):
        rows = [
            {"leagueShortcut": "pl", "leagueName": "Premier League 2025/26",
             "leagueSeason": "2025"},
            {"leagueShortcut": "laX", "leagueName": "La Liga Primera División",
             "leagueSeason": "2025"},
            {"leagueShortcut": "bl1", "leagueName": "Bundesliga", "leagueSeason": "2025"},
            {"leagueShortcut": "pl", "leagueName": "Premier League 2025/26",
             "leagueSeason": "2025"},  # duplicated source entry
        ]
        summary = audit.candidate_records(rows)
        self.assertEqual(summary["source_entries"], 4)
        self.assertEqual(summary["matching_entries"], 2)
        self.assertEqual(summary["listed_shortcuts"], {"pl": True, "la1": False})
        self.assertFalse(summary["automatic_promotion"])
        exact, suggestion = summary["manual_review_leads"]
        self.assertEqual(exact["shortcut"], "pl")
        self.assertTrue(exact["exact_old_shortcut"])
        self.assertEqual(suggestion["shortcut"], "laX")
        self.assertFalse(suggestion["exact_old_shortcut"])
        self.assertEqual(suggestion["why_listed"], "name_similarity_only")

    def test_unrelated_leagues_never_count_as_present(self):
        rows = [{"leagueShortcut": "bl1", "leagueName": "Bundesliga",
                 "leagueSeason": "2025"},
                {"leagueShortcut": "test", "leagueName": "First League",
                 "leagueSeason": "2025"}]
        x = audit.candidate_records(rows)
        self.assertEqual(x["listed_shortcuts"], {"pl": False, "la1": False})
        self.assertEqual(x["manual_review_leads"], [])
        self.assertFalse(x["automatic_promotion"])

    def test_name_normalization_and_markdown_safe_labels(self):
        x = audit.candidate_records([
            {"leagueShortcut": "esp", "leagueName": "Primera División | Spain\n<a>",
             "leagueSeason": "2025"}
        ])
        self.assertEqual(x["matching_entries"], 1)
        row = x["manual_review_leads"][0]
        self.assertEqual(row["name"], "Primera División   Spain  a")
        self.assertNotIn("|", row["name"])
        self.assertNotIn("\n", row["name"])

    def test_invalid_json_structure_is_rejected(self):
        for value in (None, {}, "oops", 5):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    audit.candidate_records(value)
        with self.assertRaises(ValueError):
            audit.candidate_records([{}] * 50001)

    def test_report_is_readonly_and_success_requires_fetched_inventory(self):
        rows = [
            {"leagueShortcut": "pl", "leagueName": "Premier League", "leagueSeason": "2025"},
            {"leagueShortcut": "l25", "leagueName": "LaLiga", "leagueSeason": "2025"},
        ]
        with tempfile.TemporaryDirectory() as tmp, patch.object(
                audit, "fetch_inventory", return_value=rows):
            doc = audit.run(Path(tmp), NOW)
            self.assertTrue(doc["fetch_ok"])
            self.assertFalse(doc["automatic_promotion"])
            self.assertEqual(doc["listed_shortcuts"], {"pl": True, "la1": False})
            body = (Path(tmp) / "SKROTY_LIG_2025.md").read_text(encoding="utf-8")
            self.assertIn("pl — NA LIŚCIE", body)
            self.assertIn("la1 — BRAK NA LIŚCIE", body)
            self.assertIn("ręczna ocena", body)
            self.assertIn("nie potwierdza danych historycznych", body)
            other = json.loads((Path(tmp) / "skroty_lig_2025.json").read_text())
            self.assertEqual(other["kind"], "historical_league_shortcut_inventory_only")

    def test_failure_is_visible_not_turned_into_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
                audit, "fetch_inventory", side_effect=TimeoutError("API timeout")):
            doc = audit.run(Path(tmp), NOW)
            self.assertFalse(doc["fetch_ok"])
            self.assertIn("TimeoutError", doc["error"])
            self.assertNotIn("listed_shortcuts", doc)
            text = (Path(tmp) / "SKROTY_LIG_2025.md").read_text()
            self.assertIn("Nie udało się potwierdzić", text)
            self.assertNotIn("— BRAK NA LIŚCIE", text)

    def test_no_production_mutations_or_alias_autopromotion(self):
        path = Path(__file__).resolve().parents[1] / "league_shortcuts_2025.py"
        src = path.read_text(encoding="utf-8")
        self.assertIn('"automatic_promotion": False', src)
        self.assertNotIn("subprocess.", src)
        self.assertNotIn("forecast_engine", src)
        self.assertNotIn("lab_forward/", src)
        self.assertNotIn("predictions.json", src)
        self.assertNotIn("getmatchdata/", src)
        self.assertEqual(audit.ENDPOINT,
                         "https://api.openligadb.de/getavailableleagues/2025")


if __name__ == "__main__":
    unittest.main()
