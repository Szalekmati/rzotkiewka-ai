"""RZOTKIEWKA AI: wewnetrzny audyt metadanych lig API-FOOTBALL.

Tylko jedno zapytanie do /leagues?season=YYYY. Nie publikuje, nie zapisuje,
nie pobiera statystyk meczowych i nie zmienia prognoz/LAB.
"""
import argparse
from datetime import datetime, timezone
import os

from api_football_probe import api_get, verify_subscription

# Identyfikatory kandydatow, jeszcze NIE zatwierdzonych do publikacji.
CANDIDATES = (
    (39, "Premier League"),
    (140, "LaLiga"),
    (78, "Bundesliga"),
    (135, "Serie A"),
    (61, "Ligue 1"),
    (106, "Ekstraklasa"),
    (2, "Liga Mistrzow UEFA"),
)
FIELDS = (
    ("standings",),
    ("players",),
    ("injuries",),
    ("odds",),
    ("fixtures", "events"),
    ("fixtures", "lineups"),
    ("fixtures", "statistics_fixtures"),
)


def coverage_flag(coverage, path):
    item = coverage
    for name in path:
        if not isinstance(item, dict) or name not in item:
            return "?"
        item = item[name]
    if item is True:
        return "T"
    if item is False:
        return "N"
    return "?"


def check_quota(status, needed=1, reserve=100):
    limit = status["limit_day"]
    used = status["used_today"]
    if (not isinstance(limit, int) or isinstance(limit, bool)
            or not isinstance(used, int) or isinstance(used, bool)
            or used < 0 or used > limit or limit - used < reserve + needed):
        raise RuntimeError("Zbyt malo wolnego limitu; zapytanie wstrzymane.")


def summarize_leagues(payload, season):
    response = payload.get("response")
    if not isinstance(response, list):
        raise RuntimeError("Odpowiedz /leagues nie ma listy rozgrywek.")
    pages = payload.get("paging", {})
    if isinstance(pages, dict) and pages.get("total", 1) != 1:
        raise RuntimeError("Wynik stronicowany; nie wolno traktowac go jako pelnego.")
    expected = {n for n, _ in CANDIDATES}
    matched = {}
    for item in response:
        if not isinstance(item, dict):
            continue
        league = item.get("league")
        if not isinstance(league, dict):
            continue
        lid = league.get("id")
        if type(lid) is not int or lid not in expected:
            continue
        seasons = item.get("seasons")
        if not isinstance(seasons, list):
            continue
        chosen = [s for s in seasons if isinstance(s, dict) and s.get("year") == season]
        if not chosen:
            continue
        if lid in matched or len(chosen) != 1:
            raise RuntimeError("Niejednoznaczny identyfikator ligi lub sezonu.")
        coverage = chosen[0].get("coverage")
        matched[lid] = {
            "id": lid,
            "api_name": str(league.get("name", ""))[:70],
            "country": str((item.get("country") or {}).get("name", ""))[:45]
                       if isinstance(item.get("country"), dict) else "",
            "flags": {"/".join(path): coverage_flag(coverage, path) for path in FIELDS},
        }
    result = []
    for lid, label in CANDIDATES:
        found = matched.get(lid)
        result.append({"id": lid, "candidate": label, "found": found is not None, "details": found})
    return result, len(response)


def run(season, key):
    if not 2010 <= season <= datetime.now(timezone.utc).year + 1:
        raise ValueError("Sezon poza dozwolonym zakresem.")
    status = verify_subscription(api_get("status", key))
    check_quota(status)
    print(f"PRO OK: limit dzienny {status['limit_day']}; uzycie przed audytem: {status['used_today']}")
    data = api_get("leagues", key, {"season": str(season)})
    records, count = summarize_leagues(data, season)
    if count == 0:
        raise RuntimeError("Pusty katalog; nie mozna ocenic dostepnosci lig.")
    print(f"Katalog sezon {season}: odpowiedzi lig API {count}; badanych kandydatow {len(records)}")
    for row in records:
        if not row["found"]:
            print(f"ID {row['id']} | {row['candidate']}: BRAK potwierdzenia sezonu")
            continue
        details = row["details"]
        flags = " ".join(f"{k}={v}" for k, v in details["flags"].items())
        print(f"ID {row['id']} | {row['candidate']} | API: {details['api_name']} "
              f"| kraj: {details['country']} | metadata sezonu TAK | {flags}")
    print("T=deklarowana dostepnosc metadanych, N=brak, ?=nieznane. "
          "To NIE potwierdza kompletnosci ani praw publikacji.")
    print("Nie zapisano danych API, nie zmieniono prognoz ani LAB.")


def main():
    parser = argparse.ArgumentParser(description="Audyt tylko do odczytu metadanych lig")
    parser.add_argument("--season", default="2026")
    args = parser.parse_args()
    try:
        if not args.season.isdecimal() or len(args.season) != 4:
            raise ValueError("Sezon musi byc czterocyfrowy.")
        run(int(args.season), os.environ.get("API_FOOTBALL_KEY", ""))
    except (ValueError, RuntimeError) as err:
        parser.exit(1, f"Audyt API-FOOTBALL: {err}\n")


if __name__ == "__main__":
    main()
