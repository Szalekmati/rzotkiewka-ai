"""Offline contract tests for the fail-closed club identity release gate."""
import copy
from datetime import date
import json
from pathlib import Path
import unittest

from club_identity_release_gate import inspect, DEFAULT_REGISTRY
from api_football_official_roster import OFFICIAL


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
        self.assertEqual(r["submitted_identity_link_entries"], 0)
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
            "official_club_name": "Arsenal", "provider_team_id": 10001,
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
            "official_club_name": "Arsenal", "provider_team_id": 10001,
            "independent_identity_url": "https://example.org/clubs/arsenal",
            "reviewed_by": "reviewer", "reviewed_on": "2026-11-11"
        }
        other = copy.deepcopy(template)
        other["source_team_name"] = "Sample B"
        other["official_club_name"] = "Chelsea"
        r["reviewed_identity_links"] = [template, other]
        with self.assertRaises(ValueError):
            inspect(r)

    def test_manual_review_entry_is_not_automatic_production_approval(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 1
        r["reviewed_identity_links"] = [{
            "league_id": 39, "season": 2026, "source_team_name": "Example FC",
            "official_club_name": "Arsenal", "provider_team_id": 123456,
            "independent_identity_url": "https://example.org/clubs/arsenal",
            "reviewed_by": "human reviewer", "reviewed_on": "2026-11-11"
        }]
        result = inspect(r)
        self.assertEqual(result["submitted_identity_link_entries"], 1)
        self.assertEqual(result["independently_verified_id_links"], 0)
        self.assertTrue(any("wpisy ID sa deklaracjami" in x for x in result["blocked_reasons"]))
        self.assertFalse(result["production_release_allowed"])

    def test_unknown_official_club_is_rejected(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 1
        r["reviewed_identity_links"] = [{
            "league_id": 39, "season": 2026, "source_team_name": "Fake FC",
            "official_club_name": "Fictional Town", "provider_team_id": 999123,
            "independent_identity_url": "https://example.org/clubs/arsenal",
            "reviewed_by": "reviewer", "reviewed_on": "2026-11-11"
        }]
        with self.assertRaises(ValueError):
            inspect(r)

    def test_club_from_other_league_is_rejected(self):
        r = self.registry()
        r["competitions"][1]["independently_reviewed_club_ids"] = 1
        r["reviewed_identity_links"] = [{
            "league_id": 140, "season": 2026, "source_team_name": "Arsenal",
            "official_club_name": "Arsenal", "provider_team_id": 123456,
            "independent_identity_url": "https://example.org/clubs/arsenal",
            "reviewed_by": "reviewer", "reviewed_on": "2026-11-11"
        }]
        with self.assertRaises(ValueError):
            inspect(r)

    def test_one_official_club_cannot_have_two_provider_ids(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 2
        r["reviewed_identity_links"] = [
            {"league_id": 39, "season": 2026, "source_team_name": "Arsenal",
             "official_club_name": "Arsenal", "provider_team_id": 101,
             "independent_identity_url": "https://example.org/clubs/arsenal",
             "reviewed_by": "reviewer", "reviewed_on": "2026-11-11"},
            {"league_id": 39, "season": 2026, "source_team_name": "Arsenal London",
             "official_club_name": "Arsenal", "provider_team_id": 102,
             "independent_identity_url": "https://example.org/clubs/arsenal",
             "reviewed_by": "reviewer", "reviewed_on": "2026-11-11"},
        ]
        with self.assertRaises(ValueError):
            inspect(r)

    def test_wrong_season_official_roster_is_rejected(self):
        r = self.registry()
        r["competitions"][0]["season"] = 2027
        with self.assertRaises(ValueError):
            inspect(r)

    def test_wrong_official_roster_url_is_rejected(self):
        r = self.registry()
        r["competitions"][0]["official_roster_url"] = "https://example.com/other-league"
        with self.assertRaises(ValueError):
            inspect(r)

    def test_generic_official_club_directory_is_not_identity_evidence(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 1
        r["reviewed_identity_links"] = [{
            "league_id": 39, "season": 2026,
            "source_team_name": "Arsenal", "official_club_name": "Arsenal",
            "provider_team_id": 101,
            "independent_identity_url": "https://www.premierleague.com/en/clubs",
            "reviewed_by": "synthetic", "reviewed_on": "2026-11-11"
        }]
        with self.assertRaises(ValueError):
            inspect(r)

    def test_generic_laliga_club_directory_is_not_identity_evidence(self):
        r = self.registry()
        r["competitions"][1]["independently_reviewed_club_ids"] = 1
        r["reviewed_identity_links"] = [{
            "league_id": 140, "season": 2026,
            "source_team_name": "FC Barcelona", "official_club_name": "FC Barcelona",
            "provider_team_id": 101,
            "independent_identity_url": "https://www.laliga.com/en-US/laliga-easports/clubs",
            "reviewed_by": "synthetic", "reviewed_on": "2026-11-11"
        }]
        with self.assertRaises(ValueError):
            inspect(r)

    def test_official_roster_overview_is_not_identity_evidence(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 1
        r["reviewed_identity_links"] = [{
            "league_id": 39, "season": 2026,
            "source_team_name": "Arsenal", "official_club_name": "Arsenal",
            "provider_team_id": 101,
            "independent_identity_url": r["competitions"][0]["official_roster_url"],
            "reviewed_by": "synthetic", "reviewed_on": "2026-11-11"
        }]
        with self.assertRaises(ValueError):
            inspect(r)

    def test_future_dated_review_is_not_valid(self):
        r = self.registry()
        r["review_date"] = "2026-11-42"
        with self.assertRaises(ValueError):
            inspect(r)

    def test_partial_id_reviews_explicitly_report_incomplete_coverage(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 1
        r["reviewed_identity_links"] = [{
            "league_id": 39, "season": 2026, "source_team_name": "Arsenal",
            "official_club_name": "Arsenal", "provider_team_id": 123456,
            "independent_identity_url": "https://example.org/clubs/arsenal",
            "reviewed_by": "synthetic reviewer", "reviewed_on": "2026-11-11"
        }]
        outcome = inspect(r)
        self.assertFalse(outcome["production_release_allowed"])
        self.assertTrue(any("1/17" in reason for reason in outcome["blocked_reasons"]))

    def test_all_evidence_flags_cannot_override_final_release_gate(self):
        r = self.registry()
        r["competitions"][0]["independently_reviewed_club_ids"] = 1
        r["reviewed_identity_links"] = [{
            "league_id": 39, "season": 2026, "source_team_name": "Example FC",
            "official_club_name": "Arsenal", "provider_team_id": 123456,
            "independent_identity_url": "https://example.org/clubs/arsenal",
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
        with self.assertRaisesRegex(ValueError, "niepelna kontrola ID"):
            inspect(r)


    def test_full_17_submitted_urls_still_does_not_verify_provider_ids(self):
        """A syntactically complete register must never become verified proof."""
        r = self.registry()
        for competition in r["competitions"]:
            league_id = competition["league_id"]
            season = competition["season"]
            count = competition["candidate_aliases"]
            competition["independently_reviewed_club_ids"] = count
            for index, official_name in enumerate(sorted(OFFICIAL[league_id]["clubs"])[:count], 1):
                r["reviewed_identity_links"].append({
                    "league_id": league_id, "season": season,
                    "source_team_name": f"synthetic-{league_id}-{index}",
                    "official_club_name": official_name,
                    "provider_team_id": league_id * 10000 + index,
                    "independent_identity_url": f"https://example.org/clubs/{league_id}-{index}",
                    "reviewed_by": "synthetic", "reviewed_on": "2026-11-11"
                })

        result = inspect(r)
        self.assertEqual(result["submitted_identity_link_entries"], 17)
        self.assertEqual(result["independently_verified_id_links"], 0)
        self.assertFalse(result["production_release_allowed"])
        self.assertTrue(any("brak niezaleznie zweryfikowanej tresci dowodow" in reason
                            for reason in result["blocked_reasons"]))

        r["release"].update({
            "requested": True, "rights_review_approved": True,
            "rights_review_document_url": "https://example.org/rights",
            "forward_time_model_test_approved": True,
            "forward_time_test_report_url": "https://example.org/forward-test",
            "authorized_by": "synthetic", "authorized_on": "2026-11-11",
            "decision_url": "https://example.org/release-decision",
        })
        with self.assertRaisesRegex(ValueError, "brak niezaleznie zweryfikowanej tresci dowodow"):
            inspect(r)

if __name__ == "__main__":
    unittest.main()
