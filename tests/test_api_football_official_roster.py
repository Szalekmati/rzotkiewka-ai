"""Synthetic-only roster verification tests; no internet or API key."""
import unittest

from api_football_official_roster import (
    OFFICIAL, official_pivot, triangulate, validate_registry,
)


class OfficialRosterTests(unittest.TestCase):
    def test_premier_reference_has_20_unique_teams(self):
        self.assertEqual(len(validate_registry(OFFICIAL[39]["clubs"])), 20)
        self.assertTrue(OFFICIAL[39]["url"].startswith("https://www.premierleague.com/"))

    def test_laliga_reference_has_20_unique_teams(self):
        self.assertEqual(len(validate_registry(OFFICIAL[140]["clubs"])), 20)
        self.assertTrue(OFFICIAL[140]["url"].startswith("https://www.laliga.com/"))

    def test_duplicate_official_name_rejected(self):
        with self.assertRaises(ValueError):
            validate_registry(tuple(["Arsenal"] * 20))

    def test_exact_premier_name(self):
        self.assertEqual(official_pivot("AFC Bournemouth", OFFICIAL[39]["clubs"]),
                         "bournemouth")
        self.assertEqual(official_pivot("Arsenal", OFFICIAL[39]["clubs"]),
                         "arsenal")

    def test_lexical_spelling_brighton(self):
        self.assertEqual(
            official_pivot("Brighton", OFFICIAL[39]["clubs"]),
            "brighton and hove albion",
        )

    def test_lexical_spelling_tottedham(self):
        self.assertEqual(
            official_pivot("Tottenham", OFFICIAL[39]["clubs"]),
            "tottenham hotspur",
        )

    def test_lexical_spelling_celta(self):
        self.assertEqual(
            official_pivot("RC Celta de Vigo", OFFICIAL[140]["clubs"]), "celta"
        )

    def test_generic_madrid_is_not_inferred(self):
        self.assertIsNone(official_pivot("Madrid", OFFICIAL[140]["clubs"]))

    def test_completely_different_name_is_not_joined(self):
        self.assertIsNone(official_pivot("Barcellona", OFFICIAL[140]["clubs"]))

    def test_no_auto_approval_even_when_supported(self):
        result = triangulate({"arsenal", "tottenham hotspur"},
                             {"arsenal", "tottenham"},39)
        self.assertEqual(result["proposed_aliases"],1)
        self.assertEqual(result["official_name_support"],1)
        self.assertEqual(result["auto_approved_aliases"],0)

    def test_conflict_remains_blocked_even_with_lexical_proposal(self):
        # Source = "Real Madrid"; provider = "Madrid" may be proposed
        # lexically in a small 2-name universe, but official roster
        # must NOT infer "Madrid" unambiguously as a specific club.
        result = triangulate({"real madrid","arsenal"}, {"madrid","arsenal"},140)
        self.assertEqual(result["auto_approved_aliases"],0)

    def test_unresolved_names_remain_unapproved(self):
        result = triangulate({"barcellona","arsenal"}, {"barcelona","arsenal"},39)
        self.assertEqual(result["official_roster_source_matches"],1)
        self.assertEqual(result["auto_approved_aliases"],0)

    def test_registry_is_season_specific(self):
        for league in (39,140):
            self.assertEqual(OFFICIAL[league]["season"],"2026/27")
            self.assertEqual(OFFICIAL[league]["observed"],"2026-11-11")


if __name__ == "__main__":
    unittest.main()
