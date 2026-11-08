#!/usr/bin/env python3
"""RZOTKIEWKA 1.7: audytowalne prognozy, kontrola wynikow i diagnostyka 1X2.

Dziala bez zewnetrznych zaleznosci; kontrola planowana co 2 godziny przez GitHub Actions.
Nie wykonuje zakladow, nie obsluguje kont ani platnosci.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

BASE = 'https://api.openligadb.de/getmatchdata'
LEAGUES = {'bl1': 'Bundesliga', 'bl2': '2. Bundesliga', 'bl3': '3. Liga'}
FILE = Path(__file__).resolve().parent / 'predictions.json'
MODEL_VERSION = '1.3.0'
MIN_LEAGUE = 24
MIN_TEAM = 4
RECENT = 8
SETTLE_HOURS = 3
MIN_LEAD_HOURS = 2
MAX_LEAD_DAYS = 8
MAX_GOALS = 12


def utc_now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def parse_date(raw):
    utc_value = raw.get('matchDateTimeUTC')
    local_value = raw.get('matchDateTime')
    value = utc_value or local_value
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc if utc_value else ZoneInfo('Europe/Berlin'))
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def parse_score(raw):
    if raw.get('matchIsFinished') is not True:
        return None
    for r in raw.get('matchResults') or []:
        if not isinstance(r, dict):
            continue
        if r.get('resultTypeID') != 2 and 'endergebnis' not in str(r.get('resultName', '')).lower():
            continue
        a, b = r.get('pointsTeam1'), r.get('pointsTeam2')
        if type(a) is int and type(b) is int and a >= 0 and b >= 0:
            return [a, b]
    return None


def normalize_match(raw):
    if not isinstance(raw, dict):
        return None
    dt = parse_date(raw)
    home, away = raw.get('team1') or {}, raw.get('team2') or {}
    if not isinstance(home, dict) or not isinstance(away, dict):
        return None
    id_, hid, aid = raw.get('matchID'), home.get('teamId'), away.get('teamId')
    if not dt or not all(type(v) is int and v > 0 for v in (id_, hid, aid)):
        return None
    if not isinstance(home.get('teamName'), str) or not isinstance(away.get('teamName'), str):
        return None
    return {
        'id': id_, 'kickoff': dt, 'home_id': hid, 'away_id': aid,
        'home': home['teamName'][:90], 'away': away['teamName'][:90],
        'score': parse_score(raw),
    }


def prior_history(matches, kickoff, now):
    limit = min(kickoff, now) - timedelta(hours=SETTLE_HOURS)
    return [m for m in matches if m['score'] is not None and m['kickoff'] <= limit]


def team_recent(history, tid):
    return sorted((m for m in history if m['home_id'] == tid or m['away_id'] == tid),
                  key=lambda m: m['kickoff'], reverse=True)[:RECENT]


def team_rates(rows, tid, venue, typical):
    # Recency: wagi kolejnych meczow (najnowszy -> starszy): 1.00 do 0.65.
    overall_for = overall_against = overall_weight = 0.0
    venue_for = venue_against = venue_weight = 0.0
    for i, m in enumerate(rows):
        weight = 1.0 - 0.05 * i
        is_home = m['home_id'] == tid
        scored = m['score'][0 if is_home else 1]
        conceded = m['score'][1 if is_home else 0]
        overall_for += weight * scored
        overall_against += weight * conceded
        overall_weight += weight
        if is_home == (venue == 'home'):
            venue_for += weight * scored
            venue_against += weight * conceded
            venue_weight += weight
    smooth_for = (overall_for + 6 * typical) / (overall_weight + 6)
    smooth_against = (overall_against + 6 * typical) / (overall_weight + 6)
    return ((venue_for + 4 * smooth_for) / (venue_weight + 4),
            (venue_against + 4 * smooth_against) / (venue_weight + 4))


def clamp(value, low, high):
    return max(low, min(high, value))


def poisson(lam):
    result = [math.exp(-lam)]
    for k in range(1, MAX_GOALS):
        result.append(result[-1] * lam / k)
    result.append(max(0.0, 1.0 - sum(result)))
    return result


def predict(match, matches, now):
    history = prior_history(matches, match['kickoff'], now)
    home_rows = team_recent(history, match['home_id'])
    away_rows = team_recent(history, match['away_id'])
    if len(history) < MIN_LEAGUE or min(len(home_rows), len(away_rows)) < MIN_TEAM:
        return None
    home_goals = sum(m['score'][0] for m in history)
    away_goals = sum(m['score'][1] for m in history)
    avg_home = (home_goals + 12 * 1.45) / (len(history) + 12)
    avg_away = (away_goals + 12 * 1.15) / (len(history) + 12)
    typical = (avg_home + avg_away) / 2
    hf, ha = team_rates(home_rows, match['home_id'], 'home', typical)
    af, aa = team_rates(away_rows, match['away_id'], 'away', typical)
    exp_home = clamp(avg_home * math.sqrt(clamp(hf / avg_home, .5, 1.8) *
                                          clamp(aa / avg_home, .5, 1.8)), .35, 3.5)
    exp_away = clamp(avg_away * math.sqrt(clamp(af / avg_away, .5, 1.8) *
                                          clamp(ha / avg_away, .5, 1.8)), .35, 3.5)
    probs = {'1': 0.0, 'X': 0.0, '2': 0.0}
    for i, p1 in enumerate(poisson(exp_home)):
        for j, p2 in enumerate(poisson(exp_away)):
            probs['1' if i > j else 'X' if i == j else '2'] += p1 * p2
    total = sum(probs.values())
    probs = {k: round(probs[k] / total, 6) for k in ('1', 'X', '2')}
    # Kompensacja zaokraglenia do dokladnie 1,000000.
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


def sha256(obj):
    encoded = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def result_outcome(score):
    return '1' if score[0] > score[1] else '2' if score[0] < score[1] else 'X'


def create_record(league, season, m, f, now):
    snapshot = {
        'match_id': m['id'], 'league': league, 'season': season,
        'home': m['home'], 'away': m['away'], 'kickoff': iso(m['kickoff']),
        'created_at': iso(now), 'model_version': MODEL_VERSION,
        **f,
    }
    return {
        'id': f'{league}-{season}-{m["id"]}',
        'snapshot': snapshot,
        'snapshot_sha256': sha256(snapshot),
        'settlement': {'state': 'pending', 'score': None, 'outcome': None, 'graded_at': None},
    }


def valid_doc(doc):
    """Odrzuc niepoprawne migawki i rozliczenia przed zapisem."""
    if not isinstance(doc, dict) or doc.get('schema') != 1 or not isinstance(doc.get('forecasts'), list):
        raise ValueError('predictions.json ma niewlasciwy format')
    ids = set()
    for rec in doc['forecasts']:
        if not isinstance(rec, dict) or not isinstance(rec.get('snapshot'), dict):
            raise ValueError('Nieprawidlowy rekord archiwum')
        snapshot = rec['snapshot']
        rid = rec.get('id')
        if not isinstance(rid, str) or not rid:
            raise ValueError('Nieprawidlowy identyfikator rekordu')
        if rid in ids:
            raise ValueError('Zduplikowany rekord w archiwum')
        ids.add(rid)
        if sha256(snapshot) != rec.get('snapshot_sha256'):
            raise ValueError(f'Wykryto zmiane zamrozonej prognozy: {rid}')
        probabilities = snapshot.get('probabilities')
        if (not isinstance(probabilities, dict)
            or any(type(probabilities.get(k)) not in (float, int) or
                   not 0 <= probabilities[k] <= 1 for k in ('1', 'X', '2'))
            or abs(sum(probabilities[k] for k in ('1', 'X', '2')) - 1) > 0.00001):
            raise ValueError(f'Nieprawidlowe prawdopodobienstwa: {rid}')
        try:
            created = datetime.fromisoformat(snapshot['created_at'].replace('Z', '+00:00'))
            kickoff = datetime.fromisoformat(snapshot['kickoff'].replace('Z', '+00:00'))
            if created.tzinfo is None or kickoff.tzinfo is None or created >= kickoff:
                raise ValueError('Nieprawidlowa chronologia')
        except (KeyError, AttributeError, TypeError, ValueError) as exc:
            raise ValueError(f'Nieprawidlowy czas prognozy: {rid}') from exc
        settlement = rec.get('settlement')
        if not isinstance(settlement, dict) or settlement.get('state') not in ('pending', 'graded'):
            raise ValueError(f'Nieprawidlowy status rozliczenia: {rid}')
        if settlement['state'] == 'graded':
            score = settlement.get('score')
            if (not isinstance(score, list) or len(score) != 2
                or any(type(n) is not int or n < 0 for n in score)
                or settlement.get('outcome') != result_outcome(score)):
                raise ValueError(f'Niespojne rozliczenie: {rid}')
            try:
                at = datetime.fromisoformat(settlement['graded_at'].replace('Z', '+00:00'))
                if at.tzinfo is None or at < kickoff:
                    raise ValueError('Bad timestamp')
            except (KeyError, TypeError, AttributeError, ValueError) as exc:
                raise ValueError(f'Nieprawidlowy czas rozliczenia: {rid}') from exc
        elif (settlement.get('score') is not None or settlement.get('outcome') is not None
              or settlement.get('graded_at') is not None):
            raise ValueError(f'Oczekujace rozliczenie ma wynik: {rid}')
    return doc

def fetch_matches(league, season):
    url = f'{BASE}/{league}/{season}'
    req = Request(url, headers={'User-Agent': 'Rzotkiewka-FootballLab/1.7 (public GitHub Actions)','Accept': 'application/json'})
    data = None
    for attempt in range(3):
        try:
            with urlopen(req, timeout=30) as response:
                data = json.load(response)
            break
        except (HTTPError, URLError, TimeoutError) as exc:
            if isinstance(exc, HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 2:
                raise
            print(f'Pobieranie {league}/{season}: chwilowy blad, ponowienie {attempt + 1}/2: {exc}')
            time.sleep(2 * (attempt + 1))
    if not isinstance(data, list):
        raise ValueError(f'Niepoprawna odpowiedz OpenLigaDB: {league}')
    matches = [normalize_match(r) for r in data]
    return sorted((m for m in matches if m), key=lambda m: m['kickoff'])


def apply_league(doc, league, season, matches, now):
    records = {r['id']: r for r in doc['forecasts']}
    new_count = graded_count = 0
    for m in matches:
        rid = f'{league}-{season}-{m["id"]}'
        if rid in records:
            existing = records[rid]
            if m['score'] is not None and now >= m['kickoff'] + timedelta(hours=SETTLE_HOURS):
                score = m['score']
                out = result_outcome(score)
                settlement = existing['settlement']
                if settlement.get('score') != score or settlement.get('outcome') != out:
                    existing['settlement'] = {'state': 'graded', 'score': score,
                                              'outcome': out, 'graded_at': iso(now)}
                    graded_count += 1
            continue
        if m['score'] is not None:
            continue  # Nigdy nie tworzymy prognoz po zakonczonym meczu.
        if not (now + timedelta(hours=MIN_LEAD_HOURS) < m['kickoff'] <= now + timedelta(days=MAX_LEAD_DAYS)):
            continue
        f = predict(m, matches, now)
        if f is None:
            continue
        rec = create_record(league, season, m, f, now)
        records[rid] = rec
        new_count += 1
    doc['forecasts'] = sorted(records.values(),
                              key=lambda x: (x['snapshot']['kickoff'], x['id']))
    return new_count, graded_count


def update_doc(doc, data_by_league, now):
    doc = valid_doc(doc)
    new_count = graded_count = 0
    for (league, season), matches in data_by_league.items():
        added, graded = apply_league(doc, league, season, matches, now)
        new_count += added
        graded_count += graded
    if new_count or graded_count:
        doc['updated_at'] = iso(now)
    valid_doc(doc)
    return doc, new_count, graded_count



def diagnose_league(doc, league, season, matches, now):
    """Tylko analiza przyczyn: NIE zmienia archiwum i NIE tworzy typow."""
    ids = {rec['id'] for rec in doc['forecasts']}
    counts = {
        'archiwum': 0,
        'za_blisko': 0,
        'poza_oknem': 0,
        'za_malo_danych': 0,
        'gotowe_do_prognozy': 0,
    }
    future = sorted((m for m in matches
                     if m['score'] is None and m['kickoff'] > now),
                    key=lambda m: m['kickoff'])
    for m in future:
        rid = f'{league}-{season}-{m["id"]}'
        if rid in ids:
            counts['archiwum'] += 1
        elif m['kickoff'] <= now + timedelta(hours=MIN_LEAD_HOURS):
            counts['za_blisko'] += 1
        elif m['kickoff'] > now + timedelta(days=MAX_LEAD_DAYS):
            counts['poza_oknem'] += 1
        else:
            history = prior_history(matches, m['kickoff'], now)
            h = team_recent(history, m['home_id'])
            a = team_recent(history, m['away_id'])
            if len(history) < MIN_LEAGUE or min(len(h), len(a)) < MIN_TEAM:
                counts['za_malo_danych'] += 1
            else:
                counts['gotowe_do_prognozy'] += 1

    print(f'DIAGNOZA {league} {season}: przyszle bez wyniku={len(future)}, '
          f'juz zapisane={counts["archiwum"]}, '
          f'start za <= {MIN_LEAD_HOURS}h={counts["za_blisko"]}, '
          f'dalej niz {MAX_LEAD_DAYS} dni={counts["poza_oknem"]}, '
          f'za malo danych={counts["za_malo_danych"]}, '
          f'kwalifikuje sie={counts["gotowe_do_prognozy"]}')
    if future:
        m = future[0]
        print(f'NAJBLIZSZY MECZ {league}: {m["home"]} - {m["away"]}, '
              f'{iso(m["kickoff"])} (UTC)')
    else:
        print(f'NAJBLIZSZY MECZ {league}: brak przyszlych meczow w odpowiedzi API')
    return counts

def run():
    now = utc_now()
    year = now.year if now.month >= 7 else now.year - 1
    default = {'schema': 1, 'updated_at': None, 'forecasts': []}
    doc = json.loads(FILE.read_text(encoding='utf-8')) if FILE.exists() else default
    valid_doc(doc)  # Sprawdz archiwum przed odczytem zaleglych typow.
    data = {}
    # Rozliczaj takze zalegle prognozy z poprzednich sezonow bez ich przeliczania.
    targets = {(league, year) for league in LEAGUES}
    for rec in doc.get('forecasts', []):
        snap = rec.get('snapshot', {})
        if (rec.get('settlement', {}).get('state') == 'pending'
                and snap.get('league') in LEAGUES
                and type(snap.get('season')) is int
                and year - 3 <= snap['season'] < year):
            targets.add((snap['league'], snap['season']))
    for league, season in sorted(targets):
        try:
            matches = fetch_matches(league, season)
            if not matches:
                raise ValueError('Pusta lista spotkan (brak aktualizacji)')
            data[(league, season)] = matches
            print(f'{league} {season}: {len(matches)} spotkan z OpenLigaDB')
        except Exception as exc:
            print(f'OSTRZEZENIE: {league}/{season} niepobrana: {exc}')
    if not data:
        raise RuntimeError('Brak danych ze wszystkich lig; nie modyfikujemy archiwum')
    # Prawdziwe przyczyny braku prognoz sa widoczne w logach GitHub Actions.
    # Diagnostyka dziala na stanie archiwum PRZED aktualizacja.
    for (league, season), matches in sorted(data.items()):
        if season == year:
            diagnose_league(doc, league, season, matches, now)
    original = json.dumps(doc, ensure_ascii=False, sort_keys=True)
    doc, added, graded = update_doc(doc, data, now)
    updated = json.dumps(doc, ensure_ascii=False, sort_keys=True)
    if original != updated:
        tmp = FILE.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(tmp, FILE)
    print(f'Nowe prognozy: {added}; nowe/zmienione wyniki: {graded}; archiwum: {len(doc["forecasts"])}')
    if added == 0:
        print('INFO: Brak nowych typow. Szczegoly sa w liniach DIAGNOZA powyzej. '
              'To nie oznacza awarii, jesli API poprawnie zwrocilo spotkania.')


if __name__ == '__main__':
    run()
