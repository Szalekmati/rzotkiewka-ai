"""RZOTKIEWKA: two-source score cross-check, internal research only.

Compares pinned public OpenFootball snapshots and API-FOOTBALL in RAM.
Never saves, prints or republishes individual API match records; counts only.
No production changes, no model retraining and no LAB modifications.
"""
from collections import Counter
from datetime import date, datetime, timezone
import argparse
import os
import re
import unicodedata

from api_football_probe import api_get, verify_subscription
from api_football_league_catalog import check_quota
from api_football_fixtures_quality import utc_kickoff
from openfootball_history_audit import fetch_text, source_url

SEASON = 2026
SOURCES = (
    (39, "Premier League", {
        "repo": "openfootball/england",
        "commit": "9ee7a0c351805c99cc334478a9bf04b7d0432fec",
        "path": "2026-27/1-premierleague.txt",
    }),
    (140, "LaLiga", {
        "repo": "openfootball/espana",
        "commit": "80035a93dd4920985af52aa097a54a6fb888563b",
        "path": "2026-27/1-liga.txt",
    }),
)
MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
DAY_RE = re.compile(r"^\s*(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+"
                    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
                    r"(\d{1,2})(?:\s+(20\d{2}))?\s*$")
MATCH_RE = re.compile(r"^\s*(?:\d{1,2}:\d{2}\s+)?"
    r"(?P<home>.+?)\s+v\s+(?P<away>.+?)\s{2,}"
    r"(?P<home_goals>\d{1,2})-(?P<away_goals>\d{1,2})"
    r"(?:\s+\(\d{1,2}-\d{1,2}\))?\s*$")
EDGE_WORDS = {"fc", "cf", "afc"}
FINAL = {"FT", "AET"}  # PEN excluded: penalty score might not be final goals.


def clean_team(value):
    if not isinstance(value, str):
        return ""
    s = unicodedata.normalize("NFKD", value).casefold()
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("&", " and ")
    tokens = re.findall(r"[a-z0-9]+", s)
    while tokens and tokens[0] in EDGE_WORDS:
        tokens.pop(0)
    while tokens and tokens[-1] in EDGE_WORDS:
        tokens.pop()
    return " ".join(tokens)


def read_openfootball_matches(text, start, end):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Nieprawidlowy albo pusty plik OpenFootball.")
    observed_date = None
    records = []
    duplicate = set()
    invalid = 0
    for line in text.splitlines():
        m = DAY_RE.fullmatch(line)
        if m:
            weekday, mon, day, year = m.groups()
            month = MONTHS[mon]
            try:
                # This file starts in August 2026 and ends in 2027.
                observed_date = date(int(year) if year else
                                     (SEASON if month >= 7 else SEASON + 1),
                                     month, int(day))
                if WEEKDAYS[observed_date.weekday()] != weekday:
                    raise ValueError("Niezgodny dzien tygodnia w zrodle.")
            except ValueError as err:
                raise ValueError("Bledny naglowek daty OpenFootball.") from err
            continue
        if observed_date is None or not start <= observed_date <= end:
            continue
        if " v " not in line or not re.search(r"\d{1,2}-\d{1,2}", line):
            continue
        m = MATCH_RE.fullmatch(line)
        if not m:
            invalid += 1
            continue
        home, away = clean_team(m.group("home")), clean_team(m.group("away"))
        score = (int(m.group("home_goals")), int(m.group("away_goals")))
        if not home or not away or home == away or max(score) > 20:
            invalid += 1
            continue
        key = (observed_date, home, away)
        if key in duplicate:
            raise RuntimeError("OpenFootball ma zduplikowany mecz w probie.")
        duplicate.add(key)
        records.append((observed_date, home, away, score))
    if invalid:
        raise RuntimeError("Nie mozna jednoznacznie odczytac wynikow OpenFootball.")
    return records


