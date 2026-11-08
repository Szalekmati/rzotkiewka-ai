#!/usr/bin/env python3
"""Offline: trening kalibracji na sezonie 2024, ewaluacja na 2025.

Odczytuje archiwalny raport v2.1, ale kalibruje kolumny old_p_*
pochodzace z zamrozonego silnika 2.0. Nigdy nie modyfikuje predictions.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

from candidate_v22 import OUTCOMES, PENALTY, fit, calibrated_probs, score

COLS = ('league','season','match_id','kickoff_utc','as_of_utc','outcome',
        'old_p_1','old_p_X','old_p_2','new_p_1','new_p_X','new_p_2')


def load_csv(path):
    result=[]
    seen=set()
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader=csv.DictReader(f)
        if not set(COLS).issubset(reader.fieldnames or []):
            raise ValueError('Brak kolumn w CSV backtestu 2.1')
        for d in reader:
            season=int(d['season'])
            if season not in (2024, 2025) or d['outcome'] not in OUTCOMES:
                raise ValueError('Oczekiwane sezony 2024/2025 i wynik 1/X/2')
            kickoff=datetime.fromisoformat(d['kickoff_utc'].replace('Z','+00:00'))
            asof=datetime.fromisoformat(d['as_of_utc'].replace('Z','+00:00'))
            if kickoff.tzinfo is None or asof.tzinfo is None or kickoff-asof!=timedelta(hours=168):
                raise ValueError('Bledne okno czasowe: oczekiwane T-168h')
            key=(d['league'], season, d['match_id'])
            if key in seen:
                raise ValueError(f'Duplikat meczu: {key}')
            seen.add(key)
            old={k:float(d[f'old_p_{k}']) for k in OUTCOMES}
            new={k:float(d[f'new_p_{k}']) for k in OUTCOMES}
            for p in (old, new):
                if (any(not math.isfinite(v) or v<0 or v>1 for v in p.values())
                        or abs(sum(p.values())-1)>0.00001):
                    raise ValueError(f'Nieprawidlowe prawdopodobienstwa {key}')
            result.append({'league':d['league'],'season':season,'match_id':d['match_id'],
                           'kickoff':kickoff,'as_of':asof,'outcome':d['outcome'],
                           'old':old,'previous':new})
    if not result or {r['season'] for r in result}!={2024,2025}:
        raise ValueError('Brakuje sezonu treningowego 2024 lub testowego 2025')
    return sorted(result,key=lambda r:(r['kickoff'],r['match_id']))


def auc(rows, prefix):
    """ROC AUC dla remisu; wyniki porownywane po rankingu, z remisami wagowo."""
    pos=sorted([r[prefix]['X'] for r in rows if r['outcome']=='X'])
    neg=sorted([r[prefix]['X'] for r in rows if r['outcome']!='X'])
    if not pos or not neg:
        return None
    # AUC = odsetek par, dla ktorych pX(remis) > pX(nie-remis)
    import bisect
    correct=sum(bisect.bisect_left(neg,x)+0.5*(bisect.bisect_right(neg,x)-bisect.bisect_left(neg,x)) for x in pos)
    return correct/(len(pos)*len(neg))


def metrics(rows, col):
    n=len(rows)
    if n==0:
        return None
    s=[score(r[col],r['outcome']) for r in rows]
    return {'n':n, 'accuracy':sum(z['pick']==r['outcome'] for z,r in zip(s,rows))/n,
            'brier':sum(z['brier'] for z in s)/n,
            'log_loss':sum(z['log_loss'] for z in s)/n,
            'p_x_mean':sum(r[col]['X'] for r in rows)/n,
            'draw_rate':sum(r['outcome']=='X' for r in rows)/n,
            'draw_auc':auc(rows,col),
            'picks':dict(Counter(z['pick'] for z in s))}


def paired_brier_ci(test, iterations=1200):
    """Orientacyjny blokowy bootstrap po tygodniach kalendarzowych.

    Nie zastępuje prospektywnej walidacji; zalezności wewnatrz sezonow
    mogą być silniejsze, niż uwzglednia próbkowanie tygodniami.
    """
    groups=defaultdict(list)
    for r in test:
        y,w,_=r['kickoff'].isocalendar()
        groups[(y,w)].append(r)
    blocks=list(groups.values())
    randomizer=random.Random(220)
    results=[]
    for _ in range(iterations):
        sample=[r for _ in blocks for r in randomizer.choice(blocks)]
        if not sample:
            continue
        delta=sum(score(r['v22'],r['outcome'])['brier']-score(r['old'],r['outcome'])['brier']
                  for r in sample)/len(sample)
        results.append(delta)
    results.sort()
    if not results:
        return None
    return [results[int(.025*(len(results)-1))],results[int(.975*(len(results)-1))]]


def run(rows):
    train=[r for r in rows if r['season']==2024]
    test=[r for r in rows if r['season']==2025]
    if max(r['kickoff'] for r in train) >= min(r['kickoff'] for r in test):
        raise ValueError('Nakladajace sie kalendarze treningu i testu')
    params=fit([(r['old'],r['outcome']) for r in train])
    for r in rows:
        r['v22']=calibrated_probs(r['old'],params)
    by_league={}
    for lg in sorted({r['league'] for r in test}):
        subset=[r for r in test if r['league']==lg]
        by_league[lg]={k:metrics(subset,k) for k in ('old','previous','v22')}
    return {'status':'EKSPERYMENT - NIE WDROZONO',
            'source':'zamrozony CSV z retrospektywnego backtestu 2.1',
            'model_base':'2.0.0', 'candidate':'2.2.0-lab',
            'train_season':2024,'test_season':2025,'train_n':len(train),'test_n':len(test),
            'lead_hours':168, 'penalty':PENALTY,
            'paired_brier_delta_95pct_week_bootstrap':paired_brier_ci(test),
            'params':{'log_power':params[0],'draw_bias':params[1],'away_bias':params[2]},
            'train':{k:metrics(train,k) for k in ('old','previous','v22')},
            'test':{k:metrics(test,k) for k in ('old','previous','v22')},
            'test_by_league':by_league,
            'limitations':[
                '2025 jest testem retrospektywnym i nie dowodzi przyszlej skutecznosci.',
                'Sezon 2024 sluzyl do strojenia kalibracji, 2025 jedynie do wstepnej walidacji.',
                'Wyniki bazuja na zapisanych P(1/X/2) z backtestu 2.1; nie sa nowymi migawkami na zywo.',
                'Brak archiwalnych kursow bukmacherskich - nie mozna wyliczyc przewagi ani ROI.',
                'Model moze byc niestabilny miedzy sezonami; potrzebna dalsza walidacja.',
            ]}


def report(d):
    def p(x):return f'{100*x:.2f}%'
    def num(x):return '—' if x is None else f'{x:.5f}'
    old,v21,v22=(d['test'][k] for k in ('old','previous','v22'))
    s=['# RZOTKIEWKA AI 2.2 — LABORATORIUM', '',
       '**Status: eksperyment, NIE jest wgrany do silnika produkcyjnego.**','',
       f"Dane: trening **2024 ({d['train_n']} meczow)**; test **2025 ({d['test_n']} meczow)**; symulacja na T-7 dni.",
       'Kalibracja: Brier + regularyzacja L2, z bazowym modelem v2.0.','',
       '| Test 2025 | v2.0 | v2.1 | kandydat v2.2 |','|---|---:|---:|---:|']
    for label,key,fmt in [('Trafnosc 1X2','accuracy',p),('Brier ↓','brier',num),
                          ('Log loss ↓','log_loss',num),('Srednie P(X)','p_x_mean',p),
                          ('AUC remisu','draw_auc',num)]:
        s.append(f'| {label} | {fmt(old[key])} | {fmt(v21[key])} | {fmt(v22[key])} |')
    s+=['',f"Roznica Brier v2.2 - v2.0: **{v22['brier']-old['brier']:+.5f}** (ujemna jest lepsza).",
         f"Orientacyjny przedzial 95% roznicy Brier (bootstrap tygodniowy): **{d['paired_brier_delta_95pct_week_bootstrap'][0]:+.5f} do {d['paired_brier_delta_95pct_week_bootstrap'][1]:+.5f}**.",
         '', 'Parametry wyuczone tylko na 2024: '+json.dumps(d['params'],ensure_ascii=False),
         '', '## Ligi, sezon testowy 2025','','| Liga | N | Brier 2.0 | Brier 2.2 |','|---|---:|---:|---:|']
    for lg,part in d['test_by_league'].items():
        s.append(f"| {lg} | {part['old']['n']} | {num(part['old']['brier'])} | {num(part['v22']['brier'])} |")
    s+=['','## Ograniczenia','']
    s.extend('- '+x for x in d['limitations'])
    return '\n'.join(s)+'\n'


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=Path('data/mecze_21.csv'))
    parser.add_argument('--output', type=Path, default=Path('raport_22'))
    a=parser.parse_args(argv)
    d=run(load_csv(a.input))
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'wyniki_22.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (a.output/'RAPORT_22.md').write_text(report(d),encoding='utf-8')
    print(report(d))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
