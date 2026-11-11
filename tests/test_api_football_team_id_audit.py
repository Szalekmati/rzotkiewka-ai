"""Offline synthetic tests - don't access API or external data."""
from datetime import date
import unittest

from api_football_team_id_audit import read_roster, fixture_ids, inspect_identity

START = date(2026,8,21)
END = date(2026,8,31)
TEST_START = date(2026,9,4)
TEST_END = date(2026,9,14)


def payload(items):
    return {"results":len(items), "paging":{"current":1,"total":1}, "response":items}


def team(id,name):
    return {"team":{"id":id,"name":name}, "venue":{"id":1}}


def match(id, date, h_id=1, a_id=2, h="Coventry", a="Arsenal"):
    return {
        "fixture":{"id":id,"date":date+"T18:00:00+00:00","status":{"short":"FT"}},
        "league":{"id":39,"season":2026},
        "teams":{"home":{"id":h_id,"name":h}, "away":{"id":a_id,"name":a}},
        "goals":{"home":1,"away":0},
    }

ROSTER = [team(1,"Coventry"),team(2,"Arsenal")]


class TeamIDAuditTests(unittest.TestCase):
    def test_valid_roster(self):
        ids, names = read_roster(payload(ROSTER))
        self.assertEqual(ids,{1:"coventry",2:"arsenal"})
        self.assertEqual(names["coventry"],1)

    def test_duplicate_team_ids_rejected(self):
        with self.assertRaises(RuntimeError):
            read_roster(payload([team(1,"Coventry"),team(1,"Arsenal")]))

    def test_duplicate_normalized_names_rejected(self):
        with self.assertRaises(RuntimeError):
            read_roster(payload([team(1,"FC Coventry"),team(2,"Coventry FC")]))

    def test_roster_pagination_refused(self):
        p=payload(ROSTER)
        p["paging"]["total"]=2
        with self.assertRaises(RuntimeError):
            read_roster(p)

    def test_known_fixture_ids_and_roster(self):
        roster,_=read_roster(payload(ROSTER))
        a=fixture_ids(payload([match(11,"2026-08-21")]),39,2026,START,END,roster)
        self.assertEqual(a["unknown_id_occurrences"],0)
        self.assertEqual(a["roster_name_variations"],0)

    def test_unknown_id_detected(self):
        roster,_=read_roster(payload(ROSTER))
        a=fixture_ids(payload([match(11,"2026-08-21",h_id=91)]),39,2026,START,END,roster)
        self.assertEqual(a["unknown_id_occurrences"],1)

    def test_name_variant_not_silently_approved(self):
        roster,_=read_roster(payload(ROSTER))
        a=fixture_ids(payload([match(11,"2026-08-21",h="Coventry City")]),39,2026,START,END,roster)
        self.assertEqual(a["roster_name_variations"],1)

    def test_club_cannot_play_itself(self):
        roster,_=read_roster(payload(ROSTER))
        with self.assertRaises(RuntimeError):
            fixture_ids(payload([match(11,"2026-08-21",a_id=1)]),39,2026,START,END,roster)

    def test_fixture_dates_outside_window_rejected(self):
        roster,_=read_roster(payload(ROSTER))
        with self.assertRaises(RuntimeError):
            fixture_ids(payload([match(11,"2026-09-05")]),39,2026,START,END,roster)

    def test_duplicate_fixture_ids_rejected(self):
        roster,_=read_roster(payload(ROSTER))
        with self.assertRaises(RuntimeError):
            fixture_ids(payload([match(11,"2026-08-21"),match(11,"2026-08-22")]),39,2026,START,END,roster)

    def test_source_alias_mapped_to_unique_roster_id_but_not_approved(self):
        res=inspect_identity(payload(ROSTER),
            payload([match(11,"2026-08-21")]),
            payload([match(12,"2026-09-04")]),39,
            [(START,"coventry city","arsenal",(1,0))])
        self.assertEqual(res["alias_candidates"],1)
        self.assertEqual(res["candidates_linked_to_unique_api_id"],1)
        self.assertEqual(res["shared_ids_across_windows"],2)
        self.assertFalse(res["APPROVED_FOR_PRODUCTION"])

    def test_unknown_fixture_id_blocks_clean_quality(self):
        res=inspect_identity(payload(ROSTER),
            payload([match(11,"2026-08-21",h_id=99)]),
            payload([match(12,"2026-09-04")]),39,
            [(START,"coventry city","arsenal",(1,0))])
        self.assertEqual(res["quality"],"DO_WERYFIKACJI_ID")

    def test_api_roster_name_variation_blocks_clean_quality(self):
        res=inspect_identity(payload(ROSTER),
            payload([match(11,"2026-08-21",h="Coventry City")]),
            payload([match(12,"2026-09-04")]),39,
            [(START,"coventry city","arsenal",(1,0))])
        self.assertEqual(res["quality"],"DO_WERYFIKACJI_NAZW")

    def test_shared_fixture_id_across_windows_refused(self):
        with self.assertRaises(RuntimeError):
            inspect_identity(payload(ROSTER),
                payload([match(11,"2026-08-21")]),
                payload([match(11,"2026-09-04")]),39,
                [(START,"coventry city","arsenal",(1,0))])


if __name__ == "__main__":
    unittest.main()
