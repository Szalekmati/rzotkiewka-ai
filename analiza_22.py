#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RZOTKIEWKA 2.2 – diagnostyka kalibracji 1/X/2, bez zewnetrznych bibliotek.

Uruchomienie: python analiza_22.py --csv data/mecze_21.csv --out wyniki_22
Testy wbudowane: python analiza_22.py --self-test

To AUDYT na wynikach 2.0/2.1, nie nowy produkcyjny silnik prognoz.
Caly dobor parametrow odbywa sie na sezonie 2024, kontrola na sezonie 2025.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

CATS = ('1', 'X', '2')
SEASON_TRAIN = '2024'
SEASON_TEST = '2025'
EPS = 1e-12


@dataclass(frozen=True)
class Match:
    league: str
    season: str
    match_id: str
    kickoff_utc: str
    as_of_utc: str
    home: str
    away: str
    outcome: str
    old: tuple[float, float, float]
    new: tuple[float, float, float]


@dataclass(frozen=True)
class Params:
    temperature: float = 1.0
    draw_bias: float = 0.0
    home_bias: float = 0.0


def parse_iso(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError(f'Data bez strefy czasowej: {value}')
    return result.astimezone(timezone.utc)


def read_matches(path: Path) -> list[Match]:
    needed = {'league', 'season', 'match_id', 'kickoff_utc', 'as_of_utc',
              'home', 'away', 'outcome', *[f'{v}_p_{k}' for v in ('old', 'new') for k in CATS]}
    records: list[Match] = []
    unique: set[tuple[str, str, str]] = set()
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames or not needed.issubset(set(rdr.fieldnames)):
            raise ValueError('CSV nie ma wymaganych kolumn: ' + ', '.join(sorted(needed - set(rdr.fieldnames or []))))
        for rownum, r in enumerate(rdr, start=2):
            if not any(r.values()):
                continue
            try:
                old = tuple(float(r[f'old_p_{k}']) for k in CATS)
                new = tuple(float(r[f'new_p_{k}']) for k in CATS)
                for version, p in (('old', old), ('new', new)):
                    if any(not math.isfinite(x) or x <= 0 or x >= 1 for x in p):
                        raise ValueError(f'{version}: niepoprawne prawdopodobienstwa')
                    if abs(sum(p) - 1.0) > 0.002:
                        raise ValueError(f'{version}: suma prawdopodobienstw != 1')
                if r['outcome'] not in CATS:
                    raise ValueError('Nieznany wynik 1/X/2')
                if r['season'] not in (SEASON_TRAIN, SEASON_TEST):
                    raise ValueError('Nieoczekiwany sezon; wymagana jawna zmiana planu walidacji')
                as_of, kickoff = parse_iso(r['as_of_utc']), parse_iso(r['kickoff_utc'])
                if not as_of < kickoff:
                    raise ValueError('as_of_utc musi byc przed rozpoczeciem meczu')
                if abs((kickoff - as_of).total_seconds() - 168 * 3600) > 60:
                    raise ValueError('Nieprawidlowy horyzont: wymagane 168 godzin')
                ident = (r['league'], r['season'], r['match_id'])
                if ident in unique:
                    raise ValueError('Powtorzony mecz: ' + repr(ident))
                unique.add(ident)
                records.append(Match(r['league'], r['season'], r['match_id'],
                                     r['kickoff_utc'], r['as_of_utc'], r['home'], r['away'],
                                     r['outcome'], old, new))
            except (ValueError, TypeError, KeyError) as ex:
                raise ValueError(f'{path.name}: wiersz {rownum}: {ex}') from ex
    if not records:
        raise ValueError('Pusty plik CSV')
    return sorted(records, key=lambda m: (m.kickoff_utc, m.league, m.match_id))


def transform(p: tuple[float, float, float], params: Params) -> tuple[float, float, float]:
    # Skala temperatury i przesuniecia logitow, potem softmax.
    l0 = math.log(max(p[0], EPS)) / params.temperature + params.home_bias
    l1 = math.log(max(p[1], EPS)) / params.temperature + params.draw_bias
    l2 = math.log(max(p[2], EPS)) / params.temperature
    maximum = max(l0, l1, l2)
    e0, e1, e2 = math.exp(l0 - maximum), math.exp(l1 - maximum), math.exp(l2 - maximum)
    s = e0 + e1 + e2
    return (e0 / s, e1 / s, e2 / s)


def brier(p: tuple[float, float, float], outcome: str) -> float:
    ix = CATS.index(outcome)
    return sum((pi - float(j == ix)) ** 2 for j, pi in enumerate(p))


def logloss(p: tuple[float, float, float], outcome: str) -> float:
    return -math.log(max(p[CATS.index(outcome)], EPS))


def argmax(p: tuple[float, float, float]) -> str:
    return CATS[max(range(3), key=lambda j: p[j])]


def summarize(records: list[Match], forecasts: list[tuple[float, float, float]]) -> dict:
    n = len(records)
    if n == 0 or n != len(forecasts):
        raise ValueError('Nieprawidlowa liczba typow')
    brier_values = [brier(p, m.outcome) for m, p in zip(records, forecasts)]
    logloss_values = [logloss(p, m.outcome) for m, p in zip(records, forecasts)]
    predictions = [argmax(p) for p in forecasts]
    return {
        'n': n,
        'accuracy': sum(pred == m.outcome for pred, m in zip(predictions, records)) / n,
        'brier': sum(brier_values) / n,
        'log_loss': sum(logloss_values) / n,
        'avg_p_x': sum(p[1] for p in forecasts) / n,
        'actual_draw_rate': sum(m.outcome == 'X' for m in records) / n,
        'picks': {k: sum(p == k for p in predictions) for k in CATS},
    }


def probability_bins(records: list[Match], forecasts: list[tuple[float, float, float]], label: str) -> list[dict]:
    ret = []
    for start in range(0, 10):
        pairs = [(m, p) for m, p in zip(records, forecasts) if min(int(p[1] * 10), 9) == start]
        if not pairs:
            continue
        ret.append({'bin': f'{start * 10}-{(start + 1) * 10}%', 'n': len(pairs),
                    'avg_p_x': sum(p[1] for _, p in pairs) / len(pairs),
                    'real_draw_rate': sum(m.outcome == 'X' for m, _ in pairs) / len(pairs),
                    'model': label})
    return ret


def param_grid() -> Iterable[tuple[str, Params, float]]:
    # Wartosci i kary zdefiniowane Z GORY; test 2025 nigdy nie sluzy do doboru.
    yield ('bez_zmian', Params(), 0.0)
    temperatures = [x / 100 for x in range(85, 151, 5)]
    draws = [x / 100 for x in range(-20, 21, 5)]
    homes = [x / 100 for x in range(-20, 21, 10)]
    for t in temperatures:
        yield ('temperatura', Params(t), 0.0005)
    for t in temperatures:
        for d in draws:
            yield ('temperatura_remis', Params(t, d), 0.001)
    for t in temperatures:
        for d in draws:
            for h in homes:
                yield ('temperatura_remis_dom', Params(t, d, h), 0.002)


def fit_train_only(records: list[Match]) -> dict:
    if not records or {m.season for m in records} != {SEASON_TRAIN}:
        raise ValueError('Wyciek danych: dobierac parametry wolno tylko na sezonie 2024')
    best = None
    for name, params, penalty in param_grid():
        score = sum(brier(transform(m.new, params), m.outcome) for m in records) / len(records)
        penalized = score + penalty
        if best is None or penalized < best['selection_score'] - 1e-12:
            best = {'family': name, 'params': params, 'train_brier': score,
                    'penalty': penalty, 'selection_score': penalized}
    return best


def pair_bootstrap_ci(records: list[Match], reference: list[tuple[float, float, float]],
                      candidate: list[tuple[float, float, float]], repeats: int = 1200) -> list[float]:
    # Dodatnia wartosc = poprawa kandydata; grupowanie po dacie spotkania.
    groups = defaultdict(list)
    for m, ref, cand in zip(records, reference, candidate):
        groups[m.kickoff_utc[:10]].append((brier(ref, m.outcome) - brier(cand, m.outcome)))
    blocks = list(groups.values())
    if not blocks:
        return [0.0, 0.0]
    rng = random.Random(2202)
    results = []
    for _ in range(repeats):
        block_idx = [rng.randrange(len(blocks)) for _ in blocks]
        n = sum(len(blocks[j]) for j in block_idx)
        value = sum(sum(blocks[j]) for j in block_idx) / n
        results.append(value)
    results.sort()
    return [results[int(0.025 * (repeats - 1))], results[int(0.975 * (repeats - 1))]]


def average(s: list[float]) -> float:
    return sum(s) / len(s)


def run(records: list[Match], out_dir: Path) -> dict:
    train = [m for m in records if m.season == SEASON_TRAIN]
    test = [m for m in records if m.season == SEASON_TEST]
    if not train or not test:
        raise ValueError('Do testu wymagane sa oba sezony: 2024 i 2025')
    if max(parse_iso(m.kickoff_utc) for m in train) >= min(parse_iso(m.kickoff_utc) for m in test):
        raise ValueError('Naruszona chronologia: dane treningowe nachodza na testowe')
    fit = fit_train_only(train)
    params = fit['params']
    tr_old, tr_new = [m.old for m in train], [m.new for m in train]
    te_old, te_new = [m.old for m in test], [m.new for m in test]
    tr_cand = [transform(p, params) for p in tr_new]
    te_cand = [transform(p, params) for p in te_new]
    all_metrics = {
        'train_2024': {'v20': summarize(train, tr_old), 'v21': summarize(train, tr_new),
                       'kalibracja_22': summarize(train, tr_cand)},
        'test_2025': {'v20': summarize(test, te_old), 'v21': summarize(test, te_new),
                      'kalibracja_22': summarize(test, te_cand)},
    }
    by_league = {}
    for league in sorted({m.league for m in test}):
        idx = [i for i, m in enumerate(test) if m.league == league]
        subset = [test[i] for i in idx]
        by_league[league] = {
            'v20': summarize(subset, [te_old[i] for i in idx]),
            'v21': summarize(subset, [te_new[i] for i in idx]),
            'kalibracja_22': summarize(subset, [te_cand[i] for i in idx]),
        }
    mm = all_metrics['test_2025']
    ci = pair_bootstrap_ci(test, te_new, te_cand)
    gain_brier_21 = mm['v21']['brier'] - mm['kalibracja_22']['brier']
    gain_brier_20 = mm['v20']['brier'] - mm['kalibracja_22']['brier']
    max_league_loss = max(
        v['kalibracja_22']['brier'] - v['v21']['brier'] for v in by_league.values()
    )
    # Wartosc progu wpisana przed ocena. Pojedynczy test retrospektywny
    # nie wystarcza jeszcze do publikacji modelu dla klientow.
    passed_history = (
        gain_brier_21 >= 0.002 and gain_brier_20 >= 0.002
        and mm['kalibracja_22']['log_loss'] <= min(mm['v20']['log_loss'], mm['v21']['log_loss']) + 0.001
        and max_league_loss <= 0.003 and ci[0] > 0.0
    )
    status = 'KANDYDAT_DO_TESTOW_PROSPEKTYWNYCH' if passed_history else 'BRAK_POTWIERDZONEJ_POPRAWY'
    result = {
        'name': 'RZOTKIEWKA 2.2 – audyt, NIE wydanie produkcyjne',
        'input_rows': len(records), 'train_season': SEASON_TRAIN, 'test_season': SEASON_TEST,
        'n_train': len(train), 'n_test': len(test),
        'data_cutoff_rule': 'as_of_utc = kickoff_utc - 168 h; bez niezaleznej weryfikacji archiwalnosci API',
        'fit_family': fit['family'], 'fit_params': params.__dict__,
        'train_selection_score': fit['selection_score'],
        'train_complexity_penalty': fit['penalty'],
        'metrics': all_metrics, 'by_league_test': by_league,
        'draw_bins_test_v21': probability_bins(test, te_new, 'v21'),
        'draw_bins_test_calibrated': probability_bins(test, te_cand, 'kalibracja_22'),
        'brier_gain_vs_v21': gain_brier_21,
        'brier_gain_vs_v20': gain_brier_20,
        'bootstrap_95pct_gain_vs_v21_by_date': ci,
        'max_league_brier_loss_vs_v21': max_league_loss,
        'historical_gate_passed': passed_history,
        'recommendation': status,
        'note': ('Dobor parametrow tylko na sezonie 2024; ewaluacja na 2025. '
                 'Retrospektywny test z jednego okresu, bez kursow i ROI. '
                 'Brak gwarancji przewagi; przed wdrozeniem zbierac prognozy ex ante.'),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'ocena_22.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (out_dir / 'mecze_test_22.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['league','season','match_id','kickoff_utc','home','away','outcome',
                         'v20_p1','v20_px','v20_p2','v21_p1','v21_px','v21_p2',
                         'kal_p1','kal_px','kal_p2','v21_typ','kal_typ','v21_brier','kal_brier'])
        for m, old, new, cal in zip(test, te_old, te_new, te_cand):
            writer.writerow([m.league, m.season, m.match_id, m.kickoff_utc,
                             m.home, m.away, m.outcome,
                             *[f'{x:.6f}' for x in old], *[f'{x:.6f}' for x in new],
                             *[f'{x:.6f}' for x in cal], argmax(new), argmax(cal),
                             f'{brier(new,m.outcome):.6f}', f'{brier(cal,m.outcome):.6f}'])
    (out_dir / 'RAPORT_22.md').write_text(make_report(result), encoding='utf-8')
    return result


def make_report(r: dict) -> str:
    mt, mv = r['metrics']['train_2024'], r['metrics']['test_2025']
    f = lambda x: f'{x:.4f}'
    perc = lambda x: f'{100*x:.1f}%'
    t = [
        '# 🫜 RZOTKIEWKA AI — audyt 2.2', '',
        '**To nie jest wersja produkcyjna silnika.** Paczka testuje kalibracje',
        'na historycznych prognozach 2.1 i sprawdza, czy poprawa przechodzi',
        'kontrole poza probą treningową.', '',
        f"- Dane: {r['input_rows']} meczów; sezon 2024 = **trening {r['n_train']}**, "
        f"sezon 2025 = **test chronologiczny {r['n_test']}**.",
        '- Funkcja wyboru: Brier + kara za złożoność na treningu; test 2025 bez dopasowania.',
        f"- Wybrana metoda: **{r['fit_family']}**, parametry {json.dumps(r['fit_params'], ensure_ascii=False)}.",
        '', '## Porównanie na sezonie 2025 (test)', '',
        '| Model | Trafność 1X2 | Brier ↓ | Log loss ↓ | Średnie P(X) |',
        '|---|---:|---:|---:|---:|',
    ]
    for key, label in [('v20','2.0'),('v21','2.1'),('kalibracja_22','2.1 + kalibracja eksperymentalna')]:
        m = mv[key]
        t.append(f"| {label} | {perc(m['accuracy'])} | {f(m['brier'])} | {f(m['log_loss'])} | {perc(m['avg_p_x'])} |")
    t += ['', '## Porównanie na sezonie 2024 (trening)', '',
          '| Model | Trafność 1X2 | Brier ↓ | Log loss ↓ |', '|---|---:|---:|---:|']
    for key, label in [('v20','2.0'),('v21','2.1'),('kalibracja_22','kalibracja eksperymentalna')]:
        m = mt[key]
        t.append(f"| {label} | {perc(m['accuracy'])} | {f(m['brier'])} | {f(m['log_loss'])} |")
    t += ['', '## Rozbicie testu na ligi', '',
          '| Liga | Meczów | Brier 2.0 | Brier 2.1 | Brier kalibracji |',
          '|---|---:|---:|---:|---:|']
    for league, scores in r['by_league_test'].items():
        t.append(f"| {league} | {scores['v21']['n']} | {f(scores['v20']['brier'])} | "
                 f"{f(scores['v21']['brier'])} | {f(scores['kalibracja_22']['brier'])} |")
    t += ['', '## Decyzja', '',
          f"**{r['recommendation']}**", '',
          f"Zmiana Brier vs 2.1 (plus = lepiej): **{f(r['brier_gain_vs_v21'])}**.",
          f"95% przedział bootstrap poprawy, według dni meczowych: "
          f"**[{f(r['bootstrap_95pct_gain_vs_v21_by_date'][0])}, "
          f"{f(r['bootstrap_95pct_gain_vs_v21_by_date'][1])}]**.",
          '', 'Warunki przejścia historycznego progu: przewaga Brier co najmniej',
          '0.002 nad 2.0 i 2.1, log loss nie gorszy o ponad 0.001,',
          'maksymalna strata w lidze nie większa niż 0.003, dolna granica',
          'bootstrapowej roznicy Brier > 0.', '',
          '## Co dalej', '',
          '1. Jeżeli bramka nie przeszła: NIE podmieniać forecast_engine.py.',
          '2. Zbierać prognozy z podpisaną datą ich utworzenia PRZED startem meczu.',
          '3. Dodać kursy z czasu prognozy i koszty przed badaniem ROI lub premium.',
          '4. Rozszerzać ligę/dyscyplinę dopiero po sprawdzeniu jakości danych.', '',
          '**Ograniczenia:** symulacja retrospektywna, brak potwierdzenia',
          'archiwalności danych z API, brak kursów i ROI, test tylko z dwóch sezonów;',
          'test historyczny nie oznacza udowodnionej przewagi predykcyjnej.',
    ]
    return '\n'.join(t) + '\n'


def self_test() -> None:
    assert abs(brier((1, 0, 0), '1')) < 1e-10
    assert abs(brier((0, 1, 0), '1') - 2.0) < 1e-10
    assert abs(logloss((0.5, 0.25, 0.25), '1') - math.log(2)) < 1e-10
    assert argmax((0.2, 0.6, 0.2)) == 'X'
    x = (0.42, 0.28, 0.30)
    actual = transform(x, Params())
    assert max(abs(a - b) for a, b in zip(actual, x)) < 1e-12
    assert abs(sum(transform(x, Params(1.2, 0.12, -0.05))) - 1) < 1e-12
    fake = Match('bl1','2025','1','2025-09-02T12:00:00Z','2025-08-26T12:00:00Z',
                 'A','B','1',x,x)
    try:
        fit_train_only([fake])
        raise AssertionError('Dobor parametrow z sezonu testowego nie zostal zablokowany')
    except ValueError:
        pass
    print('OK: 7 kontroli (Brier, logloss, typ, softmax, brak wycieku)')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=Path('data/mecze_21.csv'))
    parser.add_argument('--out', type=Path, default=Path('wyniki_22'))
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    records = read_matches(args.csv)
    summary = run(records, args.out)
    print('Testy OK; meczow:', summary['input_rows'])
    print('Metoda:', summary['fit_family'], summary['fit_params'])
    print('Decyzja:', summary['recommendation'])
    print('Raport:', args.out / 'RAPORT_22.md')


if __name__ == '__main__':
    main()
