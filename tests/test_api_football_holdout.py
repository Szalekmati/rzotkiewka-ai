"""Synthetic-only tests of time-disjoint candidate training and holdout."""
from datetime import date
import unittest
from unittest.mock import patch

import api_football_holdout as audit

D_TRAIN = date(2026, 8, 23)
D_TEST = date(2026, 9, 9)


def row(home, away, score=(1, 0), when=D_TRAIN):
    return (when, home, away, score)


class HoldoutTests(unittest.TestCase):
    def test_windows_do_not_overlap(self):
        audit.assert_windows(audit.TRAIN_START, audit.TRAIN_END,
                             audit.HOLDOUT_START, audit.HOLDOUT_END)
        with self.assertRaises(ValueError):
            audit.assert_windows(D_TRAIN, D_TEST, D_TEST, D_TEST)
        with self.assertRaises(ValueError):
            audit.assert_windows(D_TRAIN, D_TEST, D_TRAIN, D_TEST)

    def test_window_too_large_fails(self):
        with self.assertRaises(ValueError):
            audit.assert_windows(date(2026, 8, 1), date(2026, 8, 20),
                                 D_TEST, date(2026, 9, 14))
        with self.assertRaises(ValueError):
            audit.assert_windows(D_TRAIN, date(2026, 8, 31),
                                 D_TEST, date(2026, 10, 16))

    def test_training_names_applied_to_separate_games(self):
        train_src = [row("coventry city", "arsenal")]
        train_api = [row("coventry", "arsenal")]
        test_src = [row("arsenal", "coventry city", (0, 3), D_TEST)]
        test_api = [row("arsenal", "coventry", (0, 3), D_TEST)]
        r = audit.score_holdout(train_src, train_api, test_src, test_api)
        self.assertEqual(r["proposals_training_only"], 1)
        self.assertEqual(r["holdout_baseline_matches"], 0)
        self.assertEqual(r["holdout_candidate_matches"], 1)
        self.assertEqual(r["holdout_agree"], 1)

    def test_historical_training_does_not_use_holdout_names(self):
        src = [row("arsenal", "chelsea")]
        api = [row("arsenal", "chelsea")]
        test_src = [row("nottingham forest", "chelsea", (2, 1), D_TEST)]
        test_api = [row("nottingham", "chelsea", (2, 1), D_TEST)]
        r = audit.score_holdout(src, api, test_src, test_api)
        self.assertEqual(r["proposals_training_only"], 0)
        self.assertEqual(r["holdout_candidate_matches"], 0)
        self.assertEqual(r["holdout_new_source_names"], 1)

    def test_score_disagreement_is_reported_not_used_for_aliases(self):
        train_src = [row("coventry city", "arsenal", (0, 8))]
        train_api = [row("coventry", "arsenal", (8, 0))]
        test_src = [row("arsenal", "coventry city", (2, 1), D_TEST)]
        test_api = [row("arsenal", "coventry", (1, 2), D_TEST)]
        r = audit.score_holdout(train_src, train_api, test_src, test_api)
        self.assertEqual(r["holdout_candidate_matches"], 1)
        self.assertEqual(r["holdout_disagree"], 1)
        self.assertEqual(r["holdout_agree"], 0)

    def test_empty_holdout_never_reports_perfect_accuracy(self):
        train = [row("arsenal", "chelsea")]
        with self.assertRaises(RuntimeError):
            audit.score_holdout(train, train, [], train)
        with self.assertRaises(RuntimeError):
            audit.score_holdout(train, train, train, [])

    def test_empty_training_never_infers_alias_from_validation(self):
        test = [row("coventry city", "arsenal", when=D_TEST)]
        with self.assertRaises(RuntimeError):
            audit.score_holdout([], [], test, test)

    def test_roster_keeps_training_and_validation_separate(self):
        train = [row("foo", "bar")]
        holdout = [row("foo", "baz", when=D_TEST)]
        self.assertEqual(audit.roster(train), {"foo", "bar"})
        self.assertEqual(audit.roster(holdout) - audit.roster(train), {"baz"})

    def test_score_holdout_uses_only_training_names_for_proposals(self):
        train_src = [row("arsenal", "coventry city")]
        train_api = [row("arsenal", "coventry")]
        test_src = [row("arsenal", "some future team", when=D_TEST)]
        test_api = [row("arsenal", "some future", when=D_TEST)]
        with patch.object(audit, "propose_names", wraps=audit.propose_names) as spy:
            audit.score_holdout(train_src, train_api, test_src, test_api)
        args = spy.call_args.args
        self.assertNotIn("some future team", args[0])
        self.assertNotIn("some future", args[1])

    def test_only_four_fixture_calls_budgeted(self):
        self.assertEqual(audit.MAX_FIXTURE_CALLS, 2 * len(audit.SOURCES))


if __name__ == "__main__":
    unittest.main()
