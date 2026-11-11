"""Synthetic records only; offline tests never use a real API key."""
import unittest
from datetime import date, datetime, timezone

from api_football_fixtures_quality import analyze_fixtures, bounded_window


TODAY = date(2026, 11, 11)
START, END = date(2026, 11, 1), date(2026, 11, 10)
NOW = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)


def fixture(fid=101, league_id=39, season=2026, kickoff="2026-11-07T15:00:00+00:00",
            status="FT", home=3, away=1):
    return {
        "fixture": {"id": fid, "date": kickoff, "status": {"short": status}},
        "league": {"id": league_id, "season": season},
        "teams": {"home": {"id": 1, "name": "Home"},
                  "away": {"id": 2, "name": "Away"}},
        "goals": {"home": home, "away": away},
    }


def payload(rows):
    return {"results": len(rows), "paging": {"current": 1, "total": 1}, "response": rows}


class FixtureAuditTests(unittest.TestCase):
    def analyze(self, rows):
        return analyze_fixtures(payload(rows), 39, 2026, START, END, now=NOW)

    def test_one_finished_valid(self):
        a = self.analyze([fixture()])
        self.assertEqual(a["mecze"], 1)
        self.assertEqual(a["zakonczone"], 1)
        self.assertEqual(a["wynik_koncowy_niepelny"], 0)
        self.assertEqual(a["zla_data"], 0)

    def test_duplicates_and_wrong_league(self):
        a = self.analyze([fixture(), fixture(league_id=140)])
        self.assertEqual(a["duplikaty_id"], 1)
        self.assertEqual(a["zla_liga_sezon"], 1)

    def test_final_without_score_detected(self):
        a = self.analyze([fixture(home=None)])
        self.assertEqual(a["wynik_koncowy_niepelny"], 1)

    def test_incomplete_teams_detected(self):
        f = fixture()
        f["teams"]["away"]["id"] = 1
        self.assertEqual(self.analyze([f])["niepelne_druzyny"], 1)

    def test_invalid_timezone_and_date_detected(self):
        f = fixture(kickoff="2026-11-07T15:00:00")
        self.assertEqual(self.analyze([f])["zla_data"], 1)
        g = fixture(fid=102, kickoff="2026-10-30T15:00:00Z")
        self.assertEqual(self.analyze([g])["zla_data"], 1)

    def test_old_nonfinal_warns_without_inventing_result(self):
        f = fixture(status="NS", home=None, away=None)
        a = self.analyze([f])
        self.assertEqual(a["zakonczone"], 0)
        self.assertEqual(a["stare_nierozliczone"], 1)
        self.assertEqual(a["wynik_koncowy_niepelny"], 0)

    def test_postponed_is_not_assumed_played(self):
        self.assertEqual(self.analyze([fixture(status="PST")])["stare_nierozliczone"], 0)

    def test_response_mismatch_fails(self):
        x = payload([fixture()])
        x["results"] = 2
        with self.assertRaises(RuntimeError):
            analyze_fixtures(x, 39, 2026, START, END)

    def test_pagination_fails(self):
        x = payload([fixture()])
        x["paging"]["total"] = 2
        with self.assertRaises(RuntimeError):
            analyze_fixtures(x, 39, 2026, START, END)

    def test_bounded_window(self):
        self.assertEqual(bounded_window(2026, "", "", today=TODAY),
                         (date(2026, 11, 1), TODAY))
        for start, end in [("2026-10-01", "2026-11-11"),
                           ("2026-11-13", "2026-11-13"),
                           ("2026-11-10", "2026-11-09"),
                           ("2025-11-05", "2025-11-06")]:
            with self.assertRaises(ValueError):
                bounded_window(2026, start, end, today=TODAY)


if __name__ == "__main__":
    unittest.main()
