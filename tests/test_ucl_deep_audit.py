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


def reference_2024_season():
    # Simulated history exercises the checker; real data is independently
    # fetched from OpenLigaDB by GitHub Actions.
    rows = season_data(2024)
    for i in range(89):
        rows.append(match(2024900 + i, datetime(2025, 4, 1, tzinfo=timezone.utc) +
                          timedelta(days=i % 30), home=301 + i % 18,
                          away=401 + i % 18))
    official_names = {
        "real madrid": "Real Madrid CF",
        "stuttgart": "VfB Stuttgart",
        "manchester city": "Manchester City FC",
        "inter": "FC Internazionale Milano",
        "arsenal": "Arsenal FC",
        "paris": "Paris Saint-Germain",
        "bayern": "FC Bayern München",
    }
    for i, spec in enumerate(audit.UEFA_2024_SPOTCHECKS):
        row = match(990000 + i, datetime.fromisoformat(spec["date"] + "T20:00:00+00:00"),
                    home=9000 + 2*i, away=9001 + 2*i)
        row["team1"]["teamName"] = official_names[spec["home"]]
        row["team2"]["teamName"] = official_names[spec["away"]]
        row["matchResults"] = [{"resultTypeID": 2, "pointsTeam1": spec["score"][0],
                                "pointsTeam2": spec["score"][1]}]
        rows[i] = row
    return rows


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
        blocks = [audit.inspect_season(reference_2024_season() if y == 2024 else season_data(y), y, NOW)
                  for y in (2024, 2025, 2026)]
        blocks[0]["uefa_2024_reference"] = audit.uefa_2024_reference_check(reference_2024_season())
        blocks[0]["uefa_2024_spotchecks"] = audit.uefa_2024_match_spotchecks(reference_2024_season())
        self.assertEqual(blocks[0]["finished_with_score"], 189)
        self.assertEqual(blocks[1]["finished_with_score"], 100)
        self.assertEqual(blocks[2]["future_scheduled"], 55)
        self.assertEqual(audit.decide(blocks), ("DO RĘCZNEGO SPRAWDZENIA", []))

    def test_official_uefa_reference_requires_count_and_final_result(self):
        full = reference_2024_season()
        self.assertEqual(len(full), 189)
        reference = audit.uefa_2024_reference_check(full)
        self.assertTrue(reference["count_matches_uefa"])
        self.assertTrue(reference["uefa_final_paris_inter_5_0_found"])
        reference = audit.uefa_2024_reference_check([r for r in full if r["matchDateTimeUTC"][:10] != "2025-05-31"])
        self.assertFalse(reference["count_matches_uefa"])
        self.assertFalse(reference["uefa_final_paris_inter_5_0_found"])

    def test_eight_uefa_spotchecks_and_discrepancies(self):
        full = reference_2024_season()
        result = audit.uefa_2024_match_spotchecks(full)
        self.assertEqual(result["checked"], 8)
        self.assertEqual(result["passed"], 8)
        self.assertTrue(result["all_passed"])
        self.assertEqual([r["outcome"] for r in result["matches"]], ["ZGODNY"]*8)
        self.assertTrue(audit.team_matches("Paris Saint-Germain", "paris"))
        self.assertTrue(audit.team_matches("FC Internazionale Milano", "inter"))

        missing = audit.uefa_2024_match_spotchecks(full[1:])
        self.assertFalse(missing["all_passed"])
        self.assertEqual(missing["matches"][0]["outcome"], "BRAK MECZU")

        wrong_result = [dict(row) for row in full]
        wrong_result[0]["matchResults"] = [
            {"resultTypeID": 2, "pointsTeam1": 0, "pointsTeam2": 3}]
        result = audit.uefa_2024_match_spotchecks(wrong_result)
        self.assertEqual(result["matches"][0]["outcome"], "NIEZGODNY WYNIK")
        self.assertFalse(result["all_passed"])

        duplicated = full + [dict(full[0], matchID=888888)]
        result = audit.uefa_2024_match_spotchecks(duplicated)
        self.assertEqual(result["matches"][0]["outcome"], "NIEJEDNOZNACZNY")
        self.assertFalse(result["all_passed"])

    def test_wrong_home_away_is_not_silently_accepted(self):
        full = reference_2024_season()
        changed = [dict(row) for row in full]
        changed[0]["team1"], changed[0]["team2"] = changed[0]["team2"], changed[0]["team1"]
        result = audit.uefa_2024_match_spotchecks(changed)
        self.assertEqual(result["matches"][0]["outcome"], "BRAK MECZU")

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
        def fixture_fetch(code, yr):
            if code == "ucl" and yr == 2024:
                return []
            if code == "ucl24" and yr == 2024:
                return reference_2024_season()
            return season_data(yr)
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(audit, "get_matches", side_effect=fixture_fetch) as fetch:
                result = audit.run(now=NOW, output=Path(folder))
            self.assertEqual(fetch.call_count, 4)
            self.assertEqual([c.args for c in fetch.call_args_list],
                             [("ucl", 2024), ("ucl24", 2024), ("ucl", 2025), ("ucl", 2026)])
            self.assertEqual(result["seasons"][0]["source_shortcut"], "ucl24")
            self.assertTrue(result["seasons"][0]["uefa_2024_reference"]["count_matches_uefa"])
            self.assertEqual(result["seasons"][0]["uefa_2024_spotchecks"]["passed"], 8)
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
