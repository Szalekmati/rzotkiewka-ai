"""Offline tests for candidate league discovery. No network or model changes."""
from datetime import datetime, timedelta, timezone
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import league_candidates as audit


NOW = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)


def fixture(match_id, when, *, finished=False, result=True):
    return {
        "matchID": match_id,
        "matchDateTimeUTC": when.isoformat(),
        "matchIsFinished": finished,
        "team1": {"teamId": 101, "teamName": "Home"},
        "team2": {"teamId": 202, "teamName": "Away"},
        "matchResults": ([{"resultTypeID": 2, "pointsTeam1": 1, "pointsTeam2": 0}]
                         if finished and result else []),
    }


def history():
    return [fixture(i + 1, NOW - timedelta(days=200 + i), finished=True) for i in range(100)]


def current():
    return (
        [fixture(i + 200, NOW - timedelta(days=i + 1), finished=True) for i in range(50)] +
        [fixture(i + 300, NOW + timedelta(days=i + 1)) for i in range(50)]
    )


class LeagueCandidateAuditTests(unittest.TestCase):
    def test_candidates_are_only_proposals(self):
        self.assertEqual(set(audit.CANDIDATES), {"pl", "la1", "ucl"})
        script = (Path(__file__).resolve().parents[1] / "league_candidates.py").read_text()
        self.assertNotIn("forecast_engine", script)
        self.assertNotIn("predictions.json", script.split("def get_matches(", 1)[1].split("def run(", 1)[0])
        self.assertIn('"automatic_promotion": False', script)

    def test_match_normalization_and_final_score(self):
        item = audit.normalize(fixture(1, NOW - timedelta(days=2), finished=True))
        self.assertEqual(item["score"], [1, 0])
        self.assertEqual(item["kickoff"].tzinfo, timezone.utc)
        self.assertIsNone(audit.normalize(fixture(True, NOW)))
        broken = fixture(2, NOW)
        broken["team2"]["teamId"] = broken["team1"]["teamId"]
        self.assertIsNone(audit.normalize(broken))
        broken = fixture(3, NOW)
        broken["matchDateTimeUTC"] = "bad-time"
        self.assertIsNone(audit.normalize(broken))

    def test_utc_kickoff_must_be_explicit_and_never_guessed(self):
        # The provider also exposes a local matchDateTime field; neither a
        # naive datetime nor date-only data can be silently interpreted as UTC.
        for value in (
            "2026-11-13T18:30:00",
            "2026-11-13 18:30:00",
            "2026-11-13",
            "2026-11-13T18:30:00 ",
            "2026-11-13T18:30:00Z ",
            "",
        ):
            with self.subTest(utc=value):
                row = fixture(20, NOW + timedelta(days=3))
                row["matchDateTimeUTC"] = value
                self.assertIsNone(audit.normalize(row))
        row = fixture(21, NOW + timedelta(days=3))
        row["matchDateTimeUTC"] = "2026-11-13T18:30:00+01:00"
        parsed = audit.normalize(row)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["kickoff"].isoformat(), "2026-11-13T17:30:00+00:00")
        row["matchDateTimeUTC"] = "2026-11-13T17:30:00Z"
        self.assertEqual(audit.normalize(row)["kickoff"], parsed["kickoff"])
        row["matchDateTimeUTC"] = "2026-11-13T17:30:00.125Z"
        self.assertEqual(audit.normalize(row)["kickoff"].microsecond, 125000)
        # Invalid datetime is reported as an incomplete candidate, not
        # quietly accepted as if the provider supplied valid UTC.
        broken = [fixture(i + 1, NOW - timedelta(days=i + 1), finished=True)
                  for i in range(100)]
        broken[1]["matchDateTimeUTC"] = "2026-11-10T18:30:00"
        report = audit.assess(broken, NOW)
        self.assertEqual(report["valid"], 99)
        self.assertEqual(report["valid_fraction"], 0.99)
        self.assertIsNone(audit.normalize({"matchDateTimeUTC": None}))

    def test_finished_requires_accepted_final_result(self):
        item = audit.normalize(fixture(1, NOW - timedelta(days=1), finished=True, result=False))
        self.assertTrue(item["finished_flag"])
        self.assertIsNone(item["score"])
        summary = audit.assess([fixture(1, NOW - timedelta(days=1), finished=True, result=False)], NOW)
        self.assertEqual(summary["finished_without_accepted_score"], 1)

    def test_missing_score_diagnostic_distinguishes_provider_fields(self):
        when = NOW - timedelta(hours=60)
        rows = []
        empty_unfinished = fixture(110, when)
        rows.append(empty_unfinished)  # scheduled/unfinished + no score

        final_but_open = fixture(111, when)
        final_but_open["matchResults"] = [
            {"resultTypeID": 2, "pointsTeam1": 2, "pointsTeam2": 0}]
        rows.append(final_but_open)  # final present, end flag still False

        finished_empty = fixture(112, when, finished=True, result=False)
        rows.append(finished_empty)

        finished_no_list = fixture(113, when, finished=True)
        finished_no_list["matchResults"] = None
        rows.append(finished_no_list)

        finished_halftime_only = fixture(114, when, finished=True)
        finished_halftime_only["matchResults"] = [
            {"resultTypeID": 1, "pointsTeam1": 1, "pointsTeam2": 0}]
        rows.append(finished_halftime_only)

        finished_bad_points = fixture(115, when, finished=True)
        finished_bad_points["matchResults"] = [
            {"resultTypeID": 2, "pointsTeam1": "2", "pointsTeam2": 0}]
        rows.append(finished_bad_points)

        expected = {
            "not_marked_finished_no_final": 1,
            "not_marked_finished_with_final": 1,
            "marked_finished_empty_result_list": 1,
            "marked_finished_invalid_result_list": 1,
            "marked_finished_no_final_result": 1,
            "marked_finished_invalid_final_points": 1,
        }
        summary = audit.assess(rows, NOW)
        self.assertEqual(summary["overdue_without_result_48h"], 6)
        self.assertEqual(summary["overdue_cause_counts"], expected)
        self.assertEqual(len(summary["overdue_without_result_samples"]), 6)
        self.assertEqual([x["match_id"] for x in summary["overdue_without_result_samples"]],
                         [110, 111, 112, 113, 114, 115])
        self.assertEqual(summary["finished_with_score"], 0)
        sample = summary["overdue_without_result_samples"][1]
        self.assertEqual(sample["home"], "Home")
        self.assertEqual(sample["away"], "Away")
        self.assertEqual(sample["cause"], "not_marked_finished_with_final")
        self.assertFalse(sample["finished_flag"])

        valid = fixture(116, when, finished=True)
        self.assertIsNone(audit.normalize(valid)["missing_score_reason"])
        self.assertEqual(audit.assess([valid], NOW)["overdue_cause_counts"], {})

    def test_team_labels_escaped_in_markdown_without_corrupting_letters(self):
        example = fixture(121, NOW - timedelta(days=3))
        example["team1"]["teamName"] = "Northern|Rangers [A]\\n<b>Club</b>"
        team = audit.normalize(example)
        self.assertIsNotNone(team)
        self.assertEqual(team["home"], "Northern Rangers  A b Club /b")
        self.assertEqual(team["away"], "Away")

    def test_overdue_without_result_uses_48_hour_grace_period(self):
        rows = [
            fixture(10, NOW - timedelta(hours=49), finished=False),
            fixture(11, NOW - timedelta(hours=48), finished=False),
            fixture(12, NOW - timedelta(hours=47), finished=False),
            fixture(13, NOW - timedelta(hours=50), finished=True, result=False),
        ]
        counts = audit.assess(rows, NOW)
        self.assertEqual(counts["overdue_without_result_48h"], 3)  # 48 h włącznie
        self.assertEqual([r["match_id"] for r in counts["overdue_without_result_samples"]],
                         [13, 10, 11])
        self.assertEqual(
            counts["overdue_without_result_samples"][0]["kickoff_utc"],
            (NOW - timedelta(hours=50)).isoformat())
        self.assertEqual(counts["finished_without_accepted_score"], 1)

        past, present = audit.assess(history(), NOW), audit.assess(current(), NOW)
        present["overdue_without_result_48h"] = 1
        decision, reasons = audit.verdict(past, present)
        self.assertEqual(decision, "DANE NIEWYSTARCZAJĄCE")
        self.assertTrue(any("Zaległe mecze" in item for item in reasons))

    def test_overdue_evidence_is_sorted_bounded_and_not_model_input(self):
        # Eleven overdue records with IDs deliberately out of order.
        rows = [fixture(50 - i, NOW - timedelta(days=3+i), finished=False)
                for i in range(11)]
        report = audit.assess(rows, NOW)
        self.assertEqual(report["overdue_without_result_48h"], 11)
        self.assertEqual(len(report["overdue_without_result_samples"]), 10)
        self.assertEqual(report["overdue_without_result_samples"][0]["match_id"], 40)
        self.assertNotIn("probabilities", report["overdue_without_result_samples"][0])
        self.assertEqual(audit.assess([], NOW)["overdue_without_result_samples"], [])

    def test_good_coverage_requires_manual_review_not_automatic_promotion(self):
        past, present = audit.assess(history(), NOW), audit.assess(current(), NOW)
        self.assertEqual(past["finished_with_score"], 100)
        self.assertEqual(present["future_with_kickoff"], 50)
        self.assertEqual(present["finished_with_score"], 50)
        self.assertEqual(audit.verdict(past, present), ("DO RĘCZNEJ OCENY", []))

    def test_duplicates_and_incomplete_data_fail_quality_gate(self):
        past, present = audit.assess(history(), NOW), audit.assess(current(), NOW)
        repeated = current()
        repeated[1]["matchID"] = repeated[0]["matchID"]
        dup = audit.assess(repeated, NOW)
        self.assertEqual(dup["duplicate_ids"], 1)
        self.assertEqual(audit.verdict(past, dup)[0], "DANE NIEWYSTARCZAJĄCE")
        missing = audit.assess([fixture(4, NOW + timedelta(days=1))], NOW)
        self.assertEqual(audit.verdict(past, missing)[0], "DANE NIEWYSTARCZAJĄCE")

    def test_api_failure_not_silently_accepted(self):
        past = audit.assess(history(), NOW)
        verdict, reasons = audit.verdict(past, {"error": "timeout", "season": 2026})
        self.assertEqual(verdict, "DANE NIEWYSTARCZAJĄCE")
        self.assertTrue(any("API" in reason for reason in reasons))

    def test_run_writes_reports_without_touching_production_files(self):
        def fake_fetch(code, season):
            self.assertIn(code, audit.CANDIDATES)
            return history() if season == 2025 else current()
        with tempfile.TemporaryDirectory() as directory, patch.object(audit, "get_matches", fake_fetch):
            result = audit.run(NOW, Path(directory))
            self.assertEqual(len(result["candidates"]), 3)
            self.assertFalse(result["automatic_promotion"])
            self.assertTrue(all(item["decision"] == "DO RĘCZNEJ OCENY"
                                for item in result["candidates"]))
            self.assertTrue((Path(directory) / "RAPORT_LIG.md").exists())
            data = json.loads((Path(directory) / "wyniki_lig.json").read_text())
            self.assertEqual(data["kind"], "read_only_league_candidate_audit")
            text = (Path(directory) / "RAPORT_LIG.md").read_text(encoding="utf-8")
            self.assertIn("Historia: mecze | Historia: wyniki", text)
            self.assertIn("100 | 100 | 100 | 50 | 50 |", text)
            self.assertNotIn("Zaległe spotkania sezonu", text)

    def test_empty_historical_league_lists_manual_discovery_without_guessing(self):
        def fake_fetch(code, season):
            return [] if season == 2025 else current()
        with tempfile.TemporaryDirectory() as directory, patch.object(audit, "get_matches", fake_fetch):
            result = audit.run(NOW, Path(directory))
            self.assertTrue(all(row["decision"] == "DANE NIEWYSTARCZAJĄCE"
                                for row in result["candidates"]))
            report = (Path(directory) / "RAPORT_LIG.md").read_text(encoding="utf-8")
            self.assertIn("https://api.openligadb.de/getavailableleagues/2025", report)
            self.assertIn("Pusta lista meczów nie dowodzi", report)
            self.assertFalse(result["automatic_promotion"])

    def test_run_report_lists_overdue_ids_and_counts_without_auto_accept(self):
        def fake_fetch(code, season):
            if season == 2025:
                return history()
            rows = current()
            rows[2]["matchResults"] = []
            return rows
        with tempfile.TemporaryDirectory() as directory, patch.object(audit, "get_matches", fake_fetch):
            result = audit.run(NOW, Path(directory))
            self.assertFalse(result["automatic_promotion"])
            self.assertTrue(all(row["decision"] == "DANE NIEWYSTARCZAJĄCE"
                                for row in result["candidates"]))
            report = (Path(directory) / "RAPORT_LIG.md").read_text(encoding="utf-8")
            self.assertIn("Zaległe spotkania sezonu 2026", report)
            self.assertIn("próbka do 10 z 1", report)
            self.assertIn("#202 — ", report)
            self.assertIn("Home / Away — Flaga zakończenia jest, lista wyników pusta (marked_finished_empty_result_list)", report)
            self.assertIn("Przyczyny według pól źródła", report)
            self.assertIn("marked_finished_empty_result_list=1", report)
            json_report = json.loads((Path(directory) / "wyniki_lig.json").read_text())
            self.assertEqual(json_report["candidates"][0]["current"]
                             ["overdue_without_result_samples"][0]["match_id"], 202)
            self.assertEqual(json_report["candidates"][0]["current"]
                             ["overdue_cause_counts"]["marked_finished_empty_result_list"], 1)


if __name__ == "__main__":
    unittest.main()
