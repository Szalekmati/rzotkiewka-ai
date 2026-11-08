"""Offline regression checks. No API calls and no wagers."""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import forecast_engine as engine

ROOT = Path(__file__).resolve().parents[1]


class ArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((ROOT / 'predictions.json').read_text(encoding='utf-8'))

    def test_existing_snapshots_untouched_and_valid(self):
        validated = engine.valid_doc(copy.deepcopy(self.original))
        self.assertEqual(len(validated['forecasts']), len(self.original['forecasts']))
        self.assertTrue(all(engine.sha256(r['snapshot']) == r['snapshot_sha256'] for r in validated['forecasts']))

    def test_tampered_forecast_is_rejected(self):
        bad = copy.deepcopy(self.original)
        bad['forecasts'][0]['snapshot']['probabilities']['1'] = 0.99
        with self.assertRaisesRegex(ValueError, 'zamrozonej prognozy'):
            engine.valid_doc(bad)

    def test_inconsistent_settlement_rejected(self):
        bad = copy.deepcopy(self.original)
        bad['forecasts'][0]['settlement'] = {'state': 'graded', 'score': [2, 0], 'outcome': '2', 'graded_at': '2026-11-09T16:00:00Z'}
        with self.assertRaisesRegex(ValueError, 'Niespojne rozliczenie'):
            engine.valid_doc(bad)

    def test_settlement_does_not_modify_forecast(self):
        doc = copy.deepcopy(self.original)
        rec = doc['forecasts'][0]
        snap = copy.deepcopy(rec['snapshot'])
        m = {
            'id': snap['match_id'],
            'kickoff': datetime.fromisoformat(snap['kickoff'].replace('Z', '+00:00')),
            'home': snap['home'], 'away': snap['away'],
            'home_id': 201, 'away_id': 202, 'score': [3, 1],
        }
        later = m['kickoff'] + timedelta(hours=5)
        updated, added, graded = engine.update_doc(doc, {(snap['league'], snap['season']): [m]}, later)
        self.assertEqual((added, graded), (0, 1))
        changed = next(r for r in updated['forecasts'] if r['id'] == rec['id'])
        self.assertEqual(changed['snapshot'], snap)
        self.assertEqual(changed['snapshot_sha256'], engine.sha256(snap))
        self.assertEqual(changed['settlement']['outcome'], '1')

    def test_no_retroactive_forecast_on_finished_match(self):
        doc = {'schema': 1, 'updated_at': None, 'forecasts': []}
        past = {'id': 1, 'kickoff': datetime(2026, 11, 7, 12, tzinfo=timezone.utc),
                'home_id': 10, 'away_id': 11, 'home': 'A', 'away': 'B', 'score': [1, 1]}
        doc, added, graded = engine.update_doc(doc, {('bl1', 2026): [past]}, datetime(2026, 11, 8, tzinfo=timezone.utc))
        self.assertEqual((added, graded), (0, 0))
        self.assertEqual(doc['forecasts'], [])

    def test_previous_season_pending_match_is_revisited(self):
        doc = copy.deepcopy(self.original)
        rec = doc['forecasts'][0]
        rec['snapshot']['season'] = 2026
        rec['snapshot']['league'] = 'bl2'
        rec['id'] = 'bl2-2026-' + str(rec['snapshot']['match_id'])
        rec['snapshot_sha256'] = engine.sha256(rec['snapshot'])
        doc['forecasts'] = [rec]
        kickoff = datetime.fromisoformat(rec['snapshot']['kickoff'].replace('Z', '+00:00'))
        sample = {'id': rec['snapshot']['match_id'], 'kickoff': kickoff, 'home_id': 2,
                  'away_id': 3, 'home': 'A', 'away': 'B', 'score': [0, 0]}
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'predictions.json'
            archive.write_text(json.dumps(doc), encoding='utf-8')
            with patch.object(engine, 'FILE', archive), \
                 patch.object(engine, 'utc_now', return_value=datetime(2027, 8, 5, tzinfo=timezone.utc)), \
                 patch.object(engine, 'fetch_matches', side_effect=lambda league, season: [sample] if (league, season) == ('bl2', 2026) else []):
                engine.run()
            result = json.loads(archive.read_text(encoding='utf-8'))
            self.assertEqual(result['forecasts'][0]['settlement']['state'], 'graded')
            self.assertEqual(result['forecasts'][0]['settlement']['outcome'], 'X')

    def test_probability_distribution_is_normalized(self):
        for avg in (0.35, 1.0, 2.8, 3.5):
            probs = engine.poisson(avg)
            self.assertAlmostEqual(sum(probs), 1.0, places=10)
            self.assertTrue(all(0 <= p <= 1 for p in probs))


if __name__ == '__main__':
    unittest.main()
