"""Fail-closed offline tests: source data never becomes a live league."""
import unittest

from tools.candidate_fixture_identity_gate import evaluate_fixtures


def fixture(home="Real Madrid", away="FC Barcelona", home_id=101, away_id=102,
            mid=900001, when="2026-11-23T20:00:00Z"):
    return {
        "matchID": mid, "matchDateTimeUTC": when,
        "team1": {"teamName": home, "teamId": home_id},
        "team2": {"teamName": away, "teamId": away_id},
        "matchIsFinished": False, "matchResults": [],
    }


class CandidateFixtureGateTests(unittest.TestCase):
    def test_consistent_official_names_are_research_only(self):
        result = evaluate_fixtures([fixture()], 140)
        self.assertEqual(result["status"], "NAMES_CONSISTENT_NEEDS_INDEPENDENT_REVIEW")
        self.assertEqual(result["blocking_reasons"], [])
        self.assertFalse(result["production_release_allowed"])
        self.assertFalse(result["public_fixture_preview_allowed"])
        self.assertFalse(result["predictions_allowed"])

    def test_english_candidate_name_checks_but_never_promotes(self):
        result = evaluate_fixtures([fixture("Arsenal", "Liverpool")], 39)
        self.assertEqual(result["status"], "NAMES_CONSISTENT_NEEDS_INDEPENDENT_REVIEW")
        self.assertFalse(result["production_release_allowed"])

    def test_dutch_clubs_inside_laliga_feed_are_blocked(self):
        result = evaluate_fixtures([fixture("AZ Alkmaar", "Excelsior Rotterdam")], 140)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("outside verified name roster" in s for s in result["blocking_reasons"]))

    def test_other_foreign_feed_is_blocked(self):
        result = evaluate_fixtures([fixture("SC Cambuur", "AFC Ajax")], 140)
        self.assertEqual(result["status"], "BLOCKED")

    def test_missing_or_ambiguous_alias_is_blocked(self):
        result = evaluate_fixtures([fixture("Madrid", "Barcelona")], 140)
        self.assertEqual(result["status"], "BLOCKED")

    def test_duplicate_match_id_and_inconsistent_team_id(self):
        two = fixture("FC Barcelona", "Real Betis", home_id=101, away_id=103)
        result = evaluate_fixtures([fixture(), two], 140)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("duplicate match ID" in s for s in result["blocking_reasons"]))
        self.assertTrue(any("different names" in s for s in result["blocking_reasons"]))

    def test_invalid_or_naive_kickoff_is_blocked(self):
        for bad in ("2026-11-23T20:00:00", "2026-02-30T20:00:00Z", "tomorrow"):
            with self.subTest(bad=bad):
                self.assertEqual(evaluate_fixtures([fixture(when=bad)], 140)["status"], "BLOCKED")

    def test_unregistered_ucl_and_wrong_season_are_blocked(self):
        self.assertEqual(evaluate_fixtures([fixture()], 2)["status"], "BLOCKED")
        self.assertEqual(evaluate_fixtures([fixture()], 140, 2025)["status"], "BLOCKED")
        self.assertEqual(evaluate_fixtures([fixture()], True)["status"], "BLOCKED")

    def test_empty_malformed_and_self_match_never_pass(self):
        self.assertEqual(evaluate_fixtures([], 140)["status"], "BLOCKED")
        self.assertEqual(evaluate_fixtures({"matches": []}, 140)["status"], "BLOCKED")
        self.assertEqual(evaluate_fixtures([fixture(home_id=100, away_id=100)], 140)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
