"""RZOTKIEWKA 1.6: testy jednostkowe bez Internetu i bez prawdziwych transakcji."""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import forecast_engine as engine

NOW = datetime(2026, 11, 8, 10, tzinfo=timezone.utc)

def example_record(kickoff=NOW + timedelta(hours=5)):
    m = {'id': 83999, 'kickoff': kickoff, 'home_id': 101, 'away_id': 102,
         'home': 'Druzyna A', 'away': 'Druzyna B', 'score': None}
    f = {'probabilities': {'1': .5, 'X': .3, '2': .2},
         'expected_home_goals': 1.5, 'expected_away_goals': 1.0,
         'league_matches_used': 90, 'home_matches_used': 8, 'away_matches_used': 8,
         'home_match_ids': [], 'away_match_ids': []}
    return engine.create_record('bl1', 2026, m, f, NOW), m

def doc_with_record():
    rec, m = example_record()
    return {'schema': 1, 'updated_at': engine.iso(NOW), 'forecasts': [rec]}, m

class ArchiveTests(unittest.TestCase):
    def test_snapshot_integrity(self):
        doc, _ = doc_with_record()
        self.assertIs(engine.valid_doc(doc), doc)
        self.assertEqual(doc['forecasts'][0]['snapshot_sha256'], engine.sha256(doc['forecasts'][0]['snapshot']))

    def test_tampered_snapshot_is_rejected(self):
        doc, _ = doc_with_record()
        doc['forecasts'][0]['snapshot']['probabilities']['1'] = .8
        with self.assertRaisesRegex(ValueError, 'zamrozonej prognozy'):
            engine.valid_doc(doc)

    def test_inconsistent_settlement_rejected(self):
        doc, _ = doc_with_record()
        doc['forecasts'][0]['settlement'] = {'state':'graded','score':[2,0],'outcome':'2','graded_at':engine.iso(NOW + timedelta(hours=8))}
        with self.assertRaisesRegex(ValueError, 'Niespojne rozliczenie'):
            engine.valid_doc(doc)

    def test_settlement_preserves_snapshot(self):
        doc, match = doc_with_record()
        old = copy.deepcopy(doc['forecasts'][0]['snapshot'])
        match['score'] = [2, 1]
        doc, added, graded = engine.update_doc(doc, {('bl1', 2026): [match]}, NOW + timedelta(hours=9))
        self.assertEqual((added,graded),(0,1))
        self.assertEqual(doc['forecasts'][0]['snapshot'], old)
        self.assertEqual(doc['forecasts'][0]['settlement']['outcome'], '1')

    def test_not_settled_too_early(self):
        doc, match = doc_with_record()
        match['score'] = [2, 1]
        doc, added, graded = engine.update_doc(doc, {('bl1', 2026): [match]}, NOW + timedelta(hours=7))
        self.assertEqual((added, graded),(0,0))
        self.assertEqual(doc['forecasts'][0]['settlement']['state'], 'pending')

    def test_no_settlement_without_final_result(self):
        doc, match = doc_with_record()
        doc, added, graded = engine.update_doc(doc, {('bl1', 2026): [match]}, NOW + timedelta(days=2))
        self.assertEqual((added, graded),(0,0))

    def test_double_settlement_is_idempotent(self):
        doc, match = doc_with_record()
        match['score']=[1,1]
        later=NOW + timedelta(hours=9)
        doc, a, b=engine.update_doc(doc,{('bl1',2026):[match]},later)
        first=copy.deepcopy(doc)
        doc, a2, b2=engine.update_doc(doc,{('bl1',2026):[match]},later + timedelta(hours=2))
        self.assertEqual((a,b,a2,b2),(0,1,0,0))
        self.assertEqual(doc,first)

    def test_no_backfilled_prediction_on_finished_match(self):
        doc={'schema':1,'updated_at':None,'forecasts':[]}
        m={'id':12,'kickoff':NOW-timedelta(days=1),'home_id':5,'away_id':6,
           'home':'Druzyna A','away':'Druzyna B','score':[1,1]}
        doc, a, b=engine.update_doc(doc,{('bl1',2026):[m]},NOW)
        self.assertEqual((a,b),(0,0))
        self.assertEqual(doc['forecasts'],[])

    def test_previous_season_pending_revisited(self):
        doc,match=doc_with_record()
        snap=doc['forecasts'][0]['snapshot']
        snap['season']=2025
        doc['forecasts'][0]['id']='bl1-2025-'+str(snap['match_id'])
        doc['forecasts'][0]['snapshot_sha256']=engine.sha256(snap)
        match['score']=[0,0]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'predictions.json'
            path.write_text(json.dumps(doc), encoding='utf-8')
            with patch.object(engine,'FILE',path), patch.object(engine,'utc_now',return_value=datetime(2026,11,9,tzinfo=timezone.utc)), \
                 patch.object(engine,'fetch_matches',side_effect=lambda league,season: [match] if (league,season)==('bl1',2025) else []):
                engine.run()
            result=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(result['forecasts'][0]['settlement']['outcome'],'X')

    def test_parse_score_requires_finished(self):
        raw={'matchIsFinished':False,'matchResults':[{'resultTypeID':2,'pointsTeam1':3,'pointsTeam2':1}]}
        self.assertIsNone(engine.parse_score(raw))
        raw['matchIsFinished']=True
        self.assertEqual(engine.parse_score(raw),[3,1])

    def test_poisson_distribution(self):
        for lam in (.35,1,2.8,3.5):
            self.assertAlmostEqual(sum(engine.poisson(lam)),1.0)

if __name__=='__main__':
    unittest.main()
