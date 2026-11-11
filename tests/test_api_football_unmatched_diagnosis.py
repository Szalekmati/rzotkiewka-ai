"""Synthetic-only offline tests of mismatch diagnosis."""
import unittest
from datetime import date, timedelta

from api_football_unmatched_diagnosis import diagnose, split_unmatched

D = date(2026, 8, 21)
def m(h,a,when=0,score=(2,1)):
    return (D + timedelta(days=when),h,a,score)

class Tests(unittest.TestCase):
    def test_concordant_pairs(self):
        r = diagnose([m("arsenal","chelsea")],[m("arsenal","chelsea")])
        self.assertEqual(r["base"]["same_score"],1)
        self.assertEqual(sum(r["unpaired_source"].values()),0)

    def test_diff_result_never_changes_pairing(self):
        r = diagnose([m("a","b")],[m("a","b",score=(3,0))])
        self.assertEqual(r["base"]["matched"],1)
        self.assertEqual(r["base"]["score_disagreements"],1)

    def test_pair_date_offset_class(self):
        r = diagnose([m("a","b")],[m("a","b",when=3)])
        self.assertEqual(r["unpaired_source"]["pair_other_date"],1)

    def test_both_names_exist_but_different_opponents(self):
        x = [m("a","b"), m("c","d")]
        y = [m("a","d"), m("c","b")]
        r = diagnose(x,y)
        self.assertEqual(r["unpaired_source"]["both_names_exist"],2)
        self.assertEqual(r["base"]["matched"],0)

    def test_only_home_seen(self):
        r = diagnose([m("a","b")],[m("a","c")])
        self.assertEqual(r["unpaired_source"]["only_home_name"],1)

    def test_only_away_seen(self):
        r = diagnose([m("a","b")],[m("c","b")])
        self.assertEqual(r["unpaired_source"]["only_away_name"],1)

    def test_neither_seen(self):
        r = diagnose([m("a","b")],[m("c","d")])
        self.assertEqual(r["unpaired_source"]["neither_name"],1)

    def test_ambiguous_does_not_fake_match(self):
        left = [m("a","b")]
        right = [m("a","b",when=0),m("a","b",when=1)]
        r = diagnose(left,right)
        self.assertEqual(r["base"]["ambiguous"],1)
        self.assertEqual(r["base"]["matched"],0)
        self.assertEqual(sum(r["unpaired_source"].values()),1)

    def test_count_partition(self):
        l=[m("a","b"),m("c","d"),m("e","f")]
        r=[m("a","b"),m("c","e")]
        un_l, un_r, n, ambiguity = split_unmatched(l,r)
        self.assertEqual((len(un_l),len(un_r),n,ambiguity),(2,1,1,0))
        report=diagnose(l,r)
        self.assertEqual(sum(report["unpaired_source"].values()),2)
        self.assertEqual(sum(report["unpaired_api"].values()),1)


if __name__=="__main__":
    unittest.main()
