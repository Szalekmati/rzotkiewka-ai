"""RZOTKIEWKA: offline-safe, bounded audit of real API-FOOTBALL fixture records.

Live use requires GitHub Actions secret; only aggregates go to logs.
This NEVER writes fixtures, predictions, LAB snapshots or any provider data.
"""
import argparse
from datetime import date, datetime, timedelta, timezone
import os

from api_football_probe import api_get, verify_subscription
from api_football_league_catalog import CANDIDATES, check_quota

FINAL = {"FT", "AET", "PEN"}
NONFINAL = {"NS", "TBD", "PST", "CANC", "ABD", "SUSP", "AWD", "WO", "INT", "LIVE",
            "1H", "HT", "2H", "ET", "BT", "P"}
MAX_WINDOW_DAYS = 14
RESERVE_REQUESTS = 100


def bounded_window(season, from_text, to_text, today=None):
    today = today or datetime.now(timezone.utc).date()
    if type(season) is not int or not 2010 <= season <= today.year + 1:
        raise ValueError("Nieprawidlowy sezon.")
    try:
        start = date.fromisoformat(from_text) if from_text else today - timedelta(days=10)
        end = date.fromisoformat(to_text) if to_text else today
    except ValueError:
        raise ValueError("Daty musza miec format RRRR-MM-DD.") from None
    if start > end or (end - start).days >= MAX_WINDOW_DAYS or end > today:
        raise ValueError("Dozwolone maksymalnie 14 dni do dzis UTC; bez dat przyszlych.")
    if not (season <= start.year <= season + 1 and season <= end.year <= season + 1):
        raise ValueError("Daty nie naleza do wybranego sezonu.")
    return start, end


def valid_positive_id(value):
    return type(value) is int and value > 0


def utc_kickoff(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None or dt.utcoffset() is None:
        return None
    return dt.astimezone(timezone.utc)


def analyze_fixtures(payload, league_id, season, start, end, now=None):
    now = now or datetime.now(timezone.utc)
    response = payload.get("response")
    if not isinstance(response, list):
        raise RuntimeError("Brak listy meczow.")
    results = payload.get("results")
    if type(results) is not int or results != len(response):
        raise RuntimeError("Licznik wynikow jest niezgodny z odpowiedzia.")
    pages = payload.get("paging")
    if not isinstance(pages, dict) or pages.get("total") != 1:
        raise RuntimeError("Niepelna lub niejednoznaczna paginacja.")
    counts = {
        "mecze": len(response),
        "zakonczone": 0, "planowane_lub_inne": 0,
        "brak_id_meczu": 0, "duplikaty_id": 0,
        "zla_liga_sezon": 0, "zla_data": 0,
        "niepelne_druzyny": 0, "wynik_koncowy_niepelny": 0,
        "nieznany_status": 0, "stare_nierozliczone": 0,
    }
    seen = set()
    for row in response:
        if not isinstance(row, dict):
            counts["brak_id_meczu"] += 1
            continue
        fx = row.get("fixture")
        lg = row.get("league")
        teams = row.get("teams")
        if not isinstance(fx, dict):
            counts["brak_id_meczu"] += 1
            continue
        fid = fx.get("id")
        if not valid_positive_id(fid):
            counts["brak_id_meczu"] += 1
        elif fid in seen:
            counts["duplikaty_id"] += 1
        else:
            seen.add(fid)
        if not isinstance(lg, dict) or lg.get("id") != league_id or lg.get("season") != season:
            counts["zla_liga_sezon"] += 1
        kickoff = utc_kickoff(fx.get("date"))
        if kickoff is None or not start <= kickoff.date() <= end:
            counts["zla_data"] += 1
        if (not isinstance(teams, dict) or
                any(not isinstance(teams.get(side), dict) or
                    not valid_positive_id(teams[side].get("id")) or
                    not isinstance(teams[side].get("name"), str) or
                    not teams[side]["name"].strip() for side in ("home", "away")) or
                (isinstance(teams.get("home"), dict) and
                 isinstance(teams.get("away"), dict) and
                 teams["home"].get("id") == teams["away"].get("id"))):
            counts["niepelne_druzyny"] += 1
        status = fx.get("status")
        code = status.get("short") if isinstance(status, dict) else None
        if code in FINAL:
            counts["zakonczone"] += 1
            goals = row.get("goals")
            if (not isinstance(goals, dict) or any(
                    type(goals.get(side)) is not int or goals[side] < 0
                    for side in ("home", "away"))):
                counts["wynik_koncowy_niepelny"] += 1
        else:
            counts["planowane_lub_inne"] += 1
            if code not in NONFINAL:
                counts["nieznany_status"] += 1
            # Nie kazdy opozniony mecz zostal faktycznie rozegrany.
            if kickoff and kickoff < now - timedelta(hours=48) and code not in {
                    "PST", "CANC", "ABD", "AWD", "WO", "SUSP"}:
                counts["stare_nierozliczone"] += 1
    return counts


def audit(season, start, end, key):
    # Exactly seven real fixtures calls after one read-only status call.
    status = verify_subscription(api_get("status", key))
    check_quota(status, needed=len(CANDIDATES), reserve=RESERVE_REQUESTS)
    print(f"Plan PRO aktywny. Limit: {status['limit_day']}; wykorzystano przed audytem: {status['used_today']}.")
    print(f"Okno UTC: {start.isoformat()} .. {end.isoformat()}, sezon {season}.")
    for league_id, label in CANDIDATES:
        response = api_get("fixtures", key, {
            "league": str(league_id), "season": str(season),
            "from": start.isoformat(), "to": end.isoformat(), "timezone": "UTC",
        })
        summary = analyze_fixtures(response, league_id, season, start, end)
        metric_text = " ".join(f"{k}={v}" for k, v in summary.items())
        problems = sum(summary[x] for x in (
            "brak_id_meczu", "duplikaty_id", "zla_liga_sezon", "zla_data",
            "niepelne_druzyny", "wynik_koncowy_niepelny", "nieznany_status"))
        state = ("PUSTA_PROBA" if not summary["mecze"] else
                 "DO_WERYFIKACJI" if problems or summary["stare_nierozliczone"] else
                 "SCHEMAT_OK")
        print(f"Liga {league_id} ({label}) | {state} | {metric_text}")
    print("Status SCHEMAT_OK nie oznacza pelnych danych sezonu, legalnej publikacji "
          "ani jakosci modelu. Nie zapisano rekordow API i nie zmieniono LAB.")


def main():
    parser = argparse.ArgumentParser(description="Kontrolowany odczyt 7 lig, bez zapisu danych")
    parser.add_argument("--season", default="2026")
    parser.add_argument("--from-date", default="")
    parser.add_argument("--to-date", default="")
    args = parser.parse_args()
    try:
        if not args.season.isdecimal() or len(args.season) != 4:
            raise ValueError("Sezon musi miec cztery cyfry.")
        start, end = bounded_window(int(args.season), args.from_date, args.to_date)
        audit(int(args.season), start, end, os.environ.get("API_FOOTBALL_KEY", ""))
    except (ValueError, RuntimeError) as err:
        parser.exit(1, f"Audyt meczow: {err}\n")


if __name__ == "__main__":
    main()
