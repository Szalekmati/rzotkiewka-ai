#!/usr/bin/env python3
"""RZOTKIEWKA AI: bezpieczny, retrospektywny backtest 1.3 vs 2.0.

Zero modyfikacji predictions.json, zadnych platnosci ani zakladow.
Stdlib only. Uruchom z katalogu glownego repozytorium:
    python backtest.py --seasons 2024 2025 --leagues bl1 bl2 bl3 --lead-hours 168
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import unittest
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import forecast_engine as engine

ORDER = ('1', 'X', '2')
LEGACY_VERSION = '1.3.0'


def old_predict(match, matches, as_of):
    """Zamrozony algorytm predict() 1.3.0, bez zmiany parametrow.

    team_rates, poisson, prior_history, team_recent sa NIEZMIENIONE miedzy
    kodem 1.3.0 a 2.0.0 (porownano kod z archiwum projektu).
    """
    history = engine.prior_history(matches, match['kickoff'], as_of)
    home_rows = engine.team_recent(history, match['home_id'])
    away_rows = engine.team_recent(history, match['away_id'])
    if len(history) < engine.MIN_LEAGUE or min(len(home_rows), len(away_rows)) < engine.MIN_TEAM:
        return None
    home_goals = sum(m['score'][0] for m in history)
    away_goals = sum(m['score'][1] for m in history)
    avg_home = (home_goals + 12 * 1.45) / (len(history) + 12)
    avg_away = (away_goals + 12 * 1.15) / (len(history) + 12)
    typical = (avg_home + avg_away) / 2
    hf, ha = engine.team_rates(home_rows, match['home_id'], 'home', typical)
    af, aa = engine.team_rates(away_rows, match['away_id'], 'away', typical)
    exp_home = engine.clamp(avg_home * math.sqrt(engine.clamp(hf / avg_home, .5, 1.8) *
                                                  engine.clamp(aa / avg_home, .5, 1.8)), .35, 3.5)
    exp_away = engine.clamp(avg_away * math.sqrt(engine.clamp(af / avg_away, .5, 1.8) *
                                                  engine.clamp(ha / avg_away, .5, 1.8)), .35, 3.5)
    probs = {'1': 0.0, 'X': 0.0, '2': 0.0}
    for i, p1 in enumerate(engine.poisson(exp_home)):
        for j, p2 in enumerate(engine.poisson(exp_away)):
            probs['1' if i > j else 'X' if i == j else '2'] += p1 * p2
    total = sum(probs.values())
    probs = {k: round(probs[k] / total, 6) for k in ORDER}
    probs['2'] = round(1.0 - probs['1'] - probs['X'], 6)
    return {
        'probabilities': probs,
        'expected_home_goals': round(exp_home, 3),
        'expected_away_goals': round(exp_away, 3),
        'league_matches_used': len(history),
        'home_matches_used': len(home_rows),
        'away_matches_used': len(away_rows),
        'home_match_ids': [m['id'] for m in home_rows],
        'away_match_ids': [m['id'] for m in away_rows],
    }


def pick(probs):
    return max(ORDER, key=lambda outcome: probs[outcome])


def validate_probs(probs):
    if set(probs) != set(ORDER):
        raise ValueError('Zly zestaw prawdopodobienstw')
    if any(not isinstance(probs[key], (int, float)) or
           not math.isfinite(probs[key]) or probs[key] < 0 or probs[key] > 1
           for key in ORDER):
        raise ValueError('Nieprawidlowe prawdopodobienstwa')
    if abs(sum(probs.values()) - 1) > 1e-5:
        raise ValueError('Suma prawdopodobienstw jest rozna od 1')


def score_prediction(probs, outcome):
    validate_probs(probs)
    return {
        'pick': pick(probs),
        'hit': int(pick(probs) == outcome),
        # Brier dla 3 klas w skali 0..2. Im mniejszy, tym lepiej.
        'brier': sum((probs[k] - int(k == outcome)) ** 2 for k in ORDER),
        'log_loss': -math.log(max(1e-12, probs[outcome])),
    }


def evaluate_one(league, season, match, matches, lead_hours):
    if match['score'] is None:
        return None
    as_of = match['kickoff'] - timedelta(hours=lead_hours)
    old = old_predict(match, matches, as_of)
    new = engine.predict(match, matches, as_of)
    if old is None or new is None:
        return None  # Dokladnie ta sama probka dla obu wersji
    outcome = engine.result_outcome(match['score'])
    p_old, p_new = old['probabilities'], new['probabilities']
    m_old, m_new = score_prediction(p_old, outcome), score_prediction(p_new, outcome)
    return {
        'league': league, 'season': season,
        'match_id': match['id'], 'kickoff_utc': engine.iso(match['kickoff']),
        'as_of_utc': engine.iso(as_of), 'home': match['home'], 'away': match['away'],
        'score': ':'.join(str(n) for n in match['score']), 'outcome': outcome,
        **{f'old_p_{k}': p_old[k] for k in ORDER},
        **{f'new_p_{k}': p_new[k] for k in ORDER},
        **{f'old_{k}': v for k, v in m_old.items()},
        **{f'new_{k}': v for k, v in m_new.items()},
    }


def evaluate_season(league, season, matches, lead_hours, cutoff=None):
    """Nie dopuszczamy przyszlych spotkan / wynikow z niezakończonych meczow."""
    cutoff = cutoff or datetime.now(timezone.utc)
    if cutoff.tzinfo is None:
        raise ValueError('cutoff musi miec strefe czasowa')
    seen = set()
    rows = []
    all_matches = sorted(matches, key=lambda m: (m['kickoff'], m['id']))
    stats = Counter()
    for m in all_matches:
        if m['id'] in seen:
            raise ValueError(f'Zduplikowany identyfikator meczu: {m["id"]}')
        seen.add(m['id'])
        if m['score'] is None or m['kickoff'] + timedelta(hours=engine.SETTLE_HOURS) > cutoff:
            stats['without_final_result'] += 1
            continue
        result = evaluate_one(league, season, m, all_matches, lead_hours)
        if result is None:
            stats['insufficient_history'] += 1
        else:
            rows.append(result)
    stats['evaluated'] = len(rows)
    return rows, dict(stats)


def aggregate(rows, prefix):
    n = len(rows)
    if not n:
        return {'n': 0, 'accuracy': None, 'brier': None, 'log_loss': None,
                'picks': {'1': 0, 'X': 0, '2': 0}}
    c = Counter(r[f'{prefix}_pick'] for r in rows)
    return {
        'n': n,
        'accuracy': round(sum(r[f'{prefix}_hit'] for r in rows) / n, 4),
        'brier': round(sum(r[f'{prefix}_brier'] for r in rows) / n, 4),
        'log_loss': round(sum(r[f'{prefix}_log_loss'] for r in rows) / n, 4),
        'picks': {k: c[k] for k in ORDER},
    }


def summarize(rows, skipped, lead_hours):
    by_league = {}
    for league in sorted({r['league'] for r in rows}):
        subset = [r for r in rows if r['league'] == league]
        by_league[league] = {'old': aggregate(subset, 'old'),
                             'new': aggregate(subset, 'new')}
    old = aggregate(rows, 'old')
    new = aggregate(rows, 'new')
    wins = sum(r['new_brier'] < r['old_brier'] - 1e-10 for r in rows)
    losses = sum(r['new_brier'] > r['old_brier'] + 1e-10 for r in rows)
    return {
        'backtest_type': 'retrospective_walk_forward_not_archived_forecasts',
        'model_old': LEGACY_VERSION,
        'model_new': engine.MODEL_VERSION,
        'lead_hours': lead_hours,
        'n': len(rows),
        'old': old, 'new': new,
        'brier_delta_new_minus_old': round(new['brier'] - old['brier'], 4),
        'paired_brier_new_better': wins,
        'paired_brier_old_better': losses,
        'paired_brier_equal': len(rows) - wins - losses,
        'real_outcome_counts': dict(Counter(r['outcome'] for r in rows)),
        'per_league': by_league,
        'data_coverage': skipped,
        'limitations': [
            'Symulacja na historycznej bazie, nie prognozy faktycznie zarchiwizowane przed meczem.',
            'Nie znamy historycznego momentu publikacji ani pozniejszych korekt wynikow w API.',
            'Dane historyczne sa filtrowane do cutoff (mecz minus lead_hours minus bufor).',
            'Brak kursow; nie mierzymy ROI, ani nie gwarantujemy przewagi nad bukmacherem.',
            'Test jest opisowy; roznica nie dowodzi przewagi w przyszlosci.',
        ],
    }


def md_report(summary):
    def pct(v):
        return '—' if v is None else f'{100*v:.1f}%'
    def number(v):
        return '—' if v is None else f'{v:.4f}'
    o, n = summary['old'], summary['new']
    lines = [
        '# RZOTKIEWKA AI — retrospektywny backtest', '',
        f"Porownanie: **{summary['model_old']}** vs **{summary['model_new']}**  ",
        f"Punkt symulacji: **{summary['lead_hours']} godzin przed meczem**  ",
        f"Ta sama probka: **{summary['n']}** zakonczonych spotkan.", '',
        '| Metryka | Stary model | Nowy model |',
        '|---|---:|---:|',
        f"| Trafnosc 1X2 | {pct(o['accuracy'])} | {pct(n['accuracy'])} |",
        f"| Brier (mniej = lepiej) | {number(o['brier'])} | {number(n['brier'])} |",
        f"| Log loss (mniej = lepiej) | {number(o['log_loss'])} | {number(n['log_loss'])} |",
        f"| Wskazania 1 (gospodarze) | {o['picks']['1']} | {n['picks']['1']} |",
        f"| Wskazania X (remis) | {o['picks']['X']} | {n['picks']['X']} |",
        f"| Wskazania 2 (goscie) | {o['picks']['2']} | {n['picks']['2']} |",
        '', f"Roznica Brier (nowy minus stary): **{summary['brier_delta_new_minus_old']:+.4f}** ",
        '(ujemna oznacza lepszy nowy model).', '',
        f"Po meczu lepszy Brier nowego: {summary['paired_brier_new_better']}; "
        f"starego: {summary['paired_brier_old_better']}; "
        f"remis: {summary['paired_brier_equal']}.", '',
        '## Rozbicie na ligi', '',
        '| Liga | N | Trafnosc stary | Trafnosc nowy | Brier stary | Brier nowy |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for league, d in summary['per_league'].items():
        a, b = d['old'], d['new']
        lines.append(f"| {league} | {a['n']} | {pct(a['accuracy'])} | "
                     f"{pct(b['accuracy'])} | {number(a['brier'])} | {number(b['brier'])} |")
    lines += ['', '## Pokrycie danych', '',
              '| Liga / sezon | Pobrano | Oceniono | Pominięte / błąd |',
              '|---|---:|---:|---|']
    for name, d in summary['data_coverage'].items():
        if 'error' in d:
            lines.append(f"| {name} | — | — | {str(d['error']).replace('|', '/')} |")
        else:
            excluded = d.get('insufficient_history', 0) + d.get('without_final_result', 0)
            lines.append(f"| {name} | {d['fetched']} | {d['evaluated']} | {excluded} |")
    lines += ['', '## Ograniczenia', '']
    lines.extend(f'- {x}' for x in summary['limitations'])
    return '\n'.join(lines) + '\n'


def write_report(out_dir, rows, summary):
    out_dir.mkdir(parents=True, exist_ok=True)
    columns = [
        'league', 'season', 'match_id', 'kickoff_utc', 'as_of_utc',
        'home', 'away', 'score', 'outcome',
        'old_p_1', 'old_p_X', 'old_p_2', 'new_p_1', 'new_p_X', 'new_p_2',
        'old_pick', 'new_pick', 'old_hit', 'new_hit',
        'old_brier', 'new_brier', 'old_log_loss', 'new_log_loss',
    ]
    with (out_dir / 'mecze.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows({k: row[k] for k in columns} for row in rows)
    (out_dir / 'wyniki.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (out_dir / 'RAPORT.md').write_text(md_report(summary), encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Porownanie historyczne 1.3 vs 2.0; bez zmian w archiwum')
    parser.add_argument('--seasons', type=int, nargs='+', default=[2024, 2025])
    parser.add_argument('--leagues', nargs='+', choices=list(engine.LEAGUES),
                        default=list(engine.LEAGUES))
    parser.add_argument('--lead-hours', type=int, default=168)
    parser.add_argument('--out-dir', type=Path, default=Path('backtest_reports'))
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args(argv)
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(BacktestTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1
    if engine.MODEL_VERSION != '2.0.0':
        parser.error('Potrzebny forecast_engine.py z MODEL_VERSION=2.0.0')
    if not 3 <= args.lead_hours <= 24 * 8:
        parser.error('Ustaw --lead-hours od 3 do 192 (do 8 dni)')
    rows = []
    stats = {}
    loaded = 0
    for league in args.leagues:
        for season in args.seasons:
            name = f'{league}/{season}'
            try:
                matches = engine.fetch_matches(league, season)
                if not matches:
                    raise ValueError('Brak danych dla sezonu')
            except Exception as exc:
                stats[name] = {'error': str(exc)}
                print(f'OSTRZEZENIE: {name} pominiete: {exc}', file=sys.stderr)
                continue
            loaded += 1
            season_rows, season_stats = evaluate_season(league, season, matches, args.lead_hours)
            stats[name] = {'fetched': len(matches), **season_stats}
            rows.extend(season_rows)
            print(f'{name}: pobrano {len(matches)}, oceniono {len(season_rows)}', flush=True)
    if loaded == 0 or not rows:
        print('BLAD: brak ocenionych spotkan — nie tworzymy pozornego raportu.', file=sys.stderr)
        return 2
    rows.sort(key=lambda r: (r['kickoff_utc'], r['league'], r['match_id']))
    summary = summarize(rows, stats, args.lead_hours)
    write_report(args.out_dir, rows, summary)
    print('\n' + md_report(summary), flush=True)
    print(f'RAPORT ZAPISANY: {args.out_dir.resolve()}', flush=True)
    return 0


class BacktestTests(unittest.TestCase):
    def setUp(self):
        self.today = datetime(2025, 1, 1, tzinfo=timezone.utc)
        self.matches = []
        # 40 spotkan rozegranych, kazda druzyna >= 4; rozne wyniki.
        for i in range(40):
            teams = [(1, 2), (3, 4), (2, 3), (4, 1)][i % 4]
            self.matches.append({
                'id': i+1, 'home_id': teams[0], 'away_id': teams[1],
                'home': f'D{teams[0]}', 'away': f'D{teams[1]}',
                'kickoff': self.today + timedelta(days=i),
                'score': [[2, 1], [0, 2], [1, 1], [3, 0]][i % 4],
            })
        self.fixture = {
            'id': 90, 'home_id': 1, 'away_id': 2, 'home': 'D1', 'away': 'D2',
            'kickoff': self.today + timedelta(days=53), 'score': [0, 2],
        }

    def test_old_and_new_are_evaluated_same_fixture(self):
        row = evaluate_one('bl1', 2024, self.fixture, self.matches + [self.fixture], 168)
        self.assertIsNotNone(row)
        self.assertEqual(row['outcome'], '2')
        self.assertAlmostEqual(sum(row[f'old_p_{k}'] for k in ORDER), 1.0)
        self.assertAlmostEqual(sum(row[f'new_p_{k}'] for k in ORDER), 1.0)

    def test_future_scores_do_not_change_predictions(self):
        fixture = self.fixture.copy()
        base = evaluate_one('bl1', 2024, fixture, self.matches + [fixture], 168)
        later = {
            'id': 101, 'home_id': 1, 'away_id': 2, 'home': 'D1', 'away': 'D2',
            'kickoff': self.today + timedelta(days=49), 'score': [50, 0],
        }
        after = evaluate_one('bl1', 2024, fixture, self.matches + [fixture, later], 168)
        self.assertEqual(base, after)  # T-7 dni: mecz pozniejszy jest wykluczony

    def test_an_earlier_match_may_change_both_models(self):
        fixture = self.fixture.copy()
        before = evaluate_one('bl1', 2024, fixture, self.matches + [fixture], 168)
        earlier = {
            'id': 102, 'home_id': 1, 'away_id': 2, 'home': 'D1', 'away': 'D2',
            'kickoff': self.today + timedelta(days=44), 'score': [0, 20],
        }
        after = evaluate_one('bl1', 2024, fixture, self.matches + [fixture, earlier], 168)
        self.assertNotEqual(before['new_p_2'], after['new_p_2'])

    def test_no_result_not_scored(self):
        fixture = self.fixture.copy()
        fixture['score'] = None
        self.assertIsNone(evaluate_one('bl1', 2024, fixture, self.matches + [fixture], 168))

    def test_brier_perfect_and_uniform(self):
        self.assertAlmostEqual(score_prediction({'1': 1.0, 'X': 0., '2': 0.}, '1')['brier'], 0)
        self.assertAlmostEqual(score_prediction({'1': 1/3, 'X': 1/3, '2': 1/3}, '1')['brier'], 2/3)

    def test_duplicate_matches_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_season('bl1', 2024, [self.matches[0], self.matches[0]], 168,
                            cutoff=self.today + timedelta(days=100))

    def test_archived_file_not_accessed_or_changed(self):
        with TemporaryDirectory() as directory:
            archive = Path(directory) / 'predictions.json'
            archive.write_text('\"NIE ZMIENIAC ARCHIWUM\"', encoding='utf-8')
            with patch.object(engine, 'FILE', archive):
                row = evaluate_one('bl1', 2024, self.fixture, self.matches + [self.fixture], 168)
                self.assertTrue(row['as_of_utc'] < row['kickoff_utc'])
            self.assertEqual(archive.read_text(encoding='utf-8'), '\"NIE ZMIENIAC ARCHIWUM\"')


if __name__ == '__main__':
    sys.exit(main())
