"""All source and API data synthetic; no network calls."""
from datetime import date
import unittest

from api_football_crosscheck import (
    clean_team, read_openfootball_matches, read_api_matches, reconcile
)

START = date(2026, 8, 21)
END = date(2026, 8, 31)
SAMPLE = """= English Premier League 2026/27
▪ Matchday 1
  Fri Aug 21 2026
    20:00  Arsenal FC              v Coventry City FC         3-0 (2-0)
  Sat Aug 22
    12:30  Hull City AFC           v Manchester United FC     2-0 (2-0)
           Leeds United FC         v Brentford FC             0-0
"""


def api_row(fid, day, home, away, score, code="FT"):
    return {"fixture": {"id": fid, "date": day + "T15:00:00+00:00", "status": {"short": code}},
            "league": {"id": 39, "season": 2026},
            "teams": {"home": {"id": fid * 10, "name": home},
                      "away": {"id": fid * 10 + 1, "name": away}},
            "goals": {"home": score[0], "away": score[1]}}


def api_response(rows):
    return {"results": len(rows), "paging": {"total": 1}, "response": rows}


class IndependentResultsTests(unittest.TestCase):
    def test_source_formats_and_dates(self):
        records = read_openfootball_matches(SAMPLE, START, END)
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0], (date(2026, 8, 21), "arsenal", "coventry city", (3, 0)))
        self.assertEqual(records[2][-1], (0, 0))

    def test_normalization_is_conservative(self):
        self.assertEqual(clean_team("AFC Bournemouth"), "bournemouth")
        self.assertEqual(clean_team("Club Atlético de Madrid"), "club atletico de madrid")
        self.assertNotEqual(clean_team("Real Madrid CF"), clean_team("Real Sociedad"))

    def test_weekday_error_detected(self):
        with self.assertRaises(ValueError):
            read_openfootball_matches(SAMPLE.replace("Fri Aug 21", "Sat Aug 21"), START, END)

    def test_duplicate_source_fails(self):
        with self.assertRaises(RuntimeError):
            read_openfootball_matches(SAMPLE + "    19:00  Leeds United FC v Brentford FC    0-0\n", START, END)

    def test_api_rejects_duplicates_and_wrong_league(self):
        a = api_row(1, "2026-08-21", "Arsenal", "Coventry City", (3, 0))
        with self.assertRaises(RuntimeError):
            read_api_matches(api_response([a, a]), 39, 2026, START, END)
        b = api_row(2, "2026-08-21", "Arsenal", "Coventry City", (3, 0))
        b["league"]["id"] = 140
        with self.assertRaises(RuntimeError):
            read_api_matches(api_response([b]), 39, 2026, START, END)

    def test_api_excludes_unfinished_without_inventing_result(self):
        x = api_row(1, "2026-08-21", "Arsenal", "Coventry City", (None, None), "NS")
        scores, skipped = read_api_matches(api_response([x]), 39, 2026, START, END)
        self.assertEqual(scores, [])
        self.assertEqual(skipped, 1)

    def test_match_scores_and_disagreements_and_unmatched(self):
        src = read_openfootball_matches(SAMPLE, START, END)
        a = [
            api_row(1, "2026-08-21", "Arsenal", "Coventry City", (3, 0)),
            api_row(2, "2026-08-22", "Hull City", "Manchester United", (1, 0)),
        ]
        official, _ = read_api_matches(api_response(a), 39, 2026, START, END)
        s = reconcile(src, official)
        self.assertEqual(s["matched"], 2)
        self.assertEqual(s["same_score"], 1)
        self.assertEqual(s["score_disagreements"], 1)
        self.assertEqual(s["source_unmatched"], 1)

    def test_ambiguous_no_guess_and_shift_tracked(self):
        src = [(date(2026, 8, 21), "arsenal", "coventry", (3, 0))]
        data = [
            (date(2026, 8, 20), "arsenal", "coventry", (3, 0)),
            (date(2026, 8, 22), "arsenal", "coventry", (3, 0)),
        ]
        s = reconcile(src, data)
        self.assertEqual(s["ambiguous"], 1)
        self.assertEqual(s["matched"], 0)
        s2 = reconcile(src, [data[0]])
        self.assertEqual(s2["day_shifts"], 1)

    def test_unsupported_api_status_and_pagination(self):
        a = api_row(1, "2026-08-21", "Arsenal", "Coventry", (1, 0))
        data = api_response([a])
        data["paging"]["total"] = 2
        with self.assertRaises(RuntimeError):
            read_api_matches(data, 39, 2026, START, END)


if __name__ == "__main__":
    unittest.main()
