"""Offline timing tests: no paid API, personal data or fixture IDs logged."""
from datetime import datetime, timedelta, timezone
import unittest

from api_football_next_window import window_summary, display_time
from api_football_prematch_readiness import parse_fixtures

NOW = datetime(2026,11,11,12,0,tzinfo=timezone.utc)


def game(fid, kickoff, status="NS", score=None):
    return {"id":fid,"kickoff":kickoff,"status":status,"score":score,
            "home_id":fid+100,"away_id":fid+200}


class WindowsTests(unittest.TestCase):
    def test_no_fixtures(self):
        res=window_summary([],NOW)
        self.assertEqual(res["scheduled_future"],0)
        self.assertIsNone(res["next_open"])

    def test_nearest_outside_window_is_planned(self):
        t=NOW+timedelta(days=12)
        res=window_summary([game(1,t)],NOW)
        self.assertEqual(res["windows_currently_active"],0)
        self.assertEqual(res["next_open"],NOW+timedelta(days=4))
        self.assertEqual(res["next_close"],t-timedelta(hours=2))
        self.assertEqual(res["nearest_kickoff"],t)

    def test_opening_is_inclusive(self):
        t=NOW+timedelta(days=8)
        res=window_summary([game(1,t)],NOW)
        self.assertEqual(res["windows_currently_active"],1)
        self.assertIsNone(res["next_open"])

    def test_closing_is_exclusive(self):
        t=NOW+timedelta(hours=2)
        res=window_summary([game(1,t)],NOW)
        self.assertEqual(res["windows_currently_active"],0)
        self.assertIsNone(res["next_open"])

    def test_after_closing_even_future_fixture_not_actionable(self):
        t=NOW+timedelta(hours=1)
        res=window_summary([game(1,t)],NOW)
        self.assertEqual(res["scheduled_future"],1)
        self.assertIsNone(res["next_open"])
        self.assertEqual(res["windows_currently_active"],0)

    def test_exclude_postponed_cancelled_completed(self):
        rows=[game(1,NOW+timedelta(days=9),"PST"),
              game(2,NOW+timedelta(days=11),"CANC"),
              game(3,NOW+timedelta(days=10),"FT",[1,0])]
        self.assertEqual(window_summary(rows,NOW)["scheduled_future"],0)

    def test_next_open_earliest_when_sorted_unsorted_games(self):
        t1=NOW+timedelta(days=14)
        t2=NOW+timedelta(days=9)
        res=window_summary([game(1,t1),game(2,t2)],NOW)
        self.assertEqual(res["next_open"],t2-timedelta(days=8))

    def test_active_and_future_counts_are_disjoint(self):
        res=window_summary([game(1,NOW+timedelta(days=4)),
                            game(2,NOW+timedelta(days=11))],NOW)
        self.assertEqual(res["windows_currently_active"],1)
        self.assertEqual(res["windows_to_open_later"],1)

    def test_timezone_dst_winter_in_poland(self):
        text=display_time(datetime(2026,11,13,18,30,tzinfo=timezone.utc))
        self.assertIn("19:30 CET",text)

    def test_timezone_dst_summer_in_poland(self):
        text=display_time(datetime(2026,9,13,18,30,tzinfo=timezone.utc))
        self.assertIn("20:30 CEST",text)

    def test_none_is_not_fake_scheduled_date(self):
        self.assertEqual(display_time(None),"BRAK")

    def test_naive_now_rejected(self):
        with self.assertRaises(ValueError):
            window_summary([],datetime(2026,11,11,12,0))

    def test_finished_match_cannot_create_window(self):
        kickoff=NOW+timedelta(days=9)
        result=window_summary([game(1,kickoff,"FT",[3,0])],NOW)
        self.assertIsNone(result["next_open"])

    def test_no_predictions_created_by_window_summary(self):
        rows=[game(1,NOW+timedelta(days=10))]
        original=[dict(x) for x in rows]
        res=window_summary(rows,NOW)
        self.assertEqual(rows,original)
        self.assertNotIn("probabilities",res)


if __name__=="__main__":
    unittest.main()
