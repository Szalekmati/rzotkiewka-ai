"""Offline contract tests for the fail-closed club identity release gate."""
import copy
from datetime import date
import json
from pathlib import Path
import unittest

from club_identity_release_gate import inspect, DEFAULT_REGISTRY


class ReleaseGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))

    def registry(self):
        return copy.deepcopy(self.reference)

    def test_current_report_is_valid_but_production_blocked(self):
        r = inspect(self.registry())
        self.assertEqual(r["checked_competitions"], 2)
        self.assertEqual(r["name_supported_alias_candidates"], 17)
        self.assertEqual(r["independently_verified_id_links"], 0)
        self.assertFalse(r["production_release_allowed"])
        self.assertGreaterEqual(len(r["blocked_reasons"]), 3)

    def test_duplicate_competition_fails(self):
        r = self.registry()
        r["competitions"].append(copy.deepcopy(r["competitions"][0]))
        with self.assertRaises(ValueError):
            inspect(r)

    def test_bad_count_and_bool_as_int_rejected(self):
        r = self.registry()
        r["competitions"][0]["name_supported_by_official_roster"] = 7
        with self.assertRaises(ValueError):
            inspect(r)
        r = self.registry()
        r["competitions"][0]["mapped_inside_api_to_unique_id"] = True
        with self.assertRaises(ValueError):
            inspect(r)

    def test_unsubstantiated_id_counter_rejected(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 1
        with self.assertRaises(ValueError):
            inspect(r)

    def test_release_request_without_evidence_rejected(self):
        r = self.registry()
        r["release"]["requested"] = True
        with self.assertRaises(ValueError):
            inspect(r)

    def test_false_rights_approval_without_document_fails(self):
        r = self.registry()
        r["release"]["rights_review_approved"] = True
        with self.assertRaises(ValueError):
            inspect(r)

    def test_invalid_url_is_rejected(self):
        r = self.registry()
        r["competitions"][0]["official_roster_url"] = "http://localhost"
        with self.assertRaises(ValueError):
            inspect(r)

    def test_independent_proof_cannot_come_from_api_provider(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 1
        r["reviewed_identity_links"] = [{
            "league_id": 39, "season": 2026, "source_team_name": "Sample FC",
            "official_club_name": "Sample", "provider_team_id": 10001,
            "independent_identity_url": "https://v3.football.api-sports.io/teams?id=10001",
            "reviewed_by": "reviewer", "reviewed_on": "2026-11-11"
        }]
        with self.assertRaises(ValueError):
            inspect(r)

    def test_duplicate_provider_id_across_clubs_fails(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 2
        template = {
            "league_id": 39, "season": 2026, "source_team_name": "Sample A",
            "official_club_name": "Sample A", "provider_team_id": 10001,
            "independent_identity_url": "https://www.premierleague.com/en/clubs",
            "reviewed_by": "reviewer", "reviewed_on": "2026-11-11"
        }
        other = copy.deepcopy(template)
        other["source_team_name"] = "Sample B"
        other["official_club_name"] = "Sample B"
        r["reviewed_identity_links"] = [template, other]
        with self.assertRaises(ValueError):
            inspect(r)

    def test_manual_review_entry_is_not_automatic_production_approval(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 1
        r["reviewed_identity_links"] = [{
            "league_id": 39, "season": 2026, "source_team_name": "Example FC",
            "official_club_name": "Example", "provider_team_id": 123456,
            "independent_identity_url": "https://www.premierleague.com/en/clubs",
            "reviewed_by": "human reviewer", "reviewed_on": "2026-11-11"
        }]
        result = inspect(r)
        self.assertEqual(result["independently_verified_id_links"], 1)
        self.assertFalse(result["production_release_allowed"])

    def test_future_dated_review_is_not_valid(self):
        r = self.registry()
        r["review_date"] = "2026-11-42"
        with self.assertRaises(ValueError):
            inspect(r)

    def test_all_evidence_flags_cannot_override_final_release_gate(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 1
        r["reviewed_identity_links"] = [{
            "league_id": 39, "season": 2026, "source_team_name": "Example FC",
            "official_club_name": "Example", "provider_team_id": 123456,
            "independent_identity_url": "https://www.premierleague.com/en/clubs",
            "reviewed_by": "human reviewer", "reviewed_on": "2026-11-11"
        }]
        release = r["release"]
        release.update({
            "requested": True, "rights_review_approved": True,
            "rights_review_document_url": "https://example.com/licence-review",
            "forward_time_model_test_approved": True,
            "forward_time_test_report_url": "https://example.com/forward-test",
            "authorized_by": "human reviewer", "authorized_on": "2026-11-11",
            "decision_url": "https://example.com/release-decision",
        })
        result = inspect(r)
        self.assertFalse(result["production_release_allowed"])


if __name__ == "__main__":
    unittest.main()
