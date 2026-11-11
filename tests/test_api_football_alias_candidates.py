"""Offline safety tests: no API and no external data."""
import unittest
from datetime import date

from api_football_alias_candidates import propose_names, evaluate, tokens

D = date(2026, 8, 21)
def f(h,a,s=(1,0),d=D):
    return (d,h,a,s)


class ClubNamesTests(unittest.TestCase):
    def test_suffixes_and_accents(self):
        self.assertEqual(tokens("Club Atlético de Madrid"), frozenset(("atletico","madrid")))
        self.assertEqual(tokens("RC Celta de Vigo"), frozenset(("celta","vigo")))

    def test_safe_unique_prefix(self):
        names, counts = propose_names(
            {"tottenham hotspur", "manchester city", "arsenal"},
            {"tottenham", "manchester city", "arsenal"}
        )
        self.assertEqual(names, {"tottenham hotspur":"tottenham"})
        self.assertEqual(counts["exact_team_names"], 2)

    def test_short_common_token_not_sufficient(self):
        names, counts = propose_names(
            {"real sociedad", "real madrid"}, {"madrid", "sociedad"}
        )
        # Distinctive tokens alone are insufficient unless structurally subset:
        # each unique identity stays candidate, never an approved club ID.
        self.assertEqual(names["real sociedad"], "sociedad")
        self.assertEqual(names["real madrid"], "madrid")

    def test_generic_token_never_unique_identity(self):
        names, counts = propose_names(
            {"manchester city","manchester united"}, {"city","united"}
        )
        self.assertEqual(names, {})
        self.assertEqual(counts["unique_candidates"], 0)

    def test_many_to_one_ambiguity_rejected(self):
        names, counts = propose_names(
            {"brighton north","brighton south"}, {"brighton north south"}
        )
        self.assertEqual(names, {})
        self.assertEqual(counts["ambiguous_api_names"], 1)

    def test_no_fuzzy_spelling(self):
        names, counts = propose_names({"barcellona"}, {"barcelona"})
        self.assertEqual(names, {})
        self.assertEqual(counts["unique_candidates"], 0)

    def test_missing_name_rejected(self):
        with self.assertRaises(ValueError):
            propose_names({""}, {"a"})

    def test_no_score_based_alias_proposal(self):
        names, _ = propose_names({"tottenham hotspur"}, {"tottenham"})
        self.assertEqual(names, {"tottenham hotspur":"tottenham"})
        # Misleading scores must not change proposed team identity.
        a, b, c = evaluate([f("tottenham hotspur","arsenal",(0,9))],
                           [f("tottenham","arsenal",(2,0))])
        self.assertEqual(c["matched"], 1)
        self.assertEqual(c["score_disagreements"], 1)

    def test_unmatched_with_no_identity(self):
        a,b,c = evaluate([f("crystal palace","brentford")],
                         [f("nottingham","brentford")])
        self.assertEqual(c["matched"], 0)

    def test_proposed_mapping_must_not_override_exact(self):
        names, _ = propose_names({"brighton","brighton and hove albion"},
                                 {"brighton","hove albion"})
        self.assertNotIn("brighton", names)
        self.assertEqual(names["brighton and hove albion"], "hove albion")


if __name__ == "__main__":
    unittest.main()
