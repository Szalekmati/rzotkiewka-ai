"""Offline tests of the read-only LAB overview; no API access or data writes."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "lab_status_readonly", ROOT / "lab_forward" / "status_readonly.py")
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)


def example():
    ledger = {
        "schema": 1,
        "forecasts": [
            {"id": "bl1-1", "snapshot": {
                "league": "bl1", "created_at": "2026-11-13T12:00:00Z",
                "fixture": {"kickoff": "2026-11-20T17:30:00Z"}}},
            {"id": "bl2-2", "snapshot": {
                "league": "bl2", "created_at": "2026-11-13T13:00:00Z",
                "fixture": {"kickoff": "2026-11-21T13:00:00Z"}}},
        ],
        "settlements": {
            "bl1-1": [{"observed_at": "2026-11-15T12:00:00Z",
                       "result": {"state": "pending"}}],
            "bl2-2": [{"observed_at": "2026-11-15T12:00:00Z",
                       "result": {"state": "pending"}}],
        },
    }
    experiment = {"config": {"review_after_settled_pairs": 300}}
    return ledger, experiment


class LabReadOnlyStatus(unittest.TestCase):
    def setUp(self):
        self.ledger, self.experiment = example()
        self.now = datetime(2026, 11, 15, tzinfo=timezone.utc)

    def audit(self):
        return lab.summary(self.ledger, self.experiment, now=self.now)

    def test_pending_pairs_do_not_generate_metrics(self):
        result = self.audit()
        self.assertEqual(result["pairs"], 2)
        self.assertEqual(result["states"], {"pending": 2})
        self.assertEqual(result["graded"], 0)
        self.assertEqual(result["remaining"], 300)
        self.assertEqual(result["by_league"], {"bl1": 1, "bl2": 1})
        text = lab.format_report(result)
        self.assertIn("2026-11-20 18:30 CET", text)
        self.assertNotIn("Trafnosc", text)
        self.assertNotIn("ROI:", text)

    def test_latest_observation_wins_even_if_history_is_unsorted(self):
        self.ledger["settlements"]["bl1-1"] = [
            {"observed_at": "2026-11-15T18:00:00Z",
             "result": {"state": "pending"}},
            {"observed_at": "2026-11-15T12:00:00Z",
             "result": {"state": "graded"}},
        ]
        self.assertEqual(self.audit()["graded"], 0)
        self.ledger["settlements"]["bl1-1"][0]["result"]["state"] = "graded"
        self.assertEqual(self.audit()["graded"], 1)
        self.assertEqual(self.audit()["remaining"], 299)

    def test_corrupt_or_unmatched_records_stop(self):
        self.ledger["forecasts"][1]["id"] = "bl1-1"
        with self.assertRaises(ValueError):
            self.audit()
        self.ledger, _ = example()
        self.ledger["settlements"]["unexpected"] = []
        with self.assertRaises(ValueError):
            self.audit()

    def test_missing_timezone_or_post_kickoff_forecast_stops(self):
        self.ledger["forecasts"][0]["snapshot"]["fixture"]["kickoff"] = "2026-11-20T17:30:00"
        with self.assertRaises(ValueError):
            self.audit()
        self.ledger, _ = example()
        self.ledger["forecasts"][0]["snapshot"]["created_at"] = "2026-11-20T18:00:00Z"
        with self.assertRaises(ValueError):
            self.audit()

    def test_invalid_threshold_and_missing_result_stop(self):
        self.experiment["config"]["review_after_settled_pairs"] = 0
        with self.assertRaises(ValueError):
            self.audit()
        self.experiment["config"]["review_after_settled_pairs"] = 300
        self.ledger["settlements"]["bl1-1"][0]["result"] = {}
        with self.assertRaises(ValueError):
            self.audit()

    def test_repository_ledger_is_readable_but_not_evidence_of_accuracy(self):
        import json
        ledger = json.loads((ROOT / "lab_forward/ledger.json").read_text(encoding="utf-8"))
        exp = json.loads((ROOT / "lab_forward/experiment.json").read_text(encoding="utf-8"))
        report = lab.summary(ledger, exp, now=self.now)
        self.assertGreaterEqual(report["pairs"], 1)
        self.assertEqual(report["threshold"], 300)
        self.assertEqual(sum(report["states"].values()), report["pairs"])


if __name__ == "__main__":
    unittest.main()
