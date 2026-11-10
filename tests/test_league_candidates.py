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

    def test_finished_requires_accepted_final_result(self):
        item = audit.normalize(fixture(1, NOW - timedelta(days=1), finished=True, result=False))
        self.assertTrue(item["finished_flag"])
        self.assertIsNone(item["score"])
        summary = audit.assess([fixture(1, NOW - timedelta(days=1), finished=True, result=False)], NOW)
        self.assertEqual(summary["finished_without_accepted_score"], 1)

    def test_overdue_without_result_uses_48_hour_grace_period(self):
        rows = [
            fixture(10, NOW - timedelta(hours=49), finished=False),
            fixture(11, NOW - timedelta(hours=48), finished=False),
            fixture(12, NOW - timedelta(hours=47), finished=False),
            fixture(13, NOW - timedelta(hours=50), finished=True, result=False),
        ]
        counts = audit.assess(rows, NOW)
        self.assertEqual(counts["overdue_without_result_48h"], 3)  # 48 h włącznie
        self.assertEqual(counts["finished_without_accepted_score"], 1)

        past, present = audit.assess(history(), NOW), audit.assess(current(), NOW)
        present["overdue_without_result_48h"] = 1
        decision, reasons = audit.verdict(past, present)
        self.assertEqual(decision, "DANE NIEWYSTARCZAJĄCE")
        self.assertTrue(any("Zaległe mecze" in item for item in reasons))

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


if __name__ == "__main__":
    unittest.main()
