"""Offline tests for UCL second-stage fixture audit. No network or predictions."""
from datetime import datetime, timedelta, timezone
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import ucl_deep_audit as audit


NOW = datetime(2026, 11, 10, 11, tzinfo=timezone.utc)


def match(ident, kickoff, home=101, away=202, finished=True, score=True):
    result = [{"resultTypeID": 2, "pointsTeam1": 2, "pointsTeam2": 1}] if score else []
    return {
        "matchID": ident, "matchDateTimeUTC": kickoff.isoformat(),
        "matchIsFinished": finished,
        "team1": {"teamId": home, "teamName": "Dom"},
        "team2": {"teamId": away, "teamName": "Wyjazd"},
        "group": {"groupName": "Liga"},
        "matchResults": result,
    }


def season_data(year):
    if year < 2026:
        start = datetime(year, 9, 1, tzinfo=timezone.utc)
        return [match(year * 1000 + i, start + timedelta(days=i),
                      home=101 + i % 25, away=201 + i % 25)
                for i in range(100)]
    past = [match(year * 1000 + i, datetime(2026, 8, 1, tzinfo=timezone.utc) +
                  timedelta(days=i), home=101 + i % 25, away=201 + i % 25)
            for i in range(40)]
    future = [match(year * 1000 + 100 + i,
                    NOW + timedelta(days=i + 5), home=101 + i % 25,
                    away=201 + i % 25, finished=False, score=False)
              for i in range(55)]
    return past + future


class UclDeepAuditTests(unittest.TestCase):
    def test_three_seasons_clean_candidate_is_not_admitted(self):
        blocks = [audit.inspect_season(season_data(y), y, NOW)
                  for y in (2024, 2025, 2026)]
        self.assertEqual(blocks[0]["finished_with_score"], 100)
        self.assertEqual(blocks[1]["finished_with_score"], 100)
        self.assertEqual(blocks[2]["future_scheduled"], 55)
        self.assertEqual(audit.decide(blocks), ("DO RĘCZNEGO SPRAWDZENIA", []))

    def test_duplicate_id_and_repeated_pair_date_are_flagged(self):
        data = season_data(2025)
        duplicate = dict(data[0])
        duplicate["matchID"] = data[0]["matchID"]
        data.append(duplicate)
        block = audit.inspect_season(data, 2025, NOW)
        self.assertEqual(block["duplicate_match_ids"], 1)
        self.assertEqual(block["duplicate_pair_same_day"], 1)

    def test_missing_score_after_48_hours_is_flagged(self):
        data = season_data(2026)
        old = match(999999, NOW - timedelta(hours=49),
                    finished=False, score=False)
        data.append(old)
        block = audit.inspect_season(data, 2026, NOW)
        self.assertEqual(block["overdue_48h_missing_score"], 1)

    def test_future_result_and_out_of_season_are_flagged(self):
        data = season_data(2026)
        data.append(match(999998, NOW + timedelta(days=5),
                          home=102, away=203, finished=True))
        data.append(match(999997, datetime(2026, 5, 1, tzinfo=timezone.utc),
                          home=103, away=204, finished=True))
        block = audit.inspect_season(data, 2026, NOW)
        self.assertEqual(block["future_but_marked_finished"], 1)
        self.assertEqual(block["matches_outside_july_june_season"], 1)

    def test_missing_group_is_only_info_not_false_failure(self):
        data = season_data(2025)
        data[0].pop("group")
        block = audit.inspect_season(data, 2025, NOW)
        self.assertEqual(block["missing_group_name"], 1)
        self.assertEqual(block["malformed_matches"], 0)

    def test_cross_season_duplicate_id_is_flagged(self):
        blocks = [audit.inspect_season(season_data(y), y, NOW)
                  for y in (2024, 2025, 2026)]
        blocks[1]["all_match_ids"].append(blocks[0]["all_match_ids"][0])
        status, issues = audit.decide(blocks)
        self.assertEqual(status, "WYMAGA WYJAŚNIENIA")
        self.assertTrue(any("występuje w sezonach" in reason for reason in issues))

    def test_error_is_never_a_clean_pass(self):
        blocks = [
            {"season": 2024, "error": "HTTPError"},
            audit.inspect_season(season_data(2025), 2025, NOW),
            audit.inspect_season(season_data(2026), 2026, NOW),
        ]
        status, issues = audit.decide(blocks)
        self.assertEqual(status, "WYMAGA WYJAŚNIENIA")
        self.assertTrue(any("API" in issue for issue in issues))

    def test_report_is_readonly_and_uses_mocked_source(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(audit, "get_matches",
                              side_effect=lambda code, yr: season_data(yr)) as fetch:
                result = audit.run(now=NOW, output=Path(folder))
            self.assertEqual(fetch.call_count, 3)
            self.assertEqual([c.args for c in fetch.call_args_list],
                             [("ucl", 2024), ("ucl", 2025), ("ucl", 2026)])
            self.assertFalse(result["automatic_admission"])
            self.assertFalse(result["models_changed"])
            self.assertNotIn("all_match_ids", result["seasons"][0])
            self.assertTrue((Path(folder) / "UCL_AUDYT.md").is_file())
            document = json.loads((Path(folder) / "UCL_AUDYT.json").read_text())
            self.assertEqual(document["status"], "DO RĘCZNEGO SPRAWDZENIA")
        script = (Path(__file__).resolve().parents[1] / "ucl_deep_audit.py").read_text()
        self.assertNotIn("git push", script)
        self.assertNotIn("predictions.json", script)
        self.assertNotIn("forecast_engine", script)


if __name__ == "__main__":
    unittest.main()