def read_api_matches(payload, league_id, season, start, end):
    rows = payload.get("response")
    if not isinstance(rows, list) or type(payload.get("results")) is not int:
        raise RuntimeError("Niewlasciwa odpowiedz API.")
    if len(rows) != payload["results"] or not isinstance(payload.get("paging"), dict) or payload["paging"].get("total") != 1:
        raise RuntimeError("Niepelna strona odpowiedzi API.")
    result = []
    seen_ids = set()
    skipped = 0
    for item in rows:
        if not isinstance(item, dict):
            raise RuntimeError("Nieprawidlowy rekord API.")
        fixture, lg, teams, goals = (item.get(k) for k in ("fixture", "league", "teams", "goals"))
        if not all(isinstance(x, dict) for x in (fixture, lg, teams)):
            raise RuntimeError("Niepelna struktura meczu API.")
        fid = fixture.get("id")
        if type(fid) is not int or fid <= 0 or fid in seen_ids:
            raise RuntimeError("Brak lub duplikat identyfikatora meczu API.")
        seen_ids.add(fid)
        if lg.get("id") != league_id or lg.get("season") != season:
            raise RuntimeError("Niezgodna liga lub sezon API.")
        kickoff = utc_kickoff(fixture.get("date"))
        if kickoff is None or not start <= kickoff.date() <= end:
            raise RuntimeError("Nieprawidlowa data meczu API.")
        status = fixture.get("status")
        if not isinstance(status, dict) or status.get("short") not in FINAL:
            skipped += 1
            continue
        if not isinstance(goals, dict) or any(
                type(goals.get(side)) is not int or not 0 <= goals[side] <= 20
                for side in ("home", "away")):
            skipped += 1
            continue
        if not all(isinstance(teams.get(side), dict) for side in ("home", "away")):
            raise RuntimeError("Niekompletne druzyny w API.")
        home = clean_team(teams["home"].get("name"))
        away = clean_team(teams["away"].get("name"))
        if not home or not away or home == away:
            skipped += 1
            continue
        result.append((kickoff.date(), home, away, (goals["home"], goals["away"])))
    return result, skipped


def reconcile(source, official):
    """Exact normalized home+away, one-to-one only, at most 1 calendar day offset.

    Differences and nonmatches are reported separately; no fuzzy/guessed aliases.
    """
    remaining = list(official)
    matched = same_score = disagreed = date_shift = ambiguous = 0
    for d, home, away, score in source:
        candidates = [i for i, x in enumerate(remaining)
                      if x[1] == home and x[2] == away
                      and abs((x[0] - d).days) <= 1]
        if len(candidates) > 1:
            ambiguous += 1
        elif len(candidates) == 1:
            obs = remaining.pop(candidates[0])
            matched += 1
            if obs[0] != d:
                date_shift += 1
            if obs[3] == score:
                same_score += 1
            else:
                disagreed += 1
    return {
        "source_scores": len(source),
        "api_finals": len(official),
        "matched": matched,
        "same_score": same_score,
        "score_disagreements": disagreed,
        "day_shifts": date_shift,
        "ambiguous": ambiguous,
        "source_unmatched": len(source) - matched,
        "api_unmatched": len(remaining),
    }


def audit(start, end, key):
    status = verify_subscription(api_get("status", key))
    check_quota(status, needed=len(SOURCES), reserve=100)
    print(f"Status PRO OK. Limit dzienny {status['limit_day']}, wykorzystano przed audytem: {status['used_today']}.")
    print(f"Porownanie zrodel, okno {start} .. {end}; 2 ligi, max 2 zapytania /fixtures.")
    for league_id, label, spec in SOURCES:
        text = fetch_text(spec)
        source_rows = read_openfootball_matches(text, start, end)
        data = api_get("fixtures", key, {
            "league": str(league_id), "season": str(SEASON),
            "from": start.isoformat(), "to": end.isoformat(),
            "timezone": "UTC",
        })
        official, skipped = read_api_matches(data, league_id, SEASON, start, end)
        summary = reconcile(source_rows, official)
        metrics = " ".join(f"{k}={v}" for k, v in summary.items())
        print(f"{label}: {metrics} api_skipped_nonfinal_or_incomplete={skipped}")
        print(f"Archiwum przypiete: {source_url(spec)}")
    print("UWAGA: Nieporownane mecze to NIE potwierdzone bledy. "
          "Zgodne wyniki nie dowodza niezaleznej wiarygodnosci wszystkich meczow. "
          "Brak dostepu produkcyjnego, licencji do publikacji i dowodu jakosci modelu.")
    print("Wyniki indywidualne i dane dostawcy nie zostaly zapisane ani opublikowane.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-date", default="2026-08-21")
    parser.add_argument("--to-date", default="2026-08-31")
    args = parser.parse_args()
    try:
        start, end = date.fromisoformat(args.from_date), date.fromisoformat(args.to_date)
        if start < date(2026, 8, 1) or end > date(2026, 10, 15) or start > end or (end - start).days > 13:
            raise ValueError("Wymagane okno do 14 dni w 2026-08-01 .. 2026-10-15.")
        audit(start, end, os.environ.get("API_FOOTBALL_KEY", ""))
    except (RuntimeError, ValueError, OSError, UnicodeError) as err:
        parser.exit(1, f"Porownanie dwoch zrodel: {type(err).__name__}.\n")


if __name__ == "__main__":
    main()
