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

    def test_distinct_match_ids_cannot_duplicate_same_fixture(self):
        # Z and +00:00 represent the same instant; different IDs do not
        # make a duplicated match legitimate.
        duplicate = fixture(mid=900002, when="2026-11-23T20:00:00+00:00")
        result = evaluate_fixtures([fixture(), duplicate], 140)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("duplicate fixture" in reason for reason in result["blocking_reasons"]))
        self.assertFalse(result["production_release_allowed"])

    def test_club_cannot_play_two_fixtures_at_one_kickoff(self):
        other_opponent = fixture(
            home="Real Madrid", away="Real Betis", home_id=101,
            away_id=103, mid=900002
        )
        result = evaluate_fixtures([fixture(), other_opponent], 140)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("club scheduled more than once" in reason
                            for reason in result["blocking_reasons"]))

    def test_same_home_away_pair_on_different_dates_is_blocked(self):
        second = fixture(mid=900003, when="2027-02-23T20:00:00Z")
        result = evaluate_fixtures([fixture(), second], 140)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("repeated home-away pairing" in s
                            for s in result["blocking_reasons"]))
        self.assertFalse(result["predictions_allowed"])

    def test_reverse_home_away_fixture_at_later_date_is_not_duplicate(self):
        reverse = fixture("FC Barcelona", "Real Madrid", home_id=102,
                          away_id=101, mid=900003, when="2027-02-23T20:00:00Z")
        result = evaluate_fixtures([fixture(), reverse], 140)
        self.assertEqual(result["status"], "NAMES_CONSISTENT_NEEDS_INDEPENDENT_REVIEW")
        self.assertFalse(result["public_fixture_preview_allowed"])

    def test_invalid_or_naive_kickoff_is_blocked(self):
        for bad in ("2026-11-23T20:00:00", "2026-02-30T20:00:00Z", "tomorrow"):
            with self.subTest(bad=bad):
                self.assertEqual(evaluate_fixtures([fixture(when=bad)], 140)["status"], "BLOCKED")

    def test_cross_season_kickoffs_are_blocked(self):
        for when in ("2026-06-30T23:59:59Z", "2027-07-01T00:00:00Z",
                     "2025-11-23T20:00:00Z"):
            with self.subTest(when=when):
                result = evaluate_fixtures([fixture(when=when)], 140)
                self.assertEqual(result["status"], "BLOCKED")
                self.assertTrue(any("outside 2026/27 season window" in reason
                                    for reason in result["blocking_reasons"]))
                self.assertFalse(result["public_fixture_preview_allowed"])

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
