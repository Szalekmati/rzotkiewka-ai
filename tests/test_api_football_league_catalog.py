"""Testy offline katalogu lig - zadnych polaczen ani kluczy."""
import unittest

from api_football_league_catalog import (
    CANDIDATES, check_quota, coverage_flag, summarize_leagues,
)


class LeagueCatalogTests(unittest.TestCase):
    def sample(self):
        return {"paging": {"current": 1, "total": 1}, "response": [
            {"league": {"id": 39, "name": "Premier League"},
             "country": {"name": "England"},
             "seasons": [{"year": 2026, "coverage": {
                 "standings": True, "players": False,
                 "fixtures": {"events": True, "lineups": False}}}]},
            {"league": {"id": 140, "name": "La Liga"},
             "country": {"name": "Spain"},
             "seasons": [{"year": 2025, "coverage": {"standings": True}}]},
        ]}

    def test_nested_flags_never_assume_missing_is_true(self):
        c = {"fixtures": {"events": True}, "odds": False}
        self.assertEqual(coverage_flag(c, ("fixtures", "events")), "T")
        self.assertEqual(coverage_flag(c, ("fixtures", "lineups")), "?")
        self.assertEqual(coverage_flag(c, ("odds",)), "N")
        self.assertEqual(coverage_flag({}, ("fixtures", "events")), "?")

    def test_exact_season_and_missing_not_approved(self):
        rows, count = summarize_leagues(self.sample(), 2026)
        self.assertEqual(count, 2)
        self.assertEqual(len(rows), len(CANDIDATES))
        premier = next(row for row in rows if row["id"] == 39)
        la_liga = next(row for row in rows if row["id"] == 140)
        self.assertTrue(premier["found"])
        self.assertEqual(premier["details"]["flags"]["standings"], "T")
        self.assertEqual(premier["details"]["flags"]["injuries"], "?")
        self.assertFalse(la_liga["found"])

    def test_duplicates_refused(self):
        data = self.sample()
        data["response"].append(data["response"][0])
        with self.assertRaises(RuntimeError):
            summarize_leagues(data, 2026)

    def test_pagination_refused(self):
        data = self.sample()
        data["paging"]["total"] = 3
        with self.assertRaises(RuntimeError):
            summarize_leagues(data, 2026)

    def test_invalid_list_refused(self):
        with self.assertRaises(RuntimeError):
            summarize_leagues({"response": {}}, 2026)

    def test_quota_reserve(self):
        check_quota({"limit_day": 7500, "used_today": 7399})
        for used in (7400, 7499, 7500, -1, 8000):
            with self.assertRaises(RuntimeError):
                check_quota({"limit_day": 7500, "used_today": used})


if __name__ == "__main__":
    unittest.main()
