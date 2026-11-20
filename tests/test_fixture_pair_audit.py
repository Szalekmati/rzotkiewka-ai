"""Synthetic offline regression tests: no network, tokens or provider data."""
import unittest
from research.fixture_pair_audit import audit_pairs


def api(**changes):
    row = dict(fixture_id=101, league_id=39, season=2026,
               kickoff_utc="2026-11-07T15:00:00Z",
               home_team_id=1, away_team_id=2, home_goals=2, away_goals=1)
    row.update(changes)
    return row


def reference(**changes):
    row = dict(league_id=39, season=2026,
               kickoff_utc="2026-11-07T16:00:00+01:00",
               home_team_code="HOME", away_team_code="AWAY",
               home_goals=2, away_goals=1)
    row.update(changes)
    return row


APPROVED = {1: "HOME", 2: "AWAY"}


class PairAuditTests(unittest.TestCase):
    def test_matching_after_timezone_conversion(self):
        self.assertEqual(audit_pairs([api()], [reference()], APPROVED)["agreed"], 1)

    def test_missing_approval_never_automatches(self):
        result = audit_pairs([api()], [reference()], {1: "HOME"})
        self.assertEqual(result["unmapped_team"], 1)
        self.assertEqual(result["agreed"], 0)

    def test_score_mismatch(self):
        self.assertEqual(audit_pairs([api()], [reference(away_goals=0)], APPROVED)["different_score"], 1)

    def test_wrong_venue_side(self):
        self.assertEqual(audit_pairs([api()], [reference(home_team_code="AWAY",
                                                         away_team_code="HOME")], APPROVED)["not_found"], 1)

    def test_wrong_date(self):
        self.assertEqual(audit_pairs([api()], [reference(kickoff_utc="2026-11-10T15:00:00Z")], APPROVED)["different_date"], 1)

    def test_ambiguous_candidates(self):
        self.assertEqual(audit_pairs([api()], [reference(), reference()], APPROVED)["ambiguous"], 1)

    def test_duplicate_api_fixture_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_pairs([api(), api()], [reference()], APPROVED)

    def test_naive_datetime_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_pairs([api(kickoff_utc="2026-11-07T15:00:00")], [reference()], APPROVED)

    def test_invalid_score_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_pairs([api(home_goals=None)], [reference()], APPROVED)

    def test_two_ids_same_team_disallowed(self):
        with self.assertRaises(ValueError):
            audit_pairs([api()], [reference()], {1: "HOME", 2: "HOME"})

    def test_no_map_never_counts_as_agreement(self):
        self.assertEqual(audit_pairs([api()], [reference()], {})["agreed"], 0)

    def test_two_api_ids_same_match_are_rejected(self):
        with self.assertRaises(ValueError):
            audit_pairs([api(), api(fixture_id=102)], [reference()], APPROVED)

    def test_reference_match_cannot_be_reused_for_two_api_matches(self):
        with self.assertRaises(ValueError):
            audit_pairs([api(), api(fixture_id=102,
                                    kickoff_utc="2026-11-07T20:00:00Z")],
                        [reference()], APPROVED)

    def test_distinct_matches_with_distinct_reference_records(self):
        rows = [api(), api(fixture_id=102, kickoff_utc="2026-12-07T15:00:00Z")]
        refs = [reference(), reference(kickoff_utc="2026-12-07T15:00:00Z")]
        self.assertEqual(audit_pairs(rows, refs, APPROVED)["agreed"], 2)

    def test_no_data_is_not_success(self):
        result = audit_pairs([], [], APPROVED)
        self.assertEqual(result["agreed"], 0)
        self.assertEqual(result["api_records"], 0)


if __name__ == "__main__":
    unittest.main()
