"""Offline tests for a new-league API adapter; never call real provider."""
from datetime import datetime, timedelta, timezone
import unittest

from api_football_prematch_readiness import parse_fixtures, inspect_asof
from forecast_engine import MIN_LEAGUE, MIN_TEAM, SETTLE_HOURS

NOW = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)


def game(fid, dt, status="FT", home=1, away=2, goals=(1, 0),
         league=39, season=2026):
    return {
        "fixture": {"id": fid, "date": dt.isoformat(), "status": {"short": status}},
        "league": {"id": league, "season": season},
        "teams": {"home": {"id": home, "name": "Home FC"},
                  "away": {"id": away, "name": "Away FC"}},
        "goals": {"home": goals[0], "away": goals[1]},
    }


def response(items, pages=1):
    return {"results": len(items), "paging": {"current": 1, "total": pages},
            "response": items}


class ReadinessTests(unittest.TestCase):
    def test_valid_match_normalization(self):
        m = game(1, NOW - timedelta(days=2))
        rows, quality = parse_fixtures(response([m]), 39, 2026)
        self.assertEqual(rows[0]["home_id"], 1)
        self.assertEqual(rows[0]["score"], [1, 0])
        self.assertEqual(quality["incomplete_final"], 0)

    def test_bad_league_blocks(self):
        with self.assertRaises(ValueError):
            parse_fixtures(response([game(1, NOW, league=140)]), 39, 2026)

    def test_duplicate_fixture_id_blocks(self):
        a = game(1, NOW - timedelta(days=2))
        with self.assertRaises(ValueError):
            parse_fixtures(response([a, a]), 39, 2026)

    def test_pagination_blocks(self):
        with self.assertRaises(ValueError):
            parse_fixtures(response([game(1, NOW)], pages=2), 39, 2026)

    def test_invalid_date_or_team_ids_block(self):
        a = game(1, NOW)
        a["fixture"]["date"] = "2026-11-11T12:00:00"
        with self.assertRaises(ValueError):
            parse_fixtures(response([a]), 39, 2026)
        b = game(1, NOW, away=1)
        with self.assertRaises(ValueError):
            parse_fixtures(response([b]), 39, 2026)

    def test_completed_without_score_not_in_history(self):
        rows, qual = parse_fixtures(response([
            game(1, NOW - timedelta(days=3), goals=(None, None))
        ]), 39, 2026)
        self.assertEqual(qual["incomplete_final"], 1)
        self.assertEqual(inspect_asof(rows, NOW)["past_completed_settled"], 0)

    def test_live_or_postponed_never_becomes_finished_history(self):
        rows, qual = parse_fixtures(response([
            game(1, NOW - timedelta(days=3), status="PST"),
            game(2, NOW - timedelta(hours=1), status="1H", goals=(1, 1))
        ]), 39, 2026)
        self.assertEqual(qual["discarded_other_status"], 2)
        self.assertEqual(inspect_asof(rows, NOW)["past_completed_settled"], 0)

    def test_recent_match_is_excluded_by_settlement_window(self):
        rows, _ = parse_fixtures(response([
            game(1, NOW - timedelta(hours=SETTLE_HOURS-1)),
            game(2, NOW - timedelta(hours=SETTLE_HOURS+1))
        ]), 39, 2026)
        self.assertEqual(inspect_asof(rows, NOW)["past_completed_settled"], 1)

    def test_history_requirements_detected_on_future_fixture(self):
        past = [
            game(i+1, NOW - timedelta(days=20) + timedelta(hours=i))
            for i in range(max(MIN_LEAGUE, MIN_TEAM+1))
        ]
        upcoming = game(200, NOW + timedelta(days=2), status="NS", goals=(None, None))
        rows, _ = parse_fixtures(response(past + [upcoming]), 39, 2026)
        summary = inspect_asof(rows, NOW)
        self.assertEqual(summary["enough_history_in_window"], 1)
        self.assertEqual(summary["not_enough_history_in_window"], 0)
        self.assertEqual(summary["forecast_records_written"], 0)

    def test_not_enough_history_detected(self):
        rows, _ = parse_fixtures(response([
            game(1, NOW - timedelta(days=20)),
            game(200, NOW + timedelta(days=2), status="NS", goals=(None, None))
        ]), 39, 2026)
        summary = inspect_asof(rows, NOW)
        self.assertEqual(summary["possible_window"], 1)
        self.assertEqual(summary["not_enough_history_in_window"], 1)

    def test_future_completed_status_flagged_not_used(self):
        rows, _ = parse_fixtures(response([
            game(1, NOW + timedelta(hours=2), status="FT")
        ]), 39, 2026)
        summary = inspect_asof(rows, NOW)
        self.assertEqual(summary["finished_kickoff_after_snapshot"], 1)
        self.assertEqual(summary["past_completed_settled"], 0)

    def test_no_scheduled_match_means_no_readiness_claim(self):
        rows, _ = parse_fixtures(response([]), 39, 2026)
        summary = inspect_asof(rows, NOW)
        self.assertEqual(summary["possible_window"], 0)
        self.assertEqual(summary["enough_history_in_window"], 0)


if __name__ == "__main__":
    unittest.main()
